# Appendix M: The Deep End of the Specification — Twelve Technical Details Usually Skipped

> For the sake of narrative flow, the main text often stops at "this is how it works." This appendix keeps digging where the main text stopped.
> **It is not introductory material but reference material** — turn to it when you hit a specific problem in implementation.
>
> ⚠️ **Version premise**: this appendix takes **WebAssembly 3.0** (announced complete in September 2025) as its baseline. **Material written before 3.0 will call GC, Memory64, exception handling, tail calls and multiple memories "proposals" — those descriptions are out of date.**

---

## 1. Taking a `.wasm` Apart Byte by Byte

### 1-1 LEB128: why every length is variable-length

Every integer field in Wasm (section lengths, indices, constants) uses **LEB128 (Little Endian Base 128)** encoding — each byte stores 7 bits of data in its low bits and uses the top bit as a "there is more" continuation flag.

```
Unsigned LEB128:
  value 624485 (0x98765)
  → binary 1001 1000 0111 0110 0101
  → in groups of 7 bits (low to high): 1100101  1110110  0100110
  → with continuation bits:           11100101  11110110  00100110
  → bytes                             E5        F6        26

Small numbers take one byte (0–127), and that is exactly the point:
  the overwhelming majority of indices and lengths are small, so variable-length
  encoding shrinks the whole module noticeably.
```

**The signed version (sLEB128)** is used for constants like `i32.const` / `i64.const`, with sign extension on the final group.

> **Practical significance**: this explains two things — **(1)** why a Wasm binary is much smaller than an equivalent fixed-length format, and **(2)** why you **cannot** patch a `.wasm` at a fixed offset: changing one number may change its byte count, and everything after it has to be recomputed. **If you want to modify a binary, use Binaryen or WABT; don't do it by hand.**

### 1-2 The common structure of a section

```
┌────────┬───────────────┬──────────────────────────┐
│ id (1) │ size (u32 LEB)│ contents (size bytes)     │
└────────┴───────────────┴──────────────────────────┘
```

**The value of `size` existing**: a parser can **skip** any section it doesn't recognize (custom sections especially). That is the cornerstone of Wasm's forward compatibility — when an old engine meets custom metadata a newer toolchain stuffed in, it just skips over it.

### 1-3 Type encoding

| Value type | Byte |
|---|---|
| `i32` | `0x7F` |
| `i64` | `0x7E` |
| `f32` | `0x7D` |
| `f64` | `0x7C` |
| `v128` | `0x7B` |
| `funcref` | `0x70` |
| `externref` | `0x6F` |
| Function type (functype) prefix | `0x60` |

**Note these are all negative sLEB128 encodings** (`0x7F` = −1, `0x7E` = −2, …). That is no accident: **positive numbers were reserved for "type indices,"** so when GC came to introduce references to user-defined types like `(ref $MyStruct)`, the encoding space had been reserved all along. **That "deliberately small" specification from 2015 left a door open in its type encoding.**

### 1-4 A complete walkthrough: an `add` function

```wat
(module
  (func $add (param i32 i32) (result i32)
    local.get 0
    local.get 1
    i32.add)
  (export "add" (func $add)))
```

```
00 61 73 6D            magic number \0asm
01 00 00 00            version 1

01 07                  Type section (id=1), length 7
   01                    1 type
   60                    functype
   02 7F 7F              2 parameters: i32, i32
   01 7F                 1 result: i32

03 02                  Function section (id=3), length 2
   01 00                 1 function, using type #0

07 07                  Export section (id=7), length 7
   01                    1 export
   03 61 64 64           name length 3: "add"
   00 00                 kind=func(0x00), index 0

0A 09                  Code section (id=10), length 9
   01                    1 function body
   07                    body length 7
   00                    ★ local declarations: 0 groups
   20 00                 local.get 0
   20 01                 local.get 1
   6A                    i32.add
   0B                    ★ end (every function body ends with 0x0B)
```

> **When Chapter 2 said "five bytes," it meant the instruction sequence `20 00 20 01 6A`.** A complete function body also needs the leading local declaration `00` and the trailing `0B` — **those two bytes are mandated by the specification, and everyone assembling a binary by hand misses the `0x0B` on their first try.**

### 1-5 Common opcodes at a glance

| Instruction | Opcode | Instruction | Opcode |
|---|---|---|---|
| `unreachable` | `0x00` | `end` | `0x0B` |
| `nop` | `0x01` | `br` | `0x0C` |
| `block` | `0x02` | `br_if` | `0x0D` |
| `loop` | `0x03` | `br_table` | `0x0E` |
| `if` | `0x04` | `return` | `0x0F` |
| `else` | `0x05` | `call` | `0x10` |
| `drop` | `0x1A` | `call_indirect` | `0x11` |
| `select` | `0x1B` | `local.get` | `0x20` |
| `i32.load` | `0x28` | `local.set` | `0x21` |
| `i32.store` | `0x36` | `local.tee` | `0x22` |
| `memory.size` | `0x3F` | `global.get` | `0x23` |
| `memory.grow` | `0x40` | `i32.const` | `0x41` |
| `i32.add` | `0x6A` | `i32.sub` | `0x6B` |

**SIMD and some newer instructions use prefix bytes** (`0xFD` is the SIMD prefix, `0xFC` the bulk-memory/saturating-conversion prefix), followed by a LEB128 sub-opcode.

---

## 2. The Validation Algorithm: The Polymorphic Stack, and a Very Clever Trick

Chapter 2 said the validator checks "stack type consistency." **But one situation would stall a naive implementation**:

```wat
(func (result i32)
  unreachable       ;; control flow terminates here
  i32.add)          ;; ← nothing on the stack, so how is this line validated?
```

Code after `unreachable` **will never execute**, yet the validator still has to make a judgement about it (because it must be single-pass, linear, and perform no reachability analysis).

**The specification's solution is the "polymorphic stack"**: on entering the unreachable state, the validator marks the stack as **able to supply any number of values of any type**. So `i32.add` wants two `i32`s and the polymorphic stack supplies them; the next instruction wants three `f64`s and it supplies those too. **That way any instruction sequence in dead code passes validation without the compiler having to prove it unreachable.**

```
The validation state machine (simplified):
  Normal state    ── unreachable / br / return / br_table ──▶ Polymorphic state
  Polymorphic     ── on end or the block's boundary ────────▶ back to the block's declared types
```

> 💡 **This is a direct product of the design goal "keep validation to a single O(n) pass."** If the validator had to perform reachability analysis before checking types, it would no longer be single-pass — and streaming compilation (compile while downloading) would no longer hold. **A rule that looks like a special case is often there to preserve some more fundamental property.**

---

## 3. `call_indirect`, Tables, and What C++ Virtual Functions Look Like in Wasm

### 3-1 How function pointers are implemented

Wasm **has no function pointers** — you cannot store a function's address in linear memory. In their place there are **tables**:

```wat
(module
  (type $binop (func (param i32 i32) (result i32)))
  (table 4 funcref)                         ;; a function table with 4 slots
  (elem (i32.const 0) $add $sub $mul $div)  ;; fill in four functions

  (func $apply (param $op i32) (param $a i32) (param $b i32) (result i32)
    local.get $a
    local.get $b
    local.get $op
    call_indirect (type $binop)))           ;; ★ call by index, checking the signature
```

**In Wasm compiled from C/C++, a "function pointer" is really an `i32` table index.** That explains a common puzzle: **why can a function pointer in Wasm be stored safely in linear memory?** Because it is only an index — even if a buffer overflow changes it to an arbitrary value, the worst outcome is that `call_indirect` finds an entry whose signature doesn't match and **traps**, **rather than jumping to an attacker-controlled address to execute arbitrary code**.

### 3-2 `call_indirect`'s runtime checks

```
When call_indirect (type $sig) executes:
  1. Pop index i from the stack
  2. If i is out of the table's range     → trap "undefined element"
  3. If table[i] is null                  → trap "uninitialized element"
  4. If table[i]'s actual signature ≠ $sig → trap "indirect call type mismatch"
  5. Otherwise → call
```

**Step 4 is a runtime cost paid on every call.** That is exactly what Wasm 3.0's **typed function references** solve — with a typed reference like `(ref $sig)`, **the signature is already fixed at the type system level and needs no runtime comparison**. For C++/OOP languages with dense virtual calls, that is a real performance improvement.

### 3-3 What a C++ virtual function actually looks like

```
class Shape { virtual double area(); };

after compiling to Wasm:
  ┌ Linear memory ──────────────────────┐
  │ The Shape object:                    │
  │   +0  vptr → the vtable's address    │   ← vptr is a linear memory address
  │   +4  members…                       │
  │                                      │
  │ The vtable (also in linear memory):  │
  │   +0  area's 【function table index】(i32) │ ← ★ not a function address, a table index
  └─────────────────────────────────────┘
              ↓
  The function table (funcref): [ …, Shape::area, Circle::area, … ]
```

**So one virtual call is: read the vptr → read the vtable entry (getting an i32 index) → `call_indirect`.**

> **This is also a key foothold when reverse engineering Wasm** (Chapter 9): the `elem` section lists every function that can be called indirectly, and the vtable's layout can be inferred backwards from the usage pattern of `call_indirect`. **The class structure was erased, but the call graph's shape is still there.**

---

## 4. Exception Handling: The Tag Section and `exnref`

**Wasm 3.0 took exception handling into the core specification.** Its mechanism is worth a look, because it differs from the try/catch you know.

### 4-1 Tag: an exception's "type"

An exception is not an object; it is a **tag plus a set of payload values**. Tags are declared in the **Tag section (id = 13)**:

```wat
(module
  ;; declare an exception tag carrying one i32 payload
  (tag $oom (param i32))

  (func $alloc (param $n i32) (result i32)
    ...
    (throw $oom (local.get $n)))         ;; throw, carrying n
)
```

### 4-2 `try_table`: 3.0's new form

Early proposals used a block structure of `try` / `catch` / `delegate`; **Wasm 3.0 adopted `try_table` + `exnref`** — turning "catching" into a **branch** rather than a nested block:

```wat
(func $safe (result i32)
  (block $handler (result i32)
    (try_table (catch $oom $handler)     ;; if $oom is thrown, branch to $handler with the payload
      (call $alloc (i32.const 1000000))
      (br 1))                            ;; no exception → skip the handler
  )
  ;; $handler: $oom's payload (i32) is on the stack
)
```

**`exnref`** is an opaque exception reference type, letting you catch "any exception" and rethrow it (`catch_all_ref` + `throw_ref`) — which is necessary for implementing `finally` and for propagating exceptions across languages.

### 4-3 Why this matters a lot for performance

**Before native exception handling existed**, C++'s `try/catch` compiled to Wasm had only two paths:

| The old solution | The cost |
|---|---|
| `-fno-exceptions` | Half the ecosystem's libraries become unusable |
| **A JavaScript trampoline** | Every `try` entry means crossing into JS and back — **enormous overhead, and it prevents the JS engine from inlining** |

**After native EH**, `try_table` is a pure Wasm instruction the engine can optimize fully. **This is Wasm 3.0's most direct transfusion to the C++ ecosystem.**

---

## 5. JSPI in Depth: How Wasm "Waits" for a Promise

Chapter 3 introduced what JSPI is for; here we look at the mechanism and the cost.

### 5-1 What it actually does

```
The ordinary case:
  JS ──call──▶ Wasm ──call──▶ an imported JS function (returning a Promise)
                                  ↓
                            Wasm gets a Promise object,
                            but has no idea how to "wait" — it can only carry on ❌

JSPI:
  JS ──promising(f)──▶ Wasm ──call──▶ a Suspending-wrapped import
                                          ↓
                       ★ the engine suspends the whole Wasm execution stack
                         (locals and call chain included), moves it aside,
                         and returns a Promise to JS
                                          ↓
                            the event loop keeps running (the tab doesn't freeze)
                                          ↓
                            the Promise settles → the engine restores the stack,
                            pushes the result onto the operand stack, and
                            continues from the suspension point ✅
```

### 5-2 The API shape

```javascript
// 1. Import side: wrap a Promise-returning function as "suspendable"
const imports = {
  env: {
    read_file: new WebAssembly.Suspending(async (ptr, len) => {
      const handle = await root.getFileHandle("data.bin");
      const file = await handle.getFile();
      const buf = new Uint8Array(await file.arrayBuffer());
      new Uint8Array(memory.buffer, ptr, buf.length).set(buf);
      return buf.length;               // to Wasm's eyes this is a synchronous return
    }),
  },
};

// 2. Export side: wrap the entry point as "Promise-returning"
const { instance } = await WebAssembly.instantiateStreaming(fetch("app.wasm"), imports);
const main = WebAssembly.promising(instance.exports.main);
await main();                          // async as far as JS is concerned
```

**The Rust side barely changes**:

```rust
extern "C" { fn read_file(ptr: *mut u8, len: usize) -> usize; }

pub fn load() -> Vec<u8> {
    let mut buf = vec![0u8; 4096];
    let n = unsafe { read_file(buf.as_mut_ptr(), buf.len()) };  // looks like a synchronous call
    buf.truncate(n);
    buf
}
```

### 5-3 Three costs you must know

1. **Suspending and resuming is not free.** Each suspension moves the whole Wasm stack out and back, at a cost proportional to stack depth. **It suits "waiting on I/O occasionally"; putting it in a hot loop hurts.**
2. **It is not parallelism.** While suspended, that Wasm thread is doing nothing — **you merely yielded the waiting time to the event loop; you are not doing two things at once.**
3. **Reentrancy.** While suspended, JS may call the same Wasm instance's exports again. **If your C code assumes only one call is in flight at a time (the overwhelming majority of C code does), state gets corrupted.** You must add a reentrancy lock of your own.

### 5-4 Compared with Asyncify

| | Asyncify | JSPI |
|---|---|---|
| Mechanism | Binaryen **rewrites the whole module**, saving/restoring the stack manually through linear memory | The **engine natively** suspends the Wasm stack |
| Size impact | **Noticeable inflation** | None |
| Runtime overhead | Global (the rewritten code carries save/restore logic everywhere) | Paid only on actual suspension |
| Annotation needed | You must list which functions may unwind; miss one and it breaks | None |
| Compatibility | Works everywhere | Requires engine support (**Chrome 137+ / Firefox 139+**) |

**Migration strategy**: detect `typeof WebAssembly.Suspending === "function"`; use JSPI if present, and fall back to an Asyncify build if not.

---

## 6. Atomic Operations and the Memory Model

### 6-1 The instruction family

```wat
;; atomic loads and stores
i32.atomic.load / i32.atomic.store
i64.atomic.load8_u / …(various widths)

;; read-modify-write (RMW), each a single atomic operation
i32.atomic.rmw.add / sub / and / or / xor / xchg / cmpxchg

;; blocking and waking (futex semantics)
memory.atomic.wait32   (addr, expected, timeout_ns) -> i32
memory.atomic.notify   (addr, count) -> i32

;; memory barrier
atomic.fence
```

### 6-2 Three semantics you must remember

1. **Every atomic operation is sequentially consistent.** Wasm has **no** gradation like C++'s `memory_order_relaxed` / `acquire` / `release` — the specification offers only the strongest kind. **The benefit is that you can't get it wrong; the cost is that you can't reach the performance weaker orderings give.**
2. **Non-atomic accesses carry no ordering guarantee at all.** Non-atomic reads and writes to the same address from two threads are a data race; the specification defines that it won't break the sandbox, but **makes no guarantee about the value**.
3. **`memory.atomic.wait` traps on the main thread.** The main thread may not block — **that is a specification-level prohibition, not a convention.** So any synchronization primitive using `wait` can run only inside a Worker (which is precisely why SQLite's first-generation `opfs` VFS requires one).

### 6-3 One practical corollary

**`memory.atomic.wait32` + `notify` is a futex, and a futex suffices to implement every synchronization primitive** — mutexes, condition variables, semaphores, barriers. That is the foundation on which Emscripten maps `pthread` across in full.

---

## 7. Relaxed SIMD's Nondeterminism List

Wasm 3.0 took in relaxed SIMD, which trades **giving up determinism** for better hardware mapping. **On-chain, and in scientific computation that must reproduce results across machines, these instructions must be disabled.**

| Instruction family | Where the nondeterminism comes from |
|---|---|
| `relaxed_madd` / `relaxed_nmadd` | May use FMA (one rounding) or mul+add (two roundings) — **the floating-point result differs in the last few bits** |
| `relaxed_min` / `relaxed_max` | **NaN and ±0 handling varies by platform** |
| `relaxed_swizzle` | With an out-of-range index it returns 0 or an undefined value, **varying by platform** |
| `relaxed_trunc_*` | Converting float to integer, out-of-range or NaN results **vary by platform** |
| `relaxed_dot` | Accumulation order and saturation behaviour may differ |
| `relaxed_laneselect` | Behaviour undefined when the mask is neither all-0 nor all-1 |

**The test**: **if your output will be hashed, signed, used for consensus or compared across machines, do not use relaxed SIMD.** It suits image filters, game physics and machine learning inference — the cases where "a few ULP off, nobody notices."

---

## 8. Multiple Memories (Wasm 3.0)

```wat
(module
  (memory $a 1)
  (memory $b 1)

  ;; load/store instructions carry a memory index
  (func $get (result i32) (i32.load $b (i32.const 0)))

  ;; memory.copy can cross memories: dst_mem, src_mem
  (func $move (memory.copy $a $b (i32.const 0) (i32.const 0) (i32.const 1024)))

  ;; each grows independently
  (func $grow_b (result i32) (memory.grow $b (i32.const 16))))
```

**Three typical uses**:

| Use | Benefit |
|---|---|
| **Separating a code region from a data region** | Large assets no longer squeeze the working area's address space |
| **One memory per tenant** | One module serves several tenants with naturally isolated memory |
| **Hot/cold separation** | Hot data stays in a small memory, improving cache locality |

**The biggest value** (already covered in Chapter 8 Scenario 4): **each memory is still wasm32, so the free bounds check from guard pages is preserved intact** — something Memory64 cannot do.

**A real limitation**: **toolchain support lags the specification.** Most C/C++/Rust toolchains assume "only one memory" by default.

---

## 9. The Deployment Layer: Five Things That Will Wreck You in Production

### 9-1 The MIME type

```
Content-Type: application/wasm
```

**Without this, `instantiateStreaming` refuses outright.** GitHub Pages serves the `.wasm` extension correctly.

### 9-2 CSP

```http
Content-Security-Policy: script-src 'self' 'wasm-unsafe-eval'
```

In CSP's eyes, Wasm compilation is dynamic code generation. `'wasm-unsafe-eval'` (Chrome 97+ / Firefox 102+ / Safari 16+) **permits Wasm only, not `eval()`**.

### 9-3 Integrity verification (the SRI gap)

**This is a real ecosystem gap**: `<script integrity="sha384-…">` works for `<script>`, **but a `.wasm` loaded through `fetch()` has no built-in SRI mechanism**. To verify, you must do it yourself:

```javascript
async function loadVerified(url, expectedSha256Base64) {
  const bytes = await (await fetch(url)).arrayBuffer();
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const actual = btoa(String.fromCharCode(...new Uint8Array(digest)));
  if (actual !== expectedSha256Base64) throw new Error("wasm integrity mismatch");
  return WebAssembly.instantiate(bytes, imports);   // ⚠️ the cost: you give up streaming compilation
}
```

> **Note the trade-off here**: verifying a hash means having the complete bytes first, **so you lose streaming compilation** (Chapter 2). **Security and start-up speed collide head-on here**, with no solution that gets both. Most teams choose **same-origin hosting + a reproducible build pipeline + the CDN's TLS**, rather than runtime hash verification.

### 9-4 Compression

```
Content-Encoding: br
```

**Wasm's Brotli ratio is usually very good** — Appendix L's real case is 3.6 MB → 0.8 MB (about 4.5×). **This is the highest-return line of server configuration there is.**

> **Why Wasm suits Brotli particularly well, and how to use Compression Dictionary Transport so a new build ships only tens of kilobytes — see Appendix N §7.**

### 9-5 Code caching and Worker sharing

**Two frequently overlooked accelerations**:

```javascript
// (1) Compile once, share across Workers.
//     WebAssembly.Module is structured-cloneable, so postMessaging it doesn't recompile
const mod = await WebAssembly.compileStreaming(fetch("app.wasm"));
for (const w of workers) w.postMessage({ mod });          // ★ saves N-1 compilations

// Inside the Worker:
self.onmessage = async ({data}) => {
  const inst = await WebAssembly.instantiate(data.mod, imports);  // instantiate directly
};
```

```
(2) The browser's on-disk code cache:
    Chrome writes TurboFan's output into the HTTP cache, keyed by URL.
    → give the .wasm a stable URL (a content-hashed filename is best)
    → return visits skip the entire compilation stage; a large module's second
      load is often an order of magnitude faster
```

---

## 10. The Performance Profiling Workflow

**Many people think Wasm can't be profiled. It can — it just takes preparation.**

```bash
# 1. Keep the name custom section (otherwise you'll only see wasm-function[1234])
#    Rust: don't blindly set strip = true in release; use wasm-opt to strip debug only
wasm-opt -O3 --strip-debug --strip-producers app.wasm -o app.wasm
#                ↑ keeps the name section, strips only DWARF

# 2. Emscripten: keep function names explicitly
emcc -O3 --profiling-funcs ...
```

**Then record in Chrome DevTools' Performance panel** — Wasm frames appear in the flame graph by function name, interleaved with JS frames. **That turns "is the time going into boundary crossings or into computation" into a question you can read directly off the screen.**

**The three most common profiling conclusions, and what they look like**:

| What the flame graph looks like | Diagnosis |
|---|---|
| Many thin, interleaved JS↔Wasm bars | **Too many boundary crossings** (Chapter 2) — make the interface coarser |
| Wide Wasm frames but flat inside | It really is computing — consider SIMD or a better algorithm |
| A high share in `__wbindgen_malloc` / `free` | **Too much allocation** — switch to a memory pool or reuse buffers |

**Advanced**: `performance.mark()` / `measure()` can be called from the Wasm side through imports, putting custom regions on the timeline.

---

## 11. proxy-wasm: Wasm's Standard ABI at the Infrastructure Layer

**This is the concrete shape of Chapter 4's "multi-tenant plugin system" passage**, and one of Wasm's most successful landings on the backend.

**proxy-wasm** is a Wasm ABI designed for network proxies, adopted by **Envoy, Istio, Kong, APISIX and Higress** among others. It defines a set of callbacks between host and module:

```
Module exports (host calls module):
  proxy_on_context_create(context_id, parent_id)
  proxy_on_request_headers(context_id, num_headers, end_of_stream)
  proxy_on_request_body(context_id, body_size, end_of_stream)
  proxy_on_response_headers(...)
  proxy_on_log(context_id)
  proxy_on_tick(context_id)

Host exports (module calls host):
  proxy_get_header_map_value(...)
  proxy_set_header_map_pairs(...)
  proxy_send_local_response(...)   ← respond directly without forwarding upstream
  proxy_get_shared_data / proxy_set_shared_data
  proxy_http_call(...)             ← make an outbound HTTP call (to an auth service, say)
```

**Why this is Wasm's sweet spot** (back to Chapter 4's judgement):

- **Multi-tenancy**: one Envoy process can run hundreds of mutually untrusted customer plugins, each with its own linear memory and capability boundary. **Doing that with containers is impossible.**
- **Hot updates**: swap a `.wasm` and you swap the logic, without restarting the proxy.
- **Language-agnostic**: customers can use Rust, Go or AssemblyScript.

> **This is the evidence for Chapter 4's line**: **Wasm will not take market share from existing services; it will grow its own territory in the places containers structurally cannot reach.**

---

## 12. Code Splitting and Lazy Loading

**When a module gets large enough that it must be cut apart**, there are two routes:

### 12-1 `wasm-split` (Emscripten / Binaryen)

Split one module into **a primary and a secondary module**, loading the primary first and fetching the secondary on the first call into it.

```bash
# Profile first to get the list of "functions actually used at startup"
wasm-split app.wasm -o1 primary.wasm -o2 secondary.wasm \
  --profile=startup.prof --keep-funcs=@startup-funcs.txt
```

**Suits**: applications with a clear startup path where most functionality is "the user may never click it."

### 12-2 Splitting manually into several independent modules

```javascript
// Load only the core for the first screen
const core = await WebAssembly.instantiateStreaming(fetch("core.wasm"), imports);

// Load this only when the user clicks "Export PDF"
button.onclick = async () => {
  const pdf = await WebAssembly.instantiateStreaming(fetch("pdf.wasm"), {
    env: { memory: core.instance.exports.memory },   // ★ share the same linear memory
  });
  pdf.instance.exports.export_pdf(ptr, len);
};
```

**The key detail**: the two modules **share the same linear memory** (export memory from one side and import it on the other) so no data needs copying. **Tesseract's language packs and Pyodide's `micropip` have this exact shape.**

---

## Appendix: Cross-Reference Index to the Main Text

| What you want to know | Look here | Background in the main text |
|---|---|---|
| What the binary actually looks like | §1 of this appendix | Chapter 2 Scenario 1 |
| Why validation can complete in one pass | §2 | Chapter 2 Scenario 1 |
| Function pointers and virtual functions | §3 | Chapters 2, 9 (reverse engineering) |
| The cost of C++ exceptions | §4 | Chapters 1 (technical debt), 3 |
| How synchronous code awaits an async API | §5 | Chapter 3 Wall 7, Chapter 7, Appendix L |
| The low-level primitives of threading | §6 | Chapter 3 Wall 6, Chapter 5 |
| Which SIMD instructions can't be used on-chain | §7 | Chapter 4 (EVM determinism) |
| The third way out of 4 GiB | §8 | Chapter 8 Scenario 4 |
| The production deployment checklist | §9 | Chapter 5, Appendix C |
| How to profile Wasm | §10 | Chapter 3 Wall 8 |
| Where Wasm genuinely wins on the backend | §11 | Chapter 4 Scenario 2 |
| What to do when the module is too large | §12 | Chapter 8 |
