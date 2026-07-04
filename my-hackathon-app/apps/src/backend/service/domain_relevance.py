import re
from typing import Any


STOP_WORDS = {
    "about",
    "above",
    "across",
    "after",
    "against",
    "also",
    "because",
    "before",
    "being",
    "between",
    "cannot",
    "could",
    "different",
    "does",
    "doing",
    "each",
    "every",
    "from",
    "have",
    "into",
    "itself",
    "limited",
    "many",
    "more",
    "most",
    "must",
    "need",
    "needs",
    "only",
    "one",
    "other",
    "particularly",
    "problem",
    "propose",
    "requires",
    "same",
    "should",
    "significant",
    "similar",
    "solution",
    "substantial",
    "system",
    "task",
    "than",
    "the",
    "that",
    "their",
    "there",
    "these",
    "this",
    "through",
    "under",
    "using",
    "very",
    "what",
    "when",
    "where",
    "which",
    "while",
    "with",
    "without",
    "would",
    "your",
}

class DomainRelevanceValidator:
    """Checks whether generated candidates still refer to the current problem."""

    def validate(
        self,
        original_problem: str,
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        problem_keywords = self.extract_keywords(original_problem)
        valid_candidates = []
        irrelevant_candidates = []

        for candidate in candidates:
            result = self.validate_candidate(original_problem, candidate, problem_keywords)
            enriched = {**candidate, "domain_relevance": result}
            if result["is_relevant"]:
                valid_candidates.append(enriched)
            else:
                irrelevant_candidates.append(enriched)

        return {
            "problem_keywords": sorted(problem_keywords),
            "valid_candidates": valid_candidates,
            "irrelevant_candidates": irrelevant_candidates,
            "valid_candidate_count": len(valid_candidates),
            "irrelevant_candidate_count": len(irrelevant_candidates),
            "validation_rule": (
                "A candidate is relevant only if its important concepts overlap with "
                "the important concepts extracted from the current original problem."
            ),
        }

    def validate_analogy_candidates(
        self,
        original_problem: str,
        candidates: list[dict[str, Any]],
    ) -> dict[str, Any]:
        problem_keywords = self.extract_keywords(original_problem)
        valid_candidates = []
        irrelevant_candidates = []

        for candidate in candidates:
            result = self.validate_analogy_candidate(
                original_problem,
                candidate,
                problem_keywords,
            )
            enriched = {**candidate, "domain_relevance": result}
            if result["is_relevant"]:
                valid_candidates.append(enriched)
            else:
                irrelevant_candidates.append(enriched)

        return {
            "problem_keywords": sorted(problem_keywords),
            "valid_candidates": valid_candidates,
            "irrelevant_candidates": irrelevant_candidates,
            "valid_candidate_count": len(valid_candidates),
            "irrelevant_candidate_count": len(irrelevant_candidates),
            "validation_rule": (
                "A Design by Analogy candidate is valid when it has a source domain, "
                "a clear analogy mechanism, and a mapped solution that addresses the "
                "original problem. Source-domain keyword overlap is not required."
            ),
        }

    def validate_analogy_candidate(
        self,
        original_problem: str,
        candidate: dict[str, Any],
        problem_keywords: set[str] | None = None,
    ) -> dict[str, Any]:
        problem_keywords = problem_keywords or self.extract_keywords(original_problem)
        source_domain = self._first_text(
            candidate,
            ["source_domain", "source_analogy"],
        )
        mechanism = self._first_text(
            candidate,
            ["analogy", "mechanism", "analogy_mechanism", "analogical_mechanism"],
        )
        mapped_solution = self._first_text(
            candidate,
            ["mapped_solution", "solution_description", "solution_name"],
        )
        why_it_fits = self._first_text(
            candidate,
            ["why_it_fits_original_problem", "why_it_addresses_original_problem"],
        )
        mapped_text = f"{mapped_solution} {why_it_fits}".strip()
        mapped_keywords = self.extract_keywords(mapped_text)
        overlap = problem_keywords & mapped_keywords
        problem_signal = self._problem_phrase_signal(original_problem, mapped_text)
        is_placeholder = self._is_placeholder(self._candidate_text(candidate))
        vague_terms = {"improve", "optimize", "innovative", "better", "solution"}
        non_vague_keywords = mapped_keywords - vague_terms

        rejection_reasons = []
        if not source_domain:
            rejection_reasons.append("missing source domain")
        if not mechanism:
            rejection_reasons.append("missing clear analogy mechanism")
        if not mapped_solution:
            rejection_reasons.append("missing mapped solution")
        if is_placeholder:
            rejection_reasons.append("contains placeholder or copied problem text")
        if mapped_solution and len(non_vague_keywords) < 3:
            rejection_reasons.append("mapped solution is too vague")
        if mapped_solution and not (problem_signal or len(overlap) >= 2):
            rejection_reasons.append("mapped solution does not address the original problem")

        is_relevant = not rejection_reasons
        return {
            "is_relevant": is_relevant,
            "reason": (
                "Analogy has a source domain, mechanism, and mapped solution tied to the original problem."
                if is_relevant
                else "; ".join(rejection_reasons)
            ),
            "rejection_reasons": rejection_reasons,
            "problem_keywords": sorted(problem_keywords),
            "mapped_solution_keywords": sorted(mapped_keywords),
            "overlap_keywords": sorted(overlap),
            "is_placeholder": is_placeholder,
            "matched_problem_phrases": problem_signal,
        }

    def validate_candidate(
        self,
        original_problem: str,
        candidate: dict[str, Any],
        problem_keywords: set[str] | None = None,
    ) -> dict[str, Any]:
        problem_keywords = problem_keywords or self.extract_keywords(original_problem)
        core_problem_keywords = set(self.extract_keywords_ordered(original_problem)[:12])
        candidate_text = self._candidate_text(candidate)
        candidate_keywords = self.extract_keywords(candidate_text)

        overlap = problem_keywords & candidate_keywords
        problem_signal = self._problem_phrase_signal(original_problem, candidate_text)
        overlap_ratio = len(overlap) / max(1, len(problem_keywords))
        has_domain_anchor = bool(core_problem_keywords & candidate_keywords)
        is_placeholder = self._is_placeholder(candidate_text)

        is_relevant = (
            not is_placeholder
            and (bool(problem_signal) or has_domain_anchor or len(overlap) >= 2 or overlap_ratio >= 0.2)
        )
        reason = (
            "Candidate shares domain concepts with the original problem."
            if is_relevant
            else "Candidate does not share enough important concepts with the original problem."
        )

        return {
            "is_relevant": is_relevant,
            "reason": reason,
            "problem_keywords": sorted(problem_keywords),
            "candidate_keywords": sorted(candidate_keywords),
            "overlap_keywords": sorted(overlap),
            "overlap_ratio": round(overlap_ratio, 3),
            "has_domain_anchor": has_domain_anchor,
            "is_placeholder": is_placeholder,
            "matched_problem_phrases": problem_signal,
        }

    def extract_keywords(self, text: str) -> set[str]:
        return set(self.extract_keywords_ordered(text))

    def extract_keywords_ordered(self, text: str) -> list[str]:
        words = re.findall(r"[A-Za-z][A-Za-z-]{2,}", text.lower())
        seen = set()
        keywords = []
        for word in words:
            normalized = self._normalize(word)
            if (
                len(normalized) >= 4
                and normalized not in STOP_WORDS
                and normalized not in seen
            ):
                seen.add(normalized)
                keywords.append(normalized)
        return keywords

    def _candidate_text(self, candidate: dict[str, Any]) -> str:
        parts: list[str] = []
        for value in candidate.values():
            if isinstance(value, str):
                parts.append(value)
            elif isinstance(value, list):
                parts.extend(str(item) for item in value)
            elif isinstance(value, dict):
                parts.append(self._candidate_text(value))
        return " ".join(parts)

    def _first_text(self, candidate: dict[str, Any], keys: list[str]) -> str:
        for key in keys:
            value = candidate.get(key)
            if isinstance(value, str) and value.strip():
                return value.strip()
        return ""

    def _problem_phrase_signal(self, original_problem: str, candidate_text: str) -> list[str]:
        candidate_lower = candidate_text.lower()
        phrases = []
        for phrase in re.findall(r"[A-Za-z][A-Za-z-]+(?:\s+[A-Za-z][A-Za-z-]+){1,3}", original_problem):
            normalized_words = [
                self._normalize(word)
                for word in re.findall(r"[A-Za-z][A-Za-z-]{2,}", phrase.lower())
            ]
            useful_words = [
                word
                for word in normalized_words
                if word not in STOP_WORDS
            ]
            if len(useful_words) >= 2 and " ".join(useful_words) in candidate_lower:
                phrases.append(" ".join(useful_words))
        return phrases[:5]

    def _normalize(self, word: str) -> str:
        word = word.strip("-").lower()
        for suffix in ("ization", "isation", "ations", "ments", "ness", "ingly", "ing", "ers", "ies", "ed", "es"):
            if len(word) > len(suffix) + 3 and word.endswith(suffix):
                return word[: -len(suffix)]
        if len(word) > 5 and word.endswith("s") and not word.endswith("ss"):
            return word[:-1]
        return word

    def _is_placeholder(self, text: str) -> bool:
        lower = text.lower()
        placeholders = [
            "analogical protect concept",
            "analogical adapt concept",
            "variable configuration for",
            "systems for protecting",
            "glowny parametr",
            "the stated target domain",
            "citi produce enormou",
            "cities produce enormous",
            "concrete mechanism / prototypeable concept",
            "honeycomb inspired citi",
            "skin inspired citi",
            "seed pod inspired citi",
        ]
        return any(placeholder in lower for placeholder in placeholders)
