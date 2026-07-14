from __future__ import annotations
import re
from codeguard.models.entities import ToolResult, FeedbackResult


class TestValidator:
    def validate(self, result: ToolResult) -> FeedbackResult:
        output = result.output
        if result.exit_code == 0 or result.success:
            return FeedbackResult(validator="test", success=True, details=output)
        failures = self._parse_failures(output)
        return FeedbackResult(
            validator="test",
            success=False,
            details=output,
            failures=failures,
            suggestions=["Fix the failing tests listed above"],
        )

    def _parse_failures(self, output: str) -> list[str]:
        patterns = [r"(FAILED.*)", r"(.*assert.*)", r"(.*Error:.*)"]
        failures = []
        for line in output.splitlines():
            for pattern in patterns:
                if re.search(pattern, line):
                    failures.append(line.strip())
                    break
        return failures or ["Test failed (see details)"]


class LintValidator:
    def validate(self, result: ToolResult) -> FeedbackResult:
        output = result.output
        if result.exit_code == 0 or result.success:
            return FeedbackResult(validator="lint", success=True, details=output)
        errors = self._parse_errors(output)
        return FeedbackResult(
            validator="lint",
            success=False,
            details=output,
            failures=errors,
            suggestions=["Fix the lint errors listed above"],
        )

    def _parse_errors(self, output: str) -> list[str]:
        errors = []
        for line in output.splitlines():
            if re.search(r"^\S+:\d+:", line):
                errors.append(line.strip())
        return errors or ["Lint errors detected (see details)"]
