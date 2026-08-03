# 附录O　测试、CI 与运行期安全

> 这是本书最后补上的一块，而它补的是一个很尴尬的洞：**前面那十四份附录教你怎么把 Wasm 做出来、做小、做快、做得不被抄走——却没有一份告诉你怎么确认它是对的。**
>
> 第 3 章说过一句话：**「评估一项技术的成熟度，最准的指针不是它跑多快，是它坏掉的时候有多容易查。」** 这份附录就是那句话的操作手册。

---

## 一、Wasm 测试的三层金字塔

**Wasm 项目的测试有一个特殊之处：同一份代码可以在三个环境里跑，而它们抓得到的错误完全不同。**

```
        ┌───────────────────────────────┐
        │  ③ 浏览器集成测试（最慢、最真）  │  ← 抓：JS 绑定、DOM/API 交互、
        │     wasm-bindgen-test          │        OPFS/Worker 行为、真实引擎差异
        ├───────────────────────────────┤
        │  ② Wasm 环境单元测试            │  ← 抓：Wasm 特有的行为
        │     wasm32 target + Node/WASI  │        （内存对齐、i32 溢出、跨界）
        ├───────────────────────────────┤
        │  ① 原生单元测试（最快、最多）    │  ← 抓：纯逻辑错误
        │     cargo test / ctest         │        **这一层应该占 80%**
        └───────────────────────────────┘
```

**最重要的一条原则**：**能在第 ① 层抓到的错，绝不要拖到第 ③ 层。** 原生测试跑一次是毫秒，浏览器集成测试跑一次是几十秒——**把纯逻辑写成不依赖 Wasm 的形状，是 Wasm 项目最值得做的一次架构投资。**

```rust
// ✅ 这个形状让 80% 的测试可以在原生跑
mod core {                                   // 纯逻辑，不碰 wasm-bindgen
    pub fn transform(input: &[u8]) -> Vec<u8> { /* ... */ }
}

#[cfg(target_arch = "wasm32")]
mod bindings {                               // 只有这一层需要 Wasm 环境
    use wasm_bindgen::prelude::*;
    #[wasm_bindgen]
    pub fn transform(input: &[u8]) -> Vec<u8> { super::core::transform(input) }
}

#[cfg(test)]
mod tests {                                  // cargo test 直接跑，不需要浏览器
    #[test] fn roundtrip() { assert_eq!(super::core::transform(b"abc"), b"..."); }
}
```

---

## 二、`wasm-bindgen-test`：在真的引擎里跑测试

```rust
use wasm_bindgen_test::*;

// 在浏览器里跑（默认是 Node）
wasm_bindgen_test_configure!(run_in_browser);

#[wasm_bindgen_test]
fn works_in_wasm() {
    assert_eq!(crate::core::transform(b"abc"), b"...");
}

// ★ 异步测试：OPFS、fetch、任何 Promise
#[wasm_bindgen_test]
async fn opfs_roundtrip() {
    let engine = WasmStorageEngine::new().await.unwrap();
    engine.save_file("t.bin", &[1, 2, 3]).await.unwrap();
    assert_eq!(engine.load_file("t.bin").await.unwrap(), vec![1, 2, 3]);
}

// 只在 Worker 里跑（sync access handle 的规范限制，见第 7 章）
wasm_bindgen_test_configure!(run_in_dedicated_worker);
```

```bash
wasm-pack test --headless --chrome        # 无头 Chrome
wasm-pack test --headless --firefox
wasm-pack test --node                     # 最快，但拿不到浏览器 API
```

**三个实务要点**：

1. **`run_in_dedicated_worker` 是 OPFS 测试的必要条件**——`createSyncAccessHandle` 在主线程会直接失败（第 7 章）。
2. **每个测试档是一个独立的 Wasm 模块**，所以测试之间**不共用线性内存**——这是好事（隔离），但也意味着测试启动成本不低。
3. **`--headless` 需要对应的 driver**（chromedriver / geckodriver），CI 上要一并安装。

---

## 三、C/C++ 的路径

```bash
# Emscripten：直接产出可用 node 运行的测试
emcc test.cpp -o test.js -sEXIT_RUNTIME=1 -sASSERTIONS=2
node test.js

# ★ Sanitizer 在 Wasm 上可用——这是弥补「沙盒内没有 ASLR/canary」的最实际手段
emcc app.cpp -fsanitize=address -sALLOW_MEMORY_GROWTH=1 -o app-asan.js
emcc app.cpp -fsanitize=undefined -o app-ubsan.js
```

**为什么 Sanitizer 在 Wasm 上特别重要**（第 2 章 ⚠️ 的直接推论）：

> 线性内存内部**没有 ASLR、没有 NX、没有 stack canary**。一个在 x86 上会被操作系统挡下、立刻崩溃的缓冲区溢出，在 Wasm 里可能**安静地写坏相邻数据然后继续跑**——你会在几百行之后看到一个莫名其妙的错误结果，而不是一个清楚的 segfault。
>
> **ASan/UBSan 是你在 Wasm 里唯一能拿回这些保护的方式。** 代价是体积与速度都会显著变差，所以它是**测试建置**，不是发布建置。

**WASI 场景**：

```bash
# 用 wasmtime 直接跑测试二进位
cargo test --target wasm32-wasip1 --no-run
wasmtime run --dir=. target/wasm32-wasip1/debug/deps/mytest-*.wasm
```

---

## 四、Fuzzing：Wasm 特别值得做的一件事

**理由很直接**：Wasm 模块的入口通常是「喂一坨字节进来」，**这正是 fuzzing 最有效的形状**。

```rust
// fuzz_targets/parse.rs
#![no_main]
use libfuzzer_sys::fuzz_target;

fuzz_target!(|data: &[u8]| {
    let _ = mycrate::core::parse(data);      // 不能 panic、不能越界、不能无限循环
});
```

```bash
cargo fuzz run parse -- -max_total_time=300
```

**而 Wasm 给了 fuzzing 一个额外的好处**：**你可以把 fuzzer 本身跑在 Wasm 沙盒里**，于是即使目标代码被构造出的输入打爆，**也绝对伤不到宿主**（这正是附录 E 案例 50「字体模糊测试」的原理）。

**三个一定要 fuzz 的地方**：任何**解析器**（文件格式、协定、输入）、任何**索引运算**、任何**从 JS 传进来的长度/偏移量**。

---

## 五、CI：一份可以直接用的 workflow

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

      # ① 原生单元测试（最快，抓 80% 的错）
      - run: cargo test --all-features
      - run: cargo clippy --all-targets -- -D warnings

      # ② Wasm 环境测试
      - run: curl https://rustwasm.github.io/wasm-pack/installer/init.sh -sSf | sh
      - run: wasm-pack test --node

      # ③ 浏览器集成测试
      - uses: browser-actions/setup-chrome@latest
      - run: wasm-pack test --headless --chrome

      # ④ ★ 体积回归守门（见附录 N）
      - name: Build & check size budget
        run: |
          wasm-pack build --target web --release
          npm install -g binaryen
          f=$(ls pkg/*_bg.wasm)
          wasm-opt -Oz --strip-debug "$f" -o "$f"
          raw=$(stat -c%s "$f")
          br=$(brotli -q 11 -c "$f" | wc -c)
          echo "raw=$raw brotli=$br"
          # 超过预算就让 CI 红灯——体积回归跟性能回归一样需要守门
          test "$br" -le 900000 || { echo "::error::Brotli size $br > budget 900000"; exit 1; }

      # ⑤ ★ 安全红线（第 9 章）
      - name: Secret scan in binary
        run: |
          if strings pkg/*_bg.wasm | grep -Eq 'sk-|AKIA|BEGIN [A-Z ]*PRIVATE KEY'; then
            echo "::error::possible secret embedded in wasm"; exit 1
          fi
```

**第 ④ 与第 ⑤ 步是这份 workflow 真正的价值所在**，因为它们守的是两件**只会慢慢恶化、不会突然坏掉**的事：

- **体积回归**：没有守门的话，`.wasm` 会在半年内从 800KB 长到 4MB，而没有任何一次 commit 该为此负责。**把预算写进 CI，让每一次超标都有人回答「为什么」。**
- **密钥泄漏**：第 9 章的两大物理禁区之一。**这是一行 `grep`，却是全书投报率最高的一行 CI 设置。**

---

## 六、跨引擎差异：那些只在某一家坏掉的东西

**「在 Chrome 上好好的」是 Wasm 项目最常见的假象。** 已知的差异来源：

| 差异点 | 具体表现 |
|---|---|
| **内存上限** | 各引擎与平台不同（第 8 章）；**行动端远低于桌面** |
| **特性支持度** | SIMD、threads、GC、JSPI、memory64 的落地时程各家不同 |
| **OPFS 行为** | `createSyncAccessHandle` 的并行语意、配额与驱逐策略有实作差异（第 7 章） |
| **计时器精度** | 未跨来源隔离时被粗化，各家粗化程度不同（附录 N §15） |
| **编译策略** | 分层编译的 tier-up 时机不同 → **微基准的结果可能完全不同** |
| **堆栈深度** | 递归爆栈的阈值不同 |

**对策是一条纪律**：**在 CI 里至少跑两家引擎（Chrome + Firefox），并在真实的低级行动设备上实测一次。** 桌面开发机是所有 Wasm 项目最危险的乐观来源。

**运行期侦测 + 降级路径**：

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

> 💡 **维护多个建置变体是有成本的。** 先问一句：**没有 SIMD 的那条路径，我真的测过吗？** 一个从来没被运行过的降级路径，跟没有降级路径是一样的——**只是你会更晚才发现。**

---

## 七、运行期安全：那个被「Wasm 很安全」盖住的攻击面

**第 3 章说过「Wasm 所以安全」不是一个可以写进安全评估报告的句子。这一节把那句话展开。**

### 7-1　三层攻击面，被保护的只有第一层

```
① 模块伤不到宿主        ← ✅ 这一层 Wasm 保护得很好（类型系统 + 验证器 + 沙盒）
② 模块内部的内存安全   ← ❌ 完全没有保护（无 ASLR/NX/canary，见第 2 章）
③ 运行期本身的实作漏洞   ← ❌ 这是被谈得最少的一层
```

**第 ③ 层值得单独说**：Wasm 运行期是一大坨用 C++/Rust 写的复杂软件——**它有 JIT、有信号处理器、有内存映射管理**，而这些正是历史上漏洞最密集的地方。Wasmtime、V8 的 Wasm 实作、以及其他运行期都出现过安全公告。**「跑在 Wasm 沙盒里」降低了风险，没有消除风险。**

**实务对策**：

| 场景 | 对策 |
|---|---|
| 浏览器 | 依赖浏览器自身的更新机制（这一层你管不了，也不该管） |
| **后端运行不信任的模块** | **运行期必须跟着上游更新**；并且**不要只靠 Wasm 沙盒**——外面再包一层 OS 级隔离（容器 / seccomp / 独立进程） |
| 多租户 | 限制每个实例的内存与运行时间（燃料/计量）；**别让一个租户的无穷循环拖死整个进程** |

> **注意最后一项与附录 L 的呼应**：FluffOS 的 Wasm 建置**没有 eval limit**，因此「一段无穷的 LPC 循环会卡死整个分页」。**在浏览器里这只是用户体验问题；在多租户后端，这就是 DoS。**

### 7-2　供应链：那个有漂亮 commit 纪录的恶意模块

**第 9 章提过但值得展开**：静态托管的「代码锁在 Git 里」听起来很安全，**但如果你的建置流程引入了被投毒的套件，产出的 `.wasm` 本身就是恶意的——而它同样有一个干净的 commit 纪录。**

```bash
# 最低限度的供应链纪律
cargo audit                    # 已知漏洞
cargo deny check               # 授权、来源、重复依赖
cargo vet                      # 依赖审查纪录
# C/C++：锁定第三方库版本并自行建置，不要用来路不明的预编译 .a
```

**加上两条 Wasm 特有的**：

1. **对产出的 `.wasm` 做 `wasm-objdump -x`，检查 import 清单。** **模块要求了哪些能力，那张清单就是它的攻击面**（第 1、7 章的能力式安全）。**一个影像处理模块突然 import 了网络相关的宿主函数，那就是红旗。**
2. **可重现建置**：同一份原代码在 CI 上编出来的 `.wasm` 哈希应该稳定。**做得到的话，社群就能验证「这个二进位确实是那份原代码编的」**——这正是第 9 章那条「可稽核 ≠ 已稽核」的补救方式。

---

## 八、可观测性：在线坏掉的时候你手上有什么

**这是第 3 章「墙八：调试困难」的正式环境版本。**

```
发布版你做了什么           →  你失去了什么          →  怎么补回来
────────────────────────────────────────────────────────────
strip = true              →  函数名               →  ★ 保留一份带符号的建置
--strip-debug             →  DWARF                →  存进符号服务器/artifact
panic = "abort"           →  panic 消息与堆栈      →  自建错误码
panic_immediate_abort     →  连错误码都没有        →  只在确定不需要时用
```

**一份最小可行的在线错误回报**：

```javascript
window.addEventListener("error", (e) => {
  if (e.error instanceof WebAssembly.RuntimeError) {
    report({
      kind: "wasm_trap",
      message: e.error.message,          // "memory access out of bounds" 等
      stack: e.error.stack,              // 含 wasm-function[N] —— 需要符号才有意义
      build: __BUILD_HASH__,             // ★ 对应到你保留的那份带符号建置
      caps: { simd: ..., threads: ..., isolated: self.crossOriginIsolated },
      memPages: wasm.memory.buffer.byteLength / 65536,   // 撞上限了吗？
    });
  }
});
```

**三个最值得回报的字段**（它们对应到本书三个最常见的在线故障）：

| 字段 | 对应的故障 |
|---|---|
| `memPages` | **撞到内存上限**（第 8 章）——行动设备最常见 |
| `caps.isolated` / `caps.threads` | **多线程建置跑在非隔离页面上**（第 5 章） |
| `build` | **用户拿到了旧版**（Service Worker 缓存，附录 C 疑难排解） |

> 💡 君之一席话
> 与君一席话：**一个系统的成熟度，不看它顺利时多漂亮，看它出事时留下多少线索。** Wasm 的整条工具链都在鼓励你把线索丢掉——strip 掉符号省体积、abort 掉 panic 省体积、关掉断言省体积，**而每一项都是拿「未来某个凌晨三点」去换今天的几十 KB。** 这个交易不一定不划算，但它必须是**被明确做出的决定**，而不是拷贝粘贴一份 `Cargo.toml` 的副作用。**最低限度的纪律只有一条：不管你 strip 掉什么，都要留一份没 strip 的、和发布版字节级对应的建置。** 那份东西平常一文不值，出事那天它是你唯一的证据。

---

## 九、上线前的完整检查清单（集成版）

> 这份清单集成了附录 C（部署）、附录 N（体积与速度）与本附录（测试与安全）。

```
【正确性】
□ 原生单元测试通过（应涵盖 80% 的逻辑）
□ wasm-pack test --node 通过
□ wasm-pack test --headless --chrome 与 --firefox 都通过
□ 解析器类代码跑过 fuzzing
□ 用 -fsanitize=address 的测试建置跑过一轮

【体积】（附录 N）
□ wasm-objdump -h 看过区段预算（Data 占比高就先裁数据）
□ wasm-opt -Oz --converge 跑过
□ twiggy top / dominators 没有意外的凶手
□ CI 有体积预算守门

【性能】（附录 N）
□ 分开量过：编译 / 实例化 / 运行期初始化
□ 量测时的跨来源隔离状态一致（否则计时器被降精度）
□ 热路径上没有细碎跨界调用
□ 大区块搬移用的是 memcpy 而不是逐字节循环

【部署】（附录 C）
□ Content-Type: application/wasm、Content-Encoding: br
□ 内容哈希文件名（稳定 URL → 代码缓存）
□ CSP 含 'wasm-unsafe-eval'（若站台有 CSP）
□ .nojekyll、相对路径、await init()
□ 确认过有没有「不需要 SharedArrayBuffer」的后端可用

【安全】（第 9 章 + 本附录）
□ strings 扫过二进位，没有密钥  ★ 最重要
□ wasm-objdump -x 看过 import 清单，没有意外的能力需求
□ cargo audit / cargo deny 通过
□ 后端运行不信任模块时：运行期已更新，且外层有 OS 级隔离
□ 有内存与运行时间的配额限制

【可观测性】
□ 保留了一份带符号、与发布版字节级对应的建置
□ 在线有 WebAssembly.RuntimeError 的回报，含 build hash 与 memPages
□ 降级路径（无 SIMD / 无 threads）真的被运行过，不只是写在那里
```

---

## 附：与正文的对照索引

| 主题 | 本附录 | 正文背景 |
|---|---|---|
| 测试分层 | §1–3 | 第 3 章墙八 |
| Sanitizer 为何在 Wasm 上特别重要 | §3 | **第 2 章情境 1 ⚠️**（沙盒内没有 ASLR/canary） |
| Fuzzing | §4 | 附录 E 案例 50 |
| CI 的体积与密钥守门 | §5 | 附录 N、第 9 章 |
| 跨引擎差异 | §6 | 第 8 章、附录 N §15 |
| 运行期本身的攻击面 | §7-1 | 第 3 章情境 1（「Wasm 所以安全」不是一句可以写进报告的话） |
| 供应链 | §7-2 | 第 9 章情境 4 ⚠️ |
| 可观测性 | §8 | 第 3 章墙八、第 12 章（三年后谁修） |
