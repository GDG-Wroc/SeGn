from typing import Any

from app.core.config import config
from app.services.analogy_pipeline import DesignByAnalogyPipeline


async def generate_analogy_solutions(
    problem: str,
    minimum_solutions: int = 3,
) -> dict[str, Any]:
    """Generate solution candidates using a structured Design by Analogy pipeline."""
    minimum_solutions = max(3, minimum_solutions)
    if not problem or not problem.strip():
        return {
            "method": "Design by Analogy",
            "input_problem": problem,
            "minimum_solutions_required": minimum_solutions,
            "logic_trace": [],
            "candidates": [],
            "candidate_count": 0,
            "is_successful": False,
            "error": {
                "type": "InvalidInput",
                "message": "problem must be a non-empty string",
            },
        }

    pipeline = DesignByAnalogyPipeline()
    return await pipeline.run(problem.strip(), minimum_solutions)


def health_check() -> dict[str, Any]:
    """Return basic server health and configuration state."""
    return {
        "status": "ok",
        "name": "design-by-analogy-mcp",
        "transport": "streamable-http",
        "host": config.MCP_HOST,
        "port": config.MCP_PORT,
        "path": "/mcp",
        "llm_configured": bool(config.ANALOGY_LLM_BASE_URL),
    }
