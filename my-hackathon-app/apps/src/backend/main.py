from fastapi import FastAPI, Depends
from fastapi.middleware.cors import CORSMiddleware
from backend.api.schemas.pydantic_schemas import UserInput
from backend.service.mcp_service import MCP, AnalogyMCP
from backend.service.orchestrator import MCPOrchestrator
from backend.dependencies.depends import get_mcp, get_analogy_mcp

def create_app() -> FastAPI:
    app = FastAPI()
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
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
