# 附錄O　測試、CI 與執行期安全

> 這是本書最後補上的一塊，而它補的是一個很尷尬的洞：**前面那十四份附錄教你怎麼把 Wasm 做出來、做小、做快、做得不被抄走——卻沒有一份告訴你怎麼確認它是對的。**
>
> 第 3 章說過一句話：**「評估一項技術的成熟度，最準的指標不是它跑多快，是它壞掉的時候有多容易查。」** 這份附錄就是那句話的操作手冊。

---

## 一、Wasm 測試的三層金字塔

**Wasm 專案的測試有一個特殊之處：同一份程式碼可以在三個環境裡跑，而它們抓得到的錯誤完全不同。**

```
        ┌───────────────────────────────┐
        │  ③ 瀏覽器整合測試（最慢、最真）  │  ← 抓：JS 綁定、DOM/API 互動、
        │     wasm-bindgen-test          │        OPFS/Worker 行為、真實引擎差異
        ├───────────────────────────────┤
        │  ② Wasm 環境單元測試            │  ← 抓：Wasm 特有的行為
        │     wasm32 target + Node/WASI  │        （記憶體對齊、i32 溢位、跨界）
        ├───────────────────────────────┤
        │  ① 原生單元測試（最快、最多）    │  ← 抓：純邏輯錯誤
        │     cargo test / ctest         │        **這一層應該佔 80%**
        └───────────────────────────────┘
```

**最重要的一條原則**：**能在第 ① 層抓到的錯，絕不要拖到第 ③ 層。** 原生測試跑一次是毫秒，瀏覽器整合測試跑一次是幾十秒——**把純邏輯寫成不依賴 Wasm 的形狀，是 Wasm 專案最值得做的一次架構投資。**

```rust
// ✅ 這個形狀讓 80% 的測試可以在原生跑
mod core {                                   // 純邏輯，不碰 wasm-bindgen
    pub fn transform(input: &[u8]) -> Vec<u8> { /* ... */ }
}

#[cfg(target_arch = "wasm32")]
mod bindings {                               // 只有這一層需要 Wasm 環境
    use wasm_bindgen::prelude::*;
    #[wasm_bindgen]
    pub fn transform(input: &[u8]) -> Vec<u8> { super::core::transform(input) }
}

#[cfg(test)]
mod tests {                                  // cargo test 直接跑，不需要瀏覽器
    #[test] fn roundtrip() { assert_eq!(super::core::transform(b"abc"), b"..."); }
}
```

---

## 二、`wasm-bindgen-test`：在真的引擎裡跑測試

```rust
use wasm_bindgen_test::*;

// 在瀏覽器裡跑（預設是 Node）
wasm_bindgen_test_configure!(run_in_browser);

#[wasm_bindgen_test]
fn works_in_wasm() {
    assert_eq!(crate::core::transform(b"abc"), b"...");
}

// ★ 非同步測試：OPFS、fetch、任何 Promise
#[wasm_bindgen_test]
async fn opfs_roundtrip() {
    let engine = WasmStorageEngine::new().await.unwrap();
    engine.save_file("t.bin", &[1, 2, 3]).await.unwrap();
    assert_eq!(engine.load_file("t.bin").await.unwrap(), vec![1, 2, 3]);
}

// 只在 Worker 裡跑（sync access handle 的規範限制，見第 7 章）
wasm_bindgen_test_configure!(run_in_dedicated_worker);
```

```bash
wasm-pack test --headless --chrome        # 無頭 Chrome
wasm-pack test --headless --firefox
wasm-pack test --node                     # 最快，但拿不到瀏覽器 API
```

**三個實務要點**：

1. **`run_in_dedicated_worker` 是 OPFS 測試的必要條件**——`createSyncAccessHandle` 在主執行緒會直接失敗（第 7 章）。
2. **每個測試檔是一個獨立的 Wasm 模組**，所以測試之間**不共用線性記憶體**——這是好事（隔離），但也意味著測試啟動成本不低。
3. **`--headless` 需要對應的 driver**（chromedriver / geckodriver），CI 上要一併安裝。

---

## 三、C/C++ 的路徑

```bash
# Emscripten：直接產出可用 node 執行的測試
emcc test.cpp -o test.js -sEXIT_RUNTIME=1 -sASSERTIONS=2
node test.js

# ★ Sanitizer 在 Wasm 上可用——這是彌補「沙盒內沒有 ASLR/canary」的最實際手段
emcc app.cpp -fsanitize=address -sALLOW_MEMORY_GROWTH=1 -o app-asan.js
emcc app.cpp -fsanitize=undefined -o app-ubsan.js
```

**為什麼 Sanitizer 在 Wasm 上特別重要**（第 2 章 ⚠️ 的直接推論）：

> 線性記憶體內部**沒有 ASLR、沒有 NX、沒有 stack canary**。一個在 x86 上會被作業系統擋下、立刻崩潰的緩衝區溢位，在 Wasm 裡可能**安靜地寫壞相鄰資料然後繼續跑**——你會在幾百行之後看到一個莫名其妙的錯誤結果，而不是一個清楚的 segfault。
>
> **ASan/UBSan 是你在 Wasm 裡唯一能拿回這些保護的方式。** 代價是體積與速度都會顯著變差，所以它是**測試建置**，不是發布建置。

**WASI 場景**：

```bash
# 用 wasmtime 直接跑測試二進位
cargo test --target wasm32-wasip1 --no-run
wasmtime run --dir=. target/wasm32-wasip1/debug/deps/mytest-*.wasm
```

---

## 四、Fuzzing：Wasm 特別值得做的一件事

**理由很直接**：Wasm 模組的入口通常是「餵一坨位元組進來」，**這正是 fuzzing 最有效的形狀**。

```rust
// fuzz_targets/parse.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    let _ = mycrate::core::parse(data);      // 不能 panic、不能越界、不能無限迴圈
});
```

```bash
cargo fuzz run parse -- -max_total_time=300
```

**而 Wasm 給了 fuzzing 一個額外的好處**：**你可以把 fuzzer 本身跑在 Wasm 沙盒裡**，於是即使目標程式碼被構造出的輸入打爆，**也絕對傷不到宿主**（這正是附錄 E 案例 50「字型模糊測試」的原理）。

**三個一定要 fuzz 的地方**：任何**解析器**（檔案格式、協定、輸入）、任何**索引運算**、任何**從 JS 傳進來的長度/偏移量**。

---

## 五、CI：一份可以直接用的 workflow

```yaml
name: Wasm CI

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4
      - uses: dtolnay/rust-toolchain@stable
        with: { targets: wasm32-unknown-unknown, components: clippy }

      # ① 原生單元測試（最快，抓 80% 的錯）
      - run: cargo test --all-features
      - run: cargo clippy --all-targets -- -D warnings

      # ② Wasm 環境測試
      - run: curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh
      - run: wasm-pack test --node

      # ③ 瀏覽器整合測試
      - uses: browser-actions/setup-chrome@latest
      - run: wasm-pack test --headless --chrome

      # ④ ★ 體積回歸守門（見附錄 N）
      - name: Build & check size budget
        run: |
          wasm-pack build --target web --release
          npm install -g binaryen
          f=$(ls pkg/*_bg.wasm)
          wasm-opt -Oz --strip-debug "$f" -o "$f"
          raw=$(stat -c%s "$f")
          br=$(brotli -q 11 -c "$f" | wc -c)
          echo "raw=$raw brotli=$br"
          # 超過預算就讓 CI 紅燈——體積回歸跟效能回歸一樣需要守門
          test "$br" -le 900000 || { echo "::error::Brotli size $br > budget 900000"; exit 1; }

      # ⑤ ★ 安全紅線（第 9 章）
      - name: Secret scan in binary
        run: |
          if strings pkg/*_bg.wasm | grep -Eq 'sk-|AKIA|BEGIN [A-Z ]*PRIVATE KEY'; then
            echo "::error::possible secret embedded in wasm"; exit 1
          fi
```

**第 ④ 與第 ⑤ 步是這份 workflow 真正的價值所在**，因為它們守的是兩件**只會慢慢惡化、不會突然壞掉**的事：

- **體積回歸**：沒有守門的話，`.wasm` 會在半年內從 800KB 長到 4MB，而沒有任何一次 commit 該為此負責。**把預算寫進 CI，讓每一次超標都有人回答「為什麼」。**
- **金鑰洩漏**：第 9 章的兩大物理禁區之一。**這是一行 `grep`，卻是全書投報率最高的一行 CI 設定。**

---

## 六、跨引擎差異：那些只在某一家壞掉的東西

**「在 Chrome 上好好的」是 Wasm 專案最常見的假象。** 已知的差異來源：

| 差異點 | 具體表現 |
|---|---|
| **記憶體上限** | 各引擎與平台不同（第 8 章）；**行動端遠低於桌面** |
| **特性支援度** | SIMD、threads、GC、JSPI、memory64 的落地時程各家不同 |
| **OPFS 行為** | `createSyncAccessHandle` 的並行語意、配額與驅逐策略有實作差異（第 7 章） |
| **計時器精度** | 未跨來源隔離時被粗化，各家粗化程度不同（附錄 N §15） |
| **編譯策略** | 分層編譯的 tier-up 時機不同 → **微基準的結果可能完全不同** |
| **堆疊深度** | 遞迴爆棧的閾值不同 |

**對策是一條紀律**：**在 CI 裡至少跑兩家引擎（Chrome + Firefox），並在真實的低階行動裝置上實測一次。** 桌面開發機是所有 Wasm 專案最危險的樂觀來源。

**執行期偵測 + 降級路徑**：

```javascript
const caps = {
  simd:    WebAssembly.validate(new Uint8Array([0,97,115,109,1,0,0,0,1,5,1,96,0,1,123,3,2,1,0,10,10,1,8,0,65,0,253,15,26,11])),
  threads: typeof SharedArrayBuffer === "function" && self.crossOriginIsolated,
  jspi:    typeof WebAssembly.Suspending === "function",
  opfs:    !!navigator.storage?.getDirectory,
};
const build = caps.threads && caps.simd ? "app-mt-simd.wasm"
            : caps.simd                 ? "app-simd.wasm"
            :                             "app-baseline.wasm";
```

> 💡 **維護多個建置變體是有成本的。** 先問一句：**沒有 SIMD 的那條路徑，我真的測過嗎？** 一個從來沒被執行過的降級路徑，跟沒有降級路徑是一樣的——**只是你會更晚才發現。**

---

## 七、執行期安全：那個被「Wasm 很安全」蓋住的攻擊面

**第 3 章說過「Wasm 所以安全」不是一個可以寫進安全評估報告的句子。這一節把那句話展開。**

### 7-1　三層攻擊面，被保護的只有第一層

```
① 模組傷不到宿主        ← ✅ 這一層 Wasm 保護得很好（型別系統 + 驗證器 + 沙盒）
② 模組內部的記憶體安全   ← ❌ 完全沒有保護（無 ASLR/NX/canary，見第 2 章）
③ 執行期本身的實作漏洞   ← ❌ 這是被談得最少的一層
```

**第 ③ 層值得單獨說**：Wasm 執行期是一大坨用 C++/Rust 寫的複雜軟體——**它有 JIT、有訊號處理器、有記憶體映射管理**，而這些正是歷史上漏洞最密集的地方。Wasmtime、V8 的 Wasm 實作、以及其他執行期都出現過安全公告。**「跑在 Wasm 沙盒裡」降低了風險，沒有消除風險。**

**實務對策**：

| 場景 | 對策 |
|---|---|
| 瀏覽器 | 依賴瀏覽器自身的更新機制（這一層你管不了，也不該管） |
| **後端執行不信任的模組** | **執行期必須跟著上游更新**；並且**不要只靠 Wasm 沙盒**——外面再包一層 OS 級隔離（容器 / seccomp / 獨立程序） |
| 多租戶 | 限制每個實例的記憶體與執行時間（燃料/計量）；**別讓一個租戶的無窮迴圈拖死整個程序** |

> **注意最後一項與附錄 L 的呼應**：FluffOS 的 Wasm 建置**沒有 eval limit**，因此「一段無窮的 LPC 迴圈會卡死整個分頁」。**在瀏覽器裡這只是使用者體驗問題；在多租戶後端，這就是 DoS。**

### 7-2　供應鏈：那個有漂亮 commit 紀錄的惡意模組

**第 9 章提過但值得展開**：靜態託管的「程式碼鎖在 Git 裡」聽起來很安全，**但如果你的建置流程引入了被投毒的套件，產出的 `.wasm` 本身就是惡意的——而它同樣有一個乾淨的 commit 紀錄。**

```bash
# 最低限度的供應鏈紀律
cargo audit                    # 已知漏洞
cargo deny check               # 授權、來源、重複依賴
cargo vet                      # 依賴審查紀錄
# C/C++：鎖定第三方庫版本並自行建置，不要用來路不明的預編譯 .a
```

**加上兩條 Wasm 特有的**：

1. **對產出的 `.wasm` 做 `wasm-objdump -x`，檢查 import 清單。** **模組要求了哪些能力，那張清單就是它的攻擊面**（第 1、7 章的能力式安全）。**一個影像處理模組突然 import 了網路相關的宿主函數，那就是紅旗。**
2. **可重現建置**：同一份原始碼在 CI 上編出來的 `.wasm` 雜湊應該穩定。**做得到的話，社群就能驗證「這個二進位確實是那份原始碼編的」**——這正是第 9 章那條「可稽核 ≠ 已稽核」的補救方式。

---

## 八、可觀測性：線上壞掉的時候你手上有什麼

**這是第 3 章「牆八：偵錯困難」的正式環境版本。**

```
發布版你做了什麼           →  你失去了什麼          →  怎麼補回來
────────────────────────────────────────────────────────────
strip = true              →  函數名               →  ★ 保留一份帶符號的建置
--strip-debug             →  DWARF                →  存進符號伺服器/artifact
panic = "abort"           →  panic 訊息與堆疊      →  自建錯誤碼
panic_immediate_abort     →  連錯誤碼都沒有        →  只在確定不需要時用
```

**一份最小可行的線上錯誤回報**：

```javascript
window.addEventListener("error", (e) => {
  if (e.error instanceof WebAssembly.RuntimeError) {
    report({
      kind: "wasm_trap",
      message: e.error.message,          // "memory access out of bounds" 等
      stack: e.error.stack,              // 含 wasm-function[N] —— 需要符號才有意義
      build: __BUILD_HASH__,             // ★ 對應到你保留的那份帶符號建置
      caps: { simd: ..., threads: ..., isolated: self.crossOriginIsolated },
      memPages: wasm.memory.buffer.byteLength / 65536,   // 撞上限了嗎？
    });
  }
});
```

**三個最值得回報的欄位**（它們對應到本書三個最常見的線上故障）：

| 欄位 | 對應的故障 |
|---|---|
| `memPages` | **撞到記憶體上限**（第 8 章）——行動裝置最常見 |
| `caps.isolated` / `caps.threads` | **多執行緒建置跑在非隔離頁面上**（第 5 章） |
| `build` | **使用者拿到了舊版**（Service Worker 快取，附錄 C 疑難排解） |

> 💡 君之一席話
> 與君一席話：**一個系統的成熟度，不看它順利時多漂亮，看它出事時留下多少線索。** Wasm 的整條工具鏈都在鼓勵你把線索丟掉——strip 掉符號省體積、abort 掉 panic 省體積、關掉斷言省體積，**而每一項都是拿「未來某個凌晨三點」去換今天的幾十 KB。** 這個交易不一定不划算，但它必須是**被明確做出的決定**，而不是複製貼上一份 `Cargo.toml` 的副作用。**最低限度的紀律只有一條：不管你 strip 掉什麼，都要留一份沒 strip 的、和發布版位元組級對應的建置。** 那份東西平常一文不值，出事那天它是你唯一的證據。

---

## 九、上線前的完整檢查清單（整合版）

> 這份清單整合了附錄 C（部署）、附錄 N（體積與速度）與本附錄（測試與安全）。

```
【正確性】
□ 原生單元測試通過（應涵蓋 80% 的邏輯）
□ wasm-pack test --node 通過
□ wasm-pack test --headless --chrome 與 --firefox 都通過
□ 解析器類程式碼跑過 fuzzing
□ 用 -fsanitize=address 的測試建置跑過一輪

【體積】（附錄 N）
□ wasm-objdump -h 看過區段預算（Data 佔比高就先裁資料）
□ wasm-opt -Oz --converge 跑過
□ twiggy top / dominators 沒有意外的兇手
□ CI 有體積預算守門

【效能】（附錄 N）
□ 分開量過：編譯 / 實例化 / 執行期初始化
□ 量測時的跨來源隔離狀態一致（否則計時器被降精度）
□ 熱路徑上沒有細碎跨界呼叫
□ 大區塊搬移用的是 memcpy 而不是逐位元組迴圈

【部署】（附錄 C）
□ Content-Type: application/wasm、Content-Encoding: br
□ 內容雜湊檔名（穩定 URL → 程式碼快取）
□ CSP 含 'wasm-unsafe-eval'（若站台有 CSP）
□ .nojekyll、相對路徑、await init()
□ 確認過有沒有「不需要 SharedArrayBuffer」的後端可用

【安全】（第 9 章 + 本附錄）
□ strings 掃過二進位，沒有金鑰  ★ 最重要
□ wasm-objdump -x 看過 import 清單，沒有意外的能力需求
□ cargo audit / cargo deny 通過
□ 後端執行不信任模組時：執行期已更新，且外層有 OS 級隔離
□ 有記憶體與執行時間的配額限制

【可觀測性】
□ 保留了一份帶符號、與發布版位元組級對應的建置
□ 線上有 WebAssembly.RuntimeError 的回報，含 build hash 與 memPages
□ 降級路徑（無 SIMD / 無 threads）真的被執行過，不只是寫在那裡
```

---

## 附：與正文的對照索引

| 主題 | 本附錄 | 正文背景 |
|---|---|---|
| 測試分層 | §1–3 | 第 3 章牆八 |
| Sanitizer 為何在 Wasm 上特別重要 | §3 | **第 2 章情境 1 ⚠️**（沙盒內沒有 ASLR/canary） |
| Fuzzing | §4 | 附錄 E 案例 50 |
| CI 的體積與金鑰守門 | §5 | 附錄 N、第 9 章 |
| 跨引擎差異 | §6 | 第 8 章、附錄 N §15 |
| 執行期本身的攻擊面 | §7-1 | 第 3 章情境 1（「Wasm 所以安全」不是一句可以寫進報告的話） |
| 供應鏈 | §7-2 | 第 9 章情境 4 ⚠️ |
| 可觀測性 | §8 | 第 3 章牆八、第 12 章（三年後誰修） |
