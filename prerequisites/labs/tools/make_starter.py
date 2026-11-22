"""Author tool: generate learner starters from the reference solutions.

    python -m labs.tools.make_starter phase1            # refuses to overwrite existing labs
    python -m labs.tools.make_starter phase1 --force    # regenerates, DISCARDING learner edits

A solution marks what the learner must write:

    # >>> SOLUTION: Sum the rewards until the episode ends
    ...reference code...
    # <<< SOLUTION

becomes a TODO comment plus ``raise NotImplementedError("TODO <lab>: ...")``, and a line ending
in ``# >>> ANSWER`` has its value replaced by ``None``. Everything else is copied verbatim, so
a starter can never drift from its solution.
"""

from __future__ import annotations

import json
import re
import shutil
import sys
from pathlib import Path

import yaml

LABS = Path(__file__).resolve().parents[1]
OPEN = re.compile(r"^(\s*)# >>> SOLUTION: (.*)$")
CLOSE = re.compile(r"^\s*# <<< SOLUTION\s*$")
ANSWER = re.compile(r"^(\s*[A-Za-z_][A-Za-z0-9_\[\]\"']*\s*=\s*).*?\s*# >>> ANSWER\s*$")


def strip(source: str, lab_id: str) -> str:
    out, skipping = [], False
    for line in source.split("\n"):
        if skipping:
            skipping = not CLOSE.match(line)
            continue
        m = OPEN.match(line)
        if m:
            indent, what = m.groups()
            out.append(f"{indent}# TODO: {what}")
            out.append(f"{indent}raise NotImplementedError({json.dumps(f'TODO {lab_id}: {what}', ensure_ascii=False)})")
            skipping = True
            continue
        m = ANSWER.match(line)
        if m:
            out.append(f"{m.group(1)}None  # TODO: your answer")
            continue
        out.append(line)
    if skipping:
        raise SystemExit(f"{lab_id}: unclosed SOLUTION marker")
    return "\n".join(out)


def strip_notebook(text: str, lab_id: str) -> str:
    nb = json.loads(text)
    for cell in nb["cells"]:
        if cell["cell_type"] == "code":
            cell["source"] = strip("".join(cell["source"]), lab_id).splitlines(keepends=True)
            cell["outputs"], cell["execution_count"] = [], None
    return json.dumps(nb, indent=1, ensure_ascii=False) + "\n"


def generate(phase: str, force: bool) -> None:
    for lab_yaml in sorted((LABS / "solutions" / phase).glob("*/lab.yaml")):
        src = lab_yaml.parent
        dst = LABS / phase / src.name
        lab_id = yaml.safe_load(lab_yaml.read_text(encoding="utf-8"))["id"]
        if dst.exists():
            if not force:
                print(f"skip   {dst.relative_to(LABS)} (exists; --force overwrites learner work)")
                continue
            shutil.rmtree(dst)
        for path in sorted(src.rglob("*")):
            if path.is_dir() or "__pycache__" in path.parts or ".ipynb_checkpoints" in path.parts:
                continue
            target = dst / path.relative_to(src)
            target.parent.mkdir(parents=True, exist_ok=True)
            if path.suffix == ".py":
                target.write_text(strip(path.read_text(encoding="utf-8"), lab_id), encoding="utf-8", newline="\n")
            elif path.suffix == ".ipynb":
                target.write_text(strip_notebook(path.read_text(encoding="utf-8"), lab_id), encoding="utf-8", newline="\n")
            else:
                shutil.copyfile(path, target)
        print(f"wrote  {dst.relative_to(LABS)}")


if __name__ == "__main__":
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    if not args:
        raise SystemExit(__doc__)
    generate(args[0], "--force" in sys.argv)
