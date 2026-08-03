# 付録G：ストレージ機構の実装ソース参照（Rust + Wasm + OPFS）

> この付録は**フロントエンドのウェブ（Rust + WebAssembly + OPFS）** の完全な実装案を提供する——現在の産業界（Figma、Adobe Web の類）が純粋なフロントエンドの環境で大規模データの高性能な永続化を解決する黄金標準である。
>
> 例は、OPFS の `FileSystemWritableFileStream` と `FileSystemSyncAccessHandle` を使い、Wasm 内部で**ゼロコピー**のバイナリの大きなファイルの読み書きを行い、ページをリロードしてもデータがクライアントに永久に残ることを保証する方法を示す。
>
> ⚠️ **`web-sys` の API の名称とビルダーの形はバージョンによって変わる**（`FileSystemGetFileOptions` の構築の仕方はバージョンによって異なる、など）。以下のコードは**アーキテクチャの参照**であり、実際にコンパイルするときは使用する `web-sys` のバージョンのドキュメントを根拠とすること。

---

## 1. 案 A：非同期の書き込みストリーム（メインスレッドで使える）

### 1. Rust の中核（`src/lib.rs`）

```rust
use wasm_bindgen::prelude::*;
use wasm_bindgen_futures::JsFuture;
use web_sys::{FileSystemDirectoryHandle, FileSystemWritableFileStream, StorageManager};

#[wasm_bindgen]
pub struct WasmStorageEngine {
    /// エンジンの状態を保ち、初期化の繰り返しを避ける
    root_dir: FileSystemDirectoryHandle,
}

#[wasm_bindgen]
impl WasmStorageEngine {
    /// 1. エンジンの初期化：ブラウザへ OPFS のルートディレクトリのハンドルを要求する
    #[wasm_bindgen(constructor)]
    pub async fn new() -> Result<WasmStorageEngine, JsValue> {
        let window = web_sys::window().ok_or("window オブジェクトが見つからない")?;
        let storage: StorageManager = window.navigator().storage();

        // Origin Private File System のルートを非同期に取得する
        let root_dir_jsval = JsFuture::from(storage.get_directory()).await?;
        let root_dir: FileSystemDirectoryHandle = root_dir_jsval.into();

        Ok(WasmStorageEngine { root_dir })
    }

    /// 2. 高性能な永続化の書き込み：Wasm のメモリ上のバイナリデータを OPFS へ直通で書く
    pub async fn save_file(&self, filename: &str, data: &[u8]) -> Result<(), JsValue> {
        // ファイルを作るか開く
        let mut options = web_sys::FileSystemGetFileOptions::new();
        options.create(true);
        let fh_jsval = JsFuture::from(
            self.root_dir.get_file_handle_with_options(filename, &options)
        ).await?;
        let file_handle: web_sys::FileSystemFileHandle = fh_jsval.into();

        // OPFS 専用の高性能な書き込みストリームを開く
        let writable_jsval = JsFuture::from(file_handle.create_writable()).await?;
        let writable: FileSystemWritableFileStream = writable_jsval.into();

        // ★ ゼロコピーの最適化：Rust の &[u8] のスライスを JS の Uint8Array のビューへ直接写像する
        //   この一段は線形メモリ内のポインタ演算だけであり、オーバーヘッドはゼロである
        //
        //   ⚠️ SAFETY：このビューは次の memory.grow のあと無効になる。
        //   ビューが生きているあいだ、メモリの確保が一切起きないことを保証せねばならない。
        let js_buffer = unsafe { js_sys::Uint8Array::view(data) };

        JsFuture::from(writable.write_with_buffer_source(&js_buffer)?).await?;

        // ストリームを閉じ、キャッシュを物理ディスクへ強制的に書く
        JsFuture::from(writable.close()).await?;
        Ok(())
    }

    /// 3. 読み取り：OPFS のファイルの内容を Wasm の線形メモリへ読み戻す
    pub async fn load_file(&self, filename: &str) -> Result<Vec<u8>, JsValue> {
        let fh_jsval = JsFuture::from(
            self.root_dir.get_file_handle(filename)
        ).await?;
        let file_handle: web_sys::FileSystemFileHandle = fh_jsval.into();

        let file_jsval = JsFuture::from(file_handle.get_file()).await?;
        let file: web_sys::File = file_jsval.into();

        let buf_jsval = JsFuture::from(file.array_buffer()).await?;
        let array = js_sys::Uint8Array::new(&buf_jsval);
        Ok(array.to_vec())      // この一段は避けられないコピーである（JS ヒープ → Wasm 線形メモリ）
    }
}
```

### 2. `Cargo.toml`

```toml
[package]
name = "wasm_opfs_engine"
version = "0.1.0"
edition = "2021"

[lib]
crate-type = ["cdylib"]

[dependencies]
wasm-bindgen = "0.2"
wasm-bindgen-futures = "0.4"
js-sys = "0.3"

[dependencies.web-sys]
version = "0.3"
features = [
  "Window",
  "Navigator",
  "StorageManager",
  "FileSystemDirectoryHandle",
  "FileSystemFileHandle",
  "FileSystemGetFileOptions",
  "FileSystemWritableFileStream",
  "File",
]

# ★ リリース版では必ず有効にすること（第 9 章参照）
[profile.release]
opt-level = 3
lto = true
codegen-units = 1
panic = "abort"
strip = true
```

ビルド：

```bash
wasm-pack build --target web
```

### 3. フロントエンドの統合（`index.html`）

```html
<!DOCTYPE html>
<html lang="ja">
<head>
  <meta charset="UTF-8">
  <title>Wasm OPFS Storage Engine</title>
</head>
<body>
  <h1>WebAssembly OPFS 高性能ストレージのデモ</h1>
  <button id="saveBtn" disabled>Wasm の大規模データをディスクへ書く</button>
  <button id="loadBtn" disabled>読み戻して検証する</button>
  <p id="status">状態：初期化を待っています…</p>

  <script type="module">
    import init, { WasmStorageEngine } from './pkg/wasm_opfs_engine.js';

    const status = document.getElementById('status');

    async function run() {
      await init();
      status.textContent = '状態：Wasm エンジンの初期化に成功';

      const engine = await new WasmStorageEngine();
      document.getElementById('saveBtn').disabled = false;
      document.getElementById('loadBtn').disabled = false;

      document.getElementById('saveBtn').addEventListener('click', async () => {
        status.textContent = '状態：大規模データの計算と書き込み中…';

        const dataSize = 10 * 1024 * 1024;           // 10 MB
        const mockBigData = new Uint8Array(dataSize);
        for (let i = 0; i < dataSize; i++) mockBigData[i] = i % 256;

        try {
          const t0 = performance.now();
          await engine.save_file('firmware_backup.bin', mockBigData);
          const t1 = performance.now();
          status.textContent =
            `状態：10 MB の書き込み成功。所要 ${(t1 - t0).toFixed(2)} ミリ秒（リロードしても失われない）`;
        } catch (err) {
          status.textContent = `エラー：${err}`;
        }
      });

      document.getElementById('loadBtn').addEventListener('click', async () => {
        const t0 = performance.now();
        const back = await engine.load_file('firmware_backup.bin');
        const t1 = performance.now();
        status.textContent =
          `状態：${(back.length / 1024 / 1024).toFixed(1)} MB を読み戻し、` +
          `所要 ${(t1 - t0).toFixed(2)} ミリ秒、先頭バイト = ${back[0]}`;
      });
    }
    run();
  </script>
</body>
</html>
```

**検証の方法**：ページをリロードしてから「読み戻す」を押せば、データはまだそこにある。DevTools の **Application → Storage → File System** のパネルで OPFS の内容を観察することもできる。

---

## 2. 案 B：同期アクセスハンドル（Worker 内。性能の天井）

**これは産業界が非常に大きなファイル（>50 MB）とデータベースを扱う正解である**（第 7 章シナリオ 3 参照）。

### `worker.js`

```javascript
import init, { ChunkedEngine } from './pkg/wasm_opfs_engine.js';

let engine;

self.onmessage = async (e) => {
  const { cmd, payload } = e.data;

  if (cmd === 'init') {
    await init();
    engine = new ChunkedEngine();
    // ★ createSyncAccessHandle は Worker の中でしか呼べない
    const root = await navigator.storage.getDirectory();
    const fh = await root.getFileHandle('bigdata.bin', { create: true });
    const handle = await fh.createSyncAccessHandle();
    engine.attach(handle);              // ハンドルを Wasm 側へ渡す
    self.postMessage({ ok: true });
    return;
  }

  if (cmd === 'process') {
    // 大きな buffer は Transferable で渡されている。ゼロコピー
    const result = engine.process_chunk(payload);
    // 返すときも同じく Transferable を使う
    self.postMessage({ result }, [result.buffer]);
  }
};
```

### メインスレッド

```javascript
const worker = new Worker('./worker.js', { type: 'module' });

worker.postMessage({ cmd: 'init' });

// ★ 第二引数が Transferable を宣言する：複製ではなく所有権の移転（マイクロ秒級）
const buf = new ArrayBuffer(50 * 1024 * 1024);
worker.postMessage({ cmd: 'process', payload: buf }, [buf]);
// ⚠️ 移転後、メインスレッド側の buf.byteLength は即座に 0 になる
```

### 同期アクセスハンドルの中核の操作

```javascript
const handle = await fh.createSyncAccessHandle();

handle.write(buffer, { at: offset });   // 同期の書き込み。Promise なし
handle.read(buffer,  { at: offset });   // 同期のランダム読み取り。pread のよう
handle.getSize();                       // ファイルのサイズ
handle.truncate(newSize);               // 切り詰め
handle.flush();                         // ディスクへ強制的に書く
handle.close();                         // ★ 必ず閉じること。さもないとロックが解放されない
```

---

## 3. スライディングウィンドウの分割読み取り（4 GB 上限の回避）

```rust
/// 概念の骨格：メモリは 50 MB しかないのに 100 GB のファイルを扱える
const CHUNK: u64 = 4 * 1024 * 1024;              // 4 MB の整列
const WINDOW: usize = 50 * 1024 * 1024;          // 50 MB の常駐ウィンドウ

pub struct ChunkedReader {
    handle: SyncHandle,          // OPFS の同期ハンドル（あるいは HTTP Range のラッパ）
    window: Vec<u8>,
    window_start: u64,
    window_len: usize,
    file_size: u64,
}

impl ChunkedReader {
    /// 任意の位置を読む。現在のウィンドウを出るときだけディスク I/O が起きる
    pub fn read_at(&mut self, offset: u64, len: usize) -> &[u8] {
        let end = offset + len as u64;
        let in_window = offset >= self.window_start
            && end <= self.window_start + self.window_len as u64;

        if !in_window {
            // ブロックの境界へ整列させ、一バイト読むためにウィンドウ全体を再読み込みするのを避ける
            self.window_start = (offset / CHUNK) * CHUNK;
            let want = WINDOW.min((self.file_size - self.window_start) as usize);
            self.window.resize(want, 0);
            self.window_len = self.handle.read_at(&mut self.window, self.window_start);
        }

        let local = (offset - self.window_start) as usize;
        &self.window[local .. local + len]
    }
}
```

**四つの実装の要点**：

1. **ウィンドウを整列させる**：1 MB/4 MB の境界へ。
2. **アクセスパターンに合わせて調整する**：順次走査 → 大きなウィンドウ + 先読み。ランダムな飛び回り → 小さなウィンドウ + 複数ウィンドウの LRU。
3. **Worker の中でなければならない**（`createSyncAccessHandle` の仕様上の制約）。
4. **リモートのファイルは同じロジックを使う**——`handle.read_at()` を `fetch(url, { headers: { Range: 'bytes=A-B' } })` に置き換えるだけ。

---

## 4. 三つのストレージ機構の選定と対応する実装

| 場面 | 機構 | 鍵となる API |
|---|---|---|
| 大きなファイル / データベース（>50 MB） | **OPFS + Worker の同期ハンドル** | `createSyncAccessHandle()` |
| ゲームのセーブ / 小さな JSON（互換性が高い） | **IndexedDB / IDBFS** | `FS.mount(IDBFS)` + `FS.syncfs()` |
| バックエンドのクラウドネイティブ | **WASI のファイルシステム** | `std::fs` + 事前に開かれたディレクトリの能力 |

### IDBFS（Emscripten）

```javascript
// C 側はいつもどおり fopen("/save/game.sav", "wb")
Module.onRuntimeInitialized = () => {
  FS.mkdir('/save');
  FS.mount(IDBFS, {}, '/save');
  FS.syncfs(true, err => {        // true = IndexedDB から MEMFS へ読み込む
    if (err) throw err;
    startGame();
  });
};

function saveGame() {
  FS.syncfs(false, err => {       // false = MEMFS から IndexedDB へ書き戻す
    if (err) console.error(err);
  });
}
```

### WASI（バックエンド）

```rust
// target: wasm32-wasip1
use std::fs::File;
use std::io::{Read, Write};

fn main() -> std::io::Result<()> {
    // ホストが事前に開いて認可したディレクトリにしかアクセスできない
    let mut f = File::create("/sandbox/output.bin")?;
    f.write_all(b"hello from wasm")?;

    let mut buf = String::new();
    File::open("/sandbox/input.txt")?.read_to_string(&mut buf)?;
    println!("{}", buf);
    Ok(())
}
```

```bash
# ホスト側：能力の一覧はこの一行がすべてである
wasmtime run --dir=./data::/sandbox app.wasm
```

---

## 5. アーキテクチャの利点と盲点の防御

| 観点 | やり方 | なぜか |
|---|---|---|
| **ゼロコピー** | `js_sys::Uint8Array::view(data)` | 「Rust の線形メモリ → JS のヒープ」という二重のメモリのオーバーヘッドを避ける |
| ⚠️ **ビューの無効化** | ビューが生きているあいだ、メモリの確保を**一切起こさない** | `memory.grow` は `ArrayBuffer` を detach し、ビューを無効な領域へ向けてしまう |
| **メインスレッドの固まりの回避** | ストレージのエンジンを Web Worker へ入れる | 同期 I/O はメインスレッドで UI を凍らせる（だから仕様が端的に禁じている） |
| **極限の I/O 性能** | Worker 内で `createSyncAccessHandle()` を使う | 非同期のポーリングのオーバーヘッドを消し、ネイティブに近い順次書き込みに達する |
| **容量の追い出し** | `await navigator.storage.persist()` | persistent と印されていないデータはディスク圧で消されうる |
| **複数タブのロックの奪い合い** | Web Locks API か `BroadcastChannel` で調整する | 同一ファイルに同時に一つの sync access handle しか持てない |
| **ユーザがバックアップできない** | 「ファイルの書き出し」機能を自前で用意する | OPFS はユーザには見えない |

---

## 6. 測定のテンプレート

```javascript
// 書き込みのスループット
const t0 = performance.now();
await engine.save_file('bench.bin', data);
const t1 = performance.now();
const mbps = (data.length / 1024 / 1024) / ((t1 - t0) / 1000);
console.log(`書き込みスループット：${mbps.toFixed(1)} MB/s`);

// メモリのフットプリント（Chrome）
if (performance.measureUserAgentSpecificMemory) {
  const m = await performance.measureUserAgentSpecificMemory();
  console.log('タブのメモリ：', (m.bytes / 1024 / 1024).toFixed(1), 'MB');
}

// 容量
const est = await navigator.storage.estimate();
console.log(`使用 ${(est.usage/1e6).toFixed(1)} MB / 割当 ${(est.quota/1e6).toFixed(1)} MB`);
```
