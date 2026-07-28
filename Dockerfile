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

RUN groupadd -r pit && useradd -r -g pit -d /app pit

COPY --from=builder /root/.local /home/pit/.local
COPY src/ src/
COPY web/ web/
COPY assets/ assets/

RUN chown -R pit:pit /app /home/pit
USER pit

ENV HOME="/home/pit"
ENV PATH="/home/pit/.local/bin:${PATH}"
ENV PYTHONPATH="/app/src"
EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=10s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8000/v1/health')"

CMD ["uvicorn", "pit.api:app", "--host", "0.0.0.0", "--port", "8000"]
