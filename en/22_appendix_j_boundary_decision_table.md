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
