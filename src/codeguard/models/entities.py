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
    """SPEC §3.6 全部 8 个状态 — 审批生命周期由 HITLManager 管理，执行生命周期由 AgentLoop 管理。"""
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
    FILE_OUTPUT = "file_output"


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
