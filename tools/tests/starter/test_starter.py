"""Selbsttests des Golden Master (Python-Starter).

Prüft, dass der Starter die Vorgaben der Plattform erfüllt: Aufbau, Manifest, Abhängigkeiten,
Ruff-Verbote, Container, Gerüst der App, Anmeldung auf jeder Route und unveränderte
Portal-Bibliothek. Die Tests bleiben grün, wenn eine Person ihre App im Starter baut,
solange sie sich an die Regeln hält.

Aufruf: make check-starter            (ohne Container)
        CHECK_DOCKER=1 make check-starter   (baut und startet zusätzlich den Container)
"""

from __future__ import annotations

import ast
import json
import os
import re
import shutil
import subprocess
import time
import urllib.request

import pytest
from common import ROOT, banned_modules, make_targets, manifest_errors, pruefung, pyproject
from fastapi.routing import APIRoute
from fastapi.testclient import TestClient
from starlette.routing import Mount

SRC = ROOT / "src" / "app"
DOCKERFILE = (ROOT / "Dockerfile").read_text(encoding="utf-8")
PY_FILES = sorted(SRC.rglob("*.py"))
TEMPLATES = sorted((SRC / "templates").rglob("*.html"))
CSS_FILES = sorted((SRC / "static").rglob("*.css"))


def python_minor() -> str:
    return re.search(r">=\s*(3\.\d+)", pyproject()["project"]["requires-python"]).group(1)


# ── Aufbau ───────────────────────────────────────────────────────────────────

MANAGED = [
    "Makefile",
    "Dockerfile",
    ".dockerignore",
    ".gitignore",
    "pyproject.toml",
    "uv.lock",
    "manifest.json",
    "README.md",
    ".agents/skills/README.md",
    "platform_sdk/VERSION",
    "platform_sdk/SHA256",
    "src/app/__init__.py",
    "src/app/main.py",
    "src/app/views.py",
    "src/app/static/app.css",
    "tests/conftest.py",
]


@pruefung("Aufbau", "Pflichtdateien vorhanden")
@pytest.mark.parametrize("path", MANAGED)
def test_datei_vorhanden(path):
    assert (ROOT / path).is_file()


@pruefung("Aufbau", "Befehle dev, start, test, lint, docker, lock, sdk-update")
def test_make_befehle():
    assert {"dev", "start", "test", "lint", "docker", "lock", "sdk-update"} <= make_targets()


@pruefung("Aufbau", "Keine .env-Datei im Repository", "R-SEC-1")
def test_keine_env_datei_im_repository():
    assert not list(ROOT.glob(".env*"))


# ── Manifest ─────────────────────────────────────────────────────────────────


@pruefung("Manifest", "manifest.json entspricht dem Schema", "R-PORT-4")
def test_manifest_gueltig():
    assert manifest_errors(json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))) == []


@pruefung("Manifest", "Schnittstellen-Rechte passen genau zum Code", "R-SCHN-5")
def test_manifest_adapter_rechte_passen_zum_code():
    """R-SCHN-5: genau die Rechte, die der Code über portal.adapters.<system> nutzt."""
    manifest = json.loads((ROOT / "manifest.json").read_text(encoding="utf-8"))
    declared = {a.split(":")[0] for a in manifest.get("adapters", [])}
    used = set()
    for file in PY_FILES:
        used |= set(re.findall(r"portal\.adapters\.([a-z]+)\.", file.read_text(encoding="utf-8")))
    assert declared == used


# ── Abhängigkeiten und Ruff ──────────────────────────────────────────────────


@pruefung("Abhängigkeiten und Lint", "Python 3.14 in pyproject.toml und Ruff")
def test_python_version():
    assert python_minor() == "3.14"
    assert pyproject()["tool"]["ruff"]["target-version"] == "py314"


@pruefung("Abhängigkeiten und Lint", "Keine verbotenen Abhängigkeiten", "R-SCHN-1", "R-PORT-1", "R-DES-2")
def test_keine_verbotenen_abhaengigkeiten():
    forbidden = {"requests", "aiohttp", "passlib", "bcrypt", "authlib", "python-jose", "itsdangerous", "fastapi-login"}
    names = {re.split(r"[\[<>=~ ]", d)[0].lower() for d in pyproject()["project"]["dependencies"]}
    assert not names & forbidden
    assert not names & {"bootstrap", "tailwindcss"}


@pruefung("Abhängigkeiten und Lint", "Testwerkzeuge nur in der dev-Gruppe")
def test_testwerkzeuge_nur_in_dev():
    names = {re.split(r"[\[<>=~ ]", d)[0].lower() for d in pyproject()["project"]["dependencies"]}
    assert not names & {"pytest", "ruff", "httpx2"}


@pruefung(
    "Abhängigkeiten und Lint", "Ruff-Verbote vollständig, keine Ausnahmen für src/", "R-SCHN-1", "R-PORT-1", "R-PORT-6"
)
def test_ruff_verbote():
    required = {
        "requests", "httpx", "aiohttp", "urllib3", "urllib.request", "http.client", "socket",
        "jwt", "jose", "authlib", "passlib", "bcrypt", "itsdangerous",
        "fastapi_login", "fastapi_users", "starlette.middleware.sessions", "markupsafe.Markup",
    }  # fmt: skip
    assert required <= banned_modules()
    ruff = pyproject()["tool"]["ruff"]
    assert {"S", "TID", "B"} <= set(ruff["lint"]["select"])
    assert "platform_sdk" in ruff.get("extend-exclude", [])
    ignores = ruff["lint"].get("per-file-ignores", {})
    assert not any(k.startswith("src") for k in ignores), "Ausnahmen für src/ sind nicht erlaubt"


@pruefung("Abhängigkeiten und Lint", "uv.lock passt zu pyproject.toml")
@pytest.mark.skipif(shutil.which("uv") is None, reason="uv fehlt")
def test_lock_aktuell():
    result = subprocess.run(["uv", "lock", "--check"], cwd=ROOT, capture_output=True, text=True)
    assert result.returncode == 0, result.stderr


@pruefung("Abhängigkeiten und Lint", "Ruff meldet eingespielten verbotenen Import", "R-SCHN-1")
@pytest.mark.skipif(shutil.which("uv") is None, reason="uv fehlt")
def test_ruff_meldet_verbotenen_import(tmp_path):
    """Kanarienvogel (07 ST6): ein verbotener Import in src/ muss gemeldet werden."""
    canary = SRC / "_canary_check.py"
    canary.write_text("import requests\n\nrequests.get\n", encoding="utf-8")
    try:
        result = subprocess.run(
            ["uv", "run", "ruff", "check", "--no-cache", str(canary)], cwd=ROOT, capture_output=True, text=True
        )
    finally:
        canary.unlink()
    assert result.returncode != 0 and "TID251" in result.stdout


# ── Container ────────────────────────────────────────────────────────────────


@pruefung("Container", "Python-Version im Dockerfile wie in pyproject.toml")
def test_dockerfile_python_version_wie_pyproject():
    assert f"ARG PYTHON_MAIN_VERSION={python_minor()}" in DOCKERFILE


@pruefung("Container", "Betriebsregeln: UID 10001, HEALTHCHECK, /data (PF-113)", "R-PORT-5")
def test_dockerfile_betriebsregeln():
    """PF-113: kein root, Gesundheitstest, Schreibrechte nur in /tmp und /data."""
    assert re.search(r"^USER 10001:10001$", DOCKERFILE, re.M)
    assert "HEALTHCHECK" in DOCKERFILE and "platform_sdk.healthcheck" in DOCKERFILE
    assert "DATA_DIR=/data" in DOCKERFILE and "chown 10001:10001 /data" in DOCKERFILE
    assert "EXPOSE 8080" in DOCKERFILE
    assert "app.main:app" in DOCKERFILE


@pruefung("Container", "Container enthält nur .venv, SDK, src, Manifest")
def test_dockerfile_kopiert_nur_das_noetige():
    copies = re.findall(r"^COPY (?:--from=\S+ )?(\S+)", DOCKERFILE, re.M)
    assert set(copies) == {"/app/.venv", "platform_sdk", "src", "manifest.json"}


@pruefung("Container", "Kein Entwicklungsmodus im Betrieb (PF-107)")
def test_kein_entwicklungsmodus_im_betrieb():
    """PF-107: PORTAL_DEV nur im Makefile (make dev), nie in Dateien, die in den Betrieb gehen."""
    for path in [ROOT / "Dockerfile", ROOT / "manifest.json", *PY_FILES, *TEMPLATES]:
        assert "PORTAL_DEV" not in path.read_text(encoding="utf-8"), path


@pruefung("Container", ".dockerignore schließt .env, .git, Tests aus", "R-SEC-1")
def test_dockerignore():
    ignored = (ROOT / ".dockerignore").read_text(encoding="utf-8").split()
    assert {".env", ".git", ".venv", "tests", ".agents"} <= set(ignored)


@pruefung("Container", ".gitignore schließt .env aus", "R-SEC-1")
def test_gitignore():
    ignored = (ROOT / ".gitignore").read_text(encoding="utf-8").split()
    assert {".env", ".venv/"} <= set(ignored)


# ── Gerüst der App ───────────────────────────────────────────────────────────


def main_calls() -> list[str]:
    tree = ast.parse((SRC / "main.py").read_text(encoding="utf-8"))
    return [ast.unparse(node.value) for node in tree.body if isinstance(node, ast.Expr | ast.Assign)]


@pruefung("Gerüst der App", "FastAPI ohne /docs, /redoc, /openapi.json", "R-PORT-2")
def test_main_ohne_api_doku():
    assert any(c == "FastAPI(docs_url=None, redoc_url=None, openapi_url=None)" for c in main_calls())


@pruefung("Gerüst der App", "portal.install(app) vor allen Routen", "R-PORT-1", "R-PORT-2")
def test_install_vor_allen_routen():
    calls = main_calls()
    install = next(i for i, c in enumerate(calls) if c == "portal.install(app)")
    routes = [
        i for i, c in enumerate(calls) if c.startswith(("app.include_router", "app.mount", "app.get", "app.post"))
    ]
    assert routes and install < min(routes)


@pruefung("Gerüst der App", "Routen nur am Router aus portal.router()", "R-PORT-3")
def test_keine_routen_direkt_an_app():
    for file in PY_FILES:
        assert not re.search(r"@app\.(get|post|put|patch|delete|api_route)\(", file.read_text(encoding="utf-8")), file


@pruefung("Gerüst der App", "Keine Cookies im Code", "R-PORT-6")
def test_keine_cookies_im_code():
    """R-PORT-6."""
    for file in PY_FILES:
        text = file.read_text(encoding="utf-8")
        assert "set_cookie" not in text and ".cookies" not in text and "SessionMiddleware" not in text, file


@pruefung("Gerüst der App", "Kein HTML in Python-Code", "R-DES-4")
def test_kein_html_im_python_code():
    for file in PY_FILES:
        text = file.read_text(encoding="utf-8")
        assert not re.search(r"""f["']\s*<[a-zA-Z]""", text), f"{file}: HTML nur in Vorlagen"


@pruefung("Gerüst der App", "Geheimnisse nur aus APP_SECRET_…, ohne Ersatzwert", "R-SEC-1", "R-SEC-2")
def test_geheimnisse_nur_aus_der_umgebung():
    """R-SEC-2: os.environ["APP_SECRET_…"] ohne Ersatzwert."""
    for file in PY_FILES:
        text = file.read_text(encoding="utf-8")
        assert not re.search(r"(getenv|environ\.get)\(\s*[\"']APP_SECRET_[A-Z0-9_]+[\"']\s*,", text), file


# ── Vorlagen und CSS ─────────────────────────────────────────────────────────


@pruefung(
    "Vorlagen und CSS",
    "Vorlagen: kein Rahmen, kein Menü, keine „/“-Links, alt",
    "R-DES-3",
    "R-DES-4",
    "R-UI-1",
    "R-PORT-3",
    "R-A11Y-2",
    "R-A11Y-7",
)
@pytest.mark.parametrize("path", TEMPLATES, ids=lambda p: p.name)
def test_vorlage(path):
    html = path.read_text(encoding="utf-8")
    assert not re.search(r"<(html|head|body)\b", html, re.I), (
        "R-DES-4: eigener Seitenrahmen (<html>, <head>, <body>) in der Vorlage"
    )
    assert not re.search(r"<nav\b", html, re.I), "R-UI-1: eigenes Menü (<nav>) in der Vorlage"
    assert not re.search(r'(href|src|action)="/', html), "R-PORT-3: Adresse beginnt mit „/“ statt portal.url()"
    assert not re.search(r'(href|src)="(https?:)?//', html), "R-DES-3: externe Adresse in der Vorlage"
    assert "|safe" not in html.replace(" ", ""), "R-DES-4: |safe schaltet den Schutz der Vorlage ab"
    assert "outline: none" not in html and "onclick" not in html, "R-A11Y-2: outline: none oder onclick in der Vorlage"
    assert not re.search(r"<img(?![^>]*\balt=)", html), "R-A11Y-7: Bild ohne Alternativtext (alt)"


@pruefung(
    "Vorlagen und CSS",
    "CSS nur mit Variablen, ohne externe Quellen",
    "R-DES-1",
    "R-DES-3",
    "R-A11Y-2",
)
@pytest.mark.parametrize("path", CSS_FILES, ids=lambda p: p.name)
def test_css_nur_variablen(path):
    css = re.sub(r"/\*.*?\*/", "", path.read_text(encoding="utf-8"), flags=re.S)
    assert not re.search(r"#[0-9a-fA-F]{3,8}\b|\b(rgb|rgba|hsl|hsla)\(", css), (
        "R-DES-1: Farbwert (#…, rgb(…), hsl(…)) im eigenen CSS"
    )
    assert not re.search(r"@import|url\(\s*[\"']?(https?:)?//", css), "R-DES-3: externe Quelle oder @import im CSS"
    assert not re.search(r"outline\s*:\s*(none|0)", css), "R-A11Y-2: Fokus-Rahmen im CSS abgeschaltet"


# ── Laufende App ─────────────────────────────────────────────────────────────


@pytest.fixture(scope="module")
def app():
    from app.main import app

    return app


def all_routes(routes) -> list:
    """Routen flach, auch aus eingebundenen Routern (FastAPI: _IncludedRouter)."""
    flat = []
    for route in routes:
        inner = getattr(route, "original_router", None)
        flat += all_routes(inner.routes) if inner is not None else [route]
    return flat


def get_paths(app) -> list[str]:
    paths = []
    for route in all_routes(app.routes):
        if isinstance(route, APIRoute) and route.path != "/healthz" and "{" not in route.path:
            paths.append(route.path)
        elif isinstance(route, Mount) and not route.path.startswith("/__dev"):
            paths.append(route.path + "/app.css")
    return paths


@pruefung("Laufende App", "/healthz antwortet ohne Anmeldung", "R-PORT-5")
def test_healthz_ohne_anmeldung(app):
    assert TestClient(app).get("/healthz").status_code == 200


@pruefung("Laufende App", "Jede Route antwortet ohne Anmeldung mit 401", "R-PORT-2", "R-PORT-6")
def test_jede_route_verlangt_anmeldung(app):
    """R-PORT-2, wie die Konformitätsprüfung (PF-110): ohne Assertion immer 401."""
    client = TestClient(app)
    paths = get_paths(app)
    assert "/" in paths and "/static/app.css" in paths
    for path in paths:
        for method in ("GET", "POST"):
            response = client.request(method, path)
            assert response.status_code == 401, f"{method} {path}"
            assert "set-cookie" not in response.headers


@pruefung("Laufende App", "Keine API-Dokumentation erreichbar", "R-PORT-2")
def test_keine_api_doku_erreichbar(app):
    paths = {getattr(r, "path", None) for r in all_routes(app.routes)}
    assert not paths & {"/docs", "/redoc", "/openapi.json"}


# ── Portal-Bibliothek ────────────────────────────────────────────────────────


@pruefung("Portal-Bibliothek", "platform_sdk/ unverändert (PF-103)", "R-PORT-5")
def test_portal_bibliothek_unveraendert():
    """PF-103."""
    result = subprocess.run(
        ["python", "-m", "platform_sdk.verify_tree"], cwd=ROOT, capture_output=True, text=True, env=os.environ
    )
    assert result.returncode == 0, result.stderr


@pruefung("Portal-Bibliothek", "platform_sdk/ wie in sdk-releases.json freigegeben", "R-PORT-5")
def test_portal_bibliothek_wie_freigegeben():
    releases = ROOT.parent / "portal" / "sdk" / "sdk-releases.json"
    if not releases.is_file():
        pytest.skip("Portal-Repository liegt nicht neben diesem Repository")
    version = (ROOT / "platform_sdk" / "VERSION").read_text(encoding="utf-8").strip()
    expected = json.loads(releases.read_text(encoding="utf-8"))[version]["python"]
    assert (ROOT / "platform_sdk" / "SHA256").read_text(encoding="utf-8").strip() == expected


# ── Container (nur mit CHECK_DOCKER=1) ───────────────────────────────────────

docker = pytest.mark.skipif(
    os.environ.get("CHECK_DOCKER") != "1" or shutil.which("docker") is None, reason="CHECK_DOCKER=1 setzen"
)


@pruefung("Container im Betrieb", "Container: schreibgeschützt, UID 10001, gesund, 401", "R-PORT-2", "R-PORT-5")
@docker
def test_container():
    """ST4: läuft als 10001, schreibgeschützt, ohne Rechte, und wird gesund."""
    image, name = "hka/portal-app:selftest", f"gold-py-selftest-{os.getpid()}"
    subprocess.run(["docker", "build", "--quiet", "--tag", image, "."], cwd=ROOT, check=True, capture_output=True)
    subprocess.run(
        ["docker", "run", "--detach", "--rm", "--name", name, "--read-only", "--cap-drop=ALL",
         "--tmpfs", "/tmp", "--publish", "127.0.0.1::8080", image],
        check=True, capture_output=True,
    )  # fmt: skip
    try:
        port = subprocess.run(["docker", "port", name, "8080"], check=True, capture_output=True, text=True)
        url = "http://" + port.stdout.split()[0]
        status = ""
        for _ in range(30):
            status = subprocess.run(
                ["docker", "inspect", "--format", "{{.State.Health.Status}}", name], capture_output=True, text=True
            ).stdout.strip()
            if status in ("healthy", "unhealthy"):
                break
            time.sleep(1)
        assert status == "healthy"
        user = subprocess.run(["docker", "exec", name, "id", "-u"], capture_output=True, text=True).stdout.strip()
        assert user == "10001"
        with urllib.request.urlopen(url + "/healthz", timeout=2) as response:
            assert response.status == 200
        with pytest.raises(urllib.error.HTTPError) as exc:
            urllib.request.urlopen(url + "/", timeout=2)
        assert exc.value.code == 401
    finally:
        subprocess.run(["docker", "stop", name], capture_output=True)
