"""Author tool: prove every lab is sound.

    python -m labs.tools.selftest [phase]

For each lab: the reference solution must pass, and the learner starter must fail *only*
because of unfinished TODOs (NotImplementedError), never because of a crash or a wrong test.
Nothing is written to the progress record.
"""

from __future__ import annotations

import sys

from ..runner import LABS, discover, run_notebook, run_pytest


def main(phase: str | None) -> int:
    solutions = discover(LABS / "solutions")
    starters = discover(LABS)
    problems = 0
    for lab_id, sol in solutions.items():
        if phase and sol.path.parent.name != phase:
            continue
        notes = []
        if sol.format == "pytest":
            ok, results, out = run_pytest(sol, record=False)
            if not ok:
                notes.append("SOLUTION FAILS:\n" + out[-1500:])
        else:
            ok, err = run_notebook(sol, record=False)
            if not ok:
                notes.append(f"SOLUTION FAILS: {err}")

        starter = starters.get(lab_id)
        if starter is None:
            notes.append("no starter generated")
        elif starter.format == "pytest":
            ok, results, out = run_pytest(starter, record=False)
            bad = [
                line
                for line in out.splitlines()
                if line.startswith(("FAILED", "ERROR")) and "NotImplementedError" not in line and "LabTodo" not in line
            ]
            if ok:
                notes.append("starter passes without any work")
            if bad:
                notes.append("starter fails for a reason other than a TODO:\n  " + "\n  ".join(bad))
        else:
            ok, err = run_notebook(starter, record=False)
            if ok:
                notes.append("starter notebook passes without any work")
            elif not err.startswith(("NotImplementedError", "LabTodo")):
                notes.append(f"starter notebook fails for a reason other than a TODO: {err}")

        print(f"{'ok  ' if not notes else 'FAIL'} {lab_id}")
        for n in notes:
            print("     " + n.replace("\n", "\n     "))
        problems += bool(notes)
    print(f"{problems} lab(s) with problems")
    return 1 if problems else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1] if len(sys.argv) > 1 else None))
