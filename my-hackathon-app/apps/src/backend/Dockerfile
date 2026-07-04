FROM python:3.13-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

ENV PYTHONUNBUFFERED=1
ENV UV_PYTHON_DOWNLOADS=0
ENV PORT=8080

WORKDIR /app

COPY pyproject.toml uv.lock ./

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked --no-install-project

COPY . /app

RUN --mount=type=cache,target=/root/.cache/uv \
    uv sync --locked

EXPOSE 8080

CMD ["sh", "-c", "uv run uvicorn backend.main:app --host 0.0.0.0 --port ${PORT}"]
