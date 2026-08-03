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
