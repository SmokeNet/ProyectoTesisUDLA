FROM python:3.14.6-slim-trixie AS builder

ENV PIP_DISABLE_PIP_VERSION_CHECK=1 \
    PIP_NO_CACHE_DIR=1
WORKDIR /build
COPY requirements-api.txt .
RUN python -m venv /opt/venv \
    && /opt/venv/bin/pip install --no-compile -r requirements-api.txt

FROM python:3.14.6-slim-trixie

ENV PATH="/opt/venv/bin:$PATH" \
    PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1
RUN groupadd --system app && useradd --system --gid app --home-dir /app app
COPY --from=builder /opt/venv /opt/venv
WORKDIR /app/api
COPY --chown=app:app api/ /app/api/
USER app
EXPOSE 8000
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--no-server-header"]
