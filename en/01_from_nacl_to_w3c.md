# Part I: Origins and Physics

# Chapter 1: From NaCl to W3C — How a Failed Plugin Became the Web's Fourth Language

> In 2011 Google shipped something called **Native Client** inside Chrome, claiming you could now run native C/C++ in the browser. Technically it worked. Commercially it failed completely — because apart from Chrome, no browser vendor was willing to implement it. Fourteen years later the same thing got done, with one difference: **this time nobody moved first alone.**

## Scenario 1: The project that succeeded technically and failed politically

**Background.** The Web's performance ceiling was not a new problem. JavaScript is dynamically typed, garbage collected, single threaded; irreplaceable for UI logic, but it hits a wall the moment you need dense computation — video transcoding, 3D rendering, image filtering, large matrix math. Around 2010, two routes were competing under that ceiling.

**Route one: Google's NaCl / PNaCl (Native Client / Portable Native Client).** The idea was blunt: if you want speed, **run native machine code directly.** NaCl used a static validator to scan x86 machine code, forcing instructions onto 32-byte alignment, banning unsafe jumps and system calls, then locking the whole thing into a sandbox fenced by segment registers. PNaCl went further: instead of shipping x86 machine code, ship **LLVM bitcode** and let the browser do the final mile of translation, escaping CPU-architecture lock-in.

**Why it failed.** Not because it was slow — it wasn't slow at all. It failed on three things:

- **It wasn't the Web.** A NaCl module lived inside a plugin container called `<embed>`, separated from the DOM and from JavaScript by a message-passing interface. It was **a native program parasitic on a web page**, not part of the page.
- **It was one company's specification.** Mozilla publicly opposed it; Apple and Microsoft never signalled an intent to implement. A "web standard" supported only by Chrome is, to a developer, a liability.
- **The validator was too complex.** Writing a provably correct machine-code validator for every CPU architecture is an extremely expensive commitment in security engineering.

**Route two: Mozilla's asm.js.** The idea was the opposite, and slightly sly — **introduce nothing new at all.** asm.js is an **extremely strict subset of JavaScript**: every numeric operation annotates its type with bitwise operators (`x|0` means 32-bit integer, `+x` means double), all memory access goes through one enormous typed-array `ArrayBuffer`, and objects, closures and garbage collection are forbidden.

```javascript
// What asm.js looks like: a comment marks the module, bit ops nail down the types
function AsmModule(stdlib, foreign, heap) {
  "use asm";                          // ← the engine sees this and switches to an AOT path
  var HEAP32 = new stdlib.Int32Array(heap);
  function add(x, y) {
    x = x|0;                          // ← declaration: x is a 32-bit integer
    y = y|0;
    return (x + y)|0;                 // ← declaration: so is the return value
  }
  return { add: add };
}
```

**The essence of the trick is that it is legal JavaScript.** In a browser that has never heard of asm.js, the code still runs correctly (just slowly); in one that has, the engine sees `"use asm"`, skips the whole JIT warm-up, and treats it as a statically typed language for ahead-of-time compilation. **Emscripten** compiled C/C++ through LLVM into this dialect of JavaScript, and for the first time "put the entire Unreal Engine in a browser" became something you could demo on stage.

**Each route proved one thing.** NaCl proved that **a browser sandbox can safely execute near-native code**; asm.js proved that **you can get within 2× of native without a plugin, purely through engine optimization, and all four browsers can implement it.**

> 💡 A Word to the Wise
> **Whether a technical proposal survives depends on how many people it lets say "I don't have to agree."** NaCl asked the other three vendors to swallow a huge new execution environment and a machine-code validator wholesale — that is asking others to bet heavily on your judgement. asm.js asked only "you need do nothing; it's legal JS anyway, I've just optimized for it" — that is **driving adoption cost to zero and leaving the optimization upside to whoever chooses to follow.** The former is a political proposal; the latter is a technical fact. This rule holds in every cross-organizational standards fight: **the proposal that can start running at zero cost to the other side wins; the one that requires the other side to pay first usually doesn't get discussed at all.** It is also why the road Wasm eventually took was asm.js's politics plus NaCl's technical ambition.

> 🔍 Deeper Commentary — asm.js's three fatal bottlenecks are, one by one, Wasm's design motivations
> asm.js won the politics and lost the physics, and the three places it lost map exactly onto Wasm's design. **First, parse cost.** However well optimized, asm.js is ultimately **text**. A 40 MB asm.js file has to go through complete JavaScript lexing and parsing before the engine can even discover "ah, this is asm.js." Parsing alone eats hundreds of milliseconds to seconds, and that bill is paid again on every cold start. Wasm's binary format compresses that step to nearly nothing — it can be **compiled while downloading** (streaming compilation), with the compiler starting work when the first byte arrives. **Second, types were guaranteed by convention rather than by specification.** `x|0` is a "please trust me" arrangement with the engine; the moment code deviates slightly the engine silently falls back to the ordinary JS path, performance falls off a cliff, and the developer usually sees no warning at all. Wasm's types are written into the binary and enforced by a validator at load time — **either it passes validation or it refuses to load; there is no middle state.** Third, **it can never obtain anything JS doesn't have.** 64-bit integers (`i64`) have no native type in JavaScript, so asm.js could only emulate them with two 32-bit numbers; SIMD vector instructions, atomics and shared memory across threads simply cannot be expressed in JS syntax. Wasm put `i32/i64/f32/f64` into the specification from day one. So the accurate historical narrative is not "Wasm replaced asm.js" but — **asm.js was a successful market-validation experiment. It proved the demand was real, proved all four engines could digest a statically typed optimization path, and then it burned itself as Wasm's fuel.** This strategy — using a proposal you know will be superseded to prove the next one is worth investing in — recurs constantly in infrastructure evolution.

## Scenario 2: 2015 — why four vendors suddenly sat at the same table

**Background.** In June 2015, Google, Mozilla, Microsoft and Apple jointly announced they would develop a brand-new binary format standard: **WebAssembly**. In the history of the browser wars this is rare to the point of strangeness — four companies that obstruct one another on nearly every issue, aligned in one go.

**Why the deal closed this time** comes down to **three "nobody loses"**:

| Vendor | Assets already sunk | What Wasm preserved |
|---|---|---|
| Google | NaCl/PNaCl sandbox and validator experience; V8's TurboFan backend | The sandbox work got a standardized outlet instead of a spec nobody else would follow |
| Mozilla | asm.js, the Emscripten toolchain, SpiderMonkey's OdinMonkey AOT path | The existing Emscripten ecosystem could swap backends painlessly; the asm.js investment wasn't wasted |
| Microsoft | Edge needed to catch up on the performance narrative fast | A clearly specified target with clean implementation boundaries, instead of reverse-engineering someone else's JS engine |
| Apple | JavaScriptCore's FTL JIT | A "small and closed" specification is far cheaper to security-review than "support arbitrary LLVM bitcode" |

**The key design trade-off — it was deliberately made small.** The Wasm MVP (Minimum Viable Product, landed 2017) deliberately **omitted** a great deal: no garbage collection, no exception handling, no threads, no DOM access, no system calls — not even a string type. It had four numeric types, one contiguous block of memory, one set of stack instructions, and a validation algorithm that completes in linear time at load.

**That deliberate smallness was a political necessity.** The smaller the spec, the lower the chance four independent implementations diverge in behaviour; the simpler the validator, the cheaper the security review; the fewer the capabilities, the narrower the attack surface for misuse. **The Wasm MVP was very nearly a signed agreement saying "we promise not to frighten you."**

**Timeline** (verifiable specification milestones):

- **June 2015**: the four parties jointly announce WebAssembly.
- **From March 2017**: Chrome, Firefox, Safari and Edge ship Wasm engines; the MVP becomes a shared capability across all four browsers.
- **December 2019**: the W3C formally makes the WebAssembly Core Specification 1.0 a Recommendation. Wasm stands alongside HTML, CSS and JavaScript as the Web's fourth core language.
- **From 2019**: the **WASI** (WebAssembly System Interface) proposal appears, and Wasm begins to leave the browser for the server, cloud native and edge computing.

> ⚠️ Authenticity Caveat
> "Four giants joined forces in 2015," "all four browsers supported it in 2017," and "the W3C made it a standard in 2019" are all verifiable public facts. But the embellished version you often see — for instance, framing Wasm as "the W3C-anointed fourth programming language that will replace JavaScript" — is narrative exaggeration. **The specification has never positioned Wasm as a replacement for JavaScript; it positions it explicitly as a complement.** To this day Wasm cannot manipulate the DOM on its own and cannot load itself; every startup requires JavaScript (or the host) to hand it the first key.

> 🔍 Deeper Commentary — the compound interest of "deliberately small," and the interest it is now paying
> The MVP's minimalism was the key to victory in 2017, but by 2026 all its bills had come due. **Bill one: no GC means the entire Java/Kotlin/Dart/C# ecosystem is locked outside.** Those languages must compile their whole garbage collector into the `.wasm`, producing artefacts that start at several megabytes — which is exactly the motivation for **Wasm GC** (letting Wasm reuse the host engine's existing collector, **now in the core specification as of Wasm 3.0**), and after Wasm GC landed, languages like Kotlin/Wasm and Dart (Flutter Web) could shrink their output substantially. **Bill two: no exception handling means C++'s `try/catch` could only be emulated through a JavaScript trampoline**, with a significant cost at every boundary crossing — the motivation for **native exception handling** (Wasm 3.0). **Bill three: no tail calls means deep recursion in functional languages (Scheme, OCaml, Haskell) always blows the stack** — the motivation for **tail calls** (`return_call`, Wasm 3.0). **Bill four: only numeric types means every string round trip is manual encode/decode** — the motivation behind **Reference Types** and **JS String Builtins**. So the right way to read the Wasm proposal list (SIMD, threads, bulk memory, multi-value, reference types, GC, exception handling, tail call, memory64, multiple memories, relaxed SIMD, branch hinting…) is not "more and more features," but — **every one of them is repaying a debt deliberately incurred in 2015 to get four vendors to the negotiating table.**
> **And that debt was essentially repaid in September 2025.** That month **WebAssembly 3.0 was declared complete**, folding **GC, Memory64, exception handling, tail calls, multiple memories, typed function references, extended constant expressions, branch hinting and 128-bit SIMD** into the core specification in one release. **Everything cut ten years ago for the sake of consensus was added back, one item at a time, and the core model never once collapsed.**
>
> This rule is worth remembering for anyone building a platform: **the subtraction you perform to win consensus becomes, after you succeed, a debt you must add back item by item; and whether you can repay it depends on whether the things you cut broke the consistency of the core model.** Wasm could repay it because it cut *capabilities* and left the two load-bearing pillars — type safety and linear memory — untouched. **Had they compromised on the type system for performance in 2015, the last decade would not have been repayment; it would have been a rewrite.**

## Scenario 3: Breaking out — WASI, and that endlessly quoted sentence

**Background.** In 2019 Wasm left the browser. A Wasm module in the core specification **has no system capabilities at all** — it cannot open a file, cannot make a connection, cannot read a clock. Every capability must be handed in explicitly by the host as an **import**. That design existed for the browser sandbox, and turned out to be exactly what the server side wanted.

**What WASI did.** It defined a **set of OS-independent standard interfaces** — files, clocks, random numbers, environment variables, networking (in later versions) — so the same `.wasm` executes with the same semantics on Linux, Windows and macOS. More importantly, its security model:

- **Capability-based security.** A Wasm module starts **empty-handed** by default. It has no permission to call `open()`; it has only the directory handles the host **pre-opens and hands to it**.
- **Path escape is blocked at runtime.** If the module tries to reach `/sandbox/../etc/passwd`, the runtime stops it at the capability boundary, rather than leaving it to filesystem permissions and luck.

```bash
# Wasmtime: map the host's ./my_storage as /sandbox in the module's view — and only that
wasmtime run --dir=./my_storage::/sandbox my_server.wasm
```

**The difference from a traditional server process is qualitative, not quantitative.** A compromised Node.js process gets **all the privileges of the user running it**; a compromised Wasm module gets **exactly the few things the host handed in, and not one thing more.** That is the difference between deny-by-default and allow-by-default.

**The endlessly quoted sentence.** In that widely circulated 2019 tweet, Docker's founder Solomon Hykes wrote — **"If WASM+WASI existed in 2008, we wouldn't have needed to create Docker."**

> ⚠️ Authenticity Caveat
> The sentence exists and is quoted constantly, but it is routinely taken out of context as "Wasm will replace Docker." **The next line of the original tweet is "Wasm is the future of computing" — not "containers are dead"** — and Hykes himself later clarified that it was praise for a bundle of properties (light, portable, cross-platform), not a declaration that containers are obsolete. In reality the two are **complementary**: Docker/OCI isolates an entire operating-system userland and can run any existing binary; Wasm isolates only a single application, buying an order-of-magnitude advantage in startup time and size, but **can only run things that have been recompiled.** In practice the most common deployment shape is **Wasm modules running inside containerized runtimes** (for example runwasi or Krustlet-style approaches on Kubernetes), not one instead of the other.

**Three concrete advantages of Wasm on the backend** (quantifiable, verifiable):

| Dimension | Container (OCI / Docker) | Wasm + WASI |
|---|---|---|
| Cold start | Tens of ms to seconds (pull image, create namespaces, run init) | Microseconds to milliseconds (module instantiation; code can be precompiled and cached) |
| Artefact size | Tens to hundreds of MB (base image plus OS layers) | Tens of KB to a few MB (your code and the necessary runtime only) |
| Isolation boundary | Linux namespaces + cgroups + seccomp (OS level) | A memory-safe virtual machine (language level), plus capability-based API grants |
| Cross-architecture | One image per CPU architecture | A single `.wasm` everywhere (the runtime does the last mile) |
| What it can run | Any existing Linux binary | **Only what has been recompiled** (the biggest practical limitation) |

**Major runtimes.** **Wasmtime** (led by the Bytecode Alliance; the WASI reference implementation and spec driver), **WasmEdge** (a CNCF sandbox project optimized for cloud native, microservices and AI inference, with GPU access from inside Wasm), **Wasmer** (emphasizing portability and cross-language embedding), and **Spin** (from Fermyon, a framework for building and running Wasm microservices, letting developers write serverless functions in familiar languages).

> 💡 A Word to the Wise
> **The real value of capability-based security is not that it is safer, but that it turns "security" into something you can read in a deploy script.** Traditional sandbox security is **subtractive** — you strip privileges one at a time with seccomp allowlists, AppArmor rules and capability drops, and you are never certain you didn't miss one. Capability-based security is **additive** — the line `--dir=./my_storage::/sandbox` is the **complete inventory** of what this service can do, down to the last character. Security review goes from "prove there is no hole" to "read one argument," and that is an order-of-magnitude drop in audit cost. Scale the principle up and you see the same struggle in database permissions, cloud IAM, OAuth scopes and browser extension permissions: **every permission model that grants everything and subtracts later eventually evolves into granting nothing and adding explicitly — and each of those migrations is expensive enough that people postpone it for a decade.**

## Scenario 4: Where it actually landed — four incontrovertible commercial cases

**Background.** However elegant the technical narrative, four products you use every day are more persuasive. The following are the most frequently cited heavyweight deployments, each with public engineering write-ups behind it:

- **Figma.** The core rendering engine is written in C++ and compiled to Wasm. This is the key to editing tens of thousands of vector layers smoothly in a browser. Figma's public engineering post documents a measured, substantial drop in load time after migrating from asm.js to Wasm.
- **Adobe Photoshop Web.** Adobe moved millions of lines of legacy C++ into the browser via Wasm (with Emscripten, and later multithreading and SIMD support), letting users do professional layer editing without installing anything.
- **Google Earth.** The early 3D globe required a dedicated plugin (an NPAPI-era artefact); today it renders global 3D terrain directly in the browser through Wasm.
- **AutoCAD Web.** Decades of C++ CAD core moved into the browser, so engineering drawings no longer have to detour through desktop software.

**What these four have in common matters more than their differences.** Every one of them is a company that **already owned millions of lines of mature C/C++.** Wasm's value to them is not "it runs fast" but **"we don't have to rewrite it"** — moving twenty years of geometry kernels, imaging algorithms and font layout engines onto an entirely new distribution channel through one compilation pipeline, instead of having three hundred engineers rewrite it in TypeScript.

**Conversely, this also draws the line where Wasm doesn't pay.** If what you are building is a form CRUD app, a blog, an e-commerce storefront, **Wasm gives you nothing** and is pure liability (an extra compilation layer, extra bytes, an extra set of debugging difficulties). Chapter 3 makes that case rather more brutally.

> 💡 A Word to the Wise
> **A new technology's real commercial value is often not "what new things it lets you do" but "how many existing assets it saves from write-off."** When Figma, Adobe and Autodesk adopted Wasm, they weren't chasing a few percentage points on a benchmark; they were **cashing in the residual value of decades of C++ assets in one move** — a number that appears on no slide but is large enough to decide whether a company bets on a new platform at all. This is why the disruption narrative so often misleads: **what actually drives large organizations to adopt new technology is usually a conservative motive (protect the existing investment), not a radical one (embrace the future).** When you need to persuade an organization to adopt something, "it lets you do what you couldn't before" rarely moves the decision maker; "it lets the money you already spent earn a second time, on a new channel" does.

## Chapter Summary

- Wasm's prehistory is the confluence of two routes: **NaCl proved a browser sandbox can safely run near-native code; asm.js proved you can get near-native performance without a plugin and that all four vendors can implement it** — the first contributed technical ambition, the second political intelligence.
- **Four-party consensus in 2015, four browsers shipping in 2017, W3C Recommendation in 2019** (all verifiable). The deal closed because the spec was deliberately made small: no GC, no exceptions, no threads, no DOM — **the smaller the spec, the lower the chance four independent implementations diverge.**
- Every Wasm feature today (SIMD, threads, GC, exception handling, tail calls, memory64, multiple memories…) is essentially **repaying a debt deliberately incurred in 2015 to reach consensus** — and that debt was largely settled by **WebAssembly 3.0 in September 2025**.
- **WASI is what let Wasm break out**, and its core is not "now it can open files" but **capability-based security**: a module starts empty-handed, every capability must be handed in explicitly by the host, and the complete inventory is written in the launch arguments.
- "If WASI had existed in 2008 we wouldn't have needed Docker" was really said, but **it does not mean containers are dead** — in practice the common shape is Wasm running inside containerized runtimes (see the ⚠️ in Scenario 3).
- What Figma, Photoshop Web, Google Earth and AutoCAD Web share is that they all hold millions of lines of mature C++. **Wasm's value to them is "we don't have to rewrite it," not "it runs fast."**

History done; now the machine itself. The next question is concrete: **when the browser receives that string of bytes beginning with `\0asm`, what exactly does it do? And why can that string be proven safe before it finishes arriving?** Turn to Chapter 2.
