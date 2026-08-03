# 附录N　体积与速度：Wasm 的压缩与加速全解

> 这是全书技术密度最高的一份附录。它回答两个问题：**「我的 `.wasm` 为什么这么大，怎么变小？」** 与 **「它为什么没有想像中快，怎么变快？」**
>
> **一条贯穿全篇的纪律**：**先量测，再优化，然后再量测一次。** 下面每一项技术都有它适用的形状；把它们无差别地全部套上去，通常会得到一个又慢又难维护的建置流程。

---

# 第一部：体积

## 一、先解剖：你的字节到底花在哪里

**在动任何旗标之前，先做这一步。** 没有这一步的优化都是猜测。

```bash
# 1. 区段层级的预算：哪个区段最肥
wasm-objdump -h app.wasm
#   Type       start=0x0000000b end=0x000001a4 (size=0x00000199) count: 52
#   Function   ...
#   Code       start=0x00012f4a end=0x0031b2c1 (size=0x00308377) ← 通常是这个
#   Data       start=0x0031b2c3 end=0x004a9f10 (size=0x0018ec4d) ← 但别忽略这个

# 2. 符号层级：谁在吃 Code 区段
twiggy top -n 30 app.wasm

# 3. 保留链：谁把谁拖下水（最有用的一个）
twiggy dominators app.wasm

# 4. 为什么某个函数还在？（回答「我明明没用到它」）
twiggy paths app.wasm -- 'core::fmt::write'
```

**四个区段的典型占比与对应武器**：

| 区段 | 典型占比 | 它是什么 | 对应武器 |
|---|---|---|---|
| **Code** | 50–80% | 所有函数本体 | 编译旗标、LTO、死码消除、`wasm-opt` |
| **Data** | 10–45% | 静态数据、字符串常数、查表 | **裁剪数据本身**（见 §6）、运行期解压 |
| **Custom (`name`/DWARF)** | 0–30% | 调试符号 | `--strip-debug`（发布版必做） |
| **Element / Table** | <5% | 函数表初始内容 | 减少间接调用的目标数量 |

> **第一个常见误判**：看到文件很大就冲去调 `opt-level`。**但如果你的 Data 区段占了 45%，把 Code 再压 10% 也只换来 5% 的总体积。** 先看 `wasm-objdump -h`。

---

## 二、编译期旗标：它们真正砍掉的是什么

### 2-1　Rust

```toml
[profile.release]
opt-level = "z"      # 体积优先（"s" 平衡、3 速度优先）
lto = "fat"          # 全程序优化：跨 crate 内联 + 全域死码消除
codegen-units = 1    # ★ 让 LTO 有完整视野；平行编译变慢，但产物显著更小
panic = "abort"      # 砍掉 unwinding 表与 landing pad
strip = true         # 剥离 name section
overflow-checks = false
debug = false
incremental = false  # 增量编译会妨碍跨单元优化
```

**每一项真正砍掉什么**：

| 旗标 | 砍掉什么 | 代价 |
|---|---|---|
| `opt-level = "z"` | 停用循环展开与**自动矢量化** | **⚠️ 这会关掉 SIMD 自动矢量化**——若你靠它，改用 `"s"` 或 `3` |
| `lto = "fat"` | 跨 crate 内联后的死码、重复的泛型实例 | 编译时间显著上升 |
| `codegen-units = 1` | 让 LTO 看到全部——**这一项单独就常有 5–15%** | 编译不能平行 |
| `panic = "abort"` | unwinding 表、landing pad、`Drop` 展开路径 | panic 不能被 catch（Wasm 上本来就少用） |
| `strip = true` | `name` 自订区段 | **失去可读的堆栈追踪**（见 §12 的取舍） |

### 2-2　Rust 最大的隐藏体积凶手：panic 的格式化机制

**这是绝大多数 Rust/Wasm 项目最没被发现的一块肥肉。**

一句 `panic!("index {} out of range", i)` 会把 **`core::fmt` 的整套格式化机制**拉进二进位——那是一台包含 trait 对象分派、宽度/精度处理、浮点数格式化的小型机器，**轻易占掉数十 KB 到上百 KB**。而更糟的是：**每一个 `unwrap()`、每一次数组索引、每一次整数溢出检查，都可能在失败路径上引用它。**

```bash
# 确认它是不是凶手
twiggy paths app.wasm -- 'core::fmt::write' | head -20
```

**根治手段（需要 nightly）**：

```bash
cargo +nightly build --release --target wasm32-unknown-unknown \
  -Z build-std=std,panic_abort \
  -Z build-std-features=panic_immediate_abort
```

`panic_immediate_abort` 让所有 panic 直接变成 `unreachable` 指令，**整套格式化机制与 panic 消息字符串全部消失**。对小型模块，这一招的效果常常超过其他所有旗标的总和。

**代价很诚实**：**panic 之后你什么消息都拿不到**，只有一个 `RuntimeError: unreachable`。**这是一个「发布版换体积、调试版保消息」的双建置决策，不是全域决策。**

**保守一点的做法**（不需要 nightly）：

```rust
// 避免带格式化的 panic
let v = arr.get(i).ok_or(MyError::OutOfRange)?;   // 而不是 arr[i]
// 避免 Display / format!
// 用静态字符串而不是 format!("...{}", x)
```

### 2-3　Rust 的第二个凶手：单型化爆炸

泛型在 Rust 里是**单型化（monomorphization）** 的——`Vec<u8>` 与 `Vec<u32>` 会生成两份完全独立的代码。一个被十种类型实例化的复杂泛型函数，就是十份。

```rust
// ❌ 整个函数本体被拷贝 N 份
pub fn process<P: AsRef<Path>>(path: P, data: &[u8]) { /* 两百行 */ }

// ✅ 外层薄壳负责转型，内层单一实例做重活
pub fn process<P: AsRef<Path>>(path: P, data: &[u8]) {
    process_inner(path.as_ref(), data)      // 薄壳，被拷贝也没关系
}
fn process_inner(path: &Path, data: &[u8]) { /* 两百行，只有一份 */ }
```

**这个「泛型薄壳 + 具体实作」的模式，是 Rust 生态里最有效的体积技巧之一**，而 `twiggy top` 会直接把重复的实例列出来让你看见。

### 2-4　C / C++

```bash
emcc app.cpp \
  -Oz \
  -flto \
  -fno-exceptions \                  # C++ 例外的展开表通常很大
  -fno-rtti \                        # typeid / dynamic_cast 的中继数据
  -ffunction-sections -fdata-sections \
  -Wl,--gc-sections \                # 未使用的 section 整段丢掉
  -sASSERTIONS=0 \                   # 移除运行期断言与消息字符串
  -sFILESYSTEM=0 \                   # ★ 不需要 MEMFS 就别打包整套文件系统
  -sENVIRONMENT=web \                # 移除 node/worker/shell 的分支
  -sMALLOC=emmalloc \                # 比 dlmalloc 小得多的配置器
  -sMINIMAL_RUNTIME=1 \              # 极简 JS 胶水（限制较多）
  --closure 1 \                      # 用 Closure Compiler 压 JS 胶水
  -sEXPORTED_FUNCTIONS='["_main","_process"]' \
  -o app.js
```

**几个特别值得注意的**：

- **`-sFILESYSTEM=0`**：如果你的代码没有真的调用 `fopen`，Emscripten 默认仍可能连进整套 MEMFS。**这一项常常直接省下数十 KB 的 JS 胶水。**
- **`-sMALLOC=emmalloc`**：`emmalloc` 远小于默认的 `dlmalloc`，代价是某些配置模式下较慢。**如果你的代码几乎不做动态配置（例如全部用 arena），这是纯赚。**
- **`--closure 1`**：注意它压的是 **JS 胶水**不是 `.wasm`。对 Emscripten 项目，胶水本身可能有数十 KB。

### 2-5　配置器的选择

| 配置器 | 体积 | 速度 | 备注 |
|---|---|---|---|
| Rust 默认（dlmalloc） | 中 | 好 | 大多数情况的正确选择 |
| `emmalloc`（Emscripten） | **小** | 中 | 配置模式简单时的好选择 |
| **自建 bump/arena** | **极小** | **极快** | **见 §11**——如果你的配置模式是「一批分配、一次全放」，这是双赢 |
| `wee_alloc` | 极小 | 差 | ⚠️ **已不再维护且有已知的内存回收问题，不建议新项目采用** |

---

## 三、`wasm-opt`：不只是一个 `-Oz`

**Binaryen 的 `wasm-opt` 是整条链上投报率最高的单一工具**，但多数人只会用一个旗标。

```bash
wasm-opt -Oz \
  --strip-debug --strip-producers --strip-target-features \
  --low-memory-unused \
  --zero-filled-memory \
  --converge \
  app.wasm -o app.opt.wasm
```

**它内部真正做的事**（`-Oz` 是一组 pass 的组合）：

| Pass 类别 | 代表 pass | 做什么 |
|---|---|---|
| 死码与清理 | `--dce`、`--vacuum`、`--remove-unused-module-elements` | 移除到不了的代码、没用到的导入/全域/函数 |
| 去重 | `--duplicate-function-elimination` | **合并二进位完全相同的函数**——单型化爆炸的解药之一 |
| 内联 | `--inlining-optimizing` | 把小函数展开，再对结果重新优化 |
| 指令层 | `--optimize-instructions` | 窥孔优化：`x*2` → `x<<1` 这一类 |
| 区域变量 | `--simplify-locals`、`--coalesce-locals`、`--reorder-locals` | 减少区域变量数量与索引大小（**LEB128 下小索引更省字节**） |
| 布局 | `--reorder-functions` | **依调用频率重排函数索引**，让热门函数拿到小索引 → LEB128 编码更短 |

**三个常被忽略的旗标**：

- **`--converge`**：反复运行优化直到不再变小。**通常再挤出 1–3%**，代价是编译时间翻倍。
- **`--low-memory-unused`**：告诉优化器「低地址那一段没被使用」，让它能对寻址做更激进的假设。**Emscripten 项目通常安全，手写内存布局的项目要小心。**
- **`--zero-filled-memory`**：声明内存初始为零，让优化器移除多余的清零代码。

> ⚠️ **顺序陷阱**：`wasm-opt` 必须在 **`wasm-bindgen` 之后**运行。`wasm-pack` 默认会做这件事，但如果你手动串工具链，**在 `wasm-bindgen` 之前先跑 `wasm-opt` 会让它砍掉 bindgen 还需要的东西**，症状是运行期出现莫名的 `LinkError`。

---

## 四、`no_std` 与砍掉标准库

**当你的模块是纯运算内核时**，整个 `std` 可能都是负担：

```rust
#![no_std]
extern crate alloc;                  // 只要堆积配置，不要 std 的其他部分

use alloc::vec::Vec;

#[panic_handler]
fn panic(_: &core::panic::PanicInfo) -> ! { core::arch::wasm32::unreachable() }
```

**收益**：省下 `std` 的运行期初始化、I/O 抽象、线程与同步原语、以及（最重要的）它拖进来的格式化机制。
**代价**：不能用 `String`（要用 `alloc::string::String`）、不能用 `std::collections::HashMap`（要换 `hashbrown`）、生态中一大半的 crate 不支持。

**判准**：**如果你的模块导出的是「喂字节进去、拿字节出来」的纯函数，`no_std` 几乎总是划算的。** 如果它需要文件、时间、随机数，那 `std` 带来的便利通常值那些字节。

---

## 五、消除跨语言的重复：`wasm-bindgen` 的体积成本

```rust
// ❌ 每一个 #[wasm_bindgen] 都会生成一份 JS 胶水与 Wasm 侧的 shim
#[wasm_bindgen]
pub fn process_pixel(r: u8, g: u8, b: u8) -> u32 { /* ... */ }

// ✅ 一个粗接口，内部自己循环
#[wasm_bindgen]
pub fn process_image(ptr: *mut u8, len: usize) { /* ... */ }
```

**这件事同时是体积优化与性能优化**（见 §13）——**细粒度的导出接口既胖又慢。**

**其他几个具体手段**：

- 回传 `Vec<u8>` 会经过 bindgen 的配置/释放样板；**回传 `(ptr, len)` 让 JS 自己读线性内存更省**。
- `js_sys` / `web_sys` **只开你用到的 feature**——它们的 feature 清单极长，全开会拉进大量绑定。
- `#[wasm_bindgen(js_name = "...")]` 不影响体积，但 `catch` / `getter` / `setter` 等属性会生成额外样板。

---

## 六、数据才是大宗：一般化 FluffOS 的那一课

**附录 L 记录了一个数字：FluffOS 的 Wasm 建置把 ICU 数据从约 30 MB 砍到约 780 KB（−97%），而整个驱动器的代码本体才 3.6 MB。**

**把它一般化成一条规则**：

> **大型 C/C++ 项目的 Wasm 产物里，往往有一半以上是它拖进来的数据表，而那些表通常有 90% 你用不到。**

**常见的数据肥肉与对应手术**：

| 数据 | 常见大小 | 手术 |
|---|---|---|
| ICU / Unicode 表 | 数 MB ~ 30 MB | 只保留需要的规则（断词/校对/转写各自可裁） |
| 字体 | 数 MB | 子集化（只留用到的字符） |
| 语言模型 / 训练数据 | 数十 MB | **不要打包进 `.wasm`**，改成运行期抓（可缓存） |
| 时区数据库 | 数百 KB | 只保留目标地区 |
| 内置测试数据 / 范例 | 常被忘记 | 用编译条件排除 |
| 查表（三角函数、CRC…） | KB ~ MB | **考虑运行期计算**——CPU 通常比内存便宜 |

**还有一招：把数据压缩后嵌入，运行期解压。**

```
把 2 MB 的数据表用 zstd 压成 400 KB 嵌进 Data 区段，
启动时用一个 15 KB 的解压器展开到线性内存。
→ 净省 1.6 MB 传输，代价是启动时多几毫秒。
⚠️ 但先确认：外层的 Brotli 传输压缩是不是已经帮你压过了？
   若是，这一招只是把压缩从传输层搬到了应用层，可能反而更差。
```

---

## 七、传输层：Brotli，以及一个会改变游戏规则的新东西

### 7-1　为什么 Wasm 特别适合 Brotli

**经验上 Wasm 的压缩率常在 3.5–5 倍**（附录 L 的实例是 3.6 MB → 0.8 MB，约 4.5 倍）。原因有三：

1. **LEB128 让小数字只占一个字节**，且分布高度集中 → 熵低。
2. **脚本的重复性极高**：`20 xx 20 yy 6A`（load/load/add）这种模式在整个模块里出现千万次。
3. **Data 区段常含大量零与重复字符串**。

```nginx
# 静态预压缩优于即时压缩（省 CPU、且能用最高等级）
brotli_static on;
# 产出：app.wasm + app.wasm.br（brotli -q 11）
```

### 7-2　★ 压缩字典传输（Compression Dictionary Transport）

**这是 Wasm 更新分发上这几年最重要的一项变化，而它几乎没有出现在 Wasm 的讨论里。**

**问题**：你的 `app.wasm` 有 8 MB（Brotli 后 1.8 MB）。你改了三行代码发新版——**用户要重新下载整整 1.8 MB**，即使 99% 的字节跟他缓存里的旧版一模一样。

**解法**：**用用户已经缓存的旧版本，当作压缩新版本的字典。**

```http
# 第一次回应：声明「这个文件可以当作未来的字典」
HTTP/2 200
Content-Type: application/wasm
Use-As-Dictionary: match="/app-*.wasm"

# 之后用户要新版时，浏览器自动带上：
Available-Dictionary: :pZGm1Av0IEBKARczz7exkNYsZb8LzaMrV7J32a2fFG4=:
Accept-Encoding: br, dcb, dcz

# 服务器用旧版当字典压缩新版：
HTTP/2 200
Content-Encoding: dcb        # Dictionary-Compressed Brotli（dcz = Zstandard 版）
→ 实际传输可能只有几十 KB
```

**状态**：**RFC 9842**；**Chrome 130+、Edge 130+ 支持，Firefox 进行中**。CDN 侧，**Cloudflare 于 2026 年 4 月推出边缘支持**（其实作本身就是用 Wasm 编译的 Zstandard）。

**它对 Wasm 的意义特别大**，因为 Wasm 应用有两个特征：**（一）** 单一大文件；**（二）** 改版时大部分字节不变。**这正是差分压缩效果最好的形状。**

> 💡 **一个推论**：一旦这条路普及，**「模块要不要切小」这个决策的权重会下降**——切小的主要动机之一（让更新只重下载一部分）被差分压缩取代了，而切小的代价（多次往返、跨模块调用）依然存在。

---

## 八、切割与延迟加载

| 手段 | 机制 | 适合 |
|---|---|---|
| **`wasm-split`**（Binaryen） | 依剖析结果把模块切成 primary + secondary，第一次调用到才抓 | 启动路径明确、大量功能用户可能永远不点 |
| **手动多模块 + 共用内存** | 把 `memory` 从一边 export、另一边 import | 功能边界清晰（如 PDF 导出、OCR 语言包） |
| **运行期抓资产** | 数据不进 `.wasm`，用 `fetch` + Cache API | 模型权重、字体、语言包 |

```javascript
// 手动切割：两个模块共用同一块线性内存，数据不必拷贝
const core = await WebAssembly.instantiateStreaming(fetch("core.wasm"), imports);
const pdf  = await WebAssembly.instantiateStreaming(fetch("pdf.wasm"), {
  env: { memory: core.instance.exports.memory },   // ★ 关键
});
```

---

## 九、体积优化投报率总表

| # | 手段 | 典型收益 | 成本 | 何时做 |
|---|---|---|---|---|
| 0 | **裁剪数据本身** | **可达 −90%** | 需要领域判断 | **最先做** |
| 1 | `wasm-opt -Oz --converge` | −15~40% | 建置时间 | 一定做 |
| 2 | `lto` + `codegen-units=1` | −5~15% | 编译时间 | 一定做 |
| 3 | **Brotli 传输** | **−70~80%（传输）** | 几乎为零 | **一定做** |
| 4 | `panic_immediate_abort`（Rust） | 小模块可 −30%+ | 失去 panic 消息 | 发布版 |
| 5 | `--strip-debug` | −0~30% | 失去堆栈追踪 | 发布版（保留一份带符号的） |
| 6 | 泛型薄壳、去除单型化重复 | −5~20% | 重构 | 有测到才做 |
| 7 | `no_std` | −10~30% | 生态受限 | 纯运算内核 |
| 8 | `-sFILESYSTEM=0` 等 Emscripten 旗标 | −数十 KB 胶水 | 功能受限 | 确认没用到 |
| 9 | 模块切割 | 首屏 −50%+ | 架构复杂度 | 启动路径明确时 |
| 10 | **压缩字典传输** | **更新时 −90%+** | 需 CDN/服务器支持 | 有频繁改版时 |

---

# 第二部：速度

## 十、启动路径的四段拆解

**「Wasm 很慢」的抱怨，八成是在讲启动而不是稳态。** 而启动是四段独立的成本，各有各的武器：

```
① 网络传输  ── 受压缩后体积与 RTT 支配 ──→ 第一部全部
② 编译      ── 与字节数线性相关      ──→ §10-1
③ 实例化    ── 配置内存、跑 Data 段初始化、运行 start ──→ §10-2
④ 运行期初始化 ── 全域建构子、语言 runtime 自举、数据结构创建 ──→ §10-3 ★最常被低估
```

### 10-1　编译阶段的四个武器

```javascript
// ① 串流编译：第一个字节到达就开工（服务器必须回 application/wasm）
const { instance } = await WebAssembly.instantiateStreaming(fetch("app.wasm"), imports);

// ② 编译一次，N 个 Worker 共用（WebAssembly.Module 可结构化拷贝）
const mod = await WebAssembly.compileStreaming(fetch("app.wasm"));
workers.forEach(w => w.postMessage({ mod }));      // ★ 省下 N−1 次完整编译

// ③ 磁盘代码缓存：给 .wasm 一个稳定 URL（内容哈希文件名最佳）
//    引擎会把优化后的机器码写进 HTTP 缓存，回访可跳过整个编译阶段
//    → 大型模块的第二次加载常快一个量级
```

**④ 分层编译是自动的，但你可以理解它**：Liftoff 先产出可运行码（快而烂），TurboFan 在背景产出好码再热替换。**这意味着「刚启动的前几百毫秒，你的 Wasm 跑的是未优化版本」**——如果你在启动后立刻做一次基准测试，量到的是 Liftoff 的数字，不是稳态性能。

### 10-2　★ Wizer：把「初始化」搬到建置时

**这是服务器端与 CLI 场景最被低估的一项技术。**

很多模块启动时要做大量一次性工作：解析设置、创建查表、加载数据结构、初始化解释器。**Wizer（Bytecode Alliance）的想法是：在建置时就把这些做完，然后把「初始化之后的内存状态」快照回一个新的 `.wasm`。**

```bash
# 建置时：实例化模块、运行初始化函数、把结果快照成新模块
wizer app.wasm -o app.initialized.wasm --allow-wasi
```

```rust
// 模块侧：标记哪个函数是「初始化」
#[export_name = "wizer.initialize"]
pub extern "C" fn init() {
    LOOKUP_TABLE.set(build_expensive_table());   // 这些在建置时就跑完了
}
```

**运行期拿到的模块，Data 区段里已经是初始化完成的内存映像**——启动时什么都不用做。官方基准宣称**实例化与初始化快 1.35 到 6.00 倍**，实际收益取决于你原本要做多少初始化工作。

**代价与限制**：**（一）** 快照会让 Data 区段变大（**体积换启动速度**，与第一部直接冲突，要量测取舍）；**（二）** 初始化过程中不能依赖运行期才有的东西（时间、随机数、网络）；**（三）** 主要用于服务器端/CLI，浏览器场景要衡量体积代价。

**同一个思路的其他形态**：

| 技术 | 场景 |
|---|---|
| **Wizer** | 通用预初始化快照 |
| `wasmtime compile` → `.cwasm` | **后端 AOT**：把编译完全移到部署前，运行期零编译 |
| 引擎的 pooling allocator | 预先配置好实例池，省下每次实例化的内存配置 |

### 10-3　那个最常被低估的第四段

**Pyodide 下载完 30 MB 之后，还要花时间自举 CPython。** Emscripten 项目要跑完所有 C++ 全域建构子。这些发生在**编译完成之后**，而且不会出现在「模块加载时间」这个指针里。

```javascript
// 分开量测，否则你会优化错地方
const t0 = performance.now();
const mod = await WebAssembly.compileStreaming(fetch("app.wasm"));
const t1 = performance.now();                       // ← 编译
const inst = await WebAssembly.instantiate(mod, imports);
const t2 = performance.now();                       // ← 实例化
inst.exports.app_init();
const t3 = performance.now();                       // ← 运行期初始化 ★
console.log(`编译 ${(t1-t0)|0}ms / 实例化 ${(t2-t1)|0}ms / 初始化 ${(t3-t2)|0}ms`);
```

---

## 十一、稳态性能之一：让编译器产出更好的码

### 11-1　SIMD：开了不等于用了

```bash
# Rust
RUSTFLAGS="-C target-feature=+simd128" cargo build --release --target wasm32-unknown-unknown
# Emscripten
emcc -msimd128 -O3 ...
```

**三个必须知道的现实**：

1. **`opt-level = "z"` 会关掉自动矢量化。** 你不能同时要最小体积与自动 SIMD——**这是一个必须做的选择。**
2. **自动矢量化很挑剔**：循环边界要在编译期可知或可推断、不能有数据相依、不能有指针别名疑虑。**没被矢量化时编译器不会警告你**，只能看反汇编或量测。
3. **手写 intrinsics 是保底手段**：

```rust
use core::arch::wasm32::*;

pub fn add_f32x4(a: &[f32], b: &[f32], out: &mut [f32]) {
    for i in (0..a.len()).step_by(4) {
        unsafe {
            let va = v128_load(a.as_ptr().add(i) as *const v128);
            let vb = v128_load(b.as_ptr().add(i) as *const v128);
            v128_store(out.as_mut_ptr().add(i) as *mut v128, f32x4_add(va, vb));
        }
    }
}
```

**别忘了第 3 章的天花板**：**Wasm SIMD 固定 128 比特**，为 AVX2（256）手写优化的代码移植过来，矢量宽度直接砍半。**典型加速比是 2–4 倍，不是 8–16 倍。**

### 11-2　Bulk memory：一个常被忽略的巨大免费午餐

```c
// ❌ 逐字节循环：每个字节一条 load + 一条 store
for (size_t i = 0; i < n; i++) dst[i] = src[i];

// ✅ 编译成 memory.copy 单一指令 → 引擎映射到宿主的 memcpy（SIMD 化、对齐优化过）
memcpy(dst, src, n);
```

**`memory.copy` / `memory.fill` 是 Wasm 2.0 起的内核指令**，引擎会把它们直接映射到高度优化的原生 `memcpy`/`memset`。**大区块搬移的差距可以是一个量级。** 确认你的工具链开了 bulk memory（现代工具链默认打开）。

### 11-3　其他 codegen 层面的杠杆

| 特性 | 收益 | 备注 |
|---|---|---|
| **分支提示**（Wasm 3.0） | 让引擎把热路径排在 fall-through | 由 PGO 或 `likely()` 标注驱动 |
| **尾调用** `return_call` | 深递归不爆栈，且省下堆栈框 | 解释器、状态机受益最大 |
| **Multi-value** | 多回传值不必经过内存 | 减少 load/store 往返 |
| **Relaxed SIMD** 的 `relaxed_madd` | 映射到硬件 FMA | ⚠️ **牺牲确定性**（附录 M §7） |
| **具类型函数参考**（Wasm 3.0） | 间接调用省下运行期签章检查 | 虚拟函数密集的 C++/OOP 受益 |

---

## 十二、稳态性能之二：内存与缓存

**第 6 章说过那个关键事实：L1 命中约 4 个周期，DRAM 访问约 200 个周期。** 所以内存布局的影响常常压过指令层面的优化。

### 12-1　SoA 而不是 AoS

```rust
// ❌ AoS：算 x 的平均值也要把 y、z 拖进缓存
struct Particle { x: f32, y: f32, z: f32, vx: f32, vy: f32, vz: f32 }
let particles: Vec<Particle>;

// ✅ SoA：只扫 xs，完美的缓存局部性，也是自动矢量化的前提
struct Particles { xs: Vec<f32>, ys: Vec<f32>, zs: Vec<f32>, /* ... */ }
```

### 12-2　Arena / bump 配置器

**在 Wasm 里 `malloc` 相对昂贵**（它是编译进来的一份用户空间实作，没有操作系统帮忙）。**如果你的配置模式是「处理一帧 / 一个请求时分配一堆，结束后全部丢掉」，bump 配置器是压倒性的赢家**：

```rust
struct Bump { buf: Vec<u8>, top: usize }
impl Bump {
    #[inline] fn alloc(&mut self, n: usize, align: usize) -> *mut u8 {
        let p = (self.top + align - 1) & !(align - 1);
        self.top = p + n;                       // 分配 = 一次加法
        unsafe { self.buf.as_mut_ptr().add(p) }
    }
    #[inline] fn reset(&mut self) { self.top = 0; }   // 释放全部 = 一次赋值
}
```

**它同时是体积优化**（可以搭配 `-sMALLOC=none` 或极小配置器）**与性能优化**。

### 12-3　三个具体陷阱

| 陷阱 | 说明 |
|---|---|
| **热路径上的 `memory.grow`** | 会使所有既有 `TypedArray` 视图失效，且可能触发一次大的内存重新映射。**预先配置好上限，别让它在循环里长。** |
| **对齐提示** | `i32.load align=2` 是**提示**不是保证——声明错不会 trap，但引擎可能因此产出较慢的码。**让编译器自己填。** |
| **跨页的随机访问** | 线性内存很大时，随机访问会频繁 TLB 未命中。**能排序就排序，能分块就分块。** |

---

## 十三、稳态性能之三：边界

**第 2 章说「边界是收费站」，这里给实际的减费手段。**

```javascript
// ❌ 每次都配置一个新的 Uint8Array 来编码字符串
const bytes = new TextEncoder().encode(str);
const ptr = wasm.alloc(bytes.length);
new Uint8Array(wasm.memory.buffer, ptr, bytes.length).set(bytes);

// ✅ encodeInto 直接写进 Wasm 内存，零中间配置
const view = new Uint8Array(wasm.memory.buffer, ptr, cap);
const { written } = new TextEncoder().encodeInto(str, view);
```

**五条规则**：

1. **批量化**：`process_image(ptr, w, h)` 而不是 `process_pixel()` 一百万次。
2. **`encodeInto` / `decode` 重用视图**，避免每次配置。
3. **结果用环形缓冲回传**，而不是每次事件一个回呼（物理引擎、游戏循环的标准做法）。
4. **`externref` 持有 JS 对象**，避免自建「JS 对象 ↔ 整数 handle」的侧表（那张表的维护成本与泄漏风险都不低）。
5. **量测跨界次数本身**：在胶水里加一个计数器，你会经常发现它比你以为的多一个量级。

---

## 十四、稳态性能之四：并行

```javascript
// Worker pool + SharedArrayBuffer（需跨来源隔离，见第 5 章）
const mem = new WebAssembly.Memory({ initial: 256, maximum: 4096, shared: true });
// 每个 Worker 用同一个 Module + 同一块 shared memory 实例化
```

**三个实务要点**：

1. **Worker 数量用 `navigator.hardwareConcurrency`，但要留余裕**（主线程还要渲染）。实务上常用 `max(1, hc - 1)`。
2. **主线程不能 `Atomics.wait`**（规范禁止），要用 **`Atomics.waitAsync`**。
3. **工作切分的粒度**要大到盖过同步成本——**太细的并行比单线程还慢**，这在 Wasm 上比在原生上更明显，因为跨 Worker 的协调要经过 JS。

**如果数据可切分，回头看第 8 章情境 3**：**多实例隔离不需要跨来源隔离**，往往是更划算的并行路径。

---

## 十五、量测：一个会让你量错的陷阱

**⚠️ 没有跨来源隔离时，`performance.now()` 的分辨率会被降低。**

这是 Spectre 余波的另一个后果（第 3 章）：**未隔离的页面上，计时器分辨率被粗化**（各家实作不同，常见量级是数十到上百微秒），**而隔离之后才会恢复到微秒级**。

**这意味着**：

- 量测微秒级的操作（单次跨界调用、小函数）**在未隔离的页面上根本量不准**。
- **不要用单次 `performance.now()` 差值去量小操作**——跑一万次取总时间再除。
- 比较两份建置时，**确认两边的隔离状态相同**，否则你比较的是计时器精度而不是代码。

```javascript
// 正确的微基准形状
function bench(fn, iters = 100_000) {
  fn(); fn(); fn();                       // 预热（让 TurboFan 完成 tier-up）
  const t0 = performance.now();
  for (let i = 0; i < iters; i++) fn();
  return (performance.now() - t0) / iters; // 平均单次
}
```

**剖析工作流**（附录 M §10 已述，这里补三条）：

- **保留 `name` 区段**，否则火焰图只有 `wasm-function[1234]`（`wasm-opt --strip-debug` 保留 name、只剥 DWARF）。
- **后端用 `perf`**：Wasmtime 支持输出 perf/jitdump 对应信息，可以看到 Wasm 函数名。
- **量「跨界次数」与「配置次数」**，不要只量时间——它们才是可以直接行动的指针。

---

## 十六、性能优化投报率总表

| # | 手段 | 典型收益 | 何时做 |
|---|---|---|---|
| 0 | **确认瓶颈是启动还是稳态** | — | **最先做**（两者的武器完全不同） |
| 1 | `instantiateStreaming` + 正确 MIME | 省一整趟下载时间 | 一定做 |
| 2 | **降低体积**（第一部） | 直接缩短 ①② 段 | 一定做 |
| 3 | 稳定 URL → 代码缓存 | 回访快一个量级 | 一定做 |
| 4 | **把边界做粗** | 常见 2–10 倍 | **测到跨界密集就做** |
| 5 | Module 结构化拷贝给 N 个 Worker | 省 N−1 次编译 | 用多 Worker 时 |
| 6 | SoA + arena 配置器 | 常见 2–5 倍 | 数据密集时 |
| 7 | `memcpy` 取代逐字节循环 | 大区块可达一个量级 | 一定检查 |
| 8 | SIMD（`-msimd128` + 手写 intrinsics） | 2–4 倍 | 数值密集时 |
| 9 | **Wizer 预初始化** | 实例化+初始化 1.35–6 倍 | 初始化重的后端/CLI |
| 10 | 后端 AOT（`wasmtime compile`） | 运行期零编译 | 服务器端 |
| 11 | 多线程 | ≤ 内核数 | **最后才做**（复杂度与隔离代价最高） |

---

## 十七、反模式清单

| 反模式 | 为什么错 |
|---|---|
| 没量测就开始调旗标 | 八成调错地方（Data 区段占一半时，压 Code 没用） |
| 同时要 `opt-level="z"` 与 SIMD 自动矢量化 | **`-Oz` 关掉矢量化**，两者互斥 |
| 把 Wasm 当「更快的函数库」逐函数替换 JS | 每个函数变快，整体变慢——**跨界次数暴增** |
| 在热循环里调用 JS | 每次都是收费站；把循环整个搬进 Wasm |
| 用 `wee_alloc` 图体积 | **已不再维护且有已知问题** |
| 在未隔离的页面上量微秒级操作 | **计时器被降精度**，你量的是杂讯 |
| 启动后立刻跑基准测试 | 量到的是 Liftoff 的未优化码 |
| 把 30 MB 模型权重打包进 `.wasm` | 它应该是可缓存的资产，不是代码 |
| 为了更新体积而过度切割模块 | **压缩字典传输**（§7-2）可能已经解决了这个问题，而切割的代价还在 |
| 发布版无脑 `strip` 掉全部符号 | 在线崩溃时你什么都查不到——**保留一份带符号的建置** |

---

## 附：与正文的对照索引

| 主题 | 本附录 | 正文背景 |
|---|---|---|
| 体积的解剖与工具 | §1 | 第 3 章墙三、第 8 章 |
| Rust 的隐藏肥肉 | §2-2、§2-3 | 第 3 章墙九 |
| `wasm-opt` 内部 | §3 | 第 8 章 |
| 数据才是大宗 | §6 | 第 8 章第 0 条、附录 L |
| Brotli 与差分更新 | §7 | 第 2 章、附录 M §9 |
| 启动四段 | §10 | 第 2 章情境 3 |
| Wizer | §10-2 | 第 2 章、附录 M |
| SIMD 的真实天花板 | §11-1 | 第 2 章 🔍、第 4 章 |
| 边界减费 | §13 | 第 2 章情境 4 |
| 计时器精度陷阱 | §15 | 第 3 章墙六、第 5 章 |
| 把体积与性能写进 CI 守门 | — | **附录 O §5** |
