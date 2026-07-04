import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from backend.service.orchestrator import MCPOrchestrator
from backend.service.response_builder import ResponseBuilder


WASTEWATER_QUERY = (
    "Cities produce enormous volumes of wastewater daily, and treatment plants must "
    "process all of it to keep up with demand from growing populations. Treatment "
    "plants vary widely in how thoroughly they can purify water before releasing or "
    "reusing it, and many cities, especially fast-growing ones, struggle to treat "
    "their full wastewater volume to a consistently safe standard. Inadequately "
    "treated water returns to rivers, aquifers, and drinking supplies, spreading "
    "disease and damaging ecosystems. Your task: propose a way to treat "
    "significantly more wastewater to a safe standard without the massive cost or "
    "time investment of traditional plant expansion (we can treat more, but the "
    "quality will drop). And stop taking showers is NOT a solution here."
)


class DesignByAnalogyResponseTests(unittest.TestCase):
    def test_wastewater_response_contains_three_analogy_examples(self) -> None:
        orchestrator = MCPOrchestrator(triz_mcp=None, analogy_mcp=None)
        analogy_result = orchestrator._format_analogy_response(
            WASTEWATER_QUERY,
            {
                "status": "success",
                "raw_response": {
                    "summary": "",
                    "analogy_examples": [],
                    "candidates": [],
                    "is_successful": True,
                },
            },
        )

        response = ResponseBuilder().build_user_response(
            WASTEWATER_QUERY,
            self._triz_result(),
            analogy_result,
        )

        assert response["design_by_analogy"]["analogy_examples"]
        assert len(response["design_by_analogy"]["analogy_examples"]) >= 3
        assert response["design_by_analogy"]["summary"]

        for example in response["design_by_analogy"]["analogy_examples"]:
            assert example["source_domain"]
            assert example["analogy"]
            assert example["mapped_solution"]

    def test_parser_accepts_requested_analogy_examples_schema(self) -> None:
        orchestrator = MCPOrchestrator(triz_mcp=None, analogy_mcp=None)
        analogy_result = orchestrator._format_analogy_response(
            WASTEWATER_QUERY,
            {
                "status": "success",
                "raw_response": {
                    "summary": "Analogy examples map external mechanisms back to wastewater capacity.",
                    "analogy_examples": [
                        {
                            "source_domain": "Biology / kidneys",
                            "source_analogy": "Kidney nephron",
                            "analogy_mechanism": "Parallel staged filtration cleans fluid continuously.",
                            "mapped_solution": "Use modular wastewater pretreatment and polishing stages before central release.",
                            "why_it_fits_original_problem": "It treats more wastewater while preserving safe quality.",
                        },
                        {
                            "source_domain": "Ecosystems / wetlands",
                            "source_analogy": "Constructed wetland",
                            "analogy_mechanism": "Distributed biological filtration removes contaminants slowly.",
                            "mapped_solution": "Add biofiltration polishing zones to increase safe wastewater treatment capacity.",
                            "why_it_fits_original_problem": "It increases treatment without traditional plant expansion.",
                        },
                        {
                            "source_domain": "Software / load balancing",
                            "source_analogy": "Load balancer",
                            "analogy_mechanism": "Traffic is routed across available servers by capacity.",
                            "mapped_solution": "Route wastewater across side-stream modules, storage, and polishing paths by capacity and quality.",
                            "why_it_fits_original_problem": "It avoids overloading one treatment path and quality drop.",
                        },
                    ],
                    "is_successful": True,
                },
            },
        )

        response = ResponseBuilder().build_user_response(
            WASTEWATER_QUERY,
            self._triz_result(),
            analogy_result,
        )

        self.assertEqual(len(response["design_by_analogy"]["analogy_examples"]), 3)

    def _triz_result(self) -> dict:
        return {
            "status": "success",
            "recommendation": {
                "summary": "TRIZ suggests increasing capacity through modularity and routing.",
                "parameters": [],
                "recommended_directions": [
                    {
                        "solution_name": "Upstream pretreatment",
                        "solution_description": "Reduce load before wastewater reaches the main plant.",
                        "why_it_fits_original_problem": "It prevents overload while preserving quality.",
                    },
                    {
                        "solution_name": "Modular side-stream units",
                        "solution_description": "Add parallel treatment modules.",
                        "why_it_fits_original_problem": "It adds capacity without full expansion.",
                    },
                    {
                        "solution_name": "Adaptive routing",
                        "solution_description": "Route flow based on quality and capacity.",
                        "why_it_fits_original_problem": "It avoids forcing all flow through one path.",
                    },
                ],
            },
            "raw_response": {},
        }


if __name__ == "__main__":
    unittest.main()
