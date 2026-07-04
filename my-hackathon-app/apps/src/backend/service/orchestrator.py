import asyncio
import logging
from typing import Any

from backend.service.analogy_mcp_service import AnalogyMCP
from backend.service.mcp_service import MCP
from backend.service.response_builder import ResponseBuilder
from backend.service.triz_interpreter import TRIZResultInterpreter


logger = logging.getLogger(__name__)


class MCPOrchestrator:
    def __init__(
        self,
        triz_mcp: MCP,
        analogy_mcp: AnalogyMCP,
        triz_interpreter: TRIZResultInterpreter | None = None,
        response_builder: ResponseBuilder | None = None,
    ) -> None:
        self.triz_mcp = triz_mcp
        self.analogy_mcp = analogy_mcp
        self.triz_interpreter = triz_interpreter or TRIZResultInterpreter()
        self.response_builder = response_builder or ResponseBuilder()

    async def run(self, query: str) -> dict[str, Any]:
        logger.info("API received query: %s", query)
        triz_raw, analogy_raw = await asyncio.gather(
            self.call_triz_mcp(query),
            self.call_analogy_mcp(query),
        )

        triz_result = self._summarize_triz_response(query, triz_raw)
        analogy_result = self._format_analogy_response(query, analogy_raw)
        return self.response_builder.build_user_response(query, triz_result, analogy_result)

    async def call_triz_mcp(self, query: str) -> dict[str, Any]:
        logger.info("Sending query to TRIZ MCP: %s", query)
        try:
            response = await self.triz_mcp.send_query_to_mcp(query)
            logger.info("TRIZ MCP status: success")
            return {"status": "success", "raw_response": response}
        except Exception as exc:
            logger.exception("TRIZ MCP status: error")
            return {
                "status": "error",
                "raw_response": None,
                "error": {"type": exc.__class__.__name__, "message": str(exc)},
            }

    async def call_analogy_mcp(self, query: str) -> dict[str, Any]:
        logger.info("Sending query to Design by Analogy MCP: %s", query)
        try:
            response = await self.analogy_mcp.send_query_to_mcp(query)
            status = "success" if self._is_successful_mcp_response(response) else "error"
            logger.info("Design by Analogy MCP status: %s", status)
            return {"status": status, "raw_response": response}
        except Exception as exc:
            logger.exception("Design by Analogy MCP status: error")
            return {
                "status": "error",
                "raw_response": None,
                "error": {"type": exc.__class__.__name__, "message": str(exc)},
            }

    def _summarize_triz_response(
        self,
        query: str,
        triz_mcp_result: dict[str, Any],
    ) -> dict[str, Any]:
        if triz_mcp_result["status"] != "success":
            return {
                "status": "error",
                "recommendation": None,
                "raw_response": triz_mcp_result.get("raw_response"),
                "error": triz_mcp_result.get("error"),
            }

        interpreted = self.triz_interpreter.interpret(
            original_problem=query,
            triz_raw_response=triz_mcp_result["raw_response"],
        )
        return {
            "status": "success",
            "recommendation": {
                "summary": interpreted["summary"],
                "identified_parameters": interpreted["identified_parameters"],
                "recommended_directions": interpreted["recommended_directions"],
            },
            "raw_response": interpreted["raw_response"],
        }

    def _format_analogy_response(
        self,
        query: str,
        analogy_mcp_result: dict[str, Any],
    ) -> dict[str, Any]:
        raw_response = analogy_mcp_result.get("raw_response")
        if analogy_mcp_result["status"] != "success":
            return {
                "status": "error",
                "recommendation": None,
                "raw_response": raw_response,
                "error": analogy_mcp_result.get("error") or self._extract_mcp_error(raw_response),
            }

        candidates = self._normalize_analogy_candidates(raw_response)
        if len(candidates) < 3:
            return {
                "status": "error",
                "recommendation": None,
                "raw_response": raw_response,
                "error": {
                    "type": "InsufficientAnalogyCandidates",
                    "message": "Design by Analogy MCP returned fewer than 3 valid candidates.",
                },
            }

        return {
            "status": "success",
            "recommendation": {
                "summary": (
                    "Design by Analogy proposes solutions inspired by systems that "
                    "regulate flow, buffering, or adaptation under changing conditions."
                ),
                "candidates": candidates,
            },
            "raw_response": raw_response,
        }

    def _normalize_analogy_candidates(self, raw_response: Any) -> list[dict[str, Any]]:
        if not isinstance(raw_response, dict):
            return []

        normalized = []
        for index, candidate in enumerate(raw_response.get("candidates", []), start=1):
            if not isinstance(candidate, dict):
                continue
            normalized.append(
                {
                    "candidate_id": candidate.get("candidate_id") or f"ANALOGY-{index}",
                    "method": "Design by Analogy",
                    "solution_name": candidate.get("solution_name", ""),
                    "source_analogy": candidate.get("source_analogy")
                    or candidate.get("source_domain", ""),
                    "mechanism": candidate.get("mechanism")
                    or candidate.get("analogical_mechanism", ""),
                    "transferred_principle": candidate.get("transferred_principle", ""),
                    "solution_description": candidate.get("solution_description", ""),
                    "why_it_fits_original_problem": candidate.get("why_it_fits_original_problem")
                    or candidate.get("why_it_addresses_original_problem", ""),
                    "benefits": candidate.get("benefits")
                    or candidate.get("expected_benefits", []),
                    "risks": candidate.get("risks")
                    or candidate.get("possible_risks", []),
                    "implementation_complexity": candidate.get(
                        "implementation_complexity",
                        "medium",
                    ),
                }
            )
        return [
            candidate
            for candidate in normalized
            if candidate["solution_name"]
            and candidate["source_analogy"]
            and candidate["solution_description"]
            and candidate["why_it_fits_original_problem"]
        ]

    def _is_successful_mcp_response(self, response: Any) -> bool:
        if isinstance(response, dict) and "is_successful" in response:
            return bool(response["is_successful"])
        return True

    def _extract_mcp_error(self, response: Any) -> dict[str, str] | None:
        if isinstance(response, dict) and isinstance(response.get("error"), dict):
            return response["error"]
        return None
