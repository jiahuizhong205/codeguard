# SPEC_PROCESS.md — SPEC 缺陷与歧义记录

> 生成于 Task 7（护栏引擎）和 Task 9（HITL 管理器）实现过程中。
> 仅基于 SPEC.md 和 PLAN.md，不依赖任何外部上下文。

---

## 已解决的歧义

### 歧义 1：护栏引擎对未知动作类型的默认行为

- **位置：** SPEC §3.5 vs PLAN Task 7
- **冲突：** SPEC 写"未知动作类型默认 ASK"，PLAN 实现为默认 ALLOW
- **决策：** 采用 **默认 ALLOW**
- **理由：**
  - 护栏引擎的设计哲学是规则驱动 — 危险动作应由显式规则覆盖（R001-R011），而非靠"未知就拦"兜底
  - 默认 ASK 会导致每个未命中规则的普通动作都暂停等确认，系统实际不可用
  - PLAN 的 `GuardrailLevel.ALLOW + "No rule matched"` 更符合规则引擎理念：命中规则才拦截，未命中则放行
  - SPEC 中"未知动作类型默认 ASK"可理解为草案阶段的保守描述

### 歧义 2：HITL 状态机状态管理范围

- **位置：** SPEC §3.6 vs PLAN Task 9
- **冲突：** SPEC 定义 8 个状态（PENDING/APPROVED/DENIED/TIMEOUT/EXECUTING/COMPLETED/SKIPPED/FAILED），PLAN 的 HITLManager 只管理 4 个
- **决策：** **HITLState 枚举包含全部 8 个状态，但状态转换职责分层管理**
- **理由：**
  - HITLManager 保持单一职责 — 管理**审批**生命周期（PENDING → APPROVED/DENIED/TIMEOUT）
  - AgentLoop 作为编排者负责**执行**生命周期（APPROVED → EXECUTING → COMPLETED/FAILED，DENIED → SKIPPED）
  - 8 个状态记录在同一 HITLRequest 对象上，形成完整的审批→执行追溯链
  - 避免 HITLManager 变成同时管理审批+执行的"上帝对象"
- **状态分配：**

| 状态 | 转换负责方 |
|------|-----------|
| PENDING → APPROVED/DENIED | HITLManager.resolve() |
| PENDING → TIMEOUT | HITLManager.check_timeout() |
| APPROVED → EXECUTING | AgentLoop |
| EXECUTING → COMPLETED | AgentLoop |
| EXECUTING → FAILED | AgentLoop |
| DENIED → SKIPPED | AgentLoop |

---

## 发现的 SPEC/PLAN 缺陷

### 缺陷 1：pyproject.toml build-backend 配置错误

- **位置：** PLAN Task 1 步骤 1
- **问题：** PLAN 指定的 `build-backend = "setuptools.backends._legacy:_Backend"` 模块不存在
- **影响：** 直接使用 PLAN 的配置会导致 `pip install -e .` 失败
- **严重程度：** 阻塞级 — 项目无法安装
- **状态：** ✅ **已修复** — `pyproject.toml` 中改为 `build-backend = "setuptools.build_meta"`
- **修复文件：** `pyproject.toml:2`

### 缺陷 2：SPEC HITLManager.request() 伪代码引用未定义方法

- **位置：** SPEC §3.6 伪代码第 313 行
- **问题：** `return await self._wait_for_resolution(req)` 中的 `_wait_for_resolution` 方法从未定义
- **影响：** 实现者无法确定"等待用户响应"的具体机制
- **严重程度：** 中等
- **状态：** ✅ **已修复（文档层面）** — 在 `hitl.py` HITLManager 类 docstring 中明确说明：
  - HITLManager 是同步状态机，不负责等待用户输入
  - `_wait_for_resolution()` 的职责实际由 AgentLoop 承担（WebSocket 推送 → 等待用户响应 → resolve/check_timeout）
  - 这种分层设计使 HITLManager 可独立单测（不依赖 WebSocket/事件循环）
- **修复文件：** `src/codeguard/governance/hitl.py:7-36`

### 缺陷 3：SPEC 中 R012 规则的加载机制未定义

- **位置：** SPEC §3.5 规则表 R012
- **问题：** R012 标记为"用户自定义规则（YAML 配置）"，但加载机制完全未定义
- **影响：** Task 7 实现时只能覆盖 R001-R011
- **严重程度：** 中等
- **状态：** ✅ **已修复** — 在 `rules.py` 中新增 `load_custom_rules()` 和 `_load_from_path()`：
  - 从 `config/guardrails.yaml` 加载自定义规则
  - 支持 `type: shell`（正则匹配命令）和 `type: path`（正则匹配路径）
  - 文件不存在或格式错误时降级返回空列表
  - 规则自动适配为 `ShellRule` 或 `PathRule` 实例
  - 新增 6 个单测覆盖正常加载、边界情况、错误处理
- **修复文件：** `src/codeguard/governance/rules.py:83-154`, `config/guardrails.yaml`, `tests/test_guardrail_config.py`

### 缺陷 4：SPEC §3.6 状态转换图中的 FAILED 状态处理不明确

- **位置：** SPEC §3.6 状态转换图：`EXECUTING → FAILED → (error feedback to agent)`
- **问题：** "error feedback to agent" 表述模糊 — 谁负责、通过什么机制、是否需要 WebSocket
- **影响：** 实现时 FAILED 状态的后续处理逻辑不确定
- **严重程度：** 低 — Task 9 实现不涉及 EXECUTING/FAILED
- **状态：** ✅ **已修复（文档层面）** — 在 `hitl.py` HITLManager 类 docstring 中明确说明：
  - EXECUTING → FAILED 由 AgentLoop 负责（AgentLoop 捕获执行异常后转换状态）
  - FAILED 后的错误信息由 AgentLoop 回灌到 LLM 消息队列
  - 是否需要 WebSocket 通知取决于 AgentLoop 的实现决策
- **修复文件：** `src/codeguard/governance/hitl.py:7-36`

### 缺陷 5：check_timeout() 比较符号问题

- **位置：** PLAN Task 9 check_timeout 实现
- **问题：** `elapsed > timedelta(seconds=self._timeout)` 用 `>` 导致 `timeout=0` 时测试不稳定
- **严重程度：** 低 — 边界条件问题
- **状态：** ✅ **已修复** — 改为 `>=`，确保 timeout=0 场景立即超时
- **修复文件：** `src/codeguard/governance/hitl.py:41`

### 缺陷 6：SPEC 与 PLAN 目录结构不一致

- **位置：** SPEC 附录 vs PLAN 文件结构
- **问题：**
  - SPEC 将 `ListFiles` 和 `SearchContent` 放在独立的 `tools/search_tools.py`，PLAN 将它们合并到 `file_tools.py`
  - FeedbackValidator 的 validate 签名 SPEC 为 `validate(output, exit_code)`，PLAN 为 `validate(result: ToolResult)`
- **影响：** 前后不一致可能导致后续 Task 实现时接口不匹配
- **严重程度：** 中等
- **状态：** ⚠️ **留待后续** — 影响 Task 5（文件工具）和 Task 11（反馈验证器），不在当前实现范围内。建议在实现 Task 5 时统一按 PLAN 的 `file_tools.py` 布局，在实现 Task 11 时统一按 PLAN 的 `validate(result: ToolResult)` 签名

## 汇总

| 类别 | 数量 | 已修复 | 留待后续 |
|------|------|--------|----------|
| 已解决歧义 | 2 | 2 | 0 |
| SPEC 缺陷 | 6 | 5 | 1 |
| - 阻塞级 | 1 | 1 | 0 |
| - 中等 | 3 | 2 | 1 |
| - 低 | 2 | 2 | 0 |

