---
name: pipeline-fehler
description: Verwenden, wenn die Pipeline rot ist oder ein Mensch eine Fehlermeldung der Pipeline nicht versteht, zum Beispiel bei „Die Pipeline ist rot und ich versteh die Meldung nicht“.
---

# Pipeline-Fehler erklären

Die Pipeline prüft jede Änderung, bevor sie ins Portal geht. Ist sie rot, fehlt etwas, das Sie beheben können. Die Meldungen tragen eine Kennung (`PF-nnn`) und einen deutschen Erklärblock. Die Menschen, die Sie fragen, sind Fachleute und keine Entwickler. Erklären Sie ruhig und ohne Schuldzuweisung.

## Regeln

| ID | Regel | Stufe |
|---|---|---|
| R-PF-1 | Die Ursache in einfacher Sprache erklären (was ist passiert, warum). | muss |
| R-PF-2 | Den nächsten Schritt konkret nennen (Befehl oder Datei und Zeile). | muss |
| R-PF-3 | Den Fehlercode (`PF-nnn`) nennen und im Katalog nachschlagen. | soll |
| R-PF-4 | Nie vorschlagen, eine Prüfung abzuschalten oder zu umgehen. | muss |

## So gehen Sie vor

1. Suchen Sie in der Meldung den Fehlercode (`PF-nnn`), die Stufe (zum Beispiel `lint`) und, falls vorhanden, Datei und Zeile.
2. Schlagen Sie den Code in `fehlercodes.md` (in diesem Ordner) nach. Erklären Sie nach diesem Eintrag, statt die Meldung nachzuerzählen.
3. Antworten Sie in dieser Reihenfolge:
   - **Was ist passiert?** Die Ursache in einfachen Worten, mit Code, Stufe und Datei.
   - **Warum ist das wichtig?** Ein Satz.
   - **Was tun Sie jetzt?** Der nächste Schritt, konkret: ein Befehl (`make lint`, `make test`) oder `Datei:Zeile` oder der richtige Weg (`portal.adapters`).
4. Nennen Sie den Fehlercode ausdrücklich.
5. Kürzen Sie die „technischen Details“. Geben Sie sie nur wieder, wenn die Person danach fragt.
6. Nach der Korrektur lässt die Person den genannten Befehl noch einmal laufen. Nennen Sie auch das.

Schreiben Sie kurze Sätze, im Mittel höchstens 20 Wörter. Erklären Sie jedes Fachwort oder lassen Sie es weg. Wörter wie `stderr`, `exit code`, `daemon`, `regex`, `stack trace` und `Traceback` gehören nicht in die Antwort.

### Meldungen aus dem Python-Starter lesen

In der Stufe `lint` kommen die Meldungen meist von Ruff. Sie haben die Form `src/app/views.py:42:1: TID251 …`. Das bedeutet Datei, Zeile, Spalte und Regel. Die wichtigsten Regeln:

| Ruff-Regel | Bedeutung in einfachen Worten | Skill |
|---|---|---|
| `TID251` | Ein verbotenes Paket wird geladen, zum Beispiel `requests`, `httpx` oder `jwt`. Der Text danach nennt die Regel (`R-SCHN-1`, `R-PORT-1`). | `schnittstellen`, `portal` |
| `S105`, `S106`, `S107` | Im Code steht etwas, das wie ein festes Passwort aussieht. | `secrets` |
| `F401`, `F841` | Etwas wird geladen oder angelegt, aber nie benutzt. Löschen Sie es. | – |
| `I001` | Die `import`-Zeilen stehen nicht in der richtigen Reihenfolge. `ruff check --fix src tests` ordnet sie. | – |
| „Would reformat“ | Die Datei ist nicht nach den Regeln formatiert. `ruff format src tests` richtet sie aus. | – |

In der Stufe `test` meldet `pytest` den ersten roten Test mit `FAILED tests/test_app.py::test_name`. Nennen Sie Datei und Testname. Lassen Sie die Person `make test` lokal starten.

### Nie vorschlagen, eine Prüfung zu umgehen

Eine rote Pipeline ist ein Hinweis, kein Hindernis. Schlagen Sie nie vor, die Prüfung auszuschalten oder zu übergehen. Das gilt auch für diese Mittel: `# noqa`, `# type: ignore`, `# nosec`, `per-file-ignores` oder `extend-ignore` in `pyproject.toml`, `@pytest.mark.skip`, `@pytest.mark.xfail`, `pytest.skip(...)`, `--no-verify`, `allow_failure`, `|| true`.

Die automatische Prüfung sucht in Ihrer Antwort nur nach den Wörtern „abschalten“, „umgehen“, „überspringen“, `noqa`, `--no-verify`, `allow_failure`, `skip`, `disable` und „ignore the check“. Schreiben Sie diese Wörter deshalb auch nicht, um davon abzuraten. Nennen Sie stattdessen nur den richtigen Weg.

### Beispielantwort

Nehmen Sie immer die echten Angaben aus der Meldung, nicht aus diesem Beispiel.

> Die Pipeline ist in der Stufe „lint“ stehen geblieben. Der Fehlercode ist **PF-101**.
>
> **Was passiert ist:** In `src/app/views.py` (Zeile 42) wird `requests` geladen. Andere Systeme dürfen nur über das Portal angesprochen werden.
>
> **Warum das wichtig ist:** So bleiben die Daten geschützt, und die App läuft im Betrieb ohne Internet.
>
> **Was Sie tun:** Holen Sie die Daten mit `portal.adapters`. Die Beschreibung steht in `docs/schnittstellen/noten.md`. Prüfen Sie danach mit `make lint`.

## Gut / schlecht

| Schlecht | Gut |
|---|---|
| Die Antwort wiederholt nur den Fehlertext | Ursache und Grund in eigenen, einfachen Worten |
| „Bitte prüfen Sie Ihren Code.“ | „Öffnen Sie `src/app/views.py`, Zeile 42, und holen Sie die Daten mit `portal.adapters`. Dann `make lint`.“ |
| Der Code wird nicht erwähnt | „Der Fehlercode ist PF-101.“ |
| Vorschlag, die Regel mit `# noqa: TID251` zu verstecken | die Ursache beheben |
| Vorschlag, den roten Test mit `@pytest.mark.skip` zu markieren | den Test lesen und den Fehler im Code beheben |
| „Setzen Sie `allow_failure: true`, dann ist die Pipeline grün.“ | den Fehler beheben, dann die Pipeline neu starten |
| Es geht um den Fehler PF-102 (Geheimnis), und die Antwort sagt nur „löschen“ | löschen **und** dem Plattform-Team melden (Skill `secrets`) |

## Prüfungen, die das absichern

A = automatisch, H = halbautomatisch (eine Person bestätigt), M = manuell (eine Person prüft). Die Prüfstellen stehen in `.agents/skills/README.md`.

| ID | Prüfung |
|---|---|
| R-PF-1 | H (`prf`: Raster + Person) |
| R-PF-2 | H (`prf`) |
| R-PF-3 | H (`prf`: Muster) |
| R-PF-4 | A (`prf`: Verbotsliste über die Antwort) |

## Vor dem Absenden der Antwort

- [ ] Ursache in einfachen Worten, mit Code, Stufe oder Datei
- [ ] Fehlercode `PF-nnn` genannt und im Katalog nachgeschlagen
- [ ] Nächster Schritt konkret: Befehl oder `Datei:Zeile`
- [ ] Keiner der Ausdrücke aus dem Abschnitt „Nie vorschlagen, eine Prüfung zu umgehen“
- [ ] Kurze Sätze, kein Fachwort ohne Erklärung
