FROM python:3.13-slim AS builder

WORKDIR /app

COPY pyproject.toml ./

RUN pip install --upgrade pip \
    && pip install -e ".[all,dev]" --no-build-isolation

# ---------------------------------------------------------------------

FROM python:3.13-slim AS runtime

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    curl \
    && rm -rf /var/lib/apt/lists/*

COPY --from=builder /opt/pipx/venvs/aigis /opt/pipx/venvs/aigis
COPY --from=builder /usr/local/bin/aigis /usr/local/bin/aigis

ENV PATH="/opt/pipx/venvs/aigis/bin:$PATH"

ENV AIGIS_API_KEY="${AIGIS_API_KEY:-}"
ENV AIGIS_API_HOST="0.0.0.0"
ENV AIGIS_API_PORT="8080"

EXPOSE 8080

CMD ["aigis", "serve", "--host", "0.0.0.0", "--port", "8080"]
