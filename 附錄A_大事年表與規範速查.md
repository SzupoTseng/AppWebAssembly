# 附錄A　Wasm 大事年表與規範速查

> 本附錄的定位是「查得到、可核對」。**年表與規範狀態請以 WebAssembly 官方規範（webassembly.github.io/spec）、提案清單（github.com/WebAssembly/proposals）與 MDN 為最終依據**——本書寫於 2026 年，而提案狀態是會移動的。

---

## 一、大事年表

| 時間 | 事件 | 意義 |
|---|---|---|
| 2011–2013 | **Google NaCl / PNaCl** | 靜態驗證 x86 機器碼 + 分段沙盒；後改分發 LLVM bitcode。技術成功、政治失敗（僅 Chrome 支援） |
| 2013 | **Mozilla asm.js** | JavaScript 的嚴格子集，用 `x\|0` / `+x` 標註型別。**證明了不用外掛就能拿到接近原生的效能，且四家引擎都能實作** |
| 2013 起 | **Emscripten 成熟** | LLVM → asm.js（後 → Wasm）的 C/C++ 編譯管線，Unreal Engine 等大型專案得以搬上瀏覽器 |
| **2015-06** | **四方共同宣布 WebAssembly** | Google、Mozilla、Microsoft、Apple。談成的關鍵是「刻意做小」 |
| 2017-03 起 | **四大瀏覽器內建 Wasm MVP** | Chrome、Firefox、Safari、Edge。MVP 成為共同能力 |
| 2019 起 | **WASI 提案面世** | Wasm 脫離瀏覽器，進軍伺服器端、雲原生、邊緣運算 |
| 2019 | Docker 創辦人 Solomon Hykes 的推文 | 「如果 2008 年就有 WASM+WASI，我們根本不需要發明 Docker」（常被斷章取義，見第 1 章 ⚠️） |
| **2019-12** | **W3C 正式定為推薦標準（Recommendation）** | WebAssembly Core Specification 1.0。與 HTML、CSS、JavaScript 並列為 Web 的第四種核心語言 |
| 2020 前後 | Bytecode Alliance 成立、Wasmtime / Lucet / WAMR 等執行期成形 | 後端生態的基礎設施 |
| 2020–2021 | SIMD、bulk memory、reference types、multi-value 等提案陸續落地 | MVP 欠下的技術債開始償還 |
| 2021 起 | WasmEdge 進入 CNCF 沙盒；Fermyon Spin 等框架出現 | 雲原生正式接受 Wasm |
| 2022 前後 | **Wasm 2.0**（含 SIMD、bulk memory、reference types、multi-value 等） | 核心規範的第二個里程碑 |
| 2023–2024 | **Component Model / WIT 成形；WASI 0.2 (Preview 2) 發布** | 從「單體模組」走向「可組合元件」 |
| 2025-04 | **JSPI（JavaScript Promise Integration）進入 Phase 4** | 同步的 Wasm 程式碼終於能呼叫非同步的 Web API |
| **2025-09** | **★ WebAssembly 3.0 宣布完成，成為現行標準** | **MVP 那筆技術債，到這裡基本上還完了**（見下表） |
| 2025 起 | JSPI 於 **Chrome 137、Firefox 139** 出貨 | 見附錄 M 第五節 |
| 持續進行 | Component Model、stack switching、JS String Builtins、custom page sizes、shared-everything threads… | 見下方提案速查 |

> ⚠️ **本書修訂說明**：Wasm 3.0 是一次分水嶺。**在它之前，GC／memory64／尾呼叫／例外處理／multiple memories 都是「提案」；在它之後，它們是核心規範的一部分。** 如果你讀到任何把這些東西稱為「提案」「實驗性」的資料（**包括本書初稿**），請以此為準——那些敘述寫於 3.0 之前。

---

## 二、二進位格式速查

**檔案開頭永遠是 8 個位元組**：`00 61 73 6D`（`\0asm` 魔數）+ `01 00 00 00`（版本 1）。

**區段（section）順序是規範強制的**，這正是單趟線性驗證與串流編譯的前提：

| ID | 名稱 | 內容 | 能否剝離 |
|---|---|---|---|
| 0 | Custom | `name`（函數/變數名）、DWARF 除錯資訊、Source Map 連結、語言中繼資料 | **✅ 可（`strip`）** |
| 13 | Tag | 例外標籤（Wasm 3.0 的例外處理） | ❌ |
| 1 | Type | 所有函數簽章 | ❌ |
| 2 | Import | 從宿主要進來的函數/記憶體/表/全域 | ❌ |
| 3 | Function | 函數 → 簽章的對應 | ❌ |
| 4 | Table | 函數參考表（間接呼叫目標） | ❌ |
| 5 | Memory | 線性記憶體的初始頁數與上限 | ❌ |
| 6 | Global | 全域變數 | ❌ |
| 7 | Export | **對外曝露的一切（攻擊者永遠看得到）** | ❌ |
| 8 | Start | 實例化後自動執行的函數 | ❌ |
| 9 | Element | 表的初始內容 | ❌ |
| 10 | Code | 每個函數的指令與區域變數 | ❌ |
| 11 | Data | **線性記憶體的初始資料（明文字串就在這裡）** | ❌ |
| 12 | DataCount | 資料段數量（bulk memory 提案引入） | ❌ |

**核心型別**：

| 類別 | 型別 |
|---|---|
| 數值 | `i32`、`i64`、`f32`、`f64` |
| 向量（SIMD 提案） | `v128` |
| 參考（reference types 提案） | `funcref`、`externref` |
| 堆積型別（GC，Wasm 3.0） | `struct`、`array`、`i31`、以及型別化參考 `(ref $T)` |

**記憶體單位**：**1 頁 = 64 KiB**。`memory.grow` 只能增長，沒有 `shrink`。

---

## 三、規範狀態速查（依對工程決策的影響排序）

### 3-1　已進入核心規範（Wasm 1.0 / 2.0 / **3.0**）

> **這些不再是「提案」，它們就是 Wasm。** 剩下的問題只有「你的目標執行期跟上了沒有」。

| 特性 | 進入版本 | 解決什麼 | 對你的意義 |
|---|---|---|---|
| **Bulk memory** | 2.0 | `memory.copy` / `memory.fill` 等批次操作 | 大幅加速 `memcpy` 類操作 |
| **Reference types** | 2.0 | `externref` 持有不透明的宿主參考 | 縮小 JS↔Wasm 的橋接成本 |
| **Multi-value** | 2.0 | 函數可回傳多個值 | 減少為了回傳而配置記憶體的樣板 |
| **SIMD (`v128`)** | 2.0 / 3.0 確立 | 一條指令處理多筆資料 | 2–4 倍加速。**注意只有 128 位元寬，遠窄於 AVX2/AVX-512** |
| **Threads / Atomics** | — | 共享線性記憶體 + 原子操作 | **依賴 `SharedArrayBuffer`，需跨來源隔離**（第 5 章的頭號障礙） |
| **★ GC** | **3.0** | `struct`/`array`/`i31` + 宿主 GC | **Kotlin/Dart/Java 的體積結構性下降。對 Rust/C/C++ 幾乎無用** |
| **★ Memory64** | **3.0** | `i64` 定址（記憶體與表） | 突破 4GiB，**但失去保護頁的免費界檢查，有效能代價**（第 8 章） |
| **★ Multiple memories** | **3.0** | 一個模組可宣告多塊線性記憶體，並直接在其間搬資料 | **第 8 章的第三條破圈路徑**：在 wasm32 下把資料分到多塊 4GiB 記憶體裡 |
| **★ Exception handling** | **3.0** | 例外標籤（Tag section）與 payload | C++ 例外不必再靠 JS 蹦床，跨界開銷大降（附錄 M 第四節） |
| **★ Tail call (`return_call`)** | **3.0** | 尾呼叫優化 | **函數式語言的深層遞迴不再爆棧**（附錄 F 案例 92 的關鍵） |
| **★ Typed function references** | **3.0** | `(ref $sig)` 具型別的函數參考 | 間接呼叫可省下執行期簽章檢查（附錄 M 第三節） |
| **★ Extended const expressions** | **3.0** | 初始化式可做算術 | 減少為了初始化而跑 start 函數 |
| **★ Branch hinting** | **3.0** | 分支機率提示 | 幫助引擎產出更好的機器碼 |
| **★ Relaxed SIMD** | **3.0** | 放寬部分 SIMD 語意以更好映射硬體 | 換取效能，**代價是結果可能因平台而異**——鏈上與任何需要確定性的場景必須禁用 |

### 3-2　核心規範之外、但已可用

| 特性 | 狀態 | 意義 |
|---|---|---|
| **JSPI（JS Promise Integration）** | **Phase 4（2025-04 標準化）**；Chrome 137、Firefox 139 出貨 | **同步的 Wasm 程式碼可以呼叫非同步的 Web API**——把 Wasm「不能阻塞」這道牆打開了一個口（附錄 M 第五節） |
| **Component Model / WIT** | 演進中 | WASI 0.2 的基礎；試圖從根本解決「邊界收費站」 |
| **JS String Builtins** | 演進中 | 讓 Wasm 直接操作 JS 字串，減少編解碼稅 |
| **Stack switching** | 演進中 | 協程的原生支援（JSPI 是它的一個特例應用） |
| **Custom page sizes** | 演進中 | 讓嵌入式場景不必被 64KiB 的頁大小綁死 |

> **提案分五階段**：Phase 0（前期構想）→ 1（提案）→ 2（規格草案）→ 3（實作草案）→ 4（標準化）。**狀態隨時間變動，請以官方 proposals 倉庫與 `webassembly.github.io/spec` 上標註的版本日期為準。**

---

## 四、WASI 兩個世代的對照

| | `wasi_snapshot_preview1` | **WASI 0.2 (Preview 2)** |
|---|---|---|
| 模型 | POSIX 風格的檔案描述符 | **Component Model + WIT 介面定義** |
| 介面形態 | 一大包扁平的函數 | 拆成 `wasi:io`、`wasi:filesystem`、`wasi:sockets`、`wasi:http`、`wasi:clocks`、`wasi:random` 等 |
| Rust target | `wasm32-wasip1` | `wasm32-wasip2` |
| 生態成熟度 | **高**（TinyGo、多數工具鏈都支援） | 演進中，工具鏈逐步跟上 |
| 可組合性 | 差（單體） | **好**（可以只給某元件 `wasi:clocks`，不給檔案系統） |

**能力式安全的核心語法**：

```bash
# 只授權 ./my_storage 這一個目錄，映射為模組眼中的 /sandbox
wasmtime run --dir=./my_storage::/sandbox my_server.wasm
# 環境變數也要顯式授予
wasmtime run --env API_MODE=prod app.wasm
# 網路（0.2）
wasmtime serve --wasi inherit-network app.wasm
```

---

## 五、瀏覽器 API 速查

```javascript
// ── 載入（★ 首選：邊下載邊編譯）───────────────────────────
const { instance, module } = await WebAssembly.instantiateStreaming(
  fetch("app.wasm"),            // 伺服器必須回傳 Content-Type: application/wasm
  importObject                  // 遞給模組的能力
);

// ── 只編譯不實例化（可快取 module 給多個 Worker 用）────────
const mod = await WebAssembly.compileStreaming(fetch("app.wasm"));
const inst = await WebAssembly.instantiate(mod, importObject);

// ── 記憶體 ───────────────────────────────────────────────
const mem = new WebAssembly.Memory({ initial: 16, maximum: 256, shared: false });
//                                    ↑ 頁數（每頁 64KiB）      ↑ 多執行緒需要 shared:true
new Uint8Array(mem.buffer);      // ★ grow 之後必須重新取得視圖

// ── 表（間接呼叫目標）─────────────────────────────────────
const tbl = new WebAssembly.Table({ initial: 2, element: "anyfunc" });

// ── 錯誤型別 ─────────────────────────────────────────────
WebAssembly.CompileError    // 二進位格式錯誤或驗證失敗
WebAssembly.LinkError       // import 對不上
WebAssembly.RuntimeError    // 執行期 trap（越界、除以零、unreachable）

// ── 跨來源隔離偵測 ────────────────────────────────────────
if (self.crossOriginIsolated) { /* SharedArrayBuffer 可用 */ }
```

---

## 六、常見 trap 與它們的來源

| Trap 訊息 | 原因 |
|---|---|
| `memory access out of bounds` | 讀寫超出當前線性記憶體大小 |
| `integer divide by zero` | `i32.div_s` / `i32.rem_s` 等除以零 |
| `integer overflow` | `i32.div_s(INT_MIN, -1)` 這類溢位 |
| `invalid conversion to integer` | `f64` → `i32` 轉換時值為 NaN 或超界（非飽和版本） |
| `unreachable` | 執行到 `unreachable` 指令（多半是 Rust 的 `panic!` 或 C++ 的 `abort()`） |
| `indirect call type mismatch` | 間接呼叫時實際函數簽章與宣告不符 |
| `call stack exhausted` | 遞迴過深（**`return_call` 尾呼叫就是為了這個**，Wasm 3.0） |
| `null function or function signature mismatch` | 函數表項目為空或簽章不符 |

---

## 七、參考資源

| 主題 | 位置 |
|---|---|
| 核心規範 | `webassembly.github.io/spec/core/` |
| 提案清單與階段 | `github.com/WebAssembly/proposals` |
| MDN WebAssembly 指南 | `developer.mozilla.org/docs/WebAssembly` |
| Emscripten 文件 | `emscripten.org/docs` |
| Rust and WebAssembly Book | `rustwasm.github.io/docs/book/` |
| `wasm-bindgen` 指南 | `rustwasm.github.io/wasm-bindgen/` |
| WABT（二進位工具集） | `github.com/WebAssembly/wabt` |
| Binaryen（`wasm-opt`） | `github.com/WebAssembly/binaryen` |
| Bytecode Alliance / Wasmtime | `bytecodealliance.org` |
| WASI 與 WIT | `wasi.dev` · `component-model.bytecodealliance.org` |
