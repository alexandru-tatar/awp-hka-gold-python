#!/usr/bin/env bash
# Container-Image bauen und eindeutig taggen (HKA-65). Verwaltete Datei: in beiden Golden Mastern gleich.
#
# Aufruf:  tools/build-image.sh                                        # Name = slug aus manifest.json, Stufe test
#          STUFE=prod tools/build-image.sh                             # Produktiv-Build
#          tools/build-image.sh hka/app-noten --platform linux/amd64   # eigener Name, weitere Optionen für docker build
#
# Ergebnis:  <name>:<stufe>-JJJJMMTT-HHMM mit der Bauzeit in Europe/Berlin, z. B. noten-uebersicht:test-20261125-1430.
#            Gibt es das Tag schon (zweiter Build in derselben Minute), kommt ein Zähler dazu: …-1430-2, …-1430-3.
#            Ein vorhandenes Tag wird nie überschrieben. Das Tag "latest" vergibt das Skript nie.
#            Labels (docker inspect): org.opencontainers.image.created  Bauzeit, RFC 3339, z. B. 2026-11-25T14:30:00+01:00
#                                     org.opencontainers.image.revision Git-Commit, mit "-dirty" bei nicht committeten
#                                                                       Änderungen (sie kommen mit ins Image)
#
# Ablauf:  Bauzeit und Commit bestimmen --> docker build (ohne Tag) --> freies Tag suchen --> docker tag
#          Das Tag wird erst nach dem Bauen vergeben. So bekommt auch ein Build, der während eines anderen startet und
#          nach ihm fertig wird, den Zähler.
#          Die Labels kommen per --label dazu, nicht über das Dockerfile: Sie ändern sich bei jedem Build und sollen den
#          Build-Cache nicht ungültig machen.
#
# Ausgabe: Fortschritt auf stderr. Auf stdout steht nur die fertige Image-Referenz, z. B. für
#          IMAGE=$(bash tools/build-image.sh …)
#
# Umgebungsvariablen:
#   STUFE     test oder prod                                                     (Standard: test)
#   BAUZEIT   feste Bauzeit für Tests, RFC 3339 in Europe/Berlin                 (Standard: jetzt)
#             z. B. BAUZEIT=2026-11-25T14:30:00+01:00
#
# Voraussetzung: Docker mit buildx (BuildKit). Läuft mit bash ab 3.2 (macOS), mit GNU und BSD date.

set -euo pipefail

fehler() { echo "FEHLER: $*" >&2; exit 1; }

cd "$(dirname "$0")/.."

# ── Stufe und Name ───────────────────────────────────────────────────────────

STUFE="${STUFE:-test}"
case "$STUFE" in
  test | prod) ;;
  *) fehler "STUFE muss test oder prod sein, nicht: $STUFE" ;;
esac

if [ $# -gt 0 ] && [ "${1#-}" = "$1" ]; then
  NAME="$1"
  shift
else
  NAME=$(sed -nE 's/^[[:space:]]*"slug"[[:space:]]*:[[:space:]]*"([^"]+)".*/\1/p' manifest.json | head -n 1)
  [ -n "$NAME" ] || fehler "kein slug in manifest.json. Namen angeben: tools/build-image.sh <name>"
fi
NAME_MUSTER='^[a-z0-9]+([._/-][a-z0-9]+)*$'
[[ "$NAME" =~ $NAME_MUSTER ]] || fehler "ungültiger Image-Name: $NAME (Kleinbuchstaben, Ziffern, . _ - /, ohne Tag)"

for arg in "$@"; do
  case "$arg" in
    -t | --tag | -t=* | --tag=*) fehler "kein eigenes Tag angeben, das Skript vergibt es selbst" ;;
  esac
done

# ── Bauzeit (Europe/Berlin) ──────────────────────────────────────────────────
# Ein einziger Aufruf von date, damit Tag und Label dieselbe Minute zeigen. %z liefert +0100, RFC 3339 verlangt +01:00.
# Kennt das System die Zeitzone nicht, rechnet date still in UTC (+0000): Das fängt die Prüfung auf +01:00/+02:00 ab.

if [ -n "${BAUZEIT:-}" ]; then
  CREATED="$BAUZEIT"
else
  jetzt=$(TZ=Europe/Berlin date +%Y-%m-%dT%H:%M:%S%z)
  CREATED="${jetzt:0:22}:${jetzt:22:2}"
fi
ZEIT_MUSTER='^([0-9]{4})-([0-9]{2})-([0-9]{2})T([0-9]{2}):([0-9]{2}):[0-9]{2}[+]0[12]:00$'
[[ "$CREATED" =~ $ZEIT_MUSTER ]] \
  || fehler "Bauzeit nicht in Europe/Berlin (erwartet z. B. 2026-11-25T14:30:00+01:00): $CREATED"
BASIS="$STUFE-${BASH_REMATCH[1]}${BASH_REMATCH[2]}${BASH_REMATCH[3]}-${BASH_REMATCH[4]}${BASH_REMATCH[5]}"

# ── Git-Commit ───────────────────────────────────────────────────────────────

if REVISION=$(git rev-parse HEAD 2>/dev/null); then
  if [ -n "$(git status --porcelain)" ]; then
    REVISION="$REVISION-dirty"
    echo "WARNUNG: nicht committete Änderungen, sie kommen mit ins Image (revision …-dirty)." >&2
  fi
else
  REVISION="unbekannt"
  echo "WARNUNG: kein Git-Repository oder noch kein Commit, revision ist \"unbekannt\"." >&2
fi

# ── Bauen ────────────────────────────────────────────────────────────────────

docker buildx version >/dev/null 2>&1 \
  || fehler "docker buildx fehlt (BuildKit, das Dockerfile braucht es). Ubuntu/Debian: sudo apt install docker-buildx; Docker Desktop hat es schon."

IIDFILE=$(mktemp "${TMPDIR:-/tmp}/build-image.XXXXXX")
trap 'rm -f "$IIDFILE"' EXIT

echo "==> Image bauen: $NAME (Stufe $STUFE, Bauzeit $CREATED, Commit $REVISION)" >&2
docker build ${1+"$@"} \
  --label "org.opencontainers.image.created=$CREATED" \
  --label "org.opencontainers.image.revision=$REVISION" \
  --iidfile "$IIDFILE" \
  . >&2
ID=$(cat "$IIDFILE")
[ -n "$ID" ] || fehler "docker build hat keine Image-ID geliefert"

# ── Freies Tag vergeben ──────────────────────────────────────────────────────

TAG="$BASIS"
n=1
while docker image inspect "$NAME:$TAG" >/dev/null 2>&1; do
  n=$((n + 1))
  [ "$n" -le 99 ] || fehler "mehr als 99 Builds in derselben Minute"
  TAG="$BASIS-$n"
done
docker tag "$ID" "$NAME:$TAG"

echo "==> fertig: $NAME:$TAG" >&2
echo "$NAME:$TAG"
