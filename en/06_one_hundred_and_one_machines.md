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
