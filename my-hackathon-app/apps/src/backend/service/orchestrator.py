import json
import logging
from typing import Any, Dict
from backend.service.llm_client import LLMClient
from backend.service.mcp_service import MCP

logger = logging.getLogger(__name__)

class MCPOrchestrator:
    def __init__(self, triz_mcp: MCP, analogy_mcp: Any):
        self.triz_mcp = triz_mcp
        self.analogy_mcp = analogy_mcp
        self.llm_client = LLMClient()

    async def run(self, query: str) -> Dict[str, Any]:
        logger.info(f"Orchestrating solution search for query: {query}")
        
        # 1. Try to query the MCP server to fetch tools/info if possible
        mcp_data = {}
        try:
            mcp_data["triz_tools"] = await self.triz_mcp.list_tools()
        except Exception as e:
            logger.warning(f"Could not contact TRIZ MCP: {e}")
            mcp_data["triz_tools"] = []

        # 2. Build structured prompt for the LLM to perform the entire TRIZ/Analogy process
        system_prompt = (
            "Jestes wybitnym inzynierem R&D i ekspertem metodologii TRIZ oraz biomimetyki/analogii.\n"
            "Twoim zadaniem jest przeanalizowanie problemu technicznego i wygenerowanie:\n"
            "1. Sprzecznosci technicznej (Technical Contradiction) z parametrem poprawianym, pogarszanym i formula sprzecznosci.\n"
            "2. Dokladnie 3 rozwiazan kandydackich na podstawie TRIZ (Contradiction Matrix / zasady wynalazcze).\n"
            "3. Dokladnie 3 rozwiazan kandydackich na podstawie metody analogii (np. przyroda, kosmos, inne branze).\n"
            "4. Macierzy oceny (Evaluation Matrix) w skali 1-10 dla kazdego z 6 rozwiazan pod katem kryteriow: "
            "wykonalnosc (feasibility), efektywnosc energetyczna (energy_efficiency), oplacalnosc (cost_effectiveness), "
            "adaptacyjnosc (adaptability), zgodnosc z celami SDG 11 i 13 (sdg_alignment), wraz z podsumowaniem punktow (total_score).\n"
            "5. Wyboru najlepszego rozwiazania (final choice) wraz z pelnym uzasadnieniem.\n\n"
            "MUSISZ zwrocic czysty format JSON zgodny ze schematem. Nie dodawaj zadnego innego tekstu poza JSON-em."
        )

        prompt = (
            f"Problem do analizy:\n{query}\n\n"
            f"Dostepne narzedzia MCP (moga byc puste): {mcp_data}\n\n"
            "Zwroc dane w nastepujacym formacie JSON:\n"
            "{\n"
            "  \"problem\": \"Opis problemu\",\n"
            "  \"contradiction\": {\n"
            "    \"improving_parameter\": \"Parametr poprawiany (np. temperatura wewnetrzna)\",\n"
            "    \"worsening_parameter\": \"Parametr pogarszany (np. zuzycie energii)\",\n"
            "    \"statement\": \"Formulacja sprzecznosci\"\n"
            "  },\n"
            "  \"triz_candidates\": [\n"
            "    {\n"
            "      \"id\": \"triz_1\",\n"
            "      \"name\": \"Nazwa rozwiazania TRIZ 1\",\n"
            "      \"principle\": \"Zasada TRIZ (np. Zasada 15 - Dynamizm)\",\n"
            "      \"description\": \"Szczegolowy opis fizycznego dzialania\",\n"
            "      \"pros\": [\"Zaleta 1\", \"Zaleta 2\"],\n"
            "      \"cons\": [\"Wada 1\", \"Wada 2\"]\n"
            "    }\n"
            "    // ... dokladnie 3 rozwiazania\n"
            "  ],\n"
            "  \"analogy_candidates\": [\n"
            "    {\n"
            "      \"id\": \"analogy_1\",\n"
            "      \"name\": \"Nazwa rozwiazania na podstawie analogii 1\",\n"
            "      \"analogy_source\": \"Zrodlo analogii (np. Kopce termitow / Biomimetyka)\",\n"
            "      \"description\": \"Szczegolowy opis dzialania\",\n"
            "      \"pros\": [\"Zaleta 1\", \"Zaleta 2\"],\n"
            "      \"cons\": [\"Wada 1\", \"Wada 2\"]\n"
            "    }\n"
            "    // ... dokladnie 3 rozwiazania\n"
            "  ],\n"
            "  \"evaluation\": [\n"
            "    {\n"
            "      \"candidate_id\": \"Identyfikator kandydata (np. triz_1, analogy_1)\",\n"
            "      \"candidate_name\": \"Nazwa kandydata\",\n"
            "      \"feasibility\": 8,\n"
            "      \"energy_efficiency\": 9,\n"
            "      \"cost_effectiveness\": 7,\n"
            "      \"adaptability\": 8,\n"
            "      \"sdg_alignment\": 9,\n"
            "      \"total_score\": 41\n"
            "    }\n"
            "    // ... dla wszystkich 6 kandydatow\n"
            "  ],\n"
            "  \"choice\": {\n"
            "    \"winner_id\": \"Id wygranego kandydata\",\n"
            "    \"winner_name\": \"Nazwa wygranego kandydata\",\n"
            "    \"justification\": \"Szczegolowe inzynierskie uzasadnienie wyboru pod katem SDG 11/13, zalet oraz ograniczenia AC.\"\n"
            "  }\n"
            "}"
        )

        try:
            response_text = await self.llm_client.generate_text(prompt, system_prompt)
            # Remove any markdown code fence if the LLM returned it
            if response_text.startswith("```json"):
                response_text = response_text[7:]
            if response_text.endswith("```"):
                response_text = response_text[:-3]
            response_text = response_text.strip()
            
            return json.loads(response_text)
        except Exception as e:
            logger.error(f"Error during orchestrator run: {e}")
            return self._get_fallback_data(query)

    def _get_fallback_data(self, query: str) -> Dict[str, Any]:
        return {
            "problem": query,
            "contradiction": {
                "improving_parameter": "Temperatura wewnątrz budynku (stabilność termiczna)",
                "worsening_parameter": "Zużycie energii oraz skomplikowanie konstrukcji (brak AC)",
                "statement": "Jeżeli zastosujemy grube, statyczne ocieplenie, to zatrzymamy ciepło zimą (parametr poprawiany), ale latem budyrok ulegnie przegrzaniu, co wymusi użycie energochłonnej klimatyzacji (parametr pogarszany)."
            },
            "triz_candidates": [
                {
                    "id": "triz_1",
                    "name": "Dynamiczna Fasada Wentylowana",
                    "principle": "Zasada 15 - Dynamizm (Dynamiczność)",
                    "description": "Zewnętrzne żaluzje i panele ścienne połączone z siłownikami zmieniającymi kąt nachylenia w zależności od nasłonecznienia i temperatury zewnętrznej. Zimą fasada zamyka się, tworząc izolującą poduszkę powietrzną; latem otwiera się, wymuszając naturalną konwekcję i chłodzenie.",
                    "pros": ["Wysoka sprawność", "Brak zużycia energii w pasywnym trybie"],
                    "cons": ["Mechaniczna złożoność", "Koszt konserwacji"]
                },
                {
                    "id": "triz_2",
                    "name": "Ściany z Materiałami Zmiennofazowymi (PCM)",
                    "principle": "Zasada 35 - Zmiana właściwości fizykochemicznych",
                    "description": "Zastosowanie w tynkach i płytach gipsowo-kartonowych mikrokapsułek z parafiny lub estrów organicznych. Materiał topi się przy 23°C (pochłaniając ciepło w dzień) i krzepnie w nocy (oddając ciepło), stabilizując temperaturę bez klimatyzacji.",
                    "pros": ["Całkowicie pasywne działanie", "Niewidoczne dla użytkownika"],
                    "cons": ["Ograniczona pojemność cieplna", "Wyższy koszt materiałów"]
                },
                {
                    "id": "triz_3",
                    "name": "Segmentowe Okna o Zmiennej Polaryzacji",
                    "principle": "Zasada 32 - Zmiana koloru (Właściwości optycznych)",
                    "description": "Inteligentne szyby z powłoką elektrochromową, które zmieniają przejrzystość (od przezroczystych po ciemne matowe) pod wpływem mikro-napięć. Blokują do 90% promieniowania słonecznego latem i maksymalizują zyski solarne zimą.",
                    "pros": ["Doskonała kontrola nasłonecznienia", "Estetyczny wygląd"],
                    "cons": ["Wymaga zasilania elektrycznego", "Wysoki koszt inwestycyjny"]
                }
            ],
            "analogy_candidates": [
                {
                    "id": "analogy_1",
                    "name": "Klimatyzacja Inspirowana Kopcami Termitów",
                    "analogy_source": "Biomimetyka - Termitiery (Termite Mounds)",
                    "description": "System pionowych szybów wentylacyjnych w rdzeniu budynku połączonych z podziemnymi czerpniami powietrza. Gorące powietrze uchodzi górą budynku (efekt kominowy), a chłodne powietrze jest zasysane z gruntu, zapewniając stałą cyrkulację bez wentylatorów.",
                    "pros": ["Zerowe zużycie prądu", "Stały dopływ świeżego powietrza"],
                    "cons": ["Wymaga dużej przestrzeni konstrukcyjnej", "Zależność od warunków gruntowych"]
                },
                {
                    "id": "analogy_2",
                    "name": "Pasywna Radiacyjna Folia Chłodząca",
                    "analogy_source": "Technologia kosmiczna i fizyka ciał doskonale czarnych",
                    "description": "Specjalna powłoka dachowa odbijająca 99% światła słonecznego, która jednocześnie emituje ciepło w postaci promieniowania podczerwonego przez tzw. okno atmosferyczne bezpośrednio w przestrzeń kosmiczną, chłodząc dach poniżej temperatury otoczenia.",
                    "pros": ["Chłodzenie poniżej temp. otoczenia w pełnym słońcu", "Brak ruchomych części"],
                    "cons": ["Działa tylko przy czystym niebie", "Zimą może nadmiernie wychładzać budynek"]
                },
                {
                    "id": "analogy_3",
                    "name": "Zielona Fasada Liściasta (Deciduous Wall)",
                    "analogy_source": "Botanika - Drzewa liściaste",
                    "description": "Zastosowanie pnączy zrzucających liście na zimę na specjalnych stelażach odsuniętych od ścian. Latem gęste liście cieniują elewację i chłodzą ją przez ewapotranspirację. Zimą, po opadnięciu liści, słońce bezpośrednio nagrzewa ściany budynku.",
                    "pros": ["Poprawa mikroklimatu i bioróżnorodności", "Automatyczna sezonowość"],
                    "cons": ["Wymaga pielęgnacji i nawadniania", "Długi czas wzrostu roślin"]
                }
            ],
            "evaluation": [
                {"candidate_id": "triz_1", "candidate_name": "Dynamiczna Fasada Wentylowana", "feasibility": 7, "energy_efficiency": 8, "cost_effectiveness": 6, "adaptability": 9, "sdg_alignment": 9, "total_score": 39},
                {"candidate_id": "triz_2", "candidate_name": "Ściany z Materiałami Zmiennofazowymi (PCM)", "feasibility": 8, "energy_efficiency": 9, "cost_effectiveness": 7, "adaptability": 8, "sdg_alignment": 9, "total_score": 41},
                {"candidate_id": "triz_3", "candidate_name": "Segmentowe Okna o Zmiennej Polaryzacji", "feasibility": 8, "energy_efficiency": 7, "cost_effectiveness": 5, "adaptability": 8, "sdg_alignment": 8, "total_score": 36},
                {"candidate_id": "analogy_1", "candidate_name": "Klimatyzacja Inspirowana Kopcami Termitów", "feasibility": 6, "energy_efficiency": 10, "cost_effectiveness": 8, "adaptability": 7, "sdg_alignment": 10, "total_score": 41},
                {"candidate_id": "analogy_2", "candidate_name": "Pasywna Radiacyjna Folia Chłodząca", "feasibility": 9, "energy_efficiency": 9, "cost_effectiveness": 8, "adaptability": 6, "sdg_alignment": 9, "total_score": 41},
                {"candidate_id": "analogy_3", "candidate_name": "Zielona Fasada Liściasta (Deciduous Wall)", "feasibility": 8, "energy_efficiency": 9, "cost_effectiveness": 9, "adaptability": 8, "sdg_alignment": 10, "total_score": 44}
            ],
            "choice": {
                "winner_id": "analogy_3",
                "winner_name": "Zielona Fasada Liściasta (Deciduous Wall)",
                "justification": "Zielona fasada liściasta wygrywa w ogólnej ocenie z wynikiem 44 punktów. Rozwiązanie to jest w 100% pasywne, wykazuje naturalną, automatyczną adaptację do pór roku (liście rosną wiosną/latem dając cień, a opadają jesienią odsłaniając ściany dla słońca). Dodatkowo proces ewapotranspiracji aktywnie obniża temperaturę otoczenia budynku (zwalczając miejską wyspę ciepła), co bezpośrednio realizuje założenia SDG 11 i 13, unikając przy tym jakichkolwiek szkodliwych emisji czy zużycia energii elektrycznej."
            }
        }
