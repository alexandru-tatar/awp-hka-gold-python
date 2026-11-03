# Pipeline: Prüfung bei Pull Requests

*Status: Entwurf · Stand 03.11.2026 · Ticket HKA-47 · Verantwortlich: Yaraslau Krautsou*

Beschreibt [`.github/workflows/pruefung.yml`](../.github/workflows/pruefung.yml). Die Datei ist in beiden Golden Mastern gleich und kommt in jede daraus angelegte App. Verwaltete Datei: nicht verändern.

## Wann sie läuft

| Auslöser | Zweig |
|---|---|
| Pull Request | nach `main` oder `develop` |
| Push | auf `develop` |
| von Hand | GitHub, Reiter „Actions“, „Prüfung“, „Run workflow“ |

Die Pipeline prüft nur. Sie spielt nichts auf einen Server ein.

## Was sie prüft

Ein Job mit dem Namen `check`. Er ist nur grün, wenn alles besteht:

1. **Secret-Scan** mit Gitleaks über den ganzen Verlauf des Zweigs.
2. **`make check`** mit `CHECK_DOCKER=1`: Selbsttests der Skills und des Starters (mit Container), `make lint` und `make test`.

Beide Schritte laufen immer zu Ende, auch wenn einer rot ist. So entsteht der Prüfnachweis auch bei einem Fehler.

## Wo das Ergebnis steht

- **Seite des Laufs:** Prüfnachweis und Checkliste Code-Review in der Zusammenfassung.
- **Artefakt `pruefberichte`** (30 Tage): `build/pruefberichte/` mit `pruefnachweis-aktuell.md` und den Prüfberichten. Den Prüfnachweis (Vorlage B) kopieren Sie als Kommentar ins Jira-Ticket, wenn es auf „In Review“ geht. Link zum Lauf und zum Pull Request stehen schon darin.

## Branchschutz

Der Branchschutz auf `main` verlangt den Pflicht-Check **`check`** und die Freigabe durch eine zweite Person. Einrichten kann ihn nur, wer den Account des Repositories besitzt. Das Skript für neue Apps soll ihn setzen (HKA-54).

## Nur in den Golden Mastern

Die Selbsttests vergleichen den Golden Master mit dem anderen Golden Master und mit dem freigegebenen Portal-SDK. Die Pipeline legt dafür `awp-hka-gold-python` bzw. `awp-hka-gold-js` und `portal` neben das Repository. Gibt es dort einen Zweig mit demselben Namen wie Ihr Zweig, wird er genommen. So besteht eine Regel, die Sie in beiden Golden Mastern gleich ändern, den Gleichlauf schon vor dem Merge. In einer App fehlen beide Repositories, die Prüfungen stehen dann als „übersprungen“ im Bericht.

## Wenn die Pipeline rot ist

1. Öffnen Sie den Lauf und den roten Schritt.
2. Führen Sie lokal `make check` aus. Mit `CHECK_DOCKER=1 make check` läuft auch der Container-Test. Das Ergebnis ist dasselbe wie in der Pipeline.
3. Meldet Gitleaks ein Geheimnis: Löschen Sie es nicht nur aus der Datei. Widerrufen Sie es und tauschen Sie es aus (Skill `secrets`, Regel R-SEC-4).
4. Schalten Sie die Prüfung nicht ab und ändern Sie `.github/workflows/` nicht.
