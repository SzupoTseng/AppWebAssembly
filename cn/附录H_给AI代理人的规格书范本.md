# 附录H　给 AI 编码代理人的规格书范本

> 使用 Claude Code 这类直接内嵌于终端机、具备自主项目重构能力的 AI 工具时，最内核的技巧是**「给予清晰的系统架构边界、明确的依赖条件，并要求防御性设计」**。
> 因为这类代理人可以直接读写你的文件、运行测试与编译，你的 Prompt 必须像一份**高级系统架构规格书**，而不是一句愿望。
>
> 本附录提供三份可直接拷贝使用的范本：**（一）通用保存机制规格书、（二）三种保存机制的专属调校指令、（三）终局四层架构的完整初始化指令。**

---

## 一、通用规格书：Wasm 数据保存机制

> 直接拷贝以下结构化 Prompt，并替换 `[括号]` 内的选项。

```markdown
I want you to implement a high-performance, non-volatile data storage mechanism
for our Rust WebAssembly application using [选择一个：OPFS / IndexedDB (IDBFS) / WASI File System].

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

## 二、三种保存机制的专属调校指令

在上面的 Prompt 中**追加**以下对应段落。

### （一）OPFS + Web Worker —— 极致性能，适合 >50MB 大型文件 / 数据库

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

### （二）IndexedDB / IDBFS —— 高兼容性，适合游戏存盘 / 小型 JSON

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

### （三）后端 WASI —— 云原生服务器端

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

## 三、终局架构初始化指令（第 12 章的四层拓扑）

> 这一份用于**从零创建**一个「免维护、零服务器成本、极致性能」的专属 Wasm 应用骨架。

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

## 四、与 AI 代理人协作的工作节奏

**第一步：分析与规划**
代理人会先回复它预计修改哪些文件（`Cargo.toml`、`src/lib.rs` 等）。**此时先不要让它盲目写代码，看清楚它的架构。** 如果它的分层与你的预期不同，现在改最便宜。

**第二步：授权编译与建构**
写完代码后，代理人通常会问是否可以运行 `wasm-pack build --target web` 来验证。**同意它。**

> **经验谈**：Wasm 的跨边界（JS-bind）编译很容易因为 `web-sys` 的 feature 没开而喷出极长的错误。让代理人自己在终端机编译，它能根据编译器日志自行修复到过关为止——**这能省下大量查文档的时间。**

**第三步：要求查看关键指针**
编译成功后追加一句：

```
Confirm that you used the zero-copy `view` method instead of copying into a new
Uint8Array. Show me the file and line number, and explain the SAFETY invariant
you are relying on.
```

**这可以确保它没有用偷懒的拷贝法**，逼出 Wasm 最纯粹的读写性能。

**第四步：安全红线检查（不可省略）**

```
Run: strings pkg/*.wasm | grep -Ei 'sk-|AKIA|BEGIN.*PRIVATE|password|secret|token'
Report the exact output. If anything matches, stop and tell me where it came from.
```

---

## 五、写给 AI 代理人的规格书：五条通则

> 这五条与 Wasm 无关，适用于所有交给编码代理人的任务。

1. **先给边界，再给任务。** 「不准用任何 npm 套件」「只能用标准 Web API」「这一层不准包含算法」——**约束比目标更能决定产出的品质**，因为模型永远能找到一条你不想要的捷径。

2. **要求它先讲计划，再动手。** 架构错了，写得再快都是负债。**这一步的成本是一次对话，回报是整个项目的方向。**

3. **给它一个可以自己验证的循环。** 「跑编译」「跑测试」「跑 benchmark 并回报数字」——**能自己验证的代理人，品质远高于只能写代码的代理人。**

4. **用 schema 当约束工具。** 当你叫它修改某一侧时，**schema 是它唯一不能自由发挥的地方**（第 12 章）。这是控制 AI 产出漂移最有效的手段。

5. **把「不变的」与「可抛弃的」分开告诉它。** 明确说「这一层设计目标是十年不动」「这一层允许每三年重写」——**代理人会照着这个指示调整它的抽象程度与依赖选择**，而这正是对抗维护熵增的关键（第 12 章）。
