# Appendix H: Specification Templates for AI Coding Agents

> When using an AI tool like Claude Code — embedded directly in the terminal and capable of autonomous project refactoring — the core technique is **giving clear system architecture boundaries, explicit dependency conditions, and a demand for defensive design**.
> Because that kind of agent can read and write your files, run tests and compile, your prompt must read like a **high-level system architecture specification**, not a wish.
>
> This appendix provides three templates you can copy and use directly: **(1) a general storage mechanism specification, (2) tuning directives for each of the three storage mechanisms, and (3) a complete initialization directive for the endgame four-layer architecture.**

---

## 1. General specification: a Wasm data storage mechanism

> Copy the structured prompt below and replace the options inside `[brackets]`.

```markdown
I want you to implement a high-performance, non-volatile data storage mechanism
for our Rust WebAssembly application using [pick one: OPFS / IndexedDB (IDBFS) / WASI File System].

Please follow these specifications strictly:

### 1. Architecture & Scope
- **Domain**: WebAssembly Client-Side Storage Engine.
- **Language Stack**: Rust, `wasm-bindgen`, `web-sys`, and `js-sys`.
- **Target Mode**: Browser context (`--target web`), [single-threaded / multi-threaded].
- **Core Requirement**: Map our internal Rust binary structure/buffer into
  persistent host storage with ZERO-COPY memory optimization.

### 2. Implementation Checklist
1. **Dependency Injection**
   - Check and update `Cargo.toml`. Add the necessary `web-sys` feature flags
     (e.g. `FileSystemDirectoryHandle`, `FileSystemFileHandle`,
     `FileSystemWritableFileStream`, `StorageManager`) depending on the chosen engine.
   - Set the release profile: `opt-level = 3`, `lto = true`, `codegen-units = 1`,
     `panic = "abort"`, `strip = true`.

2. **Rust Core Layer (`src/storage.rs`)**
   - Implement a struct named `WasmStorageEngine`.
   - Implement `async fn save_data(&self, key: &str, data: &[u8]) -> Result<(), JsValue>`.
   - Implement `async fn load_data(&self, key: &str) -> Result<Vec<u8>, JsValue>`.
   - Use `unsafe { js_sys::Uint8Array::view(data) }` or a `WritableStream` to prevent
     double-buffering and achieve zero-copy during transfer.
   - **Document the SAFETY invariant**: the view is invalidated by any `memory.grow`;
     no allocation may occur while the view is alive.

3. **Memory Safety & Defenses**
   - Handle JavaScript exceptions (`JsValue`) gracefully using Rust's `Result` type.
     Never `unwrap()` on a `JsValue` boundary.
   - Implement a safe allocation fallback check to prevent out-of-bounds crashes
     if the incoming byte buffer size approaches the browser's per-instance
     memory allocation limit.
   - Explicitly handle quota errors (`QuotaExceededError`) and surface them as a
     typed Rust error, not a generic failure.

4. **JS Glue Integration & Demo**
   - Create or update `index.html` demonstrating initialization, saving, and
     cross-session loading of this storage engine.
   - Measure and display the raw disk write latency using `performance.now()`.
   - Use RELATIVE paths only (`./pkg/...`), because this will be deployed to
     GitHub Pages under a project subpath.

### 3. Execution Constraints
- DO NOT use any heavy third-party JavaScript npm packages; rely completely on native Web APIs.
- Write unit tests or a mock integration script if applicable, and run
  `wasm-pack build --target web` to verify the compilation succeeds with zero warnings.
- Keep the code modular. Separate storage logic from UI rendering logic.
- Add a `.nojekyll` file to the output directory.

Review the workspace files first, tell me which files you plan to modify,
then build the project and report the benchmarks.
```

---

## 2. Tuning directives for each of the three storage mechanisms

**Append** the matching section below to the prompt above.

### (1) OPFS + Web Worker — maximum performance, for large files/databases over 50 MB

```markdown
Since we are targeting heavy multi-threaded datasets, force the WasmStorageEngine
to run inside a Web Worker context and utilize the synchronous
`createSyncAccessHandle` / `FileSystemSyncAccessHandle` APIs instead of the
asynchronous writable stream. This eliminates the async poll loop overhead and
ensures raw native-speed sequential and random disk performance.

Additionally:
- Implement a sliding-window chunked reader so we never load the whole file into
  linear memory. Align window boundaries to 4MB.
- Use Transferable Objects (`postMessage(buffer, [buffer])`) for all large payloads
  crossing the main-thread/worker boundary.
- Always call `handle.close()` in a Drop impl or an explicit teardown path;
  a leaked sync access handle holds an exclusive lock on the file.
- Coordinate multi-tab access using the Web Locks API.
```

### (2) IndexedDB / IDBFS — broad compatibility, for game saves and small JSON

```markdown
Implement the solution using the Emscripten IDBFS / IndexedDB bridge.
The Rust layer must interact with an in-memory virtual file system (MEMFS).
After performing standard file mutations, automatically inject a JS wrapper that
executes `FS.syncfs(false, callback)` to flush the binary blocks into the browser's
IndexedDB store, ensuring cross-session persistence.

Be explicit about the cost model in comments:
- `syncfs` serializes the ENTIRE mount point, not a delta.
- Therefore this design is only appropriate for payloads under a few megabytes.
- Document the load path (`FS.syncfs(true, ...)` on startup) as well.
```

### (3) Server-side WASI — cloud-native

```markdown
We are deploying this on a server-side WebAssembly runtime (Wasmtime / WasmEdge)
instead of a browser. Change the target triple to `wasm32-wasip1`
(and note what would change for `wasm32-wasip2` / the Component Model).

Utilize the native Rust `std::fs::File` and standard library I/O.
Implement a capability-based security boundary check to verify that any path
resolution does not escape the pre-opened directory map provided by the WASI host.

Also produce the exact host invocation line, e.g.:
    wasmtime run --dir=./data::/sandbox app.wasm
and document which capabilities the module requires — this list IS the security
audit surface.
```

---

## 3. Endgame architecture initialization directive (Chapter 12's four-layer topology)

> Use this to **build from scratch** the skeleton of a "maintenance-free, zero-server-cost, maximum-performance" bespoke Wasm application.

```markdown
Initialize a next-generation, high-performance, single-page application workspace
based on a hybrid Wasm architecture. Your goal is to build an un-clonable,
low-maintenance file-processing engine.

Please execute the following technical plan autonomously:

1. **Workspace Setup**
   - Initialize a Rust library workspace. Configure `Cargo.toml` with
     `crate-type = ["cdylib"]`.
   - Turn on the maximum aggressive release profile: `opt-level = 3`, `lto = true`,
     `codegen-units = 1`, `panic = "abort"`, `strip = true` — strip all debug symbols
     and let LTO scramble the code structure.
   - Inject dependencies for `wasm-bindgen`, `js-sys`, and `web-sys` with features
     enabled for `FileSystemDirectoryHandle`, `FileSystemSyncAccessHandle`, and `Crypto`.

2. **Core Implementation (`src/lib.rs`)**
   - Create a struct named `CoreComputeEngine`.
   - Implement an automated sliding-window memory management pattern: read data
     chunks from host disk, perform high-speed binary manipulation inside Wasm
     linear memory WITHOUT generating intermediate high-level JS garbage objects,
     and flush state back.
   - Ensure all inter-op boundary parameters use zero-copy
     `js_sys::Uint8Array::view` mechanisms, and document the SAFETY invariants.
   - ARCHITECTURAL RULE: this layer must NOT depend on any JavaScript framework.
     Only standard binary Web APIs (Canvas 2D / WebGL, OPFS) are allowed.
     This layer is designed to remain unchanged for a decade.

3. **Web Worker Thread Isolation**
   - Generate a dedicated `worker.js` to host the compiled `.wasm`.
   - Use the synchronous OPFS API (`createSyncAccessHandle`) inside the worker to
     enable block-based sequential and random file read/writes.
   - Set up the main-thread message bus using Transferable Objects
     (`postMessage(buffer, [buffer])`) for microsecond-level pointer transfer.

4. **Data Protocol**
   - Do NOT use JSON across the Wasm boundary. Define all cross-boundary messages
     with a schema (Protocol Buffers or FlatBuffers). Generate the schema file first,
     then the bindings.
   - Rationale: the schema is the ONE thing that must stay stable while everything
     around it is rewritten.

5. **Verification & Benchmark**
   - Create an `index.html` with a benchmark dashboard measuring raw
     memory-to-disk write throughput using `performance.now()`.
   - Use relative paths only; add `.nojekyll`; the target is GitHub Pages.
   - Execute `wasm-pack build --target web` and ensure compilation succeeds
     with zero warnings.
   - Run `wasm-opt -Oz --strip-debug` on the output and report the size delta.
   - Run `strings pkg/*.wasm | grep -Ei 'sk-|AKIA|password|secret'` and confirm
     the output is EMPTY.

Analyze the current system state, draft the modules, compile the binary,
and report the micro-benchmark results.
```

---

## 4. The working rhythm of collaborating with an AI agent

**Step one: analysis and planning**
The agent will first reply with which files it intends to modify (`Cargo.toml`, `src/lib.rs` and so on). **Do not let it start writing code blindly at this point — look carefully at its architecture.** If its layering differs from what you expected, changing it now is the cheapest it will ever be.

**Step two: authorize compilation and building**
Once the code is written, the agent will usually ask whether it may run `wasm-pack build --target web` to verify. **Say yes.**

> **From experience**: Wasm's cross-boundary (JS-bind) compilation very easily emits enormously long errors because a `web-sys` feature wasn't enabled. Let the agent compile in the terminal itself and it will repair its way to a clean build from the compiler log — **which saves an enormous amount of documentation searching.**

**Step three: ask it to review the key metric**
After a successful build, add one line:

```
Confirm that you used the zero-copy `view` method instead of copying into a new
Uint8Array. Show me the file and line number, and explain the SAFETY invariant
you are relying on.
```

**That ensures it didn't take the lazy copying route**, and forces out Wasm's purest read/write performance.

**Step four: the security red line check (not optional)**

```
Run: strings pkg/*.wasm | grep -Ei 'sk-|AKIA|BEGIN.*PRIVATE|password|secret|token'
Report the exact output. If anything matches, stop and tell me where it came from.
```

---

## 5. Writing specifications for AI agents: five general rules

> These five have nothing to do with Wasm; they apply to every task you hand a coding agent.

1. **Give the boundaries before the task.** "No npm packages at all," "standard Web APIs only," "this layer must contain no algorithm" — **constraints determine output quality more than goals do**, because the model can always find a shortcut you didn't want.

2. **Make it state the plan before it acts.** If the architecture is wrong, writing fast only accumulates debt. **This step costs one exchange and returns the whole project's direction.**

3. **Give it a loop it can verify itself.** "Run the build," "run the tests," "run the benchmark and report the numbers" — **an agent that can verify itself produces far higher quality than one that can only write code.**

4. **Use the schema as your constraint tool.** When you ask it to modify one side, **the schema is the one place it cannot improvise** (Chapter 12). It is the most effective means of controlling drift in AI output.

5. **Tell it explicitly which parts are permanent and which are disposable.** Say "this layer is designed to be unchanged for a decade" and "this layer may be rewritten every three years" — **the agent will adjust its abstraction level and dependency choices accordingly**, and that is exactly what fights maintenance entropy (Chapter 12).
