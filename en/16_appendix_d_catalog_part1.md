# Appendix D: The Hundred-Case Catalog of Static-Page Wasm (Part 1) — Cases 1–35

> **This catalog's provenance and calibration**: the original conversation produced "120 classic cases." On comparison, **19 of them turned out to be renumbered restatements** (26–30 restate 21–25; 32–35 restate 21–24; 61–65 restate 46–50; 66–70 restate 36–40), leaving **101 genuinely distinct entries**. This catalog renumbers them 1–101 in order of first appearance, with the original number in parentheses.
>
> **Authenticity tags**:
> 🟢 **Verifiable** — the project really exists, with an official Wasm build or a widely used Wasm port.
> 🟡 **Upstream real, Wasm port unverified** — the upstream C/C++/Rust project is entirely real, but a Wasm version under this name has not been verified.
> 🔴 **Illustrative construction** — no such project was found; the technical path is sound, and the entry stands as "this road can be walked."
>
> **All performance numbers are the claims made in the original conversation** and have not been independently verified for this book. Read them by Chapter 4 Scenario 1's standard: **trust the direction, doubt the multiplier.**

---

## I. Audio, Video and Signal Processing

### 1. (originally 1) FFmpeg.wasm — Pure front-end media transcoding and editing 🟢

**Pain point**: Traditional transcoding depends on the server side (AWS MediaConvert or a self-hosted FFmpeg cluster), with three pain points: extremely high bandwidth and compute costs, private files that must be uploaded, and no offline capability.

**How it works**: Emscripten compiles FFmpeg's millions of lines of C into `ffmpeg.wasm`. It uses a "main thread (UI) + Web Worker (compute)" model. JS writes the video into Wasm's virtual filesystem **MEMFS** as an `ArrayBuffer`; JS calls the exported command-line interface (`ffmpeg -i input.mp4 output.avi`), and Wasm decodes and encodes the in-memory bitstream directly; when finished, the output is read back out of MEMFS and turned into a Blob URL for download.

**Performance**: Claimed to reach **60%–80%** of native C with SIMD and threads (`SharedArrayBuffer`).

**Advantages**: Absolute privacy (data never leaves the device), zero hosting cost, support for nearly every mainstream format.
**Disadvantages**: Constrained by browser memory limits (usually 2–4 GB), so it cannot handle tens of gigabytes of 4K footage; the first load requires downloading roughly 20–30 MB of module; the multithreaded build **must have COOP/COEP configured**, which on GitHub Pages means relying on `coi-serviceworker`.

**Competitors**: Cloud transcoding (unlimited compute, high cost, privacy risk); pure-JS media libraries (video.js/jsmpeg, capable only of simple playback and containers, unable to carry H.264/H.265 core codecs).

---

### 2. (originally 2) Rust-uBlock — A Wasm ad-blocking match engine 🟡

**Pain point**: A modern ad blocker must match tens of thousands of network requests in real time against hundreds of thousands of filter rules (EasyList). Doing that much string comparison and regex matching in pure JS consumes a lot of CPU and causes small stutters (jank) on tab switches.

**How it works**: The core matching logic is written in Rust and compiled to Wasm through `wasm-bindgen`. It uses a **rule tree** structure: a highly optimized trie plus a Bloom filter built inside linear memory. When a request is intercepted, the URL is passed into Wasm, which performs a binary search over hundreds of thousands of rules within microseconds and returns an allow/block boolean.

**Performance**: Claimed **3–5× faster** than pure JS for string comparison and rule lookup, with stable memory usage, entirely avoiding the GC pauses caused by JS constantly creating string objects.

**Advantages**: Noticeably lowers CPU load and power draw on low-end devices (mobile browsers); the rule database sits compactly in linear memory with little fragmentation.
**Disadvantages**: Passing URL strings across the JS↔Wasm boundary frequently incurs boundary conversion overhead (string encoding/decoding), so a carefully designed shared-buffer mechanism is required.

**Competitors**: Pure-JS blocking engines (easy to develop, mature ecosystem, but visibly higher memory and CPU peaks past 500,000 rules); the browser's native declarative blocking (Manifest V3's `declarativeNetRequest`, highest performance but a limited rule count and no custom complex logic).

---

### 3. (originally 3) v86 — An in-browser x86 hardware emulator 🟢

**Pain point**: To run Linux or Windows 95 on a web page, the traditional approach was a backend virtual machine (KVM) streaming the screen over VNC — high server cost, high latency, poor interactivity.

**How it works**: The CPU emulation, memory management and disk controller (IDE) core are compiled to Wasm. Wasm emulates x86's registers, physical memory and interrupt vector table inside linear memory, and includes a **JIT compiler that translates x86 machine code into Wasm instructions on the fly** (see Chapter 6 Scenario 4). For display output, VRAM data is copied out and rendered by JS through Canvas/WebGL; keyboard and mouse events are captured by JS and fed into Wasm's interrupt handlers.

**Performance**: Claimed to run Linux in the browser at roughly early-Pentium speed, booting to a terminal within seconds and running classic 3D games such as Doom smoothly.

**Advantages**: Fully decentralized — GitHub Pages need only host the image (say a 10 MB Linux ISO); the boot state can be serialized out to a file and saved at any time.
**Disadvantages**: Cannot use the host's hardware virtualization (Intel VT-x); it is pure software emulation, so **it cannot run modern heavyweight 64-bit operating systems**.

**Competitors**: Backend Docker/VNC (good performance, good compatibility, but cost grows linearly with users and it cannot work offline); pure-JS emulators (like the early jor1k, more than 10× slower for lack of precise bit operations and compact memory, with screen tearing and audio stutter).

---

### 4. (originally 4) ONNX Runtime Web (Wasm) — A front-end AI inference engine 🟢

**Pain point**: For face recognition, background blur or speech-to-text on the web, the traditional approach sends data back to a backend GPU — carrying privacy problems, GPU cost and network latency.

**How it works**: Microsoft compiled the open-source ONNX Runtime C++ core to Wasm. Developers put the `.onnx` model on GitHub Pages; JS loads the model and the multimedia input (a webcam frame, say) and passes the image matrix into Wasm; Wasm implements the neural network's matrix multiplications and activation functions. The core optimizations are **Wasm SIMD** hardware acceleration and **Web Worker** multi-core parallelism.

**Performance**: Claimed **10–20× faster** than a pure-JS neural network once SIMD and threads are on; lightweight models (MobileNet, YOLOv8-nano) can get a single inference under 30 milliseconds, reaching 30 FPS real-time analysis.

**Advantages**: Compute is spread across users' browsers, so static hosting alone gives you a massively concurrent AI service; works offline, and the data stays safe.
**Disadvantages**: Large models (a several-hundred-megabyte LLM or Stable Diffusion) take too long to download; CPU inference still lags WebGPU acceleration.

**Competitors**: TensorFlow.js (its WebGL/WebGPU modes exploit the GPU better, but ONNX Runtime Wasm has sturdier cross-platform compatibility and is the fallback on devices without good GPU drivers); a backend Python API (supports huge models, but is expensive under high concurrency).

---

### 5. (originally 5) DuckDB-Wasm — An in-browser analytical SQL database 🟢

**Pain point**: When a page needs to process, analyze and filter millions of records of big data (CSV, Parquet, logs), loading it all into JS memory produces so many objects that you get OOM or long GC pauses. Standing up a backend database for a demo dashboard is far too heavy.

**How it works**: The C++ core of DuckDB — an embedded **columnar** SQL database — is compiled to Wasm in full. It uses a **vectorized execution engine**, reading big data as a stream and storing it directly in linear memory in the compact Arrow columnar format. The user types standard SQL, and Wasm's internal query optimizer scans memory at high speed in parallel. **The prettiest part is remote reading**: it natively supports issuing **HTTP Range Requests** against remote Parquet/CSV, fetching only the byte ranges it needs (see Chapter 6 Scenario 4).

**Performance**: Claimed to complete a 10-million-row aggregate query in **100–200 milliseconds**, more than **60× faster** than iterating JS arrays (`Array.filter.reduce`).

**Advantages**: Lets a static page host a powerful BI dashboard; can query remote data without downloading the whole file.
**Disadvantages**: Data lives in memory by default and vanishes when the tab closes (it can be persisted to OPFS/IndexedDB, subject to quota).

**Competitors**: SQLite-Wasm (excellent at transactional OLTP, but columnar DuckDB wins outright on million-row OLAP statistics); pure-JS data processing libraries (Lodash, Crossfilter, out of their depth past a million rows).

---

### 6. (originally 6) SQLite-Wasm — A complete ACID relational database in the browser 🟢

**Pain point**: Complex front-end applications (offline notes, expense tracking, a PWA mail client) had only IndexedDB to lean on — an asynchronous, event-driven API that is tedious to write and supports no multi-table JOINs, no prepared statements and no strong ACID transactions.

**How it works**: SQLite's own team compiles the standard C source to `sqlite3.wasm` via Emscripten. **The most elegant part is the persistence layer (VFS)**: the project developed a dedicated virtual filesystem using **OPFS (Origin Private File System)** or IndexedDB as the underlying storage medium (mechanism detailed in Chapter 7). The execution architecture isolates work in a Web Worker: the main thread sends SQL by `postMessage`, the Wasm engine inside the Worker manipulates the B-tree indexes and data pages in memory, and writes back synchronously through the VFS.

**Performance**: Claimed that on OPFS, single inserts and complex JOINs are almost indistinguishable from local native, with read/write throughput **2–4× faster** than JS-wrapped IndexedDB, and crash safety guaranteed.

**Advantages**: The front end gets full standard SQL and transaction support; the `.db` file can be packaged and downloaded directly, making backup and migration trivial.
**Disadvantages**: Wasm plus glue runs to a few hundred KB; if the browser lacks OPFS, falling back to an IndexedDB-simulated VFS drops write performance sharply.

**Competitors**: Native IndexedDB (no download, no size cost, but no relational queries or transaction capability); a backend database (handles massive data and multi-tenancy, but costs a server and offers no true offline capability).

---

### 7. (originally 7) Pyodide — A Python scientific computing runtime in the browser 🟢

**Pain point**: Python rules data science (NumPy, Pandas, Matplotlib), but running Python on a web page or building an interactive teaching platform previously meant standing up a Jupyter kernel on a server — expensive, and prone to collapse under concurrency.

**How it works**: The CPython core plus a large set of C-extension scientific libraries (NumPy, Pandas, SciPy, scikit-learn) are compiled to Wasm in full. **Two-way type bridging**: a JS `Array` can be read by Python as a `list`/`dict` and vice versa; a chart drawn by Matplotlib can be turned into a binary stream and rendered by JS onto a `<canvas>`.

**Performance**: Pure Python code runs at roughly **1/3–1/5** of native (an interpreter inside a virtual machine — two layers of abstraction); but once you call NumPy/Pandas C kernels, matrix work approaches **70%** of native.

**Advantages**: Genuinely zero backend cost, with a complete data science environment running on the client; excellent for interactive teaching and data-visualization dashboards.
**Disadvantages**: **The initial load is catastrophic** — CPython plus base libraries easily runs 30–50 MB. Mitigations: on-demand package loading (`micropip`), persistent Service Worker caching, or switching to MicroPython/Wasm.

**Competitors**: Google Colab / a backend JupyterHub (strong performance, GPU support, but high operating and scaling costs); Brython/Skulpt (pure-JS Python interpreters, tiny files but only syntax emulation — **they cannot run C-extension scientific libraries**).

---

### 8. (originally 8) Canvas-GIMP / wasm-img — High-performance image and filter processing 🟡

**Pain point**: For pixel-level processing of high-resolution photos on the front end (blur, sharpen, colour matrices, edge detection), iterating tens of millions of RGBA pixels in JS causes severe GC stutter, and single-threaded computation makes the page throw up "this page is unresponsive."

**How it works**: GIMP's core algorithms (or OpenCV's C++ imaging modules) are compiled to Wasm. **Shared memory architecture**: after Canvas reads the image's `ImageData`, the pixel pointer is written directly into Wasm linear memory, avoiding bulk JS↔Wasm copying. **Parallel pixel computation**: SIMD is enabled internally (one instruction handling floating-point work on four pixel channels at once), and the image is cut into tiles distributed to Wasm threads inside several Workers.

**Performance**: Claimed that for a 4K photo (about 12 million pixels), a high-order filter such as Gaussian blur usually finishes in under **50 milliseconds**, **15–30× faster** than iterating arrays in pure JS.

**Advantages**: Extreme compute performance, squeezing the multi-core CPU dry; photos never need uploading to any server, meeting medical-grade privacy requirements.
**Disadvantages**: The algorithms are fixed inside the compiled module, so JS cannot easily inject or modify a filter algorithm dynamically — flexibility is lower.

**Competitors**: Pure CSS filters / the Canvas 2D API (hardware-accelerated by the browser and extremely fast, but limited to basic operations, with no custom complex matrix math or advanced background removal); cloud image APIs (Cloudinary and the like — powerful but metered, with latency and privacy risk).

---

### 9. (originally 9) OpenTTD-Wasm — Porting a large simulation/management game 🟢

**Pain point**: OpenTTD contains tens of thousands of lines of C++, extensive pathfinding (A*), vehicle AI and dynamic map rendering. The community wanted "click and play" while overcoming cross-platform audio, input and graphics compatibility.

**How it works**: Emscripten plus **SDL2** compiles the entire C++ game to Wasm. SDL2's low-level drawing calls are translated automatically into WebGL; mouse, keyboard and audio are bridged through the Web Audio API and DOM events. Saves and MOD resources sync to browser storage through Emscripten's **IDBFS** (an IndexedDB-backed virtual filesystem).

**Performance**: Claimed to hold a steady **60 FPS** even under the heavy load of thousands of trains and aircraft computing routes simultaneously on the map.

**Advantages**: Extremely convenient porting — a twenty-year-old game comes back to life with almost no changes to the C++ core logic; entirely free and backend-free.
**Disadvantages**: The first entry requires downloading a fairly large asset pack (sprites and sound effects); sandbox restrictions make LAN multiplayer with the native build hard for the web version.

**Competitors**: Rewriting in JS/HTML5 (an enormous engineering effort, and JS's dynamic typing and GC drop frames badly when pathfinding for thousands of game objects in real time).

---

### 10. (originally 10) swc-wasm — Ultra-fast JS/TS transpilation and bundling 🟢

**Pain point**: Modern front ends must transpile new-syntax JS/TS to compatible versions (Babel's job). As projects grow, Babel — written in Node.js — crawls when parsing tens of thousands of AST nodes, and builds routinely take minutes.

**How it works**: `swc` is a high-performance JS/TS transpiler written in **Rust**. Compiled to Wasm, it can be deployed straight onto a static page as a live transpiler (playground) or a micro-bundler. The user types modern TS, JS passes the string into Wasm memory, and the Rust parser builds an AST with a highly optimized memory layout, performing minification and transpilation. All string analysis and tokenization happen entirely inside Wasm, avoiding the JS engine's constant object collection.

**Performance**: Claimed **20–40× faster** than pure-JS Babel; even in a single-threaded browser environment, transpiling ten thousand lines of complex TypeScript takes only a dozen milliseconds.

**Advantages**: Ideal for building a backend-free online IDE, code formatter or static analysis platform.
**Disadvantages**: Compared with the native local binary, the Wasm build is about 2× slower thanks to the sandbox and cross-boundary string passing (but still far faster than Babel).

**Competitors**: Babel (an extremely rich ecosystem and plugin set, but limited by the JS language and outclassed on large-scale transpilation).

---

## II. Search, Parsing and Toolchains

### 11. (originally 11) Sonic-Wasm — A pure front-end full-text search engine 🟡

**Pain point**: A static blog (Hexo, Hugo, Jekyll) or a large documentation site on GitHub Pages needs full-text search. Backend options (Elasticsearch, Algolia) cost money or require operations; pure-JS options (Lunr.js) load megabytes of JSON index into memory and get slow during fuzzy search and reranking, triggering GC and typing latency.

**How it works**: The core of Sonic, a lightweight search engine written in Rust, is compiled to Wasm. It builds a highly compact **inverted index plus Bloom filter** in linear memory, with data laid out as a binary byte stream. On query, JS passes the keyword through a shared buffer, and Wasm runs bitmask operations and N-gram term-frequency analysis internally, returning document IDs in microseconds.

**Performance**: Claimed that when searching an index of tens of thousands of articles (roughly 50 MB of text), a complex fuzzy match completes in **2–5 milliseconds**, more than **10× faster** than Lunr.js, using a quarter of the memory of the JS version.

**Advantages**: Brings millisecond, backend-free full-text search to a static page; zero operating cost.
**Disadvantages**: When content changes often, the front end must regenerate and download a large binary index regularly.

**Competitors**: Algolia/Elasticsearch (support massive data and dynamic weighting, but cost money or operations); Lunr.js/Fuse.js (nothing to learn, but CPU peaks are too high when searching long texts past tens of thousands of words).

---

### 12. (originally 12) Web-Wireshark (Wasm-Pcap) — Network packet analysis 🟡

**Pain point**: Diagnosing a network fault means opening a `.pcap` capture file. Traditionally that meant uploading it to a backend for a C program (libpcap) to parse — but pcaps usually contain a company's sensitive network topology and packet contents, so uploading them to the cloud is a serious risk.

**How it works**: A C/C++ network analysis library (libpcap, or Rust's pcap-parser) is compiled to Wasm. **Streaming binary parsing**: the user drops in a several-hundred-megabyte `.pcap`, and JS reads it as a stream through the File API and writes it into Wasm memory; Wasm takes it apart bit by bit, reconstructing the protocol tree from Ethernet through IP, TCP and UDP up to the application layer (HTTP/DNS), and hands the structured data back to JS to render as an interactive collapsible tree.

**Performance**: Claimed to parse a 100 MB pcap of hundreds of thousands of frames in about **200 milliseconds**, **15–20× faster** than pure JS.

**Advantages**: 100% privacy-safe — corporate packets never leave the device; static hosting alone provides a diagnostic tool engineers worldwide can use for free.
**Disadvantages**: Sandbox restrictions mean Wasm cannot call the local NIC for **live capture**; it can only analyze static capture files.

**Competitors**: Local Wireshark (the most complete, with live capture, but it requires installation and can't be embedded in a page to share); pure-JS packet parsing libraries (lacking efficient binary pointer manipulation and struct alignment, and prone to OOM on large files).

---

### 13. (originally 13) OpenCascade-Wasm — An industrial 3D CAD modelling kernel 🟢

**Pain point**: An industrial 3D modelling kernel (the kind inside AutoCAD or SolidWorks) is usually millions of lines of heavily optimized C++. To edit complex industrial parts (`.STEP`, `.IGES`) on a web page, a pure-JS library (Three.js) can only handle surface meshes and **cannot compute exact boundary representation (B-Rep), boolean operations or surface fitting at all**.

**How it works**: The open-source industrial geometry kernel **OpenCascade (OCCT)** is compiled to Wasm in full. Exact geometric mathematical models (3D curves, NURBS surfaces) are stored in linear memory, and every boolean topology operation, fillet and shelling algorithm runs entirely inside Wasm. Once computed, the result is tessellated dynamically into triangles and the vertex buffer handed straight to WebGL/WebGPU for hardware-accelerated rendering.

**Performance**: Claimed that complex 3D solid boolean trimming reaches **75%** of native C++, responding to mouse operations within a few hundred milliseconds.

**Advantages**: Overturns the limit that "the web can view 3D but not model it," running geometric algebra as exact as desktop software on a static page.
**Disadvantages**: The module is enormous (**10–15 MB even compressed**), so the first load takes a long time.

**Competitors**: Three.js/Babylon.js (fine for visualization, but without the mathematics of industrial geometric topology and solid modelling); Onshape (commercial cloud CAD, powerful but computing on a backend GPU cluster with a steep subscription).

---

### 14. (originally 14) FontForge-Wasm — Font editing and conversion 🟡

**Pain point**: Optimizing web fonts often means subsetting a large font (a 15 MB `.TTF`/`.OTF`, keeping only common characters), compressing it (to `.WOFF2`) or editing outlines. Building that as a web service burns bandwidth uploading large fonts, and processing enormous numbers of Bézier curves on the backend is expensive.

**How it works**: FontForge's C-language font processing and layout engine is compiled to Wasm. **Vector outline parsing**: the TrueType parser inside Wasm reads the binary structure tables (`glyf`, `head`, `cmap`) and loads each character's quadratic/cubic Bézier outlines into memory. **Dynamic subsetting**: after the user selects the characters they need, Wasm removes the unselected glyph data directly in memory, recomputes every internal pointer and offset, and calls Brotli to package the result on the fly.

**Performance**: Claimed that trimming a huge font containing 20,000 Chinese characters and exporting `.WOFF2` takes only **1–2 seconds**, nearly **25× faster** than pure JS.

**Advantages**: Fonts are processed entirely locally, consuming none of the developer's bandwidth.
**Disadvantages**: Font design involves complex OpenType feature layout (kerning and the like), and emulating that C-language rendering on the front end demands highly optimized glue code to keep the UI responsive.

**Competitors**: Backend Python (fontTools — a mature ecosystem but it needs a server); opentype.js (capable of basic reading and drawing, but insufficient in performance and completeness for high-order WOFF2 compression and thorough subsetting).

---

### 15. (originally 15) WebXm-Tracker — Chiptune (MOD) synthesis and playback 🟡

**Pain point**: The chiptunes of the 80s and 90s (`.XM`, `.MOD`, `.IT`) are only tens of kilobytes because what they store is score instructions and sampled instruments rather than waveforms. Converting them to MP3 destroys that size advantage; decoding and mixing them live in pure JS easily produces popping artifacts from main-thread interference.

**How it works**: A C-language chiptune decoding engine (libmodplug, or a Rust tracker engine) is compiled to Wasm. **It uses an AudioWorklet architecture**: Wasm is loaded onto the high-priority audio rendering thread, fully isolated from the main UI thread. Inside Wasm, 44,100 samples are computed per second, note, volume and portamento effect commands are parsed in real time, instrument waveform frequencies are modified dynamically, and the computed floating-point audio buffer is fed straight to the output.

**Performance**: Claimed that Wasm's compute time on the audio thread is usually under **0.1 milliseconds** (far below the 2.9-millisecond hard deadline for a 128-sample block), so the music stays perfectly smooth even while the main page is loading a large image.

**Advantages**: Extremely low CPU and memory overhead, faithfully recreating hardware-level retro music; a few tens of kilobytes and the music starts.
**Disadvantages**: Audio pointer manipulation demands extremely high memory safety — one array overrun and the whole audio thread goes silent and dies, and debugging is hard.

**Competitors**: Traditional MP3/AAC playback (over 100× larger, and unable to control tracks dynamically or visualize the score in real time); pure-JS audio decoders (disrupted by irregular GC pauses, and prone to pops and dropouts whenever the page animates or scrolls).

---

### 16. (originally 16) Web-GnuPG (Wasm-GPG) — Front-end PGP encryption and digital signing 🟡

**Pain point**: PGP is the gold standard for encrypting mail and files, but traditional GnuPG requires installing a local CLI, which is a high barrier. Making it a web service by uploading the private key or plaintext to a backend destroys the core principle of end-to-end encryption entirely. Pure-JS crypto libraries are extremely slow generating a 4096-bit RSA key pair, often freezing the tab.

**How it works**: The C-language GnuPG (or Rust's Sequoia-PGP) is compiled to Wasm. **Bignum optimization**: the cryptographic core involves intensely dense modular exponentiation over very large integers, and Wasm uses `i64` instructions for register-level bit manipulation directly in linear memory. **Random-number safety**: Wasm cannot access a hardware entropy source directly, so the architecture injects entropy into the Wasm engine by having JS glue call the browser's native `crypto.getRandomValues()`.

**Performance**: Claimed **85%** of native C when generating 4096-bit RSA or processing hundreds of megabytes of AES-256; key generation takes only 1–2 seconds, **8–10× faster** than early openpgp.js and without freezing the UI.

**Advantages**: A genuinely zero-knowledge architecture — keys and plaintext never leave the device; static hosting makes it very hard for an attacker to tamper with the front-end crypto logic through a backend vulnerability.
**Disadvantages**: Sandbox restrictions mean it cannot read the local GPG keyring, so each use requires manually importing a key or storing it in the browser (the latter carries risk).

**Competitors**: Local Gpg4win / the GnuPG CLI (the most secure and best integrated, but requires installation); pure-JS crypto libraries (SJCL, forge — lacking low-level memory alignment and bit-operation optimization, with CPU peaks that are too high on large files).

---

### 17. (originally 17) esbuild-wasm — An ultra-fast front-end compile-and-bundle playground 🟢

**Pain point**: If a code playground on a static page uses the JS versions of Webpack or Babel, the user waits seconds after each edited line, destroying the live-feedback experience.

**How it works**: `esbuild` is an ultra-fast bundler written in **Go**. The project uses Go's Wasm target (`GOOS=js GOARCH=wasm`) to compile the whole esbuild core into `.wasm`. It emulates an in-memory filesystem internally; JS passes several files' code in as strings, and esbuild instantly destructures and bundles them into a single JS/CSS output.

**Performance**: Claimed to bundle a React project of 50 modules and roughly ten thousand lines in **30–50 milliseconds** in the browser, more than **30× faster** than pure-JS Rollup/Babel.

**Advantages**: Gives online IDEs and technical documentation live transpilation with no backend Node.js compile service at all.
**Disadvantages**: **Wasm modules compiled from Go are generally large (usually 8–12 MB)** and include Go's own runtime, which is unfriendly to first load (a textbook instance of Chapter 3's "language runtime burden").

**Competitors**: Babel-Standalone (smaller, but limited by JS's dynamic typing and GC and outclassed when parsing large volumes of code); the native esbuild binary (exploits multiple cores and is 3–5× faster than the Wasm build, but cannot run inside a browser).

---

### 18. (originally 18) Tesseract.wasm — Multilingual pure front-end OCR 🟢

**Pain point**: OCR traditionally means uploading to a cloud API (Google Cloud Vision and the like), with metering and privacy problems (the risk of leaking ID cards and invoice photos). Pure-JS character matching algorithms are far too inaccurate for complex backgrounds or handwriting.

**How it works**: The C++ open-source OCR engine Tesseract is compiled to Wasm via Emscripten. Since 4.0 Tesseract has used an **LSTM**-based engine; the Wasm module loads the trained language pack (`.traineddata`) directly and performs matrix multiplication in linear memory. **Dynamic language pack loading**: the engine itself stays light, and JS downloads the corresponding binary feature pack only when the user picks a language.

**Performance**: Claimed that with SIMD on, recognizing a text-covered A4 image takes about **0.5–1.5 seconds** at over 95% accuracy, reaching **70%** of native C++.

**Advantages**: 100% offline capable, with data staying entirely in the browser; static hosting alone gives you an infinitely concurrent, zero-operations, free text extraction tool.
**Disadvantages**: Language training packs are large (a Chinese pack often runs **10–40 MB**), so the wait is long on mobile or a poor connection.

**Competitors**: Commercial cloud OCR APIs (the most accurate, but metered per call and unable to protect privacy); basic pure-JS image recognition (with no machine learning model behind it, it loses all ability on skewed or noisy images).

---

### 19. (originally 19) WebManiac-GameBoy — A hardware-accurate Game Boy emulator 🟡

**Pain point**: Early pure-JS emulators ran into a wall emulating hardware clocks and precise interrupts — JS's `setInterval` is imprecise, and page scrolling or background tasks throw audio and video badly out of sync, producing dropped frames and shrill pops.

**How it works**: A precise Game Boy emulator core written in Rust is compiled to Wasm. **Cycle-accurate clock emulation**: the Game Boy's LR35902 CPU executes about 4.19 million clock cycles per second, and Wasm emulates register state, memory-mapped I/O (MMIO) and the PPU's scanlines in a strictly cycle-accurate loop. **Double-buffered rendering**: Wasm maintains the raw 160×144 pixel buffer in linear memory and, on each frame's V-blank interrupt, copies it quickly into JS's Canvas `ImageData`, synchronizing to the 60 Hz refresh rate with `requestAnimationFrame`.

**Performance**: Claimed that emulating the hardware clock consumes under **2% of CPU**, locking the picture solidly to 60 FPS with perfectly smooth 8-bit audio.

**Advantages**: Perfect hardware fidelity with flawless audio/video sync; game state can be exported as a binary snapshot with one click and restored in milliseconds.
**Disadvantages**: Sandbox restrictions preclude advanced rumble feedback on some USB controllers and special hardware peripherals.

**Competitors**: Pure-JS emulators (dynamic type conversion and irregular GC pauses cause slight tearing and audio dropouts); local RetroArch (the most feature-complete, but requires installation and configuration).

---

### 20. (originally 20) Libzen-Wasm (MediaInfo) — Deep multimedia metadata parsing 🟡

**Pain point**: Video professionals often need to inspect a media file's detailed parameters (codec, bitrate, frame rate, colour space, audio tracks, subtitle packaging). Modern containers (`.MKV`, `.MP4`) may scatter metadata at the very start or the very end of the file, and uploading gigabytes of video or transferring it in frequent chunks burns enormous bandwidth.

**How it works**: C++ MediaInfo (built on libzen and libmediainfo) is compiled to Wasm. **Range reads**: when the user drops in a 4 GB video, JS uses the HTML5 File API to **extract only the header and footer of the file structure precisely** (the MP4 `moov` atom, for instance). **Binary structure destructuring**: JS passes those fragments into Wasm, and the parser inside takes apart the container's binary tables within microseconds, returning hundreds of structured parameters as JSON.

**Performance**: Claimed that parsing a 5 GB 4K video with multiple audio channels and embedded subtitles takes no more than **10 milliseconds** and under 5 MB of memory.

**Advantages**: Analyzes videos of any size on the front end in seconds with minimal resources; saves 100% of server bandwidth.
**Disadvantages**: For corrupted containers or rare formats, if the exception handling wasn't fully optimized at compile time, the module can crash outright.

**Competitors**: mp4box.js (usually MP4 only, helpless before MKV, AVI, MOV and FLV); backend FFprobe (powerful, but I/O and CPU saturate under concurrency, and the user endures a long upload).

---

### 21. (originally 21) Viz.js / Web-Graphviz — Automatic graph layout for the DOT language 🟢

**Pain point**: Graphviz generates flowcharts, topology diagrams and dependency graphs from DOT scripts, and its core value is a powerful automatic layout algorithm. Before Wasm, converting DOT to SVG live on a page meant a round trip to a backend; pure-JS graph libraries (vis.js) lack the compute for thousands of nodes and edges and freeze the page for seconds.

**How it works**: Graphviz's C-language layout engine (including the dot, neato and twopi engines) is compiled to Wasm via Emscripten. The user types DOT syntax and JS passes the string in through a memory pointer; Wasm builds the graph's adjacency matrix and runs hierarchy assignment, force-directed stress relaxation and coordinate allocation; when finished it generates a standard SVG text stream directly in linear memory, which JS extracts and inserts into the DOM.

**Performance**: Claimed that a complex dependency graph of 500 nodes and 2,000 edges lays out in **30–50 milliseconds**, more than **20× faster** than pure-JS layout algorithms.

**Advantages**: Brings live diagram rendering to a static documentation platform, with no backend drawing server.
**Disadvantages**: Graphviz's native code is large, so the compiled Wasm is usually **2–3 MB**.

**Competitors**: Mermaid.js (the most popular on the front end, small and with a good ecosystem, but clearly inferior to Graphviz-Wasm in both performance and layout quality on very large dense topologies).

---

### 22. (originally 22) Web-7z (p7zip-wasm) — A high-ratio decompression engine 🟡

**Pain point**: When a page has to handle `.7z`, `.rar` or `.tar.xz` — high compression ratio formats — the traditional route uploads to a backend to unpack. Large archives devour bandwidth, and the dense computation of decompression saturates backend CPU fast.

**How it works**: p7zip (7-Zip's Linux C/C++ port) is compiled to Wasm. **Streaming decompression architecture**: the user drops in a `.7z`, and JS reads the binary byte stream through the File API and writes it into Wasm's MEMFS. Based on the header, Wasm calls the corresponding LZMA, LZMA2 or PPMd algorithm, doing dictionary matching and decompression directly in linear memory, then returns each file's binary stream to the front end to make a download link.

**Performance**: Claimed that unpacking a standard 50 MB `.7z` reaches **70%–80%** of native C for LZMA2 decoding.

**Advantages**: Fully decentralized — the trade secrets inside the archive never leave the device; it solves the pain point that static pages cannot handle the complex `.7z` format.
**Disadvantages**: Bounded by the memory ceiling — **if unpacking needs a huge dictionary (a 1 GB dictionary size, say), Wasm cannot get enough linear memory and the tab crashes** (Chapter 8's 4 GB ceiling made concrete).

**Competitors**: JSZip (a popular front-end ZIP library, small, but **with no 7z/RAR support at all** and very slow on large files).

---

### 23. (originally 23) Web-Sass (sass.wasm / grass) — CSS preprocessor compilation 🟢

**Pain point**: Offering live SCSS compilation on a static page (an online sandbox, a teaching platform) previously required a Node.js environment. Early JS versions were unbearably slow parsing complex `@import`, nested selectors and mixins.

**How it works**: `grass` (written in Rust) or `libsass` (C++) is compiled to Wasm. The user edits SCSS, JS converts the string to binary and passes it in; the high-speed parser inside Wasm tokenizes, builds a compact AST in memory, performs variable substitution, nesting expansion and reduction, and assembles the final CSS in linear memory to return.

**Performance**: Claimed that compiling thousands of lines of SCSS with complex mixins and variable arithmetic takes only **5–10 milliseconds**, **15–30× faster** than the pure-JS version — "compile as you type."

**Advantages**: Delivers a compilation experience nearly identical to the local native binary; an online compilation tool on a static page needs no backend API at all.
**Disadvantages**: If the SCSS depends on many remote images or external stylesheets, the sandboxed Wasm needs external JS to handle those network requests, increasing glue complexity.

**Competitors**: The official Dart Sass compiled to JS (perfect compatibility, but without strict type optimization its compile performance on large files trails the Wasm build).

---

### 24. (originally 24) Web-Gnuplot — A scientific statistical plotting engine 🟡

**Pain point**: Gnuplot is the well-known command-line scientific plotting program, supporting complex mathematical formula plotting, three-dimensional surface fitting and statistical analysis. Sharing and live-tweaking scripts on the web previously meant standing up a Linux server to generate images and send them back; under concurrency the backend buckles under 3D mesh matrix computation.

**How it works**: The long-lived C-language Gnuplot is compiled to Wasm in full. The user types a command (`splot sin(x)*cos(y)`, say), the C-language syntax parser inside Wasm parses the mathematical expression directly, and hundreds of thousands of floating-point operations run in linear memory to generate the 3D vertex matrix. Gnuplot's native plotting terminal output is redirected: Wasm emits a Canvas 2D/WebGL drawing command stream directly, or returns high-resolution SVG.

**Performance**: Claimed that the dense floating-point matrix work for 3D surface fitting and lighting reaches **80%** of native C, redrawing a detailed chart within **20 milliseconds**.

**Advantages**: Recreates thirty-odd years of accumulated industrial-grade scientific plotting on a free static page; the data stays entirely local.
**Disadvantages**: Without a modern UI wrapper, Gnuplot's command-line logic has a very steep learning curve for ordinary users.

**Competitors**: Chart.js / ECharts (good for business and financial charts, but no comparison at all when faced with hardcore academic formula plotting, complex arithmetic or high-precision 3D scientific fitting).

---

### 25. (originally 25) Web-Esprima / oxc-wasm — JS syntax analysis and AST generation 🟢

**Pain point**: Building a web-based code editor (Monaco Editor), linter or highlighting engine requires parsing JS into an AST in real time. When the user pastes in a huge third-party library of tens of thousands of lines, a pure-JS parser causes severe GC stutter creating hundreds of thousands of AST node objects.

**How it works**: An ultra-fast JS parser written in C++/Rust (part of `oxc`, for instance) is compiled to Wasm. **Object-free AST layout** (this is the core of Wasm's dominance over JS here): while parsing, Wasm creates no object per node; instead AST nodes sit compactly in a contiguous memory block (a memory pool), with nodes linked to each other by 4-byte integer indices alone. Tokenization and syntax tree construction happen entirely inside the Wasm sandbox, exposing only the core result to the front end as a `TypedArray`.

**Performance**: Claimed to parse a 5 MB JS file in **15–20 milliseconds** (a pure-JS parser needs 300–500 milliseconds) — more than **20× faster**, with zero GC impact on the main thread.

**Advantages**: Brings smooth live syntax checking and error highlighting to front-end editors.
**Disadvantages**: The AST lives in Wasm memory, so if front-end JS wants to traverse that tree deeply and often, cross-boundary serialization/deserialization adds overhead.

**Competitors**: Babel Parser (the most powerful with the richest plugin set, but far behind in memory consumption and parse speed when handling large sources purely on the front end).

---

### 26. (originally 31) Web-Jq (jq-wasm) — High-speed JSON filtering and transformation 🟢

**Pain point**: `jq` is the command line's JSON power tool, able to slice, filter and map complex JSON through a powerful DSL. But offering an online JSON playground on the web with a pure-JS approach means that a several-hundred-megabyte JSON log creates millions of JS objects, causing GC stutters of several seconds or an outright tab crash.

**How it works**: The C-language jq core is compiled to Wasm via Emscripten. **Streaming memory destructuring**: when the user pastes a huge JSON or uploads a file, JS writes the byte stream straight into Wasm's contiguous memory through a shared buffer. **DSL engine parsing**: Wasm parses the filter expression live (`.items[] | select(.status == "active")`, say) and traverses the compactly laid-out binary JSON tree in memory at high speed (**creating no JS objects**), returning the result as a string.

**Performance**: Claimed that a 100 MB-class complex JSON file parses, filters and transforms in **80–150 milliseconds**, **15–25× faster** than pure JS.

**Advantages**: Fully decentralized, zero backend cost, second-scale processing of large JSON; meets the requirement that highly sensitive logs never leave the device.
**Disadvantages**: JS↔Wasm string boundary passing adds overhead when handling extremely frequent tiny queries, so large batches must be used to optimize.

**Competitors**: Native `JSON.parse` plus a custom filter (light for small files, but memory and CPU peaks explode exponentially for large log structures past a few hundred thousand lines).

---

### 27. (originally 36) OpenCV.js (Wasm) — Industrial computer vision and matrix math 🟢

**Pain point**: For real-time image processing on the web (recognizing the outline of a handheld credit card, say), pure-JS graphics libraries (tracking.js) are woefully unoptimized; JS lacks compact multidimensional matrix layouts and direct pointer control, so iterating the millions of pixels in 1080p triggers severe GC stutter and cannot meet interactive real-time requirements.

**How it works**: Millions of lines of C++ OpenCV core are cross-compiled to `opencv.wasm` via Emscripten, with the underlying `cv::Mat` matrix structure mapped to the front end. **Zero-copy image flow**: the `ImageData` pointer for each frame captured from an HTML5 video is written directly into Wasm linear memory, eliminating copy overhead. **Hardware-level operator acceleration**: SIMD is enabled internally, so a single CPU instruction handles greyscale conversion (Canny), Gaussian filtering or Sobel operators on four pixels at once.

**Performance**: Claimed that on a 720p live video stream, ORB feature detection takes only **12–15 milliseconds**, easily holding 60 FPS — more than **20×** the pure-JS version.

**Advantages**: Perfect privacy protection (ID scanning and the like never leave the device); static hosting alone deploys a massively concurrent CV application.
**Disadvantages**: OpenCV is vast, so the compiled Wasm plus glue is still **6–9 MB** compressed, usually requiring dynamic lazy loading.

**Competitors**: tracking.js (small but crude, lacking high-order matrix transforms, feature matching and optical flow); cloud vision APIs (accurate, but with latency, metering and privacy risk).

---

### 28. (originally 37) solc-wasm — The Ethereum smart contract compiler 🟢

**Pain point**: Blockchain developers must turn Solidity into EVM bytecode. Traditionally that meant installing the `solc` binary, or having the front end send code to a remote server to compile — and for a web environment like Remix IDE, depending on a backend compile server means operating cost and easy collapse under load or attack.

**How it works**: The Ethereum Foundation compiles the official C++ Solidity compiler into `soljson.wasm`. When the user clicks compile, JS passes the Solidity source string into Wasm memory; Wasm performs lexical analysis, parsing, AST construction and type checking, and emits EVM-compatible bytecode, the ABI interface definition and source maps directly in linear memory.

**Performance**: Claimed that compiling a standard ERC-20 contract takes only **100–300 milliseconds**, reaching **80%** of the local native binary.

**Advantages**: Gives a DApp's online IDE (Remix, for instance) fully backend-free, zero-operations compilation; code compiles locally, so unpublished contracts can't be intercepted by a third party.
**Disadvantages**: Because it includes a large optimizer and cryptographic components, `soljson.wasm` is very large (usually **10–15 MB**), so first load is slow.

**Competitors**: A backend compile API (the page loads fast, but there is downtime, service interruption and contract leakage risk).

---

### 29. (originally 38) xterm's Wasm parsing plugin — Million-line log terminal rendering 🟡

**Pain point**: Watching live container logs scroll by on the web (a Kubernetes console, a cloud shell), the backend sends hundreds of kilobytes of ANSI escape sequences per second. Doing all that string parsing, UTF-8 decoding and screen buffer management, mainstream xterm.js triggers severe GC and freezes the UI outright.

**How it works**: The terminal's most critical component — the **ANSI sequence parser and state machine** — is rewritten in C++/Rust and compiled to Wasm as a performance plugin for xterm.js. **Raw binary byte stream passthrough**: raw bytes arriving over WebSocket skip JS string conversion and are written into Wasm memory as a `Uint8Array` directly. **An efficient state machine**: Wasm recognizes control sequences like `\x1b[31m` at high speed with a statically typed integer state machine, maintaining the virtual screen's two-dimensional array in binary form in linear memory, and notifying JS's WebGL rendering layer only of what changed per frame.

**Performance**: Claimed **10–15× higher throughput** than pure-JS regex parsing in an extreme "log storm" test; a steady 60 FPS while processing 500,000 lines of ANSI characters per second, with CPU usage down 70%.

**Advantages**: Definitively solves the problem of a web terminal freezing under heavy log traffic; substantially improves the battery life and smoothness of running a cloud console on a low-end laptop.
**Disadvantages**: Solidifying originally flexible JS parsing logic into Wasm makes it less agile to upgrade if a new non-standard escape extension protocol appears.

**Competitors**: The pure-JS xterm.js parser (perfect compatibility and easy to extend, but it OOMs on millions of lines of CI/CD build logs).

---

### 30. (originally 39) HarfBuzz.js (Wasm) — A complex text shaping and layout engine 🟢

**Pain point**: "Text shaping" turns Unicode characters into a font's glyphs at precise geometric coordinates, and it is indispensable for scripts with complex ligatures and dynamic forms such as Arabic, Indic languages and Thai. The browser's native layout is strong, but in Canvas 2D/WebGL, a web game engine or online PDF generation, developers cannot call into the browser's layout internals, so complex scripts come out misplaced, mis-broken or with broken ligatures.

**How it works**: **HarfBuzz** — the world's foremost open-source text shaping engine, written in C++, and the underlying dependency for both Chrome and Android — is compiled to Wasm. JS passes the Unicode string to lay out plus a binary pointer to the OpenType font into Wasm; Wasm parses the font's `GSUB` (glyph substitution) and `GPOS` (glyph positioning) tables deeply in linear memory, computes each character's X/Y offset and advance precisely, and returns a structured array of glyph IDs and coordinates that WebGL draws directly.

**Performance**: Claimed that for large-scale Arabic or Thai layout, the ligature mathematics is nearly indistinguishable from the local system in efficiency, handling hundreds of thousands of characters per second and more than **30× faster** than a JS-simulated layout engine.

**Advantages**: Guarantees 100% pixel-identical and correct layout of complex scripts across every browser, canvas and exported PDF, filling a major gap in web graphics.
**Disadvantages**: An extremely vertical, specialized tool with a very low-level API; a front-end engineer needs deep typographic knowledge to integrate it successfully.

**Competitors**: Home-grown layout on opentype.js (supports only simple Latin letters, and produces entirely wrong results for context-aware Arabic or Indic scripts).

---

### 31. (originally 40) Z-Music (libgme-wasm) — Retro console audio chip emulation 🟡

**Pain point**: Playing early consoles' native music (the NES's Ricoh 2A03, the SNES's SPC700, the Mega Drive's YM2612; formats such as `.nsf`, `.spc`, `.vgm`) is enchanting — these files are only a few kilobytes because they are instructions driving hardware directly. But emulating those chips' filters and waveform generators in pure JS produces constant popping from imprecise timers and dynamic typing, at an unreasonably high CPU cost.

**How it works**: The C++ audio chip emulation library **Game Music Emulator (GME)** is compiled to Wasm and deployed with an **AudioWorklet**. **Thread isolation**: Wasm loads onto the highest-priority dedicated audio thread, entirely undisturbed by UI rendering, scrolling or main-thread blocking. **Register-level hardware emulation**: Wasm emulates those old chips' internal register state in linear memory, computing 44,100 waveform floats per second at 44.1 kHz and mixing square, triangle, noise channels and PCM samples dynamically.

**Performance**: Claimed that emulating a complex 16-bit SNES audio chip consumes under **0.5% of CPU**, with audio buffer computation taking under 0.05 milliseconds.

**Advantages**: Perfectly revives retro hardware audio at minimal overhead; a few kilobytes of audio file and a whole game soundtrack starts playing.
**Disadvantages**: A corrupt, non-standard ROM easily triggers memory overruns, so strict sandbox bounds checking is required.

**Competitors**: Traditional MP3/OGG playback (over 1000× larger, and losing the hardware-level interactive fun of toggling tracks live or changing tempo without changing pitch); pure-JS audio emulators (disturbed by GC pauses, dropping out and popping the moment the user scrolls the page).

---

### 32. (originally 41) Stockfish.wasm — A world-class chess AI engine 🟢

**Pain point**: Stockfish's competitive edge lies in dense alpha-beta pruning search, NNUE neural network evaluation and massive bitboard arithmetic. Providing strong analysis on the web previously meant sending it to a backend CPU server fleet — enormous maintenance cost, and compute saturated instantly when tens of thousands of players analyzed at once.

**How it works**: The C++17 Stockfish source is compiled to Wasm via Emscripten as the front-end analysis engine for mainstream chess sites (Lichess, for instance). **Multithreaded and SIMD architecture**: Web Workers plus `SharedArrayBuffer` provide massively parallel search, with SIMD internally accelerating NNUE's weight matrix multiplications. **Bitboard passthrough**: board state is represented as `i64` in linear memory, and bitmask plus bit-scan instructions enumerate millions of legal moves instantly.

**Performance**: Claimed that with SIMD and 4 cores, search speed (NPS) reaches **75%–85%** of native C++, computing millions to tens of millions of positions per second on the front end at depths past 20 plies.

**Advantages**: Genuinely decentralized — static hosting alone provides world-class AI analysis at zero server compute cost; usable offline, with no network latency.
**Disadvantages**: NNUE weight files typically run from a few to a dozen-odd megabytes; heavy search saturates the user's CPU, heating the device and draining the battery. **And it is the textbook case of needing `SharedArrayBuffer` — on GitHub Pages it must be paired with `coi-serviceworker`.**

**Competitors**: Pure-JS chess engines (capable only of elementary calculation and utterly outclassed in complex endgames); backend cloud analysis (unlimited compute, but unable to serve millions of players' free concurrent demand).

---

### 33. (originally 42) Web-GnuTLS (Wasm-TLS) — A front-end TLS micro network stack 🟡

**Pain point**: When building a backend-free, decentralized web application (a P2P network, a browser-side MQTT console), the front end sometimes needs to establish a secure TLS connection directly with an external TCP/UDP server (through a WebSocket relay). But the browser's own `fetch` security mechanism is very strict and **does not let developers customize certificate validation, cipher suite negotiation or private CA registration during the TLS handshake**.

**How it works**: C-language GnuTLS is compiled to Wasm in full, building a "micro encrypted network stack" entirely under front-end control on a static page. **Memory-buffer network I/O (BIO mode)**: Wasm never calls a system network API directly; instead it writes TLS handshake packets into a ring buffer in memory, and external JS extracts and sends them over WebSocket or a WebRTC data channel. **Cryptographic operator acceleration**: the TLS handshake involves heavy asymmetric (ECDHE, RSA) and symmetric (AES-GCM, ChaCha20-Poly1305) work, and Wasm performs bignum multiplication at high speed inside the sandbox using 64-bit integer operations and compact layout.

**Performance**: Claimed a complete TLS 1.3 handshake and key exchange in no more than **5–10 milliseconds**, with throughput on par with the local C build and more than **10× faster** than pure-JS crypto libraries.

**Advantages**: Breaks the browser's black-box hold on the network security protocol layer, allowing custom certificate validation and mutual TLS (mTLS) on a static page; keys never leave the device.
**Disadvantages**: A TLS network stack is extremely complex and the Wasm module is fairly large; and because it cannot touch sockets directly, complex JS glue must be written for packet forwarding and reassembly.

**Competitors**: Pure-JS cryptographic protocol libraries (forge and the like, able to emulate parts of the TLS flow, but with GC stutter under high-frequency encrypted packet throughput and inadequate TLS 1.3 support and security).

---

### 34. (originally 43) QuickJS-Wasm — A secure sandboxed "JS inside JS" runtime 🟢

**Pain point**: Online playgrounds, low-code platforms and applications with user-authored plugins need to "run user-supplied JavaScript" on the front end. Using `eval()` or `new Function()` directly lets user code reach `window`, `document` and `cookie`, a fatal XSS risk. Even with iframe isolation, an attacker can still freeze the main thread solid with `while(true)`.

**How it works**: **QuickJS** — the small, efficient C-language JS engine written by Fabrice Bellard — is compiled to Wasm in full, achieving the elegant trick of "running another JavaScript inside JavaScript." **Double sandbox**: the user's script does not execute in the browser's native V8; it is passed into QuickJS-Wasm as a string and interpreted inside Wasm's enclosed linear memory sandbox, **entirely unable to reach any DOM or sensitive information on the outer page**. **Time and memory quotas**: the Wasm module installs an interrupt handler internally, and if user code exceeds its quota (500 milliseconds, say) or requests too much memory, it is terminated immediately — perfectly preventing an infinite loop from freezing the page.

**Performance**: Although it interprets, QuickJS is extremely light, running standard JS inside Wasm at millions of instructions per second — enough for complex business logic, unit tests or data transformation to run smoothly.

**Advantages**: Brings a military-grade secure code execution environment to a static page, eliminating XSS and infinite loops entirely; a few hundred kilobytes compressed, so it loads fast.
**Disadvantages**: As an "interpreter inside an interpreter," it cannot match JIT-optimized native V8 (usually 10–20× slower) and is unsuited to heavy graphics or matrix work.

**Competitors**: Native `eval()` / iframe sandboxing (highest performance, but a fragile security boundary that is very hard to defend against advanced exploits and malicious infinite loops); a JS interpreter written in JS (similar size, but far behind QuickJS in syntax coverage and the completeness of memory quota control).

---

### 35. (originally 44) Web-GSL — The GNU Scientific Library's numerical analysis and matrix routines 🟡

**Pain point**: Engineering, physics and quantitative finance routinely need complex numerical computation: high-order matrix eigenvalue solving, numerical solutions to ordinary differential equations (ODEs), least-squares fitting, fast Fourier transforms (FFT), sampling from complex statistical distributions. Traditionally that relies on the authoritative C library **GSL**. Writing those formulas by hand over JS float arrays is not only slow — for lack of operator overloading, compact memory alignment and fast pointer arithmetic — but also prone to producing scientifically wrong results through lost floating-point precision.

**How it works**: The vast, rigorous C-language GNU Scientific Library core is compiled to Wasm in full, creating an online scientific numerical workbench. **Exact memory layout (BLAS integration)**: efficient basic linear algebra subprograms (CBLAS) are integrated internally, with multidimensional matrices laid out as strictly aligned contiguous double-precision floats (`f64`) to maximize L1/L2 cache hit rates. **Zero GC interference**: every differential equation approximation and nonlinear least-squares iteration runs entirely inside Wasm's internal memory pool.

**Performance**: Claimed **80%–90%** of native C when solving the eigenvalues of a 500×500 matrix or running a million-point FFT, **20–40× faster** than pure-JS numerical libraries.

**Advantages**: Brings an install-free, entirely free industrial-grade numerical computation platform to education, research and financial engineering, at precision matching GNU's international scientific standards.
**Disadvantages**: GSL's API is highly academic and extremely low-level, offering none of the chained calls or JSON interfaces modern front-end developers expect, so a fairly heavy JS wrapper layer is required.

**Competitors**: math.js (fine for everyday algebra and ordinary plotting, but no comparison at all for hardcore industrial ODE solving, large sparse matrices and high-precision numerical fitting).

---

> **Summary of this part (1–35)**: The first 35 cases cluster in three areas — **audio/video signal processing, data querying, and parsers and toolchains** — and form **the most verifiable stretch** of the Wasm ecosystem: FFmpeg.wasm, v86, Pyodide, DuckDB-Wasm, SQLite-Wasm, esbuild, swc, OpenCV.js, Tesseract.js, solc, Stockfish, HarfBuzz, QuickJS and Viz.js are every one of them real, widely used projects.
> Their shape is remarkably consistent: **move a mature C/C++/Rust core into linear memory, hand off to JS through zero-copy views, and add SIMD and Workers where needed**. The only difference is which wall each of them hits — **FFmpeg hits the memory ceiling, Pyodide hits download size, Stockfish hits `SharedArrayBuffer`, OpenCascade hits module size**.
> The next part (36–70) moves into **compression, geography, cryptography, graph algebra and reverse engineering**, where the proportion of 🟡 entries begins to rise.
