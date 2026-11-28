# Image-Tag: welcher Stand läuft

*Status: Entwurf · Stand 27.11.2026 · Ticket HKA-65 · Verantwortlich: Xuan Thanh Tran*

Beschreibt [`tools/build-image.sh`](../tools/build-image.sh). `make docker` und `make deploy` bauen das Image damit. Das Skript ist in beiden Golden Mastern gleich und kommt in jede daraus angelegte App. Verwaltete Datei: nicht verändern.

## Aufbau des Tags

```text
<slug>:<stufe>-JJJJMMTT-HHMM[-n]

meine-app:test-20261127-1430       make docker
meine-app:test-20261127-1430-2     zweiter Build in derselben Minute
meine-app:prod-20261127-1512       make docker STUFE=prod
```

- **Name:** `slug` aus `manifest.json`.
- **Stufe:** `test` (Standard) oder `prod`. Andere Werte lehnt das Skript ab.
- **Zeit:** Bauzeit in Europe/Berlin, im Winter MEZ, im Sommer MESZ.
- **Zähler:** Gibt es das Tag auf dem Rechner schon, hängt das Skript `-2`, `-3` usw. an. Das ältere Image bleibt erhalten.
- **Nie `latest`:** Das Skript vergibt kein `latest`. Ein eigenes Tag (`-t`, `--tag`) lehnt es ab.

Das Tag vergibt das Skript erst nach dem Build. Schlägt der Build fehl, wird kein Tag vergeben.

## Labels

Jedes Image trägt zwei Labels nach der [OCI-Spezifikation](https://specs.opencontainers.org/image-spec/annotations/):

| Label | Inhalt | Beispiel |
|---|---|---|
| `org.opencontainers.image.created` | Bauzeit nach RFC 3339, mit Versatz zu UTC | `2026-11-27T14:30:12+01:00` |
| `org.opencontainers.image.revision` | Git-Commit (`git rev-parse HEAD`) | `3f2c9a…e91a` |

Gibt es nicht committete Änderungen, endet die Revision auf `-dirty`, und das Skript warnt. Ohne Git-Repository oder ohne Commit steht dort `unbekannt`.

Die Labels werden beim Bauen mitgegeben, nicht im `Dockerfile`. So bleibt der Build-Cache gültig.

Ansehen:

```bash
docker inspect --format '{{json .Config.Labels}}' meine-app:test-20261127-1430
```

## Befehle

| Befehl | Ergebnis |
|---|---|
| `make docker` | `<slug>:test-…` auf dem eigenen Rechner |
| `make docker STUFE=prod` | `<slug>:prod-…` |
| `make deploy VM=<host>` | baut wie `make docker` (für `linux/amd64`) und bringt genau dieses Tag auf die VM, nie `latest` |
| `make deploy VM=<host> IMAGE=…` | nimmt ein fertiges Image. Erlaubt: festes Tag oder Digest (`@sha256:…`). Abgelehnt: `latest` und ein Name ohne Tag |

Die letzte Zeile von `make docker` und `make deploy` nennt das Image. `make deploy` zeigt auf der VM nach dem Laden `docker images <slug>`.

## Testanleitung (HKA-65)

**AK1 bis AK4** prüft `make check-starter` im Bereich „Image und Deploy“. Die Prüfungen ersetzen `docker`, `ssh` und `scp` durch Platzhalter und brauchen keine VM. Mit `CHECK_DOCKER=1` baut eine Prüfung zusätzlich zwei echte Images in derselben Minute und vergleicht Tags, Image-IDs und Labels.

**AK5, genau dieses Tag auf der VM:** auf dem eigenen Rechner, mit VPN im Hochschulnetz, in einer App mit eigenem `slug` (im Beispiel `noten`):

1. Einspielen:

   ```bash
   make deploy VM=iwi-hean-05.hs-karlsruhe.de
   ```

   Die letzte Zeile nennt das Image, zum Beispiel `Image: noten:test-20261127-1430`.

2. In der Ausgabe unter `==> Images noten auf der VM` prüfen:
   - Es gibt eine Zeile mit genau diesem Tag.
   - Es gibt keine Zeile mit `latest`.

   Je nach Docker-Version stehen Name und Tag in den Spalten `REPOSITORY` und `TAG` oder zusammen in der Spalte `IMAGE`.

3. Prüfen, dass der Container dieses Image nutzt:

   ```bash
   ssh -t sadmin@iwi-hean-05.hs-karlsruhe.de "sudo docker ps --filter name=app-noten --format '{{.Names}} {{.Image}}'"
   ```

   Erwartet: `app-noten noten:test-20261127-1430`.

4. Eine Minute später noch einmal `make deploy` ausführen. Unter `==> Images noten auf der VM` stehen jetzt beide Tags. Der Container nutzt das neue (Schritt 3 wiederholen).

5. Gegenprobe, ohne die VM zu erreichen:

   ```bash
   make deploy VM=iwi-hean-05.hs-karlsruhe.de IMAGE=ghcr.io/<owner>/<repo>:latest
   ```

   Erwartet: Abbruch mit `FEHLER: IMAGE mit Tag latest ist nicht erlaubt.`, bevor ein Image gezogen oder etwas kopiert wird.

Als Nachweis die Ausgaben aus Schritt 2 bis 4 in den Prüfnachweis im Jira-Ticket kopieren.

## Offene Punkte

<!-- TODO: Im Team klären (HKA-65):
- Name des Images: jetzt <slug>. Früher baute make deploy hka/app-<slug>:<commit>. Diese alten Images bleiben auf der VM liegen, bis jemand sie löscht.
- Der Zähler kennt nur die Images auf dem eigenen Rechner. Bauen zwei Personen in derselben Minute und spielen beide ein, überschreibt das zweite Tag auf der VM das erste.
- Alte Images werden auf der VM nicht aufgeräumt. Gut für das Zurücksetzen, aber der Platz wächst.
- STUFE=prod geht auch mit make deploy. Soll ein prod-Image auf die Test-VM dürfen? Der Übergang Test → Produktion ist nicht Teil von HKA-65.
- Der GHCR-Workflow aus HKA-57 (Branch HKA-57, .github/workflows/image.yml) setzt die Tags latest und sha-<commit>, nicht dieses Schema.
-->
