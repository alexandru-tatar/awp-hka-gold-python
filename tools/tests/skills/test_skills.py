"""Selbsttests der Skills in `.agents/skills/`.

Prüft Form und Zusammenhang der Skills, ohne eine KI aufzurufen: Kopf, Regeltabellen,
Prüfungen, Zählung im README, Beispiele (Python, JSON), Verweise auf Befehle und Dateien,
Übereinstimmung mit `pyproject.toml` und mit dem JavaScript-Golden-Master.
Ob die KI die Skills befolgt, prüft das Prüfskript mit der Testaufgabe (HKA-30).

Aufruf: make check-skills
"""

from __future__ import annotations

import ast
import json
import re
import statistics

import pytest
from common import (
    JS_SKILLS_DIR,
    ROOT,
    RULE_PREFIX,
    SKILL_NAMES,
    SKILLS_DIR,
    banned_modules,
    code_blocks,
    load_skill,
    make_targets,
    manifest_errors,
    prose,
    pruefung,
    table_rows,
)

SKILLS = {name: load_skill(SKILLS_DIR, name) for name in SKILL_NAMES}
README = (SKILLS_DIR / "README.md").read_text(encoding="utf-8")
CATALOG = (SKILLS_DIR / "pipeline-fehler" / "fehlercodes.md").read_text(encoding="utf-8")
STAGES = {"lint", "test", "ci", "konf", "prf"}

# Befehle, die in den Skills stehen, aber nicht im Makefile des Starters
MAKE_ELSEWHERE = {"sdk-release"}  # Portal-Repository
MAKE_PLANNED = {"template-update"}  # Architekturvorschlag 07 §1, noch nicht umgesetzt

# Dateien, auf die die Skills verweisen, die es im Starter noch nicht gibt (Phase 2)
PATHS_PLANNED = {
    "AGENTS.md",
    "AGENTS.local.md",
    ".devcontainer/",
    "docs/schnittstellen/noten.md",
    "docs/schnittstellen/mail.md",
    "docs/schnittstellen/eakte.md",
    "docs/fehlercodes.md",
    "tools/a11y-structural.mjs",
    "build/a11y/",
}

# Paketnamen in den Skills → Modulname in banned-api
PACKAGE_TO_MODULE = {
    "python-jose": "jose",
    "fastapi-login": "fastapi_login",
    "fastapi-users": "fastapi_users",
    "SessionMiddleware": "starlette.middleware.sessions",
}


def rules(skill) -> list[list[str]]:
    return skill.table("Regeln")


def checks(skill) -> list[list[str]]:
    return skill.table("Prüfungen")


# ── Kopf ─────────────────────────────────────────────────────────────────────


@pruefung("Kopf und Aufbau", "Genau die sieben Skills sind vorhanden")
def test_genau_die_sieben_skills():
    found = sorted(p.parent.name for p in SKILLS_DIR.glob("*/SKILL.md"))
    assert found == sorted(SKILL_NAMES)


@pruefung("Kopf und Aufbau", "Kopf: name passt zum Ordner, description „Verwenden …“")
@pytest.mark.parametrize("name", SKILL_NAMES)
def test_kopf(name):
    meta = SKILLS[name].meta
    assert set(meta) == {"name", "description"}
    assert meta["name"] == name
    assert re.fullmatch(r"[a-z0-9-]{1,64}", meta["name"])
    assert meta["description"].startswith("Verwenden")
    assert 50 <= len(meta["description"]) <= 1024


@pruefung("Kopf und Aufbau", "Beschreibungen sind eindeutig")
def test_beschreibungen_verschieden():
    descriptions = [s.meta["description"] for s in SKILLS.values()]
    assert len(set(descriptions)) == len(descriptions)


# ── Aufbau ───────────────────────────────────────────────────────────────────


@pruefung("Kopf und Aufbau", "Pflichtabschnitte vorhanden")
@pytest.mark.parametrize("name", SKILL_NAMES)
def test_pflichtabschnitte(name):
    skill = SKILLS[name]
    for prefix in ("Regeln", "Gut / schlecht", "Prüfungen, die das absichern", "Vor dem"):
        skill.section(prefix)
    assert skill.body.lstrip().startswith("# "), "Titel (# …) fehlt"


@pruefung("Kopf und Aufbau", "Abschnitt „So geht es im Python-Starter“")
@pytest.mark.parametrize("name", [n for n in SKILL_NAMES if n != "pipeline-fehler"])
def test_python_abschnitt(name):
    SKILLS[name].section("So geht es im Python-Starter")


@pruefung("Kopf und Aufbau", "Prüfliste endet mit make lint und make test")
@pytest.mark.parametrize("name", SKILL_NAMES)
def test_pruefliste(name):
    items = re.findall(r"^- \[ \] (.+)$", SKILLS[name].section("Vor dem"), re.M)
    assert len(items) >= 4
    if name != "pipeline-fehler":
        assert "`make lint` und `make test` laufen ohne Fehler" in items[-1]


@pruefung("Kopf und Aufbau", "Tabelle „Gut / schlecht“ mit mindestens vier Paaren")
@pytest.mark.parametrize("name", SKILL_NAMES)
def test_gut_schlecht(name):
    rows = SKILLS[name].table("Gut / schlecht")
    assert len(rows) >= 4
    assert all(len(r) == 2 and r[0] and r[1] for r in rows)


# ── Regeln und Prüfungen ─────────────────────────────────────────────────────


@pruefung("Regeln und Prüfungen", "Regel-IDs fortlaufend, Stufe „muss“ oder „soll“")
@pytest.mark.parametrize("name", SKILL_NAMES)
def test_regeln_fortlaufend(name):
    ids = [r[0] for r in rules(SKILLS[name])]
    prefix = RULE_PREFIX[name]
    assert ids == [f"R-{prefix}-{i}" for i in range(1, len(ids) + 1)]
    assert all(r[2] in ("muss", "soll") for r in rules(SKILLS[name]))


@pruefung("Regeln und Prüfungen", "Jede Regel hat Prüfart (A/H/M) und Prüfstelle")
@pytest.mark.parametrize("name", SKILL_NAMES)
def test_jede_regel_hat_eine_pruefung(name):
    rule_ids = [r[0] for r in rules(SKILLS[name])]
    check_rows = checks(SKILLS[name])
    assert [r[0] for r in check_rows] == rule_ids
    for rule_id, check in check_rows:
        assert re.match(r"^[AHM] \(", check), f"{rule_id}: Prüfart A/H/M fehlt"
        assert set(re.findall(r"`([a-z]+)`", check)) & STAGES, f"{rule_id}: Prüfstelle fehlt"


@pruefung("Regeln und Prüfungen", "Zählung im README stimmt (40 / 33 muss / 7 soll)")
def test_readme_zaehlung():
    rows = {r[0].strip("`"): r for r in table_rows(README.split("## Zuordnung der Skills zu den Regeln")[1])}
    total = must = should = 0
    for name in SKILL_NAMES:
        levels = [r[2] for r in rules(SKILLS[name])]
        row = rows[name]
        count = int(re.search(r"\((\d+)\)", row[2]).group(1))
        assert count == len(levels), name
        assert int(row[3]) == levels.count("muss"), name
        assert int(row[4]) == levels.count("soll"), name
        total, must, should = total + count, must + levels.count("muss"), should + levels.count("soll")
    summe = rows["**Summe**"]
    assert summe[2] == f"**{total}**" and summe[3] == f"**{must}**" and summe[4] == f"**{should}**"
    assert (total, must, should) == (40, 33, 7)
    assert f"**{total} Einzelregeln**" in README


@pruefung("Regeln und Prüfungen", "README nennt alle Skill-Dateien")
def test_readme_aufbau_nennt_alle_dateien():
    for name in SKILL_NAMES:
        assert f"{name}/SKILL.md" in README
    assert "pipeline-fehler/fehlercodes.md" in README


# ── Beispiele ────────────────────────────────────────────────────────────────


@pruefung("Beispiele", "Python-Beispiele sind gültiger Code")
@pytest.mark.parametrize("name", SKILL_NAMES)
def test_python_beispiele_sind_gueltig(name):
    for block in code_blocks(SKILLS[name].text, "python"):
        ast.parse(block)


@pruefung("Beispiele", "Python-Beispiele ohne verbotene Importe", "R-SCHN-1", "R-PORT-1")
@pytest.mark.parametrize("name", SKILL_NAMES)
def test_python_beispiele_ohne_verbotene_importe(name):
    banned = banned_modules()
    for block in code_blocks(SKILLS[name].text, "python"):
        for node in ast.walk(ast.parse(block)):
            modules = []
            if isinstance(node, ast.Import):
                modules = [a.name for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.module:
                modules = [node.module] + [f"{node.module}.{a.name}" for a in node.names]
            for module in modules:
                assert not any(module == b or module.startswith(b + ".") for b in banned), f"{name}: {module}"


@pruefung("Beispiele", "Manifest-Beispiel entspricht dem Schema", "R-PORT-4")
def test_manifest_beispiel_ist_gueltig():
    blocks = code_blocks(SKILLS["portal"].text, "json")
    assert blocks
    for block in blocks:
        assert manifest_errors(json.loads(block)) == []


@pruefung("Beispiele", "Kategorien und Icons wie im Manifest-Schema", "R-PORT-4")
def test_manifest_tabelle_passt_zum_schema():
    from common import CATEGORIES, ICONS

    table = dict((r[0].strip("`"), r[1]) for r in SKILLS["portal"].table("So geht es"))
    assert set(re.findall(r"`([^`]+)`", table["category"])) == CATEGORIES
    assert set(re.findall(r"`([^`]+)`", table["menu.icon"])) == ICONS


@pruefung("Beispiele", "HTML-Beispiele ohne Rahmen, externe Adressen, „/“-Links", "R-DES-3", "R-DES-4", "R-PORT-3")
@pytest.mark.parametrize("name", SKILL_NAMES)
def test_html_beispiele_ohne_externe_adressen_und_rahmen(name):
    for block in code_blocks(SKILLS[name].text, "html"):
        assert not re.search(r'(src|href)="(https?:)?//', block)
        assert "<html" not in block and "<body" not in block
        assert 'href="/' not in block


@pruefung("Beispiele", "CSS-Beispiele nur mit Variablen des Portals", "R-DES-1")
def test_css_beispiele_nur_variablen():
    gut = [r[1] for r in SKILLS["design"].table("Gut / schlecht")]
    assert not any(re.search(r"#[0-9a-fA-F]{3,6}\b|rgb\(", g) for g in gut)


# ── Verweise ─────────────────────────────────────────────────────────────────


def all_skill_text() -> str:
    return "\n".join(s.text for s in SKILLS.values()) + README + CATALOG


@pruefung("Verweise", "Jeder genannte make-Befehl existiert")
def test_make_befehle_gibt_es():
    mentioned = set(re.findall(r"`make ([a-z][a-z-]*)", all_skill_text()))
    missing = mentioned - make_targets() - MAKE_ELSEWHERE - MAKE_PLANNED
    assert not missing, f"Befehle fehlen im Makefile: {sorted(missing)}"


@pruefung("Verweise", "Liste der geplanten Befehle ist aktuell")
def test_geplante_befehle_noch_offen():
    """Schlägt fehl, sobald ein geplanter Befehl umgesetzt ist: dann aus MAKE_PLANNED streichen."""
    assert not MAKE_PLANNED & make_targets()


@pruefung("Verweise", "Jeder genannte Pfad existiert (außer geplanten)")
def test_dateiverweise_gibt_es():
    candidates = set(
        re.findall(r"`((?:src|tests|platform_sdk|docs|tools|build|\.devcontainer)/[^`*<>\s]*)`", all_skill_text())
    )
    candidates |= set(
        re.findall(
            r"`((?:manifest\.json|pyproject\.toml|Makefile|Dockerfile|AGENTS(?:\.local)?\.md))`", all_skill_text()
        )
    )
    missing = {c for c in candidates if not (ROOT / c).exists()} - PATHS_PLANNED
    assert not missing, f"Verweise ohne Datei: {sorted(missing)}"


@pruefung("Verweise", "Jeder genannte Fehlercode steht im Katalog", "R-PF-3")
def test_fehlercodes_im_katalog():
    catalog = set(re.findall(r"^\| (PF-\d{3}) \|", CATALOG, re.M))
    assert len(catalog) >= 15
    mentioned = set(re.findall(r"PF-\d{3}", "\n".join(s.text for s in SKILLS.values())))
    assert mentioned <= catalog, sorted(mentioned - catalog)


@pruefung("Verweise", "Fehlerkatalog verweist nur auf vorhandene Skills")
def test_katalog_nennt_nur_skills_die_es_gibt():
    for name in re.findall(r"Skill[s]? (?:zur Regel laden )?\(?`([a-z-]+)`", CATALOG):
        assert name in SKILL_NAMES


@pruefung("Verweise", "Verweise auf andere Skills sind gültig")
def test_skillverweise_gibt_es():
    for name in re.findall(r"Skill `([a-z-]+)`", all_skill_text()):
        assert name in SKILL_NAMES, name


# ── Übereinstimmung mit dem Code des Starters ────────────────────────────────


@pruefung("Übereinstimmung mit dem Starter", "Verbotene Web-Bibliotheken meldet Ruff", "R-SCHN-1")
def test_verbotene_wege_aus_schnittstellen_meldet_ruff():
    sentence = re.search(
        r"Verbotene Wege, die `make lint` \(Ruff\) meldet: ([^\n]+?)\. Ebenso", SKILLS["schnittstellen"].text
    )
    named = set(re.findall(r"`([^`]+)`", sentence.group(1)))
    assert named and named <= banned_modules()


@pruefung("Übereinstimmung mit dem Starter", "Weitere verbotene Wege sind in Ruff eingetragen", "R-SCHN-1")
def test_ebenso_verbotene_wege_sind_in_ruff():
    sentence = re.search(
        r"Ebenso verboten, auch wenn die Prüfung sie noch nicht kennt: ([^\n]+)", SKILLS["schnittstellen"].text
    )
    named = {
        n for n in re.findall(r"`([^`]+)`", sentence.group(1).split(". ")[0]) if "." not in n or n == "http.client"
    }
    named -= {"psycopg", "pymysql", "sqlalchemy"}  # Datenbanktreiber: nur mit fremder Adresse verboten
    missing = named - banned_modules()
    assert not missing, f"In Ruff nachtragen oder Text anpassen: {sorted(missing)}"


@pruefung("Übereinstimmung mit dem Starter", "Verbotene Login-Bibliotheken meldet Ruff", "R-PORT-1")
def test_login_bibliotheken_aus_portal_meldet_ruff():
    item = re.search(r"\*\*Keine Login-Bibliotheken:\*\* ([^\n]+)", SKILLS["portal"].text).group(1)
    libraries = item.split(". ")[0]  # danach folgt der Hinweis auf platform_sdk/
    named = {PACKAGE_TO_MODULE.get(n, n) for n in re.findall(r"`([^`]+)`", libraries)}
    assert named <= banned_modules(), sorted(named - banned_modules())


@pruefung("Übereinstimmung mit dem Starter", "Sitzungs-Cookies meldet Ruff", "R-PORT-6")
def test_cookie_verbote_aus_portal_meldet_ruff():
    assert "starlette.middleware.sessions" in banned_modules()


@pruefung("Übereinstimmung mit dem Starter", "Python-Version im README wie in pyproject.toml")
def test_python_version_in_readme():
    major_minor = re.search(r">=(3\.\d+)", ROOT.joinpath("pyproject.toml").read_text()).group(1)
    assert f"Python {major_minor}" in README


# ── Antworten der KI (Beispiele in den Skills) ───────────────────────────────

FORBIDDEN_IN_ANSWER = [
    "abschalten",
    "umgehen",
    "überspringen",
    "noqa",
    "--no-verify",
    "allow_failure",
    "skip",
    "disable",
    "ignore the check",
]


def quote(text: str) -> str:
    return "\n".join(line[1:].strip() for line in text.splitlines() if line.startswith(">"))


@pruefung(
    "Beispielantworten der KI",
    "Pipeline: Ursache, Code, nächster Schritt, keine Verbotswörter",
    "R-PF-1",
    "R-PF-2",
    "R-PF-3",
    "R-PF-4",
)
def test_pipeline_beispielantwort():
    answer = quote(SKILLS["pipeline-fehler"].text.split("### Beispielantwort")[1].split("## Gut")[0])
    assert answer
    lowered = answer.lower()
    assert not [w for w in FORBIDDEN_IN_ANSWER if w in lowered]
    assert re.search(r"PF-\d{3}", answer), "Fehlercode fehlt (R-PF-3)"
    assert re.search(r"`make (lint|test)`", answer) or re.search(r"\(Zeile \d+\)|:\d+", answer), (
        "nächster Schritt fehlt (R-PF-2)"
    )
    assert "Was passiert ist" in answer and "Warum das wichtig ist" in answer and "Was Sie tun" in answer


@pruefung("Beispielantworten der KI", "Pipeline: Verbotsliste im Skill vollständig", "R-PF-4")
def test_pipeline_verbotsliste_wie_im_text():
    text = SKILLS["pipeline-fehler"].text
    for word in FORBIDDEN_IN_ANSWER:
        assert word in text


@pruefung("Beispielantworten der KI", "Geheimnisse: Antwort lehnt ab und zeigt den Weg", "R-SEC-3")
def test_secrets_beispielantwort():
    answer = quote(SKILLS["secrets"].text.split("Beispielantwort:")[1].split("## ")[0])
    assert answer.startswith("Das lege ich nicht")
    assert "portal.adapters" in answer and "APP_SECRET_" in answer and "Plattform-Team" in answer
    assert not re.search(r"(passwort|password)\s*[:=]", answer, re.I)


@pruefung("Beispielantworten der KI", "Geheimnisse: gutes Beispiel ohne Ersatzwert", "R-SEC-2")
def test_secrets_ohne_ersatzwert_im_guten_beispiel():
    gut = " ".join(r[1] for r in SKILLS["secrets"].table("Gut / schlecht"))
    assert "os.environ[" in gut
    assert not re.search(r"getenv\([^)]*,", gut)


# ── Sprache ──────────────────────────────────────────────────────────────────


@pruefung("Sprache", "Kurze Sätze (im Mittel höchstens 20 Wörter)")
@pytest.mark.parametrize("name", SKILL_NAMES)
def test_kurze_saetze(name):
    sentences = [s for s in re.split(r"(?<=[.!?])\s+", prose(SKILLS[name].body)) if len(s.split()) >= 3]
    assert statistics.mean(len(s.split()) for s in sentences) <= 20


@pruefung("Sprache", "Sie-Form, kein „du“")
@pytest.mark.parametrize("name", SKILL_NAMES)
def test_sie_form(name):
    text = prose(SKILLS[name].body)
    assert not re.search(r"\b(du|dein|deine|dich|dir)\b", text, re.I)


@pruefung("Sprache", "Gute Beispiele ohne englische Standardwörter", "R-UI-7")
@pytest.mark.parametrize("name", SKILL_NAMES)
def test_keine_englischen_standardwoerter_in_guten_beispielen(name):
    gut = " ".join(r[1] for r in SKILLS[name].table("Gut / schlecht"))
    assert not re.search(r"„(Submit|Cancel|OK|Loading…?)“", gut)


# ── Gleichlauf mit dem JavaScript-Golden-Master ──────────────────────────────

js = pytest.mark.skipif(not JS_SKILLS_DIR.is_dir(), reason="awp-hka-gold-js liegt nicht neben diesem Repository")


@pruefung("Gleichlauf mit JavaScript", "Kopf, Regeln, Prüfungen wie im JS-Golden-Master")
@js
@pytest.mark.parametrize("name", SKILL_NAMES)
def test_gleich_wie_js(name):
    other = load_skill(JS_SKILLS_DIR, name)
    assert other.meta == SKILLS[name].meta
    assert rules(other) == rules(SKILLS[name])
    assert checks(other) == checks(SKILLS[name])


@pruefung("Gleichlauf mit JavaScript", "Fehlerkatalog wie im JS-Golden-Master")
@js
def test_fehlerkatalog_gleich_wie_js():
    assert (JS_SKILLS_DIR / "pipeline-fehler" / "fehlercodes.md").read_text(encoding="utf-8") == CATALOG
