# 附錄H　給 AI 編碼代理人的規格書範本

> 使用 Claude Code 這類直接內嵌於終端機、具備自主專案重構能力的 AI 工具時，最核心的技巧是**「給予清晰的系統架構邊界、明確的依賴條件，並要求防禦性設計」**。
> 因為這類代理人可以直接讀寫你的檔案、執行測試與編譯，你的 Prompt 必須像一份**高階系統架構規格書**，而不是一句願望。
>
> 本附錄提供三份可直接複製使用的範本：**（一）通用儲存機制規格書、（二）三種儲存機制的專屬調校指令、（三）終局四層架構的完整初始化指令。**

---

## 一、通用規格書：Wasm 資料儲存機制

> 直接複製以下結構化 Prompt，並替換 `[括號]` 內的選項。

```markdown
I want you to implement a high-performance, non-volatile data storage mechanism
for our Rust WebAssembly application using [選擇一個：OPFS / IndexedDB (IDBFS) / WASI File System].

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

## 二、三種儲存機制的專屬調校指令

在上面的 Prompt 中**追加**以下對應段落。

### （一）OPFS + Web Worker —— 極致效能，適合 >50MB 大型檔案 / 資料庫

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

### （二）IndexedDB / IDBFS —— 高相容性，適合遊戲存檔 / 小型 JSON

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

### （三）後端 WASI —— 雲原生伺服器端

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

## 三、終局架構初始化指令（第 12 章的四層拓撲）

> 這一份用於**從零建立**一個「免維護、零伺服器成本、極致效能」的專屬 Wasm 應用骨架。

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

## 四、與 AI 代理人協作的工作節奏

**第一步：分析與規劃**
代理人會先回覆它預計修改哪些檔案（`Cargo.toml`、`src/lib.rs` 等）。**此時先不要讓它盲目寫程式碼，看清楚它的架構。** 如果它的分層與你的預期不同，現在改最便宜。

**第二步：授權編譯與建構**
寫完程式碼後，代理人通常會問是否可以執行 `wasm-pack build --target web` 來驗證。**同意它。**

> **經驗談**：Wasm 的跨邊界（JS-bind）編譯很容易因為 `web-sys` 的 feature 沒開而噴出極長的錯誤。讓代理人自己在終端機編譯，它能根據編譯器日誌自行修復到過關為止——**這能省下大量查文件的時間。**

**第三步：要求檢視關鍵指標**
編譯成功後追加一句：

```
Confirm that you used the zero-copy `view` method instead of copying into a new
Uint8Array. Show me the file and line number, and explain the SAFETY invariant
you are relying on.
```

**這可以確保它沒有用偷懶的複製法**，逼出 Wasm 最純粹的讀寫效能。

**第四步：安全紅線檢查（不可省略）**

```
Run: strings pkg/*.wasm | grep -Ei 'sk-|AKIA|BEGIN.*PRIVATE|password|secret|token'
Report the exact output. If anything matches, stop and tell me where it came from.
```

---

## 五、寫給 AI 代理人的規格書：五條通則

> 這五條與 Wasm 無關，適用於所有交給編碼代理人的任務。

1. **先給邊界，再給任務。** 「不准用任何 npm 套件」「只能用標準 Web API」「這一層不准包含演算法」——**約束比目標更能決定產出的品質**，因為模型永遠能找到一條你不想要的捷徑。

2. **要求它先講計畫，再動手。** 架構錯了，寫得再快都是負債。**這一步的成本是一次對話，回報是整個專案的方向。**

3. **給它一個可以自己驗證的迴圈。** 「跑編譯」「跑測試」「跑 benchmark 並回報數字」——**能自己驗證的代理人，品質遠高於只能寫程式碼的代理人。**

4. **用 schema 當約束工具。** 當你叫它修改某一側時，**schema 是它唯一不能自由發揮的地方**（第 12 章）。這是控制 AI 產出漂移最有效的手段。

5. **把「不變的」與「可拋棄的」分開告訴它。** 明確說「這一層設計目標是十年不動」「這一層允許每三年重寫」——**代理人會照著這個指示調整它的抽象程度與依賴選擇**，而這正是對抗維護熵增的關鍵（第 12 章）。
