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
