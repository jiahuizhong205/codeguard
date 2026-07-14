from __future__ import annotations
from codeguard.models.entities import ToolResult
from codeguard.tools.base import Tool
from codeguard.tools.shell_tools import RunShell


class RunTests(Tool):
    name = "run_tests"

    def __init__(self):
        self._shell = RunShell()

    def execute(self, params: dict) -> ToolResult:
        return self._shell.execute(params)


class RunLint(Tool):
    name = "run_lint"

    def __init__(self):
        self._shell = RunShell()

    def execute(self, params: dict) -> ToolResult:
        return self._shell.execute(params)
