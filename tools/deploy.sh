#!/usr/bin/env bash
# App von Hand auf die Test-VM bringen (HKA-50, AK8) oder in den lokalen Stack. Verwaltete Datei: in beiden Golden Mastern gleich.
#
# Aufruf:  make deploy VM=iwi-hean-05.hs-karlsruhe.de
#          make deploy VM=… IMAGE=ghcr.io/<owner>/<repo>@sha256:…    # fertiges Image aus GHCR statt lokal bauen (HKA-57)
#          make deploy-local                                         # lokaler Stack (im Gateway-Repository: make server-up)
#
# Ablauf:
#   VM (Standard, ZIEL=vm):
#     Rechner:  Image bereitstellen (lokal bauen oder aus GHCR ziehen) --> docker save | gzip --> scp (Images + manifest.json)
#     VM:       docker load --> Container app-<slug> neu starten --> warten auf "healthy" --> portal-deploy check --> register
#   Lokal (ZIEL=lokal):
#     Image bereitstellen --> Container app-<slug> neu starten --> warten auf "healthy" --> Manifest prüfen --> registrieren.
#     Prüfen und Registrieren laufen wie in portal-deploy auf der VM: Portal-Image ohne Netz, schreibgeschützt, ohne
#     Capabilities. Image, Konfiguration und Ordner (Manifeste, Registry) liest das Skript aus dem laufenden Portal-Container;
#     geschrieben wird nur im Container (UID des Portals), nie als eigener Benutzer.
#
# Ein Container (Standard) oder mehrere (optional): Liegt compose.yml im Repository, startet das Skript alle Services daraus.
# Pflicht ist dann ein Service "app" (die App selbst). Nur "app" kommt ins Netz des Portals; weitere Services (z. B. eine
# Datenbank) sind nur im eigenen Netz der App erreichbar. Härtung und Portal-Einstellungen für "app" setzt das Skript selbst.
# Vor dem Start prüft es compose.yml: keine Ports, kein privileged/network_mode/pid/ipc/cap_add/devices, keine Bind-Mounts,
# weitere Services nur mit fertigem Image (kein build) und ohne eigene Netze.
#
# Voraussetzungen: Docker mit compose und buildx (BuildKit, das Dockerfile nutzt RUN --mount; Ubuntu: Paket docker-buildx).
# Für die VM: ssh/scp mit Zugang als VM_USER (VPN im Hochschulnetz), auf der VM sudo und portal-deploy (HKA-53). Lokal:
# laufender Stack (im Gateway-Repository: make server-init, make server-up).
# Für die Prüfung von compose.yml: python3 oder ein Python-Image über Docker.
# Bei einem Fehler bricht das Skript ab und sagt, in welchem Schritt. Ein abgelehntes Manifest ändert nichts am Menü.
#
# Umgebungsvariablen:
#   ZIEL          vm oder lokal                                        (Standard: vm)
#   VM            Rechnername der VM                                   (Pflicht bei ZIEL=vm)
#   VM_USER       Benutzer auf der VM                                  (Standard: sadmin)
#   IMAGE         leer: lokal bauen; sonst dieses Image ziehen         (Standard: leer)
#   PORTAL_NETZ   Docker-Netz der Apps                                 (Standard: hka-portal-apps, HKA-60)
#   PORTAL_API    Gateway im Docker-Netz (JWKS, Menü /nav)             (Standard: http://gateway:8080)
#   PORTAL_ADAPTERS Adapter im Docker-Netz (z. B. bwSync)              (Standard: http://adapter:8080)
#   PORTAL_ISSUER Aussteller der Tokens, mit Schrägstrich am Ende      (Standard: vm https://$VM/, lokal http://localhost:18080/)
#   PORTAL_STACK  Compose-Projekt des lokalen Stacks                   (Standard: hka-local, nur ZIEL=lokal)
#   OWNER_REPO    Besitzer der App (owner/repo)                        (Standard: aus git remote origin)
#
# Das Skript liest und schreibt keine Zugangsdaten.

set -euo pipefail

LETZTER="Vorbereitung"
schritt() { LETZTER="$*"; echo "==> $*"; }
fehler() { echo "FEHLER: $*" >&2; exit 1; }
abbruch() { local rc=$?; if [ "$rc" -ne 0 ]; then echo "Abbruch im Schritt: $LETZTER" >&2; fi; }
trap abbruch EXIT

ZIEL="${ZIEL:-vm}"
IMAGE="${IMAGE:-}"
PORTAL_NETZ="${PORTAL_NETZ:-hka-portal-apps}"
PORTAL_API="${PORTAL_API:-http://gateway:8080}"
PORTAL_ADAPTERS="${PORTAL_ADAPTERS:-http://adapter:8080}"
case "$ZIEL" in
  vm)
    : "${VM:?VM fehlt. Aufruf: make deploy VM=iwi-hean-05.hs-karlsruhe.de}"
    VM_USER="${VM_USER:-sadmin}"
    PORTAL_ISSUER="${PORTAL_ISSUER:-https://$VM/}"
    SUDO="sudo "
    PLATTFORM=(--platform linux/amd64)   # die VM ist amd64
    ;;
  lokal)
    PORTAL_ISSUER="${PORTAL_ISSUER:-http://localhost:18080/}"
    PORTAL_STACK="${PORTAL_STACK:-hka-local}"
    SUDO=""
    PLATTFORM=()                         # eigene Plattform, keine Emulation
    ;;
  *) fehler "ZIEL muss vm oder lokal sein, nicht: $ZIEL" ;;
esac

cd "$(dirname "$0")/.."

# ── Angaben aus Repository und Manifest ──────────────────────────────────────

schritt "Angaben lesen"
SLUG=$(sed -nE 's/^[[:space:]]*"slug"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' manifest.json | head -n 1)
[[ "$SLUG" =~ ^[a-z][a-z0-9-]{2,30}$ ]] || fehler "kein gültiger slug in manifest.json"
[ "$SLUG" != "meine-app" ] || fehler "slug ist noch meine-app. Erst in manifest.json einen eigenen Kurznamen eintragen."

if [ -z "${OWNER_REPO:-}" ]; then
  URL=$(git remote get-url origin 2>/dev/null) || fehler "kein git remote origin. OWNER_REPO=owner/repo angeben."
  OWNER_REPO=$(sed -E 's#^(https://[^/]+/|git@[^:]+:)##; s#\.git$##' <<<"$URL")
fi
[[ "$OWNER_REPO" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9._-]+$ ]] || fehler "ungültiger Besitzer: $OWNER_REPO"

# Werte landen in der erzeugten Compose-Datei und im Befehl auf der VM: nur einfache Zeichen.
EINFACH='^[A-Za-z0-9._:/@-]+$'
for wert in "$PORTAL_NETZ" "$PORTAL_API" "$PORTAL_ADAPTERS" "$PORTAL_ISSUER"; do
  [[ "$wert" =~ $EINFACH ]] || fehler "ungültiger Wert: $wert"
done

NAME="app-$SLUG"
MODUS="ein Container"
[ -f compose.yml ] && MODUS="compose.yml"
if [ "$ZIEL" = vm ]; then
  ZIEL_HOST="$VM_USER@$VM"
  echo "    App $SLUG, Besitzer $OWNER_REPO, Ziel $ZIEL_HOST, Modus: $MODUS"
else
  echo "    App $SLUG, Besitzer $OWNER_REPO, Ziel lokaler Stack $PORTAL_STACK, Modus: $MODUS"
fi

# ── Lokal: laufendes Portal finden ───────────────────────────────────────────
# Image, Konfiguration und Ordner kommen aus dem Portal-Container: kein Pfad in ein anderes Repository.

if [ "$ZIEL" = lokal ]; then
  schritt "Lokalen Stack finden ($PORTAL_STACK)"
  BACKEND=$(docker ps -q --filter "label=com.docker.compose.project=$PORTAL_STACK" \
                         --filter "label=com.docker.compose.service=backend")
  [ -n "$BACKEND" ] || fehler "Portal läuft nicht. Im Gateway-Repository: make server-up"
  [ "$(wc -l <<<"$BACKEND")" -eq 1 ] || fehler "mehr als ein Portal-Container im Projekt $PORTAL_STACK"
  docker network inspect "$PORTAL_NETZ" >/dev/null 2>&1 || fehler "Docker-Netz $PORTAL_NETZ fehlt. Im Gateway-Repository: make server-up"
  quelle() { docker inspect -f "{{range .Mounts}}{{if eq .Destination \"$1\"}}{{.Source}}{{end}}{{end}}" "$BACKEND"; }
  PORTAL_IMAGE=$(docker inspect -f '{{.Config.Image}}' "$BACKEND")
  PORTAL_CONFIG_IN_IMAGE=$(docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$BACKEND" | sed -n 's/^PORTAL_CONFIG=//p')
  MANIFESTS_DIR=$(quelle /var/lib/portal/manifests)
  REGISTRY_DIR=$(quelle /var/lib/portal/registry)
  [ -n "$MANIFESTS_DIR" ] && [ -n "$REGISTRY_DIR" ] && [ -n "$PORTAL_CONFIG_IN_IMAGE" ] \
    || fehler "Portal-Container ohne Ordner für Manifeste/Registry oder ohne PORTAL_CONFIG"
  echo "    Portal $PORTAL_IMAGE, Konfiguration $PORTAL_CONFIG_IN_IMAGE"
fi

# ── Image bereitstellen ──────────────────────────────────────────────────────
# Einziger Schritt, der von der Herkunft abhängt. Mit HKA-57 setzt man nur IMAGE; alles danach bleibt gleich.

if [ -z "$IMAGE" ]; then
  IMAGE="hka/$NAME:$(git rev-parse --short HEAD)"
  schritt "Image lokal bauen: $IMAGE${PLATTFORM[*]+ (${PLATTFORM[*]})}"
  docker buildx version >/dev/null 2>&1 \
    || fehler "docker buildx fehlt (BuildKit, das Dockerfile braucht es). Ubuntu/Debian: sudo apt install docker-buildx; Docker Desktop hat es schon."
  [ -z "$(git status --porcelain)" ] || echo "WARNUNG: nicht committete Änderungen, sie kommen mit ins Image." >&2
  docker build ${PLATTFORM[@]+"${PLATTFORM[@]}"} --tag "$IMAGE" .
else
  [[ "$IMAGE" =~ $EINFACH ]] || fehler "ungültiger Image-Name: $IMAGE"
  schritt "Image ziehen: $IMAGE${PLATTFORM[*]+ (${PLATTFORM[*]})}"
  docker pull ${PLATTFORM[@]+"${PLATTFORM[@]}"} "$IMAGE"
fi

mkdir -p build/deploy
BILDER=("$IMAGE")

# ── Optional: compose.yml prüfen und ergänzen ────────────────────────────────

ERGAENZUNG="build/deploy/compose.deploy.yml"
if [ "$MODUS" = compose.yml ]; then
  schritt "compose.yml ergänzen und prüfen"
  cat >"$ERGAENZUNG" <<EOF
# Erzeugt von tools/deploy.sh: Einstellungen für den Service "app" ($ZIEL). Nicht von Hand bearbeiten.
name: $NAME
services:
  app:
    image: "$IMAGE"
    container_name: $NAME
    pull_policy: never
    restart: unless-stopped
    read_only: true
    tmpfs: [/tmp]
    cap_drop: [ALL]
    security_opt: ["no-new-privileges:true"]
    mem_limit: 512m
    pids_limit: 256
    volumes: ["app-data:/data"]
    environment:
      PORTAL_ENV: production
      PORTAL_SLUG: $SLUG
      PORTAL_BASE_PATH: /apps/$SLUG
      PORTAL_API_URL: "$PORTAL_API"
      PORTAL_ADAPTERS_URL: "$PORTAL_ADAPTERS"
      PORTAL_ISSUER: "$PORTAL_ISSUER"
    networks: [default, portal]
networks:
  portal:
    external: true
    name: "$PORTAL_NETZ"
volumes:
  app-data:
    name: $NAME-data
EOF
  KONFIG=$(docker compose -f compose.yml -f "$ERGAENZUNG" config --format json) || fehler "compose.yml ist ungültig"

  PRUEFUNG=$(cat <<'PY'
import json, sys
cfg = json.load(sys.stdin)
services = cfg.get("services", {})
fehler = []
if "app" not in services:
    fehler.append('Service "app" fehlt')
verboten = ["ports", "privileged", "network_mode", "pid", "ipc", "cap_add", "devices", "userns_mode"]
for name, s in services.items():
    for key in verboten:
        if s.get(key):
            fehler.append(f"{name}: {key} ist nicht erlaubt")
    for v in s.get("volumes", []):
        if v.get("type") != "volume" and not (v.get("type") == "tmpfs"):
            fehler.append(f"{name}: nur benannte Volumes, kein {v.get('type')} ({v.get('source', '')})")
    netze = set(s.get("networks", {}) or {"default": None})
    for n, c in (s.get("networks") or {}).items():
        if c and (c.get("aliases") or c.get("ipv4_address") or c.get("ipv6_address")):
            fehler.append(f"{name}: aliases und feste Adressen im Netz {n} sind nicht erlaubt")
    if name == "app":
        if netze - {"default", "portal"}:
            fehler.append(f"app: nur die Netze default und portal, nicht {sorted(netze - {'default', 'portal'})}")
        continue
    if s.get("build"):
        fehler.append(f"{name}: build ist nur für app erlaubt, sonst ein fertiges Image")
    if s.get("container_name"):
        fehler.append(f"{name}: container_name ist nicht erlaubt")
    if netze - {"default"}:
        fehler.append(f"{name}: nur das Netz default, nicht {sorted(netze - {'default'})}")
for n, net in cfg.get("networks", {}).items():
    if net.get("external") and n != "portal":
        fehler.append(f"Netz {n}: externe Netze sind nicht erlaubt")
if fehler:
    print("\n".join(fehler), file=sys.stderr)
    sys.exit(1)
for name, s in services.items():
    if name != "app":
        print(s["image"])
PY
)
  if command -v python3 >/dev/null 2>&1 && python3 -c "" 2>/dev/null; then
    WEITERE=$(python3 -c "$PRUEFUNG" <<<"$KONFIG") || fehler "compose.yml erfüllt die Regeln nicht (siehe oben)"
  else
    WEITERE=$(docker run --rm -i python:3-alpine python -c "$PRUEFUNG" <<<"$KONFIG") || fehler "compose.yml erfüllt die Regeln nicht (siehe oben)"
  fi
  for bild in $WEITERE; do
    [[ "$bild" =~ $EINFACH ]] || fehler "ungültiger Image-Name in compose.yml: $bild"
    schritt "Image ziehen: $bild${PLATTFORM[*]+ (${PLATTFORM[*]})}"
    docker pull ${PLATTFORM[@]+"${PLATTFORM[@]}"} "$bild"
    BILDER+=("$bild")
  done
fi

# ── Starten und warten (VM und lokal gleich) ─────────────────────────────────
# Läuft als eigenes bash-Skript: auf der VM über ssh, lokal direkt. ${SUDO} ist auf der VM "sudo ", lokal leer.

if [ "$MODUS" = compose.yml ]; then
  if [ "$ZIEL" = vm ]; then
    COMPOSE="sudo docker compose -p $NAME -f ~/deploy/$NAME/compose.yml -f ~/deploy/$NAME/compose.deploy.yml"
  else
    COMPOSE="docker compose -p $NAME -f compose.yml -f $ERGAENZUNG"
  fi
  STARTEN="$COMPOSE up -d --no-build --remove-orphans"
else
  STARTEN=$(cat <<EOF
${SUDO}docker compose -p $NAME down --remove-orphans >/dev/null 2>&1 || true
${SUDO}docker run -d --name $NAME --network $PORTAL_NETZ --restart unless-stopped \\
  --read-only --tmpfs /tmp --cap-drop ALL --security-opt no-new-privileges \\
  --memory 512m --pids-limit 256 \\
  -v $NAME-data:/data \\
  -e PORTAL_ENV=production -e PORTAL_SLUG=$SLUG -e PORTAL_BASE_PATH=/apps/$SLUG \\
  -e PORTAL_API_URL=$PORTAL_API -e PORTAL_ADAPTERS_URL=$PORTAL_ADAPTERS -e PORTAL_ISSUER=$PORTAL_ISSUER \\
  $IMAGE >/dev/null
EOF
)
fi

STARTEN_UND_WARTEN=$(cat <<EOF
echo "==> $NAME neu starten ($MODUS)"
${SUDO}docker rm -f $NAME >/dev/null 2>&1 || true
$STARTEN
echo "==> warten auf healthy"
for _ in \$(seq 1 30); do
  status=\$(${SUDO}docker inspect -f '{{.State.Health.Status}}' $NAME)
  [ "\$status" = healthy ] && break
  [ "\$status" = unhealthy ] && break
  sleep 2
done
if [ "\$status" != healthy ]; then
  echo "FEHLER: $NAME ist nicht healthy (\$status). Letzte Zeilen aus dem Log:" >&2
  ${SUDO}docker logs --tail 30 $NAME >&2
  exit 1
fi
EOF
)

# ── Lokal: starten und registrieren ──────────────────────────────────────────

if [ "$ZIEL" = lokal ]; then
  # Wie portal-deploy auf der VM: Portal-Image ohne Netz, schreibgeschützt, ohne Capabilities; Ordner nur bei register
  # beschreibbar. Läuft als Benutzer des Portal-Images, dem die Ordner gehören.
  portal_registry() {  # $1 = check | register; Manifest auf der Standardeingabe
    local rw=ro
    if [ "$1" = register ]; then rw=rw; fi
    docker run --rm -i \
      --network none --read-only --tmpfs /tmp \
      --cap-drop ALL --security-opt no-new-privileges \
      --memory 256m --pids-limit 64 \
      -v "$MANIFESTS_DIR:/var/lib/portal/manifests:$rw" \
      -v "$REGISTRY_DIR:/var/lib/portal/registry:$rw" \
      --entrypoint python \
      "$PORTAL_IMAGE" \
      -m portal.registry "$1" --config "$PORTAL_CONFIG_IN_IMAGE" --owner "$OWNER_REPO" <manifest.json
  }

  schritt "Lokal starten"
  bash -c "set -euo pipefail
$STARTEN_UND_WARTEN"
  schritt "Manifest prüfen"
  portal_registry check
  schritt "Manifest registrieren"
  portal_registry register

  LETZTER="fertig"
  echo ""
  echo "Fertig. In etwa 10 s im Menü: http://localhost:18080/  (App: http://localhost:18080/apps/$SLUG/)"
  exit 0
fi

# ── VM: übertragen ───────────────────────────────────────────────────────────

PAKET="build/deploy/$NAME.tar.gz"
schritt "Images packen: $PAKET"
docker save "${BILDER[@]}" | gzip >"$PAKET"

schritt "Auf die VM kopieren"
# shellcheck disable=SC2029  # $NAME soll auf dem Rechner eingesetzt werden
ssh "$ZIEL_HOST" "install -d -m 0700 ~/deploy ~/deploy/$NAME ~/manifests"
scp "$PAKET" "$ZIEL_HOST:~/deploy/$NAME.tar.gz"
scp manifest.json "$ZIEL_HOST:~/manifests/$SLUG.json"
if [ "$MODUS" = compose.yml ]; then
  scp compose.yml "$ERGAENZUNG" "$ZIEL_HOST:~/deploy/$NAME/"
fi

# ── VM: einspielen und registrieren ──────────────────────────────────────────
# Ein ssh-Aufruf mit Terminal (-t), damit sudo einmal nach dem Passwort fragen kann.

q() { printf '%q' "$1"; }
REMOTE=$(cat <<EOF
set -euo pipefail
echo "==> docker load"
gunzip -c ~/deploy/$NAME.tar.gz | sudo docker load
sudo docker network inspect $PORTAL_NETZ >/dev/null 2>&1 || { echo "FEHLER: Docker-Netz $PORTAL_NETZ fehlt. Läuft das Portal?" >&2; exit 1; }
$STARTEN_UND_WARTEN
echo "==> portal-deploy check"
sudo portal-deploy check --owner $OWNER_REPO < ~/manifests/$SLUG.json
echo "==> portal-deploy register"
sudo portal-deploy register --owner $OWNER_REPO < ~/manifests/$SLUG.json
rm -f ~/deploy/$NAME.tar.gz
EOF
)

schritt "Auf der VM einspielen und registrieren"
ssh -t "$ZIEL_HOST" "bash -c $(q "$REMOTE")"

LETZTER="fertig"
echo ""
echo "Fertig. In etwa 10 s im Menü: https://$VM/  (App: https://$VM/apps/$SLUG/)"
