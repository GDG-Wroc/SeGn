from backend.service.mcp_service import MCP, AnalogyMCP
from backend.service.llm_client import LLMClient

def get_mcp():
    return MCP()

def get_analogy_mcp():
    return AnalogyMCP()

def get_llm_client():
    return LLMClient()
