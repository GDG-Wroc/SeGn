from typing import Any


class TRIZResultInterpreter:
    """Turns raw TRIZ MCP output into a user-facing recommendation."""

    def interpret(self, original_problem: str, triz_raw_response: Any) -> dict[str, Any]:
        identified_parameters = self._extract_parameters(triz_raw_response)
        directions = self._recommended_directions(original_problem, identified_parameters)

        if identified_parameters:
            parameters_text = ", ".join(identified_parameters[:5])
            summary = (
                "TRIZ indicates that the problem is related to these parameters: "
                f"{parameters_text}. At this stage, this is treated as a set of "
                "design directions derived from TRIZ parameters, not as a full "
                "contradiction-matrix analysis."
            )
        else:
            summary = (
                "The TRIZ MCP returned a response, but parameter names could not "
                "be extracted with confidence. The recommendations below are a "
                "careful summary of the raw output and the original problem."
            )

        return {
            "method": "TRIZ",
            "summary": summary,
            "identified_parameters": identified_parameters,
            "recommended_directions": directions,
            "raw_response": triz_raw_response,
        }

    def _extract_parameters(self, value: Any) -> list[str]:
        candidates: list[str] = []

        def visit(node: Any) -> None:
            if isinstance(node, dict):
                for key, item in node.items():
                    lower_key = str(key).lower()
                    if lower_key in {
                        "parameter",
                        "parameter_name",
                        "name",
                        "title",
                        "triz_parameter",
                    } and isinstance(item, str):
                        candidates.append(item)
                    else:
                        visit(item)
            elif isinstance(node, list):
                for item in node:
                    visit(item)

        visit(value)
        seen = set()
        unique = []
        for candidate in candidates:
            normalized = " ".join(candidate.strip().split())
            if normalized and normalized.lower() not in seen:
                seen.add(normalized.lower())
                unique.append(normalized)
        return unique

    def _recommended_directions(
        self,
        original_problem: str,
        identified_parameters: list[str],
    ) -> list[dict[str, str]]:
        lower_problem = original_problem.lower()
        lower_params = " ".join(identified_parameters).lower()
        thermal_context = any(
            word in lower_problem
            for word in ["warm", "cool", "winter", "summer", "temperature", "heat", "thermal"]
        )
        energy_context = "energy" in lower_problem or "energy" in lower_params

        if thermal_context:
            return [
                {
                    "name": "Dynamic building envelope",
                    "description": (
                        "Use a facade, insulation layer, or intermediate layer that "
                        "changes thermal permeability depending on season and weather."
                    ),
                    "why_it_fits_problem": (
                        "It addresses the limitation of static insulation, which behaves "
                        "the same way in winter and summer."
                    ),
                },
                {
                    "name": "Controlled heat storage and release",
                    "description": (
                        "The system buffers excess heat, recovers it, or releases it "
                        "when doing so improves indoor comfort."
                    ),
                    "why_it_fits_problem": (
                        "It reduces energy losses and limits the need for intensive "
                        "heating or cooling."
                    ),
                },
                {
                    "name": "Thermal segmentation",
                    "description": (
                        "Different building zones respond differently to sunlight, "
                        "outdoor temperature, and local occupant needs."
                    ),
                    "why_it_fits_problem": (
                        "It avoids forcing one static solution onto the whole building."
                    ),
                },
            ]

        first_parameter = identified_parameters[0] if identified_parameters else "glowny parametr TRIZ"
        return [
            {
                "name": "Variable system configuration",
                "description": (
                    "Replace a fixed setup with elements that can change their "
                    "properties depending on conditions."
                ),
                "why_it_fits_problem": f"This direction follows from the parameter: {first_parameter}.",
            },
            {
                "name": "Separate the function across time or space",
                "description": (
                    "Split the problem into states, zones, or operating modes instead "
                    "of searching for one compromise for every situation."
                ),
                "why_it_fits_problem": "It helps handle conflicting requirements without one rigid compromise.",
            },
            {
                "name": "Reduce resource losses",
                "description": (
                    "Identify where the system loses energy, material, time, or "
                    "information, then add recovery or buffering."
                ),
                "why_it_fits_problem": (
                    "It fits problems where the current solution requires too much "
                    "resource use."
                    if energy_context
                    else "It is a cautious improvement direction derived from TRIZ."
                ),
            },
        ]
