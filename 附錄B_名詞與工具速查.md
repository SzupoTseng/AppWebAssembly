# 附錄B　名詞與工具速查

> 這是一份**查閱表**，不是教材。每一列的最後一欄標明它在書裡的出處——**看到不懂的名詞先查這裡，需要理解為什麼再翻過去。**

## 一、核心概念名詞

| 名詞 | 一句話解釋 | 在本書哪裡 |
|---|---|---|
| **WebAssembly (Wasm)** | 一台規格定義出來的抽象堆疊機器的二進位指令格式；不是任何實體 CPU 的機器碼 | 第 2 章 |
| **WAT (WebAssembly Text)** | Wasm 的可讀文字格式，與二進位一一對應（`wasm2wat` 可無損轉換） | 第 2、9 章 |
| **線性記憶體 (Linear Memory)** | 一整塊連續、可定址的位元組陣列；1 頁 = 64 KiB，只能增長不能縮小 | 第 2、8 章 |
| **Trap** | 執行期的不可捕捉錯誤（越界、除以零、unreachable），在 JS 側表現為 `RuntimeError` | 附錄 A |
| **保護頁 (Guard Page)** | 引擎保留 8GiB 虛擬位址空間，用 MMU 免費完成界檢查的技巧 | 第 2、8 章 |
| **結構化控制流** | Wasm 沒有 `goto`，只有 `block`/`loop`/`if` 與往外跳的 `br`——這是單趟驗證的前提 | 第 2 章 |
| **驗證器 (Validator)** | 載入時做 O(n) 單趟檢查：堆疊型別一致、控制流結構化、索引在界內 | 第 2 章 |
| **分層編譯 (Tiering)** | Liftoff（快速產碼）→ TurboFan（優化產碼）的雙軌賽跑 | 第 2 章 |
| **串流編譯 (Streaming Compilation)** | `instantiateStreaming`：第一個位元組到達就開始編譯 | 第 2、5 章 |
| **膠水程式碼 (Glue Code)** | JS 側負責型別轉換、記憶體管理、API 橋接的那一層 | 第 2 章 |
| **零拷貝 (Zero-copy)** | 用 `TypedArray` 在同一塊 `ArrayBuffer` 上開視圖，而不搬資料 | 第 2、6 章 |
| **SoA (Structure of Arrays)** | 把 `[{x,y,z}...]` 改成三條連續陣列——快取友善佈局 | 第 6 章 |
| **CSR / CSC** | 壓縮稀疏列/行格式，稀疏矩陣的標準緊湊表示 | 附錄 E、F |
| **跨來源隔離 (Cross-Origin Isolation)** | COOP + COEP 同時滿足時的頁面狀態，`SharedArrayBuffer` 的前提 | 第 3、5 章 |
| **能力式安全 (Capability-based Security)** | 模組預設兩手空空，能力必須由宿主顯式遞入 | 第 1、7 章 |
| **Component Model / WIT** | Wasm 模組之間用高階型別溝通的介面模型與描述語言 | 第 7 章、附錄 A |
| **LEB128** | 變長整數編碼；Wasm 所有長度與索引都用它 | 附錄 M §1 |
| **多型堆疊 (Polymorphic Stack)** | `unreachable` 之後的死程式碼如何通過驗證的機制 | 附錄 M §2 |
| **Table / `call_indirect`** | Wasm 沒有函數指標，函數指標其實是「表索引」 | 附錄 M §3 |
| **Tag / `exnref`** | Wasm 3.0 例外處理的標籤與不透明例外參考 | 附錄 M §4 |
| **JSPI** | JavaScript Promise Integration：引擎在堆疊層面掛起/恢復 Wasm，讓同步程式碼能等 Promise | 第 3 章牆七、附錄 M §5 |
| **Asyncify** | JSPI 之前的替代方案：Binaryen 改寫整個模組來模擬掛起（貴） | 附錄 M §5 |
| **Relaxed SIMD** | 放棄確定性換硬體映射；**需要確定性的場景必須禁用** | 附錄 M §7 |
| **Multiple memories** | Wasm 3.0：一個模組多塊線性記憶體，各自仍是 wasm32 | 第 8 章情境 4、附錄 M §8 |
| **proxy-wasm** | Envoy/Istio 等代理採用的 Wasm 外掛 ABI | 附錄 M §11 |

---

## 二、儲存相關

| 名詞 | 解釋 | 適用 |
|---|---|---|
| **MEMFS** | Emscripten 在線性記憶體裡假造的 POSIX 檔案系統 | 暫存中間檔（**吃 4GB 額度**） |
| **IDBFS** | 把 MEMFS 整包同步進 IndexedDB（`FS.syncfs`） | 遊戲存檔、設定（幾百 KB） |
| **WASMFS** | Emscripten 新一代檔案系統後端，可直通 OPFS | 取代 MEMFS/IDBFS 的方向 |
| **OPFS** | Origin Private File System，瀏覽器為每個來源開的私有磁碟空間 | **一切需要持久化的東西** |
| **`opfs` VFS**（SQLite） | 第一代 OPFS 後端，靠非同步代理 + `Atomics.wait`；**需要 `SharedArrayBuffer`／跨來源隔離** | 需要多連線時 |
| **`opfs-sahpool` VFS** | 同步控制代碼池；**不需要 COOP/COEP，且官方文件列為最快**；不支援多連線 | **靜態託管的首選** |
| **`createSyncAccessHandle()`** | OPFS 的同步隨機存取控制代碼（**只能在 Worker 裡用**） | 資料庫、大檔案串流 |
| **`navigator.storage.persist()`** | 請求把資料標記為 persistent，避免磁碟壓力下被驅逐 | 重要資料 |
| **VFS (Virtual File System)** | SQLite 為移植性設計的儲存抽象層；OPFS VFS 就是它的一個實作 | 第 7 章 |

---

## 三、工具鏈

### 編譯器 / 工具鏈前端

| 工具 | 語言 | 特性 |
|---|---|---|
| **Emscripten** (`emcc`) | C / C++ | **模擬一整個 POSIX 環境**（libc、檔案系統、SDL→WebGL、pthread→Worker）。移植現成大型 C/C++ 專案的首選 |
| **`wasm-pack` / `wasm-bindgen`** | Rust | **只做型別橋接**，膠水精簡。從零寫的新專案首選 |
| **`cargo` + `wasm32-unknown-unknown`** | Rust | 不帶任何 JS 綁定的裸 Wasm |
| **TinyGo** | Go | 大幅縮減 Go 執行期體積（代價：支援子集） |
| **AssemblyScript** | TS 風格語法 | 語法近似 TypeScript，直接編譯為 Wasm，前端工程師的平滑入口 |
| **Zig** | Zig | 原生支援 `wasm32-freestanding` / `wasm32-wasi`，無執行期負擔 |
| **Blazor** | C# | .NET 生態；體積與冷啟動是主要代價 |

### 二進位工具

| 工具 | 用途 |
|---|---|
| **`wasm-opt`**（Binaryen） | **最高投報率的優化工具**。`-Oz` 體積優先、`-O3` 速度優先、`--strip-debug` |
| **`wasm2wat` / `wat2wasm`**（WABT） | 二進位 ↔ 文字格式無損互轉 |
| **`wasm-objdump`**（WABT） | 檢視區段、反組譯（`-d`）、看 import/export（`-x`） |
| **`wasm-decompile`**（WABT） | 產出類 C 的可讀偽碼（逆向分析的第一站） |
| **`wasm-strip`**（WABT） | 剝離 Custom Section |
| **`twiggy`** | **體積診斷**：`twiggy top`（誰在吃體積）、`twiggy dominators`（誰把誰拖下水） |
| **`wasm-snip`** | 手動把指定函數替換成 `unreachable`，砍掉不需要的程式碼路徑 |
| **`wasm-split`**（Binaryen） | 依剖析結果把模組切成 primary + secondary，延遲載入 |
| **`wizer`** | **建置時預初始化**：跑完初始化再把記憶體狀態快照回新模組（附錄 N §10-2） |
| **`wasmtime compile`** | 後端 AOT，產出 `.cwasm`，執行期零編譯 |
| **`wabt` 的 `wasm-validate`** | 離線驗證模組是否合法 |

### 執行期（後端）

| 執行期 | 定位 |
|---|---|
| **Wasmtime** | Bytecode Alliance 主導，WASI 的參考實作；Cranelift 為程式碼產生後端 |
| **WasmEdge** | CNCF 沙盒專案，針對雲原生、微服務與 AI 推理優化（支援 GPU 調用） |
| **Wasmer** | 強調可攜與多語言嵌入；有 WAPM 套件生態 |
| **WAMR** (WebAssembly Micro Runtime) | 極輕量，適合 IoT 與嵌入式 |
| **Spin** (Fermyon) | 建構與執行 Wasm 微服務的框架，Serverless 形態 |
| **wasm3** | 極快的解譯器（無 JIT），適合受限環境 |

### 瀏覽器端輔助

| 工具 | 用途 |
|---|---|
| **`coi-serviceworker`** | 在前端合成 COOP/COEP，讓靜態託管也能用 `SharedArrayBuffer`（第 5 章） |
| **`COEP: credentialless`** | 比 `require-corp` 溫和的隔離模式：允許未表態的跨來源資源，但不帶憑證請求 |
| **`'wasm-unsafe-eval'`** | CSP 關鍵字，只放行 Wasm 編譯而不放行 `eval()`（Chrome 97+／FF 102+／Safari 16+） |
| **`wasm-split`** | Emscripten/Binaryen 的模組切割工具，主模組 + 延遲載入的次模組 |
| **C/C++ DevTools Support (DWARF)** | Chrome 擴充；讓你在 DevTools 裡看 C++ 原始碼、下中斷點、看變數 |
| **Chrome DevTools 的 Memory / Performance 面板** | 觀察 Wasm 記憶體成長與編譯耗時 |
| **`performance.measureUserAgentSpecificMemory()`** | 量測分頁整體記憶體（含 Wasm） |
| **壓縮字典傳輸**（RFC 9842） | 用使用者快取的舊版當字典壓縮新版，`dcb`/`dcz` 編碼；Chrome/Edge 130+（附錄 N §7-2） |
| **`TextEncoder.encodeInto()`** | 直接把字串編碼寫進 Wasm 記憶體，零中間配置（附錄 N §13） |

---

## 四、關鍵編譯旗標速查

```toml
# ── Rust: Cargo.toml（發布版）────────────────────────────
[profile.release]
opt-level = 3        # 速度優先；體積優先用 "z"，平衡用 "s"
lto = true           # 全局連結時最佳化（跨 crate 內聯 + 死碼消除）
codegen-units = 1    # 讓 LTO 有完整視野
panic = "abort"      # 砍掉 unwinding 表（省體積、也省一層複雜度）
strip = true         # 剝離符號（name section）

[lib]
crate-type = ["cdylib"]
```

```bash
# ── Rust: 開啟 SIMD ─────────────────────────────────────
RUSTFLAGS="-C target-feature=+simd128" wasm-pack build --target web --release

# ── Emscripten ──────────────────────────────────────────
emcc app.cpp -O3 \
  -msimd128 \                       # SIMD
  -pthread -s PTHREAD_POOL_SIZE=4 \ # 多執行緒（需跨來源隔離！）
  -s ALLOW_MEMORY_GROWTH=1 \        # 允許 memory.grow
  -s INITIAL_MEMORY=64MB \
  -s MAXIMUM_MEMORY=2GB \
  -s EXPORTED_FUNCTIONS='["_main","_process"]' \
  -s MODULARIZE=1 -s EXPORT_ES6=1 \ # 產出 ES module
  -flto --closure 1 \               # LTO + Closure 壓縮膠水
  -o app.js

# ── 除錯建置（保留符號與 DWARF）──────────────────────────
emcc app.cpp -g -gsource-map -s ASSERTIONS=2 -fsanitize=address -o app.js

# ── 後處理 ──────────────────────────────────────────────
wasm-opt -Oz --strip-debug --strip-producers app.wasm -o app.opt.wasm
twiggy top -n 20 app.opt.wasm
```

---

## 五、`--target` 選對了嗎（`wasm-pack`）

| target | 產出 | 用在哪 |
|---|---|---|
| `web` | ES module，可直接 `<script type="module">` | **靜態託管部署的正解** |
| `bundler` | 給 webpack/rollup/vite 的模組 | 有打包工具的專案 |
| `nodejs` | CommonJS | 伺服器端 |
| `no-modules` | 掛在全域變數上的傳統腳本 | 舊環境、Worker 裡用 `importScripts` |

---

## 六、常見錯誤訊息 → 病因對照

| 你看到 | 實際原因 |
|---|---|
| `404`（載入 `.wasm` 時） | ① `pkg/` 被 `.gitignore` 忽略 ② 用了絕對路徑但站台在子路徑 ③ Jekyll 吃掉了 `_` 開頭的資料夾（放 `.nojekyll`） |
| `TypeError: WebAssembly.instantiateStreaming(): Incorrect response MIME type` | 伺服器沒回 `Content-Type: application/wasm` |
| `ReferenceError: SharedArrayBuffer is not defined` | 沒有跨來源隔離（見第 5 章） |
| `RuntimeError: memory access out of bounds` | Wasm 內部的記憶體錯誤（用 ASan 建置去抓） |
| `TypeError: Cannot perform Construct on a detached ArrayBuffer` | `memory.grow` 後沒有重新取得 `TypedArray` 視圖 |
| `LinkError: import object field 'xxx' is not a Function` | `importObject` 缺了模組要求的 import |
| `RangeError: WebAssembly.Memory(): could not allocate memory` | 撞到瀏覽器的記憶體上限（見第 8 章） |
| 一切正常但結果是亂碼 | 字串編解碼沒對上（UTF-8 vs UTF-16），或指標傳錯 |
