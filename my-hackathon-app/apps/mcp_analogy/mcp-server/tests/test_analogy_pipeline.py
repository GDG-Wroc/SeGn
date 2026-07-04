import unittest
from pathlib import Path
import sys


sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.analogy_pipeline import DesignByAnalogyPipeline


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

EWASTE_QUERY = (
    "Every year, people buy more phones, laptops, and electronic devices, and every "
    "year more of them are thrown away. Most of these devices are manufactured to "
    "be affordable, compact, and quick to produce, which shapes how they're "
    "assembled and what materials go into them. Once discarded, only a small "
    "fraction of this waste is properly collected and processed, and the rest is "
    "shipped informally, buried, or scrapped in ways that release toxic materials "
    "into the environment. Valuable materials like rare earths, copper, and gold "
    "are being lost or turned into a health hazard instead of recovered. Your task: "
    "propose a way to significantly increase the safe, effective recovery of "
    "materials from discarded electronics. And remember, I still want to buy this "
    "newest phone every year!"
)


class DesignByAnalogyPipelineTests(unittest.IsolatedAsyncioTestCase):
    async def test_wastewater_pipeline_returns_domain_grounded_candidates(self) -> None:
        result = await DesignByAnalogyPipeline().run(WASTEWATER_QUERY, 3)

        self.assertTrue(result["is_successful"])
        self.assertGreaterEqual(result["candidate_count"], 3)

        candidates = result["candidates"]
        names = " ".join(candidate["solution_name"] for candidate in candidates).lower()
        self.assertIn("kidney-inspired distributed filtration", names)
        self.assertIn("wetland-inspired biological polishing", names)
        self.assertIn("gut-microbiome-inspired staged treatment", names)

        forbidden = [
            "citi produce enormou",
            "cities produce enormous",
            "packaging",
            "protective surface",
            "recyclable material",
            "compostable liner",
            "seed pod end-of-use trigger",
            "honeycomb lightweight cellular structure",
            "concrete mechanism / prototypeable concept",
        ]
        for candidate in candidates:
            self.assertEqual(candidate["method"], "Design by Analogy")
            self.assertIn("wastewater", candidate["solution_description"].lower())
            candidate_text = str(candidate).lower()
            for term in forbidden:
                self.assertNotIn(term, candidate_text)

    async def test_ewaste_pipeline_uses_meaningful_target_and_concrete_analogies(self) -> None:
        result = await DesignByAnalogyPipeline().run(EWASTE_QUERY, 3)

        self.assertTrue(result["is_successful"])
        self.assertGreaterEqual(result["candidate_count"], 3)
        self.assertIn("discarded consumer electronics", result["summary"].lower())

        forbidden = [
            "year people buy",
            "for converting every",
            "for converting year",
            "for converting people",
            "create a target-domain solution",
            "uses distributed roles, feedback, thresholds, or modular variation",
        ]
        required_terms = [
            "electronics",
            "e-waste",
            "devices",
            "recovery",
            "recycling",
            "disassembly",
            "materials",
            "collection",
        ]

        examples = result["analogy_examples"]
        self.assertGreaterEqual(len(examples), 3)
        for example in examples:
            self.assertTrue(example["source_domain"])
            self.assertTrue(example["analogy_mechanism"])
            self.assertTrue(example["mapped_solution"])

            source_domain = example["source_domain"].lower()
            mapped_solution = example["mapped_solution"].lower()
            combined_text = f"{source_domain} {mapped_solution}"
            for term in forbidden:
                self.assertNotIn(term, combined_text)
            self.assertTrue(
                any(term in mapped_solution for term in required_terms),
                mapped_solution,
            )


if __name__ == "__main__":
    unittest.main()
