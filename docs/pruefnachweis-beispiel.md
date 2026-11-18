# Prüfnachweis · Golden Master Python · Gesamt

| Feld | Inhalt |
| --- | --- |
| Erzeugt mit | `make check` |
| Zeitpunkt | 18.11.2026, 12:00 Uhr |
| Repository | alexandru-tatar/awp-hka-gold-python · Stand 1a2b3c4 (sauber) |
| Ausgeführt | Pipeline (https://github.com/alexandru-tatar/awp-hka-gold-python/actions/runs/123456789) |
| Gesamtergebnis | **NICHT BESTANDEN** |
| Vorlage | [Vorlage: User Story, Akzeptanzkriterien und Prüfnachweis](https://hka-awp.atlassian.net/wiki/spaces/HKA/pages/19922945) – Vorlage B und Checkliste Code-Review |

## 1. Prüfnachweis (Vorlage B)

Der Reviewer legt den Prüfnachweis an: Er kopiert diesen Block als Kommentar ins Jira-Ticket, prüft jeden Beleg selbst und ersetzt alle [OFFEN]. Den Block nur aus einem Pipeline-Lauf oder aus dem eigenen `make check` nehmen, nicht aus dem Lauf der umsetzenden Person: Ihre Aussagen sind kein Beleg.

```text
Prüfnachweis
Urteil: [OFFEN] (abgenommen / zurück an Umsetzung / nicht prüfbar)
Geprüft von, Datum: [OFFEN]
Stand: alexandru-tatar/awp-hka-gold-python, Commit 1a2b3c4, Pull Request https://github.com/alexandru-tatar/awp-hka-gold-python/pull/12, Lauf https://github.com/alexandru-tatar/awp-hka-gold-python/actions/runs/123456789
AK1: [OFFEN] – Beleg: [Test, Befehl oder Link] – [OFFEN] (selbst ausgeführt / Pipeline / nur gelesen)
AK2: [OFFEN] – Beleg: [Test, Befehl oder Link] – [OFFEN] (selbst ausgeführt / Pipeline / nur gelesen)
Lint: erfüllt – Beleg: make lint, Lauf https://github.com/alexandru-tatar/awp-hka-gold-python/actions/runs/123456789 – Pipeline
Tests: nicht erfüllt – Beleg: make test, make check-skills, make check-starter, Lauf https://github.com/alexandru-tatar/awp-hka-gold-python/actions/runs/123456789 – Pipeline
Muss: [OFFEN] (Befund mit Fundstelle oder „keine“)
Sollte: [OFFEN] (Befund oder „keine“)
Nicht geprüft: [OFFEN] (was und warum, oder „nichts“)
Code-Review-Checkliste durchgegangen: [OFFEN] (ja / nein)
```

## 2. Checkliste Code-Review

`[x]` belegt der automatische Lauf, der Reviewer bestätigt. `[ ]` prüft der Reviewer. ✘ markiert einen Fehler im Lauf.

**Funktion**

- [ ] Jedes Akzeptanzkriterium ist umgesetzt — prüft der Reviewer
- [ ] Prüfweg je Kriterium ausgeführt, auch der Negativfall — prüft der Reviewer
- [ ] Tests grün (lokal oder Pipeline) — ✘ Selbsttest Skills BESTANDEN, Selbsttest Starter BESTANDEN, make test FEHLER

**Qualität**

- [x] Linter fehlerfrei (Ruff / ESLint) — automatisch: make lint bestanden
- [ ] Konventionen und Code-Standards eingehalten — prüft der Reviewer
- [ ] Code verständlich, keine toten oder auskommentierten Teile — prüft der Reviewer
- [ ] Regeln aus AGENTS.md / Golden Master eingehalten — teilweise automatisch: 5 von 5 Einzelregeln bestanden; übrige prüft der Reviewer

**Sicherheit**

- [x] Keine Secrets, Tokens oder Passwörter im Code — automatisch: R-SEC-1, R-SEC-2 bestanden
- [x] Login und Rollen nur über das Portal — automatisch: R-PORT-1, R-PORT-2 bestanden
- [ ] Nur Testdaten und Mocks, kein Zugriff auf Produktivsysteme — prüft der Reviewer

**Doku**

- [ ] README oder Confluence-Seite aktualisiert — prüft der Reviewer
- [ ] Manifest angepasst, wenn relevant — prüft der Reviewer; Schema automatisch geprüft (R-PORT-4 bestanden)
- [x] Commit-Nachrichten beginnen mit der Ticket-ID — automatisch: alle 1 Commits gegenüber origin/main

## 3. Ergebnis der automatischen Läufe

| Lauf | Ergebnis |
| --- | --- |
| `make check-skills` | BESTANDEN · 10 Prüfungen (20 Einzelfälle) · 0 Fehler · 0 übersprungen |
| `make check-starter` | BESTANDEN · 10 Prüfungen (20 Einzelfälle) · 0 Fehler · 0 übersprungen |
| `make lint` | BESTANDEN |
| `make test` | NICHT BESTANDEN |

## 4. Ausgabe von `make test` (letzte Zeilen)

```text
FAILED tests/test_app.py::test_beispiel - assert 1 == 2
```

## 5. Prüfbericht Skills

```text
 Beispiel: Prüfbericht Skills
```

## 6. Prüfbericht Starter

```text
 Beispiel: Prüfbericht Starter
```
