# 附录B　名词与工具速查

> 这是一份**查阅表**，不是教材。每一列的最后一栏标明它在书里的出处——**看到不懂的名词先查这里，需要理解为什么再翻过去。**

## 一、内核概念名词

| 名词 | 一句话解释 | 在本书哪里 |
|---|---|---|
| **WebAssembly (Wasm)** | 一台规格定义出来的抽象堆栈机器的二进位指令格式；不是任何实体 CPU 的机器码 | 第 2 章 |
| **WAT (WebAssembly Text)** | Wasm 的可读文本格式，与二进位一一对应（`wasm2wat` 可无损转换） | 第 2、9 章 |
| **线性内存 (Linear Memory)** | 一整块连续、可寻址的字节数组；1 页 = 64 KiB，只能增长不能缩小 | 第 2、8 章 |
| **Trap** | 运行期的不可捕捉错误（越界、除以零、unreachable），在 JS 侧表现为 `RuntimeError` | 附录 A |
| **保护页 (Guard Page)** | 引擎保留 8GiB 虚拟地址空间，用 MMU 免费完成界检查的技巧 | 第 2、8 章 |
| **结构化控制流** | Wasm 没有 `goto`，只有 `block`/`loop`/`if` 与往外跳的 `br`——这是单趟验证的前提 | 第 2 章 |
| **验证器 (Validator)** | 加载时做 O(n) 单趟检查：堆栈类型一致、控制流结构化、索引在界内 | 第 2 章 |
| **分层编译 (Tiering)** | Liftoff（快速产码）→ TurboFan（优化产码）的双轨赛跑 | 第 2 章 |
| **串流编译 (Streaming Compilation)** | `instantiateStreaming`：第一个字节到达就开始编译 | 第 2、5 章 |
| **胶水代码 (Glue Code)** | JS 侧负责类型转换、内存管理、API 桥接的那一层 | 第 2 章 |
| **零拷贝 (Zero-copy)** | 用 `TypedArray` 在同一块 `ArrayBuffer` 上开视图，而不搬数据 | 第 2、6 章 |
| **SoA (Structure of Arrays)** | 把 `[{x,y,z}...]` 改成三条连续数组——缓存友善布局 | 第 6 章 |
| **CSR / CSC** | 压缩稀疏列/行格式，稀疏矩阵的标准紧凑表示 | 附录 E、F |
| **跨来源隔离 (Cross-Origin Isolation)** | COOP + COEP 同时满足时的页面状态，`SharedArrayBuffer` 的前提 | 第 3、5 章 |
| **能力式安全 (Capability-based Security)** | 模块默认两手空空，能力必须由宿主显式递入 | 第 1、7 章 |
| **Component Model / WIT** | Wasm 模块之间用高级类型沟通的接口模型与描述语言 | 第 7 章、附录 A |
| **LEB128** | 变长整数编码；Wasm 所有长度与索引都用它 | 附录 M §1 |
| **多态堆栈 (Polymorphic Stack)** | `unreachable` 之后的死代码如何通过验证的机制 | 附录 M §2 |
| **Table / `call_indirect`** | Wasm 没有函数指针，函数指针其实是「表索引」 | 附录 M §3 |
| **Tag / `exnref`** | Wasm 3.0 例外处理的标签与不透明例外参考 | 附录 M §4 |
| **JSPI** | JavaScript Promise Integration：引擎在堆栈层面挂起/恢复 Wasm，让同步代码能等 Promise | 第 3 章墙七、附录 M §5 |
| **Asyncify** | JSPI 之前的替代方案：Binaryen 改写整个模块来仿真挂起（贵） | 附录 M §5 |
| **Relaxed SIMD** | 放弃确定性换硬件映射；**需要确定性的场景必须禁用** | 附录 M §7 |
| **Multiple memories** | Wasm 3.0：一个模块多块线性内存，各自仍是 wasm32 | 第 8 章情境 4、附录 M §8 |
| **proxy-wasm** | Envoy/Istio 等代理采用的 Wasm 插件 ABI | 附录 M §11 |

---

## 二、保存相关

| 名词 | 解释 | 适用 |
|---|---|---|
| **MEMFS** | Emscripten 在线性内存里假造的 POSIX 文件系统 | 暂存中间档（**吃 4GB 额度**） |
| **IDBFS** | 把 MEMFS 整包同步进 IndexedDB（`FS.syncfs`） | 游戏存盘、设置（几百 KB） |
| **WASMFS** | Emscripten 新一代文件系统后端，可直通 OPFS | 取代 MEMFS/IDBFS 的方向 |
| **OPFS** | Origin Private File System，浏览器为每个来源开的私有磁盘空间 | **一切需要持久化的东西** |
| **`opfs` VFS**（SQLite） | 第一代 OPFS 后端，靠异步代理 + `Atomics.wait`；**需要 `SharedArrayBuffer`／跨来源隔离** | 需要多连接时 |
| **`opfs-sahpool` VFS** | 同步句柄池；**不需要 COOP/COEP，且官方文档列为最快**；不支持多连接 | **静态托管的首选** |
| **`createSyncAccessHandle()`** | OPFS 的同步随机访问句柄（**只能在 Worker 里用**） | 数据库、大文件串流 |
| **`navigator.storage.persist()`** | 请求把数据标记为 persistent，避免磁盘压力下被驱逐 | 重要数据 |
| **VFS (Virtual File System)** | SQLite 为移植性设计的保存抽象层；OPFS VFS 就是它的一个实作 | 第 7 章 |

---

## 三、工具链

### 编译器 / 工具链前端

| 工具 | 语言 | 特性 |
|---|---|---|
| **Emscripten** (`emcc`) | C / C++ | **仿真一整个 POSIX 环境**（libc、文件系统、SDL→WebGL、pthread→Worker）。移植现成大型 C/C++ 项目的首选 |
| **`wasm-pack` / `wasm-bindgen`** | Rust | **只做类型桥接**，胶水精简。从零写的新项目首选 |
| **`cargo` + `wasm32-unknown-unknown`** | Rust | 不带任何 JS 绑定的裸 Wasm |
| **TinyGo** | Go | 大幅缩减 Go 运行期体积（代价：支持子集） |
| **AssemblyScript** | TS 风格语法 | 语法近似 TypeScript，直接编译为 Wasm，前端工程师的平滑入口 |
| **Zig** | Zig | 原生支持 `wasm32-freestanding` / `wasm32-wasi`，无运行期负担 |
| **Blazor** | C# | .NET 生态；体积与冷启动是主要代价 |

### 二进位工具

| 工具 | 用途 |
|---|---|
| **`wasm-opt`**（Binaryen） | **最高投报率的优化工具**。`-Oz` 体积优先、`-O3` 速度优先、`--strip-debug` |
| **`wasm2wat` / `wat2wasm`**（WABT） | 二进位 ↔ 文本格式无损互转 |
| **`wasm-objdump`**（WABT） | 查看区段、反汇编（`-d`）、看 import/export（`-x`） |
| **`wasm-decompile`**（WABT） | 产出类 C 的可读伪码（逆向分析的第一站） |
| **`wasm-strip`**（WABT） | 剥离 Custom Section |
| **`twiggy`** | **体积诊断**：`twiggy top`（谁在吃体积）、`twiggy dominators`（谁把谁拖下水） |
| **`wasm-snip`** | 手动把指定函数替换成 `unreachable`，砍掉不需要的代码路径 |
| **`wasm-split`**（Binaryen） | 依剖析结果把模块切成 primary + secondary，延迟加载 |
| **`wizer`** | **建置时预初始化**：跑完初始化再把内存状态快照回新模块（附录 N §10-2） |
| **`wasmtime compile`** | 后端 AOT，产出 `.cwasm`，运行期零编译 |
| **`wabt` 的 `wasm-validate`** | 脱机验证模块是否合法 |

### 运行期（后端）

| 运行期 | 定位 |
|---|---|
| **Wasmtime** | Bytecode Alliance 主导，WASI 的参考实作；Cranelift 为代码产生后端 |
| **WasmEdge** | CNCF 沙盒项目，针对云原生、微服务与 AI 推理优化（支持 GPU 调用） |
| **Wasmer** | 强调可携与多语言嵌入；有 WAPM 套件生态 |
| **WAMR** (WebAssembly Micro Runtime) | 极轻量，适合 IoT 与嵌入式 |
| **Spin** (Fermyon) | 建构与运行 Wasm 微服务的框架，Serverless 形态 |
| **wasm3** | 极快的解译器（无 JIT），适合受限环境 |

### 浏览器端辅助

| 工具 | 用途 |
|---|---|
| **`coi-serviceworker`** | 在前端合成 COOP/COEP，让静态托管也能用 `SharedArrayBuffer`（第 5 章） |
| **`COEP: credentialless`** | 比 `require-corp` 温和的隔离模式：允许未表态的跨来源资源，但不带凭证请求 |
| **`'wasm-unsafe-eval'`** | CSP 关键字，只放行 Wasm 编译而不放行 `eval()`（Chrome 97+／FF 102+／Safari 16+） |
| **`wasm-split`** | Emscripten/Binaryen 的模块切割工具，主模块 + 延迟加载的次模块 |
| **C/C++ DevTools Support (DWARF)** | Chrome 扩充；让你在 DevTools 里看 C++ 原代码、下中断点、看变量 |
| **Chrome DevTools 的 Memory / Performance 面板** | 观察 Wasm 内存成长与编译耗时 |
| **`performance.measureUserAgentSpecificMemory()`** | 量测分页整体内存（含 Wasm） |
| **压缩字典传输**（RFC 9842） | 用用户缓存的旧版当字典压缩新版，`dcb`/`dcz` 编码；Chrome/Edge 130+（附录 N §7-2） |
| **`TextEncoder.encodeInto()`** | 直接把字符串编码写进 Wasm 内存，零中间配置（附录 N §13） |

---

## 四、关键编译旗标速查

```toml
# ── Rust: Cargo.toml（发布版）────────────────────────────
[profile.release]
opt-level = 3        # 速度优先；体积优先用 "z"，平衡用 "s"
lto = true           # 全局链接时优化（跨 crate 内联 + 死码消除）
codegen-units = 1    # 让 LTO 有完整视野
panic = "abort"      # 砍掉 unwinding 表（省体积、也省一层复杂度）
strip = true         # 剥离符号（name section）

[lib]
crate-type = ["cdylib"]
```

```bash
# ── Rust: 打开 SIMD ─────────────────────────────────────
RUSTFLAGS="-C target-feature=+simd128" wasm-pack build --target web --release

# ── Emscripten ──────────────────────────────────────────
emcc app.cpp -O3 \
  -msimd128 \                       # SIMD
  -pthread -s PTHREAD_POOL_SIZE=4 \ # 多线程（需跨来源隔离！）
  -s ALLOW_MEMORY_GROWTH=1 \        # 允许 memory.grow
  -s INITIAL_MEMORY=64MB \
  -s MAXIMUM_MEMORY=2GB \
  -s EXPORTED_FUNCTIONS='["_main","_process"]' \
  -s MODULARIZE=1 -s EXPORT_ES6=1 \ # 产出 ES module
  -flto --closure 1 \               # LTO + Closure 压缩胶水
  -o app.js

# ── 调试建置（保留符号与 DWARF）──────────────────────────
emcc app.cpp -g -gsource-map -s ASSERTIONS=2 -fsanitize=address -o app.js

# ── 后处理 ──────────────────────────────────────────────
wasm-opt -Oz --strip-debug --strip-producers app.wasm -o app.opt.wasm
twiggy top -n 20 app.opt.wasm
```

---

## 五、`--target` 选对了吗（`wasm-pack`）

| target | 产出 | 用在哪 |
|---|---|---|
| `web` | ES module，可直接 `<script type="module">` | **静态托管部署的正解** |
| `bundler` | 给 webpack/rollup/vite 的模块 | 有打包工具的项目 |
| `nodejs` | CommonJS | 服务器端 |
| `no-modules` | 挂在全域变量上的传统脚本 | 旧环境、Worker 里用 `importScripts` |

---

## 六、常见错误消息 → 病因对照

| 你看到 | 实际原因 |
|---|---|
| `404`（加载 `.wasm` 时） | ① `pkg/` 被 `.gitignore` 忽略 ② 用了绝对路径但站台在子路径 ③ Jekyll 吃掉了 `_` 开头的文件夹（放 `.nojekyll`） |
| `TypeError: WebAssembly.instantiateStreaming(): Incorrect response MIME type` | 服务器没回 `Content-Type: application/wasm` |
| `ReferenceError: SharedArrayBuffer is not defined` | 没有跨来源隔离（见第 5 章） |
| `RuntimeError: memory access out of bounds` | Wasm 内部的内存错误（用 ASan 建置去抓） |
| `TypeError: Cannot perform Construct on a detached ArrayBuffer` | `memory.grow` 后没有重新取得 `TypedArray` 视图 |
| `LinkError: import object field 'xxx' is not a Function` | `importObject` 缺了模块要求的 import |
| `RangeError: WebAssembly.Memory(): could not allocate memory` | 撞到浏览器的内存上限（见第 8 章） |
| 一切正常但结果是乱码 | 字符串编解码没对上（UTF-8 vs UTF-16），或指针传错 |
