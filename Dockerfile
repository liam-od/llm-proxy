# LiteLLM proxy with custom handlers. Serves the Modal-backed aliases
# (modal-llm / modal-transcribe / modal-embed); the claude-code aliases need the
# `claude` CLI and only work where it's installed (not in this image).
FROM python:3.12-slim

COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

WORKDIR /app
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

COPY config.yaml ./
COPY handlers ./handlers

EXPOSE 4001
# Provide VLLM_API_KEY, MODAL_TOKEN_ID, MODAL_TOKEN_SECRET (and optionally
# PROXY_MASTER_KEY) at run time, e.g. `docker run --env-file .env ...`.
CMD ["uv", "run", "litellm", "--config", "config.yaml", "--host", "0.0.0.0", "--port", "4001"]
