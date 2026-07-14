from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from codeguard.models.entities import Action, GuardrailDecision, ToolResult, AuditEntry

_SENSITIVE_KEYS = ("key", "secret", "token", "password", "credential", "api_key")


class AuditLog:
    def __init__(self, log_path: Path):
        self._path = log_path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def record(self, action: Action, decision: GuardrailDecision, result: ToolResult) -> None:
        entry = AuditEntry(
            timestamp=datetime.now(),
            action_name=action.name,
            params=self._sanitize(action.params),
            decision=decision.level.value,
            result=(result.output[:500] if result.output else result.error)[:500] if result.output or result.error else None,
        )
        try:
            with open(self._path, "a", encoding="utf-8") as f:
                f.write(json.dumps(entry.__dict__, default=str, ensure_ascii=False) + "\n")
        except OSError:
            pass

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
