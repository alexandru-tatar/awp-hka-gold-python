"""Testumgebung der Starter-Selbsttests: Betriebsmodus, ohne echtes Portal."""

import os
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))  # tools/tests/common.py

os.environ.pop("PORTAL_DEV", None)
os.environ.pop("PORTAL_BASE_PATH", None)
os.environ["PORTAL_ENV"] = "test"


def pytest_configure(config):
    from report import register

    register(config, "Prüfbericht Starter", "starter")
