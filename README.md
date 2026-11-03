# awp-hka-gold-python

Golden Master für Portal-Apps in Python (FastAPI). Der Starter enthält eine leere Seite; Ihre App bauen Sie darauf auf.

Zuerst in `manifest.json` Name, Kurzname (`slug`), Kategorie, Menü und Rollen eintragen.

## Befehle

| Befehl | Was passiert |
|---|---|
| `make dev` | App mit Test-Anmeldung starten: <http://localhost:8080> |
| `make start` | App wie im Betrieb starten (ohne Test-Anmeldung) |
| `make test` | automatische Tests |
| `make lint` | Regeln prüfen (Ruff, Formatierung, Portal-Bibliothek) |
| `make docker` | Container bauen |

Voraussetzung: [`uv`](https://docs.astral.sh/uv/). Python 3.14 holt `uv` selbst.

## Aufbau

```text
manifest.json          Name, Menü, Rollen, Schnittstellen-Rechte der App
src/app/main.py        App-Gerüst (nicht ändern)
src/app/views.py       Seiten der App
src/app/templates/     Jinja2-Vorlagen (nur Seiteninhalt)
src/app/static/app.css eigenes CSS (nur Variablen des Portals)
tests/                 Tests (pytest)
platform_sdk/          Portal-Bibliothek (verwaltet, nicht ändern; vorläufige Fassung 1.0.0-dev)
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
