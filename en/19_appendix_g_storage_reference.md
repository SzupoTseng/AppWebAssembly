# Appendix G: Storage Implementation Reference (Rust + Wasm + OPFS)

> This appendix provides a complete implementation for the **front-end web (Rust + WebAssembly + OPFS)** — currently the industry's gold standard (Figma, Adobe Web and the like) for high-performance big-data persistence in a pure front-end environment.
>
> The examples show how to use OPFS's `FileSystemWritableFileStream` and `FileSystemSyncAccessHandle` to perform **zero-copy** binary large-file reads and writes inside Wasm, so the data stays on the client permanently even after the page reloads.
>
> ⚠️ **`web-sys`'s API names and builder forms change between versions** (the way `FileSystemGetFileOptions` is constructed differs across versions, for instance). The code below is an **architectural reference**; when you actually compile, follow the documentation for the `web-sys` version you use.

---

## 1. Approach A: An asynchronous write stream (usable on the main thread)

### 1. The Rust core (`src/lib.rs`)

```rust
use wasm_bindgen::prelude::*;
use wasm_bindgen_futures::JsFuture;
use web_sys::{FileSystemDirectoryHandle, FileSystemWritableFileStream, StorageManager};

#[wasm_bindgen]
pub struct WasmStorageEngine {
    /// Hold the engine state so we don't re-initialize
    root_dir: FileSystemDirectoryHandle,
}

#[wasm_bindgen]
impl WasmStorageEngine {
    /// 1. Initialize the engine: ask the browser for the OPFS root directory handle
    #[wasm_bindgen(constructor)]
    pub async fn new() -> Result<WasmStorageEngine, JsValue> {
        let window = web_sys::window().ok_or("no window object")?;
        let storage: StorageManager = window.navigator().storage();

        // Asynchronously obtain the Origin Private File System root
        let root_dir_jsval = JsFuture::from(storage.get_directory()).await?;
        let root_dir: FileSystemDirectoryHandle = root_dir_jsval.into();

        Ok(WasmStorageEngine { root_dir })
    }

    /// 2. High-performance persistent write: binary data in Wasm memory straight into OPFS
    pub async fn save_file(&self, filename: &str, data: &[u8]) -> Result<(), JsValue> {
        // Create or open the file
        let mut options = web_sys::FileSystemGetFileOptions::new();
        options.create(true);
        let fh_jsval = JsFuture::from(
            self.root_dir.get_file_handle_with_options(filename, &options)
        ).await?;
        let file_handle: web_sys::FileSystemFileHandle = fh_jsval.into();

        // Open OPFS's dedicated high-performance write stream
        let writable_jsval = JsFuture::from(file_handle.create_writable()).await?;
        let writable: FileSystemWritableFileStream = writable_jsval.into();

        // ★ Zero-copy optimization: map Rust's &[u8] slice directly as a JS Uint8Array view.
        //   This step is pure pointer arithmetic inside linear memory, at zero cost.
        //
        //   ⚠️ SAFETY: this view is invalidated by the next memory.grow.
        //   You must ensure no allocation happens while the view is alive.
        let js_buffer = unsafe { js_sys::Uint8Array::view(data) };

        JsFuture::from(writable.write_with_buffer_source(&js_buffer)?).await?;

        // Close the stream, forcing the cache to physical disk
        JsFuture::from(writable.close()).await?;
        Ok(())
    }

    /// 3. Read: pull the OPFS file's contents back into Wasm linear memory
    pub async fn load_file(&self, filename: &str) -> Result<Vec<u8>, JsValue> {
        let fh_jsval = JsFuture::from(
            self.root_dir.get_file_handle(filename)
        ).await?;
        let file_handle: web_sys::FileSystemFileHandle = fh_jsval.into();

        let file_jsval = JsFuture::from(file_handle.get_file()).await?;
        let file: web_sys::File = file_jsval.into();

        let buf_jsval = JsFuture::from(file.array_buffer()).await?;
        let array = js_sys::Uint8Array::new(&buf_jsval);
        Ok(array.to_vec())      // this copy is unavoidable (JS heap → Wasm linear memory)
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

# ★ Always enable these for release builds (see Chapter 9)
[profile.release]
opt-level = 3
lto = true
codegen-units = 1
panic = "abort"
strip = true
```

Build:

```bash
wasm-pack build --target web
```

### 3. Front-end integration (`index.html`)

```html
<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8">
  <title>Wasm OPFS Storage Engine</title>
</head>
<body>
  <h1>WebAssembly OPFS high-performance storage demo</h1>
  <button id="saveBtn" disabled>Write Wasm big data to disk</button>
  <button id="loadBtn" disabled>Read back and verify</button>
  <p id="status">Status: waiting for initialization…</p>

  <script type="module">
    import init, { WasmStorageEngine } from './pkg/wasm_opfs_engine.js';

    const status = document.getElementById('status');

    async function run() {
      await init();
      status.textContent = 'Status: Wasm engine initialized';

      const engine = await new WasmStorageEngine();
      document.getElementById('saveBtn').disabled = false;
      document.getElementById('loadBtn').disabled = false;

      document.getElementById('saveBtn').addEventListener('click', async () => {
        status.textContent = 'Status: computing and writing big data…';

        const dataSize = 10 * 1024 * 1024;           // 10 MB
        const mockBigData = new Uint8Array(dataSize);
        for (let i = 0; i < dataSize; i++) mockBigData[i] = i % 256;

        try {
          const t0 = performance.now();
          await engine.save_file('firmware_backup.bin', mockBigData);
          const t1 = performance.now();
          status.textContent =
            `Status: wrote 10 MB in ${(t1 - t0).toFixed(2)} ms (survives a reload)`;
        } catch (err) {
          status.textContent = `Error: ${err}`;
        }
      });

      document.getElementById('loadBtn').addEventListener('click', async () => {
        const t0 = performance.now();
        const back = await engine.load_file('firmware_backup.bin');
        const t1 = performance.now();
        status.textContent =
          `Status: read back ${(back.length / 1024 / 1024).toFixed(1)} MB in ` +
          `${(t1 - t0).toFixed(2)} ms, first byte = ${back[0]}`;
      });
    }
    run();
  </script>
</body>
</html>
```

**How to verify**: reload the page and click "Read back" — the data is still there. You can also inspect the OPFS contents in DevTools under **Application → Storage → File System**.

---

## 2. Approach B: A synchronous access handle (inside a Worker, the performance ceiling)

**This is the industry's answer for very large files (>50 MB) and databases** (see Chapter 7 Scenario 3).

### `worker.js`

```javascript
import init, { ChunkedEngine } from './pkg/wasm_opfs_engine.js';

let engine;

self.onmessage = async (e) => {
  const { cmd, payload } = e.data;

  if (cmd === 'init') {
    await init();
    engine = new ChunkedEngine();
    // ★ createSyncAccessHandle can only be called inside a Worker
    const root = await navigator.storage.getDirectory();
    const fh = await root.getFileHandle('bigdata.bin', { create: true });
    const handle = await fh.createSyncAccessHandle();
    engine.attach(handle);              // hand the handle over to the Wasm side
    self.postMessage({ ok: true });
    return;
  }

  if (cmd === 'process') {
    // the large buffer arrived as a transferable — zero copy
    const result = engine.process_chunk(payload);
    // send it back as a transferable too
    self.postMessage({ result }, [result.buffer]);
  }
};
```

### The main thread

```javascript
const worker = new Worker('./worker.js', { type: 'module' });

worker.postMessage({ cmd: 'init' });

// ★ the second argument declares transferables: ownership transfer, not a copy (microseconds)
const buf = new ArrayBuffer(50 * 1024 * 1024);
worker.postMessage({ cmd: 'process', payload: buf }, [buf]);
// ⚠️ after transfer, buf.byteLength on the main-thread side immediately becomes 0
```

### The sync access handle's core operations

```javascript
const handle = await fh.createSyncAccessHandle();

handle.write(buffer, { at: offset });   // synchronous write, no Promise
handle.read(buffer,  { at: offset });   // synchronous random read, like pread
handle.getSize();                       // file size
handle.truncate(newSize);               // truncate
handle.flush();                         // force to disk
handle.close();                         // ★ always close, or the lock is never released
```

---

## 3. Sliding-window chunked reading (getting around the 4 GB ceiling)

```rust
/// Conceptual skeleton: only 50 MB of memory, yet it handles a 100 GB file
const CHUNK: u64 = 4 * 1024 * 1024;              // 4 MB alignment
const WINDOW: usize = 50 * 1024 * 1024;          // a resident 50 MB window

pub struct ChunkedReader {
    handle: SyncHandle,          // the OPFS sync access handle (or an HTTP Range wrapper)
    window: Vec<u8>,
    window_start: u64,
    window_len: usize,
    file_size: u64,
}

impl ChunkedReader {
    /// Read at an arbitrary position; disk I/O happens only when we leave the window
    pub fn read_at(&mut self, offset: u64, len: usize) -> &[u8] {
        let end = offset + len as u64;
        let in_window = offset >= self.window_start
            && end <= self.window_start + self.window_len as u64;

        if !in_window {
            // Align to a block boundary, so reading one byte doesn't reload the whole window
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

**Four implementation points**:

1. **Align the window** to a 1 MB/4 MB boundary.
2. **Tune to the access pattern**: sequential scan → a large window plus readahead; random jumps → small windows plus an LRU of several.
3. **It must run in a Worker** (a specification restriction on `createSyncAccessHandle`).
4. **Remote files use the same logic** — swap `handle.read_at()` for `fetch(url, { headers: { Range: 'bytes=A-B' } })`.

---

## 4. Choosing among the three storage mechanisms, and their implementations

| Scenario | Mechanism | Key API |
|---|---|---|
| Large files / databases (>50 MB) | **OPFS + a Worker sync access handle** | `createSyncAccessHandle()` |
| Game saves / small JSON (broad compatibility) | **IndexedDB / IDBFS** | `FS.mount(IDBFS)` + `FS.syncfs()` |
| Backend cloud-native | **The WASI filesystem** | `std::fs` plus pre-opened directory capabilities |

### IDBFS (Emscripten)

```javascript
// The C side still calls fopen("/save/game.sav", "wb") as usual
Module.onRuntimeInitialized = () => {
  FS.mkdir('/save');
  FS.mount(IDBFS, {}, '/save');
  FS.syncfs(true, err => {        // true = load from IndexedDB into MEMFS
    if (err) throw err;
    startGame();
  });
};

function saveGame() {
  FS.syncfs(false, err => {       // false = write MEMFS back to IndexedDB
    if (err) console.error(err);
  });
}
```

### WASI (server side)

```rust
// target: wasm32-wasip1
use std::fs::File;
use std::io::{Read, Write};

fn main() -> std::io::Result<()> {
    // Only directories the host pre-opened and granted are reachable
    let mut f = File::create("/sandbox/output.bin")?;
    f.write_all(b"hello from wasm")?;

    let mut buf = String::new();
    File::open("/sandbox/input.txt")?.read_to_string(&mut buf)?;
    println!("{}", buf);
    Ok(())
}
```

```bash
# On the host: this one line is the entire capability list
wasmtime run --dir=./data::/sandbox app.wasm
```

---

## 5. Architectural advantages and defending the blind spots

| Aspect | Approach | Why |
|---|---|---|
| **Zero copy** | `js_sys::Uint8Array::view(data)` | Avoids the doubled memory cost of "Rust linear memory → JS heap" |
| ⚠️ **View invalidation** | **No** allocation may occur while the view is alive | `memory.grow` detaches the `ArrayBuffer`, leaving the view pointing at invalid space |
| **Avoiding a frozen main thread** | Put the storage engine inside a Web Worker | Synchronous I/O on the main thread would freeze the UI (which is why the specification forbids it outright) |
| **Maximum I/O performance** | Use `createSyncAccessHandle()` inside the Worker | Removes async poll overhead, reaching near-native sequential write throughput |
| **Quota eviction** | `await navigator.storage.persist()` | Data not marked persistent may be cleared under disk pressure |
| **Multiple tabs fighting for the lock** | Coordinate with the Web Locks API or `BroadcastChannel` | One file may have only one sync access handle at a time |
| **The user cannot back up** | Provide an "export file" feature yourself | OPFS is invisible to the user |

---

## 6. A measurement template

```javascript
// Write throughput
const t0 = performance.now();
await engine.save_file('bench.bin', data);
const t1 = performance.now();
const mbps = (data.length / 1024 / 1024) / ((t1 - t0) / 1000);
console.log(`Write throughput: ${mbps.toFixed(1)} MB/s`);

// Memory footprint (Chrome)
if (performance.measureUserAgentSpecificMemory) {
  const m = await performance.measureUserAgentSpecificMemory();
  console.log('Tab memory:', (m.bytes / 1024 / 1024).toFixed(1), 'MB');
}

// Quota
const est = await navigator.storage.estimate();
console.log(`Used ${(est.usage/1e6).toFixed(1)} MB / quota ${(est.quota/1e6).toFixed(1)} MB`);
```
