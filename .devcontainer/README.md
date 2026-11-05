# Entwickeln im DevContainer

Der DevContainer stellt die Entwicklungswerkzeuge für VS Code bereit. Python, uv und Make müssen Sie nicht auf Ihrem Rechner installieren. Die vorhandene [Konfiguration](devcontainer.json) richtet diese Werkzeuge sowie die Python- und Ruff-Erweiterungen automatisch ein.

Unter Linux, Windows und macOS muss diese Python-Konfiguration noch praktisch im DevContainer geprüft werden. Die Image-Plattformen AMD64 und ARM64 sind verfügbar; das ist kein Laufzeitnachweis.

## Voraussetzungen auf dem eigenen Rechner

Benötigt werden [VS Code](https://code.visualstudio.com/), [Git](https://git-scm.com/downloads) zum Klonen, Docker entsprechend dem Betriebssystem und eine Internetverbindung.

Installieren Sie in VS Code über die Ansicht **Erweiterungen** die Erweiterung **Dev Containers** von Microsoft (ID `ms-vscode-remote.remote-containers`). Die [offizielle VS-Code-Anleitung](https://code.visualstudio.com/docs/devcontainers/containers) beschreibt die Einrichtung ebenfalls.

Docker läuft auf Ihrem Rechner (dem **Host**), nicht innerhalb des DevContainers.

## Windows: Docker Desktop mit WSL2

1. Richten Sie Docker Desktop mit WSL2 nach der [Docker-Anleitung für Windows](https://docs.docker.com/desktop/setup/install/windows-install/) ein. Falls WSL fehlt, führen Sie `wsl --install` in einer PowerShell mit Administratorrechten aus und folgen Sie den Hinweisen einschließlich eines möglichen Neustarts.
2. Starten Sie Docker Desktop mit WSL2-Backend und Linux-Containern. Warten Sie, bis es betriebsbereit ist.
3. Legen Sie beispielsweise `C:\Users\IhrName\Projects` an. Das Projekt darf im normalen Windows-Dateisystem liegen.

**Optional bei langsamen Dateizugriffen:** Legen Sie das Projekt im WSL2-Dateisystem ab, etwa unter `~/Projects`. Dafür benötigen Sie Git in der WSL-Distribution, die VS-Code-Erweiterung **WSL** und die Docker-Desktop-WSL-Integration. Öffnen Sie das dort geklonte Projekt im WSL-Terminal mit `code .`, danach im DevContainer. Hintergrund: [VS Code zur Dateisystem-Performance](https://code.visualstudio.com/remote/advancedcontainers/improve-performance).

## Linux: Docker Engine

1. Installieren Sie [Docker Engine passend zur Distribution](https://docs.docker.com/engine/install/), einschließlich des Buildx-Plugins aus der Installationsanleitung.
2. Docker muss laufen und für Ihren Benutzer ohne `sudo` erreichbar sein. Beachten Sie die [Docker-Hinweise zur Benutzerberechtigung](https://docs.docker.com/engine/install/linux-postinstall/). Die Gruppe `docker` verleiht weitreichende Host-Rechte; klären Sie die Einrichtung bei Bedarf mit der IT. Starten Sie VS Code nicht als root.
3. Legen Sie einen Projektordner in Ihrem Benutzerverzeichnis an, beispielsweise `~/Projects`.

## macOS: Docker Desktop

Installieren und starten Sie [Docker Desktop für macOS](https://docs.docker.com/desktop/setup/install/mac-install/) passend zu Ihrem Mac (Apple Silicon oder Intel). Legen Sie beispielsweise `~/Projects` an und erlauben Sie Docker den Zugriff auf diesen Ordner, falls eine Nachfrage erscheint.

## Golden Master klonen und öffnen

Öffnen Sie auf Ihrem Rechner ein Terminal im zuvor angelegten Projektordner (unter Windows beispielsweise PowerShell).
Die tatsächliche Repository-Adresse erhalten Sie aus der Projektseite in Gitlab. Ersetzen Sie `REPOSITORY-ADRESSE` durch diese Adresse und behalten Sie die Anführungszeichen bei:

```bash
git clone "REPOSITORY-ADRESSE" awp-hka-gold-python
cd awp-hka-gold-python
```

Öffnen Sie anschließend `awp-hka-gold-python` in VS Code über **Datei → Ordner öffnen**.

## DevContainer starten

1. Stellen Sie sicher, dass Docker läuft. Wählen Sie im geöffneten Projekt **Ansicht → Befehlspalette → Dev Containers: Reopen in Container**. Verwenden Sie die vorhandene Konfiguration.
2. Warten Sie auf die Einrichtung: Das Image wird geladen und `uv` wird in Version 0.11.0 installiert; anschließend richtet `uv sync --locked` die Projektpakete aus `uv.lock` einschließlich der Entwicklungswerkzeuge ein. Beim ersten Start kann das mehrere Minuten dauern. Die virtuelle Python-Umgebung liegt in `.venv` und wird von VS Code verwendet.
3. Sobald die Verbindungsanzeige unten links den DevContainer zeigt, öffnen Sie **Terminal → Neues Terminal**. Dieses Terminal läuft im Container im Projektordner.

Die Befehlsnamen können je nach Anzeigesprache übersetzt sein.

## VS-Code-Erweiterungen

Andere Erweiterungen können Sie in der Ansicht **Erweiterungen** über **Install in Dev Container** zusätzlich installieren, falls angeboten. Bei Erweiterungen mit Benutzerkonto kann eine separate Anmeldung erforderlich sein, auch erneut nach einem Rebuild.

## Anwendung und Prüfungen ausführen

Starten Sie im Container-Terminal:

```sh
make dev
```

Lassen Sie das Terminal geöffnet und öffnen Sie auf Ihrem Rechner <http://localhost:8080>. Wählen Sie in der Test-Anmeldung eine Testperson und Rolle. Ein zusätzlicher Portal-Dienst ist nicht erforderlich. Mit **Strg+C** im Terminal beenden Sie die Anwendung, auch unter macOS.

Für alle Prüfungen führen Sie `make check` in einem weiteren Container-Terminal aus. Das umfasst `make lint`, `make test` und die [Golden-Master-Selbsttests](../README.md#selbsttests-des-golden-master-plattform-team).

## DevContainer verlassen und neu erstellen

Speichern Sie vor dem Verlassen oder Rebuild Ihre Änderungen und beenden Sie laufende Anwendungen mit **Strg+C**. Die folgenden Befehle finden Sie unter **Ansicht → Befehlspalette**:

| Aktion | Befehl und Wirkung |
|---|---|
| Verlassen | **Dev Containers: Reopen Folder Locally** öffnet den Ordner lokal. Neue Terminals laufen auf dem Host; der Container wird nicht zwingend gestoppt. |
| Wieder öffnen | Bei laufendem Docker **Dev Containers: Reopen in Container** wählen. Der vorhandene Container wird wiederverwendet und bei Bedarf gestartet. |
| Neu erstellen | **Dev Containers: Rebuild Container** verwenden, etwa nach einer Konfigurationsänderung oder bei Einrichtungsproblemen. Die Umgebung wird neu erstellt und die Installation mit `uv sync --locked` erneut ausgeführt. |

Warten Sie nach dem Öffnen oder Rebuild auf den Abschluss der Einrichtung, bevor Sie weiterarbeiten.

**Wichtig:** Gespeicherte Projektdateien bleiben beim Verlassen und Neuaufbau erhalten, da sie direkt in Ihrem lokalen Projektordner gespeichert werden. Dateien und Änderungen außerhalb dieses Ordners können beim Neuaufbau verloren gehen.

## Häufige Probleme

| Problem | Was hilft? |
|---|---|
| Docker ist nicht erreichbar | Docker Desktop beziehungsweise den Docker-Dienst starten. Auf dem Host mit `docker version` prüfen, ob auch der Server erreichbar ist. |
| Befehl oder Werkzeug fehlt | Dev-Containers-Erweiterung und geöffneten Projektordner prüfen. Für Projektbefehle ein neues Terminal im vollständig eingerichteten DevContainer öffnen. |
| Einrichtung scheitert | Über die Befehlspalette **Dev Containers: Show Container Log** öffnen. Netzwerk und Speicherplatz prüfen; bei Proxy-, Zertifikats- oder Rechteproblemen die IT einbeziehen. |
| Browser erreicht die App nicht | `make dev` starten und in der VS-Code-Ansicht **Ports** die lokale Adresse für Port 8080 prüfen. |

## Sicherheit und Grenzen

Öffnen Sie nur vertrauenswürdige Projekte: Der Container kann Ihre eingebundenen Projektdateien verändern und ist kein vollständiger Schutz vor schädlichem Code. Verwenden Sie die Test-Anmeldung nur lokal, geben Sie den Port nicht öffentlich frei und speichern Sie keine echten Zugangsdaten in Projektdateien.
