from __future__ import annotations
from abc import ABC, abstractmethod
from codeguard.models.entities import ToolResult


class Tool(ABC):
    name: str

    @abstractmethod
    def execute(self, params: dict) -> ToolResult:
        ...
