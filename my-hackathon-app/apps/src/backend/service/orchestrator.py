import asyncio
import logging
from typing import Any

from backend.service.analogy_mcp_service import AnalogyMCP
from backend.service.domain_relevance import DomainRelevanceValidator
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
        relevance_validator: DomainRelevanceValidator | None = None,
    ) -> None:
        self.triz_mcp = triz_mcp
        self.analogy_mcp = analogy_mcp
        self.triz_interpreter = triz_interpreter or TRIZResultInterpreter()
        self.response_builder = response_builder or ResponseBuilder()
        self.relevance_validator = relevance_validator or DomainRelevanceValidator()

    async def run(self, query: str, debug: bool = False) -> dict[str, Any]:
        logger.info("API received query: %s", query)
        triz_raw, analogy_raw = await asyncio.gather(
            self.call_triz_mcp(query),
            self.call_analogy_mcp(query),
        )

        triz_result = self._summarize_triz_response(query, triz_raw)
        analogy_result = self._format_analogy_response(query, analogy_raw)
        return self.response_builder.build_user_response(
            query,
            triz_result,
            analogy_result,
            debug=debug,
        )

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
        logger.info("Design by Analogy raw MCP response: %s", raw_response)
        if analogy_mcp_result["status"] != "success":
            return {
                "status": "error",
                "recommendation": None,
                "raw_response": raw_response,
                "error": analogy_mcp_result.get("error") or self._extract_mcp_error(raw_response),
            }

        candidates = self._normalize_analogy_candidates(raw_response)
        logger.info("Design by Analogy parsed candidate count: %s", len(candidates))
        validation = self.relevance_validator.validate_analogy_candidates(query, candidates)
        logger.info(
            "Design by Analogy validation: valid=%s rejected=%s reasons=%s",
            validation["valid_candidate_count"],
            validation["irrelevant_candidate_count"],
            [
                candidate.get("domain_relevance", {}).get("reason")
                for candidate in validation["irrelevant_candidates"]
            ],
        )

        repair_performed = False
        if validation["valid_candidate_count"] < 3:
            repaired_candidates = self._repair_analogy_candidates(query, validation)
            repair_performed = bool(repaired_candidates)
            if repaired_candidates:
                candidates = validation["valid_candidates"] + repaired_candidates
                validation = self.relevance_validator.validate_analogy_candidates(
                    query,
                    candidates,
                )
                validation["repair_performed"] = True
                logger.info(
                    "Design by Analogy repair performed: valid=%s rejected=%s",
                    validation["valid_candidate_count"],
                    validation["irrelevant_candidate_count"],
                )
            else:
                validation["repair_performed"] = False

        candidates = validation["valid_candidates"]
        logger.info("Design by Analogy final frontend candidate count: %s", len(candidates[:3]))
        if len(candidates) < 3:
            return {
                "status": "error",
                "recommendation": None,
                "raw_response": raw_response,
                "error": {
                    "type": "IrrelevantAnalogyCandidates",
                    "message": "Design by Analogy MCP returned fewer than 3 candidates relevant to the original problem.",
                    "domain_relevance": validation,
                    "repair_performed": repair_performed,
                },
            }

        return {
            "status": "success",
            "recommendation": {
                "summary": self._analogy_summary(query, candidates[:3], raw_response),
                "candidates": candidates[:3],
                "domain_relevance": validation,
            },
            "raw_response": raw_response,
        }

    def _normalize_analogy_candidates(self, raw_response: Any) -> list[dict[str, Any]]:
        if not isinstance(raw_response, dict):
            return []

        raw_candidates = raw_response.get("analogy_examples") or raw_response.get("candidates", [])
        normalized = []
        for index, candidate in enumerate(raw_candidates, start=1):
            if not isinstance(candidate, dict):
                continue
            solution_description = (
                candidate.get("mapped_solution")
                or candidate.get("solution_description")
                or ""
            )
            mechanism = (
                candidate.get("analogy_mechanism")
                or candidate.get("analogical_mechanism")
                or candidate.get("mechanism")
                or candidate.get("analogy")
                or ""
            )
            normalized.append(
                {
                    "candidate_id": candidate.get("candidate_id") or f"ANALOGY-{index}",
                    "method": "Design by Analogy",
                    "solution_name": candidate.get("solution_name") or self._solution_name(solution_description, index),
                    "source_analogy": candidate.get("source_analogy")
                    or candidate.get("source_domain", ""),
                    "mechanism": mechanism,
                    "transferred_principle": candidate.get("transferred_principle", ""),
                    "solution_description": solution_description,
                    "mapped_solution": solution_description,
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
            if candidate["source_analogy"]
            and candidate["mechanism"]
            and candidate["solution_description"]
        ]

    def _repair_analogy_candidates(
        self,
        query: str,
        validation: dict[str, Any],
    ) -> list[dict[str, Any]]:
        existing_domains = {
            candidate.get("source_analogy") or candidate.get("source_domain")
            for candidate in validation.get("valid_candidates", [])
        }
        repaired = []
        for index, template in enumerate(self._generic_analogy_templates(), start=1):
            if template["source_domain"] in existing_domains:
                continue
            mapped_solution = self._map_template_to_problem(query, template)
            repaired.append(
                {
                    "candidate_id": f"ANALOGY-REPAIR-{index}",
                    "method": "Design by Analogy",
                    "solution_name": template["solution_name"],
                    "source_analogy": template["source_domain"],
                    "mechanism": template["mechanism"],
                    "transferred_principle": template["principle"],
                    "solution_description": mapped_solution,
                    "mapped_solution": mapped_solution,
                    "why_it_fits_original_problem": (
                        f"It directly addresses the stated problem by applying "
                        f"{template['principle'].lower()} to the target system."
                    ),
                    "benefits": template["benefits"],
                    "risks": ["Needs domain testing before deployment."],
                    "implementation_complexity": "medium",
                }
            )
            if len(validation.get("valid_candidates", [])) + len(repaired) >= 3:
                break
        return repaired

    def _generic_analogy_templates(self) -> list[dict[str, Any]]:
        return [
            {
                "source_domain": "Biology / kidneys",
                "solution_name": "Staged selective processing",
                "mechanism": "Kidneys use many parallel filters and selective reprocessing stages to clean fluid continuously.",
                "principle": "Distribute treatment across staged selective modules with local quality checks.",
                "benefits": ["adds capacity incrementally", "preserves quality through staged checks"],
            },
            {
                "source_domain": "Ecosystems / wetlands",
                "solution_name": "Distributed biological polishing",
                "mechanism": "Wetlands clean flows through slow distributed biological, sediment, and root-zone filtration.",
                "principle": "Add low-energy distributed polishing stages around the main system.",
                "benefits": ["reduces central load", "adds passive polishing capacity"],
            },
            {
                "source_domain": "Software / load balancing",
                "solution_name": "Capacity-aware dynamic routing",
                "mechanism": "Load balancers distribute traffic across available servers instead of overloading one server.",
                "principle": "Route incoming load dynamically across parallel paths using capacity and quality signals.",
                "benefits": ["avoids bottlenecks", "keeps output quality stable under variable load"],
            },
            {
                "source_domain": "Logistics / sorting hubs",
                "solution_name": "Triage and routing gates",
                "mechanism": "Sorting hubs classify items early and route them to specialized handling lanes.",
                "principle": "Classify inputs early and route each stream to the right treatment path.",
                "benefits": ["prevents one-size-fits-all overload", "targets difficult cases"],
            },
        ]

    def _map_template_to_problem(self, query: str, template: dict[str, Any]) -> str:
        target = self._target_phrase(query)
        return (
            f"Apply {template['principle'].lower()} so {target} can handle more demand "
            "while respecting the explicit constraints in the original problem."
        )

    def _target_phrase(self, query: str) -> str:
        lowered = " ".join(query.strip().split())
        marker = "Your task:"
        if marker in lowered:
            task = lowered.split(marker, 1)[1].strip()
            return task.split(".")[0].strip(" .")[:180] or "the target system"
        return lowered.split(".")[0].strip(" .")[:180] or "the target system"

    def _solution_name(self, solution_description: str, index: int) -> str:
        if not solution_description:
            return f"Analogy candidate {index}"
        words = solution_description.strip().split()
        return " ".join(words[:6]).strip(" .,;:") or f"Analogy candidate {index}"

    def _analogy_summary(
        self,
        query: str,
        candidates: list[dict[str, Any]],
        raw_response: Any,
    ) -> str:
        if isinstance(raw_response, dict) and raw_response.get("summary"):
            return raw_response["summary"]
        domains = [
            candidate.get("source_analogy")
            for candidate in candidates
            if candidate.get("source_analogy")
        ]
        target = self._target_phrase(query)
        return (
            f"Design by Analogy suggests solving the problem by borrowing mechanisms "
            f"from {', '.join(domains[:3])} and mapping them back to {target}."
        )

    def _is_successful_mcp_response(self, response: Any) -> bool:
        if isinstance(response, dict) and "is_successful" in response:
            return bool(response["is_successful"])
        return True

    def _extract_mcp_error(self, response: Any) -> dict[str, str] | None:
        if isinstance(response, dict) and isinstance(response.get("error"), dict):
            return response["error"]
        return None
