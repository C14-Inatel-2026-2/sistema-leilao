FROM python:3.11-slim

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=2.4.2 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONPATH=/app

RUN pip install --no-cache-dir "poetry==${POETRY_VERSION}"

COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --no-root --with dev \
    && rm -rf /root/.cache/pypoetry /tmp/poetry_cache

COPY . .
RUN mkdir -p reports

CMD ["pytest", "-q", "--cov", "--cov-report=term-missing", "--cov-report=xml:reports/coverage.xml", "--junitxml=reports/junit.xml"]
