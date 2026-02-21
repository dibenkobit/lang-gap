"""Repo-root-relative directory constants."""

from pathlib import Path

# src/lang_gap/_paths.py -> src/lang_gap -> src -> <repo root>
REPO_ROOT = Path(__file__).resolve().parents[2]

QUESTIONS_DIR = REPO_ROOT / "questions"
RESULTS_DIR = REPO_ROOT / "results"
REPORTS_DIR = REPO_ROOT / "reports"
