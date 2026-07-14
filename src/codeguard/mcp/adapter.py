from __future__ import annotations
import logging
from codeguard.models.entities import ToolResult
from codeguard.tools.base import Tool
from codeguard.tools.dispatcher import ToolDispatcher

logger = logging.getLogger(__name__)


class MCPToolWrapper(Tool):
    def __init__(self, name: str, mcp_client):
        self.name = name
        self._client = mcp_client

    def execute(self, params: dict) -> ToolResult:
        import asyncio
        try:
            coro = self._client.call_tool(self.name, params)
            try:
                asyncio.get_running_loop()
                running = True
            except RuntimeError:
                running = False

            if running:
                import concurrent.futures
                with concurrent.futures.ThreadPoolExecutor() as pool:
                    result = pool.submit(asyncio.run, coro).result()
            else:
                result = asyncio.run(coro)
            return ToolResult(success=True, output=str(result.get("result", "")))
        except Exception as e:
            return ToolResult(success=False, error=str(e))


class MCPToolAdapter:
    def __init__(self, dispatcher: ToolDispatcher):
        self._dispatcher = dispatcher

    async def connect(self, server_name: str, mcp_client) -> list[Tool]:
        try:
            tool_defs = await mcp_client.list_tools()
        except Exception as e:
            logger.warning(f"Failed to connect to MCP server '{server_name}': {e}")
            return []

        registered = []
        for td in tool_defs:
            tool = MCPToolWrapper(td["name"], mcp_client)
            self._dispatcher.register(tool)
            registered.append(tool)
        return registered
