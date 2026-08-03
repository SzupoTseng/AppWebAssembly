# Chapter 3: Advantages, Drawbacks, and the Limits Nobody Says Out Loud

> The least useful thing in any technical evaluation document is the table with five advantages and three drawbacks — because the drawbacks are always written more politely than the advantages, and what actually kills a project is usually the fourth one nobody wrote down. This chapter lays out the limits across three dimensions — **the browser, the system and architecture, development and ecosystem** — and asks, for each, *why is it like this?*

## Scenario 1: Four advantages, and the fine print under each

**Background.** You can find Wasm's advantages in any introductory article. But under each advantage there is a line of fine print, and the fine print is what engineering decisions run on.

**Advantage one: near-native performance.**

- **Why it's fast.** The binary format parses at almost no cost; static types mean the compiler need not insert type checks; there is no garbage collector pausing at random; linear memory is laid out compactly, so CPU cache hit rates are high.
- **Fine print.** All four of those advantages **hold only in the shape of dense computation.** If your code spends most of its time waiting on the network, mutating the DOM, or concatenating strings, Wasm helps with none of it — and you have additionally paid for the module download and the boundary crossings. **Wasm's performance advantage has a threshold; below enough compute, it is a net negative.**

**Advantage two: sandbox safety.**

- **Why it's safe.** It executes by default in a memory-safe isolated environment, cannot reach host resources, and every capability must be imported explicitly.
- **Fine print.** **"Sandbox safety" protects the host, not your program.** And on the backend, whether that sandbox is genuinely airtight depends on the runtime's implementation quality — a Wasm runtime is a large body of complex software containing a JIT, signal handlers and memory-mapping management, **which is historically where vulnerabilities are densest.** **"It's Wasm, therefore it's safe" is not a sentence you can put in a security assessment** (the full three-layer attack surface and countermeasures are in Appendix O §7).

**Advantage three: language independence.**

- **Why it works.** Anything that compiles to LLVM (or has its own Wasm backend) can emit `.wasm`. Rust, C/C++, Go, Zig, AssemblyScript, C# (Blazor), Kotlin, Swift and Dart all work.
- **Fine print.** **"Can compile" and "compiles into something usable" are two different things.** The dividing line is whether the language drags a runtime along with it:

| Language | Runtime burden | Typical `.wasm` size (hello-world class) | Honest assessment |
|---|---|---|---|
| Rust / C / C++ / Zig | Essentially none (no GC, no runtime) | Several KB to tens of KB | **A natural fit** |
| AssemblyScript | Tiny runtime plus a simple GC | Several KB | A smooth on-ramp for frontend engineers |
| Go | **Full runtime + GC + scheduler** | ~1.5 MB+ with the standard `GOOS=js` toolchain | Size is the main pain (TinyGo shrinks it a lot, at the cost of a subset) |
| C# / Blazor | .NET runtime (or AOT-trimmed) | Several MB | Powerful ecosystem; size and cold start are the price |
| Java / Kotlin | Traditionally had to package the JVM semantic layer | Enormous | **Only genuinely usable after Wasm GC (now in the 3.0 core specification)** |
| Python | The entire CPython interpreter | Pyodide's full bundle is 30–50 MB | Worth it only when you need the whole scientific ecosystem |

**Advantage four: extremely light, extremely fast to start.**

- **Why it works.** Compared with Docker images that run to hundreds of MB and require pulling an image and creating namespaces, `.wasm` is usually a few KB to a few MB and instantiates in microseconds.
- **Fine print.** **That comparison holds only on the backend.** In the browser, your competitor is not Docker; it is "plain JavaScript, which downloads nothing." An 8 MB Wasm module against a 200 KB JS bundle is **forty times** the weight. "Lightweight" is a question of relative to whom, and swapping the comparison group inverts the conclusion.

> 💡 A Word to the Wise
> **Every technical advantage is a ratio, and the denominator can be swapped.** "Wasm is extremely lightweight" is true against Docker and false against `<script>`; "Wasm approaches native performance" is true against JavaScript and discounted against a native binary. Nobody is lying — **every performance claim presupposes a comparison group, and that group is usually omitted.** So the most valuable move when evaluating any technology is to restore the omitted denominator, then ask: **in my situation, who is my real alternative?** Most failed technology choices were not the wrong technology; they were the wrong comparison.

## Scenario 2: Three walls in the browser

**Background.** Every frontend Wasm project hits these three, in almost the same order.

**Wall one: no direct DOM access.**

Wasm still cannot reach HTML, CSS or DOM elements. It must pass data through JavaScript as an intermediary (the glue code).

- **Why, technically.** The DOM is a high-level API built on JavaScript's object model, involving a garbage-collected object graph, strings and prototype chains — and **none of those types exist in the core Wasm specification.** Letting Wasm touch the DOM directly would mean first moving the entire JS object model into Wasm's type system.
- **Today's answer.** `wasm-bindgen` / `web-sys` generate bindings so Rust appears to call `document.createElement()` — but underneath, **every one of those calls still detours through JavaScript.**
- **Tomorrow's answer.** **Reference Types** (letting Wasm hold opaque host references, Wasm 2.0) and **Wasm GC** (letting Wasm understand host objects, Wasm 3.0) have narrowed the gap considerably, and **JS String Builtins** continues to push. But "direct DOM manipulation with no bridging cost" remains unrealistic for the foreseeable future.
- **Practical conclusion.** **Do not write UI in Wasm.** Compute in Wasm, draw in JS. This is exactly what Figma does — Wasm computes geometry and layout, WebGL paints pixels, the DOM handles only menus and panels.

**Wall two: data transfer with JavaScript is expensive.**

Wasm knows only numbers. Strings, objects and arrays must be serialized into linear memory and deserialized back out (mechanics in Chapter 2, Scenario 4).

- **A measured mental model.** The fixed overhead of a boundary crossing is on the order of nanoseconds, but **one string round trip's encode/decode can easily reach microseconds.** When you make a hundred thousand fine-grained calls per second, that bill lands squarely in the middle of your flame graph.
- **The classic disaster.** Treating Wasm as "a faster library" and replacing JS function by function — every function gets faster and the whole thing gets slower, because boundary crossings explode.

**Wall three: file size gets out of hand easily.**

- **Primary cause.** Languages with large runtimes (Go, C#, Java) must package their entire GC and standard library.
- **Secondary cause.** Static linking. Wasm traditionally had no dynamic linking, so using `libpng` means compiling all of `libpng` in — ten modules using the same library compile it ten times.
- **Weapons available:**

```bash
# 1. Binaryen's wasm-opt: the single most important step; wins size and speed together
wasm-opt -Oz --strip-debug --strip-producers input.wasm -o output.wasm

# 2. Rust side: write optimization and stripping into Cargo.toml
#    [profile.release]
#    opt-level = "z"      # or 3 (speed first) / "s" (balanced)
#    lto = true           # cross-crate inlining and dead-code elimination
#    codegen-units = 1    # give LTO the whole picture
#    panic = "abort"      # drop the unwinding tables (Rust-specific, saves real size)
#    strip = true         # strip symbols

# 3. Diagnose: twiggy tells you which symbol is eating your bytes
twiggy top -n 20 output.wasm

# 4. Transport: always enable Brotli (Wasm compresses well — commonly 3.5–5×)
```

> **This is only the entrance.** The complete size arsenal — section-level dissection, what each `wasm-opt` pass actually does, Rust's formatting machinery hiding inside `panic!` (which can be over 30% of a small module), the "generic thin shell" cure for monomorphization blowup, `no_std`, data trimming, and **Compression Dictionary Transport** (which makes a new release ship as tens of KB) — **is in Appendix N, Part One.**

> ⚠️ Authenticity Caveat
> The widely repeated "Wasm files are usually a few KB to a few MB" applies **to a pure computational core.** The moment a complete language runtime or a large C++ library is involved, real sizes are an order of magnitude up: OpenCV.js around 6–9 MB, the Solidity compiler `soljson.wasm` around 10–15 MB, Pyodide's full bundle 30–50 MB. **When quoting a size figure, always confirm which layer it refers to.**

> 🔍 Deeper Commentary — "can't touch the DOM" is actually a blessing, and nobody wants to say so
> This is the most counterintuitive passage in the chapter. Every introduction lists "can't touch the DOM" as a drawback. But what would happen if Wasm really could manipulate the DOM directly? **First, it would be slower.** The bottleneck in DOM manipulation has never been "which language issued the call"; it is style recalculation, reflow and paint — all inside the browser's rendering pipeline, independent of the calling language. A Wasm that could call `appendChild` directly **would not be faster than JS; it would merely make it easier for you to write code that triggers a thousand reflows per frame.** **Second, it would tear the ecosystem apart.** The moment Wasm could touch the DOM, we would get a "Wasm React" and a "Wasm Vue," and their interoperability with the JS ecosystem would be a permanent wound. **Third, and most important: it would destroy the clear architectural dividing line.** That line currently forces everyone into a healthy decision — **put heavy computation in Wasm, keep interaction and presentation in JS.** That is precisely the shape Figma, Photoshop Web and AutoCAD Web all independently adopted — and they adopted it **under compulsion.** So the truth is: **Wasm's inability to reach the DOM is a guardrail that rescues architects from their own temptations.** The principle generalizes: **a platform's most valuable limitations are the ones that stop you doing things that look convenient and rot in the long run.** gRPC forcing you to define a schema first, Rust forcing you to think about ownership, Wasm forcing you to separate computation from presentation — the same disease, cured the same way.

## Scenario 3: Four walls in the system and architecture

**Wall four: a strict sandbox — no native system access.**

Wasm has no concept of an operating system by default. It cannot read files, open sockets or touch hardware. In the browser it passes data through JS; on the backend it takes capabilities through WASI — and **the WASI specification is still evolving:**

- **`wasi_snapshot_preview1`.** The de facto first generation, modelled on POSIX-style file descriptors. Widest ecosystem, best tooling support, but semantically welded too tightly to POSIX.
- **WASI 0.2 (Preview 2).** Rebuilt on the **Component Model**, describing interfaces with **WIT** (Wasm Interface Types), splitting the world into composable interfaces like `wasi:io`, `wasi:filesystem`, `wasi:sockets` and `wasi:http`. The direction is right; the ecosystem migration is still in progress.
- **Practical conclusion.** **The backend Wasm you write today should be prepared to be migrated once.** That is part of the adoption cost and should not be ignored.

**Wall five: constrained memory management.**

One contiguous linear memory that can only expand, never contract; and if your code leaks internally, Wasm will not reclaim it for you (see Chapter 2, Scenario 2). Two practical consequences:

- **A long-lived tab grows monotonically fatter.** The cure is "throw away the whole instance and re-instantiate" — cheap enough in Wasm (microseconds) to be a routine operation.
- **The `ArrayBuffer` detach trap** bites when you are busiest (heavy allocation → triggers grow → every view invalidated).

**Wall six: imperfect multithreading.**

Wasm itself cannot create threads. In the browser it must rely on **Web Workers plus `SharedArrayBuffer`** (the threads feature provides the `shared` marker on `memory` and a set of atomic instructions `i32.atomic.*`, `memory.atomic.wait/notify` — see Appendix M §6).

**And `SharedArrayBuffer` has a bloody history.** After the 2018 **Spectre / Meltdown** class of speculative-execution side channels, `SharedArrayBuffer` became part of the attack toolkit because it enables nanosecond-resolution timers, and **every major browser disabled it by default overnight.** It came back, but with a stringent condition — **cross-origin isolation**:

```http
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: require-corp
```

The **server** must return both headers for the page to enter the isolated state, for `self.crossOriginIsolated` to be `true`, and for `SharedArrayBuffer` to exist at all.

**This is the wall that becomes the single most important obstacle in Chapter 5** — because **GitHub Pages does not allow custom HTTP headers.**

**Wall seven: synchronous code meeting an asynchronous world.**

This is the least discussed of the system walls, and the one that most often trips people mid-port.

**The shape of the problem.** The C/C++/Rust code you are porting is written **synchronously** — you call `read(fd, buf, n)` and expect the data to be in `buf` when it returns. But **the browser's world is almost entirely asynchronous**: `fetch()` returns a Promise, IndexedDB returns events, OPFS's async API returns Promises. **And Wasm has no way to *wait* on a Promise** — it cannot block, and blocking freezes the whole tab.

**Three historical solutions, each better than the last:**

| Solution | Mechanism | Cost |
|---|---|---|
| **Rewrite as asynchronous** | Convert the whole call chain into callbacks/state machines | **Infeasible** for hundreds of thousands of lines of existing C |
| **Asyncify** (Emscripten's binary transform) | Binaryen rewrites the entire module, manually saving and restoring the call stack in linear memory | **Works, but expensive**: code size can balloon, execution slows, and you must carefully annotate which functions unwind |
| **★ JSPI (JavaScript Promise Integration)** | **The engine suspends and resumes at the Wasm stack level** | **Native, near-zero rewriting** — this is the right answer |

**JSPI's status is worth memorizing**: it reached **Phase 4 (standardized) in April 2025** and has shipped in **Chrome 137 and Firefox 139**. It works like this: **when Wasm calls an imported function that returns a Promise, the engine suspends the entire Wasm execution stack; when the Promise resolves, execution resumes from the suspension point with the result handed back** — from Wasm's side, that was an ordinary synchronous call.

```javascript
// Conceptual sketch: wrap a Promise-returning JS function as a synchronous import to Wasm
const asyncImport = new WebAssembly.Suspending(async (url) => {
  const res = await fetch(url);           // the asynchronous world
  return new Uint8Array(await res.arrayBuffer());
});
// And wrap the exported entry point with Promising so it appears async to JS
const run = WebAssembly.promising(instance.exports.main);
await run();
```

**It opens a hole in a difficulty shared by Chapter 5, Chapter 7 and Appendix L**: OPFS's async API, `fetch` and IndexedDB **no longer require "move into a Worker with sync handles" or "rewrite with Asyncify" before synchronous C code can use them.**

**But don't treat it as a cure-all — three caveats.** **(a)** Suspension and resumption are not free, and at high call frequency the overhead is significant — **it suits "occasionally wait for I/O," not the hot loop.** **(b)** Support still needs feature detection and a fallback path. **(c)** **It solves waiting, not parallelism** — you still have exactly one thread.

> 💡 A Word to the Wise
> **A security vulnerability's real cost is rarely the engineering to patch it; it is the permanent tax it leaves on the entire ecosystem.** Spectre's fixes at the CPU microcode and compiler level were completed long ago, but the tax it left — **every web page that wants multithreading must pay the heavy deployment cost of cross-origin isolation, and isolation collaterally breaks third-party iframes, ads, embedded video and CDN resources** — will be paid by the whole Web for a decade or more. That yields a brutal corollary in security: **when assessing a vulnerability's severity, the question is not "how much damage can it do" but "how much inconvenience will the world pay over the next decade to prevent it."** The first is one-off; the second compounds.

## Scenario 4: Two walls in development and ecosystem

**Wall eight: debugging is extremely difficult.**

When Wasm crashes, the browser console usually gives you `RuntimeError: memory access out of bounds` and a string of `wasm-function[1234]`.

- **Why it's hard.** Compilation has already erased types, variable names and source structure. The stack has function indices, not names.
- **What you can do** (more than most assume):
  - **Keep the `name` custom section.** This is the section in the Wasm specification specifically for function names. Don't blindly `--strip-all` at compile time; keeping it turns stack traces back into human language.
  - **DWARF debug info.** Both Emscripten and Rust can embed DWARF in Wasm. Paired with Chrome DevTools' **C/C++ DevTools Support (DWARF)** extension, you can **read C++ source, set breakpoints and inspect variables** in the browser. This is the most underrated experience improvement of recent years.
  - **`wasm2wat` / `wasm-objdump`** (the WABT toolset): convert the binary back to readable text and inspect instructions line by line.
  - **Emscripten's sanitizers.** `-fsanitize=address` and `-fsanitize=undefined` work on Wasm and catch out-of-bounds and undefined behaviour inside linear memory — **the most practical compensation for "no ASLR/canary inside the sandbox."**
  - **The `console.log` school.** Emscripten's `EM_ASM` and Rust's `web_sys::console::log_1` — always available, always effective.
- **But production is another matter.** When you ship you will set `strip = true` (Chapter 9), which removes exactly the debug information you need. **You must keep a build with symbols and map back through source maps or a symbol server** — an area far less mature in the Wasm ecosystem than in the native world.

**Wall nine: not every language pays off when compiled.**

- **GC-free languages (Rust, C/C++, Zig).** A natural fit.
- **Heavy-runtime languages (Java, Python, JavaScript-in-Wasm).** Post-compilation performance is often **below expectations, and can be slower than running natively** in the original environment. The reason is direct: you are running one virtual machine inside another (an interpreter's interpreter), two layers of abstraction stacked. QuickJS compiled to Wasm running JS is 10–20× slower than the browser's native V8 — a predictable physical result, not an implementation defect.
- **What Wasm GC changed.** It lets languages like Kotlin, Dart, Java and Scheme **use the host engine's existing, heavily optimized garbage collector** instead of packaging their own. That is an order-of-magnitude improvement in size and a real help to performance — but it requires engine support, and it does little for existing projects already full of `i32`-pointer-style code.

> 💡 A Word to the Wise
> **The most accurate indicator of a technology's maturity is not how fast it runs, but how easily you can investigate it when it breaks.** You can measure performance in a benchmark and put it on a slide; but "it's 3 a.m., production is down, how fast can you find the line" appears on no technology-selection comparison sheet, and it is the variable that decides how the team's next three years go. Wasm's performance story has been told for a decade; its observability story has only just started — **and that is the real reason it currently suits "a computational core owned by one team with clean boundaries" rather than "the body of the whole application."** When selecting, ask one more question: **when this thing fails, what do I have in my hands?**

## Chapter Summary

- The four advantages each carry fine print: **the performance advantage has a compute threshold**, **the sandbox protects the host, not your program**, **the language-independence dividing line is runtime burden**, and **"lightweight" inverts when you swap the comparison group** (light against Docker, heavy against `<script>`).
- Three browser walls (one to three): **can't touch the DOM** (because the core specification has no object or string types), **cross-boundary data is expensive** (one string round trip = two encode/decode passes + two copies), **size gets out of hand easily** (heavy runtimes plus static linking).
- **"Can't touch the DOM" is in substance a guardrail** — it forced out the healthy "Wasm computes, JS draws" architecture used by Figma and Photoshop Web (see the 🔍 in Scenario 2).
- Four system walls: **WASI is still migrating from preview1 to 0.2** (backend Wasm written today should expect one migration), **linear memory only grows**, **multithreading requires `SharedArrayBuffer`, which the aftershocks of Spectre have shackled to cross-origin isolation**, and **synchronous code meeting an asynchronous world.**
- The fourth wall's answer is **JSPI** (standardized April 2025; Chrome 137 / Firefox 139): **the engine suspends and resumes Wasm at the stack level**, letting synchronous C code use Promise-returning Web APIs directly, replacing the expensive Asyncify binary transform. But it **solves waiting, not parallelism**, and does not belong in a hot loop.
- Two development walls (eight and nine): **debugging is hard** (but the `name` section, DWARF plus the Chrome extension, `wasm2wat` and sanitizers are genuinely usable — far better than the "console.log only" impression), and **heavy-runtime languages often don't pay off** (a virtual machine inside a virtual machine).
- That cross-origin isolation constraint becomes the pivotal obstacle of the next Part — because **free static hosting is precisely what refuses to let you set HTTP headers.**

The limits are catalogued, but knowing your own limits isn't enough. The next question: **in the same situation, who is my real alternative, what does it beat me at, and where does it lose?** Turn to Chapter 4.
