from __future__ import annotations
from codeguard.models.entities import Action, GuardrailDecision, GuardrailLevel
from codeguard.governance.rules import Rule


class GuardrailEngine:
    """Deterministic guardrail engine — pure function, no LLM needed.

    默认行为：未命中任何规则时返回 ALLOW。
    规则按顺序评估，首个命中（非 None）的规则决定结果。
    """

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
