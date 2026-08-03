# 附錄C　GitHub Pages × Wasm 部署實戰手冊

> 這一份是「照著做就能跑」的操作手冊。第 5 章講的是為什麼，這裡講的是怎麼做。

---

## 一、先做決策：你需要多執行緒嗎？

**這是整份手冊最重要的一個岔路口**，走錯會多花兩週。

```
你的 Wasm 用到 pthread / rayon / SharedArrayBuffer 嗎？
│
├─ 否（大多數專案）
│   → 直接部署，不需要 coi-serviceworker，不需要任何特殊設定
│   → 跳到「二、單執行緒部署路徑」
│
└─ 是 → 依序問三個問題，能在前面停下就別往後走：
    │
    ├─ ① 你依賴的函式庫有沒有「不需要 SharedArrayBuffer」的後端？
    │     例：SQLite-Wasm 的 opfs-sahpool VFS（不需 COOP/COEP 且最快，見第 7 章）
    │     → 有 → ★ 用它，整個問題消失
    │
    ├─ ② 你的任務資料可以切分嗎？（批次處理、分塊渲染、獨立查詢）
    │     → 可以 → ★ 改用「多實例隔離」（N 個 Worker × N 個 Wasm 實例）
    │              不需要跨來源隔離，且順便突破 4GB 上限（第 8 章）
    │
    └─ ③ 真的需要細粒度共享狀態（物理模擬、圖遍歷）？
          → 是 → 走 coi-serviceworker，並優先試 COEP: credentialless
          → 跳到「三、多執行緒部署路徑」
```

---

## 二、單執行緒部署路徑

### 步驟 1：編譯

```bash
# Rust
wasm-pack build --target web --release

# C/C++
emcc app.cpp -O3 -s MODULARIZE=1 -s EXPORT_ES6=1 -o pkg/app.js
```

### 步驟 2：優化（強烈建議，通常砍 15–40% 體積）

```bash
wasm-opt -Oz --strip-debug --strip-producers \
  pkg/your_project_bg.wasm -o pkg/your_project_bg.wasm
```

### 步驟 3：`index.html`

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Wasm on GitHub Pages</title>
</head>
<body>
  <input type="file" id="file">
  <p id="status">初始化中…</p>

  <script type="module">
    // ★ 必須用相對路徑（./），否則專案頁的子路徑會 404
    import init, { process } from './pkg/your_project.js';

    const status = document.getElementById('status');

    async function main() {
      await init();                        // ★ 一定要 await，否則呼叫會炸
      status.textContent = 'Wasm 就緒';

      document.getElementById('file').addEventListener('change', async (e) => {
        const buf = new Uint8Array(await e.target.files[0].arrayBuffer());
        const t0 = performance.now();
        const out = process(buf);          // 一次呼叫處理整批 —— 邊界要粗
        status.textContent = `完成，耗時 ${(performance.now() - t0).toFixed(1)} ms`;
      });
    }
    main();
  </script>
</body>
</html>
```

### 步驟 4：專案結構與 `.nojekyll`

```
your-repo/
├── index.html
├── .nojekyll          ← ★ 空檔案，阻止 Jekyll 吃掉 _ 開頭的資料夾
└── pkg/
    ├── your_project.js
    └── your_project_bg.wasm
```

### 步驟 4.5：如果你的站台有 CSP

Wasm 的編譯在 CSP 眼中屬於動態程式碼產生，**沒放行就直接被擋**：

```http
Content-Security-Policy: script-src 'self' 'wasm-unsafe-eval'
```

`'wasm-unsafe-eval'`（Chrome 97+／Firefox 102+／Safari 16+）**只放行 Wasm 編譯，不放行 `eval()`**。
**症狀是 CSP violation 而不是 Wasm 錯誤**——特別容易在「被嵌進別人的 iframe」與「瀏覽器擴充套件」兩種場合咬人。

### 步驟 5：開啟 Pages

1. 推到 GitHub。
2. **Settings → Pages → Build and deployment**。
3. 選擇來源分支（`main` 或 `gh-pages`）與資料夾（`/` 或 `/docs`）。
4. 等幾分鐘，造訪 `https://<帳號>.github.io/<專案名>/`。

---

## 三、多執行緒部署路徑（需要 `SharedArrayBuffer`）

### 步驟 1：取得 `coi-serviceworker.js`

從其開源倉庫取得腳本，放到站台根目錄。

### 步驟 2：在 `<head>` 最前面引入

```html
<head>
  <script src="coi-serviceworker.js"></script>   <!-- ★ 必須是第一個 script -->
  <meta charset="UTF-8">
  ...
</head>
```

**行為**：首次載入時 Service Worker 尚未接管，腳本會自動重整一次頁面；第二次載入起所有回應都帶上 COOP/COEP，`self.crossOriginIsolated === true`。

### 步驟 3：驗證

```javascript
console.log('crossOriginIsolated:', self.crossOriginIsolated);   // 必須是 true
console.log('SharedArrayBuffer:', typeof SharedArrayBuffer);     // 必須是 "function"
```

### 步驟 4：編譯時開啟執行緒

```bash
# Emscripten
emcc app.cpp -O3 -pthread -s PTHREAD_POOL_SIZE=4 \
     -s ALLOW_MEMORY_GROWTH=1 -o pkg/app.js

# Rust（rayon + wasm-bindgen-rayon）
RUSTFLAGS='-C target-feature=+atomics,+bulk-memory,+mutable-globals' \
  rustup run nightly wasm-pack build --target web -- -Z build-std=panic_abort,std
```

### ⚠️ 開啟隔離後會壞掉的東西

> 💡 **先試 `COEP: credentialless` 再試 `require-corp`**：前者允許載入沒有表態的跨來源資源（只是不帶憑證請求），能大幅減少下表的損害。`coi-serviceworker` 一類的方案通常可設定要合成哪一種。

| 會壞掉 | 為什麼 | 解法 |
|---|---|---|
| Google Fonts / 外部 CDN 字型 | 沒有 `Cross-Origin-Resource-Policy` 標頭 | 把字型自行託管在同源 |
| 第三方圖片 | 同上 | 自行託管，或確認對方支援 CORS 並加 `crossorigin` 屬性 |
| YouTube / 外部 iframe | COEP 阻擋 | 改用 `credentialless` 模式（支援度有限）或移除 |
| 廣告 / 統計腳本 | 同上 | 多半只能移除 |

**這就是為什麼第 5 章說「先確認你真的需要多執行緒」——這個代價是實質的。**

---

## 四、GitHub Actions 自動化建置與部署

**比手動 commit `pkg/` 乾淨得多**：原始碼與產物分離，且每次推送都是可重現的建置。

```yaml
name: Build & Deploy Wasm to Pages

on:
  push:
    branches: [main]
  workflow_dispatch:

permissions:
  contents: read
  pages: write
  id-token: write

concurrency:
  group: pages
  cancel-in-progress: true

jobs:
  build:
    runs-on: ubuntu-latest
    steps:
      - uses: actions/checkout@v4

      - name: Setup Rust
        uses: dtolnay/rust-toolchain@stable
        with:
          targets: wasm32-unknown-unknown

      - name: Cache cargo
        uses: actions/cache@v4
        with:
          path: |
            ~/.cargo/registry
            ~/.cargo/git
            target
          key: ${{ runner.os }}-cargo-${{ hashFiles('**/Cargo.lock') }}

      - name: Install wasm-pack
        run: curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh

      - name: Build
        run: wasm-pack build --target web --release

      - name: Install binaryen & optimize
        run: |
          npm install -g binaryen
          for f in pkg/*_bg.wasm; do
            wasm-opt -Oz --strip-debug --strip-producers "$f" -o "$f.opt"
            mv "$f.opt" "$f"
          done
          ls -lh pkg/*.wasm

      - name: Assemble site
        run: |
          mkdir -p dist
          cp index.html dist/
          cp -r pkg dist/
          # 若需要多執行緒，把 coi-serviceworker.js 一併複製
          [ -f coi-serviceworker.js ] && cp coi-serviceworker.js dist/ || true
          touch dist/.nojekyll

      - uses: actions/upload-pages-artifact@v3
        with:
          path: dist

  deploy:
    needs: build
    runs-on: ubuntu-latest
    environment:
      name: github-pages
      url: ${{ steps.deployment.outputs.page_url }}
    steps:
      - id: deployment
        uses: actions/deploy-pages@v4
```

---

## 五、疑難排解對照表（依踩到的頻率排序）

| 症狀 | 病因 | 解法 |
|---|---|---|
| `.wasm` 404 | `pkg/` 被 `.gitignore` 忽略 | 加進版控，或改用 Actions 建置 |
| `.wasm` 404 | 用了絕對路徑 `/pkg/...`，但站台在 `/repo/` 子路徑 | 全部改成相對路徑 `./pkg/...` |
| `.wasm` 404 | Jekyll 忽略了 `_` 開頭的資料夾 | 根目錄放空的 `.nojekyll` |
| `Incorrect response MIME type` | 伺服器沒回 `application/wasm` | GitHub Pages 對 `.wasm` 副檔名會正確回傳；若失敗，檢查檔名是否真的是 `.wasm` |
| `SharedArrayBuffer is not defined` | 沒有跨來源隔離 | 引入 `coi-serviceworker`（見第三節） |
| 呼叫函數時 `undefined is not a function` | 忘了 `await init()` | 所有呼叫都放在 `await init()` 之後 |
| 第一次載入正常、部署新版後拿到舊版 | Service Worker 快取 | 在 SW 裡處理 `skipWaiting()` / `clients.claim()`，或給資源加版本查詢字串 |
| 本機正常、線上崩潰 | 本機是 `localhost`（被視為安全來源），線上不是 | 確認 HTTPS 與隔離狀態 |
| 手機上直接崩潰 | 記憶體上限比桌面低得多 | 降低初始記憶體、改用串流分塊（第 8 章） |
| 首次載入極慢 | 模組體積過大 | `wasm-opt -Oz` + Brotli + 模組分割延遲載入 |

---

## 六、上線前檢查清單

```
□ wasm-opt -Oz 跑過了，體積在可接受範圍（前端建議 < 30MB，理想 < 10MB）
□ 用 wasm-objdump -h 看過區段預算（Data 佔比高就先裁資料，不是調旗標）
□ 用 twiggy top / dominators 確認過沒有意外的體積兇手
□ 發布版開了 strip = true / lto = true（第 9 章）
□ strings app.wasm | grep -Ei 'sk-|AKIA|password|secret' 是空的  ★ 最重要
□ 所有路徑都是相對路徑
□ .nojekyll 存在
□ await init() 在所有呼叫之前
□ memory.grow 之後有重新取得 TypedArray 視圖
□ 大檔案走串流分塊，沒有一次全量讀入
□ 重運算在 Worker 裡，主執行緒不被阻塞
□ 若用了多執行緒：crossOriginIsolated 為 true，且確認過第三方資源沒被 COEP 打壞
□ 先確認過「有沒有不需要 SharedArrayBuffer 的後端」（如 SQLite 的 opfs-sahpool）
□ 若站台有 CSP：script-src 已含 'wasm-unsafe-eval'
□ 伺服器回傳 Content-Type: application/wasm 與 Content-Encoding: br（預壓縮 .wasm.br 優於即時壓縮）
□ .wasm 用內容雜湊檔名（穩定 URL → 回訪可命中程式碼快取）
□ 量測時確認過跨來源隔離狀態一致（未隔離時計時器被降精度）
□ 多個 Worker 時，用 postMessage 傳 WebAssembly.Module 而不是各自重新編譯
□ 準備了一份帶符號的建置產物，用於線上問題的堆疊還原
□ 在目標裝置（含低階手機）實測過，不是只在開發機上跑過
```
