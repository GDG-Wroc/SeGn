from typing import Any


class ResponseBuilder:
    def build_user_response(
        self,
        original_problem: str,
        triz_result: dict[str, Any],
        analogy_result: dict[str, Any],
    ) -> dict[str, Any]:
        return {
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
