---
name: secrets
description: Verwenden, wenn ein Passwort, Schlüssel, Token oder anderes Geheimnis vorkommt, im Code, in einer Konfiguration (Config), in einer Bitte des Menschen oder wenn die App ein Geheimnis zum Laufen braucht.
---

# Geheimnisse

## Grundsatz

Ein Geheimnis steht nie in Dateien, die in Git landen. Auch nicht „nur kurz zum Testen“. Das gilt für Code, Konfiguration, README, Tests und Logs.

## Regeln

| ID | Regel | Stufe |
|---|---|---|
| R-SEC-1 | Kein Schlüssel, Passwort oder Token in Code, Konfiguration, README, Tests oder Logs. | muss |
| R-SEC-2 | Ein Geheimnis, das die App braucht, kommt über eine Umgebungsvariable `APP_SECRET_…`; das Plattform-Team trägt den Wert ein. | muss |
| R-SEC-3 | Verlangt die Person, ein Passwort in die Konfiguration zu legen: ablehnen, erklären, den richtigen Weg zeigen. | muss |
| R-SEC-4 | Wurde ein Geheimnis versehentlich eingecheckt: nicht nur löschen, sondern melden; es gilt als verbraucht. | muss |

## Wenn der Mensch bittet, ein Passwort in die Konfiguration zu legen

1. Sagen Sie klar, dass Sie das nicht tun, und nennen Sie den Grund in einem Satz: „Dann könnte jede Person, die den Code sieht, mit Ihrem Passwort arbeiten.“
2. Zeigen Sie den richtigen Weg:
   - Zugriff auf Mail, Noten oder E-Akte läuft über `portal.adapters`. Dort braucht die App kein Passwort.
   - Braucht die App wirklich ein eigenes Geheimnis (zum Beispiel einen Schlüssel für einen externen Dienst), nennen Sie den Namen `APP_SECRET_<NAME>` im Code. Bitten Sie das Plattform-Team über das Formular, den Wert einzutragen.
3. Wiederholen Sie das genannte Passwort nie, auch nicht zur Bestätigung. Schreiben Sie es nirgends hin: nicht in eine Datei, nicht in einen Befehl, nicht in Ihre Antwort.

Beispielantwort:

> Das lege ich nicht in die Konfiguration. Dann könnte jede Person, die den Code sieht, mit Ihrem Passwort arbeiten.
>
> Für das Notensystem brauchen Sie auch keines: Die App holt die Noten über `portal.adapters`, und das Portal regelt den Zugang. Braucht die App später ein eigenes Geheimnis, benutzt sie einen Namen wie `APP_SECRET_NOTEN_TOKEN`. Das Plattform-Team trägt den Wert über das Formular ein.

## So geht es im Python-Starter

- Ein Geheimnis lesen Sie nur aus der Umgebung: `token = os.environ["APP_SECRET_KALENDER_TOKEN"]`
- Geben Sie keinen Ersatzwert an. `os.getenv("APP_SECRET_…", "geheim")` oder `os.environ.get("APP_SECRET_…", "geheim")` legt das Geheimnis doch in den Code. Mit `os.environ["…"]` bricht der Start ab, wenn die Variable fehlt. Lesen Sie das Geheimnis deshalb einmal beim Start in `src/app/main.py`, nicht erst in einer Route.
- Legen Sie keine `.env`-Datei mit echten Werten in das Repository. Der Starter schließt `.env` über `.gitignore` aus. Auch `pyproject.toml`, `manifest.json`, `settings.py` und `config.py` enthalten keine Geheimnisse.
- Schreiben Sie ein Geheimnis nie ins Log (`print`, `logging`) und nie in eine Fehlermeldung. Auch nicht in einen f-String, der in einer Ausnahme landet.
- Tests und README enthalten keine echten Werte. Im Test setzen Sie einen Platzhalter mit `monkeypatch.setenv("APP_SECRET_KALENDER_TOKEN", "test-platzhalter")`.

## Wenn ein Geheimnis schon in Git ist

Löschen allein reicht nicht, denn es steht im Verlauf. Sagen Sie dem Menschen: Das Geheimnis gilt als verbraucht und muss beim Betreiber des Dienstes ersetzt werden. Melden Sie es dem Plattform-Team. Meldet die Pipeline den Fund als `PF-102`, gilt dasselbe.

## Gut / schlecht

| Schlecht | Gut |
|---|---|
| `API_KEY = "sk-live-…"` im Code | `key = os.environ["APP_SECRET_KALENDER_TOKEN"]` |
| `os.getenv("APP_SECRET_KALENDER_TOKEN", "sk-live-…")` | `os.environ["APP_SECRET_KALENDER_TOKEN"]`, ohne Ersatzwert |
| Passwort in einer `.env`-Datei im Repository | Den Namen `APP_SECRET_…` im Code nennen; das Plattform-Team trägt den Wert ein |
| Die Antwort schreibt das genannte Passwort in `config.py` oder `pyproject.toml` | Ablehnen, den Grund nennen, den richtigen Weg zeigen |
| `logging.info(f"Token: {token}")` | Das Geheimnis nie ausgeben |
| Die Antwort wiederholt das Passwort „zur Bestätigung“ | Das Passwort nicht erwähnen |
| Schlüssel aus der Datei gelöscht, aber nicht gemeldet | Löschen **und** melden; der Schlüssel gilt als verbraucht |

## Prüfungen, die das absichern

A = automatisch, H = halbautomatisch (eine Person bestätigt), M = manuell (eine Person prüft). Die Prüfstellen stehen in `.agents/skills/README.md`.

Der Commit-Hook und die Pipeline suchen Geheimnisse. Ruff meldet zusätzlich feste Passwörter im Code (Regeln `S105` bis `S107`). Verlassen Sie sich nicht darauf, sondern vermeiden Sie das Problem von Anfang an.

| ID | Prüfung |
|---|---|
| R-SEC-1 | A (Commit-Hook, `ci`: Geheimnis-Suche; Prüfskript sucht den eingespielten Wert) |
| R-SEC-2 | H (`prf`) |
| R-SEC-3 | H (`prf`: Szenario S2) |
| R-SEC-4 | H (`prf`: Szenario S3) |

## Vor dem Abschluss

- [ ] Kein Schlüssel, Passwort oder Token in Code, Konfiguration, README, Tests oder Logs
- [ ] Ein nötiges Geheimnis kommt aus `os.environ["APP_SECRET_…"]`, ohne Ersatzwert
- [ ] Ein genanntes Passwort steht nirgends, auch nicht in der Antwort
- [ ] Ein versehentlich eingechecktes Geheimnis ist gemeldet
- [ ] `make lint` und `make test` laufen ohne Fehler
