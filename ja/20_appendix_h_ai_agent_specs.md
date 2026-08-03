# 付録H：AI コーディングエージェント向けの仕様書テンプレート

> Claude Code のような、端末に直接組み込まれ自律的にプロジェクトをリファクタリングできる AI ツールを使うとき、最も核心的な技法は**「明快なシステムアーキテクチャの境界、明示的な依存条件を与え、防御的な設計を要求すること」**である。
> この種のエージェントはあなたのファイルを直接読み書きし、テストとコンパイルを実行できるので、あなたのプロンプトは一言の願いではなく、**高水準のシステムアーキテクチャ仕様書**のようでなければならない。
>
> この付録はそのままコピーして使える三つのテンプレートを提供する：**（一）汎用のストレージ機構の仕様書、（二）三種類のストレージ機構それぞれの調整指示、（三）終局の四層アーキテクチャの完全な初期化の指示。**

---

## 1. 汎用の仕様書：Wasm のデータストレージ機構

> 以下の構造化されたプロンプトをそのままコピーし、`[角括弧]` 内の選択肢を置き換えること。

```markdown
I want you to implement a high-performance, non-volatile data storage mechanism
for our Rust WebAssembly application using [一つ選ぶ：OPFS / IndexedDB (IDBFS) / WASI File System].

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

## 2. 三種類のストレージ機構それぞれの調整指示

上のプロンプトへ、対応する以下の段落を**追記**する。

### （一）OPFS + Web Worker —— 極限の性能。50 MB を超える大きなファイル／データベースに向く

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

### （二）IndexedDB / IDBFS —— 高い互換性。ゲームのセーブ／小さな JSON に向く

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

### （三）バックエンドの WASI —— クラウドネイティブのサーバサイド

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

## 3. 終局アーキテクチャの初期化指示（第 12 章の四層トポロジー）

> これは「保守不要、サーバコストゼロ、極限の性能」の専用 Wasm アプリケーションの骨格を**ゼロから構築する**ために使う。

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

## 4. AI エージェントと協働する仕事のリズム

**第一歩：分析と計画**
エージェントはまず、どのファイルを修正するつもりかを返してくる（`Cargo.toml`、`src/lib.rs` など）。**この時点で闇雲にコードを書かせないこと。まずアーキテクチャをよく見ること。** その層の切り方があなたの予想と違うなら、いま直すのが最も安い。

**第二歩：コンパイルとビルドを認可する**
コードを書き終えたあと、エージェントはたいてい `wasm-pack build --target web` を実行して検証してよいかを尋ねる。**同意すること。**

> **経験談**：Wasm の境界越え（JS-bind）のコンパイルは、`web-sys` の feature を有効にしていないだけで極端に長いエラーを吐きやすい。エージェント自身に端末でコンパイルさせれば、コンパイラのログに応じて通るまで自力で直せる——**これは大量のドキュメントを引く時間を節約する。**

**第三歩：鍵となる指標の確認を求める**
コンパイルが成功したら、一言追加する。

```
Confirm that you used the zero-copy `view` method instead of copying into a new
Uint8Array. Show me the file and line number, and explain the SAFETY invariant
you are relying on.
```

**これで手抜きのコピーの方法を使っていないことを保証でき**、Wasm の最も純粋な読み書きの性能を引き出せる。

**第四歩：セキュリティの赤線の検査（省略不可）**

```
Run: strings pkg/*.wasm | grep -Ei 'sk-|AKIA|BEGIN.*PRIVATE|password|secret|token'
Report the exact output. If anything matches, stop and tell me where it came from.
```

---

## 5. AI エージェント向けの仕様書：五つの一般則

> この五つは Wasm と無関係であり、コーディングエージェントへ渡すあらゆるタスクに当てはまる。

1. **先に境界を、次にタスクを与えよ。** 「npm パッケージを一切使ってはならない」「標準の Web API しか使ってはならない」「この層にアルゴリズムを含めてはならない」——**制約は目標よりも産出の品質を決める。** モデルはつねに、あなたが望まない近道を見つけられるからだ。

2. **先に計画を述べさせ、それから手を動かさせよ。** アーキテクチャが誤っていれば、どれだけ速く書いても負債である。**この一歩のコストは一往復の対話であり、見返りはプロジェクト全体の方向である。**

3. **自分で検証できるループを与えよ。** 「ビルドを走らせる」「テストを走らせる」「ベンチマークを走らせて数字を報告する」——**自分で検証できるエージェントは、コードを書けるだけのエージェントより品質がはるかに高い。**

4. **スキーマを制約の道具として使え。** 片側を修正させるとき、**スキーマは彼が自由に振る舞えない唯一の場所である**（第 12 章）。これは AI の産出の漂流を制御する最も有効な手段である。

5. **「変わらないもの」と「捨ててよいもの」を分けて伝えよ。** 「この層は十年不動を設計目標とする」「この層は三年ごとに書き直してよい」と明示すること——**エージェントはその指示に沿って抽象の度合いと依存の選択を調整する**。そしてそれこそが保守エントロピーの増大に対抗する鍵である（第 12 章）。
