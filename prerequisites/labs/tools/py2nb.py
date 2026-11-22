"""Author tool: build solution notebooks from plain-text sources.

    python -m labs.tools.py2nb phase1

Each labs/tools/nb_src/<phase>/<lab_folder>[.<name>].py becomes
labs/solutions/<phase>/<lab_folder>/<name or "lab">.ipynb. Cells are separated by
``# %%`` (code) or ``# %% [markdown]`` (markdown, every line prefixed with "# ").
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

LABS = Path(__file__).resolve().parents[1]


def convert(text: str) -> dict:
    cells, kind, lines = [], None, []

    def flush():
        if kind is None:
            return
        body = "\n".join(lines).strip("\n")
        if kind == "markdown":
            body = "\n".join(line[2:] if line.startswith("# ") else line.lstrip("#") for line in body.split("\n"))
            cells.append({"cell_type": "markdown", "metadata": {}, "source": body.splitlines(keepends=True)})
        elif body:
            cells.append({"cell_type": "code", "metadata": {}, "execution_count": None, "outputs": [], "source": body.splitlines(keepends=True)})

    for line in text.split("\n"):
        if line.startswith("# %%"):
            flush()
            kind, lines = ("markdown" if "[markdown]" in line else "code"), []
        else:
            lines.append(line)
    flush()
    for i, cell in enumerate(cells):
        cell["id"] = f"cell-{i:02d}"
    return {
        "cells": cells,
        "metadata": {
            "kernelspec": {"display_name": "Python 3", "language": "python", "name": "python3"},
            "language_info": {"name": "python"},
        },
        "nbformat": 4,
        "nbformat_minor": 5,
    }


def main(phase: str) -> None:
    for src in sorted((LABS / "tools" / "nb_src" / phase).glob("*.py")):
        folder, _, name = src.stem.partition(".")
        out = LABS / "solutions" / phase / folder / f"{name or 'lab'}.ipynb"
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(json.dumps(convert(src.read_text(encoding="utf-8")), indent=1, ensure_ascii=False) + "\n", encoding="utf-8", newline="\n")
        print("built", out.relative_to(LABS))


if __name__ == "__main__":
    main(sys.argv[1])
