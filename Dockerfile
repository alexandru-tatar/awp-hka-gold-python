# syntax=docker.io/docker/dockerfile-upstream:1.22.0
# check=error=true

# Container für eine Portal-App (Python-Golden-Master)
# Verwaltete Datei: Änderungen nur über die Plattform (sonst PF-108)
#
# Aufruf:   docker build --tag hka/portal-app:0.1.0 .
#               ggf. --no-cache
#
#           Windows:   Get-Content Dockerfile | docker run --rm --interactive hadolint/hadolint:v2.14.0-debian
#           macOS:     cat Dockerfile | docker run --rm --interactive hadolint/hadolint:v2.14.0-debian
#
#           docker run --rm --read-only --cap-drop=ALL --tmpfs /tmp --publish 8080:8080 hka/portal-app:0.1.0
#           docker scout cves hka/portal-app:0.1.0

# https://docs.docker.com/build/building/multi-stage
# https://github.com/astral-sh/uv-docker-example/blob/main/multistage.Dockerfile

# ARG: "build-time" Variable
# ENV: "build-time" und "runtime" Variable
ARG PYTHON_MAIN_VERSION=3.14
ARG PYTHON_VERSION=${PYTHON_MAIN_VERSION}.3
ARG UV_VERSION=0.11.0

# ------------------------------------------------------------------------------
# S t a g e   b u i l d e r
# ------------------------------------------------------------------------------
FROM ghcr.io/astral-sh/uv:${UV_VERSION}-python${PYTHON_MAIN_VERSION}-trixie-slim AS builder

WORKDIR /app

# Bytecode beim Bauen erzeugen (das Dateisystem ist im Betrieb schreibgeschuetzt)
# Copy statt Link, weil der Cache ein gemountetes Volume ist
# Kein Python-Download erforderlich
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy \
    UV_PYTHON_DOWNLOADS=0 \
    UV_NO_MANAGED_PYTHON=true

# Nur die Abhaengigkeiten aus uv.lock in /app/.venv installieren (ohne dev-Gruppe).
# Die App selbst wird nicht installiert, sondern ueber PYTHONPATH geladen.
RUN --mount=type=cache,target=/root/.cache/uv \
    --mount=type=bind,source=uv.lock,target=uv.lock \
    --mount=type=bind,source=pyproject.toml,target=pyproject.toml \
    ["/usr/local/bin/uv", "sync", "--frozen", "--no-install-project", "--no-default-groups", "--no-editable"]

# ------------------------------------------------------------------------------
# S t a g e   f i n a l
# ------------------------------------------------------------------------------
FROM python:${PYTHON_VERSION}-slim-trixie AS final

# Anzeige bei "docker inspect ..."
# https://specs.opencontainers.org/image-spec/annotations
LABEL org.opencontainers.image.title="hka-portal-app" \
    org.opencontainers.image.description="HKA Portal-App (Python-Golden-Master) mit Basis-Image Trixie" \
    org.opencontainers.image.version="0.1.0"

# Eigener Benutzer mit fester UID statt "root"; /data ist der einzige beschreibbare Ordner neben /tmp
RUN useradd --system --uid 10001 --no-create-home --shell /usr/sbin/nologin app \
    && mkdir /data \
    && chown 10001:10001 /data

# "working directory" fuer die Docker-Kommandos RUN, ENTRYPOINT, CMD, COPY und ADD
WORKDIR /app

# .venv, Portal-SDK, Quellcode und Manifest 
COPY --from=builder /app/.venv ./.venv
COPY platform_sdk ./platform_sdk
COPY src ./src
COPY manifest.json ./

USER 10001:10001

# .venv vorne im PATH; platform_sdk liegt in /app, das Paket "app" in /app/src
ENV PATH="/app/.venv/bin:$PATH" \
    PYTHONPATH=/app:/app/src \
    PYTHONUNBUFFERED=1 \
    PYTHONDONTWRITEBYTECODE=1 \
    PORT=8080 \
    DATA_DIR=/data

EXPOSE 8080

# Nur Standardbibliothek (urllib.request auf /healthz), kein curl im Image
HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=3 \
    CMD ["python", "-m", "platform_sdk.healthcheck"]

STOPSIGNAL SIGINT

ENTRYPOINT ["python", "-m", "uvicorn", "app.main:app", "--app-dir", "src", "--host", "0.0.0.0", "--port", "8080"]
