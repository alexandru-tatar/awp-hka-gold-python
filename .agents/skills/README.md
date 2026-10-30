# Skills für den Python-Golden-Master

*Status: Entwurf · Version 0.1.0 · Stand 30.10.2026 · Ticket HKA-40 · Verantwortlich: [Name]*

## Zweck

Diese sieben Skills sagen der KI, woran sie sich beim Bau einer Micro-App im Python-Starter (FastAPI) halten muss. Sie setzen die **sieben Regeln des Golden Master** um (Confluence: „Die sieben Regeln des Golden Master (Entwurf 0.1)“, Ticket HKA-29). Die sieben Regeln bestehen aus **40 Einzelregeln** mit fester Kennung wie `R-SEC-3`. Eine Regel ist **erfüllt**, wenn alle Einzelregeln der Stufe „muss“ bestanden sind. Einzelregeln der Stufe „soll“ werden berichtet, entscheiden aber nicht.

Die Tabellen „Regeln“ und „Prüfungen“ in jedem Skill sind Wort für Wort aus dem Regelpapier übernommen. Wer eine Regel ändern will, ändert zuerst das Regelpapier und dann den Skill.

Die Skills sind aus dem JavaScript-Golden-Master (`awp-hka-gold-js/.agents/skills/`) übernommen. Gleich bleiben: Kopf (`name`, `description`), Regeln, Prüfungen und `pipeline-fehler/fehlercodes.md`. Angepasst sind die Abschnitte „So geht es im Python-Starter“, die Beispiele, „Gut / schlecht“ und die Prüflisten. Ändert sich eine Regel, werden beide Fassungen gleich geändert.

## Aufbau

```text
.agents/skills/
├── README.md                    diese Datei
├── design/SKILL.md              Aussehen, Farben, Abstände, Schrift
├── barrierefreiheit/SKILL.md    WCAG 2.1 AA
├── ui-regeln/SKILL.md           Dialoge, Knöpfe, Meldungen, Pflichtfelder
├── schnittstellen/SKILL.md      Mail, Noten, E-Akte über portal.adapters
├── portal/SKILL.md              Anmeldung, Rollen, Menü, Manifest, Links
├── pipeline-fehler/SKILL.md     rote Pipeline verständlich erklären
├── pipeline-fehler/fehlercodes.md   Katalog der Fehlercodes PF-nnn
└── secrets/SKILL.md             Passwörter, Schlüssel, Token
```

Die KI liest immer zuerst die Hauptregeln der App (`AGENTS.md`, kommt mit Phase 2). Einen Skill lädt sie nur, wenn die `description` im Kopf der Datei zur Aufgabe passt. Deshalb beginnt jede Beschreibung mit „Verwenden, wenn …“ und nennt Wörter, die Menschen wirklich sagen.

## Zuordnung der Skills zu den Regeln

| Skill | Wird geladen bei | Einzelregeln | muss | soll |
|---|---|---|---|---|
| `design` | Aussehen, Farben, Abstände, Schrift, CSS | R-DES-1 bis R-DES-5 (5) | 4 | 1 |
| `barrierefreiheit` | Seiten, Formulare, Tabellen, Farben, Tastatur | R-A11Y-1 bis R-A11Y-8 (8) | 7 | 1 |
| `ui-regeln` | Dialoge, Knöpfe, Meldungen, Pflichtfelder | R-UI-1 bis R-UI-7 (7) | 4 | 3 |
| `schnittstellen` | Daten aus Mail, Noten oder E-Akte | R-SCHN-1 bis R-SCHN-5 (5) | 5 | 0 |
| `portal` | Anmeldung, Rollen, Menü, Manifest, Links, Fertigstellen | R-PORT-1 bis R-PORT-7 (7) | 6 | 1 |
| `pipeline-fehler` | rote Pipeline, Fehlermeldung der Pipeline | R-PF-1 bis R-PF-4 (4) | 3 | 1 |
| `secrets` | Passwort, Schlüssel, Token | R-SEC-1 bis R-SEC-4 (4) | 4 | 0 |
| **Summe** | | **40** | **33** | **7** |

## Prüfstellen und Prüfarten

- Prüfarten: **A** = automatisch (Skript, ohne Mensch), **H** = halbautomatisch (Skript bewertet nach festem Raster, eine Person bestätigt), **M** = manuell (eine Person prüft und trägt das Ergebnis im Prüfprotokoll ein).
- Prüfstellen: `lint` = `make lint` (Ruff, `ruff format --check`, Stylelint, Prüfsumme von `platform_sdk/`), `test` = `make test` (`pytest` und Strukturprüfung der gerenderten Seiten mit axe-core), `ci` = Pipeline, `konf` = Konformitätsprüfung der Pipeline, `prf` = Prüfskript und Prüfprotokoll.

## So wird geprüft

Die Skills werden mit der Testaufgabe „Baue eine Noten-Übersicht“ geprüft (Ticket HKA-30): sechs feste Prompts, drei Läufe je Version, ein Prüfprotokoll. Der Starter selbst enthält nur eine leere Seite; die Noten-Übersicht entsteht erst im Testlauf. Jeder Prompt berührt bestimmte Skills:

| Prompt | Berührte Skills |
|---|---|
| 1 Seite und Tabelle anlegen | `portal` |
| 2 Noten aus dem Notensystem holen | `schnittstellen` |
| 3 Passwort in die Konfiguration legen (eingespielter Fehlerfall) | `secrets` |
| 4 Wie im Intranet und barrierefrei | `design`, `barrierefreiheit`, `ui-regeln` |
| 5 „Bring sie ins Portal“ | `portal` (vorbereitend `pipeline-fehler`) |
| 6 Rote Pipeline (eingespielter Fehlerfall) | `pipeline-fehler` |

Ein Lauf ohne Abweichungen wird als **Goldener Standard** gespeichert. Jede neue Version der Skills wird mit ihm verglichen. Die Version der Skills steht im Prüfprotokoll (Git-Tag `skills-vMAJOR.MINOR.PATCH`).

**Stand:** Es hat noch kein Testlauf stattgefunden. Die Skills bleiben Entwurf, bis die Testaufgabe durchgelaufen ist und die Abweichungen eingearbeitet sind.

## Konventionen in den Beispielen

- Python 3.14 (wie das Portal; der Architekturvorschlag nennt noch 3.12), Abhängigkeiten mit `uv` und `uv.lock`, FastAPI, Jinja2 (über `Jinja2Templates`, `autoescape` an), pytest, Ruff: sonst wie im Architekturvorschlag (Starter und Runtime, §2). Aufbau: `src/app/main.py`, `src/app/views.py`, `src/app/templates/`, `src/app/static/app.css`, `tests/`.
- Die Namen des Portal-SDK (`Portal.from_env`, `portal.install`, `portal.router`, `portal.user`, `portal.requires`, `portal.url`, `portal.layout`, `portal.adapters`, `User`, `AdapterError` mit `detail` und `request_id`) folgen dem Architekturvorschlag (Portal SDK, §3.1 und §8).
- Unterschiede zu JavaScript, die in den Skills stehen: Die Person kommt über `Depends(portal.user)` statt `req.portal.user`. Der Adapter-Client braucht kein `req`; er liest die Person aus der laufenden Anfrage. Namen sind klein mit Unterstrich (`list_my_grades`, `request_id`).
- Die Texte sind für die KI geschrieben: Sie-Form, einfache Sprache, kurze Sätze.

## Offene Punkte

1. **Vorläufiges SDK:** `platform_sdk/` ist eine Kopie des Portal-SDK in Version `1.0.0-dev` (Quelle: `portal/sdk/`, dort `make sdk-release`; hier `make sdk-update`). Was dem SDK noch fehlt, steht in `portal/sdk/README.md`. Ändern sich dort Namen, werden die Beispiele in den Skills angepasst.
2. **SDK-Namen:** `platform_sdk/` gibt es erst in Phase 2. Im vorläufigen SDK gibt `portal.requires(...)` die Person zurück. Die Skills nutzen trotzdem beides getrennt (`dependencies=[…]` und `Depends(portal.user)`); das bleibt richtig, falls das endgültige SDK nur prüft.
3. **Lint-Regeln:** `pyproject.toml` verbietet über Ruff (`flake8-tidy-imports.banned-api`) `requests`, `httpx`, `aiohttp`, `urllib3`, `urllib.request`, `http.client`, `socket`, `jwt`, `jose`, `authlib`, `passlib`, `bcrypt`, `itsdangerous`, `fastapi_login`, `fastapi_users`, `starlette.middleware.sessions` und `Markup`. `platform_sdk/` ist von Ruff ausgenommen. Noch ohne Prüfung: `set_cookie`, `request.cookies`, `|safe` in Vorlagen, Stylelint für `app.css` (braucht Node). Dass `docs_url`, `redoc_url` und `openapi_url` auf `None` stehen, prüft `tests/test_app.py`.
4. **Links in Vorlagen:** Die Prüfung auf `href="/` und `src="/` (R-PORT-3) muss die Jinja2-Vorlagen in `src/app/templates/` lesen. Klären, ob das Ruff oder ein eigenes Skript übernimmt.
5. **Prüfung der Seiten:** Geplant ist, dass `make test` die Seiten nach `build/a11y/` rendert und mit `tools/a11y-structural.mjs` (axe-core) prüft. Das gibt es noch nicht; bisher prüft `tests/test_app.py` nur einzelne Merkmale (`lang="de"`, Sprunglink, eine `<h1>`). Für axe-core braucht auch der Python-Starter Node im DevContainer. Mit dem Plattform-Team abstimmen.
6. **Schnittstellenbeschreibungen und Fehlerkatalog:** `docs/schnittstellen/*.md` und `docs/fehlercodes.md` erzeugt die Plattform später aus den OpenAPI-Dateien und aus `failure-codes.yml`. `pipeline-fehler/fehlercodes.md` ist ein Auszug aus dem Architekturvorschlag (Pipeline und Deployment, §6) und gleich wie im JavaScript-Golden-Master. Sobald die Plattform den Katalog liefert, ersetzt er diese Datei.
7. **Manifest-Beispiel:** Der Architekturvorschlag (Starter und Runtime, §7) nennt für Noten das Icon `table`. Das Manifest-Schema erlaubt es nicht. Die Skills nutzen `grades`.
8. **Eigenes CSS einbinden:** Der Architekturvorschlag legt das nicht fest. Das vorläufige SDK bindet `{PORTAL_BASE_PATH}/static/app.css` in `layout()` immer ein. Mit dem JavaScript-Golden-Master und dem Plattform-Team abstimmen.
9. **Nicht abgedeckte Vorgaben:** Drei Vorgaben stehen nicht unter den 40 Einzelregeln (Regelpapier, Abschnitt „Offene Punkte“): Entscheidungen in der README festhalten, `Dockerfile` und `docker-compose.yml` nicht ohne Absprache ändern, `.editorconfig` und Projektstruktur einhalten. Sie sind bewusst nicht in den Skills, bis das Team entschieden hat.
10. **Hauptregeln der App (`AGENTS.md`):** Die Datei, die diese Skills nennt und lädt, gehört nicht zu HKA-40.
11. **Kopien für einzelne KI-Werkzeuge:** Diese Dateien sind die Quelle. Kopien im Format der jeweiligen Werkzeuge erzeugt später die Plattform (Architekturvorschlag, KI-Schicht, §7).
