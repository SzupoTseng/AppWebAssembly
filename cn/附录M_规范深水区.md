# 附录M　规范深水区：十二个常被跳过的技术细节

> 正文为了叙事流畅，很多地方只讲到「它是这样运作的」就停住了。这一份附录把那些停住的地方继续往下挖。
> **它不是入门材料，是查阅材料**——当你在实作中撞到某个具体问题时再翻进来。
>
> ⚠️ **版本前提**：本附录以 **WebAssembly 3.0**（2025 年 9 月宣布完成）为基准。**在 3.0 之前写成的数据会把 GC、Memory64、例外处理、尾调用、多重内存称为「提案」——那些叙述已经过时。**

---

## 一、把一个 `.wasm` 逐字节拆开

### 1-1　LEB128：为什么所有长度都是变长的

Wasm 的所有整数字段（区段长度、索引、常数）都用 **LEB128（Little Endian Base 128）** 编码——每个字节用低 7 位存数据、最高位当「还有后续」的续行旗标。

```
无号 LEB128：
  值 624485 (0x98765)
  → 二进位 1001 1000 0111 0110 0101
  → 每 7 位一组（由低到高）：1100101  1110110  0100110
  → 加续行位：11100101  11110110  00100110
  → 字节   E5        F6        26

小的数字只占 1 个字节（0–127），这正是重点：
  绝大多数索引与长度都很小，变长编码让整个模块显著缩小。
```

**有号版本（sLEB128）** 用于 `i32.const` / `i64.const` 这类常数，最后一组要做符号扩展。

> **实务意义**：这解释了两件事——**（一）** 为什么 Wasm 二进位比同等的定长格式小得多；**（二）** 为什么你**不能**用固定偏移量去 patch 一个 `.wasm`——改一个数字可能让它的字节数变了，后面全部要重算。**想改二进位，用 Binaryen 或 WABT，别自己动手。**

### 1-2　区段的通用结构

```
┌────────┬──────────────┬──────────────────────────┐
│ id (1) │ size (u32 LEB)│ contents (size 个字节)  │
└────────┴──────────────┴──────────────────────────┘
```

**`size` 存在的价值**：解析器可以**跳过**任何它不认识的区段（特别是 Custom Section）。这是 Wasm 向前兼容的基石——一个旧引擎遇到新版工具链塞进去的自订中继数据，只要跳过去就好。

### 1-3　类型编码

| 值类型 | 字节 |
|---|---|
| `i32` | `0x7F` |
| `i64` | `0x7E` |
| `f32` | `0x7D` |
| `f64` | `0x7C` |
| `v128` | `0x7B` |
| `funcref` | `0x70` |
| `externref` | `0x6F` |
| 函数类型（functype）前缀 | `0x60` |

**注意这些都是负数的 sLEB128 编码**（`0x7F` = −1、`0x7E` = −2……）。这不是巧合：**正数留给了「类型索引」**，于是 GC 要引入 `(ref $MyStruct)` 这种指向用户定义类型的参考时，编码空间早就预留好了。**2015 年那个「刻意做小」的规格，在类型编码上留了门。**

### 1-4　完整走一遍：一个 `add` 函数

```wat
(module
  (func $add (param i32 i32) (result i32)
    local.get 0
    local.get 1
    i32.add)
  (export "add" (func $add)))
```

```
00 61 73 6D            魔数 \0asm
01 00 00 00            版本 1

01 07                  Type 区段 (id=1)，长度 7
   01                    1 个类型
   60                    functype
   02 7F 7F              2 个参数：i32, i32
   01 7F                 1 个结果：i32

03 02                  Function 区段 (id=3)，长度 2
   01 00                 1 个函数，用类型 #0

07 07                  Export 区段 (id=7)，长度 7
   01                    1 个导出
   03 61 64 64           名称长度 3："add"
   00 00                 kind=func(0x00)，索引 0

0A 09                  Code 区段 (id=10)，长度 9
   01                    1 个函数本体
   07                    本体长度 7
   00                    ★ 区域变量声明：0 组
   20 00                 local.get 0
   20 01                 local.get 1
   6A                    i32.add
   0B                    ★ end（每个函数本体都以 0x0B 结尾）
```

> **正文第 2 章说「五个字节」指的是 `20 00 20 01 6A` 这段指令串行。** 完整的函数本体还要加上前面的区域变量声明 `00` 与结尾的 `0B`——**这两个字节是规范强制的，任何手工组装二进位的人第一次都会漏掉 `0x0B`。**

### 1-5　常用脚本速查

| 指令 | 码 | 指令 | 码 |
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

**SIMD 与部分新指令使用前缀码**（`0xFD` 为 SIMD 前缀、`0xFC` 为 bulk memory/saturating 转换前缀），后接一个 LEB128 的子脚本。

---

## 二、验证算法：多态堆栈与那个很聪明的技巧

第 2 章说验证器会做「堆栈类型一致性」检查。**但有一个情况会让天真的实作卡住**：

```wat
(func (result i32)
  unreachable       ;; 到这里控制流就终止了
  i32.add)          ;; ← 堆栈上什么都没有，但这行怎么验证？
```

`unreachable` 之后的代码**永远不会运行**，可是验证器仍然必须对它做出判断（因为它必须是单趟、线性、不做可达性分析的）。

**规范的解法是「多态堆栈（polymorphic stack）」**：进入 unreachable 状态后，验证器把堆栈标记为「**可以提供任意数量、任意类型的值**」。于是 `i32.add` 要两个 `i32`，多态堆栈就给它两个 `i32`；下一个指令要三个 `f64`，也照给。**这样任何在死代码里的指令串行都能通过验证，而不需要编译器去证明它不可达。**

```
验证状态机（简化）：
  正常状态  ── unreachable / br / return / br_table ──▶ 多态状态
  多态状态  ── 遇到 end 或该区块的边界 ─────────────▶ 恢复为该区块的声明类型
```

> 💡 **这是「让验证保持在 O(n) 单趟」这个设计目标的直接产物。** 如果验证器必须先做可达性分析才能检查类型，它就不再是单趟的了，而串流编译（边下载边编译）也就不成立。**一个看起来像特例的规则，往往是为了保住某个更根本的性质。**

---

## 三、`call_indirect`、表，与 C++ 虚拟函数在 Wasm 里的样子

### 3-1　函数指针是怎么实作的

Wasm **没有函数指针**——你不能把一个函数的地址存进线性内存。取而代之的是**表（Table）**：

```wat
(module
  (type $binop (func (param i32 i32) (result i32)))
  (table 4 funcref)                      ;; 一张有 4 格的函数表
  (elem (i32.const 0) $add $sub $mul $div)  ;; 填入四个函数

  (func $apply (param $op i32) (param $a i32) (param $b i32) (result i32)
    local.get $a
    local.get $b
    local.get $op
    call_indirect (type $binop)))        ;; ★ 依索引调用，并检查签章
```

**在 C/C++ 编译出来的 Wasm 里，「函数指针」其实是一个 `i32` 表索引。** 这解释了一个常见的困惑：**为什么 Wasm 里的函数指针可以安全地存在线性内存里？** 因为它只是一个索引——就算被缓冲区溢出改成任意值，最坏的结果也只是 `call_indirect` 找到一个签章不符的项目而 **trap**，**而不是跳到攻击者控制的地址运行任意代码**。

### 3-2　`call_indirect` 的运行期检查

```
call_indirect (type $sig) 运行时：
  1. 从堆栈弹出索引 i
  2. 若 i 超出表的范围           → trap「undefined element」
  3. 若 table[i] 为 null         → trap「uninitialized element」
  4. 若 table[i] 的实际签章 ≠ $sig → trap「indirect call type mismatch」
  5. 通过 → 调用
```

**第 4 步是每次调用都要付的运行期成本。** 这正是 Wasm 3.0 **具类型的函数参考（typed function references）** 要解决的问题——用 `(ref $sig)` 这种带类型的参考，**签章在类型系统层面就已经确定，运行期不必再比对**。对虚拟函数调用密集的 C++ / OOP 语言，这是实质的性能改善。

### 3-3　C++ 虚拟函数的真实样貌

```
class Shape { virtual double area(); };

编译到 Wasm 之后：
  ┌ 线性内存 ────────────────────┐
  │ Shape 对象：                    │
  │   +0  vptr → 指向 vtable 的地址  │   ← vptr 是线性内存地址
  │   +4  成员…                     │
  │                                 │
  │ vtable（也在线性内存里）：      │
  │   +0  area 的【函数表索引】(i32) │   ← ★ 不是函数字址，是表索引
  └────────────────────────────────┘
              ↓
  函数表 (funcref)：[ …, Shape::area, Circle::area, … ]
```

**于是一次虚拟调用是：读 vptr → 读 vtable 项目（得到 i32 索引）→ `call_indirect`。**

> **这也是逆向工程 Wasm 时的一个关键着力点**（第 9 章）：`elem` 区段列出了所有可被间接调用的函数，而 vtable 的布局可以从 `call_indirect` 的使用模式反推出来。**类别结构被抹掉了，但调用图的形状还在。**

---

## 四、例外处理：Tag 区段与 `exnref`

**Wasm 3.0 把例外处理收进了内核规范。** 它的机制值得看，因为它跟你熟悉的 try/catch 不太一样。

### 4-1　Tag：例外的「类型」

例外不是对象，是一个 **tag（标签）+ 一组 payload 值**。Tag 声明在 **Tag 区段（id = 13）**：

```wat
(module
  ;; 声明一个例外标签，携带一个 i32 payload
  (tag $oom (param i32))

  (func $alloc (param $n i32) (result i32)
    ...
    (throw $oom (local.get $n)))         ;; 丢出，带着 n
)
```

### 4-2　`try_table`：3.0 的新形式

早期提案用 `try` / `catch` / `delegate` 的区块结构；**Wasm 3.0 采用的是 `try_table` + `exnref`**——把「捕捉」变成一种**分支**，而不是一种嵌套区块：

```wat
(func $safe (result i32)
  (block $handler (result i32)
    (try_table (catch $oom $handler)     ;; 若丢出 $oom，带着 payload 跳到 $handler
      (call $alloc (i32.const 1000000))
      (br 1))                            ;; 没丢出例外 → 跳过 handler
  )
  ;; $handler：堆栈上是 $oom 的 payload (i32)
)
```

**`exnref`** 是一个不透明的例外参考类型，让你可以捕捉「任意例外」再重新丢出（`catch_all_ref` + `throw_ref`）——这是实作 `finally` 与跨语言例外传递所必需的。

### 4-3　为什么这件事对性能很重要

**在原生的例外处理出现之前**，C++ 的 `try/catch` 编译到 Wasm 只有两条路：

| 旧解法 | 代价 |
|---|---|
| `-fno-exceptions` | 整个生态有一半的函数库不能用 |
| **JavaScript 蹦床（trampoline）** | 每一次 `try` 进入都要跨界到 JS 再跨回来——**开销极大，且让 JS 引擎无法内联** |

**原生 EH 之后**，`try_table` 是一条纯 Wasm 指令，引擎可以完整优化。**这是 Wasm 3.0 对 C++ 生态最直接的一次补血。**

---

## 五、JSPI 深入：Wasm 如何「等」一个 Promise

第 3 章介绍了 JSPI 的用途，这里看它的机制与代价。

### 5-1　它到底做了什么

```
一般情况：
  JS ──call──▶ Wasm ──call──▶ 导入的 JS 函数（回传 Promise）
                                  ↓
                            Wasm 拿到一个 Promise 对象，
                            但它不知道怎么「等」——只能立刻继续运行 ❌

JSPI：
  JS ──promising(f)──▶ Wasm ──call──▶ Suspending 包装过的导入
                                          ↓
                       ★ 引擎把整个 Wasm 运行堆栈（连同区域变量、
                         调用链）挂起，搬到一旁，并回传一个 Promise 给 JS
                                          ↓
                            事件循环继续跑（分页不冻结）
                                          ↓
                            Promise 解决 → 引擎把堆栈恢复，
                            把结果推回操作数堆栈，从挂起处继续 ✅
```

### 5-2　API 形状

```javascript
// 1. 导入侧：把回传 Promise 的函数包成「可挂起的」
const imports = {
  env: {
    read_file: new WebAssembly.Suspending(async (ptr, len) => {
      const handle = await root.getFileHandle("data.bin");
      const file = await handle.getFile();
      const buf = new Uint8Array(await file.arrayBuffer());
      new Uint8Array(memory.buffer, ptr, buf.length).set(buf);
      return buf.length;               // Wasm 眼中就是一个同步回传值
    }),
  },
};

// 2. 导出侧：把入口包成「会回传 Promise 的」
const { instance } = await WebAssembly.instantiateStreaming(fetch("app.wasm"), imports);
const main = WebAssembly.promising(instance.exports.main);
await main();                          // 对 JS 而言是 async
```

**Rust 侧几乎不用改**：

```rust
extern "C" { fn read_file(ptr: *mut u8, len: usize) -> usize; }

pub fn load() -> Vec<u8> {
    let mut buf = vec![0u8; 4096];
    let n = unsafe { read_file(buf.as_mut_ptr(), buf.len()) };  // 看起来就是同步调用
    buf.truncate(n);
    buf
}
```

### 5-3　三个必须知道的代价

1. **挂起／恢复不是免费的。** 每次挂起都要把整条 Wasm 堆栈搬走再搬回来，成本与堆栈深度相关。**适合「偶尔等一次 I/O」，放进热循环会很痛。**
2. **它不是并行。** 挂起期间那条 Wasm 线程什么都没做——**你只是把等待的时间让给了事件循环，不是同时做了两件事。**
3. **重入问题。** 挂起期间，JS 可能再次调用同一个 Wasm 实例的导出函数。**如果你的 C 代码假设「同一时间只有一个调用在跑」（绝大多数 C 代码都这样假设），这会造成状态损坏。** 需要自己加一层重入锁。

### 5-4　与 Asyncify 的对照

| | Asyncify | JSPI |
|---|---|---|
| 机制 | Binaryen **改写整个模块**，用线性内存手动保存/还原堆栈 | **引擎原生**挂起 Wasm 堆栈 |
| 体积影响 | **显著膨胀** | 无 |
| 运行开销 | 全局的（改写后的代码一直带着保存/还原逻辑） | 只在实际挂起时付 |
| 需要标注 | 要指定哪些函数会 unwind，漏标就出错 | 不需要 |
| 兼容性 | 到处都能用 | 需要引擎支持（**Chrome 137+／Firefox 139+**） |

**迁移策略**：侦测 `typeof WebAssembly.Suspending === "function"`，有就用 JSPI，没有就退回 Asyncify 建置。

---

## 六、原子操作与内存模型

### 6-1　指令家族

```wat
;; 原子读写
i32.atomic.load / i32.atomic.store
i64.atomic.load8_u / ...（各种宽度）

;; 读-改-写（RMW），全部是单一原子操作
i32.atomic.rmw.add / sub / and / or / xor / xchg / cmpxchg

;; 阻塞与唤醒（futex 语意）
memory.atomic.wait32   (addr, expected, timeout_ns) -> i32
memory.atomic.notify   (addr, count) -> i32

;; 内存屏障
atomic.fence
```

### 6-2　三条必须记住的语意

1. **所有原子操作都是循序一致（sequentially consistent）的。** Wasm **没有** C++ 那种 `memory_order_relaxed` / `acquire` / `release` 的分级——规范只提供最强的那一种。**好处是不会写错，代价是拿不到弱序带来的性能。**
2. **非原子访问没有任何顺序保证。** 两条线程对同一地址的非原子读写是数据竞争；规范定义了它不会破坏沙盒，但**值是什么没有保证**。
3. **`memory.atomic.wait` 在主线程上会 trap。** 主线程不允许阻塞——**这是规范层面的禁止，不是惯例。** 所以任何用到 `wait` 的同步原语都只能在 Worker 里跑（这也正是 SQLite 第一代 `opfs` VFS 必须有 Worker 的原因）。

### 6-3　一个实用的推论

**`memory.atomic.wait32` + `notify` 就是 futex，而 futex 足以实作出所有的同步原语**——mutex、条件变量、号志、屏障。这正是 Emscripten 能把 `pthread` 完整映射过来的底层基础。

---

## 七、Relaxed SIMD 的不确定性清单

Wasm 3.0 收进了 relaxed SIMD，它用**放弃确定性**换取更好的硬件映射。**在链上、在需要跨机器重现结果的科学计算里，这些指令必须禁用。**

| 指令族 | 不确定性从何而来 |
|---|---|
| `relaxed_madd` / `relaxed_nmadd` | 可能用 FMA（单次舍入）也可能用 mul+add（两次舍入）——**浮点结果会差在最后几位** |
| `relaxed_min` / `relaxed_max` | **NaN 与 ±0 的处理方式因平台而异** |
| `relaxed_swizzle` | 索引超出范围时，回传 0 或未定义值，**因平台而异** |
| `relaxed_trunc_*` | 浮点转整数时，超界或 NaN 的结果**因平台而异** |
| `relaxed_dot` | 累加顺序与饱和行为可能不同 |
| `relaxed_laneselect` | 遮罩非全 0/全 1 时行为未定 |

**判断准则**：**只要你的输出会被拿去做哈希、签章、共识、或跨机器比对，就不要用 relaxed SIMD。** 影像滤镜、游戏物理、机器学习推理这类「差几个 ULP 没人看得出来」的场景才适合。

---

## 八、多重内存（Wasm 3.0）

```wat
(module
  (memory $a 1)
  (memory $b 1)

  ;; 加载/保存指令带内存索引
  (func $get (result i32) (i32.load $b (i32.const 0)))

  ;; memory.copy 可跨内存：dst_mem, src_mem
  (func $move (memory.copy $a $b (i32.const 0) (i32.const 0) (i32.const 1024)))

  ;; 各自独立成长
  (func $grow_b (result i32) (memory.grow $b (i32.const 16))))
```

**三个典型用法**：

| 用法 | 好处 |
|---|---|
| **代码区 / 数据区分离** | 大型资产不再挤压工作区的地址空间 |
| **多租户各一块** | 一个模块服务多个租户，内存天然隔离 |
| **冷热分离** | 热数据留在小块内存里，缓存局部性更好 |

**最大的价值**（第 8 章情境 4 已述）：**每块内存仍是 wasm32，因此保护页的免费界检查完整保留**——这是 Memory64 做不到的。

**现实限制**：**工具链支持落后于规范。** 多数 C/C++/Rust 工具链默认假设「只有一块内存」。

---

## 九、部署层：五件会让你在正式环境翻车的事

### 9-1　MIME 类型

```
Content-Type: application/wasm
```

**没有这个，`instantiateStreaming` 会直接拒绝。** GitHub Pages 对 `.wasm` 扩展名会正确回传。

### 9-2　CSP

```http
Content-Security-Policy: script-src 'self' 'wasm-unsafe-eval'
```

Wasm 编译在 CSP 眼中属于动态代码产生。`'wasm-unsafe-eval'`（Chrome 97+／Firefox 102+／Safari 16+）**只放行 Wasm，不放行 `eval()`**。

### 9-3　完整性验证（SRI 的空白）

**这是一个真实的生态缺口**：`<script integrity="sha384-…">` 对 `<script>` 有效，**但 `fetch()` 加载的 `.wasm` 没有内置的 SRI 机制**。想验证得自己来：

```javascript
async function loadVerified(url, expectedSha256Base64) {
  const bytes = await (await fetch(url)).arrayBuffer();
  const digest = await crypto.subtle.digest("SHA-256", bytes);
  const actual = btoa(String.fromCharCode(...new Uint8Array(digest)));
  if (actual !== expectedSha256Base64) throw new Error("wasm integrity mismatch");
  return WebAssembly.instantiate(bytes, imports);   // ⚠️ 代价：放弃串流编译
}
```

> **注意这里有一个取舍**：要验哈希就得先拿到完整字节，**于是你失去了串流编译**（第 2 章）。**安全与启动速度在这里直接对撞**，没有两全的解法。多数团队的选择是：**同源托管 + 建置流程可重现 + CDN 的 TLS**，而不是运行期验哈希。

### 9-4　压缩

```
Content-Encoding: br
```

**Wasm 的 Brotli 压缩率通常很好**——附录 L 的实例是 3.6 MB → 0.8 MB（约 4.5 倍）。**这是投报率最高的一行服务器设置。**

> **为什么 Wasm 特别适合 Brotli，以及如何用「压缩字典传输」让改版只传几十 KB——见附录 N §7。**

### 9-5　代码缓存与 Worker 共享

**两个常被忽略的加速手段**：

```javascript
// (1) 编译一次，多个 Worker 共用
//     WebAssembly.Module 是可结构化拷贝的，postMessage 过去不会重新编译
const mod = await WebAssembly.compileStreaming(fetch("app.wasm"));
for (const w of workers) w.postMessage({ mod });          // ★ 省下 N-1 次编译

// Worker 内：
self.onmessage = async ({data}) => {
  const inst = await WebAssembly.instantiate(data.mod, imports);  // 直接实例化
};
```

```
(2) 浏览器的磁盘代码缓存：
    Chrome 会把 TurboFan 的产物写进 HTTP 缓存，键是 URL。
    → 给 .wasm 一个稳定的 URL（带内容哈希的文件名最佳）
    → 回访时可跳过整个编译阶段，大型模块的第二次加载常快一个量级
```

---

## 十、性能剖析工作流

**很多人以为 Wasm 没办法剖析，其实可以，只是需要准备。**

```bash
# 1. 保留 name 自订区段（否则你只会看到 wasm-function[1234]）
#    Rust：发布版不要无脑 strip = true，改用 wasm-opt 只剥 debug
wasm-opt -O3 --strip-debug --strip-producers app.wasm -o app.wasm
#                ↑ 保留 name section，只剥 DWARF

# 2. Emscripten：明确保留函数名
emcc -O3 --profiling-funcs ...
```

**接着在 Chrome DevTools 的 Performance 面板录制**——Wasm 的框架会以函数名出现在火焰图里，与 JS 框架混合显示。**这让「时间花在跨界还是花在计算」变成一个可以直接看出来的问题。**

**三个最常见的剖析结论，以及它们的长相**：

| 火焰图长相 | 诊断 |
|---|---|
| 大量细碎的 JS↔Wasm 交错条 | **边界穿越太频繁**（第 2 章）——把接口做粗 |
| Wasm 框架宽但内部平坦 | 真的在计算——考虑 SIMD 或算法 |
| `__wbindgen_malloc` / `free` 占比高 | **分配太多**——改用内存池或重用缓冲区 |

**高级**：`performance.mark()` / `measure()` 可以从 Wasm 侧通过导入调用进去，让自订区段出现在时间轴上。

---

## 十一、proxy-wasm：Wasm 在基础设施层的标准 ABI

**这是第 4 章「多租户插件系统」那一段的具体长相**，也是 Wasm 在后端最成功的落地形态之一。

**proxy-wasm** 是一套为网络代理设计的 Wasm ABI，被 **Envoy、Istio、Kong、APISIX、Higress** 等采用。它定义了一组宿主与模块之间的回呼：

```
模块导出（宿主调用模块）：
  proxy_on_context_create(context_id, parent_id)
  proxy_on_request_headers(context_id, num_headers, end_of_stream)
  proxy_on_request_body(context_id, body_size, end_of_stream)
  proxy_on_response_headers(...)
  proxy_on_log(context_id)
  proxy_on_tick(context_id)

宿主导出（模块调用宿主）：
  proxy_get_header_map_value(...)
  proxy_set_header_map_pairs(...)
  proxy_send_local_response(...)   ← 直接回应，不转发到上游
  proxy_get_shared_data / proxy_set_shared_data
  proxy_http_call(...)             ← 对外发 HTTP（例如查鉴权服务）
```

**它为什么是 Wasm 的甜蜜点**（回到第 4 章的判断）：

- **多租户**：一个 Envoy 进程里可以跑上百个互不信任的客户插件，各有独立的线性内存与能力边界。**用容器做这件事是不可能的。**
- **热更新**：换一个 `.wasm` 就换一套逻辑，不用重启代理。
- **语言无关**：客户用 Rust、Go、AssemblyScript 都行。

> **这正是第 4 章那句话的证据**：**Wasm 不会从既有服务手上抢市场，它会在那些容器结构上进不去的地方长出自己的地盘。**

---

## 十二、代码分割与延迟加载

**当模块大到必须切开时**，有两条路：

### 12-1　`wasm-split`（Emscripten / Binaryen）

把一个模块切成**主模块 + 次模块**，主模块先加载，次模块在第一次调用到时才抓。

```bash
# 先用剖析取得「启动时真正用到的函数」清单
wasm-split app.wasm -o1 primary.wasm -o2 secondary.wasm \
  --profile=startup.prof --keep-funcs=@startup-funcs.txt
```

**适合**：启动路径明确、大部分功能是「用户可能永远不会点」的应用。

### 12-2　手动切成多个独立模块

```javascript
// 首屏只载内核
const core = await WebAssembly.instantiateStreaming(fetch("core.wasm"), imports);

// 用户点了「导出 PDF」才载
button.onclick = async () => {
  const pdf = await WebAssembly.instantiateStreaming(fetch("pdf.wasm"), {
    env: { memory: core.instance.exports.memory },   // ★ 共用同一块线性内存
  });
  pdf.instance.exports.export_pdf(ptr, len);
};
```

**关键细节**：两个模块**共用同一块线性内存**（把 memory 从一边 export、另一边 import），这样数据不需要拷贝。**Tesseract 的语言包、Pyodide 的 `micropip` 都是这个形状。**

---

## 附：本附录与正文的对照索引

| 你想知道 | 看这里 | 正文背景 |
|---|---|---|
| 二进位到底长怎样 | 本附录 §1 | 第 2 章情境 1 |
| 为什么验证能单趟完成 | §2 | 第 2 章情境 1 |
| 函数指针与虚拟函数 | §3 | 第 2 章、第 9 章（逆向） |
| C++ 例外的代价 | §4 | 第 1 章（技术债）、第 3 章 |
| 同步代码怎么等异步 API | §5 | 第 3 章墙七、第 7 章、附录 L |
| 多线程的底层原语 | §6 | 第 3 章墙六、第 5 章 |
| 哪些 SIMD 指令不能用在链上 | §7 | 第 4 章（EVM 确定性） |
| 4GiB 的第三条出路 | §8 | 第 8 章情境 4 |
| 正式环境部署清单 | §9 | 第 5 章、附录 C |
| 怎么剖析 Wasm | §10 | 第 3 章墙八 |
| Wasm 在后端真正赢的地方 | §11 | 第 4 章情境 2 |
| 模块太大怎么办 | §12 | 第 8 章 |
