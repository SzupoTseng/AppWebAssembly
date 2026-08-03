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
