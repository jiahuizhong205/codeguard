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
