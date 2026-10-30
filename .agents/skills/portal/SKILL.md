---
name: portal
description: Verwenden beim Anlegen einer neuen Web-App im Portal und bei Anmeldung (Login), Rollen, Menü, manifest.json, Links und Seitenrahmen, und wenn die App fertig ist und ins Portal soll, zum Beispiel bei „Fertig. Bring sie ins Portal.“ oder beim Pull Request.
---

# Portal

Die App läuft im HKA Portal. Das Portal meldet die Person an, zeichnet den Seitenrahmen und das Menü und entscheidet, wer die App sehen darf. Ihre App baut nichts davon nach.

## Regeln

| ID | Regel | Stufe |
|---|---|---|
| R-PORT-1 | Kein eigenes Login, Passwort oder eigene Token-Prüfung. | muss |
| R-PORT-2 | Wer die Person ist, kommt nur aus `portal.user`; jede Seite verlangt Anmeldung. | muss |
| R-PORT-3 | Links nur über `portal.url(...)`; keine Adressen, die mit `/` beginnen. | muss |
| R-PORT-4 | `manifest.json` ist vollständig und aktuell (Name, Kategorie, Menü, Rollen, Version). | muss |
| R-PORT-5 | `/healthz` bleibt unverändert; `platform_sdk/` wird nicht verändert. | muss |
| R-PORT-6 | Die App setzt und liest keine Cookies. | muss |
| R-PORT-7 | Rollen im Manifest sind die kleinste Gruppe, die die App braucht. | soll |

## So geht es im Python-Starter

1. **Anmeldung:** Es gibt kein eigenes Login, kein Passwort und keine eigene Token-Prüfung. `portal.install(app)` steht in `src/app/main.py` direkt nach `FastAPI(...)` und vor allen Routen. Dort bleibt es.
2. **Keine offenen Seiten von FastAPI:** `FastAPI(docs_url=None, redoc_url=None, openapi_url=None)` bleibt so. Sonst liefert FastAPI `/docs` und `/openapi.json` aus.
3. **Routen:** Bauen Sie Routen nur am Router aus `portal.router()`. Er setzt die Adresse der App davor. Schreiben Sie Routen nie direkt an `app`.
4. **Person:** Wer angemeldet ist, kommt nur über `user: User = Depends(portal.user)` (`sub`, `name`, `roles`, `email`). Jede Route hat diese Abhängigkeit. Lesen Sie die Rolle nie aus der Adresse, aus einem Formular oder aus einem Header.
5. **Rollen:** Eine Seite für bestimmte Rollen schützen Sie mit `dependencies=[Depends(portal.requires("student"))]`. Tragen Sie im Manifest die kleinste Gruppe ein, die die App braucht. Fragen Sie, wer die App sehen darf. Rollen heißen zum Beispiel `student`, `employee` und `professor`. Erlaubt sind nur Namen aus dem Rollenverzeichnis der Plattform.
6. **Links:** Links bauen Sie mit `portal.url("/pfad")` im Code und geben sie an die Vorlage. Auch `RedirectResponse` bekommt `portal.url(...)`. Schreiben Sie nie eine Adresse, die mit `/` beginnt. Der Pfad im Routen-Dekorator (`@router.get("/noten")`) ist kein Link; dort ist `/` richtig.
7. **Manifest:** `manifest.json` ist vollständig und aktuell. Unbekannte Felder werden abgelehnt.
8. **Unverändert lassen:** `/healthz` und den Ordner `platform_sdk/`.
9. **Keine Cookies:** Die App setzt und liest keine. Kein `response.set_cookie(...)`, kein `request.cookies`, keine `SessionMiddleware`. Zustand liegt auf dem Server, nicht beim Browser.
10. **Keine Login-Bibliotheken:** zum Beispiel `jwt` (PyJWT), `python-jose`, `authlib`, `passlib`, `bcrypt`, `itsdangerous`, `fastapi-login`, `fastapi-users`. PyJWT steht in den Abhängigkeiten nur für `platform_sdk/`.

```python
# src/app/main.py
from pathlib import Path

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from platform_sdk import Portal

from . import views

portal = Portal.from_env()
app = FastAPI(docs_url=None, redoc_url=None, openapi_url=None)
portal.install(app)  # Anmeldung und /healthz: vor allen Routen, nicht entfernen
app.mount(portal.url("/static"), StaticFiles(directory=Path(__file__).parent / "static"), name="static")
app.include_router(views.build_router(portal))
```

```python
# src/app/views.py
from fastapi import Depends
from fastapi.responses import HTMLResponse
from platform_sdk import User


def build_router(portal):
    router = portal.router()

    @router.get("/", response_class=HTMLResponse, dependencies=[Depends(portal.requires("student"))])
    async def home(user: User = Depends(portal.user)):  # einzige Quelle für Name und Rollen
        ...

    return router
```

```json
{
  "slug": "noten",
  "name": "Noten-Übersicht",
  "category": "Studium",
  "menu": { "label": "Meine Noten", "icon": "grades" },
  "roles": ["student"],
  "adapters": ["noten:read"],
  "version": "1.0.0"
}
```

Pflichtfelder sind `slug`, `name`, `category`, `menu` (mit `label` und `icon`), `roles` und `version`. Erlaubt sind:

| Feld | Werte |
|---|---|
| `slug` | Kleinbuchstaben, Ziffern, Bindestrich; 3 bis 31 Zeichen; beginnt mit einem Buchstaben |
| `category` | `Studium`, `Verwaltung`, `Kommunikation`, `Sonstiges` |
| `menu.icon` | `grades`, `mail`, `calendar`, `document`, `people`, `book`, `room`, `settings`, `info` |
| `roles` | mindestens eine Rolle aus dem Rollenverzeichnis, zum Beispiel `student` |
| `adapters` | optional; Form `system:recht`, zum Beispiel `noten:read`, `mail:send` |
| `version` | drei Zahlen mit Punkt, zum Beispiel `1.0.0` |

Quelle ist `schemas/manifest.schema.json` im Portal. Weicht dieser Text davon ab, gilt das Schema.

## Fertigstellen

1. Führen Sie `make lint` und `make test` aus und beheben Sie alle Fehler.
2. Erklären Sie der Person in zwei oder drei Sätzen, was ein Pull Request ist: eine Bitte, die Änderung in den Hauptzweig zu übernehmen. Eine zweite Person liest sie und gibt sie frei. Erst bei grüner Pipeline und mit Freigabe wird sie übernommen. In GitLab heißt er „Merge Request“.
3. Legen Sie den Pull Request an.

## Gut / schlecht

| Schlecht | Gut |
|---|---|
| eigenes Anmeldeformular, `import jwt`, `passlib` | `user: User = Depends(portal.user)` |
| Die Rolle wird aus der Adresse `?rolle=prof` gelesen | `Depends(portal.requires("professor"))` und `user.roles` |
| `@app.get("/noten")` direkt an der App | `@router.get("/noten")` am Router aus `portal.router()` |
| Route ohne `Depends(portal.user)` | jede Route mit `Depends(portal.user)` |
| `FastAPI()` mit `/docs` und `/openapi.json` | `FastAPI(docs_url=None, redoc_url=None, openapi_url=None)` |
| `<a href="/noten">` | `<a href="{{ noten_url }}">` in der Vorlage; im Code `noten_url=portal.url("/noten")` übergeben |
| `RedirectResponse("/danke")` | `RedirectResponse(portal.url("/danke"), status_code=303)` |
| `"roles": []` oder das Feld fehlt | `"roles": ["student"]` |
| eine Datei in `platform_sdk/` bearbeitet | `platform_sdk/` unverändert lassen |
| `response.set_cookie("theme", "dark")` | Einstellungen auf dem Server speichern oder weglassen |
| App für Noten mit den Rollen „Studierende“ und „Mitarbeitende“ | `"roles": ["student"]` |

## Prüfungen, die das absichern

A = automatisch, H = halbautomatisch (eine Person bestätigt), M = manuell (eine Person prüft). Die Prüfstellen stehen in `.agents/skills/README.md`.

| ID | Prüfung |
|---|---|
| R-PORT-1 | A (`lint`: verbotene Bibliotheken) |
| R-PORT-2 | A (`konf`: jede Route liefert ohne Anmeldung 401) |
| R-PORT-3 | A (`lint`) |
| R-PORT-4 | A (`ci`: Schema-Prüfung) |
| R-PORT-5 | A (`ci`: Prüfsumme, Routenliste) |
| R-PORT-6 | A (`konf`) |
| R-PORT-7 | M (`prf`) |

## Vor dem Abschluss

- [ ] Kein eigenes Login, `portal.install(app)` steht vor allen Routen
- [ ] `docs_url`, `redoc_url` und `openapi_url` sind `None`
- [ ] Alle Routen hängen am Router aus `portal.router()` und haben `Depends(portal.user)`
- [ ] Alle Links und Weiterleitungen laufen über `portal.url(...)`
- [ ] `manifest.json` ist vollständig, die Rollen sind so klein wie möglich
- [ ] `/healthz` und `platform_sdk/` sind unverändert
- [ ] Keine Cookies, keine `SessionMiddleware`
- [ ] `make lint` und `make test` laufen ohne Fehler
