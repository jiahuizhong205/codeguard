from __future__ import annotations
from codeguard.models.entities import Action, LLMResponse


def parse_action(response: LLMResponse) -> Action | None:
    if not response.tool_calls:
        return None
    call = response.tool_calls[0]
    return Action(
        name=call.get("name", ""),
        params=call.get("params", {}),
        raw_llm_output=response.content,
    )
