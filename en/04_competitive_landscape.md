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
