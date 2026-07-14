from __future__ import annotations
from codeguard.models.entities import Action, ToolResult
from codeguard.tools.base import Tool


class ToolDispatcher:
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
