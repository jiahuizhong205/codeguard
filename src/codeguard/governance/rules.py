from __future__ import annotations
import logging
import re
from abc import ABC, abstractmethod
from pathlib import Path

import yaml

from codeguard.models.entities import Action, GuardrailDecision, GuardrailLevel

logger = logging.getLogger(__name__)


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


# ── YAML 配置加载（修复 SPEC 缺陷 3：R012 加载机制缺失） ──

_LEVEL_MAP = {
    "allow": GuardrailLevel.ALLOW,
    "ask": GuardrailLevel.ASK,
    "deny": GuardrailLevel.DENY,
}

_CONFIG_PATHS = [
    Path("config/guardrails.yaml"),
    Path("../config/guardrails.yaml"),
]


def _load_from_path(config_path: Path) -> list[Rule]:
    """从指定路径加载 YAML 护栏规则配置。文件不存在或格式错误时返回空列表。"""
    if not config_path.exists():
        return []
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
    except (yaml.YAMLError, OSError) as e:
        logger.warning(f"Failed to parse guardrail config {config_path}: {e}")
        return []

    if not data or "rules" not in data:
        return []

    rules: list[Rule] = []
    for entry in data["rules"]:
        try:
            rule = _parse_rule_entry(entry)
            if rule:
                rules.append(rule)
        except Exception as e:
            logger.warning(f"Skipping invalid rule entry {entry.get('id', '?')}: {e}")
    return rules


def _parse_rule_entry(entry: dict) -> Rule | None:
    rule_id = entry.get("id", "")
    level_str = entry.get("level", "ask").lower()
    reason = entry.get("reason", "")
    rule_type = entry.get("type", "shell").lower()

    level = _LEVEL_MAP.get(level_str, GuardrailLevel.ASK)

    if rule_type == "shell":
        return ShellRule(rule_id, entry["pattern"], level, reason)
    elif rule_type == "path":
        pattern = re.compile(entry["pattern"])
        return PathRule(rule_id, level, reason, lambda p: bool(pattern.search(p)))
    else:
        logger.warning(f"Unknown rule type '{rule_type}' for rule {rule_id}")
        return None


def load_custom_rules() -> list[Rule]:
    """加载自定义护栏规则（config/guardrails.yaml），补充内置 R001-R011。

    SPEC R012 自定义规则通过此函数加载，文件不存在或格式错误时降级返回空列表。
    """
    for config_path in _CONFIG_PATHS:
        if config_path.exists():
            return _load_from_path(config_path)
    return []
