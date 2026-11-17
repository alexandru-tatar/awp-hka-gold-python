---
name: schnittstellen
description: Verwenden, wenn Daten aus Noten, bwSync&Share, Mail oder E-Akte geholt oder gesendet werden sollen, zum Beispiel bei „Hol die Noten aus dem Notensystem“ oder „Zeig die Dateien aus bwSync&Share“, oder wenn ein Web-Aufruf, eine Datenbankverbindung oder eine Adresse eines anderen Systems gebraucht wird.
---

# Schnittstellen (Noten, bwSync&Share, Mail, E-Akte)

Andere Systeme erreichen Sie nur über `portal.adapters`. Die App hat im Betrieb kein Internet und braucht für diese Systeme kein Passwort. Das Portal prüft, wer die Person ist und was die App darf.

Was jedes System kann, steht in seiner Beschreibung im SDK: `platform_sdk/adapters/noten/README.md` und `platform_sdk/adapters/bwsync/README.md`. Für Mail und E-Akte gibt es noch keine Beschreibung; diese Systeme gibt es für Apps also noch nicht. Die Regeln des SDK stehen in der README des Portal-SDK (Abschnitt „Regeln“).

## Regeln

| ID | Regel | Stufe |
|---|---|---|
| R-SCHN-1 | Mail, Noten und E-Akte nur über `portal.adapters`; keine eigenen Web-Aufrufe. | muss |
| R-SCHN-2 | Nur Aufrufe, Felder und Fehlertypen verwenden, die in der README des Systems (`platform_sdk/adapters/<system>/README.md`) stehen; nichts erfinden. | muss |
| R-SCHN-3 | Fehler der Schnittstelle werden nach `type` behandelt und der Person mit einem eigenen Text der App angezeigt; `detail` höchstens zusätzlich. | muss |
| R-SCHN-4 | Persönliche Daten aus Schnittstellen werden nicht gespeichert. | muss |
| R-SCHN-5 | Das Manifest nennt genau die benötigten Schnittstellen-Rechte. | muss |

## So geht es im Python-Starter

1. Lesen Sie zuerst die Beschreibung des Systems in `platform_sdk/adapters/<system>/README.md` (zum Beispiel `platform_sdk/adapters/noten/README.md`). Nur Aufrufe, Felder und Fehler, die dort stehen, sind erlaubt. Steht etwas nicht dort, gibt es das nicht. Erfinden Sie nichts und fragen Sie nach.
2. Rufen Sie das System mit `await portal.adapters.<system>.<aufruf>(...)` auf, zum Beispiel `await portal.adapters.noten.list_my_grades()`. Die Namen sind in Python klein mit Unterstrich. Die Werte übergeben Sie mit Namen (`semester="2026W"`).
3. Rufen Sie die Schnittstelle nur innerhalb einer Route auf. Das Portal erkennt die angemeldete Person an der laufenden Anfrage. Beim Start der App oder in einem Hintergrund-Task gibt es keine Person. Dann kommt der Fehler `no-user-context`.
4. Es gibt keine Möglichkeit, Daten einer anderen Person abzufragen. Fragen Sie nicht danach.
5. Fehler entscheiden Sie **nach `err.type`** (und `err.status`), nie nach einem Text, und vergleichen mit der Konstante aus `platform_sdk.adapters.<system>.errors` bzw. `platform_sdk.adapters.transport` (zum Beispiel `errors.EXISTS`, `transport.BACKEND_UNAVAILABLE`). Den Text für die Person schreiben Sie selbst; welche Reaktion passt, steht in der Fehler-Tabelle der README. Zeigen Sie dazu die Nummer (`err.request_id`). `err.detail` ist für Logs und Fehlersuche, Sie dürfen ihn zusätzlich anzeigen, müssen aber nicht; er kann leer sein. Eine leere Seite ist nie die Antwort. Fangen Sie nur `AdapterError`, nie `Exception`.
6. Speichern Sie keine persönlichen Daten aus Schnittstellen: nicht in Dateien, nicht in einer Datenbank (auch nicht in `db.py` oder `$DATA_DIR`), nicht in einer Variablen auf Modulebene, nicht mit `functools.lru_cache` oder `functools.cache`.
7. Tragen Sie im `manifest.json` unter `adapters` genau die Rechte ein, die der Code nutzt, zum Beispiel `"noten:read"` (Skill `portal`).

```python
from fastapi import Depends
from fastapi.responses import HTMLResponse
from platform_sdk import AdapterError, User
from platform_sdk.adapters import transport


@router.get("/", response_class=HTMLResponse)
async def home(user: User = Depends(portal.user)):
    grades = []
    problem = None
    try:
        result = await portal.adapters.noten.list_my_grades()
        grades = result.items
    except AdapterError as err:
        # eigener Text nach type; der Noten-Adapter kennt nur die allgemeinen Typen (README)
        text = "Die Noten sind gerade nicht abrufbar. Bitte versuchen Sie es später erneut."
        if err.type == transport.BACKEND_TIMEOUT:
            text = "Das Notensystem antwortet gerade zu langsam. Bitte versuchen Sie es gleich noch einmal."
        problem = {"text": text, "request_id": err.request_id}
    body = templates.get_template("noten.html").render(grades=grades, problem=problem)
    return await portal.layout(title="Meine Noten", body=body, current=portal.url("/"), user=user)
```

Die Vorlage zeigt bei `problem` den Text `problem.text` samt Nummer. Bei einer leeren Liste zeigt sie „Es liegen noch keine Noten vor.“ Wie die Liste im Ergebnis heißt (hier `items`), steht in `platform_sdk/adapters/noten/README.md`.

Für Anzeigen gibt es fertige Hilfen ohne HTML in `platform_sdk/common/`: Zeitpunkte (`dates.format_datetime`), Dateigrößen (`sizes.format_size`) und Download-Header (`downloads.download_headers`). Für bwSync&Share prüft `platform_sdk.adapters.bwsync.paths` Namen und Pfade und liefert die Pfadleiste als Daten (`breadcrumbs`); das HTML dazu baut die App.

Verbotene Wege, die `make lint` (Ruff) meldet: `requests`, `httpx`, `urllib.request`. Ebenso verboten, auch wenn die Prüfung sie noch nicht kennt: `aiohttp`, `urllib3`, `http.client`, `socket`, eigene Datenbanktreiber zu anderen Systemen (`psycopg`, `pymysql`, `sqlalchemy` mit fremder Adresse). `httpx` benutzt nur `platform_sdk/` selbst.

## Tests

Im Test rufen Sie kein echtes System auf. Jedes System hat im SDK einen Fake, der sich wie das echte System verhält (gleiche Fehlertypen), zum Beispiel `FakeNoten` und `FakeBwSync`. Testen Sie auch den Fehlerfall: `fake.fail = (status, type)`.

```python
import pytest
from platform_sdk.adapters import transport
from platform_sdk.adapters.noten.testing import FakeNoten


@pytest.fixture
def noten():
    fake = FakeNoten({"student-test": [{"module": "Mathe 1", "semester": "2026W", "grade": "1,3", "credits": 5}]})
    fake.install(portal)
    yield fake
    fake.uninstall()


def test_noten_nicht_abrufbar(client, noten):
    noten.fail = (503, transport.BACKEND_UNAVAILABLE)
    ...
```

Im Entwicklungsmodus (`make dev`) liefert das Portal feste Testdaten aus `platform_sdk/adapters/noten/fixtures/`; dafür brauchen Sie nichts zu tun.

## Gut / schlecht

| Schlecht | Gut |
|---|---|
| `import httpx; await httpx.AsyncClient().get("https://…")` | `await portal.adapters.noten.list_my_grades()` |
| `import requests` | `portal.adapters` |
| Zugriff auf ein erfundenes Feld `matrikelnummer` | nur Felder aus `platform_sdk/adapters/noten/README.md` (`module`, `semester`, `grade`) |
| leere Seite bei „System nicht erreichbar“ | Seite mit eigenem Text und der Nummer `err.request_id` |
| `if "existiert" in err.detail:` oder `err.type == "bwsync-exists"` | `err.type == errors.EXISTS` (Konstante aus `platform_sdk.adapters.bwsync.errors`) |
| `except Exception: pass` | `except AdapterError as err:` und einen Text nach `err.type` anzeigen |
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
- [ ] Jeder Aufruf, jedes Feld und jeder Fehlertyp steht in der README des Systems unter `platform_sdk/adapters/`
- [ ] Schnittstellen nur innerhalb von Routen aufgerufen
- [ ] Jeder Fehler wird nach `type` behandelt und mit eigenem Text angezeigt
- [ ] Nichts aus den Schnittstellen wird gespeichert oder zwischengespeichert
- [ ] `manifest.json` nennt genau die genutzten Rechte
- [ ] `make lint` und `make test` laufen ohne Fehler
