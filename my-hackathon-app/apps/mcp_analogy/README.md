# Design by Analogy MCP

Generic Design by Analogy MCP server for producing structured innovation candidates.

The server is independent from the TRIZ MCP server and listens by default on:

- Transport: Streamable HTTP
- URL: `http://127.0.0.1:8124/mcp`
- MCP name: `design-by-analogy-mcp`

## Run locally

```bash
cd SeGn/my-hackathon-app/apps/mcp_analogy/mcp-server
uv sync
uv run python app/main.py
```

Optional OpenAI-compatible LLM configuration can be placed in `../.env` or the shell:

```bash
ANALOGY_LLM_BASE_URL=http://localhost:1234/v1
ANALOGY_LLM_MODEL=local-model
ANALOGY_LLM_API_KEY=optional-key
```

If no LLM endpoint is configured, the server still runs with deterministic generic fallback logic. The fallback uses only broad source-domain categories and problem-derived keywords, not a problem-specific analogy database.

## Tools

- `generate_analogy_solutions(problem: str, minimum_solutions: int = 3) -> dict`
- `health_check() -> dict`

`generate_analogy_solutions` always enforces at least 3 solutions and returns the full trace:

`problem -> problem analysis -> abstract function -> source domains -> mechanisms -> transferred solution candidates -> validation`

## Example problem

```text
Buildings must stay warm in winter and cool in summer without relying on static insulation all year or energy-intensive air conditioning.
```

Expected high-level response shape:

```json
{
  "method": "Design by Analogy",
  "input_problem": "...",
  "minimum_solutions_required": 3,
  "logic_trace": [
    {"step": 1, "name": "Problem analysis", "output": {}},
    {"step": 2, "name": "Function abstraction", "output": {}},
    {"step": 3, "name": "Source domain discovery", "output": {}},
    {"step": 4, "name": "Mechanism extraction", "output": {}},
    {"step": 5, "name": "Candidate generation", "output": {}},
    {"step": 6, "name": "Candidate validation", "output": {}}
  ],
  "candidates": [],
  "candidate_count": 3,
  "is_successful": true
}
```
