# Appendix B: Glossary and Toolchain Quick Reference

> This is a **lookup table**, not a tutorial. The last column of each row points to where the term appears in the book — **look a term up here first, and turn to the chapter only when you need to understand why.**

## 1. Core Concepts

| Term | One-line explanation | Where in this book |
|---|---|---|
| **WebAssembly (Wasm)** | A binary instruction format for an abstract stack machine defined by a specification; not the machine code of any physical CPU | Chapter 2 |
| **WAT (WebAssembly Text)** | Wasm's human-readable text format, in one-to-one correspondence with the binary (`wasm2wat` converts losslessly) | Chapters 2, 9 |
| **Linear memory** | One contiguous, addressable byte array; 1 page = 64 KiB, grow-only, never shrinks | Chapters 2, 8 |
| **Trap** | An uncatchable runtime error (out of bounds, divide by zero, unreachable), surfacing on the JS side as `RuntimeError` | Appendix A |
| **Guard page** | The trick where the engine reserves 8 GiB of virtual address space and lets the MMU perform bounds checks for free | Chapters 2, 8 |
| **Structured control flow** | Wasm has no `goto`, only `block`/`loop`/`if` plus `br` that jumps outward — the precondition for single-pass validation | Chapter 2 |
| **Validator** | An O(n) single-pass check at load time: stack types consistent, control flow structured, indices in bounds | Chapter 2 |
| **Tiering** | The two-track race of Liftoff (fast codegen) → TurboFan (optimizing codegen) | Chapter 2 |
| **Streaming compilation** | `instantiateStreaming`: compilation starts the moment the first byte arrives | Chapters 2, 5 |
| **Glue code** | The JS-side layer responsible for type conversion, memory management and API bridging | Chapter 2 |
| **Zero-copy** | Opening a `TypedArray` view over the same `ArrayBuffer` instead of moving the data | Chapters 2, 6 |
| **SoA (Structure of Arrays)** | Turning `[{x,y,z}...]` into three contiguous arrays — a cache-friendly layout | Chapter 6 |
| **CSR / CSC** | Compressed sparse row/column format, the standard compact representation for sparse matrices | Appendices E, F |
| **Cross-origin isolation** | The page state when COOP and COEP are both satisfied; the precondition for `SharedArrayBuffer` | Chapters 3, 5 |
| **Capability-based security** | A module starts empty-handed; every capability must be handed in explicitly by the host | Chapters 1, 7 |
| **Component Model / WIT** | The interface model and description language letting Wasm modules talk to each other in high-level types | Chapter 7, Appendix A |
| **LEB128** | Variable-length integer encoding; every length and index in Wasm uses it | Appendix M §1 |
| **Polymorphic stack** | The mechanism by which dead code after `unreachable` still passes validation | Appendix M §2 |
| **Table / `call_indirect`** | Wasm has no function pointers; a function pointer is really a table index | Appendix M §3 |
| **Tag / `exnref`** | The tag and opaque exception reference of Wasm 3.0 exception handling | Appendix M §4 |
| **JSPI** | JavaScript Promise Integration: the engine suspends/resumes Wasm at the stack level so synchronous code can await a Promise | Chapter 3 Wall 7, Appendix M §5 |
| **Asyncify** | The pre-JSPI alternative: Binaryen rewrites the whole module to simulate suspension (expensive) | Appendix M §5 |
| **Relaxed SIMD** | Trades determinism for better hardware mapping; **must be disabled anywhere determinism is required** | Appendix M §7 |
| **Multiple memories** | Wasm 3.0: several linear memories in one module, each still wasm32 | Chapter 8 Scenario 4, Appendix M §8 |
| **proxy-wasm** | The Wasm plugin ABI adopted by proxies such as Envoy and Istio | Appendix M §11 |

---

## 2. Storage

| Term | Explanation | Where it applies |
|---|---|---|
| **MEMFS** | A POSIX filesystem Emscripten fakes inside linear memory | Temporary intermediate files (**it eats your 4 GB budget**) |
| **IDBFS** | Syncs the whole of MEMFS into IndexedDB (`FS.syncfs`) | Game saves, settings (a few hundred KB) |
| **WASMFS** | Emscripten's next-generation filesystem backend, able to reach OPFS directly | The direction replacing MEMFS/IDBFS |
| **OPFS** | Origin Private File System, the private disk space the browser opens for each origin | **Everything that needs to persist** |
| **`opfs` VFS** (SQLite) | The first-generation OPFS backend, using an async proxy plus `Atomics.wait`; **requires `SharedArrayBuffer` / cross-origin isolation** | When you need multiple connections |
| **`opfs-sahpool` VFS** | A sync-access-handle pool; **needs no COOP/COEP and is listed as the fastest in the official docs**; no multi-connection support | **The first choice for static hosting** |
| **`createSyncAccessHandle()`** | OPFS's synchronous random-access handle (**usable only inside a Worker**) | Databases, large-file streaming |
| **`navigator.storage.persist()`** | Requests that data be marked persistent, so it isn't evicted under disk pressure | Important data |
| **VFS (Virtual File System)** | SQLite's storage abstraction layer, designed for portability; the OPFS VFS is one implementation of it | Chapter 7 |

---

## 3. Toolchain

### Compilers / toolchain front ends

| Tool | Language | Character |
|---|---|---|
| **Emscripten** (`emcc`) | C / C++ | **Emulates an entire POSIX environment** (libc, filesystem, SDL→WebGL, pthread→Worker). The first choice for porting existing large C/C++ projects |
| **`wasm-pack` / `wasm-bindgen`** | Rust | **Type bridging only**, with lean glue. The first choice for a new project written from scratch |
| **`cargo` + `wasm32-unknown-unknown`** | Rust | Bare Wasm with no JS bindings at all |
| **TinyGo** | Go | Drastically shrinks the Go runtime (at the cost of supporting a subset) |
| **AssemblyScript** | TS-style syntax | Syntax close to TypeScript, compiled straight to Wasm; a smooth entry point for front-end engineers |
| **Zig** | Zig | Native support for `wasm32-freestanding` / `wasm32-wasi`, no runtime burden |
| **Blazor** | C# | The .NET ecosystem; size and cold start are the main costs |

### Binary tools

| Tool | Purpose |
|---|---|
| **`wasm-opt`** (Binaryen) | **The highest-return optimization tool.** `-Oz` for size, `-O3` for speed, `--strip-debug` |
| **`wasm2wat` / `wat2wasm`** (WABT) | Lossless conversion between binary and text formats |
| **`wasm-objdump`** (WABT) | Inspect sections, disassemble (`-d`), view imports/exports (`-x`) |
| **`wasm-decompile`** (WABT) | Emits readable C-like pseudocode (the first stop in reverse engineering) |
| **`wasm-strip`** (WABT) | Strips custom sections |
| **`twiggy`** | **Size diagnosis**: `twiggy top` (who is eating the bytes), `twiggy dominators` (who drags whom in) |
| **`wasm-snip`** | Manually replaces named functions with `unreachable`, cutting out unwanted code paths |
| **`wasm-split`** (Binaryen) | Splits a module into primary and secondary parts by profiling data, for lazy loading |
| **`wizer`** | **Build-time pre-initialization**: run the initializer, then snapshot the memory state back into a new module (Appendix N §10-2) |
| **`wasmtime compile`** | Backend AOT, producing `.cwasm` with zero compilation at runtime |
| **WABT's `wasm-validate`** | Offline validation that a module is well-formed |

### Runtimes (server side)

| Runtime | Position |
|---|---|
| **Wasmtime** | Led by the Bytecode Alliance, the WASI reference implementation; Cranelift as the code generation backend |
| **WasmEdge** | A CNCF sandbox project, optimized for cloud-native, microservices and AI inference (with GPU access) |
| **Wasmer** | Emphasizes portability and multi-language embedding; has the WAPM package ecosystem |
| **WAMR** (WebAssembly Micro Runtime) | Extremely lightweight, suited to IoT and embedded |
| **Spin** (Fermyon) | A framework for building and running Wasm microservices, in a serverless shape |
| **wasm3** | An extremely fast interpreter (no JIT), suited to constrained environments |

### Browser-side helpers

| Tool | Purpose |
|---|---|
| **`coi-serviceworker`** | Synthesizes COOP/COEP on the front end so static hosting can use `SharedArrayBuffer` (Chapter 5) |
| **`COEP: credentialless`** | A gentler isolation mode than `require-corp`: allows cross-origin resources that haven't opted in, but requests them without credentials |
| **`'wasm-unsafe-eval'`** | The CSP keyword that permits Wasm compilation without permitting `eval()` (Chrome 97+ / FF 102+ / Safari 16+) |
| **`wasm-split`** | Emscripten/Binaryen's module splitter: a main module plus a lazily loaded secondary module |
| **C/C++ DevTools Support (DWARF)** | A Chrome extension; lets you see C++ source in DevTools, set breakpoints and inspect variables |
| **Chrome DevTools Memory / Performance panels** | Observe Wasm memory growth and compilation time |
| **`performance.measureUserAgentSpecificMemory()`** | Measures the tab's overall memory (including Wasm) |
| **Compression Dictionary Transport** (RFC 9842) | Compresses the new build using the old one cached on the user's machine as a dictionary; `dcb`/`dcz` encodings; Chrome/Edge 130+ (Appendix N §7-2) |
| **`TextEncoder.encodeInto()`** | Encodes a string directly into Wasm memory with no intermediate allocation (Appendix N §13) |

---

## 4. Key Compiler Flags

```toml
# ── Rust: Cargo.toml (release) ───────────────────────────
[profile.release]
opt-level = 3        # speed first; use "z" for size, "s" for balance
lto = true           # link-time optimization (cross-crate inlining + dead code elimination)
codegen-units = 1    # give LTO the full picture
panic = "abort"      # drop the unwinding tables (saves size and a layer of complexity)
strip = true         # strip symbols (the name section)

[lib]
crate-type = ["cdylib"]
```

```bash
# ── Rust: enabling SIMD ─────────────────────────────────
RUSTFLAGS="-C target-feature=+simd128" wasm-pack build --target web --release

# ── Emscripten ──────────────────────────────────────────
emcc app.cpp -O3 \
  -msimd128 \                       # SIMD
  -pthread -s PTHREAD_POOL_SIZE=4 \ # threads (needs cross-origin isolation!)
  -s ALLOW_MEMORY_GROWTH=1 \        # permit memory.grow
  -s INITIAL_MEMORY=64MB \
  -s MAXIMUM_MEMORY=2GB \
  -s EXPORTED_FUNCTIONS='["_main","_process"]' \
  -s MODULARIZE=1 -s EXPORT_ES6=1 \ # emit an ES module
  -flto --closure 1 \               # LTO + Closure-compressed glue
  -o app.js

# ── Debug build (keeping symbols and DWARF) ─────────────
emcc app.cpp -g -gsource-map -s ASSERTIONS=2 -fsanitize=address -o app.js

# ── Post-processing ─────────────────────────────────────
wasm-opt -Oz --strip-debug --strip-producers app.wasm -o app.opt.wasm
twiggy top -n 20 app.opt.wasm
```

---

## 5. Did You Pick the Right `--target`? (`wasm-pack`)

| target | Output | Where it's used |
|---|---|---|
| `web` | An ES module, usable directly with `<script type="module">` | **The right answer for static-hosting deployment** |
| `bundler` | A module for webpack/rollup/vite | Projects with a bundler |
| `nodejs` | CommonJS | Server side |
| `no-modules` | A traditional script hanging off a global variable | Legacy environments, and `importScripts` inside a Worker |

---

## 6. Common Error Messages → Diagnosis

| What you see | The actual cause |
|---|---|
| `404` (loading the `.wasm`) | ① `pkg/` was ignored by `.gitignore` ② an absolute path was used but the site lives under a subpath ③ Jekyll swallowed a folder beginning with `_` (add `.nojekyll`) |
| `TypeError: WebAssembly.instantiateStreaming(): Incorrect response MIME type` | The server didn't return `Content-Type: application/wasm` |
| `ReferenceError: SharedArrayBuffer is not defined` | No cross-origin isolation (see Chapter 5) |
| `RuntimeError: memory access out of bounds` | A memory error inside Wasm (build with ASan to catch it) |
| `TypeError: Cannot perform Construct on a detached ArrayBuffer` | The `TypedArray` view wasn't re-acquired after `memory.grow` |
| `LinkError: import object field 'xxx' is not a Function` | `importObject` is missing an import the module requires |
| `RangeError: WebAssembly.Memory(): could not allocate memory` | You hit the browser's memory ceiling (see Chapter 8) |
| Everything runs but the output is garbage | String encoding didn't line up (UTF-8 vs UTF-16), or a pointer was passed wrongly |
