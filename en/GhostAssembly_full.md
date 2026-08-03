# 《Ghost Assembly》
### ——The machine that does not exist, and its silent execution in every tab

![Ghost Assembly — cover poster](GhostAssembly.png)

> Merged single-file edition. For educational and research use: a survey and critical commentary spanning WebAssembly's execution model, its deployment on static hosting, and the commercial structures of the post-moat era.


---

## Contents

- Preface: The Machine Running on Someone Else's Computer

**Part I: Origins and Physics**

- Chapter 1: From NaCl to W3C — How a Failed Plugin Became the Web's Fourth Language
- Chapter 2: The Physics of the Binary — Every Byte After the Magic Number
- Chapter 3: Advantages, Drawbacks, and the Limits Nobody Says Out Loud
- Chapter 4: The Competitive Landscape — JavaScript, Docker, V8 Isolates, EVM, WebGPU and Native

**Part II: Building a Machine on a Static Page**

- Chapter 5: Running a Machine on a Static Page — The COOP/COEP Wall, and One Ingenious Way Around It
- Chapter 6: One Hundred and One Machines — A Panorama of Wasm on Static Pages, and Five Universal Architectures
- Chapter 7: The Memory of a Stateless Machine — MEMFS, IDBFS, OPFS and WASI
- Chapter 8: The 4 GB Ceiling — File Size, App Size, and Four Ways Around It

**Part III: The Moat After Everyone Can See It**

- Chapter 9: Everyone Can See It — Natural Obfuscation, Two Absolute No-Go Zones, and the Hybrid Architecture
- Chapter 10: Why Figma Isn't Afraid — From a Local Private Server to the Cloud Core
- Chapter 11: Will the Moat Last? — The Dynamics of Commoditization and Network Effects
- Chapter 12: When Tokens Cost Almost Nothing — The Time Trap of Building Your Own Wheel, and the Endgame Architecture
- Appendix A: Wasm Timeline and Specification Quick Reference
- Appendix B: Glossary and Toolchain Quick Reference
- Appendix C: The GitHub Pages × Wasm Deployment Playbook
- Appendix D: The Hundred-Case Catalog of Static-Page Wasm (Part 1) — Cases 1–35
- Appendix E: The Hundred-Case Catalog of Static-Page Wasm (Part 2) — Cases 36–70
- Appendix F: The Hundred-Case Catalog of Static-Page Wasm (Part 3) — Cases 71–101
- Appendix G: Storage Implementation Reference (Rust + Wasm + OPFS)
- Appendix H: Specification Templates for AI Coding Agents
- Appendix I: Limits and Ceilings Cheat Sheet
- Appendix J: The Front/Back Boundary Decision Table and Moat Checklist
- Appendix K: Controversies and Authenticity Calibration Q&A
- Appendix L: A Deep-Water Case — FluffOS × Wasm, Moving an Entire MUD Server onto a Static Page
- Appendix M: The Deep End of the Specification — Twelve Technical Details Usually Skipped
- Appendix N: Size and Speed — A Complete Guide to Compressing and Accelerating Wasm
- Appendix O: Testing, CI and Runtime Security


---



## Preface: The Machine Running on Someone Else's Computer

At 3:40 on a summer afternoon in 2026, a perfectly ordinary question was typed into a search box:

> **"Explain WebAssembly in detail — its history, pros and cons, competitors, and notable applications or open-source projects."**

Every engineer has asked that question. But over the next hour or so, the conversation refused to stay at the beginner level. It slid from *what is Wasm* to *what are Wasm's limits*, then down a side road that looked unrelated — *"Are GitHub Pages sites static? Can you run a server on them?"* — and after that it never came back.

Because at the end of that side road sat an unsettling fact: **a web-hosting space that costs nothing, plus one Wasm engine, can run FFmpeg, run Linux, run a SQL database, run a large language model.** The server hadn't gotten cheaper. It had been removed entirely. The computation didn't disappear — it was simply pushed onto the CPU of every person who opened the page.

So the conversation asked the next question: what is everyone else running up there? The answer ran to a hundred and twenty entries.

And then, after the hundred and twentieth, the conversation turned and asked something that had nothing to do with technology — and that rearranged everything:

> **"If you run your program on GitHub Pages, isn't everyone able to see it?"**

Yes. Completely. Your `.wasm` file is downloaded in full onto every stranger's computer.

> **"If Figma is Wasm, isn't Figma exposed too?"**

Also yes. `figma.wasm` is downloaded onto hundreds of millions of machines every day.

> **"Then you wouldn't even need to fully decompile it — just download it and run it locally. Doesn't that break Figma's business model?"**

That is where this book actually begins. **Because the answer is no — and understanding *why* it is no matters more than understanding Wasm itself.**

---

### Three different things, stirred into one pot

The raw material for this investigation was a messy technical transcript. Three kinds of ingredient float in it, and separating them is this book's first lesson:

1. **Things that hold up.** Wasm's binary format and type system; the 4 GB addressing ceiling of linear memory; the causal chain from COOP/COEP to `SharedArrayBuffer`; OPFS's `createSyncAccessHandle`; WASI's capability-based security model; the fact that Figma and Photoshop Web really did move C++ into the browser via Wasm. All verifiable, all reproducible.
2. **Claims you can't get to the bottom of.** Among the hundred and twenty "classic cases" in the transcript, a substantial share are **real, well-known open-source projects** (FFmpeg.wasm, v86, Pyodide, DuckDB-Wasm, SQLite-Wasm, esbuild, Stockfish, OpenCV.js…), but a substantial share are **illustrative constructions derived from technical logic** (`Web-Biconical`, `Espace3D-Wasm`, `Cubism-OLAP-Wasm`, `Hologram3D-Wasm`…) — the technical path they describe holds up, but **the project itself is unverified and quite possibly does not exist under that name.** Everything in that category is tagged "⚠️ Authenticity Caveat." Every "N times faster" and "X% of native" figure gets the same treatment: **trust the order of magnitude, doubt the decimal point.**
3. **Intuitions that will mislead you.** "Binaries are hard to reverse, therefore safe." "If it's exposed, there's no business model." "Tokens got cheap, so anyone can build anything." Each of those is half right — and it is the other half that decides whether your architecture rots two years from now.

> ⚠️ The book's authenticity discipline
> This book spans verifiable specification facts and unverified community claims. The latter are always tagged "⚠️ Authenticity Caveat." **For anything at the specification level (binary format, spec status, browser API behaviour), defer to the official WebAssembly specification, MDN, and each engine's implementation docs.** This book is written against **WebAssembly 3.0** (completed September 2025), in a field that is still moving. **Any source that calls GC / memory64 / tail calls / exception handling a "proposal" was written before 3.0.**

---

### How the investigation runs

| Part | Where it goes | Contents |
|----|------|------|
| Part I — Origins and Physics | Where this machine came from and how it runs (Ch. 1–4) | NaCl/asm.js prehistory · the four-vendor consensus · binary format and type system · tiered compilation · linear memory · pros, cons and limits · six simultaneous competitions with JS, Docker, V8 Isolates, EVM, **WebGPU and native** |
| Part II — Building a Machine on a Static Page | Moving the machine somewhere that costs nothing (Ch. 5–8) | The COOP/COEP wall and `coi-serviceworker` · a taxonomy of 101 cases · the four storage layers MEMFS/IDBFS/OPFS/WASI · the 4 GB ceiling and four ways around it |
| Part III — The Moat After Everyone Can See It | What's left once the machine has been downloaded (Ch. 9–12) | The "natural obfuscation" of binaries and two absolute no-go zones · Figma's four lines of defence · the dynamics of commoditization versus network effects · the time trap and the endgame architecture once tokens cost nothing |
| Appendices | A timeline & spec cheatsheet · B glossary & tools · C GitHub Pages playbook · **D–F the 101-case catalog of static-page Wasm, entry by entry, with authenticity tags** · G storage implementation reference · H spec templates for AI coding agents · I limits cheatsheet · J the front/back boundary decision table · K disputes and calibration Q&A · **L deep case study: FluffOS × Wasm — an entire MUD server moved onto a static page** · **M the spec deep end (twelve details everyone skips)** · **N size and speed (compression and acceleration, in full)** · **O testing, CI and runtime security** |

### Three movements: understand it, use it, defend it

- **Movement One — Understand It (Ch. 1–4).** Wasm is not "faster JavaScript." It is **a machine whose specification is nailed shut**: a stack virtual machine, structured control flow, a single contiguous linear memory, a type system that can prove safety before execution. It is fast not because it is clever but because **it lets you touch nothing.** And every capability cut in 2015 to get four browser vendors to the same table was added back, one at a time, over ten years — **by WebAssembly 3.0 in September 2025, that debt was essentially repaid.** **Goal: know every physical law of this machine, because every limit later in the book is a direct consequence of them.**
- **Movement Two — Use It (Ch. 5–8).** The most interesting thing about a machine is that it can run somewhere it has no business running. GitHub Pages gives you no HTTP headers, no listening ports, not one line of backend — and the community got video transcoding, an x86 emulator, an OLAP database and LLM inference running on it anyway. **Goal: get the machine actually moving, and know exactly which wall it hits first.**
- **Movement Three — Defend It (Ch. 9–12).** When your machine has been downloaded in full onto every stranger's computer, what do you have left? The answer isn't in an obfuscator; it's on an architecture diagram. **Goal: draw the line between "which computation you give away" and "which relationships you lock up" — the only line still standing once LLMs push the marginal cost of writing code toward zero.**

If you'd like to see **a real example that completed all three at once** — a MUD server whose compiler, virtual machine and telnet stack all run inside a browser tab, whose entire source has been freely downloadable for thirty years, and whose value has not diminished by a cent because of it — **turn straight to Appendix L.** It is the cleanest living specimen of this book's central thesis.

Understand it, use it, defend it — the three verbs interlock. The 4 GB linear-memory ceiling from Movement One is precisely why FFmpeg.wasm in Movement Two can't swallow a large 4K file; and the sweetness of Movement Two's "push the compute onto the client for free" is precisely why Movement Three's moat **has to** be built somewhere else.

> 💡 **The book's central thesis**
> **What can be downloaded will eventually be copied; what cannot be taken away is the moat.**
> Wasm turned computation into something infinitely copyable and free to distribute — which is both its greatest gift and its most complete demolition of a business model. Real architectural skill is not in hiding your code well; it is in **knowing clearly which things were never hideable, and then putting the value somewhere else.**

### About the title

**Assembly language died once.**

It was the only language that touched the machine directly, and then high-level languages abstracted it away layer by layer, until it became a craft practised by a few and welded to one particular CPU. **It died of not being portable — a block of x86 assembly moved to ARM is just a pile of dead bytes.**

And it came back, wearing a different body: **this time, its machine does not exist.**

WebAssembly is the assembly language of an abstract stack machine that exists in a specification and nowhere in physics. **And precisely because that machine does not exist, it is everywhere** — running right now in the tab you have open, and in billions of computers you will never see, quietly, while their owners mostly have no idea.

**Something with no body, invisible, and everywhere at once. There is a word for that.**

And what this book is really about is what happens after that ghost drifts into someone else's house: **the thing you gave away — is it still yours?**

Each chapter closes with "💡 A Word to the Wise" as the note for that evening, followed by "🔍 Deeper Commentary," digging into the engineering reality behind the case and the road you can't see.

---

### How to read this book

The twelve chapters are a line; reading them in order works best. **The fifteen appendices are not** — they are reference material, each answering a different situation. Rather than starting from the front, pick the path that matches the question you have right now:

| Who you are / what you're doing | Suggested path |
|---|---|
| **Ten minutes, want to know what this book is** | Ch. 9 (Everyone Can See It) + Appendix J (the boundary decision table). **The two most immediately actionable pieces in the book.** |
| **Deciding whether to use Wasm for a feature** | Ch. 3 (limits) → Ch. 4 (competitors) → Appendix I (limits cheatsheet) → Appendix J (decision table) |
| **Porting a C/C++ project to the web** | Ch. 2 (physical laws) → Ch. 5 (the deployment wall) → Ch. 7 (storage) → Appendix C (playbook) |
| **Module too big / too slow** | Ch. 8 (the ceiling) → **Appendix N (size and speed, with two ROI tables)** |
| **Persistence on static hosting** | Ch. 7 → Appendix G (Rust + OPFS source). **Pay attention to the `opfs-sahpool` fork in Ch. 7 — it can save you two weeks.** |
| **Curious what people actually run on static pages** | Ch. 6 (taxonomy and the five shared architectures) → Appendices D–F (101 cases) |
| **Want one case taken all the way down** | **Appendix L** (FluffOS: an entire MUD server inside a browser tab) |
| **Making architectural or business decisions** | Ch. 9–12 + Appendix J |
| **Digging into the spec** | Ch. 2 → **Appendix M** (binary encoding, the validation algorithm, `call_indirect`, the exception ABI, JSPI, atomics…) |
| **Setting up tests and CI** | **Appendix O** (the three-tier pyramid, `wasm-bindgen-test`, fuzzing, CI gates for size and secrets, cross-engine divergence) |
| **Doing a security review** | Ch. 9 → Appendix O §7 (the runtime's own attack surface, and supply chain) |
| **Handing work to an AI agent** | Appendix H (spec templates you can copy verbatim) |
| **Suspicious of a claim in the book** | **Appendix K** (disputes and calibration Q&A — every ⚠️ in the book, gathered and re-checked) |

> **If you'll only read one appendix**: read **N** (size and speed) to solve the problem in front of you, or **L** (that thirty-year open-source control experiment) to understand what this is really about.

> ⚠️ Educational and research notice
> This book is for educational and research purposes: a survey and commentary on public material and the current state of the technology. Its treatment of binary protection, reverse engineering and code obfuscation is **risk disclosure for architectural decisions only** — not operational advice for circumventing someone else's licence, cracking commercial software, or defeating technical protection measures. Analysing a binary **you have the right to analyse** is legitimate; cracking and redistributing someone else's protected commercial software may violate licence agreements, copyright law and technical-protection-measure provisions.

The coffee is half cold and the cursor is still blinking in the search box. The first question is a small one: **where did this thing come from?** We start with a failed Google project.

---



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

---



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

---



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

---



# Chapter 4: The Competitive Landscape — JavaScript, Docker, V8 Isolates, EVM, WebGPU and Native

> "Who is Wasm's competitor?" has no single answer, because **Wasm fights on six entirely different battlefields against six entirely different opponents.** In the browser it divides labour with JavaScript; in cloud native it contests the isolation boundary with containers; at the edge it races V8 Isolates on cold start; on-chain it argues with the EVM over who owns the virtual machine; in dense computation it divides labour with **WebGPU**; and beyond all of those sits the most fundamental opponent of all — **don't build a web app at all.** **It wins differently in each, and it loses differently too.**

## Scenario 1: The browser — Wasm vs. plain JavaScript

**Background.** This is the most misunderstood comparison, because it is not an opposition at all.

**The physical basis of the division of labour:**

| Dimension | JavaScript | WebAssembly |
|---|---|---|
| Types | Dynamic, inferred at runtime | Static, validated at load |
| Memory | Garbage-collected object heap | Manually managed linear memory |
| Startup | Parse → interpret → JIT warm-up (performance climbs with call count) | Parse → compile directly (performance is stable from the first call) |
| Performance predictability | Poor (deoptimization, GC pauses, hidden-class transitions all cause spikes) | **Good** (no GC pauses, no deoptimization; suited to real-time) |
| DOM / browser APIs | Native, zero cost | Must bridge through JS |
| Strings and objects | Extremely strong | Extremely weak (manual encode/decode) |
| Suited to | UI interaction, event handling, business logic, data assembly | 3D rendering, audio/video codecs, cryptography, large matrix math, parsers |

**"Performance predictability" is worth more than "average performance."** This is decisive in games, audio and real-time interaction. JavaScript's average performance is in fact very good, but it will **occasionally** stall for 30 ms on a GC pause or a deoptimization — and in a game loop budgeted at 16.6 ms per frame, that is a visible dropped frame. Wasm's performance curve is flat. **Running Wasm inside an AudioWorklet has become industry practice precisely because the audio thread cannot tolerate a single unpredictable pause.**

**When plain JS is actually faster:**

- The workload is smaller than the boundary overhead (computing one pixel at a time, comparing one string).
- Heavy string processing — V8's string implementation (ropes, interning, shared slices) is extremely optimized, while Wasm pays the encode/decode tax.
- Heavy DOM work — every operation detours through JS; Wasm is a pure loss.
- Cold-start-sensitive scenarios with modest computation — that 500 KB module's download and compilation will never be earned back.

> ⚠️ Authenticity Caveat
> The common claim is "Wasm is 10–30× faster than JavaScript." Those multiples **hold only on benchmarks of a particular shape** (dense numeric loops with no GC pressure, compared against an unoptimized JS implementation). When V8 is fully warmed up and the code is a type-stable monomorphic hot loop, **JavaScript can approach Wasm, with the gap often inside 1–2×.** Every "N times faster" figure in the 101 cases of Appendices D–F should be read by this standard: **trust the direction, doubt the multiplier.**

> 💡 A Word to the Wise
> **In engineering, "better on average" frequently loses to "better in the worst case."** JavaScript's average performance is not far behind Wasm, but its P99 gets punched through by GC; Wasm's average may not crush anything, but its P99 is flat. Users never experience the average — **they experience that one stutter, that one audio pop, that one dropped frame.** This principle is called tail latency, and it explains a pile of apparently irrational technical choices: why trading systems prefer languages without GC, why databases sacrifice throughput for P99, why real-time audio uses Wasm even when JS is already fast enough. **When making a selection, first establish whether this system is judged by its average or by its worst case — those two want completely different technologies.**

## Scenario 2: Cloud native — Wasm + WASI vs. Docker / containers

**Background.** This comparison is most often exaggerated into "Wasm will replace Docker," and the truth is far more interesting — **they are not isolating the same layer at all.**

**The layer difference in the isolation boundary** (the key to everything else):

```
Container (OCI / Docker):
  ┌───────────────────────────────────────┐
  │ your program + a full userland          │  ← isolates "an entire OS distribution"
  │ (glibc, coreutils, /etc, package mgr…)  │
  ├───────────────────────────────────────┤
  │ namespaces + cgroups + seccomp + caps   │  ← isolation provided by the Linux kernel
  ├───────────────────────────────────────┤
  │           shared host kernel            │  ← attack surface: the whole syscall interface
  └───────────────────────────────────────┘

Wasm + WASI:
  ┌───────────────────────────────────────┐
  │ your program (compiled to Wasm)         │  ← isolates "a single application"
  ├───────────────────────────────────────┤
  │ Wasm runtime (memory-safe VM)           │  ← isolation from the type system and validator
  ├───────────────────────────────────────┤
  │ WASI capability interface (only what    │  ← attack surface: the few functions you import
  │ the host explicitly granted)            │
  └───────────────────────────────────────┘
```

**Item by item:**

| Dimension | Container | Wasm + WASI | Winner |
|---|---|---|---|
| Cold start | Tens of ms to seconds | Microseconds to milliseconds | **Wasm, by orders of magnitude** |
| Image/module size | Tens to hundreds of MB | Tens of KB to a few MB | **Wasm** |
| Memory footprint | Tens of MB per instance | Hundreds of KB to a few MB per instance | **Wasm** |
| Cross-architecture | One image per architecture | A single `.wasm` everywhere | **Wasm** |
| Attack surface | The whole syscall interface | The handful of functions explicitly imported | **Wasm** (though the runtime itself can have holes) |
| Can run existing software | **Any Linux binary** | Only what has been recompiled | **Container, decisively** |
| Ecosystem maturity | Over a decade, complete tooling | Still evolving (WASI 0.2 migration) | **Container** |
| Threads / networking | Complete | Being filled in | **Container** |
| Observability | Complete (strace, perf, eBPF…) | Comparatively poor | **Container** |

**How to read "100× faster."** If it means **cold start**, that order of magnitude is credible (microseconds vs. tens of milliseconds). If it means **execution performance**, it is wrong — **Wasm's execution performance is below native code inside a container**, because a container runs a genuine native binary while Wasm is a compiled intermediate representation.

> ⚠️ Authenticity Caveat
> "Wasm is 100× faster than Docker and extremely light" is common in marketing material. **The accurate statement is: Wasm's cold start and memory footprint are one to several orders of magnitude better than containers, but steady-state execution performance is usually below native code inside a container.** That difference decides the applicable scenarios: **Wasm wins on "many, short-lived, bursty" functions (serverless, edge, multi-tenant plugins); containers win on "long-running services that depend on the existing ecosystem."** Treating them as mutually exclusive substitutes is the most common misuse of this technology.

**Wasm's genuinely killer scenarios on the backend** are the things containers **cannot** do:

1. **Multi-tenant plugin systems.** Letting customers upload their own code to run inside your service. With containers you need one container per customer (heavy, slow, expensive); with Wasm you can run a thousand mutually untrusted modules in a single process, each with its own linear memory and capability boundary. Envoy, Istio, Shopify Functions and Redpanda's data transforms all take this road.
2. **Extreme cold-start requirements at the edge.** Edge nodes have no local traffic; nearly every request is a cold start. Tens of milliseconds is unacceptable there.
3. **Compile once, deploy everywhere.** The same `.wasm` on x86 servers, ARM edge devices and in browsers.

> 🔍 Deeper Commentary — "can't run existing binaries" is the deciding move
> In the table Wasm wins seven and loses four, which looks like a clear advantage. But one of those four outweighs all the rest: **Wasm can only run things that have been recompiled.** In practice that means — **every Python script, Java service, Node.js application and that ancestral PHP nobody dares touch, accumulated over the last decade at your company, cannot move across unless someone rewrites or at minimum recompiles them.** The container's historic victory was never about technical elegance (cgroups plus namespaces are not elegant); it was that it offered a **zero-rewrite migration path**: `FROM ubuntu:22.04`, pack your mess in unchanged, ship to Kubernetes tomorrow. That is why the "Wasm replaces Docker" narrative has been shouted from 2019 to 2026 while the market share gap remains enormous. **Adoption curves are decided by migration cost, not by technical superiority.** And that also predicts Wasm's real growth path on the backend: it will not take market share from existing services; it will grow its own territory **in the places containers are structurally unsuited to** (multi-tenant plugins, extreme cold start, cross-architecture edge) and then expand toward the middle. **When judging an infrastructure technology's future, don't look at whether it can beat the incumbent; look at whether there is a place the incumbent structurally cannot enter.**

## Scenario 3: The edge — Wasm vs. V8 Isolates

**Background.** This is the closest-quarters of the six, because the opponent uses the same engine.

**What a V8 Isolate is.** The core idea behind Cloudflare Workers — instead of a process or container per tenant, open an `Isolate` (V8's isolated execution environment, each with its own heap and global object) inside **one V8 process**. Cold start drops below 5 ms and the memory footprint is a few MB.

**The comparison:**

| Dimension | V8 Isolates | Wasm modules |
|---|---|---|
| Cold start | Extremely fast (~5 ms or better) | Extremely fast (microseconds to milliseconds) |
| Languages | **JS / TypeScript only** | Dozens that compile to Wasm |
| Memory footprint | Lower (shares V8's builtins and code) | Each instance needs its own linear memory |
| Isolation strength | Depends on V8's own security (V8 has a long CVE history) | An additional specification-level type and memory isolation layer |
| Ecosystem | npm, enormous | Each language's own; cross-language integration still developing |

**The reality is that they have already merged.** Cloudflare Workers **supports** executing Wasm modules inside an Isolate; Fastly's Compute@Edge is built directly on Wasm (the Lucet/Wasmtime lineage). **So the right question is not "which one" but "what language is your logic written in"** — JS/TS goes through an Isolate, Rust/Go/C++ compiles to Wasm and gets embedded.

> 💡 A Word to the Wise
> **When two technologies coexist long-term and nest inside one another, they are not solving the same problem — the market merely put them on the same shelf at first.** Isolates solve "how to multi-tenant safely inside one JS engine"; Wasm solves "how to let non-JS languages run safely anywhere." They look like competitors because they happen to collide in the specific product shape called edge serverless. **Whenever you see two technologies compared, go find the thing each does best that the other cannot do at all — that thing is their real definition.** Comparing two differently defined things with one set of metrics is the most common logical error in technical evaluation.

## Scenario 4: The blockchain — eWasm vs. EVM

**Background.** This is the most political of the six, because it involves not just technology but hundreds of billions of dollars of assets already locked on-chain.

**The EVM's problems:**

- **256-bit words.** The EVM's native word is 256 bits because it was designed around cryptographic hashing. But that means **every addition must be emulated as several operations on a 64-bit physical CPU** — an enormous waste for ordinary, non-cryptographic computation.
- **A closed toolchain.** You essentially write Solidity or Vyper, and the compiler, debugger and analyzer all have to be built from scratch.
- **Low execution performance.** It was designed for verifiable determinism, not speed.

**Wasm's advantages as a contract VM:**

- **A mature multi-language toolchain.** Rust, C++ and AssemblyScript can all write contracts, reusing existing compiler optimizations, debuggers and fuzzing tools.
- **One to several orders of magnitude better execution efficiency** (for non-cryptographic computation).
- **The specification has already been validated by four browser implementations**, so you needn't maintain a VM specification yourself.

**Wasm's fatal difficulties on-chain** (usually omitted from marketing material):

1. **Determinism.** A blockchain requires every node to compute **exactly the same** result for the same transaction. Wasm's specification has several **non-deterministic** corners: NaN bit patterns in floating point may differ across implementations, some SIMD operations differ, and when `memory.grow` fails depends on host resources. **On-chain Wasm must first define a "deterministic subset"** (usually by banning floating point outright), and that is the first engineering task of every Wasm chain.
2. **Metering (gas).** Every EVM instruction has a published gas price. Wasm has no such concept and must implement it through **instrumentation** — automatically inserting counting code into the compiled module — which costs anywhere from 10% to 50% in performance, eating directly into the speed advantage.
3. **Ecosystem inertia.** The assets locked, contracts deployed and audited libraries on Ethereum mainnet are all EVM bytecode. **The coordination cost of migration is astronomical.**

**Where it actually went.** eWasm as a replacement execution layer for Ethereum 1.x has effectively been shelved (Ethereum's roadmap turned toward EOF and other directions); but Wasm succeeded enormously on **other chains** — Polkadot's runtime *is* Wasm (hot-upgradeable), and NEAR, Cosmos's CosmWasm and the Internet Computer all use Wasm as their execution environment.

> 🔍 Deeper Commentary — metering exposes the fundamental tension of using a general VM for a specialized purpose
> The difficulty of implementing gas metering is not an engineering detail; it is the symptom of a paradigm clash, and it is worth unpacking. **The EVM wrote "how much does each instruction cost" into its specification from day one**, because its entire purpose is to execute untrusted code in an untrusted environment and be able to stop and charge for it. **Wasm excluded metering from its specification from day one**, because its purpose is to execute already-validated safe code as fast as possible, and any metering is pure overhead. So anyone using Wasm as a contract VM must instrument the compiled module — with three knock-on consequences: **first**, the instrumented module is not the same thing as the original, and your optimizer may optimize the instrumentation away, so metering and optimization fight each other; **second**, instrumentation granularity trades accuracy against overhead (per instruction is too expensive; once per basic block leaves room for infinite-loop exploits); **third**, different chains instrument differently, so "the same Wasm consumes different gas on different chains," discounting the portability promise. **The general lesson: when you take a general substrate designed for speed and use it to solve a problem that requires measurability, interruptibility and auditability, the layer you add on top tends to consume the very reason you chose it.** The question to ask when selecting is not "is this substrate fast enough" but — **will the things I have to bolt on turn it back into a mediocre solution?**

## Scenario 5: Dense computation — Wasm vs. WebGPU

**Background.** This is the newest of the six opponents and the easiest to misjudge — because only in 2026 did it genuinely become an option everyone can use.

**WebGPU's status changed.** It achieved **full shipping across mainstream browsers in January 2026** (Chrome since 113; Firefox since 141 on Windows, extended in 145 to Apple Silicon macOS; Safari 26.0 covering macOS/iOS/iPadOS/visionOS). **That means "dense computation in the browser" has, for the first time, two options worth seriously considering rather than one.**

**Their essential difference is not speed; it is the shape of the parallelism:**

| | **Wasm (+SIMD +threads)** | **WebGPU (compute shaders)** |
|---|---|---|
| Hardware | CPU | **GPU** |
| Parallel model | A few coarse-grained threads (≈ core count) | **Thousands of fine-grained threads** (SIMT) |
| Vector width | **Fixed 128 bits** | Determined by hardware, far wider |
| Branch divergence | Cheap | **Expensive** (different branches in one warp serialize) |
| Random memory access | Cheap (large caches) | **Expensive** (needs coalesced access to be fast) |
| Recursion / complex control flow | Natural | **WGSL has no recursion**; dynamic control flow is constrained |
| Precision | Full `f32`/`f64` | Mostly `f32`; `f64` support limited or absent |
| Startup latency | Milliseconds | **Must acquire adapter/device, compile shaders, build pipelines** |
| Reading results back | Zero copy (same memory) | **Must `mapAsync` back, with appreciable latency** |
| Availability | Nearly 100% | ~70%, with large variation on mobile and across drivers |
| Debugging | Hard | **Harder** |

**So the division of labour is clear:**

```
Is your computation "the same operation applied to millions of independent elements"?
├─ Yes, and the data can stay on the GPU across several steps
│    → WebGPU (matrix multiply, convolution, image filtering, particles, ray tracing)
│
├─ Yes, but you immediately need the result back on the CPU for something else
│    → ⚠️ Measure the readback latency first — it often eats the time the GPU saved
│
└─ No: complex branching, recursion, random access, or f64 precision required
     → Wasm (parsers, compression, databases, emulators, geometry solvers)
```

**The real-world answer is usually "both"** — and Appendix D's case 4 (ONNX Runtime Web) is the best example: **it maintains a WebGPU backend and a Wasm backend simultaneously**, the former for speed, the latter because it "runs on any device." **Wasm's role here is not competitor; it is the fallback layer.**

> ⚠️ Authenticity Caveat
> A common claim is "WebGPU is 10–100× faster than Wasm." **On suitable workloads that order of magnitude is credible** (large matrix multiplies, convolutions), **but it omits three bills**: **(a)** startup cost — acquiring the device, compiling WGSL, building pipelines, which can dominate for short tasks; **(b)** readback cost — the latency of `mapAsync` bringing results back to the CPU; **(c)** availability cost — you must maintain a Wasm path for devices without WebGPU, so you now maintain two implementations. **"N times faster" describes steady-state throughput; what your users experience is end-to-end time.**

> 💡 A Word to the Wise
> **When two technologies land on the same comparison table, first confirm that their parallelism has the same *grain*.** CPU parallelism is "a few clever workers each doing their own thing"; GPU parallelism is "thousands of workers performing exactly the same motion simultaneously" — **the former is good at judgement, the latter at repetition.** Throw work requiring judgement at a GPU and you get branch divergence; keep purely repetitive work on the CPU and you waste a thousandfold of compute. This principle extends well beyond Wasm and WebGPU: thread pools vs. SIMD, batch vs. stream, microservices vs. monolith — **the real difference in every one of those pairs is how the work is cut apart, not which is faster.** Choosing wrong doesn't cost you a little speed; it means the shape of your work doesn't match the shape of your tool, and no amount of optimization will fix that.

## Scenario 6: The most fundamental opponent — don't build a web app

**Background.** This section asks a question the entire book has presupposed an answer to and never voiced — **should this thing be in a browser at all?**

**Because if it isn't a browser, half of the dozen walls we've discussed simply vanish**: no 4 GiB ceiling, no COOP/COEP, no boundary toll booth, no download-size anxiety, threads available, direct access to the filesystem and hardware, and 100% of native performance instead of 60–90%.

**Three concrete shapes of "not a web app":**

| Shape | What it is | Trade-off against Wasm |
|---|---|---|
| **Ship a native binary** | An ordinary desktop program | Fastest, no constraints; **but zero-install disappears entirely**, and you must build, sign and update per platform |
| **Electron** | Bundles an entire Chromium plus Node.js | Full Node capabilities and filesystem; **at the cost of 100+ MB per app and a substantial memory footprint** |
| **Tauri** | Renders the frontend in the **system's built-in WebView**, with a native Rust backend | Artefacts of a few MB; the frontend is still web technology, **but heavy computation runs as native Rust — no need to compile to Wasm, so no 4 GiB ceiling, no boundary tax, and threads are available** |

**The Tauri row deserves a pause**, because it reveals something: **many people use Wasm in order to "write UI with web technology," not in order to "run in a browser."** If your users are going to install an app anyway, compiling heavy computation to Wasm is a **pure loss** — you pay every cost of Wasm and receive none of its one benefit (zero install, no updates, a single cross-platform artefact).

**Which leaves exactly one criterion:**

> **Ask what "zero install" is worth to this product.**
>
> - **Worth a lot** (a one-off tool, share-a-link-and-it-works, enterprises that forbid installs, needs to be indexed by search engines, must run inside someone else's site) → **browser plus Wasm; every wall in this book is a necessary evil.**
> - **Not worth much** (users will install anyway, long sessions, heavy local file access, needs background execution) → **Tauri or native. You will save yourself all four chapters of Part II.**

**Two common misjudgements:**

1. **"We're writing Rust anyway, so compile to Wasm and cover both."** It sounds elegant; in practice the Wasm build is dragged down by 4 GiB, the boundary tax and the absence of threads, while the native build is dragged by none of them. **Sharing the core logic is right, but accept that the two sides have different capability boundaries.**
2. **"Electron is too fat, so I'll use Wasm."** Those two are not opposites — Electron's substitute is Tauri, not Wasm. **If what you are comparing is app size, Tauri is the answer.**

> 🔍 Deeper Commentary — laid side by side, the six opponents reveal one clear definition
> Spread this chapter's six competitions out and Wasm's position becomes unmistakable — and it differs from most people's intuition. **Wasm is not "a faster way to execute"; it is the general solution to "safely executing your code on someone else's territory."** Every one of the six confirms it: **against JavaScript** it wins because "you can bring your existing C++ assets with you," not because it is fast; **against containers** it wins because "a thousand mutually untrusted tenants in one process," not on performance; **against V8 Isolates** it wins because "you aren't limited to JS"; **against the EVM** it wins because "the toolchain already exists"; **against WebGPU** it does not compete at all — it is the fallback layer that "runs on any device"; **against native** it wins on zero install and loses on everything else.
> **String the six together and the definition surfaces: Wasm is a portable trust boundary.** All of its advantages come from "the host can safely execute it," and all of its limits come from the same source. So the question when selecting is not "is Wasm fast" but — **whose territory does this code need to run on, and why should that landlord trust me?** If the answer is "on my own machine," you probably don't need Wasm; if the answer is "in the browsers of millions of strangers," "next to other tenants in the same process," "on a chain where every node must compute the same result" — **there is no second option.**

## Chapter Summary

- **Six battlefields, six ways to win**: divides labour with JS in the browser (Wasm computes, JS draws); competes off-axis with containers in cloud native (wins cold start and multi-tenancy, loses the existing ecosystem); has already merged with V8 Isolates at the edge (Isolates run JS, Wasm runs everything else); wins on performance on-chain but is stuck on determinism and ecosystem inertia; **divides labour rather than competes with WebGPU** in dense computation; and against **native** it wins exactly one thing — **zero install**.
- Against JS: **"performance predictability" is worth more than "average performance"** — Wasm's curve is flat, decisive in audio and game loops. But small workloads, string-heavy and DOM-heavy work are **faster in plain JS**.
- Against containers: **Wasm wins cold start and footprint by one to several orders of magnitude, but steady-state execution is below native code inside a container.** And "can't run existing binaries" outweighs every other advantage — **adoption curves are decided by migration cost, not technical superiority** (see the 🔍 in Scenario 2).
- Against the EVM: Wasm's speed and toolchain advantages are real, but **gas metering must be bolted on through instrumentation, and instrumentation eats part of the speed advantage** — the fundamental tension of using a general substrate for a specialized purpose (see the 🔍 in Scenario 4).
- Against WebGPU: **their parallelism has a different grain** — CPU is "a few clever workers each doing their own thing"; GPU is "thousands doing exactly the same motion." **In browser AI inference Wasm's role is the fallback layer, not the competitor** (ONNX Runtime Web maintaining both backends is the proof). Note that "10–100× faster" omits startup, readback and availability (see the ⚠️ in Scenario 5).
- Against native: **one criterion only — what is "zero install" worth to this product.** If not much, Tauri or native saves you all four chapters of Part II. **Note that Electron's substitute is Tauri, not Wasm.**
- Every "N times faster" claim should be read by **the shape of the comparison group**, including the hundred and one cases in this book's appendices (see the ⚠️ in Scenario 1).
- **String the six together and the definition surfaces: Wasm is a portable trust boundary.** Every advantage comes from "the host can safely execute it," and every limit from the same source. The question is not "is Wasm fast" but — **whose territory does this code need to run on, and why should that landlord trust me?** (see the 🔍 in Scenario 6).

Part I ends here — the machine's origins, physical laws, capability boundaries and opponents are all accounted for. **Part II does something that looks impossible on paper: move this machine somewhere that gives you no HTTP headers, no listening ports, and not one line of backend code.** Turn to Chapter 5.

---



# Part II: Building a Machine on a Static Page

# Chapter 5: Running a Machine on a Static Page — The COOP/COEP Wall, and One Ingenious Way Around It

> **"Are GitHub Pages sites static? Can you run a server on them?"**
> This is where the investigation turned. The answer: the site itself is not static at all, but no, you genuinely cannot run a traditional server on it. **And Wasm makes a third answer possible — you can move the server into the user's browser.**

## Scenario 1: First, separate three things — GitHub the site, GitHub Pages, and "running a server"

**Background.** These three get conflated constantly, producing a very common misconception: "GitHub is static."

**GitHub the site: not static at all.** When you browse a repository, open an issue or submit a pull request, you are looking at a highly dynamic page: heavy JavaScript on the front end (React components) handling live interaction, and GitHub's own large server fleet behind it (built mainly on Ruby on Rails) handling requests, databases and the filesystem.

**GitHub Pages: hosts static files only.** It serves the HTML, CSS, JS, images and `.wasm` in your repo through a CDN, unchanged.

- ❌ **Cannot**: run a Node.js / Django / Go backend process, listen on a port, connect to a database, run scheduled jobs.
- ⭕ **Can**: host a single-page app (React / Vue / Svelte), and **arbitrarily complex frontend computation driven by WebAssembly**.

**The other two places GitHub lets you "run things"** (worth clarifying, because people reach for them as substitutes):

| Service | What it can run | Hard limits |
|---|---|---|
| **GitHub Pages** | Static files plus everything browser-side (including Wasm) | No custom HTTP headers, no backend, no database |
| **GitHub Actions** | Any process inside a VM (Linux/Windows/macOS), including databases and servers | **Built for testing and packaging**: a single run has a time limit (commonly 6 hours per job on public repositories) and the VM is destroyed afterward — **it cannot be a permanent web host** |
| **GitHub Codespaces** | A complete cloud development container; you can `npm start` or `python manage.py runserver`, with automatic port forwarding to a temporary URL | For development; idles and sleeps — **not a production host** |

**The key connection**: if you want something that behaves like a backend inside a "static hosting environment," **Wasm is one of the answers.** Projects already exist (StackBlitz's **WebContainers**, for instance) that use Wasm to compile and run a substantial portion of the Node.js runtime and OS kernel inside the browser — the user opens a page, and the browser uses Wasm to "simulate" a backend server on the front end, needing no cloud host at all.

**And if you want to see this taken all the way**: **FluffOS** — a still-maintained LPMud driver (a modern fork of MudOS, written in C++) — has made **WebAssembly one of its official build targets**. The official README's words are "**the whole driver runs in a browser page — compiler, VM, efuns, telnet.**" Its mudlib (the source of an entire game world) is packed into a static bundle by Emscripten's `file_packager`, **requiring no server**. Which means a multiplayer game server with a heartbeat, timers, persistent world state, and a compiler for user code at runtime becomes three static files you can drop onto a CDN. **Full teardown in Appendix L.**

> ⚠️ Authenticity Caveat
> "WebContainers runs Node.js in the browser" is real and verifiable (StackBlitz's public engineering posts explain it in detail). But understand its boundary precisely: **it is not Node.js's C++ source compiled unchanged into Wasm**; it is a reimplemented runtime that executes on Wasm and is API-compatible with Node.js, using a Service Worker to intercept network requests and simulate server behaviour. **The precise version of "running a real server in the browser" is: simulating, inside the browser, a server whose behaviour is consistent for this page.** Other people on the open internet **cannot** reach that "server" by URL — not without P2P traversal on top.

> 💡 A Word to the Wise
> **"Static" and "dynamic" were never properties of a web page; they are properties of *which end the computation happens on*.** The same HTML file is static when it sits on a CDN, but the Wasm module it pulls up can finish a video transcode, run a SQL query, push a round of neural-network inference on the client. The computation did not decrease — **it merely changed who pays for it**, from your server bill to the user's CPU cycles and battery. The commercial implication far outweighs the technical one: **when an expensive cost can be transferred to users painlessly, and users feel no pain, that cost will be transferred.** Ad SDKs do it, cryptocurrency mining scripts do it, and Wasm lets legitimate heavy computation do it too. So the next time you see the words "zero server cost," get in the habit of appending the second half: **the cost did not disappear; it became someone else's electricity bill.**

## Scenario 2: The wall 90% of people hit — COOP / COEP

**Background.** Your FFmpeg.wasm runs beautifully under `python -m http.server` locally, and the moment you push it to GitHub Pages:

```
ReferenceError: SharedArrayBuffer is not defined
```

or

```
Uncaught DOMException: Failed to construct 'Worker': ... blocked by cross-origin isolation
```

**The full causal chain** (the key to everything; the fuse laid in Chapter 3 detonates here):

```
Spectre (2018, CPU speculative-execution side channel)
   ↓ the attack needs a high-resolution timer to measure cache timing
SharedArrayBuffer + Atomics can construct a nanosecond timer
   ↓ so browsers disabled SharedArrayBuffer by default across the board
   ↓ later restored, with a condition: the page must be "cross-origin isolated"
Cross-origin isolation requires the server to return two HTTP headers
   ↓
Cross-Origin-Opener-Policy: same-origin      ← severs window references from other origins
Cross-Origin-Embedder-Policy: require-corp   ← every cross-origin subresource must opt in
   ↓ when both hold, self.crossOriginIsolated === true
   ↓ only then does SharedArrayBuffer exist
   ↓ and Wasm multithreading depends on SharedArrayBuffer
   ↓
❌ GitHub Pages does not allow custom HTTP headers
   ↓
every multithreaded Wasm project (multithreaded FFmpeg.wasm,
parallel OpenCV, Emscripten pthread, Rust rayon-wasm…)
simply cannot run on GitHub Pages
```

**What each header defends against:**

- `Cross-Origin-Opener-Policy: same-origin` (COOP): severs the `window.opener` reference chain across origins, preventing windows from other origins from sharing an OS process with you (same process means same address space, which is Spectre's opening to read your memory).
- `Cross-Origin-Embedder-Policy: require-corp` (COEP): requires **every** cross-origin resource the page loads (images, scripts, iframes, fonts) to explicitly consent to being embedded — via a `Cross-Origin-Resource-Policy: cross-origin` response header, or through CORS. **Anything that hasn't opted in is blocked.**

**COEP's collateral damage is the painful part.** The moment you turn on cross-origin isolation, **every third-party resource without CORP/CORS headers breaks** — Google Fonts, CDN images, YouTube embeds, ads, analytics scripts. That is why, even if you *can* set headers (self-hosted Nginx, or Cloudflare Pages' `_headers`), enabling isolation is still a decision with a price.

> 💡 **The solution: `coi-serviceworker`**
> The open-source community produced an ingenious way around this. You include a script called **`coi-serviceworker`**, which uses the browser's **Service Worker** to intercept, **on the front end**, all requests the page itself makes, and "adds" the two headers to the responses.
> How: drop `coi-serviceworker.js` in the root of your GitHub Pages site and include it at the very top of `index.html`'s `<head>`:
> ```html
> <script src="coi-serviceworker.js"></script>
> ```
> On first load the Service Worker has not taken control yet, so the script reloads the page once; on the second load every response carries COOP/COEP, `crossOriginIsolated` becomes `true`, and `SharedArrayBuffer` appears.

**Why it is legitimate, and why it is safe.** A Service Worker is a proxy layer **registered by the same-origin page itself**, able to intercept only requests within its own scope. It does not bypass the browser's security model — **it declares, within the page's own authority, "I voluntarily enter the isolated state."** The browser accepts that declaration, because the cost of isolation (losing cross-origin resources) is borne by that same page.

**Its four costs** (know them, or you will be caught in production):

1. **One extra page load** (the Service Worker only takes effect after registration), so the first experience flickers.
2. **Requires HTTPS** (GitHub Pages has it by default; `localhost` also counts as a secure context).
3. **Cross-origin resources without CORP are still blocked** — identical to genuinely setting the headers; a Service Worker can only modify responses it can see.
4. **Service Workers have their own caching and update semantics**, so deploying a new version can leave users on the old one; you need to handle `skipWaiting` / `clients.claim`.

**When you don't need any of this.** **If your Wasm is single-threaded, you do not need COOP/COEP at all.** Most projects (`wasm-pack`'s default output, most parsers and compilers) are single-threaded and just work when pushed to GitHub Pages. **Confirm you genuinely need multithreading before paying this price.**

### Two options that cost less

**Option one: `COEP: credentialless` instead of `require-corp`.**

`require-corp` demands that every cross-origin subresource **actively opt in** to being embedded (by returning `Cross-Origin-Resource-Policy`) — and you have no control over whether third parties do. `credentialless` takes a different approach: **allow cross-origin resources that haven't opted in, but request them without credentials** (no cookies, no client certificates).

```http
Cross-Origin-Opener-Policy: same-origin
Cross-Origin-Embedder-Policy: credentialless    ← far gentler than require-corp
```

**It still makes `crossOriginIsolated` true**, without killing off every public image and font that simply never set CORP. The cost: **cross-origin resources that require cookies become unreachable** (the request carries no credentials), and browser support is less uniform than `require-corp`. **Try `credentialless` first; fall back to `require-corp`.**

**Option two: switch to a backend that doesn't need `SharedArrayBuffer`.**

This one is routinely undervalued. Take persistent SQLite: the official SQLite-Wasm ships **two** OPFS VFS implementations. The first-generation `opfs` needs `SharedArrayBuffer` (and therefore isolation), while **`opfs-sahpool` needs no COOP/COEP at all and is the fastest option in the official documentation** (details in Chapter 7).

> 💡 **Plenty of teams have wrestled with `SharedArrayBuffer` and isolation for two weeks when the thing they wanted had a path that never needed it. Spend ten minutes reading whether your library has a second backend before you start.**

### And one more wall you may not have hit yet, but will: CSP

**If your site sets a Content-Security-Policy, Wasm compilation is blocked outright.**

The reason: `WebAssembly.compile()` / `instantiate()` / `compileStreaming()` count as **dynamic code generation** in CSP's eyes, in the same category as `eval()`. Early on the only workaround was enabling `'unsafe-eval'` — **which is handing over your entire XSS defence.**

**The current answer is a dedicated keyword:**

```http
Content-Security-Policy: script-src 'self' 'wasm-unsafe-eval'
```

`'wasm-unsafe-eval'` **permits WebAssembly compilation only, and does not permit `eval()` or `new Function()`.** Support: **Chrome 97+, Firefox 102+, Safari 16+** (Chrome extensions can use it in the manifest's `content_security_policy` from v103).

**This bites in three situations in particular**: **(a)** your Wasm is embedded in someone else's iframe whose CSP doesn't allow it; **(b)** browser extensions; **(c)** corporate portals with a uniform CSP policy. **The symptom is a CSP violation error, not a Wasm error — which is why it so easily sends you looking in the wrong place.**

> 🔍 Deeper Commentary — `coi-serviceworker` is a "legitimate protocol loophole," and such things deserve wariness about their lifespan
> This workaround stands on a subtle premise in the security model: **the browser treats "the page voluntarily entering isolation" and "the server requiring the page to enter isolation" as equivalent in security terms**, because the thing isolation protects is that page itself. The reasoning is sound, so `coi-serviceworker` is not an exploit; it is a **correct use of the specification.** But two things deserve long-term wariness. **First, it depends on a combined behaviour that was never explicitly promised.** No line of specification says "COOP/COEP headers synthesized by a Service Worker must be treated as equivalent to those emitted by the server" — it is a natural inference each implementation drew. Any technique that relies on inferred behaviour at the intersection of several specifications carries the risk of being tightened in a future version. **Second, and more fundamentally: it reveals a structural fact — free static hosting gives you a CDN, gives you HTTPS, gives you version control, and gives you everything except control over response headers; and the Web's advanced capabilities (cross-origin isolation, CSP, Permissions Policy, Trusted Types, even some origin trials) are all fastened to response headers.** So the real lesson is not "learn to use coi-serviceworker" but — **when you choose a free platform, what you give up is often not what you need today, but the control you will need in two years.** A free platform's ceiling is always discovered at the moment you grow to a certain size, by which point the migration cost is already high. This resurfaces in another form in Chapters 11 and 12 on moats: **control is the only genuinely scarce thing.**

## Scenario 3: The complete deployment path, from `cargo` to that `github.io` URL

**Background.** Collapsing the theory into a path you can follow. Using the mainstream **Rust + WebAssembly** as the example.

**Step 1: build locally**

Use `wasm-pack` to compile Rust into web-targeted Wasm and JS glue:

```bash
wasm-pack build --target web
```

This produces a `pkg/` directory containing the `.wasm` and the `.js` glue.

**Choose `--target` correctly** (the most commonly misconfigured thing for newcomers):

| target | Output shape | For |
|---|---|---|
| `web` | An ES module, usable directly via `<script type="module">` | **The correct answer for static GitHub Pages deployment** |
| `bundler` | A module for webpack/rollup/vite (with `import` syntax) | Projects with a bundler |
| `nodejs` | CommonJS, for Node.js | Server side |
| `no-modules` | A traditional script hanging off a global | Old environments, or `importScripts` inside a Worker |

**Step 2: write the front-end HTML**

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <!-- Only needed if you use multithreading, and it must come first -->
  <script src="coi-serviceworker.js"></script>
  <title>Wasm on GitHub Pages</title>
</head>
<body>
  <script type="module">
    import init, { greet } from './pkg/your_project.js';
    async function run() {
      await init();              // initialize the Wasm module (uses instantiateStreaming internally)
      greet("GitHub Pages");     // call a function inside Wasm
    }
    run();
  </script>
</body>
</html>
```

**Step 3: push and enable Pages**

1. Push the project (with `index.html` and `pkg/`) to a GitHub repository.
2. Go to **Settings → Pages**.
3. Under **Build and deployment**, publish from your branch (`main` or `gh-pages`).
4. Wait a few minutes and visit `https://<account>.github.io/<project>/`.

**Four traps you will definitely hit** (ordered by how often they catch people):

1. **`.gitignore` excluded `pkg/`.** Many Rust templates ignore the `pkg/` directory `wasm-pack` produces, so what you pushed is a site with no `.wasm`. **Fix**: either add `pkg/` to version control, or build in CI with GitHub Actions (below).
2. **Paths are relative, and project pages live under a subpath.** The subpath in `https://user.github.io/repo/` makes absolute paths like `/pkg/xxx.js` 404. **Fix**: use relative paths, `./pkg/xxx.js`.
3. **Jekyll ate the underscore-prefixed folder.** GitHub Pages runs Jekyll by default, which ignores files and folders beginning with `_`. **Fix**: put an empty `.nojekyll` file at the root.
4. **You forgot `await init()`.** Wasm loading is asynchronous; calling any exported function before initialization completes will blow up.

**Building and deploying automatically with GitHub Actions** (much cleaner than committing `pkg/` by hand):

```yaml
name: Deploy Wasm to Pages
on:
  push:
    branches: [main]
permissions:
  contents: read
  pages: write
  id-token: write
jobs:
  build-deploy:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with:
          targets: wasm32-unknown-unknown
      - name: Install wasm-pack
        run: curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh
      - name: Build
        run: wasm-pack build --target web --release
      - name: Optimize
        run: |
          npm install -g binaryen
          wasm-opt -Oz --strip-debug pkg/*_bg.wasm -o pkg/tmp.wasm
          mv pkg/tmp.wasm pkg/$(ls pkg | grep _bg.wasm)
      - name: Assemble site
        run: |
          mkdir -p dist && cp index.html dist/
          cp -r pkg dist/ && touch dist/.nojekyll
      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist
      - uses: actions/deploy-pages@v4
```

> 💡 A Word to the Wise
> **The difficulty of a deployment path lies not in how many steps it has, but in how far the error message sits from the actual cause.** Each of those four traps has a lying error message: `pkg/` not pushed gives you a 404; absolute paths give you a 404; Jekyll eating your folder gives you — **still a 404**. Three completely different causes, one symptom. That is why "I followed the tutorial and it doesn't work" is the most common beginner frustration — **tutorials describe the happy path, while in reality you spend 90% of your time interpreting an error message pointing the wrong way.** Which means the genuinely valuable document is not a step list but a **symptom-to-cause table.** The same holds when you write your own tools, libraries and error messages: **a good error message is worth ten pages of tutorial.**

## Scenario 4: The four classic shapes of "what are people running up there"

**Background.** Before diving into a hundred and one cases, look at the four most typical shapes — the ones that best explain *why* anyone would do this.

**Shape one: shift the server's work onto the user — in-browser video editing (FFmpeg.wasm)**

Compile the C-language FFmpeg toolkit into Wasm. The user drags a video into a page on GitHub Pages, and **the transcode happens on the user's own CPU**, consuming none of your bandwidth.

- **The value is not speed; it's not paying.** A cloud transcoding service (something like AWS MediaConvert) bills by the minute and eats enormous upload bandwidth; FFmpeg.wasm's marginal cost is zero.
- **A privacy dividend comes along for free.** The user's video never leaves their computer. For personal video, medical imaging or internal corporate material, that argument is more persuasive than performance.

**Shape two: bring the dead back — retro game emulators in the browser**

Many Game Boy, NES and PS1 emulators written in C++ or Rust are compiled to Wasm, hosted on GitHub Pages, playable the moment you open the page.

- **Why Wasm is decisive**: an emulator needs to simulate CPU cycles **clock-accurately.** JavaScript's timers are imprecise and garbage collection pauses at random, producing audio/video desync and pops. Wasm's performance curve is flat — exactly what an emulator wants.

**Shape three: push AI to the edge — in-browser inference (ONNX Runtime Web)**

Load a lightweight model (object detection, face recognition) on GitHub Pages and run it through Wasm in real time, **saving even the cost of server AI silicon.**

- **Wasm's role here is the fallback.** WebGPU/WebGL backends are faster but depend on drivers and hardware; the Wasm CPU backend runs on anything. **This is a choice about availability, not performance.**

**Shape four: move the entire server in — a MUD driver in the browser (FluffOS × Wasm)**

The first three shapes move a **function** across — feed it input, take its output. **The fourth is different: it moves a server that has a heartbeat, state, and stays alive.**

- **Why it is harder than the first three**: a MUD driver is not a request handler. It has heartbeats, `call_out` timers, persistent world state, multiple concurrent connections — **and it compiles the mudlib's LPC source into bytecode at runtime**, so the compiler and virtual machine have to come into the browser too.
- **How it solves "the browser cannot block"**: the native driver blocks inside libevent's event loop, which is a dead end in a browser. The solution is **handing ownership of the loop to the host** — the page calls the exported `fluffos_tick(now_ms)` on a `setInterval`, which advances the scheduler, drains due events and returns immediately. **The scheduling core is shared with the native build; only who rings the bell differs**, so the mudlib needs no changes at all.
- **The costs**: no sockets (DNS is stubbed to return `127.0.0.1`), no threads, no TLS (the browser owns that), and **writes currently survive only within the page session** (MEMFS; an IDBFS/OPFS overlay is still on the roadmap).

**This shape pushes "static hosting plus Wasm" to its logical conclusion**: an entire persistent multiplayer world becomes three static files. **See Appendix L.**

**What the four shapes have in common** (the skeleton of Part II):

```
    what the server used to do
          ↓
    ┌─────────────────┐
    │ heavy, expensive │  ← the algorithm itself is public (FFmpeg, emulators,
    │ dense computation│     ONNX inference) — no trade secret, only compute cost
    │ with no secrets  │
    └─────────────────┘
          ↓ compiled to Wasm
    ┌─────────────────┐
    │ executed in the  │  ← cost goes to zero, privacy improves, concurrency unlimited
    │ user's browser   │     price: first-load size, device heat, battery
    └─────────────────┘
```

**And conversely, what cannot be pushed out**: anything touching keys, authentication, billing, and any core algorithm whose leak would end the company. **That line is what all four chapters of Part III are about drawing.**

## Chapter Summary

- **GitHub the site is not static; GitHub Pages is.** Pages hosts files only; Actions is a CI environment with a time limit that is destroyed afterward; Codespaces is a development container that sleeps. **None of the three is a permanent host — and Wasm offers a fourth road: move the server into the browser.**
- **COOP/COEP is the number one obstacle to running Wasm on static hosting**, and the full causal chain is: Spectre → `SharedArrayBuffer` disabled → restored but requiring cross-origin isolation → isolation requiring two HTTP headers → **GitHub Pages won't let you set headers** → multithreaded Wasm dies.
- **`coi-serviceworker`** synthesizes those two headers on the front end via a Service Worker — a correct use of the specification, not an exploit. Costs: one extra load, HTTPS required, **cross-origin resources without CORP are still blocked**, and Service Worker update semantics.
- **Two cheaper options**: **`COEP: credentialless`** (allows resources that never opted in, requested without credentials — far gentler than `require-corp`), and **switching to a backend that doesn't need `SharedArrayBuffer`** (SQLite-Wasm's `opfs-sahpool` VFS, which **needs no isolation and is the fastest**, Chapter 7).
- **Confirm you genuinely need multithreading** — most Wasm projects are single-threaded and just work when pushed, without touching any of this.
- **CSP is another wall you will eventually hit**: Wasm compilation counts as dynamic code generation, and **the answer is `script-src 'wasm-unsafe-eval'`** (Chrome 97+ / Firefox 102+ / Safari 16+), which permits Wasm compilation without permitting `eval()`. **The symptom is a CSP violation, not a Wasm error, which sends people looking in the wrong place.**
- The four deployment traps (`pkg/` gitignored, absolute paths 404, Jekyll eating underscore folders, forgetting `await init()`) **all produce a 404 with completely different causes** — the root of "I followed the tutorial and it doesn't work."
- The four classic shapes share one structure: **push "heavy, expensive, algorithmically public" computation into the user's browser.** The fourth shape (FluffOS moving an entire MUD driver into a tab, with `fluffos_tick` handing loop ownership to the host) takes that to its conclusion — **an entire persistent multiplayer world = three static files** (Appendix L). What cannot be pushed out is Part III's subject.
- **The second half of "zero server cost" is always: the cost did not disappear; it became someone else's electricity bill.**

The wall is crossed and the machine is running. So — **what exactly are people running up there?** That list of a hundred and twenty starts getting taken apart in the next chapter. Turn to Chapter 6.

---



# Chapter 6: One Hundred and One Machines — A Panorama of Wasm on Static Pages, and Five Universal Architectures

> The list grew like this: **"Describe 100 classic cases in detail, 500 words each, covering background, mechanism, architecture, pros and cons, competitors and performance."** Then it rolled out five at a time, all the way to 120.
> This chapter does not repeat the per-entry detail in the appendices. It does three things the appendices cannot: **calibrate 120 down to 101 real entries, sort them into ten categories, and extract the five architectures every one of them shares.**

## Scenario 1: A calibration first — 19 of the 120 are duplicates

**Background.** This has to be dealt with before anything else, because it is simultaneously a data-quality problem and a lesson about AI-generated content.

**The calibration result.** Of that "120 cases," **19 are entries that had already appeared, renumbered and retold**:

| Duplicated range | What it repeats | Count |
|---|---|---|
| 26–30 | 21–25 (Graphviz, 7z, Sass, Gnuplot, Esprima) verbatim | 5 |
| 32–35 | 21–24 (the same four) again | 4 |
| 61–65 | 46–50 (libvpx, Hjson, Proj, Brotli, FLAC) verbatim | 5 |
| 66–70 | 36–40 (OpenCV, Solc, Xterm, HarfBuzz, Z-Music) verbatim | 5 |
| **Total** | | **19** |

**120 − 19 = 101 genuinely distinct cases.** Appendices D–F contain those 101, each with an authenticity tag.

**This is worth recording, because it is an observable generation pattern.** From case 55 onward the user began appending "**give me ones that don't repeat what came before**"; from 61 they wrote outright "**you repeated yourself**"; at 71, "**change the application category, you're going in circles**" — and the repetition continued anyway. That exposes a concrete failure mode in long conversations: **without an externally maintained list of what has already been produced, the generator can only deduplicate against conversational context, and once that context exceeds the effective attention window, deduplication fails.** The solution the user eventually landed on was the right one — **not demanding "don't repeat," but specifying new categorical dimensions** ("application categories: networking, games, ERP, servers, open-source ports"; "software engines, physics engines, world engines, LLM engines, graphics engines"). **Constraining the search space works better than demanding memory.**

**A second calibration: which projects are real?** The 101 fall into three authenticity tiers:

| Tier | Criterion | Rough share | Representatives |
|---|---|---|---|
| **🟢 Verifiable** | The project exists, with an official Wasm build or a widely used Wasm port | ~40% | FFmpeg.wasm, v86, Pyodide, DuckDB-Wasm, SQLite-Wasm (official), esbuild-wasm, swc, OpenCV.js, Tesseract.js, solc-js, Stockfish (lichess), Viz.js, sql.js, QuickJS, HarfBuzz.js, Rapier3D, Tantivy, markdown-it/pulldown-cmark, Brotli, Zstd, libp2p, Qiskit, CuraEngine |
| **🟡 Upstream real, Wasm port unverified** | The upstream C/C++/Rust project unquestionably exists, but whether a Wasm build under that name runs on GitHub Pages is unverified | ~40% | GnuPG, GnuTLS, libvlc, libsndfile, libxslt, HTML Tidy, GNU tar, p7zip, Gnuplot, GSL, PROJ, Orekit, minimap2, EPANET, OpenVDB, Project Chrono, AMReX, pagmo, Mitsuba, NimBLE, WireGuard |
| **🔴 Illustrative construction** | The name and description are highly plausible but the project cannot be found; the technical path holds, the specific project is an example | ~20% | `Web-Biconical`, `Espace3D-Wasm`, `Cubism-OLAP-Wasm`, `Hologram3D-Wasm`, `LiFiLight-Wasm`, `SonarICA-Wasm`, `Microfluidic3D-Wasm`, `CivEvo-Core-Wasm`, `FinCopula-Wasm`, `DNAKinetics-Wasm` and others |

> ⚠️ Authenticity Caveat (this book's stance on the 101)
> **You cannot discard the whole list because the third tier exists; nor can you treat it as a project index because the first tier exists.** The right reading is: **treat it as a feasibility map of Wasm across domains, not as a list you can `git clone`.** The technical paths described by tier-three entries almost all hold — compiling C++ acoustic ray tracing, vectorized OLAP aggregation or Copula risk computation to Wasm and running it on a static page has no engineering obstacle; **it is simply that nobody has done it, or has done it under a different name.** So a tier-three entry's value is not "go download it" but "**this road is open; if you need it, you can walk it yourself.**" Every entry in Appendices D–F carries a 🟢🟡🔴 tag.

> 💡 A Word to the Wise
> **When a list grows too long to verify entry by entry, the right response is not verification; it is stratification.** Faced with 120 entries you cannot `git clone` one at a time, verifying each costs an astronomical amount, accepting all of it is negligence, discarding all of it is waste — and stratification preserves the most value for the least cost: **use the verifiable ones as an index, the upstream-real ones as proof of feasibility, and the illustrative ones as design inspiration.** All three have legitimate uses, so long as you don't confuse them. This principle holds anywhere information overloads: reading papers, evaluating vendors, auditing code, looking at any long list an AI produced. **"Is this true?" is often a question with no answer; "how true is it, and true enough for what?" has one.**

## Scenario 2: Ten categories — which domains has Wasm actually taken?

**Background.** Sorting the 101 by "what it replaced" produces a remarkably tidy picture.

| # | Category | Order of magnitude | Representatives | Shared motive |
|---|---|---|---|---|
| 1 | **Audio, video and signals** | ~10 | FFmpeg.wasm, libvpx/dav1d, libvlc, libFLAC, libsndfile, MediaInfo, libmodplug/GME, liquid-dsp | Kill the transcoding server cost + files never leave the device |
| 2 | **Databases and query** | ~8 | DuckDB-Wasm, SQLite-Wasm, jq, Tantivy, Sonic, time-series parsing, OLAP cubes | Give a static page a real query engine |
| 3 | **Language runtimes and toolchains** | ~12 | Pyodide, QuickJS, swc, esbuild, sass/grass, solc, oxc/Esprima, pulldown-cmark, HTML Tidy, libxslt, LISP | Online playgrounds and IDEs with no backend |
| 4 | **Emulators and system ports** | ~8 | v86, Game Boy, OpenTTD, a Minecraft server, a micro HTTP server, GNU tar, p7zip, GnuCash | Make desktop software "open and go" |
| 5 | **Graphics, geometry and CAD** | ~10 | OpenCascade, CuraEngine, Rapier3D, OpenVDB, Mitsuba, procedural planets, 2D nesting, 3D topology optimization | Move industrial C++ geometry kernels onto the web |
| 6 | **Text layout and fonts** | ~4 | HarfBuzz, FontForge, Graphite2, font fuzzing | Fill gaps in native browser layout |
| 7 | **Cryptography and security** | ~7 | GnuPG/Sequoia, GnuTLS, CRYSTALS-Kyber, Circom ZKP, WireGuard, Ghidra decompilation | **Keys never leave the device** (the precondition for end-to-end encryption) |
| 8 | **Scientific and engineering computation** | ~30 | GSL, Gnuplot, Graphviz, minimap2, Orekit, Qiskit, EPANET, power flow, phase field, CSTR, adaptive optics, neuron simulation… | Replace expensive workstations and HPC licences |
| 9 | **Networking and protocol stacks** | ~6 | libp2p, NimBLE, pcap parsing, Brotli, Zstd, TSN scheduling | Implement, in the browser, the protocols the browser won't give you |
| 10 | **AI and inference** | ~6 | ONNX Runtime Web, RWKV, MoE inference, Tesseract, OpenCV, HOG features | **Inference cost to zero + data never leaves the device** |
| — | **(outside the catalog) Multi-user persistent worlds** | 1 | **FluffOS × Wasm** (an entire LPMud driver plus the mudlib archive — Appendix L) | Asset revival + cultural preservation |

**What deserves the most attention in that table is why category 8 is the largest** (about 30%). Scientific computing has a peculiar structure:

- **The algorithms are entirely public** (finite element methods, Monte Carlo, Newton–Raphson, FFT — all textbook material, no trade secrets);
- **The existing implementations are mature C/C++ libraries** (GSL, EPANET, OpenVDB, pagmo — porting cost is low);
- **The original barrier to entry was absurdly high** (install a Linux workstation, buy a commercial licence costing tens of thousands, or queue for an HPC cluster);
- **The data is extremely sensitive** (patient genomes, grid topology, alloy formulations, financial positions — cloud services face compliance obstacles).

**Stack those four conditions and Wasm's value is not speed; it is driving an entire field's barrier to entry to zero.** A graduate student opens a page and runs gene sequence alignment; a power engineer computes island-wide load flow on a laptop in the field — and not one byte of data leaves their machine.

**Conversely, what is *not* on that table carries just as much information**: no CRUD backends, no e-commerce, no content management, no social features. **Because the bottleneck in those was never compute; it was data and state** — which is exactly Part III's subject.

> 🔍 Deeper Commentary — the ordering of these ten hints at a clear value filter
> Spread out the motive column across all 101 cases and they all fall onto four reasons — and **the relative weight of those four is an operable decision rule.** **Reason one: shifting compute cost (present in nearly every entry).** Public algorithm, large computation, no trade secret — Wasm's least controversial sweet spot. **Reason two: data sovereignty (about 70%).** Medicine, finance, defence, personal privacy — "the data never leaves the device" is not a bonus in those fields, it is an entry requirement. **Reason three: capability gaps (about 30%).** The browser doesn't support XSLT 2.0, doesn't support Graphite fonts, doesn't expose a Brotli API, doesn't hardware-decode AV1 — Wasm is the only way to fill them. **Reason four: asset revival (about 20%).** Hundreds of thousands of lines of C++ geometry kernel, a twenty-year-old game, decades of accumulated GNU toolchain — rewriting is impossible; recompiling is feasible. **The extreme form of this reason is cultural preservation**: `fluffos/mudlibs` restored two hundred Chinese MUD codebases from the mid-1990s to around 2015 (covering 158 distinct codebases) and compiled the entire FluffOS driver to Wasm so dozens of them can be played by clicking a link — **the code itself was barely broken; what broke was every assumption it made about its environment** (Appendix L). **So the decision rule reads: the more reasons your situation hits, the higher Wasm's return; if it hits only reason one, carefully price the download size and boundary overhead; if it hits none, don't use Wasm.** Note in particular — **reason two (data sovereignty) is the only one where "plain JS could do it too, but nobody would believe you."** Technically, plain JavaScript can equally keep data from being uploaded; but when you have to convince a lawyer, a compliance officer or a hospital's security department, the narrative "the entire algorithm is compiled into an inspectable binary, running in the user's own browser sandbox, with not one outbound request in the network tab" is far more persuasive than "trust me, my JS isn't sending anything." **That is a value outside technology — it sells auditability, not performance.**

## Scenario 3: Five universal architectures — the 101 cases really have only five shapes

**Background.** Read all 101 and you notice something: their architecture descriptions are startlingly alike. That is not narrative laziness; it is because **under Wasm's physical laws, there really are only these few viable architectures.**

### Pattern one: flat memory plus zero-copy views

**Frequency: 101/101.** The bedrock of every Wasm performance story.

```
JS side:   write data into Wasm's linear memory, or open a TypedArray view over it
                    ↓ pass only a pointer and a length, never the contents
Wasm side: process it as a contiguous byte array (struct-of-arrays, CSR sparse
           matrices, Roaring bitmaps, memory pools, B+ trees…)
                    ↓ write results back into the same memory
JS side:   read the result at the pointer (or hand it straight to a WebGL vertex buffer)
```

**Its real advantage is usually stated wrongly.** Most accounts say "because it avoids JS's garbage collection," which is only half right. **The bigger factor is the CPU cache.** JavaScript objects are allocated discretely on the heap, so iterating a million `{x, y, z}` objects means up to a million potential cache misses; the same data in Wasm is three contiguous `Float64Array`s, and the CPU's prefetcher works perfectly. **An L1 hit is roughly 4 cycles and a DRAM access roughly 200 — that 50× gap is the real source of those "30× faster" numbers, not GC.**

### Pattern two: Worker isolation plus transferable objects

**Frequency: about 60%.** The moment computation exceeds 16 ms, it must leave the main thread.

```javascript
// Main thread: the second argument to postMessage is the point
const buf = new ArrayBuffer(50 * 1024 * 1024);
worker.postMessage({ cmd: "process", buf }, [buf]);
// ↑ the second argument [buf] declares this transferable:
//   rather than copying 50 MB, ownership of the memory moves to the Worker (microseconds)
//   the price: after transfer, buf on this side has length 0 and is unusable
```

**Three ways of passing data, clearly distinguished:**

| Method | Cost | For |
|---|---|---|
| Structured clone (default) | O(n); painful for large data | Small messages; both sides need the data |
| **Transferable** (`postMessage(x, [x])`) | O(1); ownership only | Large buffers moving one way |
| **`SharedArrayBuffer`** | O(1); visible to both simultaneously | Genuine multithreaded sharing (**requires cross-origin isolation**, Chapter 5) |

### Pattern three: SIMD vectorization (`v128`)

**Frequency: about 40%.** Applicable whenever the work is "do the same thing to a lot of data."

Wasm SIMD provides a fixed 128-bit `v128` type and a set of lane operations; one instruction handles four `f32`, two `f64` or sixteen `i8` at once. Typical speedups land at 2–4× (not 4–16×, because memory bandwidth and data shuffling eat part of it).

```bash
# Enable SIMD (Rust)
RUSTFLAGS="-C target-feature=+simd128" cargo build --target wasm32-unknown-unknown --release
# Enable SIMD (Emscripten)
emcc -msimd128 -O3 ...
```

**Two practical traps.** **First, SIMD is a detectable feature** — older browsers lack it, so you need a non-SIMD fallback build and runtime detection. **Second, Wasm SIMD is only 128 bits** — native AVX2 is 256 and AVX-512 is 512. As Chapter 2 said: code hand-optimized for AVX2, ported here, has its vector width halved outright.

### Pattern four: streaming and chunked processing (sliding window)

**Frequency: about 30%, but 100% in "large file" scenarios.** This is the only practical way around the 4 GB ceiling (detail in Chapter 8).

```
Don't: read a 10 GB file entirely into linear memory  ❌ immediate OOM
Do   : open a 50 MB sliding window inside Wasm and use OPFS's
       FileSystemSyncAccessHandle to read(buffer, {at: offset})
       — like watching a tape, fetch whichever segment you need  ✅
```

MediaInfo reading only an MP4's `moov` atom; DuckDB-Wasm fetching only the needed column chunks of a Parquet file via HTTP Range Requests; Tantivy downloading only the index blocks that matched — **all the same move.**

### Pattern five: AudioWorklet, or high-priority thread isolation

**Frequency: every audio case (about 6).** The audio thread has a brutal hard deadline:

```
At a 44.1 kHz sample rate, one 128-sample block = 2.9 ms
→ your processing function must return within 2.9 ms or it is an audible pop
→ there is no room for a single GC pause here
→ hence AudioWorklet + Wasm has become industry practice
```

FLAC encoding, chiptune synthesis (libmodplug/GME), SDR demodulation — all take this road.

> 💡 A Word to the Wise
> **When every successful case in a field has an identical architecture, that is not a lack of creativity; that is physics talking.** The 101 cases span audio, databases, genomics, power grids, astronomy and finance — domains with nothing whatever in common — and yet their architecture diagrams are nearly interchangeable, because they face the same constraints: **one flat memory, one expensive boundary, a 16 ms frame budget, a 2.9 ms audio budget, a 4 GB ceiling.** That yields a highly practical corollary: **when you enter a new field, go find the architecture diagrams of three successful cases. If they look alike, that shape is the field's physics and you should not try to innovate on it; if they look completely different, the field has not yet found its shape, and that is where the opportunity is.** The ability to tell those two situations apart is worth more than any specific technology.

## Scenario 4: Three representative cases, taken to the bottom

**Background.** The appendices give 500 words each; here we take three all the way down — because each represents a distinct mechanism by which Wasm makes the impossible possible.

### DuckDB-Wasm: an OLAP engine on a static page, and the HTTP Range trick

**What it does.** Compiles DuckDB — a columnar analytical SQL database written in C++ — entirely to Wasm. Users type standard SQL in a web page and run aggregate queries over millions of rows in the browser.

**Why it beats plain JS by 60×** (the source list claims a 10-million-row aggregate query completing in 100–200 ms):

1. **Vectorized execution.** Not row by row, but a whole batch (typically 1024–2048 values) of a column vector at a time. Branch-prediction friendly, SIMD friendly, cache friendly.
2. **Apache Arrow's columnar memory layout.** Data sits column-contiguous in linear memory, so `SELECT SUM(price)` sweeps one contiguous array and touches nothing else.
3. **Zero-copy handoff.** Query results stay in linear memory in Arrow format, and the JS side reads them through a `TypedArray` view with no serialization.

**The most elegant part is how it reads remote files:**

```sql
-- This line does not download the whole Parquet file
SELECT region, SUM(revenue) FROM 'https://example.com/sales.parquet' GROUP BY region;
```

Parquet's structure is "data blocks plus trailing metadata (the footer)." DuckDB-Wasm will:

```
1. Issue an HTTP Range Request for only the last few KB → read the footer, learn the byte
   offset of every column and row group
2. From the SQL, determine which columns and row groups are needed (pruning via the
   footer's min/max statistics — predicate pushdown)
3. Issue a few more Range Requests, fetching only those byte spans
   → a 2 GB Parquet file might download only 8 MB
```

**This is the full power of the "static hosting plus Wasm" combination**: the CDN supplies Range Requests (a free capability available everywhere) and Wasm supplies the intelligence to understand the file format. **You have obtained a data warehouse with no server.**

### Pyodide: moving all of CPython into the sandbox, and the price of those 30 MB

**What it does.** Compiles the CPython interpreter itself, plus NumPy, Pandas, SciPy and scikit-learn — libraries **containing large amounts of C** — entirely to Wasm.

**The hardest part is not compiling CPython; it is those C extensions.** NumPy's core is hundreds of thousands of lines of C that assume a world with `dlopen`, a POSIX filesystem and CPU-specialized paths. Pyodide must:

- fabricate an entire filesystem with Emscripten's **MEMFS/IDBFS**;
- deal with the early absence of dynamic linking in Wasm (Emscripten's `SIDE_MODULE`/`MAIN_MODULE` dynamic linking, or compiling everything in statically);
- implement **bidirectional type bridging**: a JS `Array` readable as a Python `list`, Python objects accessible from JS, and a Matplotlib figure convertible to a binary stream that JS renders into a `<canvas>`.

**Two layers of performance reality** (an instructive contrast):

| What you run | Relative to native | Why |
|---|---|---|
| A pure Python loop | **about 1/3 to 1/5** | You are running an interpreter inside a virtual machine — two layers of abstraction |
| Calling NumPy / Pandas C kernels | **about 70%** | The hot loop is in C; Wasm executes compiled machine code directly |

**That 3–5× gap says something important**: Pyodide's value is not "Python runs fast" but "**the C core of Python's ecosystem can be called from a browser.**" Writing dense pure-Python loops with it is a misuse; running `df.groupby().agg()` is the correct use.

**Those 30–50 MB** are its greatest pain, and there are three realistic mitigations: on-demand package loading (Pyodide supports `micropip.install` at runtime), persistent caching via a Service Worker (a second visit is nearly instant), and for cases needing only the language itself, **MicroPython/Wasm** (two orders of magnitude smaller).

### v86: an entire x86 computer inside the browser

**What it does.** Simulates a complete x86 virtual machine — CPU, MMU, IDE disk controller, VGA, keyboard interrupts — inside a purely static web page. It runs Linux, runs Windows 95, runs DOOM.

**Its core technique is deeply counterintuitive: dynamic recompilation (JIT).**

```
The naive emulator: loop { read an x86 instruction → switch(opcode) → execute }
                    → pay decode and dispatch on every instruction; 100× slower

What v86 does:      take a block of x86 → dynamically translate it into Wasm instructions
                    → compile that Wasm on the fly with WebAssembly.instantiate
                    → thereafter this block executes at native speed
                    → i.e.: a JIT that emits Wasm, which the browser then JITs to machine code
```

**This is a two-layer structure where a JIT produces another JIT's input**, and it works because of a rarely discussed Wasm property: **a `WebAssembly.Module` can be constructed at runtime from a byte array.** In other words, **Wasm is a compilation target that programs can generate**, which makes it the natural backend for every emulator, dynamic-language runtime and, ultimately, JIT compiler.

**The wall it hits is equally clear**: it cannot use the host's hardware virtualization (Intel VT-x / AMD-V), which needs ring 0; every address translation is a software-simulated page table. So it runs Pentium-class 32-bit systems and **cannot run modern 64-bit operating systems.**

> 💡 A Word to the Wise
> **To judge whether a technology platform has long-term life, one thing suffices — can it become *other things'* compilation target?** A format only humans can hand-write is capped by human output; a format programs can generate is capped by the sum of every system that wants to move onto it. v86 dynamically emits Wasm, Pyodide compiles CPython across, Cranelift compiles Wasm to machine code, and Wasm itself even gets compiled to C and back to native (wasm2c) — **that property, "anyone can translate themselves into it," is an intermediate representation's real moat.** It is why the JVM lived thirty years, why LLVM IR came to dominate compiler backends, and why Wasm has a chance to be next. Conversely it gives you a practical test: **when evaluating a new format, protocol or platform, ask "is anyone generating it automatically?" — if the answer is no, it is a tool, not a platform.**

## Chapter Summary

- That "120 cases" is in fact **101 distinct entries**; 19 are renumbered retellings. This exposes a concrete failure mode in long-form generation: **without an externally maintained list of prior output, deduplication depends on context, and context fails** — and the effective remedy is **constraining the search space (specifying new categories), not demanding memory.**
- The 101 fall into three authenticity tiers: **🟢 verifiable (~40%), 🟡 upstream real but Wasm port unverified (~40%), 🔴 illustrative construction (~20%).** The right reading is as a **feasibility map**, not a project index.
- Of the ten categories, **scientific and engineering computation is 30%**, because it satisfies four conditions at once: public algorithms, mature C implementations, an absurdly high original barrier, and extremely sensitive data. **Wasm's value here is not speed; it is driving a whole field's barrier to entry to zero.**
- The 101 cases have only **five architectural shapes**: flat-memory zero copy, Worker isolation with transferables, SIMD vectorization, streaming sliding windows, and AudioWorklet hard-deadline isolation. **When every successful case shares an architecture, that is physics talking.**
- The real source of those "N times faster" figures is usually misstated — **it is not garbage collection; it is the CPU cache** (an L1 hit ≈ 4 cycles, a DRAM access ≈ 200).
- The three deep cases each represent a mechanism: **DuckDB-Wasm** = a CDN's Range Requests plus Wasm's format intelligence = a data warehouse with no server; **Pyodide** = pure Python is 3–5× slower but C kernels reach 70%, and its value lies in "the ecosystem's C core becomes callable"; **v86** = a two-layer JIT emitting Wasm, proving that **Wasm is a compilation target programs can generate.**

The machines run, and run fast enough. But they all share one fatal flaw — **reload the page and everything they remembered evaporates.** The next chapter deals with that. Turn to Chapter 7.

---



# Chapter 7: The Memory of a Stateless Machine — MEMFS, IDBFS, OPFS and WASI

> WebAssembly is itself a **stateless** sandboxed virtual machine. It has no disk and no native database. By default it has only one flat block of memory allocated by the host, and **the moment the page reloads, everything inside it evaporates like foam.**
> The way it solves this comes down to two words: **delegated capability.**

## Scenario 1: Layer one — MEMFS, the fake Linux living in memory

**Background.** When you compile a C/C++ project (FFmpeg, SQLite, GNU tar) to Wasm, the code is full of this sort of thing:

```c
FILE *f = fopen("input.mp4", "rb");
fread(buf, 1, size, f);
fclose(f);
```

Wasm has no `fopen`. It does not even have the concept of a system call. So how does that line run?

**The answer: Emscripten fabricates an entire POSIX filesystem inside linear memory.** It is called **MEMFS** (In-Memory File System), and it uses typed arrays in Wasm's linear memory to simulate the standard Linux directory structure (`/tmp`, `/home`, `/dev`), redirecting all of libc's file functions into it.

```
C code:      fopen("/work/input.mp4", "rb")
                    ↓ Emscripten's libc implementation
JS glue:     FS.open("/work/input.mp4", "r")
                    ↓
MEMFS:       look up a JS-object directory tree built in linear memory,
             return a file descriptor pointing at some Uint8Array
```

**A typical data flow** (FFmpeg.wasm as the example):

```javascript
// 1. Write the user's dropped file into Wasm's virtual filesystem
ffmpeg.FS('writeFile', 'input.mp4', await fetchFile(file));
// 2. Run the command line — internally, Wasm genuinely believes it is a CLI
await ffmpeg.run('-i', 'input.mp4', '-c:v', 'libx264', 'output.mp4');
// 3. Read the result back out of the virtual filesystem
const data = ffmpeg.FS('readFile', 'output.mp4');
// 4. Turn it into a Blob URL for the user to download
const url = URL.createObjectURL(new Blob([data.buffer], {type: 'video/mp4'}));
```

**MEMFS's two fatal problems:**

1. **It is ephemeral.** Close the page, reload, or exhaust memory (OOM), and the files are gone.
2. **It consumes your linear-memory budget.** A 500 MB video written into MEMFS occupies 500 MB of that 4 GB ceiling — and FFmpeg needs more on top during transcoding. **That, not any limitation of FFmpeg itself, is why FFmpeg.wasm cannot handle large files.**

**MEMFS also has a rarely mentioned positive use: bundled distribution.** Emscripten's `file_packager` can pack thousands of files into **a single `.data` image plus a `.js` loader**, mounted at a chosen path before the runtime starts. FluffOS's Wasm build distributes an entire mudlib exactly this way — **tens of thousands of LPC files in a game world become one static blob.** The cost is stated with complete honesty in the official docs: **"writes currently persist only for the page session,"** and the next step on its roadmap is precisely the two layers this section is about to cover — **mounting an IDBFS or OPFS overlay over the write paths** (Appendix L).

> **This is the best live confirmation this book can offer**: a real, complex, actively maintained project is stuck at layer one of this four-layer ladder right now, and it knows exactly which way it needs to climb.

> 💡 A Word to the Wise
> **The essence of compatibility is faithfully reconstructing the old environment's lies inside the new one.** Emscripten did not make C programs "adapt" to the browser; it did the opposite — **it made the browser pretend to be Linux**, convincingly enough that `fopen`, `ioctl`, `pthread_create` and `SDL_CreateWindow` all get fooled. That is why a twenty-year-old C++ game can run on the web with essentially no change to its core logic. The principle has a more general form in system migration: **when moving a large body of existing assets to a new platform, "modify the assets to fit the platform" costs O(number of assets), while "emulate the old environment on the platform" costs O(1).** WSL, Rosetta, Wine, Docker, the JVM — all the same move. And the price is the same too: **what you moved across is a complete set of the old world's assumptions, including the inefficiencies you could have avoided in the new one.**

## Scenario 2: Layer two — IDBFS, rewinding memory into the browser's database

**Background.** To solve MEMFS's impermanence, Emscripten provides **IDBFS** — connecting the virtual filesystem to the browser's **IndexedDB**.

**How it works:**

```javascript
// Mount: bind the virtual directory /save to IndexedDB
FS.mkdir('/save');
FS.mount(IDBFS, {}, '/save');

// Load from IndexedDB into memory (at startup)
FS.syncfs(true, err => { /* true = read from IDB into MEMFS */ });

// The C code writes files as normal
// ... fopen("/save/game.sav", "wb") ...

// Sync memory back to IndexedDB (when saving)
FS.syncfs(false, err => { /* false = write from MEMFS back to IDB */ });
```

**The crucial point is that it rewinds the whole bundle, not random access.** `syncfs` serializes the **entire** mount point into IndexedDB (or the reverse). That decides its applicable boundary:

- ✅ **Suited to**: game saves (a few hundred KB), configuration files, small JSON, user preferences. **This is exactly how retro game emulators on the web persist saves.**
- ❌ **Not suited to**: database files, large media, anything requiring random access. A 500 MB SQLite file gets moved in full on every `syncfs`.

**IndexedDB's own problems come along for the ride** as well: an asynchronous event-driven API, mediocre write throughput, browser quota limits, and being restricted or cleared in some browsers' private modes.

## Scenario 3: Layer three — OPFS, which is the actual answer

**Background.** The **Origin Private File System** has in recent years become the gold standard for Wasm storage on the front end, and it is why DuckDB-Wasm and the official SQLite-Wasm can handle multi-gigabyte databases in a browser while guaranteeing ACID.

**What it is.** The browser opens, for each origin, a **highly isolated, heavily optimized private disk area.** It does not appear in the user's file manager, needs no permission dialog, cannot be seen by other sites — and, crucially, **it has a set of low-level APIs designed for performance.**

**Two access modes, and the difference is night and day:**

```javascript
// ── Mode A: asynchronous writable stream (usable on the main thread) ────────
const root = await navigator.storage.getDirectory();
const fh = await root.getFileHandle('data.bin', { create: true });
const writable = await fh.createWritable();
await writable.write(uint8array);
await writable.close();        // every step is a Promise, with microtask scheduling overhead

// ── Mode B: synchronous access handle (★ Web Workers only) ──────────────────
// This is the performance watershed
const root = await navigator.storage.getDirectory();
const fh = await root.getFileHandle('db.sqlite', { create: true });
const handle = await fh.createSyncAccessHandle();

handle.write(buffer, { at: offset });   // ← fully synchronous, no Promise
handle.read(buffer,  { at: offset });   // ← random access, like native pread/pwrite
handle.flush();
handle.truncate(newSize);
handle.getSize();
handle.close();
```

**Why `createSyncAccessHandle()` is the key.** The storage layer of a database written in C (SQLite, DuckDB) is **synchronous** — it calls `pread(fd, buf, len, offset)` and expects the data to be in the buffer immediately. You **cannot** implement that on an API that returns Promises, unless you rewrite the entire program asynchronously — which is impossible, because it is hundreds of thousands of lines of C.

**`createSyncAccessHandle` gives Wasm a genuinely synchronous, randomly seekable file handle** — so SQLite's VFS (the storage abstraction layer SQLite designed for portability) needs only a handful of functions implemented, and the whole database runs:

```
SQLite core (unmodified C code)
        ↓ calls the VFS interface: xOpen / xRead / xWrite / xTruncate / xSync / xLock
The OPFS VFS implementation in the Emscripten glue layer
        ↓
FileSystemSyncAccessHandle.read/write/flush
        ↓
The browser's private disk area (genuinely persisted)
```

**Costs and limits** (specification-level, not implementation defects):

1. **`createSyncAccessHandle` can only be called inside a Web Worker.** The main thread is forbidden, because synchronous I/O would block the UI. That means **your entire Wasm database engine must move into a Worker**, with the main thread communicating only through `postMessage`.
2. **An exclusive lock by default.** Only one sync access handle per file at a time. Multiple tabs opening the same application contend for the lock — you need your own coordination (the Web Locks API or a `BroadcastChannel`).
   **But this has since been relaxed**: newer browsers support `createSyncAccessHandle({ mode: "readwrite-unsafe" })`, permitting **multiple handles on the same file simultaneously.** The `unsafe` in the name is honest — **it hands responsibility for concurrency control entirely back to you**, and the browser stops arbitrating. Ask yourself before using it: does my engine have its own locking?
3. **Quotas.** Browsers impose per-origin storage quotas (usually tied to available disk space; query with `navigator.storage.estimate()`) and may **evict** data not marked persistent under disk pressure. To avoid being cleared, call `navigator.storage.persist()`.
4. **The user cannot see it.** That is both an advantage (it doesn't clutter their files) and a drawback (they cannot back it up themselves, so you must provide an export function).

### ★ A fork that will change your deployment decision: SQLite-Wasm's two OPFS VFS implementations

**This is the most practically valuable passage in the chapter, and it appears in almost no introductory article.** Official SQLite-Wasm does not provide one OPFS backend; it provides **two**, and their deployment costs differ enormously:

| | **`opfs` VFS** (first generation) | **`opfs-sahpool` VFS** (SAH = SyncAccessHandle) |
|---|---|---|
| Mechanism | An asynchronous proxy between the main thread and OPFS, made synchronous with `Atomics.wait` | **Holds a pool of pre-opened sync access handles**, reading and writing synchronously inside a Worker |
| **Needs `SharedArrayBuffer`** | **✅ Yes** | **❌ No** |
| **Needs COOP/COEP cross-origin isolation** | **✅ Yes** | **❌ No** |
| Performance | Usable | **Listed in the official documentation as the highest of all OPFS options** |
| Multiple connections | Supported | **Does not support multiple simultaneous connections** |
| Availability | Earlier | Broadly available in mainstream browsers since around March 2023 |

**Translated into one sentence:**

> **If you need a persistent SQLite somewhere like GitHub Pages where you cannot set HTTP headers, choose `opfs-sahpool` — it needs no cross-origin isolation and it is also the fastest one.**
> The official recommendation says exactly this: **clients that value performance over concurrency, or that cannot set COOP/COEP response headers, should use `opfs-sahpool`.**

**This routes around Chapter 5's "number one obstacle" entirely**, and the only price is "no multiple connections" — which, for the overwhelming majority of single-user frontend applications, is not a price at all.

> 💡 **There is a more general lesson here**: when you find yourself about to pay a heavy architectural cost for a platform limitation (here, the wholesale breakage of third-party resources caused by COOP/COEP), **first confirm whether the library you depend on offers a path that doesn't need that limitation.** Many teams have wrestled with `SharedArrayBuffer` and isolation for two weeks when the thing they wanted had a backend that never required it.

> ⚠️ Authenticity Caveat
> Claims like "Sqlite-Wasm's read/write throughput is 2–4× IndexedDB's" and "OPFS lets Wasm read and write at near-native disk speed" point in the right direction, but **the specific multiples depend heavily on workload and browser version.** Only three qualitative conclusions are reliable: **(a)** `createSyncAccessHandle` eliminates asynchronous scheduling overhead, so the improvement is most pronounced for "many small random I/Os" (precisely a database's access pattern); **(b)** for "write one large block at a time," async and sync differ little; **(c)** OPFS performance is strongly implementation-dependent, and Safari, Firefox and Chrome have shown clear differences. **Measure on your target browsers; do not copy anyone's multiple.**

**The full four-layer comparison:**

| | MEMFS | IDBFS | OPFS (async) | OPFS (sync handle) |
|---|---|---|---|---|
| Persistent | ❌ | ✅ | ✅ | ✅ |
| Random access | ✅ (in memory) | ❌ (whole-bundle rewind) | Limited | **✅ genuine pread/pwrite** |
| Consumes linear memory | **✅ (fatal)** | During sync | ❌ | ❌ |
| Usable on the main thread | ✅ | ✅ | ✅ | **❌ Workers only** |
| Performance | Memory speed | Poor | Medium | **Near native disk** |
| For | Temporary intermediates | Game saves, settings | Ordinary files | **Databases, large files, streaming** |

> 🔍 Deeper Commentary — OPFS is what actually turned Wasm from a library into an application platform
> This section deserves pulling out separately, because it marks a watershed. **Before OPFS, Wasm in the browser was essentially a pure-function accelerator**: you feed it input, it produces output, and then it deserves to be forgotten. Everything requiring state — the user's project files, databases, caches — had to detour back through JavaScript and be stored via IndexedDB's asynchronous API. That seam meant "move desktop applications to the browser" was always one mile short: **you could compile SQLite in, but you had nothing for it to use as a filesystem.** What `createSyncAccessHandle` closed was exactly that mile, and the way it closed it is interesting — **it did not give Wasm a new capability; it gave Wasm an interface shaped the way the C world expects.** Synchronous, seekable, lockable, flushable. Those four properties are not there because they are best, but because **every piece of storage software written in the last fifty years was written to that shape.** So the real insight is: **for a new platform to receive existing software assets, what matters is not how powerful a capability you offer but whether you offer the interface shape the other side expects.** That explains why OPFS chose an API design that looks "insufficiently modern" (synchronous, blocking) — because a modern asynchronous design would have locked the entire C/C++ ecosystem out. **When you design a platform's API, the most important question is not "what design is most elegant" but "what shape were the assets I want to receive written to?"**

## Scenario 4: Layer four — WASI on the backend, and the complete form of delegated capability

**Background.** When Wasm breaks out to the backend (Wasmtime, WasmEdge), it is no longer constrained by the browser sandbox but faces the problem of OS-level disk access. And its answer is fundamentally the same as on the front end.

**What capability-based security actually means:**

- On traditional Linux, a compromised Node.js process can read `/etc/passwd` directly — because it has **all** of that user's privileges.
- A Wasm runtime is by default **completely empty-handed**: it has no permission to call `open()`, because that import was never provided.

```bash
# At launch, explicitly grant the host's ./my_storage as /sandbox in the module's view
wasmtime run --dir=./my_storage::/sandbox my_server.wasm
```

If the module tries to reach `/sandbox/../etc/passwd`, the runtime intercepts it at the capability boundary and terminates — **not by relying on filesystem permissions and luck, but through the structural guarantee that the directory handle you hold cannot walk upward** (technically this corresponds to POSIX `openat` semantics and path-resolution restrictions).

**WASI's two generations** (distinguish them carefully when selecting):

| | `wasi_snapshot_preview1` | WASI 0.2 (Preview 2) |
|---|---|---|
| Model | POSIX-style file descriptors | **Component Model** plus WIT interface definitions |
| Interface | One large flat bag of functions | Split into `wasi:filesystem`, `wasi:io`, `wasi:sockets`, `wasi:http`, `wasi:clocks`… |
| Ecosystem | **Mature**: Rust's `wasm32-wasip1`, TinyGo and most toolchains support it | Evolving; toolchains catching up |
| Composability | Poor (monolithic interface) | **Good** (you can grant a component `wasi:clocks` and no filesystem) |

**The Component Model is the end of this road.** It lets Wasm modules communicate with **high-level types** (strings, records, variants, streams) instead of only `i32` pointers — in other words, it attempts to solve Chapter 2's "boundary toll booth" at the root. **WIT (Wasm Interface Types)** is its interface description language:

```wit
// A WIT interface definition: like an IDL, but bindings for each language
// can be generated at compile time
package example:storage@0.1.0;

interface kv {
  record entry { key: string, value: list<u8> }
  get: func(key: string) -> option<list<u8>>;
  put: func(key: string, value: list<u8>) -> result<_, string>;
  list-all: func() -> list<entry>;
}
```

**The summary of the technical idea.** Wasm solves storage through **memory mapping plus delegated capability**:

- On the **front end**, it delegates disk operations to the browser's IndexedDB or OPFS APIs;
- On the **backend**, it delegates disk operations to the WASI runtime's pre-authorized channel.

This preserves the Wasm virtual machine's sandbox isolation completely while giving it I/O throughput approaching a native C program.

> 💡 A Word to the Wise
> **The most honest thing about a system is the list of what it says it needs.** WASI's import section, a browser extension's `permissions` field, Android's manifest, Kubernetes' ServiceAccount — the value of those lists is not that they "stopped bad actors" (a genuinely malicious program will simply request everything it needs); it is that **they turn "what can this thing do" into a fact you can read in five seconds, rather than a question requiring reverse engineering.** Security audit cost drops from "prove it won't do anything bad" to "look at what it asked for." The corollary is practical: **when evaluating any third-party component, the first thing to look at is not its code but its permission list — and if that list doesn't exist, or is too long to read, you already have your answer.**

## Chapter Summary

- Wasm is itself **stateless**: one linear memory, evaporating on reload. Its solution is two words — **delegated capability.**
- **MEMFS**: an entire POSIX filesystem fabricated by Emscripten inside linear memory so `fopen()` has somewhere to go. **Ephemeral, and it consumes your 4 GB budget** — the real reason FFmpeg.wasm cannot handle large files. Its positive use is bundled distribution via `file_packager`.
- **IDBFS**: `FS.syncfs()` rewinds the entire mount point in and out of IndexedDB. Good for game saves and settings (hundreds of KB); **useless for databases or anything needing random access.**
- **OPFS is the real answer**, and the watershed is **`createSyncAccessHandle()`** — it hands Wasm a synchronous, randomly seekable file handle with locking and flush, so SQLite's VFS needs only a few functions to bring the whole database up. Costs: **Workers only, exclusive by default (`{mode:"readwrite-unsafe"}` relaxes it but the responsibility becomes yours), quota-limited, invisible to the user.**
- **★ The most practically valuable item**: SQLite-Wasm has **two** OPFS VFS implementations. The first-generation `opfs` needs `SharedArrayBuffer` and therefore **cross-origin isolation**; **`opfs-sahpool` needs no COOP/COEP and is the fastest option in the official documentation**, at the cost of not supporting multiple connections. **For persistent SQLite on GitHub Pages, choose the latter and Chapter 5's number-one obstacle disappears entirely.**
- The general lesson: **when you are about to pay a heavy architectural cost for a platform limitation, first check whether your dependency has a path that doesn't need it.**
- OPFS's design lesson: **for a new platform to receive existing software assets, what matters is not how powerful a capability you offer but whether you offer the interface shape the other side expects** — even when that shape (synchronous, blocking) looks insufficiently modern (see the 🔍 in Scenario 3).
- The backend's **WASI** is the same philosophy from another side: **capability-based security**, empty-handed by default, with the capability inventory written into the launch arguments. Note that **preview1 and 0.2 are two generations**, so what you write today should expect one migration.
- Front end delegates to OPFS/IndexedDB, backend delegates to WASI — **one doctrine, two hosts.**

The memory problem is solved. But one hard wall remains: **what happens when your data exceeds 4 GB, and when your module exceeds 30 MB?** Turn to Chapter 8.

---



# Chapter 8: The 4 GB Ceiling — File Size, App Size, and Four Ways Around It

> **"What's Wasm's file size limit? App size limit?"**
> Those two questions sound like the same thing and are in fact two entirely independent ceilings: **one decided by how large a module the engine can compile, the other by how much memory the virtual machine can address.** Conflating them is where every large Wasm project comes off the rails at architecture review.

## Scenario 1: Two ceilings, four numbers

**Background.** Get the four numbers straight first; every architectural decision below is derived from this table.

### Ceiling one: how large the `.wasm` file itself can be

| Environment | Hard limit | Practical ceiling | The nature of the limit |
|---|---|---|---|
| **Browser** | Typically on the order of 1–2 GB | **Strongly recommended under 10–30 MB** | Streaming compilation must build a large compiler state in memory; and download time eats your first paint directly |
| **Backend runtime** (Wasmtime / WasmEdge) | No clear limit; bounded by physical memory | Hundreds of MB to 1 GB+ all workable | With enough memory you can pack neural-network weights straight into the module |

**Why the browser's practical ceiling is so far below the hard limit.** An oversized file stacks three costs: network download time lengthens, parsing hundreds of MB of Wasm spikes a mobile CPU to full and heats the device, and time-to-first-paint (and every Core Web Vital with it) degrades. **This is an experience problem, not a capability problem** — and it is harder to route around than a capability problem.

### Ceiling two: how large the runtime's linear memory can be

| Addressing mode | Hard limit | The browser's real interception | Status |
|---|---|---|---|
| **wasm32** (today's overwhelming default) | **Welded to 4 GiB** (2³² bytes) | Chrome typically throws OOM and kills the tab at **2–3 GiB** on protective grounds | Universally supported |
| **wasm64** (Memory64, **now in the Wasm 3.0 core specification**) | Theoretically 2⁶⁴ (16 EiB class) | Bounded by the host OS and cgroup quotas | Standardized, **but with a performance cost** |

**wasm32's 4 GiB is mathematics, not an implementation choice**: addresses are 32-bit pointers, `2³² = 4,294,967,296` bytes. There is no way around that line.

**The direct consequence for industrial cases**: **FFmpeg.wasm handling video, and v86 running Linux, cannot by default process or load a single file larger than 2–3 GB** — because the file must first be read whole into that linear memory (Chapter 7's MEMFS).

**Memory64's hidden cost** (the passage marketing material never mentions; the fuse was laid in Chapter 2):

```
wasm32's free bounds checking:
  the engine reserves 8 GiB of virtual address space (4 GiB addressable + guard regions)
  → a 32-bit offset mathematically cannot exceed the reservation
  → out of bounds triggers SIGSEGV via the MMU; the engine catches and turns it into a trap
  → bounds-check instructions on the hot path: 0

And wasm64?
  you cannot reserve 2⁶⁴ of virtual address space per memory
  → the guard-page trick fails
  → you must fall back to "explicit compare and branch before every access"
  → performance regression: from a few percent to double digits depending on the benchmark
```

**So the correct mental model is: below 4 GiB you enjoy safety subsidized by hardware; past that line, safety starts charging you.** Which yields an architectural principle directly — **if chunked streaming (Scenario 2) or multiple memories (Scenario 4) can solve it under 4 GiB, don't rush to wasm64.**

> ⚠️ Authenticity Caveat
> "wasm64's hard limit is 16 EB" is mathematically correct and practically meaningless — no host provides memory at that magnitude. Two numbers matter more: **(a)** browsers' actual per-memory limit has historically varied between 2 and 4 GiB by version and platform, so **do not treat 4 GiB as available budget**; **(b)** although Memory64 is now in the **Wasm 3.0** core specification, **its performance varies significantly across engines — measure in your target environment before adopting it.**
>
> **One more easily confused semantic**: `memory.grow` **does not trap on failure; it returns `-1`** (and on success returns the page count before growth). This means **memory exhaustion is a return value you must check, not an exception that blows up on its own** — and most C code that treats `malloc` failure as "won't happen" will quietly write into memory that doesn't exist here, and only trap on the next access. **The out-of-bounds error you are looking at is often that unchecked grow failure several hundred lines earlier.**

> 💡 A Word to the Wise
> **Every "free" system property rests on a physical precondition you didn't notice, and the bill arrives the moment you cross it.** Wasm's bounds checking is free below 4 GiB because a 64-bit host's virtual address space is cheap enough to waste wholesale; ask for 64-bit addressing and that precondition disappears, so what was free starts costing. The pattern recurs throughout systems engineering: allocating small objects is free (there is a slab allocator) until your objects get big; caching is free (the working set fits in L3) until your data gets big; synchronization is free (there is one thread) until you add a second. **So the most valuable single item of engineering intuition is knowing what precondition makes each "it's fast anyway" thing fast** — because growth always breaks the precondition before it reveals the cost.

## Scenario 2: Escape route one — OPFS chunked streaming (the sliding window)

**Background.** The most important and most underrated of the four. Its core idea is to **refuse to read the whole file into memory.**

**The method.** Do not read a 10 GB file into Wasm memory at once. Instead use OPFS's `FileSystemSyncAccessHandle` to `read(buffer, { at: offset })` — keep only a 50 MB **sliding window cache** inside Wasm and, like watching a tape, reach out with a direct pointer for whichever segment you need.

**Result: 50 MB of memory, streaming smoothly through a 100 GB file.**

```rust
// Skeleton: random reads through a synchronous handle inside a Worker
const WINDOW: usize = 50 * 1024 * 1024;   // 50 MB sliding window

struct ChunkedReader {
    handle: FileSystemSyncAccessHandle,   // from OPFS
    window: Vec<u8>,                      // the only resident memory
    window_start: u64,                    // file offset the window currently covers
    window_len: usize,
    file_size: u64,
}

impl ChunkedReader {
    /// Read any position; disk I/O happens only when you step outside the window
    fn read_at(&mut self, offset: u64, len: usize) -> &[u8] {
        let in_window = offset >= self.window_start
            && offset + len as u64 <= self.window_start + self.window_len as u64;
        if !in_window {
            // Reposition the window aligned to a chunk boundary, so reading one byte
            // does not force a whole-window reload
            self.window_start = (offset / CHUNK) * CHUNK;
            self.window_len = self.handle
                .read_at(&mut self.window, self.window_start);   // ← synchronous pread
        }
        let local = (offset - self.window_start) as usize;
        &self.window[local .. local + len]
    }
}
```

**Four implementation points** (they decide whether this is usable or merely slow):

1. **Align the window.** Align the offset to a 1 MB or 4 MB boundary before reading, so reading a single byte does not trigger a whole-window reload.
2. **Consider the access pattern.** Sequential scans (video decoding) want a large window plus read-ahead; random jumps (database indexes) want a small window plus an LRU of several windows.
3. **It must be in a Worker** (the specification restriction on `createSyncAccessHandle`, Chapter 7).
4. **Remote files use the same logic via HTTP Range Requests** — replace `handle.read_at()` with `fetch(url, {headers: {Range: 'bytes=...'}})` and the architecture is identical. **That is exactly how DuckDB-Wasm queries remote Parquet** (Chapter 6).

**The power of this move is that it converts a "memory ceiling" problem into an "I/O bandwidth" problem** — and the latter can be softened with read-ahead, caching and compression, while the former is a wall.

## Scenario 3: Escape route two — multi-module memory isolation (4 GB × N)

**Background.** If a single Wasm instance tops out at 4 GiB, open a lot of them.

**The method.** Start several independent Web Workers in the browser, **each loading its own separate Wasm runtime instance.** Because every virtual machine has its own 4 GiB linear memory, you can use the main thread as a data bus, distribute work across Workers, and **multiply the app's total compute and memory ceiling to 4 GiB × N.**

```
                Main thread (scheduling only, no computation)
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   Worker 1         Worker 2        Worker 3
   Wasm instance A  Wasm instance B Wasm instance C
   4 GiB linear mem 4 GiB linear mem 4 GiB linear mem
   (segment 1)      (segment 2)     (segment 3)
        │               │               │
        └───────────────┴───────────────┘
              results returned as transferables, zero copy
```

**This is a completely different thing from "Wasm multithreading"** (the most commonly confused point):

| | Multi-instance isolation (this section) | Wasm threads (`SharedArrayBuffer`) |
|---|---|---|
| Memory | 4 GiB per instance, independent | **One shared** linear memory; the total is still capped at 4 GiB |
| Communication | `postMessage` plus transferables (copy or move ownership) | Direct reads/writes of the same memory plus atomics |
| Needs cross-origin isolation | **❌ No** | **✅ Yes, COOP/COEP** |
| Suited to | Partitionable work (chunked processing, parallel rendering, independent queries) | Algorithms needing fine-grained shared state (physics simulation, graph traversal) |
| On GitHub Pages | **Works directly** | Needs `coi-serviceworker` |

**That table has a very practical corollary**: **if your task is data-partitionable (and the vast majority of batch processing is), use multi-instance isolation — it needs no cross-origin isolation, doesn't break your third-party resources, and breaks the 4 GiB ceiling as a bonus.** Plenty of teams fight COOP/COEP for two weeks before discovering they never needed shared memory at all.

## Scenario 4: Escape route three — multiple memories (new in Wasm 3.0)

**Background.** This road entered the core specification only in September 2025, and it attacks the 4 GiB problem head-on.

**The method.** **Wasm 3.0's multiple memories let one module declare and access several linear memories, and move data directly between them.**

```wat
(module
  (memory $code 16)          ;; memory 0: code working area
  (memory $assets 1024)      ;; memory 1: assets / bulk data
  (memory $scratch 64)       ;; memory 2: scratch space

  (func $copy_in
    ;; memory.copy can cross memories: destination index, source index
    (memory.copy $scratch $assets
      (i32.const 0) (i32.const 4096) (i32.const 65536)))
  ;; loads and stores can also name a memory
  (func $peek (result i32)
    (i32.load $assets (i32.const 1024))))
```

**Its relationship to the previous two routes is worth drawing clearly:**

| | Multiple memories (this section) | Multi-module isolation (Scenario 3) | Memory64 |
|---|---|---|---|
| Wasm instances | **One** | N | One |
| Memories | **Several** | One per instance | One (very large) |
| Data movement cost | **`memory.copy` across memories, done at engine level** | `postMessage` across threads | No movement needed |
| Free guard-page bounds checking | **✅ each is still wasm32, fully preserved** | ✅ | **❌ lost** |
| Needs a Worker | ❌ | ✅ | ❌ |
| Needs cross-origin isolation | ❌ | ❌ | ❌ |
| Suited to | **Single-threaded, partitionable large applications** | Partitionable batch work | Genuinely needing one huge address space |

**The elegant part is the fourth row**: because each memory **remains 32-bit addressed**, the whole "reserve virtual address space plus guard pages equals free bounds checking" mechanism is **fully preserved.** In other words —

> **Multiple memories break the single-4 GiB limit without giving up free bounds checking.**
> That is precisely the trade Memory64 cannot make, and why, wherever the data partitions naturally (code area / asset area / scratch, one per tenant, hot/cold separation), **multiple memories almost always beat Memory64.**

**The practical caveat**: **toolchain support lags the specification.** Most C/C++/Rust toolchains still assume a single memory by default; using this today usually means hand-written WAT or a newer toolchain with the right attributes. **Specification first, toolchain later — the normal state of every new feature, and why "spec status" and "can I use it today" must be asked separately.**

## Scenario 5: Escape route four — enable Wasm GC and give the runtime back to the browser

**Background.** The first three all attack the **memory** ceiling. This one attacks the other ceiling Scenario 1 established — **file size.**

**The problem.** If you compile a high-level language like Java, Kotlin, Dart or C# to Wasm, the traditional approach packs the language's entire garbage collector and standard library into the `.wasm`, inflating it to several megabytes or more.

**The method.** Enable **Wasm GC** (in the core specification since Wasm 3.0, September 2025) and let Wasm use the browser's native, heavily optimized garbage collector (V8's Orinoco, SpiderMonkey's GC) instead of carrying its own.

**What Wasm GC adds at the specification level** (worth detailing, as it is the newest piece here):

- **Heap types**: `struct`, `array`, and `i31` (a small-integer optimization that fits inside a pointer).
- **Typed references**: `(ref $MyStruct)`, `(ref null $MyArray)` — for the first time Wasm can point at *a structured object* rather than merely an `i32` offset.
- **Subtyping and `br_on_cast`**: so object-oriented languages' inheritance and dynamic casts can be expressed.

```wat
;; Wasm GC: real objects, managed by the host GC, not occupying linear memory
(type $Point (struct (field $x f64) (field $y f64)))
(func $make (result (ref $Point))
  (struct.new $Point (f64.const 1.0) (f64.const 2.0)))
```

**Benefits and costs:**

| | Benefit | Cost |
|---|---|---|
| Size | **Substantial reduction** (no need to pack a GC and part of the runtime) | — |
| Performance | Uses a heavily optimized host GC, usually better than a bundled simple one | You lose control of collection timing — **GC pauses are back** |
| Applies to | Kotlin/Wasm, Dart (Flutter Web), Java, Scheme, etc. | **Nearly useless for Rust/C/C++** — their data already lives in linear memory |
| Support | **In the Wasm 3.0 core specification**; mainstream browsers support it | Backend runtimes and toolchains lag the browsers |

> ⚠️ Authenticity Caveat
> A common claim: "enabling Wasm GC cuts `.wasm` size by over 80%." **The direction is right, but that number holds only for languages that would otherwise pack an entire language runtime** (Java, Kotlin, Dart), and the actual reduction depends on how much was being packed. **For Rust, C and C++, enabling Wasm GC yields essentially no size benefit** — their objects already live in linear memory and there is no GC to remove. Applying this advice indiscriminately across languages is a very common misreading.

**Before you touch any compiler flag, do rule zero** — its return usually exceeds everything else combined:

> **★ Rule zero: cut data before you cut code.**
> More than half of a large C/C++ project's Wasm artefact is often the **data tables** it drags in, and 90% of those tables you never use.
> **A real example** (Appendix L): FluffOS's Wasm build keeps only ICU's break-iterator rules, cutting **data from about 30 MB to about 780 KB (−97%), while the driver's entire code body is 3.6 MB.**
> **So the first action is not to enable a flag; it is `wasm-objdump -h` to look at your section budget** — if Data is half the file, squeezing another 10% out of Code buys you 5% of the total.

**Once you have checked the section budget, then the toolchain applies**: `wasm-opt -Oz` → compile-time settings (`lto` / `codegen-units=1` / `panic="abort"` / `strip`) → `twiggy` diagnosis → dead-code elimination → Brotli transport → module splitting.

> **That is only the list. What each item actually removes, at what cost, and the things not on the list — Rust's formatting machinery hiding inside `panic!`, the "generic thin shell" cure for monomorphization blowup, what each `wasm-opt` pass does, how Compression Dictionary Transport makes a new release ship as tens of KB — are all in Appendix N, Part One, with an item-by-item ROI table.**

> 🔍 Deeper Commentary — the four escape routes are one idea projected four ways
> Put all four side by side and they solve the same problem: **"all of it at once" is the common root cause of every resource ceiling.** Chunked streaming says "don't bring all the data in at once"; multi-module isolation says "don't fit it all in one instance"; multiple memories says "don't cram it all into one address space"; module splitting and lazy loading say "don't download all the code at once." **All four convert a *total* problem into a *partitioning* problem along a time or space axis** — and partitioning problems are always easier than totals, because you can flatten them with read-ahead, caching, priority and background loading. The principle generalizes enormously: database pagination, adaptive video streaming (HLS/DASH), virtual scrolling lists in the front end, paged KV caches in LLM serving (PagedAttention), an operating system's virtual memory — **all the same thought: don't ask "how much do I have," ask "which slice do I need right now?"** The next time you hit any kind of capacity ceiling, the first question is not "how do I raise the limit" but — **do I genuinely need all of it at the same instant?** Nine times in ten the answer is no, and the tenth is when it becomes worth buying a bigger machine.

## Chapter Summary

- **Two independent ceilings**: `.wasm` **file size** (hard limit 1–2 GB class in browsers, **practically 10–30 MB**; effectively unlimited on the backend) and **linear memory size** (wasm32 is **welded to 4 GiB**, and browsers commonly OOM at 2–3 GiB).
- **wasm64 is not free**: once addresses are 64-bit, the "8 GiB virtual reservation plus guard pages" free bounds check stops working and you fall back to explicit comparison, with a real performance regression. **Below 4 GiB you are enjoying hardware-subsidized safety.**
- **Escape one: OPFS chunked streaming (sliding window)** — random reads with `createSyncAccessHandle`'s `read(buffer, {at})` let 50 MB of memory stream through a 100 GB file. Remote files use the same logic through HTTP Range Requests.
- **Escape two: multi-module memory isolation** — N Workers × N Wasm instances = 4 GiB × N. **This is a completely different thing from Wasm threads**: multi-instance **needs no COOP/COEP** and works directly on GitHub Pages. **When the task partitions, prefer this.**
- **Escape three: multiple memories** (new in Wasm 3.0) — several linear memories per module, with `memory.copy` moving data between them. **The greatest advantage is that each remains wasm32, so the free guard-page bounds check is fully preserved** — exactly the trade Memory64 cannot make. But **toolchain support lags the specification** (Scenario 4).
- **Escape four: Wasm GC** (in the Wasm 3.0 core specification) — hand garbage collection back to the host engine; substantial size benefit, **but only for languages that would otherwise pack a runtime (Java/Kotlin/Dart); nearly useless for Rust/C/C++** (see the ⚠️ in Scenario 5).
- `memory.grow` **returns `-1` on failure rather than trapping** — memory exhaustion is a return value you must check, and **the out-of-bounds error you see is often that unchecked grow failure several hundred lines earlier.**
- Size reduction's **rule zero is "cut data before code"** — run `wasm-objdump -h` on your section budget first; squeezing Code is pointless when Data is half the file. Example in Appendix L (ICU 30 MB → 780 KB). **The full arsenal and ROI table are in Appendix N, Part One.**
- The four escape routes are one idea projected four ways: **convert a "total" problem into a "partitioning along time or space" problem** — when you hit any capacity ceiling, first ask "do I genuinely need all of it at the same instant?" (see the 🔍 in Scenario 5).

Part II ends here. The machine is built, running, remembering things, and past its capacity limits. **Now to face the question that has hung over everything from the start: this machine has been downloaded, in full, onto every stranger's computer.** Turn to Chapter 9.

---



# Part III: The Moat After Everyone Can See It

# Chapter 9: Everyone Can See It — Natural Obfuscation, Two Absolute No-Go Zones, and the Hybrid Architecture

> **"If you run your program on GitHub Pages, isn't everyone able to see it?"**
> Yes. Completely. That is not a defect; it is the definition of static hosting. When a user browses your site, the browser downloads **every** HTML, JavaScript and `.wasm` file **onto their computer** and executes it there. Anyone who presses F12 can take all of it.
> **This chapter does not ask "how do I prevent that." It asks "given that you cannot, how should you design?"**

## Scenario 1: How strong is a binary's "natural obfuscation," really?

**Background.** A `.wasm` can be downloaded, but it differs fundamentally from JavaScript.

**JavaScript remains readable even after minification**: the variable names are gone, but the control flow, string constants, API calls and the whole shape of the business logic are laid out in the open. An experienced person can work out what a block of minified JS does in half an hour.

**Wasm, by contrast, is a low-level binary instruction format produced by C++, Rust or Go.** When someone obtains your `.wasm`, they do not see source; they see this:

```wat
(func (;42;) (param i32 i32 i32) (result i32)
  (local i32 i32 i32 f64)
  local.get 0
  i32.load offset=12
  local.tee 3
  i32.const 3
  i32.shl
  local.get 1
  i32.add
  f64.load
  local.set 6
  ...
  br_if 2 (;@1;)
  ...)
```

**And there is a crucial information loss here**: C++'s classes, inheritance relationships, template instantiations, Rust's trait dispatch, every variable and function name — **all erased during compilation.** What remains is a few million flat stack instructions.

**Industrial-grade defensive compilation settings:**

```toml
# Cargo.toml — the four switches a release build must have
[profile.release]
opt-level = 3        # or "z" for size
strip = true         # ★ forcibly remove every function and variable name (the name section)
lto = true           # ★ link-time optimization — cross-crate inlining scrambles the original boundaries
codegen-units = 1    # give LTO the whole picture; inlining becomes far more thorough
panic = "abort"      # drop the unwinding tables (and save size while you're at it)
```

```bash
# C/C++ (Emscripten)
emcc -O3 -flto --closure 1 -s ASSERTIONS=0 ...
# One more pass: strip again with Binaryen
wasm-opt -O3 --strip-debug --strip-producers --strip-target-features in.wasm -o out.wasm
```

**Compiled this way, even if an attacker disassembles it with reverse-engineering tools (`wasm2wat`, `wasm-decompile`, or Ghidra's Wasm loader), what they see is a pile of semantically empty `func_1`, `func_2`. Recovering the core algorithm approaches the difficulty of reverse-engineering a commercial single-player game.**

**But understand precisely what "difficult" means**, because there is a technical reality here that has to be stated:

| Level | What the attacker gets | Difficulty |
|---|---|---|
| 1. Read every plaintext string | `strings app.wasm`, or scan the Data section | **Seconds** — anyone can do it |
| 2. See the module's interface | The Import/Export sections are mandated by the specification and **can never be stripped**; signatures are laid bare | **Seconds** |
| 3. Disassemble to WAT | `wasm2wat` / `wasm-objdump -d`, yielding a readable instruction sequence | **Minutes**, with off-the-shelf tools |
| 4. Roughly recover control and data flow | `wasm-decompile` (in WABT), Ghidra plus a Wasm plugin, yielding C-like pseudocode | **Hours** |
| 5. Work out *what algorithm this is* | Requires domain knowledge plus a lot of cross-referencing | **Days to weeks** |
| 6. Recover maintainable, extensible source | There is almost no economic reason to do this | **Months or more; usually not worth it** |

**Note level 2**: Wasm's Export section is required by the specification and you **cannot** strip it — an attacker can always see that the module exports `compute_risk_score(i32, i32) -> f64`. Stripping symbols blocks levels 5 and 6; it does nothing about the first four.

> ⚠️ Authenticity Caveat
> "Wasm is an irreversible binary translation" **is false.** Wasm's binary format is **entirely public and structured**, and disassembling back to WAT is lossless, mechanical and has ready-made tooling — which makes it **considerably easier** than reverse-engineering x86 machine code (x86 also has variable-length instructions, data mixed with code, indirect jump tables; Wasm has none of that). The accurate statement is: **Wasm hides "the semantic layer of the source" (types, naming, abstraction), not "the behavioural layer of the program."** A determined analyst with domain knowledge can fully understand what a Wasm module does — **obfuscation raises the cost, not the possibility.**

> 💡 A Word to the Wise
> **Every code-protection technology sells "not worth it," never "impossible."** No obfuscation, packing or white-box cryptography can mathematically stop someone who holds the binary, has time and has determination; all of them do exactly one thing — **raise the cost of attack above the reward.** Which means the right unit for protection strength is not "how hard is it to break" but "how much can you make by breaking it." Obfuscation protecting a week-long promotional lottery can be weak; obfuscation protecting a core pricing model may never be strong enough, because the attacker's reward may be your entire market. **So every time you discuss "is this secure enough," the first question should be: how much money does a successful attacker walk away with?** That number defines the protection level you need, and it also defines the point at which you should stop investing in protection and move the asset somewhere else.

## Scenario 2: Two absolute no-go zones that break instantly

**Background.** Wasm binaries are hard to fully recover, **but if your code contains either of the following, it breaks in one second.**

### No-go zone one: hard-coded keys (API keys, private keys)

**Never** hard-code an AWS secret, an OpenAI API key, a database password or a signing key into Wasm.

**The attacker does not need to understand your algorithm** — they only need to run a binary string scanner (Linux's `strings`) over your `.wasm` and every plaintext string falls out in a second:

```bash
$ strings app.wasm | grep -Ei 'sk-|AKIA|BEGIN.*PRIVATE|password|secret'
sk-proj-aBcD1234...
AKIAIOSFODNN7EXAMPLE
-----BEGIN RSA PRIVATE KEY-----
```

**Why stripping symbols cannot save you**: `strip` removes the **name custom section** (function and variable names). **String constants live in the Data section**, which is data the program needs to execute and **cannot be stripped.** It is right there, in plaintext, waiting to be grepped.

**Common attempted fixes and why they don't work:**

| Attempted fix | Why it fails |
|---|---|
| Base64-encode the key | `strings` misses it, but `base64 -d` restores it in a second — and the decoding function is sitting right next to it |
| Split the key into pieces and concatenate | The concatenation code is in the binary; run it once dynamically and it spits the key out |
| XOR-encrypt the key | The key to the key is also in the binary (the fundamental predicament of white-box cryptography) |
| "Nobody will reverse my little project" | Automated scanners crawl GitHub Pages and npm daily; they do not pick targets |

**The only correct answer**: **keys never enter the client.** The front end asks *your* backend for a **short-lived, scope-limited** token, and only the backend holds the real key. This rule is identical for Wasm, for JS and for mobile apps — **Wasm does not make a wrong architecture right.**

### No-go zone two: core commercial secrets

If your company makes money from a proprietary "exclusive core prediction algorithm," and leaking it would end the company, **that business absolutely cannot run as Wasm on GitHub Pages.**

**The test is simple** — ask yourself one question: **if a competitor obtained this logic in full tomorrow, what would I have left?**

- "I'd still have the data, the users, the channel, the brand, the compliance credentials" → it can go on the front end.
- "Nothing" → it must be on a server, and it must be a server you control.

## Scenario 3: The industry's standard answer — the hybrid architecture

**Background.** To get both "static hosting's zero cost and unlimited concurrency" and "commercial secrecy," mature teams use a **hybrid architecture.**

**How to draw the line:**

```
┌──────────────── Client side (fully downloadable) ─────────────────┐
│                                                                   │
│  Front-end Wasm handles dense computation and pixel rendering     │
│  ─────────────────────────────────────────                        │
│  · 3D geometry, matrix math, finite element solving               │
│  · High-frequency filtering, media chunking, codecs               │
│  · Local big-data analysis, SQL queries, index search             │
│  · Standard algorithms (convolution, FFT, A*, Newton…) — all public│
│                                                                   │
│  Character: large code, heavy compute, but the algorithm is public│
│  Payoff: enormous backend compute savings, data stays local,      │
│          unlimited concurrency                                    │
└───────────────────────────┬───────────────────────────────────────┘
                            ↕  a minimal, encrypted, authenticated interface
┌──────────────── Server side (entirely under your control) ────────┐
│                                                                   │
│  The backend API handles auth, verification and the secret core   │
│  ─────────────────────────────────────────                        │
│  · Login, sessions, permission decisions                          │
│  · Billing, quotas, metering, audit logs                          │
│  · Key custody, signing, encryption and decryption                │
│  · Database reads and writes, multi-user conflict resolution      │
│  · The genuinely secret algorithm (if you have one)               │
│                                                                   │
│  Character: small computation, but catastrophic if leaked         │
│  Form: can be extremely light (Lambda or Workers is plenty)       │
└───────────────────────────────────────────────────────────────────┘
```

**The economics of this architecture are elegant**: **the compute-heavy part (expensive but not secret) is given away to the client for free; the secret part (valuable but computationally small) stays on one cheap server.** The two cost structures are exactly complementary — which is not a coincidence; it is why this became the standard answer.

**A practical line-drawing question** (more useful than any architecture diagram):

> Ask of every functional module: **"If this logic were published verbatim on a blog, would my business suffer?"**
> - No → put it in front-end Wasm and save money.
> - Yes → put it on the backend, then ask the second question: **"Is the computation it needs worth running a server for?"**
>   - Yes → a standard backend service.
>   - No → redesign it, splitting into "compute on the front end, verify on the back."

**The third question is the most valuable one.** A great deal of apparently backend-only heavy computation can be split into **the front end computing a result and the backend verifying it.** Verification is usually orders of magnitude cheaper than computation (think proof of work; think zero-knowledge proofs; think "sorting is expensive, checking whether something is sorted is cheap"). **This is the hybrid architecture's most refined layer.**

> 💡 A Word to the Wise
> **The essence of architectural design is putting different *kinds* of cost where each is cheapest to bear.** Compute is cheap but voluminous — so put it where there are infinitely many free computers (the user's browser); secrecy is expensive but small — so put it somewhere you can lock (your server). Real architectural skill is not choosing the right framework; it is **seeing what *kind* each cost is, and finding the position on its cost curve where it is flattest.** The principle extends to every engineering decision: caches go where reads dominate writes, indexes go on high-cardinality columns, async goes where waits are long, rate limiting goes closest to the source of attack. **Whenever you hesitate over "where should this go," don't ask "where is it technically possible"; ask "what kind of cost is this, and where is it cheapest to carry?"**

## Scenario 4: Thinking in reverse — being seen is sometimes the ultimate weapon

**Background.** In some domains, "everyone can see it" is not a defect; it is **the only way to establish trust.**

### The foundation of trust in end-to-end encryption

In cryptography and zero-knowledge proofs, why would a user dare put a highly sensitive private key into your web page for computation?

**Because your page is deployed on GitHub Pages, with the code entirely open and transparent.** The user can open DevTools (F12) and inspect every line of Wasm code, confirming that **you are not quietly uploading their data to a third-party server.** That is exactly the core advantage of decentralized applications.

**How that chain of trust actually holds** (rather more precise than the word "open source"):

1. **Auditable network behaviour.** The user opens DevTools' Network tab, and if your PGP tool makes **not one outbound request** after they click "encrypt," that is a fact anyone can verify.
2. **An auditable binary.** The `.wasm`'s hash can be computed, recorded and compared. Paired with reproducible builds, the community can verify that "this `.wasm` really was produced from that source."
3. **No server to compromise.** Static hosting has no application backend, therefore no SQL injection, no SSRF, and no possibility of quietly substituting responses after a breach.
4. **Changes are on the record.** Code and `.wasm` are locked into your Git commit history; anyone wanting to alter your code must go through your Git signature. **An attacker cannot quietly substitute a single response for a specific user** — they must push a commit everyone can see.

### The other side of tamper resistance

If your service has a backend, **a compromised backend can inject a phishing script into the front end** — silently, targeting specific users, untraceable afterwards. Static hosting removes that attack surface entirely.

> ⚠️ Authenticity Caveat
> "Code on GitHub Pages is locked into the Git commit record, so security is extremely high" needs three qualifications: **(a)** an attacker who obtains your GitHub account or a personal access token can push commits just as easily — **account security is the real boundary** (enable the necessary two-factor authentication and branch protection). **(b)** Supply-chain risk remains: if your build pipeline pulls in a poisoned npm package or crate, the `.wasm` you produce is itself malicious, and it will have an equally beautiful commit history. **Two Wasm-specific checks are worth remembering: run `wasm-objdump -x` over the import list (whatever capabilities the module asked for *is* its attack surface), and use reproducible builds (so the community can verify "this binary really was compiled from that source") — see Appendix O §7-2.** **(c)** "Users can inspect every line of Wasm" holds in theory and **almost never happens in practice** — barring a third-party audit or ongoing community scrutiny. **Transparency provides "auditable," not "audited."** The gap between those two is where most security incidents live.

> 🔍 Deeper Commentary — the same property has opposite signs under two business models
> The thing worth taking from this chapter is not any technique but a structural observation: **"the code can be fully inspected" is neither good nor bad in itself; its sign is determined by the business model.** For a company selling **the algorithm itself** (say, a vendor licensing a proprietary compression algorithm), transparency is pure liability — all of its value is in that code, and being seen means being worth zero. For a product selling **trust** (cryptographic tools, dApps, privacy wallets, medical data processing), transparency is the core asset — its entire value is "you can verify for yourself that I am not misbehaving," and hiding it makes it worthless. And between those two poles sit the overwhelming majority of software companies: **their value is neither in the algorithm nor in the transparency, but in data, in user relationships, in compliance credentials, in the ecosystem** — for them, code visibility is in fact **irrelevant**, and agonizing over it is an expensive distraction. **So before spending any budget on code protection, answer one question honestly: is my moat actually in the code?** Most people don't dare answer, because the answer is usually "no" — and admitting it means facing a harder question: **then where is it?** Which is precisely what the next three chapters are about.

## Chapter Summary

- Everything on static hosting is downloaded in full. **That is the definition, not a defect.** The discussion must start from "given that you cannot prevent it, how should you design?"
- Wasm's "natural obfuscation" is real, but understand the levels precisely: **plaintext strings (seconds), the Export interface (seconds, and mandated by the specification so it can never be stripped), disassembly to WAT (minutes), pseudocode recovery (hours), understanding the algorithm (days to weeks), recovering maintainable source (months, usually not worth it).** `strip` and `lto` only block the last two.
- **"Wasm is irreversible" is false** — its format is entirely public and structured, and disassembling it is **considerably easier** than reverse-engineering x86. Obfuscation raises the cost, not the possibility (see the ⚠️ in Scenario 1).
- **Two absolute no-go zones**: **hard-coded keys** (`strings` finds them in a second, the Data section cannot be stripped, and every encoding/splitting/XOR remedy fails) and **core commercial secrets** (test: if a competitor had this logic in full tomorrow, what would I have left?).
- **The hybrid architecture is the standard answer**: push the compute-heavy but algorithmically public part to the client (save money); lock the computationally small but catastrophic-if-leaked part on the server (stay safe). Its most refined layer is — **a great deal of heavy computation can be split into "the front end computes, the backend verifies," and verification is usually orders of magnitude cheaper than computation.**
- **In some domains transparency is the core asset** (end-to-end encryption, dApps, privacy tools), because it supplies auditable network behaviour, an auditable binary, no compromisable backend, and an on-the-record change history. But remember: **transparency provides "auditable," not "audited"** (see the ⚠️ in Scenario 4).
- The final question is not "how do I hide my code" but — **is my moat actually in the code?**

Theory done. The next chapter looks at a real case that took this architecture to its extreme: **`figma.wasm` is downloaded onto hundreds of millions of computers every day, so why has nobody produced a usable clone?** Turn to Chapter 10.

---



# Chapter 10: Why Figma Isn't Afraid — From a Local Private Server to the Cloud Core

> **"If Figma is Wasm, isn't Figma exposed too?"**
> Yes. `figma.wasm` is downloaded in full into every user's browser; in theory it is entirely "seen."
> **So why has no company or hacker group anywhere ever produced a working clone of Figma?**
> Because in its architecture, Figma combined **low-level machine-code obfuscation** with a **backend real-time collaboration network stack** to the point of building a **physical-grade commercial moat.**

## Scenario 1: The first line of defence — a "binary scripture" of millions of lines of C++

**Background.** Figma's core binary runs to tens of megabytes compressed, containing millions of lines of heavily optimized C++.

**The structure is completely flattened.** Figma compiles with the highest level of **Link-Time Optimization (LTO)**, so every C++ class, inheritance relationship, variable name and function name is erased (stripped) and compiled into millions of flat, low-level virtual-machine instructions like `i32.add` and `local.get`.

**A slaughterhouse for reverse engineering.** If a hacker takes `figma.wasm` to a reverse-engineering tool like Ghidra, what they see is an enormous, semantically empty low-level state machine. Recovering Figma's proprietary **Vector Networks** algorithm from those millions of instructions **costs far more effort than writing an entirely new piece of software from scratch.**

**A technical note is worth adding here, because it explains how *scale itself* becomes a defence:**

| Source of reverse-engineering difficulty | Why scale makes it exponentially worse |
|---|---|
| **LTO scattered the function boundaries** | Cross-translation-unit inlining destroys the assumption that "one function equals one logical unit." One Wasm function you see may be five original C++ functions fused together |
| **Template instantiation explosion** | C++ templates generate a specialization per type. The reverser sees twenty nearly identical functions with subtle differences, where the source had one template |
| **No types, no structures** | A `struct Node { id, parent, children, transform, style }` becomes `i32.load offset=24`. You must infer the field layout of that structure from every access site |
| **Control flow was rewritten as structured** | To satisfy Wasm's structured control flow (Chapter 2), the compiler introduces state variables and `br_table`, deforming what were clean loops and jumps |
| **Sheer scale** | Reversing 1,000 lines is a weekend project; reversing a million lines is a team-years engineering effort — **and you must simultaneously understand an entire domain** (Bézier boolean operations, font layout, incremental rendering) |

**The essence of this line is not "impossible" but "not worth it"** — rather than spending three years reverse-engineering code you will neither fully understand nor be able to maintain, you would write your own in the same time. **And that is the definition of successful defence.**

## Scenario 2: The second line — the core commercial barrier lives on the backend

**Background.** This is Figma's truly lethal moat: **Figma is not a single-user drawing program; it is a multi-user real-time collaboration system.**

**What front-end Wasm is responsible for**: dense computation only. You drag a rectangle with the mouse, and Wasm computes the geometric matrices at extreme speed, handles font layout, and renders a smooth 60 FPS frame through WebGL.

**What the backend server is responsible for**: when several people edit the same layer on the same canvas simultaneously, the data must not conflict. Figma's backend runs an entire distributed network engine based on **CRDTs (Conflict-free Replicated Data Types).**

**Why CRDTs are a genuine moat** (much deeper than "there is a server on the backend"):

```
The problem: A and B drag the same layer in different directions at the same time,
             with network latency. Both screens must end up identical, and
             neither person's operation may vanish.

Naive answer: last write wins
        → somebody's operation disappears into thin air and the user goes mad

Figma's answer: design a data structure for the document model in which operations commute
        → whatever order operations arrive in, the state converges
        → the layer tree's parent-child relationships, properties and ordering each
          need their own merge semantics
        → and it must handle offline editing, history rewind, interleaved permissions,
          and incremental sync of large documents
```

**The difficulty of this is not in the algorithm papers; it is in countless edge cases**: two people simultaneously drag A into B and B into A — does that create a cycle? Someone edits offline for three hours; how do you merge on return? How is version history expressed on top of CRDTs? **These take years and dozens of engineers of product experience to grind out, and all of it lives on the server; not one line has been downloaded into your browser.**

**The defensive boundary**: even if a hacker steals the front-end `figma.wasm`, what they have is **a soulless empty-shell renderer.** Without the powerful, confidential distributed collaboration host on the backend, that Wasm simply cannot function.

## Scenario 3: The third and fourth lines — no plaintext data, and the law

**The third: the Wasm contains no plaintext data at all**

As noted earlier, plaintext strings are what leaks most easily from Wasm (Chapter 9's first no-go zone). Figma applied extremely strict isolation here:

- Figma's Wasm contains **no hard-coded API keys, passwords or strings.**
- All user data, layer structures — even UI text labels — are streamed into Wasm's linear memory **at runtime**, over an encrypted WebSocket channel from Figma's servers.
- **A hacker who grabs only the `.wasm` finds not one letter of user data inside it.**

**This design has a side effect worth noting**: because even UI text is streamed in, the `.wasm` doesn't even tell you what a button is called — **the reverser loses even the most basic semantic anchors, and in reverse-engineering practice string constants are the most important signposts of all.** Take them away and the difficulty more than doubles.

**The fourth: commercial and legal defence**

- **Black-box asset attribution.** If some company really did ship a knock-off, Figma's legal and security teams need only analyse the other party's network traffic, or use **binary signature matching**, to determine whether specific compiled Wasm fragments of Figma's were appropriated.
- **Expensive litigation.** Once appropriation of binary code is established, it means intellectual-property litigation and legal liability, and **no legitimate technology company will take that risk.**

> ⚠️ Authenticity Caveat
> This chapter's description of Figma's architecture is **partly based on Figma's public engineering blog** (the Wasm migration, multi-user collaboration and rendering pipeline all have official write-ups) and **partly a reasonable inference from technical logic** (specific implementation details like "all UI text is streamed" and "the backend performs binary signature matching" have not been publicly confirmed by Figma). **Read it as an example of an architectural pattern, not as an authoritative account of Figma's internal design.** Separately, "Vector Networks" is genuinely a publicly promoted core technical feature of Figma, but its specific algorithm is not public.

> 💡 A Word to the Wise
> **When you hand something out generously, you must make sure it is *incomplete* once it leaves you.** Figma ships its most core rendering engine to hundreds of millions of computers every day and sleeps soundly, not because it hid anything well, but because **it split the thing in two and sends out only the half that cannot be used.** This strategy is everywhere in nature: a seed can scatter on the wind because it needs soil to germinate; every wax cell of a hive is public, and the value is in the colony's organization. The principle holds for anyone about to open-source, publish an API or ship a client: **you do not need to hide all of it; you only need to ensure that the part taken is dead without your other half.** And designing *which half is alive* is an architect's most important job.

## Scenario 4: The sharpest follow-up — what if I don't decompile it, just run it locally?

**Background.** This is the best question in the entire investigation, because it strikes at software engineering's classic "local crack and offline licensing" hole.

> **"If it can be downloaded, you wouldn't even need to fully decompile it — just download it and get it running locally. Doesn't that break Figma's business model?"**

**Looking only at the front-end code, the inference is correct**: a hacker genuinely doesn't need to decompile anything; write a simple Node.js server locally to serve the Wasm (colloquially, local splicing) and the software seems to come alive.

**And yet Figma is not afraid, because from the outset it welded its network topology and its core business model to the cloud.** Even if a hacker downloads `figma.wasm` and forces it to run on `localhost`, four physical-grade defences render the cracked version commercially worthless:

### Defence one: the files aren't stored locally at all

**Traditional single-user software (Photoshop, AutoCAD) can be perfectly cracked and used offline because their files (`.psd`, `.dwg`) sit on the user's own disk.**

**Figma's design is the opposite**: Figma's canvases and project files **do not exist on your hard drive at all.** What you see is the backend database turning layers into an enormous binary node stream and shipping it dynamically into Wasm's linear memory to be rendered.

**A physical discontinuity**: when a hacker runs `figma.wasm` on `localhost`, that virtual-machine memory is **absolutely empty.** A local private server has none of Figma's cloud PostgreSQL and distributed file storage cluster; **there is simply no project file to open or read.**

**That sentence is worth three seconds of thought**: a drawing program with no files is a blank sheet that can never open anything. **What the cracker obtains is not a free Figma; it is a blank canvas program.**

### Defence two: the core computation stays in the cloud

Figma did not compile 100% of the software's functionality into Wasm; it performed a strict **split of computation**:

| What local Wasm does | What the cloud backend does |
|---|---|
| UI interaction and real-time rendering (dragging, Bézier control, WebGL drawing) | Team permission verification |
| Geometric matrix math, font layout | Dynamic font library loading |
| | Multi-file version control and history rewind |
| | **The CRDT real-time collaboration engine** |
| | Asset libraries, component libraries, design-system distribution |

**The price of a cracked build**: a hacker running that Wasm locally obtains a **crippled single-user sketchpad** that **cannot invite a team, cannot save files, cannot auto-update, has no version history and cannot load custom fonts.** For Figma's core paying customers (enterprise design teams, product managers, front-end engineers), such a build **is entirely unusable for real production work.**

### Defence three: what they buy is not software; it is collaboration efficiency

Figma's business model is **B2B SaaS**, and its customer is not the independent designer but "an entire technology company's product development organization."

- **The enterprise's pain point.** A company pays a monthly per-seat subscription not for "the ability to draw rectangles and circles" but for **the collaboration efficiency and trust boundary** of "the designer finishes, the product manager comments online immediately, the front-end engineer copies the CSS with one click."
- **The private server's fatal flaw.** No legitimate technology company will have its employees download a hacker's locally cracked Figma to save a little subscription money. It loses the soul of real-time collaboration entirely, and exposes the company to serious security holes, IP litigation and data-leak risk.

### Defence four: the backend's authorization judgement on the client

Modern cloud applications typically deploy this line:

- **Handshake tokens.** When the front-end Wasm starts and opens a WebSocket to the backend, the backend performs dynamic fingerprinting and integrity verification on the client.
- **Instant termination.** If a hacker modifies the front-end code to bypass login, or opens a connection from an unauthorized domain (`localhost`, say), the backend's security gateway identifies a forged client and refuses to stream any canvas data, leaving the local Wasm stuck at the loading screen.

> ⚠️ Authenticity Caveat
> Defence four describes a common industry practice (origin checks, token binding, client integrity attestation), but **the specific technique of "dynamically fingerprinting the Wasm's memory hash" is technically fragile** — any client-side self-verification can be bypassed by local modification (a direct corollary of the security axiom that the client cannot be trusted). What is genuinely effective is **server-side authorization judgement** (which account does this token belong to, has it paid, does it have access to this file), not the client vouching for itself. **Placing the defensive centre of gravity on client integrity checks is a common but fundamentally untenable design.**

> 🔍 Deeper Commentary — from "prevent copying" to "prevent usefulness," the biggest paradigm shift in the history of software protection
> This entire chapter describes a paradigm shift that has already completed, and which many people have not noticed. **In the single-user era the goal of protection was "stop you copying it"** — serial numbers, dongles, packers, online activation, DRM. The defenders lost that war for thirty years, because it loses mathematically: **you hand someone a complete, independently functional thing and simultaneously demand that they not use it.** That is a self-contradictory demand; cracking is only a matter of time. **In the cloud era the goal became "make the copy useless"** — not stopping you from taking the client, but ensuring the client is an empty shell once it leaves the server. The defenders win this war, because it no longer demands anything contradictory: **take the thing freely, because the thing is not the value; the value is in the data, in the collaborative relationships, in the connection you cannot make.** And that shift yields a corollary important to every product person: **"prevent copying" is a technical problem, and technical problems are eventually solved by attackers; "prevent usefulness" is an architectural problem, and once designed correctly an architectural problem no longer needs defending.** So when you find yourself pouring effort into "how do I protect my code," that is usually a signal — **your value is still in the wrong place.** The correct move is not to strengthen protection; it is to move the value.
>
> But one deeper question remains unanswered: **if Figma's moat is no longer technology but data, collaboration and ecosystem, then once the open-source community fully commoditizes the technical part, how long does that moat hold?** Which is exactly what the next chapter takes up.

## Chapter Summary

- Figma's first line is **the reverse-engineering cost created by scale**: LTO scatters function boundaries, template instantiation explodes, types and structures vanish, control flow is rewritten — plus a million lines of volume and a domain barrier. **The work of reversing far exceeds writing it fresh, and that is the definition of successful defence.**
- The second line is **the core commercial barrier living on the backend**: the difficulty of a CRDT real-time collaboration engine is not in the papers but in countless edge cases, and not one line of it has been downloaded into the browser. **Stealing `figma.wasm` gets you a soulless empty-shell renderer.**
- The third is **no plaintext data in the binary at all** (even UI text is streamed at runtime) — which simultaneously removes the semantic signposts reverse engineering relies on most. The fourth is **the law and binary signature matching.**
- The sharpest follow-up, "don't decompile, just run it locally," is blocked by four things: **the files aren't local at all** (a blank canvas), **the core computation is in the cloud** (a crippled single-user build), **enterprises buy collaboration, not features**, and **the backend's authorization judgement on the client** (but note: client self-verification is technically untenable — see the ⚠️ in Scenario 4).
- This is a **paradigm shift that has already completed**: from "prevent copying" (a technical problem the defenders must lose) to "prevent usefulness" (an architectural problem that stops needing defence once designed right).
- **Corollary**: if you find yourself pouring effort into protecting code, that is a signal your value is in the wrong place. **The correct move is not to strengthen protection; it is to move the value.**

But this moat rests on an assumption — **that the technical barrier is high enough that nobody can reproduce it soon.** What if that assumption stops holding? Turn to Chapter 11.

---



# Chapter 11: Will the Moat Last? — The Dynamics of Commoditization and Network Effects

> **"Can that moat last?"**
> The frank conclusion: **over the long run the technical moat will get shallower, but the real commercial moat will remain impregnable.**
> This is a textbook dynamic contest between **the commoditization of technology** and **network effects.** And understanding their respective time constants matters more than understanding any individual technology.

## Scenario 1: On the technical side — the open-source community's downward strike

**Background.** Extend the timeline five or ten years, and as the WebAssembly ecosystem and edge computing explode, this moat will face two hard technical challenges.

### Challenge one: the rise of open-source alternatives (commoditization)

Figma's proudly held C++ Wasm vector rendering engine and CRDT backend collaboration engine were black magic in 2017. Today, **the open-source community has produced tools like Penpot — fully open-source, web-based collaborative design software.**

**The result**: once the core technology is no longer a handful of giants' proprietary advantage, any company can stand up a "self-hosted, entirely free" design collaboration platform inside its own private cloud (AWS/GCP) using open-source rendering and collaboration engines. **The technical barrier is being levelled by time.**

**The speed of commoditization depends on three variables** (which determine how many years your moat has left):

| Variable | Effect on commoditization speed | In the design-collaboration case |
|---|---|---|
| **Is the problem clearly defined?** | The clearer, the faster | Extremely clear — "a multi-user real-time vector editor"; everybody knows what to build |
| **Are there reusable open-source building blocks?** | The more mature, the faster | Quite mature — CRDTs have Yjs and Automerge, rendering has Skia/WebGPU, fonts have HarfBuzz |
| **Does it require scale to function?** | Things requiring scale commoditize slowest | **This is the real gate** — a single-user build can be cloned; "millions of teams are already on it" cannot |

**Note the third row**: the first two variables both accelerate commoditization; only the third does not. **That is why the technical barrier collapses and the commercial one does not.**

### Challenge two: the maturing of distributed P2P

Figma depends on expensive central cloud servers for CRDT collaboration. But if future open-source software combines **Wasm with a P2P network stack (libp2p-Wasm)**, letting designers synchronize with one another directly through browser WebRTC — **decentralized, serverless** real-time collaboration — then Figma's cloud-server barrier faces structural, physical subversion.

**The real obstacles on that road are not technical; they are four engineering realities** (the part this narrative most often skips):

1. **NAT traversal does not succeed 100% of the time.** WebRTC needs STUN for address discovery, and behind symmetric NAT (corporate networks, some mobile networks) it must fall back to a **TURN relay** — **and TURN servers cost money, bandwidth and operations.** "Serverless" in practice usually means "serverless most of the time."
2. **Offline and asynchronous collaboration.** P2P syncs directly only when both parties are online. The most common collaboration pattern of all — "I finish on Friday, you open it on Monday" — requires **a node that is always online.** That is a server; it just has a different name.
3. **Who is the source of truth?** Enterprises don't want "everyone's copy eventually converges"; they want an authoritative version, an audit trail, access control, and the ability to revoke a departing employee's access. **P2P is inherently weak at revocation** — the data is already on the other machine.
4. **Compliance.** SOC 2, ISO 27001, data-residency requirements — the first question an audit asks is "where does the data live and who can access it." **"Scattered across every employee's browser" is not an answer that passes.**

> ⚠️ Authenticity Caveat
> "The open-source community has produced Wasm-based web collaborative design tools like Penpot" — **Penpot genuinely exists and is a real open-source design collaboration tool**, but describing it as "Wasm-based" is inaccurate; its stack is primarily ClojureScript/SVG. This kind of detail slippage is common in technical narratives, and it misleads architectural decisions. **The accurate statement is: open-source alternatives do exist and are maturing, but their technical paths are not necessarily the same as the commercial products'.**

> 💡 A Word to the Wise
> **The real cost of decentralized technology is never the technology; it is that it also decentralizes the question of who is responsible.** P2P drives server cost to zero and simultaneously makes "who guarantees the data isn't lost," "who fixes the sync bug at 3 a.m.," and "who answers in court for a data breach" disappear too — **and they disappear not by being solved, but by nobody owning them.** For an individual that is freedom; for an enterprise it is unacceptable risk. This explains a long-standing phenomenon: **decentralized technology keeps succeeding in personal and community settings and keeps failing in enterprise settings** — not because enterprises are stupid or conservative, but because one of the things an enterprise buys is "somebody who can be held accountable," and a decentralized architecture eliminates exactly that.

## Scenario 2: If the technology can be copied, why does the moat still hold?

**Background.** Even as the technical barrier lowers, Figma will keep its commercial dominance, because it long ago completed a physical transition from a **technical moat** to an **ecosystem moat.**

### One: terrifying network effects and switching costs

Replacing a piece of foundational software in a modern enterprise is enormously expensive.

- **Ecosystem lock-in.** Inside Figma sit years of accumulated design assets, UI component libraries (design systems) and version history from millions of companies worldwide.
- **Workflow deadlock.** Designers are used to Figma, product managers are used to leaving comments in it, front-end engineers are used to clicking to copy code. **Even if an open-source alternative with identical performance and zero cost appeared tomorrow, a company would not dare move its whole team over** — because "retraining employees plus migrating data" costs far more than the subscription.

**The complete list of switching costs** (far longer than most people assume):

```
Direct cost: the subscription difference (the only line favouring the competitor)
─────────────────────────────────────────
Migration cost:
  · Fidelity of exporting/importing historical files (gradients, blend modes,
    auto-layout, component variants — loss is nearly certain)
  · Rebuilding the design system and component library
  · Loss of version history and comment threads (almost no tool migrates these)
  · Rewriting third-party plugins and automation
Organizational cost:
  · Retraining every employee (times headcount, times hourly rate)
  · Redefining cross-functional workflow (PM/design/front end/QA each change habits)
  · Running both in parallel during transition (the most expensive stretch)
  · Security review again, legal contracting again
Risk cost:
  · The new vendor's survival risk
  · Productivity loss during migration
  · The cost of rolling back after discovering it doesn't work
```

**That list *is* the moat.** It has nothing to do with technology, and **it increases monotonically with time in use** — which is the definition of a compounding moat.

### Two: the plugin ecosystem's downward strike

Figma lets developers write plugins in JavaScript/Wasm and hosts an active plugin and template marketplace.

**Those plugins are Figma's App Store. Even if a hacker cloned the core rendering shell, they cannot clone an ecosystem maintained by tens of thousands of independent developers worldwide.**

**Why a plugin ecosystem cannot be copied** (mechanically):

- It is a **two-sided market**: developers write plugins for the platform with users, and users pick the platform with plugins. **Cold-starting requires one side to invest for nothing first**, and a latecomer has no reason to make developers invest first.
- It produces **sunk, specific investment**: a developer who spent two years on Figma's plugin API has knowledge and code worth nothing on another platform.
- It is **distributed**: you cannot acquire it and you cannot reimplement it — it is the sum of tens of thousands of independent decisions.

### Three: enterprise compliance and trust

For a large enterprise, the top priority when buying software is not "how cool are the features" but **"information-security compliance (SOC 2 Type II), enterprise single sign-on (SSO), data isolation and round-the-clock SLA guarantees."**

**Those are core commercial barriers that no open-source private deployment or cracked build can ever provide.**

**This item is the one engineers most underestimate**, because it has no technical difficulty at all — SSO is wiring up SAML/OIDC, an audit log is a table, an SLA is a document. **But its value is not in the implementation; it is in the commitment and the liability**: a 99.99% SLA means somebody signed a contract agreeing to pay if it is missed. **An open-source project cannot sign that.**

> 🔍 Deeper Commentary — the time constants of the three moats determine where you should spend
> The most practical thing in this chapter is ordering the three kinds of moat by **how fast they erode**, because that directly determines investment order. **Type one: technical lead (time constant 1–3 years).** Any algorithm, architecture or performance advantage you build today will be matched by the open-source community within one to three years — if it has value. Which means **a pure technical lead is not worth treating as a long-term strategic investment; it is worth treating as a way to buy time.** **Type two: ecosystem and network effects (time constant 5–15 years).** Once formed they erode extremely slowly, because they are the sum of countless independent decisions and no single decision can overturn them. But building them requires scale, and scale requires a technical lead first — **so the real use of a technical lead is to buy the window in which you build an ecosystem.** **Type three: compliance, trust and the capacity to be held accountable (time constant 10 years or more, and entirely unrelated to technology).** This one is nearly immune to technological progress, because its essence is "a legal entity willing to bear responsibility" — **and no amount of AI or open source can produce an entity that can be sued.** So the strategy becomes clear: **buy time with a technical lead, build an ecosystem with the time, and support a compliance-and-trust premium with the ecosystem.** The most common failure mode is getting that order backwards — **pouring everything into defending a technical lead before you have an ecosystem.** That is a fight you are guaranteed to lose within three years, and when you lose it you will discover you built nothing.

## Scenario 3: Endgame thinking — whether it lasts depends on how you define it

**In summary, whether this moat lasts depends entirely on how you define it:**

| How you define the moat | Does it last | Why |
|---|---|---|
| **Pure technology (the Wasm code, the algorithms)** | **It does not** | No purely front-end Wasm code and no public algorithm escapes being completely commoditized and made transparent by time and the open-source community |
| **The commercial system (data + collaboration + ecosystem)** | **It lasts a very long time** | Technology is merely the *means* to lower cost and improve experience; the real commercial core is **data gravity and workflow lock-in (vendor lock-in)** |

**This is why the best companies today, when planning systems, no longer chase "absolute code secrecy" but instead demand "squeeze every drop of compute out of front-end Wasm, and weld the data relationship chain to the cloud." That is the architecture that survives the open-source era.**

**But an honest qualification has to be added**, or this chapter becomes an apologia for incumbents:

**Vendor lock-in is a moat for the vendor and a risk for the customer.** Read that switching-cost list from the customer's side and it is a **captivity assessment.** A mature technical decision-maker should use the same table in reverse when purchasing:

- Can I export my data in full? Is the export format open or proprietary?
- Once exported, is there a second place that can import it?
- How many proprietary APIs have my automation workflows welded themselves to?
- If this company triples its price tomorrow, what is my worst case?

**This is not a moral question; it is a symmetric commercial judgement**: vendors build lock-in as a matter of course, and customers assess and limit lock-in as a matter of course. **Knowing how a moat is built is also knowing how not to fall into one.**

> 💡 A Word to the Wise
> **When you hear a flawless argument about moats, ask one question: who is saying this, and to whom?** Data gravity, workflow lock-in, switching costs — the same set of concepts is **strategy** from the mouth of a VC or a CEO, **risk** from the perspective of procurement or a CTO, and **being held hostage** from the user's. All three readings are correct, because they describe different faces of the same structure. Genuine maturity of judgement is not choosing which reading to believe; it is **being able to hold all three at once and know clearly which side you are standing on right now.** The principle applies to every commercial and technical argument: **any doctrine that sounds unassailable has a position built into it that was never stated aloud** — find that position and you have actually understood it.

## Scenario 4: The larger follow-up

**Background.** Up to here, this long march through Wasm — from history to performance limits to the boundaries of commercial defence — appears to have concluded. The conclusion is clear: technology gets commoditized, but data, collaboration and ecosystem hold.

**But one assumption has gone unexamined throughout:**

> **It assumes that copying a piece of software requires many engineers, a long time, and a high cost.**

Technical commoditization is slow enough to leave you time to build an ecosystem because the open-source community needs three years to catch up. **What if those three years became three hours?**

- What if one engineer — or an ordinary person — could say a single sentence to an LLM and have it perfectly imitate and reconstruct a high-performance `figma.wasm` rendering shell in seconds?
- What if the marginal cost of writing code went to zero, and no software feature was scarce in front of an LLM any more?

**Then the premise "the technical moat has a time constant of 1–3 years" collapses** — and once it collapses, so does the first step of the strategy above, "buy time with a technical lead, build an ecosystem with the time."

**That is the question this book has actually been travelling toward.** Turn to Chapter 12.

## Chapter Summary

- **The technical moat gets shallower; the commercial moat does not.** Commoditization speed depends on three variables: whether the problem is clearly defined (accelerates), whether mature open-source building blocks exist (accelerates), and **whether it requires scale to function (the only decelerator).**
- The real obstacle to P2P "serverless collaboration" is not technical but four engineering realities: **NAT traversal needs paid TURN relays, offline collaboration needs an always-online node, enterprises need a single authoritative source and revocable access, and compliance audits do not accept "the data is scattered across everyone's browser."**
- **The switching-cost list is itself the moat**: direct cost + migration cost + organizational cost + risk cost — and it **increases monotonically** with time in use.
- A plugin ecosystem cannot be copied because it is a **two-sided market** (cold start requires one side to invest for nothing), it produces **sunk specific investment**, and it is **the sum of tens of thousands of independent decisions** (unpurchasable, unrewritable).
- Compliance and SLAs derive their value **not from implementation difficulty but from commitment and liability** — "a 99.99% SLA means somebody signed a contract agreeing to pay, and an open-source project cannot sign it."
- **The three moats' time constants determine investment order**: technical lead 1–3 years (worth using only to buy time), ecosystem and network effects 5–15 years, compliance and accountability 10 years or more and immune to technological progress. **The most common failure is getting the order backwards** (see the 🔍 in Scenario 2).
- The honest qualification: **vendor lock-in is a moat for the vendor and a risk for the customer.** The same list, read from the other side, is a captivity assessment.
- **This entire argument rests on one unexamined assumption: that copying software requires many engineers and a long time.** If LLMs compress that time toward zero, the first domino falls.

And it is falling. **When the marginal cost of writing code goes to zero, "buy time with a technical lead" has no time left to buy — so can the remaining four lines of defence hold?** Turn to Chapter 12.

---



# Chapter 12: When Tokens Cost Almost Nothing — The Time Trap of Building Your Own Wheel, and the Endgame Architecture

> **"When every app can be built or imitated by an LLM, how does a moat persist?"**
> **"Nobody wants to pay; everyone rebuilds the wheel themselves. But if tokens are cheap enough, building it yourself only costs time."**
> Those two questions strike directly at the collective anxiety of the entire software industry and venture capital: **when the marginal cost of writing code goes to zero, no software feature is scarce in front of an LLM.**
> And the second sentence's inference is correct — **it merely omits two bills hidden inside the word "time."**

## Scenario 1: Five lines of defence that still stand after code becomes free

**Background.** If the traditional technical and product-feature moats are going to collapse entirely, how does a company build a new, physical-grade moat in an era of fully automated software replication? Here are the five that remain visible.

### One: data gravity and state monopoly

**An LLM can replicate code instantly. It cannot replicate a user's accumulated data and relationship graph.**

- **Code flows; data is viscous.** AI can build you ten thousand imitation-Figma 3D rendering engines, but the millions of UI components, design systems, every revision in the version history, and the cross-departmental approval comments your company accumulated over five years all live in the original vendor's cloud database.
- **The final line.** What an enterprise buys is not that Wasm's drawing throughput; it is **the continuity of its data and a single source of truth.** The more data there is, the stronger the pull on surrounding applications — and none of that can be carried off by cloning a block of code.

**One honest technical note has to be added**: the strength of data gravity is **inversely proportional to data portability.** If the format is open, there is a complete export API, and a third party can import it, the pull is weak; if the format is proprietary, export is lossy, and there is no second destination, the pull is strong. **So "data gravity" in practice is largely a consequence of format and API design choices, not a natural consequence of data volume.** That matters equally to builders and to buyers.

### Two: workflow lock-in and the organization's collaboration network

Software's role inside a modern enterprise is essentially **a protocol for internal communication.**

- **Features are easy to copy; habits are hard to migrate.** In a ten-thousand-person technology company, everyone from the PM and the UI/UX designer to the front-end engineer and QA has built tight, intuitive cross-functional workflows around one piece of software.
- **Trust and collaboration boundaries.** Replacing software is not just changing a URL; it requires mobilizing the whole company's management overhead, retraining staff and passing security review again.

> **An LLM can build you a more perfect guitar. It cannot conjure an orchestra that already knows how to play together.**

### Three: physical-world hardware anchoring and bandwidth cost

In a world where LLMs can build all the software, physical resources like compute and bandwidth become **more** expensive, not less.

- Even if AI writes you a superb decentralized P2P collaboration system, handling **million-scale concurrency, low-latency synchronization across international data centres, enormous file storage and DDoS defence** requires real cloud hardware, real electricity bills and real bandwidth costs.
- **Those physical resources are a moat that pure-software AI cannot conjure out of code.**

**This item's weight is rising rather than falling in the AI era** — because as software gets cheap, all remaining scarcity concentrates in **things software cannot replicate**: power, land, fibre, GPU capacity, and the long-term contracts that secure them.

### Four: enterprise compliance, liability and the trust premium

In B2B this is an absolute physical law. When large enterprises (finance, healthcare, multinational technology companies) buy software, the first consideration is never "how cheap are the features" but **compliance and who carries the risk.**

- **Accountability.** If an LLM-generated knock-off leaks data through an edge-case bug, or goes down at 2 a.m. and costs the enterprise a million dollars, **who is responsible?**
- **The industrial barrier.** SOC 2 Type II certification, ISO 27001, a 99.99% SLA guarantee, and a professional customer-success engineering team on call — **that is the real reason enterprises pay a premium subscription. They are buying the trust premium of "when something goes wrong, someone can take the blame and pay."**

**This item will strengthen rather than weaken in the AI era, for a direct reason**: the more AI-generated systems there are, the more "who is responsible when this breaks" becomes a question with no answer. **And questions without answers make vendors who have answers more valuable.**

### Five: the two-way ecosystem of plugins and AI agents

When code can be seen and copied at will, the moat shifts from the software itself to **the dynamic ecosystem built around the software.**

- **App Store logic, again.** Even if AI clones the main program, the plugin market is empty.
- **Agentic lock-in.** In the coming era, autonomous AI agents will be dispatched to execute tasks across platforms. **If one platform becomes the standard API and data format that the entire industry's AI agents connect to by default, then software imitated by an LLM — having no connection to that AI ecosystem's upstream and downstream — remains an unvisited digital island.**

**The fifth is the newest and most worth watching**: it means that in the AI era, **"is your API the default choice for AI agents" becomes an entirely new axis of competition** — just as "is your app in the App Store" was in the 2010s.

### A control experiment that has already run for thirty years

**Those five lines of defence sound reasonable, but they all lack one thing: validation by time.** How do we know "value migrates to data and community once code is free" is not merely a consoling phrase?

**There is a sample that can answer that, and it has been running for thirty years.**

The Chinese MUDs of the 1990s — those text-based martial-arts worlds written in LPC — **had their complete source available for download from day one.** The world map, the NPC dialogue, the martial-arts systems, the economic rules, the description of every room, all of it in a directory called the mudlib. In those days it travelled as packed archives; today it travels as `git clone`; and now **the entire driver has been compiled to WebAssembly and you can click them open in a browser** (Appendix L).

**Zero secrecy, zero copying cost, a trivially low barrier to modification.** By the old logic that code is an asset, these things should have been drowned by better copies long ago.

**They were not.** They lived thirty years, forked and modified and reopened long after their original authors left; and today someone is still expending enormous effort restoring two hundred broken archives, converting encodings, fixing bugs, recording every change — **purely so they can be opened again.**

**That is the measured result of the five lines of defence**: what users want has never been "a copy of code that runs"; it is **that world, and the people in it.** And those two things `git clone` cannot take, and an LLM cannot generate.

> 💡 A Word to the Wise
> **When the production cost of a resource goes to zero, value does not disappear; it migrates to the scarce thing that complements it.** The printing press drove the cost of copying text to zero, and value migrated from "owning a book" to "the author's reputation" and "the editor's curation"; streaming drove the cost of copying music to zero, and value migrated from "the record" to "the concert" and "the artist." Now LLMs are driving the cost of producing code to zero, and value is migrating from "software" to **data, relationships, liability and ecosystem** — four things that share one property: **none of them can be copied, because none of them is information; they are relationships.** So whenever a technology claims to "make X free," the most valuable question is not "what happens to X's business" but — **what complements X and did not get cheaper along with it?** Wherever that answer lies is the new centre of value.

## Scenario 2: The time trap — what you need is not build time, it is the opportunity cost of debugging

**Background.** That follow-up was exactly right: "if tokens are cheap enough, building it yourself only costs time." **That inference strikes the core physical truth of software commoditization in the AI era.**

**An LLM writing a hundred thousand lines of high-performance code (including complex Wasm matrix math and a database) might take five minutes and cost a dollar in tokens.**

**But software engineering's hardest law is: writing code is 20% of the time; debugging and edge cases are 80%.**

**That road runs into two walls:**

### Wall one: the 5% of extreme scenarios

- **While the wheel turns.** The bespoke design tool or ERP the AI shaped for you runs beautifully in 95% of ordinary scenarios.
- **The physical wall.** At the 96th percentile — **the browser suddenly adjusts OPFS storage quotas after an OS update, say; or a vanishingly rare distributed state conflict emerges during multi-user connection** — your bespoke wheel jams.
- **The invisible cost.** Now you, or the AI at your instruction, must comb through those hundred thousand lines. The **attention, energy and opportunity cost** consumed by that process (time you could have spent closing deals, being with family, or developing your actual core business) instantly exceeds the few tens of dollars a month you would have paid the original vendor for "buy it and stop worrying."

**A more precise analysis is worth adding here, because it is the most practical part of the chapter:**

**When AI builds the wheel, the cost structure undergoes a critical deformation** —

```
Traditional development:
  cost of writing code  ████████░░  high (needs engineers)
  cost of debugging     ████████░░  high (needs engineers)
  → same order of magnitude, so a team naturally balances writing against fixing

AI-assisted development:
  cost of writing code  ░░░░░░░░░░  approaching zero
  cost of debugging     ████████░░  high (still needs someone who understands the system)
  → the gap reaches several orders of magnitude
  → result: code is produced far faster than code is understood
  → so "code nobody actually understands" accumulates at unprecedented speed
```

**The consequence of that deformation is not "development got faster"; it is "the growth rate of the unread codebase got faster."** And a system's maintainability depends on the latter, not the former.

### Wall two: the maintenance entropy of a system

**Software is not stone; it is a living organism.** Operating systems upgrade, browsers change API specifications (the security constraints on WebGPU and Wasm multithreading in the latest 2026 browsers shift constantly).

- **The day after you build the wheel.** You have built a perfect ERP for a trivial token cost.
- **The disaster two years later.** The W3C deprecates a low-level API your wheel depended on heavily. Your wheel breaks in front of a customer.
- **Entropy explosion.** You generated it with an LLM in one shot, and **neither you nor your staff ever genuinely understood the underlying architecture of those hundred thousand lines.** You must re-engage the LLM to understand this "two-year-old wheel," or throw the whole thing out and start again.

**That long-term maintenance debt and lifecycle cost is the biggest blind spot for people who build their own wheels.**

**Use the concrete technologies from Chapters 5–8 to make this vivid:**

| What your wheel depends on | How it might change within two years |
|---|---|
| `SharedArrayBuffer` + COOP/COEP | Isolation requirements may tighten; the behavioural inference `coi-serviceworker` relies on may be clarified or narrowed by the specification (Chapter 5 🔍) |
| OPFS's `createSyncAccessHandle` | Quota policy, eviction strategy and cross-tab lock semantics may all shift |
| `wasi_snapshot_preview1` | **Already being replaced by WASI 0.2** — not a hypothetical; it is happening |
| Emscripten's MEMFS/IDBFS | The official direction has moved to WasmFS |
| Specific Wasm features (GC, EH, tail calls) | Semantics were adjusted repeatedly during standardization |

**A hundred-thousand-line system nobody understands, meeting any one of those five, becomes a heavyweight operation of "ask the AI to re-understand the whole project."** And every time, you are betting that the AI understands it as well as it did last time.

> 🔍 Deeper Commentary — what "cheap wheels" really changes is the distribution of scale, not the total
> This section is worth pushing one step further, because it predicts the shape of the next decade of the software industry. **When the cost of building a wheel drops from "three engineers for six months" to "one person for an afternoon," what changes is not "whether people build wheels" but "what size of wheel is worth building."** In the past, a tool only you would use (personal accounting, a private CRM, a shift roster for your five-person team) was never worth developing — the fixed cost overwhelmed the return. Now it is. **So the market splits in two: on one side the long tail of "too small to buy, but now worth building yourself," and on the other the core systems "too large to build yourself, so you must buy." And the layer in between — the mediocre, single-purpose, lightweight SaaS tools — gets eliminated entirely.** The implication for practitioners is concrete: **if your product can be 90% reproduced by one person in one afternoon with AI, you are in the layer being eliminated.** And the only way out is not making the product more complex (complexity can be replicated too) but moving toward one of the two ends — **either descend into the long tail and build "tools that help other people build wheels," or ascend to the core systems that require scale, data, liability and ecosystem to function.** The middle is disappearing, at a rate set by how fast token prices fall.

## Scenario 3: Two moat shapes for the endgame

**Background.** When building your own wheel becomes this cheap, business models inevitably move toward two ultimate shapes.

### Shape one: buying insurance and an endorsement

**This is also why technology giants, who never lack the ability to build software themselves, still buy external SaaS in bulk.**

Enterprises don't want to pay for software, but they are extremely willing to **pay for a service-level agreement that says "if it breaks, someone compensates you, and someone fixes it through the night within fifteen minutes."**

**In the commercial world, paying Figma or a large ERP vendor is essentially not buying features; it is buying insurance that outsources risk.**

**This item will strengthen rather than weaken in the AI era, for a direct reason**: the more AI-generated systems exist, the more "who is responsible when this breaks" becomes a question with no answer. **And questions without answers make vendors who have answers more valuable.**

### Shape two: the standard protocol and interoperability

If every company uses an LLM to build a bespoke ERP or design tool, then when two companies need to collaborate, exchange orders or co-design a product, their self-built wheels — with entirely different data formats and API interfaces — face a severe **digital Tower of Babel** crisis.

**At that point, whoever can define the globally common "standard data protocol and ecosystem bus" holds the ultimate moat that AI cannot replicate.**

**There is a strong historical analogy here**: when desktop publishing tools bloomed, the real winner was not the best layout program; it was **PDF**. When instant-messaging apps were everywhere, what held enterprise interoperability together was **SMTP/email**. **A protocol's value comes from "everyone agreeing," and "everyone agreeing" is something an LLM cannot generate — it takes time, coordination, and the entangled interests of many parties.**

### The future splits into two kinds of people

| | Individuals and small teams | Modern industry and large enterprises |
|---|---|---|
| Behaviour | Use extremely cheap tokens to build furiously customized "micro-wheels" of their own (bespoke accounting, a tiny CRM, a purpose-built tool) | Still pay top vendors |
| Reason | The value of customization exceeds the maintenance cost (small scale, stable requirements, they fix it themselves when it breaks) | **Spending time on their own core money-printing business and outsourcing the technical entropy of building and fixing wheels is the highest-ROI decision overall** |
| Consequence | **Eliminates every mediocre, single-purpose, lightweight software company** | Concentration among top vendors rises |

> 💡 A Word to the Wise
> **Between "I can build it myself" and "I should build it myself" lies an entire lifecycle of cost.** That sentence matters more than ever in the AI era, because AI has enormously shortened the distance to "I can" while barely shortening the distance to "I should" — **maintenance, upgrades, debugging and bearing consequences: none of those four got cheaper alongside tokens.** So a dangerous cognitive gap appears: **the barrier to building a wheel collapsed; the barrier to keeping one alive did not; and most people make the decision at the moment the first barrier collapses.** There is a simple test for whether you should build: **ask "in three years, when this breaks at midnight, who fixes it — and are they still at the company?"** If that question has no clear answer, what you built is not a wheel; it is debt.

## Scenario 4: The endgame architecture — a "maintenance-free, zero-server-cost, maximum-performance" bespoke engine

**Background.** Since the conclusion is that small teams will build their own wheels, let us design that wheel — **a blueprint for a next-generation micro high-performance bespoke Wasm application, for an era in which the marginal cost of tokens has gone to zero, built to be maximally durable and minimally prone to technical debt.**

**The core idea**: **commoditize and standardize the high-maintenance-cost lower parts completely, and weld the high-compute, high-privacy, highly customized business core into the front end through Wasm.**

### Three defensive architectural principles

To keep the wheel you built from collapsing in two years under browser updates and technical entropy, three iron rules:

**Principle one: host-agnostic isolation**

Do not let Wasm code bind deeply to any specific JavaScript frontend framework (a particular version of React or Vue). Inside Wasm, keep to standard ANSI C++ or pure Rust logic, **interfacing with hardware only through standard binary Web APIs (Canvas 2D/WebGL, OPFS).**

> **That way, however the JavaScript frameworks of the future churn, your Wasm core never breaks.**

**The technical basis for this principle**: the Web platform's **standard APIs carry an extremely strong backward-compatibility commitment** ("don't break the Web" is browser vendors' first engineering principle), and **frameworks carry none.** React 18 → 19 had more breaking changes than the Canvas API has had in a decade. **Bind the core to standards and the shell to a framework, so the shell can be rewritten cheaply.**

**Principle two: a typed data protocol**

For communication between Wasm and the outside world, never use JSON — flexible, and easily collapsed. Use **Protocol Buffers or FlatBuffers** for serialization throughout.

**That guarantees that however you later use an LLM to modify front-end or backend components, the data communication protocol — the digital Tower of Babel — stays locked and never conflicts.**

**Two more technical reasons** (beyond stability):

- **FlatBuffers supports zero-copy reads** — you can read a field without deserializing, which lines up exactly with Chapter 2's "the boundary is a toll booth."
- **A schema is a machine-readable contract** — and that has a new value in the AI era: **when you ask an LLM to modify one side, the schema is the one place it cannot improvise**, making it the most effective constraint tool you hold.

**Principle three: a stateless compute window**

Treat the Wasm virtual machine as a pure "black-box processor." Read data in from OPFS, compute and render at speed inside Wasm's memory, then immediately write state back to disk and clear memory.

**That perfectly defends against wasm32's innate 4 GB out-of-memory blind spot** (Chapter 8). And because Wasm instantiation is extremely cheap (microseconds), **"throw the whole instance away when done" is a routine technique in Wasm**, not a last resort.

### The four-layer topology

```
┌─ Layer 1: interface and event dispatch (pure HTML5 / JS) ────────────────┐
│  Responsibility: capture mouse clicks and keyboard input; basic DOM layout│
│  Iron rule: this layer may contain no core computational algorithm.       │
│             It is a display panel.                                        │
│  → This layer is consumable; it is allowed to be rewritten by an LLM in   │
│    whatever framework is fashionable, every three years                    │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │ postMessage + transferable objects
                             │ (memory ownership transfer, zero copy)
┌─ Layer 2: asynchronous bus on an isolated thread (Web Worker) ───────────┐
│  Responsibility: start a dedicated Worker and load the whole Wasm storage │
│                  and compute core into it, fully isolated from the UI     │
│  Key optimization: postMessage(buffer, [buffer]) with transfer enabled    │
│                  → OS-level memory ownership transfer, overhead near zero │
│  Bonus: createSyncAccessHandle is only usable inside a Worker anyway      │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │
┌─ Layer 3: the business core Wasm engine (Rust / C++) ────────────────────┐
│  Responsibility: execute your bespoke wheel's hard functionality          │
│                  (a financial ERP's aggregation matrices, 3D trajectory   │
│                   planning, full-text search…)                            │
│  Defence: opt-level = 3, lto = true, strip = true                         │
│           even if downloaded, it holds no commercial reverse-engineering  │
│           value                                                            │
│  → This layer is an asset; the design goal is ten years untouched         │
└────────────────────────────┬─────────────────────────────────────────────┘
                             │ FileSystemSyncAccessHandle
┌─ Layer 4: high-performance persistence (OPFS Sync API) ──────────────────┐
│  Responsibility: use the Worker-exclusive createSyncAccessHandle()        │
│  Optimization: let Wasm perform disk I/O like a native C program —        │
│                fully synchronous, zero Promise overhead, chunked          │
│                sliding-window random reads and writes                     │
│                → breaking clean through the 4 GB memory ceiling           │
└──────────────────────────────────────────────────────────────────────────┘
```

**This architecture's most important property does not appear on the diagram**: it divides the system into **a consumable layer and an asset layer.**

- Layer 1 is consumable: welded to whatever framework is fashionable, **designed to be discarded and rewritten cheaply.**
- Layers 3 and 4 are assets: depending only on standard APIs and a binary protocol, **designed to be untouched for ten years.**
- Layer 2 is the firewall: `postMessage` plus a typed protocol separate the two, **ensuring the consumable layer's rot does not spread into the assets.**

**That is the only effective structure against maintenance entropy** — not making everything rot-proof (impossible), but **confining the rot to the layer you are willing to throw away.**

**A complete specification template for AI agents** (ready to use — see **Appendix H**): this chapter's architectural blueprint has been written up as a system specification you can paste straight into Claude Code or another coding agent, covering dependency setup, core implementation, Worker isolation and benchmarking in four stages, plus tailored directives for three storage mechanisms (OPFS / IndexedDB / WASI).

> 💡 A Word to the Wise
> **The right way to fight rot is not to make every part durable; it is to decide which parts are allowed to rot.** A system whose every component is designed to be unchanging for ten years will be written off entirely in year three because it cannot adapt to change; a system whose every component follows fashion will drown in endless migration by year two. Every system that lives a long time has one clear dividing line: **write the core in the most conservative, most standard, most boring technology available; write the shell in the most convenient, most fashionable, easiest-to-hire-for technology; and put an interface between them so narrow it cannot go wrong.** Unix's file descriptors, the browser's DOM, a database's SQL, the network's IP — every single thing that has lived thirty years or more has this shape. **When you design anything meant to last, draw that line before you write any code.**

## Chapter Summary

- **Five lines of defence that still stand after code becomes free**: data gravity and state monopoly, workflow and organizational lock-in, physical hardware and bandwidth anchoring, compliance and accountability, and the plugin and AI-agent ecosystem.
- The honest note: **data gravity's strength is inversely proportional to data portability** — it is largely a consequence of format and API design choices, not of data volume.
- **"Building it yourself only costs time" is a correct inference that omits two bills**: the **time trap** (writing is 20%, debugging is 80%, and AI only zeroed the former) and **maintenance entropy** (the W3C deprecates an API and nobody ever truly read those hundred thousand lines).
- The real deformation AI-assisted development causes is not "development got faster" but — **code is produced far faster than code is understood, so "code nobody actually understands" accumulates at unprecedented speed.**
- **The market splits in two**: the long tail (too small to buy, now worth building) and the core (too large to build, must buy) — **and the mediocre lightweight SaaS layer in between gets eliminated.** The way out is to move toward one of the ends (see the 🔍 in Scenario 2).
- The endgame's two moat shapes: **buying insurance (SLAs and accountability)** and **the standard protocol (PDF's and SMTP's position)** — the latter's value comes from "everyone agreeing," which an LLM cannot generate.
- **The endgame architecture's three iron rules**: host-agnostic isolation (bind to standards, not frameworks), a typed data protocol (Protobuf/FlatBuffers — the schema is your most effective constraint on an LLM), and a stateless compute window (throw away the whole instance).
- The four-layer topology's most important property does not appear on the diagram: **it splits the system into a consumable layer and an asset layer, separated by a narrow interface.** The way to fight rot is not to make everything durable but **to confine the rot to the layer you are willing to discard.**

---

## Coda: Back to 3:40 That Afternoon

That conversation began with "explain WebAssembly's history in detail" and stopped, an hour or so later, at the two words "plan it." In between came a hundred and twenty cases, four layers of storage architecture, a 4 GB ceiling, a follow-up asking "isn't it all exposed," and an argument about moats in the age of AI.

**If the whole journey compresses into one sentence, it is this:**

> **What can be downloaded will eventually be copied; what cannot be taken away is the moat.**

And the best evidence for that sentence is not in Silicon Valley; it is in a set of Chinese text games from the 1990s — **whose source has been copied in full for thirty years, and which are still here** (Appendix L).

Wasm is an outstanding technology — it pushed computation safely, cheaply and without limit to the edge, onto every computer in the world. **And precisely because it succeeded so completely, it also demolished an assumption that had held for half a century: that code is an asset.**

So this book's real conclusion is not a technical checklist; it is three questions. **Before you build anything, ask yourself:**

1. **Is this computation "heavy, public and secret-free"?** If so, compile it to Wasm, push it to the client, and the money you save is pure profit.
2. **After this thing is published verbatim, what do I have left?** If nothing, it does not belong on the client; if data, relationships, liability and ecosystem remain, let the client see whatever it likes.
3. **In three years, when this breaks at midnight, who fixes it?** Until that question has a clear answer, what you built is not a wheel; it is debt.

**If you want a harsher version of the second question**, use the form those mudlibs already answered:

> **If my source were published in full tomorrow, would anyone still be using it in thirty years?**

The garage light can go off now. **You now know how that machine runs, where it can run, and — once it is running — whose hands the value actually stayed in.**

---



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

---



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

---



# Appendix C: The GitHub Pages × Wasm Deployment Playbook

> This one is a "follow it and it runs" operations manual. Chapter 5 explains why; this explains how.

---

## 1. Decide First: Do You Actually Need Threads?

**This is the most important fork in the whole playbook**, and taking the wrong branch costs two extra weeks.

```
Does your Wasm use pthread / rayon / SharedArrayBuffer?
│
├─ No (most projects)
│   → Deploy directly. No coi-serviceworker, no special configuration at all
│   → Skip to "2. The single-threaded deployment path"
│
└─ Yes → Ask three questions in order, and stop as early as you can:
    │
    ├─ ① Does the library you depend on have a backend that doesn't need SharedArrayBuffer?
    │     Example: SQLite-Wasm's opfs-sahpool VFS (no COOP/COEP, and fastest — Chapter 7)
    │     → Yes → ★ Use it. The entire problem disappears
    │
    ├─ ② Can your workload be partitioned? (batch processing, tiled rendering, independent queries)
    │     → Yes → ★ Switch to "multi-instance isolation" (N Workers × N Wasm instances)
    │              No cross-origin isolation needed, and it breaks the 4 GB ceiling too (Chapter 8)
    │
    └─ ③ Do you genuinely need fine-grained shared state (physics simulation, graph traversal)?
          → Yes → Go with coi-serviceworker, and try COEP: credentialless first
          → Skip to "3. The multithreaded deployment path"
```

---

## 2. The Single-Threaded Deployment Path

### Step 1: Compile

```bash
# Rust
wasm-pack build --target web --release

# C/C++
emcc app.cpp -O3 -s MODULARIZE=1 -s EXPORT_ES6=1 -o pkg/app.js
```

### Step 2: Optimize (strongly recommended — usually cuts 15–40% of the size)

```bash
wasm-opt -Oz --strip-debug --strip-producers \
  pkg/your_project_bg.wasm -o pkg/your_project_bg.wasm
```

### Step 3: `index.html`

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Wasm on GitHub Pages</title>
</head>
<body>
  <input type="file" id="file">
  <p id="status">Initializing…</p>

  <script type="module">
    // ★ Must use a relative path (./), or a project page's subpath will 404
    import init, { process } from './pkg/your_project.js';

    const status = document.getElementById('status');

    async function main() {
      await init();                        // ★ Always await, or calls blow up
      status.textContent = 'Wasm ready';

      document.getElementById('file').addEventListener('change', async (e) => {
        const buf = new Uint8Array(await e.target.files[0].arrayBuffer());
        const t0 = performance.now();
        const out = process(buf);          // one call handles the whole batch — keep the boundary coarse
        status.textContent = `Done in ${(performance.now() - t0).toFixed(1)} ms`;
      });
    }
    main();
  </script>
</body>
</html>
```

### Step 4: Project layout and `.nojekyll`

```
your-repo/
├── index.html
├── .nojekyll          ← ★ an empty file, stopping Jekyll from swallowing folders starting with _
└── pkg/
    ├── your_project.js
    └── your_project_bg.wasm
```

### Step 4.5: If your site has a CSP

In CSP's eyes, compiling Wasm is dynamic code generation, and **without an allowance it is simply blocked**:

```http
Content-Security-Policy: script-src 'self' 'wasm-unsafe-eval'
```

`'wasm-unsafe-eval'` (Chrome 97+ / Firefox 102+ / Safari 16+) **permits Wasm compilation without permitting `eval()`**.
**The symptom is a CSP violation rather than a Wasm error** — which bites especially often in two situations: being embedded inside someone else's iframe, and browser extensions.

### Step 5: Turn on Pages

1. Push to GitHub.
2. **Settings → Pages → Build and deployment**.
3. Choose the source branch (`main` or `gh-pages`) and folder (`/` or `/docs`).
4. Wait a few minutes and visit `https://<account>.github.io/<project>/`.

---

## 3. The Multithreaded Deployment Path (needs `SharedArrayBuffer`)

### Step 1: Get `coi-serviceworker.js`

Fetch the script from its open-source repository and place it at the site root.

### Step 2: Include it at the very top of `<head>`

```html
<head>
  <script src="coi-serviceworker.js"></script>   <!-- ★ must be the first script -->
  <meta charset="UTF-8">
  ...
</head>
```

**Behaviour**: on the first load the Service Worker has not taken over yet, so the script reloads the page once automatically; from the second load onward every response carries COOP/COEP and `self.crossOriginIsolated === true`.

### Step 3: Verify

```javascript
console.log('crossOriginIsolated:', self.crossOriginIsolated);   // must be true
console.log('SharedArrayBuffer:', typeof SharedArrayBuffer);     // must be "function"
```

### Step 4: Enable threads at compile time

```bash
# Emscripten
emcc app.cpp -O3 -pthread -s PTHREAD_POOL_SIZE=4 \
     -s ALLOW_MEMORY_GROWTH=1 -o pkg/app.js

# Rust (rayon + wasm-bindgen-rayon)
RUSTFLAGS='-C target-feature=+atomics,+bulk-memory,+mutable-globals' \
  rustup run nightly wasm-pack build --target web -- -Z build-std=panic_abort,std
```

### ⚠️ What breaks once isolation is on

> 💡 **Try `COEP: credentialless` before `require-corp`**: the former allows loading cross-origin resources that haven't opted in (it simply requests them without credentials), which sharply reduces the damage in the table below. Solutions of the `coi-serviceworker` kind can usually be configured to synthesize either one.

| What breaks | Why | Fix |
|---|---|---|
| Google Fonts / external CDN fonts | No `Cross-Origin-Resource-Policy` header | Self-host the fonts same-origin |
| Third-party images | Same as above | Self-host, or confirm the other side supports CORS and add the `crossorigin` attribute |
| YouTube / external iframes | Blocked by COEP | Switch to `credentialless` mode (limited support) or remove them |
| Ad / analytics scripts | Same as above | Usually there is nothing to do but remove them |

**This is exactly why Chapter 5 says "confirm you really need threads first" — the cost is real.**

---

## 4. Automated Build and Deploy with GitHub Actions

**Far cleaner than committing `pkg/` by hand**: source and artifacts stay separate, and every push is a reproducible build.

```yaml
name: Build & Deploy Wasm to Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          targets: wasm32-unknown-unknown

      - name: Cache cargo
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            target
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}

      - name: Install wasm-pack
        run: curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh

      - name: Build
        run: wasm-pack build --target web --release

      - name: Install binaryen & optimize
        run: |
          npm install -g binaryen
          for f in pkg/*_bg.wasm; do
            wasm-opt -Oz --strip-debug --strip-producers "$f" -o "$f.opt"
            mv "$f.opt" "$f"
          done
          ls -lh pkg/*.wasm

      - name: Assemble site
        run: |
          mkdir -p dist
          cp index.html dist/
          cp -r pkg dist/
          # copy coi-serviceworker.js too if you need threads
          [ -f coi-serviceworker.js ] && cp coi-serviceworker.js dist/ || true
          touch dist/.nojekyll

      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

---

## 5. Troubleshooting Table (ordered by how often people hit it)

| Symptom | Cause | Fix |
|---|---|---|
| `.wasm` 404 | `pkg/` was ignored by `.gitignore` | Commit it, or build with Actions instead |
| `.wasm` 404 | An absolute path `/pkg/...` was used, but the site lives under the `/repo/` subpath | Change everything to relative paths `./pkg/...` |
| `.wasm` 404 | Jekyll ignored a folder starting with `_` | Put an empty `.nojekyll` at the root |
| `Incorrect response MIME type` | The server didn't return `application/wasm` | GitHub Pages serves the `.wasm` extension correctly; if it fails, check the filename really ends in `.wasm` |
| `SharedArrayBuffer is not defined` | No cross-origin isolation | Bring in `coi-serviceworker` (see §3) |
| `undefined is not a function` when calling | You forgot `await init()` | Put every call after `await init()` |
| First load works; after deploying a new build you get the old one | Service Worker cache | Handle `skipWaiting()` / `clients.claim()` in the SW, or add a version query string to resources |
| Works locally, crashes in production | Locally you were on `localhost` (treated as a secure origin); production isn't | Verify HTTPS and the isolation state |
| Crashes outright on phones | The memory ceiling is far lower than on desktop | Lower the initial memory, switch to streaming in chunks (Chapter 8) |
| First load is extremely slow | The module is too large | `wasm-opt -Oz` + Brotli + module splitting with lazy loading |

---

## 6. Pre-Launch Checklist

```
□ wasm-opt -Oz has been run, and the size is acceptable (front end: < 30 MB recommended, < 10 MB ideal)
□ Section budget reviewed with wasm-objdump -h (if Data dominates, cut data first, not flags)
□ twiggy top / dominators confirms there is no unexpected size culprit
□ The release build has strip = true / lto = true (Chapter 9)
□ strings app.wasm | grep -Ei 'sk-|AKIA|password|secret' comes back empty  ★ most important
□ Every path is relative
□ .nojekyll exists
□ await init() precedes every call
□ TypedArray views are re-acquired after memory.grow
□ Large files go through streaming chunks; nothing is read in all at once
□ Heavy computation runs in a Worker; the main thread is never blocked
□ If using threads: crossOriginIsolated is true, and third-party resources have been checked for COEP damage
□ You checked first whether a backend exists that needs no SharedArrayBuffer (e.g. SQLite's opfs-sahpool)
□ If the site has a CSP: script-src already includes 'wasm-unsafe-eval'
□ The server returns Content-Type: application/wasm and Content-Encoding: br (pre-compressed .wasm.br beats on-the-fly)
□ The .wasm uses a content-hashed filename (stable URL → return visits hit the code cache)
□ When measuring, the cross-origin isolation state was consistent (timers are coarsened when not isolated)
□ With several Workers, postMessage the WebAssembly.Module rather than recompiling in each
□ A symbol-bearing build artifact is kept for reconstructing stacks from production issues
□ It has been tested on the target devices (including low-end phones), not only on the dev machine
```

---



# Appendix D: The Hundred-Case Catalog of Static-Page Wasm (Part 1) — Cases 1–35

> **This catalog's provenance and calibration**: the original conversation produced "120 classic cases." On comparison, **19 of them turned out to be renumbered restatements** (26–30 restate 21–25; 32–35 restate 21–24; 61–65 restate 46–50; 66–70 restate 36–40), leaving **101 genuinely distinct entries**. This catalog renumbers them 1–101 in order of first appearance, with the original number in parentheses.
>
> **Authenticity tags**:
> 🟢 **Verifiable** — the project really exists, with an official Wasm build or a widely used Wasm port.
> 🟡 **Upstream real, Wasm port unverified** — the upstream C/C++/Rust project is entirely real, but a Wasm version under this name has not been verified.
> 🔴 **Illustrative construction** — no such project was found; the technical path is sound, and the entry stands as "this road can be walked."
>
> **All performance numbers are the claims made in the original conversation** and have not been independently verified for this book. Read them by Chapter 4 Scenario 1's standard: **trust the direction, doubt the multiplier.**

---

## I. Audio, Video and Signal Processing

### 1. (originally 1) FFmpeg.wasm — Pure front-end media transcoding and editing 🟢

**Pain point**: Traditional transcoding depends on the server side (AWS MediaConvert or a self-hosted FFmpeg cluster), with three pain points: extremely high bandwidth and compute costs, private files that must be uploaded, and no offline capability.

**How it works**: Emscripten compiles FFmpeg's millions of lines of C into `ffmpeg.wasm`. It uses a "main thread (UI) + Web Worker (compute)" model. JS writes the video into Wasm's virtual filesystem **MEMFS** as an `ArrayBuffer`; JS calls the exported command-line interface (`ffmpeg -i input.mp4 output.avi`), and Wasm decodes and encodes the in-memory bitstream directly; when finished, the output is read back out of MEMFS and turned into a Blob URL for download.

**Performance**: Claimed to reach **60%–80%** of native C with SIMD and threads (`SharedArrayBuffer`).

**Advantages**: Absolute privacy (data never leaves the device), zero hosting cost, support for nearly every mainstream format.
**Disadvantages**: Constrained by browser memory limits (usually 2–4 GB), so it cannot handle tens of gigabytes of 4K footage; the first load requires downloading roughly 20–30 MB of module; the multithreaded build **must have COOP/COEP configured**, which on GitHub Pages means relying on `coi-serviceworker`.

**Competitors**: Cloud transcoding (unlimited compute, high cost, privacy risk); pure-JS media libraries (video.js/jsmpeg, capable only of simple playback and containers, unable to carry H.264/H.265 core codecs).

---

### 2. (originally 2) Rust-uBlock — A Wasm ad-blocking match engine 🟡

**Pain point**: A modern ad blocker must match tens of thousands of network requests in real time against hundreds of thousands of filter rules (EasyList). Doing that much string comparison and regex matching in pure JS consumes a lot of CPU and causes small stutters (jank) on tab switches.

**How it works**: The core matching logic is written in Rust and compiled to Wasm through `wasm-bindgen`. It uses a **rule tree** structure: a highly optimized trie plus a Bloom filter built inside linear memory. When a request is intercepted, the URL is passed into Wasm, which performs a binary search over hundreds of thousands of rules within microseconds and returns an allow/block boolean.

**Performance**: Claimed **3–5× faster** than pure JS for string comparison and rule lookup, with stable memory usage, entirely avoiding the GC pauses caused by JS constantly creating string objects.

**Advantages**: Noticeably lowers CPU load and power draw on low-end devices (mobile browsers); the rule database sits compactly in linear memory with little fragmentation.
**Disadvantages**: Passing URL strings across the JS↔Wasm boundary frequently incurs boundary conversion overhead (string encoding/decoding), so a carefully designed shared-buffer mechanism is required.

**Competitors**: Pure-JS blocking engines (easy to develop, mature ecosystem, but visibly higher memory and CPU peaks past 500,000 rules); the browser's native declarative blocking (Manifest V3's `declarativeNetRequest`, highest performance but a limited rule count and no custom complex logic).

---

### 3. (originally 3) v86 — An in-browser x86 hardware emulator 🟢

**Pain point**: To run Linux or Windows 95 on a web page, the traditional approach was a backend virtual machine (KVM) streaming the screen over VNC — high server cost, high latency, poor interactivity.

**How it works**: The CPU emulation, memory management and disk controller (IDE) core are compiled to Wasm. Wasm emulates x86's registers, physical memory and interrupt vector table inside linear memory, and includes a **JIT compiler that translates x86 machine code into Wasm instructions on the fly** (see Chapter 6 Scenario 4). For display output, VRAM data is copied out and rendered by JS through Canvas/WebGL; keyboard and mouse events are captured by JS and fed into Wasm's interrupt handlers.

**Performance**: Claimed to run Linux in the browser at roughly early-Pentium speed, booting to a terminal within seconds and running classic 3D games such as Doom smoothly.

**Advantages**: Fully decentralized — GitHub Pages need only host the image (say a 10 MB Linux ISO); the boot state can be serialized out to a file and saved at any time.
**Disadvantages**: Cannot use the host's hardware virtualization (Intel VT-x); it is pure software emulation, so **it cannot run modern heavyweight 64-bit operating systems**.

**Competitors**: Backend Docker/VNC (good performance, good compatibility, but cost grows linearly with users and it cannot work offline); pure-JS emulators (like the early jor1k, more than 10× slower for lack of precise bit operations and compact memory, with screen tearing and audio stutter).

---

### 4. (originally 4) ONNX Runtime Web (Wasm) — A front-end AI inference engine 🟢

**Pain point**: For face recognition, background blur or speech-to-text on the web, the traditional approach sends data back to a backend GPU — carrying privacy problems, GPU cost and network latency.

**How it works**: Microsoft compiled the open-source ONNX Runtime C++ core to Wasm. Developers put the `.onnx` model on GitHub Pages; JS loads the model and the multimedia input (a webcam frame, say) and passes the image matrix into Wasm; Wasm implements the neural network's matrix multiplications and activation functions. The core optimizations are **Wasm SIMD** hardware acceleration and **Web Worker** multi-core parallelism.

**Performance**: Claimed **10–20× faster** than a pure-JS neural network once SIMD and threads are on; lightweight models (MobileNet, YOLOv8-nano) can get a single inference under 30 milliseconds, reaching 30 FPS real-time analysis.

**Advantages**: Compute is spread across users' browsers, so static hosting alone gives you a massively concurrent AI service; works offline, and the data stays safe.
**Disadvantages**: Large models (a several-hundred-megabyte LLM or Stable Diffusion) take too long to download; CPU inference still lags WebGPU acceleration.

**Competitors**: TensorFlow.js (its WebGL/WebGPU modes exploit the GPU better, but ONNX Runtime Wasm has sturdier cross-platform compatibility and is the fallback on devices without good GPU drivers); a backend Python API (supports huge models, but is expensive under high concurrency).

---

### 5. (originally 5) DuckDB-Wasm — An in-browser analytical SQL database 🟢

**Pain point**: When a page needs to process, analyze and filter millions of records of big data (CSV, Parquet, logs), loading it all into JS memory produces so many objects that you get OOM or long GC pauses. Standing up a backend database for a demo dashboard is far too heavy.

**How it works**: The C++ core of DuckDB — an embedded **columnar** SQL database — is compiled to Wasm in full. It uses a **vectorized execution engine**, reading big data as a stream and storing it directly in linear memory in the compact Arrow columnar format. The user types standard SQL, and Wasm's internal query optimizer scans memory at high speed in parallel. **The prettiest part is remote reading**: it natively supports issuing **HTTP Range Requests** against remote Parquet/CSV, fetching only the byte ranges it needs (see Chapter 6 Scenario 4).

**Performance**: Claimed to complete a 10-million-row aggregate query in **100–200 milliseconds**, more than **60× faster** than iterating JS arrays (`Array.filter.reduce`).

**Advantages**: Lets a static page host a powerful BI dashboard; can query remote data without downloading the whole file.
**Disadvantages**: Data lives in memory by default and vanishes when the tab closes (it can be persisted to OPFS/IndexedDB, subject to quota).

**Competitors**: SQLite-Wasm (excellent at transactional OLTP, but columnar DuckDB wins outright on million-row OLAP statistics); pure-JS data processing libraries (Lodash, Crossfilter, out of their depth past a million rows).

---

### 6. (originally 6) SQLite-Wasm — A complete ACID relational database in the browser 🟢

**Pain point**: Complex front-end applications (offline notes, expense tracking, a PWA mail client) had only IndexedDB to lean on — an asynchronous, event-driven API that is tedious to write and supports no multi-table JOINs, no prepared statements and no strong ACID transactions.

**How it works**: SQLite's own team compiles the standard C source to `sqlite3.wasm` via Emscripten. **The most elegant part is the persistence layer (VFS)**: the project developed a dedicated virtual filesystem using **OPFS (Origin Private File System)** or IndexedDB as the underlying storage medium (mechanism detailed in Chapter 7). The execution architecture isolates work in a Web Worker: the main thread sends SQL by `postMessage`, the Wasm engine inside the Worker manipulates the B-tree indexes and data pages in memory, and writes back synchronously through the VFS.

**Performance**: Claimed that on OPFS, single inserts and complex JOINs are almost indistinguishable from local native, with read/write throughput **2–4× faster** than JS-wrapped IndexedDB, and crash safety guaranteed.

**Advantages**: The front end gets full standard SQL and transaction support; the `.db` file can be packaged and downloaded directly, making backup and migration trivial.
**Disadvantages**: Wasm plus glue runs to a few hundred KB; if the browser lacks OPFS, falling back to an IndexedDB-simulated VFS drops write performance sharply.

**Competitors**: Native IndexedDB (no download, no size cost, but no relational queries or transaction capability); a backend database (handles massive data and multi-tenancy, but costs a server and offers no true offline capability).

---

### 7. (originally 7) Pyodide — A Python scientific computing runtime in the browser 🟢

**Pain point**: Python rules data science (NumPy, Pandas, Matplotlib), but running Python on a web page or building an interactive teaching platform previously meant standing up a Jupyter kernel on a server — expensive, and prone to collapse under concurrency.

**How it works**: The CPython core plus a large set of C-extension scientific libraries (NumPy, Pandas, SciPy, scikit-learn) are compiled to Wasm in full. **Two-way type bridging**: a JS `Array` can be read by Python as a `list`/`dict` and vice versa; a chart drawn by Matplotlib can be turned into a binary stream and rendered by JS onto a `<canvas>`.

**Performance**: Pure Python code runs at roughly **1/3–1/5** of native (an interpreter inside a virtual machine — two layers of abstraction); but once you call NumPy/Pandas C kernels, matrix work approaches **70%** of native.

**Advantages**: Genuinely zero backend cost, with a complete data science environment running on the client; excellent for interactive teaching and data-visualization dashboards.
**Disadvantages**: **The initial load is catastrophic** — CPython plus base libraries easily runs 30–50 MB. Mitigations: on-demand package loading (`micropip`), persistent Service Worker caching, or switching to MicroPython/Wasm.

**Competitors**: Google Colab / a backend JupyterHub (strong performance, GPU support, but high operating and scaling costs); Brython/Skulpt (pure-JS Python interpreters, tiny files but only syntax emulation — **they cannot run C-extension scientific libraries**).

---

### 8. (originally 8) Canvas-GIMP / wasm-img — High-performance image and filter processing 🟡

**Pain point**: For pixel-level processing of high-resolution photos on the front end (blur, sharpen, colour matrices, edge detection), iterating tens of millions of RGBA pixels in JS causes severe GC stutter, and single-threaded computation makes the page throw up "this page is unresponsive."

**How it works**: GIMP's core algorithms (or OpenCV's C++ imaging modules) are compiled to Wasm. **Shared memory architecture**: after Canvas reads the image's `ImageData`, the pixel pointer is written directly into Wasm linear memory, avoiding bulk JS↔Wasm copying. **Parallel pixel computation**: SIMD is enabled internally (one instruction handling floating-point work on four pixel channels at once), and the image is cut into tiles distributed to Wasm threads inside several Workers.

**Performance**: Claimed that for a 4K photo (about 12 million pixels), a high-order filter such as Gaussian blur usually finishes in under **50 milliseconds**, **15–30× faster** than iterating arrays in pure JS.

**Advantages**: Extreme compute performance, squeezing the multi-core CPU dry; photos never need uploading to any server, meeting medical-grade privacy requirements.
**Disadvantages**: The algorithms are fixed inside the compiled module, so JS cannot easily inject or modify a filter algorithm dynamically — flexibility is lower.

**Competitors**: Pure CSS filters / the Canvas 2D API (hardware-accelerated by the browser and extremely fast, but limited to basic operations, with no custom complex matrix math or advanced background removal); cloud image APIs (Cloudinary and the like — powerful but metered, with latency and privacy risk).

---

### 9. (originally 9) OpenTTD-Wasm — Porting a large simulation/management game 🟢

**Pain point**: OpenTTD contains tens of thousands of lines of C++, extensive pathfinding (A*), vehicle AI and dynamic map rendering. The community wanted "click and play" while overcoming cross-platform audio, input and graphics compatibility.

**How it works**: Emscripten plus **SDL2** compiles the entire C++ game to Wasm. SDL2's low-level drawing calls are translated automatically into WebGL; mouse, keyboard and audio are bridged through the Web Audio API and DOM events. Saves and MOD resources sync to browser storage through Emscripten's **IDBFS** (an IndexedDB-backed virtual filesystem).

**Performance**: Claimed to hold a steady **60 FPS** even under the heavy load of thousands of trains and aircraft computing routes simultaneously on the map.

**Advantages**: Extremely convenient porting — a twenty-year-old game comes back to life with almost no changes to the C++ core logic; entirely free and backend-free.
**Disadvantages**: The first entry requires downloading a fairly large asset pack (sprites and sound effects); sandbox restrictions make LAN multiplayer with the native build hard for the web version.

**Competitors**: Rewriting in JS/HTML5 (an enormous engineering effort, and JS's dynamic typing and GC drop frames badly when pathfinding for thousands of game objects in real time).

---

### 10. (originally 10) swc-wasm — Ultra-fast JS/TS transpilation and bundling 🟢

**Pain point**: Modern front ends must transpile new-syntax JS/TS to compatible versions (Babel's job). As projects grow, Babel — written in Node.js — crawls when parsing tens of thousands of AST nodes, and builds routinely take minutes.

**How it works**: `swc` is a high-performance JS/TS transpiler written in **Rust**. Compiled to Wasm, it can be deployed straight onto a static page as a live transpiler (playground) or a micro-bundler. The user types modern TS, JS passes the string into Wasm memory, and the Rust parser builds an AST with a highly optimized memory layout, performing minification and transpilation. All string analysis and tokenization happen entirely inside Wasm, avoiding the JS engine's constant object collection.

**Performance**: Claimed **20–40× faster** than pure-JS Babel; even in a single-threaded browser environment, transpiling ten thousand lines of complex TypeScript takes only a dozen milliseconds.

**Advantages**: Ideal for building a backend-free online IDE, code formatter or static analysis platform.
**Disadvantages**: Compared with the native local binary, the Wasm build is about 2× slower thanks to the sandbox and cross-boundary string passing (but still far faster than Babel).

**Competitors**: Babel (an extremely rich ecosystem and plugin set, but limited by the JS language and outclassed on large-scale transpilation).

---

## II. Search, Parsing and Toolchains

### 11. (originally 11) Sonic-Wasm — A pure front-end full-text search engine 🟡

**Pain point**: A static blog (Hexo, Hugo, Jekyll) or a large documentation site on GitHub Pages needs full-text search. Backend options (Elasticsearch, Algolia) cost money or require operations; pure-JS options (Lunr.js) load megabytes of JSON index into memory and get slow during fuzzy search and reranking, triggering GC and typing latency.

**How it works**: The core of Sonic, a lightweight search engine written in Rust, is compiled to Wasm. It builds a highly compact **inverted index plus Bloom filter** in linear memory, with data laid out as a binary byte stream. On query, JS passes the keyword through a shared buffer, and Wasm runs bitmask operations and N-gram term-frequency analysis internally, returning document IDs in microseconds.

**Performance**: Claimed that when searching an index of tens of thousands of articles (roughly 50 MB of text), a complex fuzzy match completes in **2–5 milliseconds**, more than **10× faster** than Lunr.js, using a quarter of the memory of the JS version.

**Advantages**: Brings millisecond, backend-free full-text search to a static page; zero operating cost.
**Disadvantages**: When content changes often, the front end must regenerate and download a large binary index regularly.

**Competitors**: Algolia/Elasticsearch (support massive data and dynamic weighting, but cost money or operations); Lunr.js/Fuse.js (nothing to learn, but CPU peaks are too high when searching long texts past tens of thousands of words).

---

### 12. (originally 12) Web-Wireshark (Wasm-Pcap) — Network packet analysis 🟡

**Pain point**: Diagnosing a network fault means opening a `.pcap` capture file. Traditionally that meant uploading it to a backend for a C program (libpcap) to parse — but pcaps usually contain a company's sensitive network topology and packet contents, so uploading them to the cloud is a serious risk.

**How it works**: A C/C++ network analysis library (libpcap, or Rust's pcap-parser) is compiled to Wasm. **Streaming binary parsing**: the user drops in a several-hundred-megabyte `.pcap`, and JS reads it as a stream through the File API and writes it into Wasm memory; Wasm takes it apart bit by bit, reconstructing the protocol tree from Ethernet through IP, TCP and UDP up to the application layer (HTTP/DNS), and hands the structured data back to JS to render as an interactive collapsible tree.

**Performance**: Claimed to parse a 100 MB pcap of hundreds of thousands of frames in about **200 milliseconds**, **15–20× faster** than pure JS.

**Advantages**: 100% privacy-safe — corporate packets never leave the device; static hosting alone provides a diagnostic tool engineers worldwide can use for free.
**Disadvantages**: Sandbox restrictions mean Wasm cannot call the local NIC for **live capture**; it can only analyze static capture files.

**Competitors**: Local Wireshark (the most complete, with live capture, but it requires installation and can't be embedded in a page to share); pure-JS packet parsing libraries (lacking efficient binary pointer manipulation and struct alignment, and prone to OOM on large files).

---

### 13. (originally 13) OpenCascade-Wasm — An industrial 3D CAD modelling kernel 🟢

**Pain point**: An industrial 3D modelling kernel (the kind inside AutoCAD or SolidWorks) is usually millions of lines of heavily optimized C++. To edit complex industrial parts (`.STEP`, `.IGES`) on a web page, a pure-JS library (Three.js) can only handle surface meshes and **cannot compute exact boundary representation (B-Rep), boolean operations or surface fitting at all**.

**How it works**: The open-source industrial geometry kernel **OpenCascade (OCCT)** is compiled to Wasm in full. Exact geometric mathematical models (3D curves, NURBS surfaces) are stored in linear memory, and every boolean topology operation, fillet and shelling algorithm runs entirely inside Wasm. Once computed, the result is tessellated dynamically into triangles and the vertex buffer handed straight to WebGL/WebGPU for hardware-accelerated rendering.

**Performance**: Claimed that complex 3D solid boolean trimming reaches **75%** of native C++, responding to mouse operations within a few hundred milliseconds.

**Advantages**: Overturns the limit that "the web can view 3D but not model it," running geometric algebra as exact as desktop software on a static page.
**Disadvantages**: The module is enormous (**10–15 MB even compressed**), so the first load takes a long time.

**Competitors**: Three.js/Babylon.js (fine for visualization, but without the mathematics of industrial geometric topology and solid modelling); Onshape (commercial cloud CAD, powerful but computing on a backend GPU cluster with a steep subscription).

---

### 14. (originally 14) FontForge-Wasm — Font editing and conversion 🟡

**Pain point**: Optimizing web fonts often means subsetting a large font (a 15 MB `.TTF`/`.OTF`, keeping only common characters), compressing it (to `.WOFF2`) or editing outlines. Building that as a web service burns bandwidth uploading large fonts, and processing enormous numbers of Bézier curves on the backend is expensive.

**How it works**: FontForge's C-language font processing and layout engine is compiled to Wasm. **Vector outline parsing**: the TrueType parser inside Wasm reads the binary structure tables (`glyf`, `head`, `cmap`) and loads each character's quadratic/cubic Bézier outlines into memory. **Dynamic subsetting**: after the user selects the characters they need, Wasm removes the unselected glyph data directly in memory, recomputes every internal pointer and offset, and calls Brotli to package the result on the fly.

**Performance**: Claimed that trimming a huge font containing 20,000 Chinese characters and exporting `.WOFF2` takes only **1–2 seconds**, nearly **25× faster** than pure JS.

**Advantages**: Fonts are processed entirely locally, consuming none of the developer's bandwidth.
**Disadvantages**: Font design involves complex OpenType feature layout (kerning and the like), and emulating that C-language rendering on the front end demands highly optimized glue code to keep the UI responsive.

**Competitors**: Backend Python (fontTools — a mature ecosystem but it needs a server); opentype.js (capable of basic reading and drawing, but insufficient in performance and completeness for high-order WOFF2 compression and thorough subsetting).

---

### 15. (originally 15) WebXm-Tracker — Chiptune (MOD) synthesis and playback 🟡

**Pain point**: The chiptunes of the 80s and 90s (`.XM`, `.MOD`, `.IT`) are only tens of kilobytes because what they store is score instructions and sampled instruments rather than waveforms. Converting them to MP3 destroys that size advantage; decoding and mixing them live in pure JS easily produces popping artifacts from main-thread interference.

**How it works**: A C-language chiptune decoding engine (libmodplug, or a Rust tracker engine) is compiled to Wasm. **It uses an AudioWorklet architecture**: Wasm is loaded onto the high-priority audio rendering thread, fully isolated from the main UI thread. Inside Wasm, 44,100 samples are computed per second, note, volume and portamento effect commands are parsed in real time, instrument waveform frequencies are modified dynamically, and the computed floating-point audio buffer is fed straight to the output.

**Performance**: Claimed that Wasm's compute time on the audio thread is usually under **0.1 milliseconds** (far below the 2.9-millisecond hard deadline for a 128-sample block), so the music stays perfectly smooth even while the main page is loading a large image.

**Advantages**: Extremely low CPU and memory overhead, faithfully recreating hardware-level retro music; a few tens of kilobytes and the music starts.
**Disadvantages**: Audio pointer manipulation demands extremely high memory safety — one array overrun and the whole audio thread goes silent and dies, and debugging is hard.

**Competitors**: Traditional MP3/AAC playback (over 100× larger, and unable to control tracks dynamically or visualize the score in real time); pure-JS audio decoders (disrupted by irregular GC pauses, and prone to pops and dropouts whenever the page animates or scrolls).

---

### 16. (originally 16) Web-GnuPG (Wasm-GPG) — Front-end PGP encryption and digital signing 🟡

**Pain point**: PGP is the gold standard for encrypting mail and files, but traditional GnuPG requires installing a local CLI, which is a high barrier. Making it a web service by uploading the private key or plaintext to a backend destroys the core principle of end-to-end encryption entirely. Pure-JS crypto libraries are extremely slow generating a 4096-bit RSA key pair, often freezing the tab.

**How it works**: The C-language GnuPG (or Rust's Sequoia-PGP) is compiled to Wasm. **Bignum optimization**: the cryptographic core involves intensely dense modular exponentiation over very large integers, and Wasm uses `i64` instructions for register-level bit manipulation directly in linear memory. **Random-number safety**: Wasm cannot access a hardware entropy source directly, so the architecture injects entropy into the Wasm engine by having JS glue call the browser's native `crypto.getRandomValues()`.

**Performance**: Claimed **85%** of native C when generating 4096-bit RSA or processing hundreds of megabytes of AES-256; key generation takes only 1–2 seconds, **8–10× faster** than early openpgp.js and without freezing the UI.

**Advantages**: A genuinely zero-knowledge architecture — keys and plaintext never leave the device; static hosting makes it very hard for an attacker to tamper with the front-end crypto logic through a backend vulnerability.
**Disadvantages**: Sandbox restrictions mean it cannot read the local GPG keyring, so each use requires manually importing a key or storing it in the browser (the latter carries risk).

**Competitors**: Local Gpg4win / the GnuPG CLI (the most secure and best integrated, but requires installation); pure-JS crypto libraries (SJCL, forge — lacking low-level memory alignment and bit-operation optimization, with CPU peaks that are too high on large files).

---

### 17. (originally 17) esbuild-wasm — An ultra-fast front-end compile-and-bundle playground 🟢

**Pain point**: If a code playground on a static page uses the JS versions of Webpack or Babel, the user waits seconds after each edited line, destroying the live-feedback experience.

**How it works**: `esbuild` is an ultra-fast bundler written in **Go**. The project uses Go's Wasm target (`GOOS=js GOARCH=wasm`) to compile the whole esbuild core into `.wasm`. It emulates an in-memory filesystem internally; JS passes several files' code in as strings, and esbuild instantly destructures and bundles them into a single JS/CSS output.

**Performance**: Claimed to bundle a React project of 50 modules and roughly ten thousand lines in **30–50 milliseconds** in the browser, more than **30× faster** than pure-JS Rollup/Babel.

**Advantages**: Gives online IDEs and technical documentation live transpilation with no backend Node.js compile service at all.
**Disadvantages**: **Wasm modules compiled from Go are generally large (usually 8–12 MB)** and include Go's own runtime, which is unfriendly to first load (a textbook instance of Chapter 3's "language runtime burden").

**Competitors**: Babel-Standalone (smaller, but limited by JS's dynamic typing and GC and outclassed when parsing large volumes of code); the native esbuild binary (exploits multiple cores and is 3–5× faster than the Wasm build, but cannot run inside a browser).

---

### 18. (originally 18) Tesseract.wasm — Multilingual pure front-end OCR 🟢

**Pain point**: OCR traditionally means uploading to a cloud API (Google Cloud Vision and the like), with metering and privacy problems (the risk of leaking ID cards and invoice photos). Pure-JS character matching algorithms are far too inaccurate for complex backgrounds or handwriting.

**How it works**: The C++ open-source OCR engine Tesseract is compiled to Wasm via Emscripten. Since 4.0 Tesseract has used an **LSTM**-based engine; the Wasm module loads the trained language pack (`.traineddata`) directly and performs matrix multiplication in linear memory. **Dynamic language pack loading**: the engine itself stays light, and JS downloads the corresponding binary feature pack only when the user picks a language.

**Performance**: Claimed that with SIMD on, recognizing a text-covered A4 image takes about **0.5–1.5 seconds** at over 95% accuracy, reaching **70%** of native C++.

**Advantages**: 100% offline capable, with data staying entirely in the browser; static hosting alone gives you an infinitely concurrent, zero-operations, free text extraction tool.
**Disadvantages**: Language training packs are large (a Chinese pack often runs **10–40 MB**), so the wait is long on mobile or a poor connection.

**Competitors**: Commercial cloud OCR APIs (the most accurate, but metered per call and unable to protect privacy); basic pure-JS image recognition (with no machine learning model behind it, it loses all ability on skewed or noisy images).

---

### 19. (originally 19) WebManiac-GameBoy — A hardware-accurate Game Boy emulator 🟡

**Pain point**: Early pure-JS emulators ran into a wall emulating hardware clocks and precise interrupts — JS's `setInterval` is imprecise, and page scrolling or background tasks throw audio and video badly out of sync, producing dropped frames and shrill pops.

**How it works**: A precise Game Boy emulator core written in Rust is compiled to Wasm. **Cycle-accurate clock emulation**: the Game Boy's LR35902 CPU executes about 4.19 million clock cycles per second, and Wasm emulates register state, memory-mapped I/O (MMIO) and the PPU's scanlines in a strictly cycle-accurate loop. **Double-buffered rendering**: Wasm maintains the raw 160×144 pixel buffer in linear memory and, on each frame's V-blank interrupt, copies it quickly into JS's Canvas `ImageData`, synchronizing to the 60 Hz refresh rate with `requestAnimationFrame`.

**Performance**: Claimed that emulating the hardware clock consumes under **2% of CPU**, locking the picture solidly to 60 FPS with perfectly smooth 8-bit audio.

**Advantages**: Perfect hardware fidelity with flawless audio/video sync; game state can be exported as a binary snapshot with one click and restored in milliseconds.
**Disadvantages**: Sandbox restrictions preclude advanced rumble feedback on some USB controllers and special hardware peripherals.

**Competitors**: Pure-JS emulators (dynamic type conversion and irregular GC pauses cause slight tearing and audio dropouts); local RetroArch (the most feature-complete, but requires installation and configuration).

---

### 20. (originally 20) Libzen-Wasm (MediaInfo) — Deep multimedia metadata parsing 🟡

**Pain point**: Video professionals often need to inspect a media file's detailed parameters (codec, bitrate, frame rate, colour space, audio tracks, subtitle packaging). Modern containers (`.MKV`, `.MP4`) may scatter metadata at the very start or the very end of the file, and uploading gigabytes of video or transferring it in frequent chunks burns enormous bandwidth.

**How it works**: C++ MediaInfo (built on libzen and libmediainfo) is compiled to Wasm. **Range reads**: when the user drops in a 4 GB video, JS uses the HTML5 File API to **extract only the header and footer of the file structure precisely** (the MP4 `moov` atom, for instance). **Binary structure destructuring**: JS passes those fragments into Wasm, and the parser inside takes apart the container's binary tables within microseconds, returning hundreds of structured parameters as JSON.

**Performance**: Claimed that parsing a 5 GB 4K video with multiple audio channels and embedded subtitles takes no more than **10 milliseconds** and under 5 MB of memory.

**Advantages**: Analyzes videos of any size on the front end in seconds with minimal resources; saves 100% of server bandwidth.
**Disadvantages**: For corrupted containers or rare formats, if the exception handling wasn't fully optimized at compile time, the module can crash outright.

**Competitors**: mp4box.js (usually MP4 only, helpless before MKV, AVI, MOV and FLV); backend FFprobe (powerful, but I/O and CPU saturate under concurrency, and the user endures a long upload).

---

### 21. (originally 21) Viz.js / Web-Graphviz — Automatic graph layout for the DOT language 🟢

**Pain point**: Graphviz generates flowcharts, topology diagrams and dependency graphs from DOT scripts, and its core value is a powerful automatic layout algorithm. Before Wasm, converting DOT to SVG live on a page meant a round trip to a backend; pure-JS graph libraries (vis.js) lack the compute for thousands of nodes and edges and freeze the page for seconds.

**How it works**: Graphviz's C-language layout engine (including the dot, neato and twopi engines) is compiled to Wasm via Emscripten. The user types DOT syntax and JS passes the string in through a memory pointer; Wasm builds the graph's adjacency matrix and runs hierarchy assignment, force-directed stress relaxation and coordinate allocation; when finished it generates a standard SVG text stream directly in linear memory, which JS extracts and inserts into the DOM.

**Performance**: Claimed that a complex dependency graph of 500 nodes and 2,000 edges lays out in **30–50 milliseconds**, more than **20× faster** than pure-JS layout algorithms.

**Advantages**: Brings live diagram rendering to a static documentation platform, with no backend drawing server.
**Disadvantages**: Graphviz's native code is large, so the compiled Wasm is usually **2–3 MB**.

**Competitors**: Mermaid.js (the most popular on the front end, small and with a good ecosystem, but clearly inferior to Graphviz-Wasm in both performance and layout quality on very large dense topologies).

---

### 22. (originally 22) Web-7z (p7zip-wasm) — A high-ratio decompression engine 🟡

**Pain point**: When a page has to handle `.7z`, `.rar` or `.tar.xz` — high compression ratio formats — the traditional route uploads to a backend to unpack. Large archives devour bandwidth, and the dense computation of decompression saturates backend CPU fast.

**How it works**: p7zip (7-Zip's Linux C/C++ port) is compiled to Wasm. **Streaming decompression architecture**: the user drops in a `.7z`, and JS reads the binary byte stream through the File API and writes it into Wasm's MEMFS. Based on the header, Wasm calls the corresponding LZMA, LZMA2 or PPMd algorithm, doing dictionary matching and decompression directly in linear memory, then returns each file's binary stream to the front end to make a download link.

**Performance**: Claimed that unpacking a standard 50 MB `.7z` reaches **70%–80%** of native C for LZMA2 decoding.

**Advantages**: Fully decentralized — the trade secrets inside the archive never leave the device; it solves the pain point that static pages cannot handle the complex `.7z` format.
**Disadvantages**: Bounded by the memory ceiling — **if unpacking needs a huge dictionary (a 1 GB dictionary size, say), Wasm cannot get enough linear memory and the tab crashes** (Chapter 8's 4 GB ceiling made concrete).

**Competitors**: JSZip (a popular front-end ZIP library, small, but **with no 7z/RAR support at all** and very slow on large files).

---

### 23. (originally 23) Web-Sass (sass.wasm / grass) — CSS preprocessor compilation 🟢

**Pain point**: Offering live SCSS compilation on a static page (an online sandbox, a teaching platform) previously required a Node.js environment. Early JS versions were unbearably slow parsing complex `@import`, nested selectors and mixins.

**How it works**: `grass` (written in Rust) or `libsass` (C++) is compiled to Wasm. The user edits SCSS, JS converts the string to binary and passes it in; the high-speed parser inside Wasm tokenizes, builds a compact AST in memory, performs variable substitution, nesting expansion and reduction, and assembles the final CSS in linear memory to return.

**Performance**: Claimed that compiling thousands of lines of SCSS with complex mixins and variable arithmetic takes only **5–10 milliseconds**, **15–30× faster** than the pure-JS version — "compile as you type."

**Advantages**: Delivers a compilation experience nearly identical to the local native binary; an online compilation tool on a static page needs no backend API at all.
**Disadvantages**: If the SCSS depends on many remote images or external stylesheets, the sandboxed Wasm needs external JS to handle those network requests, increasing glue complexity.

**Competitors**: The official Dart Sass compiled to JS (perfect compatibility, but without strict type optimization its compile performance on large files trails the Wasm build).

---

### 24. (originally 24) Web-Gnuplot — A scientific statistical plotting engine 🟡

**Pain point**: Gnuplot is the well-known command-line scientific plotting program, supporting complex mathematical formula plotting, three-dimensional surface fitting and statistical analysis. Sharing and live-tweaking scripts on the web previously meant standing up a Linux server to generate images and send them back; under concurrency the backend buckles under 3D mesh matrix computation.

**How it works**: The long-lived C-language Gnuplot is compiled to Wasm in full. The user types a command (`splot sin(x)*cos(y)`, say), the C-language syntax parser inside Wasm parses the mathematical expression directly, and hundreds of thousands of floating-point operations run in linear memory to generate the 3D vertex matrix. Gnuplot's native plotting terminal output is redirected: Wasm emits a Canvas 2D/WebGL drawing command stream directly, or returns high-resolution SVG.

**Performance**: Claimed that the dense floating-point matrix work for 3D surface fitting and lighting reaches **80%** of native C, redrawing a detailed chart within **20 milliseconds**.

**Advantages**: Recreates thirty-odd years of accumulated industrial-grade scientific plotting on a free static page; the data stays entirely local.
**Disadvantages**: Without a modern UI wrapper, Gnuplot's command-line logic has a very steep learning curve for ordinary users.

**Competitors**: Chart.js / ECharts (good for business and financial charts, but no comparison at all when faced with hardcore academic formula plotting, complex arithmetic or high-precision 3D scientific fitting).

---

### 25. (originally 25) Web-Esprima / oxc-wasm — JS syntax analysis and AST generation 🟢

**Pain point**: Building a web-based code editor (Monaco Editor), linter or highlighting engine requires parsing JS into an AST in real time. When the user pastes in a huge third-party library of tens of thousands of lines, a pure-JS parser causes severe GC stutter creating hundreds of thousands of AST node objects.

**How it works**: An ultra-fast JS parser written in C++/Rust (part of `oxc`, for instance) is compiled to Wasm. **Object-free AST layout** (this is the core of Wasm's dominance over JS here): while parsing, Wasm creates no object per node; instead AST nodes sit compactly in a contiguous memory block (a memory pool), with nodes linked to each other by 4-byte integer indices alone. Tokenization and syntax tree construction happen entirely inside the Wasm sandbox, exposing only the core result to the front end as a `TypedArray`.

**Performance**: Claimed to parse a 5 MB JS file in **15–20 milliseconds** (a pure-JS parser needs 300–500 milliseconds) — more than **20× faster**, with zero GC impact on the main thread.

**Advantages**: Brings smooth live syntax checking and error highlighting to front-end editors.
**Disadvantages**: The AST lives in Wasm memory, so if front-end JS wants to traverse that tree deeply and often, cross-boundary serialization/deserialization adds overhead.

**Competitors**: Babel Parser (the most powerful with the richest plugin set, but far behind in memory consumption and parse speed when handling large sources purely on the front end).

---

### 26. (originally 31) Web-Jq (jq-wasm) — High-speed JSON filtering and transformation 🟢

**Pain point**: `jq` is the command line's JSON power tool, able to slice, filter and map complex JSON through a powerful DSL. But offering an online JSON playground on the web with a pure-JS approach means that a several-hundred-megabyte JSON log creates millions of JS objects, causing GC stutters of several seconds or an outright tab crash.

**How it works**: The C-language jq core is compiled to Wasm via Emscripten. **Streaming memory destructuring**: when the user pastes a huge JSON or uploads a file, JS writes the byte stream straight into Wasm's contiguous memory through a shared buffer. **DSL engine parsing**: Wasm parses the filter expression live (`.items[] | select(.status == "active")`, say) and traverses the compactly laid-out binary JSON tree in memory at high speed (**creating no JS objects**), returning the result as a string.

**Performance**: Claimed that a 100 MB-class complex JSON file parses, filters and transforms in **80–150 milliseconds**, **15–25× faster** than pure JS.

**Advantages**: Fully decentralized, zero backend cost, second-scale processing of large JSON; meets the requirement that highly sensitive logs never leave the device.
**Disadvantages**: JS↔Wasm string boundary passing adds overhead when handling extremely frequent tiny queries, so large batches must be used to optimize.

**Competitors**: Native `JSON.parse` plus a custom filter (light for small files, but memory and CPU peaks explode exponentially for large log structures past a few hundred thousand lines).

---

### 27. (originally 36) OpenCV.js (Wasm) — Industrial computer vision and matrix math 🟢

**Pain point**: For real-time image processing on the web (recognizing the outline of a handheld credit card, say), pure-JS graphics libraries (tracking.js) are woefully unoptimized; JS lacks compact multidimensional matrix layouts and direct pointer control, so iterating the millions of pixels in 1080p triggers severe GC stutter and cannot meet interactive real-time requirements.

**How it works**: Millions of lines of C++ OpenCV core are cross-compiled to `opencv.wasm` via Emscripten, with the underlying `cv::Mat` matrix structure mapped to the front end. **Zero-copy image flow**: the `ImageData` pointer for each frame captured from an HTML5 video is written directly into Wasm linear memory, eliminating copy overhead. **Hardware-level operator acceleration**: SIMD is enabled internally, so a single CPU instruction handles greyscale conversion (Canny), Gaussian filtering or Sobel operators on four pixels at once.

**Performance**: Claimed that on a 720p live video stream, ORB feature detection takes only **12–15 milliseconds**, easily holding 60 FPS — more than **20×** the pure-JS version.

**Advantages**: Perfect privacy protection (ID scanning and the like never leave the device); static hosting alone deploys a massively concurrent CV application.
**Disadvantages**: OpenCV is vast, so the compiled Wasm plus glue is still **6–9 MB** compressed, usually requiring dynamic lazy loading.

**Competitors**: tracking.js (small but crude, lacking high-order matrix transforms, feature matching and optical flow); cloud vision APIs (accurate, but with latency, metering and privacy risk).

---

### 28. (originally 37) solc-wasm — The Ethereum smart contract compiler 🟢

**Pain point**: Blockchain developers must turn Solidity into EVM bytecode. Traditionally that meant installing the `solc` binary, or having the front end send code to a remote server to compile — and for a web environment like Remix IDE, depending on a backend compile server means operating cost and easy collapse under load or attack.

**How it works**: The Ethereum Foundation compiles the official C++ Solidity compiler into `soljson.wasm`. When the user clicks compile, JS passes the Solidity source string into Wasm memory; Wasm performs lexical analysis, parsing, AST construction and type checking, and emits EVM-compatible bytecode, the ABI interface definition and source maps directly in linear memory.

**Performance**: Claimed that compiling a standard ERC-20 contract takes only **100–300 milliseconds**, reaching **80%** of the local native binary.

**Advantages**: Gives a DApp's online IDE (Remix, for instance) fully backend-free, zero-operations compilation; code compiles locally, so unpublished contracts can't be intercepted by a third party.
**Disadvantages**: Because it includes a large optimizer and cryptographic components, `soljson.wasm` is very large (usually **10–15 MB**), so first load is slow.

**Competitors**: A backend compile API (the page loads fast, but there is downtime, service interruption and contract leakage risk).

---

### 29. (originally 38) xterm's Wasm parsing plugin — Million-line log terminal rendering 🟡

**Pain point**: Watching live container logs scroll by on the web (a Kubernetes console, a cloud shell), the backend sends hundreds of kilobytes of ANSI escape sequences per second. Doing all that string parsing, UTF-8 decoding and screen buffer management, mainstream xterm.js triggers severe GC and freezes the UI outright.

**How it works**: The terminal's most critical component — the **ANSI sequence parser and state machine** — is rewritten in C++/Rust and compiled to Wasm as a performance plugin for xterm.js. **Raw binary byte stream passthrough**: raw bytes arriving over WebSocket skip JS string conversion and are written into Wasm memory as a `Uint8Array` directly. **An efficient state machine**: Wasm recognizes control sequences like `\x1b[31m` at high speed with a statically typed integer state machine, maintaining the virtual screen's two-dimensional array in binary form in linear memory, and notifying JS's WebGL rendering layer only of what changed per frame.

**Performance**: Claimed **10–15× higher throughput** than pure-JS regex parsing in an extreme "log storm" test; a steady 60 FPS while processing 500,000 lines of ANSI characters per second, with CPU usage down 70%.

**Advantages**: Definitively solves the problem of a web terminal freezing under heavy log traffic; substantially improves the battery life and smoothness of running a cloud console on a low-end laptop.
**Disadvantages**: Solidifying originally flexible JS parsing logic into Wasm makes it less agile to upgrade if a new non-standard escape extension protocol appears.

**Competitors**: The pure-JS xterm.js parser (perfect compatibility and easy to extend, but it OOMs on millions of lines of CI/CD build logs).

---

### 30. (originally 39) HarfBuzz.js (Wasm) — A complex text shaping and layout engine 🟢

**Pain point**: "Text shaping" turns Unicode characters into a font's glyphs at precise geometric coordinates, and it is indispensable for scripts with complex ligatures and dynamic forms such as Arabic, Indic languages and Thai. The browser's native layout is strong, but in Canvas 2D/WebGL, a web game engine or online PDF generation, developers cannot call into the browser's layout internals, so complex scripts come out misplaced, mis-broken or with broken ligatures.

**How it works**: **HarfBuzz** — the world's foremost open-source text shaping engine, written in C++, and the underlying dependency for both Chrome and Android — is compiled to Wasm. JS passes the Unicode string to lay out plus a binary pointer to the OpenType font into Wasm; Wasm parses the font's `GSUB` (glyph substitution) and `GPOS` (glyph positioning) tables deeply in linear memory, computes each character's X/Y offset and advance precisely, and returns a structured array of glyph IDs and coordinates that WebGL draws directly.

**Performance**: Claimed that for large-scale Arabic or Thai layout, the ligature mathematics is nearly indistinguishable from the local system in efficiency, handling hundreds of thousands of characters per second and more than **30× faster** than a JS-simulated layout engine.

**Advantages**: Guarantees 100% pixel-identical and correct layout of complex scripts across every browser, canvas and exported PDF, filling a major gap in web graphics.
**Disadvantages**: An extremely vertical, specialized tool with a very low-level API; a front-end engineer needs deep typographic knowledge to integrate it successfully.

**Competitors**: Home-grown layout on opentype.js (supports only simple Latin letters, and produces entirely wrong results for context-aware Arabic or Indic scripts).

---

### 31. (originally 40) Z-Music (libgme-wasm) — Retro console audio chip emulation 🟡

**Pain point**: Playing early consoles' native music (the NES's Ricoh 2A03, the SNES's SPC700, the Mega Drive's YM2612; formats such as `.nsf`, `.spc`, `.vgm`) is enchanting — these files are only a few kilobytes because they are instructions driving hardware directly. But emulating those chips' filters and waveform generators in pure JS produces constant popping from imprecise timers and dynamic typing, at an unreasonably high CPU cost.

**How it works**: The C++ audio chip emulation library **Game Music Emulator (GME)** is compiled to Wasm and deployed with an **AudioWorklet**. **Thread isolation**: Wasm loads onto the highest-priority dedicated audio thread, entirely undisturbed by UI rendering, scrolling or main-thread blocking. **Register-level hardware emulation**: Wasm emulates those old chips' internal register state in linear memory, computing 44,100 waveform floats per second at 44.1 kHz and mixing square, triangle, noise channels and PCM samples dynamically.

**Performance**: Claimed that emulating a complex 16-bit SNES audio chip consumes under **0.5% of CPU**, with audio buffer computation taking under 0.05 milliseconds.

**Advantages**: Perfectly revives retro hardware audio at minimal overhead; a few kilobytes of audio file and a whole game soundtrack starts playing.
**Disadvantages**: A corrupt, non-standard ROM easily triggers memory overruns, so strict sandbox bounds checking is required.

**Competitors**: Traditional MP3/OGG playback (over 1000× larger, and losing the hardware-level interactive fun of toggling tracks live or changing tempo without changing pitch); pure-JS audio emulators (disturbed by GC pauses, dropping out and popping the moment the user scrolls the page).

---

### 32. (originally 41) Stockfish.wasm — A world-class chess AI engine 🟢

**Pain point**: Stockfish's competitive edge lies in dense alpha-beta pruning search, NNUE neural network evaluation and massive bitboard arithmetic. Providing strong analysis on the web previously meant sending it to a backend CPU server fleet — enormous maintenance cost, and compute saturated instantly when tens of thousands of players analyzed at once.

**How it works**: The C++17 Stockfish source is compiled to Wasm via Emscripten as the front-end analysis engine for mainstream chess sites (Lichess, for instance). **Multithreaded and SIMD architecture**: Web Workers plus `SharedArrayBuffer` provide massively parallel search, with SIMD internally accelerating NNUE's weight matrix multiplications. **Bitboard passthrough**: board state is represented as `i64` in linear memory, and bitmask plus bit-scan instructions enumerate millions of legal moves instantly.

**Performance**: Claimed that with SIMD and 4 cores, search speed (NPS) reaches **75%–85%** of native C++, computing millions to tens of millions of positions per second on the front end at depths past 20 plies.

**Advantages**: Genuinely decentralized — static hosting alone provides world-class AI analysis at zero server compute cost; usable offline, with no network latency.
**Disadvantages**: NNUE weight files typically run from a few to a dozen-odd megabytes; heavy search saturates the user's CPU, heating the device and draining the battery. **And it is the textbook case of needing `SharedArrayBuffer` — on GitHub Pages it must be paired with `coi-serviceworker`.**

**Competitors**: Pure-JS chess engines (capable only of elementary calculation and utterly outclassed in complex endgames); backend cloud analysis (unlimited compute, but unable to serve millions of players' free concurrent demand).

---

### 33. (originally 42) Web-GnuTLS (Wasm-TLS) — A front-end TLS micro network stack 🟡

**Pain point**: When building a backend-free, decentralized web application (a P2P network, a browser-side MQTT console), the front end sometimes needs to establish a secure TLS connection directly with an external TCP/UDP server (through a WebSocket relay). But the browser's own `fetch` security mechanism is very strict and **does not let developers customize certificate validation, cipher suite negotiation or private CA registration during the TLS handshake**.

**How it works**: C-language GnuTLS is compiled to Wasm in full, building a "micro encrypted network stack" entirely under front-end control on a static page. **Memory-buffer network I/O (BIO mode)**: Wasm never calls a system network API directly; instead it writes TLS handshake packets into a ring buffer in memory, and external JS extracts and sends them over WebSocket or a WebRTC data channel. **Cryptographic operator acceleration**: the TLS handshake involves heavy asymmetric (ECDHE, RSA) and symmetric (AES-GCM, ChaCha20-Poly1305) work, and Wasm performs bignum multiplication at high speed inside the sandbox using 64-bit integer operations and compact layout.

**Performance**: Claimed a complete TLS 1.3 handshake and key exchange in no more than **5–10 milliseconds**, with throughput on par with the local C build and more than **10× faster** than pure-JS crypto libraries.

**Advantages**: Breaks the browser's black-box hold on the network security protocol layer, allowing custom certificate validation and mutual TLS (mTLS) on a static page; keys never leave the device.
**Disadvantages**: A TLS network stack is extremely complex and the Wasm module is fairly large; and because it cannot touch sockets directly, complex JS glue must be written for packet forwarding and reassembly.

**Competitors**: Pure-JS cryptographic protocol libraries (forge and the like, able to emulate parts of the TLS flow, but with GC stutter under high-frequency encrypted packet throughput and inadequate TLS 1.3 support and security).

---

### 34. (originally 43) QuickJS-Wasm — A secure sandboxed "JS inside JS" runtime 🟢

**Pain point**: Online playgrounds, low-code platforms and applications with user-authored plugins need to "run user-supplied JavaScript" on the front end. Using `eval()` or `new Function()` directly lets user code reach `window`, `document` and `cookie`, a fatal XSS risk. Even with iframe isolation, an attacker can still freeze the main thread solid with `while(true)`.

**How it works**: **QuickJS** — the small, efficient C-language JS engine written by Fabrice Bellard — is compiled to Wasm in full, achieving the elegant trick of "running another JavaScript inside JavaScript." **Double sandbox**: the user's script does not execute in the browser's native V8; it is passed into QuickJS-Wasm as a string and interpreted inside Wasm's enclosed linear memory sandbox, **entirely unable to reach any DOM or sensitive information on the outer page**. **Time and memory quotas**: the Wasm module installs an interrupt handler internally, and if user code exceeds its quota (500 milliseconds, say) or requests too much memory, it is terminated immediately — perfectly preventing an infinite loop from freezing the page.

**Performance**: Although it interprets, QuickJS is extremely light, running standard JS inside Wasm at millions of instructions per second — enough for complex business logic, unit tests or data transformation to run smoothly.

**Advantages**: Brings a military-grade secure code execution environment to a static page, eliminating XSS and infinite loops entirely; a few hundred kilobytes compressed, so it loads fast.
**Disadvantages**: As an "interpreter inside an interpreter," it cannot match JIT-optimized native V8 (usually 10–20× slower) and is unsuited to heavy graphics or matrix work.

**Competitors**: Native `eval()` / iframe sandboxing (highest performance, but a fragile security boundary that is very hard to defend against advanced exploits and malicious infinite loops); a JS interpreter written in JS (similar size, but far behind QuickJS in syntax coverage and the completeness of memory quota control).

---

### 35. (originally 44) Web-GSL — The GNU Scientific Library's numerical analysis and matrix routines 🟡

**Pain point**: Engineering, physics and quantitative finance routinely need complex numerical computation: high-order matrix eigenvalue solving, numerical solutions to ordinary differential equations (ODEs), least-squares fitting, fast Fourier transforms (FFT), sampling from complex statistical distributions. Traditionally that relies on the authoritative C library **GSL**. Writing those formulas by hand over JS float arrays is not only slow — for lack of operator overloading, compact memory alignment and fast pointer arithmetic — but also prone to producing scientifically wrong results through lost floating-point precision.

**How it works**: The vast, rigorous C-language GNU Scientific Library core is compiled to Wasm in full, creating an online scientific numerical workbench. **Exact memory layout (BLAS integration)**: efficient basic linear algebra subprograms (CBLAS) are integrated internally, with multidimensional matrices laid out as strictly aligned contiguous double-precision floats (`f64`) to maximize L1/L2 cache hit rates. **Zero GC interference**: every differential equation approximation and nonlinear least-squares iteration runs entirely inside Wasm's internal memory pool.

**Performance**: Claimed **80%–90%** of native C when solving the eigenvalues of a 500×500 matrix or running a million-point FFT, **20–40× faster** than pure-JS numerical libraries.

**Advantages**: Brings an install-free, entirely free industrial-grade numerical computation platform to education, research and financial engineering, at precision matching GNU's international scientific standards.
**Disadvantages**: GSL's API is highly academic and extremely low-level, offering none of the chained calls or JSON interfaces modern front-end developers expect, so a fairly heavy JS wrapper layer is required.

**Competitors**: math.js (fine for everyday algebra and ordinary plotting, but no comparison at all for hardcore industrial ODE solving, large sparse matrices and high-precision numerical fitting).

---

> **Summary of this part (1–35)**: The first 35 cases cluster in three areas — **audio/video signal processing, data querying, and parsers and toolchains** — and form **the most verifiable stretch** of the Wasm ecosystem: FFmpeg.wasm, v86, Pyodide, DuckDB-Wasm, SQLite-Wasm, esbuild, swc, OpenCV.js, Tesseract.js, solc, Stockfish, HarfBuzz, QuickJS and Viz.js are every one of them real, widely used projects.
> Their shape is remarkably consistent: **move a mature C/C++/Rust core into linear memory, hand off to JS through zero-copy views, and add SIMD and Workers where needed**. The only difference is which wall each of them hits — **FFmpeg hits the memory ceiling, Pyodide hits download size, Stockfish hits `SharedArrayBuffer`, OpenCascade hits module size**.
> The next part (36–70) moves into **compression, geography, cryptography, graph algebra and reverse engineering**, where the proportion of 🟡 entries begins to rise.

---



# Appendix E: The Hundred-Case Catalog of Static-Page Wasm (Part 2) — Cases 36–70

> Authenticity tags and reading method are the same as Appendix D. 🟢 Verifiable · 🟡 Upstream real, Wasm port unverified · 🔴 Illustrative construction. **All performance numbers are claims from the original conversation and have not been independently verified.**

---

## III. Fonts, Media Codecs and Compression

### 36. (originally 45) Web-Graphite (Graphite2-Wasm) — Smart typesetting for minority-language scripts 🟡

**Pain point**: Many of the world's special scripts (Burmese, Khmer, North American indigenous writing systems, and non-Latin typefaces with complex contextual shaping rules) use the **Graphite typesetting system** — a smart-font technology more flexible than OpenType, with its own rule description language. Firefox has native Graphite support, but **Chrome and Safari have none at all**, so pages presenting minority-culture material come out completely scrambled in different browsers.

**How it works**: The C++ Graphite2 smart-font layout core is compiled to Wasm, providing a browser-universal layout solution in a static environment. JS passes the complex Unicode text and the Graphite-capable `.ttf` into Wasm memory; the Graphite2 engine inside executes the complex state-machine rules embedded in the font, dynamically reconstructing glyph chains and adjusting overlap coordinates and baseline offsets. When done it outputs precise glyph outline indices and a pixel geometry matrix, and the front end draws pixel-accurately through the Canvas API, bypassing the defects of the browser's native layout engine.

**Performance**: Claimed that shaping and computing bounds for an entire Khmer document of tens of thousands of characters completes in **10–15 milliseconds**, more than **35× faster** than JS emulation.

**Advantages**: A perfect cultural preservation technology, definitively solving the historical pain of Chrome/Safari being unable to render Graphite smart fonts correctly; static hosting alone builds a display site for the world's minority-language documents.
**Disadvantages**: A highly specialized vertical tool, with steep costs to understand layout debugging and the font's embedded rules.

**Competitors**: Native OpenType / HarfBuzz (the mainstream standard for web layout, but less expressive than Graphite for historical documents needing extremely flexible contextual rules).

---

### 37. (originally 46) Web-libvpx / dav1d-wasm — A next-generation video decoding engine 🟡

**Pain point**: Modern web pages depend heavily on high-quality compression formats such as VP9 and AV1, but many older operating systems, mobile devices and particular browsers **have no hardware decoder for them**. Parsing AV1's complex bitstream and computing pixel prediction directly in JS is astonishingly slow, causing severe dropped frames or freezing the main thread outright.

**How it works**: Google's open-source codec core **libvpx** (or AV1's **dav1d**, written in C and assembly) is compiled to Wasm via Emscripten as a fallback decoding engine for the browser's MSE (Media Source Extensions). **Multithreaded pixel decoding**: Web Workers plus `SharedArrayBuffer` split decoding tasks (intra prediction, inverse DCT) into parallel blocks. **SIMD vector optimization**: a single CPU instruction handles deblocking filter work for 4 or 8 pixel groups at once, writing decoded raw YUV pixels straight into memory.

**Performance**: Claimed that with SIMD and threads on, 1080p VP9/AV1 decodes in software at **30–45 FPS** on a low-end machine with no hardware acceleration at all, reaching **70%** of native C.

**Advantages**: Gives a static media platform "cross-browser, 100% format-compatible" playback independent of the host's hardware chips; fully usable offline.
**Disadvantages**: Software decoding is very CPU-hungry, and decoding 1080p in software for long stretches heats the device up substantially, drawing far more power than hardware decoding.

**Competitors**: Native `<video>` (highest performance and very power-efficient, but shows a black screen or errors outright for an AV1 or specific codec the device doesn't support).

---

### 38. (originally 47) Hjson-Wasm — Human-friendly configuration syntax transpilation 🟡

**Pain point**: Standard JSON syntax is harsh (no comments, strings must use double quotes, no trailing commas), which is very unfriendly to humans, so the community produced **Hjson (Human JSON)**. Converting Hjson to standard JSON live on a static page with a pure-JS parser causes typing latency in the editor for very large configurations of tens of thousands of lines (complex game level data, enterprise architecture definitions), from constant string slicing and GC.

**How it works**: The `hjson` core, written in Rust (or C), is compiled to Wasm. **Zero-copy lexical scanning**: the user's Hjson text is passed in by JS through a memory pointer, and the Rust parser inside Wasm **creates no intermediate string objects at all**, instead doing lexical analysis directly on the raw byte stream using pointer offsets. **AST memory pool**: a highly compact syntax tree is built in linear memory, and after stripping every comment and whitespace character, standard JSON is formatted straight out.

**Performance**: Claimed that transpiling a 10 MB Hjson with deep nesting and many comments takes only **8–12 milliseconds**, more than **20× faster** than the pure-JS version, with main-thread GC pauses reduced to zero.

**Advantages**: Brings zero-latency live configuration syntax validation and conversion to front-end editors (as a Monaco Editor plugin, for instance).
**Disadvantages**: A relatively vertical syntax tool — **if the configuration file itself is only a few kilobytes, Wasm's initial load overhead outweighs any performance it brings** (a textbook counterexample to Chapter 3's "performance advantage has a compute-volume threshold").

**Competitors**: A pure-JS Hjson parser (flexible and easy to integrate, but with exponentially exploding memory and CPU peaks for large-scale generated configurations or bulk data cleaning).

---

### 39. (originally 48) Web-Proj (PROJ-Wasm) — Map projection and geographic coordinate transformation 🟡

**Pain point**: In GIS development, converting global geographic coordinates (WGS84 latitude/longitude) to a country's engineering projection (Taiwan's TWD97 two-degree zone, say) requires complex geodesy and high-order spherical trigonometry, usually relying on the authoritative C/C++ library **PROJ**. Processing large GIS point clouds or cadastral maps on a static page previously meant a round trip to a backend geographic server (GeoServer), since pure-JS coordinate transforms are imprecise and slow.

**How it works**: PROJ is compiled to Wasm in full, providing a decentralized workbench for exact coordinate transformation. **High-precision floating-point matrices**: contiguous `f64` memory is configured internally, and millions of point coordinates (X, Y, Z) are written directly as `TypedArray`s. **Dynamic datum transformation**: Wasm performs complex 3D affine transformations, the Molodensky model and grid distortion corrections entirely at the binary level.

**Performance**: Claimed to complete a full coordinate system reprojection of a geographic dataset containing a million points in **40 milliseconds**, more than **25× faster** than pure-JS geographic libraries.

**Advantages**: Brings static map analysis tools the precision and efficiency of desktop GIS (QGIS); government cadastral or commercial point-cloud data never leaves the device.
**Disadvantages**: PROJ depends on a large geodetic grid database (grid files, correcting gravitational distortion in specific regions), and those files are fairly large and must be downloaded dynamically by the front end with range requests.

**Competitors**: proj4js (lightweight and fine for ordinary web map display, but no comparison at all in performance or precision for multimillion-point clouds or industrial cartography needing global high-precision grid corrections).

---

### 40. (originally 49) Brotli-Wasm — Brotli codec at extreme compression ratios 🟢

**Pain point**: Brotli is Google's modern lossless compression algorithm, with a compression ratio well beyond Gzip. Although browsers natively support Brotli decompression at the **HTTP transport layer**, they **do not expose a native Brotli API to front-end JavaScript**. That means if you want to compress user data to a tiny file for IndexedDB inside a page, or manually decompress a custom `.br` file, pure JS cannot call the engine the browser already ships.

**How it works**: Google's official C-language Brotli codec core is compiled to Wasm, opening the low-level compression API to the front end directly. **Sliding-window memory optimization**: Brotli depends heavily on a huge sliding window (up to 16 MB) for context modelling, and Wasm allocates that contiguous space directly in linear memory, running high-speed Huffman coding and binary byte-stream matching. **Object-free streaming compression**: data streams in as binary byte blocks, and Wasm spits out a `Uint8Array` when done, creating no JS garbage objects at any point.

**Performance**: Claimed **85%** of native C when compressing or decompressing 20 MB of plain text or JSON, taking only **30–50 milliseconds**, nearly **15× faster** than pure-JS Brotli emulation libraries.

**Advantages**: Breaks through the browser's API blockade, giving a static application the ability to run top-tier lossless compression inside the browser; excellent for optimizing a PWA's offline cache footprint.
**Disadvantages**: Brotli's highest compression level (Quality 11) is computationally brutal, and blindly enabling it on the front end causes a brief main-thread freeze, so **it usually must run inside a Web Worker**.

**Competitors**: Pure-JS Brotli implementations (lacking efficient bit operations and compact memory, with CPU peaks that are too high on large files).

---

### 41. (originally 50) libFLAC-Wasm — Real-time high-fidelity lossless audio encoding 🟡

**Pain point**: When a user records through a microphone on a web page (an online podcast tool, a music creation sandbox), the browser natively supports only lossy Opus/WebM, or entirely uncompressed and enormous WAV. Saving the sound as **FLAC** — the world's mainstream lossless format — purely on the front end is impossible in pure JS: it cannot compute dense linear predictive coding (LPC) and Huffman residual encoding in real time while recording, so frames drop and the audio breaks up.

**How it works**: The official C-language **libFLAC** core is compiled to Wasm and integrated deeply with an **AudioWorklet** (the high-priority audio thread). **A real-time streaming audio stack**: raw PCM captured from the microphone is written into a Wasm memory pointer by the JS inside the AudioWorklet with no delay. **A dense mathematical budget**: the libFLAC encoder inside Wasm immediately performs lattice analysis, mid-side channel coupling and residual compression, packing FLAC bitstream within microseconds.

**Performance**: Claimed that Wasm's encoding time on the audio thread stays under **0.1 milliseconds** at under **1% CPU**, perfectly generating 24-bit/96 kHz high-fidelity FLAC while recording.

**Advantages**: Brings broadcast-grade lossless recording to static recording and music platforms, with no backend audio processing server at all.
**Disadvantages**: FLAC encoding is very demanding of memory stability and needs carefully configured linear memory; if the input channel count or sample rate changes abruptly and the glue doesn't handle it, memory corruption follows easily.

**Competitors**: Pure-JS FLAC encoders (disrupted by irregular GC pauses so they fall behind whenever the page animates or the user clicks, producing severe dropouts and pops in the recording).

---

## IV. Graph Algebra, Document Conversion and Reverse Engineering

### 42. (originally 51) Web-Biconical — Planarizing layout of biconnected components in large graphs 🔴

**Pain point**: In network security (tracing attack paths), bioinformatics (protein interaction networks) and blockchain transaction tracing, engineers often need planarizing layout of "giant graphs" with tens of thousands of nodes and complex cyclic structures. Computing biconnected components, strongly connected components and a centroid spring model in a pure-JS graph library (Cytoscape.js) means dense pointer chasing and array addressing, triggering severe dynamic allocation and GC that freeze the page or exhaust memory outright.

**How it works**: An academic C++ high-performance graph algorithm core is compiled to Wasm. **Contiguous graph layout in memory**: nodes and edges no longer live as discrete JS objects but are compressed into cache-friendly contiguous arrays (**CSR, Compressed Sparse Row** format), maximizing L1/L2 hit rates. **Parallel topological divide-and-conquer**: threads split the giant graph into several independent biconnected subgraphs, and different Workers perform crossing-minimization computations in step.

**Performance**: Claimed to lay out a very large attack-chain topology of 50,000 nodes and 150,000 edges in **180–250 milliseconds**, more than **40× faster** than the fastest pure-JS graph algorithms.

**Advantages**: Allows exploring million-scale big-data graphs directly on a static dashboard; a government or large enterprise's network topology data never leaves.
**Disadvantages**: The memory layout is extremely abstract and low-level, and **if the front end frequently adds or removes individual nodes, re-aligning memory is expensive** — so it suits one-off analysis or large batch updates better.

**Competitors**: d3-force / vis.js (fine for small interactive graphs under 1,000 nodes, but the page freezes solid on industrial topologies of tens of thousands).

---

### 43. (originally 52) pulldown-cmark-wasm — Million-word-scale Markdown parsing 🟢

**Pain point**: Modern documentation platforms need to render very long Markdown live. Pure-JS parsers (markdown-it, marked) are popular, but when a user pastes in a "million-word specification" of tens of thousands of words with heavily nested tables, code blocks and mathematical formulas, regex matching and constant string slicing saturate the CPU and make typing stutter.

**How it works**: **pulldown-cmark**, the industrial-grade Markdown parser core written in Rust, is compiled to Wasm. **Streaming event parsing**: Wasm abandons the heavy AST object tree for a pull-based event stream — reading the raw byte stream, it only advances a pointer in linear memory and emits token events dynamically. **Zero-copy HTML generation**: parsing creates no intermediate JS string objects; Wasm translates Markdown straight into a binary HTML byte array, converted once at the end into a large string injected into the DOM.

**Performance**: Claimed to parse a million-word technical manual in **15–25 milliseconds**, **25–35× faster** than the pure-JS version, achieving latency-free live synchronized preview.

**Advantages**: Brings latency-free live transpilation and search to static documentation sites, handling extreme text volumes with ease.
**Disadvantages**: As a compiled binary module, it is harder to extend than a pure-JS parser if a developer wants to add non-standard syntax plugins dynamically.

**Competitors**: Pure-JS Markdown parsers (rich ecosystem, plugins everywhere, but a clear performance bottleneck on very large documents past tens of thousands of lines).

---

### 44. (originally 53) Zstd-Wasm — High-speed compression and decompression for big data 🟢

**Pain point**: Zstandard (Zstd) is Facebook's real-time lossless compression algorithm, matching or beating Gzip's ratio with astonishing decompression speed, and it has become standard in backend and big-data ecosystems (Hadoop, Kafka, Parquet). But **browsers still expose no native Zstd API to the front end**. When the front end must download and decompress hundreds of megabytes of structured big data, telemetry logs or 3D game assets from a static site, JS-emulated Zstd cannot come close to the algorithm's physical limits.

**How it works**: Facebook's official C-language Zstd codec core is compiled to Wasm in full. **Finite state entropy (FSE) decoding**: Zstd's core is Jarek Duda's finite state entropy coding, and Wasm performs the extremely dense bit shifting and table lookups directly in linear memory. **Streaming block processing**: when the user drops in or the front end downloads a large `.zst`, JS passes the data in blocks through the Streams API, and Wasm decompresses within microseconds and returns a `Uint8Array`, creating no JS garbage objects throughout.

**Performance**: Claimed to decompress a 100 MB Zstd log file at **400–600 MB/s**, close to **85%** of native C and more than **20× faster** than traditional pure-JS decompression libraries.

**Advantages**: Breaks past the browser's protocol restrictions so a statically hosted big-data dashboard can transfer large files at very high compression ratios and decompress them instantly on the front end, cutting download waits and server bandwidth substantially.
**Disadvantages**: Zstd's high-strength compression modes need a fairly large linear memory as a dictionary buffer, so the architecture must bound the virtual machine's memory ceiling carefully.

**Competitors**: pako / zlib.js (only the older DEFLATE/Gzip, comprehensively surpassed in both ratio and decompression throughput).

---

### 45. (originally 54) libsndfile-Wasm — Multi-format audio metadata and sample stream parsing 🟡

**Pain point**: Audio engineers and speech AI developers working on the front end often need to read professional and unusual formats (`.wav`, `.aiff`, `.flac`, `.ogg`, `.voc`, `.sf`). The browser's Web Audio API natively supports only a few consumer formats (MP3, AAC). Analyzing, editing or extracting professional audio tracks, quantization bit depth or raw PCM samples on the web is severely underserved by pure-JS parsers, which OOM easily on large files.

**How it works**: The industrial C-language audio file processing library **libsndfile** is compiled to Wasm. **Precise binary structure destructuring**: after the user drops a file in, the parser inside Wasm rapidly takes apart the audio container's binary tables (WAV's RIFF header, AIFF's COMM chunk) and returns structured parameters like sample rate and channel count as JSON. **Zero-copy floating-point sample stream**: the decoding core converts each track's raw data straight to standard `f32` and exposes it through a `TypedArray` pointer to WebGL (drawing a high-precision spectrogram) or the Web Audio API.

**Performance**: Claimed to parse a 200 MB industrial lossless multitrack WAV and extract every sample in no more than **15 milliseconds**, with very low memory use.

**Advantages**: Brings deep parsing and direct playback control of dozens of professional audio formats to a static platform; a musician's unreleased masters never leave the device.
**Disadvantages**: libsndfile pursues maximum performance, so its exception handling and defence against corrupt files depend heavily on compile-time bounds checking; a maliciously crafted audio file must be prevented from crashing the virtual machine.

**Competitors**: Native `decodeAudioData` (good performance but a very narrow format range, entirely unable to read professional formats like AIFF or VOC); backend SoX/FFmpeg (powerful, but with server cost and a long upload).

---

### 46. (originally 55) libxslt-Wasm — The XSLT stylesheet transformation engine for XML 🟡

**Pain point**: In enterprise data interchange, healthcare information systems (HL7) and legal document management, XML is still the core format, and XSLT is the industrial standard for transforming XML into HTML/JSON dynamically. **But modern browsers (especially Chrome and Safari) support high-order XSLT 2.0/3.0 very poorly, or have deprecated it.** Hand-writing a whole Turing-complete XSLT engine in JS on the front end performs so badly on large XML node trees that it is unusable.

**How it works**: The GNOME project's authoritative C library **libxslt** (plus the underlying **libxml2**) is compiled to Wasm in full, providing a browser-universal industrial XML transformation platform. **An exact in-memory DOM tree**: once the XML data and XSLT stylesheet arrive, the C core inside Wasm builds a highly compact binary XML node tree in memory. **XPath engine acceleration**: XSLT's core is heavy XPath node retrieval, and Wasm performs Turing-complete template matching and data formatting through fast pointer-driven table lookups, assembling the transformed text stream directly in linear memory.

**Performance**: Claimed that a high-order XSLT transformation of a medical XML dataset with tens of thousands of nodes completes in **8–12 milliseconds**, reaching **80%** of native C and more than **30× faster** than JS emulation.

**Advantages**: Perfectly solves the pain of modern browsers' broken XSLT 2.0/3.0 support, letting enterprises move seamlessly to a pure front end without changing their existing XML/XSLT architecture; zero server cost.
**Disadvantages**: XML parsing is a large codebase, so the compiled Wasm is about **2–3 MB** compressed, and the API is low-level, needing a glue layer for strings and buffers.

**Competitors**: Native `XSLTProcessor` (no download, no size overhead, but **no support at all for syntax past XSLT 2.0** — seriously out of date); a backend Saxon service (the most complete, but with server cost, network latency and privacy risk).

---

### 47. (originally 56) VLC.wasm (libvlc) — A universal multimedia playback and streaming decode core 🟡

**Pain point**: The browser's built-in `<video>` is strict about formats (usually MP4, WebM, Ogg only). When a user needs to play `.mkv` (with multiple subtitle tracks), `.avi`, `.flv` or a professional RTSP/RTMP live surveillance stream, the browser simply refuses. The old fix was an expensive live transcoding server on the backend (converting MKV to HLS), whose cost explodes catastrophically with tens of thousands of concurrent users.

**How it works**: Millions of lines of C-language **VLC (libvlc)** core are compiled to Wasm in full via Emscripten. **A software decoding network stack**: the user drops in a video or types a stream URL, JS fetches binary blocks over WebSocket or fetch, **bypasses the browser's multimedia parser** and writes them straight into Wasm's MEMFS; the demuxer and decoders inside Wasm decode the video and audio bitstreams in software within the sandbox. **YUV-to-RGB hardware passthrough**: the decoded YUV420p raw pixels never pass through JS conversion; the memory pointer is exposed directly and JS runs colour space conversion and rendering on the GPU through a WebGL/WebGPU shader.

**Performance**: Claimed that with SIMD and threads on, 1080p/30 FPS MKV or H.264 decodes smoothly in software with no hardware acceleration, with playback latency under **30 milliseconds** at **70%–75%** of native VLC.

**Advantages**: Brings genuinely "universal format compatibility" playback to a static site, at zero backend cost, with the video never leaving the device.
**Disadvantages**: Dense software decoding puts a heavy load on CPU, noticeably heating and draining a low-end phone or tablet playing high-resolution video.

**Competitors**: hls.js / flv.js (popular front-end streaming libraries, but essentially only remuxing — **underneath they still depend heavily on the browser's built-in decoding hardware**).

---

### 48. (originally 57) SuiteSparse:GraphBLAS-Wasm — Sparse-matrix graph algebra supercomputing 🟡

**Pain point**: In big-data analysis, social network mining (PageRank over hundreds of millions of relationships) and financial risk control, graphs are usually turned into massive "sparse matrices" for algebraic computation, relying on the industrial C library **SuiteSparse:GraphBLAS**. Hand-writing those giant, 99%-zero matrix multiplications over JS arrays produces heavy memory fragmentation from the object allocator and lacks binary pointer-chasing optimization, freezing the browser for tens of seconds.

**How it works**: The SuiteSparse:GraphBLAS core is compiled to Wasm in full. **Compressed sparse layout**: matrices are laid out strictly in linear memory in binary **CSC (Compressed Sparse Column)** format, storing no zero elements at all, maximizing cache hit rates and bypassing JS object creation entirely. **Semiring algebra**: every graph traversal and shortest-path computation is converted into bitmask and fast binary multiply-add operations inside Wasm, with several Workers scanning linear memory in parallel.

**Performance**: Claimed to complete PageRank iterations on a giant social graph of 100,000 nodes and 2,000,000 edges in **80–120 milliseconds**, more than **50× faster** than pure-JS graph matrix libraries.

**Advantages**: Gives a free static dashboard the ability to run hardcore graph algebra over million-scale network graphs; 100% data confidentiality.
**Disadvantages**: GraphBLAS's API is extremely academic and abstract, so a front-end developer cannot add or remove nodes intuitively and must write a heavy data transformation glue layer.

**Competitors**: math.js (fine for ordinary dense matrix algebra, but orders of magnitude behind on industrial sparse graph computation past tens of thousands of dimensions with vast numbers of zeros).

---

### 49. (originally 58) HTML Tidy-Wasm — Industrial cleanup and repair of dirty HTML/XML 🟡

**Pain point**: In web crawlers, online HTML editors and code review tools, the front end constantly receives "dirty HTML/XML" with broken syntax, unclosed tags and scrambled attributes. Pure-JS regex matching is far too imprecise, and on millions of lines of page source, string slicing and DOM tree reconstruction saturate the CPU.

**How it works**: The long-lived and extremely robust authoritative C library **HTML Tidy** is compiled to Wasm. **A byte-stream lexical state machine**: the user's dirty HTML is written in by JS through a memory pointer, and the C parsing core inside Wasm **creates no intermediate string objects at all**, scanning the raw byte stream lexically with a fast integer state machine. **In-memory tree reconstruction**: Wasm builds a highly compact DOM node tree in its enclosed linear memory, filling in missing closing tags automatically, repairing attribute quoting, and assembling perfect standard HTML in memory in one pass to return.

**Performance**: Claimed to clean and format 20 MB of very large page source riddled with nesting errors in only **10–15 milliseconds**, **20–30× faster** than pure-JS repair libraries, with very low memory use.

**Advantages**: Brings latency-free live syntax cleanup and automatic repair to a static online code sandbox; zero backend cost.
**Disadvantages**: A relatively vertical tool — **when the code volume is tiny, the Wasm module's own load time cancels out the performance gain**.

**Competitors**: htmlparser2 (good compatibility, mature ecosystem, but a clear performance bottleneck on enterprise-scale page data cleaning past hundreds of thousands of lines).

---

### 50. (originally 59) Web-Fontfuzz — Security fuzzing of font files 🔴

**Pain point**: Font files (`.ttf`, `.otf`, `.woff2`) have complex structures and contain miniature hardware instructions (a TrueType bytecode interpreter). Historically, many severe remote code execution (RCE) vulnerabilities in operating systems and browsers came from parsing maliciously crafted fonts. Security researchers doing font fuzzing must set up a complex Linux environment and cluster locally. Building an instantly available detection platform on the web is impossible with traditional front-end technology, which cannot mutate the internal tables of a binary font at high frequency or analyze the resulting crashes.

**How it works**: A Rust/C++ font security fuzzing core (libFuzzer-based font parsing operators, say) is compiled to Wasm and deployed statically. **A mutation state machine**: the user drops in a font, and Wasm performs tens of thousands of random bit flips and structural corruptions per second on its binary structures (the `glyf` and `loca` tables) in linear memory. **Sandboxed memory isolation**: the mutated malicious font is fed straight into the virtual parser inside Wasm; if it triggers a memory overrun, **the Wasm sandbox catches that RuntimeError precisely and absolutely never touches the user's real operating system or browser security** (exactly the positive application of Chapter 2's "the sandbox protects the host").

**Performance**: Claimed **5,000–8,000** font structure mutations and deep parse tests per second single-threaded, at **80%** of the native C++ core.

**Advantages**: Gives security engineers a 100% isolated, decentralized, web-based font vulnerability diagnosis tool.
**Disadvantages**: The web environment means that when the Wasm VM crashes, it cannot export a full core dump the way local Linux can, so carefully written glue must stream memory logs out live.

**Competitors**: Local AFL++ / libFuzzer (unlimited compute and the most complete debugging, but fiddly to install and without the instant availability of a web page).

---

### 51. (originally 60) Web-Gidra (the Ghidra decompiler core) — Binary reverse engineering 🔴

**Pain point**: Reverse engineers analyzing malware or binary executables (x86/ARM `.exe`, `.bin`) need to decompile machine code back into readable high-level C. The core is an enormous decompilation semantics engine (such as the NSA's open-source Ghidra). Offering a fast binary analysis playground on the web previously meant uploading the malicious binary to a backend — a serious security hazard (the malware could contaminate the backend), and building a control flow graph (CFG) is CPU-expensive.

**How it works**: Ghidra's C++ core decompilation engine (the Sleigh decoder and constant propagation optimizer) is compiled to Wasm, creating an online reverse engineering range. **An intermediate language (P-code) translation tree**: the user drops in a binary executable, the decoder inside Wasm reads the machine code at high speed and translates it into an architecture-independent intermediate representation (P-code), building a highly compact control flow graph in linear memory. **Structured semantic reconstruction**: the internal optimizer performs dead code elimination and variable type inference, assembling the decompiled C string directly in linear memory.

**Performance**: Claimed to decompile a roughly 2 MB x86 library into high-quality C in **200–400 milliseconds**, reaching **75%** of desktop Ghidra.

**Advantages**: **100% absolute security isolation** — the malicious binary is decompiled entirely inside Wasm's sealed sandbox and cannot infect the local system; a static site's operating cost is zero.
**Disadvantages**: Ghidra's C++ decompilation core is enormous, so the compiled Wasm is still **5–8 MB** compressed and slow on first load.

**Competitors**: Pure-JS binary parsers (usually capable of only hex viewing or simple disassembly, and utterly helpless before decompilation tasks needing complex control flow optimization and semantic reconstruction).

> **A self-reference worth noticing**: this case forms an interesting loop with Chapter 9 — **running a decompiler in Wasm to analyze someone else's Wasm.** In fact the Ghidra community does have a Wasm loader plugin that takes `.wasm` as its analysis target, and WABT's `wasm-decompile` produces C-like pseudocode too. **The fact that the reverse engineering tool and the object of reverse engineering run in the same sandbox is by itself proof that "binaries are irreversible" is an untenable claim.**

---

## V. Cryptography, Scientific Computing and P2P

### 52. (originally 71) Circom-Witness-Wasm — Front-end zero-knowledge proof generation 🟢

**Pain point**: Zero-knowledge proofs (ZKP) let a user prove to a server that they hold a permission without revealing a password or identity (private voting, zk-Rollups). But generating a ZK proof means constructing a large arithmetic circuit and computing extremely dense cryptographic polynomials (MSM and NTT). As a web DApp, pure-JS libraries perform so badly on tens of thousands of circuit gates that the browser throws up "this page is unresponsive."

**How it works**: The witness computation code produced by the ZK circuit compiler `circom` is compiled directly into a Wasm module hosted statically. **Big-field arithmetic optimization**: ZKP involves huge integer arithmetic over a specific finite field (the BN254 elliptic curve, say), and Wasm uses `i64` instructions to open a contiguous memory pool inside the sandbox for maximally optimized modular multiplication and addition. **Zero-copy proof flow**: JS passes private inputs directly into Wasm memory as a `TypedArray`, and Wasm solves thousands of constraints at high speed inside the sandbox to generate the binary witness file.

**Performance**: Claimed that generating the proof for a private identity circuit of 50,000 gates takes only **300–500 milliseconds** on the front end, more than **25× faster** than early pure-JS versions (snarkjs's JS mode).

**Advantages**: The user's real password and private inputs **100% never leave the device**, meeting cryptography's highest security principle; backend operating cost is eliminated entirely.
**Disadvantages**: **If the circuit is enormous (a zk-EVM proof of millions of gates, say), Wasm cannot run it at all because it exceeds the 4 GB linear memory ceiling**, and backend compute is required (another concrete instance of Chapter 8's ceiling).

**Competitors**: Pure-JS cryptographic computation (with no low-level instruction optimization for custom finite fields and bignum arithmetic, it simply freezes when solving large circuits).

---

### 53. (originally 72) Qiskit-Wasm — Quantum computing state vector simulation 🟡

**Pain point**: Quantum computing researchers and students designing quantum algorithms (Shor, Grover) need to simulate qubit superposition and entanglement. IBM's Qiskit rules the field, but its core is written in C++/Python. Providing an interactive quantum programming teaching platform on the web meant sending circuits back to a backend queue; when many students run at once, the backend's matrix multiplication capacity is instantly consumed.

**How it works**: A lightweight quantum simulation core (a C++/Rust state vector calculator) is compiled to Wasm and deployed on a static page. **Complex matrix tensor products**: qubit simulation is essentially dense complex vector and Kronecker product arithmetic, and Wasm builds compact `f64` real and imaginary arrays in linear memory. **Probability amplitude streaming sampling**: when the user performs a quantum measurement, the Monte Carlo state machine inside Wasm samples memory at high speed and returns the histogram as JSON for Canvas to draw.

**Performance**: Claimed that simulating a composite circuit of arbitrary logic gates (Hadamard, CNOT and so on) on 16 qubits completes full state vector evolution in **10–20 milliseconds**, at **80%** of native C++.

**Advantages**: Brings quantum computing education platforms a fully backend-free, latency-free live simulation experience, cutting academic institutions' cost of standing up compute servers dramatically.
**Disadvantages**: **The dimension of the quantum state vector explodes exponentially with qubit count (2ⁿ)**, so the front end tops out around **20–24 qubits** and crashes with OOM beyond that. **This is the cleanest expression of the 4 GB ceiling anywhere: a 24-qubit complex state vector lands exactly in the hundreds-of-megabytes-to-gigabytes range.**

**Competitors**: Pure-JS complex matrix computation (unable to guarantee contiguous memory alignment, so large matrix multiplications thrash L1/L2 constantly and run more than 15× slower).

---

### 54. (originally 73) libp2p-Wasm — A distributed P2P network multiplexing protocol stack 🟢

**Pain point**: Building decentralized network applications (IPFS, a browser P2P chatroom, WebTorrent), the front end must establish complex P2P connections with nodes worldwide. But the browser offers only the high-level WebRTC API, without low-level stream multiplexing, node routing (DHT) or secure encrypted handshake negotiation. Traditionally that means the heavy JS libp2p, but maintaining hundreds of P2P virtual channels and parsing binary packet headers burns a lot of CPU through dynamic typing and makes the UI stutter intermittently.

**How it works**: The industrial libp2p core network stack in Go or Rust (including `mplex` multiplexing, `yamux` and the `noise` encryption layer) is compiled to Wasm in full. **A binary packet pipeline**: raw P2P byte streams arriving on the WebRTC data channel are written into Wasm memory directly as a `Uint8Array`, and the parser inside takes packet headers apart with a fast integer state machine and routes them automatically to their virtual subchannels. **In-memory network buffers**: Wasm maintains efficient sliding windows and ring queues internally, running flow control and cryptographic defence, creating no JS garbage objects throughout.

**Performance**: Claimed that in a stress test maintaining 200 simultaneous P2P node connections at 50 MB/s throughput, protocol parsing is **12–18× faster** than the pure-JS version, with CPU usage down 65%.

**Advantages**: Brings statically hosted DApps an industry-standard "serverless P2P connectivity," substantially improving the transfer stability of a browser-side IPFS node.
**Disadvantages**: Sandbox restrictions mean it **still cannot open a traditional TCP/UDP listener directly** and must rely on external JS using WebRTC or WebSocket as a springboard for the physical NIC (echoing Chapter 11's four reservations about P2P being "serverless").

**Competitors**: js-libp2p (highly complete, but causing severe GC stutter under very high-frequency binary packet destructuring and Noise handshakes).

---

### 55. (originally 74) minimap2-Wasm — High-speed gene sequence alignment 🟡

**Pain point**: In modern biomedicine, scientists must align the vast DNA base sequences (reads) produced by a sequencer against a known reference genome to catch genetic variants or infectious disease signatures, usually relying on the authoritative C library **minimap2** (with precise dynamic programming and a seed-and-extend algorithm). Biologists previously had to install a Linux terminal or upload highly sensitive personal genetic data to a hospital cloud — an enormous privacy risk, with high backend cluster maintenance cost besides.

**How it works**: Tens of thousands of lines of maximally optimized C-language gene alignment engine are compiled to Wasm via Emscripten, creating a web-based genetic diagnosis workbench. **Binary index lookup**: the reference genome's huge index table (hundreds of megabytes) is loaded into Wasm linear memory in one pass as a binary byte stream. **SIMD-accelerated dynamic programming**: the heart of gene alignment is solving the Smith-Waterman matrix, and with SIMD on, a single instruction computes the score matrix and penalty weights for 4 or 8 bases in parallel.

**Performance**: Claimed to align an unknown viral DNA sequence of 10,000 base pairs in only **80–150 milliseconds**, at **75%** of native C.

**Advantages**: **100% medical-grade privacy** — personal DNA data stays entirely in the local sandbox; a researcher in the field can align in real time by opening a web page on a phone.
**Disadvantages**: The human reference genome's index file (`.mmi`) often runs to hundreds of megabytes or even gigabytes, so the front end's first load and memory quota control need a very carefully designed streaming architecture (precisely the scenario Chapter 8's "escape route one" exists for).

**Competitors**: Pure-JS string matching algorithms (lacking binary pointer manipulation and SIMD vector acceleration, orders of magnitude slower on large-scale genetic data and with no industrial viability at all).

---

### 56. (originally 75) Orekit-Wasm — Astrodynamics and satellite orbit prediction 🟡

**Pain point**: Aerospace engineers and astronomy enthusiasts predicting the exact orbital position of a satellite (the ISS, Starlink) must run extremely precise astrodynamic numerics: Earth's gravitational field irregularity (spherical harmonic models), solar radiation pressure, atmospheric drag and multi-body gravitational perturbations. The authoritative open-source library is **Orekit**. Hand-writing those orbital perturbation differential equations over ordinary JS floats produces accumulated errors of kilometres within days, for lack of exact 64-bit alignment and fast matrix iteration.

**How it works**: A rigorous astrodynamics core is compiled to Wasm, providing a decentralized satellite tracking dashboard. **An exact numerical integrator**: Wasm implements a high-order Runge-Kutta (Dormand-Prince) ODE solver internally, advancing orbital elements and geocentric coordinates strictly as contiguous `f64` in linear memory. **A time and coordinate system conversion state machine**: complex matrix transformations between IERS-standard time scales (TAI, UTC) and inertial frames (EME2000, ITRF) run at high speed at the binary level, bypassing JS's GC interference throughout.

**Performance**: Claimed to predict a satellite's exact position over the next 30 days (continuous integration at a one-second step) in only **40–60 milliseconds**, at aerospace-industry precision and more than **30× faster** than pure JS.

**Advantages**: Brings an entirely install-free, zero-backend, aerospace-precision online orbit propagation tool; pairs perfectly with Three.js for live 3D orbital visualization around the Earth.
**Disadvantages**: It needs the global gravity field model (EGM96) and precise leap-second observation data loaded, and those static data files must be requested and injected dynamically by the front end.

**Competitors**: satellite.js (based on the simpler SGP4 model, fast, but so physically simplified that it cannot compute high-order gravity field irregularity or atmospheric drag perturbation at all).

---

### 57. (originally 76) WireGuard-Wasm — A front-end VPN network protocol stack 🟡

**Pain point**: In remote work and zero-trust architectures, WireGuard is the high-performance lightweight encrypted VPN protocol. But a traditional VPN must install a virtual NIC driver deep in the operating system, requiring very high system privileges. To let employees connect securely to internal company resources by opening a web page without installing anything, pure-JS crypto libraries are entirely unequal to reassembling ChaCha20-Poly1305 packets at tens of megabytes per second and running the Noise handshake state machine.

**How it works**: WireGuard's official Go or Rust userspace network stack core is compiled to Wasm. **Tunnel packet destructuring**: Wasm emulates a virtual NIC in its sandboxed linear memory; when external JS receives an encrypted UDP packet over WebRTC or WebSocket (as the physical relay) it passes it straight into Wasm memory, and the state machine inside decrypts, verifies and unpacks the original internal IP packet at high speed. **Memory buffer flow**: the decrypted data is repackaged inside Wasm as a front-end-readable `ArrayBuffer` and talks directly to a tiny in-page client (a web SSH client, say), never touching the operating system's network stack.

**Performance**: Claimed that packet processing and decryption throughput is **12–20× faster** than pure-JS crypto emulation, reaching **30–50 MB/s** of encrypted transfer in the browser at stable CPU usage.

**Advantages**: Brings a static page install-free "native-grade secure VPN tunnel connectivity"; the encryption private key stays inside the user's browser forever.
**Disadvantages**: Bounded by the sandbox, **the tunnel can serve only the current tab or the current application's network requests, and cannot provide global VPN encryption for every other piece of software on the operating system.**

**Competitors**: Pure-JS cryptographic network libraries (lacking efficient binary bit shifting and compact memory alignment, causing severe GC stutter and disconnections under heavy VPN packet throughput).

---

### 58. (originally 77) Minestom-Wasm — A Minecraft server engine inside the browser 🔴

**Pain point**: A Minecraft world is made of tens of billions of blocks, and multiplayer traditionally means renting an expensive Java server to handle block generation, player synchronization and physics collision. The community wants a "click and play, no host needed" multiplayer experience on a static page — which means **the browser front end must itself become a server**. A game server written in pure JS performs so badly on 3D block-world collision volumes and mass packet serialization that the page freezes.

**How it works**: The open-source high-performance Minecraft server core **Minestom** (or a Rust server implementation) is compiled to Wasm and runs directly in the browser front end. **A sandboxed in-memory server**: Wasm builds a highly compact 3D world block database in linear memory, with player positions, block breaking and generation, and mob AI all computed inside Wasm. **P2P network forwarding**: through a WebRTC data channel, other players connect P2P directly to the host player's Wasm server; Wasm serializes memory-generated 3D chunks into a binary byte stream and distributes them at high speed.

**Performance**: Claimed that this in-browser server handles **10–15 players** online simultaneously with physics collision and 3D world synchronization, keeping server tick time within **2 milliseconds** (far below the game's 50-millisecond budget).

**Advantages**: Genuinely decentralized — players rent no cloud host at all and can open a multiplayer 3D game server on free static hosting; level saves export as a binary file.
**Disadvantages**: Bounded by the 4 GB memory ceiling, it cannot support a large render distance or more than about 20 players.

> ★ **A real version of this idea exists, and it is harder**: **FluffOS × Wasm** compiles an entire LPMud driver (LPC compiler, virtual machine, efuns, telnet protocol) into a browser tab, with the mudlib packaged by `file_packager` as a static bundle. It solves two problems beyond this concept: **compiling user code at runtime**, and **replacing the blocking event loop with a host-driven `fluffos_tick()`**. **See Appendix L.**

**Competitors**: A traditional standalone Java/C++ server (feature-complete, supporting tens of thousands of players, but requiring a VPS purchase and complex port forwarding configuration).

---

### 59. (originally 78) GnuCash-Wasm — An enterprise double-entry accounting and ERP core 🟡

**Pain point**: Small and medium enterprises managing finances, issuing invoices or preparing balance sheets need an ERP or double-entry accounting system, and the authoritative open-source tool is GnuCash. As a cloud service, a company's highly sensitive transaction flows, profits and payroll must be uploaded to a third party — an enormous risk. Hand-writing an accounting core in JS runs into a wall on tens of thousands of transactions, cross-currency compound interest and live recomputation of account balances, because **JS lacks exact 64-bit fixed-point arithmetic and easily throws the books out of balance through lost floating-point precision**.

**How it works**: The open-source C-language accounting core **GnuCash (libgnucash)** is compiled to Wasm in full. **High-precision fixed-point memory**: accounting abhors floating-point error, so Wasm strictly uses `i64` to emulate high-precision accounting fixed-point numbers, advancing every debit-credit balance computation directly through contiguous binary structures and avoiding GC entirely. **XML/SQL save synchronization**: transaction data can be compressed directly into a `.gnucash` file (gzipped XML) or SQLite and synced locally through the virtual filesystem, so financial data 100% never leaves the device.

**Performance**: Claimed that recomputing a full year's general ledger of 50,000 cross-border transactions with automatic exchange-rate conversion across five currencies takes only **20–40 milliseconds** on the front end to produce the income statement and balance sheet, **30× faster** than pure JS.

**Advantages**: Brings industrial-grade high-precision accounting to a static enterprise back office; 100% data confidentiality, meeting the ACID transaction safety standard financial audit requires.
**Disadvantages**: GnuCash's native C architecture is very large, so the compiled Wasm runs about **3–4 MB**, and the API is low-level, needing a modern web UI designed for a smooth fit.

**Competitors**: Commercial SaaS cloud accounting (powerful and highly automated, but with a subscription fee and core financial data hosted entirely by a third party).

---

### 60. (originally 79) Micro-Apache-Wasm — A miniature web server inside the browser 🟡

**Pain point**: In front-end teaching, static demonstration or building an offline PWA tool, you sometimes need to virtualize "a real web server" inside the browser to parse standard HTTP requests, handle custom route rewriting (`.htaccess`) or process virtual POST forms. That previously required installing Node.js, Apache or Nginx. Pure JS brute-forcing HTTP header string parsing and status code redirection at very high frequency has CPU peaks that are too high, and it is hard to reproduce a real server's underlying architecture.

**How it works**: A lightweight C-language embedded HTTP server engine core is compiled to Wasm via Emscripten. **Virtual port listening (in-memory socket)**: the sandbox prevents Wasm from actually opening physical port 80, so the architecture uses a **Service Worker** — when the user visits a virtual URL (`/api/users`, say), the Service Worker intercepts that real HTTP request. **Server state machine solving**: the Service Worker passes the request's raw bytes straight into Wasm memory, the C server core inside performs route matching, header sanitization and virtual file addressing at high speed, and finally generates a standard HTTP response packet in linear memory to return.

**Performance**: Claimed that under high-frequency virtual API requests, a standard HTTP request parse, route match and response generation completes in **under 1 millisecond**, with QPS more than **15× higher** than a mock server written with pure-JS regexes.

**Advantages**: Reproduces a complete, standard, rewrite-capable server engine on free static hosting; ideal for building an install-free online backend development and network protocol teaching platform.
**Disadvantages**: **This is only a virtual server "running in browser memory," and real users on the external internet cannot connect through it into that user's computer** (unless paired with a P2P traversal tunnel) — exactly the same point as Chapter 5's authenticity caveat about WebContainers.

> ★ **The real control group is again FluffOS × Wasm (Appendix L)**, and the difference is instructive: this concept emulates **stateless request-response**; what FluffOS moves in is a server with **a heartbeat, `call_out` timers, persistent world state and multiple concurrent connections**. **How hard "move the server into the browser" is depends entirely on whether that server has state.**

**Competitors**: Mock.js / MSW (fine for ordinary front-end API data mocking, but with none of a real web server's underlying C state machine, custom rewrite rules or real HTTP byte-stream destructuring).

---

### 61. (originally 80) GNU-Tar-Wasm — An industrial archiving and checksum engine 🟡

**Pain point**: `tar` is the absolute standard for packaging and backup in the Linux world. When a static application must package thousands of tiny files into a standard `.tar` or `.tar.gz`, pure JS hits a wall: concatenating tens of thousands of files' bytes and computing POSIX-standard headers (512-byte block alignment, octal UID/GID string conversion, exact octal checksums) triggers constant fragmented allocation, crashing the page or dropping frames badly.

**How it works**: The most authentic official **GNU tar** C-language toolchain is ported and compiled in full into `tar.wasm`. **Flat 512-byte alignment**: Wasm allocates a contiguous flat linear memory internally, and when external JS passes in many small files, the GNU core inside uses efficient binary pointer arithmetic to lay them out in memory in strictly 512-byte-aligned structures and quickly compute the low-level binary checksums. **Streaming archive output**: files are never concatenated by JS; when Wasm finishes archiving it emits a fully POSIX-conformant `Uint8Array` directly, guaranteeing the archive unpacks perfectly with `tar -xvf` on any Linux system.

**Performance**: Claimed to archive and checksum a project structure of 5,000 tiny files (50 MB total) in only **8–15 milliseconds**, more than **25× faster** than pure-JS archiving libraries.

**Advantages**: A 100% clone of GNU's decades of highly compatible archiving algorithms, ensuring the archives produced on the front end are never corrupt; consumes none of the developer's server bandwidth or CPU.
**Disadvantages**: A low-level tool focused tightly on archive format and checksum compatibility — **if the user only needs one simple file, the Wasm module's initial load exceeds the performance gain**.

**Competitors**: Pure-JS archive libraries (simple to write, but far behind an authentic port in efficiency and format compatibility when densely packaging thousands of files with precise POSIX header byte alignment and octal checksums).

---

### 62. (originally 81) CuraEngine-Wasm — An industrial 3D printing slicing engine 🟢

**Pain point**: In 3D printing, converting a model file (`.stl`, `.obj`) into the G-code toolpath the printer understands is called "slicing." It involves extremely dense 3D geometric intersection computation, polygon offsetting (AABB trees and Minkowski sums) and optimal path planning. The world's foremost core is Ultimaker's open-source **CuraEngine** (C++). Offering slicing on the web previously meant uploading hundreds of megabytes of STL to a backend — consuming enormous bandwidth, and overloading backend CPU instantly when many users slice at once.

**How it works**: The CuraEngine core — hundreds of thousands of lines of accumulated C++ — is cross-compiled to Wasm via Emscripten, providing desktop-grade slicing on a static page. **Flat memory space geometry**: the model's millions of triangle vertices are written into linear memory as a binary byte stream, and Wasm builds a 3D AABB spatial tree through pointer manipulation. **Multithreaded layered slicing**: with Web Workers plus `SharedArrayBuffer`, the model is cut into thousands of horizontal layers along Z, and each layer's polygon topology filling and path computation is distributed in parallel across CPU cores.

**Performance**: Claimed to slice a complex model of 500,000 triangles and generate 20 MB of G-code in only **1.5–3 seconds** on the front end, at **80%** of the native C++ desktop version.

**Advantages**: Brings the static 3D printing community desktop-grade slicing at zero backend cost; an industrial designer's prototype stays 100% local, removing IP leakage risk.
**Disadvantages**: If the model geometry is badly broken (non-manifold geometry, say), designing the glue for debugging and cleaning up memory when the C++ core throws inside Wasm is extremely complex.

**Competitors**: Pure-JS geometric slicing libraries (lacking strict typing and efficient multidimensional spatial tree addressing, so the page OOMs outright or freezes in long GC past 50,000 triangles).

---

### 63. (originally 82) liquid-dsp-Wasm — Software-defined radio (SDR) digital signal processing 🟡

**Pain point**: Software-defined radio lets you process radio signals in software (FM broadcast, aircraft ADS-B, weather satellite imagery). The core is dense digital signal processing: FFT, FIR filtering, phase-locked loops (PLL) and demodulation. The most popular tiny C DSP library is **liquid-dsp**. Receiving a USB SDR receiver's raw IQ sample stream live on the web previously meant decoding on a backend and converting to an audio stream — enormous latency and very high server load.

**How it works**: liquid-dsp is compiled to Wasm in full as a direct demodulation core for the Web USB / Web Serial APIs. **A zero-copy signal pipeline**: after the browser obtains millions of raw IQ samples per second from an RTL-SDR over WebUSB, they are written straight into Wasm's ring buffer as a `TypedArray`. **SIMD-accelerated demodulation**: with SIMD on, one CPU instruction runs several complex dot-product matrix operations and filter iterations in parallel, restoring the high-frequency radio byte stream to raw audio PCM inside the sandbox.

**Performance**: Claimed that demodulating 2.4 MSps (2.4 million samples per second) wideband QAM or standard WBFM in real time consumes under **3% of CPU**, with audio decoding latency down to **5 milliseconds**.

**Advantages**: Breaks the taboo that the web cannot handle "high-frequency hardware digital signals" — plug in a USB receiver and the browser becomes a fully functional radio receiver, at zero server cost.
**Disadvantages**: The solving algorithms inside Wasm are fixed, so it is less flexible if the front end wants to inject an entirely new custom modulation formula dynamically.

**Competitors**: Pure-JS DSP libraries (unable to guarantee contiguous memory alignment of 64-bit complex vectors, so a flood of IQ samples causes constant GC stutter and the decoded audio comes out with harsh pops and distortion).

---

### 64. (originally 83) Tantivy-Wasm — Industrial full-text search and inverted indexing 🟢

**Pain point**: On a static big-data display site or a very large documentation system, users need live full-text search and weighted filtering across hundreds of thousands or even millions of structured records. Pure-JS search libraries (Lunr.js) can only do simple string matching, and past tens of thousands of records the index balloons and performance collapses; a backend option (Elasticsearch) means expensive operations.

**How it works**: **Tantivy**, the industrial search engine core written in Rust (holding the same position as Lucene in the Java world), is compiled to Wasm. **A highly compact inverted index layout**: JSON is abandoned for a highly compact inverted index built in linear memory on **finite state transducers (FST)** and binary bitmaps (**Roaring Bitmaps**). **Zero-GC vector retrieval**: when the user submits a multi-condition compound search (boolean queries with BM25 term-frequency relevance ranking), JS passes the query string in, and Wasm parses the query tree and runs extremely fast intersections and unions over binary memory.

**Performance**: Claimed to complete a fuzzy match and paginated relevance ranking over an index of 500,000 complex logs or product records (roughly 200 MB of raw text) in **2–4 milliseconds**, more than **40× faster** than pure-JS search libraries, with a fifth of the memory of the JS version.

**Advantages**: Brings a static platform "Lucene-class" professional search, supporting complex phrase matching, regex filtering and field faceting; 100% zero backend cost.
**Disadvantages**: The index file must be pre-generated in binary form and placed on the static host; at very large data volumes it needs careful **HTTP Range Request** streaming of just the index blocks it needs (another application of Chapter 8's escape route one).

**Competitors**: Fuse.js / Lunr.js (fine for lightweight fuzzy search on a thousand records, but they freeze the main thread outright on large text corpora past a hundred thousand).

---

### 65. (originally 84) Rapier3D-Wasm — Rust's industrial 3D rigid body physics engine 🟢

**Pain point**: Building 3D simulations, robotic kinematics control or high-precision web games on the front end requires computing rigid body collisions, joint constraints, gravitational acceleration and contact mechanics among thousands of objects. Traditional front-end physics engines (Ammo.js, a downgraded rewrite of the C++ Bullet engine) are very bloated; pure-JS physics libraries, lacking exact 64-bit memory layout optimization, produce severe **jittering** or tunnelling when many objects stack.

**How it works**: **Rapier3D**, the next-generation high-performance 3D rigid body physics engine written in Rust, is compiled to Wasm. **Cache-friendly data arrays (SoA layout)**: every object's mass, 3D coordinates, velocity and rotation quaternion are laid out strictly as contiguous **structure-of-arrays** in linear memory, maximizing L1/L2 hit rates. **Symplectic numerical integration**: the physics optimizer inside Wasm runs a rigorous collision detection state machine (broad-phase sweep plus narrow-phase exact solve) and solves the linear complementarity problem (LCP) at high speed at the binary level, with no JS garbage allocation anywhere.

**Performance**: Claimed that simulating **5,000 complex rigid bodies** falling, colliding and stacking in one scene takes no more than **4–6 milliseconds** per physics step, locking 60 FPS solidly.

**Advantages**: Provides industrial-robot-grade high-precision physical feedback, eliminating the tunnelling and unnatural jitter common in pure-JS physics engines; **the Wasm module is only a few hundred kilobytes compressed and loads very fast** (the classic advantage of Rust's zero runtime burden).
**Disadvantages**: Very high-frequency collision event callbacks into JS incur boundary conversion overhead from passing many event objects, so a memory event ring buffer optimization is needed.

**Competitors**: Cannon.js / Oimo.js (small and quick to learn, but their compute and numerical precision are entirely inadequate for industrial or high-end game scenarios with dense multi-object stacking, complex joint constraints and continuous collision detection (CCD)).

---

### 66. (originally 85) Cubism-OLAP-Wasm — A multidimensional online analysis (OLAP) data cube 🔴

**Pain point**: In business intelligence, engineers need multidimensional online analysis of massive data (millions of sales, log or telemetry records), building a "data cube" live and running roll-up, drill-down and dice aggregations. Traditionally that relies on a large backend OLAP database (ClickHouse, Apache Druid). To offer a backend-free million-scale BI dashboard on an entirely static page, pure JS doing multidimensional group-by traversal and hash aggregation produces severe memory fragmentation and processor overload.

**How it works**: A C++/Rust vectorized multidimensional aggregation core is compiled to Wasm. **Vectorized execution architecture**: the data file (Apache Parquet, say) streams into linear memory as binary columnar blocks, and Wasm processes not one record at a time but whole "data vectors" fed to the processor core in one go. **In-memory radix hash tables**: Wasm builds a highly optimized radix hash table inside the sandbox and runs multithreaded parallel aggregation, creating no JavaScript objects at any point.

**Performance**: Claimed that a complex compound group-by aggregation and live cross-tabulation recomputation over a 5,000,000-row structured dataset with 10 dimensions takes only **60–90 milliseconds** on the front end, more than **50× faster** than pure JS.

**Advantages**: Brings a static site "ClickHouse-class" ultra-fast front-end multidimensional aggregation and BI dashboards, saving expensive cloud database maintenance.
**Disadvantages**: Data is buffered entirely in Wasm memory by default, so **supporting persistent analysis of hundreds of millions of rows requires a complex binary chunked disk I/O design over OPFS**.

**Competitors**: Lodash.groupBy / Crossfilter (out of their depth past a million rows, prone to OOM or multi-second UI freezes). **More noteworthy is DuckDB-Wasm (case 5) — the real, verifiable version of this idea**, which has already solved OPFS persistence and remote Parquet querying.

---

### 67. (originally 86) NimBLE-Wasm — A Bluetooth Low Energy (BLE) protocol stack 🟡

**Pain point**: When developing a web IoT console or a medical wearable monitoring station, the front end talks to hardware through the Web Bluetooth API. But the browser's native Bluetooth API exposes only the high-level GATT read/write interface, without low-level packet destructuring, multi-device retry and flow control state machines, or special encrypted handshake support. Hand-writing high-frequency Bluetooth characteristic binary parsing and custom protocol reassembly in JS causes intermittent GC stutter through dynamic allocation, and packets are easily lost under high-frequency data flows (a live ECG at 100 samples per second).

**How it works**: The industrial C-language BLE core protocol stack **NimBLE** (familiar from ESP32 and Apache Mynewt) is compiled to Wasm. **A byte-stream protocol parsing pipeline (L2CAP/ATT layers)**: the raw `ArrayBuffer` the browser receives skips JS parsing and is written straight into Wasm's ring queue through a memory pointer; the NimBLE state machine inside takes protocol headers apart at the binary level at high speed, verifies them and reassembles packets. **Isolated memory defence**: every timeout retry and sliding-window flow control runs entirely inside the Wasm sandbox at very low overhead.

**Performance**: Claimed that under a stress test maintaining four Bluetooth medical devices with tens of thousands of characteristic bytes per second, protocol parsing is **15–22× faster** than pure JS, with CPU usage down 70%.

**Advantages**: Brings a static IoT back office an industrial-grade Bluetooth protocol stack with strong interference resistance and flow control; device data is parsed entirely locally.
**Disadvantages**: **It cannot bypass the browser's underlying security sandbox** and must still rely on external JS using the Web Bluetooth API as the hardware bridge, requiring a carefully designed secure event callback layer.

**Competitors**: A custom pure-JS Bluetooth parser (easy to develop, but inefficient under multi-device concurrency, high-frequency bit-shift parsing and precise flow control state machines, and prone to data delay or disconnection).

---

### 68. (originally 87) Espace3D-Wasm — 3D indoor acoustic ray tracing simulation 🔴

**Pain point**: In architectural engineering, concert hall design and high-end audio space planning, engineers must assess sound reflection, absorption and diffraction in 3D space to compute reverberation time (RT60) and sound field distribution. That requires dense **acoustic ray tracing**. Traversing a 3D geometry model in pure JS and running mesh intersection and material absorption iteration for millions of acoustic rays — without exact 64-bit spatial tree (BVH) addressing optimization — freezes the main thread for a long time.

**How it works**: A C++ high-performance indoor acoustic simulation core is compiled to Wasm via Emscripten, providing desktop-grade acoustic design. **Spatial boundary representation memory (BVH layout)**: the 3D building model's geometric vertices and the material acoustic absorption coefficient table (eight octave bands from 125 Hz to 8 kHz) are written strictly into linear memory as a binary byte stream, with a compact spatial partitioning tree built in memory. **Multi-core parallel ray evolution**: with Web Workers plus `SharedArrayBuffer`, the launch and reflection trajectories of millions of virtual acoustic rays are distributed in parallel across CPU cores, solving the impulse response at high speed at the binary level.

**Performance**: Claimed that launching 100,000 acoustic rays through a complex concert hall model of 10,000 polygons and computing full-band reverberation takes only **400–600 milliseconds** on the front end, at **80%** of native C++.

**Advantages**: Brings industrial-grade acoustic simulation to a static architectural design dashboard; **it pairs perfectly with the Web Audio API — the simulated impulse response (IR) can be convolved with music directly on the front end for live binaural monitoring preview of 3D spatial audio.**
**Disadvantages**: Dense geometry and ray tracing saturate the CPU briefly, so the total ray count must be capped carefully to avoid overload on mobile.

**Competitors**: Pure-JS geometric simulation libraries (lacking efficient vector arithmetic and cache-friendly multidimensional spatial tree addressing, more than 25× slower on high-precision spatial acoustic boundaries and entirely impractical).

---

### 69. (originally 88) Telemetry-Wasm — High-speed parsing of streaming telemetry time series 🔴

**Pain point**: Monitoring a large server cluster, an autonomous vehicle fleet or an industrial sensor network, the front end receives an unending stream of telemetry (timestamps, metric labels and values). Rendering a time series chart of millions of points live on a static monitoring dashboard, letting JS do the parsing means that a sudden "data storm" causes severe GC collapse from constantly turning binary into high-level objects, dropping the chart refresh rate into single digits.

**How it works**: A next-generation time series compression and parsing core written in Rust (or C), using a compression algorithm like Facebook's **Gorilla**, is compiled to Wasm. **A delta-of-delta time compression state machine**: data streams into linear memory, and Wasm runs delta-of-delta timestamp compression and XOR float value compression scanning directly on the raw byte stream through pointers (**creating no JS objects**). **A flat chart buffer**: parsed data is reassembled inside Wasm directly into a compact vertex matrix matching the WebGL/Canvas rendering format, bypassing JavaScript heap allocation throughout.

**Performance**: Claimed to parse and clean a large binary file of 2,000,000 high-frequency telemetry records in only **15–25 milliseconds**, more than **30× faster** than the pure-JS version, with main-thread GC pauses reduced to zero.

**Advantages**: Brings a free static monitoring dashboard industrial-grade time series big-data cleaning and live rendering; 100% zero backend cost, meeting enterprise privacy needs that logs never leave.
**Disadvantages**: The parsing algorithm inside is highly optimized for a specific time series format, so if the input format or standard protocol (Prometheus or a custom format) changes, the Wasm module must be recompiled.

**Competitors**: Pure-JS JSON/CSV parsers (out of their depth on streaming telemetry past a hundred thousand records, and prone to freezing the UI).

---

### 70. (originally 89) FeatureOCR-Wasm — Edge AI optical character feature extraction (HOG) 🔴

**Pain point**: For ID card recognition, licence plate scanning or handwriting recognition on the web, a preliminary step performs complex **feature extraction** and geometric correction on the image (histogram of oriented gradients (HOG), local binary patterns (LBP), texture analysis). Handing that dense computation to pure JS makes array traversal and floating-point arithmetic very inefficient on 4K photos; sending the whole large image to a cloud API brings expensive bandwidth metering and the risk of leaking highly sensitive documents.

**How it works**: The C++ core operators of industrial computer vision feature engineering are compiled to Wasm via Emscripten as the fallback compute engine for decentralized front-end AI. **Matrix sliding window acceleration**: the high-resolution image byte pointer captured from Canvas is written directly into Wasm linear memory, and fast pointer-driven table lookups run the convolution kernel and pixel matrix sliding window operations. **SIMD operator vectorization**: one CPU instruction computes the gradient direction and magnitude of 4 or 8 pixels in parallel, building a highly compact binary feature vector at high speed inside the sandbox.

**Performance**: Claimed that a 10-megapixel (4K) high-resolution ID photo takes only **35–50 milliseconds** on the front end for full-image HOG feature extraction and geometric correction, more than **25× faster** than pure JS.

**Advantages**: Brings a static page infinitely concurrent, zero-operations free AI feature preprocessing; 100% privacy-safe, with highly sensitive files staying entirely in the local sandbox.
**Disadvantages**: The feature extraction algorithm is fixed in the compiled binary module, so changing feature weights or the convolution formula dynamically requires recompilation.

**Competitors**: Pure-JS image processing libraries (lacking low-level memory alignment and bit-operation optimization, with CPU peaks that are too high on pixel-level traversal of large photos). **Note: OpenCV.js (case 27) is a more complete and verifiable superset of this idea.**

---

> **Summary of this part (36–70)**: This stretch is the catalog's **watershed**. The first half (36–51) is still mostly "move a mature C/C++ library onto the web," with the proportion of 🟡 rising noticeably; the second half (52–70) starts producing many entries that **cross into science and industry**, and 🔴 illustrative constructions appear densely for the first time.
> Three patterns are worth noticing. **First**, several 🔴 entries actually have 🟢 real counterparts (Cubism-OLAP → DuckDB-Wasm, FeatureOCR → OpenCV.js), meaning the idea's direction was right but "someone has already built it, just under a different name." **Second**, this part contains two clean demonstrations of the 4 GB ceiling (case 52's zk-EVM and case 53's 24-qubit limit). **Third**, case 51 (Ghidra-Wasm) forms a self-referential loop: running a decompiler in Wasm to analyze Wasm directly refutes the claim that "binaries are irreversible."
> The next part (71–101) enters the deepest water: **scientific and engineering simulation plus five foundational engines**, with the highest proportion of 🔴 — and also the best illustration of what "Wasm drove an entire field's barrier to entry to zero" really means.

---



# Appendix F: The Hundred-Case Catalog of Static-Page Wasm (Part 3) — Cases 71–101

> Authenticity tags and reading method are the same as Appendices D and E. 🟢 Verifiable · 🟡 Upstream real, Wasm port unverified · 🔴 Illustrative construction. **All performance numbers are claims from the original conversation and have not been independently verified.**
>
> **A special note on this part**: 71–101 has the highest proportion of 🔴 in the whole catalog. That **does not mean it is worthless** — quite the opposite. This stretch best illustrates Chapter 6's judgement: **scientific and engineering computation is Wasm's highest-value domain, because it satisfies four conditions at once — the algorithms are public, the C implementations are mature, the barrier to entry is very high, and the data is extremely sensitive.** Nearly every technical path described here holds up; it is simply that nobody has built it yet, or someone has and it goes by another name. **Read these as a feasibility map, not a project index.**

---

## VI. Industrial and Engineering Simulation

### 71. (originally 90) Kinematics-Wasm — Inverse kinematics for six-axis robots 🟡

**Pain point**: In automation engineering and smart manufacturing, engineers control multi-joint robotic arms from the web (digital twin dashboards, online industrial robot programming platforms). When the user drags the end effector to a 3D coordinate with the mouse, the system must compute every joint's rotation angle in real time — **inverse kinematics (IK)** — involving extremely dense nonlinear trigonometric system solving, Jacobian matrix inversion and Newton-Raphson iteration. Pure JS handling high-frequency matrix iteration, without operator overloading or cache optimization, solves slowly and easily produces unnatural "joint jumps" or deadlocks through lost floating-point precision.

**How it works**: An industrial robot kinematics core (something like C++/Rust Orocos KDL) is compiled to Wasm. **DH parameter matrix memory**: the arm's Denavit-Hartenberg geometric parameters and the target's six-degree-of-freedom pose matrix are laid out strictly as contiguous aligned `f64` in linear memory. **A zero-GC differential iterator**: the algebraic optimizer inside Wasm performs singular value decomposition (SVD) and pseudo-inverse of the Jacobian at high speed at the binary level, with each iteration completing entirely in enclosed memory.

**Performance**: Claimed that one high-precision IK convergence solve for a seven-degree-of-freedom (redundant) industrial arm takes only **0.1–0.3 milliseconds** on the front end (thousands of solves per second), more than **35× faster** than pure JS, achieving smooth real-time tracking of the mouse drag.

**Advantages**: Brings industrial-control-grade high-precision kinematics to a static industrial digital twin platform; pairs perfectly with Three.js for live 3D arm simulation; zero backend cost.
**Disadvantages**: IK involves multiple solutions and singularities, so catching the C++ exceptions inside Wasm requires heavy glue design to prevent VM crashes.

**Competitors**: Pure-JS math libraries (whose compute and numerical precision are entirely inadequate for industrial real-time control when iterating high-DOF nonlinear geometric systems and solving sparse Jacobians).

---

### 72. (originally 91) BioClust-Wasm — Hierarchical clustering of single-cell RNA expression matrices 🔴

**Pain point**: In cancer research and modern biomedicine, scientists analyze the enormous gene expression matrices produced by single-cell RNA sequencing (scRNA-seq) (tens of thousands of cells × tens of thousands of gene features). The core steps are **hierarchical clustering** and Pearson correlation distance matrix computation. Previously that required a backend HPC cluster; offering an interactive heatmap and clustering derivation directly on a static medical dashboard is impossible in pure JS, which permanently freezes the main thread or crashes with OOM on millions of float elements through heavy dynamic allocation and no cache optimization.

**How it works**: A C++ industrial matrix clustering core (the core operators of the C Clustering Library, say) is compiled to Wasm. **Cache-aligned flat matrix layout**: gene expression data is laid out strictly as contiguous aligned `f32` in linear memory; computing the distance matrix allocates no JS objects at all, pushing L1/L2 hit rates to the limit. **SIMD vectorization and parallel divide-and-conquer**: one instruction computes Euclidean distances or correlation coefficients for four gene expression values in parallel, while Web Workers distribute the huge matrix's tree partitioning across CPU cores.

**Performance**: Claimed that full Pearson hierarchical clustering of a medical matrix of 5,000 cells and 20,000 gene features takes only **400–650 milliseconds** on the front end, more than **45× faster** than pure JS.

**Advantages**: Brings a static genetic medicine documentation site install-free scientific computation; **the patient's genetic privacy data stays 100% inside the local sandbox**, meeting the strictest requirements of international medical privacy (HIPAA) regulation.
**Disadvantages**: The binary tree structure the clustering produces is extremely low-level, so converting it into interactive DOM nodes at high frequency incurs cross-boundary deserialization overhead, requiring a shared `TypedArray` buffer optimization.

**Competitors**: Pure-JS math matrix libraries (fine for lightweight chart statistics, but outclassed by medical-scale gene features, high-dimensional matrix iteration and hierarchical tree linkage algorithms).

---

### 73. (originally 92) Kyber-WebPlatform — Post-quantum cryptography (PQC) key exchange 🟡

**Pain point**: As quantum computing advances, traditional asymmetric encryption based on RSA or ECC risks being broken by Shor's algorithm. The global security field is moving to post-quantum cryptography (PQC), and NIST has designated **CRYSTALS-Kyber** the standard for quantum-resistant key encapsulation (KEM). But Kyber's foundation involves extremely complex lattice-based number theoretic transforms (NTT) and polynomial ring algebra. Running that dense bit manipulation in pure JS on the web performs terribly, and **JS offers no constant-time execution guarantee, making it highly vulnerable to side-channel attacks leaking the key**.

**How it works**: The official CRYSTALS-Kyber core, written in Rust or optimized C, is compiled to Wasm. **A constant-time NTT engine**: Wasm performs strict butterfly operations and modular multiplication in linear memory using `i32`/`i64` instructions; the code ensures at the compilation level that it **contains no dynamic branch dependent on private key data**, defending against timing side channels. **Memory-safe randomness injection**: Wasm has no built-in random number generator, so the architecture safely calls the browser's native `crypto.getRandomValues()` through JS glue to inject environmental entropy into the post-quantum encryption matrices.

**Performance**: Claimed that a standard Kyber-512/768/1024 key encapsulation and decapsulation takes only **0.2–0.5 milliseconds** on the front end (thousands per second), at **85%** of native C.

**Advantages**: Brings a static page quantum-resistant end-to-end encrypted communication; the encryption private key stays inside the user's browser forever; zero backend cost.
**Disadvantages**: PQC's public keys and ciphertexts (usually a few kilobytes) are noticeably larger than traditional ECC curves, so the front end needs sturdier network transport glue to move those larger cryptographic byte blocks.

> ⚠️ **A necessary technical correction**: the original description said "Wasm guarantees constant-time execution" — **that needs a more precise statement**. The Wasm specification itself **does not guarantee** constant time; what it guarantees is that there is no JS-engine-style behaviour of switching internal representations by data type dynamically (V8's Smi → HeapNumber, say). But **the compiler may still introduce branches and the CPU may still exhibit data-dependent cache behaviour**. Constant time is guaranteed by **how the source is written** (avoid branching on the private key, avoid indexing a lookup table by it); Wasm merely provides an execution substrate more controllable than JS. **"It uses Wasm, so it is constant-time" is a dangerous misreading.**

**Competitors**: Pure-JS cryptographic emulation libraries (JS engines perform automatic type conversion while running dense bit shifts and bignum modular division, so they **cannot guarantee constant time at all** — a fatal defect in security defence).

---

### 74. (originally 93) Hologram3D-Wasm — 3D optical holographic microscopy tomographic reconstruction 🔴

**Pain point**: In biophysics and cell imaging, digital holographic tomography (DHT) lets scientists reconstruct the 3D refractive index distribution inside a cell from multi-angle holograms without staining (non-destructively). The core is a huge 3D inverse scattering algorithm involving FFT over hundreds of high-resolution 2D interferograms, three-dimensional filtered back projection (FBP) and nonlinear multiple scattering iteration. That heavy computation previously depended on a workstation GPU.

**How it works**: A C++ 3D optical holographic reconstruction algorithm core is compiled to Wasm. **Complex 3D Fourier space memory**: a contiguous flat space of up to hundreds of megabytes is allocated in linear memory, storing the 3D frequency-domain matrix strictly as double-precision complex numbers (two `f64` for amplitude and phase), cutting memory addressing overhead substantially. **SIMD-accelerated back projection**: one CPU instruction computes optical path difference (OPD) and phase unwrapping iteration for several pixels in parallel, restoring multi-angle 2D interference fringes to 3D refractive index volume data inside the sandbox.

**Performance**: Claimed that reading 100 1024×1024 2D holograms and reconstructing a 512×512×512 3D cellular refractive index model takes only **1.8–3.2 seconds** on the front end, more than **40× faster** than pure JS.

**Advantages**: Brings a static research platform install-free desktop-grade 3D tomographic reconstruction; the biological sample data is parsed entirely locally.
**Disadvantages**: 3D holographic reconstruction is extremely memory-hungry. **With too many 2D holograms or too high a resolution it easily hits the 4 GB ceiling, so a careful "chunked pull" architecture is required** (the scenario Chapter 8's escape route one exists for).

**Competitors**: Pure-JS 3D matrix processing (lacking efficient pointer manipulation and cache-friendly multidimensional layout, crashing with OOM outright on massive floating-point 3D frequency-domain transforms).

---

### 75. (originally 94) Nesting2D-Wasm — Irregular polygon nesting optimization 🔴

**Pain point**: In machining, sheet metal fabrication, leather cutting and garment textiles, arranging thousands of arbitrarily shaped 2D parts on one sheet with rotation and tight packing to maximize material utilization is called **nesting optimization**. It is NP-hard, and its core involves solving the no-fit polygon (NFP) for irregular polygons, Minkowski sums, geometric collision detection and high-order heuristic search based on genetic algorithms or simulated annealing. Iterating irregular geometry vertex intersections repeatedly in pure JS on the front end is slow and easily overlaps parts through lost floating-point precision.

**How it works**: The C++ core algorithm library of an industrial CAD/CAM nesting system (optimized operators based on the open-source geometry library GEOS, say) is compiled to Wasm. **Flat polygon geometry memory (NFP layout)**: every part's polygon vertex coordinates and rotation angle matrices are laid out strictly as contiguous aligned `f64` in linear memory, computing polygon envelope cutting at high speed at the binary level. **Multi-core heuristic parallel search**: with Web Workers plus `SharedArrayBuffer`, genetic algorithm populations for different rotation angles and nesting orders are distributed in parallel across CPU cores.

**Performance**: Claimed that a deep nesting optimization of 200 highly irregular garment pieces (500 generations of population iteration) takes only **1.2–2.5 seconds** on the front end to produce a nesting configuration exceeding 85% utilization (in G-code/DXF), more than **35× faster** than pure JS.

**Advantages**: Brings industrial-control-grade geometric nesting optimization to a static industrial CAD/CAM cloud workbench; pairs perfectly with SVG/Canvas for live animation of the nesting toolpath.
**Disadvantages**: NFP computation is extremely complex, so if the parts contain high-frequency noisy vertices (a rough polygon produced by scanning, say), the front end must simplify the geometry first.

**Competitors**: Pure-JS geometry libraries (Poly2Tri and the like, whose compute and geometric precision are entirely inadequate for industrial production when solving Minkowski sums of dense irregular bodies and iterating high-order heuristics).

---

### 76. (originally 95) HydroSolver-Wasm (EPANET) — Pipe network hydraulics and transient fluid simulation 🟡

**Pain point**: In municipal engineering, water resources planning and nuclear plant cooling system design, engineers must run hydraulic dynamic simulations on giant pipe networks with tens of thousands of pipes, pumps and valves. In particular, the **water hammer effect** caused by a valve slamming shut requires solving a complex nonlinear hyperbolic system of partial differential equations. That usually relies on the authoritative C core **EPANET** (using finite element and method-of-characteristics approaches). Showing live pressure wave propagation through a pipe network on the web previously meant uploading the topology to a backend finite element workstation, at astronomical cost under concurrency.

**How it works**: The EPANET hydraulics core — hundreds of thousands of lines of rigorous C — is compiled to Wasm in full. **An exact sparse linear system solver**: the pipe network topology is converted in Wasm memory to a contiguous binary compressed sparse matrix, with an efficient incomplete Cholesky factorization and conjugate gradient (CG) iterator integrated internally. **A zero-GC transient advance state machine**: every time step's dynamic transient advance and nonlinear pipe friction term (Hazen-Williams or Darcy-Weisbach) solve completes entirely in contiguous memory.

**Performance**: Claimed that a full finite element solve of a giant urban pipe network of 10,000 pipe nodes evolving over 24 hours (fine transient simulation at a 0.1-second step) takes only **80–130 milliseconds** on the front end, at national water engineering standard precision and more than **35× faster** than pure JS.

**Advantages**: Brings industrial fluid mechanics solving to a static industrial digital twin water platform; pairs perfectly with WebGL for live colour contour visualization of citywide pipe network pressure wave oscillation.
**Disadvantages**: The finite element method involves extensive boundary conditions and topology matrix initialization; if the input pipe network has dead ends or non-physical topology errors, the C assertions inside Wasm easily crash the VM, so the front end needs very strong topology pre-validation glue.

**Competitors**: Pure-JS math libraries (whose compute and numerical stability are entirely inadequate for real-time industrial control when solving large sparse linear systems and iterating nonlinear fluid PDE time steps).

---

### 77. (originally 96) QuantMCMC-Wasm — Financial derivative pricing and MCMC simulation 🔴

**Pain point**: In quantitative finance and risk management, precisely valuing complex barrier options, Asian options or multi-asset path-dependent derivatives requires solving high-dimensional stochastic differential equations. The most authoritative approach runs **Markov chain Monte Carlo (MCMC)** path simulation and stochastic volatility model (the Heston model, say) iteration, which means high-frequency random sampling and PDE evolution over millions of asset price trajectories. That computation previously ran entirely on backend HPC financial clusters.

**How it works**: The C++/Rust industrial quantitative finance core (QuantLib's stochastic simulation operators, say) is compiled to Wasm. **A flat path memory layout**: a million simulated trajectories' time steps and asset matrices are laid out strictly as contiguous `f64` in linear memory, allocating no JS objects while computing asset expectations. **SIMD random number vectorization**: paired with a very fast Mersenne Twister or PCG random number algorithm, one CPU instruction generates four Gaussian random variables in parallel, advancing the Black-Scholes-Merton jump model at high speed at the binary level.

**Performance**: Claimed that pricing a stochastic volatility option by simulating 1,000,000 asset paths of 252 trading days each takes only **180–280 milliseconds** on the front end, more than **45× faster** than pure JS.

**Advantages**: Brings a static quantitative analysis platform workstation-grade high-precision derivative pricing; **a quant firm's core strategy parameters and client portfolios stay 100% local and are never uploaded to the cloud**, giving perfect trade secret protection.
**Disadvantages**: The MCMC path data lives in Wasm memory, so **if the front end wants to draw a detailed line chart of all million trajectories dynamically, the browser's DOM rendering layer faces an enormous bottleneck**; use a Canvas bitmap or sampling to lower the chart's load.

**Competitors**: Pure-JS financial math libraries (fine for ordinary compound interest and simple analytic Black-Scholes solutions, but outclassed by high-dimensional path dependence, multi-asset correlation matrix evolution and dense MCMC iteration).

---

### 78. (originally 97) AstroNoise-Wasm — Deep-space astronomical image denoising and PSF deconvolution 🔴

**Pain point**: Deep-space multispectral images from astronomical telescopes (FITS format) usually contain severe cosmic ray noise, thermal noise and optical distortion. To extract faint galactic outlines, astronomers must run **point spread function (PSF) deconvolution** (Richardson-Lucy iteration, say) and high-order non-local means denoising over gigabytes of raw pixel matrices. Traditionally that could only run on a large Linux workstation inside the observatory network.

**How it works**: A high-performance C-language image restoration algorithm core is compiled to Wasm via Emscripten. **A 3D multispectral band memory pool**: the very large high-precision pixel matrices of several bands are written into linear memory as a binary byte stream, building a compact flat 3D image matrix in memory and bypassing JavaScript object allocation entirely. **SIMD-accelerated matrix convolution**: one CPU instruction computes the weight kernel function and FFT frequency-domain filtering for 4 or 8 double-precision pixels in parallel, separating faint hidden starlight from the background noise inside the sandbox.

**Performance**: Claimed that processing a 4-band, 4096×4096 raw deep-space image with 50 Richardson-Lucy deconvolution iterations takes only **1.5–2.8 seconds** on the front end, at **80%** of native C.

**Advantages**: Brings a static science-sharing site install-free desktop-grade scientific image analysis; astronomical images are processed entirely locally, consuming none of the developer's bandwidth.
**Disadvantages**: Denoising large astronomical images is extremely memory-hungry, and **too many bands easily hits the 4 GB ceiling**, so the architecture needs chunked sliding-window streaming.

**Competitors**: Pure-JS image processing libraries (lacking efficient bit operations and cache-friendly multidimensional layout, freezing with OOM outright on massive floating-point 2D/3D frequency-domain transforms and matrix neighbourhood computations).

---

### 79. (originally 98) SynapseSim-Wasm — Large-scale network simulation of neuronal synaptic dynamics 🔴

**Pain point**: In computational neuroscience, simulating signal transmission and memory mechanisms in brain neuronal networks means solving biophysics's most famous **Hodgkin-Huxley nonlinear system of partial differential equations** — deriving the open/closed state of sodium and potassium ion channels on the cell membrane, the dynamic membrane potential and the weight evolution of thousands of synapses exactly. The authoritative simulation cores are usually written in C++. Hand-writing those neurodynamic time step iterations in JS on the web produces **numerically divergent** wrong results within a few iterations, for lack of exact 64-bit alignment and parallel matrix acceleration.

**How it works**: A computational neuroscience open-source core is compiled to Wasm, providing decentralized brain network simulation. **A synaptic adjacency binary matrix**: the complex synaptic links among tens of thousands of neurons are converted in linear memory into a flat, cache-friendly binary compressed sparse column (CSC) matrix. **A zero-GC exponential integrator**: the algebraic optimizer inside Wasm performs nonlinear approximation of the ion channel gating variables at high speed at the binary level; every time step advance completes entirely inside Wasm, cutting main-thread GC pauses to zero.

**Performance**: Claimed that simulating 10 seconds of network activity (fine derivation at a 0.1-millisecond step) over 10,000 neurons with 500,000 dynamic synaptic weights takes only **250–400 milliseconds** on the front end, at international neuroscience standard precision and more than **40× faster** than pure JS.

**Advantages**: Brings a static science and education dashboard workstation-precision biological network simulation; pairs perfectly with Three.js for live 3D visualization of neuronal spiking action potential propagation.
**Disadvantages**: Nonlinear differential systems are extremely sensitive to initial conditions, and if the input network topology contains non-physical isolated nodes or anomalous weights, the C assertions inside Wasm easily crash the VM.

**Competitors**: Pure-JS math libraries (whose compute and numerical stability are entirely inadequate for research-grade real-time simulation when iterating high-dimensional nonlinear differential systems and solving sparse synaptic network matrices).

---

### 80. (originally 99) GridPower-Wasm — Newton-Raphson AC power flow solving for smart grids 🔴

**Pain point**: In power engineering and energy planning, to ensure a grid does not black out during a sudden demand peak or an unplanned unit outage, the dispatch system must run dense **AC power flow** computation — solving a complex nonlinear algebraic system (the nodal power balance equations) for a network of tens of thousands of substations, generating units and transmission lines. The industry's most authoritative approach is **Newton-Raphson iteration** with admittance matrix solving. Handling the Jacobian inverse of a large sparse matrix in pure JS on the front end performs so badly that the page freezes.

**How it works**: A national-grade power system analysis open-source C core is cross-compiled to Wasm via Emscripten. **Compressed sparse admittance matrix memory (Y-bus)**: the large grid's nodal admittance matrix (99.9% zeros) is laid out strictly in contiguous binary CSC format in linear memory, with an efficient sparse LU factorization and forward/backward substitution iterator integrated internally, bypassing JS object creation entirely. **A zero-GC matrix correction iterator**: every Jacobian update and nonlinear power mismatch computation runs inside the Wasm sandbox, with multi-core CPUs scanning in parallel at the binary level.

**Performance**: Claimed that one AC power flow Newton-Raphson convergence solve for a large regional smart grid of 5,000 bus nodes and 12,000 transmission lines takes only **15–30 milliseconds** on the front end (dozens of solves per second), at IEEE industrial standard precision and more than **35× faster** than pure JS.

**Advantages**: Brings a static national power monitoring dashboard industrial-grade nonlinear grid solving; **guarantees that critical national infrastructure data (grid topology) is never transmitted across servers over the network** — extremely high security.
**Disadvantages**: Power flow computation involves multiple solutions and Jacobian singularities (grid collapse thresholds, say), and if the exception control inside Wasm is not fully optimized, the module can crash.

**Competitors**: Pure-JS matrix libraries (whose compute and precision are entirely inadequate for smart grid digital twin scenarios when performing complex LU factorization of large industrial sparse matrices and high-order iteration of nonlinear algebraic systems).

---

### 81. (originally 100) TopOpt3D-Wasm — Aerospace-grade 3D structural topology optimization (SIMP) 🔴

**Pain point**: In aerospace engineering and advanced manufacturing (design ahead of 3D printing), making a wing or satellite bracket "maximally light" while preserving ultimate strength requires **3D structural topology optimization**. The core is the **SIMP (Solid Isotropic Material with Penalization)** algorithm — chopping the 3D design space into millions of 3D finite elements, solving the stochastic elasticity PDE under given loads and boundary conditions, and optimizing each element's material density dynamically. That heavy computation previously depended entirely on CAD supercomputer workstations.

**How it works**: The aerospace industry's decades-accumulated C++ 3D finite element topology optimization core is compiled to Wasm in full, providing top-tier high-precision generative design. **Flat elasticity matrix memory**: the displacement vectors, stiffness matrices and material density gradients of millions of mesh elements in 3D space are laid out strictly as contiguous aligned `f64`, solving the finite element system (KU = F) by conjugate gradient at high speed at the binary level. **Multi-core sensitivity parallel filtering**: with Web Workers plus `SharedArrayBuffer`, each element's resultant stress, strain energy and material sensitivity filtering is distributed in parallel across CPU cores.

**Performance**: Claimed that 50 generations of standard SIMP topology optimization on a complex wing structure of 120,000 3D hexahedral elements (including reassembling and solving the stiffness system each iteration) takes only **2.5–4.5 seconds** on the front end to produce optimized geometry with 60% volume reduction and maximized strength, more than **50× faster** than pure JS.

**Advantages**: Brings a static advanced manufacturing cloud CAD platform install-free industrial 3D generative design; pairs perfectly with WebGL/WebGPU for live 3D visualization of "material disappearing step by step as the structure evolves."
**Disadvantages**: 3D finite element solving builds a large global stiffness matrix, so **memory grows exponentially with mesh resolution and too fine a mesh hits the 4 GB ceiling**, requiring careful sparse matrix reordering and streaming elimination architecture.

**Competitors**: Pure-JS math and geometry libraries (whose compute and numerical stability are entirely inadequate for aerospace design and manufacturing when solving large 3D finite element stiffness systems and filtering nonlinear material density sensitivity across time iterations).

---

### 82. (originally 101) Microfluidic3D-Wasm — Microfluidic channel topology optimization for bioprinting 🔴

**Pain point**: In 3D bioprinting of artificial organs and lab-on-a-chip development, designing the extremely complex micron-scale microfluidic channel network that delivers oxygen and nutrients precisely to every cell of an artificial tissue is a cutting-edge challenge. It means solving the low-Reynolds-number microfluidic Navier-Stokes system (Stokes flow) at microscopic scale plus geometric topology shape optimization. Medical engineers traditionally needed an expensive local finite element workstation.

**How it works**: The medical field's open-source C++ microfluidic physics operators and a **lattice Boltzmann method (LBM)** core are compiled to Wasm. **Microscopic lattice flat memory layout**: the channel space is discretized into a dense 3D virtual lattice, with each cell's fluid density and velocity distribution functions laid out strictly as contiguous `f32` in linear memory; the collision and streaming steps allocate no JS objects at all, pushing L1/L2 hit rates to their physical limit. **Multithreaded parallel flow field solving**: with Web Workers plus `SharedArrayBuffer`, the 3D microscopic space is cut into subregions distributed in parallel, computing channel shear stress and geometric shape gradients at high speed inside the sandbox.

**Performance**: Claimed that 1,000 steps of high-precision LBM flow field evolution and topology deformation optimization on a 3D organ channel of 64,000 microscopic lattice cells takes only **280–450 milliseconds** on the front end, more than **45× faster** than pure JS.

**Advantages**: Brings a static biomedical research platform install-free desktop-grade microscopic fluid simulation and generative design; **a medical institution's core artificial organ geometry patents and patient stem cell structure data stay 100% local.**
**Disadvantages**: The microfluidic simulation's memory layout is extremely abstract, so if the front end wants to sample local flow velocities at high frequency to draw fine 3D streamline animation, cross-boundary conversion adds overhead; share the memory pointer with a WebGL vertex buffer for direct hardware rendering.

**Competitors**: Pure-JS fluid simulation libraries (fine for 2D web smoke or water droplet visual effects, but outclassed by medical-grade microscopic low-Reynolds-number 3D PDE solving and industrial geometric topology sensitivity filtering).

---

### 83. (originally 102) SwarmPath-Wasm — Distributed motion planning and dynamic obstacle avoidance for drone swarms 🔴

**Pain point**: In autonomous driving, warehouse robotics and drone light show choreography, getting hundreds or thousands of individuals to advance in parallel through 3D space and avoid each other and dynamic obstacles autonomously and in real time, with no central server directing, is a core problem in robotics. The most authoritative algorithm solves the high-order **reciprocal velocity obstacle (RVO / ORCA)** model, which requires every agent to solve a 3D linear program and nonlinear convex optimization matrix at speed within a 60 Hz control cycle. Pure JS traversing and solving the interaction collision convex hulls among thousands of agents causes severe GC stutter from constant allocation — **and in drone swarm control, where real-time behaviour is critical, that translates directly into mid-air collisions.**

**How it works**: An industrial multi-agent dynamics and collision avoidance algorithm core written in Rust is compiled to Wasm. **A cache-friendly agent matrix (SoA state space)**: every drone's 3D position, velocity vector, physical radius and dynamic response constraints are laid out strictly as contiguous binary structure-of-arrays. **Two-level 3D KD-tree spatial addressing and parallel solving**: Wasm allocates contiguous flat memory internally to build a fast 3D KD-tree, drones search for neighbours at high speed inside the sandbox, and each drone's convex space linear programming solve is distributed in parallel through Web Workers.

**Performance**: Claimed that simulating fully distributed 3D trajectory planning, dynamic obstacle avoidance and convex optimization iteration for **2,000 drones** in one virtual space keeps each physics control cycle within **1.8–3.2 milliseconds**, locking 60 FPS at **85%** of the native core.

**Advantages**: Brings a static robot choreography tool latency-free real-time distributed motion planning; fully decentralized, saving the cost of renting a high-performance cloud parallel compute host; can drive derivations against drone hardware directly in a network-free environment.
**Disadvantages**: The RVO model's convex optimization may need high-order random perturbation at extreme deadlock configurations (every drone converging on the exact centre, say), and the state machine's boundary conditions inside Wasm are extremely delicate, requiring very strong defensive coding.

**Competitors**: Pure-JS pathfinding libraries (suited only to small-scale, low-dimensional, discrete grid path search, and orders of magnitude behind on multi-body nonlinear convex optimization for thousands of agents in high-dimensional continuous 3D space).

---

### 84. (originally 103) LiFiLight-Wasm — Indoor optical communication multipath diffuse light field simulation 🔴

**Pain point**: Wireless optical communication (LiFi) uses indoor LED lighting for ultra-high-speed data transfer. To assess signal coverage strength and multipath interference in every corner of a room, optical communication engineers must model the room's walls and furniture geometrically and run dense **indoor light field multipath diffuse radiosity numerical integration** — computing the geometric visibility (form factor) between any two surface patches and iterating thousands of photon diffuse reflection energy attenuations. Traditionally that required a backend finite element matrix workstation.

**How it works**: The C++ core of industrial optical engineering and 3D radiosity is compiled to Wasm via Emscripten. **Surface patch flat memory layout**: the 3D coordinates, normals, reflectances and initial optical power of the tens of thousands of radiosity patches into which every indoor polygonal surface is subdivided are written strictly as contiguous `f64` into linear memory, building a highly compact sparse form factor matrix at the binary level. **SIMD-accelerated hemispherical integration**: one CPU instruction computes optical path attenuation and hemispherical solid angle numerical integration (Gauss quadrature) between several patches in parallel, running Markov matrix multiplication iteration at high speed inside the sandbox.

**Performance**: Claimed that five complete multipath diffuse light field evolutions and LiFi signal throughput recomputations over a complex 3D indoor space of 5,000 geometric patches take only **120–190 milliseconds** on the front end, at ITU standard precision and more than **40× faster** than pure JS.

**Advantages**: Brings a static IoT planning dashboard light field distribution simulation as precise as professional optical software; pairs perfectly with WebGL to render LiFi signal strength as a dynamic 3D colour contour map.
**Disadvantages**: **The radiosity matrix's computation grows quadratically with patch count, O(N²)**, so an over-detailed unsimplified indoor geometry easily hits a processor bottleneck, requiring a sparse matrix compression architecture built inside Wasm to filter it.

**Competitors**: Pure-JS geometric simulation libraries (lacking efficient vector arithmetic and cache-friendly multidimensional sparse matrix addressing, extremely slow on high-dimensional optical numerical integration).

---

### 85. (originally 104) FinCopula-Wasm — Credit risk and copula solving for giant asset portfolios 🔴

**Pain point**: In the risk management of financial holding groups and multinational banks, guarding against systemic collapse means running extreme stress tests of value at risk (VaR) and expected loss on "giant portfolios" containing tens of thousands of loans, bonds or derivatives. The core solves a high-dimensional nonlinear algebraic system of **copulas** (Student-t or Clayton copulas, say) to capture the nonlinear "tail dependence" among many assets during an extreme market collapse. That involves dense Cholesky factorization of the Pearson correlation matrix, high-order nonlinear ODE iteration and giant matrix inversion.

**How it works**: A high-order quantitative finance core in C, recognized by international financial audit standards, is compiled to Wasm via Emscripten. **A flat financial covariance matrix**: the historical return series and volatility weights of tens of thousands of instruments in the portfolio are laid out strictly as contiguous aligned `f64`, with an efficient multivariate distribution sampling state machine integrated internally. **A zero-GC Cholesky matrix iterator**: every Jacobian update and maximum likelihood estimation (MLE) of high-dimensional copula tail dependence runs inside the Wasm sandbox, with multi-core CPUs scanning in parallel at the binary level.

**Performance**: Claimed that a full nonlinear solve and extreme loss computation for a 2,000-dimensional Student-t copula credit risk portfolio with 500,000 Monte Carlo path samples takes only **150–260 milliseconds** on the front end, meeting Basel accord precision and more than **35× faster** than pure JS.

**Advantages**: Brings a static quantitative platform workstation-grade high-dimensional portfolio risk measurement; **a financial group's core asset allocations and sensitive client loan details stay 100% local and are never uploaded to the cloud.**
**Disadvantages**: When solving extreme tail probabilities in high-dimensional copulas, if the asset data has serious gaps, the C numerical overflow catching inside Wasm needs careful glue design to prevent VM crashes.

**Competitors**: Pure-JS financial math libraries (fine for ordinary portfolio expected return and simple asset allocation solving, but orders of magnitude behind on high-dimensional copula tail nonlinear coupling, giant matrix Cholesky factorization and dense MCMC iteration).

---

### 86. (originally 105) DNAKinetics-Wasm — Multi-sequence hybridization thermodynamics for gene chips 🔴

**Pain point**: In modern biotechnology, disease gene screening and DNA computing, engineers must design the probes on a gene chip. That means simulating the **multi-sequence hybridization kinetics and thermodynamic equilibrium** by which thousands of single-stranded DNA sequences bind to sample DNA at a given temperature and salinity — solving a highly complex nonlinear system of mass action law equations, computing the Gibbs free energy and pairing partition function for each sequence pair, and the "cross-hybridization" effects imperfect matches cause. Iterating giant nonlinear biochemical state matrices in pure JS on the front end solves very slowly for lack of 64-bit memory layout optimization, and easily produces entirely wrong matching results through lost floating-point precision.

**How it works**: The bioinformatics field's authoritative C++ gene thermodynamics and kinetics core (the core operators of ViennaRNA or DINAMelt, say) is compiled to Wasm. **Flat base matrix memory**: every probe sequence's Watson-Crick base pairing energy parameter table and dynamic concentration matrix are laid out strictly as contiguous aligned `f64`, running multimer dynamic programming cutting computations at high speed at the binary level. **Multi-core biochemical equilibrium parallel search**: with Web Workers plus `SharedArrayBuffer`, the thermodynamic partition function matrix solves for different sequence combinations are distributed in parallel across CPU cores.

**Performance**: Claimed that a full nonlinear thermodynamic system solve and cross-hybridization equilibrium concentration prediction for 1,000 candidate DNA probe sequences against a complex viral sample sequence takes only **90–140 milliseconds** on the front end to produce an exact biochemical equilibrium constant report (free energy precision to 0.01 kcal/mol), more than **50× faster** than pure JS.

**Advantages**: Brings a static online bioinformatics workbench national-laboratory-grade gene thermodynamics derivation; pairs perfectly with HTML5 charts for live visualization of probe hybridization efficiency.
**Disadvantages**: Newton-Raphson iteration of multi-sequence nonlinear biochemical systems is extremely sensitive to initial concentrations, and if the input sequence contains invalid nucleotide characters, catching the C++ exceptions inside Wasm requires heavy glue design to prevent crashes.

**Competitors**: Pure-JS biochemical simulation libraries (whose compute and precision are entirely inadequate for clinical diagnosis when solving dense nucleic acid secondary structure partition functions and iterating high-order nonlinear biochemical kinetic equilibrium systems).

---

### 87. (originally 106) SonarICA-Wasm — Underwater sonar blind source separation and independent component analysis 🔴

**Pain point**: In ocean engineering and autonomous underwater vehicle (AUV) detection, the signal a sonar receives is usually mixed with ocean background noise, propeller cavitation noise and severe multipath reflections. Separating the true returns of a target submarine or the seabed from that chaotic waveform requires **blind source separation (BSS)**, whose mathematical core is dense **independent component analysis (ICA, such as FastICA)** — high-frequency singular value decomposition (SVD) of covariance matrices, nonlinear negentropy maximization iteration and whitening transforms over massive multi-channel audio byte streams. Traditionally that depended on a backend ocean computing host.

**How it works**: An industrial C++ array signal processing and ICA core algorithm library is compiled to Wasm via Emscripten. **Multi-channel audio flat memory layout**: the raw `ArrayBuffer` collected by the hydrophone array skips JS parsing and is written directly through a memory pointer into Wasm's contiguous linear memory; computing eigenvalues and the mixing matrix allocates no high-level JS objects at all. **SIMD vectorized matrix acceleration**: one CPU instruction runs fourth-order cumulants and dot product iterations for several channels' audio samples in parallel, restoring the independent sonar source signals at high speed inside the sandbox.

**Performance**: Claimed that high-precision FastICA blind source separation and deconvolution of a giant 8-channel sonar multipath signal stream at 192 kHz sample rate takes only **40–65 milliseconds** per frame on the front end, more than **35× faster** than pure JS.

**Advantages**: Brings a static ocean engineering dashboard workstation-precision array signal processing; detection data and underwater target signatures stay entirely local, protecting defence and commercial secrets.
**Disadvantages**: ICA is highly sensitive to the signal whitening initial matrix, and if underwater noise changes abruptly and the glue lacks overflow protection, catching the C++ exceptions inside Wasm requires heavy design to prevent crashes.

**Competitors**: Pure-JS signal processing libraries (fine for ordinary Web Audio filtering, but whose compute and numerical stability are entirely inadequate for industrial ocean control when iterating high-dimensional multi-channel nonlinear matrices and approximating fourth-order matrix maximum likelihood).

---

### 88. (originally 107) TSNSched-Wasm — TSN time slot scheduling and MILP heuristic search for the connected car 🔴

**Pain point**: In smart transportation, vehicle-to-everything (V2X) and Industry 4.0 smart factories, ensuring an autonomous vehicle's braking command or a robotic arm's synchronization signal is never delayed requires the network stack to adopt the **time-sensitive networking (TSN)** standard. TSN's core value is microsecond-precise gate control list (GCL) scheduling. Allocating non-conflicting time slots for thousands of periodic and aperiodic hard real-time data flows across every switch in the network is an NP-hard **mixed integer linear programming (MILP)** problem. That previously ran only on a dedicated backend scheduling server; pure JS facing tens of thousands of time window constraints freezes for minutes from array slicing and excessive CPU peaks.

**How it works**: The C++ core toolchain of industrial network scheduling plus high-performance heuristic search (tabu search, simulated annealing) algorithm libraries are compiled to Wasm. **Flat network topology memory layout**: network nodes, switch ports, flow periods and maximum tolerable latency constraints are laid out strictly as a binary structure-of-arrays. **Multi-core constraint solving parallelization**: with Web Workers plus `SharedArrayBuffer`, fast interval trees and non-conflict hash tables are built, and different scheduling branches and branch-and-bound tasks are distributed in parallel across CPU cores.

**Performance**: Claimed that GCL time slot scheduling optimization (satisfying zero-jitter constraints) for a giant TSN topology of 50 switch nodes and 2,000 high-frequency V2X data flows takes only **800–1200 milliseconds** on the front end to produce a conflict-free schedule, more than **40× faster** than pure JS.

**Advantages**: Brings a static network management console industrial-grade time-sensitive scheduling computation; fully decentralized, so an engineer commissioning a 5G V2X or factory automation line on site can compute topology extremely fast from a web page.
**Disadvantages**: MILP solving has an unpredictable convergence time at deadlock boundaries under extreme network overload, requiring a carefully built **timeout forced-interrupt state machine** inside Wasm.

**Competitors**: Pure-JS linear programming libraries (suited only to small linear optimization, and entirely inadequate in compute and memory scheduling for industrial production when facing tens of thousands of microsecond-scale hard time window constraints, dense topology routing and mixed integer approximation).

---

### 89. (originally 108) AstroAO-Wasm — Adaptive optics atmospheric turbulence wavefront reconstruction 🔴

**Pain point**: When a large ground-based astronomical telescope observes distant galaxies, starlight passing through the atmosphere is distorted by turbulence. Modern observatories use **adaptive optics (AO)**, where a wavefront sensor captures distortion data thousands of times per second and computes the adjustment voltage of the deformable mirror's hundreds of actuators in real time. The core is a large **nonlinear matrix inversion for wavefront reconstruction** — singular value decomposition of a large sparse Jacobian and high-order polynomial fitting. Traditionally that had to run on hardware FPGAs local to the observatory.

**How it works**: A top international observatory's open-source C++ adaptive optics reconstruction algorithm core is compiled to Wasm via Emscripten. **Wavefront geometry flat memory layout**: the slope data for the thousands of subapertures the wavefront sensor carves out plus the deformable mirror control matrix are written strictly as contiguous `f64` into linear memory, building a highly compact sparse control matrix at the binary level and bypassing JavaScript object allocation entirely. **SIMD-accelerated gradient inversion**: one CPU instruction computes several subapertures' wavefront phase slopes and least squares iteration in parallel, running matrix multiplication solving at high speed inside the sandbox.

**Performance**: Claimed that one full atmospheric turbulence wavefront distortion correction and control matrix recomputation for a giant AO system of 4,096 subapertures and 1,000 deformable mirror actuators takes only **8–14 milliseconds** on the front end (nearly a hundred per second), at aerospace and astronomy industrial precision and more than **45× faster** than pure JS.

**Advantages**: Brings a static science-sharing site install-free desktop-grade wavefront reconstruction and atmospheric optics simulation; astronomical optical data is processed entirely locally.
**Disadvantages**: **The wavefront inversion matrix's computation grows with the cube of the aperture count, O(N³)**, so an over-detailed sensor grid without dimensionality reduction easily hits a single-core bottleneck, requiring a sparse matrix incomplete Cholesky factorization built inside Wasm to filter it.

**Competitors**: Pure-JS image and matrix libraries (lacking efficient pointer arithmetic and cache-friendly multidimensional sparse matrix addressing, extremely slow on high-dimensional optical numerical matrix inversion).

---

### 90. (originally 109) MicroPhase-Wasm — Phase field simulation of metallic grain evolution in materials science 🔴

**Pain point**: In materials science, metallurgy and aerospace alloy manufacturing, how "grain structure" evolves during metal solidification or heat treatment determines the material's mechanical strength and fatigue life directly. Simulating grain crystallization, grain boundary segregation and dendritic growth precisely means solving a complex **phase field nonlinear system of partial differential equations (Allen-Cahn or Cahn-Hilliard)** — running hundreds of thousands of Laplacian discretizations, interface curvature computations and dense time step evolutions over a 3D or 2D microscopic space grid. That previously depended on a national materials laboratory's GPU supercomputing cluster.

**How it works**: A materials physics open-source C++ high-performance phase field simulation core is compiled to Wasm. **Flat grain order parameter memory**: each grid point's phase field order parameter, solute concentration and elastic strain energy are laid out strictly as contiguous aligned `f32`, maximizing processor cache hit rates. **A SIMD spatial difference accelerator**: one CPU instruction solves high-order finite difference Laplacians for 4 or 8 spatially symmetric points in parallel; every time step's nonlinear dynamic advance runs entirely inside the Wasm sandbox.

**Performance**: Claimed that 5,000 steps of high-precision crystallization, dendritic growth and grain boundary evolution iteration on a 512×512 grid multi-component alloy microstructure takes only **350–550 milliseconds** on the front end, at international materials physics standard precision and more than **50× faster** than pure JS.

**Advantages**: Brings a static materials engineering page research-laboratory-grade microstructural physical evolution; **an alloy's core formulation and crystallization evolution signature data stay 100% local**, protecting patents.
**Disadvantages**: The Cahn-Hilliard equation is a fourth-order nonlinear PDE with extremely strict time step stability requirements; if the user inputs non-physical initial solute fluctuations, a careful **adaptive time step control state machine** must be built inside Wasm.

**Competitors**: Pure-JS math and image libraries (orders of magnitude behind on dense microscopic-space PDE finite difference solving and multi-component order parameter time step iteration).

---

### 91. (originally 110) CSTRFlow-Wasm — Stiff ODE solving for chemical reactors 🔴

**Pain point**: In chemical engineering, fine pharmaceutical manufacturing and modern chemical plants, the continuous stirred-tank reactor (CSTR) is the core equipment for synthesizing drugs and chemical feedstocks. Controlling reaction yield precisely and preventing **thermal runaway** explosions means simulating the nonlinear multiphase chemical kinetics inside the reactor — solving extremely hardcore **stiff ordinary differential equation systems**, computing the Arrhenius reaction rate matrix and mass transfer balance for dozens of chemical components at various temperatures, pressures and stirring rates. Solving that class of highly stiff system in pure JS on the front end (where reaction rate constants differ by orders of magnitude) makes standard Runge-Kutta fail entirely; implicit methods (Gear or Radau5) then require solving a giant nonlinear Jacobian inverse at high frequency, and JS — lacking exact memory layout optimization — solves slowly and easily distorts results through lost floating-point precision.

**How it works**: The chemical industry's authoritative C++ stiff differential equation and thermodynamic equilibrium solving core is compiled to Wasm. **Chemical component thermodynamic memory**: every participating component's enthalpy, entropy, reaction rate constants and dynamic concentration matrix are laid out strictly as contiguous aligned `f64`, running implicit Euler and quasi-Newton iteration at high speed at the binary level. **A zero-GC stiff differential iterator**: the algebraic optimizer inside Wasm reassembles and solves the reaction system's sparse Jacobian dynamically at high speed in enclosed memory, creating no JS garbage objects on any time step.

**Performance**: Claimed that a 24-hour dynamic evolution and transient thermal runaway boundary prediction for an industrial CSTR with 32 chemical components, complex parallel competing reactions and non-isothermal heat balance constraints takes only **45–80 milliseconds** on the front end to produce exact concentration and temperature time series (solve precision to 10⁻⁸), more than **55× faster** than pure JS.

**Advantages**: Brings a static chemical digital twin tool industrial-grade chemical kinetics solving; pairs perfectly with HTML5 charts for live visualization of reactor temperature oscillation.
**Disadvantages**: Implicit solving of stiff systems depends heavily on the convergence of nonlinear iteration, and if the user inputs non-physical extreme negative concentrations or initial temperatures, catching the C++ exceptions inside Wasm requires heavy glue design.

**Competitors**: Pure-JS ODE libraries (whose compute and numerical stability are entirely inadequate for industrial control and digital twin scenarios when facing highly stiff chemical kinetic systems and high-frequency implicit solving of giant Jacobians).

---

## VII. Five Foundational Engines

> The five categories in this section (software engine, physics engine, world engine, LLM engine, graphics engine) are a new classification dimension the user specified themselves at entry 111 of the original conversation — **exactly the effective technique Chapter 6 mentions: constraining the search space works better than demanding recall.**

### 92. (originally 111) OpenLISP-Wasm [software engine] — A symbolic computation and functional LISP core 🟡

**Pain point**: In symbolic AI, expert systems and metaprogramming, LISP's **S-expressions** and homoiconicity ("code is data") are irreplaceable. Providing a secure symbolic computation playground or online rule compilation engine on the web by converting LISP code into JS objects directly triggers catastrophic GC freezes in JavaScript, because LISP creates cons cells, binds dynamic scopes and recurses in tail position extremely often.

**How it works**: An industrial C-language micro LISP core interpreter is compiled to Wasm. **A flat pointer memory pool**: LISP's environment binding tree and cons cells no longer live as discrete JS objects but are compressed into contiguous binary arrays in linear memory; Wasm maintains a very fast **self-built mark-and-sweep garbage collector** internally, bypassing the browser's JS heap scheduling entirely. **Tail call optimization support**: using Wasm's **`return_call` (tail calls, now in the Wasm 3.0 core specification)** instruction, LISP's deep recursion is turned at the binary level into flat register-level jumps, eliminating stack overflow.

**Performance**: Claimed that an algebraic theorem-proving script with 1,000,000 symbol substitutions and deep recursive matching takes only **35–55 milliseconds** on the front end, at **82%** of native C and more than **30× faster** than a pure-JS LISP interpreter.

**Advantages**: Brings a static online teaching and symbolic computation platform a zero-backend-cost secure execution environment; an enterprise's core business rule scripts stay entirely local.
**Disadvantages**: The LISP symbol tree is highly compact in Wasm memory, so serializing it to JSON often from front-end JS incurs cross-boundary overhead, requiring a shared `TypedArray` buffer optimization.

> 💡 **This is the only case in the whole book that uses Wasm's tail call instruction directly.** It also explains why Chapter 1's line — "without tail calls, deep recursion in functional languages will always blow the stack" — was a debt that had to be repaid.

**Competitors**: Pure-JS LISP emulation libraries (lacking efficient binary pointer manipulation and native tail call optimization, causing constant GC stutter and crashes on large symbol lists).

---

### 93. (originally 112) OpenVDB-Wasm [physics engine] — Sparse 3D volumetric fluid and smoke simulation 🟡

**Pain point**: In film visual effects and high-end industrial physical simulation, smoke, fire, liquids and the "surface tearing and dynamic collision" of complex 3D rigid bodies require storing and processing enormous 3D spatial grid data. The gold standard is DreamWorks' open-source **OpenVDB** (using the revolutionary hierarchical sparse B+ tree VDB-Tree). Simulating a giant 1024³ dynamic fluid volume with ordinary pure-JS 3D arrays costs gigabytes of memory and crashes with OOM outright during high-frequency level set curvature transforms and particle collision detection.

**How it works**: The OpenVDB volumetric physics engine core — hundreds of thousands of lines of accumulated C++ — is compiled to Wasm via Emscripten. **A highly compact sparse 3D spatial tree**: physical space is discretized into a 3D sparse topology tree, and Wasm maintains maximally optimized contiguous binary cache-friendly arrays internally, **storing only the nodes that contain fluid or smoke density**, pushing L1/L2 hit rates to the limit. **SIMD operator vectorization**: one instruction computes the Navier-Stokes pressure PDE for 4 or 8 volume grid points in parallel, advancing physics steps in parallel with threads inside the sandbox.

**Performance**: Claimed that simulating 500,000 highly sparse smoke volume particles diffusing and colliding with rigid body surfaces in a scene containing complex irregular 3D models takes no more than **8–12 milliseconds** per physics step, locking 60 FPS.

**Advantages**: Brings a static 3D effects dashboard install-free film-grade physical simulation; **it pairs perfectly with WebGPU shaders — the sparse volume matrix Wasm computes can be volume ray-cast on the GPU for live rendering.**
**Disadvantages**: OpenVDB's code volume is enormous, so the compiled Wasm is usually **4–6 MB**, a noticeable load burden on first entry.

**Competitors**: Pure-JS 3D physics libraries (suited only to small-scale, low-precision consumer effects and outclassed by industrial high-dimensional sparse 3D volume level set evolution and multi-body collision solving).

---

### 94. (originally 113) ProcPlanet-Wasm [world engine] — Infinite procedural virtual planet terrain generation 🔴

**Pain point**: In space simulation, digital twin Earths and very large sandbox games, generating a "1:1 scale virtual planet world" with exact landforms, river topology, vegetation distribution and atmospheric optical scattering in real time is extremely hardcore. The core is a **procedural world generation engine**, involving dense 64-bit high-order fractal noise (simplex noise, FBM), plate tectonic erosion algorithms and solving the nonlinear Rayleigh and Mie atmospheric light scattering equations. Computing millions of terrain mesh vertices dynamically in pure JS as the mouse moves causes severe terrain pop-in, for lack of cache-optimized multidimensional array addressing.

**How it works**: A high-precision procedural virtual world generation engine core written in Rust is compiled to Wasm. **A dynamic continuous level-of-detail octree**: the virtual planet is managed in linear memory as a flat octree structure, and as the camera moves closer or further the optimizer inside Wasm performs mesh splitting and simplification at high speed at the binary level. **SIMD operator vectorized fractals**: one CPU instruction computes the high-order noise oscillation function for 4 or 8 surface coordinates in parallel, with no JS garbage allocation anywhere.

**Performance**: Claimed that while the user flies supersonically over the virtual planet's surface, **up to 2,000,000** 3D terrain vertices with high-precision normals and erosion features can be generated dynamically per second, at **80%** of the native core, holding a full 60 FPS.

**Advantages**: Brings a static platform "cosmic-scale" infinite procedural world generation; **zero backend disk storage cost — the world is computed live from a seed and no terrain data is stored at all.**
**Disadvantages**: A procedural world engine involves complex thermodynamic atmospheric scattering integration, and on low-end devices with poor GPU support, Wasm's pure-CPU fallback for atmospheric diffuse reflection produces performance spikes.

**Competitors**: Pure-JS terrain generators (lacking low-level memory alignment and bit-operation optimization, with CPU peaks that are too high on large-scale fractal matrix computation and badly lagging terrain loading).

---

### 95. (originally 114) RWKV-Core-Wasm [LLM engine] — Ultra-low-memory inference for a linear attention large model 🟢

**Pain point**: Running large language model inference in the browser, the mainstream Transformer architecture faces a fatal bottleneck: **the KV cache grows linearly or quadratically with context length**, so the browser easily exceeds its memory ceiling and crashes on a conversation of tens of thousands of words. In response the open-source world produced the next-generation architecture **RWKV** (a Transformer based on a linear recurrent neural network), which compresses the KV cache into a **constant-size Time-Mix / Channel-Mix state vector**. But running RWKV's weight matrix multiplications smoothly on the front end is impossible in pure JS: facing billions of floating-point operations, token output slows to one character per second.

**How it works**: RWKV's official open-source C/Rust inference engine core is compiled to Wasm as the edge compute engine for a decentralized private LLM. **Flat weight matrix memory layout**: the model's quantized weights (INT4/INT8) are written directly into linear memory as a binary byte stream, and Wasm runs the linear attention matrix multiply-accumulate (GEMM) through fast pointer-driven table lookups. **SIMD operator vectorized dequantization**: one CPU instruction decompresses and converts 4 or 8 INT4 weights to floating point in parallel, while Web Workers distribute the model matrix in blocks across CPU cores for synchronized inference.

**Performance**: Claimed that with a 1.5B-parameter lightweight RWKV model loaded and SIMD and threads on, front-end token generation reaches **15–25 tokens per second**, at **75%** of the native core.

**Advantages**: Brings a static page edge AI inference with "unlimited context length and no memory explosion"; **all of the user's private conversations and confidential code stay 100% local**; zero backend GPU cost.
**Disadvantages**: Although RWKV is very memory-frugal, a 1.5B-parameter model file is still hundreds of megabytes compressed, so first entry means a long wait — **it is best configured as a PWA with local persistent caching** (exactly Chapter 7's OPFS use case).

**Competitors**: Pure-JS neural network libraries (lacking strict type optimization, efficient binary bit-shift parsing and register-level matrix arithmetic, freezing outright on large model inference).

---

### 96. (originally 115) Pagmo-Wasm [optimization engine] — Multi-objective global optimization and evolutionary computation 🟡

**Pain point**: In aerospace trajectory design (ESA's interplanetary probe path planning), logistics supply chain scheduling and advanced engineering structural design, engineers face **multi-objective global optimization** — solving hundreds of mutually conflicting extreme criteria at once while escaping vast numbers of local optima. The world's foremost nonlinear evolutionary computation core is ESA's open-source **pagmo** (based on a generalized island model). Running parallel population evolution for particle swarm optimization (PSO), differential evolution (DE) or NSGA-II in pure JS on the front end causes exponentially exploding memory and CPU peaks during high-frequency topological migration and mutation crossover, freezing the browser completely.

**How it works**: ESA's official open-source C++ multi-objective optimization engine pagmo is compiled to Wasm in full. **Heterogeneous island memory layout**: every optimization island's population gene matrix, fitness score table and constraint boundaries are laid out strictly as contiguous aligned `f64`, filtering the Pareto front at high speed at the binary level. **A multi-island heterogeneous parallel evolution state machine**: with Web Workers plus `SharedArrayBuffer`, a fast migration queue is built — **each Worker thread simulates an independently evolving ecological island, and the islands exchange genes periodically through binary pointers** — with no JS garbage allocation anywhere.

**Performance**: Claimed that a full global optimization evolution of an industrial extreme nonlinear function with 50 dimensions, 3 conflicting objectives and a population of 10,000 individuals takes only **450–700 milliseconds** on the front end to produce an exact Pareto optimal set, more than **40× faster** than pure JS.

**Advantages**: Brings a static industrial CAD/CAM workbench and research dashboard aerospace-grade multi-objective global optimization; pairs perfectly with HTML5 charts for live animation of the Pareto front's evolution.
**Disadvantages**: Evolutionary computation involves extensive random mutation, and if the objective function contains highly nonlinear singularities, catching the C++ exceptions inside Wasm requires heavy glue design.

**Competitors**: Pure-JS genetic algorithm libraries (orders of magnitude behind in compute and numerical stability on high-dimensional multi-objective optimization, large-scale heterogeneous island parallel evolution and high-frequency topological migration).

---

### 97. (originally 116) AMReX-Core-Wasm [software engine] — Adaptive mesh refinement (AMR) for giant PDE simulation 🟡

**Pain point**: In astrophysical explosion simulation, combustion fluid dynamics and climate prediction, when solving spatial PDEs some regions (a shock front, a flame core) change so violently that they need very high mesh resolution, while the remaining gentle regions need only a coarse mesh. The industrial gold standard is Lawrence Berkeley National Laboratory's open-source **AMReX** framework engine. Providing dynamic mesh splitting and reassembly on the web is impossible in pure JS, which produces constant memory fragmentation from pointer chasing and realignment across millions of multi-level nested grids, freezing the main thread permanently.

**How it works**: The AMReX software engine — hundreds of thousands of lines of accumulated C++ core — is compiled to Wasm via Emscripten. **A flat multi-level pointer memory pool**: the spatial topology and boundary conditions of the multi-level nested grids no longer live as discrete JS objects but are compressed into contiguous binary cache-friendly arrays; when a physical quantity's gradient exceeds a threshold, Wasm performs a binary pointer offset directly to split off a subgrid dynamically. **SIMD operator vectorized differencing**: one CPU instruction solves high-order finite difference fluxes for 4 or 8 grid points in parallel, bypassing the browser's JS heap allocation throughout.

**Performance**: Claimed that when simulating a nonlinear fluid flow field with shock oscillation, managing 5 nested grid levels dynamically and advancing high-precision PDE time steps takes only **180–290 milliseconds** per frame on the front end, at **80%** of native C++ and more than **35× faster** than pure JS.

**Advantages**: Brings a static teaching and research platform a national-laboratory-grade, zero-backend-cost giant algebra and mesh splitting engine; a researcher's sensitive core parameters stay entirely local.
**Disadvantages**: The data structures AMR produces are extremely low-level, so serializing them to JSON often from front-end JS incurs cross-boundary overhead; use a shared `TypedArray` buffer and render contour maps in hardware through WebGL.

**Competitors**: Pure-JS PDE libraries (lacking efficient binary pointer manipulation and compact memory alignment, with exponentially exploding memory and CPU peaks on dense adaptive dynamic mesh refinement).

---

### 98. (originally 117) ChronoEngine-Wasm [physics engine] — Multiphase granular flow and fluid-structure interaction (FSI) 🟡

**Pain point**: In mechanical engineering, off-road vehicle terrain dynamics and pharmaceutical mixing processes, you need to simulate the **fluid-structure interaction (FSI)** and nonlinear friction collisions between hundreds of thousands of discrete particles (sand, pills) and complex 3D mechanical rigid bodies. The gold standard is the open-source industrial multibody physics engine **Project Chrono**. Simulating a giant system of 100,000 sand particles colliding with a tracked vehicle in an ordinary pure-JS 3D rigid body library (Matter.js) explodes memory and collision detection complexity exponentially and crashes the tab with OOM.

**How it works**: The Chrono physics engine core — hundreds of thousands of lines of top-tier accumulated C++ — is compiled to Wasm via Emscripten. **A compressed sparse nonlinear constraint layout**: every discrete particle's mass, 3D coordinates and velocity, plus the friction contact constraints based on **DVI (differential variational inequalities)**, are laid out strictly as a contiguous binary structure-of-arrays in linear memory. **A SIMD vectorized cone programming solver**: one CPU instruction computes second-order cone programming (SOCP) convex optimization iterations for several particle contact surfaces in parallel, with the spatial partitioning of vast particle counts distributed through Web Workers plus `SharedArrayBuffer`.

**Performance**: Claimed that simulating **100,000 discrete flowing particles** colliding, stacking and solving nonlinear friction resistance against a robotic arm on irregular terrain in a 3D scene takes no more than **6–10 milliseconds** per physics step, locking 60 FPS.

**Advantages**: Provides mechanical and soil mechanics industrial-grade high-precision physical feedback, eliminating pure-JS physics engines' inability to handle "vast granular flow and multibody fluid-structure interaction"; the Wasm module is highly self-contained and needs no backend simulation server at all.
**Disadvantages**: Chrono involves extremely complex stiff differential equations and time integration solving, so an extreme non-physical impact force from the user must be prevented from crashing the Wasm VM.

**Competitors**: Ammo.js / Cannon.js (fine for lightweight 3D web game rigid body collisions, but entirely impractical for industrial FSI and nonlinear sliding friction solving past hundreds of thousands of dimensions with massive granular flows).

---

### 99. (originally 118) CivEvo-Core-Wasm [world engine] — Multi-agent geopolitics and climate economics simulation 🔴

**Pain point**: In climate change economics, macro historical dynamics (cliodynamics) and large strategy sandbox games, generating and deriving a "multi-level virtual world model" containing tens of thousands of virtual nations/factions, millions of autonomously deciding multi-agents, dynamic resource consumption and global climate feedback in real time is a technical feat. The core involves dense stochastic game matrix solving, nonlinear population dynamics (Malthusian models) and nonlinear Walrasian equilibrium iteration over giant supply-demand networks. Computing a million agents' economic transactions and resource games dynamically per time step in pure JS causes severe GC pauses from dynamic typing and constant object creation, tearing the world derivation's picture.

**How it works**: An industrial multi-agent world dynamics simulation core written in Rust or optimized C++ is compiled to Wasm. **A flat state space matrix**: every node in the virtual world, each faction's resource totals and each agent's decision weight matrix are laid out strictly as contiguous aligned `f64`, maximizing L1/L2 hit rates. **Multi-core island parallel gaming**: with Web Workers plus `SharedArrayBuffer`, Wasm allocates contiguous flat memory to build a fast market clearing graph, distributing different continents'/regions' agent decisions and resource evolution in parallel, with no JS garbage allocation anywhere.

**Performance**: Claimed that under the heavy load of a world map with 1,000 city factions and 1,000,000 independent agents, each world tick takes no more than **15–25 milliseconds**, at **82%** of the native core, sustaining very smooth live derivation.

**Advantages**: Brings a static platform "national-scale" global climate economics and geopolitical multi-level world simulation; **the world is computed live from a seed, eliminating the disk cost of vast backend save servers.**
**Disadvantages**: A world engine involves highly complex nonlinear multivariate feedback, and if one submarket's parameters go out of balance, the economic equations easily fail to converge, requiring a carefully built **adaptive damping state machine** inside Wasm.

**Competitors**: Pure-JS simulators (lacking low-level memory alignment and dense binary bit-shift parsing, with CPU peaks that are too high on large-scale multi-agent relationship graph lookups and algebraic iteration, and badly lagging world derivation).

---

### 100. (originally 119) DeepSpeed-MoE-Wasm [LLM engine] — Dynamic gated inference for the mixture-of-experts architecture 🟡

**Pain point**: For LLM inference at the edge, the latest gold standard architecture is **mixture of experts (MoE)** (Mixtral, for instance) — total parameters run to tens of billions, but each inference activates only a small subset of expert networks, saving compute. But MoE brings another fatal penalty for the front end: **the enormous model size (usually tens of gigabytes) cannot possibly fit in client memory.** And running MoE's dynamic gating network routing and weight dequantization multiplication smoothly on the front end is impossible in pure JS — facing billions of floating-point operations, token output freezes entirely.

**How it works**: An industrial large-model parallel optimization toolkit (Microsoft DeepSpeed's inference operator core, say) is compiled to Wasm as the edge solving engine for a decentralized private MoE model. **Dynamic sparse weight memory**: Wasm computes the gating network's top-K expert routing through fast pointer-driven table lookups; **only the currently activated experts' weights reside in linear memory, with OPFS performing binary block streaming swap between disk and memory**. **SIMD operator vectorized dequantization**: one CPU instruction decompresses and computes matrix multiply-accumulate for 4 or 8 INT4/INT8 weights in parallel, while Web Workers distribute the expert matrices across CPU cores.

**Performance**: Claimed that with a lightweight 8×7B MoE model that activates only 2 experts per inference loaded and SIMD and threads on, front-end token generation reaches **12–18 tokens per second**, at **75%** of the native core.

**Advantages**: Brings a static page edge AI inference with "a large model architecture and a small memory footprint"; the user's private conversations and sensitive code stay 100% local; zero backend GPU cost.
**Disadvantages**: Although weight streaming swap runs through OPFS, it **demands a lot of the local disk's random read speed (SSD performance)**, producing noticeable time-to-first-token (TTFT) latency on a traditional slow drive.

> 💡 **This is the case in the whole catalog that fuses Chapters 7 and 8 most thoroughly**: it uses both OPFS random reads (Chapter 7) and sliding-window streaming (Chapter 8's escape route one) to get around the 4 GB ceiling — **and its bottleneck lands ultimately on the user's SSD, which is the best possible footnote to the second half of the sentence "zero server cost": the cost did not vanish; it became someone else's hardware.**

**Competitors**: Pure-JS neural network libraries (lacking strict type optimization and register-level matrix arithmetic, freezing outright on MoE's complex gating network scheduling).

---

### 101. (originally 120) Mitsuba-Spectral-Wasm [graphics engine] — Multispectral radiometry and inverse ray tracing 🟡

**Pain point**: In aerospace remote sensing, coating optical design and advanced inverse rendering, an ordinary RGB three-channel rendering engine cannot meet physical accuracy requirements at all. Scientists need a **multispectral radiometric ray tracing engine** covering dozens of continuous wavelengths (380 nm–780 nm at 5 nm intervals), solving the rigorous geometric approximation of Maxwell's equations and bidirectional reflectance distribution functions (BRDF). The world's foremost research-grade core is the **Mitsuba** rendering engine (C++). Doing multispectral ray-grid intersection and surface polarization state matrix iteration with ordinary pure-JS vectors produces severe CPU peaks on high-dimensional spectral integration and freezes the page.

**How it works**: The multispectral optical solver of the Mitsuba rendering engine core is compiled to Wasm in full. **High-dimensional spectral flat memory layout**: every ray's per-band energy signature, surface geometry vertices and material complex refractive index matrices are laid out strictly as contiguous aligned `f64`, running Monte Carlo path tracing integration at high speed at the binary level. **A SIMD vectorized wavelength integration state machine**: one CPU instruction computes photon energy attenuation and Fresnel equation reflectance for 4 or 8 different wavelengths in parallel, with multi-core CPUs scanning in parallel at the binary level and no JS garbage allocation anywhere.

**Performance**: Claimed that full multispectral path tracing and inverse geometric optimization of a 3D optical scene with complex multilayer thin film interference materials takes only **400–650 milliseconds** on the front end to render one frame at aerospace optical precision, more than **45× faster** than pure JS.

**Advantages**: Brings a static aerospace remote sensing and optical design dashboard a research-laboratory-grade multispectral graphics engine; zero backend cost, keeping core optical formulation data safely parsed on the local machine.
**Disadvantages**: Multispectral rendering involves extensive random wavelength sampling, and if the material geometry boundaries are extremely complex, catching the C++ exceptions inside Wasm requires heavy glue design.

**Competitors**: Three.js (fine for commercial 3D web display, but orders of magnitude behind on hardcore physical multispectral photon energy evolution, complex refractive index polarization matrix solving and high-precision optical wavelength integration).

---

## Catalog Conclusion: Five Things 101 Cases Tell Us

**One: Wasm has successfully broken the physical wall between the browser and advanced low-level system computation.** From case 1's web media transcoding to case 101's aerospace-grade multispectral ray tracing, it has turned hardcore technologies — zero-knowledge privacy proofs, quantum state simulation, P2P network multiplexing, industrial power flow iteration, big-data multidimensional aggregation — into entirely free, decentralized, end-to-end private static web assets.

**Two: the underlying technical essence of all 101 cases is remarkably consistent.** A cache-friendly flat memory layout plus SIMD vectorization outclasses JavaScript's flexible but fragmented object allocation. **Those five architectures (flat memory zero-copy, Worker isolation, SIMD, streaming chunking, AudioWorklet isolation) are fully dissected in Chapter 6.**

**Three: four motivations determine the return on investment.** Shifting compute cost (nearly every entry), data sovereignty (about 70%), capability gap (about 30%) and asset revival (about 20%). **The more of them you hit, the higher Wasm's return; if you hit none, don't use Wasm.**

**Four: every case runs into the same few walls.** The 4 GB linear memory ceiling (case 22's dictionary, 52's zk-EVM, 53's 24 qubits, 74's holographic reconstruction, 81's mesh resolution), module size (case 7's 30–50 MB, 13's 10–15 MB, 28's 10–15 MB), and `SharedArrayBuffer` with cross-origin isolation (cases 1, 32, 62, 68, 75, 81 and every other multithreaded entry). **Those walls are fully dissected in Chapters 3, 5 and 8 — they are not implementation defects but direct corollaries of the specification.**

**Five, and most important: a substantial portion of these 101 entries is illustrative.** That does not weaken their value; it explains this catalog's real use — **it is a feasibility map of "is this road passable," not a list you can `git clone`.** Nearly every 🔴 entry's technical path holds up; it is simply that nobody has built it, or someone has and it goes by another name (case 66 versus DuckDB-Wasm and case 70 versus OpenCV.js are the best examples).

> **If you take one sentence away from this catalog, take this one**:
> **Wasm made "driving an entire field's barrier to entry to zero" something one person can do — what you need is not resources, but knowing which road is already open.**

---

**One last signpost**: this catalog is a map of "is this road passable," **and Appendix L is the place at the end of the road where someone actually lives** — FluffOS compiles an entire LPMud driver into the browser, and `fluffos/mudlibs` repairs two hundred 1990s Chinese MUD sources and packages them as static bundles. It is simultaneously the real version of this part's two 🔴 concepts (case 58 Minestom-Wasm and case 60 Micro-Apache-Wasm), and the cleanest living specimen of the book's central thesis. **If you want to see only one case taken all the way down, read that one.**

---



# Appendix G: Storage Implementation Reference (Rust + Wasm + OPFS)

> This appendix provides a complete implementation for the **front-end web (Rust + WebAssembly + OPFS)** — currently the industry's gold standard (Figma, Adobe Web and the like) for high-performance big-data persistence in a pure front-end environment.
>
> The examples show how to use OPFS's `FileSystemWritableFileStream` and `FileSystemSyncAccessHandle` to perform **zero-copy** binary large-file reads and writes inside Wasm, so the data stays on the client permanently even after the page reloads.
>
> ⚠️ **`web-sys`'s API names and builder forms change between versions** (the way `FileSystemGetFileOptions` is constructed differs across versions, for instance). The code below is an **architectural reference**; when you actually compile, follow the documentation for the `web-sys` version you use.

---

## 1. Approach A: An asynchronous write stream (usable on the main thread)

### 1. The Rust core (`src/lib.rs`)

```rust
use wasm_bindgen::prelude::*;
use wasm_bindgen_futures::JsFuture;
use web_sys::{FileSystemDirectoryHandle, FileSystemWritableFileStream, StorageManager};

#[wasm_bindgen]
pub struct WasmStorageEngine {
    /// Hold the engine state so we don't re-initialize
    root_dir: FileSystemDirectoryHandle,
}

#[wasm_bindgen]
impl WasmStorageEngine {
    /// 1. Initialize the engine: ask the browser for the OPFS root directory handle
    #[wasm_bindgen(constructor)]
    pub async fn new() -> Result<WasmStorageEngine, JsValue> {
        let window = web_sys::window().ok_or("no window object")?;
        let storage: StorageManager = window.navigator().storage();

        // Asynchronously obtain the Origin Private File System root
        let root_dir_jsval = JsFuture::from(storage.get_directory()).await?;
        let root_dir: FileSystemDirectoryHandle = root_dir_jsval.into();

        Ok(WasmStorageEngine { root_dir })
    }

    /// 2. High-performance persistent write: binary data in Wasm memory straight into OPFS
    pub async fn save_file(&self, filename: &str, data: &[u8]) -> Result<(), JsValue> {
        // Create or open the file
        let mut options = web_sys::FileSystemGetFileOptions::new();
        options.create(true);
        let fh_jsval = JsFuture::from(
            self.root_dir.get_file_handle_with_options(filename, &options)
        ).await?;
        let file_handle: web_sys::FileSystemFileHandle = fh_jsval.into();

        // Open OPFS's dedicated high-performance write stream
        let writable_jsval = JsFuture::from(file_handle.create_writable()).await?;
        let writable: FileSystemWritableFileStream = writable_jsval.into();

        // ★ Zero-copy optimization: map Rust's &[u8] slice directly as a JS Uint8Array view.
        //   This step is pure pointer arithmetic inside linear memory, at zero cost.
        //
        //   ⚠️ SAFETY: this view is invalidated by the next memory.grow.
        //   You must ensure no allocation happens while the view is alive.
        let js_buffer = unsafe { js_sys::Uint8Array::view(data) };

        JsFuture::from(writable.write_with_buffer_source(&js_buffer)?).await?;

        // Close the stream, forcing the cache to physical disk
        JsFuture::from(writable.close()).await?;
        Ok(())
    }

    /// 3. Read: pull the OPFS file's contents back into Wasm linear memory
    pub async fn load_file(&self, filename: &str) -> Result<Vec<u8>, JsValue> {
        let fh_jsval = JsFuture::from(
            self.root_dir.get_file_handle(filename)
        ).await?;
        let file_handle: web_sys::FileSystemFileHandle = fh_jsval.into();

        let file_jsval = JsFuture::from(file_handle.get_file()).await?;
        let file: web_sys::File = file_jsval.into();

        let buf_jsval = JsFuture::from(file.array_buffer()).await?;
        let array = js_sys::Uint8Array::new(&buf_jsval);
        Ok(array.to_vec())      // this copy is unavoidable (JS heap → Wasm linear memory)
    }
}
```

### 2. `Cargo.toml`

```toml
[package]
name = "wasm_opfs_engine"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
wasm-bindgen = "0.2"
wasm-bindgen-futures = "0.4"
js-sys = "0.3"

[dependencies.web-sys]
version = "0.3"
features = [
  "Window",
  "Navigator",
  "StorageManager",
  "FileSystemDirectoryHandle",
  "FileSystemFileHandle",
  "FileSystemGetFileOptions",
  "FileSystemWritableFileStream",
  "File",
]

# ★ Always enable these for release builds (see Chapter 9)
[profile.release]
opt-level = 3
lto = true
codegen-units = 1
panic = "abort"
strip = true
```

Build:

```bash
wasm-pack build --target web
```

### 3. Front-end integration (`index.html`)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Wasm OPFS Storage Engine</title>
</head>
<body>
  <h1>WebAssembly OPFS high-performance storage demo</h1>
  <button id="saveBtn" disabled>Write Wasm big data to disk</button>
  <button id="loadBtn" disabled>Read back and verify</button>
  <p id="status">Status: waiting for initialization…</p>

  <script type="module">
    import init, { WasmStorageEngine } from './pkg/wasm_opfs_engine.js';

    const status = document.getElementById('status');

    async function run() {
      await init();
      status.textContent = 'Status: Wasm engine initialized';

      const engine = await new WasmStorageEngine();
      document.getElementById('saveBtn').disabled = false;
      document.getElementById('loadBtn').disabled = false;

      document.getElementById('saveBtn').addEventListener('click', async () => {
        status.textContent = 'Status: computing and writing big data…';

        const dataSize = 10 * 1024 * 1024;           // 10 MB
        const mockBigData = new Uint8Array(dataSize);
        for (let i = 0; i < dataSize; i++) mockBigData[i] = i % 256;

        try {
          const t0 = performance.now();
          await engine.save_file('firmware_backup.bin', mockBigData);
          const t1 = performance.now();
          status.textContent =
            `Status: wrote 10 MB in ${(t1 - t0).toFixed(2)} ms (survives a reload)`;
        } catch (err) {
          status.textContent = `Error: ${err}`;
        }
      });

      document.getElementById('loadBtn').addEventListener('click', async () => {
        const t0 = performance.now();
        const back = await engine.load_file('firmware_backup.bin');
        const t1 = performance.now();
        status.textContent =
          `Status: read back ${(back.length / 1024 / 1024).toFixed(1)} MB in ` +
          `${(t1 - t0).toFixed(2)} ms, first byte = ${back[0]}`;
      });
    }
    run();
  </script>
</body>
</html>
```

**How to verify**: reload the page and click "Read back" — the data is still there. You can also inspect the OPFS contents in DevTools under **Application → Storage → File System**.

---

## 2. Approach B: A synchronous access handle (inside a Worker, the performance ceiling)

**This is the industry's answer for very large files (>50 MB) and databases** (see Chapter 7 Scenario 3).

### `worker.js`

```javascript
import init, { ChunkedEngine } from './pkg/wasm_opfs_engine.js';

let engine;

self.onmessage = async (e) => {
  const { cmd, payload } = e.data;

  if (cmd === 'init') {
    await init();
    engine = new ChunkedEngine();
    // ★ createSyncAccessHandle can only be called inside a Worker
    const root = await navigator.storage.getDirectory();
    const fh = await root.getFileHandle('bigdata.bin', { create: true });
    const handle = await fh.createSyncAccessHandle();
    engine.attach(handle);              // hand the handle over to the Wasm side
    self.postMessage({ ok: true });
    return;
  }

  if (cmd === 'process') {
    // the large buffer arrived as a transferable — zero copy
    const result = engine.process_chunk(payload);
    // send it back as a transferable too
    self.postMessage({ result }, [result.buffer]);
  }
};
```

### The main thread

```javascript
const worker = new Worker('./worker.js', { type: 'module' });

worker.postMessage({ cmd: 'init' });

// ★ the second argument declares transferables: ownership transfer, not a copy (microseconds)
const buf = new ArrayBuffer(50 * 1024 * 1024);
worker.postMessage({ cmd: 'process', payload: buf }, [buf]);
// ⚠️ after transfer, buf.byteLength on the main-thread side immediately becomes 0
```

### The sync access handle's core operations

```javascript
const handle = await fh.createSyncAccessHandle();

handle.write(buffer, { at: offset });   // synchronous write, no Promise
handle.read(buffer,  { at: offset });   // synchronous random read, like pread
handle.getSize();                       // file size
handle.truncate(newSize);               // truncate
handle.flush();                         // force to disk
handle.close();                         // ★ always close, or the lock is never released
```

---

## 3. Sliding-window chunked reading (getting around the 4 GB ceiling)

```rust
/// Conceptual skeleton: only 50 MB of memory, yet it handles a 100 GB file
const CHUNK: u64 = 4 * 1024 * 1024;              // 4 MB alignment
const WINDOW: usize = 50 * 1024 * 1024;          // a resident 50 MB window

pub struct ChunkedReader {
    handle: SyncHandle,          // the OPFS sync access handle (or an HTTP Range wrapper)
    window: Vec<u8>,
    window_start: u64,
    window_len: usize,
    file_size: u64,
}

impl ChunkedReader {
    /// Read at an arbitrary position; disk I/O happens only when we leave the window
    pub fn read_at(&mut self, offset: u64, len: usize) -> &[u8] {
        let end = offset + len as u64;
        let in_window = offset >= self.window_start
            && end <= self.window_start + self.window_len as u64;

        if !in_window {
            // Align to a block boundary, so reading one byte doesn't reload the whole window
            self.window_start = (offset / CHUNK) * CHUNK;
            let want = WINDOW.min((self.file_size - self.window_start) as usize);
            self.window.resize(want, 0);
            self.window_len = self.handle.read_at(&mut self.window, self.window_start);
        }

        let local = (offset - self.window_start) as usize;
        &self.window[local .. local + len]
    }
}
```

**Four implementation points**:

1. **Align the window** to a 1 MB/4 MB boundary.
2. **Tune to the access pattern**: sequential scan → a large window plus readahead; random jumps → small windows plus an LRU of several.
3. **It must run in a Worker** (a specification restriction on `createSyncAccessHandle`).
4. **Remote files use the same logic** — swap `handle.read_at()` for `fetch(url, { headers: { Range: 'bytes=A-B' } })`.

---

## 4. Choosing among the three storage mechanisms, and their implementations

| Scenario | Mechanism | Key API |
|---|---|---|
| Large files / databases (>50 MB) | **OPFS + a Worker sync access handle** | `createSyncAccessHandle()` |
| Game saves / small JSON (broad compatibility) | **IndexedDB / IDBFS** | `FS.mount(IDBFS)` + `FS.syncfs()` |
| Backend cloud-native | **The WASI filesystem** | `std::fs` plus pre-opened directory capabilities |

### IDBFS (Emscripten)

```javascript
// The C side still calls fopen("/save/game.sav", "wb") as usual
Module.onRuntimeInitialized = () => {
  FS.mkdir('/save');
  FS.mount(IDBFS, {}, '/save');
  FS.syncfs(true, err => {        // true = load from IndexedDB into MEMFS
    if (err) throw err;
    startGame();
  });
};

function saveGame() {
  FS.syncfs(false, err => {       // false = write MEMFS back to IndexedDB
    if (err) console.error(err);
  });
}
```

### WASI (server side)

```rust
// target: wasm32-wasip1
use std::fs::File;
use std::io::{Read, Write};

fn main() -> std::io::Result<()> {
    // Only directories the host pre-opened and granted are reachable
    let mut f = File::create("/sandbox/output.bin")?;
    f.write_all(b"hello from wasm")?;

    let mut buf = String::new();
    File::open("/sandbox/input.txt")?.read_to_string(&mut buf)?;
    println!("{}", buf);
    Ok(())
}
```

```bash
# On the host: this one line is the entire capability list
wasmtime run --dir=./data::/sandbox app.wasm
```

---

## 5. Architectural advantages and defending the blind spots

| Aspect | Approach | Why |
|---|---|---|
| **Zero copy** | `js_sys::Uint8Array::view(data)` | Avoids the doubled memory cost of "Rust linear memory → JS heap" |
| ⚠️ **View invalidation** | **No** allocation may occur while the view is alive | `memory.grow` detaches the `ArrayBuffer`, leaving the view pointing at invalid space |
| **Avoiding a frozen main thread** | Put the storage engine inside a Web Worker | Synchronous I/O on the main thread would freeze the UI (which is why the specification forbids it outright) |
| **Maximum I/O performance** | Use `createSyncAccessHandle()` inside the Worker | Removes async poll overhead, reaching near-native sequential write throughput |
| **Quota eviction** | `await navigator.storage.persist()` | Data not marked persistent may be cleared under disk pressure |
| **Multiple tabs fighting for the lock** | Coordinate with the Web Locks API or `BroadcastChannel` | One file may have only one sync access handle at a time |
| **The user cannot back up** | Provide an "export file" feature yourself | OPFS is invisible to the user |

---

## 6. A measurement template

```javascript
// Write throughput
const t0 = performance.now();
await engine.save_file('bench.bin', data);
const t1 = performance.now();
const mbps = (data.length / 1024 / 1024) / ((t1 - t0) / 1000);
console.log(`Write throughput: ${mbps.toFixed(1)} MB/s`);

// Memory footprint (Chrome)
if (performance.measureUserAgentSpecificMemory) {
  const m = await performance.measureUserAgentSpecificMemory();
  console.log('Tab memory:', (m.bytes / 1024 / 1024).toFixed(1), 'MB');
}

// Quota
const est = await navigator.storage.estimate();
console.log(`Used ${(est.usage/1e6).toFixed(1)} MB / quota ${(est.quota/1e6).toFixed(1)} MB`);
```

---



# Appendix H: Specification Templates for AI Coding Agents

> When using an AI tool like Claude Code — embedded directly in the terminal and capable of autonomous project refactoring — the core technique is **giving clear system architecture boundaries, explicit dependency conditions, and a demand for defensive design**.
> Because that kind of agent can read and write your files, run tests and compile, your prompt must read like a **high-level system architecture specification**, not a wish.
>
> This appendix provides three templates you can copy and use directly: **(1) a general storage mechanism specification, (2) tuning directives for each of the three storage mechanisms, and (3) a complete initialization directive for the endgame four-layer architecture.**

---

## 1. General specification: a Wasm data storage mechanism

> Copy the structured prompt below and replace the options inside `[brackets]`.

```markdown
I want you to implement a high-performance, non-volatile data storage mechanism
for our Rust WebAssembly application using [pick one: OPFS / IndexedDB (IDBFS) / WASI File System].

Please follow these specifications strictly:

### 1. Architecture & Scope
- **Domain**: WebAssembly Client-Side Storage Engine.
- **Language Stack**: Rust, `wasm-bindgen`, `web-sys`, and `js-sys`.
- **Target Mode**: Browser context (`--target web`), [single-threaded / multi-threaded].
- **Core Requirement**: Map our internal Rust binary structure/buffer into
  persistent host storage with ZERO-COPY memory optimization.

### 2. Implementation Checklist
1. **Dependency Injection**
   - Check and update `Cargo.toml`. Add the necessary `web-sys` feature flags
     (e.g. `FileSystemDirectoryHandle`, `FileSystemFileHandle`,
     `FileSystemWritableFileStream`, `StorageManager`) depending on the chosen engine.
   - Set the release profile: `opt-level = 3`, `lto = true`, `codegen-units = 1`,
     `panic = "abort"`, `strip = true`.

2. **Rust Core Layer (`src/storage.rs`)**
   - Implement a struct named `WasmStorageEngine`.
   - Implement `async fn save_data(&self, key: &str, data: &[u8]) -> Result<(), JsValue>`.
   - Implement `async fn load_data(&self, key: &str) -> Result<Vec<u8>, JsValue>`.
   - Use `unsafe { js_sys::Uint8Array::view(data) }` or a `WritableStream` to prevent
     double-buffering and achieve zero-copy during transfer.
   - **Document the SAFETY invariant**: the view is invalidated by any `memory.grow`;
     no allocation may occur while the view is alive.

3. **Memory Safety & Defenses**
   - Handle JavaScript exceptions (`JsValue`) gracefully using Rust's `Result` type.
     Never `unwrap()` on a `JsValue` boundary.
   - Implement a safe allocation fallback check to prevent out-of-bounds crashes
     if the incoming byte buffer size approaches the browser's per-instance
     memory allocation limit.
   - Explicitly handle quota errors (`QuotaExceededError`) and surface them as a
     typed Rust error, not a generic failure.

4. **JS Glue Integration & Demo**
   - Create or update `index.html` demonstrating initialization, saving, and
     cross-session loading of this storage engine.
   - Measure and display the raw disk write latency using `performance.now()`.
   - Use RELATIVE paths only (`./pkg/...`), because this will be deployed to
     GitHub Pages under a project subpath.

### 3. Execution Constraints
- DO NOT use any heavy third-party JavaScript npm packages; rely completely on native Web APIs.
- Write unit tests or a mock integration script if applicable, and run
  `wasm-pack build --target web` to verify the compilation succeeds with zero warnings.
- Keep the code modular. Separate storage logic from UI rendering logic.
- Add a `.nojekyll` file to the output directory.

Review the workspace files first, tell me which files you plan to modify,
then build the project and report the benchmarks.
```

---

## 2. Tuning directives for each of the three storage mechanisms

**Append** the matching section below to the prompt above.

### (1) OPFS + Web Worker — maximum performance, for large files/databases over 50 MB

```markdown
Since we are targeting heavy multi-threaded datasets, force the WasmStorageEngine
to run inside a Web Worker context and utilize the synchronous
`createSyncAccessHandle` / `FileSystemSyncAccessHandle` APIs instead of the
asynchronous writable stream. This eliminates the async poll loop overhead and
ensures raw native-speed sequential and random disk performance.

Additionally:
- Implement a sliding-window chunked reader so we never load the whole file into
  linear memory. Align window boundaries to 4MB.
- Use Transferable Objects (`postMessage(buffer, [buffer])`) for all large payloads
  crossing the main-thread/worker boundary.
- Always call `handle.close()` in a Drop impl or an explicit teardown path;
  a leaked sync access handle holds an exclusive lock on the file.
- Coordinate multi-tab access using the Web Locks API.
```

### (2) IndexedDB / IDBFS — broad compatibility, for game saves and small JSON

```markdown
Implement the solution using the Emscripten IDBFS / IndexedDB bridge.
The Rust layer must interact with an in-memory virtual file system (MEMFS).
After performing standard file mutations, automatically inject a JS wrapper that
executes `FS.syncfs(false, callback)` to flush the binary blocks into the browser's
IndexedDB store, ensuring cross-session persistence.

Be explicit about the cost model in comments:
- `syncfs` serializes the ENTIRE mount point, not a delta.
- Therefore this design is only appropriate for payloads under a few megabytes.
- Document the load path (`FS.syncfs(true, ...)` on startup) as well.
```

### (3) Server-side WASI — cloud-native

```markdown
We are deploying this on a server-side WebAssembly runtime (Wasmtime / WasmEdge)
instead of a browser. Change the target triple to `wasm32-wasip1`
(and note what would change for `wasm32-wasip2` / the Component Model).

Utilize the native Rust `std::fs::File` and standard library I/O.
Implement a capability-based security boundary check to verify that any path
resolution does not escape the pre-opened directory map provided by the WASI host.

Also produce the exact host invocation line, e.g.:
    wasmtime run --dir=./data::/sandbox app.wasm
and document which capabilities the module requires — this list IS the security
audit surface.
```

---

## 3. Endgame architecture initialization directive (Chapter 12's four-layer topology)

> Use this to **build from scratch** the skeleton of a "maintenance-free, zero-server-cost, maximum-performance" bespoke Wasm application.

```markdown
Initialize a next-generation, high-performance, single-page application workspace
based on a hybrid Wasm architecture. Your goal is to build an un-clonable,
low-maintenance file-processing engine.

Please execute the following technical plan autonomously:

1. **Workspace Setup**
   - Initialize a Rust library workspace. Configure `Cargo.toml` with
     `crate-type = ["cdylib"]`.
   - Turn on the maximum aggressive release profile: `opt-level = 3`, `lto = true`,
     `codegen-units = 1`, `panic = "abort"`, `strip = true` — strip all debug symbols
     and let LTO scramble the code structure.
   - Inject dependencies for `wasm-bindgen`, `js-sys`, and `web-sys` with features
     enabled for `FileSystemDirectoryHandle`, `FileSystemSyncAccessHandle`, and `Crypto`.

2. **Core Implementation (`src/lib.rs`)**
   - Create a struct named `CoreComputeEngine`.
   - Implement an automated sliding-window memory management pattern: read data
     chunks from host disk, perform high-speed binary manipulation inside Wasm
     linear memory WITHOUT generating intermediate high-level JS garbage objects,
     and flush state back.
   - Ensure all inter-op boundary parameters use zero-copy
     `js_sys::Uint8Array::view` mechanisms, and document the SAFETY invariants.
   - ARCHITECTURAL RULE: this layer must NOT depend on any JavaScript framework.
     Only standard binary Web APIs (Canvas 2D / WebGL, OPFS) are allowed.
     This layer is designed to remain unchanged for a decade.

3. **Web Worker Thread Isolation**
   - Generate a dedicated `worker.js` to host the compiled `.wasm`.
   - Use the synchronous OPFS API (`createSyncAccessHandle`) inside the worker to
     enable block-based sequential and random file read/writes.
   - Set up the main-thread message bus using Transferable Objects
     (`postMessage(buffer, [buffer])`) for microsecond-level pointer transfer.

4. **Data Protocol**
   - Do NOT use JSON across the Wasm boundary. Define all cross-boundary messages
     with a schema (Protocol Buffers or FlatBuffers). Generate the schema file first,
     then the bindings.
   - Rationale: the schema is the ONE thing that must stay stable while everything
     around it is rewritten.

5. **Verification & Benchmark**
   - Create an `index.html` with a benchmark dashboard measuring raw
     memory-to-disk write throughput using `performance.now()`.
   - Use relative paths only; add `.nojekyll`; the target is GitHub Pages.
   - Execute `wasm-pack build --target web` and ensure compilation succeeds
     with zero warnings.
   - Run `wasm-opt -Oz --strip-debug` on the output and report the size delta.
   - Run `strings pkg/*.wasm | grep -Ei 'sk-|AKIA|password|secret'` and confirm
     the output is EMPTY.

Analyze the current system state, draft the modules, compile the binary,
and report the micro-benchmark results.
```

---

## 4. The working rhythm of collaborating with an AI agent

**Step one: analysis and planning**
The agent will first reply with which files it intends to modify (`Cargo.toml`, `src/lib.rs` and so on). **Do not let it start writing code blindly at this point — look carefully at its architecture.** If its layering differs from what you expected, changing it now is the cheapest it will ever be.

**Step two: authorize compilation and building**
Once the code is written, the agent will usually ask whether it may run `wasm-pack build --target web` to verify. **Say yes.**

> **From experience**: Wasm's cross-boundary (JS-bind) compilation very easily emits enormously long errors because a `web-sys` feature wasn't enabled. Let the agent compile in the terminal itself and it will repair its way to a clean build from the compiler log — **which saves an enormous amount of documentation searching.**

**Step three: ask it to review the key metric**
After a successful build, add one line:

```
Confirm that you used the zero-copy `view` method instead of copying into a new
Uint8Array. Show me the file and line number, and explain the SAFETY invariant
you are relying on.
```

**That ensures it didn't take the lazy copying route**, and forces out Wasm's purest read/write performance.

**Step four: the security red line check (not optional)**

```
Run: strings pkg/*.wasm | grep -Ei 'sk-|AKIA|BEGIN.*PRIVATE|password|secret|token'
Report the exact output. If anything matches, stop and tell me where it came from.
```

---

## 5. Writing specifications for AI agents: five general rules

> These five have nothing to do with Wasm; they apply to every task you hand a coding agent.

1. **Give the boundaries before the task.** "No npm packages at all," "standard Web APIs only," "this layer must contain no algorithm" — **constraints determine output quality more than goals do**, because the model can always find a shortcut you didn't want.

2. **Make it state the plan before it acts.** If the architecture is wrong, writing fast only accumulates debt. **This step costs one exchange and returns the whole project's direction.**

3. **Give it a loop it can verify itself.** "Run the build," "run the tests," "run the benchmark and report the numbers" — **an agent that can verify itself produces far higher quality than one that can only write code.**

4. **Use the schema as your constraint tool.** When you ask it to modify one side, **the schema is the one place it cannot improvise** (Chapter 12). It is the most effective means of controlling drift in AI output.

5. **Tell it explicitly which parts are permanent and which are disposable.** Say "this layer is designed to be unchanged for a decade" and "this layer may be rewritten every three years" — **the agent will adjust its abstraction level and dependency choices accordingly**, and that is exactly what fights maintenance entropy (Chapter 12).

---



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

---



# Appendix J: The Front/Back Boundary Decision Table and Moat Checklist

> This is the operational version of Chapters 9–12. **When you face a concrete feature and don't know which side it belongs on, follow this.**

---

## 1. The Three-Question Decision Flow

```
For each functional module, ask three questions in order:

┌────────────────────────────────────────────────────────────────────┐
│ Question 1: if this logic were published verbatim on a blog,       │
│             would my business suffer?                               │
└────────────────────────────────────────────────────────────────────┘
        │
        ├─ No ──→ 【Put it in front-end Wasm】saves money and bandwidth,
        │          improves privacy, unlimited concurrency
        │
        └─ Yes ──→ go to question 2
                  │
┌────────────────────────────────────────────────────────────────────┐
│ Question 2: is the computation it needs worth running a server for? │
└────────────────────────────────────────────────────────────────────┘
        │
        ├─ Yes ──→ 【A standard backend service】
        │
        └─ No ──→ go to question 3
                      │
┌────────────────────────────────────────────────────────────────────┐
│ Question 3: can it be split into "compute on the front, verify      │
│             on the back"?                                            │
│ (Verification is usually orders of magnitude cheaper than           │
│  computation: sorting is expensive, checking sortedness is cheap)    │
└────────────────────────────────────────────────────────────────────┘
        │
        ├─ Yes ──→ 【Hybrid: Wasm computes + a light backend verifies】★ optimal
        │
        └─ No ──→ 【It must go on the backend】and accept its cost
```

---

## 2. Classification Table

### ✅ Put it in front-end Wasm (compute-heavy, public algorithm, no secrets)

| Category | Examples |
|---|---|
| Media processing | Transcoding, filtering, background removal, thumbnails, format conversion, waveform analysis |
| Geometry and rendering | 3D matrices, boolean operations, tessellation, path planning, physics simulation |
| Data processing | Local SQL queries, aggregation, sorting, full-text search, compression and decompression |
| Parsing and transpilation | Syntax parsing, ASTs, code transpilation, format conversion, Markdown |
| Standard algorithms | FFT, convolution, finite elements, Monte Carlo, Newton's method, A* |
| Cryptographic computation | Encryption/decryption, signing, hashing, ZKP proof generation (**the algorithm is public and the key never enters the binary**) |
| Edge AI inference | Image classification, OCR, object detection, lightweight LLMs |

### ❌ Must go on the backend (leaking it is a disaster, or it needs a single authority)

| Category | Why |
|---|---|
| **Keys, passwords, signing private keys** | `strings` finds them in a second (Chapter 9's forbidden zone one) |
| **Authentication and authorization decisions** | The client is untrusted; any self-attestation can be patched locally |
| **Charging, quotas, metering** | Money is involved, so there must be a single source of truth |
| **Audit logs** | They must be tamper-proof |
| **Conflict resolution in multi-user collaboration** | It needs authoritative arbitration and a single state (Figma's CRDT engine) |
| **Data ownership and access control** | Permission revocation must take effect on the server |
| **Core trade secret algorithms** | The test: if my opponent had it tomorrow, what would I have left? |
| **Processing that compliance requires to stay in a jurisdiction** | Auditors ask where the data lives and who can reach it |

### ⚖️ Splittable into "compute on the front, verify on the back" (the most valuable category)

| Scenario | Front end does | Backend does |
|---|---|---|
| File upload | Local compression, chunking, hashing | Verify the hash, check quota and permissions |
| Forms | Live validation, formatting | **Validate again** (front-end validation is UX, not security) |
| Large file processing | Full processing, sending only a result summary | Verify the summary is plausible |
| ZKP | Generate the proof (expensive) | Verify the proof (orders of magnitude cheaper) |
| Image processing | Filters, cropping, compression | Verify output format and size |
| Scheduling / optimization | Solve (NP-hard, expensive) | Verify the solution is feasible (cheap) |
| Search | Local index retrieval | Step in only when cross-user data is needed |

---

## 3. Interface Design Principles for the Hybrid Architecture

```
┌──────────── Client (fully downloadable) ───────────────┐
│  The Wasm compute core                                  │
│  · Depends only on standard Web APIs (Canvas/WebGL/OPFS)│
│  · Contains no key and no plaintext secret              │
│  · Compiled with strip/lto                              │
└───────────────────┬─────────────────────────────────────┘
                    │ ★ Four design principles for this line:
                    │
                    │ 1. Keep it narrow: send a summary rather than everything
                    │ 2. Keep it coarse: one request for a batch of results,
                    │    not fine-grained round trips
                    │ 3. Give it a schema: Protobuf/FlatBuffers, not raw JSON
                    │ 4. Assume the other side is hostile: treat every input
                    │    as malicious
                    │
┌───────────────────┴─────────────────────────────────────┐
│  The backend API (entirely under your control)          │
│  · Short-lived, narrowly scoped tokens                  │
│    (never issue a long-lived key)                        │
│  · Every authorization decision lives here, trusting     │
│    no client claim                                       │
│  · It can be extremely light (Lambda / Workers suffice)  │
└─────────────────────────────────────────────────────────┘
```

**Four antipatterns** (be alarmed when you see them):

| Antipattern | Why it's wrong |
|---|---|
| The front end computes a "do I have permission" boolean and sends it to the backend | The client can simply change it to `true` |
| The backend trusts a price / discount / quantity sent by the front end | Same as above |
| Using a front-end Wasm hash for an integrity check | Client-side self-verification can always be bypassed |
| Setting a "short-lived token" to last six months | That is a long-lived key |

---

## 4. Moat Self-Assessment

> Score your product row by row (0 = none at all, 3 = extremely strong).

| # | Moat type | The test question | Time constant | Score |
|---|---|---|---|---|
| 1 | **Technical lead** | How long would the open-source community need to build an equivalent? | **1–3 years** | ☐ |
| 2 | **Data gravity** | How much would a user lose from their accumulated data by switching platforms? | 5–15 years | ☐ |
| 3 | **Workflow lock-in** | To replace me, how many people would the customer retrain and how many processes rewrite? | 5–15 years | ☐ |
| 4 | **Network effects** | Does the product get more valuable to each user as more users join? | 5–15 years | ☐ |
| 5 | **Ecosystem** | How many third parties have made sunk, dedicated investments in me? | 5–15 years | ☐ |
| 6 | **Physical resources** | What do I hold that software cannot conjure (compute, bandwidth, capacity, contracts)? | Long | ☐ |
| 7 | **Compliance and accountability** | Can I sign an SLA and compensate when things break? Can my competitor? | **10+ years** | ☐ |
| 8 | **Standard protocol** | Must others import into my format to interoperate? | Long | ☐ |
| 9 | **AI agent ecosystem** | When AI agents execute tasks, do they connect to my API by default? | Emerging | ☐ |

**How to read it**:

- **Only item 1 scores high** → **danger**. You will be caught within three years, and you may not have built anything else yet. **The correct action: use the technical lead to buy time, and build items 2–5.**
- **Items 2–5 score high** → solid. This is where most successful SaaS sits.
- **Items 6–8 score high** → extremely solid, **and not eroded by AI**.
- **Item 9** → a new axis of competition, only taking shape in 2026.

---

## 5. The Buyer's Mirror Checklist (the same table, read backwards)

> It is entirely natural for a vendor to build lock-in, and entirely natural for a customer to assess it. **This is not a moral question; it is a symmetric commercial judgement.**

```
□ Can I export my data in full? Is the export format open or proprietary?
□ After exporting, is there a second place that can import it? (Have I actually tried?)
□ Can the "peripheral data" — version history, comments, permission settings — come along?
□ How many proprietary APIs are my automated workflows welded to?
□ If this company tripled its price tomorrow, what is my worst case?
□ If this company folded tomorrow, would my data still exist?
□ Have I ever rehearsed "export and restore elsewhere"?
□ Of what I pay, how much buys features and how much buys "someone pays when it breaks"?
```

**The last one matters most**: if what you pay for is **mostly features**, then in the AI era you have a chance of building it yourself; if it is **mostly outsourced liability**, building it yourself just moves the risk back onto you (Chapter 12's time trap).

---

## 6. The Three-Year Self-Check

> Chapter 12's core questions, worth listing separately and putting on the agenda of every architecture review.

```
□ When this breaks at midnight three years from now, who fixes it? Are they still at the company?
□ Has a second person ever understood this code's underlying architecture?
□ Which of the standard APIs I depend on are still changing in the standards committee?
□ If a browser behaviour I depend on is tightened tomorrow (OPFS quota,
   cross-origin isolation rules, the semantics of some Wasm proposal),
   what is my fallback path?
□ Have I separated my "consumable layer" from my "asset layer"?
   Will the rot stay confined to the layer I am willing to discard?
□ Is my schema stable? Is it the most effective tool I have for constraining every future change?
```

**If the first question has no clear answer, what you built is not a wheel; it is debt.**

---



# Appendix K: Controversies and Authenticity Calibration Q&A

> This book spans verifiable specification facts and unverified community claims. This appendix collects every "⚠️ Authenticity Caveat" in the book, plus several common controversies that never appeared in the main text.
> **Format**: the question → the popular claim → the calibrated answer → which chapter it comes from.

---

## 1. On History and Positioning

### Q1. Is WebAssembly meant to replace JavaScript?

**Popular claim**: "The W3C's anointed fourth language, destined to replace JavaScript."

**Calibration**: **No.** The specification documents have never positioned Wasm as a replacement for JS but explicitly as a **complement**. Technically, Wasm still cannot touch the DOM independently or load itself — **every start-up requires JavaScript (or the host environment) to hand it the first key.** The correct division of labour is "Wasm computes, JS draws."

The part about "the W3C making it a Recommendation in 2019, standing alongside HTML/CSS/JS as the fourth core language" **is true**; what got embellished is the word "replace." → Chapters 1, 4

### Q2. "If WASI existed in 2008, we wouldn't have needed to create Docker" — so are containers dying?

**Calibration**: The line **does exist** (Docker founder Solomon Hykes, 2019), but it is routinely quoted out of context. The next sentence of the original tweet was "Wasm is the future of server-side computing," not a declaration that containers were obsolete; the author later clarified it was praise for the combination of lightweight, portable and cross-platform.

**Reality**: the two are **complementary**. A container isolates an entire OS userspace and **can run any existing binary**; Wasm isolates only a single application, buying an order-of-magnitude advantage in cold start and size, but **can only run things that were recompiled**. The most common deployment shape in practice is **Wasm modules running inside a containerized runtime**. → Chapters 1, 4

### Q3. Did NaCl fail because the technology wasn't good enough?

**Calibration**: **No.** NaCl was a technical success (statically validated x86 machine code plus a segmented sandbox really was safe and fast). It failed **politically**: only Chrome supported it, it was "a native program parasitic inside a web page" rather than part of the page, and it required other vendors to write a machine code validator for every CPU architecture (an extremely expensive commitment in security engineering). → Chapter 1

---

## 2. On Performance

### Q4. Is "Wasm has 60–80% of native performance" correct?

**Calibration**: **The sentence carries almost no information**, because it depends heavily on the workload's shape:

| Workload | Relative to native | Reason |
|---|---|---|
| A pure numeric loop with data in cache | **90%+** | TurboFan's codegen approaches Clang -O2 |
| Hand-written AVX2-optimized code ported over | **40–50%** | **Wasm SIMD is only 128 bits, halving the vector width outright** |
| Many fine-grained boundary calls | **Possibly slower than pure JS** | Fixed boundary overhead dominates |
| Heavy string and object manipulation | Pure JS crushes it | Wasm pays the encoding tax |
| Memory-bound (cache misses dominate) | Close to 100% | Both sides are waiting on DRAM |

**When reading any performance claim, the first question is always: does this benchmark's shape resemble what I'm going to run?** → Chapter 2

### Q5. "Wasm is 10–30× faster than JavaScript"?

**Calibration**: True only on particular benchmarks (a dense numeric loop with no GC pressure, against an unoptimized JS control). **In a fully warmed-up, monomorphic, type-stable hot loop, JavaScript can approach Wasm and the gap is often within 1–2×.**

But there is one thing Wasm wins reliably, and it is worth more than average performance — **performance predictability**. JS occasionally stalls for 30 milliseconds from GC or deoptimization; Wasm's curve is flat. **In audio (a 2.9-millisecond hard deadline) and game loops (a 16.6-millisecond budget) that is decisive.** → Chapter 4

### Q6. "Wasm is 100× faster than Docker"?

**Calibration**: **Credible for cold start** (microseconds versus tens of milliseconds to seconds). **Wrong for steady-state execution performance** — a container runs a genuinely native binary, while Wasm is a compiled intermediate representation, so **its execution performance is below native code inside a container**. → Chapter 4

### Q7. Are the "N× faster" numbers in Appendices D–F credible?

**Calibration**: **Trust the direction, doubt the multiplier.** They are all claims from the original conversation and have not been independently verified for this book. The direction (Wasm beating pure JS on dense computation) is credible; the specific multipliers (15×, 40×, 55×) should be read as order-of-magnitude hints, not measurements. → the introductions to Appendices D, E and F

---

## 3. On Security

### Q8. "Wasm is memory-safe" — so is my C program safe inside it?

**Calibration**: **This is the book's most important clarification.** "Wasm is memory-safe" holds only in the sense of the **sandbox boundary** — it guarantees that a Wasm module cannot harm the host, and **guarantees nothing about your C program having no memory errors inside it**.

And the situation is subtler: because linear memory is one flat `ArrayBuffer`, **the mitigations of traditional native platforms (ASLR, NX, stack canaries) mostly do not exist in Wasm**. A buffer overflow that ASLR would block on x86 may be reliably exploitable in Wasm — with the damage merely confined to that module's linear memory. Academia has discussed this explicitly ("Everything Old is New Again: Binary Security of WebAssembly", USENIX Security 2020).

**Sandbox security ≠ application security.** The practical countermeasure: build test versions with `-fsanitize=address` / `-fsanitize=undefined`. → Chapters 2, 3

### Q9. "Wasm is an irreversible binary translation"?

**Calibration**: **Wrong.** Wasm's binary format is **entirely public and structured**, and disassembling back to WAT is lossless, mechanical and served by off-the-shelf tools (`wasm2wat`, `wasm-objdump -d`, `wasm-decompile`, Ghidra's Wasm loader) — which is **far easier** than reverse engineering x86 machine code (x86 also has variable-length instructions, code mixed with data and indirect jump tables; Wasm has none of it).

The accurate statement is: **Wasm hides the source's semantic layer (types, naming, abstraction), not the program's behavioural layer. Obfuscation raises the cost, not the possibility.**

**And one point that gets overlooked constantly**: the Export section is **mandated by the specification** and can never be stripped — an attacker will always see which functions you export and what their signatures are. → Chapter 9

### Q10. Can encryption / encoding / splitting protect a hardcoded key?

**Calibration**: **None of it works.**

| Technique | Why it fails |
|---|---|
| Base64 encoding | `strings` won't catch it, but `base64 -d` recovers it in a second, and the decode function is right beside it |
| Splitting into pieces and concatenating | The concatenation code is in the binary; run it dynamically once and it hands the key over |
| XOR encryption | The key to the key is in the binary too (the fundamental dilemma of white-box cryptography) |
| "Nobody will reverse engineer my small project" | Automated scanners crawl public hosting daily and don't discriminate |

**The only correct answer: the key never enters the client.** The front end asks its own backend for a short-lived, narrowly scoped token. **Wasm does not make an architecture that was already wrong become right.** → Chapter 9

### Q11. "It uses Wasm, so it is constant-time and side-channel resistant"?

**Calibration**: **Wrong.** The Wasm specification itself **does not guarantee** constant time. What it guarantees is the absence of JS-engine-style dynamic switching of internal representation by data type (V8's Smi → HeapNumber), but **the compiler may still introduce branches and the CPU may still exhibit data-dependent cache behaviour**.

Constant time is guaranteed by **how the source is written** (avoid branching on the private key, avoid indexing a lookup table by it); Wasm merely provides an execution substrate more controllable than JS. → Appendix F case 73

### Q12. Static hosting + Git signing = high security?

**Calibration**: The direction is right, with three caveats:

1. **Account security is the real boundary** — an attacker who obtains your GitHub account or a PAT can push commits just the same. Enable two-factor authentication and branch protection.
2. **Supply chain risk remains** — if the build pipeline pulls in a poisoned package, the resulting `.wasm` is itself malicious, and it has an equally beautiful commit history.
3. **"Users can inspect every line of Wasm" is something almost nobody does in practice** — **transparency provides "auditable," not "audited."** The gap between those two is where most security incidents happen. → Chapter 9

### Q13. Can a client-side memory hash check prevent cracking?

**Calibration**: **It doesn't hold technically.** Any client-side self-verification can be bypassed by a local modification — a direct corollary of the iron rule that the client is untrusted. What actually works is **server-side authorization** (which account this token belongs to, whether it is paid, whether it has permission for this file), not the client's protestation of innocence. → Chapter 10

---

## 3b. On Specification Versions (added during this book's revision)

### Q13b. After Wasm 3.0, which common statements are out of date?

**Calibration**: **In September 2025, WebAssembly 3.0 was announced complete and became the current standard**, taking nine features into the core specification at once: **WasmGC, Memory64, exception handling, tail calls, 128-bit SIMD, multiple memories, typed function references, extended constant expressions, and branch hinting**.

**So all of these are now out of date**:

| Out-of-date claim | Current state |
|---|---|
| "Wasm GC is still a proposal / experimental" | **It is core specification** (Wasm 3.0) |
| "The memory64 proposal isn't settled" | **It is core specification**; but **the performance cost remains** (losing the free bounds check from guard pages) |
| "C++ exceptions can only go through a JS trampoline" | **Native exception handling exists**: the Tag section (id 13) + `try_table` / `exnref` |
| "Functional languages will always blow the stack on Wasm" | **`return_call` tail calls exist** |
| "A module can have only one linear memory" | **Multiple memories are standardized** — the fourth way around 4 GiB, and it **keeps the free bounds check from guard pages** (Appendix M §8) |

**But distinguish two things**: **standardized in the specification ≠ usable by you today.** Engine support has broadly caught up; **toolchains often lag** — most C/C++/Rust toolchains still assume "only one memory" by default. **"Specification status" and "can I use it today" must be asked separately.** → Appendices A, M

### Q13c. Can synchronous C code really await a Promise now?

**Calibration**: **Yes — that is JSPI (JavaScript Promise Integration).** It **reached Phase 4 (standardized) in April 2025** and has shipped in **Chrome 137 and Firefox 139**. The mechanism is that **the engine suspends the whole Wasm execution stack** and resumes from the suspension point once the Promise settles — from Wasm's side it looks like an ordinary synchronous call.

**But you must know three costs**: **(1)** the cost of suspending and resuming scales with stack depth, so **it cannot go in a hot loop**; **(2)** **it solves "waiting," not "parallelism"** — you still have only one thread; **(3)** **reentrancy**: while suspended, JS may call the same instance's exported functions again, and the overwhelming majority of C code assumes only one call is in flight at a time, which corrupts state — you must add your own reentrancy lock.

**What it replaces is Asyncify** (Binaryen rewriting the whole module binary to simulate suspension), which inflates size noticeably and requires manually annotating the functions that may unwind. **Migration strategy: detect `typeof WebAssembly.Suspending === "function"`; use JSPI if present, and fall back to an Asyncify build if not.** → Chapter 3 Wall 7, Appendix M §5

### Q13d. To run persistent SQLite on GitHub Pages, must I deal with COOP/COEP?

**Calibration**: **Not necessarily, and this is the most practically valuable correction made during this book's revision.**

The official SQLite-Wasm provides **two** OPFS VFSes:

- **`opfs` (first generation)**: an async proxy between the main thread and OPFS, turning async into sync with `Atomics.wait` → **it needs `SharedArrayBuffer` and therefore cross-origin isolation**.
- **`opfs-sahpool`**: it holds a pool of pre-opened sync access handles and reads and writes synchronously inside a Worker → **it needs no COOP/COEP, and it is the fastest option in the official documentation**; the cost is **no support for multiple simultaneous connections**. It has been broadly available in mainstream browsers since March 2023.

**The official recommendation says exactly this**: clients that value performance over concurrency, or that cannot set COOP/COEP, should use `opfs-sahpool`.

> **The general lesson**: when you are about to pay a heavy architectural price for a platform restriction, **check first whether the library you depend on has a path that doesn't need that restriction.** Many teams have wrestled with `SharedArrayBuffer` and isolation for two weeks when what they wanted had a second backend all along. → Chapters 5, 7

## 4. On Limits

### Q14. Once wasm64 arrives, is the 4 GB problem gone?

**Calibration**: **It costs something.** The reason wasm32's bounds check is zero instructions on the hot path is that "the engine reserves 8 GiB of virtual address space plus guard pages, and the MMU performs the check for free." **Once addresses become 64-bit you cannot possibly reserve 2⁶⁴ of virtual space per memory**, the guard page trick stops working, and you fall back to explicit comparison and branching, with a real performance regression.

**The correct mental model**: below 4 GiB you enjoy hardware-subsidized free safety; past that line, safety starts charging. **If chunked streaming solves it within 4 GiB, don't rush to wasm64.** → Chapters 2, 8

### Q15. "Turning on Wasm GC cuts file size by 80%"?

**Calibration**: **The direction is right, but it holds only for languages that previously had to bundle an entire language runtime** (Java, Kotlin, Dart and so on). **For Rust, C and C++, enabling Wasm GC brings almost no size benefit** — their objects were already allocated in linear memory, so there is no GC to save. Applying this advice indiscriminately to every language is a very common misreading. → Chapter 8

### Q16. Is `coi-serviceworker` exploiting a security hole?

**Calibration**: **No.** It is a **correct use** of the specification — a Service Worker is a proxy layer the same-origin page registers itself, and it can only intercept requests within its own scope. It does not bypass the browser's security model; it **declares, within the page's own authority, "I voluntarily enter the isolated state,"** and the cost of isolation (losing cross-origin resources) is borne by that page itself.

**But two things deserve long-term vigilance**: (1) the specification makes no explicit promise that "COOP/COEP synthesized by a Service Worker must be equivalent to headers sent by the server" — that is a natural inference each implementation draws from the specification, and depending on inferred behaviour at the intersection of multiple specifications carries the risk of being tightened. (2) It exposes a structural fact: **what free hosting withholds is usually not the thing you need today, but the control you will need two years from now.** → Chapter 5

### Q17. Do WebContainers really run a server inside the browser?

**Calibration**: **Technically yes, but the boundary must be stated clearly.** It does not compile Node.js's C++ source unchanged to Wasm; it **reimplemented a Node.js-API-compatible runtime running on Wasm**, and uses a Service Worker to intercept network requests to emulate server behaviour.

**The precise version**: "it emulates, inside the browser, a server that behaves consistently for this page." **Other people on the external internet cannot connect to that 'server' through a URL** — unless P2P traversal is added. → Chapter 5, Appendix E case 60

---

## 5. On That "120 Cases" List

### Q18. Are all 120 cases real projects?

**Calibration**: **No, and it takes three layers to see it.**

- **First, 19 of the 120 are duplicates** (26–30 restate 21–25; 32–35 restate 21–24; 61–65 restate 46–50; 66–70 restate 36–40). **The genuinely distinct count is 101.**
- **Second, those 101 fall into three authenticity tiers**: 🟢 verifiable (about 40%), 🟡 upstream real but the Wasm port unverified (about 40%), 🔴 illustrative construction (about 20%).
- **Finally, the correct reading is to treat it as a "feasibility map," not a "project index."** Nearly every 🔴 entry's technical path holds up; it is simply that nobody has built it, or someone has under another name (case 66 versus DuckDB-Wasm and case 70 versus OpenCV.js are the best examples). → Chapter 6, Appendices D–F

### Q19. Why the duplicates? What does that tell us?

**Calibration**: It is a concrete failure mode of long-conversation generation — **when the generating side has no externally maintained "already produced" list, deduplication can only rely on conversational context, and once that context exceeds the effective attention range, deduplication fails.**

What is interesting is how the user's response evolved in the original conversation: first "give me ones that don't repeat the earlier entries" (ineffective) → "you repeated yourself" (ineffective) → finally specifying new category dimensions ("application categories: network, games, ERP, server, open-source ports"; "software engine, physics engine, world engine, LLM engine, graphics engine") — **and that worked.**

**The lesson: constraining the search space works better than demanding recall.** → Chapter 6

### Q19b. Did FluffOS really run an entire MUD server inside the browser?

**Calibration**: **Yes, and it is one of the few heavyweight cases in this book that can be verified item by item.** The official FluffOS README lists WebAssembly among its build targets, and `src/wasm/README.md` documents the architecture in full (a host-driven `fluffos_tick()` event loop, the Transport abstraction and JS bridge, seven exported entry points, MEMFS plus `file_packager` bundling). The official wording is "the entire driver runs in one browser tab: compiler, virtual machine, efuns, telnet."

**But three boundaries must be understood precisely**: **(1)** it is **standalone** — there are no BSD sockets and DNS is stubbed to return `127.0.0.1`, so **other people cannot connect over the network to that server inside your browser** (the same point as Q17's WebContainers). **(2)** **Writes currently persist only within the tab session** (MEMFS is volatile); an IDBFS/OPFS overlay is still on the roadmap. **(3)** There is no eval limit, so **an infinite LPC loop freezes the whole tab.**

**The inventory count moves**: the repository README records 200 mudlibs / 158 codebases / 79 verified WASM-playable, while the online archive site listed numbers that did not match exactly at the time. **Statistics of this kind change with every repair push, so treat the state at the moment you visit as authoritative.** → Appendix L

### Q20. Is Penpot built on Wasm?

**Calibration**: **Penpot really exists and is a genuine open-source design collaboration tool**, and can reasonably be cited as evidence that open-source alternatives are maturing. But describing it as "built on Wasm" **is not accurate** — its stack is primarily ClojureScript/SVG.

**Slippage of this kind in details is very common in technical narrative, and it misleads architectural decisions.** The accurate statement is: open-source alternatives really exist and are maturing, but their technical paths are not necessarily the same as the commercial products'. → Chapter 11

---

## 6. On Business and Moats

### Q21. How credible is the description of Figma's architecture?

**Calibration**: **Partly based on Figma's public engineering blog** (the Wasm migration, multiplayer collaboration and rendering pipeline really do have official articles), **and partly reasonable inference from technical logic** (specific implementation details like "all UI text is streamed dynamically" and "the backend does binary feature matching" have not been publicly confirmed by Figma).

"Vector networks" is genuinely a core technical feature Figma promotes publicly, but the specific algorithm is not published.

**Read Chapter 10 as an example of an architectural pattern, not as an authoritative description of Figma's internal design.** → Chapter 10

### Q22. Does data gravity form naturally?

**Calibration**: **A large part of it is the result of design choices, not a natural consequence of data volume.** Data gravity's strength is **inversely proportional to data portability**:

- Open format, a complete export API, a third party that can import it → weak pull.
- Proprietary format, lossy export, no second destination → strong pull.

**So in practice "data gravity" is largely a product of "format and API design choices."** That matters equally to builders and buyers — the builder knows how to construct it, and the buyer therefore knows how not to fall in. → Chapter 12

### Q23. Can P2P really make collaboration "serverless"?

**Calibration**: **"Serverless most of the time."** Four engineering realities get skipped:

1. **NAT traversal doesn't succeed 100% of the time** — behind a symmetric NAT you must fall back to a **TURN relay**, and a TURN server costs money, bandwidth and operations.
2. **Offline and asynchronous collaboration** — "I finished editing on Friday, you open it on Monday" requires an always-online node, and that is a server under a different name.
3. **Who is the source of truth** — enterprises want an authoritative version, audit records, access control and permission revocation for departed employees. **P2P is inherently weak at revocation** (the data is already on the other machine).
4. **Compliance** — "the data is scattered across every employee's browser" is not an answer that passes an audit. → Chapter 11

### Q24. "Tokens got cheap, so building it yourself only costs time" — is that inference right?

**Calibration**: **The inference itself is right, but it omits two bills.**

- **The time trap**: software engineering's law is that "writing code is 20%, debugging and edge cases are 80%," and **AI only zeroed the former**. What you saved is that 20%.
- **Maintenance entropy**: two years later the W3C deprecates an API you depended on, and **nobody ever truly read those hundred thousand lines**. You must re-engage the AI to understand this pile of "old wheels," or throw it out and start again.

**A more precise description of the deformation**: AI makes "code produced" far outpace "code understood," so **"code nobody actually understands" accumulates at unprecedented speed** — and a system's maintainability depends on the latter, not the former. → Chapter 12

### Q25. So should you build it yourself or not?

**Calibration**: It splits into two kinds of people. **Individuals and small teams** building micro-wheels come out ahead (small scale, stable requirements, they fix it themselves when it breaks); **modern industry and large enterprises** come out ahead paying a vendor (outsourcing technical entropy and spending their time on the core business).

**And the layer in between — mediocre, single-purpose, lightweight SaaS — gets eliminated.**

Deciding whether you should build takes just one test: **"When this breaks at midnight three years from now, who fixes it, and are they still at the company?"** Until that question has a clear answer, **what you built is not a wheel; it is debt.** → Chapter 12

---

## 7. One General Reading Rule

> **For every specification-level statement in this book (the binary format, proposal status, browser API behaviour), treat the official WebAssembly specification, MDN and each engine's implementation documentation as authoritative.**
> This is a field where proposals are still moving, and this book was written in 2026.
>
> For every performance number: **trust the direction, doubt the multiplier.**
> For every project name: **verify before citing.**
> For every "X is dead" narrative: **go find the position that wasn't stated.**

---



# Appendix L: A Deep-Water Case — FluffOS × Wasm, Moving an Entire MUD Server onto a Static Page

> **This is the only case in the book that deserves a chapter of its own, because it is three things at once:**
> **One, it is the real version of two 🔴 illustrative constructions from Appendix E (case 58 Minestom-Wasm and case 60 Micro-Apache-Wasm)** — and it goes further than either.
> **Two, it runs into every wall the book's twelve chapters describe, all at once**, and its handling of each one is on the public engineering record.
> **Three, it is the cleanest living specimen of the book's central thesis**: **the code has been 100% downloadable, self-hostable and modifiable for thirty years, and its value has never lost a single ounce because of it.**
>
> **Authenticity tier: 🟢 verifiable.** Every technical detail in this appendix comes from the official FluffOS repository's `README.md` and `src/wasm/README.md`, plus the `fluffos/mudlibs` repository. **The only thing that moves over time is the inventory count and the proportion "already WASM-ified"** — treat the repository's current state as authoritative.

---

## 1. What It Is

### FluffOS: an LPMud driver still under maintenance

**FluffOS** is a **modern fork of MudOS** — an actively maintained **LPMUD driver** (an LPC interpreter plus game engine) written in C++. Its job is not "a game" but **a complete game server runtime**:

```
The FluffOS driver (C++)
├── LPC compiler     ← compiles the mudlib's .c sources to bytecode at runtime
├── Virtual machine  ← executes that bytecode
├── efuns            ← the built-in function library (strings, arrays, files, network, time…)
├── Scheduling core  ← heartbeat, call_out (timers), reset
└── Network layer    ← telnet / WebSocket / TLS
```

It stays backward compatible with existing MudOS mudlibs, has accumulated over a decade of performance optimization, and additionally supports **WebSocket, TLS, MySQL/PostgreSQL/SQLite3 integration** and **UTF-8 EGS-aware LPC string operations** (range operators handle emoji and other Unicode characters).

**Build targets**: CMake, supporting Ubuntu, macOS, Windows (MSYS2/MinGW64) — **and WebAssembly**.

### mudlibs: a source archive of an entire era

`github.com/fluffos/mudlibs` is a **source archaeology archive of the Chinese MUD scene** — covering work from the mid-1990s through around 2015, collecting LPC games in the wuxia and xianxia genres (*Journey to the Wild West*-style titles built from Jin Yong's novels, *Journey to the West* and their many forks) along with their branches.

The repository's organization is itself a record of repair engineering:

```
archives/                       the original archive files
libs/<slug>/raw/                the untouched extracted contents (original encoding preserved)
libs/<slug>/work/               the playable version (converted to UTF-8, repairs applied)
libs/<slug>/config.fluffos      runtime configuration
libs/<slug>/README.md           player notes
libs/<slug>/NOTES.md            the repair log
scripts/                        conversion and testing tools
lib_numbering.json              a machine-readable cross-reference
```

**Inventory status** (per the repository README; the numbers move with repair progress):

| Status | Count |
|---|---|
| Repaired mudlibs | **200** (covering **158** distinct codebases) |
| **Verified playable in the browser (WASM)** | **79** |
| Boots natively, WASM packaging pending | 117 |
| Native-only by policy | 1 |
| Confirmed unable to boot | 4 |

**Licensing**: most are held as a historical community archive with no formal licence terms (one of them, *The Reborn World*, is explicitly GPLv2). The project's stated position is "**preserve them as cultural assets**," retaining the original authors' attribution.

> ⚠️ **The numbers move**: at the time of writing, the count of playable games listed by the online archive site `mudlibs.fluffos.info` did not exactly match the repository README's statistics (the former listed around ninety-odd, the latter records 79 verified WASM-playable). **Numbers of this kind change with every repair push** — treat the repository and site as you find them, since this book cites the relationship rather than the snapshot.

---

## 2. Why It Deserves Its Own Chapter

**Because it crossed a line others only cross on slides.**

Recall Appendix E's two 🔴 entries:

- **Case 60, "Micro-Apache-Wasm"**: the concept is running a tiny HTTP server in the browser, with a Service Worker intercepting requests and feeding them to Wasm. **The concept holds, but what it emulates is the stateless thing called request-response.**
- **Case 58, "Minestom-Wasm"**: the concept is running a Minecraft server in the browser. **Closer, but it needs WebRTC for anyone else to connect.**

**What FluffOS's Wasm target achieves is harder than either** — because a MUD driver is not a request handler; it is a thing with **a heartbeat, timers, persistent world state, multiple concurrent connections, and the requirement to compile user code at runtime**:

> The official README's wording is: **"The whole driver runs in a browser page (or node) — compiler, VM, efuns, telnet."**
> Compiler, virtual machine, built-in function library, telnet protocol — **all of it** in one browser tab.

And the mudlibs are distributed like this: **"Mudlibs ship as static bundles via `tools/wasm/pack-mudlib.sh`; no server required."** — **packaged as static bundles, no server needed.**

That is the ultimate version of Chapter 5's line: **the computation didn't disappear; it just changed who pays for it.**

---

## 3. Architectural Deep Dive: Five Problems That Had to Be Solved

This section is the appendix's technical core. **FluffOS's Wasm port is not "recompile and you're done"** — it had to deal with Wasm's and the browser's physical limits one by one, and every solution is worth writing down.

### Problem one: the browser cannot block, yet a server's essence is waiting

**The native driver blocks in libevent's event loop** — `while(true) { wait_for_events(); dispatch(); }`. **That is a dead end in a browser**: block the main thread and the whole tab freezes.

**Solution: hand ownership of the event loop to the host (a host-driven tick).**

```javascript
// The page drives the driver with setInterval / requestAnimationFrame
setInterval(() => {
  Module._fluffos_tick(Date.now());   // ← advance the scheduler once, handle due events, return immediately
}, 50);
```

**The key design decision**: the scheduling core (the gametick queue, maintenance events) is **shared between native and Wasm**, and the only difference is **who advances the loop**. So **heartbeat, call_out and reset — the LPC-level mechanisms — need no changes at all**: not one line of mudlib code knows it is living in a browser.

> 💡 **This is the most elegant move in the whole port**: it did not change "how time flows," only "who rings the bell."

> 🔧 **A future option worth noting**: this "hand the loop to the host" solution addresses **active scheduling**, but it does not address **passive waiting** — when LPC code wants to read something asynchronous (OPFS's async API, or a network request), the driver still has nowhere to wait. **JSPI** (Chapter 3 Wall 7, Appendix M §5) is exactly for that: it lets the engine suspend the whole Wasm stack and resume once the Promise settles.
> The significance for this project is concrete: **the roadmap item about layering an IDBFS/OPFS overlay for persistence would, after JSPI, no longer require rewriting the whole storage layer as asynchronous.** The cost is that it introduces reentrancy — **while suspended, `fluffos_tick` may be called again** — and a driver's assumption that "only one tick runs at a time" is very strong. **This is a textbook instance of "a new capability brings a new constraint."**

### Problem two: there are no sockets, yet every player is a connection

**Solution: abstract "connection" into a byte pipe (Transport).**

Every user connection owns a `Transport` — an abstract byte pipe with just four operations: `write` / `flush` / `schedule_command` / `close`. There are three implementations beneath it:

| Implementation | Target | Underneath |
|---|---|---|
| `SocketTransport` | Native | libevent |
| `WebsocketTransport` | Native | libevent |
| **`WasmConsoleTransport`** | **Browser** | **JS bridge** |

`WasmConsoleTransport`'s two directions:

```
Outbound: bytes the driver writes → Module.fluffos.onOutput(id, bytes) → the page's terminal
Inbound:  the command the user types → the exported fluffos_input(id, bytes, count) → the driver
```

**And the most interesting detail is that the driver still emits real telnet protocol.** So the web page must supply a telnet client of its own — the official interface negotiates **ECHO, SGA, NAWS (window size) and TTYPE**, and renders the terminal with **xterm.js**.

> **This section is the real control group for Appendix E case 29 (xterm's Wasm parsing plugin)**: there, ANSI parsing was moved into Wasm; here, **the other end of the protocol** is moved wholesale into Wasm, with xterm.js outside acting as the display.

### Problem three: the export surface must be narrow enough

**The entire driver exposes just seven functions** — a textbook demonstration of both Chapter 2's "the Export section is what an attacker always sees" and Chapter 12's "keep the interface narrow":

| Exported function | Purpose |
|---|---|
| `fluffos_boot(config_path)` | Initialize the driver |
| `fluffos_tick(now_ms)` | Advance the scheduler by real time |
| `fluffos_connect()` | Establish a new virtual connection |
| `fluffos_input(id, bytes, count)` | Feed in the client's command bytes |
| `fluffos_disconnect(id)` | Close a connection |
| `fluffos_shutdown()` | Shut the driver down |
| `fluffos_flag(flag)` | Set a runtime flag (such as `'test'`) |

Instantiating the module:

```javascript
const M = await createFluffOS({ print, printErr, locateFile });
```

**Seven functions, one entire server.** Against Chapter 2 Scenario 4's line — **make the boundary coarse and the round trips few** — this is the most extreme example available.

### Problem four: a mudlib is tens of thousands of files, and Wasm has no filesystem

**Solution: MEMFS plus Emscripten's `file_packager`.**

Emscripten maps file I/O transparently onto an in-memory filesystem (MEMFS, see Chapter 7). The mudlib is packaged by `file_packager` into **a single `mudlib.data` image plus a `mudlib.js` loader**, mounted at a specified path before the runtime starts.

```bash
# Package an arbitrary mudlib
MUDLIB=/path/to/lib tools/wasm/build.sh
# or
tools/wasm/pack-mudlib.sh --mudlib <dir> --config <path>
```

**So the distribution shape becomes**: one `.wasm`, one `.js` glue file, one `.data` image — **three static files, and that is a whole game world.**

**But there is an honest current limitation here**, and it happens to be a living lesson in Chapter 7's four-tier storage ladder:

> **Writes currently persist only within the tab session (MEMFS is volatile).**
> The official roadmap's Phase 2 plan is: **layer IDBFS (or OPFS) over the mudlib's write paths (`/data`, saves, logs) and call `FS.syncfs()` on a timer and on `visibilitychange`** — so data survives a page reload. **Not yet implemented.**

**In other words: this project is currently stuck at Chapter 7's first tier (MEMFS), and it knows it needs to move to the second and third (IDBFS/OPFS).** There is no better field verification anywhere in this book.

### Problem five: capabilities must be cut away

Chapter 2 said "the cheapest way to implement security is not adding defences but removing capabilities." **FluffOS's Wasm build turns that into a table**:

| Feature | Status | Reason |
|---|---|---|
| libevent | **Removed** | Replaced by the tick queue |
| OpenSSL / TLS | **Removed** | **TLS is the browser's job**; `sys_reload_tls` does not exist |
| zlib | **Removed** | MCCP and the compress package are disabled |
| POSIX eval-limit timer | Auto-disabled | Available only on `__linux__`; an alternative is planned |
| BSD sockets | Off | No outbound socket efuns |
| DNS | **Stubbed** | Returns `127.0.0.1` synthesized on the next tick |
| External processes | Off | No `posix_spawn` support |
| Worker threads | Off | No async package |
| Database clients | Off | The MySQL/SQLite/PG libraries are unavailable |

**That table is what capability-based security actually looks like** (Chapters 1, 7): it is not "we defended these attack surfaces" but "**these attack surfaces do not exist in this build**."

It also maps precisely onto Chapter 3's four system walls — **no native system access, memory that only grows, no threads, and synchronous code meeting an asynchronous world**.

---

## 4. The Concrete Numbers

**This is the most valuable set of measured numbers in the book, because they come from a real, complex, still-maintained project rather than a benchmark toy.**

| Item | Value | Corresponding chapter |
|---|---|---|
| Initial linear memory | **64 MB** (grows to **2 GB** as needed) | Chapter 8: note the ceiling is set at 2 GB, not 4 GiB — **this is exactly "the browser's real-world interception"** |
| Stack | 16 MB | Chapter 2 |
| Code size (including PCRE) | **~3.6 MB raw** | Chapters 3, 8: far below the "30 MB practical ceiling" |
| Code size (after Brotli) | **~0.8 MB** | Chapter 8: **a compression ratio of about 4.5×, confirming that "Wasm's Brotli ratio is usually very good"** |
| ICU data | **~780 KB** (about 30 MB originally) | Chapter 8: **only the break-iterator rules are kept, cutting 97%** — this is "the highest-return step in cutting size is not a compiler flag but cutting the data you don't use" |
| DWARF debug info | Stripped at link time | Chapter 9 |
| Function names | **Kept** (for readable stack traces) | Chapter 3: **a deliberate trade-off** — a little obfuscation strength given up for debuggability |

> 🔍 **That ICU number is worth pausing on for three seconds.**
> 30 MB → 780 KB, cutting 97.4%. **Not through `wasm-opt`, not through LTO, but through thinking clearly about what ICU was actually for** — this project needs only the break-iterator (word segmentation) rules, so every other locale, time zone, collation rule and transliteration table simply isn't packaged.
> **Chapter 8's "size-cutting return ranking" should gain a step 0: cut the data before you cut the code.** Because in the Wasm output of a large C/C++ project, more than half is often the data tables it dragged in, and you usually don't use 90% of them.

---

## 5. Running It Locally Yourself

### Route A: native (fastest way to see something)

```bash
# 1. Get a mudlib
git clone https://github.com/fluffos/mudlibs
cd mudlibs/libs/<the slug you picked>

# 2. Start it with a built driver (work/ is the playable version, UTF-8 converted with repairs applied)
~/src/fluffos/build-debug/src/driver config.fluffos

# 3. telnet in
```

### Route B: WebAssembly (make it a static site)

```bash
# One-off: cross-build ICU for wasm32
tools/wasm/build-deps.sh

# Build: native codegen tools + the wasm driver + the demo bundle
tools/wasm/build.sh

# Serve it locally to look at the result
python3 -m http.server -d build-wasm/dist 8080
# open http://localhost:8080/
```

**Swapping in your own mudlib**:

```bash
tools/wasm/pack-mudlib.sh --mudlib <mudlib dir> --config <config path>
# or
MUDLIB=/path/to/lib tools/wasm/build.sh
```

**The output is a purely static directory** — drop it on GitHub Pages, any CDN or any S3 bucket and you have a playable game. **That is Chapter 5's "building machines on static pages," closed end to end.**

### Pre-launch, against Chapter 5 and Appendix C

| Check | This case's situation |
|---|---|
| Does it need COOP/COEP? | **No** — there are no threads (the async package is off), so **deploy directly** |
| The `.wasm` MIME | Static hosting must return `application/wasm` correctly |
| Relative paths | A project page lives under a subpath; watch how `locateFile` resolves |
| `.nojekyll` | Needed (so resources beginning with `_` aren't swallowed) |
| Brotli | **Strongly recommended** — 3.6 MB → 0.8 MB |

---

## 6. Every Wall It Hit (mapped back to this book)

| Wall | What happens | Chapter |
|---|---|---|
| **No blocking event loop** | Had to become `fluffos_tick(now_ms)` driven by the host | Chapters 3 (the system wall), 5 |
| **No sockets** | The Transport abstraction plus a JS bridge; DNS stubbed to `127.0.0.1` | Chapters 3, 7 |
| **No threads** | The async package is off entirely, with a synchronous replacement planned | Chapters 3, 5 |
| **No eval limit** | **An infinite LPC loop freezes the whole tab** (natively it relies on a POSIX timer; there is no replacement on Wasm yet) | Chapter 3 (the sandbox doesn't protect you from yourself) |
| **MEMFS is volatile** | Writes persist only within the session; an IDBFS/OPFS overlay is on the roadmap | **Chapter 7 (the four storage tiers)** |
| **The tab is suspended in the background** | Timers pause; on returning to the foreground the gameticks catch up (**capped at 100**) | Chapter 5 (the host environment's rhythm isn't yours to set) |
| **Table-based charsets unsupported** | Only algorithmic ones (UTF-8/16/32, Latin-1, ASCII) are supported; table-based ones are not | Chapter 8 (data is the bulk of the size) |
| **A 2 GB memory ceiling** | Not 4 GiB — **this is the browser's real-world interception** | Chapter 8 |
| **Missing browser-environment capabilities** | The archive site notes some games are "playable but with login restrictions," because capabilities like `query_ip_number()` are missing | Chapters 3, 7 (capabilities must be handed in by the host; if they can't be, they don't exist) |

> **The last row is especially worth savouring**: a mudlib written in the 1990s calls `query_ip_number()` during its login flow to record the player's IP — **and inside a browser there is no such concept as an IP to give it.** One line of code written thirty years ago has become a porting obstacle today.
> **This is what Chapter 12's "maintenance entropy" looks like most concretely: your code didn't break; the world beneath it was replaced.**

---

## 7. jsbridge: The Two-Way Door That Was Opened

FluffOS's Wasm build provides a set of `jsbridge` efuns **that exist only on the WASM target**, letting LPC and page JavaScript call each other:

```
LPC → JS:  js_eval(), js_call()      → fetch, canvas/WebGL, audio, storage…
JS  → LPC: js_export() + fluffos.callLPC()
```

**This matters more than it looks**: it means a 1990s text game **can grow a canvas map, WebGL effects, Web Audio soundtracks and browser-side storage without altering the game logic at all** — because that bridge is two-way, and the game side only has to call one more efun.

> This lines up exactly with Chapter 12's four-layer topology: **the Wasm core (the LPC driver) is an asset designed to be unchanged for a decade; the page layer (xterm.js, canvas, UI) is consumable and may be rewritten every three years.** And jsbridge is that "interface so narrow it cannot go wrong."

---

## 8. Why It Is the Living Specimen of the Book's Thesis

**Now put the technology down and look at the other side of this.**

A MUD's **entire source code** — the world map, the NPC dialogue, the martial-arts systems, the economic rules, the description of every room — is that mudlib. **It has always been downloadable in full**: in the 1990s through packed archives, today through `git clone`, and now it can even be loaded and run directly in a browser.

**Not one line of code is secret.**

By the old logic that code is an asset, a thing like this could not possibly have value. And yet:

- These games **lived thirty years**, forked, modified and reopened long after their original authors left.
- Someone **spent an enormous amount of effort repairing them** — converting encodings, fixing bugs, writing a `NOTES.md` recording every change, verifying one by one whether each still boots.
- And today someone **compiled the entire driver to Wasm**, purely so they can be opened again.

**That moat was never in the code.**

It is in those people — in the ones who remember being stuck in some room for three days at seventeen, and in the one who repaired those broken thirty-year-old archives one at a time. **These are the two hardest to copy of Chapter 12's five lines of defence: data gravity (the world state and that memory) and ecosystem (the community)** — and neither has anything to do with the code's visibility.

> 💡 A Word to the Wise
> **When something's source has been fully copyable for thirty years and it still has not been replaced, you have found a clean piece of evidence about value.** These mudlibs are a rare controlled experiment in software history — **zero secrecy, zero copying cost, a trivially low barrier to modification** — and in theory they should have drowned under better copies long ago. They did not. Because what users want has never been "a copy of code that runs"; it is **that world, and the people in it**. And those two things `git clone` cannot take.
> Put that inside Chapter 12's framework and the answer is very clear: **when LLMs drive the marginal cost of writing code to zero, we simply arrive where MUDs have always been — the code was never what was valuable; what was valuable is everything that grew around it.** The only thing that changed is that now all software must face that situation.
> So rather than worrying about whether AI will copy your product, ask something more useful: **if my source were published in full tomorrow, would anyone still be using it in thirty years?** These mudlibs' answer is yes. **What is yours?**

> 🔍 Deeper Commentary — the technical debt of preservation, and a long-term problem nobody talks about
> This case also exposes something increasingly acute in digital preservation that the software industry has broadly not started to face. **Repairing a thirty-year-old mudlib is hard not because of the code but because of the world beneath it that vanished.** What those `NOTES.md` files record is mostly not logic errors but: whether the original encoding was GB2312 or BIG5, which efuns the driver of that era had that no longer exist, and what to do about a call like `query_ip_number()` that assumed there was a network, an IP, an operating system. **The code itself is barely broken — what broke is every assumption it made about its environment.**
> **And this is exactly where Wasm's real value in cultural preservation lies, and where it differs from virtual machines and emulators.** An emulator (Appendix D case 3's v86) preserves "the hardware"; a container image preserves "the operating system and dependencies"; **compiling a driver to Wasm preserves "execution semantics"** — you need not preserve an entire 1996 Linux, only a 3.6 MB module and a host interface with a stable specification. **Wasm has therefore become, almost by accident, one of the best software preservation formats we have**: a public specification, several independent implementations, an extremely strong backward-compatibility commitment, and a host environment (the browser) that is itself the most conscientiously maintained compatibility layer humanity has.
> Turned around, that is also an uncomfortable reminder for everyone writing code today: **every assumption about the environment you write down — this API will exist, this service will exist, this format will be supported — is an exam question you are setting for someone thirty years from now.** And Chapter 12's question about "who fixes it when it breaks at midnight three years from now" reaches its final form here: **thirty years from now, will anyone still understand why you wrote it that way?** Those `NOTES.md` files are the only effective answer to that question.

---

## 9. Putting It Back in the Catalog: Whom It Replaces

| Appendix E's 🔴 concept | The real counterpart | The difference |
|---|---|---|
| Case 58 Minestom-Wasm (a game server in the browser) | **FluffOS × Wasm** | FluffOS is real, and harder — it also compiles user code at runtime |
| Case 60 Micro-Apache-Wasm (a server engine in the browser) | **FluffOS × Wasm** | Micro-Apache handles only stateless requests; FluffOS has a heartbeat, timers and persistent world state |
| Case 92 OpenLISP-Wasm (a symbolic computation interpreter) | **FluffOS's LPC compiler + VM** | The same shape: **move a language's complete runtime into Wasm** |
| Case 34 QuickJS-Wasm (JS inside JS) | **FluffOS's LPC inside Wasm** | The same shape, but FluffOS also brings a whole game runtime along |

**If the catalog in Appendices D–F is a map of "is this road passable," this appendix is the place at the end of the road where someone actually lives.**

---

## 10. Resources

| Item | Location |
|---|---|
| The FluffOS driver | `github.com/fluffos/fluffos` |
| Architecture documentation for the Wasm target | `src/wasm/README.md` (this appendix's main source) |
| Wasm build scripts | `tools/wasm/build-deps.sh`, `tools/wasm/build.sh`, `tools/wasm/pack-mudlib.sh` |
| The mudlib archive | `github.com/fluffos/mudlibs` |
| The online archive (click and play) | `mudlibs.fluffos.info` |
| Official documentation | `fluffos.info` |

> ⚠️ **A licensing note**: most works in the mudlibs archive **have no formal licence terms**; it is a community archive for cultural preservation that retains the original authors' attribution. **If you intend to do anything beyond personal study and play (commercial use especially), clarify the rights yourself.** This book's citations are likewise for education and research only.

---



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

---



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

---



# Appendix O: Testing, CI and Runtime Security

> This is the last piece added to the book, and it fills an awkward hole: **the fourteen appendices before it teach you how to build Wasm, make it small, make it fast and make it hard to steal — and not one of them tells you how to confirm it is correct.**
>
> Chapter 3 said: **"The most accurate measure of a technology's maturity is not how fast it runs but how easy it is to investigate when it breaks."** This appendix is that sentence's operations manual.

---

## 1. The Three-Layer Pyramid of Wasm Testing

**Testing a Wasm project has one peculiarity: the same code can run in three environments, and each catches entirely different errors.**

```
        ┌───────────────────────────────────┐
        │  ③ Browser integration tests       │  ← catches: JS bindings, DOM/API
        │     (slowest, truest)              │     interaction, OPFS/Worker behaviour,
        │     wasm-bindgen-test              │     real engine differences
        ├───────────────────────────────────┤
        │  ② Wasm-environment unit tests     │  ← catches: Wasm-specific behaviour
        │     wasm32 target + Node/WASI      │     (alignment, i32 overflow, the boundary)
        ├───────────────────────────────────┤
        │  ① Native unit tests (fastest,     │  ← catches: pure logic errors
        │     most numerous)                 │     **this layer should be 80%**
        │     cargo test / ctest             │
        └───────────────────────────────────┘
```

**The most important principle**: **never let an error catchable at layer ① drag on to layer ③.** A native test runs in milliseconds; a browser integration test runs in tens of seconds — **shaping the pure logic so it doesn't depend on Wasm is the single most worthwhile architectural investment in a Wasm project.**

```rust
// ✅ This shape lets 80% of tests run natively
mod core {                                   // pure logic, never touching wasm-bindgen
    pub fn transform(input: &[u8]) -> Vec<u8> { /* ... */ }
}

#[cfg(target_arch = "wasm32")]
mod bindings {                               // only this layer needs a Wasm environment
    use wasm_bindgen::prelude::*;
    #[wasm_bindgen]
    pub fn transform(input: &[u8]) -> Vec<u8> { super::core::transform(input) }
}

#[cfg(test)]
mod tests {                                  // cargo test runs it directly, no browser needed
    #[test] fn roundtrip() { assert_eq!(super::core::transform(b"abc"), b"..."); }
}
```

---

## 2. `wasm-bindgen-test`: Running Tests in a Real Engine

```rust
use wasm_bindgen_test::*;

// Run in the browser (Node is the default)
wasm_bindgen_test_configure!(run_in_browser);

#[wasm_bindgen_test]
fn works_in_wasm() {
    assert_eq!(crate::core::transform(b"abc"), b"...");
}

// ★ Async tests: OPFS, fetch, any Promise
#[wasm_bindgen_test]
async fn opfs_roundtrip() {
    let engine = WasmStorageEngine::new().await.unwrap();
    engine.save_file("t.bin", &[1, 2, 3]).await.unwrap();
    assert_eq!(engine.load_file("t.bin").await.unwrap(), vec![1, 2, 3]);
}

// Run only inside a Worker (a specification restriction on sync access handles, see Chapter 7)
wasm_bindgen_test_configure!(run_in_dedicated_worker);
```

```bash
wasm-pack test --headless --chrome        # headless Chrome
wasm-pack test --headless --firefox
wasm-pack test --node                     # fastest, but no browser APIs
```

**Three practical points**:

1. **`run_in_dedicated_worker` is a precondition for OPFS tests** — `createSyncAccessHandle` fails outright on the main thread (Chapter 7).
2. **Each test file is a separate Wasm module**, so tests **do not share linear memory** — that is good (isolation), but it also means test startup is not cheap.
3. **`--headless` needs the corresponding driver** (chromedriver / geckodriver), so install it in CI too.

---

## 3. The C/C++ Path

```bash
# Emscripten: emit tests you can run with node directly
emcc test.cpp -o test.js -sEXIT_RUNTIME=1 -sASSERTIONS=2
node test.js

# ★ Sanitizers work on Wasm — the most practical way to compensate for
#   "no ASLR/canaries inside the sandbox"
emcc app.cpp -fsanitize=address -sALLOW_MEMORY_GROWTH=1 -o app-asan.js
emcc app.cpp -fsanitize=undefined -o app-ubsan.js
```

**Why sanitizers matter especially on Wasm** (a direct corollary of Chapter 2's ⚠️):

> Inside linear memory there is **no ASLR, no NX, no stack canary**. A buffer overflow that the operating system would block on x86, crashing immediately, may **quietly corrupt adjacent data in Wasm and keep running** — and you will see an inexplicable wrong result a few hundred lines later rather than a clear segfault.
>
> **ASan/UBSan are the only way to get those protections back inside Wasm.** The cost is a noticeable hit to both size and speed, so it is a **test build**, not a release build.

**The WASI scenario**:

```bash
# Run the test binary directly with wasmtime
cargo test --target wasm32-wasip1 --no-run
wasmtime run --dir=. target/wasm32-wasip1/debug/deps/mytest-*.wasm
```

---

## 4. Fuzzing: Something Wasm Especially Deserves

**The reason is direct**: a Wasm module's entry point is usually "feed a blob of bytes in," **and that is exactly the shape fuzzing works best on.**

```rust
// fuzz_targets/parse.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    let _ = mycrate::core::parse(data);      // must not panic, go out of bounds or loop forever
});
```

```bash
cargo fuzz run parse -- -max_total_time=300
```

**And Wasm gives fuzzing an extra benefit**: **you can run the fuzzer itself inside the Wasm sandbox**, so even when a crafted input blows the target code apart, **it absolutely cannot harm the host** (which is exactly the principle behind Appendix E case 50, font fuzzing).

**Three places you must always fuzz**: any **parser** (file formats, protocols, input), any **index arithmetic**, and any **length/offset passed in from JS**.

---

## 5. CI: A Workflow You Can Use Directly

```yaml
name: Wasm CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with: { targets: wasm32-unknown-unknown, components: clippy }

      # ① Native unit tests (fastest, catching 80% of errors)
      - run: cargo test --all-features
      - run: cargo clippy --all-targets -- -D warnings

      # ② Wasm-environment tests
      - run: curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh
      - run: wasm-pack test --node

      # ③ Browser integration tests
      - uses: browser-actions/setup-chrome@latest
      - run: wasm-pack test --headless --chrome

      # ④ ★ Size regression gate (see Appendix N)
      - name: Build & check size budget
        run: |
          wasm-pack build --target web --release
          npm install -g binaryen
          f=$(ls pkg/*_bg.wasm)
          wasm-opt -Oz --strip-debug "$f" -o "$f"
          raw=$(stat -c%s "$f")
          br=$(brotli -q 11 -c "$f" | wc -c)
          echo "raw=$raw brotli=$br"
          # Over budget turns CI red — size regressions need a gate as much as performance ones
          test "$br" -le 900000 || { echo "::error::Brotli size $br > budget 900000"; exit 1; }

      # ⑤ ★ The security red line (Chapter 9)
      - name: Secret scan in binary
        run: |
          if strings pkg/*_bg.wasm | grep -Eq 'sk-|AKIA|BEGIN [A-Z ]*PRIVATE KEY'; then
            echo "::error::possible secret embedded in wasm"; exit 1
          fi
```

**Steps ④ and ⑤ are where this workflow's real value lies**, because they guard two things that **only ever degrade gradually and never break suddenly**:

- **Size regression**: without a gate, the `.wasm` grows from 800 KB to 4 MB within six months and no single commit is to blame. **Put the budget in CI so every overrun has someone answering "why."**
- **Key leakage**: one of Chapter 9's two physical forbidden zones. **It is a single line of `grep`, and it is the highest-return line of CI configuration in the whole book.**

---

## 6. Cross-Engine Differences: The Things That Break in Only One of Them

**"It works fine in Chrome" is the commonest illusion in Wasm projects.** Known sources of difference:

| Difference | How it shows up |
|---|---|
| **Memory ceiling** | Differs by engine and platform (Chapter 8); **mobile is far lower than desktop** |
| **Feature support** | SIMD, threads, GC, JSPI and memory64 landed on different timelines in each |
| **OPFS behaviour** | `createSyncAccessHandle`'s concurrency semantics, quota and eviction policies differ by implementation (Chapter 7) |
| **Timer precision** | Coarsened when not cross-origin isolated, to different degrees in each (Appendix N §15) |
| **Compilation strategy** | Tier-up timing in tiered compilation differs → **microbenchmark results can differ completely** |
| **Stack depth** | The threshold for blowing the stack in recursion differs |

**The countermeasure is a discipline**: **run at least two engines in CI (Chrome + Firefox) and test once on a real low-end mobile device.** A desktop dev machine is the most dangerous source of optimism in any Wasm project.

**Runtime detection plus fallback paths**:

```javascript
const caps = {
  simd:    WebAssembly.validate(new Uint8Array([0,97,115,109,1,0,0,0,1,5,1,96,0,1,123,3,2,1,0,10,10,1,8,0,65,0,253,15,26,11])),
  threads: typeof SharedArrayBuffer === "function" && self.crossOriginIsolated,
  jspi:    typeof WebAssembly.Suspending === "function",
  opfs:    !!navigator.storage?.getDirectory,
};
const build = caps.threads && caps.simd ? "app-mt-simd.wasm"
            : caps.simd                 ? "app-simd.wasm"
            :                             "app-baseline.wasm";
```

> 💡 **Maintaining several build variants has a cost.** Ask one question first: **have I actually tested the path without SIMD?** A fallback path that has never been executed is the same as having no fallback path — **except you find out later.**

---

## 7. Runtime Security: The Attack Surface "Wasm Is Safe" Covers Up

**Chapter 3 said "it's safe because it's Wasm" is not a sentence you can put in a security assessment. This section expands that.**

### 7-1 Three layers of attack surface; only the first is protected

```
① The module cannot harm the host    ← ✅ Wasm protects this layer well
                                         (type system + validator + sandbox)
② Memory safety inside the module    ← ❌ No protection at all
                                         (no ASLR/NX/canary, see Chapter 2)
③ Vulnerabilities in the runtime      ← ❌ The layer discussed least of all
   implementation itself
```

**Layer ③ deserves its own mention**: a Wasm runtime is a large piece of complex software written in C++/Rust — **it has a JIT, signal handlers and memory mapping management**, and historically those are exactly where vulnerabilities cluster. Wasmtime, V8's Wasm implementation and other runtimes have all issued security advisories. **"It runs inside the Wasm sandbox" lowers the risk; it does not eliminate it.**

**Practical countermeasures**:

| Scenario | Countermeasure |
|---|---|
| Browser | Rely on the browser's own update mechanism (this layer isn't yours to manage, and shouldn't be) |
| **Running untrusted modules on the backend** | **The runtime must track upstream updates**; and **do not rely on the Wasm sandbox alone** — wrap another layer of OS-level isolation around it (container / seccomp / a separate process) |
| Multi-tenancy | Bound each instance's memory and execution time (fuel/metering); **don't let one tenant's infinite loop drag the whole process down** |

> **Note how the last one echoes Appendix L**: FluffOS's Wasm build **has no eval limit**, so "an infinite LPC loop freezes the whole tab." **In a browser that is a UX problem; on a multi-tenant backend it is a DoS.**

### 7-2 Supply chain: the malicious module with a beautiful commit history

**Chapter 9 mentioned this, and it is worth expanding**: static hosting's "the code is locked in Git" sounds secure, **but if your build pipeline pulls in a poisoned package, the resulting `.wasm` is itself malicious — and it has an equally clean commit history.**

```bash
# Minimum supply chain discipline
cargo audit                    # known vulnerabilities
cargo deny check               # licences, sources, duplicate dependencies
cargo vet                      # dependency review records
# C/C++: pin third-party library versions and build them yourself; don't use
#        precompiled .a files of unknown provenance
```

**Plus two that are Wasm-specific**:

1. **Run `wasm-objdump -x` on the resulting `.wasm` and inspect the import list.** **Whatever capabilities the module requests, that list is its attack surface** (capability-based security, Chapters 1 and 7). **An image processing module suddenly importing network-related host functions is a red flag.**
2. **Reproducible builds**: the same source compiled in CI should produce a `.wasm` with a stable hash. **If you can achieve that, the community can verify "this binary really was compiled from that source"** — which is exactly the remedy for Chapter 9's "auditable ≠ audited."

---

## 8. Observability: What You Have in Hand When Production Breaks

**This is the production version of Chapter 3's "Wall 8: debugging is hard."**

```
What you did in release        →  What you lost           →  How to get it back
──────────────────────────────────────────────────────────────────────────────
strip = true                   →  function names          →  ★ keep a symbol-bearing build
--strip-debug                  →  DWARF                   →  store it in a symbol server/artifact
panic = "abort"                →  panic messages, stacks  →  build your own error codes
panic_immediate_abort          →  even the error codes    →  use only when you're sure
```

**A minimum viable production error report**:

```javascript
window.addEventListener("error", (e) => {
  if (e.error instanceof WebAssembly.RuntimeError) {
    report({
      kind: "wasm_trap",
      message: e.error.message,          // "memory access out of bounds" and the like
      stack: e.error.stack,              // contains wasm-function[N] — meaningless without symbols
      build: __BUILD_HASH__,             // ★ maps to the symbol-bearing build you kept
      caps: { simd: ..., threads: ..., isolated: self.crossOriginIsolated },
      memPages: wasm.memory.buffer.byteLength / 65536,   // did it hit the ceiling?
    });
  }
});
```

**The three fields most worth reporting** (they correspond to the book's three commonest production failures):

| Field | The failure it corresponds to |
|---|---|
| `memPages` | **Hitting the memory ceiling** (Chapter 8) — most common on mobile |
| `caps.isolated` / `caps.threads` | **A multithreaded build running on a non-isolated page** (Chapter 5) |
| `build` | **The user received an old version** (Service Worker cache, Appendix C troubleshooting) |

> 💡 A Word to the Wise
> **A system's maturity is measured not by how elegant it is when things go well but by how many clues it leaves when things go wrong.** Wasm's entire toolchain encourages you to throw the clues away — strip the symbols to save size, abort the panics to save size, turn off the assertions to save size — **and every one of those trades "some 3 a.m. in the future" for a few tens of kilobytes today.** That trade is not necessarily a bad one, but it must be **a decision made explicitly**, not a side effect of copy-pasting somebody's `Cargo.toml`. **The minimum discipline is one line: whatever you strip, keep an unstripped build that corresponds byte-for-byte to the release.** That artifact is worthless most days; on the day something breaks it is your only evidence.

---

## 9. The Complete Pre-Launch Checklist (consolidated)

> This checklist consolidates Appendix C (deployment), Appendix N (size and speed) and this appendix (testing and security).

```
【Correctness】
□ Native unit tests pass (they should cover 80% of the logic)
□ wasm-pack test --node passes
□ wasm-pack test --headless --chrome and --firefox both pass
□ Parser-class code has been fuzzed
□ A -fsanitize=address test build has been run through once

【Size】(Appendix N)
□ Section budget reviewed with wasm-objdump -h (if Data dominates, cut data first)
□ wasm-opt -Oz --converge has been run
□ twiggy top / dominators shows no unexpected culprit
□ CI has a size budget gate

【Performance】(Appendix N)
□ Measured separately: compilation / instantiation / runtime initialization
□ The cross-origin isolation state was consistent while measuring (or the timer is coarsened)
□ No fine-grained boundary calls on the hot path
□ Large block moves use memcpy rather than a byte-by-byte loop

【Deployment】(Appendix C)
□ Content-Type: application/wasm, Content-Encoding: br
□ Content-hashed filenames (a stable URL → the code cache)
□ CSP includes 'wasm-unsafe-eval' (if the site has a CSP)
□ .nojekyll, relative paths, await init()
□ Confirmed whether a backend that needs no SharedArrayBuffer is available

【Security】(Chapter 9 + this appendix)
□ strings has scanned the binary and found no keys  ★ most important
□ wasm-objdump -x reviewed the import list; no unexpected capability requests
□ cargo audit / cargo deny pass
□ When running untrusted modules on the backend: the runtime is updated and
  OS-level isolation wraps it
□ Memory and execution time quotas are in place

【Observability】
□ A symbol-bearing build corresponding byte-for-byte to the release has been kept
□ Production reports WebAssembly.RuntimeError, including the build hash and memPages
□ The fallback paths (no SIMD / no threads) have actually been executed, not merely written
```

---

## Appendix: Cross-Reference Index to the Main Text

| Topic | This appendix | Background in the main text |
|---|---|---|
| Test layering | §1–3 | Chapter 3 Wall 8 |
| Why sanitizers matter especially on Wasm | §3 | **Chapter 2 Scenario 1 ⚠️** (no ASLR/canaries inside the sandbox) |
| Fuzzing | §4 | Appendix E case 50 |
| CI's size and secret gates | §5 | Appendix N, Chapter 9 |
| Cross-engine differences | §6 | Chapter 8, Appendix N §15 |
| The runtime's own attack surface | §7-1 | Chapter 3 Scenario 1 ("it's safe because it's Wasm" is not a sentence for a report) |
| Supply chain | §7-2 | Chapter 9 Scenario 4 ⚠️ |
| Observability | §8 | Chapter 3 Wall 8, Chapter 12 (who fixes it in three years) |

---
