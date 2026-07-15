# SPEC.md — CodeGuard：一个以治理为核心的 Coding Agent Harness

> AI4SE 期末 A 类项目 · Coding Agent Harness
>
> *Spec-Driven, Subagent-Built, Human-Owned.*

---

## 目录

1. [问题陈述](#1-问题陈述)
2. [用户故事](#2-用户故事)
3. [功能规约](#3-功能规约)
4. [非功能性需求](#4-非功能性需求)
5. [系统架构](#5-系统架构)
6. [数据模型](#6-数据模型)
7. [凭据与分发设计](#7-凭据与分发设计)
8. [技术选型与理由](#8-技术选型与理由)
9. [验收标准](#9-验收标准)
10. [风险与未决问题](#10-风险与未决问题)
11. [领域与机制设计](#11-领域与机制设计)

---

## 1. 问题陈述

### 1.1 要解决什么问题

当 LLM 能完成大部分"思考"时，工程师的价值落在 harness 这层工程上——治理、反馈、上下文、安全、分发。现有框架（LangChain、AutoGen、CrewAI 等）把 agent loop 封装成高层抽象，使用者无法触及或测试内部机制。一个护栏是否生效，取决于 LLM 是否遵从提示词，而非确定性代码。

本项目从零实现一个 Coding Agent Harness，让每个核心机制（工具分发、治理拦截、反馈回灌、记忆读写、停机判断）都是**可独立验证的代码**，而非提示词。

### 1.2 核心命题

> 移除真实 LLM 后，仓库里还剩多少可独立验证的工程？

CodeGuard 的回答是——全部核心机制都可用 mock LLM 单测验证。

### 1.3 目标用户

1. **AI4SE 课程学生**：通过阅读和修改 harness 内核，理解 agent 主循环、治理护栏、反馈闭环的工程实现。
2. **对 agent 工程感兴趣的开发者**：想要一个不依赖现成框架、可读、可改、可测的 harness 参考实现。

### 1.4 为什么值得做

- 现有 agent 框架是"黑箱"——机制藏在框架内部，使用者只能写提示词。
- CodeGuard 把每个机制变成可测试的 Python 函数/类，让"治理"从提示词变成确定性代码。
- 深入治理维度（护栏、沙箱、HITL 状态机、范围围栏），这是 agent 安全落地最关键的工程层。
- "用一个 harness（Superpowers）去造另一个 harness"，从而对这套方法论形成第一手的批判性理解。

---

## 2. 用户故事

遵循 INVEST 原则（Independent、Negotiable、Valuable、Estimable、Small、Testable）。

### US-1：发送编码任务

> 作为开发者，我想通过 Web 界面向 agent 发送编码任务（如"实现一个排序函数并写测试"），以便让 agent 自主完成编码工作。

**验收：** 用户在控制台输入任务描述，agent 开始执行主循环，前端实时展示步骤。

### US-2：查看 agent 实时执行过程

> 作为开发者，我想实时看到 agent 主循环的每一步（思考、工具调用、护栏决策、反馈），以便理解 agent 的行为并在需要时干预。

**验收：** 前端实时展示每一步的类型、内容、时间戳；步骤通过 WebSocket 推送，延迟 < 100ms。

### US-3：护栏拦截危险动作（治理核心）

> 作为开发者，当 agent 试图执行危险操作（如 `rm -rf`、写 `.env`、`git push --force`）时，我希望被护栏拦截并暂停等待我的确认，以防止不可逆破坏。

**验收：** 危险动作被拦截 → 前端弹出确认 → 用户 approve/deny → 仅 approve 后执行；deny 则跳过并回灌拒绝原因。mock LLM 下可确定性复现。

### US-4：测试反馈驱动自我修正

> 作为开发者，当 agent 写的代码测试失败时，我希望 agent 收到测试失败反馈并据此修正代码，直到测试通过或达到最大重试次数。

**验收：** TestValidator 解析测试输出 → FeedbackResult 回灌 → agent 修改代码 → 重新运行测试；mock LLM 下可确定性复现"收到失败→改变下一步动作"。

### US-5：安全配置 LLM 凭据

> 作为开发者，我想在首次运行时安全录入 LLM API key，并能查看状态/更新/清除，且 key 绝不硬编码或进入日志。

**验收：** 首次运行引导录入（隐藏输入）；查看状态显示 `configured: true/false` 不回显明文；key 存储在加密文件中；grep 仓库无明文 key。

### US-6：加载技能指导 agent 行为

> 作为开发者，我想通过编写 markdown 技能文件来约束/指导 agent 的行为（如"先写测试再写实现"），以便复用工作流。

**验收：** `skills/` 目录下的 markdown 被加载；SkillLoader 根据上下文匹配技能并注入 LLM；技能加载/匹配逻辑有单测。

### US-7：连接 MCP 外部工具

> 作为开发者，我想通过 MCP 协议连接外部工具服务（如 Open Design），让 agent 能使用更多工具。

**验收：** MCPToolAdapter 连接 MCP 服务器 → 发现工具 → 注册到 ToolDispatcher → agent 可调用这些工具；适配器连接逻辑有单测。

### US-8：跨会话记忆

> 作为开发者，我希望 agent 记住项目的编码约定和历史决策，在跨会话时不需要重新说明。

**验收：** MemoryStore 保存项目约定到 `.codeguard/memory.json`；新会话启动时加载；agent 主循环按需查询记忆而非全量载入。

---

## 3. 功能规约

按模块拆分，每项描述输入/行为/输出/边界条件/错误处理。

### 3.1 Agent 主循环（AgentLoop）

| 项 | 说明 |
|---|---|
| 输入 | 用户任务描述 + 配置（最大迭代次数、超时） |
| 行为 | 组织上下文 → 调 LLM → 解析动作 → 护栏检查 → 分发执行 → 回灌结果 → 停机判断 |
| 输出 | 每一步的 StepEvent（通过 WebSocket 推送） |
| 边界 | 最大迭代次数（默认 20）、超时（默认 300s）、LLM 返回无效动作时重试（最多 3 次） |
| 错误处理 | LLM 调用失败 → 重试 3 次后报错；工具执行异常 → 回灌错误信息让 agent 决定 |

主循环伪代码：

```python
async def run(self, task: str) -> None:
    context = self.memory.load_relevant(task)
    skills = self.skill_loader.match(context)
    messages = self.build_messages(task, context, skills)

    for iteration in range(self.max_iterations):
        response = self.llm_client.call(messages)
        action = self.parse_action(response)

        decision = self.guardrail_engine.check(action)
        if decision.level == DENY:
            messages.append(assistant(action))
            messages.append(system(f"Action denied: {decision.reason}"))
            continue
        elif decision.level == ASK:
            hitl_result = await self.hitl_manager.request(action)
            if hitl_result.state == DENIED:
                messages.append(system(f"User denied: {action.name}"))
                continue

        tool_result = self.tool_dispatcher.dispatch(action)
        self.audit_log.record(action, decision, tool_result)

        if action.name in ("run_tests", "run_lint"):
            feedback = self.feedback_validator.validate(action.name, tool_result)
            messages.append(system(feedback.to_message()))
            if feedback.success:
                break  # 停机：任务完成
        else:
            messages.append(tool(tool_result))

    self.memory.save_session(context)
```

### 3.2 LLM 抽象层（LLMClient）

| 项 | 说明 |
|---|---|
| 输入 | messages: list[Message]（role + content） |
| 行为 | 调用 OpenAI 兼容 API，返回 LLMResponse |
| 输出 | LLMResponse（content + tool_calls） |
| 边界 | 抽象基类，MockLLMClient 返回预设动作序列 |
| 错误处理 | 网络超时重试（3 次，指数退避）；API 错误码映射为异常 |

```python
class LLMClient(ABC):
    @abstractmethod
    async def call(self, messages: list[Message]) -> LLMResponse:
        ...

class RealLLMClient(LLMClient):
    """OpenAI 兼容 API 客户端"""
    async def call(self, messages: list[Message]) -> LLMResponse:
        # 使用 httpx 或 openai SDK 调用课程提供的 URL
        ...

class MockLLMClient(LLMClient):
    """返回预设动作序列，用于确定性单测"""
    def __init__(self, responses: list[LLMResponse]):
        self._responses = responses
        self._index = 0

    async def call(self, messages: list[Message]) -> LLMResponse:
        response = self._responses[self._index]
        self._index += 1
        return response
```

### 3.3 工具分发器（ToolDispatcher）

| 项 | 说明 |
|---|---|
| 输入 | Action（name + params） |
| 行为 | 根据 name 路由到对应 Tool，执行并返回结果 |
| 输出 | ToolResult（success + output + error） |
| 边界 | 未知工具名 → 返回错误；工具执行超时（默认 30s）→ 中断 |
| 错误处理 | 工具异常捕获，返回 ToolResult(success=False, error=...) |

```python
class ToolDispatcher:
    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def dispatch(self, action: Action) -> ToolResult:
        tool = self._tools.get(action.name)
        if tool is None:
            return ToolResult(success=False, error=f"Unknown tool: {action.name}")
        return tool.execute(action.params)
```

### 3.4 内置工具集

| 工具 | 输入 | 输出 | 边界 |
|------|------|------|------|
| ReadFile | path | 文件内容 | 路径必须在 workspace 内 |
| WriteFile | path, content | 成功/失败 | 路径必须在 workspace 内；敏感文件禁止 |
| EditFile | path, old, new | 成功/失败 | old 必须唯一匹配 |
| RunShell | command | stdout/stderr/exit_code | 命令经护栏检查 |
| RunTests | test_command | pass/fail/详情 | 解析 pytest/jest 输出 |
| RunLint | lint_command | error/warning | 解析 ruff/eslint 输出 |
| ListFiles | pattern | 路径列表 | 限制在 workspace 内 |
| SearchContent | pattern | 匹配行列表 | 限制在 workspace 内 |

每个工具实现统一接口：

```python
class Tool(ABC):
    name: str

    @abstractmethod
    def execute(self, params: dict) -> ToolResult:
        ...
```

### 3.5 治理引擎（GuardrailEngine）— 深入维度

| 项 | 说明 |
|---|---|
| 输入 | Action（name + params） |
| 行为 | 按规则集检测 → 返回 ALLOW/ASK/DENY + 原因 |
| 输出 | GuardrailDecision(level, reason, rule_id) |
| 边界 | 纯函数，无副作用，无需 LLM |
| 错误处理 | 未知动作类型默认 ASK |

**检测规则（确定性代码，非提示词）：**

| 规则 ID | 检测对象 | 模式 | 级别 |
|---------|---------|------|------|
| R001 | shell | `rm -rf` | DENY |
| R002 | shell | `git push --force` / `git push -f` | ASK |
| R003 | shell | `sudo` | ASK |
| R004 | shell | `curl \| sh` / `wget \| sh` / `curl \| bash` | DENY |
| R005 | shell | `docker rm` / `docker rmi` / `docker system prune` | ASK |
| R006 | file | 写入 workspace 外路径 | DENY |
| R007 | file | 读写 `.env` | DENY |
| R008 | file | 读写 `.git/` 目录 | DENY |
| R009 | file | 读写含 `credentials`/`secret`/`key`/`token` 的文件名 | ASK |
| R010 | shell | `npm publish` / `pip upload` / `twine upload` | ASK |
| R011 | shell | `git push`（非 force） | ASK |
| R012 | 任意 | 用户自定义规则（YAML 配置） | 可配置 |

```python
class GuardrailEngine:
    def __init__(self, rules: list[Rule]):
        self._rules = rules

    def check(self, action: Action) -> GuardrailDecision:
        for rule in self._rules:
            decision = rule.evaluate(action)
            if decision.level != ALLOW:
                return decision
        return GuardrailDecision(level=ALLOW, reason="No rule matched", rule_id="DEFAULT")
```

规则可配置：`config/guardrails.yaml` 声明额外规则。

### 3.6 HITL 状态机（HITLManager）— 深入维度

| 项 | 说明 |
|---|---|
| 输入 | GuardrailDecision(level=ASK) + Action |
| 行为 | 创建审批请求 → 暂停循环 → 等待用户 approve/deny → 转换状态 |
| 输出 | HITLState(pending/approved/denied/timeout) |
| 边界 | 超时（默认 60s）自动 deny；状态转换记录审计日志 |
| 错误处理 | WebSocket 断开 → 状态保持 pending，重连后可继续 |

状态转换：

```
PENDING → APPROVED → EXECUTING → COMPLETED
PENDING → DENIED → SKIPPED
EXECUTING → FAILED → (error feedback to agent)
PENDING → TIMEOUT → DENIED
```

```python
class HITLManager:
    def __init__(self, timeout: int = 60):
        self._timeout = timeout
        self._requests: dict[str, HITLRequest] = {}

    async def request(self, action: Action) -> HITLRequest:
        req = HITLRequest(id=uuid4(), action=action, state=PENDING)
        self._requests[req.id] = req
        # 通过 WebSocket 推送到前端，等待用户响应
        # 超时自动 deny
        return await self._wait_for_resolution(req)

    def resolve(self, request_id: str, decision: str) -> None:
        req = self._requests[request_id]
        req.state = APPROVED if decision == "approve" else DENIED
        req.resolved_at = datetime.now()
```

### 3.7 范围围栏（ScopeFence）— 深入维度

| 项 | 说明 |
|---|---|
| 输入 | path 或 command |
| 行为 | 检查是否在允许范围内 |
| 输出 | bool + reason |
| 边界 | workspace 根目录 + 白名单路径；命令白名单/黑名单 |
| 错误处理 | 路径解析失败（如符号链接逃逸）→ 拒绝 |

```python
class ScopeFence:
    def __init__(self, workspace_root: Path, allowed_paths: list[Path]):
        self._root = workspace_root.resolve()
        self._allowed = [p.resolve() for p in allowed_paths]

    def check_path(self, path: str) -> tuple[bool, str]:
        target = (self._root / path).resolve()
        # 防止符号链接逃逸
        if not str(target).startswith(str(self._root)):
            return False, f"Path escapes workspace: {target}"
        return True, "OK"
```

### 3.8 审计日志（AuditLog）— 深入维度

| 项 | 说明 |
|---|---|
| 输入 | AuditEntry(timestamp, action, params, decision, result) |
| 行为 | 追加写入 `.codeguard/audit.log`（JSONL 格式） |
| 输出 | 可查询的日志记录 |
| 边界 | 日志中不得出现明文凭据（参数脱敏） |
| 错误处理 | 写入失败 → 降级到 stderr，不阻断主循环 |

```python
class AuditLog:
    def record(self, action: Action, decision: GuardrailDecision, result: ToolResult) -> None:
        entry = AuditEntry(
            timestamp=datetime.now(),
            action_name=action.name,
            params=self._sanitize(action.params),  # 脱敏
            decision=decision.level,
            result=result.output[:500] if result.output else None,
        )
        # 追加写入 JSONL
        with open(self._log_path, "a") as f:
            f.write(entry.to_json() + "\n")

    def _sanitize(self, params: dict) -> dict:
        """脱敏：将 key/secret/token 值替换为 ***"""
        ...
```

### 3.9 反馈验证器（FeedbackValidators）

| 验证器 | 输入 | 输出 | 边界 |
|--------|------|------|------|
| TestValidator | 测试命令输出 | FeedbackResult(success, details, failures) | 解析 pytest/jest 格式 |
| LintValidator | lint 命令输出 | FeedbackResult(success, errors, warnings) | 解析 ruff/eslint 格式 |
| TypeCheckValidator | 类型检查输出 | FeedbackResult(success, errors) | 解析 mypy/tsc 格式 |

```python
class TestValidator:
    def validate(self, output: str, exit_code: int) -> FeedbackResult:
        if exit_code == 0:
            return FeedbackResult(success=True, details="All tests passed")
        failures = self._parse_failures(output)
        return FeedbackResult(success=False, details=output, failures=failures)
```

### 3.10 记忆模块（MemoryStore）

| 项 | 说明 |
|---|---|
| 输入 | key / query |
| 行为 | 读写 `.codeguard/memory.json` |
| 输出 | 记忆条目 |
| 边界 | 按需查询，不全量载入；文件大小限制（默认 1MB） |
| 错误处理 | 文件损坏 → 降级为空记忆，不阻断 |

### 3.11 技能加载器（SkillLoader）

| 项 | 说明 |
|---|---|
| 输入 | 上下文（任务描述、当前步骤） |
| 行为 | 从 `skills/` 加载 markdown → 匹配相关技能 → 返回指令 |
| 输出 | list[Skill(name, trigger, instructions)] |
| 边界 | 技能文件格式错误 → 跳过该技能并警告 |
| 错误处理 | 目录不存在 → 返回空列表 |

技能文件格式（markdown）：

```markdown
---
name: tdd-workflow
trigger: test, tdd, red-green
---

## 指令

1. 先写失败测试
2. 运行测试确认红色
3. 写最少代码使其变绿
4. 重构
```

### 3.12 MCP 工具适配器（MCPToolAdapter）

| 项 | 说明 |
|---|---|
| 输入 | MCP 服务器配置（URL/命令） |
| 行为 | 连接 MCP 服务器 → 发现工具 → 注册到 ToolDispatcher |
| 输出 | 注册的 Tool 列表 |
| 边界 | 连接失败 → 跳过该服务器并警告 |
| 错误处理 | 超时 → 降级，不阻断启动 |

```python
class MCPToolAdapter:
    def __init__(self, tool_dispatcher: ToolDispatcher):
        self._dispatcher = tool_dispatcher

    async def connect(self, server_config: MCPServerConfig) -> list[Tool]:
        # 连接 MCP 服务器
        # 发现工具列表
        # 包装为 Tool 适配器
        # 注册到 ToolDispatcher
        tools = await self._discover_tools(server_config)
        for tool in tools:
            self._dispatcher.register(tool)
        return tools
```

### 3.13 凭据管理器（CredentialManager）

| 项 | 说明 |
|---|---|
| 输入 | 操作（store/get/update/clear）+ key 名称 |
| 行为 | 安全存储/读取/更新/清除 API key |
| 输出 | get 返回 key（仅内部使用）；status 返回 bool |
| 边界 | 绝不回显明文到日志/终端；查看状态只返回 configured: bool |
| 错误处理 | 主密码错误 → 拒绝；存储损坏 → 引导重新录入 |

```python
class CredentialManager:
    def __init__(self, storage_path: Path):
        self._path = storage_path
        self._fernet: Fernet | None = None  # 解锁后设置

    def unlock(self, master_password: str) -> bool:
        key = derive_key(master_password)
        self._fernet = Fernet(key)
        return self._verify()

    def store(self, key_name: str, value: str) -> None:
        encrypted = self._fernet.encrypt(value.encode())
        self._write_entry(key_name, encrypted)

    def get(self, key_name: str) -> str | None:
        encrypted = self._read_entry(key_name)
        if encrypted is None:
            return None
        return self._fernet.decrypt(encrypted).decode()

    def status(self, key_name: str) -> bool:
        return self._entry_exists(key_name)

    def clear(self, key_name: str) -> None:
        self._delete_entry(key_name)
```

### 3.14 API 服务器（FastAPI）

| 端点 | 方法 | 说明 |
|------|------|------|
| `/api/session` | POST | 创建新会话 |
| `/api/session/{id}/message` | POST | 发送任务 |
| `/api/session/{id}/approve` | POST | 审批 HITL 请求 |
| `/api/session/{id}/history` | GET | 获取历史步骤 |
| `/api/credentials/status` | GET | 查看凭据状态 |
| `/api/credentials/setup` | POST | 首次设置凭据 |
| `/api/skills` | GET | 列出已加载技能 |
| `/api/memory` | GET | 查看记忆内容 |
| `/ws/session/{id}` | WS | 实时步骤推送 + HITL 请求 |

### 3.15 前端（React + Vite）

前端采用**双视图架构**：落地页（Landing Page）+ 应用控制台（App Console），统一深色主题设计系统。

#### 3.15.1 设计系统与工具链

| 项 | 说明 |
|---|---|
| **设计工具** | Open Design（od CLI MCP 服务，v0.14.1） |
| **生成 Agent** | Claude Code（通过 Open Design `start_run` 调度） |
| **设计系统** | Open Design 内置深色主题（Dark Theme），靛蓝/紫色 accent 色系 |
| **Skill** | 未使用预置 Skill（`skills` 列表为空），通过 `start_run` prompt 直接描述设计需求 |
| **字体** | SF Pro Display（标题）/ SF Pro Text（正文）/ JetBrains Mono（代码） |
| **CSS 变量** | 提取为共享 `styles.css`，落地页与应用页共用同一套设计 token |

#### 3.15.2 Open Design 生成流程

1. **启动守护进程**：通过 Electron 二进制 + `ELECTRON_RUN_AS_NODE=1` 环境变量启动 Open Design daemon（监听 `127.0.0.1:7456`）
2. **创建项目**：`open-design_create_project` 创建 `codeguard-frontend` 项目
3. **启动生成**：`open-design_start_run` 指定 `agent: "claude"`，prompt 描述落地页需求（英雄区、功能卡片、聊天演示、工作流、CTA）
4. **轮询状态**：`open-design_get_run` 每 30-60s 轮询，Claude Code agent 在 5-30 分钟内完成生成
5. **获取产物**：`open-design_get_artifact` 获取生成的 `index.html`（25KB，含完整内联 CSS）
6. **集成到 React**：将 HTML 转为 `LandingPage.tsx` 组件，提取 CSS 变量到 `styles.css`

#### 3.15.3 组件清单

| 组件 | 功能 | 后端 API |
|------|------|----------|
| LandingPage | 落地页（英雄区/功能卡片/聊天演示/工作流/CTA） | 无（纯展示，"查看演示"按钮切换到应用页） |
| App.tsx | 路由切换 + session 管理 + WebSocket 连接 | `POST /api/session`、`GET /api/credentials/status` |
| ChatPanel | 深色主题聊天面板，消息列表 + 输入框 | `POST /api/session/{id}/message` + WebSocket |
| StepTimeline | 步骤时间线，7 种步骤类型颜色标识 | WebSocket `onStep` 回调 |
| HITLDialog | 模态审批对话框（批准/拒绝） | `POST /api/session/{id}/approve` |
| useWebSocket | WebSocket hook，支持 onStep/onHITL/onConnected/onDone | `WS /ws/session/{id}` |

#### 3.15.4 设计 Token（CSS 变量）

```css
:root {
  --bg: #0a0b14;              /* 主背景 */
  --bg-raised: #11131f;       /* 次背景 */
  --surface: #161825;         /* 卡片背景 */
  --fg: #e8eaf0;              /* 主文字 */
  --fg-dim: #a0a4b8;          /* 次文字 */
  --accent: #7c5cf0;          /* 主强调色（靛蓝） */
  --accent-2: #a78bfa;        /* 次强调色（紫色） */
  --gradient-accent: linear-gradient(135deg, #7c5cf0, #6366f1, #8b5cf6);
  --radius: 12px;             /* 圆角 */
  --font-display: 'SF Pro Display', ...;
  --font-mono: 'JetBrains Mono', ...;
}
```

#### 3.15.5 前端-后端 API 对接

| 前端按钮/交互 | 后端端点 | 方法 |
|---------------|---------|------|
| "查看演示"/"进入控制台" | `POST /api/session` | 创建会话 + 连接 WebSocket |
| 聊天输入框发送 | `POST /api/session/{id}/message` | 发送编码任务 |
| WebSocket 实时步骤 | `WS /ws/session/{id}` | 接收 step/hitl/done/error 事件 |
| HITL 批准/拒绝 | `POST /api/session/{id}/approve` | 人工审批决策 |
| 顶栏 LLM 状态 | `GET /api/credentials/status` | 显示 LLM 配置状态 |

---

## 4. 非功能性需求

### 4.1 性能

- Agent 主循环单步延迟 < 5s（不含 LLM 响应时间）
- WebSocket 消息推送延迟 < 100ms
- Mock LLM 下完整循环（10 步）< 1s
- MemoryStore 查询 < 10ms

### 4.2 安全

- 凭据安全存储（加密文件 + 主密码），详见 [§7](#7-凭据与分发设计)
- 路径沙箱：所有文件操作限制在 workspace 内
- 敏感文件保护：`.env`、`.git/`、`credentials` 等禁止读写
- 审计日志脱敏：key 值替换为 `***`
- CI 扫描：GitHub Actions 中 grep 检查明文 key 模式

### 4.3 可用性

- 首次运行引导式配置（主密码 + API key 录入）
- 前端实时展示每一步，用户随时可干预
- HITL 请求有视觉提示（弹窗）

### 4.4 可观测性

- 每步 StepEvent 推送到前端
- AuditLog 记录所有动作（含拦截）
- Agent 状态可查询（当前步骤、迭代次数、耗时）
- 错误信息结构化（error_code + message + context）

---

## 5. 系统架构

### 5.1 组件图

```
┌───────────────────────────────────────────────────────────┐
│                    React Frontend                          │
│              (Agent 交互控制台 + Vite)                      │
└──────────────────────┬────────────────────────────────────┘
                       │ WebSocket (实时流) + REST (动作)
┌──────────────────────▼────────────────────────────────────┐
│                  FastAPI Server                            │
│              (REST 端点 + WebSocket hub)                   │
└──────────────────────┬────────────────────────────────────┘
                       │
┌──────────────────────▼────────────────────────────────────┐
│                  Agent Main Loop                           │
│  (组织上下文 → 调LLM → 解析动作 → 护栏检查 → 分发 →        │
│   回灌结果 → 停机判断)                                     │
└──┬─────┬─────┬─────┬─────┬─────┬─────┬─────┬────────────┘
   │     │     │     │     │     │     │     │
   ▼     ▼     ▼     ▼     ▼     ▼     ▼     ▼
┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐┌─────┐
│LLM  ││Guard││Tool ││Feed-││Mem- ││Skill││Cred ││MCP  │
│Client││Engine││Disp││back ││ory  ││Loader││Mgr ││Adapt│
└──┬──┘└─────┘└──┬──┘└─────┘└─────┘└─────┘└─────┘└──┬──┘
   │              │                                    │
   │              │  ┌──────────┐    ┌──────────┐     │
   │              │  │ Built-in │    │ MCP Tools│     │
   │              │  │ Tools    │    │ (外部服务)│     │
   │              │  │read/write│    └──────────┘     │
   │              │  │/shell/   │                      │
   │              │  │test/lint │                      │
   │              │  └──────────┘                      │
   │              └────────────┘                       │
   ▼                                                   ▼
┌──────┐                                        ┌──────────┐
│ LLM  │                                        │ MCP      │
│Provider│                                      │ Servers  │
└──────┘                                        │(Open     │
                                                │Design等) │
                                                └──────────┘
```

### 5.2 数据流

1. 用户通过 WebSocket 发送任务
2. AgentLoop 从 MemoryStore 加载相关上下文 + SkillLoader 匹配相关技能注入上下文
3. AgentLoop 调用 LLMClient → LLM 返回下一步动作
4. 动作进入 GuardrailEngine：`ALLOW` → 直接执行；`ASK` → HITLManager 暂停，通过 WebSocket 请求用户确认；`DENY` → 拒绝并回灌拒绝原因
5. 用户确认后（如 approved）→ ToolDispatcher 路由（内置工具或 MCP 工具）→ 执行 → 返回 ToolResult
6. 若动作是 test/lint → FeedbackValidator 解析结果 → FeedbackResult 回灌给 AgentLoop
7. AgentLoop 判断：继续（带反馈再调 LLM）或停机（任务完成）
8. 全程每一步通过 WebSocket 实时推送到前端 + 审计日志记录

### 5.3 外部依赖

| 依赖 | 说明 |
|------|------|
| LLM 供应商 | 课程提供的 OpenAI 兼容 API |
| MCP 服务器 | Open Design (od CLI) 等外部工具服务 |
| 文件系统 | workspace 沙箱目录 |
| Shell | 执行命令、测试、lint |
| Python 3.12+ | 运行时 |
| npm/Node 20+ | 前端构建（构建时，非运行时） |

### 5.4 模块边界与可测试性

| 模块 | 接口 | 可测试性 |
|------|------|----------|
| LLMClient | 抽象基类，MockLLMClient 返回预设动作 | mock |
| GuardrailEngine | `check(action) -> decision` | 纯函数 |
| ToolDispatcher | `dispatch(action) -> ToolResult` | mock 工具 |
| MCPToolAdapter | `connect(config) -> list[Tool]` | mock MCP 服务器 |
| FeedbackValidator | `validate(output) -> FeedbackResult` | 纯函数 |
| MemoryStore | `load/save/query` | mock 文件系统 |
| SkillLoader | `load() / match(context)` | mock 目录 |
| HITLManager | `request(action) / resolve(id, decision)` | mock WebSocket |
| ScopeFence | `check_path(path) -> (bool, str)` | 纯函数 |
| AuditLog | `record(action, decision, result)` | mock 文件 |
| CredentialManager | `store/get/status/clear` | mock 文件 |
| AgentLoop | 注入 mock LLM + mock 工具 | 验证循环逻辑 |

---

## 6. 数据模型

### 6.1 核心实体关系

```
Session 1───* Step 1───1 Action 1───1 GuardrailDecision
  │                  │           │
  │                  │           *───1 ToolResult
  │                  │
  │                  *───0..1 FeedbackResult
  │                  *───0..1 HITLRequest
  │
  *───* Message
```

### 6.2 实体定义

**Session（会话）**

| 字段 | 类型 | 约束 |
|------|------|------|
| id | str (UUID) | PK |
| created_at | datetime | 非空 |
| status | enum(active/completed/failed) | 非空 |
| workspace | str | 非空，绝对路径 |
| config | JSON | 最大迭代次数、超时等 |

**Message（消息）**

| 字段 | 类型 | 约束 |
|------|------|------|
| id | str (UUID) | PK |
| session_id | str | FK → Session |
| role | enum(user/assistant/system) | 非空 |
| content | str | 非空 |
| created_at | datetime | 非空 |

**Step（步骤）**

| 字段 | 类型 | 约束 |
|------|------|------|
| id | str (UUID) | PK |
| session_id | str | FK → Session |
| step_index | int | 非空，会话内递增 |
| type | enum(think/action/tool_call/guardrail/feedback/hitl/result) | 非空 |
| content | JSON | 步骤内容（结构化） |
| created_at | datetime | 非空 |

**Action（动作）**

| 字段 | 类型 | 约束 |
|------|------|------|
| name | str | 非空（工具名） |
| params | JSON | 工具参数 |
| raw_llm_output | str | LLM 原始输出（调试用） |

**GuardrailDecision（护栏决策）**

| 字段 | 类型 | 约束 |
|------|------|------|
| level | enum(ALLOW/ASK/DENY) | 非空 |
| reason | str | 非空 |
| rule_id | str | 触发的规则 ID |

**ToolResult（工具结果）**

| 字段 | 类型 | 约束 |
|------|------|------|
| success | bool | 非空 |
| output | str | stdout/结果 |
| error | str? | 错误信息（可选） |
| exit_code | int? | 退出码（shell 类） |

**HITLRequest（人工审批请求）**

| 字段 | 类型 | 约束 |
|------|------|------|
| id | str (UUID) | PK |
| action | Action | 非空 |
| state | enum(pending/approved/denied/timeout) | 非空 |
| created_at | datetime | 非空 |
| resolved_at | datetime? | 解决时间 |
| resolved_by | str? | 解决者 |

**FeedbackResult（反馈结果）**

| 字段 | 类型 | 约束 |
|------|------|------|
| validator | enum(test/lint/typecheck) | 非空 |
| success | bool | 非空 |
| details | str | 详细信息 |
| failures | list[Failure] | 失败项列表 |
| suggestions | list[str] | 建议 |

**MemoryEntry（记忆条目）**

| 字段 | 类型 | 约束 |
|------|------|------|
| key | str | PK |
| category | enum(convention/decision/knowledge/session) | 非空 |
| value | str | 非空 |
| updated_at | datetime | 非空 |

**Skill（技能）**

| 字段 | 类型 | 约束 |
|------|------|------|
| name | str | PK |
| trigger | str | 匹配条件（关键词/正则） |
| instructions | str | 指令内容（markdown） |
| file_path | str | 源文件路径 |

**AuditEntry（审计日志）**

| 字段 | 类型 | 约束 |
|------|------|------|
| timestamp | datetime | 非空 |
| action_name | str | 非空 |
| params | JSON | **脱敏后**存储 |
| decision | enum(allow/ask/deny/approved/denied/executed/failed) | 非空 |
| result | str? | 执行结果摘要 |

### 6.3 存储方式

| 数据 | 存储 | 格式 |
|------|------|------|
| Session/Step/Message | 内存 + 可选持久化 | SQLite（可选） |
| MemoryEntry | `.codeguard/memory.json` | JSON |
| AuditEntry | `.codeguard/audit.log` | JSONL |
| Skill | `skills/*.md` | Markdown |
| 凭据 | `.codeguard/credentials.enc` | Fernet 加密 |

### 6.4 约束

- Session 内 Step 的 step_index 单调递增
- AuditEntry 的 params 必须脱敏（`.env` 内容、key 值替换为 `***`）
- MemoryEntry 总大小限制 1MB
- HITLRequest 超时 60s 自动转为 denied
- 凭据文件权限 600（仅 owner 可读写）

---

## 7. 凭据与分发设计

### 7.1 凭据威胁模型

| 威胁 ID | 威胁描述 | 风险等级 | 对策 |
|---------|---------|---------|------|
| T01 | Key 硬编码进源码 | 高 | CredentialManager 统一管理；CI 中 grep 扫描 |
| T02 | Key 提交进 Git 历史 | 高 | `.gitignore` 排除凭据文件；pre-commit hook 检查 |
| T03 | Key 写入日志/终端 | 高 | AuditEntry 参数脱敏；logging filter 过滤 |
| T04 | Key 进入 shell history | 中 | 禁止命令行 `export`；用 `.env` 或交互式录入 |
| T05 | Key 在进程环境中可见 | 中 | 优先用加密文件；env var 作为降级方案并文档说明风险 |
| T06 | Key 从磁盘被窃取 | 中 | 加密文件存储（Fernet 对称加密 + 主密码） |
| T07 | API 调用中 key 被截获 | 中 | 强制 HTTPS；不在 URL 中传 key |
| T08 | Docker 镜像泄露 key | 高 | Dockerfile 不含 key；运行时通过加密文件或 env 注入 |

### 7.2 凭据存储方案

**主方案：加密文件 + 主密码**

- 文件路径：`.codeguard/credentials.enc`
- 使用 `cryptography.fernet.Fernet` 对称加密
- 主密码通过 `getpass`（隐藏输入）获取，不回显
- 加密文件存储 key-value 对（如 `llm_api_key=xxx`）
- 首次运行：引导用户设置主密码 + 录入 API key
- 主密码不存储（仅内存中持有）
- 文件权限 600

**降级方案：环境变量（.env 文件）**

- 从 `.env` 文件加载（`python-dotenv`）
- 文档明确说明：`.env` 为明文、进程环境可见，风险高于加密文件
- 适用于 CI/CD 等无交互场景

### 7.3 凭据生命周期

```
首次运行 → 引导录入（getpass 隐藏输入）→ 加密存储
    ↓
查看状态 → "configured: true" （不回显明文）
    ↓
更新 → 验证主密码 → 解密 → 更新 → 重新加密
    ↓
清除 → 验证主密码 → 删除加密文件
```

**API：**

- `CredentialManager.unlock(master_password) -> bool` — 解锁
- `CredentialManager.store(key_name, value)` — 加密存储
- `CredentialManager.get(key_name) -> str` — 解密读取（仅内部使用）
- `CredentialManager.status(key_name) -> bool` — 查看是否已配置（不回显）
- `CredentialManager.update(key_name, new_value)` — 更新
- `CredentialManager.clear(key_name)` — 清除

### 7.4 分发设计

**形态：** Docker 容器（单镜像）

**Dockerfile 结构：**

```dockerfile
# 构建阶段：前端
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# 构建阶段：后端
FROM python:3.12-slim AS backend-builder
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e .
COPY src/ ./src/

# 运行阶段
FROM python:3.12-slim
WORKDIR /app
COPY --from=backend-builder /app /app
COPY --from=frontend-builder /frontend/dist /app/static
RUN useradd -m codeguard && chown -R codeguard:codeguard /app
USER codeguard
EXPOSE 8000
CMD ["python", "-m", "codeguard", "serve"]
```

**获取与运行：**

```bash
# 拉取镜像
docker pull ghcr.io/<user>/codeguard:latest

# 首次运行：交互式配置 key
docker run -it -p 8000:8000 -v codeguard-data:/data codeguard:latest init

# 正常运行
docker run -p 8000:8000 -v codeguard-data:/data -v /path/to/workspace:/workspace codeguard:latest serve
```

**目标平台：**

- Linux x86_64（主要）
- macOS ARM64（通过 Docker Desktop）
- Windows x86_64（通过 Docker Desktop）

**已知限制：**

- 需要安装 Docker
- workspace 需要挂载到容器内（`-v /path/to/workspace:/workspace`）
- MCP 服务器需在容器内可访问
- 容器内无系统钥匙串，凭据用加密文件方案
- 前端构建需要 Node 20+（仅构建时）

### 7.5 key 在目标机器上的安全配置方式

1. `docker pull <image>` 获取镜像
2. `docker run -it ... codeguard init` 交互式引导录入 key
3. Key 加密后存储在挂载的 volume 中（`-v codeguard-data:/data`）
4. 后续运行：`docker run -v codeguard-data:/data ... codeguard serve`
5. 或通过 env var：`docker run -e LLM_API_KEY=xxx ...`（文档说明明文风险）
6. 查看状态：`docker run ... codeguard credentials status` → 输出 `configured: true/false`

---

## 8. 技术选型与理由

| 选型 | 理由 |
|------|------|
| Python 3.12 | LLM 生态最成熟；pytest 测试框架强大；AI4SE 课程上下文 |
| FastAPI | 原生 async + WebSocket；自动 OpenAPI 文档；类型安全 |
| React + Vite | 组件生态丰富；Vite 构建快；Open Design 生成 React 组件 |
| cryptography (Fernet) | 标准库级信任度；对称加密简单可靠 |
| pytest | TDD 首选；fixture/parametrize 强大；mock 简单 |
| Docker | 自包含分发；跨平台一致；CI 中构建 |
| OpenAI 兼容 API | 课程提供；SDK 成熟；mock 简单 |
| Open Design (od CLI MCP) | 课程要求；MCP 协议集成；设计系统统一 |

### 8.1 前端设计系统

前端 UI 使用 **Open Design**（od CLI MCP 服务，v0.14.1）进行界面开发，满足作业要求"凡涉及前端 / UI，强烈推荐使用 Open Design 进行界面开发，并在 SPEC 中说明所选设计系统与 skill"。

**所选设计系统：** Open Design 内置深色主题（Dark Theme），靛蓝/紫色 accent 色系。

**所选 Skill：** 项目生成时 Open Design 的 Skills 列表为空（`skills: []`），因此未使用预置 Skill。通过 `open-design_start_run` 直接以 prompt 描述设计需求，由 Claude Code agent 自主完成生成。

**生成流程：**

1. 启动 Open Design daemon（Electron 二进制 + `ELECTRON_RUN_AS_NODE=1`，监听 `127.0.0.1:7456`）
2. `open-design_create_project` 创建项目 `codeguard-frontend`
3. `open-design_start_run(agent="claude", prompt=...)` 启动生成
4. Claude Code agent 在约 3 分钟内生成 25KB 的 `index.html`（含完整内联 CSS）
5. `open-design_get_artifact` 获取产物，转为 React 组件集成到项目

**生成结果（Claude Code 自检报告）：**

- Anti-slop 检查通过（无紫色渐变滥用、无通用 emoji 图标堆叠、无虚假指标）
- 5 维评分：哲学 4/5 · 层级 4/5 · 执行 4/5 · 特异性 5/5 · 克制 4/5
- 包含模块：导航栏、英雄区、功能卡片（Guardrails/HITL/Scope Fence/Audit Log）、聊天演示面板、工作流步骤、CTA + Footer

**集成方式：** 落地页 HTML 转为 `LandingPage.tsx` React 组件，CSS 变量提取到共享 `styles.css`，应用页组件（ChatPanel/StepTimeline/HITLDialog）复用同一套设计 token，确保视觉一致性。所有应用页按钮均对接后端 API（详见 §3.15.5）。

---

## 9. 验收标准

### 9.1 核心机制验收（mock LLM 单测）

| 机制 | 验收标准 | 验证方式 |
|------|---------|---------|
| Agent 主循环 | mock LLM 返回预设动作序列，循环按预期执行并停机 | pytest: 注入 MockLLMClient，断言步骤序列 |
| LLM 抽象层 | MockLLMClient 可替换真实 LLM，接口一致 | pytest: 同一 AgentLoop 用 mock/真实 LLM 均可运行 |
| 工具分发 | 传入 Action(name="read_file", params=...)，返回正确 ToolResult | pytest: 各工具单测 |
| 护栏引擎 | `check(Action(command="rm -rf /"))` 返回 DENY | pytest: 12 条规则逐一测试 |
| HITL 状态机 | ASK 动作 → pending → approve → executed；deny → skipped | pytest: 状态转换逐一测试 |
| 范围围栏 | workspace 外路径 → 拒绝；符号链接逃逸 → 拒绝 | pytest: 路径边界测试 |
| 反馈闭环 | 注入测试失败 → FeedbackResult 回灌 → agent 改变下一步 | pytest: mock LLM 验证反馈驱动 |
| 记忆模块 | 保存 → 加载 → 查询 → 清除 | pytest: MemoryStore CRUD |
| 技能加载 | 放入 markdown 技能 → 加载 → 匹配 → 注入上下文 | pytest: SkillLoader 单测 |
| MCP 适配 | mock MCP 服务器 → 发现工具 → 注册到 ToolDispatcher | pytest: MCPToolAdapter 单测 |
| 审计日志 | 动作执行后 → audit.log 有记录 → params 已脱敏 | pytest: 检查日志格式和脱敏 |

### 9.2 机制演示（A.6 要求）

提交一个可重复运行的演示脚本 `demo/mechanism_demo.py`，在 mock LLM 下确定性复现：

1. **护栏拦截**：agent 试图执行 `rm -rf /tmp/test` → 护栏返回 DENY → 动作被跳过 → 审计日志记录
2. **反馈闭环**：agent 写的代码测试失败 → TestValidator 解析 → FeedbackResult 回灌 → agent 修改代码 → 重新测试通过
3. **治理深度行为**：agent 试图写入 workspace 外路径 → ScopeFence 拒绝 → agent 收到拒绝原因 → 改为 workspace 内路径 → 成功

### 9.3 功能验收

| 功能 | 验收标准 |
|------|---------|
| Web 界面 | 浏览器访问 → 可发送任务 → 实时看到步骤 → HITL 弹窗可用 |
| 凭据管理 | 首次运行引导录入 → 状态查看不回显 → 更新/清除可用 |
| Docker 分发 | `docker build` + `docker run` 可启动 → key 安全配置 → agent 可运行 |
| CI | GitHub Actions push → 自动运行测试 → unit-test job pass |
| 测试覆盖 | `make test` 一键运行 → 核心机制覆盖 |

### 9.4 安全验收

| 验收项 | 标准 |
|--------|------|
| 无硬编码 key | `grep -r "sk-" src/` 无结果 |
| 无 key 在 Git | `.gitignore` 排除凭据文件 |
| 无 key 在日志 | 审计日志 params 脱敏 |
| 无 key 在终端 | 查看状态只返回 bool |

---

## 10. 风险与未决问题

### 10.1 技术风险

| 风险 ID | 风险描述 | 影响 | 缓解措施 |
|---------|---------|------|---------|
| R01 | LLM 输出格式不稳定，动作解析失败 | agent 循环中断 | 解析器容错 + 重试机制；定义严格的输出 schema |
| R02 | MCP 服务器实现差异导致适配失败 | 外部工具不可用 | 适配器层做兼容处理；连接失败降级不阻断 |
| R03 | Docker 内文件权限问题 | 工具执行失败 | Dockerfile 中设置正确用户/权限；workspace 挂载权限 |
| R04 | WebSocket 长连接断开 | 前端丢失实时状态 | 断线重连 + 历史步骤补发 |
| R05 | 测试框架输出格式多样 | FeedbackValidator 解析失败 | 支持主流格式（pytest/jest）；未知格式降级为原始输出 |
| R06 | 护栏规则不完备 | 遗漏危险动作 | 可配置规则（YAML）；社区可扩展 |
| R07 | 前端实时展示复杂度高 | 开发周期延长 | 分阶段实现：先文本流 → 再结构化展示 |
| R08 | 加密文件主密码丢失 | 凭据不可恢复 | 引导时提示备份；文档说明无法恢复 |

### 10.2 流程风险

| 风险 ID | 风险描述 | 缓解措施 |
|---------|---------|---------|
| P01 | subagent 对 SPEC 理解偏差 | 冷启动验证（§4.5）；task 颗粒度细 + 验证步骤明确 |
| P02 | TDD 在 mock LLM 场景下可能被绕过 | 测试必须先红再绿；CI 强制检查 |
| P03 | 前端与后端并行开发时接口不一致 | 先定义 API schema（OpenAPI）→ 前后端各自 mock |
| P04 | Docker 镜像构建环境与开发环境不一致 | CI 中构建镜像并运行测试 |

### 10.3 未决问题

1. **LLM 输出格式**：倾向让 LLM 返回 JSON 结构化动作（更可靠），需在 system prompt 中明确 schema。具体 schema 在 PLAN 阶段确定。
2. **会话持久化**：Session/Step 是否需要持久化到 SQLite？当前设计为内存 + 可选持久化，MVP 阶段先用内存，后续按需加 SQLite。
3. **多会话支持**：后端支持多会话（通过 session_id），前端 MVP 阶段单 tab，后续可扩展多 tab。
4. **MCP 服务器配置**：通过 `config/mcp_servers.yaml` 配置要连接的 MCP 服务器列表。

---

## 11. 领域与机制设计

> 本节为 A 类项目额外要求（§A.5），说明 coding 领域的四类机制设计及深入维度选择。

### 11.1 动作 / 工具

Coding 领域的 agent 需要执行的操作：

- **读写文件**：read_file、write_file、edit_file、list_files、search_content
- **执行命令**：run_shell（执行任意 shell 命令）
- **运行测试**：run_tests（运行测试套件，解析结果）
- **运行 lint**：run_lint（运行 linter，解析结果）

每个工具是一个 Python 类，实现统一接口 `Tool.execute(params) -> ToolResult`。工具分发器（ToolDispatcher）根据 LLM 返回的动作名路由到对应工具。工具来源可以是内置的，也可以通过 MCP 适配器从外部 MCP 服务器注册。

### 11.2 客观反馈信号

Coding 领域的反馈信号是**确定性代码**，不是提示词：

- **TestValidator**：运行测试命令 → 解析输出 → 提取 pass/fail 数量、失败详情 → 回灌给 agent
- **LintValidator**：运行 lint → 解析输出 → 提取 error/warning → 回灌
- **TypeCheckValidator**：运行类型检查 → 解析输出 → 回灌

每个 validator 实现 `validate(output, exit_code) -> FeedbackResult`，FeedbackResult 包含 `success: bool`、`details: str`、`failures: list`、`suggestions: list`。agent 主循环收到 FeedbackResult 后决定是否重试。

这些信号客观、确定、可回灌——不依赖 LLM 的"自我检查"，而是用代码解析测试/lint 的真实输出。

### 11.3 危险动作

Coding 领域的危险动作及治理：

- **Shell 命令**：`rm -rf`（DENY）、`git push --force`（ASK）、`sudo`（ASK）、`curl | sh`（DENY）
- **文件操作**：写入 workspace 外路径（DENY）、读写 `.env`（DENY）、读写 `.git/`（DENY）
- **对外发布**：`npm publish`、`pip upload`（ASK）

治理引擎（GuardrailEngine）是一个纯函数 `check(action) -> GuardrailDecision`，按规则集检测并返回 ALLOW/ASK/DENY。规则是确定性代码（正则匹配、路径检查），不是提示词。

### 11.4 记忆

Coding 领域的跨会话记忆需求：

- **项目约定**：编码风格、测试框架、构建命令
- **历史决策**：为什么选择某方案（按 task 记录）
- **代码库知识**：文件结构、关键模块入口
- **会话记忆**：当前任务上下文、之前的工具结果

记忆存储在 `.codeguard/memory.json`，按需检索（不全量载入）。agent 主循环根据当前步骤查询相关记忆。

### 11.5 深入维度：治理

**选择治理作为深入维度的理由：**

1. **天然由代码构成**：护栏拦截、HITL 状态机、范围围栏都有明确的输入/输出，最契合"机制必须是代码"要求。
2. **可确定性测试**：每个机制可用 mock LLM 确定性测试，无需真实 LLM。
3. **工程深度最明显**：是 agent 安全落地最关键的工程层。
4. **与提示词对比鲜明**：一个 `check(Action(command="rm -rf /"))` 返回 DENY 的函数，与"提醒 LLM 注意安全"的提示词形成鲜明对比。

**治理维度的四个机制：**

| 机制 | 输入 | 输出 | 测试方式 |
|------|------|------|---------|
| GuardrailEngine | Action | GuardrailDecision(ALLOW/ASK/DENY) | 纯函数，12 条规则逐一测试 |
| HITLManager | ASK 动作 | HITLState(pending→approved/denied) | 状态转换逐一测试 |
| ScopeFence | path/command | (bool, reason) | 路径边界 + 符号链接逃逸测试 |
| AuditLog | (action, decision, result) | JSONL 日志条目 | 格式 + 脱敏检查 |

**判定标准（§A.4-C）：移除真实 LLM 后，治理机制还能用单测验证吗？**

回答：能。GuardrailEngine 是纯函数，HITLManager 是状态机，ScopeFence 是路径检查，AuditLog 是日志写入——全部不依赖 LLM，全部可用确定性单元测试验证。

---

## 附录：项目目录结构

```
codeguard/
├── src/
│   └── codeguard/
│       ├── __init__.py
│       ├── cli.py                    # CLI 入口
│       ├── server.py                 # FastAPI 服务器
│       ├── agent/
│       │   ├── __init__.py
│       │   ├── loop.py               # AgentLoop 主循环
│       │   ├── llm_client.py          # LLMClient 抽象层 + MockLLMClient
│       │   └── action.py             # Action 解析
│       ├── tools/
│       │   ├── __init__.py
│       │   ├── base.py               # Tool 抽象基类
│       │   ├── dispatcher.py         # ToolDispatcher
│       │   ├── file_tools.py         # ReadFile/WriteFile/EditFile
│       │   ├── shell_tools.py        # RunShell
│       │   ├── test_tools.py         # RunTests/RunLint
│       │   └── search_tools.py       # ListFiles/SearchContent
│       ├── governance/
│       │   ├── __init__.py
│       │   ├── guardrail.py          # GuardrailEngine
│       │   ├── rules.py              # 规则定义
│       │   ├── hitl.py               # HITLManager 状态机
│       │   ├── scope_fence.py        # ScopeFence
│       │   └── audit_log.py          # AuditLog
│       ├── feedback/
│       │   ├── __init__.py
│       │   ├── validators.py         # TestValidator/LintValidator
│       │   └── result.py            # FeedbackResult
│       ├── memory/
│       │   ├── __init__.py
│       │   └── store.py             # MemoryStore
│       ├── skills/
│       │   ├── __init__.py
│       │   └── loader.py            # SkillLoader
│       ├── mcp/
│       │   ├── __init__.py
│       │   └── adapter.py           # MCPToolAdapter
│       ├── credentials/
│       │   ├── __init__.py
│       │   └── manager.py           # CredentialManager
│       └── models/
│           ├── __init__.py
│           └── entities.py          # 数据模型定义
├── frontend/
│   ├── package.json
│   ├── vite.config.ts
│   └── src/
│       ├── App.tsx
│       ├── components/
│       │   ├── ChatPanel.tsx
│       │   ├── StepTimeline.tsx
│       │   ├── HITLDialog.tsx
│       │   ├── FeedbackPanel.tsx
│       │   ├── MemoryViewer.tsx
│       │   ├── SkillList.tsx
│       │   └── ConfigPanel.tsx
│       └── hooks/
│           └── useWebSocket.ts
├── skills/                           # 技能文件目录
│   └── tdd-workflow.md
├── config/
│   ├── guardrails.yaml               # 护栏规则配置
│   └── mcp_servers.yaml               # MCP 服务器配置
├── tests/
│   ├── conftest.py
│   ├── test_agent_loop.py
│   ├── test_llm_client.py
│   ├── test_tool_dispatcher.py
│   ├── test_guardrail.py
│   ├── test_hitl.py
│   ├── test_scope_fence.py
│   ├── test_audit_log.py
│   ├── test_feedback.py
│   ├── test_memory.py
│   ├── test_skill_loader.py
│   ├── test_mcp_adapter.py
│   └── test_credential_manager.py
├── demo/
│   └── mechanism_demo.py             # 机制演示
├── Dockerfile
├── docker-compose.yml
├── pyproject.toml
├── Makefile
├── .gitignore
├── .gitlab-ci.yml
├── SPEC.md
├── PLAN.md
├── SPEC_PROCESS.md
├── AGENT_LOG.md
├── REFLECTION.md
└── README.md
```
