# Appendix N: Size and Speed — A Complete Guide to Compressing and Accelerating Wasm

> This is the book's technically densest appendix. It answers two questions: **"Why is my `.wasm` so large, and how do I shrink it?"** and **"Why isn't it as fast as I expected, and how do I speed it up?"**
>
> **One discipline runs through the whole thing**: **measure, then optimize, then measure again.** Every technique below has a shape it suits; applying them all indiscriminately usually produces a build pipeline that is both slow and hard to maintain.

---

# Part One: Size

## 1. Dissect First: Where Do Your Bytes Actually Go?

**Do this before touching a single flag.** Optimization without this step is guesswork.

```bash
# 1. The section-level budget: which section is fattest
wasm-objdump -h app.wasm
#   Type       start=0x0000000b end=0x000001a4 (size=0x00000199) count: 52
#   Function   ...
#   Code       start=0x00012f4a end=0x0031b2c1 (size=0x00308377) ← usually this one
#   Data       start=0x0031b2c3 end=0x004a9f10 (size=0x0018ec4d) ← but don't ignore this one

# 2. Symbol level: who is eating the Code section
twiggy top -n 30 app.wasm

# 3. Retention chains: who drags whom in (the most useful one)
twiggy dominators app.wasm

# 4. Why is a given function still here? (answering "but I never used it")
twiggy paths app.wasm -- 'core::fmt::write'
```

**Typical shares of the four sections, and the weapon for each**:

| Section | Typical share | What it is | The weapon |
|---|---|---|---|
| **Code** | 50–80% | Every function body | Compiler flags, LTO, dead code elimination, `wasm-opt` |
| **Data** | 10–45% | Static data, string constants, lookup tables | **Trim the data itself** (see §6), decompress at runtime |
| **Custom (`name`/DWARF)** | 0–30% | Debug symbols | `--strip-debug` (mandatory for release) |
| **Element / Table** | <5% | The function table's initial contents | Reduce the number of indirect call targets |

> **The first common misdiagnosis**: seeing a big file and rushing to tune `opt-level`. **But if your Data section is 45% of the file, squeezing another 10% out of Code buys you 5% overall.** Look at `wasm-objdump -h` first.

---

## 2. Compile-Time Flags: What They Actually Remove

### 2-1 Rust

```toml
[profile.release]
opt-level = "z"      # size first ("s" balanced, 3 speed first)
lto = "fat"          # whole-program optimization: cross-crate inlining + global dead code elimination
codegen-units = 1    # ★ gives LTO the full picture; parallel compilation slows, output shrinks noticeably
panic = "abort"      # removes unwinding tables and landing pads
strip = true         # strips the name section
overflow-checks = false
debug = false
incremental = false  # incremental compilation hinders cross-unit optimization
```

**What each one really removes**:

| Flag | What it removes | The cost |
|---|---|---|
| `opt-level = "z"` | Disables loop unrolling and **auto-vectorization** | **⚠️ This turns off SIMD auto-vectorization** — if you rely on it, use `"s"` or `3` |
| `lto = "fat"` | Dead code after cross-crate inlining, duplicate generic instances | Compile time rises noticeably |
| `codegen-units = 1` | Lets LTO see everything — **this one alone is often 5–15%** | No parallel compilation |
| `panic = "abort"` | Unwinding tables, landing pads, `Drop` unwind paths | Panics can't be caught (rarely used on Wasm anyway) |
| `strip = true` | The `name` custom section | **You lose readable stack traces** (see the trade-off in §12) |

### 2-2 Rust's biggest hidden size culprit: panic's formatting machinery

**This is the least-discovered slab of fat in the vast majority of Rust/Wasm projects.**

A single `panic!("index {} out of range", i)` drags **the whole of `core::fmt`'s formatting machinery** into the binary — a small machine with trait object dispatch, width/precision handling and floating-point formatting, **easily costing tens to hundreds of kilobytes**. And worse: **every `unwrap()`, every array index, every integer overflow check may reference it on the failure path.**

```bash
# Confirm whether it's the culprit
twiggy paths app.wasm -- 'core::fmt::write' | head -20
```

**The root fix (requires nightly)**:

```bash
cargo +nightly build --release --target wasm32-unknown-unknown \
  -Z build-std=std,panic_abort \
  -Z build-std-features=panic_immediate_abort
```

`panic_immediate_abort` turns every panic straight into an `unreachable` instruction, **and the entire formatting machinery plus every panic message string disappears**. For small modules, this one move often beats every other flag combined.

**The cost is honest**: **after a panic you get no message at all**, only a `RuntimeError: unreachable`. **This is a two-build decision — size in release, messages in debug — not a global one.**

**A more conservative approach** (no nightly needed):

```rust
// Avoid panics that format
let v = arr.get(i).ok_or(MyError::OutOfRange)?;   // rather than arr[i]
// Avoid Display / format!
// Use static strings rather than format!("...{}", x)
```

### 2-3 Rust's second culprit: monomorphization explosion

Generics in Rust are **monomorphized** — `Vec<u8>` and `Vec<u32>` produce two entirely separate copies of code. A complex generic function instantiated with ten types is ten copies.

```rust
// ❌ The whole function body is duplicated N times
pub fn process<P: AsRef<Path>>(path: P, data: &[u8]) { /* two hundred lines */ }

// ✅ A thin outer shell converts; a single inner instance does the heavy lifting
pub fn process<P: AsRef<Path>>(path: P, data: &[u8]) {
    process_inner(path.as_ref(), data)      // a thin shell — duplicating it is fine
}
fn process_inner(path: &Path, data: &[u8]) { /* two hundred lines, only one copy */ }
```

**This "generic thin shell plus concrete implementation" pattern is one of the most effective size techniques in the Rust ecosystem**, and `twiggy top` will list the duplicate instances for you to see.

### 2-4 C / C++

```bash
emcc app.cpp \
  -Oz \
  -flto \
  -fno-exceptions \                  # C++ exception unwind tables are usually large
  -fno-rtti \                        # typeid / dynamic_cast metadata
  -ffunction-sections -fdata-sections \
  -Wl,--gc-sections \                # drop unused sections wholesale
  -sASSERTIONS=0 \                   # remove runtime assertions and their message strings
  -sFILESYSTEM=0 \                   # ★ don't bundle a whole filesystem if you don't need MEMFS
  -sENVIRONMENT=web \                # drop the node/worker/shell branches
  -sMALLOC=emmalloc \                # a far smaller allocator than dlmalloc
  -sMINIMAL_RUNTIME=1 \              # minimal JS glue (with more restrictions)
  --closure 1 \                      # compress the JS glue with Closure Compiler
  -sEXPORTED_FUNCTIONS='["_main","_process"]' \
  -o app.js
```

**A few worth special attention**:

- **`-sFILESYSTEM=0`**: if your code never actually calls `fopen`, Emscripten may still link in the whole of MEMFS by default. **This one often saves tens of kilobytes of JS glue outright.**
- **`-sMALLOC=emmalloc`**: `emmalloc` is far smaller than the default `dlmalloc`, at the cost of being slower under some allocation patterns. **If your code barely allocates dynamically (everything through an arena, say), this is pure profit.**
- **`--closure 1`**: note that it compresses **the JS glue**, not the `.wasm`. For an Emscripten project, the glue alone can be tens of kilobytes.

### 2-5 Choosing an allocator

| Allocator | Size | Speed | Note |
|---|---|---|---|
| Rust's default (dlmalloc) | Medium | Good | The right choice in most cases |
| `emmalloc` (Emscripten) | **Small** | Medium | A good choice with simple allocation patterns |
| **A home-built bump/arena** | **Tiny** | **Very fast** | **See §11** — if your pattern is "allocate a batch, free it all at once," this wins both ways |
| `wee_alloc` | Tiny | Poor | ⚠️ **No longer maintained and has known memory reclamation issues; not recommended for new projects** |

---

## 3. `wasm-opt`: More Than Just a `-Oz`

**Binaryen's `wasm-opt` is the single highest-return tool in the whole chain**, and most people use exactly one flag of it.

```bash
wasm-opt -Oz \
  --strip-debug --strip-producers --strip-target-features \
  --low-memory-unused \
  --zero-filled-memory \
  --converge \
  app.wasm -o app.opt.wasm
```

**What it really does inside** (`-Oz` is a combination of passes):

| Pass category | Representative pass | What it does |
|---|---|---|
| Dead code and cleanup | `--dce`, `--vacuum`, `--remove-unused-module-elements` | Removes unreachable code and unused imports/globals/functions |
| Deduplication | `--duplicate-function-elimination` | **Merges byte-identical functions** — one antidote to monomorphization explosion |
| Inlining | `--inlining-optimizing` | Expands small functions, then re-optimizes the result |
| Instruction level | `--optimize-instructions` | Peephole optimization: `x*2` → `x<<1` and the like |
| Locals | `--simplify-locals`, `--coalesce-locals`, `--reorder-locals` | Reduces the count and index size of locals (**smaller indices cost fewer bytes under LEB128**) |
| Layout | `--reorder-functions` | **Reorders function indices by call frequency** so hot functions get small indices → shorter LEB128 encodings |

**Three frequently overlooked flags**:

- **`--converge`**: runs optimization repeatedly until it stops shrinking. **Usually squeezes out another 1–3%**, at the cost of doubled build time.
- **`--low-memory-unused`**: tells the optimizer "the low address range is unused," letting it make more aggressive assumptions about addressing. **Usually safe for Emscripten projects; be careful in projects with hand-written memory layouts.**
- **`--zero-filled-memory`**: declares memory starts zeroed, letting the optimizer remove redundant zeroing code.

> ⚠️ **The ordering trap**: `wasm-opt` must run **after `wasm-bindgen`**. `wasm-pack` does this by default, but if you wire the toolchain by hand, **running `wasm-opt` before `wasm-bindgen` lets it strip things bindgen still needs**, with the symptom being an inexplicable runtime `LinkError`.

---

## 4. `no_std` and Cutting the Standard Library

**When your module is a pure compute kernel**, the whole of `std` may be a burden:

```rust
#![no_std]
extern crate alloc;                  // heap allocation only, none of the rest of std

use alloc::vec::Vec;

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! { core::arch::wasm32::unreachable() }
```

**The gain**: you save `std`'s runtime initialization, I/O abstractions, threading and synchronization primitives, and — most importantly — the formatting machinery it drags in.
**The cost**: no `String` (use `alloc::string::String`), no `std::collections::HashMap` (switch to `hashbrown`), and half the ecosystem's crates don't support it.

**The test**: **if what your module exports is a pure function of the "feed bytes in, get bytes out" kind, `no_std` is almost always worth it.** If it needs files, time or randomness, the convenience `std` brings is usually worth those bytes.

---

## 5. Eliminating Cross-Language Duplication: `wasm-bindgen`'s Size Cost

```rust
// ❌ Every #[wasm_bindgen] generates a slice of JS glue and a Wasm-side shim
#[wasm_bindgen]
pub fn process_pixel(r: u8, g: u8, b: u8) -> u32 { /* ... */ }

// ✅ One coarse interface, looping internally
#[wasm_bindgen]
pub fn process_image(ptr: *mut u8, len: usize) { /* ... */ }
```

**This is simultaneously a size optimization and a performance optimization** (see §13) — **a fine-grained export interface is both fat and slow.**

**A few other concrete measures**:

- Returning a `Vec<u8>` goes through bindgen's allocate/free boilerplate; **returning `(ptr, len)` and letting JS read linear memory itself is leaner**.
- Enable **only the `js_sys` / `web_sys` features you use** — their feature lists are enormous, and enabling everything drags in a mass of bindings.
- `#[wasm_bindgen(js_name = "...")]` doesn't affect size, but attributes like `catch` / `getter` / `setter` generate extra boilerplate.

---

## 6. Data Is the Bulk: Generalizing FluffOS's Lesson

**Appendix L records one number: FluffOS's Wasm build cut ICU data from about 30 MB to about 780 KB (−97%), while the entire driver's code body is only 3.6 MB.**

**Generalize it into a rule**:

> **In the Wasm output of a large C/C++ project, more than half is often the data tables it dragged in, and you usually don't use 90% of them.**

**Common data fat and the corresponding surgery**:

| Data | Common size | Surgery |
|---|---|---|
| ICU / Unicode tables | A few MB to 30 MB | Keep only the rules you need (segmentation/collation/transliteration can each be trimmed) |
| Fonts | A few MB | Subset (keep only the characters used) |
| Language models / training data | Tens of MB | **Don't bundle it into the `.wasm`**; fetch at runtime (cacheable) |
| Time zone database | Hundreds of KB | Keep only the target regions |
| Built-in test data / samples | Frequently forgotten | Exclude with compile-time conditions |
| Lookup tables (trigonometry, CRC…) | KB to MB | **Consider computing at runtime** — CPU is usually cheaper than memory |

**And one more move: embed the data compressed and decompress at runtime.**

```
Compress a 2 MB data table with zstd to 400 KB, embed it in the Data section,
and expand it into linear memory at startup with a 15 KB decompressor.
→ a net saving of 1.6 MB of transfer, at the cost of a few extra milliseconds at startup.
⚠️ But confirm first: has the outer Brotli transport compression already done this for you?
   If so, this move merely relocates compression from the transport layer to the
   application layer, and may well be worse.
```

---

## 7. The Transport Layer: Brotli, and Something New That Changes the Game

### 7-1 Why Wasm suits Brotli particularly well

**Empirically Wasm's compression ratio is often 3.5–5×** (Appendix L's real case is 3.6 MB → 0.8 MB, about 4.5×). Three reasons:

1. **LEB128 makes small numbers a single byte**, with a highly concentrated distribution → low entropy.
2. **Opcodes are extremely repetitive**: a pattern like `20 xx 20 yy 6A` (load/load/add) appears tens of millions of times across a module.
3. **The Data section usually contains many zeros and repeated strings.**

```nginx
# Static pre-compression beats on-the-fly (saves CPU and lets you use the highest level)
brotli_static on;
# Produce: app.wasm + app.wasm.br (brotli -q 11)
```

### 7-2 ★ Compression Dictionary Transport

**This is the most important change in Wasm update distribution in years, and it barely appears in Wasm discussions at all.**

**The problem**: your `app.wasm` is 8 MB (1.8 MB after Brotli). You change three lines and ship a new version — **the user must re-download all 1.8 MB**, even though 99% of the bytes are identical to the old version in their cache.

**The solution**: **use the old version the user has already cached as the dictionary for compressing the new one.**

```http
# The first response: declare "this file may serve as a future dictionary"
HTTP/2 200
Content-Type: application/wasm
Use-As-Dictionary: match="/app-*.wasm"

# Later, when the user wants the new version, the browser attaches automatically:
Available-Dictionary: :pZGm1Av0IEBKARczz7exkNYsZb8LzaMrV7J32a2fFG4=:
Accept-Encoding: br, dcb, dcz

# The server compresses the new version using the old one as the dictionary:
HTTP/2 200
Content-Encoding: dcb        # Dictionary-Compressed Brotli (dcz = the Zstandard version)
→ what actually transfers may be only tens of kilobytes
```

**Status**: **RFC 9842**; **supported in Chrome 130+ and Edge 130+, in progress in Firefox**. On the CDN side, **Cloudflare shipped edge support in April 2026** (their implementation is itself a Zstandard compiled to Wasm).

**It matters especially for Wasm**, because Wasm applications have two characteristics: **(1)** a single large file; **(2)** most bytes stay unchanged across versions. **That is exactly the shape where differential compression works best.**

> 💡 **A corollary**: once this route becomes widespread, **the weight of the "should I split the module" decision drops** — one of splitting's main motivations (making an update re-download only part) is replaced by differential compression, while splitting's costs (extra round trips, cross-module calls) remain.

---

## 8. Splitting and Lazy Loading

| Approach | Mechanism | Suited to |
|---|---|---|
| **`wasm-split`** (Binaryen) | Splits a module into primary + secondary by profiling data, fetching the second on first call | A clear startup path with lots of functionality the user may never click |
| **Manual multi-module + shared memory** | Export `memory` from one side and import it on the other | Clear feature boundaries (PDF export, OCR language packs) |
| **Fetching assets at runtime** | Data stays out of the `.wasm`, loaded with `fetch` + the Cache API | Model weights, fonts, language packs |

```javascript
// Manual splitting: two modules share the same linear memory, so no data needs copying
const core = await WebAssembly.instantiateStreaming(fetch("core.wasm"), imports);
const pdf  = await WebAssembly.instantiateStreaming(fetch("pdf.wasm"), {
  env: { memory: core.instance.exports.memory },   // ★ the key
});
```

---

## 9. Size Optimization Return Table

| # | Approach | Typical gain | Cost | When to do it |
|---|---|---|---|---|
| 0 | **Trim the data itself** | **Up to −90%** | Needs domain judgement | **First** |
| 1 | `wasm-opt -Oz --converge` | −15~40% | Build time | Always |
| 2 | `lto` + `codegen-units=1` | −5~15% | Compile time | Always |
| 3 | **Brotli transport** | **−70~80% (transfer)** | Nearly zero | **Always** |
| 4 | `panic_immediate_abort` (Rust) | −30%+ for small modules | You lose panic messages | Release builds |
| 5 | `--strip-debug` | −0~30% | You lose stack traces | Release (keep a symbol-bearing copy) |
| 6 | Generic thin shells, removing monomorphization duplicates | −5~20% | Refactoring | Only if measured |
| 7 | `no_std` | −10~30% | Restricted ecosystem | Pure compute kernels |
| 8 | `-sFILESYSTEM=0` and other Emscripten flags | −tens of KB of glue | Restricted functionality | After confirming it's unused |
| 9 | Module splitting | −50%+ on the first screen | Architectural complexity | When the startup path is clear |
| 10 | **Compression Dictionary Transport** | **−90%+ on updates** | Needs CDN/server support | When you ship often |

---

# Part Two: Speed

## 10. Decomposing the Startup Path into Four Stages

**Eighty percent of "Wasm is slow" complaints are about startup, not steady state.** And startup is four independent costs, each with its own weapon:

```
① Network transfer  ── governed by compressed size and RTT ──→ all of Part One
② Compilation       ── linear in byte count                ──→ §10-1
③ Instantiation     ── allocate memory, run Data segment init, run start ──→ §10-2
④ Runtime init      ── global constructors, language runtime bootstrap,
                       data structure construction ──→ §10-3 ★ most underestimated
```

### 10-1 Four weapons for the compilation stage

```javascript
// ① Streaming compilation: start work when the first byte arrives (the server must return application/wasm)
const { instance } = await WebAssembly.instantiateStreaming(fetch("app.wasm"), imports);

// ② Compile once, share across N Workers (WebAssembly.Module is structured-cloneable)
const mod = await WebAssembly.compileStreaming(fetch("app.wasm"));
workers.forEach(w => w.postMessage({ mod }));      // ★ saves N−1 full compilations

// ③ On-disk code cache: give the .wasm a stable URL (a content-hashed filename is best)
//    the engine writes the optimized machine code into the HTTP cache, so return
//    visits skip the entire compilation stage
//    → a large module's second load is often an order of magnitude faster
```

**④ Tiered compilation is automatic, but you can understand it**: Liftoff emits executable code first (fast and bad), and TurboFan produces good code in the background and hot-swaps it in. **That means "for the first few hundred milliseconds after startup, your Wasm is running the unoptimized version"** — so if you benchmark immediately after startup, you are measuring Liftoff's numbers, not steady-state performance.

### 10-2 ★ Wizer: moving "initialization" to build time

**This is the most underestimated technique in server-side and CLI scenarios.**

Many modules do a lot of one-off work at startup: parsing configuration, building lookup tables, loading data structures, initializing an interpreter. **Wizer (Bytecode Alliance)'s idea is: do all of that at build time, then snapshot "the memory state after initialization" back into a new `.wasm`.**

```bash
# At build time: instantiate the module, run the init function, snapshot the result into a new module
wizer app.wasm -o app.initialized.wasm --allow-wasi
```

```rust
// Module side: mark which function is "initialization"
#[export_name = "wizer.initialize"]
pub extern "C" fn init() {
    LOOKUP_TABLE.set(build_expensive_table());   // this runs at build time
}
```

**The module you get at runtime already has the initialized memory image in its Data section** — nothing to do at startup. Official benchmarks claim **instantiation plus initialization is 1.35× to 6.00× faster**, with the real gain depending on how much initialization you were doing.

**Costs and limits**: **(1)** the snapshot enlarges the Data section (**size traded for startup speed**, in direct conflict with Part One — measure the trade-off); **(2)** initialization cannot depend on anything only available at runtime (time, randomness, network); **(3)** it is mainly for server-side/CLI, and browser use must weigh the size cost.

**Other forms of the same idea**:

| Technique | Scenario |
|---|---|
| **Wizer** | General pre-initialization snapshotting |
| `wasmtime compile` → `.cwasm` | **Backend AOT**: move compilation entirely before deployment, zero compilation at runtime |
| The engine's pooling allocator | A pre-allocated instance pool, saving the memory allocation of each instantiation |

### 10-3 That most-underestimated fourth stage

**After Pyodide finishes downloading 30 MB, it still has to bootstrap CPython.** An Emscripten project has to run every C++ global constructor. Those happen **after compilation completes**, and they never show up in a metric called "module load time."

```javascript
// Measure separately, or you'll optimize the wrong thing
const t0 = performance.now();
const mod = await WebAssembly.compileStreaming(fetch("app.wasm"));
const t1 = performance.now();                       // ← compilation
const inst = await WebAssembly.instantiate(mod, imports);
const t2 = performance.now();                       // ← instantiation
inst.exports.app_init();
const t3 = performance.now();                       // ← runtime initialization ★
console.log(`compile ${(t1-t0)|0}ms / instantiate ${(t2-t1)|0}ms / init ${(t3-t2)|0}ms`);
```

---

## 11. Steady-State Performance, Part One: Getting the Compiler to Emit Better Code

### 11-1 SIMD: enabling it isn't using it

```bash
# Rust
RUSTFLAGS="-C target-feature=+simd128" cargo build --release --target wasm32-unknown-unknown
# Emscripten
emcc -msimd128 -O3 ...
```

**Three realities you must know**:

1. **`opt-level = "z"` turns off auto-vectorization.** You cannot have minimum size and automatic SIMD at once — **this is a choice you must make.**
2. **Auto-vectorization is picky**: loop bounds must be known or inferable at compile time, there must be no data dependence, and no pointer aliasing doubts. **When it doesn't vectorize, the compiler doesn't warn you** — you have to read the disassembly or measure.
3. **Hand-written intrinsics are the fallback**:

```rust
use core::arch::wasm32::*;

pub fn add_f32x4(a: &[f32], b: &[f32], out: &mut [f32]) {
    for i in (0..a.len()).step_by(4) {
        unsafe {
            let va = v128_load(a.as_ptr().add(i) as *const v128);
            let vb = v128_load(b.as_ptr().add(i) as *const v128);
            v128_store(out.as_mut_ptr().add(i) as *mut v128, f32x4_add(va, vb));
        }
    }
}
```

**And don't forget Chapter 3's ceiling**: **Wasm SIMD is fixed at 128 bits**, so code hand-optimized for AVX2 (256) has its vector width halved outright on the port. **The typical speedup is 2–4×, not 8–16×.**

### 11-2 Bulk memory: a huge free lunch that gets overlooked

```c
// ❌ A byte-by-byte loop: one load and one store per byte
for (size_t i = 0; i < n; i++) dst[i] = src[i];

// ✅ Compiles to the single memory.copy instruction → the engine maps it to the host's
//    memcpy (SIMD-ized, alignment-optimized)
memcpy(dst, src, n);
```

**`memory.copy` / `memory.fill` have been core instructions since Wasm 2.0**, and engines map them directly onto highly optimized native `memcpy`/`memset`. **For large block moves the difference can be an order of magnitude.** Confirm your toolchain has bulk memory on (modern toolchains enable it by default).

### 11-3 Other codegen-level levers

| Feature | Gain | Note |
|---|---|---|
| **Branch hinting** (Wasm 3.0) | Lets the engine put the hot path in the fall-through | Driven by PGO or `likely()` annotations |
| **Tail calls** `return_call` | Deep recursion no longer blows the stack, and stack frames are saved | Interpreters and state machines benefit most |
| **Multi-value** | Multiple return values need not go through memory | Fewer load/store round trips |
| **Relaxed SIMD**'s `relaxed_madd` | Maps to hardware FMA | ⚠️ **Sacrifices determinism** (Appendix M §7) |
| **Typed function references** (Wasm 3.0) | Indirect calls skip the runtime signature check | Virtual-call-heavy C++/OOP benefits |

---

## 12. Steady-State Performance, Part Two: Memory and Cache

**Chapter 6 stated the key fact: an L1 hit is about 4 cycles, a DRAM access about 200.** So memory layout's impact often outweighs instruction-level optimization.

### 12-1 SoA rather than AoS

```rust
// ❌ AoS: computing the mean of x drags y and z into cache too
struct Particle { x: f32, y: f32, z: f32, vx: f32, vy: f32, vz: f32 }
let particles: Vec<Particle>;

// ✅ SoA: scan only xs — perfect cache locality, and the precondition for auto-vectorization
struct Particles { xs: Vec<f32>, ys: Vec<f32>, zs: Vec<f32>, /* ... */ }
```

### 12-2 Arena / bump allocators

**`malloc` is relatively expensive in Wasm** (it is a userspace implementation compiled in, with no operating system helping). **If your allocation pattern is "allocate a lot while processing one frame or one request, then throw it all away," a bump allocator wins overwhelmingly**:

```rust
struct Bump { buf: Vec<u8>, top: usize }
impl Bump {
    #[inline] fn alloc(&mut self, n: usize, align: usize) -> *mut u8 {
        let p = (self.top + align - 1) & !(align - 1);
        self.top = p + n;                       // allocation = one addition
        unsafe { self.buf.as_mut_ptr().add(p) }
    }
    #[inline] fn reset(&mut self) { self.top = 0; }   // freeing everything = one assignment
}
```

**It is simultaneously a size optimization** (it pairs with `-sMALLOC=none` or a tiny allocator) **and a performance optimization**.

### 12-3 Three concrete traps

| Trap | Explanation |
|---|---|
| **`memory.grow` on the hot path** | It invalidates every existing `TypedArray` view and may trigger a large memory remap. **Pre-allocate up to your ceiling; don't let it grow inside a loop.** |
| **Alignment hints** | `i32.load align=2` is a **hint, not a guarantee** — declaring it wrongly won't trap, but the engine may emit slower code because of it. **Let the compiler fill it in.** |
| **Random access across pages** | With a large linear memory, random access thrashes the TLB. **Sort when you can, chunk when you can.** |

---

## 13. Steady-State Performance, Part Three: The Boundary

**Chapter 2 said "the boundary is a toll booth"; here are the practical ways to lower the toll.**

```javascript
// ❌ Allocating a new Uint8Array to encode the string every time
const bytes = new TextEncoder().encode(str);
const ptr = wasm.alloc(bytes.length);
new Uint8Array(wasm.memory.buffer, ptr, bytes.length).set(bytes);

// ✅ encodeInto writes straight into Wasm memory, with no intermediate allocation
const view = new Uint8Array(wasm.memory.buffer, ptr, cap);
const { written } = new TextEncoder().encodeInto(str, view);
```

**Five rules**:

1. **Batch**: `process_image(ptr, w, h)` rather than `process_pixel()` a million times.
2. **Reuse views with `encodeInto` / `decode`**, avoiding an allocation each time.
3. **Return results through a ring buffer**, rather than one callback per event (standard practice for physics engines and game loops).
4. **Hold JS objects with `externref`**, avoiding a home-built "JS object ↔ integer handle" side table (whose maintenance cost and leak risk are both non-trivial).
5. **Measure the number of boundary crossings itself**: add a counter to the glue and you will often find it is an order of magnitude higher than you thought.

---

## 14. Steady-State Performance, Part Four: Parallelism

```javascript
// A Worker pool + SharedArrayBuffer (needs cross-origin isolation, see Chapter 5)
const mem = new WebAssembly.Memory({ initial: 256, maximum: 4096, shared: true });
// Each Worker instantiates the same Module against the same shared memory
```

**Three practical points**:

1. **Take the Worker count from `navigator.hardwareConcurrency`, but leave headroom** (the main thread still has to render). In practice `max(1, hc - 1)` is common.
2. **The main thread may not `Atomics.wait`** (the specification forbids it); use **`Atomics.waitAsync`**.
3. **The granularity of work splitting** must be coarse enough to cover the synchronization cost — **parallelism that is too fine-grained is slower than single-threaded**, and that shows up more sharply on Wasm than natively, because cross-Worker coordination goes through JS.

**If the data can be partitioned, look back at Chapter 8 Scenario 3**: **multi-instance isolation needs no cross-origin isolation** and is often the better-value parallel path.

---

## 15. Measurement: One Trap That Makes You Measure Wrong

**⚠️ Without cross-origin isolation, `performance.now()`'s resolution is reduced.**

That is another aftershock of Spectre (Chapter 3): **on a non-isolated page, timer resolution is coarsened** (implementations differ; tens to hundreds of microseconds is common), **and only after isolation does it return to microsecond granularity**.

**Which means**:

- Measuring microsecond-scale operations (a single boundary call, a small function) **simply cannot be done accurately on a non-isolated page**.
- **Don't use a single `performance.now()` delta to measure a small operation** — run it ten thousand times, take the total and divide.
- When comparing two builds, **confirm both have the same isolation state**, or you are comparing timer precision rather than code.

```javascript
// The right shape for a microbenchmark
function bench(fn, iters = 100_000) {
  fn(); fn(); fn();                       // warm up (let TurboFan finish tiering up)
  const t0 = performance.now();
  for (let i = 0; i < iters; i++) fn();
  return (performance.now() - t0) / iters; // mean per call
}
```

**The profiling workflow** (covered in Appendix M §10; three additions here):

- **Keep the `name` section**, or the flame graph shows only `wasm-function[1234]` (`wasm-opt --strip-debug` keeps name and strips only DWARF).
- **Use `perf` on the backend**: Wasmtime can emit perf/jitdump mapping information so you see Wasm function names.
- **Measure "boundary crossings" and "allocations,"** not just time — those are the metrics you can act on directly.

---

## 16. Performance Optimization Return Table

| # | Approach | Typical gain | When to do it |
|---|---|---|---|
| 0 | **Determine whether the bottleneck is startup or steady state** | — | **First** (the weapons are completely different) |
| 1 | `instantiateStreaming` + the correct MIME | Saves an entire download's worth of time | Always |
| 2 | **Reduce size** (Part One) | Directly shortens stages ① and ② | Always |
| 3 | A stable URL → the code cache | An order of magnitude faster on return visits | Always |
| 4 | **Make the boundary coarse** | 2–10× is common | **Do it when you measure boundary-heavy behaviour** |
| 5 | Structured-clone the Module to N Workers | Saves N−1 compilations | When using several Workers |
| 6 | SoA + an arena allocator | 2–5× is common | When data-intensive |
| 7 | `memcpy` instead of a byte-by-byte loop | Up to an order of magnitude on large blocks | Always check |
| 8 | SIMD (`-msimd128` + hand-written intrinsics) | 2–4× | When numerically intensive |
| 9 | **Wizer pre-initialization** | 1.35–6× on instantiation + init | Initialization-heavy backends/CLIs |
| 10 | Backend AOT (`wasmtime compile`) | Zero compilation at runtime | Server side |
| 11 | Threads | ≤ the core count | **Last** (highest complexity and isolation cost) |

---

## 17. Antipattern List

| Antipattern | Why it's wrong |
|---|---|
| Tuning flags without measuring | Eighty percent of the time you tune the wrong thing (squeezing Code does nothing when Data is half the file) |
| Wanting `opt-level="z"` and SIMD auto-vectorization together | **`-Oz` turns off vectorization**; they are mutually exclusive |
| Treating Wasm as "a faster library" and replacing JS function by function | Each function gets faster and the whole gets slower — **boundary crossings explode** |
| Calling JS inside a hot loop | Every call is a toll booth; move the whole loop into Wasm |
| Using `wee_alloc` for size | **No longer maintained and has known issues** |
| Measuring microsecond operations on a non-isolated page | **The timer is coarsened**; you are measuring noise |
| Benchmarking immediately after startup | You are measuring Liftoff's unoptimized code |
| Bundling 30 MB of model weights into the `.wasm` | They should be a cacheable asset, not code |
| Over-splitting the module for update size | **Compression Dictionary Transport** (§7-2) may already have solved that, while splitting's costs remain |
| Blindly stripping every symbol in release | When it crashes in production you can investigate nothing — **keep a symbol-bearing build** |

---

## Appendix: Cross-Reference Index to the Main Text

| Topic | This appendix | Background in the main text |
|---|---|---|
| Dissecting size, and the tools | §1 | Chapter 3 Wall 3, Chapter 8 |
| Rust's hidden fat | §2-2, §2-3 | Chapter 3 Wall 9 |
| Inside `wasm-opt` | §3 | Chapter 8 |
| Data is the bulk | §6 | Chapter 8's step 0, Appendix L |
| Brotli and differential updates | §7 | Chapter 2, Appendix M §9 |
| The four startup stages | §10 | Chapter 2 Scenario 3 |
| Wizer | §10-2 | Chapter 2, Appendix M |
| SIMD's real ceiling | §11-1 | Chapter 2 🔍, Chapter 4 |
