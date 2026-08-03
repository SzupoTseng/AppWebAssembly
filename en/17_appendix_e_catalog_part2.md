# Appendix E: The Hundred-Case Catalog of Static-Page Wasm (Part 2) — Cases 36–70

> Authenticity tags and reading method are the same as Appendix D. 🟢 Verifiable · 🟡 Upstream real, Wasm port unverified · 🔴 Illustrative construction. **All performance numbers are claims from the original conversation and have not been independently verified.**

---

## III. Fonts, Media Codecs and Compression

### 36. (originally 45) Web-Graphite (Graphite2-Wasm) — Smart typesetting for minority-language scripts 🟡

**Pain point**: Many of the world's special scripts (Burmese, Khmer, North American indigenous writing systems, and non-Latin typefaces with complex contextual shaping rules) use the **Graphite typesetting system** — a smart-font technology more flexible than OpenType, with its own rule description language. Firefox has native Graphite support, but **Chrome and Safari have none at all**, so pages presenting minority-culture material come out completely scrambled in different browsers.

**How it works**: The C++ Graphite2 smart-font layout core is compiled to Wasm, providing a browser-universal layout solution in a static environment. JS passes the complex Unicode text and the Graphite-capable `.ttf` into Wasm memory; the Graphite2 engine inside executes the complex state-machine rules embedded in the font, dynamically reconstructing glyph chains and adjusting overlap coordinates and baseline offsets. When done it outputs precise glyph outline indices and a pixel geometry matrix, and the front end draws pixel-accurately through the Canvas API, bypassing the defects of the browser's native layout engine.

**Performance**: Claimed that shaping and computing bounds for an entire Khmer document of tens of thousands of characters completes in **10–15 milliseconds**, more than **35× faster** than JS emulation.

**Advantages**: A perfect cultural preservation technology, definitively solving the historical pain of Chrome/Safari being unable to render Graphite smart fonts correctly; static hosting alone builds a display site for the world's minority-language documents.
**Disadvantages**: A highly specialized vertical tool, with steep costs to understand layout debugging and the font's embedded rules.

**Competitors**: Native OpenType / HarfBuzz (the mainstream standard for web layout, but less expressive than Graphite for historical documents needing extremely flexible contextual rules).

---

### 37. (originally 46) Web-libvpx / dav1d-wasm — A next-generation video decoding engine 🟡

**Pain point**: Modern web pages depend heavily on high-quality compression formats such as VP9 and AV1, but many older operating systems, mobile devices and particular browsers **have no hardware decoder for them**. Parsing AV1's complex bitstream and computing pixel prediction directly in JS is astonishingly slow, causing severe dropped frames or freezing the main thread outright.

**How it works**: Google's open-source codec core **libvpx** (or AV1's **dav1d**, written in C and assembly) is compiled to Wasm via Emscripten as a fallback decoding engine for the browser's MSE (Media Source Extensions). **Multithreaded pixel decoding**: Web Workers plus `SharedArrayBuffer` split decoding tasks (intra prediction, inverse DCT) into parallel blocks. **SIMD vector optimization**: a single CPU instruction handles deblocking filter work for 4 or 8 pixel groups at once, writing decoded raw YUV pixels straight into memory.

**Performance**: Claimed that with SIMD and threads on, 1080p VP9/AV1 decodes in software at **30–45 FPS** on a low-end machine with no hardware acceleration at all, reaching **70%** of native C.

**Advantages**: Gives a static media platform "cross-browser, 100% format-compatible" playback independent of the host's hardware chips; fully usable offline.
**Disadvantages**: Software decoding is very CPU-hungry, and decoding 1080p in software for long stretches heats the device up substantially, drawing far more power than hardware decoding.

**Competitors**: Native `<video>` (highest performance and very power-efficient, but shows a black screen or errors outright for an AV1 or specific codec the device doesn't support).

---

### 38. (originally 47) Hjson-Wasm — Human-friendly configuration syntax transpilation 🟡

**Pain point**: Standard JSON syntax is harsh (no comments, strings must use double quotes, no trailing commas), which is very unfriendly to humans, so the community produced **Hjson (Human JSON)**. Converting Hjson to standard JSON live on a static page with a pure-JS parser causes typing latency in the editor for very large configurations of tens of thousands of lines (complex game level data, enterprise architecture definitions), from constant string slicing and GC.

**How it works**: The `hjson` core, written in Rust (or C), is compiled to Wasm. **Zero-copy lexical scanning**: the user's Hjson text is passed in by JS through a memory pointer, and the Rust parser inside Wasm **creates no intermediate string objects at all**, instead doing lexical analysis directly on the raw byte stream using pointer offsets. **AST memory pool**: a highly compact syntax tree is built in linear memory, and after stripping every comment and whitespace character, standard JSON is formatted straight out.

**Performance**: Claimed that transpiling a 10 MB Hjson with deep nesting and many comments takes only **8–12 milliseconds**, more than **20× faster** than the pure-JS version, with main-thread GC pauses reduced to zero.

**Advantages**: Brings zero-latency live configuration syntax validation and conversion to front-end editors (as a Monaco Editor plugin, for instance).
**Disadvantages**: A relatively vertical syntax tool — **if the configuration file itself is only a few kilobytes, Wasm's initial load overhead outweighs any performance it brings** (a textbook counterexample to Chapter 3's "performance advantage has a compute-volume threshold").

**Competitors**: A pure-JS Hjson parser (flexible and easy to integrate, but with exponentially exploding memory and CPU peaks for large-scale generated configurations or bulk data cleaning).

---

### 39. (originally 48) Web-Proj (PROJ-Wasm) — Map projection and geographic coordinate transformation 🟡

**Pain point**: In GIS development, converting global geographic coordinates (WGS84 latitude/longitude) to a country's engineering projection (Taiwan's TWD97 two-degree zone, say) requires complex geodesy and high-order spherical trigonometry, usually relying on the authoritative C/C++ library **PROJ**. Processing large GIS point clouds or cadastral maps on a static page previously meant a round trip to a backend geographic server (GeoServer), since pure-JS coordinate transforms are imprecise and slow.

**How it works**: PROJ is compiled to Wasm in full, providing a decentralized workbench for exact coordinate transformation. **High-precision floating-point matrices**: contiguous `f64` memory is configured internally, and millions of point coordinates (X, Y, Z) are written directly as `TypedArray`s. **Dynamic datum transformation**: Wasm performs complex 3D affine transformations, the Molodensky model and grid distortion corrections entirely at the binary level.

**Performance**: Claimed to complete a full coordinate system reprojection of a geographic dataset containing a million points in **40 milliseconds**, more than **25× faster** than pure-JS geographic libraries.

**Advantages**: Brings static map analysis tools the precision and efficiency of desktop GIS (QGIS); government cadastral or commercial point-cloud data never leaves the device.
**Disadvantages**: PROJ depends on a large geodetic grid database (grid files, correcting gravitational distortion in specific regions), and those files are fairly large and must be downloaded dynamically by the front end with range requests.

**Competitors**: proj4js (lightweight and fine for ordinary web map display, but no comparison at all in performance or precision for multimillion-point clouds or industrial cartography needing global high-precision grid corrections).

---

### 40. (originally 49) Brotli-Wasm — Brotli codec at extreme compression ratios 🟢

**Pain point**: Brotli is Google's modern lossless compression algorithm, with a compression ratio well beyond Gzip. Although browsers natively support Brotli decompression at the **HTTP transport layer**, they **do not expose a native Brotli API to front-end JavaScript**. That means if you want to compress user data to a tiny file for IndexedDB inside a page, or manually decompress a custom `.br` file, pure JS cannot call the engine the browser already ships.

**How it works**: Google's official C-language Brotli codec core is compiled to Wasm, opening the low-level compression API to the front end directly. **Sliding-window memory optimization**: Brotli depends heavily on a huge sliding window (up to 16 MB) for context modelling, and Wasm allocates that contiguous space directly in linear memory, running high-speed Huffman coding and binary byte-stream matching. **Object-free streaming compression**: data streams in as binary byte blocks, and Wasm spits out a `Uint8Array` when done, creating no JS garbage objects at any point.

**Performance**: Claimed **85%** of native C when compressing or decompressing 20 MB of plain text or JSON, taking only **30–50 milliseconds**, nearly **15× faster** than pure-JS Brotli emulation libraries.

**Advantages**: Breaks through the browser's API blockade, giving a static application the ability to run top-tier lossless compression inside the browser; excellent for optimizing a PWA's offline cache footprint.
**Disadvantages**: Brotli's highest compression level (Quality 11) is computationally brutal, and blindly enabling it on the front end causes a brief main-thread freeze, so **it usually must run inside a Web Worker**.

**Competitors**: Pure-JS Brotli implementations (lacking efficient bit operations and compact memory, with CPU peaks that are too high on large files).

---

### 41. (originally 50) libFLAC-Wasm — Real-time high-fidelity lossless audio encoding 🟡

**Pain point**: When a user records through a microphone on a web page (an online podcast tool, a music creation sandbox), the browser natively supports only lossy Opus/WebM, or entirely uncompressed and enormous WAV. Saving the sound as **FLAC** — the world's mainstream lossless format — purely on the front end is impossible in pure JS: it cannot compute dense linear predictive coding (LPC) and Huffman residual encoding in real time while recording, so frames drop and the audio breaks up.

**How it works**: The official C-language **libFLAC** core is compiled to Wasm and integrated deeply with an **AudioWorklet** (the high-priority audio thread). **A real-time streaming audio stack**: raw PCM captured from the microphone is written into a Wasm memory pointer by the JS inside the AudioWorklet with no delay. **A dense mathematical budget**: the libFLAC encoder inside Wasm immediately performs lattice analysis, mid-side channel coupling and residual compression, packing FLAC bitstream within microseconds.

**Performance**: Claimed that Wasm's encoding time on the audio thread stays under **0.1 milliseconds** at under **1% CPU**, perfectly generating 24-bit/96 kHz high-fidelity FLAC while recording.

**Advantages**: Brings broadcast-grade lossless recording to static recording and music platforms, with no backend audio processing server at all.
**Disadvantages**: FLAC encoding is very demanding of memory stability and needs carefully configured linear memory; if the input channel count or sample rate changes abruptly and the glue doesn't handle it, memory corruption follows easily.

**Competitors**: Pure-JS FLAC encoders (disrupted by irregular GC pauses so they fall behind whenever the page animates or the user clicks, producing severe dropouts and pops in the recording).

---

## IV. Graph Algebra, Document Conversion and Reverse Engineering

### 42. (originally 51) Web-Biconical — Planarizing layout of biconnected components in large graphs 🔴

**Pain point**: In network security (tracing attack paths), bioinformatics (protein interaction networks) and blockchain transaction tracing, engineers often need planarizing layout of "giant graphs" with tens of thousands of nodes and complex cyclic structures. Computing biconnected components, strongly connected components and a centroid spring model in a pure-JS graph library (Cytoscape.js) means dense pointer chasing and array addressing, triggering severe dynamic allocation and GC that freeze the page or exhaust memory outright.

**How it works**: An academic C++ high-performance graph algorithm core is compiled to Wasm. **Contiguous graph layout in memory**: nodes and edges no longer live as discrete JS objects but are compressed into cache-friendly contiguous arrays (**CSR, Compressed Sparse Row** format), maximizing L1/L2 hit rates. **Parallel topological divide-and-conquer**: threads split the giant graph into several independent biconnected subgraphs, and different Workers perform crossing-minimization computations in step.

**Performance**: Claimed to lay out a very large attack-chain topology of 50,000 nodes and 150,000 edges in **180–250 milliseconds**, more than **40× faster** than the fastest pure-JS graph algorithms.

**Advantages**: Allows exploring million-scale big-data graphs directly on a static dashboard; a government or large enterprise's network topology data never leaves.
**Disadvantages**: The memory layout is extremely abstract and low-level, and **if the front end frequently adds or removes individual nodes, re-aligning memory is expensive** — so it suits one-off analysis or large batch updates better.

**Competitors**: d3-force / vis.js (fine for small interactive graphs under 1,000 nodes, but the page freezes solid on industrial topologies of tens of thousands).

---

### 43. (originally 52) pulldown-cmark-wasm — Million-word-scale Markdown parsing 🟢

**Pain point**: Modern documentation platforms need to render very long Markdown live. Pure-JS parsers (markdown-it, marked) are popular, but when a user pastes in a "million-word specification" of tens of thousands of words with heavily nested tables, code blocks and mathematical formulas, regex matching and constant string slicing saturate the CPU and make typing stutter.

**How it works**: **pulldown-cmark**, the industrial-grade Markdown parser core written in Rust, is compiled to Wasm. **Streaming event parsing**: Wasm abandons the heavy AST object tree for a pull-based event stream — reading the raw byte stream, it only advances a pointer in linear memory and emits token events dynamically. **Zero-copy HTML generation**: parsing creates no intermediate JS string objects; Wasm translates Markdown straight into a binary HTML byte array, converted once at the end into a large string injected into the DOM.

**Performance**: Claimed to parse a million-word technical manual in **15–25 milliseconds**, **25–35× faster** than the pure-JS version, achieving latency-free live synchronized preview.

**Advantages**: Brings latency-free live transpilation and search to static documentation sites, handling extreme text volumes with ease.
**Disadvantages**: As a compiled binary module, it is harder to extend than a pure-JS parser if a developer wants to add non-standard syntax plugins dynamically.

**Competitors**: Pure-JS Markdown parsers (rich ecosystem, plugins everywhere, but a clear performance bottleneck on very large documents past tens of thousands of lines).

---

### 44. (originally 53) Zstd-Wasm — High-speed compression and decompression for big data 🟢

**Pain point**: Zstandard (Zstd) is Facebook's real-time lossless compression algorithm, matching or beating Gzip's ratio with astonishing decompression speed, and it has become standard in backend and big-data ecosystems (Hadoop, Kafka, Parquet). But **browsers still expose no native Zstd API to the front end**. When the front end must download and decompress hundreds of megabytes of structured big data, telemetry logs or 3D game assets from a static site, JS-emulated Zstd cannot come close to the algorithm's physical limits.

**How it works**: Facebook's official C-language Zstd codec core is compiled to Wasm in full. **Finite state entropy (FSE) decoding**: Zstd's core is Jarek Duda's finite state entropy coding, and Wasm performs the extremely dense bit shifting and table lookups directly in linear memory. **Streaming block processing**: when the user drops in or the front end downloads a large `.zst`, JS passes the data in blocks through the Streams API, and Wasm decompresses within microseconds and returns a `Uint8Array`, creating no JS garbage objects throughout.

**Performance**: Claimed to decompress a 100 MB Zstd log file at **400–600 MB/s**, close to **85%** of native C and more than **20× faster** than traditional pure-JS decompression libraries.

**Advantages**: Breaks past the browser's protocol restrictions so a statically hosted big-data dashboard can transfer large files at very high compression ratios and decompress them instantly on the front end, cutting download waits and server bandwidth substantially.
**Disadvantages**: Zstd's high-strength compression modes need a fairly large linear memory as a dictionary buffer, so the architecture must bound the virtual machine's memory ceiling carefully.

**Competitors**: pako / zlib.js (only the older DEFLATE/Gzip, comprehensively surpassed in both ratio and decompression throughput).

---

### 45. (originally 54) libsndfile-Wasm — Multi-format audio metadata and sample stream parsing 🟡

**Pain point**: Audio engineers and speech AI developers working on the front end often need to read professional and unusual formats (`.wav`, `.aiff`, `.flac`, `.ogg`, `.voc`, `.sf`). The browser's Web Audio API natively supports only a few consumer formats (MP3, AAC). Analyzing, editing or extracting professional audio tracks, quantization bit depth or raw PCM samples on the web is severely underserved by pure-JS parsers, which OOM easily on large files.

**How it works**: The industrial C-language audio file processing library **libsndfile** is compiled to Wasm. **Precise binary structure destructuring**: after the user drops a file in, the parser inside Wasm rapidly takes apart the audio container's binary tables (WAV's RIFF header, AIFF's COMM chunk) and returns structured parameters like sample rate and channel count as JSON. **Zero-copy floating-point sample stream**: the decoding core converts each track's raw data straight to standard `f32` and exposes it through a `TypedArray` pointer to WebGL (drawing a high-precision spectrogram) or the Web Audio API.

**Performance**: Claimed to parse a 200 MB industrial lossless multitrack WAV and extract every sample in no more than **15 milliseconds**, with very low memory use.

**Advantages**: Brings deep parsing and direct playback control of dozens of professional audio formats to a static platform; a musician's unreleased masters never leave the device.
**Disadvantages**: libsndfile pursues maximum performance, so its exception handling and defence against corrupt files depend heavily on compile-time bounds checking; a maliciously crafted audio file must be prevented from crashing the virtual machine.

**Competitors**: Native `decodeAudioData` (good performance but a very narrow format range, entirely unable to read professional formats like AIFF or VOC); backend SoX/FFmpeg (powerful, but with server cost and a long upload).

---

### 46. (originally 55) libxslt-Wasm — The XSLT stylesheet transformation engine for XML 🟡

**Pain point**: In enterprise data interchange, healthcare information systems (HL7) and legal document management, XML is still the core format, and XSLT is the industrial standard for transforming XML into HTML/JSON dynamically. **But modern browsers (especially Chrome and Safari) support high-order XSLT 2.0/3.0 very poorly, or have deprecated it.** Hand-writing a whole Turing-complete XSLT engine in JS on the front end performs so badly on large XML node trees that it is unusable.

**How it works**: The GNOME project's authoritative C library **libxslt** (plus the underlying **libxml2**) is compiled to Wasm in full, providing a browser-universal industrial XML transformation platform. **An exact in-memory DOM tree**: once the XML data and XSLT stylesheet arrive, the C core inside Wasm builds a highly compact binary XML node tree in memory. **XPath engine acceleration**: XSLT's core is heavy XPath node retrieval, and Wasm performs Turing-complete template matching and data formatting through fast pointer-driven table lookups, assembling the transformed text stream directly in linear memory.

**Performance**: Claimed that a high-order XSLT transformation of a medical XML dataset with tens of thousands of nodes completes in **8–12 milliseconds**, reaching **80%** of native C and more than **30× faster** than JS emulation.

**Advantages**: Perfectly solves the pain of modern browsers' broken XSLT 2.0/3.0 support, letting enterprises move seamlessly to a pure front end without changing their existing XML/XSLT architecture; zero server cost.
**Disadvantages**: XML parsing is a large codebase, so the compiled Wasm is about **2–3 MB** compressed, and the API is low-level, needing a glue layer for strings and buffers.

**Competitors**: Native `XSLTProcessor` (no download, no size overhead, but **no support at all for syntax past XSLT 2.0** — seriously out of date); a backend Saxon service (the most complete, but with server cost, network latency and privacy risk).

---

### 47. (originally 56) VLC.wasm (libvlc) — A universal multimedia playback and streaming decode core 🟡

**Pain point**: The browser's built-in `<video>` is strict about formats (usually MP4, WebM, Ogg only). When a user needs to play `.mkv` (with multiple subtitle tracks), `.avi`, `.flv` or a professional RTSP/RTMP live surveillance stream, the browser simply refuses. The old fix was an expensive live transcoding server on the backend (converting MKV to HLS), whose cost explodes catastrophically with tens of thousands of concurrent users.

**How it works**: Millions of lines of C-language **VLC (libvlc)** core are compiled to Wasm in full via Emscripten. **A software decoding network stack**: the user drops in a video or types a stream URL, JS fetches binary blocks over WebSocket or fetch, **bypasses the browser's multimedia parser** and writes them straight into Wasm's MEMFS; the demuxer and decoders inside Wasm decode the video and audio bitstreams in software within the sandbox. **YUV-to-RGB hardware passthrough**: the decoded YUV420p raw pixels never pass through JS conversion; the memory pointer is exposed directly and JS runs colour space conversion and rendering on the GPU through a WebGL/WebGPU shader.

**Performance**: Claimed that with SIMD and threads on, 1080p/30 FPS MKV or H.264 decodes smoothly in software with no hardware acceleration, with playback latency under **30 milliseconds** at **70%–75%** of native VLC.

**Advantages**: Brings genuinely "universal format compatibility" playback to a static site, at zero backend cost, with the video never leaving the device.
**Disadvantages**: Dense software decoding puts a heavy load on CPU, noticeably heating and draining a low-end phone or tablet playing high-resolution video.

**Competitors**: hls.js / flv.js (popular front-end streaming libraries, but essentially only remuxing — **underneath they still depend heavily on the browser's built-in decoding hardware**).

---

### 48. (originally 57) SuiteSparse:GraphBLAS-Wasm — Sparse-matrix graph algebra supercomputing 🟡

**Pain point**: In big-data analysis, social network mining (PageRank over hundreds of millions of relationships) and financial risk control, graphs are usually turned into massive "sparse matrices" for algebraic computation, relying on the industrial C library **SuiteSparse:GraphBLAS**. Hand-writing those giant, 99%-zero matrix multiplications over JS arrays produces heavy memory fragmentation from the object allocator and lacks binary pointer-chasing optimization, freezing the browser for tens of seconds.

**How it works**: The SuiteSparse:GraphBLAS core is compiled to Wasm in full. **Compressed sparse layout**: matrices are laid out strictly in linear memory in binary **CSC (Compressed Sparse Column)** format, storing no zero elements at all, maximizing cache hit rates and bypassing JS object creation entirely. **Semiring algebra**: every graph traversal and shortest-path computation is converted into bitmask and fast binary multiply-add operations inside Wasm, with several Workers scanning linear memory in parallel.

**Performance**: Claimed to complete PageRank iterations on a giant social graph of 100,000 nodes and 2,000,000 edges in **80–120 milliseconds**, more than **50× faster** than pure-JS graph matrix libraries.

**Advantages**: Gives a free static dashboard the ability to run hardcore graph algebra over million-scale network graphs; 100% data confidentiality.
**Disadvantages**: GraphBLAS's API is extremely academic and abstract, so a front-end developer cannot add or remove nodes intuitively and must write a heavy data transformation glue layer.

**Competitors**: math.js (fine for ordinary dense matrix algebra, but orders of magnitude behind on industrial sparse graph computation past tens of thousands of dimensions with vast numbers of zeros).

---

### 49. (originally 58) HTML Tidy-Wasm — Industrial cleanup and repair of dirty HTML/XML 🟡

**Pain point**: In web crawlers, online HTML editors and code review tools, the front end constantly receives "dirty HTML/XML" with broken syntax, unclosed tags and scrambled attributes. Pure-JS regex matching is far too imprecise, and on millions of lines of page source, string slicing and DOM tree reconstruction saturate the CPU.

**How it works**: The long-lived and extremely robust authoritative C library **HTML Tidy** is compiled to Wasm. **A byte-stream lexical state machine**: the user's dirty HTML is written in by JS through a memory pointer, and the C parsing core inside Wasm **creates no intermediate string objects at all**, scanning the raw byte stream lexically with a fast integer state machine. **In-memory tree reconstruction**: Wasm builds a highly compact DOM node tree in its enclosed linear memory, filling in missing closing tags automatically, repairing attribute quoting, and assembling perfect standard HTML in memory in one pass to return.

**Performance**: Claimed to clean and format 20 MB of very large page source riddled with nesting errors in only **10–15 milliseconds**, **20–30× faster** than pure-JS repair libraries, with very low memory use.

**Advantages**: Brings latency-free live syntax cleanup and automatic repair to a static online code sandbox; zero backend cost.
**Disadvantages**: A relatively vertical tool — **when the code volume is tiny, the Wasm module's own load time cancels out the performance gain**.

**Competitors**: htmlparser2 (good compatibility, mature ecosystem, but a clear performance bottleneck on enterprise-scale page data cleaning past hundreds of thousands of lines).

---

### 50. (originally 59) Web-Fontfuzz — Security fuzzing of font files 🔴

**Pain point**: Font files (`.ttf`, `.otf`, `.woff2`) have complex structures and contain miniature hardware instructions (a TrueType bytecode interpreter). Historically, many severe remote code execution (RCE) vulnerabilities in operating systems and browsers came from parsing maliciously crafted fonts. Security researchers doing font fuzzing must set up a complex Linux environment and cluster locally. Building an instantly available detection platform on the web is impossible with traditional front-end technology, which cannot mutate the internal tables of a binary font at high frequency or analyze the resulting crashes.

**How it works**: A Rust/C++ font security fuzzing core (libFuzzer-based font parsing operators, say) is compiled to Wasm and deployed statically. **A mutation state machine**: the user drops in a font, and Wasm performs tens of thousands of random bit flips and structural corruptions per second on its binary structures (the `glyf` and `loca` tables) in linear memory. **Sandboxed memory isolation**: the mutated malicious font is fed straight into the virtual parser inside Wasm; if it triggers a memory overrun, **the Wasm sandbox catches that RuntimeError precisely and absolutely never touches the user's real operating system or browser security** (exactly the positive application of Chapter 2's "the sandbox protects the host").

**Performance**: Claimed **5,000–8,000** font structure mutations and deep parse tests per second single-threaded, at **80%** of the native C++ core.

**Advantages**: Gives security engineers a 100% isolated, decentralized, web-based font vulnerability diagnosis tool.
**Disadvantages**: The web environment means that when the Wasm VM crashes, it cannot export a full core dump the way local Linux can, so carefully written glue must stream memory logs out live.

**Competitors**: Local AFL++ / libFuzzer (unlimited compute and the most complete debugging, but fiddly to install and without the instant availability of a web page).

---

### 51. (originally 60) Web-Gidra (the Ghidra decompiler core) — Binary reverse engineering 🔴

**Pain point**: Reverse engineers analyzing malware or binary executables (x86/ARM `.exe`, `.bin`) need to decompile machine code back into readable high-level C. The core is an enormous decompilation semantics engine (such as the NSA's open-source Ghidra). Offering a fast binary analysis playground on the web previously meant uploading the malicious binary to a backend — a serious security hazard (the malware could contaminate the backend), and building a control flow graph (CFG) is CPU-expensive.

**How it works**: Ghidra's C++ core decompilation engine (the Sleigh decoder and constant propagation optimizer) is compiled to Wasm, creating an online reverse engineering range. **An intermediate language (P-code) translation tree**: the user drops in a binary executable, the decoder inside Wasm reads the machine code at high speed and translates it into an architecture-independent intermediate representation (P-code), building a highly compact control flow graph in linear memory. **Structured semantic reconstruction**: the internal optimizer performs dead code elimination and variable type inference, assembling the decompiled C string directly in linear memory.

**Performance**: Claimed to decompile a roughly 2 MB x86 library into high-quality C in **200–400 milliseconds**, reaching **75%** of desktop Ghidra.

**Advantages**: **100% absolute security isolation** — the malicious binary is decompiled entirely inside Wasm's sealed sandbox and cannot infect the local system; a static site's operating cost is zero.
**Disadvantages**: Ghidra's C++ decompilation core is enormous, so the compiled Wasm is still **5–8 MB** compressed and slow on first load.

**Competitors**: Pure-JS binary parsers (usually capable of only hex viewing or simple disassembly, and utterly helpless before decompilation tasks needing complex control flow optimization and semantic reconstruction).

> **A self-reference worth noticing**: this case forms an interesting loop with Chapter 9 — **running a decompiler in Wasm to analyze someone else's Wasm.** In fact the Ghidra community does have a Wasm loader plugin that takes `.wasm` as its analysis target, and WABT's `wasm-decompile` produces C-like pseudocode too. **The fact that the reverse engineering tool and the object of reverse engineering run in the same sandbox is by itself proof that "binaries are irreversible" is an untenable claim.**

---

## V. Cryptography, Scientific Computing and P2P

### 52. (originally 71) Circom-Witness-Wasm — Front-end zero-knowledge proof generation 🟢

**Pain point**: Zero-knowledge proofs (ZKP) let a user prove to a server that they hold a permission without revealing a password or identity (private voting, zk-Rollups). But generating a ZK proof means constructing a large arithmetic circuit and computing extremely dense cryptographic polynomials (MSM and NTT). As a web DApp, pure-JS libraries perform so badly on tens of thousands of circuit gates that the browser throws up "this page is unresponsive."

**How it works**: The witness computation code produced by the ZK circuit compiler `circom` is compiled directly into a Wasm module hosted statically. **Big-field arithmetic optimization**: ZKP involves huge integer arithmetic over a specific finite field (the BN254 elliptic curve, say), and Wasm uses `i64` instructions to open a contiguous memory pool inside the sandbox for maximally optimized modular multiplication and addition. **Zero-copy proof flow**: JS passes private inputs directly into Wasm memory as a `TypedArray`, and Wasm solves thousands of constraints at high speed inside the sandbox to generate the binary witness file.

**Performance**: Claimed that generating the proof for a private identity circuit of 50,000 gates takes only **300–500 milliseconds** on the front end, more than **25× faster** than early pure-JS versions (snarkjs's JS mode).

**Advantages**: The user's real password and private inputs **100% never leave the device**, meeting cryptography's highest security principle; backend operating cost is eliminated entirely.
**Disadvantages**: **If the circuit is enormous (a zk-EVM proof of millions of gates, say), Wasm cannot run it at all because it exceeds the 4 GB linear memory ceiling**, and backend compute is required (another concrete instance of Chapter 8's ceiling).

**Competitors**: Pure-JS cryptographic computation (with no low-level instruction optimization for custom finite fields and bignum arithmetic, it simply freezes when solving large circuits).

---

### 53. (originally 72) Qiskit-Wasm — Quantum computing state vector simulation 🟡

**Pain point**: Quantum computing researchers and students designing quantum algorithms (Shor, Grover) need to simulate qubit superposition and entanglement. IBM's Qiskit rules the field, but its core is written in C++/Python. Providing an interactive quantum programming teaching platform on the web meant sending circuits back to a backend queue; when many students run at once, the backend's matrix multiplication capacity is instantly consumed.

**How it works**: A lightweight quantum simulation core (a C++/Rust state vector calculator) is compiled to Wasm and deployed on a static page. **Complex matrix tensor products**: qubit simulation is essentially dense complex vector and Kronecker product arithmetic, and Wasm builds compact `f64` real and imaginary arrays in linear memory. **Probability amplitude streaming sampling**: when the user performs a quantum measurement, the Monte Carlo state machine inside Wasm samples memory at high speed and returns the histogram as JSON for Canvas to draw.

**Performance**: Claimed that simulating a composite circuit of arbitrary logic gates (Hadamard, CNOT and so on) on 16 qubits completes full state vector evolution in **10–20 milliseconds**, at **80%** of native C++.

**Advantages**: Brings quantum computing education platforms a fully backend-free, latency-free live simulation experience, cutting academic institutions' cost of standing up compute servers dramatically.
**Disadvantages**: **The dimension of the quantum state vector explodes exponentially with qubit count (2ⁿ)**, so the front end tops out around **20–24 qubits** and crashes with OOM beyond that. **This is the cleanest expression of the 4 GB ceiling anywhere: a 24-qubit complex state vector lands exactly in the hundreds-of-megabytes-to-gigabytes range.**

**Competitors**: Pure-JS complex matrix computation (unable to guarantee contiguous memory alignment, so large matrix multiplications thrash L1/L2 constantly and run more than 15× slower).

---

### 54. (originally 73) libp2p-Wasm — A distributed P2P network multiplexing protocol stack 🟢

**Pain point**: Building decentralized network applications (IPFS, a browser P2P chatroom, WebTorrent), the front end must establish complex P2P connections with nodes worldwide. But the browser offers only the high-level WebRTC API, without low-level stream multiplexing, node routing (DHT) or secure encrypted handshake negotiation. Traditionally that means the heavy JS libp2p, but maintaining hundreds of P2P virtual channels and parsing binary packet headers burns a lot of CPU through dynamic typing and makes the UI stutter intermittently.

**How it works**: The industrial libp2p core network stack in Go or Rust (including `mplex` multiplexing, `yamux` and the `noise` encryption layer) is compiled to Wasm in full. **A binary packet pipeline**: raw P2P byte streams arriving on the WebRTC data channel are written into Wasm memory directly as a `Uint8Array`, and the parser inside takes packet headers apart with a fast integer state machine and routes them automatically to their virtual subchannels. **In-memory network buffers**: Wasm maintains efficient sliding windows and ring queues internally, running flow control and cryptographic defence, creating no JS garbage objects throughout.

**Performance**: Claimed that in a stress test maintaining 200 simultaneous P2P node connections at 50 MB/s throughput, protocol parsing is **12–18× faster** than the pure-JS version, with CPU usage down 65%.

**Advantages**: Brings statically hosted DApps an industry-standard "serverless P2P connectivity," substantially improving the transfer stability of a browser-side IPFS node.
**Disadvantages**: Sandbox restrictions mean it **still cannot open a traditional TCP/UDP listener directly** and must rely on external JS using WebRTC or WebSocket as a springboard for the physical NIC (echoing Chapter 11's four reservations about P2P being "serverless").

**Competitors**: js-libp2p (highly complete, but causing severe GC stutter under very high-frequency binary packet destructuring and Noise handshakes).

---

### 55. (originally 74) minimap2-Wasm — High-speed gene sequence alignment 🟡

**Pain point**: In modern biomedicine, scientists must align the vast DNA base sequences (reads) produced by a sequencer against a known reference genome to catch genetic variants or infectious disease signatures, usually relying on the authoritative C library **minimap2** (with precise dynamic programming and a seed-and-extend algorithm). Biologists previously had to install a Linux terminal or upload highly sensitive personal genetic data to a hospital cloud — an enormous privacy risk, with high backend cluster maintenance cost besides.

**How it works**: Tens of thousands of lines of maximally optimized C-language gene alignment engine are compiled to Wasm via Emscripten, creating a web-based genetic diagnosis workbench. **Binary index lookup**: the reference genome's huge index table (hundreds of megabytes) is loaded into Wasm linear memory in one pass as a binary byte stream. **SIMD-accelerated dynamic programming**: the heart of gene alignment is solving the Smith-Waterman matrix, and with SIMD on, a single instruction computes the score matrix and penalty weights for 4 or 8 bases in parallel.

**Performance**: Claimed to align an unknown viral DNA sequence of 10,000 base pairs in only **80–150 milliseconds**, at **75%** of native C.

**Advantages**: **100% medical-grade privacy** — personal DNA data stays entirely in the local sandbox; a researcher in the field can align in real time by opening a web page on a phone.
**Disadvantages**: The human reference genome's index file (`.mmi`) often runs to hundreds of megabytes or even gigabytes, so the front end's first load and memory quota control need a very carefully designed streaming architecture (precisely the scenario Chapter 8's "escape route one" exists for).

**Competitors**: Pure-JS string matching algorithms (lacking binary pointer manipulation and SIMD vector acceleration, orders of magnitude slower on large-scale genetic data and with no industrial viability at all).

---

### 56. (originally 75) Orekit-Wasm — Astrodynamics and satellite orbit prediction 🟡

**Pain point**: Aerospace engineers and astronomy enthusiasts predicting the exact orbital position of a satellite (the ISS, Starlink) must run extremely precise astrodynamic numerics: Earth's gravitational field irregularity (spherical harmonic models), solar radiation pressure, atmospheric drag and multi-body gravitational perturbations. The authoritative open-source library is **Orekit**. Hand-writing those orbital perturbation differential equations over ordinary JS floats produces accumulated errors of kilometres within days, for lack of exact 64-bit alignment and fast matrix iteration.

**How it works**: A rigorous astrodynamics core is compiled to Wasm, providing a decentralized satellite tracking dashboard. **An exact numerical integrator**: Wasm implements a high-order Runge-Kutta (Dormand-Prince) ODE solver internally, advancing orbital elements and geocentric coordinates strictly as contiguous `f64` in linear memory. **A time and coordinate system conversion state machine**: complex matrix transformations between IERS-standard time scales (TAI, UTC) and inertial frames (EME2000, ITRF) run at high speed at the binary level, bypassing JS's GC interference throughout.

**Performance**: Claimed to predict a satellite's exact position over the next 30 days (continuous integration at a one-second step) in only **40–60 milliseconds**, at aerospace-industry precision and more than **30× faster** than pure JS.

**Advantages**: Brings an entirely install-free, zero-backend, aerospace-precision online orbit propagation tool; pairs perfectly with Three.js for live 3D orbital visualization around the Earth.
**Disadvantages**: It needs the global gravity field model (EGM96) and precise leap-second observation data loaded, and those static data files must be requested and injected dynamically by the front end.

**Competitors**: satellite.js (based on the simpler SGP4 model, fast, but so physically simplified that it cannot compute high-order gravity field irregularity or atmospheric drag perturbation at all).

---

### 57. (originally 76) WireGuard-Wasm — A front-end VPN network protocol stack 🟡

**Pain point**: In remote work and zero-trust architectures, WireGuard is the high-performance lightweight encrypted VPN protocol. But a traditional VPN must install a virtual NIC driver deep in the operating system, requiring very high system privileges. To let employees connect securely to internal company resources by opening a web page without installing anything, pure-JS crypto libraries are entirely unequal to reassembling ChaCha20-Poly1305 packets at tens of megabytes per second and running the Noise handshake state machine.

**How it works**: WireGuard's official Go or Rust userspace network stack core is compiled to Wasm. **Tunnel packet destructuring**: Wasm emulates a virtual NIC in its sandboxed linear memory; when external JS receives an encrypted UDP packet over WebRTC or WebSocket (as the physical relay) it passes it straight into Wasm memory, and the state machine inside decrypts, verifies and unpacks the original internal IP packet at high speed. **Memory buffer flow**: the decrypted data is repackaged inside Wasm as a front-end-readable `ArrayBuffer` and talks directly to a tiny in-page client (a web SSH client, say), never touching the operating system's network stack.

**Performance**: Claimed that packet processing and decryption throughput is **12–20× faster** than pure-JS crypto emulation, reaching **30–50 MB/s** of encrypted transfer in the browser at stable CPU usage.

**Advantages**: Brings a static page install-free "native-grade secure VPN tunnel connectivity"; the encryption private key stays inside the user's browser forever.
**Disadvantages**: Bounded by the sandbox, **the tunnel can serve only the current tab or the current application's network requests, and cannot provide global VPN encryption for every other piece of software on the operating system.**

**Competitors**: Pure-JS cryptographic network libraries (lacking efficient binary bit shifting and compact memory alignment, causing severe GC stutter and disconnections under heavy VPN packet throughput).

---

### 58. (originally 77) Minestom-Wasm — A Minecraft server engine inside the browser 🔴

**Pain point**: A Minecraft world is made of tens of billions of blocks, and multiplayer traditionally means renting an expensive Java server to handle block generation, player synchronization and physics collision. The community wants a "click and play, no host needed" multiplayer experience on a static page — which means **the browser front end must itself become a server**. A game server written in pure JS performs so badly on 3D block-world collision volumes and mass packet serialization that the page freezes.

**How it works**: The open-source high-performance Minecraft server core **Minestom** (or a Rust server implementation) is compiled to Wasm and runs directly in the browser front end. **A sandboxed in-memory server**: Wasm builds a highly compact 3D world block database in linear memory, with player positions, block breaking and generation, and mob AI all computed inside Wasm. **P2P network forwarding**: through a WebRTC data channel, other players connect P2P directly to the host player's Wasm server; Wasm serializes memory-generated 3D chunks into a binary byte stream and distributes them at high speed.

**Performance**: Claimed that this in-browser server handles **10–15 players** online simultaneously with physics collision and 3D world synchronization, keeping server tick time within **2 milliseconds** (far below the game's 50-millisecond budget).

**Advantages**: Genuinely decentralized — players rent no cloud host at all and can open a multiplayer 3D game server on free static hosting; level saves export as a binary file.
**Disadvantages**: Bounded by the 4 GB memory ceiling, it cannot support a large render distance or more than about 20 players.

> ★ **A real version of this idea exists, and it is harder**: **FluffOS × Wasm** compiles an entire LPMud driver (LPC compiler, virtual machine, efuns, telnet protocol) into a browser tab, with the mudlib packaged by `file_packager` as a static bundle. It solves two problems beyond this concept: **compiling user code at runtime**, and **replacing the blocking event loop with a host-driven `fluffos_tick()`**. **See Appendix L.**

**Competitors**: A traditional standalone Java/C++ server (feature-complete, supporting tens of thousands of players, but requiring a VPS purchase and complex port forwarding configuration).

---

### 59. (originally 78) GnuCash-Wasm — An enterprise double-entry accounting and ERP core 🟡

**Pain point**: Small and medium enterprises managing finances, issuing invoices or preparing balance sheets need an ERP or double-entry accounting system, and the authoritative open-source tool is GnuCash. As a cloud service, a company's highly sensitive transaction flows, profits and payroll must be uploaded to a third party — an enormous risk. Hand-writing an accounting core in JS runs into a wall on tens of thousands of transactions, cross-currency compound interest and live recomputation of account balances, because **JS lacks exact 64-bit fixed-point arithmetic and easily throws the books out of balance through lost floating-point precision**.

**How it works**: The open-source C-language accounting core **GnuCash (libgnucash)** is compiled to Wasm in full. **High-precision fixed-point memory**: accounting abhors floating-point error, so Wasm strictly uses `i64` to emulate high-precision accounting fixed-point numbers, advancing every debit-credit balance computation directly through contiguous binary structures and avoiding GC entirely. **XML/SQL save synchronization**: transaction data can be compressed directly into a `.gnucash` file (gzipped XML) or SQLite and synced locally through the virtual filesystem, so financial data 100% never leaves the device.

**Performance**: Claimed that recomputing a full year's general ledger of 50,000 cross-border transactions with automatic exchange-rate conversion across five currencies takes only **20–40 milliseconds** on the front end to produce the income statement and balance sheet, **30× faster** than pure JS.

**Advantages**: Brings industrial-grade high-precision accounting to a static enterprise back office; 100% data confidentiality, meeting the ACID transaction safety standard financial audit requires.
**Disadvantages**: GnuCash's native C architecture is very large, so the compiled Wasm runs about **3–4 MB**, and the API is low-level, needing a modern web UI designed for a smooth fit.

**Competitors**: Commercial SaaS cloud accounting (powerful and highly automated, but with a subscription fee and core financial data hosted entirely by a third party).

---

### 60. (originally 79) Micro-Apache-Wasm — A miniature web server inside the browser 🟡

**Pain point**: In front-end teaching, static demonstration or building an offline PWA tool, you sometimes need to virtualize "a real web server" inside the browser to parse standard HTTP requests, handle custom route rewriting (`.htaccess`) or process virtual POST forms. That previously required installing Node.js, Apache or Nginx. Pure JS brute-forcing HTTP header string parsing and status code redirection at very high frequency has CPU peaks that are too high, and it is hard to reproduce a real server's underlying architecture.

**How it works**: A lightweight C-language embedded HTTP server engine core is compiled to Wasm via Emscripten. **Virtual port listening (in-memory socket)**: the sandbox prevents Wasm from actually opening physical port 80, so the architecture uses a **Service Worker** — when the user visits a virtual URL (`/api/users`, say), the Service Worker intercepts that real HTTP request. **Server state machine solving**: the Service Worker passes the request's raw bytes straight into Wasm memory, the C server core inside performs route matching, header sanitization and virtual file addressing at high speed, and finally generates a standard HTTP response packet in linear memory to return.

**Performance**: Claimed that under high-frequency virtual API requests, a standard HTTP request parse, route match and response generation completes in **under 1 millisecond**, with QPS more than **15× higher** than a mock server written with pure-JS regexes.

**Advantages**: Reproduces a complete, standard, rewrite-capable server engine on free static hosting; ideal for building an install-free online backend development and network protocol teaching platform.
**Disadvantages**: **This is only a virtual server "running in browser memory," and real users on the external internet cannot connect through it into that user's computer** (unless paired with a P2P traversal tunnel) — exactly the same point as Chapter 5's authenticity caveat about WebContainers.

> ★ **The real control group is again FluffOS × Wasm (Appendix L)**, and the difference is instructive: this concept emulates **stateless request-response**; what FluffOS moves in is a server with **a heartbeat, `call_out` timers, persistent world state and multiple concurrent connections**. **How hard "move the server into the browser" is depends entirely on whether that server has state.**

**Competitors**: Mock.js / MSW (fine for ordinary front-end API data mocking, but with none of a real web server's underlying C state machine, custom rewrite rules or real HTTP byte-stream destructuring).

---

### 61. (originally 80) GNU-Tar-Wasm — An industrial archiving and checksum engine 🟡

**Pain point**: `tar` is the absolute standard for packaging and backup in the Linux world. When a static application must package thousands of tiny files into a standard `.tar` or `.tar.gz`, pure JS hits a wall: concatenating tens of thousands of files' bytes and computing POSIX-standard headers (512-byte block alignment, octal UID/GID string conversion, exact octal checksums) triggers constant fragmented allocation, crashing the page or dropping frames badly.

**How it works**: The most authentic official **GNU tar** C-language toolchain is ported and compiled in full into `tar.wasm`. **Flat 512-byte alignment**: Wasm allocates a contiguous flat linear memory internally, and when external JS passes in many small files, the GNU core inside uses efficient binary pointer arithmetic to lay them out in memory in strictly 512-byte-aligned structures and quickly compute the low-level binary checksums. **Streaming archive output**: files are never concatenated by JS; when Wasm finishes archiving it emits a fully POSIX-conformant `Uint8Array` directly, guaranteeing the archive unpacks perfectly with `tar -xvf` on any Linux system.

**Performance**: Claimed to archive and checksum a project structure of 5,000 tiny files (50 MB total) in only **8–15 milliseconds**, more than **25× faster** than pure-JS archiving libraries.

**Advantages**: A 100% clone of GNU's decades of highly compatible archiving algorithms, ensuring the archives produced on the front end are never corrupt; consumes none of the developer's server bandwidth or CPU.
**Disadvantages**: A low-level tool focused tightly on archive format and checksum compatibility — **if the user only needs one simple file, the Wasm module's initial load exceeds the performance gain**.

**Competitors**: Pure-JS archive libraries (simple to write, but far behind an authentic port in efficiency and format compatibility when densely packaging thousands of files with precise POSIX header byte alignment and octal checksums).

---

### 62. (originally 81) CuraEngine-Wasm — An industrial 3D printing slicing engine 🟢

**Pain point**: In 3D printing, converting a model file (`.stl`, `.obj`) into the G-code toolpath the printer understands is called "slicing." It involves extremely dense 3D geometric intersection computation, polygon offsetting (AABB trees and Minkowski sums) and optimal path planning. The world's foremost core is Ultimaker's open-source **CuraEngine** (C++). Offering slicing on the web previously meant uploading hundreds of megabytes of STL to a backend — consuming enormous bandwidth, and overloading backend CPU instantly when many users slice at once.

**How it works**: The CuraEngine core — hundreds of thousands of lines of accumulated C++ — is cross-compiled to Wasm via Emscripten, providing desktop-grade slicing on a static page. **Flat memory space geometry**: the model's millions of triangle vertices are written into linear memory as a binary byte stream, and Wasm builds a 3D AABB spatial tree through pointer manipulation. **Multithreaded layered slicing**: with Web Workers plus `SharedArrayBuffer`, the model is cut into thousands of horizontal layers along Z, and each layer's polygon topology filling and path computation is distributed in parallel across CPU cores.

**Performance**: Claimed to slice a complex model of 500,000 triangles and generate 20 MB of G-code in only **1.5–3 seconds** on the front end, at **80%** of the native C++ desktop version.

**Advantages**: Brings the static 3D printing community desktop-grade slicing at zero backend cost; an industrial designer's prototype stays 100% local, removing IP leakage risk.
**Disadvantages**: If the model geometry is badly broken (non-manifold geometry, say), designing the glue for debugging and cleaning up memory when the C++ core throws inside Wasm is extremely complex.

**Competitors**: Pure-JS geometric slicing libraries (lacking strict typing and efficient multidimensional spatial tree addressing, so the page OOMs outright or freezes in long GC past 50,000 triangles).

---

### 63. (originally 82) liquid-dsp-Wasm — Software-defined radio (SDR) digital signal processing 🟡

**Pain point**: Software-defined radio lets you process radio signals in software (FM broadcast, aircraft ADS-B, weather satellite imagery). The core is dense digital signal processing: FFT, FIR filtering, phase-locked loops (PLL) and demodulation. The most popular tiny C DSP library is **liquid-dsp**. Receiving a USB SDR receiver's raw IQ sample stream live on the web previously meant decoding on a backend and converting to an audio stream — enormous latency and very high server load.

**How it works**: liquid-dsp is compiled to Wasm in full as a direct demodulation core for the Web USB / Web Serial APIs. **A zero-copy signal pipeline**: after the browser obtains millions of raw IQ samples per second from an RTL-SDR over WebUSB, they are written straight into Wasm's ring buffer as a `TypedArray`. **SIMD-accelerated demodulation**: with SIMD on, one CPU instruction runs several complex dot-product matrix operations and filter iterations in parallel, restoring the high-frequency radio byte stream to raw audio PCM inside the sandbox.

**Performance**: Claimed that demodulating 2.4 MSps (2.4 million samples per second) wideband QAM or standard WBFM in real time consumes under **3% of CPU**, with audio decoding latency down to **5 milliseconds**.

**Advantages**: Breaks the taboo that the web cannot handle "high-frequency hardware digital signals" — plug in a USB receiver and the browser becomes a fully functional radio receiver, at zero server cost.
**Disadvantages**: The solving algorithms inside Wasm are fixed, so it is less flexible if the front end wants to inject an entirely new custom modulation formula dynamically.

**Competitors**: Pure-JS DSP libraries (unable to guarantee contiguous memory alignment of 64-bit complex vectors, so a flood of IQ samples causes constant GC stutter and the decoded audio comes out with harsh pops and distortion).

---

### 64. (originally 83) Tantivy-Wasm — Industrial full-text search and inverted indexing 🟢

**Pain point**: On a static big-data display site or a very large documentation system, users need live full-text search and weighted filtering across hundreds of thousands or even millions of structured records. Pure-JS search libraries (Lunr.js) can only do simple string matching, and past tens of thousands of records the index balloons and performance collapses; a backend option (Elasticsearch) means expensive operations.

**How it works**: **Tantivy**, the industrial search engine core written in Rust (holding the same position as Lucene in the Java world), is compiled to Wasm. **A highly compact inverted index layout**: JSON is abandoned for a highly compact inverted index built in linear memory on **finite state transducers (FST)** and binary bitmaps (**Roaring Bitmaps**). **Zero-GC vector retrieval**: when the user submits a multi-condition compound search (boolean queries with BM25 term-frequency relevance ranking), JS passes the query string in, and Wasm parses the query tree and runs extremely fast intersections and unions over binary memory.

**Performance**: Claimed to complete a fuzzy match and paginated relevance ranking over an index of 500,000 complex logs or product records (roughly 200 MB of raw text) in **2–4 milliseconds**, more than **40× faster** than pure-JS search libraries, with a fifth of the memory of the JS version.

**Advantages**: Brings a static platform "Lucene-class" professional search, supporting complex phrase matching, regex filtering and field faceting; 100% zero backend cost.
**Disadvantages**: The index file must be pre-generated in binary form and placed on the static host; at very large data volumes it needs careful **HTTP Range Request** streaming of just the index blocks it needs (another application of Chapter 8's escape route one).

**Competitors**: Fuse.js / Lunr.js (fine for lightweight fuzzy search on a thousand records, but they freeze the main thread outright on large text corpora past a hundred thousand).

---

### 65. (originally 84) Rapier3D-Wasm — Rust's industrial 3D rigid body physics engine 🟢

**Pain point**: Building 3D simulations, robotic kinematics control or high-precision web games on the front end requires computing rigid body collisions, joint constraints, gravitational acceleration and contact mechanics among thousands of objects. Traditional front-end physics engines (Ammo.js, a downgraded rewrite of the C++ Bullet engine) are very bloated; pure-JS physics libraries, lacking exact 64-bit memory layout optimization, produce severe **jittering** or tunnelling when many objects stack.

**How it works**: **Rapier3D**, the next-generation high-performance 3D rigid body physics engine written in Rust, is compiled to Wasm. **Cache-friendly data arrays (SoA layout)**: every object's mass, 3D coordinates, velocity and rotation quaternion are laid out strictly as contiguous **structure-of-arrays** in linear memory, maximizing L1/L2 hit rates. **Symplectic numerical integration**: the physics optimizer inside Wasm runs a rigorous collision detection state machine (broad-phase sweep plus narrow-phase exact solve) and solves the linear complementarity problem (LCP) at high speed at the binary level, with no JS garbage allocation anywhere.

**Performance**: Claimed that simulating **5,000 complex rigid bodies** falling, colliding and stacking in one scene takes no more than **4–6 milliseconds** per physics step, locking 60 FPS solidly.

**Advantages**: Provides industrial-robot-grade high-precision physical feedback, eliminating the tunnelling and unnatural jitter common in pure-JS physics engines; **the Wasm module is only a few hundred kilobytes compressed and loads very fast** (the classic advantage of Rust's zero runtime burden).
**Disadvantages**: Very high-frequency collision event callbacks into JS incur boundary conversion overhead from passing many event objects, so a memory event ring buffer optimization is needed.

**Competitors**: Cannon.js / Oimo.js (small and quick to learn, but their compute and numerical precision are entirely inadequate for industrial or high-end game scenarios with dense multi-object stacking, complex joint constraints and continuous collision detection (CCD)).

---

### 66. (originally 85) Cubism-OLAP-Wasm — A multidimensional online analysis (OLAP) data cube 🔴

**Pain point**: In business intelligence, engineers need multidimensional online analysis of massive data (millions of sales, log or telemetry records), building a "data cube" live and running roll-up, drill-down and dice aggregations. Traditionally that relies on a large backend OLAP database (ClickHouse, Apache Druid). To offer a backend-free million-scale BI dashboard on an entirely static page, pure JS doing multidimensional group-by traversal and hash aggregation produces severe memory fragmentation and processor overload.

**How it works**: A C++/Rust vectorized multidimensional aggregation core is compiled to Wasm. **Vectorized execution architecture**: the data file (Apache Parquet, say) streams into linear memory as binary columnar blocks, and Wasm processes not one record at a time but whole "data vectors" fed to the processor core in one go. **In-memory radix hash tables**: Wasm builds a highly optimized radix hash table inside the sandbox and runs multithreaded parallel aggregation, creating no JavaScript objects at any point.

**Performance**: Claimed that a complex compound group-by aggregation and live cross-tabulation recomputation over a 5,000,000-row structured dataset with 10 dimensions takes only **60–90 milliseconds** on the front end, more than **50× faster** than pure JS.

**Advantages**: Brings a static site "ClickHouse-class" ultra-fast front-end multidimensional aggregation and BI dashboards, saving expensive cloud database maintenance.
**Disadvantages**: Data is buffered entirely in Wasm memory by default, so **supporting persistent analysis of hundreds of millions of rows requires a complex binary chunked disk I/O design over OPFS**.

**Competitors**: Lodash.groupBy / Crossfilter (out of their depth past a million rows, prone to OOM or multi-second UI freezes). **More noteworthy is DuckDB-Wasm (case 5) — the real, verifiable version of this idea**, which has already solved OPFS persistence and remote Parquet querying.

---

### 67. (originally 86) NimBLE-Wasm — A Bluetooth Low Energy (BLE) protocol stack 🟡

**Pain point**: When developing a web IoT console or a medical wearable monitoring station, the front end talks to hardware through the Web Bluetooth API. But the browser's native Bluetooth API exposes only the high-level GATT read/write interface, without low-level packet destructuring, multi-device retry and flow control state machines, or special encrypted handshake support. Hand-writing high-frequency Bluetooth characteristic binary parsing and custom protocol reassembly in JS causes intermittent GC stutter through dynamic allocation, and packets are easily lost under high-frequency data flows (a live ECG at 100 samples per second).

**How it works**: The industrial C-language BLE core protocol stack **NimBLE** (familiar from ESP32 and Apache Mynewt) is compiled to Wasm. **A byte-stream protocol parsing pipeline (L2CAP/ATT layers)**: the raw `ArrayBuffer` the browser receives skips JS parsing and is written straight into Wasm's ring queue through a memory pointer; the NimBLE state machine inside takes protocol headers apart at the binary level at high speed, verifies them and reassembles packets. **Isolated memory defence**: every timeout retry and sliding-window flow control runs entirely inside the Wasm sandbox at very low overhead.

**Performance**: Claimed that under a stress test maintaining four Bluetooth medical devices with tens of thousands of characteristic bytes per second, protocol parsing is **15–22× faster** than pure JS, with CPU usage down 70%.

**Advantages**: Brings a static IoT back office an industrial-grade Bluetooth protocol stack with strong interference resistance and flow control; device data is parsed entirely locally.
**Disadvantages**: **It cannot bypass the browser's underlying security sandbox** and must still rely on external JS using the Web Bluetooth API as the hardware bridge, requiring a carefully designed secure event callback layer.

**Competitors**: A custom pure-JS Bluetooth parser (easy to develop, but inefficient under multi-device concurrency, high-frequency bit-shift parsing and precise flow control state machines, and prone to data delay or disconnection).

---

### 68. (originally 87) Espace3D-Wasm — 3D indoor acoustic ray tracing simulation 🔴

**Pain point**: In architectural engineering, concert hall design and high-end audio space planning, engineers must assess sound reflection, absorption and diffraction in 3D space to compute reverberation time (RT60) and sound field distribution. That requires dense **acoustic ray tracing**. Traversing a 3D geometry model in pure JS and running mesh intersection and material absorption iteration for millions of acoustic rays — without exact 64-bit spatial tree (BVH) addressing optimization — freezes the main thread for a long time.

**How it works**: A C++ high-performance indoor acoustic simulation core is compiled to Wasm via Emscripten, providing desktop-grade acoustic design. **Spatial boundary representation memory (BVH layout)**: the 3D building model's geometric vertices and the material acoustic absorption coefficient table (eight octave bands from 125 Hz to 8 kHz) are written strictly into linear memory as a binary byte stream, with a compact spatial partitioning tree built in memory. **Multi-core parallel ray evolution**: with Web Workers plus `SharedArrayBuffer`, the launch and reflection trajectories of millions of virtual acoustic rays are distributed in parallel across CPU cores, solving the impulse response at high speed at the binary level.

**Performance**: Claimed that launching 100,000 acoustic rays through a complex concert hall model of 10,000 polygons and computing full-band reverberation takes only **400–600 milliseconds** on the front end, at **80%** of native C++.

**Advantages**: Brings industrial-grade acoustic simulation to a static architectural design dashboard; **it pairs perfectly with the Web Audio API — the simulated impulse response (IR) can be convolved with music directly on the front end for live binaural monitoring preview of 3D spatial audio.**
**Disadvantages**: Dense geometry and ray tracing saturate the CPU briefly, so the total ray count must be capped carefully to avoid overload on mobile.

**Competitors**: Pure-JS geometric simulation libraries (lacking efficient vector arithmetic and cache-friendly multidimensional spatial tree addressing, more than 25× slower on high-precision spatial acoustic boundaries and entirely impractical).

---

### 69. (originally 88) Telemetry-Wasm — High-speed parsing of streaming telemetry time series 🔴

**Pain point**: Monitoring a large server cluster, an autonomous vehicle fleet or an industrial sensor network, the front end receives an unending stream of telemetry (timestamps, metric labels and values). Rendering a time series chart of millions of points live on a static monitoring dashboard, letting JS do the parsing means that a sudden "data storm" causes severe GC collapse from constantly turning binary into high-level objects, dropping the chart refresh rate into single digits.

**How it works**: A next-generation time series compression and parsing core written in Rust (or C), using a compression algorithm like Facebook's **Gorilla**, is compiled to Wasm. **A delta-of-delta time compression state machine**: data streams into linear memory, and Wasm runs delta-of-delta timestamp compression and XOR float value compression scanning directly on the raw byte stream through pointers (**creating no JS objects**). **A flat chart buffer**: parsed data is reassembled inside Wasm directly into a compact vertex matrix matching the WebGL/Canvas rendering format, bypassing JavaScript heap allocation throughout.

**Performance**: Claimed to parse and clean a large binary file of 2,000,000 high-frequency telemetry records in only **15–25 milliseconds**, more than **30× faster** than the pure-JS version, with main-thread GC pauses reduced to zero.

**Advantages**: Brings a free static monitoring dashboard industrial-grade time series big-data cleaning and live rendering; 100% zero backend cost, meeting enterprise privacy needs that logs never leave.
**Disadvantages**: The parsing algorithm inside is highly optimized for a specific time series format, so if the input format or standard protocol (Prometheus or a custom format) changes, the Wasm module must be recompiled.

**Competitors**: Pure-JS JSON/CSV parsers (out of their depth on streaming telemetry past a hundred thousand records, and prone to freezing the UI).

---

### 70. (originally 89) FeatureOCR-Wasm — Edge AI optical character feature extraction (HOG) 🔴

**Pain point**: For ID card recognition, licence plate scanning or handwriting recognition on the web, a preliminary step performs complex **feature extraction** and geometric correction on the image (histogram of oriented gradients (HOG), local binary patterns (LBP), texture analysis). Handing that dense computation to pure JS makes array traversal and floating-point arithmetic very inefficient on 4K photos; sending the whole large image to a cloud API brings expensive bandwidth metering and the risk of leaking highly sensitive documents.

**How it works**: The C++ core operators of industrial computer vision feature engineering are compiled to Wasm via Emscripten as the fallback compute engine for decentralized front-end AI. **Matrix sliding window acceleration**: the high-resolution image byte pointer captured from Canvas is written directly into Wasm linear memory, and fast pointer-driven table lookups run the convolution kernel and pixel matrix sliding window operations. **SIMD operator vectorization**: one CPU instruction computes the gradient direction and magnitude of 4 or 8 pixels in parallel, building a highly compact binary feature vector at high speed inside the sandbox.

**Performance**: Claimed that a 10-megapixel (4K) high-resolution ID photo takes only **35–50 milliseconds** on the front end for full-image HOG feature extraction and geometric correction, more than **25× faster** than pure JS.

**Advantages**: Brings a static page infinitely concurrent, zero-operations free AI feature preprocessing; 100% privacy-safe, with highly sensitive files staying entirely in the local sandbox.
**Disadvantages**: The feature extraction algorithm is fixed in the compiled binary module, so changing feature weights or the convolution formula dynamically requires recompilation.

**Competitors**: Pure-JS image processing libraries (lacking low-level memory alignment and bit-operation optimization, with CPU peaks that are too high on pixel-level traversal of large photos). **Note: OpenCV.js (case 27) is a more complete and verifiable superset of this idea.**

---

> **Summary of this part (36–70)**: This stretch is the catalog's **watershed**. The first half (36–51) is still mostly "move a mature C/C++ library onto the web," with the proportion of 🟡 rising noticeably; the second half (52–70) starts producing many entries that **cross into science and industry**, and 🔴 illustrative constructions appear densely for the first time.
> Three patterns are worth noticing. **First**, several 🔴 entries actually have 🟢 real counterparts (Cubism-OLAP → DuckDB-Wasm, FeatureOCR → OpenCV.js), meaning the idea's direction was right but "someone has already built it, just under a different name." **Second**, this part contains two clean demonstrations of the 4 GB ceiling (case 52's zk-EVM and case 53's 24-qubit limit). **Third**, case 51 (Ghidra-Wasm) forms a self-referential loop: running a decompiler in Wasm to analyze Wasm directly refutes the claim that "binaries are irreversible."
> The next part (71–101) enters the deepest water: **scientific and engineering simulation plus five foundational engines**, with the highest proportion of 🔴 — and also the best illustration of what "Wasm drove an entire field's barrier to entry to zero" really means.
