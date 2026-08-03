# 付録M　仕様の深水域：しばしば飛ばされる十二の技術の細部

> 本文は語りの流れを保つため、多くの箇所で「それはこう動く」と言ったところで止まっている。この付録は、その止まった場所からさらに下へ掘る。
> **これは入門の材料ではなく、参照の材料である**——実装の途中で具体的な問題にぶつかったときに、ここを開いてほしい。
>
> ⚠️ **版の前提**：本付録は **WebAssembly 3.0**（2025 年 9 月に完成を宣言）を基準とする。**3.0 より前に書かれた資料は GC、Memory64、例外処理、末尾呼び出し、複数メモリを「提案」と呼ぶ——その記述はすでに古い。**

---

## 1. 一つの `.wasm` をバイト単位で分解する

### 1-1　LEB128：なぜ長さがどれも可変長なのか

Wasm のすべての整数の欄（セクションの長さ、索引、定数）は **LEB128（Little Endian Base 128）** で符号化される——バイトごとに下位 7 ビットでデータを持ち、最上位ビットを「まだ続く」の継続の旗に使う。

```
符号なし LEB128：
  値 624485 (0x98765)
  → 二進 1001 1000 0111 0110 0101
  → 7 ビットずつの組（下から上へ）：1100101  1110110  0100110
  → 継続ビットを付ける：11100101  11110110  00100110
  → バイト          E5        F6        26

小さい数は 1 バイトで済む（0–127）。そこが要点である：
  索引も長さも大半は小さいので、可変長の符号化がモジュール全体を目に見えて縮める。
```

**符号つきの版（sLEB128）** は `i32.const` / `i64.const` のような定数に使い、最後の組で符号拡張をする。

> **実務上の意味**：これは二つのことを説明する——**（一）** なぜ Wasm のバイナリが同等の固定長の形式よりずっと小さいのか。**（二）** なぜ固定の変位で `.wasm` を **patch できない**のか——数字を一つ変えるとそのバイト数が変わりうるので、後ろが全部ずれる。**バイナリを直したいなら Binaryen か WABT を使え。自分の手でやるな。**

### 1-2　セクションの共通の構造

```
┌────────┬──────────────┬──────────────────────────┐
│ id (1) │ size (u32 LEB)│ contents（size バイト）   │
└────────┴──────────────┴──────────────────────────┘
```

**`size` が存在する値打ち**：パーサは知らないセクション（とりわけ Custom Section）を**飛ばせる**。これが Wasm の前方互換の礎である——古いエンジンが、新しいツールチェーンの詰め込んだ独自のメタデータに出会っても、飛ばせばよい。

### 1-3　型の符号化

| 値の型 | バイト |
|---|---|
| `i32` | `0x7F` |
| `i64` | `0x7E` |
| `f32` | `0x7D` |
| `f64` | `0x7C` |
| `v128` | `0x7B` |
| `funcref` | `0x70` |
| `externref` | `0x6F` |
| 関数型（functype）の前置 | `0x60` |

**これらがどれも負数の sLEB128 の符号化である点に注意**（`0x7F` = −1、`0x7E` = −2……）。これは偶然ではない：**正の数は「型の索引」に残してある**。ゆえに GC が `(ref $MyStruct)` のような利用者定義の型を指す参照を持ち込むとき、符号化の空間はとうに空けてあった。**2015 年の、あの「意図して小さく作った」仕様は、型の符号化に扉を残していたのである。**

### 1-4　通しで一度：ある `add` 関数

```wat
(module
  (func $add (param i32 i32) (result i32)
    local.get 0
    local.get 1
    i32.add)
  (export "add" (func $add)))
```

```
00 61 73 6D            マジックナンバー \0asm
01 00 00 00            版 1

01 07                  Type セクション (id=1)、長さ 7
   01                    型は 1 個
   60                    functype
   02 7F 7F              引数 2 個：i32, i32
   01 7F                 結果 1 個：i32

03 02                  Function セクション (id=3)、長さ 2
   01 00                 関数 1 個、型 #0 を使う

07 07                  Export セクション (id=7)、長さ 7
   01                    輸出 1 個
   03 61 64 64           名前の長さ 3："add"
   00 00                 kind=func(0x00)、索引 0

0A 09                  Code セクション (id=10)、長さ 9
   01                    関数の本体 1 個
   07                    本体の長さ 7
   00                    ★ 局所変数の宣言：0 組
   20 00                 local.get 0
   20 01                 local.get 1
   6A                    i32.add
   0B                    ★ end（すべての関数の本体は 0x0B で終わる）
```

> **本文の第 2 章が言う「五バイト」とは `20 00 20 01 6A` という命令の並びを指す。** 完全な関数の本体には、その前の局所変数の宣言 `00` と、末尾の `0B` が加わる——**この二バイトは仕様が強いるもので、手でバイナリを組む人は初回に必ず `0x0B` を落とす。**

### 1-5　よく使う命令の符号の早見

| 命令 | 符号 | 命令 | 符号 |
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

**SIMD と一部の新しい命令は前置の符号を使い**（`0xFD` が SIMD の前置、`0xFC` が bulk memory／飽和つき変換の前置）、その後ろに LEB128 の下位命令の符号が続く。

---

## 2. 検証のアルゴリズム：多相スタックと、あの賢い技

第 2 章は、検証器が「スタックの型の整合」を検査すると述べた。**だが素朴な実装を詰まらせる状況が一つある**：

```wat
(func (result i32)
  unreachable       ;; ここで制御の流れは終わる
  i32.add)          ;; ← スタックには何もない。この行はどう検証するのか？
```

`unreachable` のあとのコードは**決して実行されない**。それでも検証器は判断を下さねばならない（一回通しで、線形で、到達可能性の解析をしないものでなければならないからだ）。

**仕様の解き方は「多相スタック（polymorphic stack）」である**：unreachable の状態へ入ったあと、検証器はスタックを「**任意の数、任意の型の値をいくらでも供給できる**」と印づける。ゆえに `i32.add` が `i32` を二つ要るなら多相スタックが二つ与える。次の命令が `f64` を三つ要るなら、それも与える。**こうして死んだコードの中のどんな命令の並びも検証を通り、しかもコンパイラがそれを到達不能だと証明する必要がない。**

```
検証の状態機（簡略）：
  正常の状態  ── unreachable / br / return / br_table ──▶ 多相の状態
  多相の状態  ── end かそのブロックの境界に出会う ─────▶ そのブロックの宣言した型へ戻る
```

> 💡 **これは「検証を O(n) の一回通しに保つ」という設計の目標の直接の産物である。** 検証器が型を検査する前に到達可能性の解析をせねばならないなら、それはもう一回通しではなく、ストリーミングコンパイル（ダウンロードしながらコンパイルする）も成り立たなくなる。**例外に見える規則は、しばしば、より根本的な性質を守るためにある。**

---

## 3. `call_indirect`、テーブル、そして C++ の仮想関数が Wasm でとる姿

### 3-1　関数ポインタはどう実装されているか

Wasm には**関数ポインタがない**——関数のアドレスを線形メモリへ入れることはできない。代わりにあるのが**テーブル（Table）**である：

```wat
(module
  (type $binop (func (param i32 i32) (result i32)))
  (table 4 funcref)                      ;; 4 枠の関数のテーブル
  (elem (i32.const 0) $add $sub $mul $div)  ;; 四つの関数を入れる

  (func $apply (param $op i32) (param $a i32) (param $b i32) (result i32)
    local.get $a
    local.get $b
    local.get $op
    call_indirect (type $binop)))        ;; ★ 索引で呼び、署名を検査する
```

**C/C++ からコンパイルされた Wasm では、「関数ポインタ」は実のところ `i32` のテーブルの索引である。** これはよくある困惑を説明する：**なぜ Wasm の関数ポインタは線形メモリに安全に置けるのか？** それが索引にすぎないからだ——バッファオーバーフローで任意の値に書き換えられても、最悪の結果は `call_indirect` が署名の合わない項目を見つけて **trap** することであり、**攻撃者の握るアドレスへ飛んで任意のコードを実行することではない**。

### 3-2　`call_indirect` の実行時の検査

```
call_indirect (type $sig) の実行時：
  1. スタックから索引 i を取り出す
  2. i がテーブルの範囲を超えていれば → trap「undefined element」
  3. table[i] が null なら           → trap「uninitialized element」
  4. table[i] の実際の署名 ≠ $sig なら → trap「indirect call type mismatch」
  5. 通れば → 呼ぶ
```

**第 4 段は呼び出しのたびに払う実行時の費用である。** これこそ Wasm 3.0 の**型付き関数参照（typed function references）** が解こうとする問題だ——`(ref $sig)` という型を帯びた参照を使えば、**署名は型の体系のレベルですでに定まっており、実行時に照合し直す必要がない**。仮想関数の呼び出しが密集する C++ / OOP の言語にとって、これは実質的な性能の改善である。

### 3-3　C++ の仮想関数の実際の姿

```
class Shape { virtual double area(); };

Wasm へコンパイルしたあと：
  ┌ 線形メモリ ────────────────────┐
  │ Shape のオブジェクト：            │
  │   +0  vptr → vtable を指すアドレス │   ← vptr は線形メモリのアドレス
  │   +4  メンバ…                    │
  │                                 │
  │ vtable（これも線形メモリの中）：   │
  │   +0  area の【関数テーブルの索引】(i32) │  ← ★ 関数のアドレスではなく、テーブルの索引
  └────────────────────────────────┘
              ↓
  関数テーブル (funcref)：[ …, Shape::area, Circle::area, … ]
```

**ゆえに一度の仮想呼び出しは：vptr を読む → vtable の項目を読む（i32 の索引を得る）→ `call_indirect`、である。**

> **これは Wasm を逆解析するときの要となる足がかりでもある**（第 9 章）：`elem` セクションは間接に呼ばれうる関数をすべて並べており、vtable の配置は `call_indirect` の使われ方から逆に推せる。**クラスの構造は消されたが、呼び出しのグラフの形は残っている。**

---

## 4. 例外処理：Tag セクションと `exnref`

**Wasm 3.0 は例外処理を核心の仕様へ収めた。** その仕組みは見ておく値打ちがある。あなたの見慣れた try/catch とはやや違うからだ。

### 4-1　Tag：例外の「型」

例外はオブジェクトではなく、**tag（標識）+ 一組の payload の値**である。Tag は **Tag セクション（id = 13）** で宣言される：

```wat
(module
  ;; i32 の payload を運ぶ例外の標識を宣言する
  (tag $oom (param i32))

  (func $alloc (param $n i32) (result i32)
    ...
    (throw $oom (local.get $n)))         ;; n を連れて投げる
)
```

### 4-2　`try_table`：3.0 の新しい形

初期の提案は `try` / `catch` / `delegate` のブロックの構造を使っていた。**Wasm 3.0 が採ったのは `try_table` + `exnref` である**——「捕まえる」ことを入れ子のブロックではなく、**一種の分岐**にした：

```wat
(func $safe (result i32)
  (block $handler (result i32)
    (try_table (catch $oom $handler)     ;; $oom が投げられたら payload を連れて $handler へ跳ぶ
      (call $alloc (i32.const 1000000))
      (br 1))                            ;; 例外が投げられなければ → handler を飛ばす
  )
  ;; $handler：スタックの上には $oom の payload (i32) がある
)
```

**`exnref`** は不透明な例外の参照の型で、「任意の例外」を捕まえて投げ直せるようにする（`catch_all_ref` + `throw_ref`）——これは `finally` の実装と、言語をまたぐ例外の伝播に欠かせない。

### 4-3　なぜこれが性能にとって重いのか

**native の例外処理が現れるまで**、C++ の `try/catch` を Wasm へコンパイルする道は二つしかなかった：

| 古い解き方 | 代価 |
|---|---|
| `-fno-exceptions` | エコシステムのライブラリの半分が使えなくなる |
| **JavaScript のトランポリン** | `try` へ入るたびに JS へ越えてまた戻る——**負担が極めて大きく、しかも JS エンジンがインライン化できなくなる** |

**native の EH のあと**、`try_table` は純粋な Wasm の命令であり、エンジンが余さず最適化できる。**これは Wasm 3.0 が C++ のエコシステムへ与えた、最も直接の輸血である。**

---

## 5. JSPI の深部：Wasm はどう Promise を「待つ」のか

第 3 章は JSPI の用途を紹介した。ここではその仕組みと代価を見る。

### 5-1　それは結局、何をしているのか

```
ふつうの場合：
  JS ──call──▶ Wasm ──call──▶ import した JS の関数（Promise を返す）
                                  ↓
                            Wasm は Promise オブジェクトを受け取るが、
                            それを「待つ」術を知らない——即座に先へ進むしかない ❌

JSPI：
  JS ──promising(f)──▶ Wasm ──call──▶ Suspending で包んだ import
                                          ↓
                       ★ エンジンが Wasm の実行スタックを（局所変数と
                         呼び出しの連なりごと）中断して脇へ移し、JS へ Promise を返す
                                          ↓
                            イベントループは走り続ける（タブは凍らない）
                                          ↓
                            Promise が解決 → エンジンがスタックを戻し、
                            結果をオペランドスタックへ積み、中断の場所から続ける ✅
```

### 5-2　API の形

```javascript
// 1. import の側：Promise を返す関数を「中断できるもの」に包む
const imports = {
  env: {
    read_file: new WebAssembly.Suspending(async (ptr, len) => {
      const handle = await root.getFileHandle("data.bin");
      const file = await handle.getFile();
      const buf = new Uint8Array(await file.arrayBuffer());
      new Uint8Array(memory.buffer, ptr, buf.length).set(buf);
      return buf.length;               // Wasm の目には同期の戻り値に見える
    }),
  },
};

// 2. 輸出の側：入口を「Promise を返すもの」に包む
const { instance } = await WebAssembly.instantiateStreaming(fetch("app.wasm"), imports);
const main = WebAssembly.promising(instance.exports.main);
await main();                          // JS にとっては async
```

**Rust の側はほとんど手を入れなくてよい**：

```rust
extern "C" { fn read_file(ptr: *mut u8, len: usize) -> usize; }

pub fn load() -> Vec<u8> {
    let mut buf = vec![0u8; 4096];
    let n = unsafe { read_file(buf.as_mut_ptr(), buf.len()) };  // 見た目はただの同期の呼び出し
    buf.truncate(n);
    buf
}
```

### 5-3　知っておかねばならない三つの代価

1. **中断と再開は無料ではない。** 中断のたびに Wasm のスタックを丸ごと移して戻すので、費用はスタックの深さに関わる。**「たまに一度 I/O を待つ」には向くが、熱いループへ入れると痛い。**
2. **それは並行ではない。** 中断のあいだ、その Wasm のスレッドは何もしていない——**待ちの時間をイベントループへ譲っただけであって、二つのことを同時にしたのではない。**
3. **再入の問題。** 中断のあいだに、JS が同じ Wasm のインスタンスの輸出関数をもう一度呼びうる。**あなたの C のコードが「同時に走る呼び出しは一つだけ」を仮定しているなら（大半の C のコードはそう仮定している）、これは状態の破壊を招く。** 自分で再入のロックを一枚かぶせる必要がある。

### 5-4　Asyncify との対照

| | Asyncify | JSPI |
|---|---|---|
| 仕組み | Binaryen が**モジュール全体を書き換え**、線形メモリで手動にスタックを保存／復元する | **エンジンが native に** Wasm のスタックを中断する |
| 体積への影響 | **目に見えて膨らむ** | なし |
| 実行時の負担 | 大域的（書き換えられたコードが保存／復元のロジックをずっと連れている） | 実際に中断したときだけ払う |
| 注釈が要るか | 巻き戻す関数を指定せねばならず、落とすと壊れる | 要らない |
| 互換性 | どこでも使える | エンジンの対応が要る（**Chrome 137+／Firefox 139+**） |

**移行の戦略**：`typeof WebAssembly.Suspending === "function"` を検出し、あれば JSPI を、なければ Asyncify のビルドへ退く。

---

## 6. 原子操作とメモリモデル

### 6-1　命令の一族

```wat
;; 原子的な読み書き
i32.atomic.load / i32.atomic.store
i64.atomic.load8_u / ...（各種の幅）

;; 読み-変え-書き（RMW）。どれも単一の原子操作
i32.atomic.rmw.add / sub / and / or / xor / xchg / cmpxchg

;; 待ちと起こし（futex の意味論）
memory.atomic.wait32   (addr, expected, timeout_ns) -> i32
memory.atomic.notify   (addr, count) -> i32

;; メモリの障壁
atomic.fence
```

### 6-2　覚えておかねばならない三つの意味論

1. **すべての原子操作は逐次一貫（sequentially consistent）である。** Wasm には C++ のような `memory_order_relaxed` / `acquire` / `release` の階級が**ない**——仕様は最も強い一種しか提供しない。**書き誤りようがないのが利で、弱い順序が生む性能を取れないのが代価である。**
2. **原子でないアクセスには順序の保証がまったくない。** 二つのスレッドが同じアドレスへ原子でない読み書きをすればデータ競合である。仕様はそれがサンドボックスを壊さないことは定めているが、**値が何になるかは保証しない**。
3. **`memory.atomic.wait` はメインスレッドでは trap する。** メインスレッドで詰まることは許されない——**これは仕様のレベルの禁止であって、慣習ではない。** ゆえに `wait` を使う同期の原始的な部品はすべて Worker の中でしか走らせられない（SQLite の第一世代の `opfs` VFS に Worker が要るのも、まさにこれが理由である）。

### 6-3　実用的な帰結

**`memory.atomic.wait32` + `notify` はすなわち futex であり、futex があればあらゆる同期の原始的な部品を実装できる**——mutex、条件変数、セマフォ、障壁。これこそ Emscripten が `pthread` を余さず写し取れる下層の基礎である。

---

## 7. Relaxed SIMD の、非決定性の一覧

Wasm 3.0 は relaxed SIMD を収めた。それは**決定性を捨てる**ことで、より良いハードウェアへの写像を買う。**チェーンの上、あるいは機械をまたいで結果を再現せねばならない科学計算では、これらの命令を禁じねばならない。**

| 命令の族 | 非決定性はどこから来るか |
|---|---|
| `relaxed_madd` / `relaxed_nmadd` | FMA（丸めは一度）を使うことも、mul+add（丸めは二度）を使うこともある——**浮動小数の結果が末尾の数ビットで違う** |
| `relaxed_min` / `relaxed_max` | **NaN と ±0 の扱いがプラットフォームで異なる** |
| `relaxed_swizzle` | 索引が範囲を超えたとき、0 を返すか未定義の値を返すかが**プラットフォームで異なる** |
| `relaxed_trunc_*` | 浮動小数から整数への変換で、範囲を超えた場合や NaN の結果が**プラットフォームで異なる** |
| `relaxed_dot` | 累算の順序と飽和の振る舞いが違いうる |
| `relaxed_laneselect` | マスクが全 0／全 1 でないときの振る舞いが未定 |

**判断の基準**：**出力がハッシュ、署名、合意、あるいは機械をまたいだ照合に使われるなら、relaxed SIMD を使うな。** 画像のフィルタ、ゲームの物理、機械学習の推論のような「数 ULP 違っても誰にも分からない」場面にだけ向く。

---

## 8. 複数メモリ（Wasm 3.0）

```wat
(module
  (memory $a 1)
  (memory $b 1)

  ;; 読み込み／格納の命令はメモリの索引を伴う
  (func $get (result i32) (i32.load $b (i32.const 0)))

  ;; memory.copy はメモリをまたげる：dst_mem, src_mem
  (func $move (memory.copy $a $b (i32.const 0) (i32.const 0) (i32.const 1024)))

  ;; それぞれ独立に伸びる
  (func $grow_b (result i32) (memory.grow $b (i32.const 16))))
```

**典型的な三つの使い方**：

| 使い方 | 利 |
|---|---|
| **コードの区画／データの区画を分ける** | 大きな資産が作業域のアドレス空間を押しつぶさなくなる |
| **テナントごとに一つ** | 一つのモジュールが複数のテナントを賄い、メモリが自然に隔離される |
| **冷たいものと熱いものを分ける** | 熱いデータを小さなメモリに置き、キャッシュの局所性が良くなる |

**最大の値打ち**（第 8 章のシナリオ 4 で述べた）：**どのメモリも依然として wasm32 なので、ガードページの無料の境界検査が丸ごと残る**——これは Memory64 にはできないことである。

**現実の制約**：**ツールチェーンの対応が仕様に遅れている。** 大半の C/C++/Rust のツールチェーンは、既定で「メモリは一つだけ」を仮定している。

---

## 9. 配備の層：本番であなたを転ばせる五つのこと

### 9-1　MIME の型

```
Content-Type: application/wasm
```

**これがないと `instantiateStreaming` は端的に拒否する。** GitHub Pages は `.wasm` の拡張子に対して正しく返す。

### 9-2　CSP

```http
Content-Security-Policy: script-src 'self' 'wasm-unsafe-eval'
```

Wasm のコンパイルは CSP の目には動的なコードの生成に映る。`'wasm-unsafe-eval'`（Chrome 97+／Firefox 102+／Safari 16+）は **Wasm だけを通し、`eval()` は通さない**。

### 9-3　完全性の検証（SRI の空白）

**これはエコシステムの現実の欠落である**：`<script integrity="sha384-…">` は `<script>` には効くが、**`fetch()` で読み込む `.wasm` には内蔵の SRI の仕組みがない**。検証したければ自分でやることになる：

```javascript
async function loadVerified(url, expectedSha256Base64) {
  const bytes = await (await fetch(url)).arrayBuffer();
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const actual = btoa(String.fromCharCode(...new Uint8Array(digest)));
  if (actual !== expectedSha256Base64) throw new Error("wasm integrity mismatch");
  return WebAssembly.instantiate(bytes, imports);   // ⚠️ 代価：ストリーミングコンパイルを捨てる
}
```

> **ここには引き換えが一つあることに注意**：ハッシュを検証するにはバイト列を丸ごと先に得ねばならず、**ゆえにストリーミングコンパイルを失う**（第 2 章）。**安全と起動の速さがここで正面からぶつかり**、両立の解はない。多くのチームの選択はこうだ：**同一オリジンでのホスティング + 再現できるビルドの流れ + CDN の TLS**であって、実行時のハッシュの検証ではない。

### 9-4　圧縮

```
Content-Encoding: br
```

**Wasm の Brotli の圧縮率はたいてい良い**——付録 L の実例は 3.6 MB → 0.8 MB（およそ 4.5 倍）。**投資対効果が最も高い、サーバ設定の一行である。**

> **なぜ Wasm がとりわけ Brotli に向くのか、そして「圧縮辞書転送」で改版のたびに数十 KB しか送らずに済ませる方法は——付録 N §7 を見よ。**

### 9-5　コードキャッシュと Worker の共有

**しばしば見落とされる二つの加速の手**：

```javascript
// (1) 一度コンパイルし、複数の Worker で共有する
//     WebAssembly.Module は構造化複製できるので、postMessage しても再コンパイルされない
const mod = await WebAssembly.compileStreaming(fetch("app.wasm"));
for (const w of workers) w.postMessage({ mod });          // ★ N-1 回のコンパイルを省く

// Worker の中：
self.onmessage = async ({data}) => {
  const inst = await WebAssembly.instantiate(data.mod, imports);  // そのまま実体化する
};
```

```
(2) ブラウザのディスク上のコードキャッシュ：
    Chrome は TurboFan の産物を HTTP のキャッシュへ書き、鍵は URL である。
    → .wasm に安定した URL を与える（内容のハッシュを含むファイル名が最良）
    → 再訪のときコンパイルの段階をまるごと飛ばせる。大きなモジュールの二度目の
      読み込みは、しばしば桁で速くなる
```

---

## 10. 性能を計る作業の流れ

**Wasm はプロファイルできないと思っている人が多いが、実際にはできる。準備が要るだけだ。**

```bash
# 1. name の独自セクションを残す（さもないと wasm-function[1234] しか見えない）
#    Rust：リリース版で何も考えず strip = true にせず、wasm-opt で debug だけを剥ぐ
wasm-opt -O3 --strip-debug --strip-producers app.wasm -o app.wasm
#                ↑ name セクションを残し、DWARF だけを剥ぐ

# 2. Emscripten：関数名を明示的に残す
emcc -O3 --profiling-funcs ...
```

**そのうえで Chrome DevTools の Performance のパネルで記録する**——Wasm のフレームが関数名でフレイムグラフに現れ、JS のフレームと混ざって表示される。**これによって「時間は境界越えに使われたのか、計算に使われたのか」が、そのまま目で見える問いになる。**

**最もよくある三つの結論と、その見た目**：

| フレイムグラフの見た目 | 診断 |
|---|---|
| 細かい JS↔Wasm の縞が大量に交錯する | **境界越えが多すぎる**（第 2 章）——境界を粗くせよ |
| Wasm のフレームは幅広いが、内側が平坦 | 本当に計算している——SIMD かアルゴリズムを考えよ |
| `__wbindgen_malloc` / `free` の割合が高い | **確保しすぎ**——メモリのプールか、バッファの再利用へ |

**さらに一歩**：`performance.mark()` / `measure()` は import を通じて Wasm の側から呼べるので、独自の区間を時間軸へ載せられる。

---

## 11. proxy-wasm：インフラの層における Wasm の標準 ABI

**これは第 4 章の「多テナントのプラグインの仕組み」のくだりの具体的な姿であり**、Wasm がバックエンドで最も成功して着地した形の一つでもある。

**proxy-wasm** はネットワークのプロキシのために設計された Wasm の ABI の一式で、**Envoy、Istio、Kong、APISIX、Higress** などが採っている。ホストとモジュールのあいだの呼び戻しを一組、定めている：

```
モジュールの輸出（ホストがモジュールを呼ぶ）：
  proxy_on_context_create(context_id, parent_id)
  proxy_on_request_headers(context_id, num_headers, end_of_stream)
  proxy_on_request_body(context_id, body_size, end_of_stream)
  proxy_on_response_headers(...)
  proxy_on_log(context_id)
  proxy_on_tick(context_id)

ホストの輸出（モジュールがホストを呼ぶ）：
  proxy_get_header_map_value(...)
  proxy_set_header_map_pairs(...)
  proxy_send_local_response(...)   ← 直に応答し、上流へ転送しない
  proxy_get_shared_data / proxy_set_shared_data
  proxy_http_call(...)             ← 外へ HTTP を出す（認証のサービスに問い合わせるなど）
```

**なぜそれが Wasm の甘い場所なのか**（第 4 章の判断へ戻る）：

- **多テナント**：一つの Envoy のプロセスの中で、互いを信頼しない顧客のプラグインを百も走らせられる。それぞれが独立した線形メモリと能力の境界を持つ。**これをコンテナでやることは不可能である。**
- **熱い更新**：`.wasm` を差し替えればロジックが替わる。プロキシを再起動しなくてよい。
- **言語に依らない**：顧客は Rust でも Go でも AssemblyScript でもよい。

> **これこそ第 4 章のあの一文の証拠である**：**Wasm は既存のサービスから市場を奪うのではなく、コンテナが構造の上で入り込めない場所に、自分の地歩を生やす。**

---

## 12. コードの分割と遅延読み込み

**モジュールが切り分けねばならないほど大きくなったとき**、道は二つある：

### 12-1　`wasm-split`（Emscripten / Binaryen）

一つのモジュールを**主モジュール + 副モジュール**に切り、主を先に読み込み、副は初めて呼ばれたときに取りに行く。

```bash
# まずプロファイルで「起動時に本当に使う関数」の一覧を得る
wasm-split app.wasm -o1 primary.wasm -o2 secondary.wasm \
  --profile=startup.prof --keep-funcs=@startup-funcs.txt
```

**向くのは**：起動の経路が明確で、機能の大半が「利用者は永遠に押さないかもしれない」ものであるアプリケーション。

### 12-2　手で複数の独立したモジュールへ切る

```javascript
// 最初の画面では核だけを読む
const core = await WebAssembly.instantiateStreaming(fetch("core.wasm"), imports);

// 利用者が「PDF へ書き出す」を押してから読む
button.onclick = async () => {
  const pdf = await WebAssembly.instantiateStreaming(fetch("pdf.wasm"), {
    env: { memory: core.instance.exports.memory },   // ★ 同じ線形メモリを共有する
  });
  pdf.instance.exports.export_pdf(ptr, len);
};
```

**要となる細部**：二つのモジュールは**同じ線形メモリを共有する**（memory を一方から export し、他方で import する）。こうすればデータを複製しなくてよい。**Tesseract の言語パック、Pyodide の `micropip` はどちらもこの形である。**

---

## 附：本付録と本文の対照の索引

| 知りたいこと | ここを見よ | 本文の背景 |
|---|---|---|
| バイナリは結局どんな姿か | 本付録 §1 | 第 2 章のシナリオ 1 |
| なぜ検証が一回通しで済むのか | §2 | 第 2 章のシナリオ 1 |
| 関数ポインタと仮想関数 | §3 | 第 2 章、第 9 章（逆解析） |
| C++ の例外の代価 | §4 | 第 1 章（技術的負債）、第 3 章 |
| 同期のコードはどう非同期の API を待つのか | §5 | 第 3 章の壁七、第 7 章、付録 L |
| 複数スレッドの下層の原始的な部品 | §6 | 第 3 章の壁六、第 5 章 |
| チェーンの上で使えない SIMD の命令はどれか | §7 | 第 4 章（EVM の決定性） |
| 4 GiB の第三の出口 | §8 | 第 8 章のシナリオ 4 |
| 本番の配備のチェックリスト | §9 | 第 5 章、付録 C |
| Wasm をどうプロファイルするか | §10 | 第 3 章の壁八 |
| Wasm がバックエンドで本当に勝つ場所 | §11 | 第 4 章のシナリオ 2 |
| モジュールが大きすぎるときどうするか | §12 | 第 8 章 |
