"""Check the whole prerequisites course in one command: run it before committing a change.

    python tools/verify.py            quick: structure, quiz answers, generated files, Pit Wall parity (about a minute)
    python tools/verify.py --full     also every lab's selftest and a re-train of recorded Training room runs (minutes)

Run from the prerequisites/ folder with the project's Python environment active and Node on PATH.
Nothing is changed: generated files are rebuilt into place, compared, and then put back as they were,
so a hand edit to a generated file shows up as a failure instead of being overwritten.

Checks, in order
  structure        tools/nav.py check: every page in the manifest, titled, linked, no broken links
  style            tools/nav.py style: word counts, cold opens, banned words (warnings only, never fails)
  answers          every quiz answer is one of its options, each lab question explains itself, every
                   "Your call" cold open has exactly one reveal, radio-button names are unique per question
  generated        lab blocks and quizzes (labs.tools.site), the hub (nav.py hub) and solution notebooks
                   (labs.tools.py2nb) match what their sources would produce
  pitwall          the browser's JavaScript against the Python it mirrors: engine and oracle, table learner,
                   rival duel, duel game, DQN replay, Training room plans
  labs (--full)    labs.tools.selftest: solutions pass, starters fail only on their TODOs
  training (--full) labs.tools.pitwall_training_export check: re-trains three recorded runs
"""

from __future__ import annotations

import argparse
import os
import re
import subprocess
import sys
import time
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]          # prerequisites/
SITE = HERE / "site"
PHASES = ("phase1", "phase35", "phase4", "phase5", "phase6", "phase8", "phase9")
ENV = dict(os.environ, PYTHONPATH=str(HERE), PYTHONIOENCODING="utf-8")


def run(args: list[str]) -> tuple[int, str]:
    p = subprocess.run(args, cwd=HERE, env=ENV, capture_output=True, text=True, encoding="utf-8", errors="replace")
    return p.returncode, (p.stdout + p.stderr).strip()


def py(*args: str) -> tuple[int, str]:
    return run([sys.executable, *args])


def last(text: str, n: int = 1) -> str:
    return "\n".join(text.splitlines()[-n:])


# --------------------------------------------------------------------------- answers

class _Quiz(HTMLParser):
    """The questions, cold opens and reveals of one page."""

    def __init__(self):
        super().__init__()
        self.qs, self.cur, self.depth, self.cold = [], None, 0, None
        self.calls, self.reveals, self.stack = [], [], []

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        cls = (a.get("class") or "").split()
        if tag == "section":
            self.stack.append("cold" if "cold-open" in cls else "other")
            if "cold-open" in cls:
                self.calls.append(a.get("data-call"))
                self.cold = a.get("data-call")
            if "reveal" in cls:
                self.reveals.append(a.get("data-for"))
        if tag == "div" and "lab-q" in cls:
            self.cur = {"type": a.get("data-type"), "answer": a.get("data-answer"), "values": [],
                        "explain": a.get("data-explain"), "cold": self.cold}
            self.depth = 1
            return
        if self.cur is not None:
            if tag == "div":
                self.depth += 1
            if tag in ("input", "option") and a.get("value") not in (None, ""):
                if tag == "option" or a.get("type") in ("radio", "checkbox"):
                    self.cur["values"].append(a["value"])

    def handle_endtag(self, tag):
        if tag == "section" and self.stack and self.stack.pop() == "cold":
            self.cold = None
        if self.cur is not None and tag == "div":
            self.depth -= 1
            if self.depth == 0:
                self.qs.append(self.cur)
                self.cur = None


def answers() -> tuple[bool, str]:
    bad, n, calls = [], 0, 0
    for f in sorted(SITE.glob("phase-*/*.html")):
        text = f.read_text(encoding="utf-8")
        rel = f.relative_to(SITE).as_posix()
        p = _Quiz()
        p.feed(text)
        for q in p.qs:
            n += 1
            t, ans = q["type"], q["answer"]
            ok = bool(q["explain"]) or bool(q["cold"])
            if t == "num":
                try:
                    float(ans)
                except (TypeError, ValueError):
                    ok = False
            elif t in ("choice", "select"):
                ok = ok and ans in q["values"]
            elif t == "multi":
                ok = ok and ans is not None and all(x in q["values"] for x in ans.split(","))
            else:
                ok = False
            if not ok:
                bad.append(f"{rel}: question with answer {ans!r} ({t}) has no matching option or no explanation")
        for c in p.calls:
            calls += 1
            if p.reveals.count(c) != 1:
                bad.append(f"{rel}: cold open {c} has {p.reveals.count(c)} reveals")
        for r in p.reveals:
            if r not in p.calls:
                bad.append(f"{rel}: reveal {r} without a cold open")
        groups = Counter()
        for m in re.finditer(r'<div class="lab-q[^"]*"[^>]*>(.*?)</div>', text, re.S):
            for name in set(re.findall(r'type="radio" name="([^"]+)"', m.group(1))):
                groups[name] += 1
        bad += [f"{rel}: radio name {k!r} used by {v} questions" for k, v in groups.items() if v > 1]
    return not bad, "\n".join(bad + [f"{n} questions, {calls} cold opens, {len(bad)} problem(s)"])


# --------------------------------------------------------------------------- generated files

def generated() -> tuple[bool, str]:
    roots = [SITE, HERE / "labs" / "solutions"]
    watch = [p for r in roots for p in r.rglob("*") if p.is_file() and p.suffix in (".html", ".js", ".ipynb")]
    before = {p: p.read_bytes() for p in watch}
    log = []
    try:
        for ph in PHASES:
            for tool in ("labs.tools.site", "labs.tools.py2nb"):
                code, out = py("-m", tool, ph)
                if code:
                    log.append(f"{tool} {ph} failed:\n{last(out, 5)}")
        code, out = py("tools/nav.py", "hub")
        if code:
            log.append(f"nav.py hub failed:\n{last(out, 5)}")
        after = [p for r in roots for p in r.rglob("*") if p.is_file() and p.suffix in (".html", ".js", ".ipynb")]
        changed = [p for p in after if p not in before or p.read_bytes() != before[p]]
        log += [f"{p.relative_to(HERE).as_posix()}: differs from what its source produces" for p in changed]
    finally:
        for p, data in before.items():  # put everything back as it was
            if not p.exists() or p.read_bytes() != data:
                p.write_bytes(data)
        for r in roots:
            for p in r.rglob("*"):
                if p.is_file() and p.suffix in (".html", ".js", ".ipynb") and p not in before:
                    p.unlink()
    log.append(f"{len(PHASES)} phases regenerated and compared, {len([l for l in log if 'differs' in l or 'failed' in l])} problem(s)")
    ok = len(log) == 1
    if not ok:
        log.append("Edit the source (labs/tools/site_src, labs/tools/nb_src, lab.yaml or course.js) and regenerate, "
                   "rather than the generated file.")
    return ok, "\n".join(log)


# --------------------------------------------------------------------------- the rest

def structure() -> tuple[bool, str]:
    code, out = py("tools/nav.py", "check")
    return code == 0, "\n".join(l for l in out.splitlines() if l.startswith("ERROR")) + ("\n" if code else "") + last(out)


def style() -> tuple[bool, str]:
    _, out = py("tools/nav.py", "style")
    return True, "\n".join(l for l in out.splitlines() if l.startswith("WARN") or "warning" in l)


def pitwall() -> tuple[bool, str]:
    checks = [
        ("engine and oracle", [sys.executable, "-m", "labs.tools.pitwall_parity"]),
        ("table learner", [sys.executable, "-m", "labs.tools.pitwall_learner_parity"]),
        ("rival duel", [sys.executable, "-m", "labs.tools.pitwall_duel_parity"]),
        ("duel game", [sys.executable, "-m", "labs.tools.pitwall_duel_game_export", "check"]),
        ("DQN replay", [sys.executable, "-m", "labs.tools.pitwall_replay_export", "check"]),
        ("Training room", ["node", "labs/tools/pitwall_training_parity_node.js"]),
    ]
    ok, lines = True, []
    for name, args in checks:
        code, out = run(args)
        ok = ok and code == 0
        lines.append(f"{name:18s} {last(out) if code == 0 else 'FAILED'}")
        if code:
            lines.append(last(out, 8))
    return ok, "\n".join(lines)


def labs() -> tuple[bool, str]:
    code, out = py("-m", "labs.tools.selftest")
    return code == 0, last(out, 3 if code == 0 else 30)


def training() -> tuple[bool, str]:
    code, out = py("-m", "labs.tools.pitwall_training_export", "check")
    return code == 0, out


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--full", action="store_true", help="also run every lab's selftest and re-train recorded runs")
    a = ap.parse_args()
    steps = [("structure", structure), ("style", style), ("answers", answers), ("generated", generated), ("pitwall", pitwall)]
    if a.full:
        steps += [("labs", labs), ("training", training)]
    failed = []
    for name, fn in steps:
        t = time.time()
        print(f"== {name}", flush=True)
        ok, report = fn()
        print("\n".join("   " + l for l in report.splitlines()))
        print(f"   {'ok' if ok else 'FAILED'} ({time.time() - t:.0f} s)\n", flush=True)
        if not ok:
            failed.append(name)
    print("ALL CHECKS PASSED" if not failed else "FAILED: " + ", ".join(failed))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
