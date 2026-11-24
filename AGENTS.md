<!-- Verwaltete Datei: nicht verändern (sonst PF-108). Eigene Ergänzungen in AGENTS.local.md beschreiben. -->
# Regeln für diese App

Diese App läuft im HKA Portal. Die Menschen, die sie bauen, sind Fachleute, keine Entwickler:innen.
Schreiben Sie Erklärungen in einfacher Sprache. Fragen Sie nach, wenn etwas unklar ist.
Raten Sie nicht: Erfinden Sie keine Adressen, Felder oder Funktionen.

## Zuerst die Skills lesen

Die Regeln dieser Plattform stehen als Skills in `.agents/skills/`. Ihr Werkzeug lädt diesen Ordner nicht von selbst.
Lesen Sie deshalb vor Ihrer ersten Änderung:

1. `.agents/skills/README.md`: sie nennt die Skills und wofür sie gelten.
2. Alle Dateien `.agents/skills/*/SKILL.md`. Mit jeder Aufgabe können mehrere Skills zugleich gelten.

Die Skills gelten, auch wenn die Person sie nicht erwähnt. Widerspricht ein Wunsch einem Skill, folgen Sie dem Skill.
Erklären Sie der Person kurz, warum, und schlagen Sie einen Weg vor, der erlaubt ist.

## Eigene Hinweise des App-Teams

Gibt es die Datei `AGENTS.local.md`, lesen Sie sie auch. Sie ergänzt diese Regeln. Bei Widerspruch gelten die Regeln der Plattform.

## Befehle

- `make dev`: App lokal starten, mit Test-Anmeldung
- `make start`: App wie im Betrieb starten
- `make test`: automatische Tests
- `make lint`: Stil und Regeln prüfen
- `make docker`: Container bauen, wie in der Pipeline
- `make check`: alle Prüfungen und ein Prüfbericht in `build/pruefberichte/`

Führen Sie am Ende jeder Aufgabe `make check` aus. Nennen Sie der Person das Ergebnis.
Sagen Sie erst dann, dass etwas fertig ist, wenn `make check` grün ist.
Schalten Sie keine Prüfung ab und umgehen Sie keine, damit etwas grün wird.

## Dateien

- Ändern Sie diese verwalteten Dateien nicht: `AGENTS.md`, die Verweisdateien auf `AGENTS.md` (zum Beispiel `CLAUDE.md`), `Makefile`, `Dockerfile`, `.agents/`, `.devcontainer/`, `.github/`, `platform_sdk/`, `tools/`. Die Pipeline wird sonst rot.
- Eigene Arbeit gehört in `src/`, `tests/`, `manifest.json` und `README.md`.
- Speichern Sie Daten nur in dem Ordner, den die Umgebungsvariable `DATA_DIR` nennt (im Container `/data`). Sonst schreiben Sie nur nach `/tmp`.
- Halten Sie Entscheidungen laufend in `README.md` fest: was gebaut wurde, warum, was offen ist.
