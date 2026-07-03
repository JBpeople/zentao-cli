FROM python:3.12-slim

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1

WORKDIR /app

COPY pyproject.toml README.md LICENSE ./
COPY zentao_cli ./zentao_cli
COPY zentao_agent ./zentao_agent

RUN python -m pip install --upgrade pip \
    && python -m pip install --no-cache-dir -e .

CMD ["zentao-wecom-bot"]
