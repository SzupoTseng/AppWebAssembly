# 附錄M　規範深水區：十二個常被跳過的技術細節

> 正文為了敘事流暢，很多地方只講到「它是這樣運作的」就停住了。這一份附錄把那些停住的地方繼續往下挖。
> **它不是入門材料，是查閱材料**——當你在實作中撞到某個具體問題時再翻進來。
>
> ⚠️ **版本前提**：本附錄以 **WebAssembly 3.0**（2025 年 9 月宣布完成）為基準。**在 3.0 之前寫成的資料會把 GC、Memory64、例外處理、尾呼叫、多重記憶體稱為「提案」——那些敘述已經過時。**

---

## 一、把一個 `.wasm` 逐位元組拆開

### 1-1　LEB128：為什麼所有長度都是變長的

Wasm 的所有整數欄位（區段長度、索引、常數）都用 **LEB128（Little Endian Base 128）** 編碼——每個位元組用低 7 位存資料、最高位當「還有後續」的續行旗標。

```
無號 LEB128：
  值 624485 (0x98765)
  → 二進位 1001 1000 0111 0110 0101
  → 每 7 位一組（由低到高）：1100101  1110110  0100110
  → 加續行位：11100101  11110110  00100110
  → 位元組   E5        F6        26

小的數字只佔 1 個位元組（0–127），這正是重點：
  絕大多數索引與長度都很小，變長編碼讓整個模組顯著縮小。
```

**有號版本（sLEB128）** 用於 `i32.const` / `i64.const` 這類常數，最後一組要做符號擴展。

> **實務意義**：這解釋了兩件事——**（一）** 為什麼 Wasm 二進位比同等的定長格式小得多；**（二）** 為什麼你**不能**用固定偏移量去 patch 一個 `.wasm`——改一個數字可能讓它的位元組數變了，後面全部要重算。**想改二進位，用 Binaryen 或 WABT，別自己動手。**

### 1-2　區段的通用結構

```
┌────────┬──────────────┬──────────────────────────┐
│ id (1) │ size (u32 LEB)│ contents (size 個位元組)  │
└────────┴──────────────┴──────────────────────────┘
```

**`size` 存在的價值**：解析器可以**跳過**任何它不認識的區段（特別是 Custom Section）。這是 Wasm 向前相容的基石——一個舊引擎遇到新版工具鏈塞進去的自訂中繼資料，只要跳過去就好。

### 1-3　型別編碼

| 值型別 | 位元組 |
|---|---|
| `i32` | `0x7F` |
| `i64` | `0x7E` |
| `f32` | `0x7D` |
| `f64` | `0x7C` |
| `v128` | `0x7B` |
| `funcref` | `0x70` |
| `externref` | `0x6F` |
| 函數型別（functype）前綴 | `0x60` |

**注意這些都是負數的 sLEB128 編碼**（`0x7F` = −1、`0x7E` = −2……）。這不是巧合：**正數留給了「型別索引」**，於是 GC 要引入 `(ref $MyStruct)` 這種指向使用者定義型別的參考時，編碼空間早就預留好了。**2015 年那個「刻意做小」的規格，在型別編碼上留了門。**

### 1-4　完整走一遍：一個 `add` 函數

```wat
(module
  (func $add (param i32 i32) (result i32)
    local.get 0
    local.get 1
    i32.add)
  (export "add" (func $add)))
```

```
00 61 73 6D            魔數 \0asm
01 00 00 00            版本 1

01 07                  Type 區段 (id=1)，長度 7
   01                    1 個型別
   60                    functype
   02 7F 7F              2 個參數：i32, i32
   01 7F                 1 個結果：i32

03 02                  Function 區段 (id=3)，長度 2
   01 00                 1 個函數，用型別 #0

07 07                  Export 區段 (id=7)，長度 7
   01                    1 個匯出
   03 61 64 64           名稱長度 3："add"
   00 00                 kind=func(0x00)，索引 0

0A 09                  Code 區段 (id=10)，長度 9
   01                    1 個函數本體
   07                    本體長度 7
   00                    ★ 區域變數宣告：0 組
   20 00                 local.get 0
   20 01                 local.get 1
   6A                    i32.add
   0B                    ★ end（每個函數本體都以 0x0B 結尾）
```

> **正文第 2 章說「五個位元組」指的是 `20 00 20 01 6A` 這段指令序列。** 完整的函數本體還要加上前面的區域變數宣告 `00` 與結尾的 `0B`——**這兩個位元組是規範強制的，任何手工組裝二進位的人第一次都會漏掉 `0x0B`。**

### 1-5　常用指令碼速查

| 指令 | 碼 | 指令 | 碼 |
|---|---|---|---|
| `unreachable` | `0x00` | `end` | `0x0B` |
| `nop` | `0x01` | `br` | `0x0C` |
| `block` | `0x02` | `br_if` | `0x0D` |
| `loop` | `0x03` | `br_table` | `0x0E` |
| `if` | `0x04` | `return` | `0x0F` |
| `else` | `0x05` | `call` | `0x10` |
| `drop` | `0x1A` | `call_indirect` | `0x11` |
| `select` | `0x1B` | `local.get` | `0x20` |
| `i32.load` | `0x28` | `local.set` | `0x21` |
| `i32.store` | `0x36` | `local.tee` | `0x22` |
| `memory.size` | `0x3F` | `global.get` | `0x23` |
| `memory.grow` | `0x40` | `i32.const` | `0x41` |
| `i32.add` | `0x6A` | `i32.sub` | `0x6B` |

**SIMD 與部分新指令使用前綴碼**（`0xFD` 為 SIMD 前綴、`0xFC` 為 bulk memory/saturating 轉換前綴），後接一個 LEB128 的子指令碼。

---

## 二、驗證演算法：多型堆疊與那個很聰明的技巧

第 2 章說驗證器會做「堆疊型別一致性」檢查。**但有一個情況會讓天真的實作卡住**：

```wat
(func (result i32)
  unreachable       ;; 到這裡控制流就終止了
  i32.add)          ;; ← 堆疊上什麼都沒有，但這行怎麼驗證？
```

`unreachable` 之後的程式碼**永遠不會執行**，可是驗證器仍然必須對它做出判斷（因為它必須是單趟、線性、不做可達性分析的）。

**規範的解法是「多型堆疊（polymorphic stack）」**：進入 unreachable 狀態後，驗證器把堆疊標記為「**可以提供任意數量、任意型別的值**」。於是 `i32.add` 要兩個 `i32`，多型堆疊就給它兩個 `i32`；下一個指令要三個 `f64`，也照給。**這樣任何在死程式碼裡的指令序列都能通過驗證，而不需要編譯器去證明它不可達。**

```
驗證狀態機（簡化）：
  正常狀態  ── unreachable / br / return / br_table ──▶ 多型狀態
  多型狀態  ── 遇到 end 或該區塊的邊界 ─────────────▶ 恢復為該區塊的宣告型別
```

> 💡 **這是「讓驗證保持在 O(n) 單趟」這個設計目標的直接產物。** 如果驗證器必須先做可達性分析才能檢查型別，它就不再是單趟的了，而串流編譯（邊下載邊編譯）也就不成立。**一個看起來像特例的規則，往往是為了保住某個更根本的性質。**

---

## 三、`call_indirect`、表，與 C++ 虛擬函數在 Wasm 裡的樣子

### 3-1　函數指標是怎麼實作的

Wasm **沒有函數指標**——你不能把一個函數的位址存進線性記憶體。取而代之的是**表（Table）**：

```wat
(module
  (type $binop (func (param i32 i32) (result i32)))
  (table 4 funcref)                      ;; 一張有 4 格的函數表
  (elem (i32.const 0) $add $sub $mul $div)  ;; 填入四個函數

  (func $apply (param $op i32) (param $a i32) (param $b i32) (result i32)
    local.get $a
    local.get $b
    local.get $op
    call_indirect (type $binop)))        ;; ★ 依索引呼叫，並檢查簽章
```

**在 C/C++ 編譯出來的 Wasm 裡，「函數指標」其實是一個 `i32` 表索引。** 這解釋了一個常見的困惑：**為什麼 Wasm 裡的函數指標可以安全地存在線性記憶體裡？** 因為它只是一個索引——就算被緩衝區溢位改成任意值，最壞的結果也只是 `call_indirect` 找到一個簽章不符的項目而 **trap**，**而不是跳到攻擊者控制的位址執行任意程式碼**。

### 3-2　`call_indirect` 的執行期檢查

```
call_indirect (type $sig) 執行時：
  1. 從堆疊彈出索引 i
  2. 若 i 超出表的範圍           → trap「undefined element」
  3. 若 table[i] 為 null         → trap「uninitialized element」
  4. 若 table[i] 的實際簽章 ≠ $sig → trap「indirect call type mismatch」
  5. 通過 → 呼叫
```

**第 4 步是每次呼叫都要付的執行期成本。** 這正是 Wasm 3.0 **具型別的函數參考（typed function references）** 要解決的問題——用 `(ref $sig)` 這種帶型別的參考，**簽章在型別系統層面就已經確定，執行期不必再比對**。對虛擬函數呼叫密集的 C++ / OOP 語言，這是實質的效能改善。

### 3-3　C++ 虛擬函數的真實樣貌

```
class Shape { virtual double area(); };

編譯到 Wasm 之後：
  ┌ 線性記憶體 ────────────────────┐
  │ Shape 物件：                    │
  │   +0  vptr → 指向 vtable 的位址  │   ← vptr 是線性記憶體位址
  │   +4  成員…                     │
  │                                 │
  │ vtable（也在線性記憶體裡）：      │
  │   +0  area 的【函數表索引】(i32) │   ← ★ 不是函數位址，是表索引
  └────────────────────────────────┘
              ↓
  函數表 (funcref)：[ …, Shape::area, Circle::area, … ]
```

**於是一次虛擬呼叫是：讀 vptr → 讀 vtable 項目（得到 i32 索引）→ `call_indirect`。**

> **這也是逆向工程 Wasm 時的一個關鍵著力點**（第 9 章）：`elem` 區段列出了所有可被間接呼叫的函數，而 vtable 的佈局可以從 `call_indirect` 的使用模式反推出來。**類別結構被抹掉了，但呼叫圖的形狀還在。**

---

## 四、例外處理：Tag 區段與 `exnref`

**Wasm 3.0 把例外處理收進了核心規範。** 它的機制值得看，因為它跟你熟悉的 try/catch 不太一樣。

### 4-1　Tag：例外的「型別」

例外不是物件，是一個 **tag（標籤）+ 一組 payload 值**。Tag 宣告在 **Tag 區段（id = 13）**：

```wat
(module
  ;; 宣告一個例外標籤，攜帶一個 i32 payload
  (tag $oom (param i32))

  (func $alloc (param $n i32) (result i32)
    ...
    (throw $oom (local.get $n)))         ;; 丟出，帶著 n
)
```

### 4-2　`try_table`：3.0 的新形式

早期提案用 `try` / `catch` / `delegate` 的區塊結構；**Wasm 3.0 採用的是 `try_table` + `exnref`**——把「捕捉」變成一種**分支**，而不是一種巢狀區塊：

```wat
(func $safe (result i32)
  (block $handler (result i32)
    (try_table (catch $oom $handler)     ;; 若丟出 $oom，帶著 payload 跳到 $handler
      (call $alloc (i32.const 1000000))
      (br 1))                            ;; 沒丟出例外 → 跳過 handler
  )
  ;; $handler：堆疊上是 $oom 的 payload (i32)
)
```

**`exnref`** 是一個不透明的例外參考型別，讓你可以捕捉「任意例外」再重新丟出（`catch_all_ref` + `throw_ref`）——這是實作 `finally` 與跨語言例外傳遞所必需的。

### 4-3　為什麼這件事對效能很重要

**在原生的例外處理出現之前**，C++ 的 `try/catch` 編譯到 Wasm 只有兩條路：

| 舊解法 | 代價 |
|---|---|
| `-fno-exceptions` | 整個生態有一半的函式庫不能用 |
| **JavaScript 蹦床（trampoline）** | 每一次 `try` 進入都要跨界到 JS 再跨回來——**開銷極大，且讓 JS 引擎無法內聯** |

**原生 EH 之後**，`try_table` 是一條純 Wasm 指令，引擎可以完整優化。**這是 Wasm 3.0 對 C++ 生態最直接的一次補血。**

---

## 五、JSPI 深入：Wasm 如何「等」一個 Promise

第 3 章介紹了 JSPI 的用途，這裡看它的機制與代價。

### 5-1　它到底做了什麼

```
一般情況：
  JS ──call──▶ Wasm ──call──▶ 匯入的 JS 函數（回傳 Promise）
                                  ↓
                            Wasm 拿到一個 Promise 物件，
                            但它不知道怎麼「等」——只能立刻繼續執行 ❌

JSPI：
  JS ──promising(f)──▶ Wasm ──call──▶ Suspending 包裝過的匯入
                                          ↓
                       ★ 引擎把整個 Wasm 執行堆疊（連同區域變數、
                         呼叫鏈）掛起，搬到一旁，並回傳一個 Promise 給 JS
                                          ↓
                            事件迴圈繼續跑（分頁不凍結）
                                          ↓
                            Promise 解決 → 引擎把堆疊恢復，
                            把結果推回運算元堆疊，從掛起處繼續 ✅
```

### 5-2　API 形狀

```javascript
// 1. 匯入側：把回傳 Promise 的函數包成「可掛起的」
const imports = {
  env: {
    read_file: new WebAssembly.Suspending(async (ptr, len) => {
      const handle = await root.getFileHandle("data.bin");
      const file = await handle.getFile();
      const buf = new Uint8Array(await file.arrayBuffer());
      new Uint8Array(memory.buffer, ptr, buf.length).set(buf);
      return buf.length;               // Wasm 眼中就是一個同步回傳值
    }),
  },
};

// 2. 導出側：把入口包成「會回傳 Promise 的」
const { instance } = await WebAssembly.instantiateStreaming(fetch("app.wasm"), imports);
const main = WebAssembly.promising(instance.exports.main);
await main();                          // 對 JS 而言是 async
```

**Rust 側幾乎不用改**：

```rust
extern "C" { fn read_file(ptr: *mut u8, len: usize) -> usize; }

pub fn load() -> Vec<u8> {
    let mut buf = vec![0u8; 4096];
    let n = unsafe { read_file(buf.as_mut_ptr(), buf.len()) };  // 看起來就是同步呼叫
    buf.truncate(n);
    buf
}
```

### 5-3　三個必須知道的代價

1. **掛起／恢復不是免費的。** 每次掛起都要把整條 Wasm 堆疊搬走再搬回來，成本與堆疊深度相關。**適合「偶爾等一次 I/O」，放進熱迴圈會很痛。**
2. **它不是並行。** 掛起期間那條 Wasm 執行緒什麼都沒做——**你只是把等待的時間讓給了事件迴圈，不是同時做了兩件事。**
3. **重入問題。** 掛起期間，JS 可能再次呼叫同一個 Wasm 實例的導出函數。**如果你的 C 程式碼假設「同一時間只有一個呼叫在跑」（絕大多數 C 程式碼都這樣假設），這會造成狀態損壞。** 需要自己加一層重入鎖。

### 5-4　與 Asyncify 的對照

| | Asyncify | JSPI |
|---|---|---|
| 機制 | Binaryen **改寫整個模組**，用線性記憶體手動保存/還原堆疊 | **引擎原生**掛起 Wasm 堆疊 |
| 體積影響 | **顯著膨脹** | 無 |
| 執行開銷 | 全域性的（改寫後的程式碼一直帶著保存/還原邏輯） | 只在實際掛起時付 |
| 需要標註 | 要指定哪些函數會 unwind，漏標就出錯 | 不需要 |
| 相容性 | 到處都能用 | 需要引擎支援（**Chrome 137+／Firefox 139+**） |

**遷移策略**：偵測 `typeof WebAssembly.Suspending === "function"`，有就用 JSPI，沒有就退回 Asyncify 建置。

---

## 六、原子操作與記憶體模型

### 6-1　指令家族

```wat
;; 原子讀寫
i32.atomic.load / i32.atomic.store
i64.atomic.load8_u / ...（各種寬度）

;; 讀-改-寫（RMW），全部是單一原子操作
i32.atomic.rmw.add / sub / and / or / xor / xchg / cmpxchg

;; 阻塞與喚醒（futex 語意）
memory.atomic.wait32   (addr, expected, timeout_ns) -> i32
memory.atomic.notify   (addr, count) -> i32

;; 記憶體屏障
atomic.fence
```

### 6-2　三條必須記住的語意

1. **所有原子操作都是循序一致（sequentially consistent）的。** Wasm **沒有** C++ 那種 `memory_order_relaxed` / `acquire` / `release` 的分級——規範只提供最強的那一種。**好處是不會寫錯，代價是拿不到弱序帶來的效能。**
2. **非原子存取沒有任何順序保證。** 兩條執行緒對同一位址的非原子讀寫是資料競爭；規範定義了它不會破壞沙盒，但**值是什麼沒有保證**。
3. **`memory.atomic.wait` 在主執行緒上會 trap。** 主執行緒不允許阻塞——**這是規範層面的禁止，不是慣例。** 所以任何用到 `wait` 的同步原語都只能在 Worker 裡跑（這也正是 SQLite 第一代 `opfs` VFS 必須有 Worker 的原因）。

### 6-3　一個實用的推論

**`memory.atomic.wait32` + `notify` 就是 futex，而 futex 足以實作出所有的同步原語**——mutex、條件變數、號誌、屏障。這正是 Emscripten 能把 `pthread` 完整映射過來的底層基礎。

---

## 七、Relaxed SIMD 的不確定性清單

Wasm 3.0 收進了 relaxed SIMD，它用**放棄確定性**換取更好的硬體映射。**在鏈上、在需要跨機器重現結果的科學計算裡，這些指令必須禁用。**

| 指令族 | 不確定性從何而來 |
|---|---|
| `relaxed_madd` / `relaxed_nmadd` | 可能用 FMA（單次捨入）也可能用 mul+add（兩次捨入）——**浮點結果會差在最後幾位** |
| `relaxed_min` / `relaxed_max` | **NaN 與 ±0 的處理方式因平台而異** |
| `relaxed_swizzle` | 索引超出範圍時，回傳 0 或未定義值，**因平台而異** |
| `relaxed_trunc_*` | 浮點轉整數時，超界或 NaN 的結果**因平台而異** |
| `relaxed_dot` | 累加順序與飽和行為可能不同 |
| `relaxed_laneselect` | 遮罩非全 0/全 1 時行為未定 |

**判斷準則**：**只要你的輸出會被拿去做雜湊、簽章、共識、或跨機器比對，就不要用 relaxed SIMD。** 影像濾鏡、遊戲物理、機器學習推理這類「差幾個 ULP 沒人看得出來」的場景才適合。

---

## 八、多重記憶體（Wasm 3.0）

```wat
(module
  (memory $a 1)
  (memory $b 1)

  ;; 載入/儲存指令帶記憶體索引
  (func $get (result i32) (i32.load $b (i32.const 0)))

  ;; memory.copy 可跨記憶體：dst_mem, src_mem
  (func $move (memory.copy $a $b (i32.const 0) (i32.const 0) (i32.const 1024)))

  ;; 各自獨立成長
  (func $grow_b (result i32) (memory.grow $b (i32.const 16))))
```

**三個典型用法**：

| 用法 | 好處 |
|---|---|
| **程式碼區 / 資料區分離** | 大型資產不再擠壓工作區的位址空間 |
| **多租戶各一塊** | 一個模組服務多個租戶，記憶體天然隔離 |
| **冷熱分離** | 熱資料留在小塊記憶體裡，快取局部性更好 |

**最大的價值**（第 8 章情境 4 已述）：**每塊記憶體仍是 wasm32，因此保護頁的免費界檢查完整保留**——這是 Memory64 做不到的。

**現實限制**：**工具鏈支援落後於規範。** 多數 C/C++/Rust 工具鏈預設假設「只有一塊記憶體」。

---

## 九、部署層：五件會讓你在正式環境翻車的事

### 9-1　MIME 型別

```
Content-Type: application/wasm
```

**沒有這個，`instantiateStreaming` 會直接拒絕。** GitHub Pages 對 `.wasm` 副檔名會正確回傳。

### 9-2　CSP

```http
Content-Security-Policy: script-src 'self' 'wasm-unsafe-eval'
```

Wasm 編譯在 CSP 眼中屬於動態程式碼產生。`'wasm-unsafe-eval'`（Chrome 97+／Firefox 102+／Safari 16+）**只放行 Wasm，不放行 `eval()`**。

### 9-3　完整性驗證（SRI 的空白）

**這是一個真實的生態缺口**：`<script integrity="sha384-…">` 對 `<script>` 有效，**但 `fetch()` 載入的 `.wasm` 沒有內建的 SRI 機制**。想驗證得自己來：

```javascript
async function loadVerified(url, expectedSha256Base64) {
  const bytes = await (await fetch(url)).arrayBuffer();
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const actual = btoa(String.fromCharCode(...new Uint8Array(digest)));
  if (actual !== expectedSha256Base64) throw new Error("wasm integrity mismatch");
  return WebAssembly.instantiate(bytes, imports);   // ⚠️ 代價：放棄串流編譯
}
```

> **注意這裡有一個取捨**：要驗雜湊就得先拿到完整位元組，**於是你失去了串流編譯**（第 2 章）。**安全與啟動速度在這裡直接對撞**，沒有兩全的解法。多數團隊的選擇是：**同源託管 + 建置流程可重現 + CDN 的 TLS**，而不是執行期驗雜湊。

### 9-4　壓縮

```
Content-Encoding: br
```

**Wasm 的 Brotli 壓縮率通常很好**——附錄 L 的實例是 3.6 MB → 0.8 MB（約 4.5 倍）。**這是投報率最高的一行伺服器設定。**

> **為什麼 Wasm 特別適合 Brotli，以及如何用「壓縮字典傳輸」讓改版只傳幾十 KB——見附錄 N §7。**

### 9-5　程式碼快取與 Worker 共享

**兩個常被忽略的加速手段**：

```javascript
// (1) 編譯一次，多個 Worker 共用
//     WebAssembly.Module 是可結構化複製的，postMessage 過去不會重新編譯
const mod = await WebAssembly.compileStreaming(fetch("app.wasm"));
for (const w of workers) w.postMessage({ mod });          // ★ 省下 N-1 次編譯

// Worker 內：
self.onmessage = async ({data}) => {
  const inst = await WebAssembly.instantiate(data.mod, imports);  // 直接實例化
};
```

```
(2) 瀏覽器的磁碟程式碼快取：
    Chrome 會把 TurboFan 的產物寫進 HTTP 快取，鍵是 URL。
    → 給 .wasm 一個穩定的 URL（帶內容雜湊的檔名最佳）
    → 回訪時可跳過整個編譯階段，大型模組的第二次載入常快一個量級
```

---

## 十、效能剖析工作流

**很多人以為 Wasm 沒辦法剖析，其實可以，只是需要準備。**

```bash
# 1. 保留 name 自訂區段（否則你只會看到 wasm-function[1234]）
#    Rust：發布版不要無腦 strip = true，改用 wasm-opt 只剝 debug
wasm-opt -O3 --strip-debug --strip-producers app.wasm -o app.wasm
#                ↑ 保留 name section，只剝 DWARF

# 2. Emscripten：明確保留函數名
emcc -O3 --profiling-funcs ...
```

**接著在 Chrome DevTools 的 Performance 面板錄製**——Wasm 的框架會以函數名出現在火焰圖裡，與 JS 框架混合顯示。**這讓「時間花在跨界還是花在計算」變成一個可以直接看出來的問題。**

**三個最常見的剖析結論，以及它們的長相**：

| 火焰圖長相 | 診斷 |
|---|---|
| 大量細碎的 JS↔Wasm 交錯條 | **邊界穿越太頻繁**（第 2 章）——把介面做粗 |
| Wasm 框架寬但內部平坦 | 真的在計算——考慮 SIMD 或演算法 |
| `__wbindgen_malloc` / `free` 佔比高 | **分配太多**——改用記憶體池或重用緩衝區 |

**進階**：`performance.mark()` / `measure()` 可以從 Wasm 側透過匯入呼叫進去，讓自訂區段出現在時間軸上。

---

## 十一、proxy-wasm：Wasm 在基礎設施層的標準 ABI

**這是第 4 章「多租戶外掛系統」那一段的具體長相**，也是 Wasm 在後端最成功的落地形態之一。

**proxy-wasm** 是一套為網路代理設計的 Wasm ABI，被 **Envoy、Istio、Kong、APISIX、Higress** 等採用。它定義了一組宿主與模組之間的回呼：

```
模組導出（宿主呼叫模組）：
  proxy_on_context_create(context_id, parent_id)
  proxy_on_request_headers(context_id, num_headers, end_of_stream)
  proxy_on_request_body(context_id, body_size, end_of_stream)
  proxy_on_response_headers(...)
  proxy_on_log(context_id)
  proxy_on_tick(context_id)

宿主導出（模組呼叫宿主）：
  proxy_get_header_map_value(...)
  proxy_set_header_map_pairs(...)
  proxy_send_local_response(...)   ← 直接回應，不轉發到上游
  proxy_get_shared_data / proxy_set_shared_data
  proxy_http_call(...)             ← 對外發 HTTP（例如查鑑權服務）
```

**它為什麼是 Wasm 的甜蜜點**（回到第 4 章的判斷）：

- **多租戶**：一個 Envoy 程序裡可以跑上百個互不信任的客戶外掛，各有獨立的線性記憶體與能力邊界。**用容器做這件事是不可能的。**
- **熱更新**：換一個 `.wasm` 就換一套邏輯，不用重啟代理。
- **語言無關**：客戶用 Rust、Go、AssemblyScript 都行。

> **這正是第 4 章那句話的證據**：**Wasm 不會從既有服務手上搶市場，它會在那些容器結構上進不去的地方長出自己的地盤。**

---

## 十二、程式碼分割與延遲載入

**當模組大到必須切開時**，有兩條路：

### 12-1　`wasm-split`（Emscripten / Binaryen）

把一個模組切成**主模組 + 次模組**，主模組先載入，次模組在第一次呼叫到時才抓。

```bash
# 先用剖析取得「啟動時真正用到的函數」清單
wasm-split app.wasm -o1 primary.wasm -o2 secondary.wasm \
  --profile=startup.prof --keep-funcs=@startup-funcs.txt
```

**適合**：啟動路徑明確、大部分功能是「使用者可能永遠不會點」的應用。

### 12-2　手動切成多個獨立模組

```javascript
// 首屏只載核心
const core = await WebAssembly.instantiateStreaming(fetch("core.wasm"), imports);

// 使用者點了「匯出 PDF」才載
button.onclick = async () => {
  const pdf = await WebAssembly.instantiateStreaming(fetch("pdf.wasm"), {
    env: { memory: core.instance.exports.memory },   // ★ 共用同一塊線性記憶體
  });
  pdf.instance.exports.export_pdf(ptr, len);
};
```

**關鍵細節**：兩個模組**共用同一塊線性記憶體**（把 memory 從一邊 export、另一邊 import），這樣資料不需要複製。**Tesseract 的語言包、Pyodide 的 `micropip` 都是這個形狀。**

---

## 附：本附錄與正文的對照索引

| 你想知道 | 看這裡 | 正文背景 |
|---|---|---|
| 二進位到底長怎樣 | 本附錄 §1 | 第 2 章情境 1 |
| 為什麼驗證能單趟完成 | §2 | 第 2 章情境 1 |
| 函數指標與虛擬函數 | §3 | 第 2 章、第 9 章（逆向） |
| C++ 例外的代價 | §4 | 第 1 章（技術債）、第 3 章 |
| 同步程式碼怎麼等非同步 API | §5 | 第 3 章牆七、第 7 章、附錄 L |
| 多執行緒的底層原語 | §6 | 第 3 章牆六、第 5 章 |
| 哪些 SIMD 指令不能用在鏈上 | §7 | 第 4 章（EVM 確定性） |
| 4GiB 的第三條出路 | §8 | 第 8 章情境 4 |
| 正式環境部署清單 | §9 | 第 5 章、附錄 C |
| 怎麼剖析 Wasm | §10 | 第 3 章牆八 |
| Wasm 在後端真正贏的地方 | §11 | 第 4 章情境 2 |
| 模組太大怎麼辦 | §12 | 第 8 章 |
