"""Gemeinsame Hilfen für die Selbsttests des Golden Master (Skills und Starter)."""

from __future__ import annotations

import re
import tomllib
from dataclasses import dataclass, field
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SKILLS_DIR = ROOT / ".agents" / "skills"
JS_SKILLS_DIR = ROOT.parent / "awp-hka-gold-js" / ".agents" / "skills"

SKILL_NAMES = ["design", "barrierefreiheit", "ui-regeln", "schnittstellen", "portal", "pipeline-fehler", "secrets"]
RULE_PREFIX = {
    "design": "DES",
    "barrierefreiheit": "A11Y",
    "ui-regeln": "UI",
    "schnittstellen": "SCHN",
    "portal": "PORT",
    "pipeline-fehler": "PF",
    "secrets": "SEC",
}

# Manifest-Regeln nach portal/schemas/manifest.schema.json
SLUG_RE = re.compile(r"^[a-z][a-z0-9-]{2,30}$")
CATEGORIES = {"Studium", "Verwaltung", "Kommunikation", "Sonstiges"}
ICONS = {"grades", "mail", "calendar", "document", "people", "book", "room", "settings", "info"}
ROLE_RE = re.compile(r"^[a-z][a-z0-9-]*$")
ADAPTER_RE = re.compile(r"^[a-z][a-z0-9-]*:[a-z][a-z0-9-]*$")
VERSION_RE = re.compile(r"^(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)\.(0|[1-9][0-9]*)$")
MANIFEST_FIELDS = {"slug", "name", "category", "menu", "roles", "adapters", "claims", "version"}


def manifest_errors(m: dict) -> list[str]:
    """Abweichungen vom Manifest-Schema als Liste (leer = gültig)."""
    errors = []
    if unknown := set(m) - MANIFEST_FIELDS:
        errors.append(f"unbekannte Felder: {sorted(unknown)}")
    for key in ("slug", "name", "category", "menu", "roles", "version"):
        if key not in m:
            errors.append(f"Pflichtfeld fehlt: {key}")
    if "slug" in m and not SLUG_RE.match(str(m["slug"])):
        errors.append("slug ungültig")
    if "name" in m and not (isinstance(m["name"], str) and 1 <= len(m["name"]) <= 60):
        errors.append("name ungültig")
    if "category" in m and m["category"] not in CATEGORIES:
        errors.append("category ungültig")
    menu = m.get("menu", {})
    if "menu" in m:
        if set(menu) != {"label", "icon"}:
            errors.append("menu braucht genau label und icon")
        if not (isinstance(menu.get("label"), str) and 1 <= len(menu["label"]) <= 40):
            errors.append("menu.label ungültig")
        if menu.get("icon") not in ICONS:
            errors.append("menu.icon ungültig")
    roles = m.get("roles")
    if "roles" in m and not (
        isinstance(roles, list) and roles and len(set(roles)) == len(roles) and all(ROLE_RE.match(r) for r in roles)
    ):
        errors.append("roles ungültig")
    adapters = m.get("adapters", [])
    if not (isinstance(adapters, list) and all(ADAPTER_RE.match(a) for a in adapters)):
        errors.append("adapters ungültig")
    if "version" in m and not VERSION_RE.match(str(m["version"])):
        errors.append("version ungültig")
    return errors


@dataclass
class Skill:
    name: str
    path: Path
    text: str
    meta: dict[str, str]
    body: str
    sections: dict[str, str] = field(default_factory=dict)

    def section(self, prefix: str) -> str:
        for title, content in self.sections.items():
            if title.startswith(prefix):
                return content
        raise KeyError(f"{self.name}: Abschnitt „{prefix}…“ fehlt")

    def table(self, prefix: str) -> list[list[str]]:
        return table_rows(self.section(prefix))


def load_skill(directory: Path, name: str) -> Skill:
    path = directory / name / "SKILL.md"
    text = path.read_text(encoding="utf-8")
    match = re.match(r"^---\n(.*?)\n---\n(.*)$", text, re.S)
    assert match, f"{path}: Kopf (---) fehlt"
    meta = {}
    for line in match.group(1).splitlines():
        key, _, value = line.partition(":")
        meta[key.strip()] = value.strip()
    body = match.group(2)
    sections = {}
    for part in re.split(r"^## ", body, flags=re.M)[1:]:
        title, _, content = part.partition("\n")
        sections[title.strip()] = content
    return Skill(name, path, text, meta, body, sections)


def table_rows(markdown: str) -> list[list[str]]:
    """Datenzeilen der ersten Tabelle (ohne Kopf und Trennzeile)."""
    rows, started = [], False
    for line in markdown.splitlines():
        if line.startswith("|"):
            cells = [c.strip() for c in line.strip().strip("|").split("|")]
            if started and not all(set(c) <= {"-", ":"} for c in cells):
                rows.append(cells)
            started = True
        elif started:
            break
    return rows[0:] if rows else []


def code_blocks(markdown: str, language: str) -> list[str]:
    return re.findall(rf"^```{language}\n(.*?)^```", markdown, re.S | re.M)


def prose(markdown: str) -> str:
    """Fließtext ohne Codeblöcke, Tabellen, Überschriften, Zitate und Prüflisten."""
    text = re.sub(r"^```.*?^```", "", markdown, flags=re.S | re.M)
    lines = [
        line
        for line in text.splitlines()
        if line.strip() and not line.lstrip().startswith(("|", "#", ">", "- [ ]", "*Status", "```"))
    ]
    return "\n".join(lines)


def pyproject() -> dict:
    return tomllib.loads((ROOT / "pyproject.toml").read_text(encoding="utf-8"))


def banned_modules() -> set[str]:
    return set(pyproject()["tool"]["ruff"]["lint"]["flake8-tidy-imports"]["banned-api"])


def make_targets() -> set[str]:
    text = (ROOT / "Makefile").read_text(encoding="utf-8")
    return set(re.findall(r"^([a-z][a-z-]*):", text, re.M))


def pruefung(bereich: str, titel: str, *regeln: str):
    """Markierung für den Prüfbericht: Prüfbereich, betroffene Einzelregeln."""
    import pytest

    return pytest.mark.pruefung(bereich=bereich, titel=titel, regeln=regeln)
