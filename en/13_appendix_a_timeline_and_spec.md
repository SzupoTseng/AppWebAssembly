# Appendix A: Wasm Timeline and Specification Quick Reference

> This appendix is built to be looked up and checked. **For the timeline and specification status, treat the official WebAssembly specification (webassembly.github.io/spec), the proposals list (github.com/WebAssembly/proposals) and MDN as the final authority** — this book was written in 2026, and proposal status moves.

---

## 1. Timeline

| Date | Event | Significance |
|---|---|---|
| 2011–2013 | **Google NaCl / PNaCl** | Statically validated x86 machine code plus a segmented sandbox; later shifted to shipping LLVM bitcode. A technical success and a political failure (Chrome only) |
| 2013 | **Mozilla asm.js** | A strict subset of JavaScript, annotating types with `x\|0` / `+x`. **Proved that near-native performance was reachable without a plugin, and that all four engines could implement it** |
| from 2013 | **Emscripten matures** | An LLVM → asm.js (later → Wasm) compilation pipeline for C/C++, which is how large projects like Unreal Engine reached the browser |
| **2015-06** | **Four-party announcement of WebAssembly** | Google, Mozilla, Microsoft, Apple. The key to the agreement was **deliberately making it small** |
| from 2017-03 | **Wasm MVP built into all four major browsers** | Chrome, Firefox, Safari, Edge. The MVP became a shared capability |
| from 2019 | **The WASI proposal appears** | Wasm leaves the browser and moves into servers, cloud-native and edge computing |
| 2019 | Docker founder Solomon Hykes's tweet | "If WASM+WASI existed in 2008, we wouldn't have needed to create Docker" (routinely quoted out of context — see Chapter 1 ⚠️) |
| **2019-12** | **W3C Recommendation** | WebAssembly Core Specification 1.0. Alongside HTML, CSS and JavaScript as the Web's fourth core language |
| around 2020 | Bytecode Alliance founded; Wasmtime / Lucet / WAMR runtimes take shape | The infrastructure of the server-side ecosystem |
| 2020–2021 | SIMD, bulk memory, reference types, multi-value and others land one by one | The technical debt the MVP took on begins to be repaid |
| from 2021 | WasmEdge enters the CNCF sandbox; frameworks like Fermyon Spin appear | Cloud-native formally accepts Wasm |
| around 2022 | **Wasm 2.0** (SIMD, bulk memory, reference types, multi-value, …) | The core specification's second milestone |
| 2023–2024 | **Component Model / WIT take shape; WASI 0.2 (Preview 2) released** | From "monolithic module" toward "composable components" |
| 2025-04 | **JSPI (JavaScript Promise Integration) reaches Phase 4** | Synchronous Wasm code can finally call asynchronous Web APIs |
| **2025-09** | **★ WebAssembly 3.0 announced complete; it is the current standard** | **That technical debt from the MVP is now essentially paid off** (see the table below) |
| from 2025 | JSPI ships in **Chrome 137, Firefox 139** | See Appendix M §5 |
| ongoing | Component Model, stack switching, JS String Builtins, custom page sizes, shared-everything threads… | See the proposal reference below |

> ⚠️ **A note on this book's revisions**: Wasm 3.0 is a watershed. **Before it, GC / memory64 / tail calls / exception handling / multiple memories were all "proposals"; after it, they are part of the core specification.** If you encounter any material calling those things "proposals" or "experimental" (**including this book's first draft**), take this table as the authority — those descriptions were written before 3.0.

---

## 2. Binary Format Quick Reference

**The file always begins with eight bytes**: `00 61 73 6D` (the `\0asm` magic number) plus `01 00 00 00` (version 1).

**Section order is mandated by the specification**, and that is exactly what makes single-pass linear validation and streaming compilation possible:

| ID | Name | Contents | Strippable? |
|---|---|---|---|
| 0 | Custom | `name` (function/variable names), DWARF debug info, source map links, language metadata | **✅ Yes (`strip`)** |
| 13 | Tag | Exception tags (Wasm 3.0 exception handling) | ❌ |
| 1 | Type | All function signatures | ❌ |
| 2 | Import | Functions/memories/tables/globals requested from the host | ❌ |
| 3 | Function | Mapping from functions to signatures | ❌ |
| 4 | Table | Function reference table (indirect call targets) | ❌ |
| 5 | Memory | Initial page count and limit for linear memory | ❌ |
| 6 | Global | Global variables | ❌ |
| 7 | Export | **Everything exposed outward (an attacker always sees this)** | ❌ |
| 8 | Start | The function run automatically after instantiation | ❌ |
| 9 | Element | Initial table contents | ❌ |
| 10 | Code | Each function's instructions and locals | ❌ |
| 11 | Data | **Linear memory's initial data (plaintext strings live here)** | ❌ |
| 12 | DataCount | Number of data segments (introduced by the bulk memory proposal) | ❌ |

**Core types**:

| Category | Types |
|---|---|
| Numeric | `i32`, `i64`, `f32`, `f64` |
| Vector (SIMD proposal) | `v128` |
| Reference (reference types proposal) | `funcref`, `externref` |
| Heap types (GC, Wasm 3.0) | `struct`, `array`, `i31`, and typed references `(ref $T)` |

**Memory unit**: **1 page = 64 KiB**. `memory.grow` only grows; there is no `shrink`.

---

## 3. Specification Status Quick Reference (ordered by impact on engineering decisions)

### 3-1 Already in the core specification (Wasm 1.0 / 2.0 / **3.0**)

> **These are no longer "proposals" — they are Wasm.** The only remaining question is whether your target runtime has caught up.

| Feature | Version landed | What it solves | What it means for you |
|---|---|---|---|
| **Bulk memory** | 2.0 | `memory.copy` / `memory.fill` and other batch operations | Large speedup for `memcpy`-class operations |
| **Reference types** | 2.0 | `externref` holds an opaque host reference | Shrinks the cost of the JS↔Wasm bridge |
| **Multi-value** | 2.0 | Functions can return multiple values | Removes boilerplate that allocated memory just to return |
| **SIMD (`v128`)** | 2.0 / confirmed in 3.0 | One instruction over multiple data items | 2–4× speedup. **Note it is only 128 bits wide, far narrower than AVX2/AVX-512** |
| **Threads / Atomics** | — | Shared linear memory plus atomic operations | **Depends on `SharedArrayBuffer` and therefore cross-origin isolation** (Chapter 5's leading obstacle) |
| **★ GC** | **3.0** | `struct`/`array`/`i31` plus the host GC | **A structural size reduction for Kotlin/Dart/Java. Almost useless for Rust/C/C++** |
| **★ Memory64** | **3.0** | `i64` addressing (memories and tables) | Breaks the 4 GiB limit, **but loses the free bounds check from guard pages, at a performance cost** (Chapter 8) |
| **★ Multiple memories** | **3.0** | One module may declare several linear memories and move data directly between them | **Chapter 8's third escape route**: split data across several 4 GiB memories while staying on wasm32 |
| **★ Exception handling** | **3.0** | Exception tags (Tag section) and payloads | C++ exceptions no longer need a JS trampoline; boundary overhead drops sharply (Appendix M §4) |
| **★ Tail call (`return_call`)** | **3.0** | Tail-call optimization | **Deep recursion in functional languages stops blowing the stack** (the key to case 92 in Appendix F) |
| **★ Typed function references** | **3.0** | `(ref $sig)`, typed function references | Indirect calls can skip the runtime signature check (Appendix M §3) |
| **★ Extended const expressions** | **3.0** | Initializers may perform arithmetic | Fewer start functions needed purely for initialization |
| **★ Branch hinting** | **3.0** | Branch probability hints | Helps the engine emit better machine code |
| **★ Relaxed SIMD** | **3.0** | Relaxes some SIMD semantics to map onto hardware better | Buys performance, **at the cost of results that may differ across platforms** — must be disabled on-chain and anywhere determinism is required |

### 3-2 Outside the core specification, but already usable

| Feature | Status | Significance |
|---|---|---|
| **JSPI (JS Promise Integration)** | **Phase 4 (standardized 2025-04)**; shipped in Chrome 137, Firefox 139 | **Synchronous Wasm code can call asynchronous Web APIs** — it opens a hole in the wall that says Wasm cannot block (Appendix M §5) |
| **Component Model / WIT** | Evolving | The foundation of WASI 0.2; an attempt to solve "the boundary is a toll booth" at the root |
| **JS String Builtins** | Evolving | Lets Wasm operate on JS strings directly, cutting the encode/decode tax |
| **Stack switching** | Evolving | Native coroutine support (JSPI is one special case of it) |
| **Custom page sizes** | Evolving | Frees embedded scenarios from being locked to a 64 KiB page |

> **Proposals move through five phases**: Phase 0 (pre-proposal) → 1 (feature proposal) → 2 (spec text) → 3 (implementation phase) → 4 (standardized). **Status changes over time; treat the official proposals repository and the version dates printed on `webassembly.github.io/spec` as authoritative.**

---

## 4. The Two Generations of WASI, Compared

| | `wasi_snapshot_preview1` | **WASI 0.2 (Preview 2)** |
|---|---|---|
| Model | POSIX-style file descriptors | **Component Model + WIT interface definitions** |
| Interface shape | One large flat bag of functions | Split into `wasi:io`, `wasi:filesystem`, `wasi:sockets`, `wasi:http`, `wasi:clocks`, `wasi:random`, … |
| Rust target | `wasm32-wasip1` | `wasm32-wasip2` |
| Ecosystem maturity | **High** (TinyGo and most toolchains support it) | Evolving; toolchains are catching up |
| Composability | Poor (monolithic) | **Good** (you can hand one component `wasi:clocks` and no filesystem at all) |

**The core syntax of capability-based security**:

```bash
# Grant only ./my_storage, mapped to /sandbox as the module sees it
wasmtime run --dir=./my_storage::/sandbox my_server.wasm
# Environment variables must be granted explicitly too
wasmtime run --env API_MODE=prod app.wasm
# Networking (0.2)
wasmtime serve --wasi inherit-network app.wasm
```

---

## 5. Browser API Quick Reference

```javascript
// ── Loading (★ first choice: compile while downloading) ──────────────────
const { instance, module } = await WebAssembly.instantiateStreaming(
  fetch("app.wasm"),            // the server must return Content-Type: application/wasm
  importObject                  // the capabilities handed to the module
);

// ── Compile without instantiating (cache the module for several Workers) ─
const mod = await WebAssembly.compileStreaming(fetch("app.wasm"));
const inst = await WebAssembly.instantiate(mod, importObject);

// ── Memory ───────────────────────────────────────────────────────────────
const mem = new WebAssembly.Memory({ initial: 16, maximum: 256, shared: false });
//                                    ↑ pages (64 KiB each)   ↑ threading needs shared:true
new Uint8Array(mem.buffer);      // ★ you must re-acquire the view after a grow

// ── Table (indirect call targets) ────────────────────────────────────────
const tbl = new WebAssembly.Table({ initial: 2, element: "anyfunc" });

// ── Error types ──────────────────────────────────────────────────────────
WebAssembly.CompileError    // malformed binary or failed validation
WebAssembly.LinkError       // an import didn't match
WebAssembly.RuntimeError    // a runtime trap (out of bounds, divide by zero, unreachable)

// ── Detecting cross-origin isolation ─────────────────────────────────────
if (self.crossOriginIsolated) { /* SharedArrayBuffer is available */ }
```

---

## 6. Common Traps and Where They Come From

| Trap message | Cause |
|---|---|
| `memory access out of bounds` | A read or write past the current size of linear memory |
| `integer divide by zero` | `i32.div_s` / `i32.rem_s` and friends dividing by zero |
| `integer overflow` | Overflow such as `i32.div_s(INT_MIN, -1)` |
| `invalid conversion to integer` | An `f64` → `i32` conversion where the value is NaN or out of range (the non-saturating form) |
| `unreachable` | Execution reached an `unreachable` instruction (usually a Rust `panic!` or a C++ `abort()`) |
| `indirect call type mismatch` | The actual function signature at an indirect call didn't match the declared one |
| `call stack exhausted` | Recursion too deep (**this is exactly what `return_call` tail calls are for**, Wasm 3.0) |
| `null function or function signature mismatch` | The table entry was null, or the signature didn't match |

---

## 7. Reference Resources

| Topic | Location |
|---|---|
| Core specification | `webassembly.github.io/spec/core/` |
| Proposal list and phases | `github.com/WebAssembly/proposals` |
| MDN WebAssembly guide | `developer.mozilla.org/docs/WebAssembly` |
| Emscripten documentation | `emscripten.org/docs` |
| Rust and WebAssembly Book | `rustwasm.github.io/docs/book/` |
| `wasm-bindgen` guide | `rustwasm.github.io/wasm-bindgen/` |
| WABT (the binary toolkit) | `github.com/WebAssembly/wabt` |
| Binaryen (`wasm-opt`) | `github.com/WebAssembly/binaryen` |
| Bytecode Alliance / Wasmtime | `bytecodealliance.org` |
| WASI and WIT | `wasi.dev` · `component-model.bytecodealliance.org` |
