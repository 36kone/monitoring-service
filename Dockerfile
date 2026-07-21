FROM python:3.12-slim AS builder

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app

ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0

COPY pyproject.toml ./
RUN --mount=type=cache,target=/root/.cache/uv \
    uv lock && uv sync --no-dev --no-install-project

FROM python:3.12-slim AS runtime

RUN apt-get update && \
    apt-get install -y --no-install-recommends \
        tzdata \
        curl \
    ln -snf /usr/share/zoneinfo/America/Sao_Paulo /etc/localtime && \
    echo "America/Sao_Paulo" > /etc/timezone && \
    apt-get clean && rm -rf /var/lib/apt/lists/*

ENV TZ=America/Sao_Paulo \
    VIRTUAL_ENV=/app/.venv \
    PATH="/app/.venv/bin:$PATH"

WORKDIR /app

COPY --from=builder /app/.venv /app/.venv

COPY . .

EXPOSE 8000

CMD if [ "$MODE" = "background" ]; then \
        echo "Starting background worker..." && \
        python -m app.background_main; \
    else \
        echo "Starting FastAPI server..." && \
        uvicorn app.main:app --host 0.0.0.0 --port 8000; \
    fi

