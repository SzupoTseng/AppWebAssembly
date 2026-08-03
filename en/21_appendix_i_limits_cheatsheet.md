# Appendix I: Limits and Ceilings Cheat Sheet

> Every wall you will hit, on one page. **Each entry is labelled as a specification limit, an engine limit, or a practical recommendation** — because how easily they can be worked around differs completely.

---

## 1. Size and Memory

| Item | Value | Nature | Way around it |
|---|---|---|---|
| Linear memory page size | **64 KiB** | Specification | — |
| wasm32 addressing limit | **4 GiB** (2³²) | **Specification, unavoidable** | Streaming in chunks; multi-instance isolation; **multiple memories**; Memory64 |
| Actual browser memory limit | Often OOM by **2–3 GiB** | Engine (varies by version/platform) | Lower the initial memory, process in chunks |
| wasm64 addressing limit | 2⁶⁴ (theoretical) | Specification | **Cost: loses the free bounds check from guard pages** |
| `.wasm` file size (browser) | A hard 1–2 GB class limit | Engine | — |
| `.wasm` file size (practical recommendation) | **Under 10–30 MB** | **Practical recommendation** | **Cut the data first**, `wasm-opt -Oz`, module splitting, Brotli |
| A real reference (the FluffOS driver) | **3.6 MB raw / 0.8 MB Brotli**; ICU data 30 MB → 780 KB | Measured | See Appendix L |
| `.wasm` file size (server side) | No explicit limit | — | Bounded by physical memory |
| `memory.grow` direction | **Grow only, never shrink** | Specification | Throw the whole instance away when done (microseconds) |
| Address 0 | **Legally readable and writable** (no null pointer protection) | Specification | Emscripten can reserve low addresses as a trap region |

---

## 2. Threads and Concurrency

| Item | Limit | Nature |
|---|---|---|
| Wasm creating threads natively | **Cannot.** It must go through the host (Web Worker / OS thread) | Specification |
| Shared memory | Requires `SharedArrayBuffer` plus the threads feature | Specification |
| `SharedArrayBuffer` precondition | **Cross-origin isolation** (the COOP and COEP HTTP headers) | Browser security policy |
| Setting headers on GitHub Pages | **Not allowed** | Platform limit |
| Way around it | `coi-serviceworker` (synthesizing the headers on the front end); or switch to multi-instance isolation | — |
| Memory under multi-instance isolation | **4 GiB × N** (each independent) | — |
| Does multi-instance isolation need isolation? | **❌ No** | — |

---

## 3. SIMD

| Item | Value | For comparison |
|---|---|---|
| Wasm SIMD vector width | **Fixed at 128 bits (`v128`)** | x86 AVX2 = 256, AVX-512 = 512; ARM SVE is variable |
| Typical speedup | **2–4×** (not 4–16×) | Memory bandwidth and data shuffling eat part of it |
| Does it need detection? | **Yes**, old browsers lack it | Prepare a non-SIMD fallback build |
| Relaxed SIMD | Relaxes semantics for performance; **results may differ across platforms** | Must be disabled on-chain and anywhere determinism is required |

---

## 4. The Boundary (JS ↔ Wasm)

| Item | Cost |
|---|---|
| Passing one `i32` | Nearly free (nanoseconds) |
| Passing one string (round trip) | **Two encode/decodes + two copies + three boundary calls** (can reach microseconds) |
| `postMessage` structured clone | O(n) |
| `postMessage` + transferable | **O(1)** (ownership transfer; the source side is invalidated immediately) |
| `SharedArrayBuffer` | O(1) (visible to both at once, requires isolation) |
| Touching the DOM directly | **Cannot** — it must go through JS |
| **The golden rule** | **Make the boundary coarse and the round trips few** |
| Synchronous code awaiting an async API | **JSPI** (Chrome 137+ / FF 139+) suspends the whole Wasm stack; the fallback is Asyncify (expensive) |

---

## 5. Storage

| Mechanism | Persistent | Random access | Eats linear memory | Usable on the main thread | Suited to |
|---|---|---|---|---|---|
| **MEMFS** | ❌ | ✅ (it's in memory) | **✅ fatally** | ✅ | Temporary intermediate files |
| **IDBFS** | ✅ | ❌ (whole-mount dump) | Yes, while syncing | ✅ | Game saves, settings (< a few MB) |
| **OPFS (async)** | ✅ | Limited | ❌ | ✅ | Ordinary files |
| **OPFS (sync handle)** | ✅ | **✅ true pread/pwrite** | ❌ | **❌ Worker only** | Databases, large files, streaming |
| **WASI (server side)** | ✅ | ✅ | ❌ | — | Server side |

**Extra limits**: by default OPFS allows only **one** sync access handle per file (an exclusive lock; `{mode:"readwrite-unsafe"}` opens several, but concurrency control becomes your responsibility); data without `persist()` may be evicted under disk pressure; the user cannot see OPFS, so you must provide an export feature yourself.

---

## 6. Languages and Runtime Burden

| Language | Typical hello-world size | Suitability |
|---|---|---|
| Rust / C / C++ / Zig | A few KB to a few tens of KB | **★ Made for each other** |
| AssemblyScript | A few KB | ★ A smooth entry point for front-end developers |
| Go (standard toolchain) | ~1.5 MB+ | ⚠️ Size is the main pain point (TinyGo cuts it substantially) |
| C# / Blazor | Several megabytes | ⚠️ Strong ecosystem; cold start and size are the cost |
| Java / Kotlin | Traditionally enormous | **Only genuinely usable once Wasm GC landed** |
| Python (Pyodide) | A 30–50 MB full bundle | Worth it only when you need the whole scientific ecosystem |

**Two layers of reality about execution performance** (Pyodide as the example): a pure Python loop runs at about **1/3–1/5** of native; calling NumPy's C kernels reaches about **70%**. **Running an interpreter inside a virtual machine stacks two layers of abstraction.**

---

## 7. Things That "Do Not Exist" at the Specification Level

| Absent | Consequence | Corresponding proposal |
|---|---|---|
| `goto` / arbitrary jumps | Compilers must structure the CFG (Relooper/Stackify); a few irreducible loops get slower | multi-loop (not landed) |
| A string type | Every round trip needs encoding and decoding | JS String Builtins |
| Objects / garbage collection (absent from the MVP) | High-level languages must bring their own GC → size explodes | **✅ Now in Wasm 3.0** |
| Exception handling (absent from the MVP) | C++ try/catch went through a JS trampoline | **✅ Now in Wasm 3.0** (Tag section + `try_table`/`exnref`) |
| Tail calls (absent from the MVP) | Deep recursion in functional languages blows the stack | **✅ Now in Wasm 3.0** (`return_call`) |
| Blocking / awaiting async | Synchronous C code cannot await a Promise | **JSPI** (standardized 2025-04, Chrome 137+ / FF 139+) |
| System calls | Every capability must be imported from the host | **WASI** |
| ASLR / NX / stack canaries | **A C memory error inside linear memory may be more reliably exploitable** | None (patch with ASan/UBSan) |
| Runtime reflection / dynamic loading (in core) | Static linking means duplicated bundling | dynamic linking (Emscripten has its own scheme) |

---

## 7b. Deployment-Layer Checklist

| Item | Requirement |
|---|---|
| MIME | `Content-Type: application/wasm` (otherwise `instantiateStreaming` refuses outright) |
| Differential updates | Compression Dictionary Transport (RFC 9842, `dcb`/`dcz`): a new build ships only the delta (Appendix N §7-2) |
| ⚠️ Timer precision | **When not cross-origin isolated, `performance.now()` is coarsened** — microsecond-scale measurements are unreliable (Appendix N §15) |
| CSP | `script-src 'wasm-unsafe-eval'` (Chrome 97+ / FF 102+ / Safari 16+) |
| Compression | `Content-Encoding: br` (Wasm usually compresses very well, often 4× or better) |
| Integrity | **A `.wasm` loaded through `fetch()` has no built-in SRI**; verifying the hash yourself sacrifices streaming compilation |
| Code caching | Give the `.wasm` a stable URL (a content-hashed filename is best) so return visits skip compilation |
| Multiple Workers | `WebAssembly.Module` is structured-cloneable — **compile once and postMessage it to N Workers** |

## 8. Security Red Lines

| Red line | Why | How to check |
|---|---|---|
| **Hardcoded keys** | The string is in the Data section and **cannot be stripped** | `strings app.wasm \| grep -Ei 'sk-\|AKIA\|password\|secret'` |
| **Core trade secret algorithms** | Reverse engineering raises the cost, not the possibility | Ask: if my opponent had it tomorrow, what would I have left? |
| The Export section | **Mandated by the specification; always visible** | `wasm-objdump -x app.wasm` |
| "Client-side self-integrity checks" | The client is untrusted; any self-attestation can be patched locally | Put the authorization decision on the server |

**Six levels of reverse engineering difficulty** (see Chapter 9): read the strings (seconds) → look at the exports (seconds) → disassemble to WAT (minutes) → recover pseudocode (hours) → understand the algorithm (days to weeks) → recover maintainable source (months and up, usually not worth it).

---

## 9. Rules for Reading Performance Claims

| A common claim | The reality |
|---|---|
| "Wasm has 60–80% of native performance" | **It depends on the workload's shape**: a pure numeric loop can reach 90%+; hand-written AVX2 ported over may reach only 40–50%; fine-grained boundary calls can be slower than JS |
| "10–30× faster than JS" | True only on particular benchmarks. With V8 fully warmed up and types stable, **JS can approach Wasm, and the gap is often within 1–2×** |
| "100× faster than Docker" | **Credible for cold start**; steady-state execution performance is **below** a native binary inside a container |
| "The file is only a few KB to a few MB" | That refers to a pure compute kernel. OpenCV.js is 6–9 MB, solc 10–15 MB, Pyodide 30–50 MB |
| "Wasm is memory-safe" | It refers to **sandbox boundary** safety (it cannot harm the host), and **does not mean** your C program has no memory errors |
| "Wasm is irreversible" | **Wrong.** The format is public and structured, and disassembling it is far easier than reverse engineering x86 |
| "Turning on Wasm GC cuts size by 80%" | True only for languages that previously had to bundle a language runtime (Java/Kotlin/Dart); **it does almost nothing for Rust/C/C++** |
| "GC / memory64 / tail calls are proposals" | **Out of date.** They entered the core specification with **Wasm 3.0 in September 2025** (see Appendix A) |
| "It uses Wasm, so it is constant-time" | **Wrong.** Constant time is guaranteed by how the source is written; Wasm only provides a more controllable substrate |
