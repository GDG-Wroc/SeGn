from mcp.server.fastmcp import FastMCP

from app.tools.analogy import generate_analogy_solutions, health_check

tools = [
    generate_analogy_solutions,
    health_check,
]


def register(mcp: FastMCP) -> None:
    for tool in tools:
        mcp.tool()(tool)
