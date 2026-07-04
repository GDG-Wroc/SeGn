import { Component, OnInit } from '@angular/core';
import { CommonModule } from '@angular/common';
import { FormsModule } from '@angular/forms';
import { HttpClient } from '@angular/common/http';

@Component({
  imports: [CommonModule, FormsModule],
  selector: 'app-root',
  templateUrl: './app.html',
  styleUrl: './app.css',
  standalone: true
})
export class App implements OnInit {
  protected title = 'my-hackathon-app';
  
  queryText = '';
  loading = false;
  error: string | null = null;
  result: any = null;
  runMode: 'live' | 'fallback' | null = null;
  activeTab: 'triz' | 'analogy' | 'evaluation' = 'triz';

  constructor(private http: HttpClient) {}

  ngOnInit() {
    this.queryText = `Buildings need to stay warm in winter and cool in summer, and heating and cooling together account for a huge share of global energy use and emissions. Most buildings today are constructed with static materials and insulation that are optimized once and can't adapt as seasons change, as the same walls and windows perform the same way in January and July, regardless of what's actually needed at each moment. Your task: propose a way to help a building maintain comfortable indoor temperatures across both seasons without relying on year-round static materials or heavy energy use. And remember, the AC is not the solution- it produces A LOT of heat 😉.`;
  }

  runAnalysis() {
    this.loading = true;
    this.error = null;
    this.result = null;
    this.runMode = null;

    this.http.post('http://localhost:8000/query', { query: this.queryText }).subscribe({
      next: (res: any) => {
        this.result = res;
        this.runMode = 'live';
        this.loading = false;
      },
      error: (err) => {
        console.warn('Backend connection failed, loading premium fallback demo data...', err);
        this.result = this.getFallbackData();
        this.runMode = 'fallback';
        this.loading = false;
      }
    });
  }

  setTab(tab: 'triz' | 'analogy' | 'evaluation') {
    this.activeTab = tab;
  }

  private getFallbackData() {
    return {
      "problem": this.queryText,
      "contradiction": {
        "improving_parameter": "Temperatura wewnątrz budynku (stabilność termiczna)",
        "worsening_parameter": "Zużycie energii oraz skomplikowanie konstrukcji (brak AC)",
        "statement": "Jeżeli zastosujemy grube, statyczne ocieplenie, to zatrzymamy ciepło zimą (parametr poprawiany), ale latem budynek ulegnie przegrzaniu, co wymusi użycie energochłonnej klimatyzacji (parametr pogarszany)."
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
    };
  }
}
