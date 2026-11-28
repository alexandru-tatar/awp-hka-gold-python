# Fehlercodes der Pipeline

*Auszug aus dem Architekturvorschlag (Pipeline und Deployment, §6) · Stand 29.10.2026 · Ticket HKA-41. Sobald die Plattform den Katalog selbst liefert, ersetzt er diese Datei.*

Jeder fehlgeschlagene Schritt der Pipeline druckt einen Block in genau dieser Form:

```text
============================================================
FEHLER PF-102  –  Geheimnis im Code gefunden
Was ist passiert:   In src/app/views.py (Zeile 12) steht etwas, das wie ein Schlüssel aussieht.
Warum wichtig:      Wer den Code sieht, könnte damit arbeiten.
Was tun:            1. Entfernen Sie den Schlüssel aus dem Code.
                    2. Er gilt als verbraucht – melden Sie ihn dem Plattform-Team, damit er ersetzt wird.
                    3. Mehr dazu: Skill „secrets".
Technische Details: (gekürzt, Werte geschwärzt)
  RuleID: generic-api-key  File: src/app/views.py  Line: 12
============================================================
```

## Katalog

| Code | Stufe | Titel | Was ist passiert | Was tun |
|---|---|---|---|---|
| PF-101 | lint | Regelverstoß im Code | Eine Regel der Plattform wurde verletzt (Datei und Zeile stehen in der Meldung). | Datei und Zeile öffnen, Regel lesen, korrigieren; lokal mit `make lint` prüfen. Skill zur Regel laden (`portal`, `schnittstellen`, `design`). |
| PF-102 | secrets | Geheimnis im Code gefunden | Im Code steht etwas, das wie ein Passwort oder Schlüssel aussieht. | Entfernen. Das Geheimnis gilt als verbraucht und muss ersetzt werden – Plattform-Team informieren. Skill `secrets`. |
| PF-103 | integrity | Portal-Bibliothek verändert | Der Ordner `platform_sdk/` stimmt nicht mit der freigegebenen Version überein. | `make sdk-update` ausführen; Änderungen daran sind nicht erlaubt. |
| PF-104 | manifest | `manifest.json` ungültig | Ein Feld fehlt, ist falsch oder nennt eine unbekannte Rolle oder Schnittstelle. | Die genannte Stelle korrigieren. Erlaubte Rollen und Rechte stehen in der Meldung. Skill `portal`. |
| PF-105 | test | Tests fehlgeschlagen | Mindestens ein automatischer Test ist rot. | `make test` lokal starten, den ersten roten Test ansehen und beheben. |
| PF-106 | build | Kritische Sicherheitslücke in einer Abhängigkeit | Ein verwendetes Paket hat eine bekannte, kritische Lücke. | Paket aktualisieren (`make lock`), dann erneut versuchen. Gibt es keine neue Version: Plattform-Team fragen. |
| PF-107 | integrity | Entwicklungsmodus in der Betriebs-Konfiguration | Der Text `PORTAL_DEV` steht in einer Datei, die in den Betrieb geht. | Entfernen. Der Entwicklungsmodus gehört nur in `.devcontainer/`. |
| PF-108 | integrity | Verwaltete Datei verändert | Eine Datei, die die Plattform pflegt (z. B. `Makefile`, `AGENTS.md`, `Dockerfile`), wurde geändert. | Änderung zurücknehmen oder `make template-update` ausführen. Eigene Ergänzungen gehören in `AGENTS.local.md`. |
| PF-109 | build | Container konnte nicht gebaut werden | Beim Bauen des Containers ist ein Schritt fehlgeschlagen. | Die erste Fehlerzeile der technischen Details lesen; `make docker` lokal ausführen. |
| PF-110 | conformance | App prüft die Anmeldung nicht | Die App hat eine Anfrage ohne Anmeldung beantwortet (oder `portal.install(app)` fehlt). | In `main.py`/`app.js` `portal.install(app)` vor allen Routen aufrufen. Skill `portal`. |
| PF-111 | conformance | App startet nicht oder wird nicht gesund | Der Container wurde nicht bereit, oder `/healthz` antwortet nicht. | Logs ansehen (`make docker`, dann Container starten); `/healthz` nicht verändern. |
| PF-112 | conformance | App setzt Cookies | Die App sendet `Set-Cookie`. Das ist im Portal nicht erlaubt. | Cookies entfernen; Zustand serverseitig speichern. |
| PF-113 | conformance | Container entspricht nicht den Betriebsregeln | Läuft als Administrator, hat keinen Gesundheitstest oder braucht Schreibrechte außerhalb von `/tmp` und `/data`. | `Dockerfile` nicht verändern (`PF-108`) oder Schreibzugriffe nach `/data` verlegen. |
| PF-201 | deploy | Bereitstellung zurückgesetzt | Die neue Version wurde nicht gesund und ist automatisch durch die vorherige ersetzt worden (oder entfernt, wenn es keine gab). | Technische Details lesen; Fehler beheben; erneut bereitstellen. Die App ist weiterhin in der alten Version erreichbar. |
| PF-202 | deploy | Registrierung abgelehnt | Die Plattform lehnt die App ab (anderer Besitzer für diesen Namen, Version zu alt, unbekannte Rolle). | Meldung lesen; bei „Besitzer" das Plattform-Team fragen. |
| PF-203 | deploy | Zurücksetzen fehlgeschlagen | Auch die vorherige Version ist nicht gesund. | **Sofort das Plattform-Team benachrichtigen.** Nichts weiter versuchen. |
| PF-204 | deploy | Bereitstellung gesperrt | Eine andere Bereitstellung dieser App läuft gerade. | Einige Minuten warten, dann erneut starten. |
| PF-205 | deploy | Container-Abbild nicht gefunden oder nicht geeignet | Das veröffentlichte Abbild fehlt in der Ablage oder hat keinen Gesundheitstest bzw. den falschen Benutzer. | Pipeline für den Hauptzweig erneut laufen lassen (Stufe „publish"); bleibt es dabei, Plattform-Team informieren. |

## Catalog in English

The blocks come in English when the person or the pipeline sets `PORTAL_LANG=en` (otherwise German, see above). The code and the stage stay the same. The labels are `ERROR`, `What happened:`, `Why it matters:`, `What to do:` and `Technical details:`.

```text
============================================================
ERROR PF-102  –  Secret found in code
What happened:      In src/app/views.py (line 12) there is something that looks like a key.
Why it matters:     Anyone who sees the code could use it.
What to do:         1. Remove the key from the code.
                    2. It counts as used up – report it to the platform team so it can be replaced.
                    3. More on this: skill "secrets".
Technical details:  (shortened, values blacked out)
  RuleID: generic-api-key  File: src/app/views.py  Line: 12
============================================================
```

| Code | Stage | Title | What happened | What to do |
|---|---|---|---|---|
| PF-101 | lint | Rule violation in the code | A platform rule was broken (file and line are in the message). | Open the file and line, read the rule, fix it; check locally with `make lint`. Load the skill for the rule (`portal`, `schnittstellen`, `design`). |
| PF-102 | secrets | Secret found in code | The code contains something that looks like a password or key. | Remove it. The secret counts as used up and must be replaced – inform the platform team. Skill `secrets`. |
| PF-103 | integrity | Portal library changed | The folder `platform_sdk/` does not match the released version. | Run `make sdk-update`; changes to it are not allowed. |
| PF-104 | manifest | `manifest.json` invalid | A field is missing, wrong, or names an unknown role or interface. | Fix the place named. Allowed roles and rights are in the message. Skill `portal`. |
| PF-105 | test | Tests failed | At least one automatic test is red. | Run `make test` locally, look at the first red test and fix it. |
| PF-106 | build | Critical security hole in a dependency | A package in use has a known critical hole. | Update the package (`make lock`), then try again. If there is no new version: ask the platform team. |
| PF-107 | integrity | Development mode in the production configuration | The text `PORTAL_DEV` is in a file that goes into production. | Remove it. Development mode belongs only in `.devcontainer/`. |
| PF-108 | integrity | Managed file changed | A file the platform maintains (for example `Makefile`, `AGENTS.md`, `Dockerfile`) was changed. | Undo the change or run `make template-update`. Your own additions belong in `AGENTS.local.md`. |
| PF-109 | build | Container could not be built | A step failed while building the container. | Read the first error line of the technical details; run `make docker` locally. |
| PF-110 | conformance | App does not check the login | The app answered a request without login (or `portal.install(app)` is missing). | Call `portal.install(app)` before all routes in `main.py`/`app.js`. Skill `portal`. |
| PF-111 | conformance | App does not start or does not become healthy | The container did not become ready, or `/healthz` does not answer. | Look at the logs (`make docker`, then start the container); do not change `/healthz`. |
| PF-112 | conformance | App sets cookies | The app sends `Set-Cookie`. This is not allowed in the portal. | Remove cookies; keep state on the server. |
| PF-113 | conformance | Container does not follow the operating rules | Runs as administrator, has no health check, or needs write access outside `/tmp` and `/data`. | Do not change the `Dockerfile` (`PF-108`) or move writes to `/data`. |
| PF-201 | deploy | Deployment rolled back | The new version did not become healthy and was replaced automatically by the previous one (or removed if there was none). | Read the technical details; fix the error; deploy again. The app is still reachable in the old version. |
| PF-202 | deploy | Registration rejected | The platform rejects the app (another owner for this name, version too old, unknown role). | Read the message; for "owner" ask the platform team. |
| PF-203 | deploy | Rollback failed | The previous version is not healthy either. | **Inform the platform team at once.** Try nothing else. |
| PF-204 | deploy | Deployment locked | Another deployment of this app is running. | Wait a few minutes, then start again. |
| PF-205 | deploy | Container image not found or not suitable | The published image is missing in the registry or has no health check or the wrong user. | Run the pipeline for the main branch again (stage "publish"); if it stays, inform the platform team. |
