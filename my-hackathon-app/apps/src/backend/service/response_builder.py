from typing import Any


class ResponseBuilder:
    def build_user_response(
        self,
        original_problem: str,
        triz_result: dict[str, Any],
        analogy_result: dict[str, Any],
        debug: bool = False,
    ) -> dict[str, Any]:
        all_candidates = self._collect_candidates(triz_result, analogy_result)
        evaluation = self._evaluate_candidates(all_candidates)
        choice = evaluation[0] if evaluation else None
        response = {
            "problem": original_problem,
            "contradiction": self._build_contradiction(original_problem, triz_result),
            "all_candidates": all_candidates,
            "evaluation": evaluation,
            "choice": choice,
            "original_problem": original_problem,
            "triz": {
                "status": triz_result["status"],
                "recommendation": triz_result.get("recommendation"),
                "raw_response": triz_result.get("raw_response"),
                "error": triz_result.get("error"),
            },
            "design_by_analogy": {
                "status": analogy_result["status"],
                "recommendation": analogy_result.get("recommendation"),
                "raw_response": analogy_result.get("raw_response"),
                "error": analogy_result.get("error"),
            },
        }
        return response if debug else self._public_response(response)

    def _collect_candidates(
        self,
        triz_result: dict[str, Any],
        analogy_result: dict[str, Any],
    ) -> list[dict[str, Any]]:
        candidates = []

        triz_recommendation = triz_result.get("recommendation") or {}
        for index, candidate in enumerate(
            triz_recommendation.get("recommended_directions", []),
            start=1,
        ):
            candidates.append(
                {
                    "candidate_id": candidate.get("candidate_id") or f"TRIZ-{index}",
                    "method": "TRIZ",
                    "triz_parameter_or_principle": candidate.get("triz_parameter_or_principle"),
                    "solution_name": candidate.get("solution_name") or candidate.get("name", ""),
                    "solution_description": candidate.get("solution_description")
                    or candidate.get("description", ""),
                    "why_it_fits_original_problem": candidate.get(
                        "why_it_fits_original_problem",
                    )
                    or candidate.get("why_it_fits_problem", ""),
                    "benefits": candidate.get("benefits", []),
                    "risks": candidate.get("risks", []),
                    "implementation_complexity": candidate.get("implementation_complexity", "medium"),
                    "domain_relevance": candidate.get("domain_relevance"),
                }
            )

        analogy_recommendation = analogy_result.get("recommendation") or {}
        for candidate in analogy_recommendation.get("candidates", []):
            candidates.append(candidate)

        return candidates

    def _evaluate_candidates(self, candidates: list[dict[str, Any]]) -> list[dict[str, Any]]:
        evaluated = []
        for candidate in candidates:
            criteria = self._score_candidate(candidate)
            score = round(sum(criteria.values()) / len(criteria), 3)
            evaluated.append(
                {
                    "candidate_id": candidate.get("candidate_id"),
                    "method": candidate.get("method"),
                    "solution_name": candidate.get("solution_name") or candidate.get("name"),
                    "score": score,
                    "criteria": criteria,
                    "reason": self._evaluation_reason(candidate, criteria),
                }
            )
        return sorted(evaluated, key=lambda item: item["score"], reverse=True)

    def _build_contradiction(
        self,
        original_problem: str,
        triz_result: dict[str, Any],
    ) -> dict[str, Any]:
        recommendation = triz_result.get("recommendation") or {}
        parameters = recommendation.get("parameters") or []
        problem_lower = original_problem.lower()
        if any(word in problem_lower for word in ["packaging", "package", "shipping", "recycle", "biodegrade"]):
            statement = (
                "Packaging must be strong, moisture-resistant and protective during "
                "shipping, handling and storage, but after use it should disappear, "
                "biodegrade, recycle cleanly, or be reused responsibly."
            )
        elif any(word in problem_lower for word in ["desalination", "seawater", "freshwater", "brine"]):
            statement = (
                "Desalination must produce more freshwater from seawater, but it must "
                "avoid proportional increases in energy demand, pressure, heat stress "
                "and equipment wear."
            )
        else:
            statement = self._fallback_contradiction(original_problem)
        return {
            "statement": statement,
            "original_problem_reference": original_problem,
            "triz_parameters": parameters,
        }

    def _score_candidate(self, candidate: dict[str, Any]) -> dict[str, float]:
        text = " ".join(
            str(candidate.get(field, ""))
            for field in [
                "solution_name",
                "solution_description",
                "why_it_fits_original_problem",
                "transferred_principle",
                "mechanism",
                "source_analogy",
            ]
        ).lower()
        complexity = str(candidate.get("implementation_complexity", "medium")).lower()
        complexity_score = {"low": 0.9, "medium": 0.7, "high": 0.45}.get(complexity, 0.6)
        return {
            "protection_effectiveness": self._keyword_score(text, ["protect", "shipping", "impact", "shock", "moisture", "strong", "crush"], 0.55),
            "waste_reduction_biodegradation_reuse": self._keyword_score(text, ["reuse", "reusable", "compost", "biodegrade", "disappear", "waste", "returnable"], 0.5),
            "recyclability_simplicity": self._keyword_score(text, ["mono-material", "recycl", "single-material", "separable", "clean"], 0.5),
            "feasibility": complexity_score,
            "cost_implementation_complexity": complexity_score,
            "novelty": self._keyword_score(text, ["trigger", "mycelium", "honeycomb", "liner", "responsive", "bio-polymer", "separable"], 0.55),
        }

    def _keyword_score(self, text: str, keywords: list[str], base: float) -> float:
        matches = sum(1 for keyword in keywords if keyword in text)
        return round(min(1.0, base + matches * 0.1), 2)

    def _evaluation_reason(self, candidate: dict[str, Any], criteria: dict[str, float]) -> str:
        best = max(criteria, key=criteria.get)
        weakest = min(criteria, key=criteria.get)
        return (
            f"Scores strongest on {best.replace('_', ' ')} and is limited most by "
            f"{weakest.replace('_', ' ')}."
        )

    def _fallback_contradiction(self, original_problem: str) -> str:
        problem = original_problem.strip()
        first_sentence = problem.split(".")[0].strip()
        return (
            f"{first_sentence} must improve its desired function while avoiding the "
            "harmful trade-off explicitly described in the problem."
        )

    def _public_response(self, response: dict[str, Any]) -> dict[str, Any]:
        triz_recommendation = (
            (response.get("triz") or {}).get("recommendation") or {}
        )
        analogy_recommendation = (
            (response.get("design_by_analogy") or {}).get("recommendation") or {}
        )
        triz_recommendations = self._top_triz_recommendations(
            triz_recommendation.get("recommended_directions", []),
        )
        analogy_examples = self._analogy_examples(
            analogy_recommendation.get("candidates", []),
        )

        return {
            "original_problem_short": self._shorten_text(
                response.get("original_problem") or response.get("problem", ""),
            ),
            "triz": {
                "summary": self._shorten_text(
                    triz_recommendation.get("summary")
                    or self._fallback_triz_summary(triz_recommendations),
                    max_length=260,
                ),
                "top_recommendations": triz_recommendations,
            },
            "design_by_analogy": {
                "summary": self._shorten_text(
                    analogy_recommendation.get("summary")
                    or self._fallback_analogy_summary(analogy_examples),
                    max_length=260,
                ),
                "analogy_examples": analogy_examples,
            },
            "final_answer": self._build_final_answer(triz_recommendations, analogy_examples),
        }

    def _top_triz_recommendations(
        self,
        candidates: list[dict[str, Any]],
    ) -> list[dict[str, str]]:
        recommendations = []
        for candidate in candidates[:3]:
            recommendations.append(
                {
                    "name": self._shorten_text(
                        candidate.get("solution_name") or candidate.get("name", ""),
                        max_length=90,
                    ),
                    "short_description": self._shorten_text(
                        candidate.get("solution_description") or candidate.get("description", ""),
                        max_length=180,
                    ),
                    "why_it_fits": self._shorten_text(
                        candidate.get("why_it_fits_original_problem")
                        or candidate.get("why_it_fits_problem", ""),
                        max_length=180,
                    ),
                }
            )
        return recommendations

    def _analogy_examples(self, candidates: list[dict[str, Any]]) -> list[dict[str, str]]:
        examples = []
        for candidate in candidates[:3]:
            examples.append(
                {
                    "source_domain": self._shorten_text(
                        candidate.get("source_analogy") or candidate.get("source_domain", ""),
                        max_length=80,
                    ),
                    "analogy": self._shorten_text(
                        candidate.get("mechanism")
                        or candidate.get("analogical_mechanism")
                        or candidate.get("transferred_principle", ""),
                        max_length=160,
                    ),
                    "mapped_solution": self._shorten_text(
                        candidate.get("solution_description") or candidate.get("solution_name", ""),
                        max_length=180,
                    ),
                }
            )
        return examples

    def _fallback_triz_summary(self, recommendations: list[dict[str, str]]) -> str:
        names = [item["name"] for item in recommendations if item.get("name")]
        if not names:
            return "TRIZ did not produce enough concise recommendations for this problem."
        return "TRIZ points toward " + ", ".join(names[:3]) + "."

    def _fallback_analogy_summary(self, examples: list[dict[str, str]]) -> str:
        domains = [item["source_domain"] for item in examples if item.get("source_domain")]
        if not domains:
            return "Design by Analogy did not produce enough concise examples for this problem."
        return (
            "Design by Analogy suggests borrowing mechanisms from "
            + ", ".join(domains[:3])
            + "."
        )

    def _build_final_answer(
        self,
        triz_recommendations: list[dict[str, str]],
        analogy_examples: list[dict[str, str]],
    ) -> str:
        triz_names = [item["name"] for item in triz_recommendations if item.get("name")]
        analogy_domains = [
            item["source_domain"]
            for item in analogy_examples
            if item.get("source_domain")
        ]
        if triz_names and analogy_domains:
            return (
                f"Combine {self._natural_join(triz_names[:2])} with analogy-inspired "
                f"mechanisms from {self._natural_join(analogy_domains[:2])}."
            )
        if triz_names:
            return f"Prioritize {self._natural_join(triz_names[:3])}."
        if analogy_domains:
            return f"Use analogy-inspired mechanisms from {self._natural_join(analogy_domains[:3])}."
        return (
            "No concise recommendation is available; rerun with debug=true to "
            "inspect the raw MCP output."
        )

    def _natural_join(self, values: list[str]) -> str:
        if len(values) <= 1:
            return values[0] if values else ""
        if len(values) == 2:
            return f"{values[0]} and {values[1]}"
        return ", ".join(values[:-1]) + f", and {values[-1]}"

    def _shorten_text(self, text: Any, max_length: int = 220) -> str:
        if text is None:
            return ""
        compact = " ".join(str(text).split())
        if len(compact) <= max_length:
            return compact
        return compact[: max_length - 1].rstrip(" .,;:") + "..."

    def _sanitize_value(self, value: Any) -> Any:
        if isinstance(value, list):
            return [self._sanitize_value(item) for item in value]
        if not isinstance(value, dict):
            return value

        sanitized = {}
        for key, item in value.items():
            if key == "domain_relevance":
                sanitized[key] = self._validation_summary(item)
            elif key == "raw_response":
                continue
            elif key in {"problem_keywords", "candidate_keywords", "overlap_keywords", "overlap_ratio", "has_domain_anchor", "is_placeholder", "matched_problem_phrases"}:
                continue
            elif key == "original_mcp_validation":
                continue
            else:
                sanitized[key] = self._sanitize_value(item)
        return sanitized

    def _validation_summary(self, value: Any) -> Any:
        if not isinstance(value, dict):
            return value
        if "is_relevant" in value:
            return {
                "is_relevant": value.get("is_relevant"),
                "reason": value.get("reason", "Candidate passed relevance validation."),
            }
        return {
            "valid_candidate_count": value.get("valid_candidate_count", 0),
            "irrelevant_candidate_count": value.get("irrelevant_candidate_count", 0),
            "repair_performed": value.get("repair_performed", False),
            "summary": self._validation_summary_text(value),
        }

    def _validation_summary_text(self, value: dict[str, Any]) -> str:
        valid_count = value.get("valid_candidate_count", 0)
        original_validation = value.get("original_mcp_validation") or {}
        irrelevant_count = original_validation.get(
            "irrelevant_candidate_count",
            value.get("irrelevant_candidate_count", 0),
        )
        if value.get("repair_performed"):
            return (
                f"{valid_count} relevant candidates are available after replacing "
                f"{irrelevant_count} irrelevant or placeholder candidates."
            )
        return f"{valid_count} relevant candidates passed validation."
