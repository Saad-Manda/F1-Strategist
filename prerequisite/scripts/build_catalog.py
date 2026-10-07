"""Generate the static catalog and author inventory from the canonical lab registry.

This is an authoring tool, not a deployment build requirement. Run with --write
after editing the registry; otherwise compare generated output without modifying it.
"""

from __future__ import annotations

import argparse
from collections import defaultdict
from html import escape, unescape
from html.parser import HTMLParser
import json
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from paths import ROOT, SITE, LABS, DOCS
REGISTRY = LABS / "assets" / "lab-registry.json"


def load_registry():
    return json.loads(REGISTRY.read_text(encoding="utf-8"))


def title_for(path):
    source = path.read_text(encoding="utf-8")
    heading = re.search(r"<h1[^>]*>(.*?)</h1>", source, re.S)
    return unescape(re.sub(r"<[^>]+>", "", heading[1])) if heading else path.stem


def catalog(data):
    phases = data["phases"]
    by_id = {lab["id"]: lab for lab in data["labs"]}
    ready_count = sum(lab['status'] == 'ready' for lab in data['labs'])
    planned_count = len(data['labs']) - ready_count
    nav = '\n'.join(
        f'<li><a href="#phase-{escape(p["id"])}"><span class="n">{escape(p["id"])}</span>'
        f'<span>{escape(p["title"])}</span></a></li>' for p in phases
    )
    options = ''.join(f'<option value="{escape(p["id"])}">Phase {escape(p["id"])}</option>' for p in phases)
    sections = []
    for phase in phases:
        cards = []
        for lab in (entry for entry in data["labs"] if entry["phase"] == phase["id"]):
            needs = ', '.join(
                f'<a href="#{escape(key)}">{escape(by_id[key]["title"])}</a>'
                for key in lab["prerequisites"]
            ) or 'Python functions, loops, and lists. No prior RL required.'
            reading = ' · '.join(
                f'<a href="../{escape(path)}">{escape(title_for(SITE / path))}</a>'
                for path in lab["references"]
            )
            mode = 'Guided build' if lab["mode"] == 'build' else 'Debugging challenge'
            status = 'Ready' if lab['status'] == 'ready' else 'Planned'
            start = (f'<p><a class="start-lab" href="{escape(lab["route"])}">Open lab</a> '
                     f'<span data-progress-state="{escape(lab["id"])}">Not started</span></p>') if lab['status'] == 'ready' else ''
            # Reserved routes are deliberately not emitted while lessons are planned.
            cards.append(f'''<article class="lab-card" id="{escape(lab['id'])}" data-lab-id="{escape(lab['id'])}" data-phase="{escape(lab['phase'])}" data-mode="{escape(lab['mode'])}">
  <div class="lab-meta"><code>{escape(lab['id'])}</code><span>{mode}</span><span>About {lab['minutes']} minutes per core session</span><span class="status">{status}</span></div>
  <h3>{escape(lab['title'])}</h3>
  <p>{escape(lab['objective'])}</p>
  {start}
  <p class="dependencies"><strong>Builds on:</strong> {needs}</p>
  <details><summary>What you’ll practice</summary>
    <p><strong>In the browser:</strong> {escape(lab['browser'])}</p>
    <p><strong>In local Python:</strong> {escape(lab['localTask'])}</p>
    <p><strong>Connect it to your project:</strong> {escape(lab['transfer'])}</p>
  </details>
  <p class="reading"><strong>Read alongside:</strong> {reading}</p>
</article>''')
        sections.append(f'''<section class="phase-section" id="phase-{escape(phase['id'])}" data-phase-section="{escape(phase['id'])}" aria-labelledby="heading-{escape(phase['id'])}">
  <h2 class="phase-heading" id="heading-{escape(phase['id'])}">Phase {escape(phase['id'])} — {escape(phase['title'])}</h2>
  <p class="phase-intro">{escape(phase['objective'])}</p>
  {''.join(cards)}
</section>''')
    source = f'''<!doctype html>
<!-- Generated from assets/lab-registry.json by scripts/build_catalog.py. -->
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<meta name="description" content="A curriculum of 25 guided builds and debugging challenges for learning reinforcement learning, with browser experiments and local Python practice.">
<title>RL Lab Curriculum — Prerequisites</title>
<link rel="stylesheet" href="../assets/style.css">
<link rel="stylesheet" href="assets/labs.css?v=m7">
<script type="module" src="assets/catalog.js"></script>
</head>
<body>
<a class="skip-link" href="#main">Skip to curriculum</a>
<div class="shell">
  <nav class="sidebar" aria-label="Curriculum navigation">
    <a class="brand" href="../index.html"><span class="kicker">F1 Strategy Agent</span><span class="title">RL Lab Curriculum</span></a>
    <ul class="nav-list"><li><a href="../index.html"><span class="n">←</span><span>Prerequisite reading</span></a></li>{nav}</ul>
    <div class="sidebar-foot">Browser experiments.<br>Python on your machine.</div>
  </nav>
  <main id="main">
    <div class="doc">
      <p class="eyebrow">Learn by investigating</p>
      <h1>Understand RL by building and debugging it.</h1>
      <p class="dek">Start with a small question. Predict what the code will do, inspect the evidence, then learn the idea and implement it yourself.</p>
      <div class="catalog-summary"><span>{str(ready_count)+' ready labs' if not planned_count else str(ready_count)+' ready · '+str(planned_count)+' planned labs'}</span><span>7 prerequisite phases</span><span>Python experience → RL foundations</span></div>
      <div class="note generic"><div class="tag">Start investigating</div><p>Open a lab to experiment in the browser and download its local Python exercise. Hints and solutions appear only when you request them.</p></div>
      <h2>Choose a learning path</h2>
      <p>Start at Phase 1 and follow each lab’s “Builds on” links. These show the concepts you actually need, rather than requiring every earlier phase. Phase 9 branches from value learning; self-play in Phase 8 is optional for PPO.</p>
      <p>Tiny chains, bandits, and games keep the focus on RL mechanics. Each lab connects what you learn to your project. The time estimates describe one core session; optional training and library stages run separately on your machine.</p>
      <form class="catalog-controls" id="catalog-controls" hidden>
        <label for="phase-filter">Phase<select id="phase-filter"><option value="all">All phases</option>{options}</select></label>
        <label for="mode-filter">Activity<select id="mode-filter"><option value="all">Both activities</option><option value="build">Guided builds</option><option value="debug">Debugging challenges</option></select></label>
        <p class="filter-count" id="filter-count" role="status" aria-live="polite"></p>
      </form>
      <p id="empty-results" hidden>No labs match these filters. Try another phase or activity.</p>
      {''.join(sections)}
      <p class="catalog-footer">Nothing to install for browser investigations. Download the Python packs to implement and check the concepts on your machine. Progress stays in this browser; export it from any lab to keep a copy.</p>
    </div>
  </main>
</div>
</body>
</html>
'''
    # The catalog is a reference view; the course registry owns the learning order.
    from build_course import navigation
    source = re.sub(r'[ \t]*<nav\b.*?</nav>', navigation('labs/index.html'), source, count=1, flags=re.S)
    source = source.replace('class="shell"', 'class="course-reference"')
    source = source.replace('</head>', '<link rel="stylesheet" href="../assets/course.css">\n<script type="module" src="../assets/course-navigation.js"></script>\n</head>')
    source = source.replace('RL Lab Curriculum — Prerequisites', 'Lab reference catalog — RL course')
    source = source.replace('Understand RL by building and debugging it.', 'Lab reference catalog')
    source = source.replace('Start with a small question. Predict what the code will do, inspect the evidence, then learn the idea and implement it yourself.', 'Browse experiments and Python exercises by topic. Use the course roadmap for the guided theory → browser → Python sequence.')
    source = re.sub(r'<div class="note generic"><div class="tag">Start investigating</div>.*?</div>', '<p><a class="course-primary" href="../roadmap.html">Course roadmap</a> · <a href="../library.html">Reference library</a></p>', source, flags=re.S)
    source = re.sub(r'<h2>Choose a learning path</h2>\s*<p>.*?</p>', '<h2>Browse lab references</h2><p>Open a lesson guide for its ordered theory assignments and project checkpoint. Self-play is optional preparation for PPO.</p>', source, flags=re.S)
    for lab in data['labs']:
        source = source.replace(f'<a class="start-lab" href="{escape(lab["route"])}">Open lab</a>', f'<a href="../lessons/{escape(lab["id"])}.html">Open lesson</a> · <a class="start-lab" href="{escape(lab["route"])}">Open lab reference</a>')
    from course_assets import version_assets
    return version_assets(source)


def specifications(data):
    lines = ["# RL lab author specifications", "", 
             "**Author reference: contains acceptance answers and planted-bug descriptions.**",
             "Do not embed these answers in the learner catalog or reveal them as automatic hints.", "",
             "Canonical source: `assets/lab-registry.json`. This document is generated; edit the registry.", "",
             "Lesson delivery status is recorded per lab in the registry. Models below are implementation contracts.", "",
             "## Shared scaffolding and boundaries", "",
             "Supply environment code, fixtures, plotting, CLI parsing, and local check harnesses; the learner implements one focused RL component at a time.",
             "Python familiarity is assumed; introduce probability, sums, vectors, tensors, derivatives, and new library APIs where first needed.",
             "A model that describes a dataset or update batch is explicitly not an interactive MDP.",
             "Stop collection on termination or truncation. For continuing-task time limits, bootstrap from the final observation; cut the advantage recursion across resets.",
             "Introduce math symbols next to their first use. New concepts are taught in the lab or linked reading, not silently assumed.", "",
             "## Toy models", ""]
    for key, model in data["models"].items():
        lines.extend([f"### {key}", ""])
        lines.extend(f"- **{field.title()}:** {value}" for field, value in model.items())
        lines.append("")
    for phase in data["phases"]:
        lines.extend([f"## Phase {phase['id']} — {phase['title']}", "",
                      f"Local implementation plan: `.antigravity/plans/{phase['plan']}`.", ""])
        for lab in [entry for entry in data["labs"] if entry["phase"] == phase["id"]]:
            lines.extend([f"### {lab['id']} — {lab['title']}", "",
                          f"- **Mode / milestone / status:** {lab['mode']} / {lab['milestone']} / {lab['status']}.",
                          f"- **Prerequisite labs:** {', '.join(lab['prerequisites']) or 'None; start here.'}",
                          f"- **Assumed background:** {'; '.join(lab['background'])}.",
                          f"- **Local packages:** {', '.join(lab['dependencies']) or 'Python standard library only'}.",
                          f"- **Model:** `{lab['model']}` (full specification above).",
                          f"- **Objective:** {lab['objective']}",
                          f"- **Primary misconception:** {lab['misconception']}",
                          f"- **Browser investigation:** {lab['browser']}",
                          f"- **Local implementation:** {lab['localTask']}",
                          f"- **Plan sections:** {'; '.join(lab['planSections'])}.",
                          f"- **Audit sections:** {', '.join(lab['audit']) or 'No direct audit bug; conceptual foundation.'}",
                          f"- **Lesson URL:** `{lab['route']}` ({lab['status']}; link only when ready).", "",
                          "Acceptance examples and evidence:", ""])
            lines.extend(f"{index}. {example}" for index, example in enumerate(lab["acceptance"], 1))
            lines.extend(["", "Existing reference pages:", ""])
            lines.extend(f"- [{title_for(SITE / path)}](../{path})" for path in lab["references"])
            lines.extend(["", f"Transfer question: {lab['transfer']}", ""])
    return '\n'.join(lines) + '\n'


class Links(HTMLParser):
    def __init__(self):
        super().__init__()
        self.links = []

    def handle_starttag(self, tag, attrs):
        if tag == "a":
            self.links.extend(value for key, value in attrs if key == "href" and value)


def source_inventory(data):
    mapped = defaultdict(list)
    for lab in data["labs"]:
        for path in lab["references"]:
            mapped[path].append(lab["id"])
    lines = ["# Existing prerequisite inventory", "",
             "Generated by `scripts/build_catalog.py` from actual files and registry mappings.",
             "A page without a direct lab mapping remains useful reference material; it is not missing curriculum.", "",
             "| Phase | Existing HTML pages (including index) | Labs |", "|---|---:|---:|"]
    pages = []
    for phase in data["phases"]:
        phase_pages = sorted((SITE / phase["readingDirectory"]).glob("*.html"))
        lines.append(f"| {phase['id']} | {len(phase_pages)} | {sum(lab['phase'] == phase['id'] for lab in data['labs'])} |")
        pages.extend(phase_pages)
    lines.extend(["", "## Page coverage", "", "| Actual page | Title | Direct lab mappings |", "|---|---|---|"])
    missing = defaultdict(set)
    for page in pages:
        relative = page.relative_to(SITE).as_posix()
        title = title_for(page).replace('|', '\\|')
        lines.append(f"| `{relative}` | {title} | {', '.join(mapped[relative]) or 'Reference / navigation'} |")
        parser = Links()
        parser.feed(page.read_text(encoding="utf-8"))
        for href in parser.links:
            url = urlsplit(href)
            if url.scheme or url.netloc or not url.path:
                continue
            target = (page.parent / unquote(url.path)).resolve()
            if not target.exists():
                missing[target.relative_to(SITE).as_posix()].add(relative)
    lines.extend(["", "## Pre-existing broken reading links", "",
                  "These are source-material gaps discovered during M0. The new catalog links only to existing pages.",
                  "Repair or author the missing reading during its relevant milestone; do not pretend the files exist.", ""])
    if missing:
        lines.extend(f"- `{target}` — linked from {len(origins)} existing page(s)." for target, origins in sorted(missing.items()))
    else:
        lines.append("None found.")
    lines.extend(["", "See `CONTENT_REVIEW.md` for theory corrections and milestone ownership.", ""])
    return '\n'.join(lines)


def outputs(data):
    from build_readings import render_outputs
    return {LABS/'index.html':render_outputs()[1]['labs/index.html'],
            DOCS/'AUTHOR_SPECIFICATIONS.md':specifications(data)}

def retired_outputs(data):
    return {LABS / "index.html": catalog(data), DOCS / "AUTHOR_SPECIFICATIONS.md": specifications(data),
            DOCS / "SOURCE_INVENTORY.md": source_inventory(data)}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--write", action="store_true", help="Regenerate checked-in catalog and author documents")
    args = parser.parse_args()
    stale = []
    for path, content in outputs(load_registry()).items():
        if args.write:
            path.write_text(content, encoding="utf-8", newline="\n")
        elif not path.exists() or path.read_text(encoding="utf-8") != content:
            stale.append(path.relative_to(ROOT).as_posix())
    if stale:
        raise SystemExit("Generated files are stale: " + ', '.join(stale) + ". Run with --write.")
    print("Catalog and author documents " + ("generated." if args.write else "are current."))


if __name__ == "__main__":
    main()
