"""Prüfnachweis nach der Confluence-Vorlage „Vorlage: User Story, Akzeptanzkriterien und Prüfnachweis“
(Vorlage B: Prüfnachweis, Checkliste Code-Review).

Der automatische Lauf füllt aus, was er belegen kann (Datum, Commit, Prüfweg, Nachweis, Tests, Lint,
Regeln, Commit-Nachrichten). Alles andere bleibt [OFFEN] oder [ ] und prüft der Reviewer.

Aufruf:
  make check-skills / make check-starter  →  report.py schreibt den Bericht eines Selbsttests
  make check                              →  python tools/tests/pruefnachweis.py (gemeinsamer Nachweis)

In der Pipeline (GitHub Actions) stehen Link zum Lauf und zum Pull Request automatisch im Nachweis.
Gleicher Aufbau wie tools/tests/pruefnachweis.js im JavaScript-Golden-Master.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
from collections.abc import Mapping
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SPRACHE = "Python"
REPORT_DIR = ROOT / "build" / "pruefberichte"
VORLAGE = "https://hka-awp.atlassian.net/wiki/spaces/HKA/pages/19922945"
OFFEN = "[OFFEN]"
TICKET_RE = re.compile(r"^HKA-\d+\b")
LAEUFE = [
    ("skills", "make check-skills", "Selbsttest Skills"),
    ("starter", "make check-starter", "Selbsttest Starter"),
]
NEBENLAEUFE = [("lint", "make lint"), ("test", "make test")]

# Abschnitte und Punkte genau wie in der Vorlage; der zweite Wert sagt, womit der Lauf den Punkt belegt
CHECKLISTE: list[tuple[str, list[tuple[str, object]]]] = [
    (
        "Funktion",
        [
            ("Jedes Akzeptanzkriterium ist umgesetzt", None),
            ("Prüfweg je Kriterium ausgeführt, auch der Negativfall", None),
            ("Tests grün (lokal oder Pipeline)", "tests"),
        ],
    ),
    (
        "Qualität",
        [
            ("Linter fehlerfrei (Ruff / ESLint)", "lint"),
            ("Konventionen und Code-Standards eingehalten", None),
            ("Code verständlich, keine toten oder auskommentierten Teile", None),
            ("Regeln aus AGENTS.md / Golden Master eingehalten", "regeln"),
        ],
    ),
    (
        "Sicherheit",
        [
            ("Keine Secrets, Tokens oder Passwörter im Code", ("R-SEC-1", "R-SEC-2")),
            ("Login und Rollen nur über das Portal", ("R-PORT-1", "R-PORT-2")),
            ("Nur Testdaten und Mocks, kein Zugriff auf Produktivsysteme", None),
        ],
    ),
    (
        "Doku",
        [
            ("README oder Confluence-Seite aktualisiert", None),
            ("Manifest angepasst, wenn relevant", "manifest"),
            ("Commit-Nachrichten beginnen mit der Ticket-ID", "commits"),
        ],
    ),
]


def datum(d: dt.datetime) -> str:
    return f"{d:%d.%m.%Y}"


def stempel(d: dt.datetime) -> str:
    return f"{d:%Y-%m-%d_%H-%M-%S}"


def rel(path: Path) -> str:
    try:
        return path.relative_to(ROOT).as_posix()
    except ValueError:  # Ordner außerhalb des Repositories (Selbsttest des Prüfnachweises)
        return path.as_posix()


def _git(*args: str) -> str | None:
    try:
        result = subprocess.run(["git", *args], cwd=ROOT, capture_output=True, text=True)
    except OSError:
        return None
    return result.stdout.strip() if result.returncode == 0 else None


def git_info() -> dict:
    """Commit, Zustand und eigene Commits gegenüber dem Zielzweig (main oder GITHUB_BASE_REF)."""
    if _git("rev-parse", "--git-dir") is None:
        return {"stand": "unbekannt", "commit": None, "sauber": None, "commits": None, "basis": None}
    commit = _git("rev-parse", "--short", "HEAD")
    if commit is None:
        return {"stand": "ohne Commit", "commit": None, "sauber": None, "commits": None, "basis": None}
    sauber = not _git("status", "--porcelain")
    ziel = os.environ.get("GITHUB_BASE_REF") or "main"
    basis = next((r for r in (f"origin/{ziel}", ziel) if _git("rev-parse", "--verify", "--quiet", r) is not None), None)
    log = _git("log", "--no-merges", "--format=%s", f"{basis}..HEAD") if basis else None
    return {
        "stand": f"{commit} ({'sauber' if sauber else 'mit lokalen Änderungen'})",
        "commit": commit,
        "sauber": sauber,
        "commits": None if log is None else [s for s in log.split("\n") if s],
        "basis": basis,
    }


def ci_info(env: Mapping[str, str] | None = None) -> dict:
    """Angaben aus der Pipeline (GitHub Actions); lokal leer. `env` nur für die Selbsttests."""
    env = os.environ if env is None else env
    ci = env.get("GITHUB_ACTIONS") == "true" or env.get("CI") == "true"
    server = env.get("GITHUB_SERVER_URL") or "https://github.com"
    repo = env.get("GITHUB_REPOSITORY")
    lauf = f"{server}/{repo}/actions/runs/{env['GITHUB_RUN_ID']}" if repo and env.get("GITHUB_RUN_ID") else None
    pr = re.match(r"^refs/pull/(\d+)/", env.get("GITHUB_REF", ""))
    pull_request = env.get("PR_URL") or (f"{server}/{repo}/pull/{pr.group(1)}" if repo and pr else None)
    return {
        "ci": ci,
        "repo": repo,
        "lauf": lauf,
        "pull_request": pull_request,
        "ereignis": env.get("GITHUB_EVENT_NAME"),
        "zweig": env.get("GITHUB_HEAD_REF") or env.get("GITHUB_REF_NAME"),
    }


def repo_name(ci: dict) -> str:
    """owner/name: in der Pipeline aus GITHUB_REPOSITORY, lokal aus dem Remote origin, sonst der Ordnername."""
    if ci.get("repo"):
        return ci["repo"]
    url = _git("remote", "get-url", "origin") or ""
    treffer = re.search(r"[:/]([^/:]+/[^/]+?)(?:\.git)?/?$", url)
    return treffer.group(1) if treffer else ROOT.name


def lauf_zeile(b: dict) -> str:
    return (
        f"{b['ergebnis']} · {b['pruefungen']} Prüfungen ({b['einzelfaelle']} Einzelfälle) · "
        f"{b['fehler']} Fehler · {b['uebersprungen']} übersprungen"
    )


def lauf_name(art: str, index: int) -> str:
    return next(lauf[index] for lauf in LAEUFE if lauf[0] == art)


def bewerte(beleg, ctx: dict) -> tuple[bool, str]:
    """Bewertet einen Punkt der Checkliste: [x] nur, wenn der Lauf ihn vollständig belegt."""
    reviewer = (False, "prüft der Reviewer")
    starter = next((b for b in ctx["berichte"] if b["art"] == "starter"), None)
    if beleg is None:
        return reviewer

    if beleg == "tests":
        teile = [(lauf_name(b["art"], 2), b["fehler"] == 0, b["ergebnis"]) for b in ctx["berichte"]]
        test = ctx["nebenlaeufe"].get("test")
        if test:
            teile.append(("make test", test["ok"], "bestanden" if test["ok"] else "FEHLER"))
        text = ", ".join(f"{name} {wort}" for name, _, wort in teile)
        if not all(ok for _, ok, _ in teile):
            return False, f"✘ {text}"
        if not test:
            return False, f"teilweise automatisch: {text}; App-Tests (make test) nur bei make check"
        return True, f"automatisch: {text}"

    if beleg == "lint":
        lint = ctx["nebenlaeufe"].get("lint")
        if not lint:
            return False, "make lint läuft nur bei make check"
        return (True, "automatisch: make lint bestanden") if lint["ok"] else (False, "✘ make lint meldet Fehler")

    if beleg == "regeln":
        if not starter:
            return False, "Skills stimmig; Einhaltung im Starter nur mit make check-starter"
        regeln = starter["regeln"]
        geprueft = [r for r, o in regeln.items() if o in ("passed", "failed")]
        fehler = [r for r, o in regeln.items() if o == "failed"]
        if fehler:
            return False, f"✘ Fehler bei {', '.join(fehler)}"
        return (
            False,
            f"teilweise automatisch: {len(geprueft)} von {len(regeln)} Einzelregeln bestanden; "
            "übrige prüft der Reviewer",
        )

    if beleg == "manifest":
        if not starter:
            return reviewer
        wort = "bestanden" if starter["regeln"].get("R-PORT-4") == "passed" else "✘ Fehler"
        return False, f"prüft der Reviewer; Schema automatisch geprüft (R-PORT-4 {wort})"

    if beleg == "commits":
        commits, basis = ctx["git"]["commits"], ctx["git"]["basis"]
        if commits is None:
            return False, "nicht prüfbar (kein Zielzweig main gefunden)"
        if not commits:
            return False, f"nicht prüfbar (keine eigenen Commits gegenüber {basis})"
        ohne = [s for s in commits if not TICKET_RE.match(s)]
        if ohne:
            return False, f"✘ {len(ohne)} von {len(commits)} ohne Ticket-ID, z. B. „{ohne[0]}“"
        return True, f"automatisch: alle {len(commits)} Commits gegenüber {basis}"

    # Liste von Regel-IDs: nur der Starter prüft, ob die App sie einhält
    if not starter:
        return False, "nur mit make check-starter"
    stand = [(r, starter["regeln"].get(r)) for r in beleg]
    fehler = [r for r, o in stand if o == "failed"]
    if fehler:
        return False, f"✘ Fehler bei {', '.join(fehler)}"
    if all(o == "passed" for _, o in stand):
        return True, f"automatisch: {', '.join(beleg)} bestanden"
    return False, "prüft der Reviewer (nicht vollständig automatisch geprüft)"


def stand_zeile(ctx: dict) -> str:
    """Zeile „Stand“: Repo, Commit, Pull Request; in der Pipeline auch Link zum Lauf."""
    git, ci = ctx["git"], ctx["ci"]
    commit = git.get("commit") or "unbekannt"
    if git.get("sauber") is False:
        commit += " mit lokalen Änderungen"
    if ci["pull_request"]:
        pr = ci["pull_request"]
    elif ci["ci"]:
        ereignis, zweig = ci["ereignis"] or "unbekanntem Ereignis", ci["zweig"] or "unbekanntem Zweig"
        pr = f"kein PR, weil Lauf nach {ereignis} auf {zweig}"
    else:
        pr = OFFEN
    lauf = f", Lauf {ci['lauf']}" if ci["lauf"] else ""
    return f"Stand: {ctx['repo']}, Commit {commit}, Pull Request {pr}{lauf}"


def beleg_zeile(name: str, ok: bool | None, befehle: list[str], ctx: dict) -> str:
    """Zeile wie ein AK: Urteil, Beleg, Art des Belegs. `ok` None: der Lauf hat den Punkt nicht geprüft."""
    ci = ctx["ci"]
    if ok is None:
        return f"{name}: {OFFEN} – Beleg: nur mit make check – {OFFEN} (selbst ausgeführt / Pipeline / nur gelesen)"
    lauf = f", Lauf {ci['lauf']}" if ci["lauf"] else ""
    art = "Pipeline" if ci["ci"] else "selbst ausgeführt"
    return f"{name}: {'erfüllt' if ok else 'nicht erfüllt'} – Beleg: {', '.join(befehle)}{lauf} – {art}"


def vorlage_b(ctx: dict) -> list[str]:
    """Block „Vorlage B: Prüfnachweis“ (Entwurf 0.2): Zeilen und Reihenfolge wie in Confluence,
    dazu Lint und Tests wie ein Akzeptanzkriterium. Urteil, Reviewer und AK setzt der Reviewer."""
    neben = ctx["nebenlaeufe"]
    lint = neben["lint"]["ok"] if "lint" in neben else None
    tests = None
    if "test" in neben:
        tests = neben["test"]["ok"] and all(b["fehler"] == 0 for b in ctx["berichte"])
    test_befehle = ["make test", *(b for _, b, _ in LAEUFE)]
    ak = f"{OFFEN} – Beleg: [Test, Befehl oder Link] – {OFFEN} (selbst ausgeführt / Pipeline / nur gelesen)"
    return [
        "Prüfnachweis",
        f"Urteil: {OFFEN} (abgenommen / zurück an Umsetzung / nicht prüfbar)",
        f"Geprüft von, Datum: {OFFEN}",
        stand_zeile(ctx),
        f"AK1: {ak}",
        f"AK2: {ak}",
        beleg_zeile("Lint", lint, ["make lint"], ctx),
        beleg_zeile("Tests", tests, test_befehle, ctx),
        f"Muss: {OFFEN} (Befund mit Fundstelle oder „keine“)",
        f"Sollte: {OFFEN} (Befund oder „keine“)",
        f"Nicht geprüft: {OFFEN} (was und warum, oder „nichts“)",
        f"Code-Review-Checkliste durchgegangen: {OFFEN} (ja / nein)",
    ]


def render(ctx: dict) -> tuple[str, list[str], bool]:
    """Erzeugt Markdown (Datei) und Textzeilen (Konsole).

    ctx: titel, befehle, berichte (Zusammenfassungen aus report.py), nebenlaeufe (lint, test), zeit, datei
    """
    ctx.setdefault("git", git_info())
    ctx.setdefault("ci", ci_info())
    ctx.setdefault("repo", repo_name(ctx["ci"]))
    ok = all(b["fehler"] == 0 for b in ctx["berichte"]) and all(lauf["ok"] for lauf in ctx["nebenlaeufe"].values())
    ctx["ergebnis"] = "BESTANDEN" if ok else "NICHT BESTANDEN"
    block = vorlage_b(ctx)
    liste = [(abschnitt, [(text, *bewerte(beleg, ctx)) for text, beleg in punkte]) for abschnitt, punkte in CHECKLISTE]
    ci = ctx["ci"]
    ausgefuehrt = ("Pipeline" + (f" ({ci['lauf']})" if ci["lauf"] else "")) if ci["ci"] else "auf eigenem Rechner"
    md: list[str] = []

    md += [f"# Prüfnachweis · Golden Master {SPRACHE} · {ctx['titel']}", ""]
    md += ["| Feld | Inhalt |", "| --- | --- |"]
    md.append(f"| Erzeugt mit | `{ctx['befehle'][0]}` |")
    md.append(f"| Zeitpunkt | {ctx['zeit']:%d.%m.%Y, %H:%M} Uhr |")
    md.append(f"| Repository | {ctx['repo']} · Stand {ctx['git']['stand']} |")
    md.append(f"| Ausgeführt | {ausgefuehrt} |")
    md.append(f"| Gesamtergebnis | **{ctx['ergebnis']}** |")
    md.append(
        f"| Vorlage | [Vorlage: User Story, Akzeptanzkriterien und Prüfnachweis]({VORLAGE})"
        " – Vorlage B und Checkliste Code-Review |"
    )
    md.append("")

    md += ["## 1. Prüfnachweis (Vorlage B)", ""]
    md += [
        "Der Reviewer legt den Prüfnachweis an: Er kopiert diesen Block als Kommentar ins Jira-Ticket, prüft jeden "
        "Beleg selbst und ersetzt alle [OFFEN]. Den Block nur aus einem Pipeline-Lauf oder aus dem eigenen "
        "`make check` nehmen, nicht aus dem Lauf der umsetzenden Person: Ihre Aussagen sind kein Beleg.",
        "",
    ]
    md += ["```text", *block, "```", ""]

    md += ["## 2. Checkliste Code-Review", ""]
    md += [
        "`[x]` belegt der automatische Lauf, der Reviewer bestätigt. `[ ]` prüft der Reviewer. "
        "✘ markiert einen Fehler im Lauf.",
        "",
    ]
    for abschnitt, punkte in liste:
        md += [f"**{abschnitt}**", ""]
        md += [f"- [{'x' if ok_ else ' '}] {text} — {hinweis}" for text, ok_, hinweis in punkte]
        md.append("")

    md += ["## 3. Ergebnis der automatischen Läufe", ""]
    md += ["| Lauf | Ergebnis |", "| --- | --- |"]
    md += [f"| `{lauf_name(b['art'], 1)}` | {lauf_zeile(b)} |" for b in ctx["berichte"]]
    for art, befehl in NEBENLAEUFE:
        if lauf := ctx["nebenlaeufe"].get(art):
            md.append(f"| `{befehl}` | {'BESTANDEN' if lauf['ok'] else 'NICHT BESTANDEN'} |")
    md.append("")

    nummer = 3
    for art, befehl in NEBENLAEUFE:
        lauf = ctx["nebenlaeufe"].get(art)
        if lauf and not lauf["ok"]:
            nummer += 1
            md += [f"## {nummer}. Ausgabe von `{befehl}` (letzte Zeilen)", "", "```text", *lauf["ausgabe"], "```", ""]
    for b in ctx["berichte"]:
        nummer += 1
        md += [f"## {nummer}. {b['titel']}", "", "```text", *b["bericht"], "```", ""]

    konsole = ["", " Prüfnachweis (Vorlage B) – in den Jira-Kommentar kopieren", " " + "─" * 60]
    konsole += [f" {z}" for z in block]
    konsole += ["", " Checkliste Code-Review ([x] automatisch belegt)"]
    for abschnitt, punkte in liste:
        konsole.append(f"   {abschnitt}")
        konsole += [f"   [{'x' if ok_ else ' '}] {text} — {hinweis}" for text, ok_, hinweis in punkte]
    return "\n".join(md), konsole, ok


def schreibe(slug: str, zeit: dt.datetime, inhalt: str, endung: str = "md", verzeichnis: Path = REPORT_DIR) -> Path:
    """Schreibt Bericht mit Zeitstempel und als „-aktuell“; gibt den Pfad der Datei mit Zeitstempel zurück."""
    verzeichnis.mkdir(parents=True, exist_ok=True)
    path = verzeichnis / f"{slug}-{stempel(zeit)}.{endung}"
    path.write_text(inhalt, encoding="utf-8")
    (verzeichnis / f"{slug}-aktuell.{endung}").write_text(inhalt, encoding="utf-8")
    return path


def datei_fuer(slug: str, zeit: dt.datetime, verzeichnis: Path = REPORT_DIR) -> str:
    """Datei des Berichts zuerst festlegen, damit der Nachweis auf sie verweisen kann."""
    return rel(verzeichnis / f"{slug}-{stempel(zeit)}.md")


def laufe(befehl: str) -> dict:
    cmd, *args = befehl.split(" ")
    result = subprocess.run([cmd, "--no-print-directory", *args], cwd=ROOT, capture_output=True, text=True)
    ausgabe = (result.stdout + result.stderr).rstrip().split("\n")[-30:]
    return {"ok": result.returncode == 0, "ausgabe": ausgabe}


def gesamt(verzeichnis: Path = REPORT_DIR, fuehre_aus=laufe) -> int:
    """make check: Selbsttests zusammenführen, make lint und make test ausführen, gemeinsamen Nachweis schreiben.

    `verzeichnis` und `fuehre_aus` ersetzen die Selbsttests des Prüfnachweises (temporärer Ordner, falsche Läufe)."""
    zeit = dt.datetime.now()
    git = git_info()
    berichte, fehlend = [], []
    for art, befehl, _ in LAEUFE:
        path = verzeichnis / f"pruefbericht-{art}-aktuell.json"
        if not path.exists():
            fehlend.append(befehl)
            continue
        bericht = json.loads(path.read_text(encoding="utf-8"))
        if bericht["stand"] != git["stand"]:
            fehlend.append(f"{befehl} (Bericht gehört zu Stand {bericht['stand']})")
        else:
            berichte.append(bericht)
    if fehlend:
        print(f" Prüfnachweis nicht erstellt. Zuerst ausführen: {', '.join(fehlend)}", file=sys.stderr)
        return 1
    nebenlaeufe = {art: fuehre_aus(befehl) for art, befehl in NEBENLAEUFE}
    datei = datei_fuer("pruefnachweis", zeit, verzeichnis)
    befehle = ["make check", *(b for _, b, _ in LAEUFE), *(b for _, b in NEBENLAEUFE)]
    ctx = {"titel": "Gesamt", "befehle": befehle, "berichte": berichte, "nebenlaeufe": nebenlaeufe}
    markdown, konsole, ok = render({**ctx, "zeit": zeit, "datei": datei, "git": git})
    path = schreibe("pruefnachweis", zeit, markdown, verzeichnis=verzeichnis)
    print("\n".join(konsole))
    print()
    print(f" Gesamtergebnis: {'BESTANDEN' if ok else 'NICHT BESTANDEN'}")
    print(f" Prüfnachweis gespeichert: {rel(path)} (auch pruefnachweis-aktuell.md)")
    print()
    return 0 if ok else 1


# Festes Beispiel für docs/pruefnachweis-beispiel.md: Lint grün, Tests rot (AK4). Gleich in beiden Golden Mastern.
BEISPIEL_REPO = "alexandru-tatar/awp-hka-gold-python"


def beispiel() -> dict:
    stand = "1a2b3c4 (sauber)"
    bericht = lambda art, titel: {  # noqa: E731
        "art": art,
        "titel": titel,
        "stand": stand,
        "ergebnis": "BESTANDEN",
        "pruefungen": 10,
        "einzelfaelle": 20,
        "fehler": 0,
        "uebersprungen": 0,
        "regeln": {r: "passed" for r in ("R-SEC-1", "R-SEC-2", "R-PORT-1", "R-PORT-2", "R-PORT-4")},
        "bericht": [f" Beispiel: {titel}"],
    }
    lauf = f"https://github.com/{BEISPIEL_REPO}/actions/runs/123456789"
    return {
        "titel": "Gesamt",
        "befehle": ["make check", *(b for _, b, _ in LAEUFE), *(b for _, b in NEBENLAEUFE)],
        "berichte": [bericht("skills", "Prüfbericht Skills"), bericht("starter", "Prüfbericht Starter")],
        "nebenlaeufe": {
            "lint": {"ok": True, "ausgabe": []},
            "test": {"ok": False, "ausgabe": ["FAILED tests/test_app.py::test_beispiel - assert 1 == 2"]},
        },
        "zeit": dt.datetime(2026, 11, 18, 12, 0, 0),
        "datei": "build/pruefberichte/pruefnachweis-2026-11-18_12-00-00.md",
        "repo": BEISPIEL_REPO,
        "git": {
            "stand": stand,
            "commit": "1a2b3c4",
            "sauber": True,
            "commits": ["HKA-62: Beispiel"],
            "basis": "origin/main",
        },
        "ci": {
            "ci": True,
            "repo": BEISPIEL_REPO,
            "lauf": lauf,
            "pull_request": f"https://github.com/{BEISPIEL_REPO}/pull/12",
            "ereignis": "pull_request",
            "zweig": "HKA62",
        },
    }


if __name__ == "__main__":
    if "--beispiel" in sys.argv:  # make check ruft das nicht auf; erzeugt docs/pruefnachweis-beispiel.md
        sys.stdout.write(render(beispiel())[0])
        sys.exit(0)
    sys.exit(gesamt())
