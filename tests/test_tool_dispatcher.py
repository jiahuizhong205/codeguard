import pytest
from codeguard.tools.base import Tool
from codeguard.tools.dispatcher import ToolDispatcher
from codeguard.models.entities import Action, ToolResult


class FakeEchoTool(Tool):
    name = "echo"

    def execute(self, params: dict) -> ToolResult:
        return ToolResult(success=True, output=params.get("text", ""))


class FakeFailTool(Tool):
    name = "fail"

    def execute(self, params: dict) -> ToolResult:
        return ToolResult(success=False, output="", error="Always fails")


def test_dispatch_known_tool():
    dispatcher = ToolDispatcher()
    dispatcher.register(FakeEchoTool())
    result = dispatcher.dispatch(Action(name="echo", params={"text": "hello"}))
    assert result.success is True
    assert result.output == "hello"


def test_dispatch_unknown_tool():
    dispatcher = ToolDispatcher()
    result = dispatcher.dispatch(Action(name="nonexistent", params={}))
    assert result.success is False
    assert "Unknown tool" in result.error


def test_dispatch_fail_tool():
    dispatcher = ToolDispatcher()
    dispatcher.register(FakeFailTool())
    result = dispatcher.dispatch(Action(name="fail", params={}))
    assert result.success is False
    assert result.error == "Always fails"


def test_register_multiple_tools():
    dispatcher = ToolDispatcher()
    dispatcher.register(FakeEchoTool())
    dispatcher.register(FakeFailTool())
    assert "echo" in dispatcher.list_tools()
    assert "fail" in dispatcher.list_tools()
