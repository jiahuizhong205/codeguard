import pytest
from codeguard.mcp.adapter import MCPToolAdapter, MCPToolWrapper
from codeguard.tools.dispatcher import ToolDispatcher
from codeguard.models.entities import ToolResult


class FakeMCPClient:
    def __init__(self, tools: list[dict]):
        self._tools = tools

    async def list_tools(self) -> list[dict]:
        return self._tools

    async def call_tool(self, name: str, params: dict) -> dict:
        return {"result": f"called {name} with {params}"}


@pytest.mark.asyncio
async def test_connect_and_register():
    dispatcher = ToolDispatcher()
    adapter = MCPToolAdapter(dispatcher)
    mcp_client = FakeMCPClient(tools=[
        {"name": "design_ui", "description": "Design a UI component", "schema": {}}
    ])
    tools = await adapter.connect("test-server", mcp_client)
    assert len(tools) == 1
    assert "design_ui" in dispatcher.list_tools()


@pytest.mark.asyncio
async def test_mcp_tool_wrapper_executes():
    mcp_client = FakeMCPClient(tools=[])
    wrapper = MCPToolWrapper("echo", mcp_client)
    result = wrapper.execute({"text": "hello"})
    assert result.success is True
    assert "echo" in result.output


@pytest.mark.asyncio
async def test_connect_failure_does_not_block():
    dispatcher = ToolDispatcher()
    adapter = MCPToolAdapter(dispatcher)

    class FailingMCPClient:
        async def list_tools(self):
            raise ConnectionError("Server unavailable")

    tools = await adapter.connect("bad-server", FailingMCPClient())
    assert tools == []
    assert len(dispatcher.list_tools()) == 0
