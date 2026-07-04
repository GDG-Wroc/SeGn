from typing import Any

from fastapi import HTTPException
from fastmcp import Client


class MCP:

    def __init__(self, url: str = "http://localhost:8123/mcp"):
        self.mcp_uri = url

    async def list_tools(self) -> list[dict[str, Any]]:
        async with Client(self.mcp_uri) as client:
            tools = await client.list_tools()

        return [
            {
                "name": tool.name,
                "description": tool.description,
                "input_schema": getattr(tool, "inputSchema", None)
                or getattr(tool, "input_schema", None),
            }
            for tool in tools
        ]

    async def call_tool(self, tool_name: str, arguments: dict[str, Any]) -> Any:
        try:
            async with Client(self.mcp_uri) as client:
                result = await client.call_tool(tool_name, arguments)
        except Exception as exc:
            raise HTTPException(
                status_code=502,
                detail=f"MCP tool call failed: {exc}",
            ) from exc

        return self._extract_result(result)

    async def send_query_to_mcp(self, query: str) -> Any:
        return await self.call_tool(
            "search_parameter",
            {
                "query": query,
                "limit": 5,
            },
        )

    def _extract_result(self, result: Any) -> Any:
        data = getattr(result, "data", None)
        if data is not None:
            return getattr(data, "result", data)

        content = getattr(result, "content", None)
        if content:
            first_content = content[0]
            return getattr(first_content, "text", first_content)

        return result
