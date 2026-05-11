FROM python:3.11-slim AS base

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PIP_NO_CACHE_DIR=1 \
    PIP_DISABLE_PIP_VERSION_CHECK=1

WORKDIR /app

FROM base AS builder

RUN pip install hatch

COPY pyproject.toml README.md LICENSE ./
COPY adsreport/ ./adsreport/

RUN pip install --prefix=/install .

FROM base AS runtime

COPY --from=builder /install /usr/local

RUN useradd --create-home --shell /bin/bash adsreport

USER adsreport

VOLUME ["/data"]

ENV ADSREPORT_DATA_DIR=/data

EXPOSE 8050

HEALTHCHECK --interval=30s --timeout=10s --start-period=15s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:8050/')" || exit 1

CMD ["gunicorn", "--bind", "0.0.0.0:8050", "--workers", "2", "--timeout", "120", "adsreport.app:server"]
