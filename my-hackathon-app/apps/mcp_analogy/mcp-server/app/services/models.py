from typing import Literal

from pydantic import BaseModel, Field


TransformationType = Literal[
    "regulate",
    "protect",
    "store",
    "transport",
    "separate",
    "adapt",
    "convert",
    "detect",
    "stabilize",
    "reduce",
    "amplify",
]

Complexity = Literal["low", "medium", "high"]


class ProblemAnalysis(BaseModel):
    target_system: str
    desired_outcome: str
    current_limitation: str
    key_constraints: list[str] = Field(default_factory=list)
    harmful_effects_to_avoid: list[str] = Field(default_factory=list)
    success_criteria: list[str] = Field(default_factory=list)


class AbstractFunction(BaseModel):
    concrete_function: str
    abstract_function: str
    function_keywords: list[str] = Field(default_factory=list)
    input: str
    output: str
    constraints: list[str] = Field(default_factory=list)
    transformation_type: TransformationType


class SourceDomain(BaseModel):
    domain_name: str
    category: str
    similar_function: str
    why_relevant: str


class SourceDomains(BaseModel):
    source_domains: list[SourceDomain]


class Mechanism(BaseModel):
    source_domain: str
    observed_mechanism: str
    mechanism_principle: str
    transferable_pattern: str
    limitation_of_analogy: str


class Mechanisms(BaseModel):
    mechanisms: list[Mechanism]


class Candidate(BaseModel):
    candidate_id: str
    solution_name: str
    source_domain: str
    analogical_mechanism: str
    transferred_principle: str
    solution_description: str
    why_it_addresses_original_problem: str
    expected_benefits: list[str] = Field(default_factory=list)
    possible_risks: list[str] = Field(default_factory=list)
    implementation_complexity: Complexity = "medium"
    confidence_score: float = Field(ge=0, le=1)


class Candidates(BaseModel):
    candidates: list[Candidate]
