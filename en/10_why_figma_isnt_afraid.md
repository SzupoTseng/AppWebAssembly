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
