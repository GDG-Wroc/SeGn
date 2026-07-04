from fastapi import FastAPI
from backend.api.schemas.pydantic_schemas import UserInput
from backend.service.mcp_service import MCP
from backend.service.llm_client import LLMClient
from backend.dependencies.depends import get_llm_client, get_mcp
from fastapi import Depends

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
    MCP_Service: MCP = Depends(get_mcp),
    llm_client: LLMClient = Depends(get_llm_client),
):
    mcp_response = await MCP_Service.send_query_to_mcp(user_input.query)
    return await llm_client.explain_mcp_response(user_input.query, mcp_response)
