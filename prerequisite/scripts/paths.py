"""Paths for the portable learning project; independent of the caller's cwd."""
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SITE = ROOT / 'site'
LABS = SITE / 'labs'
SCRIPTS = ROOT / 'scripts'
DOCS = ROOT / 'docs'
