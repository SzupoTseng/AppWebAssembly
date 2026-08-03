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
