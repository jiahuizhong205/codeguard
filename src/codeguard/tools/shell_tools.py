from __future__ import annotations
import subprocess
from codeguard.models.entities import ToolResult
from codeguard.tools.base import Tool


class RunShell(Tool):
    name = "run_shell"

    def execute(self, params: dict) -> ToolResult:
        command = params["command"]
        timeout = params.get("timeout", 30)
        try:
            proc = subprocess.run(
                command, shell=True, capture_output=True, text=True, timeout=timeout
            )
            output = proc.stdout + proc.stderr
            return ToolResult(
                success=proc.returncode == 0,
                output=output,
                exit_code=proc.returncode,
            )
        except subprocess.TimeoutExpired:
            return ToolResult(success=False, error=f"Command timed out after {timeout}s")
