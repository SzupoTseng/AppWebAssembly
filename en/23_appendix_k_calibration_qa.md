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
