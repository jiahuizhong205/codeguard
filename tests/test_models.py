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


# 新增：验证 HITLState 包含全部 8 个状态
def test_hitl_state_has_all_8_states():
    """SPEC §3.6 定义的全部 8 个状态必须在枚举中。"""
    expected_states = {
        "PENDING", "APPROVED", "DENIED", "TIMEOUT",
        "EXECUTING", "COMPLETED", "SKIPPED", "FAILED",
    }
    actual_states = {s.name for s in HITLState}
    assert actual_states == expected_states
