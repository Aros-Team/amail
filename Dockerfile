# ----- Stage 1: builder -----
FROM python:3.13-slim

WORKDIR /app

RUN pip install uv

COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-install-project

COPY app/ ./app/
COPY templates/ ./templates/
COPY main.py .

# ----- Stage 2: runtime -----
FROM python:3.13-slim

WORKDIR /app

COPY --from=0 /app/.venv/ .venv/
COPY --from=0 /app/app/ ./app/
COPY --from=0 /app/templates/ ./templates/
COPY --from=0 /app/main.py .

ENV PATH="/app/.venv/bin:$PATH"
ENV PYTHONUNBUFFERED=1

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]