# 附錄G　儲存機制實作源碼參考（Rust + Wasm + OPFS）

> 本附錄提供**前端網頁（Rust + WebAssembly + OPFS）** 的完整實作方案——這是目前工業界（Figma、Adobe Web 一類）在純前端環境下解決大數據高效能持久化的黃金標準。
>
> 範例展示如何利用 OPFS 的 `FileSystemWritableFileStream` 與 `FileSystemSyncAccessHandle`，在 Wasm 內部進行**零拷貝**的二進位大檔案讀寫，確保網頁即使重整，資料依然永久保存在客戶端。
>
> ⚠️ **`web-sys` 的 API 名稱與 builder 形式會隨版本變動**（例如 `FileSystemGetFileOptions` 的建構方式在不同版本有差異）。以下程式碼為**架構參考**，實際編譯時請以你使用的 `web-sys` 版本文件為準。

---

## 一、方案 A：非同步寫入串流（主執行緒可用）

### 1. Rust 核心（`src/lib.rs`）

```rust
use wasm_bindgen::prelude::*;
use wasm_bindgen_futures::JsFuture;
use web_sys::{FileSystemDirectoryHandle, FileSystemWritableFileStream, StorageManager};

#[wasm_bindgen]
pub struct WasmStorageEngine {
    /// 保持引擎狀態，避免重複初始化
    root_dir: FileSystemDirectoryHandle,
}

#[wasm_bindgen]
impl WasmStorageEngine {
    /// 1. 初始化引擎：向瀏覽器請求 OPFS 的根目錄控制代碼
    #[wasm_bindgen(constructor)]
    pub async fn new() -> Result<WasmStorageEngine, JsValue> {
        let window = web_sys::window().ok_or("找不到 window 物件")?;
        let storage: StorageManager = window.navigator().storage();

        // 非同步取得 Origin Private File System 的根目錄
        let root_dir_jsval = JsFuture::from(storage.get_directory()).await?;
        let root_dir: FileSystemDirectoryHandle = root_dir_jsval.into();

        Ok(WasmStorageEngine { root_dir })
    }

    /// 2. 高效能持久化寫入：把 Wasm 記憶體中的二進位資料直通寫入 OPFS
    pub async fn save_file(&self, filename: &str, data: &[u8]) -> Result<(), JsValue> {
        // 建立或開啟檔案
        let mut options = web_sys::FileSystemGetFileOptions::new();
        options.create(true);
        let fh_jsval = JsFuture::from(
            self.root_dir.get_file_handle_with_options(filename, &options)
        ).await?;
        let file_handle: web_sys::FileSystemFileHandle = fh_jsval.into();

        // 開啟 OPFS 專屬的高效能寫入串流
        let writable_jsval = JsFuture::from(file_handle.create_writable()).await?;
        let writable: FileSystemWritableFileStream = writable_jsval.into();

        // ★ 零拷貝優化：把 Rust 的 &[u8] 切片直接映射為 JS 的 Uint8Array 視圖
        //   這一步完全在線性記憶體內做指標運算，開銷為零
        //
        //   ⚠️ SAFETY：這個視圖在下一次 memory.grow 之後會失效。
        //   必須確保在 view 存活期間不會發生任何記憶體配置。
        let js_buffer = unsafe { js_sys::Uint8Array::view(data) };

        JsFuture::from(writable.write_with_buffer_source(&js_buffer)?).await?;

        // 關閉串流，強制把快取寫入實體磁碟
        JsFuture::from(writable.close()).await?;
        Ok(())
    }

    /// 3. 讀取：把 OPFS 的檔案內容讀回 Wasm 線性記憶體
    pub async fn load_file(&self, filename: &str) -> Result<Vec<u8>, JsValue> {
        let fh_jsval = JsFuture::from(
            self.root_dir.get_file_handle(filename)
        ).await?;
        let file_handle: web_sys::FileSystemFileHandle = fh_jsval.into();

        let file_jsval = JsFuture::from(file_handle.get_file()).await?;
        let file: web_sys::File = file_jsval.into();

        let buf_jsval = JsFuture::from(file.array_buffer()).await?;
        let array = js_sys::Uint8Array::new(&buf_jsval);
        Ok(array.to_vec())      // 這一步是必要的複製（JS 堆 → Wasm 線性記憶體）
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

# ★ 發布版一定要開（見第 9 章）
[profile.release]
opt-level = 3
lto = true
codegen-units = 1
panic = "abort"
strip = true
```

編譯：

```bash
wasm-pack build --target web
```

### 3. 前端整合（`index.html`）

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <title>Wasm OPFS Storage Engine</title>
</head>
<body>
  <h1>WebAssembly OPFS 高效能儲存展示</h1>
  <button id="saveBtn" disabled>將 Wasm 大數據寫入硬碟</button>
  <button id="loadBtn" disabled>讀回並驗證</button>
  <p id="status">狀態：等待初始化…</p>

  <script type="module">
    import init, { WasmStorageEngine } from './pkg/wasm_opfs_engine.js';

    const status = document.getElementById('status');

    async function run() {
      await init();
      status.textContent = '狀態：Wasm 引擎初始化成功';

      const engine = await new WasmStorageEngine();
      document.getElementById('saveBtn').disabled = false;
      document.getElementById('loadBtn').disabled = false;

      document.getElementById('saveBtn').addEventListener('click', async () => {
        status.textContent = '狀態：大數據計算與寫入中…';

        const dataSize = 10 * 1024 * 1024;           // 10 MB
        const mockBigData = new Uint8Array(dataSize);
        for (let i = 0; i < dataSize; i++) mockBigData[i] = i % 256;

        try {
          const t0 = performance.now();
          await engine.save_file('firmware_backup.bin', mockBigData);
          const t1 = performance.now();
          status.textContent =
            `狀態：寫入 10 MB 成功！耗時 ${(t1 - t0).toFixed(2)} 毫秒（重整網頁不遺失）`;
        } catch (err) {
          status.textContent = `錯誤：${err}`;
        }
      });

      document.getElementById('loadBtn').addEventListener('click', async () => {
        const t0 = performance.now();
        const back = await engine.load_file('firmware_backup.bin');
        const t1 = performance.now();
        status.textContent =
          `狀態：讀回 ${(back.length / 1024 / 1024).toFixed(1)} MB，` +
          `耗時 ${(t1 - t0).toFixed(2)} 毫秒，首位元組 = ${back[0]}`;
      });
    }
    run();
  </script>
</body>
</html>
```

**驗證方式**：重新整理網頁後點「讀回」，資料仍在。也可在 DevTools 的 **Application → Storage → File System** 面板觀察 OPFS 內容。

---

## 二、方案 B：同步存取控制代碼（Worker 內，效能天花板）

**這是工業界處理超大型檔案（>50MB）與資料庫的正解**（見第 7 章情境 3）。

### `worker.js`

```javascript
import init, { ChunkedEngine } from './pkg/wasm_opfs_engine.js';

let engine;

self.onmessage = async (e) => {
  const { cmd, payload } = e.data;

  if (cmd === 'init') {
    await init();
    engine = new ChunkedEngine();
    // ★ createSyncAccessHandle 只能在 Worker 裡呼叫
    const root = await navigator.storage.getDirectory();
    const fh = await root.getFileHandle('bigdata.bin', { create: true });
    const handle = await fh.createSyncAccessHandle();
    engine.attach(handle);              // 把控制代碼交給 Wasm 側
    self.postMessage({ ok: true });
    return;
  }

  if (cmd === 'process') {
    // 大 buffer 用 Transferable 傳進來，零複製
    const result = engine.process_chunk(payload);
    // 回傳時同樣用 Transferable
    self.postMessage({ result }, [result.buffer]);
  }
};
```

### 主執行緒

```javascript
const worker = new Worker('./worker.js', { type: 'module' });

worker.postMessage({ cmd: 'init' });

// ★ 第二參數宣告 Transferable：轉移所有權而非複製（微秒級）
const buf = new ArrayBuffer(50 * 1024 * 1024);
worker.postMessage({ cmd: 'process', payload: buf }, [buf]);
// ⚠️ 轉移後主執行緒這一側的 buf.byteLength 立刻變成 0
```

### 同步控制代碼的核心操作

```javascript
const handle = await fh.createSyncAccessHandle();

handle.write(buffer, { at: offset });   // 同步寫入，無 Promise
handle.read(buffer,  { at: offset });   // 同步隨機讀取，像 pread
handle.getSize();                       // 檔案大小
handle.truncate(newSize);               // 截斷
handle.flush();                         // 強制落盤
handle.close();                         // ★ 一定要關，否則鎖不會釋放
```

---

## 三、滑動窗口分塊讀取（繞開 4GB 上限）

```rust
/// 概念骨架：記憶體只有 50MB，卻能處理 100GB 檔案
const CHUNK: u64 = 4 * 1024 * 1024;              // 4MB 對齊
const WINDOW: usize = 50 * 1024 * 1024;          // 50MB 常駐窗口

pub struct ChunkedReader {
    handle: SyncHandle,          // OPFS 同步控制代碼（或 HTTP Range 的封裝）
    window: Vec<u8>,
    window_start: u64,
    window_len: usize,
    file_size: u64,
}

impl ChunkedReader {
    /// 讀取任意位置；只有跨出當前窗口時才觸發磁碟 I/O
    pub fn read_at(&mut self, offset: u64, len: usize) -> &[u8] {
        let end = offset + len as u64;
        let in_window = offset >= self.window_start
            && end <= self.window_start + self.window_len as u64;

        if !in_window {
            // 對齊到區塊邊界，避免因為讀一個位元組而整窗重載
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

**四個實作要點**：

1. **窗口對齊**到 1MB/4MB 邊界。
2. **依存取模式調整**：順序掃描 → 大窗口 + 預讀；隨機跳躍 → 小窗口 + 多窗口 LRU。
3. **必須在 Worker 裡**（`createSyncAccessHandle` 的規範限制）。
4. **遠端檔案用同一套邏輯**——把 `handle.read_at()` 換成 `fetch(url, { headers: { Range: 'bytes=A-B' } })`。

---

## 四、三種儲存機制的選型與對應實作

| 場景 | 機制 | 關鍵 API |
|---|---|---|
| 大型檔案 / 資料庫（>50MB） | **OPFS + Worker 同步控制代碼** | `createSyncAccessHandle()` |
| 遊戲存檔 / 小型 JSON（高相容性） | **IndexedDB / IDBFS** | `FS.mount(IDBFS)` + `FS.syncfs()` |
| 後端雲原生 | **WASI 檔案系統** | `std::fs` + 預先開啟的目錄能力 |

### IDBFS（Emscripten）

```javascript
// C 側照常 fopen("/save/game.sav", "wb")
Module.onRuntimeInitialized = () => {
  FS.mkdir('/save');
  FS.mount(IDBFS, {}, '/save');
  FS.syncfs(true, err => {        // true = 從 IndexedDB 載入到 MEMFS
    if (err) throw err;
    startGame();
  });
};

function saveGame() {
  FS.syncfs(false, err => {       // false = 從 MEMFS 寫回 IndexedDB
    if (err) console.error(err);
  });
}
```

### WASI（後端）

```rust
// target: wasm32-wasip1
use std::fs::File;
use std::io::{Read, Write};

fn main() -> std::io::Result<()> {
    // 只能存取宿主預先開啟並授權的目錄
    let mut f = File::create("/sandbox/output.bin")?;
    f.write_all(b"hello from wasm")?;

    let mut buf = String::new();
    File::open("/sandbox/input.txt")?.read_to_string(&mut buf)?;
    println!("{}", buf);
    Ok(())
}
```

```bash
# 宿主端：能力清單就是這一行
wasmtime run --dir=./data::/sandbox app.wasm
```

---

## 五、架構優勢與盲點防禦

| 面向 | 做法 | 為什麼 |
|---|---|---|
| **零拷貝** | `js_sys::Uint8Array::view(data)` | 避免「Rust 線性記憶體 → JS 堆」的雙倍記憶體開銷 |
| ⚠️ **視圖失效** | view 存活期間**不得**觸發任何記憶體配置 | `memory.grow` 會 detach `ArrayBuffer`，讓 view 指向無效區域 |
| **避開主執行緒卡死** | 把儲存引擎放進 Web Worker | 同步 I/O 在主執行緒會凍結 UI（也因此規範直接禁止） |
| **極致 I/O 效能** | Worker 內用 `createSyncAccessHandle()` | 消除 async poll 開銷，達到接近原生的順序寫入 |
| **配額被驅逐** | `await navigator.storage.persist()` | 未標記 persistent 的資料可能在磁碟壓力下被清除 |
| **多分頁搶鎖** | Web Locks API 或 `BroadcastChannel` 協調 | 同一檔案同時只能有一個 sync access handle |
| **使用者無法備份** | 自行提供「匯出檔案」功能 | OPFS 對使用者不可見 |

---

## 六、量測範本

```javascript
// 寫入吞吐
const t0 = performance.now();
await engine.save_file('bench.bin', data);
const t1 = performance.now();
const mbps = (data.length / 1024 / 1024) / ((t1 - t0) / 1000);
console.log(`寫入吞吐：${mbps.toFixed(1)} MB/s`);

// 記憶體足跡（Chrome）
if (performance.measureUserAgentSpecificMemory) {
  const m = await performance.measureUserAgentSpecificMemory();
  console.log('分頁記憶體：', (m.bytes / 1024 / 1024).toFixed(1), 'MB');
}

// 配額
const est = await navigator.storage.estimate();
console.log(`已用 ${(est.usage/1e6).toFixed(1)}MB / 配額 ${(est.quota/1e6).toFixed(1)}MB`);
```
