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
