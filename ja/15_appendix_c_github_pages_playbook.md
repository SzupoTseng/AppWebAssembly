# 付録C：GitHub Pages × Wasm 配備実戦マニュアル

> これは「そのとおりにやれば動く」操作マニュアルである。第 5 章が語るのはなぜかであり、ここが語るのはどうやるかである。

---

## 1. まず判断する：マルチスレッドは要るのか

**これがマニュアル全体で最も重要な分かれ道であり**、間違えれば二週間を余計に使う。

```
あなたの Wasm は pthread / rayon / SharedArrayBuffer を使うか？
│
├─ いいえ（大半のプロジェクト）
│   → そのまま配備。coi-serviceworker も特別な設定も要らない
│   → 「2. シングルスレッドの配備経路」へ飛ぶ
│
└─ はい → 三つの問いを順に。前で止まれるなら先へ進むな：
    │
    ├─ ① 依存するライブラリに「SharedArrayBuffer が要らない」バックエンドはあるか？
    │     例：SQLite-Wasm の opfs-sahpool VFS（COOP/COEP 不要で最速。第 7 章参照）
    │     → ある → ★ それを使う。問題まるごと消える
    │
    ├─ ② タスクのデータは切り分けられるか？（バッチ処理、分割レンダリング、独立したクエリ）
    │     → できる → ★ 「複数インスタンス隔離」へ切り替える（N 個の Worker × N 個の Wasm インスタンス）
    │              クロスオリジン隔離が要らず、ついでに 4 GB 上限も突破する（第 8 章）
    │
    └─ ③ 本当に細粒度の共有状態が要るのか（物理シミュレーション、グラフ探索）？
          → はい → coi-serviceworker へ進み、まず COEP: credentialless を試す
          → 「3. マルチスレッドの配備経路」へ飛ぶ
```

---

## 2. シングルスレッドの配備経路

### ステップ 1：コンパイル

```bash
# Rust
wasm-pack build --target web --release

# C/C++
emcc app.cpp -O3 -s MODULARIZE=1 -s EXPORT_ES6=1 -o pkg/app.js
```

### ステップ 2：最適化（強く推奨。たいてい 15〜40% のサイズが落ちる）

```bash
wasm-opt -Oz --strip-debug --strip-producers \
  pkg/your_project_bg.wasm -o pkg/your_project_bg.wasm
```

### ステップ 3：`index.html`

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Wasm on GitHub Pages</title>
</head>
<body>
  <input type="file" id="file">
  <p id="status">初期化中…</p>

  <script type="module">
    // ★ 必ず相対パス（./）を使う。さもないとプロジェクトページのサブパスで 404 になる
    import init, { process } from './pkg/your_project.js';

    const status = document.getElementById('status');

    async function main() {
      await init();                        // ★ 必ず await する。さもないと呼び出しが爆発する
      status.textContent = 'Wasm 準備完了';

      document.getElementById('file').addEventListener('change', async (e) => {
        const buf = new Uint8Array(await e.target.files[0].arrayBuffer());
        const t0 = performance.now();
        const out = process(buf);          // 一回の呼び出しで一括処理する —— 境界は粗く
        status.textContent = `完了。所要 ${(performance.now() - t0).toFixed(1)} ms`;
      });
    }
    main();
  </script>
</body>
</html>
```

### ステップ 4：プロジェクトの構成と `.nojekyll`

```
your-repo/
├── index.html
├── .nojekyll          ← ★ 空ファイル。Jekyll が _ 始まりのフォルダを食うのを止める
└── pkg/
    ├── your_project.js
    └── your_project_bg.wasm
```

### ステップ 4.5：サイトに CSP がある場合

Wasm のコンパイルは CSP の目には動的コード生成であり、**許可しなければそのまま遮断される**。

```http
Content-Security-Policy: script-src 'self' 'wasm-unsafe-eval'
```

`'wasm-unsafe-eval'`（Chrome 97+／Firefox 102+／Safari 16+）は **Wasm のコンパイルだけを許し、`eval()` は許さない**。
**症状は CSP violation であって Wasm のエラーではない**——「他人の iframe に埋め込まれている」場合と「ブラウザ拡張」の二つの場面でとりわけ噛みつきやすい。

### ステップ 5：Pages を有効にする

1. GitHub へ push する。
2. **Settings → Pages → Build and deployment**。
3. 公開元のブランチ（`main` か `gh-pages`）とフォルダ（`/` か `/docs`）を選ぶ。
4. 数分待って `https://<アカウント>.github.io/<プロジェクト名>/` を訪れる。

---

## 3. マルチスレッドの配備経路（`SharedArrayBuffer` が要る）

### ステップ 1：`coi-serviceworker.js` を入手する

そのオープンソースリポジトリからスクリプトを取り、サイトのルートへ置く。

### ステップ 2：`<head>` の最前で読み込む

```html
<head>
  <script src="coi-serviceworker.js"></script>   <!-- ★ 最初の script でなければならない -->
  <meta charset="UTF-8">
  ...
</head>
```

**挙動**：初回ロード時には Service Worker がまだ引き継いでいないので、スクリプトが自動でページを一度リロードする。二度目のロードからはすべてのレスポンスに COOP/COEP が乗り、`self.crossOriginIsolated === true` になる。

### ステップ 3：検証

```javascript
console.log('crossOriginIsolated:', self.crossOriginIsolated);   // true でなければならない
console.log('SharedArrayBuffer:', typeof SharedArrayBuffer);     // "function" でなければならない
```

### ステップ 4：コンパイル時にスレッドを有効にする

```bash
# Emscripten
emcc app.cpp -O3 -pthread -s PTHREAD_POOL_SIZE=4 \
     -s ALLOW_MEMORY_GROWTH=1 -o pkg/app.js

# Rust（rayon + wasm-bindgen-rayon）
RUSTFLAGS='-C target-feature=+atomics,+bulk-memory,+mutable-globals' \
  rustup run nightly wasm-pack build --target web -- -Z build-std=panic_abort,std
```

### ⚠️ 隔離を有効にすると壊れるもの

> 💡 **`require-corp` より先に `COEP: credentialless` を試すこと**：前者は表明のないクロスオリジンリソースの読み込みを許す（ただし資格情報なしで要求する）ので、下表の被害を大きく減らせる。`coi-serviceworker` の類はたいていどちらを合成するか設定できる。

| 壊れるもの | なぜか | 解法 |
|---|---|---|
| Google Fonts / 外部 CDN のフォント | `Cross-Origin-Resource-Policy` ヘッダがない | フォントを同一オリジンで自前ホストする |
| サードパーティの画像 | 同上 | 自前ホストするか、相手が CORS に対応しているのを確認して `crossorigin` 属性を付ける |
| YouTube / 外部 iframe | COEP が遮断する | `credentialless` モードへ切り替える（対応は限定的）か、取り除く |
| 広告 / 解析スクリプト | 同上 | たいてい取り除くしかない |

**これこそ第 5 章が「本当にマルチスレッドが要るのかを先に確かめよ」と言う理由である——この代価は実質的である。**

---

## 4. GitHub Actions による自動ビルドと配備

**`pkg/` を手で commit するよりずっと清潔である**：ソースと成果物が分かれ、push のたびに再現可能なビルドになる。

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
          # マルチスレッドが要るなら coi-serviceworker.js も一緒にコピーする
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

## 5. トラブルシューティング対照表（踏まれる頻度の順）

| 症状 | 病因 | 解法 |
|---|---|---|
| `.wasm` が 404 | `pkg/` が `.gitignore` に無視された | バージョン管理へ入れるか、Actions でビルドする |
| `.wasm` が 404 | 絶対パス `/pkg/...` を使ったが、サイトが `/repo/` のサブパスにある | すべて相対パス `./pkg/...` にする |
| `.wasm` が 404 | Jekyll が `_` 始まりのフォルダを無視した | ルートに空の `.nojekyll` を置く |
| `Incorrect response MIME type` | サーバが `application/wasm` を返していない | GitHub Pages は `.wasm` 拡張子には正しく返す。失敗するならファイル名が本当に `.wasm` か確認する |
| `SharedArrayBuffer is not defined` | クロスオリジン隔離がない | `coi-serviceworker` を導入する（第 3 節参照） |
| 関数呼び出しで `undefined is not a function` | `await init()` を忘れた | すべての呼び出しを `await init()` のあとに置く |
| 初回は正常、新版を配備したら旧版が来る | Service Worker のキャッシュ | SW で `skipWaiting()` / `clients.claim()` を扱うか、リソースにバージョンのクエリ文字列を付ける |
| ローカルでは正常、本番でクラッシュ | ローカルは `localhost`（安全なオリジンとみなされる）で、本番は違う | HTTPS と隔離の状態を確認する |
| スマートフォンで即クラッシュ | メモリ上限がデスクトップよりはるかに低い | 初期メモリを下げ、ストリーミング分割へ切り替える（第 8 章） |
| 初回ロードが極端に遅い | モジュールが大きすぎる | `wasm-opt -Oz` + Brotli + モジュール分割の遅延読み込み |

---

## 6. 公開前のチェックリスト

```
□ wasm-opt -Oz を走らせ、サイズが許容範囲にある（フロントは < 30 MB 推奨、理想は < 10 MB）
□ wasm-objdump -h でセクションの予算を見た（Data の比率が高いならフラグでなくデータを削る）
□ twiggy top / dominators で予想外のサイズの犯人がいないことを確認した
□ リリース版で strip = true / lto = true を有効にした（第 9 章）
□ strings app.wasm | grep -Ei 'sk-|AKIA|password|secret' が空である  ★ 最重要
□ すべてのパスが相対パスである
□ .nojekyll が存在する
□ await init() がすべての呼び出しの前にある
□ memory.grow のあとに TypedArray のビューを取り直している
□ 大きなファイルはストリーミング分割で扱い、一度に全量を読み込んでいない
□ 重い計算は Worker の中にあり、メインスレッドをブロックしていない
□ マルチスレッドを使うなら：crossOriginIsolated が true で、サードパーティのリソースが COEP で壊れていないことを確認した
□ 「SharedArrayBuffer が要らないバックエンドがあるか」を先に確認した（SQLite の opfs-sahpool など）
□ サイトに CSP があるなら：script-src に 'wasm-unsafe-eval' が含まれている
□ サーバが Content-Type: application/wasm と Content-Encoding: br を返す（事前圧縮した .wasm.br が即時圧縮より良い）
□ .wasm は内容ハッシュのファイル名を使う（安定した URL → 再訪でコードキャッシュに当たる）
□ 測定時にクロスオリジン隔離の状態が一致していることを確認した（未隔離ではタイマの精度が落ちる）
□ Worker が複数あるときは、postMessage で WebAssembly.Module を渡し、各自で再コンパイルしない
□ 本番の問題でスタックを復元するため、シンボル付きのビルド成果物を用意した
□ 対象端末（低性能スマートフォンを含む）で実測した。開発機だけで走らせていない
```
