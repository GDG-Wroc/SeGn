import os

from backend.service.analogy_mcp_service import AnalogyMCP
from backend.service.llm_client import LLMClient
from backend.service.mcp_service import MCP


def get_mcp():
    return MCP()


def get_analogy_mcp():
    return AnalogyMCP()


def get_llm_client():
    return LLMClient()


def get_triz_llm_client():
    return LLMClient(
        base_url=os.getenv("TRIZ_LLM_BASE_URL") or os.getenv("LOCAL_LLM_BASE_URL"),
        model=os.getenv("TRIZ_LLM_MODEL") or os.getenv("LOCAL_LLM_MODEL"),
        system_prompt=(
            "You are an assistant that turns TRIZ MCP responses into short, clear "
            "recommendations in English. Do not invent facts outside the provided data."
        ),
    )


def get_analogy_llm_client():
    return LLMClient(
        base_url=os.getenv("ANALOGY_RESPONSE_LLM_BASE_URL") or os.getenv("LOCAL_LLM_BASE_URL"),
        model=os.getenv("ANALOGY_RESPONSE_LLM_MODEL") or os.getenv("LOCAL_LLM_MODEL"),
        system_prompt=(
            "You are an assistant that turns Design by Analogy MCP responses into "
            "simple, practical ideas in English. Preserve candidate names, analogy "
            "mechanisms, and the most important risks. Do not invent facts outside "
            "the provided data."
        ),
    )
