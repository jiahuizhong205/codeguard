from __future__ import annotations
import re
from pathlib import Path
from codeguard.models.entities import ToolResult
from codeguard.tools.base import Tool


class ReadFile(Tool):
    name = "read_file"

    def __init__(self, workspace_root: Path):
        self._root = workspace_root

    def execute(self, params: dict) -> ToolResult:
        path = self._root / params["path"]
        if not path.exists():
            return ToolResult(success=False, error=f"File not found: {params['path']}")
        return ToolResult(success=True, output=path.read_text())


class WriteFile(Tool):
    name = "write_file"

    def __init__(self, workspace_root: Path):
        self._root = workspace_root

    def execute(self, params: dict) -> ToolResult:
        path = self._root / params["path"]
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(params["content"])
        return ToolResult(success=True, output=f"Wrote {params['path']}")


class EditFile(Tool):
    name = "edit_file"

    def __init__(self, workspace_root: Path):
        self._root = workspace_root

    def execute(self, params: dict) -> ToolResult:
        path = self._root / params["path"]
        if not path.exists():
            return ToolResult(success=False, error=f"File not found: {params['path']}")
        content = path.read_text()
        old = params["old"]
        new = params["new"]
        if old not in content:
            return ToolResult(success=False, error=f"Pattern not found: {old}")
        count = content.count(old)
        if count > 1:
            return ToolResult(success=False, error=f"Pattern matches {count} times, must be unique")
        path.write_text(content.replace(old, new))
        return ToolResult(success=True, output=f"Edited {params['path']}")


class ListFiles(Tool):
    name = "list_files"

    def __init__(self, workspace_root: Path):
        self._root = workspace_root

    def execute(self, params: dict) -> ToolResult:
        pattern = params.get("pattern", "*")
        matches = [str(p.relative_to(self._root)) for p in self._root.rglob(pattern) if p.is_file()]
        return ToolResult(success=True, output="\n".join(matches))


class SearchContent(Tool):
    name = "search_content"

    def __init__(self, workspace_root: Path):
        self._root = workspace_root

    def execute(self, params: dict) -> ToolResult:
        pattern = params["pattern"]
        results = []
        for p in self._root.rglob("*"):
            if not p.is_file():
                continue
            for i, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
                if re.search(pattern, line):
                    results.append(f"{p.relative_to(self._root)}:{i}: {line}")
        return ToolResult(success=True, output="\n".join(results))
