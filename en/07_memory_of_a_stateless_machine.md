# Chapter 7: The Memory of a Stateless Machine — MEMFS, IDBFS, OPFS and WASI

> WebAssembly is itself a **stateless** sandboxed virtual machine. It has no disk and no native database. By default it has only one flat block of memory allocated by the host, and **the moment the page reloads, everything inside it evaporates like foam.**
> The way it solves this comes down to two words: **delegated capability.**

## Scenario 1: Layer one — MEMFS, the fake Linux living in memory

**Background.** When you compile a C/C++ project (FFmpeg, SQLite, GNU tar) to Wasm, the code is full of this sort of thing:

```c
FILE *f = fopen("input.mp4", "rb");
fread(buf, 1, size, f);
fclose(f);
```

Wasm has no `fopen`. It does not even have the concept of a system call. So how does that line run?

**The answer: Emscripten fabricates an entire POSIX filesystem inside linear memory.** It is called **MEMFS** (In-Memory File System), and it uses typed arrays in Wasm's linear memory to simulate the standard Linux directory structure (`/tmp`, `/home`, `/dev`), redirecting all of libc's file functions into it.

```
C code:      fopen("/work/input.mp4", "rb")
                    ↓ Emscripten's libc implementation
JS glue:     FS.open("/work/input.mp4", "r")
                    ↓
MEMFS:       look up a JS-object directory tree built in linear memory,
             return a file descriptor pointing at some Uint8Array
```

**A typical data flow** (FFmpeg.wasm as the example):

```javascript
// 1. Write the user's dropped file into Wasm's virtual filesystem
ffmpeg.FS('writeFile', 'input.mp4', await fetchFile(file));
// 2. Run the command line — internally, Wasm genuinely believes it is a CLI
await ffmpeg.run('-i', 'input.mp4', '-c:v', 'libx264', 'output.mp4');
// 3. Read the result back out of the virtual filesystem
const data = ffmpeg.FS('readFile', 'output.mp4');
// 4. Turn it into a Blob URL for the user to download
const url = URL.createObjectURL(new Blob([data.buffer], {type: 'video/mp4'}));
```

**MEMFS's two fatal problems:**

1. **It is ephemeral.** Close the page, reload, or exhaust memory (OOM), and the files are gone.
2. **It consumes your linear-memory budget.** A 500 MB video written into MEMFS occupies 500 MB of that 4 GB ceiling — and FFmpeg needs more on top during transcoding. **That, not any limitation of FFmpeg itself, is why FFmpeg.wasm cannot handle large files.**

**MEMFS also has a rarely mentioned positive use: bundled distribution.** Emscripten's `file_packager` can pack thousands of files into **a single `.data` image plus a `.js` loader**, mounted at a chosen path before the runtime starts. FluffOS's Wasm build distributes an entire mudlib exactly this way — **tens of thousands of LPC files in a game world become one static blob.** The cost is stated with complete honesty in the official docs: **"writes currently persist only for the page session,"** and the next step on its roadmap is precisely the two layers this section is about to cover — **mounting an IDBFS or OPFS overlay over the write paths** (Appendix L).

> **This is the best live confirmation this book can offer**: a real, complex, actively maintained project is stuck at layer one of this four-layer ladder right now, and it knows exactly which way it needs to climb.

> 💡 A Word to the Wise
> **The essence of compatibility is faithfully reconstructing the old environment's lies inside the new one.** Emscripten did not make C programs "adapt" to the browser; it did the opposite — **it made the browser pretend to be Linux**, convincingly enough that `fopen`, `ioctl`, `pthread_create` and `SDL_CreateWindow` all get fooled. That is why a twenty-year-old C++ game can run on the web with essentially no change to its core logic. The principle has a more general form in system migration: **when moving a large body of existing assets to a new platform, "modify the assets to fit the platform" costs O(number of assets), while "emulate the old environment on the platform" costs O(1).** WSL, Rosetta, Wine, Docker, the JVM — all the same move. And the price is the same too: **what you moved across is a complete set of the old world's assumptions, including the inefficiencies you could have avoided in the new one.**

## Scenario 2: Layer two — IDBFS, rewinding memory into the browser's database

**Background.** To solve MEMFS's impermanence, Emscripten provides **IDBFS** — connecting the virtual filesystem to the browser's **IndexedDB**.

**How it works:**

```javascript
// Mount: bind the virtual directory /save to IndexedDB
FS.mkdir('/save');
FS.mount(IDBFS, {}, '/save');

// Load from IndexedDB into memory (at startup)
FS.syncfs(true, err => { /* true = read from IDB into MEMFS */ });

// The C code writes files as normal
// ... fopen("/save/game.sav", "wb") ...

// Sync memory back to IndexedDB (when saving)
FS.syncfs(false, err => { /* false = write from MEMFS back to IDB */ });
```

**The crucial point is that it rewinds the whole bundle, not random access.** `syncfs` serializes the **entire** mount point into IndexedDB (or the reverse). That decides its applicable boundary:

- ✅ **Suited to**: game saves (a few hundred KB), configuration files, small JSON, user preferences. **This is exactly how retro game emulators on the web persist saves.**
- ❌ **Not suited to**: database files, large media, anything requiring random access. A 500 MB SQLite file gets moved in full on every `syncfs`.

**IndexedDB's own problems come along for the ride** as well: an asynchronous event-driven API, mediocre write throughput, browser quota limits, and being restricted or cleared in some browsers' private modes.

## Scenario 3: Layer three — OPFS, which is the actual answer

**Background.** The **Origin Private File System** has in recent years become the gold standard for Wasm storage on the front end, and it is why DuckDB-Wasm and the official SQLite-Wasm can handle multi-gigabyte databases in a browser while guaranteeing ACID.

**What it is.** The browser opens, for each origin, a **highly isolated, heavily optimized private disk area.** It does not appear in the user's file manager, needs no permission dialog, cannot be seen by other sites — and, crucially, **it has a set of low-level APIs designed for performance.**

**Two access modes, and the difference is night and day:**

```javascript
// ── Mode A: asynchronous writable stream (usable on the main thread) ────────
const root = await navigator.storage.getDirectory();
const fh = await root.getFileHandle('data.bin', { create: true });
const writable = await fh.createWritable();
await writable.write(uint8array);
await writable.close();        // every step is a Promise, with microtask scheduling overhead

// ── Mode B: synchronous access handle (★ Web Workers only) ──────────────────
// This is the performance watershed
const root = await navigator.storage.getDirectory();
const fh = await root.getFileHandle('db.sqlite', { create: true });
const handle = await fh.createSyncAccessHandle();

handle.write(buffer, { at: offset });   // ← fully synchronous, no Promise
handle.read(buffer,  { at: offset });   // ← random access, like native pread/pwrite
handle.flush();
handle.truncate(newSize);
handle.getSize();
handle.close();
```

**Why `createSyncAccessHandle()` is the key.** The storage layer of a database written in C (SQLite, DuckDB) is **synchronous** — it calls `pread(fd, buf, len, offset)` and expects the data to be in the buffer immediately. You **cannot** implement that on an API that returns Promises, unless you rewrite the entire program asynchronously — which is impossible, because it is hundreds of thousands of lines of C.

**`createSyncAccessHandle` gives Wasm a genuinely synchronous, randomly seekable file handle** — so SQLite's VFS (the storage abstraction layer SQLite designed for portability) needs only a handful of functions implemented, and the whole database runs:

```
SQLite core (unmodified C code)
        ↓ calls the VFS interface: xOpen / xRead / xWrite / xTruncate / xSync / xLock
The OPFS VFS implementation in the Emscripten glue layer
        ↓
FileSystemSyncAccessHandle.read/write/flush
        ↓
The browser's private disk area (genuinely persisted)
```

**Costs and limits** (specification-level, not implementation defects):

1. **`createSyncAccessHandle` can only be called inside a Web Worker.** The main thread is forbidden, because synchronous I/O would block the UI. That means **your entire Wasm database engine must move into a Worker**, with the main thread communicating only through `postMessage`.
2. **An exclusive lock by default.** Only one sync access handle per file at a time. Multiple tabs opening the same application contend for the lock — you need your own coordination (the Web Locks API or a `BroadcastChannel`).
   **But this has since been relaxed**: newer browsers support `createSyncAccessHandle({ mode: "readwrite-unsafe" })`, permitting **multiple handles on the same file simultaneously.** The `unsafe` in the name is honest — **it hands responsibility for concurrency control entirely back to you**, and the browser stops arbitrating. Ask yourself before using it: does my engine have its own locking?
3. **Quotas.** Browsers impose per-origin storage quotas (usually tied to available disk space; query with `navigator.storage.estimate()`) and may **evict** data not marked persistent under disk pressure. To avoid being cleared, call `navigator.storage.persist()`.
4. **The user cannot see it.** That is both an advantage (it doesn't clutter their files) and a drawback (they cannot back it up themselves, so you must provide an export function).

### ★ A fork that will change your deployment decision: SQLite-Wasm's two OPFS VFS implementations

**This is the most practically valuable passage in the chapter, and it appears in almost no introductory article.** Official SQLite-Wasm does not provide one OPFS backend; it provides **two**, and their deployment costs differ enormously:

| | **`opfs` VFS** (first generation) | **`opfs-sahpool` VFS** (SAH = SyncAccessHandle) |
|---|---|---|
| Mechanism | An asynchronous proxy between the main thread and OPFS, made synchronous with `Atomics.wait` | **Holds a pool of pre-opened sync access handles**, reading and writing synchronously inside a Worker |
| **Needs `SharedArrayBuffer`** | **✅ Yes** | **❌ No** |
| **Needs COOP/COEP cross-origin isolation** | **✅ Yes** | **❌ No** |
| Performance | Usable | **Listed in the official documentation as the highest of all OPFS options** |
| Multiple connections | Supported | **Does not support multiple simultaneous connections** |
| Availability | Earlier | Broadly available in mainstream browsers since around March 2023 |

**Translated into one sentence:**

> **If you need a persistent SQLite somewhere like GitHub Pages where you cannot set HTTP headers, choose `opfs-sahpool` — it needs no cross-origin isolation and it is also the fastest one.**
> The official recommendation says exactly this: **clients that value performance over concurrency, or that cannot set COOP/COEP response headers, should use `opfs-sahpool`.**

**This routes around Chapter 5's "number one obstacle" entirely**, and the only price is "no multiple connections" — which, for the overwhelming majority of single-user frontend applications, is not a price at all.

> 💡 **There is a more general lesson here**: when you find yourself about to pay a heavy architectural cost for a platform limitation (here, the wholesale breakage of third-party resources caused by COOP/COEP), **first confirm whether the library you depend on offers a path that doesn't need that limitation.** Many teams have wrestled with `SharedArrayBuffer` and isolation for two weeks when the thing they wanted had a backend that never required it.

> ⚠️ Authenticity Caveat
> Claims like "Sqlite-Wasm's read/write throughput is 2–4× IndexedDB's" and "OPFS lets Wasm read and write at near-native disk speed" point in the right direction, but **the specific multiples depend heavily on workload and browser version.** Only three qualitative conclusions are reliable: **(a)** `createSyncAccessHandle` eliminates asynchronous scheduling overhead, so the improvement is most pronounced for "many small random I/Os" (precisely a database's access pattern); **(b)** for "write one large block at a time," async and sync differ little; **(c)** OPFS performance is strongly implementation-dependent, and Safari, Firefox and Chrome have shown clear differences. **Measure on your target browsers; do not copy anyone's multiple.**

**The full four-layer comparison:**

| | MEMFS | IDBFS | OPFS (async) | OPFS (sync handle) |
|---|---|---|---|---|
| Persistent | ❌ | ✅ | ✅ | ✅ |
| Random access | ✅ (in memory) | ❌ (whole-bundle rewind) | Limited | **✅ genuine pread/pwrite** |
| Consumes linear memory | **✅ (fatal)** | During sync | ❌ | ❌ |
| Usable on the main thread | ✅ | ✅ | ✅ | **❌ Workers only** |
| Performance | Memory speed | Poor | Medium | **Near native disk** |
| For | Temporary intermediates | Game saves, settings | Ordinary files | **Databases, large files, streaming** |

> 🔍 Deeper Commentary — OPFS is what actually turned Wasm from a library into an application platform
> This section deserves pulling out separately, because it marks a watershed. **Before OPFS, Wasm in the browser was essentially a pure-function accelerator**: you feed it input, it produces output, and then it deserves to be forgotten. Everything requiring state — the user's project files, databases, caches — had to detour back through JavaScript and be stored via IndexedDB's asynchronous API. That seam meant "move desktop applications to the browser" was always one mile short: **you could compile SQLite in, but you had nothing for it to use as a filesystem.** What `createSyncAccessHandle` closed was exactly that mile, and the way it closed it is interesting — **it did not give Wasm a new capability; it gave Wasm an interface shaped the way the C world expects.** Synchronous, seekable, lockable, flushable. Those four properties are not there because they are best, but because **every piece of storage software written in the last fifty years was written to that shape.** So the real insight is: **for a new platform to receive existing software assets, what matters is not how powerful a capability you offer but whether you offer the interface shape the other side expects.** That explains why OPFS chose an API design that looks "insufficiently modern" (synchronous, blocking) — because a modern asynchronous design would have locked the entire C/C++ ecosystem out. **When you design a platform's API, the most important question is not "what design is most elegant" but "what shape were the assets I want to receive written to?"**

## Scenario 4: Layer four — WASI on the backend, and the complete form of delegated capability

**Background.** When Wasm breaks out to the backend (Wasmtime, WasmEdge), it is no longer constrained by the browser sandbox but faces the problem of OS-level disk access. And its answer is fundamentally the same as on the front end.

**What capability-based security actually means:**

- On traditional Linux, a compromised Node.js process can read `/etc/passwd` directly — because it has **all** of that user's privileges.
- A Wasm runtime is by default **completely empty-handed**: it has no permission to call `open()`, because that import was never provided.

```bash
# At launch, explicitly grant the host's ./my_storage as /sandbox in the module's view
wasmtime run --dir=./my_storage::/sandbox my_server.wasm
```

If the module tries to reach `/sandbox/../etc/passwd`, the runtime intercepts it at the capability boundary and terminates — **not by relying on filesystem permissions and luck, but through the structural guarantee that the directory handle you hold cannot walk upward** (technically this corresponds to POSIX `openat` semantics and path-resolution restrictions).

**WASI's two generations** (distinguish them carefully when selecting):

| | `wasi_snapshot_preview1` | WASI 0.2 (Preview 2) |
|---|---|---|
| Model | POSIX-style file descriptors | **Component Model** plus WIT interface definitions |
| Interface | One large flat bag of functions | Split into `wasi:filesystem`, `wasi:io`, `wasi:sockets`, `wasi:http`, `wasi:clocks`… |
| Ecosystem | **Mature**: Rust's `wasm32-wasip1`, TinyGo and most toolchains support it | Evolving; toolchains catching up |
| Composability | Poor (monolithic interface) | **Good** (you can grant a component `wasi:clocks` and no filesystem) |

**The Component Model is the end of this road.** It lets Wasm modules communicate with **high-level types** (strings, records, variants, streams) instead of only `i32` pointers — in other words, it attempts to solve Chapter 2's "boundary toll booth" at the root. **WIT (Wasm Interface Types)** is its interface description language:

```wit
// A WIT interface definition: like an IDL, but bindings for each language
// can be generated at compile time
package example:storage@0.1.0;

interface kv {
  record entry { key: string, value: list<u8> }
  get: func(key: string) -> option<list<u8>>;
  put: func(key: string, value: list<u8>) -> result<_, string>;
  list-all: func() -> list<entry>;
}
```

**The summary of the technical idea.** Wasm solves storage through **memory mapping plus delegated capability**:

- On the **front end**, it delegates disk operations to the browser's IndexedDB or OPFS APIs;
- On the **backend**, it delegates disk operations to the WASI runtime's pre-authorized channel.

This preserves the Wasm virtual machine's sandbox isolation completely while giving it I/O throughput approaching a native C program.

> 💡 A Word to the Wise
> **The most honest thing about a system is the list of what it says it needs.** WASI's import section, a browser extension's `permissions` field, Android's manifest, Kubernetes' ServiceAccount — the value of those lists is not that they "stopped bad actors" (a genuinely malicious program will simply request everything it needs); it is that **they turn "what can this thing do" into a fact you can read in five seconds, rather than a question requiring reverse engineering.** Security audit cost drops from "prove it won't do anything bad" to "look at what it asked for." The corollary is practical: **when evaluating any third-party component, the first thing to look at is not its code but its permission list — and if that list doesn't exist, or is too long to read, you already have your answer.**

## Chapter Summary

- Wasm is itself **stateless**: one linear memory, evaporating on reload. Its solution is two words — **delegated capability.**
- **MEMFS**: an entire POSIX filesystem fabricated by Emscripten inside linear memory so `fopen()` has somewhere to go. **Ephemeral, and it consumes your 4 GB budget** — the real reason FFmpeg.wasm cannot handle large files. Its positive use is bundled distribution via `file_packager`.
- **IDBFS**: `FS.syncfs()` rewinds the entire mount point in and out of IndexedDB. Good for game saves and settings (hundreds of KB); **useless for databases or anything needing random access.**
- **OPFS is the real answer**, and the watershed is **`createSyncAccessHandle()`** — it hands Wasm a synchronous, randomly seekable file handle with locking and flush, so SQLite's VFS needs only a few functions to bring the whole database up. Costs: **Workers only, exclusive by default (`{mode:"readwrite-unsafe"}` relaxes it but the responsibility becomes yours), quota-limited, invisible to the user.**
- **★ The most practically valuable item**: SQLite-Wasm has **two** OPFS VFS implementations. The first-generation `opfs` needs `SharedArrayBuffer` and therefore **cross-origin isolation**; **`opfs-sahpool` needs no COOP/COEP and is the fastest option in the official documentation**, at the cost of not supporting multiple connections. **For persistent SQLite on GitHub Pages, choose the latter and Chapter 5's number-one obstacle disappears entirely.**
- The general lesson: **when you are about to pay a heavy architectural cost for a platform limitation, first check whether your dependency has a path that doesn't need it.**
- OPFS's design lesson: **for a new platform to receive existing software assets, what matters is not how powerful a capability you offer but whether you offer the interface shape the other side expects** — even when that shape (synchronous, blocking) looks insufficiently modern (see the 🔍 in Scenario 3).
- The backend's **WASI** is the same philosophy from another side: **capability-based security**, empty-handed by default, with the capability inventory written into the launch arguments. Note that **preview1 and 0.2 are two generations**, so what you write today should expect one migration.
- Front end delegates to OPFS/IndexedDB, backend delegates to WASI — **one doctrine, two hosts.**

The memory problem is solved. But one hard wall remains: **what happens when your data exceeds 4 GB, and when your module exceeds 30 MB?** Turn to Chapter 8.
