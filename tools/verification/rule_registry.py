"""V0.9-G registry for model-family verification rules.

The registry keeps verification dispatch data-driven: model families declare
which rule set they use, while rule implementations remain independent.
"""
from __future__ import annotations
from dataclasses import dataclass
from typing import Any, Callable

RuleFn = Callable[[str, dict[str, Any], dict[str, Any]], list[dict[str, Any]]]


@dataclass(frozen=True)
class VerificationRuleSet:
    rule_id: str
    model_ids: tuple[str, ...]
    version: str
    handler: RuleFn


class VerificationRuleRegistry:
    def __init__(self) -> None:
        self._rules: dict[str, VerificationRuleSet] = {}
        self._model_index: dict[str, str] = {}

    def register(self, rule_set: VerificationRuleSet) -> None:
        if rule_set.rule_id in self._rules:
            raise ValueError(f"verification rule set already registered: {rule_set.rule_id}")
        for model_id in rule_set.model_ids:
            if model_id in self._model_index:
                raise ValueError(f"model already has verification rules: {model_id}")
            self._model_index[model_id] = rule_set.rule_id
        self._rules[rule_set.rule_id] = rule_set

    def resolve(self, model_id: str) -> VerificationRuleSet | None:
        rule_id = self._model_index.get(model_id)
        return self._rules.get(rule_id) if rule_id else None

    def verify(self, model_id: str, result: dict[str, Any], binding: dict[str, Any] | None = None) -> list[dict[str, Any]]:
        rule_set = self.resolve(model_id)
        if rule_set is None:
            return [{
                "check_id": "V-G99",
                "category": "other",
                "status": "NOT_RUN",
                "evidence": f"No verification rule set registered for model family: {model_id}",
            }]
        return rule_set.handler(model_id, result, binding or {})

    def manifest(self) -> list[dict[str, Any]]:
        return [{"rule_id": r.rule_id, "version": r.version, "model_ids": list(r.model_ids)} for r in self._rules.values()]
