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
# Image-Tag (HKA-65): Lokal gebaut wird wie bei make docker mit tools/build-image.sh, z. B. <slug>:test-20261125-1430,
# Bauzeit und Git-Commit stehen als Labels im Image. Genau dieses Tag kommt auf die VM, nie latest. Ein IMAGE aus GHCR
# braucht deshalb ein festes Tag oder einen Digest.
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
#   IMAGE         leer: lokal bauen; sonst ziehen (nicht latest)       (Standard: leer)
#   STUFE         test oder prod, Anfang des Image-Tags                (Standard: test, nur beim lokalen Bauen)
#   PORTAL_NETZ   Docker-Netz der Apps                                 (Standard: hka-portal-apps, HKA-60)
#   PORTAL_API    Gateway im Docker-Netz (JWKS, Menü /nav)             (Standard: http://gateway:8080)
#   PORTAL_ADAPTERS Adapter im Docker-Netz (z. B. bwSync)              (Standard: http://adapter:8080)
#   PORTAL_ISSUER Aussteller der Tokens, mit Schrägstrich am Ende      (Standard: vm https://$VM/, lokal http://localhost:18080/)
#   PORTAL_STACK  Compose-Projekt des lokalen Stacks                   (Standard: hka-local, nur ZIEL=lokal)
#   OWNER_REPO    Besitzer der App (owner/repo)                        (Standard: aus git remote origin)
#   PORTAL_LANG   Sprache der Meldungen: de oder en                    (Standard: nach LC_ALL, LC_MESSAGES, LANG, sonst de; HKA-101)
#                 Lokal gilt sie auch für die Prüfung des Manifests. Auf der VM sagt /etc/portal/deploy.env, was portal-deploy spricht.
#
# Das Skript liest und schreibt keine Zugangsdaten.

set -euo pipefail

# Sprache der Meldungen (HKA-101): PORTAL_LANG=de|en, sonst die erste gesetzte Variable aus LC_ALL, LC_MESSAGES, LANG
# ("en…" = Englisch), sonst Deutsch. t "deutscher Text" "English text" gibt den Text der Sprache aus.
sprache() {
  local wert=${PORTAL_LANG:-}
  case "$wert" in en|EN) echo en; return ;; de|DE) echo de; return ;; esac
  for wert in "${LC_ALL:-}" "${LC_MESSAGES:-}" "${LANG:-}"; do
    if [ -n "$wert" ]; then
      case "$wert" in en|en_*|en.*) echo en ;; *) echo de ;; esac
      return
    fi
  done
  echo de
}
SPRACHE=$(sprache)
t() { if [ "$SPRACHE" = en ]; then printf '%s' "$2"; else printf '%s' "$1"; fi; }

LETZTER=$(t "Vorbereitung" "Preparation")
schritt() { LETZTER="$*"; echo "==> $*"; }
fehler() { echo "$(t FEHLER ERROR): $*" >&2; exit 1; }
abbruch() { local rc=$?; if [ "$rc" -ne 0 ]; then echo "$(t "Abbruch im Schritt" "Stopped in step"): $LETZTER" >&2; fi; }
trap abbruch EXIT

ZIEL="${ZIEL:-vm}"
IMAGE="${IMAGE:-}"
PORTAL_NETZ="${PORTAL_NETZ:-hka-portal-apps}"
PORTAL_API="${PORTAL_API:-http://gateway:8080}"
PORTAL_ADAPTERS="${PORTAL_ADAPTERS:-http://adapter:8080}"
case "$ZIEL" in
  vm)
    : "${VM:?$(t "VM fehlt. Aufruf: make deploy VM=iwi-hean-05.hs-karlsruhe.de" "VM is missing. Call: make deploy VM=iwi-hean-05.hs-karlsruhe.de")}"
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
  *) fehler "$(t "ZIEL muss vm oder lokal sein, nicht: $ZIEL" "ZIEL must be vm or lokal, not: $ZIEL")" ;;
esac

cd "$(dirname "$0")/.."

# ── Angaben aus Repository und Manifest ──────────────────────────────────────

schritt "$(t "Angaben lesen" "Read details")"
SLUG=$(sed -nE 's/^[[:space:]]*"slug"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' manifest.json | head -n 1)
[[ "$SLUG" =~ ^[a-z][a-z0-9-]{2,30}$ ]] || fehler "$(t "kein gültiger slug in manifest.json" "no valid slug in manifest.json")"
[ "$SLUG" != "meine-app" ] || fehler "$(t "slug ist noch meine-app. Erst in manifest.json einen eigenen Kurznamen eintragen." "slug is still meine-app. First enter your own short name in manifest.json.")"

if [ -z "${OWNER_REPO:-}" ]; then
  URL=$(git remote get-url origin 2>/dev/null) || fehler "$(t "kein git remote origin. OWNER_REPO=owner/repo angeben." "no git remote origin. Set OWNER_REPO=owner/repo.")"
  OWNER_REPO=$(sed -E 's#^(https://[^/]+/|git@[^:]+:)##; s#\.git$##' <<<"$URL")
fi
[[ "$OWNER_REPO" =~ ^[A-Za-z0-9][A-Za-z0-9._-]*/[A-Za-z0-9._-]+$ ]] || fehler "$(t "ungültiger Besitzer: $OWNER_REPO" "invalid owner: $OWNER_REPO")"

# Werte landen in der erzeugten Compose-Datei und im Befehl auf der VM: nur einfache Zeichen.
EINFACH='^[A-Za-z0-9._:/@-]+$'
for wert in "$PORTAL_NETZ" "$PORTAL_API" "$PORTAL_ADAPTERS" "$PORTAL_ISSUER"; do
  [[ "$wert" =~ $EINFACH ]] || fehler "$(t "ungültiger Wert: $wert" "invalid value: $wert")"
done

NAME="app-$SLUG"
MODUS=$(t "ein Container" "one container")
[ -f compose.yml ] && MODUS="compose.yml"
if [ "$ZIEL" = vm ]; then
  ZIEL_HOST="$VM_USER@$VM"
  echo "    $(t "App $SLUG, Besitzer $OWNER_REPO, Ziel $ZIEL_HOST, Modus: $MODUS" "App $SLUG, owner $OWNER_REPO, target $ZIEL_HOST, mode: $MODUS")"
else
  echo "    $(t "App $SLUG, Besitzer $OWNER_REPO, Ziel lokaler Stack $PORTAL_STACK, Modus: $MODUS" "App $SLUG, owner $OWNER_REPO, target local stack $PORTAL_STACK, mode: $MODUS")"
fi

# ── Lokal: laufendes Portal finden ───────────────────────────────────────────
# Image, Konfiguration und Ordner kommen aus dem Portal-Container: kein Pfad in ein anderes Repository.

if [ "$ZIEL" = lokal ]; then
  schritt "$(t "Lokalen Stack finden ($PORTAL_STACK)" "Find local stack ($PORTAL_STACK)")"
  BACKEND=$(docker ps -q --filter "label=com.docker.compose.project=$PORTAL_STACK" \
                         --filter "label=com.docker.compose.service=backend")
  [ -n "$BACKEND" ] || fehler "$(t "Portal läuft nicht. Im Gateway-Repository: make server-up" "The portal is not running. In the gateway repository: make server-up")"
  [ "$(wc -l <<<"$BACKEND")" -eq 1 ] || fehler "$(t "mehr als ein Portal-Container im Projekt $PORTAL_STACK" "more than one portal container in project $PORTAL_STACK")"
  docker network inspect "$PORTAL_NETZ" >/dev/null 2>&1 || fehler "$(t "Docker-Netz $PORTAL_NETZ fehlt. Im Gateway-Repository: make server-up" "Docker network $PORTAL_NETZ is missing. In the gateway repository: make server-up")"
  quelle() { docker inspect -f "{{range .Mounts}}{{if eq .Destination \"$1\"}}{{.Source}}{{end}}{{end}}" "$BACKEND"; }
  PORTAL_IMAGE=$(docker inspect -f '{{.Config.Image}}' "$BACKEND")
  PORTAL_CONFIG_IN_IMAGE=$(docker inspect -f '{{range .Config.Env}}{{println .}}{{end}}' "$BACKEND" | sed -n 's/^PORTAL_CONFIG=//p')
  MANIFESTS_DIR=$(quelle /var/lib/portal/manifests)
  REGISTRY_DIR=$(quelle /var/lib/portal/registry)
  [ -n "$MANIFESTS_DIR" ] && [ -n "$REGISTRY_DIR" ] && [ -n "$PORTAL_CONFIG_IN_IMAGE" ] \
    || fehler "$(t "Portal-Container ohne Ordner für Manifeste/Registry oder ohne PORTAL_CONFIG" "portal container without manifest/registry folders or without PORTAL_CONFIG")"
  echo "    $(t "Portal $PORTAL_IMAGE, Konfiguration $PORTAL_CONFIG_IN_IMAGE" "Portal $PORTAL_IMAGE, configuration $PORTAL_CONFIG_IN_IMAGE")"
fi

# ── Image bereitstellen ──────────────────────────────────────────────────────
# Einziger Schritt, der von der Herkunft abhängt. Mit HKA-57 setzt man nur IMAGE; alles danach bleibt gleich.

if [ -z "$IMAGE" ]; then
  # Wie make docker: <slug>:<stufe>-JJJJMMTT-HHMM, Labels mit Bauzeit und Git-Commit (HKA-65)
  schritt "$(t "Image lokal bauen, Stufe" "Build image locally, stage") ${STUFE:-test}${PLATTFORM[*]+ (${PLATTFORM[*]})}"
  IMAGE=$(bash tools/build-image.sh ${PLATTFORM[@]+"${PLATTFORM[@]}"})
else
  # Nie latest: Sonst ist auf der VM nicht zu erkennen, welcher Stand läuft (HKA-65)
  REF="${IMAGE%%@*}"
  case "${REF##*/}" in
    *:latest) fehler "$(t "IMAGE mit Tag latest ist nicht erlaubt. Ein festes Tag oder einen Digest (@sha256:…) angeben." "IMAGE with tag latest is not allowed. Give a fixed tag or a digest (@sha256:…).")" ;;
    *:*) ;;
    *) [ "$REF" != "$IMAGE" ] || fehler "$(t "IMAGE ohne Tag heißt latest. Ein festes Tag oder einen Digest (@sha256:…) angeben." "IMAGE without a tag means latest. Give a fixed tag or a digest (@sha256:…).")" ;;
  esac
  [[ "$IMAGE" =~ $EINFACH ]] || fehler "$(t "ungültiger Image-Name: $IMAGE" "invalid image name: $IMAGE")"   # vor dem Ziehen prüfen
  schritt "$(t "Image ziehen" "Pull image"): $IMAGE${PLATTFORM[*]+ (${PLATTFORM[*]})}"
  docker pull ${PLATTFORM[@]+"${PLATTFORM[@]}"} "$IMAGE"
fi
[[ "$IMAGE" =~ $EINFACH ]] || fehler "$(t "ungültiger Image-Name: $IMAGE" "invalid image name: $IMAGE")"
# Name ohne Tag und Digest, für docker images auf der VM (ein Port im Registry-Namen bleibt stehen)
REPO="${IMAGE%%@*}"
case "${REPO##*/}" in *:*) REPO="${REPO%:*}" ;; esac
echo "    Image $IMAGE"

mkdir -p build/deploy
BILDER=("$IMAGE")

# ── Optional: compose.yml prüfen und ergänzen ────────────────────────────────

ERGAENZUNG="build/deploy/compose.deploy.yml"
if [ "$MODUS" = compose.yml ]; then
  schritt "$(t "compose.yml ergänzen und prüfen" "Extend and check compose.yml")"
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
  KONFIG=$(docker compose -f compose.yml -f "$ERGAENZUNG" config --format json) || fehler "$(t "compose.yml ist ungültig" "compose.yml is invalid")"

  PRUEFUNG=$(cat <<'PY'
import json, os, sys
EN = os.environ.get("DEPLOY_LANG") == "en"


def m(de, en):
    return en if EN else de


cfg = json.load(sys.stdin)
services = cfg.get("services", {})
fehler = []
if "app" not in services:
    fehler.append(m('Service "app" fehlt', 'Service "app" is missing'))
verboten = ["ports", "privileged", "network_mode", "pid", "ipc", "cap_add", "devices", "userns_mode"]
for name, s in services.items():
    for key in verboten:
        if s.get(key):
            fehler.append(f"{name}: {key} " + m("ist nicht erlaubt", "is not allowed"))
    for v in s.get("volumes", []):
        if v.get("type") != "volume" and not (v.get("type") == "tmpfs"):
            fehler.append(m(f"{name}: nur benannte Volumes, kein {v.get('type')} ({v.get('source', '')})",
                            f"{name}: named volumes only, not {v.get('type')} ({v.get('source', '')})"))
    netze = set(s.get("networks", {}) or {"default": None})
    for n, c in (s.get("networks") or {}).items():
        if c and (c.get("aliases") or c.get("ipv4_address") or c.get("ipv6_address")):
            fehler.append(m(f"{name}: aliases und feste Adressen im Netz {n} sind nicht erlaubt",
                            f"{name}: aliases and fixed addresses in network {n} are not allowed"))
    if name == "app":
        if netze - {"default", "portal"}:
            fehler.append(m(f"app: nur die Netze default und portal, nicht {sorted(netze - {'default', 'portal'})}",
                            f"app: only the networks default and portal, not {sorted(netze - {'default', 'portal'})}"))
        continue
    if s.get("build"):
        fehler.append(m(f"{name}: build ist nur für app erlaubt, sonst ein fertiges Image",
                        f"{name}: build is allowed for app only, otherwise a finished image"))
    if s.get("container_name"):
        fehler.append(f"{name}: container_name " + m("ist nicht erlaubt", "is not allowed"))
    if netze - {"default"}:
        fehler.append(m(f"{name}: nur das Netz default, nicht {sorted(netze - {'default'})}",
                        f"{name}: only the network default, not {sorted(netze - {'default'})}"))
for n, net in cfg.get("networks", {}).items():
    if net.get("external") and n != "portal":
        fehler.append(m(f"Netz {n}: externe Netze sind nicht erlaubt", f"Network {n}: external networks are not allowed"))
if fehler:
    print("\n".join(fehler), file=sys.stderr)
    sys.exit(1)
for name, s in services.items():
    if name != "app":
        print(s["image"])
PY
)
  if command -v python3 >/dev/null 2>&1 && python3 -c "" 2>/dev/null; then
    WEITERE=$(DEPLOY_LANG="$SPRACHE" python3 -c "$PRUEFUNG" <<<"$KONFIG") || fehler "$(t "compose.yml erfüllt die Regeln nicht (siehe oben)" "compose.yml does not follow the rules (see above)")"
  else
    WEITERE=$(docker run --rm -i -e DEPLOY_LANG="$SPRACHE" python:3-alpine python -c "$PRUEFUNG" <<<"$KONFIG") || fehler "$(t "compose.yml erfüllt die Regeln nicht (siehe oben)" "compose.yml does not follow the rules (see above)")"
  fi
  for bild in $WEITERE; do
    [[ "$bild" =~ $EINFACH ]] || fehler "$(t "ungültiger Image-Name in compose.yml: $bild" "invalid image name in compose.yml: $bild")"
    schritt "$(t "Image ziehen" "Pull image"): $bild${PLATTFORM[*]+ (${PLATTFORM[*]})}"
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

M_FEHLER=$(t FEHLER ERROR)
M_UNHEALTHY=$(t "ist nicht healthy" "is not healthy")
M_LOGZEILEN=$(t "Letzte Zeilen aus dem Log:" "Last log lines:")
STARTEN_UND_WARTEN=$(cat <<EOF
echo "==> $(t "$NAME neu starten ($MODUS)" "restart $NAME ($MODUS)")"
${SUDO}docker rm -f $NAME >/dev/null 2>&1 || true
$STARTEN
echo "==> $(t "warten auf healthy" "wait for healthy")"
for _ in \$(seq 1 30); do
  status=\$(${SUDO}docker inspect -f '{{.State.Health.Status}}' $NAME)
  [ "\$status" = healthy ] && break
  [ "\$status" = unhealthy ] && break
  sleep 2
done
if [ "\$status" != healthy ]; then
  echo "$M_FEHLER: $NAME $M_UNHEALTHY (\$status). $M_LOGZEILEN" >&2
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
      -e "PORTAL_LANG=$SPRACHE" \
      -v "$MANIFESTS_DIR:/var/lib/portal/manifests:$rw" \
      -v "$REGISTRY_DIR:/var/lib/portal/registry:$rw" \
      --entrypoint python \
      "$PORTAL_IMAGE" \
      -m portal.registry "$1" --config "$PORTAL_CONFIG_IN_IMAGE" --owner "$OWNER_REPO" <manifest.json
  }

  schritt "$(t "Lokal starten" "Start locally")"
  bash -c "set -euo pipefail
$STARTEN_UND_WARTEN"
  schritt "$(t "Manifest prüfen" "Check manifest")"
  portal_registry check
  schritt "$(t "Manifest registrieren" "Register manifest")"
  portal_registry register

  LETZTER=$(t "fertig" "done")
  echo ""
  echo "$(t "Fertig. In etwa 10 s im Menü" "Done. In the menu in about 10 s"): http://localhost:18080/  (App: http://localhost:18080/apps/$SLUG/)"
  echo "Image: $IMAGE"
  exit 0
fi

# ── VM: übertragen ───────────────────────────────────────────────────────────

PAKET="build/deploy/$NAME.tar.gz"
schritt "$(t "Images packen" "Pack images"): $PAKET"
docker save "${BILDER[@]}" | gzip >"$PAKET"

schritt "$(t "Auf die VM kopieren" "Copy to the VM")"
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
echo "==> $(t "Images $REPO auf der VM" "Images $REPO on the VM")"
sudo docker images $REPO
sudo docker network inspect $PORTAL_NETZ >/dev/null 2>&1 || { echo "$M_FEHLER: $(t "Docker-Netz $PORTAL_NETZ fehlt. Läuft das Portal?" "Docker network $PORTAL_NETZ is missing. Is the portal running?")" >&2; exit 1; }
$STARTEN_UND_WARTEN
echo "==> portal-deploy check"
sudo portal-deploy check --owner $OWNER_REPO < ~/manifests/$SLUG.json
echo "==> portal-deploy register"
sudo portal-deploy register --owner $OWNER_REPO < ~/manifests/$SLUG.json
rm -f ~/deploy/$NAME.tar.gz
EOF
)

schritt "$(t "Auf der VM einspielen und registrieren" "Load and register on the VM")"
ssh -t "$ZIEL_HOST" "bash -c $(q "$REMOTE")"

LETZTER=$(t "fertig" "done")
echo ""
echo "$(t "Fertig. In etwa 10 s im Menü" "Done. In the menu in about 10 s"): https://$VM/  (App: https://$VM/apps/$SLUG/)"
echo "Image: $IMAGE"
