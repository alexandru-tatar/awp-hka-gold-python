"""Prüfnachweis aus `make check`: Block im Format von Vorlage B 0.3 (HKA-91).

Gleiche erwartete Zeilen wie in tests/pruefnachweis.test.js im JavaScript-Golden-Master.
"""

import datetime as dt
import importlib.util
from pathlib import Path

DATEI = Path(__file__).resolve().parents[1] / "tools" / "tests" / "pruefnachweis.py"
_spec = importlib.util.spec_from_file_location("pruefnachweis", DATEI)
pruefnachweis = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(pruefnachweis)

PR = "https://github.com/beispiel/app/pull/7"


def erwartet(pull_request_zeile: str) -> list[str]:
    return [
        "Prüfnachweis",
        "Ergebnis: abgenommen / zurück an Umsetzung",
        "Geprüft von, am:",
        pull_request_zeile,
        "AK1: ok / nicht ok / nur gelesen – geprüft mit: <Test, Befehl oder Link>",
        "AK2: ok / nicht ok / nur gelesen – geprüft mit: <Test, Befehl oder Link>",
        "Befunde: <[Muss] oder [Sollte] mit Datei oder Stelle, sonst „keine“>",
    ]


def kontext(pull_request: str | None = None, commit: str | None = "abc1234") -> dict:
    return {
        "titel": "Gesamt",
        "befehle": ["make check"],
        "berichte": [],
        "nebenlaeufe": {},
        "zeit": dt.datetime(2026, 11, 24, 15, 0),
        "datei": "build/pruefberichte/pruefnachweis-2026-11-24_15-00-00.md",
        "git": {"stand": f"{commit} (sauber)", "commit": commit, "commits": None, "basis": None},
        "ci": {"ci": pull_request is not None, "lauf": None, "pull_request": pull_request},
    }


def test_ohne_pull_request_bleibt_feld_leer_und_commit_steht_da():
    assert pruefnachweis.vorlage_b(kontext()) == erwartet("Pull Request: (Commit abc1234)")


def test_ohne_commit_steht_unbekannt():
    assert pruefnachweis.vorlage_b(kontext(commit=None))[3] == "Pull Request: (Commit unbekannt)"


def test_pipeline_traegt_pull_request_und_commit_ein():
    assert pruefnachweis.vorlage_b(kontext(pull_request=PR)) == erwartet(f"Pull Request: {PR} (Commit abc1234)")


def test_nachweis_ohne_offen_platzhalter_und_mit_block():
    markdown, konsole, _ = pruefnachweis.render(kontext())
    assert "[OFFEN]" not in markdown
    assert "[OFFEN]" not in "\n".join(konsole)
    assert "\n".join(["```text", *erwartet("Pull Request: (Commit abc1234)"), "```"]) in markdown
    assert "legt der Reviewer als Kommentar im Jira-Ticket an" in markdown
