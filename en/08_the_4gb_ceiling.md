# Chapter 8: The 4 GB Ceiling — File Size, App Size, and Four Ways Around It

> **"What's Wasm's file size limit? App size limit?"**
> Those two questions sound like the same thing and are in fact two entirely independent ceilings: **one decided by how large a module the engine can compile, the other by how much memory the virtual machine can address.** Conflating them is where every large Wasm project comes off the rails at architecture review.

## Scenario 1: Two ceilings, four numbers

**Background.** Get the four numbers straight first; every architectural decision below is derived from this table.

### Ceiling one: how large the `.wasm` file itself can be

| Environment | Hard limit | Practical ceiling | The nature of the limit |
|---|---|---|---|
| **Browser** | Typically on the order of 1–2 GB | **Strongly recommended under 10–30 MB** | Streaming compilation must build a large compiler state in memory; and download time eats your first paint directly |
| **Backend runtime** (Wasmtime / WasmEdge) | No clear limit; bounded by physical memory | Hundreds of MB to 1 GB+ all workable | With enough memory you can pack neural-network weights straight into the module |

**Why the browser's practical ceiling is so far below the hard limit.** An oversized file stacks three costs: network download time lengthens, parsing hundreds of MB of Wasm spikes a mobile CPU to full and heats the device, and time-to-first-paint (and every Core Web Vital with it) degrades. **This is an experience problem, not a capability problem** — and it is harder to route around than a capability problem.

### Ceiling two: how large the runtime's linear memory can be

| Addressing mode | Hard limit | The browser's real interception | Status |
|---|---|---|---|
| **wasm32** (today's overwhelming default) | **Welded to 4 GiB** (2³² bytes) | Chrome typically throws OOM and kills the tab at **2–3 GiB** on protective grounds | Universally supported |
| **wasm64** (Memory64, **now in the Wasm 3.0 core specification**) | Theoretically 2⁶⁴ (16 EiB class) | Bounded by the host OS and cgroup quotas | Standardized, **but with a performance cost** |

**wasm32's 4 GiB is mathematics, not an implementation choice**: addresses are 32-bit pointers, `2³² = 4,294,967,296` bytes. There is no way around that line.

**The direct consequence for industrial cases**: **FFmpeg.wasm handling video, and v86 running Linux, cannot by default process or load a single file larger than 2–3 GB** — because the file must first be read whole into that linear memory (Chapter 7's MEMFS).

**Memory64's hidden cost** (the passage marketing material never mentions; the fuse was laid in Chapter 2):

```
wasm32's free bounds checking:
  the engine reserves 8 GiB of virtual address space (4 GiB addressable + guard regions)
  → a 32-bit offset mathematically cannot exceed the reservation
  → out of bounds triggers SIGSEGV via the MMU; the engine catches and turns it into a trap
  → bounds-check instructions on the hot path: 0

And wasm64?
  you cannot reserve 2⁶⁴ of virtual address space per memory
  → the guard-page trick fails
  → you must fall back to "explicit compare and branch before every access"
  → performance regression: from a few percent to double digits depending on the benchmark
```

**So the correct mental model is: below 4 GiB you enjoy safety subsidized by hardware; past that line, safety starts charging you.** Which yields an architectural principle directly — **if chunked streaming (Scenario 2) or multiple memories (Scenario 4) can solve it under 4 GiB, don't rush to wasm64.**

> ⚠️ Authenticity Caveat
> "wasm64's hard limit is 16 EB" is mathematically correct and practically meaningless — no host provides memory at that magnitude. Two numbers matter more: **(a)** browsers' actual per-memory limit has historically varied between 2 and 4 GiB by version and platform, so **do not treat 4 GiB as available budget**; **(b)** although Memory64 is now in the **Wasm 3.0** core specification, **its performance varies significantly across engines — measure in your target environment before adopting it.**
>
> **One more easily confused semantic**: `memory.grow` **does not trap on failure; it returns `-1`** (and on success returns the page count before growth). This means **memory exhaustion is a return value you must check, not an exception that blows up on its own** — and most C code that treats `malloc` failure as "won't happen" will quietly write into memory that doesn't exist here, and only trap on the next access. **The out-of-bounds error you are looking at is often that unchecked grow failure several hundred lines earlier.**

> 💡 A Word to the Wise
> **Every "free" system property rests on a physical precondition you didn't notice, and the bill arrives the moment you cross it.** Wasm's bounds checking is free below 4 GiB because a 64-bit host's virtual address space is cheap enough to waste wholesale; ask for 64-bit addressing and that precondition disappears, so what was free starts costing. The pattern recurs throughout systems engineering: allocating small objects is free (there is a slab allocator) until your objects get big; caching is free (the working set fits in L3) until your data gets big; synchronization is free (there is one thread) until you add a second. **So the most valuable single item of engineering intuition is knowing what precondition makes each "it's fast anyway" thing fast** — because growth always breaks the precondition before it reveals the cost.

## Scenario 2: Escape route one — OPFS chunked streaming (the sliding window)

**Background.** The most important and most underrated of the four. Its core idea is to **refuse to read the whole file into memory.**

**The method.** Do not read a 10 GB file into Wasm memory at once. Instead use OPFS's `FileSystemSyncAccessHandle` to `read(buffer, { at: offset })` — keep only a 50 MB **sliding window cache** inside Wasm and, like watching a tape, reach out with a direct pointer for whichever segment you need.

**Result: 50 MB of memory, streaming smoothly through a 100 GB file.**

```rust
// Skeleton: random reads through a synchronous handle inside a Worker
const WINDOW: usize = 50 * 1024 * 1024;   // 50 MB sliding window

struct ChunkedReader {
    handle: FileSystemSyncAccessHandle,   // from OPFS
    window: Vec<u8>,                      // the only resident memory
    window_start: u64,                    // file offset the window currently covers
    window_len: usize,
    file_size: u64,
}

impl ChunkedReader {
    /// Read any position; disk I/O happens only when you step outside the window
    fn read_at(&mut self, offset: u64, len: usize) -> &[u8] {
        let in_window = offset >= self.window_start
            && offset + len as u64 <= self.window_start + self.window_len as u64;
        if !in_window {
            // Reposition the window aligned to a chunk boundary, so reading one byte
            // does not force a whole-window reload
            self.window_start = (offset / CHUNK) * CHUNK;
            self.window_len = self.handle
                .read_at(&mut self.window, self.window_start);   // ← synchronous pread
        }
        let local = (offset - self.window_start) as usize;
        &self.window[local .. local + len]
    }
}
```

**Four implementation points** (they decide whether this is usable or merely slow):

1. **Align the window.** Align the offset to a 1 MB or 4 MB boundary before reading, so reading a single byte does not trigger a whole-window reload.
2. **Consider the access pattern.** Sequential scans (video decoding) want a large window plus read-ahead; random jumps (database indexes) want a small window plus an LRU of several windows.
3. **It must be in a Worker** (the specification restriction on `createSyncAccessHandle`, Chapter 7).
4. **Remote files use the same logic via HTTP Range Requests** — replace `handle.read_at()` with `fetch(url, {headers: {Range: 'bytes=...'}})` and the architecture is identical. **That is exactly how DuckDB-Wasm queries remote Parquet** (Chapter 6).

**The power of this move is that it converts a "memory ceiling" problem into an "I/O bandwidth" problem** — and the latter can be softened with read-ahead, caching and compression, while the former is a wall.

## Scenario 3: Escape route two — multi-module memory isolation (4 GB × N)

**Background.** If a single Wasm instance tops out at 4 GiB, open a lot of them.

**The method.** Start several independent Web Workers in the browser, **each loading its own separate Wasm runtime instance.** Because every virtual machine has its own 4 GiB linear memory, you can use the main thread as a data bus, distribute work across Workers, and **multiply the app's total compute and memory ceiling to 4 GiB × N.**

```
                Main thread (scheduling only, no computation)
                        │
        ┌───────────────┼───────────────┐
        ▼               ▼               ▼
   Worker 1         Worker 2        Worker 3
   Wasm instance A  Wasm instance B Wasm instance C
   4 GiB linear mem 4 GiB linear mem 4 GiB linear mem
   (segment 1)      (segment 2)     (segment 3)
        │               │               │
        └───────────────┴───────────────┘
              results returned as transferables, zero copy
```

**This is a completely different thing from "Wasm multithreading"** (the most commonly confused point):

| | Multi-instance isolation (this section) | Wasm threads (`SharedArrayBuffer`) |
|---|---|---|
| Memory | 4 GiB per instance, independent | **One shared** linear memory; the total is still capped at 4 GiB |
| Communication | `postMessage` plus transferables (copy or move ownership) | Direct reads/writes of the same memory plus atomics |
| Needs cross-origin isolation | **❌ No** | **✅ Yes, COOP/COEP** |
| Suited to | Partitionable work (chunked processing, parallel rendering, independent queries) | Algorithms needing fine-grained shared state (physics simulation, graph traversal) |
| On GitHub Pages | **Works directly** | Needs `coi-serviceworker` |

**That table has a very practical corollary**: **if your task is data-partitionable (and the vast majority of batch processing is), use multi-instance isolation — it needs no cross-origin isolation, doesn't break your third-party resources, and breaks the 4 GiB ceiling as a bonus.** Plenty of teams fight COOP/COEP for two weeks before discovering they never needed shared memory at all.

## Scenario 4: Escape route three — multiple memories (new in Wasm 3.0)

**Background.** This road entered the core specification only in September 2025, and it attacks the 4 GiB problem head-on.

**The method.** **Wasm 3.0's multiple memories let one module declare and access several linear memories, and move data directly between them.**

```wat
(module
  (memory $code 16)          ;; memory 0: code working area
  (memory $assets 1024)      ;; memory 1: assets / bulk data
  (memory $scratch 64)       ;; memory 2: scratch space

  (func $copy_in
    ;; memory.copy can cross memories: destination index, source index
    (memory.copy $scratch $assets
      (i32.const 0) (i32.const 4096) (i32.const 65536)))
  ;; loads and stores can also name a memory
  (func $peek (result i32)
    (i32.load $assets (i32.const 1024))))
```

**Its relationship to the previous two routes is worth drawing clearly:**

| | Multiple memories (this section) | Multi-module isolation (Scenario 3) | Memory64 |
|---|---|---|---|
| Wasm instances | **One** | N | One |
| Memories | **Several** | One per instance | One (very large) |
| Data movement cost | **`memory.copy` across memories, done at engine level** | `postMessage` across threads | No movement needed |
| Free guard-page bounds checking | **✅ each is still wasm32, fully preserved** | ✅ | **❌ lost** |
| Needs a Worker | ❌ | ✅ | ❌ |
| Needs cross-origin isolation | ❌ | ❌ | ❌ |
| Suited to | **Single-threaded, partitionable large applications** | Partitionable batch work | Genuinely needing one huge address space |

**The elegant part is the fourth row**: because each memory **remains 32-bit addressed**, the whole "reserve virtual address space plus guard pages equals free bounds checking" mechanism is **fully preserved.** In other words —

> **Multiple memories break the single-4 GiB limit without giving up free bounds checking.**
> That is precisely the trade Memory64 cannot make, and why, wherever the data partitions naturally (code area / asset area / scratch, one per tenant, hot/cold separation), **multiple memories almost always beat Memory64.**

**The practical caveat**: **toolchain support lags the specification.** Most C/C++/Rust toolchains still assume a single memory by default; using this today usually means hand-written WAT or a newer toolchain with the right attributes. **Specification first, toolchain later — the normal state of every new feature, and why "spec status" and "can I use it today" must be asked separately.**

## Scenario 5: Escape route four — enable Wasm GC and give the runtime back to the browser

**Background.** The first three all attack the **memory** ceiling. This one attacks the other ceiling Scenario 1 established — **file size.**

**The problem.** If you compile a high-level language like Java, Kotlin, Dart or C# to Wasm, the traditional approach packs the language's entire garbage collector and standard library into the `.wasm`, inflating it to several megabytes or more.

**The method.** Enable **Wasm GC** (in the core specification since Wasm 3.0, September 2025) and let Wasm use the browser's native, heavily optimized garbage collector (V8's Orinoco, SpiderMonkey's GC) instead of carrying its own.

**What Wasm GC adds at the specification level** (worth detailing, as it is the newest piece here):

- **Heap types**: `struct`, `array`, and `i31` (a small-integer optimization that fits inside a pointer).
- **Typed references**: `(ref $MyStruct)`, `(ref null $MyArray)` — for the first time Wasm can point at *a structured object* rather than merely an `i32` offset.
- **Subtyping and `br_on_cast`**: so object-oriented languages' inheritance and dynamic casts can be expressed.

```wat
;; Wasm GC: real objects, managed by the host GC, not occupying linear memory
(type $Point (struct (field $x f64) (field $y f64)))
(func $make (result (ref $Point))
  (struct.new $Point (f64.const 1.0) (f64.const 2.0)))
```

**Benefits and costs:**

| | Benefit | Cost |
|---|---|---|
| Size | **Substantial reduction** (no need to pack a GC and part of the runtime) | — |
| Performance | Uses a heavily optimized host GC, usually better than a bundled simple one | You lose control of collection timing — **GC pauses are back** |
| Applies to | Kotlin/Wasm, Dart (Flutter Web), Java, Scheme, etc. | **Nearly useless for Rust/C/C++** — their data already lives in linear memory |
| Support | **In the Wasm 3.0 core specification**; mainstream browsers support it | Backend runtimes and toolchains lag the browsers |

> ⚠️ Authenticity Caveat
> A common claim: "enabling Wasm GC cuts `.wasm` size by over 80%." **The direction is right, but that number holds only for languages that would otherwise pack an entire language runtime** (Java, Kotlin, Dart), and the actual reduction depends on how much was being packed. **For Rust, C and C++, enabling Wasm GC yields essentially no size benefit** — their objects already live in linear memory and there is no GC to remove. Applying this advice indiscriminately across languages is a very common misreading.

**Before you touch any compiler flag, do rule zero** — its return usually exceeds everything else combined:

> **★ Rule zero: cut data before you cut code.**
> More than half of a large C/C++ project's Wasm artefact is often the **data tables** it drags in, and 90% of those tables you never use.
> **A real example** (Appendix L): FluffOS's Wasm build keeps only ICU's break-iterator rules, cutting **data from about 30 MB to about 780 KB (−97%), while the driver's entire code body is 3.6 MB.**
> **So the first action is not to enable a flag; it is `wasm-objdump -h` to look at your section budget** — if Data is half the file, squeezing another 10% out of Code buys you 5% of the total.

**Once you have checked the section budget, then the toolchain applies**: `wasm-opt -Oz` → compile-time settings (`lto` / `codegen-units=1` / `panic="abort"` / `strip`) → `twiggy` diagnosis → dead-code elimination → Brotli transport → module splitting.

> **That is only the list. What each item actually removes, at what cost, and the things not on the list — Rust's formatting machinery hiding inside `panic!`, the "generic thin shell" cure for monomorphization blowup, what each `wasm-opt` pass does, how Compression Dictionary Transport makes a new release ship as tens of KB — are all in Appendix N, Part One, with an item-by-item ROI table.**

> 🔍 Deeper Commentary — the four escape routes are one idea projected four ways
> Put all four side by side and they solve the same problem: **"all of it at once" is the common root cause of every resource ceiling.** Chunked streaming says "don't bring all the data in at once"; multi-module isolation says "don't fit it all in one instance"; multiple memories says "don't cram it all into one address space"; module splitting and lazy loading say "don't download all the code at once." **All four convert a *total* problem into a *partitioning* problem along a time or space axis** — and partitioning problems are always easier than totals, because you can flatten them with read-ahead, caching, priority and background loading. The principle generalizes enormously: database pagination, adaptive video streaming (HLS/DASH), virtual scrolling lists in the front end, paged KV caches in LLM serving (PagedAttention), an operating system's virtual memory — **all the same thought: don't ask "how much do I have," ask "which slice do I need right now?"** The next time you hit any kind of capacity ceiling, the first question is not "how do I raise the limit" but — **do I genuinely need all of it at the same instant?** Nine times in ten the answer is no, and the tenth is when it becomes worth buying a bigger machine.

## Chapter Summary

- **Two independent ceilings**: `.wasm` **file size** (hard limit 1–2 GB class in browsers, **practically 10–30 MB**; effectively unlimited on the backend) and **linear memory size** (wasm32 is **welded to 4 GiB**, and browsers commonly OOM at 2–3 GiB).
- **wasm64 is not free**: once addresses are 64-bit, the "8 GiB virtual reservation plus guard pages" free bounds check stops working and you fall back to explicit comparison, with a real performance regression. **Below 4 GiB you are enjoying hardware-subsidized safety.**
- **Escape one: OPFS chunked streaming (sliding window)** — random reads with `createSyncAccessHandle`'s `read(buffer, {at})` let 50 MB of memory stream through a 100 GB file. Remote files use the same logic through HTTP Range Requests.
- **Escape two: multi-module memory isolation** — N Workers × N Wasm instances = 4 GiB × N. **This is a completely different thing from Wasm threads**: multi-instance **needs no COOP/COEP** and works directly on GitHub Pages. **When the task partitions, prefer this.**
- **Escape three: multiple memories** (new in Wasm 3.0) — several linear memories per module, with `memory.copy` moving data between them. **The greatest advantage is that each remains wasm32, so the free guard-page bounds check is fully preserved** — exactly the trade Memory64 cannot make. But **toolchain support lags the specification** (Scenario 4).
- **Escape four: Wasm GC** (in the Wasm 3.0 core specification) — hand garbage collection back to the host engine; substantial size benefit, **but only for languages that would otherwise pack a runtime (Java/Kotlin/Dart); nearly useless for Rust/C/C++** (see the ⚠️ in Scenario 5).
- `memory.grow` **returns `-1` on failure rather than trapping** — memory exhaustion is a return value you must check, and **the out-of-bounds error you see is often that unchecked grow failure several hundred lines earlier.**
- Size reduction's **rule zero is "cut data before code"** — run `wasm-objdump -h` on your section budget first; squeezing Code is pointless when Data is half the file. Example in Appendix L (ICU 30 MB → 780 KB). **The full arsenal and ROI table are in Appendix N, Part One.**
- The four escape routes are one idea projected four ways: **convert a "total" problem into a "partitioning along time or space" problem** — when you hit any capacity ceiling, first ask "do I genuinely need all of it at the same instant?" (see the 🔍 in Scenario 5).

Part II ends here. The machine is built, running, remembering things, and past its capacity limits. **Now to face the question that has hung over everything from the start: this machine has been downloaded, in full, onto every stranger's computer.** Turn to Chapter 9.
