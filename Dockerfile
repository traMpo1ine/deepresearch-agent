FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app/src

WORKDIR /app

RUN groupadd --gid 10001 appgroup \
    && useradd --uid 10001 --gid appgroup --create-home appuser

COPY pyproject.toml ./
COPY src ./src
RUN python -m pip install --no-cache-dir --upgrade pip \
    && python -m pip install --no-cache-dir ".[web,enterprise]"

COPY configs ./configs
COPY data ./data
COPY scripts ./scripts
COPY reports/final/final_sprint_check/showcase ./reports/final/final_sprint_check/showcase

RUN mkdir -p /app/reports/demo_runs /app/data/memory /app/data/uploads \
    && chown -R appuser:appgroup /app/reports /app/data

USER appuser

EXPOSE 8000

HEALTHCHECK --interval=15s --timeout=3s --start-period=20s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/api/health/ready', timeout=2)"

CMD ["python", "-m", "uvicorn", "deepresearch_agent.web.app:app", "--host", "0.0.0.0", "--port", "8000", "--no-access-log"]
