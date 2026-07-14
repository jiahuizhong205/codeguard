from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
from codeguard.models.entities import MemoryEntry


class MemoryStore:
    def __init__(self, storage_path: Path):
        self._path = storage_path
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def _read_all(self) -> dict[str, dict]:
        if not self._path.exists():
            return {}
        try:
            with open(self._path, "r", encoding="utf-8") as f:
                return json.load(f)
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_all(self, data: dict[str, dict]) -> None:
        with open(self._path, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, default=str)

    def save(self, key: str, category: str, value: str) -> None:
        data = self._read_all()
        data[key] = {
            "key": key, "category": category, "value": value,
            "updated_at": datetime.now().isoformat(),
        }
        self._write_all(data)

    def load(self, key: str) -> MemoryEntry | None:
        data = self._read_all()
        if key not in data:
            return None
        d = data[key]
        return MemoryEntry(
            key=d["key"], category=d["category"], value=d["value"],
            updated_at=datetime.fromisoformat(d["updated_at"]),
        )

    def query(self, category: str | None = None) -> list[MemoryEntry]:
        data = self._read_all()
        results = []
        for d in data.values():
            if category is None or d.get("category") == category:
                results.append(MemoryEntry(
                    key=d["key"], category=d["category"], value=d["value"],
                    updated_at=datetime.fromisoformat(d["updated_at"]),
                ))
        return results

    def clear(self, key: str) -> None:
        data = self._read_all()
        data.pop(key, None)
        self._write_all(data)
