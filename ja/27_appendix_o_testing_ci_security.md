# 付録O　テスト、CI、そして実行時のセキュリティ

> これは本書に最後に足された一枚であり、それが埋めるのは、かなり具合の悪い穴である：**先の十四の付録は Wasm をどう作り、どう小さくし、どう速くし、どう盗まれにくくするかを教えたが——それが正しいことをどう確かめるかは、どれも教えていない。**
>
> 第 3 章はこう言った：**「ある技術の成熟度を測るのに最も確かな指標は、それがどれだけ速く走るかではなく、壊れたときにどれだけ調べやすいかである。」** この付録は、その一文の操作の手引きである。

---

## 1. Wasm のテストの、三層の角錐

**Wasm のプロジェクトのテストには特殊なところがある：同じコードが三つの環境で走り、そのそれぞれが捕まえる誤りがまったく違うのだ。**

```
        ┌───────────────────────────────┐
        │  ③ ブラウザの統合テスト（最も遅く、最も本物） │  ← 捕まえる：JS の束縛、DOM/API との
        │     wasm-bindgen-test          │        やり取り、OPFS/Worker の振る舞い、実エンジンの差
        ├───────────────────────────────┤
        │  ② Wasm 環境の単体テスト        │  ← 捕まえる：Wasm 固有の振る舞い
        │     wasm32 target + Node/WASI  │        （メモリの整列、i32 の溢れ、境界越え）
        ├───────────────────────────────┤
        │  ① native の単体テスト（最も速く、最も多い） │  ← 捕まえる：純粋なロジックの誤り
        │     cargo test / ctest         │        **この層が 80% を占めるべきである**
        └───────────────────────────────┘
```

**最も重要な一つの原則**：**第 ① 層で捕まえられる誤りを、決して第 ③ 層まで引っ張るな。** native のテストは一回がミリ秒、ブラウザの統合テストは一回が数十秒である——**純粋なロジックを Wasm に依らない形へ書くことは、Wasm のプロジェクトで最もやる値打ちのあるアーキテクチャの投資である。**

```rust
// ✅ この形なら 80% のテストが native で走る
mod core {                                   // 純粋なロジック。wasm-bindgen に触れない
    pub fn transform(input: &[u8]) -> Vec<u8> { /* ... */ }
}

#[cfg(target_arch = "wasm32")]
mod bindings {                               // この層だけが Wasm の環境を要する
    use wasm_bindgen::prelude::*;
    #[wasm_bindgen]
    pub fn transform(input: &[u8]) -> Vec<u8> { super::core::transform(input) }
}

#[cfg(test)]
mod tests {                                  // cargo test でそのまま走る。ブラウザは要らない
    #[test] fn roundtrip() { assert_eq!(super::core::transform(b"abc"), b"..."); }
}
```

---

## 2. `wasm-bindgen-test`：本物のエンジンの中でテストを走らせる

```rust
use wasm_bindgen_test::*;

// ブラウザの中で走らせる（既定は Node）
wasm_bindgen_test_configure!(run_in_browser);

#[wasm_bindgen_test]
fn works_in_wasm() {
    assert_eq!(crate::core::transform(b"abc"), b"...");
}

// ★ 非同期のテスト：OPFS、fetch、あらゆる Promise
#[wasm_bindgen_test]
async fn opfs_roundtrip() {
    let engine = WasmStorageEngine::new().await.unwrap();
    engine.save_file("t.bin", &[1, 2, 3]).await.unwrap();
    assert_eq!(engine.load_file("t.bin").await.unwrap(), vec![1, 2, 3]);
}

// Worker の中でだけ走らせる（sync access handle の仕様上の制約。第 7 章参照）
wasm_bindgen_test_configure!(run_in_dedicated_worker);
```

```bash
wasm-pack test --headless --chrome        # ヘッドレスの Chrome
wasm-pack test --headless --firefox
wasm-pack test --node                     # 最も速いが、ブラウザの API は取れない
```

**実務の三つの要点**：

1. **`run_in_dedicated_worker` は OPFS のテストの必要条件である**——`createSyncAccessHandle` はメインスレッドでは端的に失敗する（第 7 章）。
2. **テストのファイルはそれぞれ独立した Wasm のモジュールである**ので、テストのあいだで**線形メモリは共有されない**——これは良いこと（隔離）だが、テストの起動の費用が安くないことも意味する。
3. **`--headless` には対応する driver が要る**（chromedriver / geckodriver）。CI では併せて入れること。

---

## 3. C/C++ の経路

```bash
# Emscripten：node で実行できるテストをそのまま出す
emcc test.cpp -o test.js -sEXIT_RUNTIME=1 -sASSERTIONS=2
node test.js

# ★ Sanitizer は Wasm でも使える——「サンドボックスの中に ASLR/canary が無い」を補う、最も実際的な手
emcc app.cpp -fsanitize=address -sALLOW_MEMORY_GROWTH=1 -o app-asan.js
emcc app.cpp -fsanitize=undefined -o app-ubsan.js
```

**なぜ Sanitizer が Wasm でとりわけ重いのか**（第 2 章の ⚠️ からの直接の帰結）：

> 線形メモリの内側には **ASLR も NX も stack canary も無い**。x86 ならオペレーティングシステムに止められて即座に落ちるはずのバッファオーバーフローが、Wasm では**静かに隣のデータを壊してそのまま走り続けうる**——あなたは数百行あとで訳の分からない誤った結果を見ることになる。はっきりした segfault ではなく。
>
> **ASan/UBSan は、Wasm の中でそれらの保護を取り戻せる唯一の方法である。** 代価は体積も速度も目に見えて悪くなることなので、それは**テストのビルド**であって、公開のビルドではない。

**WASI の場面**：

```bash
# wasmtime でテストのバイナリを直に走らせる
cargo test --target wasm32-wasip1 --no-run
wasmtime run --dir=. target/wasm32-wasip1/debug/deps/mytest-*.wasm
```

---

## 4. Fuzzing：Wasm でとりわけやる値打ちのあること

**理由はまっすぐだ**：Wasm のモジュールの入口はたいてい「バイトの塊を食わせる」であり、**それはまさに fuzzing が最もよく効く形である。**

```rust
// fuzz_targets/parse.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    let _ = mycrate::core::parse(data);      // panic せず、範囲を超えず、無限に回らないこと
});
```

```bash
cargo fuzz run parse -- -max_total_time=300
```

**そして Wasm は fuzzing に、もう一つの利をくれる**：**fuzzer そのものを Wasm のサンドボックスの中で走らせられる**ので、対象のコードが仕込まれた入力に破られても、**ホストには絶対に届かない**（これがまさに付録 E の事例 50「フォントのファジング」の原理である）。

**必ず fuzz すべき三つの場所**：あらゆる**パーサ**（ファイル形式、プロトコル、入力）、あらゆる**索引の計算**、そして **JS から渡されてくる長さ／変位**。

---

## 5. CI：そのまま使える workflow 一式

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

      # ① native の単体テスト（最も速く、誤りの 80% を捕まえる）
      - run: cargo test --all-features
      - run: cargo clippy --all-targets -- -D warnings

      # ② Wasm 環境のテスト
      - run: curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh
      - run: wasm-pack test --node

      # ③ ブラウザの統合テスト
      - uses: browser-actions/setup-chrome@latest
      - run: wasm-pack test --headless --chrome

      # ④ ★ 体積の後退の門番（付録 N 参照）
      - name: Build & check size budget
        run: |
          wasm-pack build --target web --release
          npm install -g binaryen
          f=$(ls pkg/*_bg.wasm)
          wasm-opt -Oz --strip-debug "$f" -o "$f"
          raw=$(stat -c%s "$f")
          br=$(brotli -q 11 -c "$f" | wc -c)
          echo "raw=$raw brotli=$br"
          # 予算を超えたら CI を赤くする——体積の後退は性能の後退と同じく門番が要る
          test "$br" -le 900000 || { echo "::error::Brotli size $br > budget 900000"; exit 1; }

      # ⑤ ★ セキュリティの赤線（第 9 章）
      - name: Secret scan in binary
        run: |
          if strings pkg/*_bg.wasm | grep -Eq 'sk-|AKIA|BEGIN [A-Z ]*PRIVATE KEY'; then
            echo "::error::possible secret embedded in wasm"; exit 1
          fi
```

**第 ④ と第 ⑤ の段こそ、この workflow の本当の値打ちである。** それらが守るのは、**ゆっくり悪くなるだけで、突然は壊れない**二つのことだからだ：

- **体積の後退**：門番がいなければ、`.wasm` は半年で 800 KB から 4 MB へ育ち、しかもそれについて責を負うべき commit は一つもない。**予算を CI へ書き込み、超過のたびに誰かが「なぜか」を答えるようにせよ。**
- **鍵の漏れ**：第 9 章の二つの物理的な禁域の一つ。**これは `grep` の一行にすぎないが、本書で最も投資対効果の高い CI の一行である。**

---

## 6. エンジン間の差：あるところでだけ壊れるもの

**「Chrome では問題なく動く」は、Wasm のプロジェクトで最もよくある幻である。** 知られている差の源はこうだ：

| 差の点 | 具体的な現れ |
|---|---|
| **メモリの上限** | エンジンとプラットフォームで異なる（第 8 章）。**携帯の端末はデスクトップよりはるかに低い** |
| **機能の対応の度合い** | SIMD、threads、GC、JSPI、memory64 の着地の時期は各社で違う |
| **OPFS の振る舞い** | `createSyncAccessHandle` の並行の意味論、割当と追い出しの方針に実装の差がある（第 7 章） |
| **タイマの精度** | クロスオリジン隔離がないと粗くされ、その粗さの度合いも各社で違う（付録 N §15） |
| **コンパイルの方針** | 段階的なコンパイルの tier-up の時機が違う → **マイクロベンチマークの結果がまったく違いうる** |
| **スタックの深さ** | 再帰でスタックが溢れる閾値が違う |

**対策は一つの規律である**：**CI では少なくとも二つのエンジン（Chrome + Firefox）を走らせ、そして本物の非力な携帯の端末で一度、実際に測れ。** デスクトップの開発機は、あらゆる Wasm のプロジェクトにとって最も危うい楽観の源である。

**実行時の検出 + 退路**：

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

> 💡 **ビルドの変種を複数保守することには費用がかかる。** まず一つ問え：**SIMD の無いあの経路を、私は本当に試したことがあるか？** 一度も実行されたことのない退路は、退路が無いのと同じである——**ただ、気づくのがより遅くなるだけだ。**

---

## 7. 実行時のセキュリティ：「Wasm は安全だ」に覆い隠された攻撃面

**第 3 章は「Wasm だから安全だ」がセキュリティ評価の報告書に書ける文ではないと述べた。この節はその一文を開く。**

### 7-1　三層の攻撃面。守られているのは第一層だけである

```
① モジュールがホストを害せない  ← ✅ この層は Wasm がよく守る（型の体系 + 検証器 + サンドボックス）
② モジュール内部のメモリ安全    ← ❌ まったく守られていない（ASLR/NX/canary が無い。第 2 章参照）
③ 実行環境そのものの実装の穴    ← ❌ 最も語られない層である
```

**第 ③ 層は単独で述べる値打ちがある**：Wasm の実行環境は C++/Rust で書かれた複雑なソフトウェアの大きな塊である——**JIT があり、シグナルのハンドラがあり、メモリの写像の管理がある**。そしてそれらは歴史的に、脆弱性が最も密集してきた場所だ。Wasmtime、V8 の Wasm の実装、その他の実行環境にもセキュリティの公告は出ている。**「Wasm のサンドボックスの中で走る」は危険を下げたのであって、消したのではない。**

**実務の対策**：

| 場面 | 対策 |
|---|---|
| ブラウザ | ブラウザ自身の更新の仕組みに委ねる（この層はあなたには管理できず、管理すべきでもない） |
| **バックエンドで信頼できないモジュールを走らせる** | **実行環境は上流に追随して更新せねばならない**。しかも**Wasm のサンドボックスだけに頼るな**——その外側に OS の水準の隔離（コンテナ / seccomp / 独立したプロセス）をもう一枚かぶせよ |
| 多テナント | インスタンスごとにメモリと実行時間を制限する（燃料／計量）。**一つのテナントの無限ループにプロセス全体を道連れにさせるな** |

> **最後の一項が付録 L と響き合っていることに注意**：FluffOS の Wasm のビルドには **eval limit が無い**ので、「無限の LPC のループがタブ全体を固まらせる」。**ブラウザではこれは利用者の体験の問題にすぎないが、多テナントのバックエンドでは、これは DoS である。**

### 7-2　サプライチェーン：美しい commit の記録を持つ、悪意あるモジュール

**第 9 章で触れたが、開く値打ちがある**：静的ホスティングの「コードは Git に収まっている」は安全に聞こえるが、**ビルドの流れに毒を入れられたパッケージが混じれば、出てくる `.wasm` そのものが悪意あるものになる——そしてそれには同じように清潔な commit の記録が付いている。**

```bash
# 最低限のサプライチェーンの規律
cargo audit                    # 既知の脆弱性
cargo deny check               # ライセンス、出どころ、依存の重複
cargo vet                      # 依存の審査の記録
# C/C++：第三者のライブラリの版を固定して自前でビルドする。出どころの分からない事前コンパイル済みの .a を使うな
```

**加えて、Wasm 固有の二つ**：

1. **出来た `.wasm` に `wasm-objdump -x` をかけ、import の一覧を確かめよ。** **モジュールがどの能力を要求したか、その一覧こそがその攻撃面である**（第 1、7 章の能力ベースの安全）。**画像処理のモジュールが突然ネットワークに関わるホストの関数を import していたら、それは赤い旗である。**
2. **再現できるビルド**：同じソースを CI でコンパイルして出る `.wasm` のハッシュは安定しているべきだ。**それができれば、共同体は「このバイナリは確かにあのソースからコンパイルされた」を検証できる**——これこそ第 9 章のあの「監査されうる ≠ 監査された」への手当てである。

---

## 8. 可観測性：本番で壊れたとき、あなたの手には何があるか

**これは第 3 章「壁八：デバッグが難しい」の、本番の版である。**

```
公開版で何をしたか          →  何を失ったか            →  どう取り戻すか
────────────────────────────────────────────────────────────
strip = true              →  関数名                 →  ★ 記号つきのビルドを一本残す
--strip-debug             →  DWARF                 →  記号のサーバ／artifact へ保管する
panic = "abort"           →  panic の文言とスタック   →  自前の誤りの符号を作る
panic_immediate_abort     →  誤りの符号すら無い       →  要らないと確信できるときだけ使う
```

**最小限で成り立つ、本番の誤りの報告**：

```javascript
window.addEventListener("error", (e) => {
  if (e.error instanceof WebAssembly.RuntimeError) {
    report({
      kind: "wasm_trap",
      message: e.error.message,          // "memory access out of bounds" など
      stack: e.error.stack,              // wasm-function[N] を含む —— 記号が無ければ意味を成さない
      build: __BUILD_HASH__,             // ★ 残しておいた記号つきビルドに対応する
      caps: { simd: ..., threads: ..., isolated: self.crossOriginIsolated },
      memPages: wasm.memory.buffer.byteLength / 65536,   // 上限にぶつかったか？
    });
  }
});
```

**報告する値打ちが最も高い三つの欄**（それぞれ本書で最もよくある三つの本番の故障に対応する）：

| 欄 | 対応する故障 |
|---|---|
| `memPages` | **メモリの上限にぶつかった**（第 8 章）——携帯の端末で最も多い |
| `caps.isolated` / `caps.threads` | **複数スレッドのビルドが、隔離されていないページで走っている**（第 5 章） |
| `build` | **利用者が古い版を掴んでいる**（Service Worker のキャッシュ。付録 C の困りごとの解き方） |

> 💡 座右の一言
> **あるシステムの成熟度は、順調なときにどれだけ美しいかではなく、事故のときにどれだけ手がかりを残すかで測る。** Wasm のツールチェーンはまるごと、あなたに手がかりを捨てさせようとする——記号を strip して体積を省き、panic を abort して体積を省き、表明を切って体積を省く。**そのどれもが、「未来のある午前三時」を売って今日の数十 KB を買う取引である。** この取引は必ずしも損ではないが、それは**明確に下された決断**でなければならず、`Cargo.toml` を一つ複製して貼った副作用であってはならない。**最低限の規律は一つだけだ：何を strip したとしても、strip していない、公開版とバイト単位で対応するビルドを一本残しておくこと。** それは平時には一文の値打ちもないが、事故の日には、あなたの唯一の証拠である。

---

## 9. 公開の前の、完全なチェックリスト（統合版）

> この一覧は付録 C（配備）、付録 N（体積と速度）、そして本付録（テストとセキュリティ）を統合したものである。

```
【正しさ】
□ native の単体テストが通る（ロジックの 80% を覆うべき）
□ wasm-pack test --node が通る
□ wasm-pack test --headless --chrome と --firefox の両方が通る
□ パーサの類のコードに fuzzing をかけた
□ -fsanitize=address のテストのビルドで一巡した

【体積】（付録 N）
□ wasm-objdump -h でセクションの予算を見た（Data の割合が高ければ、まずデータを削る）
□ wasm-opt -Oz --converge をかけた
□ twiggy top / dominators に思いがけない犯人がいない
□ CI に体積の予算の門番がある

【性能】（付録 N）
□ コンパイル / 実体化 / 実行時の初期化を分けて測った
□ 測ったときのクロスオリジン隔離の状態が揃っている（さもないとタイマの精度が落ちる）
□ 熱い経路に細かい境界越えの呼び出しがない
□ 大きな塊の移動はバイトごとのループではなく memcpy である

【配備】（付録 C）
□ Content-Type: application/wasm、Content-Encoding: br
□ 内容ハッシュのファイル名（安定した URL → コードキャッシュ）
□ CSP に 'wasm-unsafe-eval' がある（サイトに CSP があるなら）
□ .nojekyll、相対の経路、await init()
□ 「SharedArrayBuffer を要らない」バックエンドが使えないかを確かめた

【セキュリティ】（第 9 章 + 本付録）
□ strings でバイナリを走査し、鍵が無い  ★ 最も重要
□ wasm-objdump -x で import の一覧を見て、思いがけない能力の要求が無い
□ cargo audit / cargo deny が通る
□ バックエンドで信頼できないモジュールを走らせるとき：実行環境が更新済みで、外側に OS の水準の隔離がある
□ メモリと実行時間の割当の制限がある

【可観測性】
□ 記号つきで、公開版とバイト単位で対応するビルドを一本残した
□ 本番に WebAssembly.RuntimeError の報告があり、build hash と memPages を含む
□ 退路（SIMD 無し／threads 無し）が本当に実行されたことがある。そこに書いてあるだけではない
```

---

## 附：本文との対照の索引

| 主題 | 本付録 | 本文の背景 |
|---|---|---|
| テストの層分け | §1〜3 | 第 3 章の壁八 |
| なぜ Sanitizer が Wasm でとりわけ重いのか | §3 | **第 2 章のシナリオ 1 ⚠️**（サンドボックスの中に ASLR/canary が無い） |
| Fuzzing | §4 | 付録 E の事例 50 |
| CI の体積と鍵の門番 | §5 | 付録 N、第 9 章 |
| エンジン間の差 | §6 | 第 8 章、付録 N §15 |
| 実行環境そのものの攻撃面 | §7-1 | 第 3 章のシナリオ 1（「Wasm だから安全だ」は報告書に書ける文ではない） |
| サプライチェーン | §7-2 | 第 9 章のシナリオ 4 ⚠️ |
| 可観測性 | §8 | 第 3 章の壁八、第 12 章（三年後に誰が直すのか） |
