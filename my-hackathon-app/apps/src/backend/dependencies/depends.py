from backend.service.mcp_service import MCP
from backend.service.llm_client import LLMClient
# Narazie bez Depends 

def get_mcp():
    return MCP()

def get_llm_client():
    return LLMClient()
