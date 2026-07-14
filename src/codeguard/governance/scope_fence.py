from __future__ import annotations
from pathlib import Path


class ScopeFence:
    def __init__(self, workspace_root: Path, allowed_paths: list[Path] | None = None):
        self._root = workspace_root.resolve()
        self._allowed = [p.resolve() for p in (allowed_paths or [])]

    def check_path(self, path: str) -> tuple[bool, str]:
        target = (self._root / path).resolve()
        if str(target).startswith(str(self._root)):
            return True, "OK"
        for allowed in self._allowed:
            if str(target).startswith(str(allowed)):
                return True, "OK (allowed path)"
        return False, f"Path escapes workspace: {target}"
