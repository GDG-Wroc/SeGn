FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1
ENV UV_PYTHON_DOWNLOADS=0
ENV MCP_HOST=0.0.0.0
ENV PORT=8080
ENV MCP_PORT=8080

WORKDIR /app

COPY pyproject.toml uv.lock README.md ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

COPY app/ /app/app/

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

EXPOSE 8080

CMD ["sh", "-c", "MCP_PORT=${PORT} uv run python app/main.py"]
