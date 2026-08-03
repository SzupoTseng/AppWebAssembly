# 附录C　GitHub Pages × Wasm 部署实战手册

> 这一份是「照着做就能跑」的操作手册。第 5 章讲的是为什么，这里讲的是怎么做。

---

## 一、先做决策：你需要多线程吗？

**这是整份手册最重要的一个岔路口**，走错会多花两周。

```
你的 Wasm 用到 pthread / rayon / SharedArrayBuffer 吗？
│
├─ 否（大多数项目）
│   → 直接部署，不需要 coi-serviceworker，不需要任何特殊设置
│   → 跳到「二、单线程部署路径」
│
└─ 是 → 依序问三个问题，能在前面停下就别往后走：
    │
    ├─ ① 你依赖的函数库有没有「不需要 SharedArrayBuffer」的后端？
    │     例：SQLite-Wasm 的 opfs-sahpool VFS（不需 COOP/COEP 且最快，见第 7 章）
    │     → 有 → ★ 用它，整个问题消失
    │
    ├─ ② 你的任务数据可以切分吗？（批量处理、分块渲染、独立查找）
    │     → 可以 → ★ 改用「多实例隔离」（N 个 Worker × N 个 Wasm 实例）
    │              不需要跨来源隔离，且顺便突破 4GB 上限（第 8 章）
    │
    └─ ③ 真的需要细粒度共享状态（物理仿真、图遍历）？
          → 是 → 走 coi-serviceworker，并优先试 COEP: credentialless
          → 跳到「三、多线程部署路径」
```

---

## 二、单线程部署路径

### 步骤 1：编译

```bash
# Rust
wasm-pack build --target web --release

# C/C++
emcc app.cpp -O3 -s MODULARIZE=1 -s EXPORT_ES6=1 -o pkg/app.js
```

### 步骤 2：优化（强烈建议，通常砍 15–40% 体积）

```bash
wasm-opt -Oz --strip-debug --strip-producers \
  pkg/your_project_bg.wasm -o pkg/your_project_bg.wasm
```

### 步骤 3：`index.html`

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
    // ★ 必须用相对路径（./），否则项目页的子路径会 404
    import init, { process } from './pkg/your_project.js';

    const status = document.getElementById('status');

    async function main() {
      await init();                        // ★ 一定要 await，否则调用会炸
      status.textContent = 'Wasm 就绪';

      document.getElementById('file').addEventListener('change', async (e) => {
        const buf = new Uint8Array(await e.target.files[0].arrayBuffer());
        const t0 = performance.now();
        const out = process(buf);          // 一次调用处理整批 —— 边界要粗
        status.textContent = `完成，耗时 ${(performance.now() - t0).toFixed(1)} ms`;
      });
    }
    main();
  </script>
</body>
</html>
```

### 步骤 4：项目结构与 `.nojekyll`

```
your-repo/
├── index.html
├── .nojekyll          ← ★ 空文件，阻止 Jekyll 吃掉 _ 开头的文件夹
└── pkg/
    ├── your_project.js
    └── your_project_bg.wasm
```

### 步骤 4.5：如果你的站台有 CSP

Wasm 的编译在 CSP 眼中属于动态代码产生，**没放行就直接被挡**：

```http
Content-Security-Policy: script-src 'self' 'wasm-unsafe-eval'
```

`'wasm-unsafe-eval'`（Chrome 97+／Firefox 102+／Safari 16+）**只放行 Wasm 编译，不放行 `eval()`**。
**症状是 CSP violation 而不是 Wasm 错误**——特别容易在「被嵌进别人的 iframe」与「浏览器扩展」两种场合咬人。

### 步骤 5：打开 Pages

1. 推到 GitHub。
2. **Settings → Pages → Build and deployment**。
3. 选择来源分支（`main` 或 `gh-pages`）与文件夹（`/` 或 `/docs`）。
4. 等几分钟，造访 `https://<帐号>.github.io/<项目名>/`。

---

## 三、多线程部署路径（需要 `SharedArrayBuffer`）

### 步骤 1：取得 `coi-serviceworker.js`

从其开源仓库取得脚本，放到站台根目录。

### 步骤 2：在 `<head>` 最前面引入

```html
<head>
  <script src="coi-serviceworker.js"></script>   <!-- ★ 必须是第一个 script -->
  <meta charset="UTF-8">
  ...
</head>
```

**行为**：首次加载时 Service Worker 尚未接管，脚本会自动重整一次页面；第二次加载起所有回应都带上 COOP/COEP，`self.crossOriginIsolated === true`。

### 步骤 3：验证

```javascript
console.log('crossOriginIsolated:', self.crossOriginIsolated);   // 必须是 true
console.log('SharedArrayBuffer:', typeof SharedArrayBuffer);     // 必须是 "function"
```

### 步骤 4：编译时打开线程

```bash
# Emscripten
emcc app.cpp -O3 -pthread -s PTHREAD_POOL_SIZE=4 \
     -s ALLOW_MEMORY_GROWTH=1 -o pkg/app.js

# Rust（rayon + wasm-bindgen-rayon）
RUSTFLAGS='-C target-feature=+atomics,+bulk-memory,+mutable-globals' \
  rustup run nightly wasm-pack build --target web -- -Z build-std=panic_abort,std
```

### ⚠️ 打开隔离后会坏掉的东西

> 💡 **先试 `COEP: credentialless` 再试 `require-corp`**：前者允许加载没有表态的跨来源资源（只是不带凭证请求），能大幅减少下表的损害。`coi-serviceworker` 一类的方案通常可设置要合成哪一种。

| 会坏掉 | 为什么 | 解法 |
|---|---|---|
| Google Fonts / 外部 CDN 字体 | 没有 `Cross-Origin-Resource-Policy` 标头 | 把字体自行托管在同源 |
| 第三方图片 | 同上 | 自行托管，或确认对方支持 CORS 并加 `crossorigin` 属性 |
| YouTube / 外部 iframe | COEP 阻挡 | 改用 `credentialless` 模式（支持度有限）或移除 |
| 广告 / 统计脚本 | 同上 | 多半只能移除 |

**这就是为什么第 5 章说「先确认你真的需要多线程」——这个代价是实质的。**

---

## 四、GitHub Actions 自动化建置与部署

**比手动 commit `pkg/` 干净得多**：原代码与产物分离，且每次推送都是可重现的建置。

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
          # 若需要多线程，把 coi-serviceworker.js 一并拷贝
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

## 五、疑难排解对照表（依踩到的频率排序）

| 症状 | 病因 | 解法 |
|---|---|---|
| `.wasm` 404 | `pkg/` 被 `.gitignore` 忽略 | 加进版控，或改用 Actions 建置 |
| `.wasm` 404 | 用了绝对路径 `/pkg/...`，但站台在 `/repo/` 子路径 | 全部改成相对路径 `./pkg/...` |
| `.wasm` 404 | Jekyll 忽略了 `_` 开头的文件夹 | 根目录放空的 `.nojekyll` |
| `Incorrect response MIME type` | 服务器没回 `application/wasm` | GitHub Pages 对 `.wasm` 扩展名会正确回传；若失败，检查文件名是否真的是 `.wasm` |
| `SharedArrayBuffer is not defined` | 没有跨来源隔离 | 引入 `coi-serviceworker`（见第三节） |
| 调用函数时 `undefined is not a function` | 忘了 `await init()` | 所有调用都放在 `await init()` 之后 |
| 第一次加载正常、部署新版后拿到旧版 | Service Worker 缓存 | 在 SW 里处理 `skipWaiting()` / `clients.claim()`，或给资源加版本查找字符串 |
| 本机正常、在线崩溃 | 本机是 `localhost`（被视为安全来源），在线不是 | 确认 HTTPS 与隔离状态 |
| 手机上直接崩溃 | 内存上限比桌面低得多 | 降低初始内存、改用串流分块（第 8 章） |
| 首次加载极慢 | 模块体积过大 | `wasm-opt -Oz` + Brotli + 模块分割延迟加载 |

---

## 六、上线前检查清单

```
□ wasm-opt -Oz 跑过了，体积在可接受范围（前端建议 < 30MB，理想 < 10MB）
□ 用 wasm-objdump -h 看过区段预算（Data 占比高就先裁数据，不是调旗标）
□ 用 twiggy top / dominators 确认过没有意外的体积凶手
□ 发布版开了 strip = true / lto = true（第 9 章）
□ strings app.wasm | grep -Ei 'sk-|AKIA|password|secret' 是空的  ★ 最重要
□ 所有路径都是相对路径
□ .nojekyll 存在
□ await init() 在所有调用之前
□ memory.grow 之后有重新取得 TypedArray 视图
□ 大文件走串流分块，没有一次全量读入
□ 重运算在 Worker 里，主线程不被阻塞
□ 若用了多线程：crossOriginIsolated 为 true，且确认过第三方资源没被 COEP 打坏
□ 先确认过「有没有不需要 SharedArrayBuffer 的后端」（如 SQLite 的 opfs-sahpool）
□ 若站台有 CSP：script-src 已含 'wasm-unsafe-eval'
□ 服务器回传 Content-Type: application/wasm 与 Content-Encoding: br（预压缩 .wasm.br 优于即时压缩）
□ .wasm 用内容哈希文件名（稳定 URL → 回访可命中代码缓存）
□ 量测时确认过跨来源隔离状态一致（未隔离时计时器被降精度）
□ 多个 Worker 时，用 postMessage 传 WebAssembly.Module 而不是各自重新编译
□ 准备了一份带符号的建置产物，用于在线问题的堆栈还原
□ 在目标设备（含低级手机）实测过，不是只在开发机上跑过
```
