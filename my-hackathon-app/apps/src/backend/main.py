from fastapi import FastAPI
from backend.api.schemas.pydantic_schemas import UserInput
from backend.service.mcp_service import MCP
from backend.dependencies.depends import get_mcp
from fastapi import Depends

def create_app() -> FastAPI:
    app = FastAPI()
    return app

app = create_app()

@app.get("/")
def health():
    return {"status": "ok"}


@app.post("/query")
async def post_query(user_input: UserInput, MCP_Service : MCP =Depends(get_mcp)):
    mcp_response = await MCP_Service.send_query_to_mcp(user_input.query)
    return mcp_response
