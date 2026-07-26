FROM python:3.14-slim AS builder

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    gcc \
    libpq-dev \
    && rm -rf /var/lib/apt/lists/*

COPY pyproject.toml .
RUN pip install --no-cache-dir --user .

FROM python:3.14-slim

WORKDIR /app

RUN apt-get update && apt-get install -y --no-install-recommends \
    libpq5 \
    && rm -rf /var/lib/apt/lists/*

RUN groupadd -r pitchavi && useradd -r -g pitchavi -d /app pitchavi

COPY --from=builder /root/.local /home/pitchavi/.local
COPY src/ src/

RUN chown -R pitchavi:pitchavi /app
USER pitchavi

ENV PATH="/home/pitchavi/.local/bin:${PATH}"
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/v1/health')"

CMD ["uvicorn", "pitchavi.api:app", "--host", "0.0.0.0", "--port", "8000"]
