# Verwaltete Datei: nicht verändern (sonst PF-108). Eigene Ergänzungen in AGENTS.local.md beschreiben.
# Befehle für den Alltag: make dev | start | test | lint | docker
# Wartung: make lock | sdk-update
# Selbsttests des Golden Master (Plattform-Team): make check | check-skills | check-starter

export PYTHONPATH := .:src
IMAGE ?= hka/portal-app:0.1.0
# Gebaute SDK-Kopie aus dem Portal-Repository (dort: make sdk-release)
SDK_DIST ?= ../portal/sdk/dist/python/platform_sdk

.PHONY: dev start test lint docker lock sdk-update check check-skills check-starter

dev:     ## App mit Test-Anmeldung starten (http://localhost:8080)
	PORTAL_DEV=1 uv run uvicorn app.main:app --reload --app-dir src --host 0.0.0.0 --port 8080

start:   ## App wie im Betrieb starten
	uv run uvicorn app.main:app --app-dir src --host 0.0.0.0 --port 8080

test:    ## automatische Tests
	uv run pytest -q

lint:    ## Regeln prüfen (Ruff, Formatierung, Portal-Bibliothek)
	uv run ruff check src tests
	uv run ruff format --check src tests
	uv run python -m platform_sdk.verify_tree

docker:  ## Container bauen
	docker build --tag $(IMAGE) .

lock:    ## Abhängigkeiten neu festschreiben (uv.lock)
	uv lock --upgrade

sdk-update: ## Portal-Bibliothek (platform_sdk/) durch die freigegebene Kopie ersetzen
	@test -f $(SDK_DIST)/SHA256 || { echo "Keine SDK-Kopie in $(SDK_DIST). Im Portal-Repository: make sdk-release"; exit 1; }
	rsync -a --delete --exclude __pycache__ $(SDK_DIST)/ platform_sdk/
	uv run python -m platform_sdk.verify_tree
	@echo "platform_sdk/ ist jetzt Version $$(cat platform_sdk/VERSION)."

check: check-skills check-starter ## alle Selbsttests des Golden Master

check-skills: ## Skills in .agents/skills prüfen (Form, Regeln, Beispiele, Verweise)
	uv run pytest -q -p no:cacheprovider --junitxml=build/pruefberichte/skills.xml tools/tests/skills

check-starter: ## Starter prüfen (Aufbau, Manifest, Container-Regeln, Anmeldung); mit Container: CHECK_DOCKER=1
	uv run pytest -q -p no:cacheprovider --junitxml=build/pruefberichte/starter.xml tools/tests/starter
	uv run ruff check tools
