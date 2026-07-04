import logging

from fastapi import Depends, FastAPI

from backend.api.schemas.pydantic_schemas import UserInput
from backend.dependencies.depends import (
    get_analogy_mcp,
    get_mcp,
)
from backend.service.analogy_mcp_service import AnalogyMCP
from backend.service.mcp_service import MCP
from backend.service.orchestrator import MCPOrchestrator


logging.basicConfig(level=logging.INFO)


def create_app() -> FastAPI:
    app = FastAPI()
    return app


app = create_app()


@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/query")
async def post_query(
    user_input: UserInput,
    triz_mcp: MCP = Depends(get_mcp),
    analogy_mcp: AnalogyMCP = Depends(get_analogy_mcp),
):
    orchestrator = MCPOrchestrator(triz_mcp=triz_mcp, analogy_mcp=analogy_mcp)
    return await orchestrator.run(user_input.query)
