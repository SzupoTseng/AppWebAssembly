# 附录A　Wasm 大事年表与规范速查

> 本附录的定位是「查得到、可核对」。**年表与规范状态请以 WebAssembly 官方规范（webassembly.github.io/spec）、提案清单（github.com/WebAssembly/proposals）与 MDN 为最终依据**——本书写于 2026 年，而提案状态是会移动的。

---

## 一、大事年表

| 时间 | 事件 | 意义 |
|---|---|---|
| 2011–2013 | **Google NaCl / PNaCl** | 静态验证 x86 机器码 + 分段沙盒；后改分发 LLVM bitcode。技术成功、政治失败（仅 Chrome 支持） |
| 2013 | **Mozilla asm.js** | JavaScript 的严格子集，用 `x\|0` / `+x` 标注类型。**证明了不用插件就能拿到接近原生的性能，且四家引擎都能实作** |
| 2013 起 | **Emscripten 成熟** | LLVM → asm.js（后 → Wasm）的 C/C++ 编译管线，Unreal Engine 等大型项目得以搬上浏览器 |
| **2015-06** | **四方共同宣布 WebAssembly** | Google、Mozilla、Microsoft、Apple。谈成的关键是「刻意做小」 |
| 2017-03 起 | **四大浏览器内置 Wasm MVP** | Chrome、Firefox、Safari、Edge。MVP 成为共同能力 |
| 2019 起 | **WASI 提案面世** | Wasm 脱离浏览器，进军服务器端、云原生、边缘运算 |
| 2019 | Docker 创办人 Solomon Hykes 的推文 | 「如果 2008 年就有 WASM+WASI，我们根本不需要发明 Docker」（常被断章取义，见第 1 章 ⚠️） |
| **2019-12** | **W3C 正式定为推荐标准（Recommendation）** | WebAssembly Core Specification 1.0。与 HTML、CSS、JavaScript 并列为 Web 的第四种内核语言 |
| 2020 前后 | Bytecode Alliance 成立、Wasmtime / Lucet / WAMR 等运行期成形 | 后端生态的基础设施 |
| 2020–2021 | SIMD、bulk memory、reference types、multi-value 等提案陆续落地 | MVP 欠下的技术债开始偿还 |
| 2021 起 | WasmEdge 进入 CNCF 沙盒；Fermyon Spin 等框架出现 | 云原生正式接受 Wasm |
| 2022 前后 | **Wasm 2.0**（含 SIMD、bulk memory、reference types、multi-value 等） | 内核规范的第二个里程碑 |
| 2023–2024 | **Component Model / WIT 成形；WASI 0.2 (Preview 2) 发布** | 从「单体模块」走向「可组合组件」 |
| 2025-04 | **JSPI（JavaScript Promise Integration）进入 Phase 4** | 同步的 Wasm 代码终于能调用异步的 Web API |
| **2025-09** | **★ WebAssembly 3.0 宣布完成，成为现行标准** | **MVP 那笔技术债，到这里基本上还完了**（见下表） |
| 2025 起 | JSPI 于 **Chrome 137、Firefox 139** 出货 | 见附录 M 第五节 |
| 持续进行 | Component Model、stack switching、JS String Builtins、custom page sizes、shared-everything threads… | 见下方提案速查 |

> ⚠️ **本书修订说明**：Wasm 3.0 是一次分水岭。**在它之前，GC／memory64／尾调用／例外处理／multiple memories 都是「提案」；在它之后，它们是内核规范的一部分。** 如果你读到任何把这些东西称为「提案」「实验性」的数据（**包括本书初稿**），请以此为准——那些叙述写于 3.0 之前。

---

## 二、二进位格式速查

**文件开头永远是 8 个字节**：`00 61 73 6D`（`\0asm` 魔数）+ `01 00 00 00`（版本 1）。

**区段（section）顺序是规范强制的**，这正是单趟线性验证与串流编译的前提：

| ID | 名称 | 内容 | 能否剥离 |
|---|---|---|---|
| 0 | Custom | `name`（函数/变量名）、DWARF 调试信息、Source Map 链接、语言中继数据 | **✅ 可（`strip`）** |
| 13 | Tag | 例外标签（Wasm 3.0 的例外处理） | ❌ |
| 1 | Type | 所有函数签章 | ❌ |
| 2 | Import | 从宿主要进来的函数/内存/表/全域 | ❌ |
| 3 | Function | 函数 → 签章的对应 | ❌ |
| 4 | Table | 函数参考表（间接调用目标） | ❌ |
| 5 | Memory | 线性内存的初始页数与上限 | ❌ |
| 6 | Global | 全域变量 | ❌ |
| 7 | Export | **对外曝露的一切（攻击者永远看得到）** | ❌ |
| 8 | Start | 实例化后自动运行的函数 | ❌ |
| 9 | Element | 表的初始内容 | ❌ |
| 10 | Code | 每个函数的指令与区域变量 | ❌ |
| 11 | Data | **线性内存的初始数据（明文本串就在这里）** | ❌ |
| 12 | DataCount | 数据段数量（bulk memory 提案引入） | ❌ |

**内核类型**：

| 类别 | 类型 |
|---|---|
| 数值 | `i32`、`i64`、`f32`、`f64` |
| 矢量（SIMD 提案） | `v128` |
| 参考（reference types 提案） | `funcref`、`externref` |
| 堆积类型（GC，Wasm 3.0） | `struct`、`array`、`i31`、以及类型化参考 `(ref $T)` |

**内存单位**：**1 页 = 64 KiB**。`memory.grow` 只能增长，没有 `shrink`。

---

## 三、规范状态速查（依对工程决策的影响排序）

### 3-1　已进入内核规范（Wasm 1.0 / 2.0 / **3.0**）

> **这些不再是「提案」，它们就是 Wasm。** 剩下的问题只有「你的目标运行期跟上了没有」。

| 特性 | 进入版本 | 解决什么 | 对你的意义 |
|---|---|---|---|
| **Bulk memory** | 2.0 | `memory.copy` / `memory.fill` 等批量操作 | 大幅加速 `memcpy` 类操作 |
| **Reference types** | 2.0 | `externref` 持有不透明的宿主参考 | 缩小 JS↔Wasm 的桥接成本 |
| **Multi-value** | 2.0 | 函数可回传多个值 | 减少为了回传而配置内存的样板 |
| **SIMD (`v128`)** | 2.0 / 3.0 确立 | 一条指令处理多笔数据 | 2–4 倍加速。**注意只有 128 比特宽，远窄于 AVX2/AVX-512** |
| **Threads / Atomics** | — | 共享线性内存 + 原子操作 | **依赖 `SharedArrayBuffer`，需跨来源隔离**（第 5 章的头号障碍） |
| **★ GC** | **3.0** | `struct`/`array`/`i31` + 宿主 GC | **Kotlin/Dart/Java 的体积结构性下降。对 Rust/C/C++ 几乎无用** |
| **★ Memory64** | **3.0** | `i64` 寻址（内存与表） | 突破 4GiB，**但失去保护页的免费界检查，有性能代价**（第 8 章） |
| **★ Multiple memories** | **3.0** | 一个模块可声明多块线性内存，并直接在其间搬数据 | **第 8 章的第三条破圈路径**：在 wasm32 下把数据分到多块 4GiB 内存里 |
| **★ Exception handling** | **3.0** | 例外标签（Tag section）与 payload | C++ 例外不必再靠 JS 蹦床，跨界开销大降（附录 M 第四节） |
| **★ Tail call (`return_call`)** | **3.0** | 尾调用优化 | **函数式语言的深层递归不再爆栈**（附录 F 案例 92 的关键） |
| **★ Typed function references** | **3.0** | `(ref $sig)` 具类型的函数参考 | 间接调用可省下运行期签章检查（附录 M 第三节） |
| **★ Extended const expressions** | **3.0** | 初始化式可做算术 | 减少为了初始化而跑 start 函数 |
| **★ Branch hinting** | **3.0** | 分支几率提示 | 帮助引擎产出更好的机器码 |
| **★ Relaxed SIMD** | **3.0** | 放宽部分 SIMD 语意以更好映射硬件 | 换取性能，**代价是结果可能因平台而异**——链上与任何需要确定性的场景必须禁用 |

### 3-2　内核规范之外、但已可用

| 特性 | 状态 | 意义 |
|---|---|---|
| **JSPI（JS Promise Integration）** | **Phase 4（2025-04 标准化）**；Chrome 137、Firefox 139 出货 | **同步的 Wasm 代码可以调用异步的 Web API**——把 Wasm「不能阻塞」这道墙打开了一个口（附录 M 第五节） |
| **Component Model / WIT** | 演进中 | WASI 0.2 的基础；试图从根本解决「边界收费站」 |
| **JS String Builtins** | 演进中 | 让 Wasm 直接操作 JS 字符串，减少编解码税 |
| **Stack switching** | 演进中 | 协程的原生支持（JSPI 是它的一个特例应用） |
| **Custom page sizes** | 演进中 | 让嵌入式场景不必被 64KiB 的页大小绑死 |

> **提案分五阶段**：Phase 0（前期构想）→ 1（提案）→ 2（规格草案）→ 3（实作草案）→ 4（标准化）。**状态随时间变动，请以官方 proposals 仓库与 `webassembly.github.io/spec` 上标注的版本日期为准。**

---

## 四、WASI 两个世代的对照

| | `wasi_snapshot_preview1` | **WASI 0.2 (Preview 2)** |
|---|---|---|
| 模型 | POSIX 风格的文件描述符 | **Component Model + WIT 接口定义** |
| 接口形态 | 一大包扁平的函数 | 拆成 `wasi:io`、`wasi:filesystem`、`wasi:sockets`、`wasi:http`、`wasi:clocks`、`wasi:random` 等 |
| Rust target | `wasm32-wasip1` | `wasm32-wasip2` |
| 生态成熟度 | **高**（TinyGo、多数工具链都支持） | 演进中，工具链逐步跟上 |
| 可组合性 | 差（单体） | **好**（可以只给某组件 `wasi:clocks`，不给文件系统） |

**能力式安全的内核语法**：

```bash
# 只授权 ./my_storage 这一个目录，映射为模块眼中的 /sandbox
wasmtime run --dir=./my_storage::/sandbox my_server.wasm
# 环境变量也要显式授予
wasmtime run --env API_MODE=prod app.wasm
# 网络（0.2）
wasmtime serve --wasi inherit-network app.wasm
```

---

## 五、浏览器 API 速查

```javascript
// ── 加载（★ 首选：边下载边编译）───────────────────────────
const { instance, module } = await WebAssembly.instantiateStreaming(
  fetch("app.wasm"),            // 服务器必须回传 Content-Type: application/wasm
  importObject                  // 递给模块的能力
);

// ── 只编译不实例化（可缓存 module 给多个 Worker 用）────────
const mod = await WebAssembly.compileStreaming(fetch("app.wasm"));
const inst = await WebAssembly.instantiate(mod, importObject);

// ── 内存 ───────────────────────────────────────────────
const mem = new WebAssembly.Memory({ initial: 16, maximum: 256, shared: false });
//                                    ↑ 页数（每页 64KiB）      ↑ 多线程需要 shared:true
new Uint8Array(mem.buffer);      // ★ grow 之后必须重新取得视图

// ── 表（间接调用目标）─────────────────────────────────────
const tbl = new WebAssembly.Table({ initial: 2, element: "anyfunc" });

// ── 错误类型 ─────────────────────────────────────────────
WebAssembly.CompileError    // 二进位格式错误或验证失败
WebAssembly.LinkError       // import 对不上
WebAssembly.RuntimeError    // 运行期 trap（越界、除以零、unreachable）

// ── 跨来源隔离侦测 ────────────────────────────────────────
if (self.crossOriginIsolated) { /* SharedArrayBuffer 可用 */ }
```

---

## 六、常见 trap 与它们的来源

| Trap 消息 | 原因 |
|---|---|
| `memory access out of bounds` | 读写超出当前线性内存大小 |
| `integer divide by zero` | `i32.div_s` / `i32.rem_s` 等除以零 |
| `integer overflow` | `i32.div_s(INT_MIN, -1)` 这类溢出 |
| `invalid conversion to integer` | `f64` → `i32` 转换时值为 NaN 或超界（非饱和版本） |
| `unreachable` | 运行到 `unreachable` 指令（多半是 Rust 的 `panic!` 或 C++ 的 `abort()`） |
| `indirect call type mismatch` | 间接调用时实际函数签章与声明不符 |
| `call stack exhausted` | 递归过深（**`return_call` 尾调用就是为了这个**，Wasm 3.0） |
| `null function or function signature mismatch` | 函数表项目为空或签章不符 |

---

## 七、参考资源

| 主题 | 位置 |
|---|---|
| 内核规范 | `webassembly.github.io/spec/core/` |
| 提案清单与阶段 | `github.com/WebAssembly/proposals` |
| MDN WebAssembly 指南 | `developer.mozilla.org/docs/WebAssembly` |
| Emscripten 文档 | `emscripten.org/docs` |
| Rust and WebAssembly Book | `rustwasm.github.io/docs/book/` |
| `wasm-bindgen` 指南 | `rustwasm.github.io/wasm-bindgen/` |
| WABT（二进位工具集） | `github.com/WebAssembly/wabt` |
| Binaryen（`wasm-opt`） | `github.com/WebAssembly/binaryen` |
| Bytecode Alliance / Wasmtime | `bytecodealliance.org` |
| WASI 与 WIT | `wasi.dev` · `component-model.bytecodealliance.org` |
