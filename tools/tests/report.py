"""Prüfbericht für die Selbsttests des Golden Master (pytest-Plugin).

Ersetzt die Punkte von pytest durch einen deutschen Bericht: Prüfbereiche, jede Prüfung mit
Ergebnis, alle 40 Einzelregeln mit Stand, Gesamtergebnis. Der Bericht wird zusätzlich als
Markdown in `build/pruefberichte/` abgelegt, im Aufbau der Confluence-Vorlage „Prüfnachweis“
(Vorlage B und Checkliste Code-Review, siehe pruefnachweis.py). Eine JSON-Zusammenfassung
daneben nutzt `make check` für den gemeinsamen Prüfnachweis.

Jeder Test trägt die Markierung `pruefung` (siehe `common.pruefung`).
"""

from __future__ import annotations

import datetime as dt
import json
import re
import time
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path

import pruefnachweis
import pytest
from common import ROOT, RULE_PREFIX, SKILL_NAMES, SKILLS_DIR, load_skill

WIDTH = 100
MARK = {"passed": "✔", "failed": "✘", "skipped": "○"}
WORD = {"passed": "bestanden", "failed": "FEHLER", "skipped": "übersprungen"}


@dataclass
class Check:
    bereich: str
    titel: str
    regeln: tuple[str, ...]
    outcome: str = "passed"
    cases: int = 0
    failed_cases: list[str] = field(default_factory=list)
    messages: list[str] = field(default_factory=list)
    skip_reason: str = ""


@dataclass
class Rule:
    id: str
    text: str
    stufe: str
    pruefart: str
    skill: str


def load_rules() -> list[Rule]:
    rules = []
    for name in SKILL_NAMES:
        skill = load_skill(SKILLS_DIR, name)
        art = {r[0]: r[1] for r in skill.table("Prüfungen")}
        for rid, text, stufe in skill.table("Regeln"):
            rules.append(Rule(rid, text, stufe, art.get(rid, ""), name))
    return rules


def short(text: str, width: int) -> str:
    text = re.sub(r"`", "", text)
    return text if len(text) <= width else text[: width - 1] + "…"


def first_line(longrepr) -> str:
    crash = getattr(longrepr, "reprcrash", None)
    message = crash.message if crash else str(longrepr)
    message = message.replace("AssertionError: ", "").strip()
    line = message.splitlines()[0] if message else "Prüfung fehlgeschlagen"
    if line.startswith("assert "):
        line = "Bedingung nicht erfüllt: " + line.removeprefix("assert ")
    return short(line, WIDTH - 12)


class Pruefbericht:
    def __init__(self, config: pytest.Config, titel: str, regel_modus: str) -> None:
        self.config = config
        self.titel = titel
        self.regel_modus = regel_modus  # "skills": alle Regeln aus Sicht der Skills; "starter": Abdeckung im Starter
        self.checks: dict[str, Check] = {}
        self.order: list[str] = []
        self.case_param: dict[str, str] = {}
        self.started = time.time()
        self.git = pruefnachweis.git_info()

    # ── Sammeln ──────────────────────────────────────────────────────────────

    def pytest_collection_modifyitems(self, items: list[pytest.Item]) -> None:
        for item in items:
            mark = item.get_closest_marker("pruefung")
            if mark is None:
                raise pytest.UsageError(f"{item.nodeid}: Markierung @pruefung(...) fehlt")
            key = item.originalname if hasattr(item, "originalname") else item.name
            key = f"{item.module.__name__}::{key}"
            if bad := [r for r in mark.kwargs["regeln"] if not re.fullmatch(r"R-[A-Z0-9]+-\d+", r)]:
                raise pytest.UsageError(f"{item.nodeid}: ungültige Regel-ID {bad}")
            if key not in self.checks:
                self.checks[key] = Check(mark.kwargs["bereich"], mark.kwargs["titel"], tuple(mark.kwargs["regeln"]))
                self.order.append(key)
            self.checks[key].cases += 1
            callspec = getattr(item, "callspec", None)
            self.case_param[item.nodeid] = key + ("|" + callspec.id if callspec else "")

    def pytest_report_teststatus(self, report, config):
        # keine Punkte und Buchstaben pro Test; der Bericht folgt am Ende
        if report.when == "call" or (report.when == "setup" and report.outcome != "passed"):
            return report.outcome, "", ""
        return None

    def pytest_runtest_logreport(self, report: pytest.TestReport) -> None:
        entry = self.case_param.get(report.nodeid)
        if entry is None:
            return
        key, _, case = entry.partition("|")
        check = self.checks[key]
        if report.failed:
            check.outcome = "failed"
            check.failed_cases.append(case)
            check.messages.append(first_line(report.longrepr))
        elif report.skipped and check.outcome == "passed" and report.when in ("setup", "call"):
            check.outcome = "skipped"
            reason = report.longrepr[2] if isinstance(report.longrepr, tuple) else ""
            check.skip_reason = reason.removeprefix("Skipped: ")

    # ── Ausgabe ──────────────────────────────────────────────────────────────

    def pytest_terminal_summary(self, terminalreporter, exitstatus, config) -> None:
        tr = terminalreporter
        lines = self.render()
        tr.write_line("")
        for text, style in lines:
            tr.write_line(text, **style)
        path = self.save(lines)
        tr.write_line(f" Bericht gespeichert: {path.relative_to(ROOT)}", bold=True)
        tr.write_line("")

    def render(self) -> list[tuple[str, dict]]:
        out: list[tuple[str, dict]] = []
        add = lambda text="", **style: out.append((text, style))  # noqa: E731
        double, single = "═" * WIDTH, "─" * WIDTH
        version = (ROOT / "platform_sdk" / "VERSION").read_text(encoding="utf-8").strip()
        skills_version = re.search(r"Version (\S+)", (SKILLS_DIR / "README.md").read_text(encoding="utf-8"))
        now = dt.datetime.now()

        add(double, bold=True)
        add(f" HKA Portal · Golden Master Python · {self.titel}", bold=True)
        add(double, bold=True)
        add(f" Datum            {now:%d.%m.%Y, %H:%M} Uhr")
        add(f" Repository       {ROOT.name} · Stand {self.git['stand']}")
        add(f" Skills           Version {skills_version.group(1) if skills_version else '?'}")
        add(f" Portal-SDK       Version {version}")
        add(single)

        by_area: dict[str, list[Check]] = defaultdict(list)
        for key in self.order:
            by_area[self.checks[key].bereich].append(self.checks[key])
        for number, (area, checks) in enumerate(by_area.items(), start=1):
            done = sum(c.outcome == "passed" for c in checks)
            add("")
            add(f" {number}. {area}  ({done}/{len(checks)})", bold=True)
            for c in checks:
                count = f"{c.cases - len(c.failed_cases)}/{c.cases}" if c.cases > 1 else ""
                rules = ", ".join(c.regeln)
                label = short(c.titel, 62)
                add(f"   {MARK[c.outcome]} {label:<62} {count:>6}  {rules}", **self.style(c.outcome))
                if c.outcome == "failed":
                    for case, message in zip(c.failed_cases, c.messages, strict=False):
                        add(f"       → {('[' + case + '] ') if case else ''}{message}", red=True)
                elif c.outcome == "skipped":
                    add(f"       → übersprungen: {short(c.skip_reason, WIDTH - 22)}", yellow=True)

        add("")
        add(single)
        out += self.render_rules()
        add(single)
        failed = [c for c in self.checks.values() if c.outcome == "failed"]
        skipped = [c for c in self.checks.values() if c.outcome == "skipped"]
        cases = sum(c.cases for c in self.checks.values())
        seconds = f"{time.time() - self.started:.2f}".replace(".", ",")
        verdict = "NICHT BESTANDEN" if failed else "BESTANDEN"
        add(
            f" Gesamtergebnis: {verdict}  ·  {len(self.checks)} Prüfungen ({cases} Einzelfälle)  ·  "
            f"{len(failed)} Fehler  ·  {len(skipped)} übersprungen  ·  {seconds} s",
            bold=True,
            **({"red": True} if failed else {"green": True}),
        )
        add(double, bold=True)
        return out

    def render_rules(self) -> list[tuple[str, dict]]:
        out: list[tuple[str, dict]] = []
        rules = load_rules()
        must = sum(r.stufe == "muss" for r in rules)
        out.append(("", {}))
        if self.regel_modus == "skills":
            out.append((f" Einzelregeln in den Skills ({len(rules)}, davon {must} „muss“)", {"bold": True}))
            out.append(("   Stand: ✔ Regel, Prüfung und Beispiele des Skills sind stimmig", {}))
        else:
            out.append(
                (f" Abdeckung der Einzelregeln durch den Starter ({len(rules)}, davon {must} „muss“)", {"bold": True})
            )
            covered = sum(self.rule_outcome(r) is not None for r in rules)
            out.append(
                (f"   Im Starter geprüft: {covered} von {len(rules)}. Die übrigen prüfen Pipeline oder Prüfskript.", {})
            )
            out.append(("   Stand: ✔ bestanden · ✘ Fehler · ○ übersprungen · – hier nicht prüfbar", {}))
        current = None
        for rule in rules:
            if rule.skill != current:
                current = rule.skill
                out.append((f"   {rule.skill}", {"bold": True}))
            outcome = self.rule_outcome(rule)
            art = rule.pruefart.split(" ")[0]
            mark = MARK.get(outcome, "–")
            style = self.style(outcome) if outcome else {}
            out.append((f"   {mark} {rule.id:<10} {rule.stufe:<5} {art}  {short(rule.text, WIDTH - 30)}", style))
        return out

    def rule_outcome(self, rule: Rule) -> str | None:
        if self.regel_modus == "skills":
            # Fehler zählt für die Regel, wenn er ihren Skill (Parameter) oder sie selbst (Markierung) betrifft
            failed = any(
                c.outcome == "failed"
                and (rule.skill in c.failed_cases or (rule.id in c.regeln and self.blames(c, rule.id)))
                for c in self.checks.values()
            )
            return "failed" if failed else "passed"
        related = [c for c in self.checks.values() if rule.id in c.regeln]
        if not related:
            return None
        if any(c.outcome == "failed" and self.blames(c, rule.id) for c in related):
            return "failed"
        if all(c.outcome == "skipped" for c in related):
            return "skipped"
        return "passed"

    @staticmethod
    def blames(check: Check, rule_id: str) -> bool:
        """Nennt die Fehlermeldung Regeln, gilt der Fehler nur für diese; sonst für alle markierten."""
        named = {r for m in check.messages for r in re.findall(r"R-[A-Z0-9]+-\d+", m)}
        return rule_id in named if named else True

    @staticmethod
    def style(outcome: str | None) -> dict:
        return {"passed": {"green": True}, "failed": {"red": True}, "skipped": {"yellow": True}}.get(outcome, {})

    def summary(self, lines: list[tuple[str, dict]]) -> dict:
        checks = list(self.checks.values())
        fehler = sum(c.outcome == "failed" for c in checks)
        return {
            "art": self.regel_modus,
            "titel": self.titel,
            "stand": self.git["stand"],
            "ergebnis": "NICHT BESTANDEN" if fehler else "BESTANDEN",
            "pruefungen": len(checks),
            "einzelfaelle": sum(c.cases for c in checks),
            "fehler": fehler,
            "uebersprungen": sum(c.outcome == "skipped" for c in checks),
            "regeln": {r.id: self.rule_outcome(r) for r in load_rules()},
            "bericht": [text for text, _ in lines],
        }

    def save(self, lines: list[tuple[str, dict]]) -> Path:
        zeit = dt.datetime.now()
        slug = self.titel.lower().replace(" ", "-").replace("ü", "ue").replace("ä", "ae").replace("ö", "oe")
        bericht = self.summary(lines)
        datei = pruefnachweis.datei_fuer(slug, zeit)
        markdown, _, _ = pruefnachweis.render(
            {
                "titel": "Skills" if self.regel_modus == "skills" else "Starter",
                "befehle": [f"make check-{self.regel_modus}"],
                "berichte": [bericht],
                "nebenlaeufe": {},
                "zeit": zeit,
                "datei": datei,
                "git": self.git,
            }
        )
        summary = json.dumps({**bericht, "datei": datei}, ensure_ascii=False, indent=2)
        pruefnachweis.schreibe(slug, zeit, summary + "\n", "json")
        return pruefnachweis.schreibe(slug, zeit, markdown)


def register(config: pytest.Config, titel: str, regel_modus: str) -> None:
    config.addinivalue_line("markers", "pruefung(bereich, titel, regeln): Eintrag im Prüfbericht")
    if config.pluginmanager.has_plugin("pruefbericht"):
        return
    config.pluginmanager.register(Pruefbericht(config, titel, regel_modus), "pruefbericht")


__all__ = ["RULE_PREFIX", "register"]
