# 付録B：用語とツールのクイックリファレンス

> これは**参照表**であって教材ではない。各行の最後の列は、それが本書のどこに出てくるかを示す——**分からない用語を見たらまずここを引き、なぜかを理解したくなったら本文へ飛べばよい。**

## 1. 中核概念の用語

| 用語 | 一行の説明 | 本書のどこか |
|---|---|---|
| **WebAssembly (Wasm)** | 仕様で定義された抽象スタックマシンのバイナリ命令形式。いかなる物理 CPU の機械語でもない | 第 2 章 |
| **WAT (WebAssembly Text)** | Wasm の読めるテキスト形式。バイナリと一対一に対応する（`wasm2wat` で可逆変換できる） | 第 2、9 章 |
| **線形メモリ (Linear Memory)** | 一続きの、アドレス可能なバイト配列。1 ページ = 64 KiB、伸びるだけで縮まない | 第 2、8 章 |
| **トラップ (Trap)** | 実行時の捕捉不能なエラー（境界外、ゼロ除算、unreachable）。JS 側では `RuntimeError` として現れる | 付録 A |
| **ガードページ (Guard Page)** | エンジンが 8 GiB の仮想アドレス空間を予約し、MMU に境界検査を無料でさせる技 | 第 2、8 章 |
| **構造化制御フロー** | Wasm に `goto` はなく、`block`/`loop`/`if` と外向きに跳ぶ `br` だけがある——単一パス検証の前提である | 第 2 章 |
| **検証器 (Validator)** | ロード時に O(n) の単一パス検査を行う：スタック型の一貫性、制御フローの構造化、添字が範囲内か | 第 2 章 |
| **階層型コンパイル (Tiering)** | Liftoff（速いコード生成）→ TurboFan（最適化されたコード生成）の二本立ての競走 | 第 2 章 |
| **ストリーミングコンパイル** | `instantiateStreaming`：最初のバイトが届いた時点でコンパイルを始める | 第 2、5 章 |
| **グルーコード (Glue Code)** | JS 側で型変換、メモリ管理、API の橋渡しを担う層 | 第 2 章 |
| **ゼロコピー (Zero-copy)** | 同じ `ArrayBuffer` の上に `TypedArray` でビューを開き、データを運ばないこと | 第 2、6 章 |
| **SoA (Structure of Arrays)** | `[{x,y,z}...]` を三本の連続配列へ変える——キャッシュに優しい配置 | 第 6 章 |
| **CSR / CSC** | 圧縮疎行／列形式。疎行列の標準的な緊密表現 | 付録 E、F |
| **クロスオリジン隔離** | COOP と COEP が同時に満たされたときのページの状態。`SharedArrayBuffer` の前提 | 第 3、5 章 |
| **ケイパビリティベース・セキュリティ** | モジュールは既定で手ぶらであり、能力はホストが明示的に手渡さねばならない | 第 1、7 章 |
| **Component Model / WIT** | Wasm モジュール同士が高水準の型で会話するためのインタフェースモデルと記述言語 | 第 7 章、付録 A |
| **LEB128** | 可変長整数の符号化。Wasm のあらゆる長さと添字がこれを使う | 付録 M §1 |
| **多相スタック (Polymorphic Stack)** | `unreachable` のあとの死んだコードが検証を通る仕組み | 付録 M §2 |
| **Table / `call_indirect`** | Wasm に関数ポインタはなく、関数ポインタとは実は「テーブルの添字」である | 付録 M §3 |
| **Tag / `exnref`** | Wasm 3.0 の例外処理のタグと不透明な例外参照 | 付録 M §4 |
| **JSPI** | JavaScript Promise Integration：エンジンがスタックのレベルで Wasm を中断／再開し、同期のコードが Promise を待てるようにする | 第 3 章の壁その七、付録 M §5 |
| **Asyncify** | JSPI 以前の代替案：Binaryen がモジュール全体を書き換えて中断を模倣する（高い） | 付録 M §5 |
| **Relaxed SIMD** | 決定性を捨ててハードウェアへの対応づけを買う。**決定性を要する場面では禁止せねばならない** | 付録 M §7 |
| **Multiple memories** | Wasm 3.0：一つのモジュールに複数の線形メモリ。各枚は依然として wasm32 である | 第 8 章シナリオ 4、付録 M §8 |
| **proxy-wasm** | Envoy/Istio などのプロキシが採用する Wasm プラグインの ABI | 付録 M §11 |

---

## 2. ストレージ関連

| 用語 | 説明 | 適用 |
|---|---|---|
| **MEMFS** | Emscripten が線形メモリの中に偽造した POSIX ファイルシステム | 一時的な中間ファイル（**4 GB の枠を食う**） |
| **IDBFS** | MEMFS を一括で IndexedDB へ同期する（`FS.syncfs`） | ゲームのセーブ、設定（数百 KB） |
| **WASMFS** | Emscripten の新世代ファイルシステムバックエンド。OPFS へ直通できる | MEMFS/IDBFS を置き換える方向 |
| **OPFS** | Origin Private File System。ブラウザがオリジンごとに開く私有ディスク空間 | **永続化が要るすべて** |
| **`opfs` VFS**（SQLite） | 第一世代の OPFS バックエンド。非同期プロキシ + `Atomics.wait` に依る。**`SharedArrayBuffer`／クロスオリジン隔離が要る** | 複数接続が要るとき |
| **`opfs-sahpool` VFS** | 同期アクセスハンドルのプール。**COOP/COEP が要らず、公式ドキュメントで最速と記されている**。複数接続に非対応 | **静的ホスティングの第一選択** |
| **`createSyncAccessHandle()`** | OPFS の同期ランダムアクセスハンドル（**Worker の中でしか使えない**） | データベース、大きなファイルのストリーミング |
| **`navigator.storage.persist()`** | データを persistent と印すよう要求し、ディスク圧下での追い出しを避ける | 重要なデータ |
| **VFS (Virtual File System)** | SQLite が移植性のために設計したストレージ抽象層。OPFS VFS はその一実装である | 第 7 章 |

---

## 3. ツールチェーン

### コンパイラ／ツールチェーンのフロントエンド

| ツール | 言語 | 特性 |
|---|---|---|
| **Emscripten** (`emcc`) | C / C++ | **POSIX 環境を丸ごと模倣する**（libc、ファイルシステム、SDL→WebGL、pthread→Worker）。既存の大規模 C/C++ プロジェクトを移植する第一選択 |
| **`wasm-pack` / `wasm-bindgen`** | Rust | **型の橋渡しだけ**を行い、グルーが簡潔。ゼロから書く新規プロジェクトの第一選択 |
| **`cargo` + `wasm32-unknown-unknown`** | Rust | JS バインディングを一切持たない素の Wasm |
| **TinyGo** | Go | Go の実行環境のサイズを大幅に縮める（代価：対応は部分集合） |
| **AssemblyScript** | TS 風の構文 | 構文が TypeScript に近く、直接 Wasm へコンパイルする。フロントエンド開発者の滑らかな入口 |
| **Zig** | Zig | `wasm32-freestanding` / `wasm32-wasi` をネイティブに対応。実行環境の負担なし |
| **Blazor** | C# | .NET エコシステム。サイズとコールドスタートが主な代価 |

### バイナリツール

| ツール | 用途 |
|---|---|
| **`wasm-opt`**（Binaryen） | **投資対効果が最も高い最適化ツール**。`-Oz` はサイズ優先、`-O3` は速度優先、`--strip-debug` |
| **`wasm2wat` / `wat2wasm`**（WABT） | バイナリ ↔ テキスト形式の可逆変換 |
| **`wasm-objdump`**（WABT） | セクションを見る、逆アセンブル（`-d`）、import/export を見る（`-x`） |
| **`wasm-decompile`**（WABT） | C 風の読める疑似コードを出す（逆解析の最初の一歩） |
| **`wasm-strip`**（WABT） | カスタムセクションを剥がす |
| **`twiggy`** | **サイズの診断**：`twiggy top`（誰がサイズを食っているか）、`twiggy dominators`（誰が誰を引きずり込んでいるか） |
| **`wasm-snip`** | 指定した関数を手動で `unreachable` へ置き換え、不要なコード経路を切り落とす |
| **`wasm-split`**（Binaryen） | プロファイルの結果でモジュールを primary + secondary へ切り、遅延読み込みする |
| **`wizer`** | **ビルド時の事前初期化**：初期化を走らせきり、メモリの状態を新しいモジュールへスナップショットする（付録 N §10-2） |
| **`wasmtime compile`** | バックエンドの AOT。`.cwasm` を出力し、実行時のコンパイルをゼロにする |
| **WABT の `wasm-validate`** | モジュールが正しいかをオフラインで検証する |

### 実行環境（バックエンド）

| 実行環境 | 位置づけ |
|---|---|
| **Wasmtime** | Bytecode Alliance が主導。WASI の参照実装。Cranelift をコード生成のバックエンドとする |
| **WasmEdge** | CNCF サンドボックスプロジェクト。クラウドネイティブ、マイクロサービス、AI 推論に最適化（GPU 呼び出しに対応） |
| **Wasmer** | 可搬性と多言語の埋め込みを重視。WAPM のパッケージエコシステムを持つ |
| **WAMR** (WebAssembly Micro Runtime) | 極めて軽量。IoT と組み込みに向く |
| **Spin** (Fermyon) | Wasm マイクロサービスを構築・実行するフレームワーク。サーバレスの形態 |
| **wasm3** | 極めて速いインタプリタ（JIT なし）。制約の多い環境に向く |

### ブラウザ側の補助

| ツール | 用途 |
|---|---|
| **`coi-serviceworker`** | フロントで COOP/COEP を合成し、静的ホスティングでも `SharedArrayBuffer` を使えるようにする（第 5 章） |
| **`COEP: credentialless`** | `require-corp` より穏やかな隔離モード：表明のないクロスオリジンリソースを許すが、資格情報なしで要求する |
| **`'wasm-unsafe-eval'`** | CSP のキーワード。Wasm のコンパイルだけを許し、`eval()` は許さない（Chrome 97+／FF 102+／Safari 16+） |
| **`wasm-split`** | Emscripten/Binaryen のモジュール分割ツール。主モジュール + 遅延読み込みの副モジュール |
| **C/C++ DevTools Support (DWARF)** | Chrome 拡張。DevTools の中で C++ のソースを見て、ブレークポイントを張り、変数を見られるようにする |
| **Chrome DevTools の Memory / Performance パネル** | Wasm のメモリ増加とコンパイル時間を観察する |
| **`performance.measureUserAgentSpecificMemory()`** | タブ全体のメモリを測る（Wasm を含む） |
| **圧縮辞書転送**（RFC 9842） | ユーザがキャッシュした旧版を辞書として新版を圧縮する。`dcb`/`dcz` 符号化。Chrome/Edge 130+（付録 N §7-2） |
| **`TextEncoder.encodeInto()`** | 文字列を Wasm のメモリへ直接符号化して書く。中間の確保がゼロ（付録 N §13） |

---

## 4. 主要なコンパイルフラグのクイックリファレンス

```toml
# ── Rust: Cargo.toml（リリース版）────────────────────────
[profile.release]
opt-level = 3        # 速度優先。サイズ優先なら "z"、バランスなら "s"
lto = true           # リンク時全体最適化（クレート横断のインライン展開 + 死コード削除）
codegen-units = 1    # LTO に完全な視野を与える
panic = "abort"      # unwinding テーブルを削る（サイズも複雑さも一層減る）
strip = true         # シンボルを剥がす（name セクション）

[lib]
crate-type = ["cdylib"]
```

```bash
# ── Rust: SIMD を有効にする ─────────────────────────────
RUSTFLAGS="-C target-feature=+simd128" wasm-pack build --target web --release

# ── Emscripten ──────────────────────────────────────────
emcc app.cpp -O3 \
  -msimd128 \                       # SIMD
  -pthread -s PTHREAD_POOL_SIZE=4 \ # マルチスレッド（クロスオリジン隔離が要る！）
  -s ALLOW_MEMORY_GROWTH=1 \        # memory.grow を許す
  -s INITIAL_MEMORY=64MB \
  -s MAXIMUM_MEMORY=2GB \
  -s EXPORTED_FUNCTIONS='["_main","_process"]' \
  -s MODULARIZE=1 -s EXPORT_ES6=1 \ # ES module を出力する
  -flto --closure 1 \               # LTO + Closure でグルーを圧縮
  -o app.js

# ── デバッグビルド（シンボルと DWARF を残す）─────────────
emcc app.cpp -g -gsource-map -s ASSERTIONS=2 -fsanitize=address -o app.js

# ── 後処理 ──────────────────────────────────────────────
wasm-opt -Oz --strip-debug --strip-producers app.wasm -o app.opt.wasm
twiggy top -n 20 app.opt.wasm
```

---

## 5. `--target` は正しく選べているか（`wasm-pack`）

| target | 出力 | どこで使うか |
|---|---|---|
| `web` | ES module。`<script type="module">` で直接読み込める | **静的ホスティング配備の正解** |
| `bundler` | webpack/rollup/vite 向けのモジュール | バンドラのあるプロジェクト |
| `nodejs` | CommonJS | サーバサイド |
| `no-modules` | グローバル変数にぶら下がる従来型スクリプト | 旧環境、Worker で `importScripts` を使う場合 |

---

## 6. よくあるエラーメッセージ → 病因の対照

| 目にするもの | 実際の原因 |
|---|---|
| `404`（`.wasm` の読み込み時） | ① `pkg/` が `.gitignore` に無視された ② 絶対パスを使ったがサイトがサブパスにある ③ Jekyll が `_` 始まりのフォルダを食った（`.nojekyll` を置く） |
| `TypeError: WebAssembly.instantiateStreaming(): Incorrect response MIME type` | サーバが `Content-Type: application/wasm` を返していない |
| `ReferenceError: SharedArrayBuffer is not defined` | クロスオリジン隔離がない（第 5 章参照） |
| `RuntimeError: memory access out of bounds` | Wasm 内部のメモリエラー（ASan ビルドで捕まえる） |
| `TypeError: Cannot perform Construct on a detached ArrayBuffer` | `memory.grow` のあとに `TypedArray` のビューを取り直していない |
| `LinkError: import object field 'xxx' is not a Function` | `importObject` にモジュールが要求する import が欠けている |
| `RangeError: WebAssembly.Memory(): could not allocate memory` | ブラウザのメモリ上限にぶつかった（第 8 章参照） |
| すべて正常なのに結果が文字化けする | 文字列の符号化が合っていない（UTF-8 vs UTF-16）か、ポインタの渡し方を誤っている |
