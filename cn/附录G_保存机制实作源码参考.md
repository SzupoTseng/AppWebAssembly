# 附录G　保存机制实作源码参考（Rust + Wasm + OPFS）

> 本附录提供**前端网页（Rust + WebAssembly + OPFS）** 的完整实作方案——这是目前工业界（Figma、Adobe Web 一类）在纯前端环境下解决大数据高性能持久化的黄金标准。
>
> 范例展示如何利用 OPFS 的 `FileSystemWritableFileStream` 与 `FileSystemSyncAccessHandle`，在 Wasm 内部进行**零拷贝**的二进位大文件读写，确保网页即使重整，数据依然永久保存在客户端。
>
> ⚠️ **`web-sys` 的 API 名称与 builder 形式会随版本变动**（例如 `FileSystemGetFileOptions` 的建构方式在不同版本有差异）。以下代码为**架构参考**，实际编译时请以你使用的 `web-sys` 版本文档为准。

---

## 一、方案 A：异步写入串流（主线程可用）

### 1. Rust 内核（`src/lib.rs`）

```rust
use wasm_bindgen::prelude::*;
use wasm_bindgen_futures::JsFuture;
use web_sys::{FileSystemDirectoryHandle, FileSystemWritableFileStream, StorageManager};

#[wasm_bindgen]
pub struct WasmStorageEngine {
    /// 保持引擎状态，避免重复初始化
    root_dir: FileSystemDirectoryHandle,
}

#[wasm_bindgen]
impl WasmStorageEngine {
    /// 1. 初始化引擎：向浏览器请求 OPFS 的根目录句柄
    #[wasm_bindgen(constructor)]
    pub async fn new() -> Result<WasmStorageEngine, JsValue> {
        let window = web_sys::window().ok_or("找不到 window 对象")?;
        let storage: StorageManager = window.navigator().storage();

        // 异步取得 Origin Private File System 的根目录
        let root_dir_jsval = JsFuture::from(storage.get_directory()).await?;
        let root_dir: FileSystemDirectoryHandle = root_dir_jsval.into();

        Ok(WasmStorageEngine { root_dir })
    }

    /// 2. 高性能持久化写入：把 Wasm 内存中的二进位数据直通写入 OPFS
    pub async fn save_file(&self, filename: &str, data: &[u8]) -> Result<(), JsValue> {
        // 创建或打开文件
        let mut options = web_sys::FileSystemGetFileOptions::new();
        options.create(true);
        let fh_jsval = JsFuture::from(
            self.root_dir.get_file_handle_with_options(filename, &options)
        ).await?;
        let file_handle: web_sys::FileSystemFileHandle = fh_jsval.into();

        // 打开 OPFS 专属的高性能写入串流
        let writable_jsval = JsFuture::from(file_handle.create_writable()).await?;
        let writable: FileSystemWritableFileStream = writable_jsval.into();

        // ★ 零拷贝优化：把 Rust 的 &[u8] 切片直接映射为 JS 的 Uint8Array 视图
        //   这一步完全在线性内存内做指针运算，开销为零
        //
        //   ⚠️ SAFETY：这个视图在下一次 memory.grow 之后会失效。
        //   必须确保在 view 存活期间不会发生任何内存配置。
        let js_buffer = unsafe { js_sys::Uint8Array::view(data) };

        JsFuture::from(writable.write_with_buffer_source(&js_buffer)?).await?;

        // 关闭串流，强制把缓存写入实体磁盘
        JsFuture::from(writable.close()).await?;
        Ok(())
    }

    /// 3. 读取：把 OPFS 的文件内容读回 Wasm 线性内存
    pub async fn load_file(&self, filename: &str) -> Result<Vec<u8>, JsValue> {
        let fh_jsval = JsFuture::from(
            self.root_dir.get_file_handle(filename)
        ).await?;
        let file_handle: web_sys::FileSystemFileHandle = fh_jsval.into();

        let file_jsval = JsFuture::from(file_handle.get_file()).await?;
        let file: web_sys::File = file_jsval.into();

        let buf_jsval = JsFuture::from(file.array_buffer()).await?;
        let array = js_sys::Uint8Array::new(&buf_jsval);
        Ok(array.to_vec())      // 这一步是必要的拷贝（JS 堆 → Wasm 线性内存）
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

# ★ 发布版一定要开（见第 9 章）
[profile.release]
opt-level = 3
lto = true
codegen-units = 1
panic = "abort"
strip = true
```

编译：

```bash
wasm-pack build --target web
```

### 3. 前端集成（`index.html`）

```html
<!DOCTYPE html>
<html lang="zh-TW">
<head>
  <meta charset="UTF-8">
  <title>Wasm OPFS Storage Engine</title>
</head>
<body>
  <h1>WebAssembly OPFS 高性能保存展示</h1>
  <button id="saveBtn" disabled>将 Wasm 大数据写入硬盘</button>
  <button id="loadBtn" disabled>读回并验证</button>
  <p id="status">状态：等待初始化…</p>

  <script type="module">
    import init, { WasmStorageEngine } from './pkg/wasm_opfs_engine.js';

    const status = document.getElementById('status');

    async function run() {
      await init();
      status.textContent = '状态：Wasm 引擎初始化成功';

      const engine = await new WasmStorageEngine();
      document.getElementById('saveBtn').disabled = false;
      document.getElementById('loadBtn').disabled = false;

      document.getElementById('saveBtn').addEventListener('click', async () => {
        status.textContent = '状态：大数据计算与写入中…';

        const dataSize = 10 * 1024 * 1024;           // 10 MB
        const mockBigData = new Uint8Array(dataSize);
        for (let i = 0; i < dataSize; i++) mockBigData[i] = i % 256;

        try {
          const t0 = performance.now();
          await engine.save_file('firmware_backup.bin', mockBigData);
          const t1 = performance.now();
          status.textContent =
            `状态：写入 10 MB 成功！耗时 ${(t1 - t0).toFixed(2)} 毫秒（重整网页不遗失）`;
        } catch (err) {
          status.textContent = `错误：${err}`;
        }
      });

      document.getElementById('loadBtn').addEventListener('click', async () => {
        const t0 = performance.now();
        const back = await engine.load_file('firmware_backup.bin');
        const t1 = performance.now();
        status.textContent =
          `状态：读回 ${(back.length / 1024 / 1024).toFixed(1)} MB，` +
          `耗时 ${(t1 - t0).toFixed(2)} 毫秒，首字节 = ${back[0]}`;
      });
    }
    run();
  </script>
</body>
</html>
```

**验证方式**：刷新网页后点「读回」，数据仍在。也可在 DevTools 的 **Application → Storage → File System** 面板观察 OPFS 内容。

---

## 二、方案 B：同步访问句柄（Worker 内，性能天花板）

**这是工业界处理超大型文件（>50MB）与数据库的正解**（见第 7 章情境 3）。

### `worker.js`

```javascript
import init, { ChunkedEngine } from './pkg/wasm_opfs_engine.js';

let engine;

self.onmessage = async (e) => {
  const { cmd, payload } = e.data;

  if (cmd === 'init') {
    await init();
    engine = new ChunkedEngine();
    // ★ createSyncAccessHandle 只能在 Worker 里调用
    const root = await navigator.storage.getDirectory();
    const fh = await root.getFileHandle('bigdata.bin', { create: true });
    const handle = await fh.createSyncAccessHandle();
    engine.attach(handle);              // 把句柄交给 Wasm 侧
    self.postMessage({ ok: true });
    return;
  }

  if (cmd === 'process') {
    // 大 buffer 用 Transferable 传进来，零拷贝
    const result = engine.process_chunk(payload);
    // 回传时同样用 Transferable
    self.postMessage({ result }, [result.buffer]);
  }
};
```

### 主线程

```javascript
const worker = new Worker('./worker.js', { type: 'module' });

worker.postMessage({ cmd: 'init' });

// ★ 第二参数声明 Transferable：转移所有权而非拷贝（微秒级）
const buf = new ArrayBuffer(50 * 1024 * 1024);
worker.postMessage({ cmd: 'process', payload: buf }, [buf]);
// ⚠️ 转移后主线程这一侧的 buf.byteLength 立刻变成 0
```

### 同步句柄的内核操作

```javascript
const handle = await fh.createSyncAccessHandle();

handle.write(buffer, { at: offset });   // 同步写入，无 Promise
handle.read(buffer,  { at: offset });   // 同步随机读取，像 pread
handle.getSize();                       // 文件大小
handle.truncate(newSize);               // 截断
handle.flush();                         // 强制落盘
handle.close();                         // ★ 一定要关，否则锁不会释放
```

---

## 三、滑动窗口分块读取（绕开 4GB 上限）

```rust
/// 概念骨架：内存只有 50MB，却能处理 100GB 文件
const CHUNK: u64 = 4 * 1024 * 1024;              // 4MB 对齐
const WINDOW: usize = 50 * 1024 * 1024;          // 50MB 常驻窗口

pub struct ChunkedReader {
    handle: SyncHandle,          // OPFS 同步句柄（或 HTTP Range 的封装）
    window: Vec<u8>,
    window_start: u64,
    window_len: usize,
    file_size: u64,
}

impl ChunkedReader {
    /// 读取任意位置；只有跨出当前窗口时才触发磁盘 I/O
    pub fn read_at(&mut self, offset: u64, len: usize) -> &[u8] {
        let end = offset + len as u64;
        let in_window = offset >= self.window_start
            && end <= self.window_start + self.window_len as u64;

        if !in_window {
            // 对齐到区块边界，避免因为读一个字节而整窗重载
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

**四个实作要点**：

1. **窗口对齐**到 1MB/4MB 边界。
2. **依访问模式调整**：顺序扫描 → 大窗口 + 预读；随机跳跃 → 小窗口 + 多窗口 LRU。
3. **必须在 Worker 里**（`createSyncAccessHandle` 的规范限制）。
4. **远程文件用同一套逻辑**——把 `handle.read_at()` 换成 `fetch(url, { headers: { Range: 'bytes=A-B' } })`。

---

## 四、三种保存机制的选型与对应实作

| 场景 | 机制 | 关键 API |
|---|---|---|
| 大型文件 / 数据库（>50MB） | **OPFS + Worker 同步句柄** | `createSyncAccessHandle()` |
| 游戏存盘 / 小型 JSON（高兼容性） | **IndexedDB / IDBFS** | `FS.mount(IDBFS)` + `FS.syncfs()` |
| 后端云原生 | **WASI 文件系统** | `std::fs` + 预先打开的目录能力 |

### IDBFS（Emscripten）

```javascript
// C 侧照常 fopen("/save/game.sav", "wb")
Module.onRuntimeInitialized = () => {
  FS.mkdir('/save');
  FS.mount(IDBFS, {}, '/save');
  FS.syncfs(true, err => {        // true = 从 IndexedDB 加载到 MEMFS
    if (err) throw err;
    startGame();
  });
};

function saveGame() {
  FS.syncfs(false, err => {       // false = 从 MEMFS 写回 IndexedDB
    if (err) console.error(err);
  });
}
```

### WASI（后端）

```rust
// target: wasm32-wasip1
use std::fs::File;
use std::io::{Read, Write};

fn main() -> std::io::Result<()> {
    // 只能访问宿主预先打开并授权的目录
    let mut f = File::create("/sandbox/output.bin")?;
    f.write_all(b"hello from wasm")?;

    let mut buf = String::new();
    File::open("/sandbox/input.txt")?.read_to_string(&mut buf)?;
    println!("{}", buf);
    Ok(())
}
```

```bash
# 宿主端：能力清单就是这一行
wasmtime run --dir=./data::/sandbox app.wasm
```

---

## 五、架构优势与盲点防御

| 面向 | 做法 | 为什么 |
|---|---|---|
| **零拷贝** | `js_sys::Uint8Array::view(data)` | 避免「Rust 线性内存 → JS 堆」的双倍内存开销 |
| ⚠️ **视图失效** | view 存活期间**不得**触发任何内存配置 | `memory.grow` 会 detach `ArrayBuffer`，让 view 指向无效区域 |
| **避开主线程卡死** | 把保存引擎放进 Web Worker | 同步 I/O 在主线程会冻结 UI（也因此规范直接禁止） |
| **极致 I/O 性能** | Worker 内用 `createSyncAccessHandle()` | 消除 async poll 开销，达到接近原生的顺序写入 |
| **配额被驱逐** | `await navigator.storage.persist()` | 未标记 persistent 的数据可能在磁盘压力下被清除 |
| **多分页抢锁** | Web Locks API 或 `BroadcastChannel` 协调 | 同一文件同时只能有一个 sync access handle |
| **用户无法备份** | 自行提供「导出文件」功能 | OPFS 对用户不可见 |

---

## 六、量测范本

```javascript
// 写入吞吐
const t0 = performance.now();
await engine.save_file('bench.bin', data);
const t1 = performance.now();
const mbps = (data.length / 1024 / 1024) / ((t1 - t0) / 1000);
console.log(`写入吞吐：${mbps.toFixed(1)} MB/s`);

// 内存足迹（Chrome）
if (performance.measureUserAgentSpecificMemory) {
  const m = await performance.measureUserAgentSpecificMemory();
  console.log('分页内存：', (m.bytes / 1024 / 1024).toFixed(1), 'MB');
}

// 配额
const est = await navigator.storage.estimate();
console.log(`已用 ${(est.usage/1e6).toFixed(1)}MB / 配额 ${(est.quota/1e6).toFixed(1)}MB`);
```
