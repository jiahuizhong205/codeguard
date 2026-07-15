# REFLECTION.md — CodeGuard 项目反思报告

> AI4SE 期末 A 类项目 · Coding Agent Harness
>
> *反思是工程的核心部分——不反思的工程师只是代码打字机。*

---

## 目录

1. [Superpowers 技能评估](#1-superpowers-技能评估)
2. [TDD 在 AI 协作下的角色](#2-tdd-在-ai-协作下的角色)
3. [Subagent 自主性与 task 颗粒度](#3-subagent-自主性与-task-颗粒粒度)
4. [SPEC/PLAN 质量与实现质量](#4-specplan-质量与实现质量)
5. [最有效的 prompt / context 策略](#5-最有效的-prompt--context-策略)
6. [凭据与分发工程要求的深层影响](#6-凭据与分发工程要求的深层影响)
7. [用户交互驱动的体验优化过程](#7-用户交互驱动的体验优化过程)
8. [如果重做会改变什么](#8-如果重做会改变什么)
9. [对 Superpowers 方法论的批判](#9-对-superpowers-方法论的批判)

---

## 1. Superpowers 技能评估

### 发挥最大作用的技能

**`superpowers:brainstorming`（最大价值）**

Brainstorming 技能在项目启动阶段发挥了决定性作用。它强制我在写任何代码之前，先与用户协作完成 10 节设计呈现（问题陈述 → 领域设计 → 架构 → 用户故事 → 功能规约 → 数据模型 → 安全 → 非功能需求 → 验收标准 → 风险），每节后用户确认。这个过程产出了 1172 行的 SPEC.md，直接决定了后续 21 个 task 的清晰度和 subagent 的偏离率。

**核心价值**：它把"我想做一个 agent harness"这个模糊想法，变成了一个可以被 subagent 独立执行的精确规约。没有 brainstorming，subagent 会在第一行代码就开始偏离。

**`superpowers:writing-plans`（第二价值）**

将 SPEC 分解为 21 个 TDD task，每个 task 有明确的输入/输出/验证步骤。这个分解的质量直接决定了 subagent 能否自主运行。8 个 Phase 的分层（Foundation → Tools → Governance → Feedback → Infrastructure → Integration → Frontend → Distribution）确保了依赖关系清晰，批次内可并行。

**`superpowers:subagent-driven-development`（第三价值）**

允许将 17 个 task 分 4 次派发给 subagent，每次 2-8 个并行。控制器只需审查结果，不需要逐行监督。这把"一个人写 21 个模块"变成了"一个人审查 4 批提交"。

**`superpowers:test-driven-development`（第四价值）**

TDD 技能强制每个 task 先写测试再写实现。在 AI 协作下，这不仅是质量保障，更是**验证 subagent 是否理解了 task 的标尺**——如果 subagent 写的测试和 SPEC 验收标准不一致，说明它理解偏了。

### "形式大于实质"的技能

**`superpowers:using-git-worktrees`**

理论上每 Phase 一个 worktree 可以隔离工作，但在 Windows 上符号链接权限问题导致 1 个测试被 skip，worktree 的隔离价值没有体现——subagent 在同一仓库内工作已经足够。如果重做，我会直接用分支而非 worktree。

**`superpowers:verification-before-completion`**

这个技能要求"声称完成前必须运行验证命令"。在 subagent 场景下，subagent 本身就会运行 `pytest`，控制器的二次验证变成了重复劳动。它的价值更多在于防止"我说完了但没测"的自欺，但在 subagent-driven 流程中，CI 已经承担了这个角色。

**`superpowers:requesting-code-review` / `receiving-code-review`**

在 subagent-driven 流程中，代码审查由控制器（我）直接执行，不需要走正式的 review 流程。这两个技能更适合人类协作场景，在 AI-only 流程中显得过重。

---

## 2. TDD 在 AI 协作下的角色

### 结论：TDD 是放大器，不是阻碍

在传统开发中，TDD 的主要争议是"先写测试拖慢了开发速度"。但在 AI 协作下，情况完全不同：

**TDD 是 subagent 的"验收合同"**。当我把 Task 7（护栏引擎）派给 subagent 时，task 描述里包含了 12 条规则的具体测试用例：`check(Action(command="rm -rf /"))` 必须返回 `DENY`。subagent 不需要"理解"为什么要 DENY，它只需要让测试通过。测试就是规约的可执行形式。

**TDD 防止了 LLM 的"创造性偏离"**。LLM 天然倾向于"改进"——它会在护栏引擎里加入"智能风险评估"、在 HITL 里加入"自然语言审批理由解析"。这些听起来很酷，但不在 SPEC 里。TDD 的"先红再绿"强制 subagent 只做让测试通过的事，不多做。

**TDD 让"移除 LLM 后还剩什么"这个问题有了答案**。97 个测试全部用 MockLLMClient 运行，不依赖网络。这意味着即使 LLM 供应商倒闭，仓库里的工程价值不变。这正是 SPEC §1.2 的核心命题。

**唯一的不适**：TDD 在 mock LLM 场景下可能被"绕过"——subagent 可以写一个永远返回 True 的 mock 来让测试通过。CI 强制检查 + 控制器审查是唯一的防线。在实践中，没有发现 subagent 这么做，但这是一个结构性风险。

---

## 3. Subagent 自主性与 task 颗粒度

### Subagent 能自主运行多久？

**答案：一个批次（2-8 个 task）约 15-30 分钟，之后需要人类审查。**

在 4 批 subagent 派发中，每批的自主运行时间在 15-30 分钟。偏离通常发生在：

1. **接口不一致**：Task 5（文件工具）和 Task 11（反馈验证器）的接口签名在 SPEC 和 PLAN 之间不一致（SPEC_PROCESS.md 缺陷 6），subagent 各自按不同理解实现，导致集成时需要修复。
2. **环境差异**：Task 15（MCP 适配器）的 subagent 在 asyncio 事件循环内调用 `asyncio.run()`，在 pytest-asyncio 环境下失败。subagent 自行修复为线程池降级，但这个修复说明 subagent 对运行环境的理解有限。
3. **工具注册遗漏**：Task 20（演示脚本）的 subagent 忘记注册 RunTests 工具，导致 Demo 2 的反馈闭环无法工作。subagent 自己发现了并修复了。

### 最优 task 颗粒度

**最优颗粒度：一个 task = 一个 Python 模块 + 对应测试文件，约 50-150 行实现代码。**

- 太小（< 30 行）：task 描述的 overhead 超过实现本身，subagent 花更多时间理解 task 而非写代码。
- 太大（> 200 行）：subagent 开始"创造性发挥"，加入 SPEC 没有要求的功能。
- 50-150 行是甜区：subagent 能在一个 session 内完成，测试覆盖完整，审查成本低。

21 个 task 中，Task 16（AgentLoop）是最大的，约 130 行。subagent 完成质量良好，但需要 2 次修复（asyncio + 工具注册）。如果重做，我会把 AgentLoop 拆成"主循环骨架"和"反馈回灌逻辑"两个 task。

---

## 4. SPEC/PLAN 质量与实现质量

### 规约不清导致 subagent 偏离的具体案例

**案例：HITLManager 的 `_wait_for_resolution()` 幻觉方法**

SPEC §3.6 的伪代码写了 `return await self._wait_for_resolution(req)`，但这个方法从未在 SPEC 中定义。当 subagent 实现 Task 9（HITL 管理器）时，它面临一个未定义的接口：

- **subagent 的选择**：它没有自己发明一个 `_wait_for_resolution` 实现，而是在 docstring 中明确标注"此方法由 AgentLoop 承担"，保持了 HITLManager 的单一职责。
- **结果**：这个决策是正确的——HITLManager 保持为同步状态机，可独立单测。但 SPEC 的模糊性导致了 1 个中等级别的缺陷记录和额外的人类审查成本。

**案例：FeedbackValidator 签名不一致**

SPEC §3.9 写 `validate(output: str, exit_code: int)`，PLAN 写 `validate(result: ToolResult)`。当 Task 11 的 subagent 实现时，它选择了 PLAN 的签名（`validate(result: ToolResult)`），因为 PLAN 更具体。但 Task 16（AgentLoop）的 subagent 按 SPEC 的签名调用——导致集成时接口不匹配。

**教训**：SPEC 和 PLAN 之间的签名级别不一致是最大的偏离来源。如果重做，我会在 PLAN 阶段为每个 task 生成接口签名表，确保 SPEC 和 PLAN 在签名级别完全一致。

### SPEC 质量对实现质量的量化影响

| SPEC 质量指标 | 数值 | 影响 |
|--------------|------|------|
| SPEC 总行数 | 1172 | 充分覆盖 |
| SPEC/PLAN 缺陷数 | 6 | 5 个已修复，1 个留待后续 |
| 阻塞级缺陷 | 1（pyproject.toml build-backend） | 如果未发现，项目无法安装 |
| subagent 偏离次数 | 2（asyncio、工具注册） | 均为环境/集成问题，非 SPEC 问题 |
| 测试通过率 | 97/98（99%） | 1 个 skip 为 Windows 符号链接权限 |

---

## 5. 最有效的 prompt / context 策略

### 策略一：Task 描述包含完整的测试用例

最有效的策略是在 task 描述中直接嵌入测试代码：

```
Task 7: 实现护栏引擎

测试用例（必须全部通过）：
- check(Action(name="run_shell", params={"command": "rm -rf /"})) → DENY, rule_id="R001"
- check(Action(name="run_shell", params={"command": "git push"})) → ASK, rule_id="R011"
- check(Action(name="read_file", params={"path": ".env"})) → DENY, rule_id="R007"
```

**为什么有效**：subagent 不需要"理解"规约，它只需要让测试通过。测试用例是规约的可执行形式，消除了自然语言的歧义。

### 策略二：System prompt 中的"不要做什么"比"要做什么"更重要

在 AgentLoop 的 system prompt 中，最有效的部分不是"你是一个编码 agent"，而是：

```
When creating a file for the user, use write_file tool,
or include the filename in the code block like: ```c:hello.c
```

这个指令直接解决了"LLM 输出代码但不带文件名"的问题。负面约束（"不要做 X"）在 LLM 协作中往往比正面指令更有效，因为它限制了 LLM 的"创造性发挥"空间。

### 策略三：SPEC_PROCESS.md 作为"已知歧义注册表"

在 subagent 开始实现前，让它先读 SPEC_PROCESS.md。这个文档记录了所有已发现的 SPEC/PLAN 缺陷和歧义，以及决策理由。subagent 不需要自己重新发现这些歧义——它只需要遵循已做出的决策。

**为什么有效**：减少了 subagent 的"决策疲劳"。没有这个文档，subagent 遇到歧义时会自行决策，而它的决策可能和控制器期望的不一致。

---

## 6. 凭据与分发工程要求的深层影响

### 凭据安全迫使想清楚的问题

**1. "key 在哪里"不是一个问题，是一个状态机**

SPEC §7 定义了凭据的完整生命周期：首次录入 → 加密存储 → 查看状态（不回显）→ 更新 → 清除。这迫使我想清楚：key 在每个阶段处于什么状态（明文/加密/内存/磁盘），谁能看到它，什么时候被清除。

**2. 审计日志的脱敏不是"删掉 key"，是"替换 key 的语义"**

最初我以为脱敏就是把 `api_key=sk-xxx` 变成 `api_key=***`。但实际实现时发现，脱敏需要保留参数的结构信息（哪个参数被脱敏了），否则审计日志失去了诊断价值。最终实现了 `_sanitize()` 方法，按 key 名匹配（`key`/`secret`/`token`/`password`），只替换值不替换键名。

**3. Docker 镜像不能含 key，但 agent 需要 key 才能工作**

这迫使我想清楚"构建时"和"运行时"的分离。Dockerfile 只装代码和依赖，key 通过 volume 挂载或环境变量在运行时注入。这个分离后来也用在了 CI 中——GitHub Actions 的 secret 只在运行时注入，不在代码中。

### 分发设计迫使想清楚的问题

**1. "能跑"和"能分发"是两个不同的工程问题**

本地开发时 `pip install -e .` 就能跑。但分发要求 Docker 镜像自包含、跨平台一致、CI 可复现。Dockerfile 的多阶段构建（frontend-builder → backend-builder → runtime）迫使我想清楚构建依赖和运行依赖的分离。

**2. 前端构建产物不属于源码**

最初我把 `frontend/dist/` 加入了 .gitignore，但后来发现 CI 需要 frontend 构建产物来打包进 Docker 镜像。最终方案是：CI 中在 Docker 构建阶段重新 `npm run build`，不在仓库中存储构建产物。但为了开发便利，`src/codeguard/static/` 目录存储了本地构建产物（.gitignore 排除）。

---

## 7. 用户交互驱动的体验优化过程

> 这一节专门反思在项目"完成"后，通过亲自使用系统、发现问题、迭代优化的过程。

### 背景

21 个 task 全部完成、97 个测试通过、CI 绿灯——按照 SPEC 的验收标准，项目"完成"了。但当我真正坐下来使用这个系统时，发现了一系列 SPEC 没有覆盖的体验问题。

### 第一轮：文件去哪了？

**发现**：我让 agent "创建一个 hello.c 文件"，agent 回复"已创建"，但我不知道文件在哪。去文件系统里找——在 `/tmp` 目录下。这不对。

**问题本质**：SPEC 定义了 `WriteFile` 工具写入 workspace，但没有定义"用户如何获取生成文件"。SPEC 假设用户会去文件系统找，但实际使用中用户期望在浏览器里看到。

**解决方案**：
1. 新增 `FILE_OUTPUT` 步骤类型，agent 调用 `write_file` 时通过 WebSocket 推送文件内容到前端
2. 新增 `FilePreview` 组件——代码预览 + 下载按钮
3. 新增 `GET /api/session/{id}/artifacts/{filename}` 下载端点

**教训**：SPEC 的验收标准是"Web 界面可用"，但"可用"的定义太模糊。如果 SPEC 写了"用户可在浏览器内预览和下载 agent 生成的文件"，这个功能在 Task 18 就会被实现，而不是在项目"完成"后才发现。

### 第二轮：代码块提取太激进

**发现**：我加了自动从 LLM 回复中提取代码块的功能，结果 agent 回复里的 ` ```sh npm run build ` 也变成了可下载文件。用户界面被无关的"文件"淹没。

**问题本质**：我过度补偿了——从"不提取任何代码"跳到了"提取所有代码"。没有区分"这是用户要的文件"和"这是对话中的代码片段"。

**解决方案**：只提取带文件名的代码块（` ```c:hello.c `），无文件名的代码块（` ```sh `）不生成下载。同时改进 system prompt，引导 LLM 在创建文件时带上文件名。

**教训**：自动化需要精确的触发条件。"提取所有代码块"是一个粗粒度的规则，"提取带文件名的代码块"是一个精确的规则。粒度越细，误触发越少。

### 第三轮：等待时没有反馈

**发现**：发送消息后，界面完全静止——没有 loading、没有"正在思考"、没有任何状态变化。用户不知道系统是否在工作，只能干等。

**问题本质**：后端 `loop.run()` 收集所有步骤后一次性返回，前端只在收到步骤时更新。从发送消息到第一个步骤之间有一个"反馈真空期"。

**解决方案**：
1. **后端**：`AgentLoop.run()` 新增 `on_step` 回调，步骤生成即推送（不再等全部完成）
2. **后端**：发送 `status` 事件（"正在初始化 Agent..."）提供即时反馈
3. **前端**：`ChatPanel` 添加 thinking 动画（三点跳动）+ 状态消息
4. **前端**：`isProcessing` 状态管理，发送时立即设为 true

**教训**：这是一个架构问题，不是功能问题。`loop.run()` 的"收集后返回"设计在前端时代是不可接受的——用户期望实时反馈。如果 SPEC 写了"WebSocket 步骤推送延迟 < 100ms"（实际上写了），就应该同时写"用户发送消息后 < 1s 内必须看到反馈状态"。

### 反思总结

这三轮优化有一个共同模式：**SPEC 定义了"做什么"，但没有定义"用户体验如何"**。SPEC 写了 WebSocket 推送、HITL 弹窗、步骤展示，但没有写"用户发送消息后应该看到什么"、"文件生成后用户如何获取"、"等待时有没有反馈"。

这告诉我：**SPEC 需要包含用户体验规约，不仅仅是功能规约**。如果重做，我会在 SPEC 中新增一节"用户体验规约"，定义每个用户操作后的预期反馈（视觉、时间、交互）。

---

## 8. 如果重做会改变什么

### 会改变的

**1. SPEC 中新增"用户体验规约"节**

定义每个用户操作后的预期反馈：发送消息 → < 1s 显示 thinking 动画 → 实时推送步骤 → 完成后显示结果。文件生成 → 自动出现在预览区 → 可下载。这些在当前 SPEC 中完全缺失。

**2. AgentLoop 从一开始就设计为流式**

`run()` 方法应该从一开始就接受 `on_step` 回调，而不是先设计为"收集后返回"再改造为流式。流式是前端的刚需，不是优化。

**3. 前端和后端同步开发，而非先后**

当前流程是先完成后端（Task 1-17），再做前端（Task 18）。这导致前端需要适配后端的接口，而不是前后端共同设计接口。如果重做，我会在 Task 17（FastAPI 服务器）之后立即做前端，然后通过实际使用发现接口问题。

**4. Task 颗粒度：拆分 AgentLoop**

AgentLoop 是最复杂的 task（130 行），subagent 需要两次修复。如果重做，我会拆成"主循环骨架"和"反馈回灌"两个 task。

**5. 用分支替代 worktree**

Windows 上 worktree 的符号链接权限问题导致 1 个测试 skip。分支更简单、更可靠。

### 不会改变的

**1. Brainstorming → SPEC → PLAN → TDD task 的流程**

这个流程的核心价值在于"把模糊想法变成精确规约"。即使重做，我仍然会花 1 小时做 brainstorming 和 SPEC，再花 30 分钟做 PLAN。

**2. 治理作为深入维度**

治理（护栏、HITL、范围围栏、审计日志）是最适合"机制必须是代码"要求的维度。纯函数、确定性、可测试——这些特性让 97 个测试不需要 LLM 就能验证核心价值。

**3. MockLLMClient 的设计**

MockLLMClient 返回预设动作序列，让整个 agent 循环可以确定性测试。这是"移除 LLM 后还剩什么"这个命题的关键支撑。

---

## 9. 对 Superpowers 方法论的批判

### Superpowers 假设了什么

**假设 1：人类（控制器）能准确判断 subagent 的实现质量**

Superpowers 的 subagent-driven 流程假设控制器可以审查 subagent 的输出并判断质量。在实践中，这大部分时候成立——我可以读 subagent 的代码和测试，判断是否正确。但当 subagent 的实现涉及我不熟悉的领域（如 asyncio 事件循环、Windows 符号链接权限）时，我的审查质量下降。subagent 自己修复了 asyncio 问题，但我无法判断它的修复是否最优。

**假设 2：SPEC 足够精确，subagent 不需要"创造性"**

Superpowers 假设如果 SPEC 足够好，subagent 只需要"执行"而非"创造"。这在大部分 task 上成立（护栏规则、工具实现、数据模型），但在集成层（AgentLoop、FastAPI 服务器）不成立——这些 task 需要 subagent 做设计决策（如 WebSocket 消息格式、步骤推送时机），而 SPEC 没有覆盖这些细节。

**假设 3：TDD 能防止 subagent 偏离**

TDD 确实防止了"功能偏离"（subagent 不会在护栏引擎里加入 SPEC 没有的功能），但无法防止"接口偏离"（subagent 选择了和 SPEC 不一致的函数签名）。TDD 验证的是行为，不是接口。

**假设 4：Skill 是通用的**

Superpowers 的技能（brainstorming、writing-plans、TDD 等）假设它们在任何项目上都适用。但 `using-git-worktrees` 在 Windows 上有问题，`requesting-code-review` 在 AI-only 流程中过重。技能需要根据项目环境适配，而非盲目加载。

### 这些假设在我的项目里成立吗？

| 假设 | 是否成立 | 说明 |
|------|---------|------|
| 控制器能判断质量 | 大部分成立 | 集成层和平台特定问题除外 |
| SPEC 足够精确 | Foundation/Tools 层成立 | 集成层不成立 |
| TDD 防止偏离 | 功能层面成立 | 接口层面不成立 |
| Skill 通用 | 不完全成立 | 需要按环境适配 |

### 核心批判

Superpowers 方法论的最大价值是**把"一个人写代码"变成"一个人设计规约 + 审查实现"**。这个转变是真实的、有价值的。但它的盲区在于：

1. **它优化了"实现"阶段，但没有优化"使用"阶段**。21 个 task 完成、97 个测试通过，不代表系统"好用"。用户体验问题（文件预览、实时反馈）只有在实际使用中才能发现，而 Superpowers 没有包含"使用后反思"的技能。

2. **它假设 SPEC 是"完成"的**。实际上 SPEC 是一个活文档——在使用过程中发现的问题应该回写进 SPEC。我在项目后期更新了 SPEC §3.15（前端规约）和 §8.1（设计系统），这些更新来自实际使用，而非 brainstorming。

3. **它的技能是"写代码"导向的**。brainstorming、writing-plans、TDD、subagent-driven 都是关于"如何写代码"的。但工程不只是写代码——还有"如何验证代码在真实场景下工作"、"如何从用户反馈中迭代"。这些在 Superpowers 中缺失。

### 最终评价

Superpowers 是一套**实现阶段的方法论**，在"从 SPEC 到可运行代码"这个区间内非常有效。但它不是全生命周期方法论——使用、反馈、迭代这些阶段需要额外的工具和流程。CodeGuard 项目的前 21 个 task（SPEC → 实现）受益于 Superpowers；后 6 个 commit（用户体验优化）受益于"亲自使用 + 反思"——这部分不在 Superpowers 的覆盖范围内。

如果 Superpowers 要进化，我最希望看到的是一个 `superpowers:dogfooding` 技能——强制开发者在"完成"后亲自使用系统，记录体验问题，回写 SPEC，再迭代。这比任何代码审查技能都更能发现真实问题。

---

*反思完毕。CodeGuard 的工程价值不在于 97 个测试，而在于"移除 LLM 后，治理机制仍然可用"这个命题被验证了。用户体验的价值不在于落地页有多好看，而在于"用户发送消息后 1 秒内看到反馈"这个体验被实现了。*
