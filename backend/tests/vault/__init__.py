"""Benefit Vault tests (pytest style), run by unittest through tests/pytest_bridge.py.

``python3 -m unittest discover -s tests -t .`` reaches this package through
load_tests below. With pytest installed, ``pytest backend/tests/vault`` runs
the same files directly.
"""
from pathlib import Path


def load_tests(loader, tests, pattern):
    from tests.pytest_bridge import suite_for
    return suite_for(__name__, Path(__file__).resolve().parent)
