# syntax=docker/dockerfile:1

# ---- Stage 1: builder — install dependencies into a virtualenv ----
FROM python:3.13-slim AS builder
ENV PIP_NO_CACHE_DIR=1 PIP_DISABLE_PIP_VERSION_CHECK=1
RUN python -m venv /opt/venv
ENV PATH="/opt/venv/bin:$PATH"
WORKDIR /build
COPY requirements.txt .
RUN pip install -r requirements.txt

# ---- Stage 2: runtime — slim image with only the venv and app code ----
FROM python:3.13-slim AS runtime
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PATH="/opt/venv/bin:$PATH"
WORKDIR /srv
RUN useradd -m appuser
COPY --from=builder /opt/venv /opt/venv
COPY --chown=appuser app ./app
COPY --chown=appuser alembic.ini ./
COPY --chown=appuser migrations ./migrations
COPY --chown=appuser scripts ./scripts
USER appuser
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=3s CMD python -c "import urllib.request as u; u.urlopen('http://localhost:8000/health')"
CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000"]
