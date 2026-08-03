# Appendix F: The Hundred-Case Catalog of Static-Page Wasm (Part 3) — Cases 71–101

> Authenticity tags and reading method are the same as Appendices D and E. 🟢 Verifiable · 🟡 Upstream real, Wasm port unverified · 🔴 Illustrative construction. **All performance numbers are claims from the original conversation and have not been independently verified.**
>
> **A special note on this part**: 71–101 has the highest proportion of 🔴 in the whole catalog. That **does not mean it is worthless** — quite the opposite. This stretch best illustrates Chapter 6's judgement: **scientific and engineering computation is Wasm's highest-value domain, because it satisfies four conditions at once — the algorithms are public, the C implementations are mature, the barrier to entry is very high, and the data is extremely sensitive.** Nearly every technical path described here holds up; it is simply that nobody has built it yet, or someone has and it goes by another name. **Read these as a feasibility map, not a project index.**

---

## VI. Industrial and Engineering Simulation

### 71. (originally 90) Kinematics-Wasm — Inverse kinematics for six-axis robots 🟡

**Pain point**: In automation engineering and smart manufacturing, engineers control multi-joint robotic arms from the web (digital twin dashboards, online industrial robot programming platforms). When the user drags the end effector to a 3D coordinate with the mouse, the system must compute every joint's rotation angle in real time — **inverse kinematics (IK)** — involving extremely dense nonlinear trigonometric system solving, Jacobian matrix inversion and Newton-Raphson iteration. Pure JS handling high-frequency matrix iteration, without operator overloading or cache optimization, solves slowly and easily produces unnatural "joint jumps" or deadlocks through lost floating-point precision.

**How it works**: An industrial robot kinematics core (something like C++/Rust Orocos KDL) is compiled to Wasm. **DH parameter matrix memory**: the arm's Denavit-Hartenberg geometric parameters and the target's six-degree-of-freedom pose matrix are laid out strictly as contiguous aligned `f64` in linear memory. **A zero-GC differential iterator**: the algebraic optimizer inside Wasm performs singular value decomposition (SVD) and pseudo-inverse of the Jacobian at high speed at the binary level, with each iteration completing entirely in enclosed memory.

**Performance**: Claimed that one high-precision IK convergence solve for a seven-degree-of-freedom (redundant) industrial arm takes only **0.1–0.3 milliseconds** on the front end (thousands of solves per second), more than **35× faster** than pure JS, achieving smooth real-time tracking of the mouse drag.

**Advantages**: Brings industrial-control-grade high-precision kinematics to a static industrial digital twin platform; pairs perfectly with Three.js for live 3D arm simulation; zero backend cost.
**Disadvantages**: IK involves multiple solutions and singularities, so catching the C++ exceptions inside Wasm requires heavy glue design to prevent VM crashes.

**Competitors**: Pure-JS math libraries (whose compute and numerical precision are entirely inadequate for industrial real-time control when iterating high-DOF nonlinear geometric systems and solving sparse Jacobians).

---

### 72. (originally 91) BioClust-Wasm — Hierarchical clustering of single-cell RNA expression matrices 🔴

**Pain point**: In cancer research and modern biomedicine, scientists analyze the enormous gene expression matrices produced by single-cell RNA sequencing (scRNA-seq) (tens of thousands of cells × tens of thousands of gene features). The core steps are **hierarchical clustering** and Pearson correlation distance matrix computation. Previously that required a backend HPC cluster; offering an interactive heatmap and clustering derivation directly on a static medical dashboard is impossible in pure JS, which permanently freezes the main thread or crashes with OOM on millions of float elements through heavy dynamic allocation and no cache optimization.

**How it works**: A C++ industrial matrix clustering core (the core operators of the C Clustering Library, say) is compiled to Wasm. **Cache-aligned flat matrix layout**: gene expression data is laid out strictly as contiguous aligned `f32` in linear memory; computing the distance matrix allocates no JS objects at all, pushing L1/L2 hit rates to the limit. **SIMD vectorization and parallel divide-and-conquer**: one instruction computes Euclidean distances or correlation coefficients for four gene expression values in parallel, while Web Workers distribute the huge matrix's tree partitioning across CPU cores.

**Performance**: Claimed that full Pearson hierarchical clustering of a medical matrix of 5,000 cells and 20,000 gene features takes only **400–650 milliseconds** on the front end, more than **45× faster** than pure JS.

**Advantages**: Brings a static genetic medicine documentation site install-free scientific computation; **the patient's genetic privacy data stays 100% inside the local sandbox**, meeting the strictest requirements of international medical privacy (HIPAA) regulation.
**Disadvantages**: The binary tree structure the clustering produces is extremely low-level, so converting it into interactive DOM nodes at high frequency incurs cross-boundary deserialization overhead, requiring a shared `TypedArray` buffer optimization.

**Competitors**: Pure-JS math matrix libraries (fine for lightweight chart statistics, but outclassed by medical-scale gene features, high-dimensional matrix iteration and hierarchical tree linkage algorithms).

---

### 73. (originally 92) Kyber-WebPlatform — Post-quantum cryptography (PQC) key exchange 🟡

**Pain point**: As quantum computing advances, traditional asymmetric encryption based on RSA or ECC risks being broken by Shor's algorithm. The global security field is moving to post-quantum cryptography (PQC), and NIST has designated **CRYSTALS-Kyber** the standard for quantum-resistant key encapsulation (KEM). But Kyber's foundation involves extremely complex lattice-based number theoretic transforms (NTT) and polynomial ring algebra. Running that dense bit manipulation in pure JS on the web performs terribly, and **JS offers no constant-time execution guarantee, making it highly vulnerable to side-channel attacks leaking the key**.

**How it works**: The official CRYSTALS-Kyber core, written in Rust or optimized C, is compiled to Wasm. **A constant-time NTT engine**: Wasm performs strict butterfly operations and modular multiplication in linear memory using `i32`/`i64` instructions; the code ensures at the compilation level that it **contains no dynamic branch dependent on private key data**, defending against timing side channels. **Memory-safe randomness injection**: Wasm has no built-in random number generator, so the architecture safely calls the browser's native `crypto.getRandomValues()` through JS glue to inject environmental entropy into the post-quantum encryption matrices.

**Performance**: Claimed that a standard Kyber-512/768/1024 key encapsulation and decapsulation takes only **0.2–0.5 milliseconds** on the front end (thousands per second), at **85%** of native C.

**Advantages**: Brings a static page quantum-resistant end-to-end encrypted communication; the encryption private key stays inside the user's browser forever; zero backend cost.
**Disadvantages**: PQC's public keys and ciphertexts (usually a few kilobytes) are noticeably larger than traditional ECC curves, so the front end needs sturdier network transport glue to move those larger cryptographic byte blocks.

> ⚠️ **A necessary technical correction**: the original description said "Wasm guarantees constant-time execution" — **that needs a more precise statement**. The Wasm specification itself **does not guarantee** constant time; what it guarantees is that there is no JS-engine-style behaviour of switching internal representations by data type dynamically (V8's Smi → HeapNumber, say). But **the compiler may still introduce branches and the CPU may still exhibit data-dependent cache behaviour**. Constant time is guaranteed by **how the source is written** (avoid branching on the private key, avoid indexing a lookup table by it); Wasm merely provides an execution substrate more controllable than JS. **"It uses Wasm, so it is constant-time" is a dangerous misreading.**

**Competitors**: Pure-JS cryptographic emulation libraries (JS engines perform automatic type conversion while running dense bit shifts and bignum modular division, so they **cannot guarantee constant time at all** — a fatal defect in security defence).

---

### 74. (originally 93) Hologram3D-Wasm — 3D optical holographic microscopy tomographic reconstruction 🔴

**Pain point**: In biophysics and cell imaging, digital holographic tomography (DHT) lets scientists reconstruct the 3D refractive index distribution inside a cell from multi-angle holograms without staining (non-destructively). The core is a huge 3D inverse scattering algorithm involving FFT over hundreds of high-resolution 2D interferograms, three-dimensional filtered back projection (FBP) and nonlinear multiple scattering iteration. That heavy computation previously depended on a workstation GPU.

**How it works**: A C++ 3D optical holographic reconstruction algorithm core is compiled to Wasm. **Complex 3D Fourier space memory**: a contiguous flat space of up to hundreds of megabytes is allocated in linear memory, storing the 3D frequency-domain matrix strictly as double-precision complex numbers (two `f64` for amplitude and phase), cutting memory addressing overhead substantially. **SIMD-accelerated back projection**: one CPU instruction computes optical path difference (OPD) and phase unwrapping iteration for several pixels in parallel, restoring multi-angle 2D interference fringes to 3D refractive index volume data inside the sandbox.

**Performance**: Claimed that reading 100 1024×1024 2D holograms and reconstructing a 512×512×512 3D cellular refractive index model takes only **1.8–3.2 seconds** on the front end, more than **40× faster** than pure JS.

**Advantages**: Brings a static research platform install-free desktop-grade 3D tomographic reconstruction; the biological sample data is parsed entirely locally.
**Disadvantages**: 3D holographic reconstruction is extremely memory-hungry. **With too many 2D holograms or too high a resolution it easily hits the 4 GB ceiling, so a careful "chunked pull" architecture is required** (the scenario Chapter 8's escape route one exists for).

**Competitors**: Pure-JS 3D matrix processing (lacking efficient pointer manipulation and cache-friendly multidimensional layout, crashing with OOM outright on massive floating-point 3D frequency-domain transforms).

---

### 75. (originally 94) Nesting2D-Wasm — Irregular polygon nesting optimization 🔴

**Pain point**: In machining, sheet metal fabrication, leather cutting and garment textiles, arranging thousands of arbitrarily shaped 2D parts on one sheet with rotation and tight packing to maximize material utilization is called **nesting optimization**. It is NP-hard, and its core involves solving the no-fit polygon (NFP) for irregular polygons, Minkowski sums, geometric collision detection and high-order heuristic search based on genetic algorithms or simulated annealing. Iterating irregular geometry vertex intersections repeatedly in pure JS on the front end is slow and easily overlaps parts through lost floating-point precision.

**How it works**: The C++ core algorithm library of an industrial CAD/CAM nesting system (optimized operators based on the open-source geometry library GEOS, say) is compiled to Wasm. **Flat polygon geometry memory (NFP layout)**: every part's polygon vertex coordinates and rotation angle matrices are laid out strictly as contiguous aligned `f64` in linear memory, computing polygon envelope cutting at high speed at the binary level. **Multi-core heuristic parallel search**: with Web Workers plus `SharedArrayBuffer`, genetic algorithm populations for different rotation angles and nesting orders are distributed in parallel across CPU cores.

**Performance**: Claimed that a deep nesting optimization of 200 highly irregular garment pieces (500 generations of population iteration) takes only **1.2–2.5 seconds** on the front end to produce a nesting configuration exceeding 85% utilization (in G-code/DXF), more than **35× faster** than pure JS.

**Advantages**: Brings industrial-control-grade geometric nesting optimization to a static industrial CAD/CAM cloud workbench; pairs perfectly with SVG/Canvas for live animation of the nesting toolpath.
**Disadvantages**: NFP computation is extremely complex, so if the parts contain high-frequency noisy vertices (a rough polygon produced by scanning, say), the front end must simplify the geometry first.

**Competitors**: Pure-JS geometry libraries (Poly2Tri and the like, whose compute and geometric precision are entirely inadequate for industrial production when solving Minkowski sums of dense irregular bodies and iterating high-order heuristics).

---

### 76. (originally 95) HydroSolver-Wasm (EPANET) — Pipe network hydraulics and transient fluid simulation 🟡

**Pain point**: In municipal engineering, water resources planning and nuclear plant cooling system design, engineers must run hydraulic dynamic simulations on giant pipe networks with tens of thousands of pipes, pumps and valves. In particular, the **water hammer effect** caused by a valve slamming shut requires solving a complex nonlinear hyperbolic system of partial differential equations. That usually relies on the authoritative C core **EPANET** (using finite element and method-of-characteristics approaches). Showing live pressure wave propagation through a pipe network on the web previously meant uploading the topology to a backend finite element workstation, at astronomical cost under concurrency.

**How it works**: The EPANET hydraulics core — hundreds of thousands of lines of rigorous C — is compiled to Wasm in full. **An exact sparse linear system solver**: the pipe network topology is converted in Wasm memory to a contiguous binary compressed sparse matrix, with an efficient incomplete Cholesky factorization and conjugate gradient (CG) iterator integrated internally. **A zero-GC transient advance state machine**: every time step's dynamic transient advance and nonlinear pipe friction term (Hazen-Williams or Darcy-Weisbach) solve completes entirely in contiguous memory.

**Performance**: Claimed that a full finite element solve of a giant urban pipe network of 10,000 pipe nodes evolving over 24 hours (fine transient simulation at a 0.1-second step) takes only **80–130 milliseconds** on the front end, at national water engineering standard precision and more than **35× faster** than pure JS.

**Advantages**: Brings industrial fluid mechanics solving to a static industrial digital twin water platform; pairs perfectly with WebGL for live colour contour visualization of citywide pipe network pressure wave oscillation.
**Disadvantages**: The finite element method involves extensive boundary conditions and topology matrix initialization; if the input pipe network has dead ends or non-physical topology errors, the C assertions inside Wasm easily crash the VM, so the front end needs very strong topology pre-validation glue.

**Competitors**: Pure-JS math libraries (whose compute and numerical stability are entirely inadequate for real-time industrial control when solving large sparse linear systems and iterating nonlinear fluid PDE time steps).

---

### 77. (originally 96) QuantMCMC-Wasm — Financial derivative pricing and MCMC simulation 🔴

**Pain point**: In quantitative finance and risk management, precisely valuing complex barrier options, Asian options or multi-asset path-dependent derivatives requires solving high-dimensional stochastic differential equations. The most authoritative approach runs **Markov chain Monte Carlo (MCMC)** path simulation and stochastic volatility model (the Heston model, say) iteration, which means high-frequency random sampling and PDE evolution over millions of asset price trajectories. That computation previously ran entirely on backend HPC financial clusters.

**How it works**: The C++/Rust industrial quantitative finance core (QuantLib's stochastic simulation operators, say) is compiled to Wasm. **A flat path memory layout**: a million simulated trajectories' time steps and asset matrices are laid out strictly as contiguous `f64` in linear memory, allocating no JS objects while computing asset expectations. **SIMD random number vectorization**: paired with a very fast Mersenne Twister or PCG random number algorithm, one CPU instruction generates four Gaussian random variables in parallel, advancing the Black-Scholes-Merton jump model at high speed at the binary level.

**Performance**: Claimed that pricing a stochastic volatility option by simulating 1,000,000 asset paths of 252 trading days each takes only **180–280 milliseconds** on the front end, more than **45× faster** than pure JS.

**Advantages**: Brings a static quantitative analysis platform workstation-grade high-precision derivative pricing; **a quant firm's core strategy parameters and client portfolios stay 100% local and are never uploaded to the cloud**, giving perfect trade secret protection.
**Disadvantages**: The MCMC path data lives in Wasm memory, so **if the front end wants to draw a detailed line chart of all million trajectories dynamically, the browser's DOM rendering layer faces an enormous bottleneck**; use a Canvas bitmap or sampling to lower the chart's load.

**Competitors**: Pure-JS financial math libraries (fine for ordinary compound interest and simple analytic Black-Scholes solutions, but outclassed by high-dimensional path dependence, multi-asset correlation matrix evolution and dense MCMC iteration).

---

### 78. (originally 97) AstroNoise-Wasm — Deep-space astronomical image denoising and PSF deconvolution 🔴

**Pain point**: Deep-space multispectral images from astronomical telescopes (FITS format) usually contain severe cosmic ray noise, thermal noise and optical distortion. To extract faint galactic outlines, astronomers must run **point spread function (PSF) deconvolution** (Richardson-Lucy iteration, say) and high-order non-local means denoising over gigabytes of raw pixel matrices. Traditionally that could only run on a large Linux workstation inside the observatory network.

**How it works**: A high-performance C-language image restoration algorithm core is compiled to Wasm via Emscripten. **A 3D multispectral band memory pool**: the very large high-precision pixel matrices of several bands are written into linear memory as a binary byte stream, building a compact flat 3D image matrix in memory and bypassing JavaScript object allocation entirely. **SIMD-accelerated matrix convolution**: one CPU instruction computes the weight kernel function and FFT frequency-domain filtering for 4 or 8 double-precision pixels in parallel, separating faint hidden starlight from the background noise inside the sandbox.

**Performance**: Claimed that processing a 4-band, 4096×4096 raw deep-space image with 50 Richardson-Lucy deconvolution iterations takes only **1.5–2.8 seconds** on the front end, at **80%** of native C.

**Advantages**: Brings a static science-sharing site install-free desktop-grade scientific image analysis; astronomical images are processed entirely locally, consuming none of the developer's bandwidth.
**Disadvantages**: Denoising large astronomical images is extremely memory-hungry, and **too many bands easily hits the 4 GB ceiling**, so the architecture needs chunked sliding-window streaming.

**Competitors**: Pure-JS image processing libraries (lacking efficient bit operations and cache-friendly multidimensional layout, freezing with OOM outright on massive floating-point 2D/3D frequency-domain transforms and matrix neighbourhood computations).

---

### 79. (originally 98) SynapseSim-Wasm — Large-scale network simulation of neuronal synaptic dynamics 🔴

**Pain point**: In computational neuroscience, simulating signal transmission and memory mechanisms in brain neuronal networks means solving biophysics's most famous **Hodgkin-Huxley nonlinear system of partial differential equations** — deriving the open/closed state of sodium and potassium ion channels on the cell membrane, the dynamic membrane potential and the weight evolution of thousands of synapses exactly. The authoritative simulation cores are usually written in C++. Hand-writing those neurodynamic time step iterations in JS on the web produces **numerically divergent** wrong results within a few iterations, for lack of exact 64-bit alignment and parallel matrix acceleration.

**How it works**: A computational neuroscience open-source core is compiled to Wasm, providing decentralized brain network simulation. **A synaptic adjacency binary matrix**: the complex synaptic links among tens of thousands of neurons are converted in linear memory into a flat, cache-friendly binary compressed sparse column (CSC) matrix. **A zero-GC exponential integrator**: the algebraic optimizer inside Wasm performs nonlinear approximation of the ion channel gating variables at high speed at the binary level; every time step advance completes entirely inside Wasm, cutting main-thread GC pauses to zero.

**Performance**: Claimed that simulating 10 seconds of network activity (fine derivation at a 0.1-millisecond step) over 10,000 neurons with 500,000 dynamic synaptic weights takes only **250–400 milliseconds** on the front end, at international neuroscience standard precision and more than **40× faster** than pure JS.

**Advantages**: Brings a static science and education dashboard workstation-precision biological network simulation; pairs perfectly with Three.js for live 3D visualization of neuronal spiking action potential propagation.
**Disadvantages**: Nonlinear differential systems are extremely sensitive to initial conditions, and if the input network topology contains non-physical isolated nodes or anomalous weights, the C assertions inside Wasm easily crash the VM.

**Competitors**: Pure-JS math libraries (whose compute and numerical stability are entirely inadequate for research-grade real-time simulation when iterating high-dimensional nonlinear differential systems and solving sparse synaptic network matrices).

---

### 80. (originally 99) GridPower-Wasm — Newton-Raphson AC power flow solving for smart grids 🔴

**Pain point**: In power engineering and energy planning, to ensure a grid does not black out during a sudden demand peak or an unplanned unit outage, the dispatch system must run dense **AC power flow** computation — solving a complex nonlinear algebraic system (the nodal power balance equations) for a network of tens of thousands of substations, generating units and transmission lines. The industry's most authoritative approach is **Newton-Raphson iteration** with admittance matrix solving. Handling the Jacobian inverse of a large sparse matrix in pure JS on the front end performs so badly that the page freezes.

**How it works**: A national-grade power system analysis open-source C core is cross-compiled to Wasm via Emscripten. **Compressed sparse admittance matrix memory (Y-bus)**: the large grid's nodal admittance matrix (99.9% zeros) is laid out strictly in contiguous binary CSC format in linear memory, with an efficient sparse LU factorization and forward/backward substitution iterator integrated internally, bypassing JS object creation entirely. **A zero-GC matrix correction iterator**: every Jacobian update and nonlinear power mismatch computation runs inside the Wasm sandbox, with multi-core CPUs scanning in parallel at the binary level.

**Performance**: Claimed that one AC power flow Newton-Raphson convergence solve for a large regional smart grid of 5,000 bus nodes and 12,000 transmission lines takes only **15–30 milliseconds** on the front end (dozens of solves per second), at IEEE industrial standard precision and more than **35× faster** than pure JS.

**Advantages**: Brings a static national power monitoring dashboard industrial-grade nonlinear grid solving; **guarantees that critical national infrastructure data (grid topology) is never transmitted across servers over the network** — extremely high security.
**Disadvantages**: Power flow computation involves multiple solutions and Jacobian singularities (grid collapse thresholds, say), and if the exception control inside Wasm is not fully optimized, the module can crash.

**Competitors**: Pure-JS matrix libraries (whose compute and precision are entirely inadequate for smart grid digital twin scenarios when performing complex LU factorization of large industrial sparse matrices and high-order iteration of nonlinear algebraic systems).

---

### 81. (originally 100) TopOpt3D-Wasm — Aerospace-grade 3D structural topology optimization (SIMP) 🔴

**Pain point**: In aerospace engineering and advanced manufacturing (design ahead of 3D printing), making a wing or satellite bracket "maximally light" while preserving ultimate strength requires **3D structural topology optimization**. The core is the **SIMP (Solid Isotropic Material with Penalization)** algorithm — chopping the 3D design space into millions of 3D finite elements, solving the stochastic elasticity PDE under given loads and boundary conditions, and optimizing each element's material density dynamically. That heavy computation previously depended entirely on CAD supercomputer workstations.

**How it works**: The aerospace industry's decades-accumulated C++ 3D finite element topology optimization core is compiled to Wasm in full, providing top-tier high-precision generative design. **Flat elasticity matrix memory**: the displacement vectors, stiffness matrices and material density gradients of millions of mesh elements in 3D space are laid out strictly as contiguous aligned `f64`, solving the finite element system (KU = F) by conjugate gradient at high speed at the binary level. **Multi-core sensitivity parallel filtering**: with Web Workers plus `SharedArrayBuffer`, each element's resultant stress, strain energy and material sensitivity filtering is distributed in parallel across CPU cores.

**Performance**: Claimed that 50 generations of standard SIMP topology optimization on a complex wing structure of 120,000 3D hexahedral elements (including reassembling and solving the stiffness system each iteration) takes only **2.5–4.5 seconds** on the front end to produce optimized geometry with 60% volume reduction and maximized strength, more than **50× faster** than pure JS.

**Advantages**: Brings a static advanced manufacturing cloud CAD platform install-free industrial 3D generative design; pairs perfectly with WebGL/WebGPU for live 3D visualization of "material disappearing step by step as the structure evolves."
**Disadvantages**: 3D finite element solving builds a large global stiffness matrix, so **memory grows exponentially with mesh resolution and too fine a mesh hits the 4 GB ceiling**, requiring careful sparse matrix reordering and streaming elimination architecture.

**Competitors**: Pure-JS math and geometry libraries (whose compute and numerical stability are entirely inadequate for aerospace design and manufacturing when solving large 3D finite element stiffness systems and filtering nonlinear material density sensitivity across time iterations).

---

### 82. (originally 101) Microfluidic3D-Wasm — Microfluidic channel topology optimization for bioprinting 🔴

**Pain point**: In 3D bioprinting of artificial organs and lab-on-a-chip development, designing the extremely complex micron-scale microfluidic channel network that delivers oxygen and nutrients precisely to every cell of an artificial tissue is a cutting-edge challenge. It means solving the low-Reynolds-number microfluidic Navier-Stokes system (Stokes flow) at microscopic scale plus geometric topology shape optimization. Medical engineers traditionally needed an expensive local finite element workstation.

**How it works**: The medical field's open-source C++ microfluidic physics operators and a **lattice Boltzmann method (LBM)** core are compiled to Wasm. **Microscopic lattice flat memory layout**: the channel space is discretized into a dense 3D virtual lattice, with each cell's fluid density and velocity distribution functions laid out strictly as contiguous `f32` in linear memory; the collision and streaming steps allocate no JS objects at all, pushing L1/L2 hit rates to their physical limit. **Multithreaded parallel flow field solving**: with Web Workers plus `SharedArrayBuffer`, the 3D microscopic space is cut into subregions distributed in parallel, computing channel shear stress and geometric shape gradients at high speed inside the sandbox.

**Performance**: Claimed that 1,000 steps of high-precision LBM flow field evolution and topology deformation optimization on a 3D organ channel of 64,000 microscopic lattice cells takes only **280–450 milliseconds** on the front end, more than **45× faster** than pure JS.

**Advantages**: Brings a static biomedical research platform install-free desktop-grade microscopic fluid simulation and generative design; **a medical institution's core artificial organ geometry patents and patient stem cell structure data stay 100% local.**
**Disadvantages**: The microfluidic simulation's memory layout is extremely abstract, so if the front end wants to sample local flow velocities at high frequency to draw fine 3D streamline animation, cross-boundary conversion adds overhead; share the memory pointer with a WebGL vertex buffer for direct hardware rendering.

**Competitors**: Pure-JS fluid simulation libraries (fine for 2D web smoke or water droplet visual effects, but outclassed by medical-grade microscopic low-Reynolds-number 3D PDE solving and industrial geometric topology sensitivity filtering).

---

### 83. (originally 102) SwarmPath-Wasm — Distributed motion planning and dynamic obstacle avoidance for drone swarms 🔴

**Pain point**: In autonomous driving, warehouse robotics and drone light show choreography, getting hundreds or thousands of individuals to advance in parallel through 3D space and avoid each other and dynamic obstacles autonomously and in real time, with no central server directing, is a core problem in robotics. The most authoritative algorithm solves the high-order **reciprocal velocity obstacle (RVO / ORCA)** model, which requires every agent to solve a 3D linear program and nonlinear convex optimization matrix at speed within a 60 Hz control cycle. Pure JS traversing and solving the interaction collision convex hulls among thousands of agents causes severe GC stutter from constant allocation — **and in drone swarm control, where real-time behaviour is critical, that translates directly into mid-air collisions.**

**How it works**: An industrial multi-agent dynamics and collision avoidance algorithm core written in Rust is compiled to Wasm. **A cache-friendly agent matrix (SoA state space)**: every drone's 3D position, velocity vector, physical radius and dynamic response constraints are laid out strictly as contiguous binary structure-of-arrays. **Two-level 3D KD-tree spatial addressing and parallel solving**: Wasm allocates contiguous flat memory internally to build a fast 3D KD-tree, drones search for neighbours at high speed inside the sandbox, and each drone's convex space linear programming solve is distributed in parallel through Web Workers.

**Performance**: Claimed that simulating fully distributed 3D trajectory planning, dynamic obstacle avoidance and convex optimization iteration for **2,000 drones** in one virtual space keeps each physics control cycle within **1.8–3.2 milliseconds**, locking 60 FPS at **85%** of the native core.

**Advantages**: Brings a static robot choreography tool latency-free real-time distributed motion planning; fully decentralized, saving the cost of renting a high-performance cloud parallel compute host; can drive derivations against drone hardware directly in a network-free environment.
**Disadvantages**: The RVO model's convex optimization may need high-order random perturbation at extreme deadlock configurations (every drone converging on the exact centre, say), and the state machine's boundary conditions inside Wasm are extremely delicate, requiring very strong defensive coding.

**Competitors**: Pure-JS pathfinding libraries (suited only to small-scale, low-dimensional, discrete grid path search, and orders of magnitude behind on multi-body nonlinear convex optimization for thousands of agents in high-dimensional continuous 3D space).

---

### 84. (originally 103) LiFiLight-Wasm — Indoor optical communication multipath diffuse light field simulation 🔴

**Pain point**: Wireless optical communication (LiFi) uses indoor LED lighting for ultra-high-speed data transfer. To assess signal coverage strength and multipath interference in every corner of a room, optical communication engineers must model the room's walls and furniture geometrically and run dense **indoor light field multipath diffuse radiosity numerical integration** — computing the geometric visibility (form factor) between any two surface patches and iterating thousands of photon diffuse reflection energy attenuations. Traditionally that required a backend finite element matrix workstation.

**How it works**: The C++ core of industrial optical engineering and 3D radiosity is compiled to Wasm via Emscripten. **Surface patch flat memory layout**: the 3D coordinates, normals, reflectances and initial optical power of the tens of thousands of radiosity patches into which every indoor polygonal surface is subdivided are written strictly as contiguous `f64` into linear memory, building a highly compact sparse form factor matrix at the binary level. **SIMD-accelerated hemispherical integration**: one CPU instruction computes optical path attenuation and hemispherical solid angle numerical integration (Gauss quadrature) between several patches in parallel, running Markov matrix multiplication iteration at high speed inside the sandbox.

**Performance**: Claimed that five complete multipath diffuse light field evolutions and LiFi signal throughput recomputations over a complex 3D indoor space of 5,000 geometric patches take only **120–190 milliseconds** on the front end, at ITU standard precision and more than **40× faster** than pure JS.

**Advantages**: Brings a static IoT planning dashboard light field distribution simulation as precise as professional optical software; pairs perfectly with WebGL to render LiFi signal strength as a dynamic 3D colour contour map.
**Disadvantages**: **The radiosity matrix's computation grows quadratically with patch count, O(N²)**, so an over-detailed unsimplified indoor geometry easily hits a processor bottleneck, requiring a sparse matrix compression architecture built inside Wasm to filter it.

**Competitors**: Pure-JS geometric simulation libraries (lacking efficient vector arithmetic and cache-friendly multidimensional sparse matrix addressing, extremely slow on high-dimensional optical numerical integration).

---

### 85. (originally 104) FinCopula-Wasm — Credit risk and copula solving for giant asset portfolios 🔴

**Pain point**: In the risk management of financial holding groups and multinational banks, guarding against systemic collapse means running extreme stress tests of value at risk (VaR) and expected loss on "giant portfolios" containing tens of thousands of loans, bonds or derivatives. The core solves a high-dimensional nonlinear algebraic system of **copulas** (Student-t or Clayton copulas, say) to capture the nonlinear "tail dependence" among many assets during an extreme market collapse. That involves dense Cholesky factorization of the Pearson correlation matrix, high-order nonlinear ODE iteration and giant matrix inversion.

**How it works**: A high-order quantitative finance core in C, recognized by international financial audit standards, is compiled to Wasm via Emscripten. **A flat financial covariance matrix**: the historical return series and volatility weights of tens of thousands of instruments in the portfolio are laid out strictly as contiguous aligned `f64`, with an efficient multivariate distribution sampling state machine integrated internally. **A zero-GC Cholesky matrix iterator**: every Jacobian update and maximum likelihood estimation (MLE) of high-dimensional copula tail dependence runs inside the Wasm sandbox, with multi-core CPUs scanning in parallel at the binary level.

**Performance**: Claimed that a full nonlinear solve and extreme loss computation for a 2,000-dimensional Student-t copula credit risk portfolio with 500,000 Monte Carlo path samples takes only **150–260 milliseconds** on the front end, meeting Basel accord precision and more than **35× faster** than pure JS.

**Advantages**: Brings a static quantitative platform workstation-grade high-dimensional portfolio risk measurement; **a financial group's core asset allocations and sensitive client loan details stay 100% local and are never uploaded to the cloud.**
**Disadvantages**: When solving extreme tail probabilities in high-dimensional copulas, if the asset data has serious gaps, the C numerical overflow catching inside Wasm needs careful glue design to prevent VM crashes.

**Competitors**: Pure-JS financial math libraries (fine for ordinary portfolio expected return and simple asset allocation solving, but orders of magnitude behind on high-dimensional copula tail nonlinear coupling, giant matrix Cholesky factorization and dense MCMC iteration).

---

### 86. (originally 105) DNAKinetics-Wasm — Multi-sequence hybridization thermodynamics for gene chips 🔴

**Pain point**: In modern biotechnology, disease gene screening and DNA computing, engineers must design the probes on a gene chip. That means simulating the **multi-sequence hybridization kinetics and thermodynamic equilibrium** by which thousands of single-stranded DNA sequences bind to sample DNA at a given temperature and salinity — solving a highly complex nonlinear system of mass action law equations, computing the Gibbs free energy and pairing partition function for each sequence pair, and the "cross-hybridization" effects imperfect matches cause. Iterating giant nonlinear biochemical state matrices in pure JS on the front end solves very slowly for lack of 64-bit memory layout optimization, and easily produces entirely wrong matching results through lost floating-point precision.

**How it works**: The bioinformatics field's authoritative C++ gene thermodynamics and kinetics core (the core operators of ViennaRNA or DINAMelt, say) is compiled to Wasm. **Flat base matrix memory**: every probe sequence's Watson-Crick base pairing energy parameter table and dynamic concentration matrix are laid out strictly as contiguous aligned `f64`, running multimer dynamic programming cutting computations at high speed at the binary level. **Multi-core biochemical equilibrium parallel search**: with Web Workers plus `SharedArrayBuffer`, the thermodynamic partition function matrix solves for different sequence combinations are distributed in parallel across CPU cores.

**Performance**: Claimed that a full nonlinear thermodynamic system solve and cross-hybridization equilibrium concentration prediction for 1,000 candidate DNA probe sequences against a complex viral sample sequence takes only **90–140 milliseconds** on the front end to produce an exact biochemical equilibrium constant report (free energy precision to 0.01 kcal/mol), more than **50× faster** than pure JS.

**Advantages**: Brings a static online bioinformatics workbench national-laboratory-grade gene thermodynamics derivation; pairs perfectly with HTML5 charts for live visualization of probe hybridization efficiency.
**Disadvantages**: Newton-Raphson iteration of multi-sequence nonlinear biochemical systems is extremely sensitive to initial concentrations, and if the input sequence contains invalid nucleotide characters, catching the C++ exceptions inside Wasm requires heavy glue design to prevent crashes.

**Competitors**: Pure-JS biochemical simulation libraries (whose compute and precision are entirely inadequate for clinical diagnosis when solving dense nucleic acid secondary structure partition functions and iterating high-order nonlinear biochemical kinetic equilibrium systems).

---

### 87. (originally 106) SonarICA-Wasm — Underwater sonar blind source separation and independent component analysis 🔴

**Pain point**: In ocean engineering and autonomous underwater vehicle (AUV) detection, the signal a sonar receives is usually mixed with ocean background noise, propeller cavitation noise and severe multipath reflections. Separating the true returns of a target submarine or the seabed from that chaotic waveform requires **blind source separation (BSS)**, whose mathematical core is dense **independent component analysis (ICA, such as FastICA)** — high-frequency singular value decomposition (SVD) of covariance matrices, nonlinear negentropy maximization iteration and whitening transforms over massive multi-channel audio byte streams. Traditionally that depended on a backend ocean computing host.

**How it works**: An industrial C++ array signal processing and ICA core algorithm library is compiled to Wasm via Emscripten. **Multi-channel audio flat memory layout**: the raw `ArrayBuffer` collected by the hydrophone array skips JS parsing and is written directly through a memory pointer into Wasm's contiguous linear memory; computing eigenvalues and the mixing matrix allocates no high-level JS objects at all. **SIMD vectorized matrix acceleration**: one CPU instruction runs fourth-order cumulants and dot product iterations for several channels' audio samples in parallel, restoring the independent sonar source signals at high speed inside the sandbox.

**Performance**: Claimed that high-precision FastICA blind source separation and deconvolution of a giant 8-channel sonar multipath signal stream at 192 kHz sample rate takes only **40–65 milliseconds** per frame on the front end, more than **35× faster** than pure JS.

**Advantages**: Brings a static ocean engineering dashboard workstation-precision array signal processing; detection data and underwater target signatures stay entirely local, protecting defence and commercial secrets.
**Disadvantages**: ICA is highly sensitive to the signal whitening initial matrix, and if underwater noise changes abruptly and the glue lacks overflow protection, catching the C++ exceptions inside Wasm requires heavy design to prevent crashes.

**Competitors**: Pure-JS signal processing libraries (fine for ordinary Web Audio filtering, but whose compute and numerical stability are entirely inadequate for industrial ocean control when iterating high-dimensional multi-channel nonlinear matrices and approximating fourth-order matrix maximum likelihood).

---

### 88. (originally 107) TSNSched-Wasm — TSN time slot scheduling and MILP heuristic search for the connected car 🔴

**Pain point**: In smart transportation, vehicle-to-everything (V2X) and Industry 4.0 smart factories, ensuring an autonomous vehicle's braking command or a robotic arm's synchronization signal is never delayed requires the network stack to adopt the **time-sensitive networking (TSN)** standard. TSN's core value is microsecond-precise gate control list (GCL) scheduling. Allocating non-conflicting time slots for thousands of periodic and aperiodic hard real-time data flows across every switch in the network is an NP-hard **mixed integer linear programming (MILP)** problem. That previously ran only on a dedicated backend scheduling server; pure JS facing tens of thousands of time window constraints freezes for minutes from array slicing and excessive CPU peaks.

**How it works**: The C++ core toolchain of industrial network scheduling plus high-performance heuristic search (tabu search, simulated annealing) algorithm libraries are compiled to Wasm. **Flat network topology memory layout**: network nodes, switch ports, flow periods and maximum tolerable latency constraints are laid out strictly as a binary structure-of-arrays. **Multi-core constraint solving parallelization**: with Web Workers plus `SharedArrayBuffer`, fast interval trees and non-conflict hash tables are built, and different scheduling branches and branch-and-bound tasks are distributed in parallel across CPU cores.

**Performance**: Claimed that GCL time slot scheduling optimization (satisfying zero-jitter constraints) for a giant TSN topology of 50 switch nodes and 2,000 high-frequency V2X data flows takes only **800–1200 milliseconds** on the front end to produce a conflict-free schedule, more than **40× faster** than pure JS.

**Advantages**: Brings a static network management console industrial-grade time-sensitive scheduling computation; fully decentralized, so an engineer commissioning a 5G V2X or factory automation line on site can compute topology extremely fast from a web page.
**Disadvantages**: MILP solving has an unpredictable convergence time at deadlock boundaries under extreme network overload, requiring a carefully built **timeout forced-interrupt state machine** inside Wasm.

**Competitors**: Pure-JS linear programming libraries (suited only to small linear optimization, and entirely inadequate in compute and memory scheduling for industrial production when facing tens of thousands of microsecond-scale hard time window constraints, dense topology routing and mixed integer approximation).

---

### 89. (originally 108) AstroAO-Wasm — Adaptive optics atmospheric turbulence wavefront reconstruction 🔴

**Pain point**: When a large ground-based astronomical telescope observes distant galaxies, starlight passing through the atmosphere is distorted by turbulence. Modern observatories use **adaptive optics (AO)**, where a wavefront sensor captures distortion data thousands of times per second and computes the adjustment voltage of the deformable mirror's hundreds of actuators in real time. The core is a large **nonlinear matrix inversion for wavefront reconstruction** — singular value decomposition of a large sparse Jacobian and high-order polynomial fitting. Traditionally that had to run on hardware FPGAs local to the observatory.

**How it works**: A top international observatory's open-source C++ adaptive optics reconstruction algorithm core is compiled to Wasm via Emscripten. **Wavefront geometry flat memory layout**: the slope data for the thousands of subapertures the wavefront sensor carves out plus the deformable mirror control matrix are written strictly as contiguous `f64` into linear memory, building a highly compact sparse control matrix at the binary level and bypassing JavaScript object allocation entirely. **SIMD-accelerated gradient inversion**: one CPU instruction computes several subapertures' wavefront phase slopes and least squares iteration in parallel, running matrix multiplication solving at high speed inside the sandbox.

**Performance**: Claimed that one full atmospheric turbulence wavefront distortion correction and control matrix recomputation for a giant AO system of 4,096 subapertures and 1,000 deformable mirror actuators takes only **8–14 milliseconds** on the front end (nearly a hundred per second), at aerospace and astronomy industrial precision and more than **45× faster** than pure JS.

**Advantages**: Brings a static science-sharing site install-free desktop-grade wavefront reconstruction and atmospheric optics simulation; astronomical optical data is processed entirely locally.
**Disadvantages**: **The wavefront inversion matrix's computation grows with the cube of the aperture count, O(N³)**, so an over-detailed sensor grid without dimensionality reduction easily hits a single-core bottleneck, requiring a sparse matrix incomplete Cholesky factorization built inside Wasm to filter it.

**Competitors**: Pure-JS image and matrix libraries (lacking efficient pointer arithmetic and cache-friendly multidimensional sparse matrix addressing, extremely slow on high-dimensional optical numerical matrix inversion).

---

### 90. (originally 109) MicroPhase-Wasm — Phase field simulation of metallic grain evolution in materials science 🔴

**Pain point**: In materials science, metallurgy and aerospace alloy manufacturing, how "grain structure" evolves during metal solidification or heat treatment determines the material's mechanical strength and fatigue life directly. Simulating grain crystallization, grain boundary segregation and dendritic growth precisely means solving a complex **phase field nonlinear system of partial differential equations (Allen-Cahn or Cahn-Hilliard)** — running hundreds of thousands of Laplacian discretizations, interface curvature computations and dense time step evolutions over a 3D or 2D microscopic space grid. That previously depended on a national materials laboratory's GPU supercomputing cluster.

**How it works**: A materials physics open-source C++ high-performance phase field simulation core is compiled to Wasm. **Flat grain order parameter memory**: each grid point's phase field order parameter, solute concentration and elastic strain energy are laid out strictly as contiguous aligned `f32`, maximizing processor cache hit rates. **A SIMD spatial difference accelerator**: one CPU instruction solves high-order finite difference Laplacians for 4 or 8 spatially symmetric points in parallel; every time step's nonlinear dynamic advance runs entirely inside the Wasm sandbox.

**Performance**: Claimed that 5,000 steps of high-precision crystallization, dendritic growth and grain boundary evolution iteration on a 512×512 grid multi-component alloy microstructure takes only **350–550 milliseconds** on the front end, at international materials physics standard precision and more than **50× faster** than pure JS.

**Advantages**: Brings a static materials engineering page research-laboratory-grade microstructural physical evolution; **an alloy's core formulation and crystallization evolution signature data stay 100% local**, protecting patents.
**Disadvantages**: The Cahn-Hilliard equation is a fourth-order nonlinear PDE with extremely strict time step stability requirements; if the user inputs non-physical initial solute fluctuations, a careful **adaptive time step control state machine** must be built inside Wasm.

**Competitors**: Pure-JS math and image libraries (orders of magnitude behind on dense microscopic-space PDE finite difference solving and multi-component order parameter time step iteration).

---

### 91. (originally 110) CSTRFlow-Wasm — Stiff ODE solving for chemical reactors 🔴

**Pain point**: In chemical engineering, fine pharmaceutical manufacturing and modern chemical plants, the continuous stirred-tank reactor (CSTR) is the core equipment for synthesizing drugs and chemical feedstocks. Controlling reaction yield precisely and preventing **thermal runaway** explosions means simulating the nonlinear multiphase chemical kinetics inside the reactor — solving extremely hardcore **stiff ordinary differential equation systems**, computing the Arrhenius reaction rate matrix and mass transfer balance for dozens of chemical components at various temperatures, pressures and stirring rates. Solving that class of highly stiff system in pure JS on the front end (where reaction rate constants differ by orders of magnitude) makes standard Runge-Kutta fail entirely; implicit methods (Gear or Radau5) then require solving a giant nonlinear Jacobian inverse at high frequency, and JS — lacking exact memory layout optimization — solves slowly and easily distorts results through lost floating-point precision.

**How it works**: The chemical industry's authoritative C++ stiff differential equation and thermodynamic equilibrium solving core is compiled to Wasm. **Chemical component thermodynamic memory**: every participating component's enthalpy, entropy, reaction rate constants and dynamic concentration matrix are laid out strictly as contiguous aligned `f64`, running implicit Euler and quasi-Newton iteration at high speed at the binary level. **A zero-GC stiff differential iterator**: the algebraic optimizer inside Wasm reassembles and solves the reaction system's sparse Jacobian dynamically at high speed in enclosed memory, creating no JS garbage objects on any time step.

**Performance**: Claimed that a 24-hour dynamic evolution and transient thermal runaway boundary prediction for an industrial CSTR with 32 chemical components, complex parallel competing reactions and non-isothermal heat balance constraints takes only **45–80 milliseconds** on the front end to produce exact concentration and temperature time series (solve precision to 10⁻⁸), more than **55× faster** than pure JS.

**Advantages**: Brings a static chemical digital twin tool industrial-grade chemical kinetics solving; pairs perfectly with HTML5 charts for live visualization of reactor temperature oscillation.
**Disadvantages**: Implicit solving of stiff systems depends heavily on the convergence of nonlinear iteration, and if the user inputs non-physical extreme negative concentrations or initial temperatures, catching the C++ exceptions inside Wasm requires heavy glue design.

**Competitors**: Pure-JS ODE libraries (whose compute and numerical stability are entirely inadequate for industrial control and digital twin scenarios when facing highly stiff chemical kinetic systems and high-frequency implicit solving of giant Jacobians).

---

## VII. Five Foundational Engines

> The five categories in this section (software engine, physics engine, world engine, LLM engine, graphics engine) are a new classification dimension the user specified themselves at entry 111 of the original conversation — **exactly the effective technique Chapter 6 mentions: constraining the search space works better than demanding recall.**

### 92. (originally 111) OpenLISP-Wasm [software engine] — A symbolic computation and functional LISP core 🟡

**Pain point**: In symbolic AI, expert systems and metaprogramming, LISP's **S-expressions** and homoiconicity ("code is data") are irreplaceable. Providing a secure symbolic computation playground or online rule compilation engine on the web by converting LISP code into JS objects directly triggers catastrophic GC freezes in JavaScript, because LISP creates cons cells, binds dynamic scopes and recurses in tail position extremely often.

**How it works**: An industrial C-language micro LISP core interpreter is compiled to Wasm. **A flat pointer memory pool**: LISP's environment binding tree and cons cells no longer live as discrete JS objects but are compressed into contiguous binary arrays in linear memory; Wasm maintains a very fast **self-built mark-and-sweep garbage collector** internally, bypassing the browser's JS heap scheduling entirely. **Tail call optimization support**: using Wasm's **`return_call` (tail calls, now in the Wasm 3.0 core specification)** instruction, LISP's deep recursion is turned at the binary level into flat register-level jumps, eliminating stack overflow.

**Performance**: Claimed that an algebraic theorem-proving script with 1,000,000 symbol substitutions and deep recursive matching takes only **35–55 milliseconds** on the front end, at **82%** of native C and more than **30× faster** than a pure-JS LISP interpreter.

**Advantages**: Brings a static online teaching and symbolic computation platform a zero-backend-cost secure execution environment; an enterprise's core business rule scripts stay entirely local.
**Disadvantages**: The LISP symbol tree is highly compact in Wasm memory, so serializing it to JSON often from front-end JS incurs cross-boundary overhead, requiring a shared `TypedArray` buffer optimization.

> 💡 **This is the only case in the whole book that uses Wasm's tail call instruction directly.** It also explains why Chapter 1's line — "without tail calls, deep recursion in functional languages will always blow the stack" — was a debt that had to be repaid.

**Competitors**: Pure-JS LISP emulation libraries (lacking efficient binary pointer manipulation and native tail call optimization, causing constant GC stutter and crashes on large symbol lists).

---

### 93. (originally 112) OpenVDB-Wasm [physics engine] — Sparse 3D volumetric fluid and smoke simulation 🟡

**Pain point**: In film visual effects and high-end industrial physical simulation, smoke, fire, liquids and the "surface tearing and dynamic collision" of complex 3D rigid bodies require storing and processing enormous 3D spatial grid data. The gold standard is DreamWorks' open-source **OpenVDB** (using the revolutionary hierarchical sparse B+ tree VDB-Tree). Simulating a giant 1024³ dynamic fluid volume with ordinary pure-JS 3D arrays costs gigabytes of memory and crashes with OOM outright during high-frequency level set curvature transforms and particle collision detection.

**How it works**: The OpenVDB volumetric physics engine core — hundreds of thousands of lines of accumulated C++ — is compiled to Wasm via Emscripten. **A highly compact sparse 3D spatial tree**: physical space is discretized into a 3D sparse topology tree, and Wasm maintains maximally optimized contiguous binary cache-friendly arrays internally, **storing only the nodes that contain fluid or smoke density**, pushing L1/L2 hit rates to the limit. **SIMD operator vectorization**: one instruction computes the Navier-Stokes pressure PDE for 4 or 8 volume grid points in parallel, advancing physics steps in parallel with threads inside the sandbox.

**Performance**: Claimed that simulating 500,000 highly sparse smoke volume particles diffusing and colliding with rigid body surfaces in a scene containing complex irregular 3D models takes no more than **8–12 milliseconds** per physics step, locking 60 FPS.

**Advantages**: Brings a static 3D effects dashboard install-free film-grade physical simulation; **it pairs perfectly with WebGPU shaders — the sparse volume matrix Wasm computes can be volume ray-cast on the GPU for live rendering.**
**Disadvantages**: OpenVDB's code volume is enormous, so the compiled Wasm is usually **4–6 MB**, a noticeable load burden on first entry.

**Competitors**: Pure-JS 3D physics libraries (suited only to small-scale, low-precision consumer effects and outclassed by industrial high-dimensional sparse 3D volume level set evolution and multi-body collision solving).

---

### 94. (originally 113) ProcPlanet-Wasm [world engine] — Infinite procedural virtual planet terrain generation 🔴

**Pain point**: In space simulation, digital twin Earths and very large sandbox games, generating a "1:1 scale virtual planet world" with exact landforms, river topology, vegetation distribution and atmospheric optical scattering in real time is extremely hardcore. The core is a **procedural world generation engine**, involving dense 64-bit high-order fractal noise (simplex noise, FBM), plate tectonic erosion algorithms and solving the nonlinear Rayleigh and Mie atmospheric light scattering equations. Computing millions of terrain mesh vertices dynamically in pure JS as the mouse moves causes severe terrain pop-in, for lack of cache-optimized multidimensional array addressing.

**How it works**: A high-precision procedural virtual world generation engine core written in Rust is compiled to Wasm. **A dynamic continuous level-of-detail octree**: the virtual planet is managed in linear memory as a flat octree structure, and as the camera moves closer or further the optimizer inside Wasm performs mesh splitting and simplification at high speed at the binary level. **SIMD operator vectorized fractals**: one CPU instruction computes the high-order noise oscillation function for 4 or 8 surface coordinates in parallel, with no JS garbage allocation anywhere.

**Performance**: Claimed that while the user flies supersonically over the virtual planet's surface, **up to 2,000,000** 3D terrain vertices with high-precision normals and erosion features can be generated dynamically per second, at **80%** of the native core, holding a full 60 FPS.

**Advantages**: Brings a static platform "cosmic-scale" infinite procedural world generation; **zero backend disk storage cost — the world is computed live from a seed and no terrain data is stored at all.**
**Disadvantages**: A procedural world engine involves complex thermodynamic atmospheric scattering integration, and on low-end devices with poor GPU support, Wasm's pure-CPU fallback for atmospheric diffuse reflection produces performance spikes.

**Competitors**: Pure-JS terrain generators (lacking low-level memory alignment and bit-operation optimization, with CPU peaks that are too high on large-scale fractal matrix computation and badly lagging terrain loading).

---

### 95. (originally 114) RWKV-Core-Wasm [LLM engine] — Ultra-low-memory inference for a linear attention large model 🟢

**Pain point**: Running large language model inference in the browser, the mainstream Transformer architecture faces a fatal bottleneck: **the KV cache grows linearly or quadratically with context length**, so the browser easily exceeds its memory ceiling and crashes on a conversation of tens of thousands of words. In response the open-source world produced the next-generation architecture **RWKV** (a Transformer based on a linear recurrent neural network), which compresses the KV cache into a **constant-size Time-Mix / Channel-Mix state vector**. But running RWKV's weight matrix multiplications smoothly on the front end is impossible in pure JS: facing billions of floating-point operations, token output slows to one character per second.

**How it works**: RWKV's official open-source C/Rust inference engine core is compiled to Wasm as the edge compute engine for a decentralized private LLM. **Flat weight matrix memory layout**: the model's quantized weights (INT4/INT8) are written directly into linear memory as a binary byte stream, and Wasm runs the linear attention matrix multiply-accumulate (GEMM) through fast pointer-driven table lookups. **SIMD operator vectorized dequantization**: one CPU instruction decompresses and converts 4 or 8 INT4 weights to floating point in parallel, while Web Workers distribute the model matrix in blocks across CPU cores for synchronized inference.

**Performance**: Claimed that with a 1.5B-parameter lightweight RWKV model loaded and SIMD and threads on, front-end token generation reaches **15–25 tokens per second**, at **75%** of the native core.

**Advantages**: Brings a static page edge AI inference with "unlimited context length and no memory explosion"; **all of the user's private conversations and confidential code stay 100% local**; zero backend GPU cost.
**Disadvantages**: Although RWKV is very memory-frugal, a 1.5B-parameter model file is still hundreds of megabytes compressed, so first entry means a long wait — **it is best configured as a PWA with local persistent caching** (exactly Chapter 7's OPFS use case).

**Competitors**: Pure-JS neural network libraries (lacking strict type optimization, efficient binary bit-shift parsing and register-level matrix arithmetic, freezing outright on large model inference).

---

### 96. (originally 115) Pagmo-Wasm [optimization engine] — Multi-objective global optimization and evolutionary computation 🟡

**Pain point**: In aerospace trajectory design (ESA's interplanetary probe path planning), logistics supply chain scheduling and advanced engineering structural design, engineers face **multi-objective global optimization** — solving hundreds of mutually conflicting extreme criteria at once while escaping vast numbers of local optima. The world's foremost nonlinear evolutionary computation core is ESA's open-source **pagmo** (based on a generalized island model). Running parallel population evolution for particle swarm optimization (PSO), differential evolution (DE) or NSGA-II in pure JS on the front end causes exponentially exploding memory and CPU peaks during high-frequency topological migration and mutation crossover, freezing the browser completely.

**How it works**: ESA's official open-source C++ multi-objective optimization engine pagmo is compiled to Wasm in full. **Heterogeneous island memory layout**: every optimization island's population gene matrix, fitness score table and constraint boundaries are laid out strictly as contiguous aligned `f64`, filtering the Pareto front at high speed at the binary level. **A multi-island heterogeneous parallel evolution state machine**: with Web Workers plus `SharedArrayBuffer`, a fast migration queue is built — **each Worker thread simulates an independently evolving ecological island, and the islands exchange genes periodically through binary pointers** — with no JS garbage allocation anywhere.

**Performance**: Claimed that a full global optimization evolution of an industrial extreme nonlinear function with 50 dimensions, 3 conflicting objectives and a population of 10,000 individuals takes only **450–700 milliseconds** on the front end to produce an exact Pareto optimal set, more than **40× faster** than pure JS.

**Advantages**: Brings a static industrial CAD/CAM workbench and research dashboard aerospace-grade multi-objective global optimization; pairs perfectly with HTML5 charts for live animation of the Pareto front's evolution.
**Disadvantages**: Evolutionary computation involves extensive random mutation, and if the objective function contains highly nonlinear singularities, catching the C++ exceptions inside Wasm requires heavy glue design.

**Competitors**: Pure-JS genetic algorithm libraries (orders of magnitude behind in compute and numerical stability on high-dimensional multi-objective optimization, large-scale heterogeneous island parallel evolution and high-frequency topological migration).

---

### 97. (originally 116) AMReX-Core-Wasm [software engine] — Adaptive mesh refinement (AMR) for giant PDE simulation 🟡

**Pain point**: In astrophysical explosion simulation, combustion fluid dynamics and climate prediction, when solving spatial PDEs some regions (a shock front, a flame core) change so violently that they need very high mesh resolution, while the remaining gentle regions need only a coarse mesh. The industrial gold standard is Lawrence Berkeley National Laboratory's open-source **AMReX** framework engine. Providing dynamic mesh splitting and reassembly on the web is impossible in pure JS, which produces constant memory fragmentation from pointer chasing and realignment across millions of multi-level nested grids, freezing the main thread permanently.

**How it works**: The AMReX software engine — hundreds of thousands of lines of accumulated C++ core — is compiled to Wasm via Emscripten. **A flat multi-level pointer memory pool**: the spatial topology and boundary conditions of the multi-level nested grids no longer live as discrete JS objects but are compressed into contiguous binary cache-friendly arrays; when a physical quantity's gradient exceeds a threshold, Wasm performs a binary pointer offset directly to split off a subgrid dynamically. **SIMD operator vectorized differencing**: one CPU instruction solves high-order finite difference fluxes for 4 or 8 grid points in parallel, bypassing the browser's JS heap allocation throughout.

**Performance**: Claimed that when simulating a nonlinear fluid flow field with shock oscillation, managing 5 nested grid levels dynamically and advancing high-precision PDE time steps takes only **180–290 milliseconds** per frame on the front end, at **80%** of native C++ and more than **35× faster** than pure JS.

**Advantages**: Brings a static teaching and research platform a national-laboratory-grade, zero-backend-cost giant algebra and mesh splitting engine; a researcher's sensitive core parameters stay entirely local.
**Disadvantages**: The data structures AMR produces are extremely low-level, so serializing them to JSON often from front-end JS incurs cross-boundary overhead; use a shared `TypedArray` buffer and render contour maps in hardware through WebGL.

**Competitors**: Pure-JS PDE libraries (lacking efficient binary pointer manipulation and compact memory alignment, with exponentially exploding memory and CPU peaks on dense adaptive dynamic mesh refinement).

---

### 98. (originally 117) ChronoEngine-Wasm [physics engine] — Multiphase granular flow and fluid-structure interaction (FSI) 🟡

**Pain point**: In mechanical engineering, off-road vehicle terrain dynamics and pharmaceutical mixing processes, you need to simulate the **fluid-structure interaction (FSI)** and nonlinear friction collisions between hundreds of thousands of discrete particles (sand, pills) and complex 3D mechanical rigid bodies. The gold standard is the open-source industrial multibody physics engine **Project Chrono**. Simulating a giant system of 100,000 sand particles colliding with a tracked vehicle in an ordinary pure-JS 3D rigid body library (Matter.js) explodes memory and collision detection complexity exponentially and crashes the tab with OOM.

**How it works**: The Chrono physics engine core — hundreds of thousands of lines of top-tier accumulated C++ — is compiled to Wasm via Emscripten. **A compressed sparse nonlinear constraint layout**: every discrete particle's mass, 3D coordinates and velocity, plus the friction contact constraints based on **DVI (differential variational inequalities)**, are laid out strictly as a contiguous binary structure-of-arrays in linear memory. **A SIMD vectorized cone programming solver**: one CPU instruction computes second-order cone programming (SOCP) convex optimization iterations for several particle contact surfaces in parallel, with the spatial partitioning of vast particle counts distributed through Web Workers plus `SharedArrayBuffer`.

**Performance**: Claimed that simulating **100,000 discrete flowing particles** colliding, stacking and solving nonlinear friction resistance against a robotic arm on irregular terrain in a 3D scene takes no more than **6–10 milliseconds** per physics step, locking 60 FPS.

**Advantages**: Provides mechanical and soil mechanics industrial-grade high-precision physical feedback, eliminating pure-JS physics engines' inability to handle "vast granular flow and multibody fluid-structure interaction"; the Wasm module is highly self-contained and needs no backend simulation server at all.
**Disadvantages**: Chrono involves extremely complex stiff differential equations and time integration solving, so an extreme non-physical impact force from the user must be prevented from crashing the Wasm VM.

**Competitors**: Ammo.js / Cannon.js (fine for lightweight 3D web game rigid body collisions, but entirely impractical for industrial FSI and nonlinear sliding friction solving past hundreds of thousands of dimensions with massive granular flows).

---

### 99. (originally 118) CivEvo-Core-Wasm [world engine] — Multi-agent geopolitics and climate economics simulation 🔴

**Pain point**: In climate change economics, macro historical dynamics (cliodynamics) and large strategy sandbox games, generating and deriving a "multi-level virtual world model" containing tens of thousands of virtual nations/factions, millions of autonomously deciding multi-agents, dynamic resource consumption and global climate feedback in real time is a technical feat. The core involves dense stochastic game matrix solving, nonlinear population dynamics (Malthusian models) and nonlinear Walrasian equilibrium iteration over giant supply-demand networks. Computing a million agents' economic transactions and resource games dynamically per time step in pure JS causes severe GC pauses from dynamic typing and constant object creation, tearing the world derivation's picture.

**How it works**: An industrial multi-agent world dynamics simulation core written in Rust or optimized C++ is compiled to Wasm. **A flat state space matrix**: every node in the virtual world, each faction's resource totals and each agent's decision weight matrix are laid out strictly as contiguous aligned `f64`, maximizing L1/L2 hit rates. **Multi-core island parallel gaming**: with Web Workers plus `SharedArrayBuffer`, Wasm allocates contiguous flat memory to build a fast market clearing graph, distributing different continents'/regions' agent decisions and resource evolution in parallel, with no JS garbage allocation anywhere.

**Performance**: Claimed that under the heavy load of a world map with 1,000 city factions and 1,000,000 independent agents, each world tick takes no more than **15–25 milliseconds**, at **82%** of the native core, sustaining very smooth live derivation.

**Advantages**: Brings a static platform "national-scale" global climate economics and geopolitical multi-level world simulation; **the world is computed live from a seed, eliminating the disk cost of vast backend save servers.**
**Disadvantages**: A world engine involves highly complex nonlinear multivariate feedback, and if one submarket's parameters go out of balance, the economic equations easily fail to converge, requiring a carefully built **adaptive damping state machine** inside Wasm.

**Competitors**: Pure-JS simulators (lacking low-level memory alignment and dense binary bit-shift parsing, with CPU peaks that are too high on large-scale multi-agent relationship graph lookups and algebraic iteration, and badly lagging world derivation).

---

### 100. (originally 119) DeepSpeed-MoE-Wasm [LLM engine] — Dynamic gated inference for the mixture-of-experts architecture 🟡

**Pain point**: For LLM inference at the edge, the latest gold standard architecture is **mixture of experts (MoE)** (Mixtral, for instance) — total parameters run to tens of billions, but each inference activates only a small subset of expert networks, saving compute. But MoE brings another fatal penalty for the front end: **the enormous model size (usually tens of gigabytes) cannot possibly fit in client memory.** And running MoE's dynamic gating network routing and weight dequantization multiplication smoothly on the front end is impossible in pure JS — facing billions of floating-point operations, token output freezes entirely.

**How it works**: An industrial large-model parallel optimization toolkit (Microsoft DeepSpeed's inference operator core, say) is compiled to Wasm as the edge solving engine for a decentralized private MoE model. **Dynamic sparse weight memory**: Wasm computes the gating network's top-K expert routing through fast pointer-driven table lookups; **only the currently activated experts' weights reside in linear memory, with OPFS performing binary block streaming swap between disk and memory**. **SIMD operator vectorized dequantization**: one CPU instruction decompresses and computes matrix multiply-accumulate for 4 or 8 INT4/INT8 weights in parallel, while Web Workers distribute the expert matrices across CPU cores.

**Performance**: Claimed that with a lightweight 8×7B MoE model that activates only 2 experts per inference loaded and SIMD and threads on, front-end token generation reaches **12–18 tokens per second**, at **75%** of the native core.

**Advantages**: Brings a static page edge AI inference with "a large model architecture and a small memory footprint"; the user's private conversations and sensitive code stay 100% local; zero backend GPU cost.
**Disadvantages**: Although weight streaming swap runs through OPFS, it **demands a lot of the local disk's random read speed (SSD performance)**, producing noticeable time-to-first-token (TTFT) latency on a traditional slow drive.

> 💡 **This is the case in the whole catalog that fuses Chapters 7 and 8 most thoroughly**: it uses both OPFS random reads (Chapter 7) and sliding-window streaming (Chapter 8's escape route one) to get around the 4 GB ceiling — **and its bottleneck lands ultimately on the user's SSD, which is the best possible footnote to the second half of the sentence "zero server cost": the cost did not vanish; it became someone else's hardware.**

**Competitors**: Pure-JS neural network libraries (lacking strict type optimization and register-level matrix arithmetic, freezing outright on MoE's complex gating network scheduling).

---

### 101. (originally 120) Mitsuba-Spectral-Wasm [graphics engine] — Multispectral radiometry and inverse ray tracing 🟡

**Pain point**: In aerospace remote sensing, coating optical design and advanced inverse rendering, an ordinary RGB three-channel rendering engine cannot meet physical accuracy requirements at all. Scientists need a **multispectral radiometric ray tracing engine** covering dozens of continuous wavelengths (380 nm–780 nm at 5 nm intervals), solving the rigorous geometric approximation of Maxwell's equations and bidirectional reflectance distribution functions (BRDF). The world's foremost research-grade core is the **Mitsuba** rendering engine (C++). Doing multispectral ray-grid intersection and surface polarization state matrix iteration with ordinary pure-JS vectors produces severe CPU peaks on high-dimensional spectral integration and freezes the page.

**How it works**: The multispectral optical solver of the Mitsuba rendering engine core is compiled to Wasm in full. **High-dimensional spectral flat memory layout**: every ray's per-band energy signature, surface geometry vertices and material complex refractive index matrices are laid out strictly as contiguous aligned `f64`, running Monte Carlo path tracing integration at high speed at the binary level. **A SIMD vectorized wavelength integration state machine**: one CPU instruction computes photon energy attenuation and Fresnel equation reflectance for 4 or 8 different wavelengths in parallel, with multi-core CPUs scanning in parallel at the binary level and no JS garbage allocation anywhere.

**Performance**: Claimed that full multispectral path tracing and inverse geometric optimization of a 3D optical scene with complex multilayer thin film interference materials takes only **400–650 milliseconds** on the front end to render one frame at aerospace optical precision, more than **45× faster** than pure JS.

**Advantages**: Brings a static aerospace remote sensing and optical design dashboard a research-laboratory-grade multispectral graphics engine; zero backend cost, keeping core optical formulation data safely parsed on the local machine.
**Disadvantages**: Multispectral rendering involves extensive random wavelength sampling, and if the material geometry boundaries are extremely complex, catching the C++ exceptions inside Wasm requires heavy glue design.

**Competitors**: Three.js (fine for commercial 3D web display, but orders of magnitude behind on hardcore physical multispectral photon energy evolution, complex refractive index polarization matrix solving and high-precision optical wavelength integration).

---

## Catalog Conclusion: Five Things 101 Cases Tell Us

**One: Wasm has successfully broken the physical wall between the browser and advanced low-level system computation.** From case 1's web media transcoding to case 101's aerospace-grade multispectral ray tracing, it has turned hardcore technologies — zero-knowledge privacy proofs, quantum state simulation, P2P network multiplexing, industrial power flow iteration, big-data multidimensional aggregation — into entirely free, decentralized, end-to-end private static web assets.

**Two: the underlying technical essence of all 101 cases is remarkably consistent.** A cache-friendly flat memory layout plus SIMD vectorization outclasses JavaScript's flexible but fragmented object allocation. **Those five architectures (flat memory zero-copy, Worker isolation, SIMD, streaming chunking, AudioWorklet isolation) are fully dissected in Chapter 6.**

**Three: four motivations determine the return on investment.** Shifting compute cost (nearly every entry), data sovereignty (about 70%), capability gap (about 30%) and asset revival (about 20%). **The more of them you hit, the higher Wasm's return; if you hit none, don't use Wasm.**

**Four: every case runs into the same few walls.** The 4 GB linear memory ceiling (case 22's dictionary, 52's zk-EVM, 53's 24 qubits, 74's holographic reconstruction, 81's mesh resolution), module size (case 7's 30–50 MB, 13's 10–15 MB, 28's 10–15 MB), and `SharedArrayBuffer` with cross-origin isolation (cases 1, 32, 62, 68, 75, 81 and every other multithreaded entry). **Those walls are fully dissected in Chapters 3, 5 and 8 — they are not implementation defects but direct corollaries of the specification.**

**Five, and most important: a substantial portion of these 101 entries is illustrative.** That does not weaken their value; it explains this catalog's real use — **it is a feasibility map of "is this road passable," not a list you can `git clone`.** Nearly every 🔴 entry's technical path holds up; it is simply that nobody has built it, or someone has and it goes by another name (case 66 versus DuckDB-Wasm and case 70 versus OpenCV.js are the best examples).

> **If you take one sentence away from this catalog, take this one**:
> **Wasm made "driving an entire field's barrier to entry to zero" something one person can do — what you need is not resources, but knowing which road is already open.**

---

**One last signpost**: this catalog is a map of "is this road passable," **and Appendix L is the place at the end of the road where someone actually lives** — FluffOS compiles an entire LPMud driver into the browser, and `fluffos/mudlibs` repairs two hundred 1990s Chinese MUD sources and packages them as static bundles. It is simultaneously the real version of this part's two 🔴 concepts (case 58 Minestom-Wasm and case 60 Micro-Apache-Wasm), and the cleanest living specimen of the book's central thesis. **If you want to see only one case taken all the way down, read that one.**
