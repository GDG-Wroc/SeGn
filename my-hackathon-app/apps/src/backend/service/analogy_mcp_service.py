from typing import Any

from backend.service.mcp_service import MCP


class AnalogyMCP(MCP):
    def __init__(self, url: str = "http://localhost:8124/mcp"):
        super().__init__(url=url)

    async def send_query_to_mcp(self, query: str) -> Any:
        return await self.call_tool(
            "generate_analogy_solutions",
            {
                "problem": query,
                "minimum_solutions": 3,
            },
        )
