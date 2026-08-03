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
