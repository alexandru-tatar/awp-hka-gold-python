---
name: schnittstellen
description: Verwenden, wenn Daten aus Mail, Noten oder E-Akte geholt oder gesendet werden sollen, zum Beispiel bei „Hol die Noten aus dem Notensystem“, oder wenn ein Web-Aufruf, eine Datenbankverbindung oder eine Adresse eines anderen Systems gebraucht wird.
---

# Schnittstellen (Mail, Noten, E-Akte)

Andere Systeme erreichen Sie nur über `portal.adapters`. Die App hat im Betrieb kein Internet und braucht für diese Systeme kein Passwort. Das Portal prüft, wer die Person ist und was die App darf.

## Regeln

| ID | Regel | Stufe |
|---|---|---|
| R-SCHN-1 | Mail, Noten und E-Akte nur über `portal.adapters`; keine eigenen Web-Aufrufe. | muss |
| R-SCHN-2 | Nur Felder und Adressen verwenden, die in `docs/schnittstellen/*.md` stehen; nichts erfinden. | muss |
| R-SCHN-3 | Fehler der Schnittstelle werden der Person mit dem mitgelieferten Text angezeigt. | muss |
| R-SCHN-4 | Persönliche Daten aus Schnittstellen werden nicht gespeichert. | muss |
| R-SCHN-5 | Das Manifest nennt genau die benötigten Schnittstellen-Rechte. | muss |

## So geht es im Python-Starter

1. Lesen Sie zuerst die Beschreibung in `docs/schnittstellen/<system>.md` (`noten.md`, `mail.md`, `eakte.md`). Nur Aufrufe, Felder und Fehler, die dort stehen, sind erlaubt. Steht etwas nicht dort, gibt es das nicht. Erfinden Sie nichts und fragen Sie nach.
2. Rufen Sie das System mit `await portal.adapters.<system>.<aufruf>(...)` auf, zum Beispiel `await portal.adapters.noten.list_my_grades()`. Die Namen sind in Python klein mit Unterstrich. Die Werte übergeben Sie mit Namen (`semester="2026W"`).
3. Rufen Sie die Schnittstelle nur innerhalb einer Route auf. Das Portal erkennt die angemeldete Person an der laufenden Anfrage. Beim Start der App oder in einem Hintergrund-Task gibt es keine Person. Dann kommt der Fehler `no-user-context`.
4. Es gibt keine Möglichkeit, Daten einer anderen Person abzufragen. Fragen Sie nicht danach.
5. Fehler zeigen Sie der Person mit dem mitgelieferten Text (`err.detail`) und der Nummer (`err.request_id`). Eine leere Seite ist nie die Antwort. Fangen Sie nur `AdapterError`, nie `Exception`.
6. Speichern Sie keine persönlichen Daten aus Schnittstellen: nicht in Dateien, nicht in einer Datenbank (auch nicht in `db.py` oder `$DATA_DIR`), nicht in einer Variablen auf Modulebene, nicht mit `functools.lru_cache` oder `functools.cache`.
7. Tragen Sie im `manifest.json` unter `adapters` genau die Rechte ein, die der Code nutzt, zum Beispiel `"noten:read"` (Skill `portal`).

```python
from fastapi import Depends
from fastapi.responses import HTMLResponse
from platform_sdk import AdapterError, User


@router.get("/", response_class=HTMLResponse)
async def home(user: User = Depends(portal.user)):
    grades = []
    problem = None
    try:
        result = await portal.adapters.noten.list_my_grades()
        grades = result.items
    except AdapterError as err:
        problem = {"detail": err.detail, "request_id": err.request_id}
    body = templates.get_template("noten.html").render(grades=grades, problem=problem)
    return await portal.layout(title="Meine Noten", body=body, current=portal.url("/"), user=user)
```

Die Vorlage zeigt bei `problem` den Text `problem.detail` samt Nummer. Bei einer leeren Liste zeigt sie „Es liegen noch keine Noten vor.“ Wie die Liste im Ergebnis heißt (hier `items`), steht in `docs/schnittstellen/noten.md`.

Verbotene Wege, die `make lint` (Ruff) meldet: `requests`, `httpx`, `urllib.request`. Ebenso verboten, auch wenn die Prüfung sie noch nicht kennt: `aiohttp`, `urllib3`, `http.client`, `socket`, eigene Datenbanktreiber zu anderen Systemen (`psycopg`, `pymysql`, `sqlalchemy` mit fremder Adresse). `httpx` benutzt nur `platform_sdk/` selbst.

## Tests

Im Test rufen Sie kein echtes System auf. Ersetzen Sie den Aufruf mit `monkeypatch` durch eine feste Antwort. Testen Sie auch den Fehlerfall mit einem `AdapterError`.

```python
async def kaputt(**kwargs):
    raise AdapterError(503, "backend-unavailable", "Das System ist gerade nicht erreichbar.", "r-test-1")

monkeypatch.setattr(portal.adapters.noten, "list_my_grades", kaputt)
```

Im Entwicklungsmodus (`make dev`) liefert das Portal feste Testdaten aus `platform_sdk/fixtures/`; dafür brauchen Sie nichts zu tun.

## Gut / schlecht

| Schlecht | Gut |
|---|---|
| `import httpx; await httpx.AsyncClient().get("https://…")` | `await portal.adapters.noten.list_my_grades()` |
| `import requests` | `portal.adapters` |
| Zugriff auf ein erfundenes Feld `matrikelnummer` | nur Felder aus `docs/schnittstellen/noten.md` (`module`, `semester`, `grade`) |
| leere Seite bei „System nicht erreichbar“ | Seite mit dem Text `err.detail` und der Nummer `err.request_id` |
| `except Exception: pass` | `except AdapterError as err:` und den Text anzeigen |
| Aufruf der Schnittstelle beim Start der App | Aufruf nur in einer Route |
| gelesene Mails in `$DATA_DIR/app.db` abgelegt | Daten nur für die Anzeige verwenden, nichts ablegen |
| `@lru_cache` um den Aufruf der Schnittstelle | bei jeder Anfrage neu holen |
| Noten werden gelesen, aber `noten:read` fehlt im Manifest | `"adapters": ["noten:read"]` im `manifest.json` |

## Prüfungen, die das absichern

A = automatisch, H = halbautomatisch (eine Person bestätigt), M = manuell (eine Person prüft). Die Prüfstellen stehen in `.agents/skills/README.md`.

| ID | Prüfung |
|---|---|
| R-SCHN-1 | A (`lint`: verbotene Importe; `konf`: kein Internetzugang im Betrieb) |
| R-SCHN-2 | A (`test`: die Schnittstelle prüft Antworten streng) |
| R-SCHN-3 | A (`test`) |
| R-SCHN-4 | H (`prf`: Skript meldet Schreibzugriffe, Person bestätigt) |
| R-SCHN-5 | A (`ci`: Vergleich Manifest ↔ Code) |

## Vor dem Abschluss

- [ ] Kein `requests`, kein `httpx`, kein eigener Web-Aufruf
- [ ] Jeder Aufruf und jedes Feld steht in `docs/schnittstellen/*.md`
- [ ] Schnittstellen nur innerhalb von Routen aufgerufen
- [ ] Jeder Fehler wird mit seinem Text angezeigt
- [ ] Nichts aus den Schnittstellen wird gespeichert oder zwischengespeichert
- [ ] `manifest.json` nennt genau die genutzten Rechte
- [ ] `make lint` und `make test` laufen ohne Fehler
