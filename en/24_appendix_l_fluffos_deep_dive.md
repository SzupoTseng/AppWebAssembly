# Appendix L: A Deep-Water Case — FluffOS × Wasm, Moving an Entire MUD Server onto a Static Page

> **This is the only case in the book that deserves a chapter of its own, because it is three things at once:**
> **One, it is the real version of two 🔴 illustrative constructions from Appendix E (case 58 Minestom-Wasm and case 60 Micro-Apache-Wasm)** — and it goes further than either.
> **Two, it runs into every wall the book's twelve chapters describe, all at once**, and its handling of each one is on the public engineering record.
> **Three, it is the cleanest living specimen of the book's central thesis**: **the code has been 100% downloadable, self-hostable and modifiable for thirty years, and its value has never lost a single ounce because of it.**
>
> **Authenticity tier: 🟢 verifiable.** Every technical detail in this appendix comes from the official FluffOS repository's `README.md` and `src/wasm/README.md`, plus the `fluffos/mudlibs` repository. **The only thing that moves over time is the inventory count and the proportion "already WASM-ified"** — treat the repository's current state as authoritative.

---

## 1. What It Is

### FluffOS: an LPMud driver still under maintenance

**FluffOS** is a **modern fork of MudOS** — an actively maintained **LPMUD driver** (an LPC interpreter plus game engine) written in C++. Its job is not "a game" but **a complete game server runtime**:

```
The FluffOS driver (C++)
├── LPC compiler     ← compiles the mudlib's .c sources to bytecode at runtime
├── Virtual machine  ← executes that bytecode
├── efuns            ← the built-in function library (strings, arrays, files, network, time…)
├── Scheduling core  ← heartbeat, call_out (timers), reset
└── Network layer    ← telnet / WebSocket / TLS
```

It stays backward compatible with existing MudOS mudlibs, has accumulated over a decade of performance optimization, and additionally supports **WebSocket, TLS, MySQL/PostgreSQL/SQLite3 integration** and **UTF-8 EGS-aware LPC string operations** (range operators handle emoji and other Unicode characters).

**Build targets**: CMake, supporting Ubuntu, macOS, Windows (MSYS2/MinGW64) — **and WebAssembly**.

### mudlibs: a source archive of an entire era

`github.com/fluffos/mudlibs` is a **source archaeology archive of the Chinese MUD scene** — covering work from the mid-1990s through around 2015, collecting LPC games in the wuxia and xianxia genres (*Journey to the Wild West*-style titles built from Jin Yong's novels, *Journey to the West* and their many forks) along with their branches.

The repository's organization is itself a record of repair engineering:

```
archives/                       the original archive files
libs/<slug>/raw/                the untouched extracted contents (original encoding preserved)
libs/<slug>/work/               the playable version (converted to UTF-8, repairs applied)
libs/<slug>/config.fluffos      runtime configuration
libs/<slug>/README.md           player notes
libs/<slug>/NOTES.md            the repair log
scripts/                        conversion and testing tools
lib_numbering.json              a machine-readable cross-reference
```

**Inventory status** (per the repository README; the numbers move with repair progress):

| Status | Count |
|---|---|
| Repaired mudlibs | **200** (covering **158** distinct codebases) |
| **Verified playable in the browser (WASM)** | **79** |
| Boots natively, WASM packaging pending | 117 |
| Native-only by policy | 1 |
| Confirmed unable to boot | 4 |

**Licensing**: most are held as a historical community archive with no formal licence terms (one of them, *The Reborn World*, is explicitly GPLv2). The project's stated position is "**preserve them as cultural assets**," retaining the original authors' attribution.

> ⚠️ **The numbers move**: at the time of writing, the count of playable games listed by the online archive site `mudlibs.fluffos.info` did not exactly match the repository README's statistics (the former listed around ninety-odd, the latter records 79 verified WASM-playable). **Numbers of this kind change with every repair push** — treat the repository and site as you find them, since this book cites the relationship rather than the snapshot.

---

## 2. Why It Deserves Its Own Chapter

**Because it crossed a line others only cross on slides.**

Recall Appendix E's two 🔴 entries:

- **Case 60, "Micro-Apache-Wasm"**: the concept is running a tiny HTTP server in the browser, with a Service Worker intercepting requests and feeding them to Wasm. **The concept holds, but what it emulates is the stateless thing called request-response.**
- **Case 58, "Minestom-Wasm"**: the concept is running a Minecraft server in the browser. **Closer, but it needs WebRTC for anyone else to connect.**

**What FluffOS's Wasm target achieves is harder than either** — because a MUD driver is not a request handler; it is a thing with **a heartbeat, timers, persistent world state, multiple concurrent connections, and the requirement to compile user code at runtime**:

> The official README's wording is: **"The whole driver runs in a browser page (or node) — compiler, VM, efuns, telnet."**
> Compiler, virtual machine, built-in function library, telnet protocol — **all of it** in one browser tab.

And the mudlibs are distributed like this: **"Mudlibs ship as static bundles via `tools/wasm/pack-mudlib.sh`; no server required."** — **packaged as static bundles, no server needed.**

That is the ultimate version of Chapter 5's line: **the computation didn't disappear; it just changed who pays for it.**

---

## 3. Architectural Deep Dive: Five Problems That Had to Be Solved

This section is the appendix's technical core. **FluffOS's Wasm port is not "recompile and you're done"** — it had to deal with Wasm's and the browser's physical limits one by one, and every solution is worth writing down.

### Problem one: the browser cannot block, yet a server's essence is waiting

**The native driver blocks in libevent's event loop** — `while(true) { wait_for_events(); dispatch(); }`. **That is a dead end in a browser**: block the main thread and the whole tab freezes.

**Solution: hand ownership of the event loop to the host (a host-driven tick).**

```javascript
// The page drives the driver with setInterval / requestAnimationFrame
setInterval(() => {
  Module._fluffos_tick(Date.now());   // ← advance the scheduler once, handle due events, return immediately
}, 50);
```

**The key design decision**: the scheduling core (the gametick queue, maintenance events) is **shared between native and Wasm**, and the only difference is **who advances the loop**. So **heartbeat, call_out and reset — the LPC-level mechanisms — need no changes at all**: not one line of mudlib code knows it is living in a browser.

> 💡 **This is the most elegant move in the whole port**: it did not change "how time flows," only "who rings the bell."

> 🔧 **A future option worth noting**: this "hand the loop to the host" solution addresses **active scheduling**, but it does not address **passive waiting** — when LPC code wants to read something asynchronous (OPFS's async API, or a network request), the driver still has nowhere to wait. **JSPI** (Chapter 3 Wall 7, Appendix M §5) is exactly for that: it lets the engine suspend the whole Wasm stack and resume once the Promise settles.
> The significance for this project is concrete: **the roadmap item about layering an IDBFS/OPFS overlay for persistence would, after JSPI, no longer require rewriting the whole storage layer as asynchronous.** The cost is that it introduces reentrancy — **while suspended, `fluffos_tick` may be called again** — and a driver's assumption that "only one tick runs at a time" is very strong. **This is a textbook instance of "a new capability brings a new constraint."**

### Problem two: there are no sockets, yet every player is a connection

**Solution: abstract "connection" into a byte pipe (Transport).**

Every user connection owns a `Transport` — an abstract byte pipe with just four operations: `write` / `flush` / `schedule_command` / `close`. There are three implementations beneath it:

| Implementation | Target | Underneath |
|---|---|---|
| `SocketTransport` | Native | libevent |
| `WebsocketTransport` | Native | libevent |
| **`WasmConsoleTransport`** | **Browser** | **JS bridge** |

`WasmConsoleTransport`'s two directions:

```
Outbound: bytes the driver writes → Module.fluffos.onOutput(id, bytes) → the page's terminal
Inbound:  the command the user types → the exported fluffos_input(id, bytes, count) → the driver
```

**And the most interesting detail is that the driver still emits real telnet protocol.** So the web page must supply a telnet client of its own — the official interface negotiates **ECHO, SGA, NAWS (window size) and TTYPE**, and renders the terminal with **xterm.js**.

> **This section is the real control group for Appendix E case 29 (xterm's Wasm parsing plugin)**: there, ANSI parsing was moved into Wasm; here, **the other end of the protocol** is moved wholesale into Wasm, with xterm.js outside acting as the display.

### Problem three: the export surface must be narrow enough

**The entire driver exposes just seven functions** — a textbook demonstration of both Chapter 2's "the Export section is what an attacker always sees" and Chapter 12's "keep the interface narrow":

| Exported function | Purpose |
|---|---|
| `fluffos_boot(config_path)` | Initialize the driver |
| `fluffos_tick(now_ms)` | Advance the scheduler by real time |
| `fluffos_connect()` | Establish a new virtual connection |
| `fluffos_input(id, bytes, count)` | Feed in the client's command bytes |
| `fluffos_disconnect(id)` | Close a connection |
| `fluffos_shutdown()` | Shut the driver down |
| `fluffos_flag(flag)` | Set a runtime flag (such as `'test'`) |

Instantiating the module:

```javascript
const M = await createFluffOS({ print, printErr, locateFile });
```

**Seven functions, one entire server.** Against Chapter 2 Scenario 4's line — **make the boundary coarse and the round trips few** — this is the most extreme example available.

### Problem four: a mudlib is tens of thousands of files, and Wasm has no filesystem

**Solution: MEMFS plus Emscripten's `file_packager`.**

Emscripten maps file I/O transparently onto an in-memory filesystem (MEMFS, see Chapter 7). The mudlib is packaged by `file_packager` into **a single `mudlib.data` image plus a `mudlib.js` loader**, mounted at a specified path before the runtime starts.

```bash
# Package an arbitrary mudlib
MUDLIB=/path/to/lib tools/wasm/build.sh
# or
tools/wasm/pack-mudlib.sh --mudlib <dir> --config <path>
```

**So the distribution shape becomes**: one `.wasm`, one `.js` glue file, one `.data` image — **three static files, and that is a whole game world.**

**But there is an honest current limitation here**, and it happens to be a living lesson in Chapter 7's four-tier storage ladder:

> **Writes currently persist only within the tab session (MEMFS is volatile).**
> The official roadmap's Phase 2 plan is: **layer IDBFS (or OPFS) over the mudlib's write paths (`/data`, saves, logs) and call `FS.syncfs()` on a timer and on `visibilitychange`** — so data survives a page reload. **Not yet implemented.**

**In other words: this project is currently stuck at Chapter 7's first tier (MEMFS), and it knows it needs to move to the second and third (IDBFS/OPFS).** There is no better field verification anywhere in this book.

### Problem five: capabilities must be cut away

Chapter 2 said "the cheapest way to implement security is not adding defences but removing capabilities." **FluffOS's Wasm build turns that into a table**:

| Feature | Status | Reason |
|---|---|---|
| libevent | **Removed** | Replaced by the tick queue |
| OpenSSL / TLS | **Removed** | **TLS is the browser's job**; `sys_reload_tls` does not exist |
| zlib | **Removed** | MCCP and the compress package are disabled |
| POSIX eval-limit timer | Auto-disabled | Available only on `__linux__`; an alternative is planned |
| BSD sockets | Off | No outbound socket efuns |
| DNS | **Stubbed** | Returns `127.0.0.1` synthesized on the next tick |
| External processes | Off | No `posix_spawn` support |
| Worker threads | Off | No async package |
| Database clients | Off | The MySQL/SQLite/PG libraries are unavailable |

**That table is what capability-based security actually looks like** (Chapters 1, 7): it is not "we defended these attack surfaces" but "**these attack surfaces do not exist in this build**."

It also maps precisely onto Chapter 3's four system walls — **no native system access, memory that only grows, no threads, and synchronous code meeting an asynchronous world**.

---

## 4. The Concrete Numbers

**This is the most valuable set of measured numbers in the book, because they come from a real, complex, still-maintained project rather than a benchmark toy.**

| Item | Value | Corresponding chapter |
|---|---|---|
| Initial linear memory | **64 MB** (grows to **2 GB** as needed) | Chapter 8: note the ceiling is set at 2 GB, not 4 GiB — **this is exactly "the browser's real-world interception"** |
| Stack | 16 MB | Chapter 2 |
| Code size (including PCRE) | **~3.6 MB raw** | Chapters 3, 8: far below the "30 MB practical ceiling" |
| Code size (after Brotli) | **~0.8 MB** | Chapter 8: **a compression ratio of about 4.5×, confirming that "Wasm's Brotli ratio is usually very good"** |
| ICU data | **~780 KB** (about 30 MB originally) | Chapter 8: **only the break-iterator rules are kept, cutting 97%** — this is "the highest-return step in cutting size is not a compiler flag but cutting the data you don't use" |
| DWARF debug info | Stripped at link time | Chapter 9 |
| Function names | **Kept** (for readable stack traces) | Chapter 3: **a deliberate trade-off** — a little obfuscation strength given up for debuggability |

> 🔍 **That ICU number is worth pausing on for three seconds.**
> 30 MB → 780 KB, cutting 97.4%. **Not through `wasm-opt`, not through LTO, but through thinking clearly about what ICU was actually for** — this project needs only the break-iterator (word segmentation) rules, so every other locale, time zone, collation rule and transliteration table simply isn't packaged.
> **Chapter 8's "size-cutting return ranking" should gain a step 0: cut the data before you cut the code.** Because in the Wasm output of a large C/C++ project, more than half is often the data tables it dragged in, and you usually don't use 90% of them.

---

## 5. Running It Locally Yourself

### Route A: native (fastest way to see something)

```bash
# 1. Get a mudlib
git clone https://github.com/fluffos/mudlibs
cd mudlibs/libs/<the slug you picked>

# 2. Start it with a built driver (work/ is the playable version, UTF-8 converted with repairs applied)
~/src/fluffos/build-debug/src/driver config.fluffos

# 3. telnet in
```

### Route B: WebAssembly (make it a static site)

```bash
# One-off: cross-build ICU for wasm32
tools/wasm/build-deps.sh

# Build: native codegen tools + the wasm driver + the demo bundle
tools/wasm/build.sh

# Serve it locally to look at the result
python3 -m http.server -d build-wasm/dist 8080
# open http://localhost:8080/
```

**Swapping in your own mudlib**:

```bash
tools/wasm/pack-mudlib.sh --mudlib <mudlib dir> --config <config path>
# or
MUDLIB=/path/to/lib tools/wasm/build.sh
```

**The output is a purely static directory** — drop it on GitHub Pages, any CDN or any S3 bucket and you have a playable game. **That is Chapter 5's "building machines on static pages," closed end to end.**

### Pre-launch, against Chapter 5 and Appendix C

| Check | This case's situation |
|---|---|
| Does it need COOP/COEP? | **No** — there are no threads (the async package is off), so **deploy directly** |
| The `.wasm` MIME | Static hosting must return `application/wasm` correctly |
| Relative paths | A project page lives under a subpath; watch how `locateFile` resolves |
| `.nojekyll` | Needed (so resources beginning with `_` aren't swallowed) |
| Brotli | **Strongly recommended** — 3.6 MB → 0.8 MB |

---

## 6. Every Wall It Hit (mapped back to this book)

| Wall | What happens | Chapter |
|---|---|---|
| **No blocking event loop** | Had to become `fluffos_tick(now_ms)` driven by the host | Chapters 3 (the system wall), 5 |
| **No sockets** | The Transport abstraction plus a JS bridge; DNS stubbed to `127.0.0.1` | Chapters 3, 7 |
| **No threads** | The async package is off entirely, with a synchronous replacement planned | Chapters 3, 5 |
| **No eval limit** | **An infinite LPC loop freezes the whole tab** (natively it relies on a POSIX timer; there is no replacement on Wasm yet) | Chapter 3 (the sandbox doesn't protect you from yourself) |
| **MEMFS is volatile** | Writes persist only within the session; an IDBFS/OPFS overlay is on the roadmap | **Chapter 7 (the four storage tiers)** |
| **The tab is suspended in the background** | Timers pause; on returning to the foreground the gameticks catch up (**capped at 100**) | Chapter 5 (the host environment's rhythm isn't yours to set) |
| **Table-based charsets unsupported** | Only algorithmic ones (UTF-8/16/32, Latin-1, ASCII) are supported; table-based ones are not | Chapter 8 (data is the bulk of the size) |
| **A 2 GB memory ceiling** | Not 4 GiB — **this is the browser's real-world interception** | Chapter 8 |
| **Missing browser-environment capabilities** | The archive site notes some games are "playable but with login restrictions," because capabilities like `query_ip_number()` are missing | Chapters 3, 7 (capabilities must be handed in by the host; if they can't be, they don't exist) |

> **The last row is especially worth savouring**: a mudlib written in the 1990s calls `query_ip_number()` during its login flow to record the player's IP — **and inside a browser there is no such concept as an IP to give it.** One line of code written thirty years ago has become a porting obstacle today.
> **This is what Chapter 12's "maintenance entropy" looks like most concretely: your code didn't break; the world beneath it was replaced.**

---

## 7. jsbridge: The Two-Way Door That Was Opened

FluffOS's Wasm build provides a set of `jsbridge` efuns **that exist only on the WASM target**, letting LPC and page JavaScript call each other:

```
LPC → JS:  js_eval(), js_call()      → fetch, canvas/WebGL, audio, storage…
JS  → LPC: js_export() + fluffos.callLPC()
```

**This matters more than it looks**: it means a 1990s text game **can grow a canvas map, WebGL effects, Web Audio soundtracks and browser-side storage without altering the game logic at all** — because that bridge is two-way, and the game side only has to call one more efun.

> This lines up exactly with Chapter 12's four-layer topology: **the Wasm core (the LPC driver) is an asset designed to be unchanged for a decade; the page layer (xterm.js, canvas, UI) is consumable and may be rewritten every three years.** And jsbridge is that "interface so narrow it cannot go wrong."

---

## 8. Why It Is the Living Specimen of the Book's Thesis

**Now put the technology down and look at the other side of this.**

A MUD's **entire source code** — the world map, the NPC dialogue, the martial-arts systems, the economic rules, the description of every room — is that mudlib. **It has always been downloadable in full**: in the 1990s through packed archives, today through `git clone`, and now it can even be loaded and run directly in a browser.

**Not one line of code is secret.**

By the old logic that code is an asset, a thing like this could not possibly have value. And yet:

- These games **lived thirty years**, forked, modified and reopened long after their original authors left.
- Someone **spent an enormous amount of effort repairing them** — converting encodings, fixing bugs, writing a `NOTES.md` recording every change, verifying one by one whether each still boots.
- And today someone **compiled the entire driver to Wasm**, purely so they can be opened again.

**That moat was never in the code.**

It is in those people — in the ones who remember being stuck in some room for three days at seventeen, and in the one who repaired those broken thirty-year-old archives one at a time. **These are the two hardest to copy of Chapter 12's five lines of defence: data gravity (the world state and that memory) and ecosystem (the community)** — and neither has anything to do with the code's visibility.

> 💡 A Word to the Wise
> **When something's source has been fully copyable for thirty years and it still has not been replaced, you have found a clean piece of evidence about value.** These mudlibs are a rare controlled experiment in software history — **zero secrecy, zero copying cost, a trivially low barrier to modification** — and in theory they should have drowned under better copies long ago. They did not. Because what users want has never been "a copy of code that runs"; it is **that world, and the people in it**. And those two things `git clone` cannot take.
> Put that inside Chapter 12's framework and the answer is very clear: **when LLMs drive the marginal cost of writing code to zero, we simply arrive where MUDs have always been — the code was never what was valuable; what was valuable is everything that grew around it.** The only thing that changed is that now all software must face that situation.
> So rather than worrying about whether AI will copy your product, ask something more useful: **if my source were published in full tomorrow, would anyone still be using it in thirty years?** These mudlibs' answer is yes. **What is yours?**

> 🔍 Deeper Commentary — the technical debt of preservation, and a long-term problem nobody talks about
> This case also exposes something increasingly acute in digital preservation that the software industry has broadly not started to face. **Repairing a thirty-year-old mudlib is hard not because of the code but because of the world beneath it that vanished.** What those `NOTES.md` files record is mostly not logic errors but: whether the original encoding was GB2312 or BIG5, which efuns the driver of that era had that no longer exist, and what to do about a call like `query_ip_number()` that assumed there was a network, an IP, an operating system. **The code itself is barely broken — what broke is every assumption it made about its environment.**
> **And this is exactly where Wasm's real value in cultural preservation lies, and where it differs from virtual machines and emulators.** An emulator (Appendix D case 3's v86) preserves "the hardware"; a container image preserves "the operating system and dependencies"; **compiling a driver to Wasm preserves "execution semantics"** — you need not preserve an entire 1996 Linux, only a 3.6 MB module and a host interface with a stable specification. **Wasm has therefore become, almost by accident, one of the best software preservation formats we have**: a public specification, several independent implementations, an extremely strong backward-compatibility commitment, and a host environment (the browser) that is itself the most conscientiously maintained compatibility layer humanity has.
> Turned around, that is also an uncomfortable reminder for everyone writing code today: **every assumption about the environment you write down — this API will exist, this service will exist, this format will be supported — is an exam question you are setting for someone thirty years from now.** And Chapter 12's question about "who fixes it when it breaks at midnight three years from now" reaches its final form here: **thirty years from now, will anyone still understand why you wrote it that way?** Those `NOTES.md` files are the only effective answer to that question.

---

## 9. Putting It Back in the Catalog: Whom It Replaces

| Appendix E's 🔴 concept | The real counterpart | The difference |
|---|---|---|
| Case 58 Minestom-Wasm (a game server in the browser) | **FluffOS × Wasm** | FluffOS is real, and harder — it also compiles user code at runtime |
| Case 60 Micro-Apache-Wasm (a server engine in the browser) | **FluffOS × Wasm** | Micro-Apache handles only stateless requests; FluffOS has a heartbeat, timers and persistent world state |
| Case 92 OpenLISP-Wasm (a symbolic computation interpreter) | **FluffOS's LPC compiler + VM** | The same shape: **move a language's complete runtime into Wasm** |
| Case 34 QuickJS-Wasm (JS inside JS) | **FluffOS's LPC inside Wasm** | The same shape, but FluffOS also brings a whole game runtime along |

**If the catalog in Appendices D–F is a map of "is this road passable," this appendix is the place at the end of the road where someone actually lives.**

---

## 10. Resources

| Item | Location |
|---|---|
| The FluffOS driver | `github.com/fluffos/fluffos` |
| Architecture documentation for the Wasm target | `src/wasm/README.md` (this appendix's main source) |
| Wasm build scripts | `tools/wasm/build-deps.sh`, `tools/wasm/build.sh`, `tools/wasm/pack-mudlib.sh` |
| The mudlib archive | `github.com/fluffos/mudlibs` |
| The online archive (click and play) | `mudlibs.fluffos.info` |
| Official documentation | `fluffos.info` |

> ⚠️ **A licensing note**: most works in the mudlibs archive **have no formal licence terms**; it is a community archive for cultural preservation that retains the original authors' attribution. **If you intend to do anything beyond personal study and play (commercial use especially), clarify the rights yourself.** This book's citations are likewise for education and research only.
