"""Prerequisite labs.

    python -m labs status              what passes, per lab; refreshes the ticks on the doc site
    python -m labs open  <id>          open a lab (notebooks launch JupyterLab)
    python -m labs check <id> [stage]  run a lab's checks; for the capstone, optionally one stage
    python -m labs hint  <id> [n]      show hints 1..n (default 1)

Lab ids look like p1-03 or p1-cap. Run from the prerequisites/ folder.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

from .labkit import record
from .runner import LABS, Lab, discover, run_notebook, run_pytest, stage_progress

MANIFEST = LABS.parent / "site" / "assets" / "course.js"


def lab_status(lab: Lab) -> tuple[bool, str]:
    if lab.format == "pytest":
        ok, results, _ = run_pytest(lab)
        if not results:
            return False, "tests did not run"
        done, stages = stage_progress(results)
        if ok:
            return True, "passed"
        if stages:
            return False, f"stage {done} of {stages} complete"
        failing = sum(1 for v in results.values() if not v)
        return False, f"{failing} of {len(results)} tests failing"
    done = record.tasks_done(lab.id)
    missing = [t for t in lab.tasks if t not in done]
    if not missing:
        return True, "passed"
    return False, ("not started" if len(missing) == len(lab.tasks) else f"{len(lab.tasks) - len(missing)} of {len(lab.tasks)} tasks done")


def manifest_labs() -> list[tuple[str, str, dict]]:
    """(phase id, phase name, lab entry) for every lab the doc site lists, in course order."""
    try:
        text = MANIFEST.read_text(encoding="utf-8")
        course = json.loads(text[text.index("{") : text.rindex("}") + 1])
    except (OSError, ValueError):
        return []
    return [(ph["id"], ph["short"], p["lab"]) for ph in course["phases"] for p in ph["pages"] if p.get("lab")]


def cmd_status(labs: dict[str, Lab]) -> int:
    site: dict[str, dict] = {}
    listed = manifest_labs() or [("", "", {"id": lab.id, "title": lab.title, "format": lab.format}) for lab in labs.values()]
    current = None
    for phase_id, phase_name, entry in listed:
        if phase_id != current:
            current = phase_id
            print(f"\nPhase {phase_id}  {phase_name}")
        lab = labs.get(entry["id"])
        if lab is None:
            print(f"  {entry['id']:<7} {entry['title']:<34} in page    (tracked in the browser)")
            continue
        ok, detail = lab_status(lab)
        site[lab.id] = {"passed": ok, "detail": detail}
        print(f"  {lab.id:<7} {lab.title:<34} {lab.format:<9}  {detail}")
    record.write_site_progress(site)
    print("\nSidebar ticks updated. Reload the page to see them.")
    return 0


def cmd_check(lab: Lab, stage: str | None) -> int:
    if lab.format == "pytest":
        ok, results, out = run_pytest(lab, keyword=f"stage{stage}_" if stage else None, quiet=False)
        print(out)
        if not stage:
            done, stages = stage_progress(results)
            if stages and not ok:
                print(f"Stage {done} of {stages} complete. Next: python -m labs check {lab.id} {done + 1}")
    else:
        ok, error = run_notebook(lab)
        if ok:
            print(f"{lab.id}: the notebook ran top to bottom and every check passed.")
        else:
            print(f"{lab.id}: stopped at the first cell that failed:\n  {error}")
            print("Open the notebook to work on that cell:  python -m labs open " + lab.id)
        ok = ok and lab_status(lab)[0]
    print("PASSED" if ok else "Not passed yet.")
    return 0 if ok else 1


def cmd_hint(lab: Lab, upto: int) -> int:
    if not lab.hints:
        print("No hints for this lab.")
        return 0
    for i, hint in enumerate(lab.hints[:upto], 1):
        print(f"Hint {i} of {len(lab.hints)}: {hint}\n")
    if upto < len(lab.hints):
        print(f"More: python -m labs hint {lab.id} {upto + 1}")
    else:
        print(f"Reference solution: labs/solutions/{lab.path.parent.name}/{lab.path.name}/")
    return 0


def cmd_open(lab: Lab) -> int:
    rel = lab.path.relative_to(LABS.parent)
    if lab.format == "notebook":
        nb = lab.path / "lab.ipynb"
        print(f"Launching JupyterLab on {rel / 'lab.ipynb'} (or open that file in VS Code).")
        subprocess.Popen([sys.executable, "-m", "jupyterlab", str(nb)], cwd=lab.path)
    else:
        print(f"Edit these in your editor ({rel}):")
        for name in lab.files:
            print(f"  {rel / name}")
        print(f"Then run:  python -m labs check {lab.id}")
    return 0


def main(argv: list[str]) -> int:
    if hasattr(sys.stdout, "reconfigure"):
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    labs = discover()
    if not argv or argv[0] not in {"status", "check", "hint", "open"}:
        print(__doc__)
        return 2
    if argv[0] == "status":
        return cmd_status(labs)
    if len(argv) < 2 or argv[1] not in labs:
        print("Unknown lab. Available: " + ", ".join(labs))
        return 2
    lab = labs[argv[1]]
    extra = argv[2] if len(argv) > 2 else None
    if argv[0] == "check":
        return cmd_check(lab, extra)
    if argv[0] == "hint":
        return cmd_hint(lab, int(extra) if extra else 1)
    return cmd_open(lab)


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
