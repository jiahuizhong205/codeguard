# tests/test_guardrail_config.py
import pytest
from pathlib import Path
from codeguard.governance.rules import load_custom_rules, default_rules, Rule, ShellRule, PathRule
from codeguard.governance.guardrail import GuardrailEngine
from codeguard.models.entities import Action, GuardrailLevel


def test_load_custom_rules_from_yaml():
    """从 YAML 配置文件加载自定义规则。"""
    rules = load_custom_rules()
    assert len(rules) >= 1
    r012 = rules[0]
    assert r012.rule_id == "R012"


def test_custom_shell_rule_effective():
    """自定义 R012 shell 规则应被 GuardrailEngine 执行。"""
    custom_rules = load_custom_rules()
    all_rules = default_rules() + custom_rules
    engine = GuardrailEngine(all_rules)

    action = Action(name="run_shell", params={"command": "kubectl delete pod"})
    decision = engine.check(action)
    assert decision.level == GuardrailLevel.ASK
    assert decision.rule_id == "R012"


def test_custom_rules_are_valid_rule_instances():
    """加载的自定义规则必须是 Rule 子类实例。"""
    rules = load_custom_rules()
    for rule in rules:
        assert isinstance(rule, Rule)


def test_empty_config_when_file_missing(tmp_path: Path):
    """配置文件不存在时应返回空列表，不抛异常。"""
    from codeguard.governance.rules import _load_from_path
    rules = _load_from_path(tmp_path / "nonexistent.yaml")
    assert rules == []


def test_malformed_yaml_returns_empty(tmp_path: Path):
    """YAML 格式错误时应返回空列表，不抛异常。"""
    bad_yaml = tmp_path / "bad.yaml"
    bad_yaml.write_text(":::\ninvalid: [yaml: broken")
    from codeguard.governance.rules import _load_from_path
    rules = _load_from_path(bad_yaml)
    assert rules == []


def test_custom_shell_rule_does_not_match_other_actions():
    """自定义 ShellRule 不应匹配非 shell 动作。"""
    custom_rules = load_custom_rules()
    for rule in custom_rules:
        if rule.rule_id == "R012":
            decision = rule.evaluate(Action(name="read_file", params={"path": "test.py"}))
            assert decision is None
