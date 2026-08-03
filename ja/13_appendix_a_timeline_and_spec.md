# 付録A：Wasm の年表と仕様クイックリファレンス

> この付録の位置づけは「調べられて、突き合わせられる」ことである。**年表と仕様の状態は、WebAssembly 公式仕様（webassembly.github.io/spec）、提案一覧（github.com/WebAssembly/proposals）、MDN を最終的な根拠とすること**——本書は 2026 年に書かれており、提案の状態は動く。

---

## 1. 年表

| 時期 | 出来事 | 意義 |
|---|---|---|
| 2011–2013 | **Google NaCl / PNaCl** | x86 機械語の静的検証 + セグメントサンドボックス。のちに LLVM bitcode の配布へ移行。技術的成功、政治的失敗（Chrome だけが対応） |
| 2013 | **Mozilla asm.js** | JavaScript の厳格な部分集合。`x\|0` / `+x` で型を注釈する。**プラグインなしでネイティブに近い性能が得られ、四つのエンジンすべてが実装できることを証明した** |
| 2013 以降 | **Emscripten の成熟** | LLVM → asm.js（のち → Wasm）の C/C++ コンパイルパイプライン。Unreal Engine などの大型プロジェクトがブラウザへ移れるようになった |
| **2015-06** | **四者が共同で WebAssembly を発表** | Google、Mozilla、Microsoft、Apple。まとまった鍵は「意図的に小さく作る」ことだった |
| 2017-03 以降 | **四大ブラウザが Wasm MVP を内蔵** | Chrome、Firefox、Safari、Edge。MVP が共通の能力になる |
| 2019 以降 | **WASI 提案が登場** | Wasm がブラウザを離れ、サーバサイド、クラウドネイティブ、エッジコンピューティングへ進出 |
| 2019 | Docker 創業者 Solomon Hykes のツイート | 「2008 年に WASM+WASI があったなら、Docker を作る必要などなかった」（しばしば切り取られる。第 1 章の ⚠️ 参照） |
| **2019-12** | **W3C が正式に勧告（Recommendation）に定める** | WebAssembly Core Specification 1.0。HTML、CSS、JavaScript と並ぶ Web の第四の中核言語となる |
| 2020 前後 | Bytecode Alliance の設立、Wasmtime / Lucet / WAMR などの実行環境が形になる | バックエンドエコシステムの基盤 |
| 2020–2021 | SIMD、bulk memory、reference types、multi-value などの提案が順次着地 | MVP が負った技術的負債の返済が始まる |
| 2021 以降 | WasmEdge が CNCF サンドボックスへ。Fermyon Spin などのフレームワークが登場 | クラウドネイティブが正式に Wasm を受け入れる |
| 2022 前後 | **Wasm 2.0**（SIMD、bulk memory、reference types、multi-value などを含む） | 核心仕様の第二のマイルストーン |
| 2023–2024 | **Component Model / WIT が形になり、WASI 0.2 (Preview 2) が公開** | 「単体のモジュール」から「組み合わせ可能なコンポーネント」へ |
| 2025-04 | **JSPI（JavaScript Promise Integration）が Phase 4 へ** | 同期の Wasm コードがついに非同期の Web API を呼べるようになった |
| **2025-09** | **★ WebAssembly 3.0 の完成が宣言され、現行標準となる** | **MVP のあの技術的負債は、ここでおおむね返し終えた**（下表参照） |
| 2025 以降 | JSPI が **Chrome 137、Firefox 139** で出荷 | 付録 M 第 5 節参照 |
| 進行中 | Component Model、stack switching、JS String Builtins、custom page sizes、shared-everything threads… | 下の提案クイックリファレンス参照 |

> ⚠️ **本書の改訂に関する注記**：Wasm 3.0 は分水嶺である。**それ以前、GC／memory64／末尾呼び出し／例外処理／multiple memories はどれも「提案」だった。それ以後、それらは核心仕様の一部である。** これらを「提案」「実験的」と呼ぶ資料に出会ったら（**本書の初稿も含めて**）、この表を根拠とすること——それらの記述は 3.0 より前に書かれている。

---

## 2. バイナリ形式クイックリファレンス

**ファイルの冒頭はつねに 8 バイト**：`00 61 73 6D`（`\0asm` マジックナンバー）+ `01 00 00 00`（バージョン 1）。

**セクションの順序は仕様で強制されている**。これこそが単一パスの線形検証とストリーミングコンパイルの前提である。

| ID | 名称 | 内容 | 剥がせるか |
|---|---|---|---|
| 0 | Custom | `name`（関数／変数名）、DWARF デバッグ情報、ソースマップへのリンク、言語メタデータ | **✅ 可（`strip`）** |
| 13 | Tag | 例外タグ（Wasm 3.0 の例外処理） | ❌ |
| 1 | Type | すべての関数シグネチャ | ❌ |
| 2 | Import | ホストから受け取る関数／メモリ／テーブル／グローバル | ❌ |
| 3 | Function | 関数 → シグネチャの対応 | ❌ |
| 4 | Table | 関数参照テーブル（間接呼び出しの対象） | ❌ |
| 5 | Memory | 線形メモリの初期ページ数と上限 | ❌ |
| 6 | Global | グローバル変数 | ❌ |
| 7 | Export | **外部へ公開するすべて（攻撃者はつねに見られる）** | ❌ |
| 8 | Start | インスタンス化後に自動実行される関数 | ❌ |
| 9 | Element | テーブルの初期内容 | ❌ |
| 10 | Code | 各関数の命令とローカル変数 | ❌ |
| 11 | Data | **線形メモリの初期データ（平文文字列はここにある）** | ❌ |
| 12 | DataCount | データセグメントの数（bulk memory 提案が導入） | ❌ |

**中核の型**：

| 分類 | 型 |
|---|---|
| 数値 | `i32`、`i64`、`f32`、`f64` |
| ベクトル（SIMD 提案） | `v128` |
| 参照（reference types 提案） | `funcref`、`externref` |
| ヒープ型（GC、Wasm 3.0） | `struct`、`array`、`i31`、そして型付き参照 `(ref $T)` |

**メモリの単位**：**1 ページ = 64 KiB**。`memory.grow` は増やすだけで、`shrink` はない。

---

## 3. 仕様の状態クイックリファレンス（工学的判断への影響順）

### 3-1　すでに核心仕様に入っているもの（Wasm 1.0 / 2.0 / **3.0**）

> **これらはもう「提案」ではない。これらが Wasm である。** 残る問いは「あなたの対象実行環境が追いついているか」だけだ。

| 特性 | 入ったバージョン | 何を解決するか | あなたにとっての意味 |
|---|---|---|---|
| **Bulk memory** | 2.0 | `memory.copy` / `memory.fill` などの一括操作 | `memcpy` 系の操作を大幅に高速化 |
| **Reference types** | 2.0 | `externref` が不透明なホスト参照を保持する | JS↔Wasm の橋渡しコストを縮める |
| **Multi-value** | 2.0 | 関数が複数の値を返せる | 戻り値のためだけにメモリを確保する定型句が減る |
| **SIMD (`v128`)** | 2.0 / 3.0 で確立 | 一命令で複数のデータを処理 | 2〜4 倍の加速。**ただし 128 ビット幅しかなく、AVX2/AVX-512 よりはるかに狭い** |
| **Threads / Atomics** | — | 共有線形メモリ + アトミック操作 | **`SharedArrayBuffer` に依存し、クロスオリジン隔離が要る**（第 5 章の筆頭の障害） |
| **★ GC** | **3.0** | `struct`/`array`/`i31` + ホストの GC | **Kotlin/Dart/Java のサイズが構造的に下がる。Rust/C/C++ にはほぼ無用** |
| **★ Memory64** | **3.0** | `i64` のアドレス（メモリとテーブル） | 4 GiB を突破する。**ただしガードページの無料の境界検査を失い、性能上の代価がある**（第 8 章） |
| **★ Multiple memories** | **3.0** | 一つのモジュールが複数の線形メモリを宣言し、そのあいだで直接データを運べる | **第 8 章の第三の突破経路**：wasm32 のままデータを複数の 4 GiB メモリへ分ける |
| **★ Exception handling** | **3.0** | 例外タグ（Tag セクション）とペイロード | C++ の例外が JS のトランポリンを要さなくなり、境界越えのオーバーヘッドが大きく下がる（付録 M 第 4 節） |
| **★ Tail call (`return_call`)** | **3.0** | 末尾呼び出しの最適化 | **関数型言語の深い再帰がスタックを溢れさせなくなる**（付録 F の事例 92 の鍵） |
| **★ Typed function references** | **3.0** | `(ref $sig)` 型付きの関数参照 | 間接呼び出しで実行時のシグネチャ検査を省ける（付録 M 第 3 節） |
| **★ Extended const expressions** | **3.0** | 初期化式で算術ができる | 初期化のためだけに start 関数を走らせることが減る |
| **★ Branch hinting** | **3.0** | 分岐確率のヒント | エンジンがより良い機械語を出す助けになる |
| **★ Relaxed SIMD** | **3.0** | 一部の SIMD の意味論を緩め、ハードウェアへよりよく対応づける | 性能と引き換えに、**結果がプラットフォームによって異なりうる**——チェーン上および決定性を要するあらゆる場面で禁止せねばならない |

### 3-2　核心仕様の外にあるが、すでに使えるもの

| 特性 | 状態 | 意義 |
|---|---|---|
| **JSPI（JS Promise Integration）** | **Phase 4（2025-04 標準化）**。Chrome 137、Firefox 139 で出荷 | **同期の Wasm コードが非同期の Web API を呼べる**——Wasm が「ブロックできない」という壁に穴を開けた（付録 M 第 5 節） |
| **Component Model / WIT** | 進化中 | WASI 0.2 の基礎。「境界の料金所」を根本から解こうとしている |
| **JS String Builtins** | 進化中 | Wasm が JS の文字列を直接操作できるようにし、符号化の税を減らす |
| **Stack switching** | 進化中 | コルーチンのネイティブ対応（JSPI はその特殊な応用の一つ） |
| **Custom page sizes** | 進化中 | 組み込みの場面が 64 KiB のページサイズに縛られずに済むようにする |

> **提案は五段階に分かれる**：Phase 0（前段階の構想）→ 1（提案）→ 2（仕様草案）→ 3（実装草案）→ 4（標準化）。**状態は時とともに変わる。公式の proposals リポジトリと `webassembly.github.io/spec` に記されたバージョンの日付を根拠とすること。**

---

## 4. WASI の二つの世代の対照

| | `wasi_snapshot_preview1` | **WASI 0.2 (Preview 2)** |
|---|---|---|
| モデル | POSIX 風のファイルディスクリプタ | **Component Model + WIT のインタフェース定義** |
| インタフェースの形 | 一つの大きな平坦な関数群 | `wasi:io`、`wasi:filesystem`、`wasi:sockets`、`wasi:http`、`wasi:clocks`、`wasi:random` などへ分割 |
| Rust の target | `wasm32-wasip1` | `wasm32-wasip2` |
| エコシステムの成熟度 | **高い**（TinyGo と多くのツールチェーンが対応） | 進化中。ツールチェーンが順次追いついている |
| 組み合わせ可能性 | 悪い（単体） | **良い**（あるコンポーネントに `wasi:clocks` だけを与え、ファイルシステムを与えないことができる） |

**ケイパビリティベース・セキュリティの中核の構文**：

```bash
# ./my_storage というディレクトリだけを認可し、モジュールから見た /sandbox へ写像する
wasmtime run --dir=./my_storage::/sandbox my_server.wasm
# 環境変数も明示的に与える
wasmtime run --env API_MODE=prod app.wasm
# ネットワーク（0.2）
wasmtime serve --wasi inherit-network app.wasm
```

---

## 5. ブラウザ API クイックリファレンス

```javascript
// ── 読み込み（★ 第一選択：ダウンロードしながらコンパイル）─────────────
const { instance, module } = await WebAssembly.instantiateStreaming(
  fetch("app.wasm"),            // サーバは Content-Type: application/wasm を返さねばならない
  importObject                  // モジュールへ手渡す能力
);

// ── コンパイルだけしてインスタンス化しない（module を複数の Worker で使い回せる）──
const mod = await WebAssembly.compileStreaming(fetch("app.wasm"));
const inst = await WebAssembly.instantiate(mod, importObject);

// ── メモリ ───────────────────────────────────────────────
const mem = new WebAssembly.Memory({ initial: 16, maximum: 256, shared: false });
//                                    ↑ ページ数（1 ページ 64 KiB）  ↑ マルチスレッドには shared:true が要る
new Uint8Array(mem.buffer);      // ★ grow のあとは必ずビューを取り直す

// ── テーブル（間接呼び出しの対象）─────────────────────────
const tbl = new WebAssembly.Table({ initial: 2, element: "anyfunc" });

// ── エラーの型 ───────────────────────────────────────────
WebAssembly.CompileError    // バイナリ形式の誤り、または検証の失敗
WebAssembly.LinkError       // import が合わない
WebAssembly.RuntimeError    // 実行時のトラップ（境界外、ゼロ除算、unreachable）

// ── クロスオリジン隔離の検出 ─────────────────────────────
if (self.crossOriginIsolated) { /* SharedArrayBuffer が使える */ }
```

---

## 6. よくあるトラップとその出所

| トラップのメッセージ | 原因 |
|---|---|
| `memory access out of bounds` | 現在の線形メモリのサイズを超えた読み書き |
| `integer divide by zero` | `i32.div_s` / `i32.rem_s` などでのゼロ除算 |
| `integer overflow` | `i32.div_s(INT_MIN, -1)` のような溢れ |
| `invalid conversion to integer` | `f64` → `i32` 変換で値が NaN か範囲外（非飽和版） |
| `unreachable` | `unreachable` 命令に到達した（多くは Rust の `panic!` か C++ の `abort()`） |
| `indirect call type mismatch` | 間接呼び出しで実際の関数シグネチャが宣言と合わない |
| `call stack exhausted` | 再帰が深すぎる（**`return_call` の末尾呼び出しはまさにこのためにある**。Wasm 3.0） |
| `null function or function signature mismatch` | テーブルの項目が空か、シグネチャが合わない |

---

## 7. 参考資源

| 主題 | 場所 |
|---|---|
| 核心仕様 | `webassembly.github.io/spec/core/` |
| 提案一覧と段階 | `github.com/WebAssembly/proposals` |
| MDN WebAssembly ガイド | `developer.mozilla.org/docs/WebAssembly` |
| Emscripten ドキュメント | `emscripten.org/docs` |
| Rust and WebAssembly Book | `rustwasm.github.io/docs/book/` |
| `wasm-bindgen` ガイド | `rustwasm.github.io/wasm-bindgen/` |
| WABT（バイナリツール群） | `github.com/WebAssembly/wabt` |
| Binaryen（`wasm-opt`） | `github.com/WebAssembly/binaryen` |
| Bytecode Alliance / Wasmtime | `bytecodealliance.org` |
| WASI と WIT | `wasi.dev` · `component-model.bytecodealliance.org` |
