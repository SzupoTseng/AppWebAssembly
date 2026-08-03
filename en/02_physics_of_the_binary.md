# Chapter 2: The Physics of the Binary — Every Byte After the Magic Number

> Open any `.wasm` file and it always begins with these eight bytes: `00 61 73 6D 01 00 00 00`. The first four are the magic number `\0asm`; the last four are version `1`. **Everything after those eight bytes exists so that a machine which does not trust you can prove, before it finishes reading, that you will not misbehave.**

## Scenario 1: It isn't machine code, it's a contract that can be proven

**Background.** Most people's first impression of Wasm is "compiled machine code." That impression is wrong, and wrong in an important way. **Wasm is not the instruction set of any physical CPU** — not x86, not ARM, not RISC-V. It is **an abstract stack machine defined in a specification**, and every property of that machine exists in service of verifiability.

**The physical structure of a module.** A `.wasm` file is a linear sequence of **sections**, each beginning with a one-byte ID, followed by an LEB128-encoded length, then the content. The order is mandated by the specification:

| ID | Section | Contents |
|---|---|---|
| 1 | Type | All function signatures (things like `(i32, i32) -> i32`) |
| 2 | Import | What comes in from the host: functions, memories, tables, globals |
| 3 | Function | Which Type-section signature each function uses |
| 4 | Table | Function reference table (indirect call targets) |
| 5 | Memory | Initial page count and maximum for linear memory |
| 6 | Global | Global variables |
| 7 | Export | Functions/memories/tables/globals exposed outward |
| 8 | Start | Function run automatically after instantiation |
| 9 | Element | Initial contents of tables |
| 10 | Code | The actual instructions and locals of each function |
| 11 | Data | Initial data for linear memory |
| 12 | DataCount | Number of data segments (introduced by bulk memory, for single-pass validation) |
| 13 | Tag | Exception tags (Wasm 3.0 exception handling) |
| 0 | Custom | Any custom data (`name` debug symbols, source-map links, language metadata) |

**That order is not aesthetics, it is engineering.** Types precede function declarations; function declarations precede function bodies. This guarantees the validator **only needs one pass from beginning to end** — by the time it reads any instruction, every type it needs has already appeared. That is why Wasm validation is **O(n) single-pass linear time**, and why it can be **compiled while downloading**.

**How instructions work.** Wasm is a stack machine. `local.get 0` pushes local variable 0 onto the stack; `i32.add` pops two values and pushes one. A function adding two numbers looks like this in the text format (WAT):

```wat
(module
  (func $add (param $a i32) (param $b i32) (result i32)
    local.get $a        ;; stack: [a]
    local.get $b        ;; stack: [a, b]
    i32.add)            ;; stack: [a+b]
  (export "add" (func $add)))
```

The corresponding instruction sequence is `20 00 20 01 6A` — five bytes. `0x20` is `local.get`, `0x6A` is `i32.add`. **No register allocation, no addressing modes, no instruction prefixes**, which makes it extremely compact and extremely easy to translate mechanically into any real CPU's instructions.

> **To be precise**: those five bytes are the **instructions**. The complete "function body" in the Code section also needs a local-variable declaration in front (here `00`, meaning zero groups of locals) and `0x0B` (`end`) at the close — **both mandated by the specification.** A complete byte-by-byte teardown of an entire module (LEB128 encoding, the type encoding table, a common opcode reference) is in **Appendix M §1**.

**What the validator actually checks at load time.** This is the core of Wasm's security model, and it checks more than most people assume:

1. **Stack type consistency.** Before and after every instruction, the type sequence on the operand stack must be statically derivable. Before `i32.add`, the top of the stack **must** be two `i32`s — not `f64`, and not empty.
2. **Structured control flow.** Wasm has **no arbitrary jumps (goto)**. Control flow consists only of `block` / `loop` / `if`, plus `br` / `br_if` / `br_table`, which **can only branch to the label of a block that encloses them**. This guarantees the control-flow graph is reducible by construction, so compilers never need expensive irreducible-loop analysis.
3. **Stack height must agree at every branch.** All paths jumping to the same label must present the same types on the stack.
4. **Local indices in range**, **function indices in range**, **indirect-call signatures checked at runtime** (the four checks in `call_indirect` and how C++ virtual functions are implemented are in Appendix M §3).
5. **All memory and table accesses are bounds-checked** (next section).

**One clever trick deserves its own mention.** How do you validate dead code after `unreachable`? The specification uses a **polymorphic stack** — once in the unreachable state, the validator treats the stack as able to supply any number of values of any type, so any dead code passes validation **without the validator ever doing reachability analysis.** **A rule that looks like a special case exists precisely to preserve the more fundamental property of single-pass O(n)** (detail in Appendix M §2).

**A module that passes validation has an extremely strong property.** It **cannot** read or write a single byte outside linear memory, cannot jump to an arbitrary address, cannot forge a function pointer, cannot corrupt the call stack (return addresses live on the engine's own stack, which Wasm code cannot touch). **Buffer-overflow attacks cannot break out of the Wasm sandbox** — at worst they can corrupt data inside that module's own linear memory.

> ⚠️ Authenticity Caveat (a widely circulated misconception)
> "Wasm is memory safe" **holds only in the sandbox-boundary sense.** It guarantees "the Wasm module cannot harm the host"; it does **not** guarantee your C program has no memory errors inside it. The situation is in fact subtler: because linear memory is one flat `ArrayBuffer`, **the mitigations native platforms provide — stack canaries, ASLR, non-executable pages — largely do not exist inside Wasm.** A buffer overflow that ASLR would have blocked on x86 may be reliably exploitable in Wasm — it is simply confined to that module's linear memory. Academia has discussed this explicitly (see "Everything Old is New Again: Binary Security of WebAssembly," USENIX Security 2020). **Sandbox safety ≠ application safety.**

> 💡 A Word to the Wise
> **The cheapest way to implement security is not to add guards, it is to remove capabilities.** Wasm has no `goto`, no registers, no raw pointers, no executable stack, no system calls — it did not *defend* those attack surfaces; **those attack surfaces do not exist at the specification level.** Guards cost money (runtime checks, CPU cycles, complexity, and every guard's own potential bugs); non-existence is free and cannot have bugs. This principle has a more common name in system design: **make illegal states unrepresentable.** Whenever you find yourself writing "check whether the user did X" in a security design, step back and ask: **could X be made impossible to express in the type system, the protocol, the data structure?** What you can remove is always more reliable than what you can guard.

> 🔍 Deeper Commentary — the cost of structured control flow, and the compilation problem nobody mentions
> "No goto" sounds like a security decision, but for compiler authors it is a catastrophe — and the way out of that catastrophe is interesting. **The problem is that real-world code has goto.** C has `goto`, LLVM IR's control-flow graph is an arbitrary directed graph, and Wasm accepts only a tree of nested blocks. Recovering structured control flow from an arbitrary CFG is an old problem in compiler theory (the Relooper algorithm), which Emscripten relied on early; Binaryen later added the stronger **Stackify** algorithm. The cost? **For certain irreducible loops you must introduce an extra state variable and a large `br_table` to *simulate* the control flow** — producing a slower instruction sequence than the original. That is why some projects heavy in hand-written assembly (video decoders, say) lose more performance in a Wasm port than expected: **it isn't that Wasm instructions are slow; it's that its control flow isn't expressive enough, forcing the compiler to take a detour.** Later **funclets / multi-loop proposals** discussed relaxing this, but the core specification still holds the line on structured control flow — because that is the precondition for a validator that finishes in single-pass linear time. **This is a textbook trade-off: to make validation on every device cheap enough to ignore, the specification is willing to sacrifice performance in a small set of extreme cases.** When you evaluate any "safe execution environment," go looking for where this trade-off sits — it always exists, and it will always bite you somewhere.

## Scenario 2: Linear memory — that flat wasteland that only grows

**Background.** Wasm's memory model is almost primitive: **one contiguous, addressable array of bytes**, called linear memory. It grows in **64 KiB pages** via `memory.grow`, and you query the current page count with `memory.size`.

**On the JavaScript side, it is simply an `ArrayBuffer`**:

```javascript
const { instance } = await WebAssembly.instantiateStreaming(fetch("app.wasm"), imports);
const mem = instance.exports.memory;                 // WebAssembly.Memory
const bytes = new Uint8Array(mem.buffer);            // the whole of Wasm's memory, directly
const ints  = new Int32Array(mem.buffer);            // another view of the same bytes
```

**This is the root of every Wasm performance technique**: JS and Wasm **do not need to copy data**, because they are looking at the same bytes. "Zero-copy" means opening a `TypedArray` view over that buffer rather than moving data around.

**Its four physical properties, each of which bites in a later chapter:**

1. **It can only grow, never shrink.** There is `memory.grow`; there is no `memory.shrink`. A Wasm application that once reached 3 GB still has **that 3 GB `ArrayBuffer` charged to it by the operating system**, even after freeing every internal structure, until the whole instance is discarded. This is why long-running Wasm applications are either designed as "use it, then throw the entire instance away" or build their own internal memory pool.
2. **Growth can detach the `ArrayBuffer`.** Under the older behaviour (without growable `ArrayBuffer`), after `memory.grow` **every existing `TypedArray` view becomes invalid** (the buffer is detached). This is the classic beginner trap:

```javascript
let view = new Uint8Array(mem.buffer);
instance.exports.allocate_lots();   // internally triggers memory.grow
view[0] = 42;                       // ❌ TypeError / writing into a detached buffer
// Correct: re-acquire the view after any call that might grow memory
view = new Uint8Array(mem.buffer);
```

3. **The address *is* the index, and `0` is a legal address.** Wasm has no concept of a null pointer — address 0 is the first byte of linear memory, fully readable and writable. So C's "dereferencing NULL segfaults" protection **does not exist by default** in Wasm (Emscripten can reserve low addresses as a trap region with options like `--low-memory-unused`, but that is a toolchain patch, not a specification guarantee).
4. **Out-of-bounds access always traps.** This is a hard specification guarantee. An `i32.load` past the current memory size produces an **uncatchable trap**, surfacing on the JS side as a thrown `WebAssembly.RuntimeError`.

**How bounds checking avoids being slow.** The naive implementation inserts a compare and a branch before every `load`/`store`, which would be an unacceptable overhead. Modern engines on 64-bit hosts use an elegant trick — the **guard page**:

> The engine reserves **8 GiB** of virtual address space for each 32-bit linear memory (4 GiB of addressable space plus guard regions on either side), but only **commits** the pages actually in use as readable/writable. Address arithmetic uses a 32-bit offset, so it is **mathematically impossible to exceed that 4 GiB reservation**; the moment an access reaches uncommitted territory, the OS paging system raises SIGSEGV, the engine's signal handler catches it and translates it into a Wasm trap.
> **Result: zero bounds-check instructions on the hot path, with the cost carried for free by the MMU.**

That also explains something: why Wasm is noticeably slower on 32-bit hosts or certain embedded runtimes — **there isn't enough virtual address space to make the reservation, so they fall back to explicit comparison every time.**

> 💡 A Word to the Wise
> **The cleverest performance optimizations usually don't look like optimizations; they look like handing the work to something that was already free.** The guard-page trick doesn't "speed up" any computation. It moves "check whether this address is out of bounds" from software onto the MMU — **hardware that was already going to run on every single memory access anyway.** In other words, it makes the marginal cost of bounds checking zero, because somebody else is already paying it. This line of thinking is everywhere in systems engineering: mmap makes file reads ride along with paging, copy-on-write makes fork ride along with the MMU, DMA makes I/O ride along with the bus. **When you are agonizing over the cost of something, the most valuable question is not "how do I make it faster" but "could this be a by-product of some mechanism that is already running?"**

> 🔍 Deeper Commentary — the three-stage evolution of 4 GB, and what actually blocks the road
> Linear memory's 4 GiB ceiling comes from `i32` addressing (2³² bytes). In practice that number has three layers of ceiling, and **they occlude one another**, which is why people often can't tell which one they hit. **Layer one, the specification: wasm32 is welded to 4 GiB.** That's mathematics; there is no way around it. **Layer two, the engine: browsers usually can't reach 4 GiB.** V8 imposes its own limit on a single Wasm memory (historically varying between 2 and 4 GiB, platform dependent), and in practice many scenarios OOM at 2–3 GiB. **Layer three, paging: an `ArrayBuffer` needs contiguous virtual address space.** On 32-bit browsers or long-lived tabs with fragmented address space, `memory.grow` can fail simply because no sufficiently large contiguous region exists, even when the theoretical budget remains. **The way through is Memory64 (`i64` addressing, now in the core specification as of Wasm 3.0)**, raising the theoretical limit to 2⁶⁴ — but here is the cost nobody mentions: **once addresses become 64-bit, the "reserve 8 GiB of virtual space plus guard pages" scheme no longer works**, because you cannot reserve 2⁶⁴ of virtual address space per memory. Consequently memory64 in most implementations **must fall back to explicit bounds checks**, with a measurable performance regression (from a few percent to double digits depending on the benchmark). So the correct mental model is not "memory64 solves it" but — **below 4 GiB you are enjoying safety subsidized by hardware; past that line, safety starts charging you.** The architectural implication is direct: **if chunked streaming or multiple memories (Chapter 8) can solve it under 4 GiB, don't rush to Memory64.**

## Scenario 3: From binary to machine code — tiered compilation and the warm-up curve you can't see

**Background.** After the user hits Enter, what happens to that 20 MB `.wasm`? The answer is not "parse it and start running" but **a two-track pipeline racing against itself.**

**Modern engine tiering (V8 as the example):**

| Tier | Compiler | Character | Purpose |
|---|---|---|---|
| Tier 1 | **Liftoff** | Single pass, no optimization, near instruction-by-instruction translation | **Produces executable code extremely fast** (hundreds of MB/s of compilation throughput) so the program can start immediately |
| Tier 2 | **TurboFan** | Full SSA IR, inlining, loop optimization, register allocation | Produces high-quality machine code **on a background thread**, hot-swapped in when ready |

SpiderMonkey has the corresponding **BaseLine → Ion**; JavaScriptCore has **BBQ → OMG**. **Three engines independently chose the same shape, because the problem is the same**: users want "start now," long-run performance wants "compile well," and those cannot both be satisfied — unless you do it twice.

**Streaming compilation.** This is Wasm's most underrated advantage over JS.

```javascript
// ✅ Correct: compile while downloading; Liftoff starts when the first byte arrives
const { instance } = await WebAssembly.instantiateStreaming(
  fetch("app.wasm"), importObject);

// ❌ Common mistake: download the whole thing into an ArrayBuffer first, then compile
//    (you waste an entire download's worth of time)
const buf = await (await fetch("app.wasm")).arrayBuffer();
const { instance } = await WebAssembly.instantiate(buf, importObject);
```

`instantiateStreaming` requires the server to return `Content-Type: application/wasm` or it refuses. **GitHub Pages returns that MIME correctly for the `.wasm` extension**, which is one reason it is unexpectedly suitable for hosting Wasm.

**Code caching.** Chrome writes TurboFan's compiled output into the disk cache, so a second visit to the same URL can load compiled code and skip the whole compilation phase. This makes **the second load of a large Wasm application often an order of magnitude faster** — and it is why those "Pyodide downloads 30 MB" complaints feel completely different for returning users.

**A full breakdown of cold-start cost** (this is the bill you should actually be calculating when deciding whether Wasm is worth it):

```
total cold start =
    network transfer  (dominated by compressed size and RTT)
  + Liftoff compile   (≈ linear in byte count, usually far below network time)
  + instantiation     (allocate linear memory, run Data-segment init, execute start)
  + runtime init      (C++ global constructors, Rust lazy statics, language-runtime bootstrap)
  ─────────────────────────────────────────────
  ⚠️ The last item is the most underestimated: Pyodide's CPython bootstrap
     and Emscripten's filesystem mount both happen *after* compilation finishes.
```

**That also fixes the optimization order**: cut size first (`wasm-opt -Oz`, `--strip-debug`, split modules on demand), then cut runtime initialization (lazy init, snapshots), and only then reach for instruction-level work. **Spending your effort on instructions while ignoring a 30 MB download is the most common misallocation there is.**

**On that fourth stage, one weapon is worth knowing by name**: **Wizer** (Bytecode Alliance) can run initialization **at build time** and snapshot the post-initialization memory state back into a new `.wasm` — so the module you ship already contains the initialized image in its Data section. Official benchmarking claims **instantiation and initialization 1.35× to 6.00× faster**. **The cost is a larger Data section — trading size for startup** — which is a direct consequence of this section's point that the four costs are independent.

> **Size and speed are a whole interlocking discipline and deserve their own treatment.** From how to dissect where your bytes went, through what each `wasm-opt` pass actually does, Rust's formatting machinery hiding inside `panic!`, how Compression Dictionary Transport makes a new release ship as a few tens of KB, Wizer and backend AOT, the three realities of SIMD auto-vectorization, and a timer-precision trap that makes most measurements wrong — **all of it is in Appendix N.**

> ⚠️ Authenticity Caveat
> This is the claim the book has to puncture early, because it appears a hundred and one times in the appendices. **"Wasm has 60–80% of native performance" is a nearly information-free sentence**, because it depends entirely on the shape of the workload. Broken down: **(a) dense integer and floating-point loops whose data fits in L1/L2 with simple control flow** — Wasm approaches 90%+ of native, because TurboFan's output is not far from Clang -O2. **(b) workloads that need hand-written SIMD or platform-specific assembly** — Wasm SIMD is a fixed 128 bits (`v128`), while modern x86 has AVX2 (256) and AVX-512, and ARM has SVE. A video decoder hand-optimized for AVX2, ported to Wasm, **routinely lands at 40–50% of native**, because its vector width is halved outright, and relaxed SIMD (which loosens some semantics for better hardware mapping) cannot make up the width difference. **(c) large numbers of fine-grained calls crossing the JS/Wasm boundary** — every crossing has fixed overhead, and if your function body is a handful of instructions, that overhead dominates; here Wasm can be **slower than plain JS**. **(d) heavy string and object manipulation** — Wasm has no string type, so every round trip is encode, copy, decode; plain JS crushes it here. **(e) poor memory access patterns where cache misses dominate** — the bottleneck is the memory bus, and the gap between Wasm and native converges to nearly zero (both are waiting on DRAM). So the accurate statement is not "Wasm has N% of native performance" but — **Wasm eliminates JavaScript's dynamic type checks, GC pauses and object allocation overhead; the remaining gap depends on how much your workload relies on things that are not in the Wasm specification.** When reading any Wasm performance claim, the first question is always: **does the shape of that benchmark look like the thing I need to run?**

## Scenario 4: Crossing the boundary — `wasm-bindgen`, glue code, and the real toll booth

**Background.** Wasm knows only four numeric types (`i32`, `i64`, `f32`, `f64`, plus SIMD's `v128` and reference types). **It does not know strings, arrays, objects, or `null`.** So how does `greet("GitHub Pages")` work in the JS that `wasm-pack` emits?

**The answer: that is not one call, it is a whole protocol.** Taking Rust + `wasm-bindgen`, the complete flow of passing a string:

```rust
#[wasm_bindgen]
pub fn greet(name: &str) -> String {
    format!("Hello, {}!", name)
}
```

What actually happens underneath:

```
JS side                                   Wasm side
─────────────────────────────────────────────────────────
1. TextEncoder encodes "GitHub Pages"
   into UTF-8 bytes
2. call wasm.__wbindgen_malloc(len)  →   allocate in linear memory, return ptr
3. write the bytes into memory.buffer
   at ptr (one memory copy)
4. call wasm.greet(ptr, len)         →   Rust builds a &str from ptr/len
                                          (this step is zero-copy — it points
                                           straight into linear memory)
                                          runs format!, writes the result into
                                          a newly allocated block
                                     ←    returns (ptr2, len2) via the return area
5. read bytes from memory.buffer at ptr2
6. TextDecoder decodes into a JS string (another copy)
7. call wasm.__wbindgen_free(ptr2)   →   free
```

**One "just pass a string" costs two encode/decode passes, at least two memory copies, and three boundary crossings.** This is why the single most important piece of Wasm performance advice is: **make the interface coarse, not fine.**

**Concrete techniques:**

- **Batch.** Rather than calling `process_pixel()` a million times, call `process_image(ptr, width, height)` once.
- **Views, not copies.** On the Rust side, `js_sys::Uint8Array::view(&data)` maps a slice directly into a JS view (note this is `unsafe`, because the view is invalidated the moment `memory.grow` happens on the Wasm side).
- **Shared buffers.** Let JS allocate one large buffer, agree on offsets, and stop crossing the boundary during processing entirely.
- **Avoid per-frame callbacks.** Physics engines and game loops must never call back once per object; use a "Wasm writes into a result buffer, JS reads once per frame" ring-buffer pattern.

**The division of labour between the two main toolchains:**

| | Emscripten | `wasm-bindgen` / `wasm-pack` |
|---|---|---|
| Language | C / C++ (and other LLVM frontends) | Rust |
| Output | `.wasm` plus a large bundle of JS glue (libc, filesystem, SDL/OpenGL translation layer) | `.wasm` plus lean JS bindings (only the type conversions you use) |
| Philosophy | **Emulate an entire POSIX environment** so existing C programs compile almost unchanged | **Only bridge types**; leave everything else to Web APIs |
| Suited to | Porting large existing C/C++ projects (FFmpeg, SQLite, OpenCV) | New projects written from scratch; size-sensitive libraries |
| Typical size burden | Larger (runtime and shims included) | Smaller (a few KB to tens of KB of glue) |

**What Emscripten's glue is actually doing.** Far more than type conversion. It implements a whole **MEMFS** (an in-memory virtual filesystem, so calls like `fopen("video.mp4","rb")` have somewhere to go), translates SDL2 drawing calls into WebGL, maps `pthread` onto Web Workers plus `SharedArrayBuffer`, and wires `printf` to `console.log`. **That is why hundreds-of-thousands-of-lines C++ games and players like OpenTTD and VLC can move onto the web "almost without touching the core logic"** — not because Wasm is magic, but because Emscripten has laid an entire fake operating system underneath.

> 💡 A Word to the Wise
> **Between any two heterogeneous systems, the cost is never in the transport; it is in the translation.** Passing an `i32` between JS and Wasm is nearly free; passing a string costs two encode/decode passes and two copies — the difference is not data volume, it is that **the two sides disagree about what a value is.** This rule reaches far beyond Wasm: the object-relational impedance mismatch in ORMs, JSON serialization between microservices, the GIL boundary between Python and C extensions, data upload between CPU and GPU — **all the same disease, and all with the same cure: coarsen the interface, reduce the round trips, keep the data on one side longer.** When you find yourself optimizing an interface's transport speed, first make sure you aren't optimizing something that shouldn't be happening that often at all.

## Chapter Summary

- Wasm is **not machine code; it is the instruction encoding of an abstract stack machine.** Section order, structured control flow, stack type consistency — every design exists so validation completes in **O(n) single-pass linear time**, which is the precondition for compiling while downloading.
- A module that passes validation **cannot** read or write out of bounds, jump arbitrarily, or corrupt the call stack. But **sandbox safety ≠ application safety**: inside linear memory there is no ASLR/NX/stack canary, so C memory bugs may in fact be *more* reliably exploitable in Wasm (see the ⚠️ in Scenario 1).
- The validator uses a **polymorphic stack** for dead code after `unreachable` — a rule that looks like a special case but exists to preserve the more fundamental property of single-pass O(n) (Appendix M §2).
- **Linear memory only grows, never shrinks**, `memory.grow` invalidates existing `TypedArray` views, address 0 is legal and writable, and out-of-bounds always traps. Bounds checking costs zero instructions on the hot path via **an 8 GiB virtual reservation plus guard pages** — paid for free by the MMU.
- **Tiered compilation (Liftoff → TurboFan)** means "start now" and "run fast" need not compete on the same timeline; `instantiateStreaming` plus the correct `application/wasm` MIME is free startup optimization, and code caching drops the return-visit cost by an order of magnitude.
- **Startup is four independent costs** (transfer / compile / instantiate / runtime init), and **the fourth is the most underestimated.** There is a dedicated weapon for it — **Wizer** snapshots post-initialization memory back into the module at build time (Appendix N §10-2).
- "Wasm has 60–80% of native performance" is **almost information-free** — SIMD width, boundary frequency, string weight and cache behaviour each move that number by more than a factor of two (see the ⚠️ in Scenario 3).
- **The boundary is a toll booth**: one string round trip = two encode/decode passes + two copies + three boundary crossings. **Coarsen the interface, reduce the round trips** — the highest-return optimization in all of Wasm.

The physical laws are catalogued. The next chapter translates them into plain language — **what Wasm does beautifully, what it cannot do, and what it can do but you shouldn't let it.** Turn to Chapter 3.
