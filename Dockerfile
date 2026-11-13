FROM python:3.15.2-slim

# Correcao temporaria: CVE-2026-76844 e CVE-2026-85091 (HIGH) no zlib1g.
# Remover quando a python:3.15-slim oficial ja trouxer a versao +deb13u1.
# hadolint ignore=DL3008
RUN apt-get update \
    && apt-get install -y --only-upgrade --no-install-recommends zlib1g \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1 \
    POETRY_VERSION=2.4.2 \
    POETRY_VIRTUALENVS_CREATE=false \
    POETRY_NO_INTERACTION=1 \
    PYTHONPATH=/app

RUN pip install --no-cache-dir --upgrade "pip==26.3" \
    && pip install --no-cache-dir "poetry==${POETRY_VERSION}"

COPY pyproject.toml poetry.lock README.md ./
RUN poetry install --no-root --with dev \
    && pip install --no-cache-dir --upgrade "setuptools>=80.10.2" \
    && find /usr/local/lib -path '*/pip/_vendor/bom.cdx.json' -delete \
    && rm -rf /root/.cache/pypoetry /tmp/poetry_cache

COPY . .
RUN mkdir -p reports

CMD ["pytest", "-q", "--cov", "--cov-report=term-missing", "--cov-report=xml:reports/coverage.xml", "--junitxml=reports/junit.xml"]
