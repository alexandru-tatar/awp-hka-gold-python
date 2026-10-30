import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # tools/tests/common.py


def pytest_configure(config):
    from report import register

    register(config, "Prüfbericht Skills", "skills")
