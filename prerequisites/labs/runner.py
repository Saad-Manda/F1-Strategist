"""Discovering labs and running their checks. Used by the CLI and by the author self-test."""

from __future__ import annotations

import os
import re
import subprocess
import sys
from dataclasses import dataclass
from pathlib import Path

import yaml

LABS = Path(__file__).resolve().parent


@dataclass
class Lab:
    id: str
    title: str
    format: str  # "notebook" or "pytest"
    path: Path
    minutes: int
    tasks: list[str]
    hints: list[str]
    files: list[str]


def discover(base: Path = LABS) -> dict[str, Lab]:
    labs = {}
    for lab_yaml in sorted(base.glob("phase*/*/lab.yaml")):
        meta = yaml.safe_load(lab_yaml.read_text(encoding="utf-8"))
        labs[meta["id"]] = Lab(
            id=meta["id"],
            title=meta["title"],
            format=meta["format"],
            path=lab_yaml.parent,
            minutes=meta.get("minutes", 15),
            tasks=meta.get("tasks", []),
            hints=meta.get("hints", []),
            files=meta.get("files", []),
        )
    return labs


def run_pytest(lab: Lab, keyword: str | None = None, quiet: bool = True, record: bool = True) -> tuple[bool, dict[str, bool], str]:
    """Returns (all passed, {test name: passed}, raw output)."""
    cmd = [sys.executable, "-m", "pytest", "-p", "no:cacheprovider", "-rA", "--tb=no" if quiet else "--tb=short", "-q"]
    if keyword:
        cmd += ["-k", keyword]
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE="1", PYTHONIOENCODING="utf-8", COLUMNS="400")
    if not record:
        env["LABS_NO_RECORD"] = "1"
    proc = subprocess.run(cmd, cwd=lab.path, capture_output=True, text=True, encoding="utf-8", errors="replace", env=env)
    out = proc.stdout + proc.stderr
    results = {}
    for m in re.finditer(r"^(PASSED|FAILED|ERROR) (\S+?)(?: - (.*))?$", out, re.M):
        results[m.group(2).split("::")[-1]] = m.group(1) == "PASSED"
    return proc.returncode == 0 and bool(results), results, out


def run_notebook(lab: Lab, record: bool = True) -> tuple[bool, str]:
    """Execute lab.ipynb top to bottom in its own folder. Returns (ok, error summary)."""
    import nbformat
    from nbclient import NotebookClient
    from nbclient.exceptions import CellExecutionError

    previous = os.environ.get("LABS_NO_RECORD")
    if not record:
        os.environ["LABS_NO_RECORD"] = "1"
    try:
        nb = nbformat.read(lab.path / "lab.ipynb", as_version=4)
        client = NotebookClient(nb, timeout=180, kernel_name="python3", resources={"metadata": {"path": str(lab.path)}})
        try:
            client.execute()
        except CellExecutionError as err:
            return False, f"{err.ename}: {err.evalue}"
        return True, ""
    finally:
        if previous is None:
            os.environ.pop("LABS_NO_RECORD", None)
        else:
            os.environ["LABS_NO_RECORD"] = previous


def stage_progress(results: dict[str, bool]) -> tuple[int, int]:
    """For staged labs (tests named test_stageN_*): (highest stage with every earlier stage green, stage count)."""
    stages: dict[int, list[bool]] = {}
    for name, ok in results.items():
        m = re.match(r"test_stage(\d+)_", name)
        if m:
            stages.setdefault(int(m.group(1)), []).append(ok)
    done = 0
    for n in sorted(stages):
        if all(stages[n]):
            done = n
        else:
            break
    return done, len(stages)
