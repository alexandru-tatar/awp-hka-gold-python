# awp-hka-gold-python

Golden Master für Portal-Apps in Python (FastAPI). Der Starter enthält eine leere Seite; Ihre App bauen Sie darauf auf.

## Entwickeln im DevContainer

Für die Entwicklung empfehlen wir den vorbereiteten DevContainer. Python, uv und Make müssen dafür nicht auf dem eigenen Rechner installiert werden. Die Einrichtung und Nutzung beschreibt die [DevContainer-Anleitung](.devcontainer/README.md).

## Projekt konfigurieren

Zuerst in `manifest.json` Name, Kurzname (`slug`), Kategorie, Menü und Rollen eintragen.

## Befehle

| Befehl | Was passiert |
|---|---|
| `make dev` | App mit Test-Anmeldung starten: <http://localhost:8080> |
| `make start` | App wie im Betrieb starten (ohne Test-Anmeldung) |
| `make test` | automatische Tests |
| `make lint` | Regeln prüfen (Ruff, Formatierung, Portal-Bibliothek) |
| `make docker` | Produktionscontainer bauen; benötigt Docker auf dem Host und wird auf dem Host ausgeführt, nicht im DevContainer. |
| `make deploy VM=<host>` | App auf die Test-VM bringen und im Portal registrieren (siehe unten) |

Bei Entwicklung ohne DevContainer benötigen Sie [`uv`](https://docs.astral.sh/uv/). Python 3.14 holt `uv` dann selbst.

## Auf die Test-VM bringen

Erst nach Merge auf `main`. Auf dem eigenen Rechner (nicht im DevContainer), mit VPN im Hochschulnetz:

```bash
make deploy VM=iwi-hean-05.hs-karlsruhe.de
```

Das Skript `tools/deploy.sh` baut das Image (`linux/amd64`), kopiert es mit `manifest.json` per `scp` auf die VM, startet dort den Container `app-<slug>` und registriert die App mit `portal-deploy`. Nach etwa 10 s steht sie im Menü unter `https://<host>/apps/<slug>/`. Bei einem Fehler bricht es ab und nennt den Schritt.

- Voraussetzung: Zugang als `sadmin` (ssh, sudo). `slug` in `manifest.json` ist nicht mehr `meine-app`.
- Fertiges Image statt lokal bauen: `make deploy VM=… IMAGE=ghcr.io/<owner>/<repo>@sha256:…`
- Weitere Einstellungen stehen oben in `tools/deploy.sh`.

### Mehrere Container (optional)

Standard ist ein Container. Braucht die App mehr, zum Beispiel eine kleine Datenbank, legen Sie `compose.yml` ins Repository. `make deploy` startet dann alle Services daraus. Pflicht ist ein Service `app`. Nur `app` ist für das Portal erreichbar, die anderen Services nur innerhalb der App.

```yaml
services:
  app:
    build: .
    depends_on: [db]
  db:
    image: postgres:17-alpine
    environment: { POSTGRES_PASSWORD: nur-test }   # nur Testdaten
    volumes: ["db-daten:/var/lib/postgresql/data"]
volumes:
  db-daten:
```

Härtung und Portal-Einstellungen für `app` setzt das Skript selbst. Es bricht ab bei: `ports`, `privileged`, `network_mode`, `cap_add`, Bind-Mounts (`./ordner:…`), eigenen Netzen und `build` bei anderen Services als `app`.

## Aufbau

```text
manifest.json          Name, Menü, Rollen, Schnittstellen-Rechte der App
src/app/main.py        App-Gerüst (nicht ändern)
src/app/views.py       Seiten der App
src/app/templates/     Jinja2-Vorlagen (nur Seiteninhalt)
src/app/static/app.css eigenes CSS (nur Variablen des Portals)
tests/                 Tests (pytest)
platform_sdk/          Portal-Bibliothek (verwaltet, nicht ändern; vorläufige Fassung 1.0.1-dev)
.agents/skills/        Regeln für die KI
```

## Wartung

`make lock` schreibt die Abhängigkeiten in `uv.lock` neu.

`make sdk-update` ersetzt `platform_sdk/` durch die freigegebene Kopie aus dem Portal-Repository (`../portal/sdk/dist/python/platform_sdk`, dort mit `make sdk-release` gebaut). Andere Quelle: `make sdk-update SDK_DIST=…`.

## Selbsttests des Golden Master (Plattform-Team)

Getrennt von den Tests der App in `tests/`. Sie laufen nicht mit `make test`.

| Befehl | Was geprüft wird |
|---|---|
| `make check-skills` | `.agents/skills/`: Kopf, Regeln und Prüfungen (40 / 33 / 7), Zählung im README, Python- und JSON-Beispiele, Verweise auf Befehle und Dateien, Ruff-Verbote, Beispielantworten, Satzlänge, Gleichlauf mit `awp-hka-gold-js` |
| `make check-starter` | Aufbau, Manifest, Abhängigkeiten, Ruff-Verbote, `Dockerfile`, Gerüst der App, Vorlagen und CSS, 401 auf jeder Route, Portal-Bibliothek, Gleichlauf mit `awp-hka-gold-js`. Mit `CHECK_DOCKER=1` zusätzlich Container bauen und starten |
| `make check` | beide Selbsttests, dazu `make lint` und `make test`; schreibt den gemeinsamen Prüfnachweis. Läuft nach einem Fehler weiter, damit der Nachweis immer entsteht |

Jeder Befehl gibt einen deutschen Prüfbericht aus (Prüfbereiche, jede Prüfung mit Ergebnis und betroffenen Einzelregeln, alle 40 Einzelregeln mit Stand, Gesamtergebnis) und speichert ihn im Aufbau der Confluence-Vorlage [„Vorlage: User Story, Akzeptanzkriterien und Prüfnachweis“](https://hka-awp.atlassian.net/wiki/spaces/HKA/pages/19922945):

1. **Prüfnachweis (Vorlage B)**: Block für den Jira-Kommentar, wenn das Ticket auf „In Review“ geht. Datum, Commit, Prüfweg, Nachweis und „Auf eigenem Rechner ausgeführt“ sind ausgefüllt; was nur der Reviewer weiß, bleibt [OFFEN].
2. **Checkliste Code-Review**: `[x]`, wenn der Lauf den Punkt vollständig belegt (Tests, Lint, Secrets, Login, Ticket-ID in den Commits), sonst `[ ]` mit Hinweis.
3. Ergebnis der Läufe, danach die Prüfberichte im Detail.

Dateien in `build/pruefberichte/`:

- `pruefnachweis-aktuell.md` (letzter `make check`, an das Ticket hängen), `pruefnachweis-<Datum_Uhrzeit>.md` (jeder Lauf)
- `pruefbericht-<skills|starter>-aktuell.md` und `-<Datum_Uhrzeit>.md` (einzelne Selbsttests), `-aktuell.json` (Zusammenfassung für `make check`)
- `<skills|starter>.xml` (JUnit, für die Pipeline)

In der Pipeline (GitHub Actions) setzt der Nachweis den Link zum Lauf und zum Pull Request selbst ein.

Ob die KI die Skills befolgt, prüfen diese Tests nicht. Das macht das Prüfskript mit der Testaufgabe (HKA-30).
