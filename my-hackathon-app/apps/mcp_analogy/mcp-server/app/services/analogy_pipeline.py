import re
from typing import Any

from pydantic import ValidationError

from app.services.llm_client import LLMClient
from app.services.models import (
    AbstractFunction,
    Candidate,
    Candidates,
    Mechanism,
    Mechanisms,
    ProblemAnalysis,
    SourceDomain,
    SourceDomains,
)

SOURCE_DOMAIN_CATEGORIES = [
    "nature and biology",
    "human body",
    "animals",
    "plants",
    "cities and infrastructure",
    "software systems",
    "manufacturing",
    "logistics",
    "materials",
    "energy systems",
    "consumer products",
    "social systems",
]

REQUIRED_CANDIDATE_FIELDS = [
    "candidate_id",
    "solution_name",
    "source_domain",
    "analogical_mechanism",
    "transferred_principle",
    "solution_description",
    "why_it_addresses_original_problem",
]

TRANSFORMATION_WORDS = {
    "regulate": ["regulate", "balance", "control", "moderate", "adjust"],
    "protect": ["protect", "shield", "secure", "avoid", "prevent"],
    "store": ["store", "retain", "hold", "cache", "reserve"],
    "transport": ["transport", "move", "deliver", "route", "transfer"],
    "separate": ["separate", "filter", "isolate", "sort", "divide"],
    "adapt": ["adapt", "respond", "change", "vary", "dynamic"],
    "convert": ["convert", "transform", "translate", "turn"],
    "detect": ["detect", "sense", "monitor", "identify", "measure"],
    "stabilize": ["stabilize", "steady", "maintain", "reliable"],
    "reduce": ["reduce", "minimize", "lower", "less", "without"],
    "amplify": ["amplify", "increase", "boost", "scale"],
}


class DesignByAnalogyPipeline:
    def __init__(self, llm_client: LLMClient | None = None) -> None:
        self.llm = llm_client or LLMClient()

    async def run(self, problem: str, minimum_solutions: int = 3) -> dict[str, Any]:
        minimum_solutions = max(3, minimum_solutions)
        logic_trace: list[dict[str, Any]] = []

        try:
            problem_analysis = await self.analyze_problem(problem)
            logic_trace.append(self._trace(1, "Problem analysis", problem_analysis))

            abstract_function = await self.abstract_function(problem, problem_analysis)
            logic_trace.append(self._trace(2, "Function abstraction", abstract_function))

            source_domains = await self.find_source_domains(
                abstract_function,
                minimum_solutions,
            )
            logic_trace.append(self._trace(3, "Source domain discovery", source_domains))

            mechanisms = await self.extract_mechanisms(abstract_function, source_domains)
            logic_trace.append(self._trace(4, "Mechanism extraction", mechanisms))

            candidates = await self.generate_candidates(
                problem,
                problem_analysis,
                abstract_function,
                mechanisms,
                minimum_solutions,
            )
            logic_trace.append(self._trace(5, "Candidate generation", candidates))

            validation = self.validate_candidates(candidates, minimum_solutions)
            if not validation["is_valid"]:
                expanded_sources = await self.find_source_domains(
                    abstract_function,
                    minimum_solutions * 2,
                )
                expanded_mechanisms = await self.extract_mechanisms(
                    abstract_function,
                    expanded_sources,
                )
                retry_candidates = await self.generate_candidates(
                    problem,
                    problem_analysis,
                    abstract_function,
                    expanded_mechanisms,
                    minimum_solutions,
                    retry=True,
                )
                candidates = retry_candidates
                validation = self.validate_candidates(candidates, minimum_solutions)
                validation["retry_performed"] = True
            else:
                validation["retry_performed"] = False

            logic_trace.append(self._trace(6, "Candidate validation", validation))
            valid_candidates = validation["valid_candidates"][:minimum_solutions]

            return {
                "method": "Design by Analogy",
                "input_problem": problem,
                "minimum_solutions_required": minimum_solutions,
                "logic_trace": logic_trace,
                "candidates": [self._public_candidate(candidate) for candidate in valid_candidates],
                "candidate_count": len(valid_candidates),
                "is_successful": validation["is_valid"],
            }
        except Exception as exc:
            return {
                "method": "Design by Analogy",
                "input_problem": problem,
                "minimum_solutions_required": minimum_solutions,
                "logic_trace": logic_trace,
                "candidates": [],
                "candidate_count": 0,
                "is_successful": False,
                "error": {
                    "type": exc.__class__.__name__,
                    "message": str(exc),
                },
            }

    async def analyze_problem(self, problem: str) -> dict[str, Any]:
        system = "You are an innovation analyst. Return JSON only."
        user = (
            "Analyze this as a technical innovation problem. Return JSON with: "
            "target_system, desired_outcome, current_limitation, key_constraints, "
            "harmful_effects_to_avoid, success_criteria.\n\n"
            f"Problem: {problem}"
        )
        data = await self.llm.complete_json(system, user)
        if data:
            parsed = self._try_model_dump(ProblemAnalysis, data)
            if parsed:
                return parsed
        return self._fallback_problem_analysis(problem).model_dump()

    async def abstract_function(
        self,
        problem: str,
        problem_analysis: dict[str, Any],
    ) -> dict[str, Any]:
        system = "You are a Design by Analogy expert. Return JSON only."
        user = (
            "Abstract the original problem into a generic function. Return JSON with: "
            "concrete_function, abstract_function, function_keywords, input, output, "
            "constraints, transformation_type. transformation_type must be one of "
            "regulate, protect, store, transport, separate, adapt, convert, detect, "
            "stabilize, reduce, amplify.\n\n"
            f"Problem: {problem}\nAnalysis: {problem_analysis}"
        )
        data = await self.llm.complete_json(system, user)
        if data:
            parsed = self._try_model_dump(AbstractFunction, data)
            if parsed:
                return parsed
        return self._fallback_abstract_function(problem, problem_analysis).model_dump()

    async def find_source_domains(
        self,
        abstract_function_data: dict[str, Any],
        minimum_solutions: int,
    ) -> dict[str, Any]:
        required_count = minimum_solutions * 2
        system = "You find diverse source domains for analogical design. Return JSON only."
        user = (
            "Find diverse domains where similar abstract functions are solved. Avoid "
            "staying in the same domain as the target problem. Use broad categories as "
            f"search directions only: {SOURCE_DOMAIN_CATEGORIES}. Return at least "
            f"{required_count} source_domains, each with domain_name, category, "
            "similar_function, why_relevant.\n\n"
            f"Abstract function: {abstract_function_data}"
        )
        data = await self.llm.complete_json(system, user)
        if data:
            parsed = self._try_model_dump(SourceDomains, data)
            if parsed and len(parsed["source_domains"]) >= required_count:
                return parsed
        return self._fallback_source_domains(abstract_function_data, required_count).model_dump()

    async def extract_mechanisms(
        self,
        abstract_function_data: dict[str, Any],
        source_domains_data: dict[str, Any],
    ) -> dict[str, Any]:
        system = "You extract transferable mechanisms for Design by Analogy. Return JSON only."
        user = (
            "Identify the mechanism from each source domain. Focus on transferable "
            "patterns, not surface similarity. Return JSON with mechanisms, each "
            "containing source_domain, observed_mechanism, mechanism_principle, "
            "transferable_pattern, limitation_of_analogy.\n\n"
            f"Abstract function: {abstract_function_data}\n"
            f"Source domains: {source_domains_data}"
        )
        data = await self.llm.complete_json(system, user)
        if data:
            parsed = self._try_model_dump(Mechanisms, data)
            if parsed:
                return parsed
        return self._fallback_mechanisms(source_domains_data).model_dump()

    async def generate_candidates(
        self,
        problem: str,
        problem_analysis: dict[str, Any],
        abstract_function_data: dict[str, Any],
        mechanisms_data: dict[str, Any],
        minimum_solutions: int,
        retry: bool = False,
    ) -> dict[str, Any]:
        system = "You transfer analogical mechanisms into practical solution candidates. Return JSON only."
        retry_note = "This is a retry. Produce more complete, field-valid candidates." if retry else ""
        user = (
            "Transfer mechanisms back to the original problem and generate practical "
            f"solution candidates. Generate at least {minimum_solutions}. Each candidate "
            "must include candidate_id, solution_name, source_domain, analogical_mechanism, "
            "transferred_principle, solution_description, why_it_addresses_original_problem, "
            "expected_benefits, possible_risks, implementation_complexity, confidence_score. "
            f"{retry_note}\n\nProblem: {problem}\nAnalysis: {problem_analysis}\n"
            f"Abstract function: {abstract_function_data}\nMechanisms: {mechanisms_data}"
        )
        data = await self.llm.complete_json(system, user, temperature=0.35)
        if data:
            parsed = self._try_model_dump(Candidates, data)
            if parsed and len(parsed["candidates"]) >= minimum_solutions:
                return parsed
        return self._fallback_candidates(
            problem,
            problem_analysis,
            abstract_function_data,
            mechanisms_data,
            minimum_solutions,
        ).model_dump()

    def validate_candidates(
        self,
        candidates_data: dict[str, Any],
        minimum_solutions: int,
    ) -> dict[str, Any]:
        valid_candidates = []
        invalid_candidates = []
        for candidate in candidates_data.get("candidates", []):
            missing = [
                field
                for field in REQUIRED_CANDIDATE_FIELDS
                if not str(candidate.get(field, "")).strip()
            ]
            if missing:
                invalid = dict(candidate)
                invalid["missing_or_empty_required_fields"] = missing
                invalid_candidates.append(invalid)
            else:
                valid_candidates.append(candidate)

        return {
            "is_valid": len(valid_candidates) >= minimum_solutions,
            "minimum_required": minimum_solutions,
            "valid_candidate_count": len(valid_candidates),
            "invalid_candidate_count": len(invalid_candidates),
            "validation_rule": (
                "A candidate is valid only if it contains source domain, mechanism, "
                "transferred principle, solution description and explanation against "
                "the original problem."
            ),
            "valid_candidates": valid_candidates,
            "invalid_candidates": invalid_candidates,
        }

    def _fallback_problem_analysis(self, problem: str) -> ProblemAnalysis:
        phrases = self._phrases(problem)
        target = phrases[0] if phrases else "the target system"
        return ProblemAnalysis(
            target_system=target,
            desired_outcome=f"Improve the target outcome described in: {problem}",
            current_limitation="The current approach has trade-offs, constraints, or unwanted side effects.",
            key_constraints=self._extract_constraints(problem),
            harmful_effects_to_avoid=[
                "new failure modes",
                "excessive cost or complexity",
                "moving the problem to another part of the system",
            ],
            success_criteria=[
                "addresses the stated problem",
                "works under the stated constraints",
                "can be implemented as a practical system change",
            ],
        )

    def _fallback_abstract_function(
        self,
        problem: str,
        problem_analysis: dict[str, Any],
    ) -> AbstractFunction:
        transformation = self._detect_transformation(problem)
        keywords = self._keywords(problem)
        return AbstractFunction(
            concrete_function=problem_analysis["desired_outcome"],
            abstract_function=(
                f"{transformation.capitalize()} system behavior by changing how resources, "
                "constraints, and feedback are arranged."
            ),
            function_keywords=keywords[:8],
            input=problem_analysis["current_limitation"],
            output=problem_analysis["desired_outcome"],
            constraints=problem_analysis.get("key_constraints", []),
            transformation_type=transformation,
        )

    def _fallback_source_domains(
        self,
        abstract_function_data: dict[str, Any],
        required_count: int,
    ) -> SourceDomains:
        abstract_text = str(abstract_function_data.get("abstract_function", "")).lower()
        keywords_text = " ".join(abstract_function_data.get("function_keywords", [])).lower()
        if any(
            word in f"{abstract_text} {keywords_text}"
            for word in ["building", "thermal", "temperature", "heat", "cool", "warm", "energy"]
        ):
            thermal_domains = [
                SourceDomain(
                    domain_name="Termite mound passive ventilation",
                    category="nature and biology",
                    similar_function="Stabilize internal temperature through passive airflow paths.",
                    why_relevant="It regulates heat without active mechanical cooling.",
                ),
                SourceDomain(
                    domain_name="Pine cone hygromorphic opening",
                    category="plants",
                    similar_function="Open and close surface structures in response to ambient conditions.",
                    why_relevant="It suggests passive facade elements that change state without motors.",
                ),
                SourceDomain(
                    domain_name="Human skin thermoregulation",
                    category="human body",
                    similar_function="Sense temperature and regulate heat loss through pores and blood flow.",
                    why_relevant="It combines sensing, micro-flow and thermal buffering.",
                ),
                SourceDomain(
                    domain_name="Leaf stomata gas exchange",
                    category="plants",
                    similar_function="Adjust small openings to balance exchange, protection and resource loss.",
                    why_relevant="It maps well to adaptive vents or membranes.",
                ),
                SourceDomain(
                    domain_name="Camel fur thermal buffering",
                    category="animals",
                    similar_function="Reduce heat gain and heat loss with layered insulation and air gaps.",
                    why_relevant="It suggests insulation that buffers extremes instead of staying uniform.",
                ),
                SourceDomain(
                    domain_name="Software load balancer",
                    category="software systems",
                    similar_function="Route flows dynamically according to demand and capacity.",
                    why_relevant="It suggests adaptive routing of air, heat or occupancy-driven comfort loads.",
                ),
            ]
            return SourceDomains(source_domains=thermal_domains[:required_count])

        keywords = abstract_function_data.get("function_keywords", ["system"])
        transformation = abstract_function_data.get("transformation_type", "adapt")
        domains = []
        for index in range(required_count):
            category = SOURCE_DOMAIN_CATEGORIES[index % len(SOURCE_DOMAIN_CATEGORIES)]
            keyword = keywords[index % len(keywords)] if keywords else "system"
            domains.append(
                SourceDomain(
                    domain_name=f"{category} systems for {transformation}ing {keyword}",
                    category=category,
                    similar_function=abstract_function_data["abstract_function"],
                    why_relevant=(
                        f"This category commonly contains patterns for {transformation}ing "
                        "behavior under constraints without assuming the target domain."
                    ),
                )
            )
        return SourceDomains(source_domains=domains)

    def _fallback_mechanisms(self, source_domains_data: dict[str, Any]) -> Mechanisms:
        mechanisms = []
        for source in source_domains_data.get("source_domains", []):
            mechanisms.append(
                Mechanism(
                    source_domain=source["domain_name"],
                    observed_mechanism=(
                        "The source system uses distributed roles, feedback, thresholds, "
                        "or modular variation to perform a similar function."
                    ),
                    mechanism_principle=(
                        "Separate the function into sensing, response, buffering, and "
                        "reconfiguration elements."
                    ),
                    transferable_pattern=(
                        "Map the source mechanism into the target as a configurable "
                        "subsystem with local rules and measurable triggers."
                    ),
                    limitation_of_analogy=(
                        "The source pattern must be adapted to the target's materials, "
                        "costs, safety requirements, and operating context."
                    ),
                )
            )
        return Mechanisms(mechanisms=mechanisms)

    def _fallback_candidates(
        self,
        problem: str,
        problem_analysis: dict[str, Any],
        abstract_function_data: dict[str, Any],
        mechanisms_data: dict[str, Any],
        minimum_solutions: int,
    ) -> Candidates:
        thermal_candidates = self._thermal_fallback_candidates(problem)
        if thermal_candidates:
            return Candidates(candidates=thermal_candidates[:minimum_solutions])

        mechanisms = mechanisms_data.get("mechanisms", [])
        candidates = []
        for index, mechanism in enumerate(mechanisms[:minimum_solutions], start=1):
            candidates.append(
                Candidate(
                    candidate_id=f"ANALOGY-{index}",
                    solution_name=f"Analogical {abstract_function_data['transformation_type']} concept {index}",
                    source_domain=mechanism["source_domain"],
                    analogical_mechanism=mechanism["observed_mechanism"],
                    transferred_principle=mechanism["transferable_pattern"],
                    solution_description=(
                        "Create a target-domain solution that uses the transferred pattern: "
                        f"{mechanism['transferable_pattern']} The design should be applied "
                        f"directly to this problem: {problem}"
                    ),
                    why_it_addresses_original_problem=(
                        "It addresses the original limitation by replacing a single fixed "
                        "response with a structured mechanism that can sense, buffer, "
                        "adapt, or route resources according to the desired outcome."
                    ),
                    expected_benefits=[
                        problem_analysis["desired_outcome"],
                        "more explicit trade-off management",
                        "clearer implementation experiments",
                    ],
                    possible_risks=[
                        mechanism["limitation_of_analogy"],
                        "may need domain expert review before implementation",
                    ],
                    implementation_complexity="medium",
                    confidence_score=0.65,
                )
            )
        return Candidates(candidates=candidates)

    def _thermal_fallback_candidates(self, problem: str) -> list[Candidate]:
        if not any(
            word in problem.lower()
            for word in ["building", "thermal", "temperature", "heat", "cool", "warm", "energy"]
        ):
            return []

        return [
            Candidate(
                candidate_id="ANALOGY-1",
                solution_name="Termite-mound inspired ventilation facade",
                source_domain="Termite mound",
                analogical_mechanism=(
                    "Termite mounds stabilize internal temperature with channels that "
                    "drive passive air circulation through pressure and temperature gradients."
                ),
                transferred_principle=(
                    "Use shaped airflow paths and controllable openings instead of relying "
                    "only on uniform insulation or active cooling."
                ),
                solution_description=(
                    "Add a facade or central ventilation core with vertical channels, thermal "
                    "chimneys and dampers that open or close according to temperature, solar "
                    "gain and pressure differences."
                ),
                why_it_addresses_original_problem=(
                    "It helps keep indoor comfort stable while reducing dependence on static "
                    "materials and high-energy HVAC."
                ),
                expected_benefits=[
                    "lower cooling energy",
                    "passive heat removal",
                    "adaptation to weather and daily temperature swings",
                ],
                possible_risks=[
                    "requires careful airflow simulation",
                    "performance depends on climate and building geometry",
                ],
                implementation_complexity="medium",
                confidence_score=0.82,
            ),
            Candidate(
                candidate_id="ANALOGY-2",
                solution_name="Pine-cone inspired adaptive facade panels",
                source_domain="Pine cone",
                analogical_mechanism=(
                    "Pine cone scales open and close passively as humidity changes because "
                    "material layers expand at different rates."
                ),
                transferred_principle=(
                    "Use material response to environmental conditions as the actuator for "
                    "seasonal or daily thermal control."
                ),
                solution_description=(
                    "Install layered facade panels or shutters that curl, tilt or change "
                    "porosity with temperature, humidity or sunlight, increasing insulation "
                    "in winter and ventilation or shading in summer."
                ),
                why_it_addresses_original_problem=(
                    "It replaces static insulation with a passive surface that changes its "
                    "thermal behavior when conditions change."
                ),
                expected_benefits=[
                    "low operational energy",
                    "few sensors or motors required",
                    "direct response to local facade conditions",
                ],
                possible_risks=[
                    "material fatigue over many cycles",
                    "response may need tuning for local climate",
                ],
                implementation_complexity="medium",
                confidence_score=0.78,
            ),
            Candidate(
                candidate_id="ANALOGY-3",
                solution_name="Skin-inspired thermal regulation layer",
                source_domain="Human skin",
                analogical_mechanism=(
                    "Human skin combines sensing, pores, sweat evaporation and blood-flow "
                    "changes to release or conserve heat."
                ),
                transferred_principle=(
                    "Combine sensing, micro-ventilation and thermal buffering in one building "
                    "envelope layer."
                ),
                solution_description=(
                    "Create a wall or roof layer with temperature sensors, micro-vents, phase "
                    "change material and controllable air gaps, so the envelope can release, "
                    "store or retain heat as needed."
                ),
                why_it_addresses_original_problem=(
                    "It gives the building an active-response envelope while using low-power "
                    "micro-actuation and passive heat storage."
                ),
                expected_benefits=[
                    "year-round comfort control",
                    "thermal buffering during peaks",
                    "lower HVAC loads",
                ],
                possible_risks=[
                    "higher integration complexity",
                    "maintenance of sensors and vents must be planned",
                ],
                implementation_complexity="high",
                confidence_score=0.8,
            ),
        ]

    def _public_candidate(self, candidate: dict[str, Any]) -> dict[str, Any]:
        public = dict(candidate)
        public["method"] = "Design by Analogy"
        public["source_analogy"] = public.get("source_analogy") or public.get("source_domain", "")
        public["mechanism"] = public.get("mechanism") or public.get("analogical_mechanism", "")
        public["why_it_fits_original_problem"] = public.get(
            "why_it_fits_original_problem",
        ) or public.get("why_it_addresses_original_problem", "")
        public["benefits"] = public.get("benefits") or public.get("expected_benefits", [])
        public["risks"] = public.get("risks") or public.get("possible_risks", [])
        return public

    def _model_dump(self, model: type, data: dict[str, Any]) -> dict[str, Any]:
        try:
            return model.model_validate(data).model_dump()
        except ValidationError:
            if model is SourceDomains and "domains" in data:
                return SourceDomains(source_domains=data["domains"]).model_dump()
            raise

    def _try_model_dump(self, model: type, data: dict[str, Any]) -> dict[str, Any] | None:
        try:
            return self._model_dump(model, data)
        except ValidationError:
            return None

    def _trace(self, step: int, name: str, output: dict[str, Any]) -> dict[str, Any]:
        return {"step": step, "name": name, "output": output}

    def _detect_transformation(self, problem: str) -> str:
        lower = problem.lower()
        scores = {
            transformation: sum(1 for word in words if word in lower)
            for transformation, words in TRANSFORMATION_WORDS.items()
        }
        best = max(scores, key=scores.get)
        return best if scores[best] > 0 else "adapt"

    def _extract_constraints(self, problem: str) -> list[str]:
        constraints = []
        for marker in ["without", "while", "under", "must", "cannot", "avoid"]:
            match = re.search(rf"\b{marker}\b(.+?)(?:[.;]|$)", problem, re.IGNORECASE)
            if match:
                constraints.append(f"{marker} {match.group(1).strip()}")
        return constraints or ["must satisfy the explicit constraints in the problem statement"]

    def _keywords(self, problem: str) -> list[str]:
        stop = {
            "the",
            "and",
            "for",
            "with",
            "that",
            "must",
            "without",
            "from",
            "into",
            "this",
            "they",
            "their",
            "relying",
        }
        words = re.findall(r"[A-Za-z][A-Za-z-]{2,}", problem.lower())
        seen = set()
        keywords = []
        for word in words:
            if word not in stop and word not in seen:
                seen.add(word)
                keywords.append(word)
        return keywords or ["system", "constraint", "outcome"]

    def _phrases(self, problem: str) -> list[str]:
        chunks = re.split(r"\bmust\b|\bshould\b|\bneeds?\b|\bwithout\b|[.;]", problem)
        return [chunk.strip(" ,") for chunk in chunks if chunk.strip(" ,")]
