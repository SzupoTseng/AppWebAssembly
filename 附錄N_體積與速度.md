# 附錄N　體積與速度：Wasm 的壓縮與加速全解

> 這是全書技術密度最高的一份附錄。它回答兩個問題：**「我的 `.wasm` 為什麼這麼大，怎麼變小？」** 與 **「它為什麼沒有想像中快，怎麼變快？」**
>
> **一條貫穿全篇的紀律**：**先量測，再優化，然後再量測一次。** 下面每一項技術都有它適用的形狀；把它們無差別地全部套上去，通常會得到一個又慢又難維護的建置流程。

---

# 第一部：體積

## 一、先解剖：你的位元組到底花在哪裡

**在動任何旗標之前，先做這一步。** 沒有這一步的優化都是猜測。

```bash
# 1. 區段層級的預算：哪個區段最肥
wasm-objdump -h app.wasm
#   Type       start=0x0000000b end=0x000001a4 (size=0x00000199) count: 52
#   Function   ...
#   Code       start=0x00012f4a end=0x0031b2c1 (size=0x00308377) ← 通常是這個
#   Data       start=0x0031b2c3 end=0x004a9f10 (size=0x0018ec4d) ← 但別忽略這個

# 2. 符號層級：誰在吃 Code 區段
twiggy top -n 30 app.wasm

# 3. 保留鏈：誰把誰拖下水（最有用的一個）
twiggy dominators app.wasm

# 4. 為什麼某個函數還在？（回答「我明明沒用到它」）
twiggy paths app.wasm -- 'core::fmt::write'
```

**四個區段的典型佔比與對應武器**：

| 區段 | 典型佔比 | 它是什麼 | 對應武器 |
|---|---|---|---|
| **Code** | 50–80% | 所有函數本體 | 編譯旗標、LTO、死碼消除、`wasm-opt` |
| **Data** | 10–45% | 靜態資料、字串常數、查表 | **裁剪資料本身**（見 §6）、執行期解壓 |
| **Custom (`name`/DWARF)** | 0–30% | 除錯符號 | `--strip-debug`（發布版必做） |
| **Element / Table** | <5% | 函數表初始內容 | 減少間接呼叫的目標數量 |

> **第一個常見誤判**：看到檔案很大就衝去調 `opt-level`。**但如果你的 Data 區段佔了 45%，把 Code 再壓 10% 也只換來 5% 的總體積。** 先看 `wasm-objdump -h`。

---

## 二、編譯期旗標：它們真正砍掉的是什麼

### 2-1　Rust

```toml
[profile.release]
opt-level = "z"      # 體積優先（"s" 平衡、3 速度優先）
lto = "fat"          # 全程式最佳化：跨 crate 內聯 + 全域死碼消除
codegen-units = 1    # ★ 讓 LTO 有完整視野；平行編譯變慢，但產物顯著更小
panic = "abort"      # 砍掉 unwinding 表與 landing pad
strip = true         # 剝離 name section
overflow-checks = false
debug = false
incremental = false  # 增量編譯會妨礙跨單元最佳化
```

**每一項真正砍掉什麼**：

| 旗標 | 砍掉什麼 | 代價 |
|---|---|---|
| `opt-level = "z"` | 停用迴圈展開與**自動向量化** | **⚠️ 這會關掉 SIMD 自動向量化**——若你靠它，改用 `"s"` 或 `3` |
| `lto = "fat"` | 跨 crate 內聯後的死碼、重複的泛型實例 | 編譯時間顯著上升 |
| `codegen-units = 1` | 讓 LTO 看到全部——**這一項單獨就常有 5–15%** | 編譯不能平行 |
| `panic = "abort"` | unwinding 表、landing pad、`Drop` 展開路徑 | panic 不能被 catch（Wasm 上本來就少用） |
| `strip = true` | `name` 自訂區段 | **失去可讀的堆疊追蹤**（見 §12 的取捨） |

### 2-2　Rust 最大的隱藏體積兇手：panic 的格式化機制

**這是絕大多數 Rust/Wasm 專案最沒被發現的一塊肥肉。**

一句 `panic!("index {} out of range", i)` 會把 **`core::fmt` 的整套格式化機制**拉進二進位——那是一台包含 trait 物件分派、寬度/精度處理、浮點數格式化的小型機器，**輕易佔掉數十 KB 到上百 KB**。而更糟的是：**每一個 `unwrap()`、每一次陣列索引、每一次整數溢位檢查，都可能在失敗路徑上引用它。**

```bash
# 確認它是不是兇手
twiggy paths app.wasm -- 'core::fmt::write' | head -20
```

**根治手段（需要 nightly）**：

```bash
cargo +nightly build --release --target wasm32-unknown-unknown \
  -Z build-std=std,panic_abort \
  -Z build-std-features=panic_immediate_abort
```

`panic_immediate_abort` 讓所有 panic 直接變成 `unreachable` 指令，**整套格式化機制與 panic 訊息字串全部消失**。對小型模組，這一招的效果常常超過其他所有旗標的總和。

**代價很誠實**：**panic 之後你什麼訊息都拿不到**，只有一個 `RuntimeError: unreachable`。**這是一個「發布版換體積、除錯版保訊息」的雙建置決策，不是全域決策。**

**保守一點的做法**（不需要 nightly）：

```rust
// 避免帶格式化的 panic
let v = arr.get(i).ok_or(MyError::OutOfRange)?;   // 而不是 arr[i]
// 避免 Display / format!
// 用靜態字串而不是 format!("...{}", x)
```

### 2-3　Rust 的第二個兇手：單型化爆炸

泛型在 Rust 裡是**單型化（monomorphization）** 的——`Vec<u8>` 與 `Vec<u32>` 會生成兩份完全獨立的程式碼。一個被十種型別實例化的複雜泛型函數，就是十份。

```rust
// ❌ 整個函數本體被複製 N 份
pub fn process<P: AsRef<Path>>(path: P, data: &[u8]) { /* 兩百行 */ }

// ✅ 外層薄殼負責轉型，內層單一實例做重活
pub fn process<P: AsRef<Path>>(path: P, data: &[u8]) {
    process_inner(path.as_ref(), data)      // 薄殼，被複製也沒關係
}
fn process_inner(path: &Path, data: &[u8]) { /* 兩百行，只有一份 */ }
```

**這個「泛型薄殼 + 具體實作」的模式，是 Rust 生態裡最有效的體積技巧之一**，而 `twiggy top` 會直接把重複的實例列出來讓你看見。

### 2-4　C / C++

```bash
emcc app.cpp \
  -Oz \
  -flto \
  -fno-exceptions \                  # C++ 例外的展開表通常很大
  -fno-rtti \                        # typeid / dynamic_cast 的中繼資料
  -ffunction-sections -fdata-sections \
  -Wl,--gc-sections \                # 未使用的 section 整段丟掉
  -sASSERTIONS=0 \                   # 移除執行期斷言與訊息字串
  -sFILESYSTEM=0 \                   # ★ 不需要 MEMFS 就別打包整套檔案系統
  -sENVIRONMENT=web \                # 移除 node/worker/shell 的分支
  -sMALLOC=emmalloc \                # 比 dlmalloc 小得多的配置器
  -sMINIMAL_RUNTIME=1 \              # 極簡 JS 膠水（限制較多）
  --closure 1 \                      # 用 Closure Compiler 壓 JS 膠水
  -sEXPORTED_FUNCTIONS='["_main","_process"]' \
  -o app.js
```

**幾個特別值得注意的**：

- **`-sFILESYSTEM=0`**：如果你的程式碼沒有真的呼叫 `fopen`，Emscripten 預設仍可能連進整套 MEMFS。**這一項常常直接省下數十 KB 的 JS 膠水。**
- **`-sMALLOC=emmalloc`**：`emmalloc` 遠小於預設的 `dlmalloc`，代價是某些配置模式下較慢。**如果你的程式碼幾乎不做動態配置（例如全部用 arena），這是純賺。**
- **`--closure 1`**：注意它壓的是 **JS 膠水**不是 `.wasm`。對 Emscripten 專案，膠水本身可能有數十 KB。

### 2-5　配置器的選擇

| 配置器 | 體積 | 速度 | 備註 |
|---|---|---|---|
| Rust 預設（dlmalloc） | 中 | 好 | 大多數情況的正確選擇 |
| `emmalloc`（Emscripten） | **小** | 中 | 配置模式簡單時的好選擇 |
| **自建 bump/arena** | **極小** | **極快** | **見 §11**——如果你的配置模式是「一批分配、一次全放」，這是雙贏 |
| `wee_alloc` | 極小 | 差 | ⚠️ **已不再維護且有已知的記憶體回收問題，不建議新專案採用** |

---

## 三、`wasm-opt`：不只是一個 `-Oz`

**Binaryen 的 `wasm-opt` 是整條鏈上投報率最高的單一工具**，但多數人只會用一個旗標。

```bash
wasm-opt -Oz \
  --strip-debug --strip-producers --strip-target-features \
  --low-memory-unused \
  --zero-filled-memory \
  --converge \
  app.wasm -o app.opt.wasm
```

**它內部真正做的事**（`-Oz` 是一組 pass 的組合）：

| Pass 類別 | 代表 pass | 做什麼 |
|---|---|---|
| 死碼與清理 | `--dce`、`--vacuum`、`--remove-unused-module-elements` | 移除到不了的程式碼、沒用到的匯入/全域/函數 |
| 去重 | `--duplicate-function-elimination` | **合併二進位完全相同的函數**——單型化爆炸的解藥之一 |
| 內聯 | `--inlining-optimizing` | 把小函數展開，再對結果重新最佳化 |
| 指令層 | `--optimize-instructions` | 窺孔最佳化：`x*2` → `x<<1` 這一類 |
| 區域變數 | `--simplify-locals`、`--coalesce-locals`、`--reorder-locals` | 減少區域變數數量與索引大小（**LEB128 下小索引更省位元組**） |
| 佈局 | `--reorder-functions` | **依呼叫頻率重排函數索引**，讓熱門函數拿到小索引 → LEB128 編碼更短 |

**三個常被忽略的旗標**：

- **`--converge`**：反覆執行最佳化直到不再變小。**通常再擠出 1–3%**，代價是編譯時間翻倍。
- **`--low-memory-unused`**：告訴最佳化器「低位址那一段沒被使用」，讓它能對定址做更激進的假設。**Emscripten 專案通常安全，手寫記憶體佈局的專案要小心。**
- **`--zero-filled-memory`**：宣告記憶體初始為零，讓最佳化器移除多餘的清零程式碼。

> ⚠️ **順序陷阱**：`wasm-opt` 必須在 **`wasm-bindgen` 之後**執行。`wasm-pack` 預設會做這件事，但如果你手動串工具鏈，**在 `wasm-bindgen` 之前先跑 `wasm-opt` 會讓它砍掉 bindgen 還需要的東西**，症狀是執行期出現莫名的 `LinkError`。

---

## 四、`no_std` 與砍掉標準庫

**當你的模組是純運算核心時**，整個 `std` 可能都是負擔：

```rust
#![no_std]
extern crate alloc;                  // 只要堆積配置，不要 std 的其他部分

use alloc::vec::Vec;

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! { core::arch::wasm32::unreachable() }
```

**收益**：省下 `std` 的執行期初始化、I/O 抽象、執行緒與同步原語、以及（最重要的）它拖進來的格式化機制。
**代價**：不能用 `String`（要用 `alloc::string::String`）、不能用 `std::collections::HashMap`（要換 `hashbrown`）、生態中一大半的 crate 不支援。

**判準**：**如果你的模組導出的是「餵位元組進去、拿位元組出來」的純函數，`no_std` 幾乎總是划算的。** 如果它需要檔案、時間、隨機數，那 `std` 帶來的便利通常值那些位元組。

---

## 五、消除跨語言的重複：`wasm-bindgen` 的體積成本

```rust
// ❌ 每一個 #[wasm_bindgen] 都會生成一份 JS 膠水與 Wasm 側的 shim
#[wasm_bindgen]
pub fn process_pixel(r: u8, g: u8, b: u8) -> u32 { /* ... */ }

// ✅ 一個粗介面，內部自己迴圈
#[wasm_bindgen]
pub fn process_image(ptr: *mut u8, len: usize) { /* ... */ }
```

**這件事同時是體積優化與效能優化**（見 §13）——**細粒度的導出介面既胖又慢。**

**其他幾個具體手段**：

- 回傳 `Vec<u8>` 會經過 bindgen 的配置/釋放樣板；**回傳 `(ptr, len)` 讓 JS 自己讀線性記憶體更省**。
- `js_sys` / `web_sys` **只開你用到的 feature**——它們的 feature 清單極長，全開會拉進大量綁定。
- `#[wasm_bindgen(js_name = "...")]` 不影響體積，但 `catch` / `getter` / `setter` 等屬性會生成額外樣板。

---

## 六、資料才是大宗：一般化 FluffOS 的那一課

**附錄 L 記錄了一個數字：FluffOS 的 Wasm 建置把 ICU 資料從約 30 MB 砍到約 780 KB（−97%），而整個驅動器的程式碼本體才 3.6 MB。**

**把它一般化成一條規則**：

> **大型 C/C++ 專案的 Wasm 產物裡，往往有一半以上是它拖進來的資料表，而那些表通常有 90% 你用不到。**

**常見的資料肥肉與對應手術**：

| 資料 | 常見大小 | 手術 |
|---|---|---|
| ICU / Unicode 表 | 數 MB ~ 30 MB | 只保留需要的規則（斷詞/校對/轉寫各自可裁） |
| 字型 | 數 MB | 子集化（只留用到的字元） |
| 語言模型 / 訓練資料 | 數十 MB | **不要打包進 `.wasm`**，改成執行期抓（可快取） |
| 時區資料庫 | 數百 KB | 只保留目標地區 |
| 內建測試資料 / 範例 | 常被忘記 | 用編譯條件排除 |
| 查表（三角函數、CRC…） | KB ~ MB | **考慮執行期計算**——CPU 通常比記憶體便宜 |

**還有一招：把資料壓縮後嵌入，執行期解壓。**

```
把 2 MB 的資料表用 zstd 壓成 400 KB 嵌進 Data 區段，
啟動時用一個 15 KB 的解壓器展開到線性記憶體。
→ 淨省 1.6 MB 傳輸，代價是啟動時多幾毫秒。
⚠️ 但先確認：外層的 Brotli 傳輸壓縮是不是已經幫你壓過了？
   若是，這一招只是把壓縮從傳輸層搬到了應用層，可能反而更差。
```

---

## 七、傳輸層：Brotli，以及一個會改變遊戲規則的新東西

### 7-1　為什麼 Wasm 特別適合 Brotli

**經驗上 Wasm 的壓縮率常在 3.5–5 倍**（附錄 L 的實例是 3.6 MB → 0.8 MB，約 4.5 倍）。原因有三：

1. **LEB128 讓小數字只佔一個位元組**，且分佈高度集中 → 熵低。
2. **指令碼的重複性極高**：`20 xx 20 yy 6A`（load/load/add）這種模式在整個模組裡出現千萬次。
3. **Data 區段常含大量零與重複字串**。

```nginx
# 靜態預壓縮優於即時壓縮（省 CPU、且能用最高等級）
brotli_static on;
# 產出：app.wasm + app.wasm.br（brotli -q 11）
```

### 7-2　★ 壓縮字典傳輸（Compression Dictionary Transport）

**這是 Wasm 更新分發上這幾年最重要的一項變化，而它幾乎沒有出現在 Wasm 的討論裡。**

**問題**：你的 `app.wasm` 有 8 MB（Brotli 後 1.8 MB）。你改了三行程式碼發新版——**使用者要重新下載整整 1.8 MB**，即使 99% 的位元組跟他快取裡的舊版一模一樣。

**解法**：**用使用者已經快取的舊版本，當作壓縮新版本的字典。**

```http
# 第一次回應：宣告「這個檔案可以當作未來的字典」
HTTP/2 200
Content-Type: application/wasm
Use-As-Dictionary: match="/app-*.wasm"

# 之後使用者要新版時，瀏覽器自動帶上：
Available-Dictionary: :pZGm1Av0IEBKARczz7exkNYsZb8LzaMrV7J32a2fFG4=:
Accept-Encoding: br, dcb, dcz

# 伺服器用舊版當字典壓縮新版：
HTTP/2 200
Content-Encoding: dcb        # Dictionary-Compressed Brotli（dcz = Zstandard 版）
→ 實際傳輸可能只有幾十 KB
```

**狀態**：**RFC 9842**；**Chrome 130+、Edge 130+ 支援，Firefox 進行中**。CDN 側，**Cloudflare 於 2026 年 4 月推出邊緣支援**（其實作本身就是用 Wasm 編譯的 Zstandard）。

**它對 Wasm 的意義特別大**，因為 Wasm 應用有兩個特徵：**（一）** 單一大檔案；**（二）** 改版時大部分位元組不變。**這正是差分壓縮效果最好的形狀。**

> 💡 **一個推論**：一旦這條路普及，**「模組要不要切小」這個決策的權重會下降**——切小的主要動機之一（讓更新只重下載一部分）被差分壓縮取代了，而切小的代價（多次往返、跨模組呼叫）依然存在。

---

## 八、切割與延遲載入

| 手段 | 機制 | 適合 |
|---|---|---|
| **`wasm-split`**（Binaryen） | 依剖析結果把模組切成 primary + secondary，第一次呼叫到才抓 | 啟動路徑明確、大量功能使用者可能永遠不點 |
| **手動多模組 + 共用記憶體** | 把 `memory` 從一邊 export、另一邊 import | 功能邊界清晰（如 PDF 匯出、OCR 語言包） |
| **執行期抓資產** | 資料不進 `.wasm`，用 `fetch` + Cache API | 模型權重、字型、語言包 |

```javascript
// 手動切割：兩個模組共用同一塊線性記憶體，資料不必複製
const core = await WebAssembly.instantiateStreaming(fetch("core.wasm"), imports);
const pdf  = await WebAssembly.instantiateStreaming(fetch("pdf.wasm"), {
  env: { memory: core.instance.exports.memory },   // ★ 關鍵
});
```

---

## 九、體積優化投報率總表

| # | 手段 | 典型收益 | 成本 | 何時做 |
|---|---|---|---|---|
| 0 | **裁剪資料本身** | **可達 −90%** | 需要領域判斷 | **最先做** |
| 1 | `wasm-opt -Oz --converge` | −15~40% | 建置時間 | 一定做 |
| 2 | `lto` + `codegen-units=1` | −5~15% | 編譯時間 | 一定做 |
| 3 | **Brotli 傳輸** | **−70~80%（傳輸）** | 幾乎為零 | **一定做** |
| 4 | `panic_immediate_abort`（Rust） | 小模組可 −30%+ | 失去 panic 訊息 | 發布版 |
| 5 | `--strip-debug` | −0~30% | 失去堆疊追蹤 | 發布版（保留一份帶符號的） |
| 6 | 泛型薄殼、去除單型化重複 | −5~20% | 重構 | 有測到才做 |
| 7 | `no_std` | −10~30% | 生態受限 | 純運算核心 |
| 8 | `-sFILESYSTEM=0` 等 Emscripten 旗標 | −數十 KB 膠水 | 功能受限 | 確認沒用到 |
| 9 | 模組切割 | 首屏 −50%+ | 架構複雜度 | 啟動路徑明確時 |
| 10 | **壓縮字典傳輸** | **更新時 −90%+** | 需 CDN/伺服器支援 | 有頻繁改版時 |

---

# 第二部：速度

## 十、啟動路徑的四段拆解

**「Wasm 很慢」的抱怨，八成是在講啟動而不是穩態。** 而啟動是四段獨立的成本，各有各的武器：

```
① 網路傳輸  ── 受壓縮後體積與 RTT 支配 ──→ 第一部全部
② 編譯      ── 與位元組數線性相關      ──→ §10-1
③ 實例化    ── 配置記憶體、跑 Data 段初始化、執行 start ──→ §10-2
④ 執行期初始化 ── 全域建構子、語言 runtime 自舉、資料結構建立 ──→ §10-3 ★最常被低估
```

### 10-1　編譯階段的四個武器

```javascript
// ① 串流編譯：第一個位元組到達就開工（伺服器必須回 application/wasm）
const { instance } = await WebAssembly.instantiateStreaming(fetch("app.wasm"), imports);

// ② 編譯一次，N 個 Worker 共用（WebAssembly.Module 可結構化複製）
const mod = await WebAssembly.compileStreaming(fetch("app.wasm"));
workers.forEach(w => w.postMessage({ mod }));      // ★ 省下 N−1 次完整編譯

// ③ 磁碟程式碼快取：給 .wasm 一個穩定 URL（內容雜湊檔名最佳）
//    引擎會把最佳化後的機器碼寫進 HTTP 快取，回訪可跳過整個編譯階段
//    → 大型模組的第二次載入常快一個量級
```

**④ 分層編譯是自動的，但你可以理解它**：Liftoff 先產出可執行碼（快而爛），TurboFan 在背景產出好碼再熱替換。**這意味著「剛啟動的前幾百毫秒，你的 Wasm 跑的是未最佳化版本」**——如果你在啟動後立刻做一次基準測試，量到的是 Liftoff 的數字，不是穩態效能。

### 10-2　★ Wizer：把「初始化」搬到建置時

**這是伺服器端與 CLI 場景最被低估的一項技術。**

很多模組啟動時要做大量一次性工作：解析設定、建立查表、載入資料結構、初始化直譯器。**Wizer（Bytecode Alliance）的想法是：在建置時就把這些做完，然後把「初始化之後的記憶體狀態」快照回一個新的 `.wasm`。**

```bash
# 建置時：實例化模組、執行初始化函數、把結果快照成新模組
wizer app.wasm -o app.initialized.wasm --allow-wasi
```

```rust
// 模組側：標記哪個函數是「初始化」
#[export_name = "wizer.initialize"]
pub extern "C" fn init() {
    LOOKUP_TABLE.set(build_expensive_table());   // 這些在建置時就跑完了
}
```

**執行期拿到的模組，Data 區段裡已經是初始化完成的記憶體映像**——啟動時什麼都不用做。官方基準宣稱**實例化與初始化快 1.35 到 6.00 倍**，實際收益取決於你原本要做多少初始化工作。

**代價與限制**：**（一）** 快照會讓 Data 區段變大（**體積換啟動速度**，與第一部直接衝突，要量測取捨）；**（二）** 初始化過程中不能依賴執行期才有的東西（時間、隨機數、網路）；**（三）** 主要用於伺服器端/CLI，瀏覽器場景要衡量體積代價。

**同一個思路的其他形態**：

| 技術 | 場景 |
|---|---|
| **Wizer** | 通用預初始化快照 |
| `wasmtime compile` → `.cwasm` | **後端 AOT**：把編譯完全移到部署前，執行期零編譯 |
| 引擎的 pooling allocator | 預先配置好實例池，省下每次實例化的記憶體配置 |

### 10-3　那個最常被低估的第四段

**Pyodide 下載完 30 MB 之後，還要花時間自舉 CPython。** Emscripten 專案要跑完所有 C++ 全域建構子。這些發生在**編譯完成之後**，而且不會出現在「模組載入時間」這個指標裡。

```javascript
// 分開量測，否則你會優化錯地方
const t0 = performance.now();
const mod = await WebAssembly.compileStreaming(fetch("app.wasm"));
const t1 = performance.now();                       // ← 編譯
const inst = await WebAssembly.instantiate(mod, imports);
const t2 = performance.now();                       // ← 實例化
inst.exports.app_init();
const t3 = performance.now();                       // ← 執行期初始化 ★
console.log(`編譯 ${(t1-t0)|0}ms / 實例化 ${(t2-t1)|0}ms / 初始化 ${(t3-t2)|0}ms`);
```

---

## 十一、穩態效能之一：讓編譯器產出更好的碼

### 11-1　SIMD：開了不等於用了

```bash
# Rust
RUSTFLAGS="-C target-feature=+simd128" cargo build --release --target wasm32-unknown-unknown
# Emscripten
emcc -msimd128 -O3 ...
```

**三個必須知道的現實**：

1. **`opt-level = "z"` 會關掉自動向量化。** 你不能同時要最小體積與自動 SIMD——**這是一個必須做的選擇。**
2. **自動向量化很挑剔**：迴圈邊界要在編譯期可知或可推斷、不能有資料相依、不能有指標別名疑慮。**沒被向量化時編譯器不會警告你**，只能看反組譯或量測。
3. **手寫 intrinsics 是保底手段**：

```rust
use core::arch::wasm32::*;

pub fn add_f32x4(a: &[f32], b: &[f32], out: &mut [f32]) {
    for i in (0..a.len()).step_by(4) {
        unsafe {
            let va = v128_load(a.as_ptr().add(i) as *const v128);
            let vb = v128_load(b.as_ptr().add(i) as *const v128);
            v128_store(out.as_mut_ptr().add(i) as *mut v128, f32x4_add(va, vb));
        }
    }
}
```

**別忘了第 3 章的天花板**：**Wasm SIMD 固定 128 位元**，為 AVX2（256）手寫優化的程式碼移植過來，向量寬度直接砍半。**典型加速比是 2–4 倍，不是 8–16 倍。**

### 11-2　Bulk memory：一個常被忽略的巨大免費午餐

```c
// ❌ 逐位元組迴圈：每個位元組一條 load + 一條 store
for (size_t i = 0; i < n; i++) dst[i] = src[i];

// ✅ 編譯成 memory.copy 單一指令 → 引擎映射到宿主的 memcpy（SIMD 化、對齊優化過）
memcpy(dst, src, n);
```

**`memory.copy` / `memory.fill` 是 Wasm 2.0 起的核心指令**，引擎會把它們直接映射到高度優化的原生 `memcpy`/`memset`。**大區塊搬移的差距可以是一個量級。** 確認你的工具鏈開了 bulk memory（現代工具鏈預設開啟）。

### 11-3　其他 codegen 層面的槓桿

| 特性 | 收益 | 備註 |
|---|---|---|
| **分支提示**（Wasm 3.0） | 讓引擎把熱路徑排在 fall-through | 由 PGO 或 `likely()` 標註驅動 |
| **尾呼叫** `return_call` | 深遞迴不爆棧，且省下堆疊框 | 直譯器、狀態機受益最大 |
| **Multi-value** | 多回傳值不必經過記憶體 | 減少 load/store 往返 |
| **Relaxed SIMD** 的 `relaxed_madd` | 映射到硬體 FMA | ⚠️ **犧牲確定性**（附錄 M §7） |
| **具型別函數參考**（Wasm 3.0） | 間接呼叫省下執行期簽章檢查 | 虛擬函數密集的 C++/OOP 受益 |

---

## 十二、穩態效能之二：記憶體與快取

**第 6 章說過那個關鍵事實：L1 命中約 4 個週期，DRAM 存取約 200 個週期。** 所以記憶體佈局的影響常常壓過指令層面的優化。

### 12-1　SoA 而不是 AoS

```rust
// ❌ AoS：算 x 的平均值也要把 y、z 拖進快取
struct Particle { x: f32, y: f32, z: f32, vx: f32, vy: f32, vz: f32 }
let particles: Vec<Particle>;

// ✅ SoA：只掃 xs，完美的快取局部性，也是自動向量化的前提
struct Particles { xs: Vec<f32>, ys: Vec<f32>, zs: Vec<f32>, /* ... */ }
```

### 12-2　Arena / bump 配置器

**在 Wasm 裡 `malloc` 相對昂貴**（它是編譯進來的一份使用者空間實作，沒有作業系統幫忙）。**如果你的配置模式是「處理一幀 / 一個請求時分配一堆，結束後全部丟掉」，bump 配置器是壓倒性的贏家**：

```rust
struct Bump { buf: Vec<u8>, top: usize }
impl Bump {
    #[inline] fn alloc(&mut self, n: usize, align: usize) -> *mut u8 {
        let p = (self.top + align - 1) & !(align - 1);
        self.top = p + n;                       // 分配 = 一次加法
        unsafe { self.buf.as_mut_ptr().add(p) }
    }
    #[inline] fn reset(&mut self) { self.top = 0; }   // 釋放全部 = 一次賦值
}
```

**它同時是體積優化**（可以搭配 `-sMALLOC=none` 或極小配置器）**與效能優化**。

### 12-3　三個具體陷阱

| 陷阱 | 說明 |
|---|---|
| **熱路徑上的 `memory.grow`** | 會使所有既有 `TypedArray` 視圖失效，且可能觸發一次大的記憶體重新映射。**預先配置好上限，別讓它在迴圈裡長。** |
| **對齊提示** | `i32.load align=2` 是**提示**不是保證——宣告錯不會 trap，但引擎可能因此產出較慢的碼。**讓編譯器自己填。** |
| **跨頁的隨機存取** | 線性記憶體很大時，隨機存取會頻繁 TLB 未命中。**能排序就排序，能分塊就分塊。** |

---

## 十三、穩態效能之三：邊界

**第 2 章說「邊界是收費站」，這裡給實際的減費手段。**

```javascript
// ❌ 每次都配置一個新的 Uint8Array 來編碼字串
const bytes = new TextEncoder().encode(str);
const ptr = wasm.alloc(bytes.length);
new Uint8Array(wasm.memory.buffer, ptr, bytes.length).set(bytes);

// ✅ encodeInto 直接寫進 Wasm 記憶體，零中間配置
const view = new Uint8Array(wasm.memory.buffer, ptr, cap);
const { written } = new TextEncoder().encodeInto(str, view);
```

**五條規則**：

1. **批次化**：`process_image(ptr, w, h)` 而不是 `process_pixel()` 一百萬次。
2. **`encodeInto` / `decode` 重用視圖**，避免每次配置。
3. **結果用環形緩衝回傳**，而不是每次事件一個回呼（物理引擎、遊戲迴圈的標準做法）。
4. **`externref` 持有 JS 物件**，避免自建「JS 物件 ↔ 整數 handle」的側表（那張表的維護成本與洩漏風險都不低）。
5. **量測跨界次數本身**：在膠水裡加一個計數器，你會經常發現它比你以為的多一個量級。

---

## 十四、穩態效能之四：並行

```javascript
// Worker pool + SharedArrayBuffer（需跨來源隔離，見第 5 章）
const mem = new WebAssembly.Memory({ initial: 256, maximum: 4096, shared: true });
// 每個 Worker 用同一個 Module + 同一塊 shared memory 實例化
```

**三個實務要點**：

1. **Worker 數量用 `navigator.hardwareConcurrency`，但要留餘裕**（主執行緒還要渲染）。實務上常用 `max(1, hc - 1)`。
2. **主執行緒不能 `Atomics.wait`**（規範禁止），要用 **`Atomics.waitAsync`**。
3. **工作切分的粒度**要大到蓋過同步成本——**太細的並行比單執行緒還慢**，這在 Wasm 上比在原生上更明顯，因為跨 Worker 的協調要經過 JS。

**如果資料可切分，回頭看第 8 章情境 3**：**多實例隔離不需要跨來源隔離**，往往是更划算的並行路徑。

---

## 十五、量測：一個會讓你量錯的陷阱

**⚠️ 沒有跨來源隔離時，`performance.now()` 的解析度會被降低。**

這是 Spectre 餘波的另一個後果（第 3 章）：**未隔離的頁面上，計時器解析度被粗化**（各家實作不同，常見量級是數十到上百微秒），**而隔離之後才會恢復到微秒級**。

**這意味著**：

- 量測微秒級的操作（單次跨界呼叫、小函數）**在未隔離的頁面上根本量不準**。
- **不要用單次 `performance.now()` 差值去量小操作**——跑一萬次取總時間再除。
- 比較兩份建置時，**確認兩邊的隔離狀態相同**，否則你比較的是計時器精度而不是程式碼。

```javascript
// 正確的微基準形狀
function bench(fn, iters = 100_000) {
  fn(); fn(); fn();                       // 預熱（讓 TurboFan 完成 tier-up）
  const t0 = performance.now();
  for (let i = 0; i < iters; i++) fn();
  return (performance.now() - t0) / iters; // 平均單次
}
```

**剖析工作流**（附錄 M §10 已述，這裡補三條）：

- **保留 `name` 區段**，否則火焰圖只有 `wasm-function[1234]`（`wasm-opt --strip-debug` 保留 name、只剝 DWARF）。
- **後端用 `perf`**：Wasmtime 支援輸出 perf/jitdump 對應資訊，可以看到 Wasm 函數名。
- **量「跨界次數」與「配置次數」**，不要只量時間——它們才是可以直接行動的指標。

---

## 十六、效能優化投報率總表

| # | 手段 | 典型收益 | 何時做 |
|---|---|---|---|
| 0 | **確認瓶頸是啟動還是穩態** | — | **最先做**（兩者的武器完全不同） |
| 1 | `instantiateStreaming` + 正確 MIME | 省一整趟下載時間 | 一定做 |
| 2 | **降低體積**（第一部） | 直接縮短 ①② 段 | 一定做 |
| 3 | 穩定 URL → 程式碼快取 | 回訪快一個量級 | 一定做 |
| 4 | **把邊界做粗** | 常見 2–10 倍 | **測到跨界密集就做** |
| 5 | Module 結構化複製給 N 個 Worker | 省 N−1 次編譯 | 用多 Worker 時 |
| 6 | SoA + arena 配置器 | 常見 2–5 倍 | 資料密集時 |
| 7 | `memcpy` 取代逐位元組迴圈 | 大區塊可達一個量級 | 一定檢查 |
| 8 | SIMD（`-msimd128` + 手寫 intrinsics） | 2–4 倍 | 數值密集時 |
| 9 | **Wizer 預初始化** | 實例化+初始化 1.35–6 倍 | 初始化重的後端/CLI |
| 10 | 後端 AOT（`wasmtime compile`） | 執行期零編譯 | 伺服器端 |
| 11 | 多執行緒 | ≤ 核心數 | **最後才做**（複雜度與隔離代價最高） |

---

## 十七、反模式清單

| 反模式 | 為什麼錯 |
|---|---|
| 沒量測就開始調旗標 | 八成調錯地方（Data 區段佔一半時，壓 Code 沒用） |
| 同時要 `opt-level="z"` 與 SIMD 自動向量化 | **`-Oz` 關掉向量化**，兩者互斥 |
| 把 Wasm 當「更快的函式庫」逐函數替換 JS | 每個函數變快，整體變慢——**跨界次數暴增** |
| 在熱迴圈裡呼叫 JS | 每次都是收費站；把迴圈整個搬進 Wasm |
| 用 `wee_alloc` 圖體積 | **已不再維護且有已知問題** |
| 在未隔離的頁面上量微秒級操作 | **計時器被降精度**，你量的是雜訊 |
| 啟動後立刻跑基準測試 | 量到的是 Liftoff 的未最佳化碼 |
| 把 30 MB 模型權重打包進 `.wasm` | 它應該是可快取的資產，不是程式碼 |
| 為了更新體積而過度切割模組 | **壓縮字典傳輸**（§7-2）可能已經解決了這個問題，而切割的代價還在 |
| 發布版無腦 `strip` 掉全部符號 | 線上崩潰時你什麼都查不到——**保留一份帶符號的建置** |

---

## 附：與正文的對照索引

| 主題 | 本附錄 | 正文背景 |
|---|---|---|
| 體積的解剖與工具 | §1 | 第 3 章牆三、第 8 章 |
| Rust 的隱藏肥肉 | §2-2、§2-3 | 第 3 章牆九 |
| `wasm-opt` 內部 | §3 | 第 8 章 |
| 資料才是大宗 | §6 | 第 8 章第 0 條、附錄 L |
| Brotli 與差分更新 | §7 | 第 2 章、附錄 M §9 |
| 啟動四段 | §10 | 第 2 章情境 3 |
| Wizer | §10-2 | 第 2 章、附錄 M |
| SIMD 的真實天花板 | §11-1 | 第 2 章 🔍、第 4 章 |
| 邊界減費 | §13 | 第 2 章情境 4 |
| 計時器精度陷阱 | §15 | 第 3 章牆六、第 5 章 |
| 把體積與效能寫進 CI 守門 | — | **附錄 O §5** |
