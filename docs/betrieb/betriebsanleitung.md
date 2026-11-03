# Betriebsanleitung

*Status: Entwurf, Gliederung noch nicht im Team abgestimmt · Stand 01.11.2026 · Ticket HKA-22 · Verantwortlich: David Coric*

Für Personen, die die Plattform betreiben, aber nicht täglich damit arbeiten. Hier stehen nur Befehle, die es im Repository gibt. Alles andere ist als TODO markiert. Eine Übersicht aller Befehle steht im [README](../../README.md#befehle).

**Stopp oder Beenden?** Stopp hält die App vorübergehend an, sie kommt wieder. Beenden legt die App dauerhaft still.

**Zurücksetzen** heißt: zurück auf die vorherige Version. Es heißt nicht, dass Daten gelöscht werden.

<!-- TODO: Begriffe Stopp, Beenden und Zurücksetzen im Team abstimmen. -->

## 1. Start

**Zweck:** Die App starten.

**Voraussetzungen:** Das Werkzeug `uv` ist installiert. Python 3.14 holt `uv` selbst. Für den Container zusätzlich Docker.

**Schritte:**

1. App direkt starten: `make start`. Die App lauscht auf Port 8080.
2. Oder im Container starten. Zuerst bauen: `make docker`. Dann starten:

   ```bash
   docker run --rm --read-only --cap-drop=ALL --tmpfs /tmp --publish 8080:8080 hka/portal-app:0.1.0
   ```

3. Prüfen: <http://localhost:8080/healthz> antwortet mit `{"status":"ok"}`.

Ohne das Portal davor antworten die Seiten der App mit 401. Das ist richtig, denn die Anmeldung läuft über das Portal.

`make dev` startet die App mit Test-Anmeldung. Verwenden Sie es nur zum Entwickeln, nie im Betrieb.

<!-- TODO: Start auf der HKA-VM ergänzen. Im Repository gibt es dafür keinen Befehl. Geplant: platform.sh up (Portal-Repository, claude-proposal/10-platform-ops.md §5), deploy.sh deploy (claude-proposal/09-pipeline-and-deploy.md §5.2). -->

## 2. Stopp

**Zweck:** Die App vorübergehend anhalten, ohne etwas zu löschen.

**Voraussetzungen:** Die App läuft.

**Schritte:**

<!-- TODO: Schritte ergänzen. Das Repository enthält keinen Stopp-Befehl. Geplant: platform.sh down (claude-proposal/10-platform-ops.md §5). Dieser Befehl stoppt laut Spezifikation nur das Portal, nicht die Apps. Für eine einzelne App ist kein Stopp-Befehl festgelegt: klären. -->

## 3. Neustart

**Zweck:** Die laufende App neu starten, zum Beispiel nach einer Störung.

**Voraussetzungen:** Die App läuft oder ist abgestürzt.

**Schritte:**

<!-- TODO: Schritte ergänzen. Das Repository enthält keinen Neustart-Befehl. Geplant: platform.sh restart (claude-proposal/10-platform-ops.md §5). Für eine einzelne App ist kein Neustart-Befehl festgelegt: klären. -->

## 4. Fehlerfall

**Zweck:** Herausfinden, was nicht stimmt, und die App wieder in Betrieb bringen.

**Voraussetzungen:** Zugang zu dem Rechner, auf dem die App läuft. Für die Tests zusätzlich der Quellcode.

**Schritte:**

1. Prüfen, ob die App antwortet: <http://localhost:8080/healthz> muss `{"status":"ok"}` liefern.
2. Im Container prüft der `HEALTHCHECK` des Images dasselbe alle 10 Sekunden, nach 3 Fehlversuchen gilt der Container als ungesund. Der Prüfbefehl lautet `python -m platform_sdk.healthcheck`.
3. Automatische Tests ausführen: `make test`.
4. Regeln und Portal-Bibliothek prüfen: `make lint`.
5. Den Starter als Ganzes prüfen (Plattform-Team): `make check`. Der Bericht liegt danach in `build/pruefberichte/`. Mit `CHECK_DOCKER=1 make check-starter` wird zusätzlich der Container gebaut und gestartet.

<!-- TODO: Logs ansehen und typische Störungen ergänzen. Im Repository gibt es dafür keinen Befehl. Geplant: platform.sh status, platform.sh logs, platform.sh check (claude-proposal/10-platform-ops.md §5, Fehlermatrix §12). -->

## 5. Aktualisieren

**Zweck:** Abhängigkeiten, Portal-Bibliothek oder App auf einen neuen Stand bringen.

**Voraussetzungen:** Das Werkzeug `uv` ist installiert. Python 3.14 holt `uv` selbst. Für die Portal-Bibliothek zusätzlich eine freigegebene Kopie aus dem Portal-Repository (dort: `make sdk-release`).

**Schritte:**

Die Befehle und ihre Wirkung stehen im [README, Abschnitt „Wartung“](../../README.md#wartung):

1. Abhängigkeiten: `make lock`.
2. Portal-Bibliothek: `make sdk-update`.
3. Danach prüfen: `make test` und `make lint`.
4. Container neu bauen: `make docker`.

**Achtung:** `make sdk-update` sucht die Kopie unter `../portal/sdk/dist/python/platform_sdk`. Heißt der Ordner des Portal-Repositorys anders, zum Beispiel `awp-hka-intranet-portal`, geben Sie den Pfad mit `SDK_DIST=…` an.

<!-- TODO: Neue App-Version auf der HKA-VM einspielen. Im Repository gibt es dafür keinen Befehl. Geplant: deploy.sh deploy, für die Plattform platform.sh upgrade (claude-proposal/10-platform-ops.md §7). -->

## 6. Zurücksetzen

**Zweck:** Die App auf die vorherige Version zurückbringen, wenn die neue Version Probleme macht.

**Voraussetzungen:** Es gibt eine vorherige Version.

**Schritte:**

<!-- TODO: Schritte ergänzen. Das Repository enthält keinen Befehl dafür. Geplant: deploy.sh rollback --env <stage|prod> --slug <slug> --by <user> (claude-proposal/09-pipeline-and-deploy.md §5.2). -->

## 7. Beenden

**Zweck:** Die App dauerhaft stilllegen.

**Voraussetzungen:** Es ist entschieden, dass die App nicht mehr gebraucht wird. Daten, die erhalten bleiben sollen, sind gesichert (siehe Kapitel 8).

**Schritte:**

<!-- TODO: Schritte ergänzen. Das Repository enthält keinen Befehl dafür. Geplant: deploy.sh retire --env <stage|prod> --slug <slug> --by <user>, optional mit --purge-data --yes. Diese Option löscht die Daten der App (claude-proposal/09-pipeline-and-deploy.md §5.2). -->

## 8. Sichern

**Zweck:** Daten der App sichern und wiederherstellen.

**Voraussetzungen:** Die App speichert Daten. Im Container ist `/data` neben `/tmp` der einzige beschreibbare Ordner (`DATA_DIR=/data`, siehe `Dockerfile`).

**Schritte:**

<!-- TODO: Schritte ergänzen. Das Repository enthält weder ein Volume noch ein Backup. Geplant: platform.sh volume-backup und volume-restore (claude-proposal/10-platform-ops.md §5 und §6). Eine automatische Sicherung der App-Daten ist laut Spezifikation nicht vorgesehen. Auch die Sicherung der VM ist noch zu klären. -->
