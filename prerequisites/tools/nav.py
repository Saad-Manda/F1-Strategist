"""Navigation tooling for the prerequisites site (prerequisites/site).

    python tools/nav.py check     validate manifest, pages and links (permanent guard)
    python tools/nav.py style     the redesign's style warnings for rewritten pages (word counts,
                                  cold opens, early interactives, banned words); add a path to
                                  count any page or the pages of a git revision: style HEAD
    python tools/nav.py hub       regenerate index.html's course map from the manifest
    python tools/nav.py migrate   one-time conversion from the old per-phase layout

Run from the prerequisites/ folder. The manifest, site/assets/course.js, is the single source of truth for the
course structure. Its body is pure JSON wrapped in ``window.COURSE = ...;`` so that pages can
load it with a plain <script> tag from file:// and this script can still parse it.
"""

from __future__ import annotations

import html
import json
import re
import shutil
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / "site"
MANIFEST = ROOT / "assets" / "course.js"
SITE = "F1 Prereqs"

FONTS = (
    "https://fonts.googleapis.com/css2?family=Sora:wght@500;600;700&family=Source+Serif+4:"
    "ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&family=IBM+Plex+Mono:wght@400;500&display=swap"
)

# id, folder, short name used in the sidebar and breadcrumb, phases assumed
PHASES = [
    ("1", "phase-1-rl-prerequisites", "RL fundamentals", []),
    ("3.5", "phase-3.5-dp-oracle-prerequisites", "DP oracle", ["1"]),
    ("4", "phase-4-q-learning-prerequisites", "Q-learning", ["1", "3.5"]),
    ("5", "phase-5-dqn-prerequisites", "DQN", ["1", "3.5", "4"]),
    ("6", "phase-6-multi-car-prerequisites", "Multi-car", ["1", "3.5", "4", "5"]),
    ("8", "phase-8-self-play-prerequisites", "Self-play", ["1", "3.5", "4", "5", "6"]),
    ("9", "phase-9-ppo-prerequisites", "PPO", ["1", "3.5", "4", "5", "6", "8"]),
]

# page number each phase's glossary had before the glossaries were merged
OLD_GLOSSARY_PAGE = {"1": 8, "3.5": 8, "4": 10, "5": 12, "6": 11, "8": 11, "9": 12}

GROUP_LABEL = {"start": "", "concepts": "Concepts", "capstone": "Capstone", "project": "This project"}


# --------------------------------------------------------------------------- manifest


def load_manifest() -> dict:
    text = MANIFEST.read_text(encoding="utf-8")
    body = text[text.index("{") : text.rindex("}") + 1]
    return json.loads(body)


def save_manifest(course: dict) -> None:
    MANIFEST.write_text(
        "// Course manifest: the single source of truth for navigation. The value is pure JSON.\n"
        "window.COURSE = " + json.dumps(course, indent=2, ensure_ascii=False) + ";\n",
        encoding="utf-8",
        newline="\n",
    )


def find_page(course: dict, phase_id: str, number: int):
    for ph in course["phases"]:
        if ph["id"] == phase_id:
            for p in ph["pages"]:
                if int(p["n"]) == number:
                    return ph, p
    return None


def page_title(ph: dict, p: dict) -> str:
    return f'{p["n"]} · {p["title"]} — Phase {ph["id"]} {ph["short"]} · {SITE}'


def text_of(fragment: str) -> str:
    return html.unescape(re.sub(r"<[^>]+>", "", fragment)).strip()


# --------------------------------------------------------------------------- shared markup


def scripts(root: str, extra: str = "") -> str:
    out = "".join(f'<script src="{root}assets/{name}"></script>\n' for name in ("course.js", "progress.js", "nav.js"))
    return out + extra


def sidebar_placeholder(root: str) -> str:
    return (
        '<nav class="sidebar" id="sidebar">\n'
        f'    <noscript><a class="brand" href="{root}index.html"><span class="kicker">F1 Strategy Agent</span>'
        '<span class="title">Prerequisites — course map</span></a></noscript>\n'
        "  </nav>"
    )


def standalone_page(title: str, data_page: str, body: str, extra_scripts: str = "") -> str:
    return f"""<!doctype html>
<html lang="en">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>{title}</title>
<link rel="stylesheet" href="{FONTS}">
<link rel="stylesheet" href="assets/style.css">
</head>
<body data-page="{data_page}">
<div class="shell">
  {sidebar_placeholder("")}
  <main>
    <div class="doc">
{body}
    </div>
  </main>
</div>
{scripts("", extra_scripts)}</body>
</html>
"""


# --------------------------------------------------------------------------- cross-reference linking

NUM = r"\d{1,2}(?!\d)"
SEP = r"(?:\s*[–-]\s*|,\s*(?:and\s+|&amp;\s*)?|\s+and\s+|\s*&amp;\s*)"
LIST = rf"(?:{SEP}{NUM})*"
XREF = re.compile(
    rf"(?P<a>Phase (?P<a_ph>\d(?:\.\d)?)(?:'s|’s)?(?: own| prerequisites'| prerequisites’| set's)? (?P<a_w>pages?) (?P<a_n>{NUM}{LIST}))"
    rf"|(?P<b>(?P<b_w>[Pp]ages?) (?P<b_n>{NUM}{LIST}) of the Phase (?P<b_ph>\d(?:\.\d)?) (?:prerequisites|prerequisite set|set))"
    rf"|(?P<c>\b(?P<c_w>[Pp]ages?) (?P<c_n>{NUM}{LIST}))"
)
SKIP_TAGS = {"a", "pre", "h1", "h2", "h3", "title", "script", "style", "summary"}


class Linker:
    """Turns "Phase 1 page 3" / "pages 5 & 6" text into links, and records what it did."""

    def __init__(self, course: dict):
        self.course = course
        self.linked: list[tuple[str, str, str]] = []
        self.unresolved: list[tuple[str, str, str]] = []

    def target(self, here_phase: str | None, phase_id: str, number: int) -> str | None:
        """href relative to a page in `here_phase` (None = a page at the site root)."""
        up = "" if here_phase is None else "../"
        if OLD_GLOSSARY_PAGE.get(phase_id) == number and find_page(self.course, phase_id, number) is None:
            return f"{up}glossary.html#phase-{phase_id}"
        hit = find_page(self.course, phase_id, number)
        if hit is None:
            return None
        ph, p = hit
        if here_phase == phase_id:
            return p["file"]
        return f'{up}{ph["slug"]}/{p["file"]}'

    def link_text(self, text: str, here_phase: str | None, default_phase: str, where: str) -> str:
        def repl(m: re.Match) -> str:
            kind = "a" if m.group("a") else "b" if m.group("b") else "c"
            whole = m.group(kind)
            phase_id = m.group(f"{kind}_ph") if kind != "c" else default_phase
            word, numbers = m.group(f"{kind}_w"), m.group(f"{kind}_n")
            start = m.start(f"{kind}_n") - m.start(kind)
            head, tail = whole[:start], whole[start + len(numbers) :]
            if not word.endswith("s"):  # singular "page 3 and 4 laps": only the first number is a page
                first = re.match(NUM, numbers).group(0)
                numbers, tail = first, numbers[len(first) :] + tail
            out, pos = [], 0
            for i, nm in enumerate(re.finditer(NUM, numbers)):
                href = self.target(here_phase, phase_id, int(nm.group(0)))
                if i == 0:  # the first link carries the "Phase 1 page " lead-in
                    lead, label = "", head + numbers[: nm.end()]
                else:
                    lead, label = numbers[pos : nm.start()], nm.group(0)
                if href:
                    out.append(f'{lead}<a class="xref" href="{href}">{label}</a>')
                    self.linked.append((where, whole, href))
                else:
                    out.append(lead + label)
                    self.unresolved.append((where, whole, f"Phase {phase_id} page {nm.group(0)}"))
                pos = nm.end()
            return "".join(out) + tail

        return XREF.sub(repl, text)

    def link_html(self, fragment: str, here_phase: str | None, default_phase: str, where: str) -> str:
        parts = re.split(r"(<[^>]+>)", fragment)
        skip: list[str] = []
        for i, part in enumerate(parts):
            if part.startswith("<"):
                m = re.match(r"<(/?)([a-zA-Z0-9]+)", part)
                if not m:
                    continue
                closing, name = m.group(1), m.group(2).lower()
                eyebrow = name == "p" and 'class="eyebrow"' in part
                if closing:
                    if skip and skip[-1] == name:
                        skip.pop()
                elif name in SKIP_TAGS or eyebrow:
                    skip.append(name)
            elif not skip and "age" in part:
                parts[i] = self.link_text(part, here_phase, default_phase, where)
        return "".join(parts)


# --------------------------------------------------------------------------- hub


# case titles for rounds not rebuilt yet (redesign plan, section 4); a phase's own "case" in the
# manifest replaces its entry here once that round is rebuilt
UPCOMING_CASES = {
}


def render_hub(course: dict) -> str:
    rows = []
    for ph in course["phases"]:
        assumes = (
            "Assumes: <strong>" + ", ".join("Phase " + a for a in ph["assumes"]) + "</strong>"
            if ph["assumes"]
            else "Assumes: <strong>nothing</strong> — start here"
        )
        items = []
        for p in ph["pages"]:
            grp = GROUP_LABEL.get(p["group"], "")
            extra = ""
            if p.get("blurb"):
                extra += f'<p class="covers">{html.escape(p["blurb"])}</p>'
            if p.get("why"):
                extra += f'<p class="why">{html.escape(p["why"])}</p>'
            items.append(
                f'            <li><span class="n">{p["n"]}</span><div>'
                f'<a class="pt" data-page-link="{ph["id"]}/{p["n"]}" href="{ph["slug"]}/{p["file"]}">{html.escape(p["title"])}</a>'
                + (f'<span class="grp-label">{grp}</span>' if grp else "")
                + f"{extra}</div></li>"
            )
        note = f'\n          <p class="desc"><strong>{html.escape(ph["status"])}</strong></p>' if ph.get("status") else ""
        rows.append(
            f"""        <details class="phase-row" data-phase="{ph["id"]}">
          <summary>
            <span class="num">{ph["id"]}</span>
            <span class="name">{html.escape(ph["title"])}</span>
            <span class="counts" data-phase-count="{ph["id"]}">{len(ph["pages"])} pages</span>
            <p class="desc">{ph["desc"]}</p>{note}
            <div class="chain">{assumes}</div>
          </summary>
          <div class="phase-body">
            <a class="start" href="{ph["slug"]}/{ph["pages"][0]["file"]}">Open Phase {ph["id"]} overview →</a>
            <ul class="page-map">
{chr(10).join(items)}
            </ul>
          </div>
        </details>"""
        )
    total = sum(len(ph["pages"]) for ph in course["phases"])
    rounds = []
    for i, ph in enumerate(course["phases"], 1):
        case = ph.get("case") or {"title": UPCOMING_CASES.get(ph["id"], "")}
        label = "Case " + str(i) if ph.get("case") else "case to come"
        rounds.append(
            f'        <a class="round" href="{ph["slug"]}/{ph["pages"][0]["file"]}">'
            f'<span class="r-n">R{i} · Phase {ph["id"]}</span>'
            f'<span class="r-name">{html.escape(ph["short"])}</span>'
            f'<span class="r-case">{label}: {html.escape(case["title"])}</span>'
            f'<span class="r-pts" data-round-pts="{ph["id"]}">{len(ph["pages"])} pages</span>'
            f'<span class="r-bar"><i style="width:0%"></i></span></a>'
        )
    body = f"""      <p class="eyebrow">Course map</p>
      <h1>Prerequisites</h1>
      <p class="dek">Seven rounds, {total} pages, one season. Each round is a phase of the project with a case to crack; each page earns points. Nothing is locked: the points only keep score.</p>

      <div class="standings" id="standings"></div>
      <div class="season">
{chr(10).join(rounds)}
      </div>

      <div id="resume"><noscript><p><a class="inline-link" href="{course["phases"][0]["slug"]}/{course["phases"][0]["pages"][0]["file"]}">Start: Phase 1 · Overview →</a></p></noscript></div>

      <div class="pw-panel">
        <div class="pw-kicker"><b>The Pit Wall</b><span>a 20-lap toy race you call lap by lap</span></div>
        <p style="margin:0 0 10px">Call a race against an oracle that plays it perfectly on average, then open it as an MDP. Phase 1 opens Race mode; each later round adds a mode.</p>
        <a class="pw-btn go" href="pitwall.html" style="text-decoration:none;display:inline-block">Open the Pit Wall</a>
      </div>

      <h2>Course map</h2>
      <p>Open a phase to see its pages, what each one covers, and why that phase needs it.</p>
      <div class="phase-grid">
{chr(10).join(rows)}
      </div>

      <h2>How the course works</h2>
      <p>The sets are cumulative: each assumes every set above it and nothing later. Read top to bottom on a first pass, and jump straight to a phase only once the sets it lists under "Assumes" are behind you.</p>
      <p>Every set has the same three parts, marked in the sidebar. <strong>Concepts</strong> build one continuous argument and are read in order, with the F1 examples inside them as illustration. <strong>Capstone</strong> is the hands-on page: you build a small toy version of the phase's technique yourself, one complication at a time, under names that deliberately do not match the real project. <strong>This project</strong> then maps the same ideas onto the real design and gives a reading guide to the phase's implementation plan. Terms from every set are collected in the <a class="inline-link" href="glossary.html">glossary</a>.</p>
      <p><strong>Labs.</strong> Where a set has labs, every page ends in one: a hand calculation or quiz checked in the page, or a notebook or code exercise in <code>prerequisites/labs/</code>, opened and checked with <code>python -m labs</code> from inside the <code>prerequisites/</code> folder (see <code>prerequisites/README.md</code>). The capstone page is the brief for a longer staged build. Every set has labs.</p>
      <p><strong>Points.</strong> A page read is 1 point, a cold-open call 1, an in-page lab 3, a code lab 5, a capstone 10, a case closed 10, and a Pit Wall race within a second of the oracle 5 per mode. Every phase is built as a case: a mystery opened on its first page and closed on its last.</p>
      <p>The sidebar marks a page as opened when you visit it and as finished when you reach its end, and ticks in-page labs as you complete them. That record lives in this browser only. Code labs are ticked by running <code>python -m labs status</code> and reloading.</p>

      <h2>Where things stand</h2>
      <div class="note grounded">
        <div class="tag">Read before relying on these pages</div>
        <p><strong>Only Phase 0 of the project is implemented.</strong> Every phase's "Back to the plan" page is a reading guide to files that are planned, not yet present in <code>src/</code>.</p>
      </div>
      <div class="note generic">
        <div class="tag">Not covered yet</div>
        <p>Phases 2, 7, and any phase after 9 have no prerequisite set here. A new set is a new phase folder plus one entry in <code>assets/course.js</code>.</p>
      </div>

      <p><button class="reset-btn" id="reset-progress" type="button">Reset reading progress</button></p>"""
    return standalone_page(f"Course map · {SITE}", "hub", body)


# --------------------------------------------------------------------------- one-time migration

ALIASES = {
    "action masking": "action mask",
    "reward hacking / proxy optimization": "reward hacking",
    "non-stationarity (multi-agent case)": "non-stationarity",
    "blocking constraint / track position as a resource": "blocking constraint",
}

# small text repairs that navigation depends on (nav plan, Appendix A): (file, old, new)
TEXT_FIXES = [
    ("phase-3.5-dp-oracle-prerequisites/index.html", "second correlated random process", "second, independent random process"),
    (
        "phase-3.5-dp-oracle-prerequisites/07-code-walkthrough.html",
        "the same justification page 6's Phase 1 prerequisite page gave for the live environment",
        "the same justification Phase 1 pages 2 and 3 gave for the live environment",
    ),
    ("phase-1-rl-prerequisites/08-glossary.html", "See pages 2 &amp; 5.", "See pages 2 &amp; 6."),
]


def group_of(filename: str) -> str:
    if filename.startswith("00-"):
        return "start"
    if re.search(r"build-it-yourself|building-the-environment|build-a-toy-solver", filename):
        return "capstone"
    if re.search(r"formalized|this-project|code-walkthrough|reading-the-plan", filename):
        return "project"
    return "concepts"


def bootstrap_manifest() -> dict:
    hub = (ROOT / "index.html").read_text(encoding="utf-8")
    cards = {}
    for m in re.finditer(
        r'<a class="phase-card" href="([^/"]+)/index\.html">.*?<span class="name">(.*?)</span>.*?<p class="desc">(.*?)</p>',
        hub,
        re.S,
    ):
        cards[m.group(1)] = (text_of(m.group(2)), m.group(3).strip())

    phases = []
    for pid, slug, short, assumes in PHASES:
        index = (ROOT / slug / "index.html").read_text(encoding="utf-8")
        rows = {}
        for m in re.finditer(r'<tr><td class="mono">(\d+)</td><td>.*?</td><td>(.*?)</td><td>(.*?)</td></tr>', index, re.S):
            rows[m.group(1)] = (text_of(m.group(2)), text_of(m.group(3)))
        pages = [{"n": "00", "file": "00-overview.html", "title": "Overview", "group": "start"}]
        nav = re.search(r'<ul class="nav-list">(.*?)</ul>', index, re.S).group(1)
        for m in re.finditer(r'<a[^>]*href="([^"]+)"><span class="n">(\d+)</span><span>(.*?)</span></a>', nav):
            file, n, label = m.group(1), m.group(2), text_of(m.group(3))
            if file == "index.html" or "glossary" in file or not (ROOT / slug / file).exists():
                continue
            page = {"n": n, "file": file, "title": label, "group": group_of(file)}
            if n in rows:
                page["blurb"], page["why"] = rows[n]
            pages.append(page)
        title, desc = cards[slug]
        phase = {"id": pid, "slug": slug, "short": short, "title": title, "desc": desc, "assumes": assumes, "pages": pages}
        phases.append(phase)
    return {"phases": phases}


def build_glossary(course: dict, linker: Linker) -> str:
    entries: dict[str, dict] = {}
    scopes = []
    for ph in course["phases"]:
        files = list((ROOT / ph["slug"]).glob("*-glossary.html"))
        if not files:
            continue
        src = files[0].read_text(encoding="utf-8")
        scope = re.search(r'<div class="tag">Scope note</div>\s*<p>(.*?)</p>', src, re.S)
        if scope:
            scopes.append((ph["id"], scope.group(1).strip()))
        for m in re.finditer(r"<div><dt>(.*?)</dt><dd>(.*?)</dd></div>", src, re.S):
            term, definition = m.group(1).strip(), m.group(2).strip()
            definition = linker.link_html(definition, None, ph["id"], f"glossary (Phase {ph['id']}: {text_of(term)})")
            key = text_of(term).lower()
            key = ALIASES.get(key, key)
            entry = entries.setdefault(key, {"term": term, "defs": []})
            entry["defs"].append((ph, term, definition))

    def sort_key(item):
        return re.sub(r"[^a-z0-9 ]", "", item[0].replace("ε", "epsilon"))

    used, blocks = set(), []
    for key, entry in sorted(entries.items(), key=sort_key):
        slug = re.sub(r"[^a-z0-9]+", "-", key.replace("ε", "epsilon").replace("λ", "lambda")).strip("-") or "term"
        while slug in used:
            slug += "-x"
        used.add(slug)
        phases = " ".join(ph["id"] for ph, _, _ in entry["defs"])
        tags = "".join(
            f'<a class="g-tag" href="{ph["slug"]}/{ph["pages"][0]["file"]}">Phase {ph["id"]}</a>' for ph, _, _ in entry["defs"]
        )
        first_ph, _, first_def = entry["defs"][0]
        dds = [f"<dd>{first_def}</dd>"]
        for ph, term, definition in entry["defs"][1:]:
            named = "" if text_of(term).lower() == text_of(entry["term"]).lower() else f" (as “{term}”)"
            dds.append(f'<dd class="g-refined"><span class="g-label">Refined in Phase {ph["id"]}{named}</span>{definition}</dd>')
        blocks.append(
            f'        <div class="g-entry" id="term-{slug}" data-phases="{phases}"><dt>{entry["term"]} '
            f'<span class="g-tags">{tags}</span></dt>{"".join(dds)}</div>'
        )

    with_terms = [ph["id"] for ph in course["phases"] if any(ph["id"] in b.split('data-phases="')[1].split('"')[0].split() for b in blocks)]
    chips = '<button class="g-chip on" type="button" data-phase="">All phases</button>' + "".join(
        f'<button class="g-chip" type="button" data-phase="{pid}">Phase {pid}</button>' for pid in with_terms
    )
    scope_html = "\n".join(
        f'      <div class="note generic g-scope" data-phase="{pid}"><div class="tag">Phase {pid} scope note</div><p>{text}</p></div>'
        for pid, text in scopes
    )
    body = f"""      <p class="eyebrow">Reference</p>
      <h1>Glossary</h1>
      <p class="dek">Every term from every prerequisite set, in one list. Each entry is tagged with the phase that introduces it; where a later phase sharpens a definition, that refinement sits under the original.</p>

      <div class="g-tools">
        <input class="g-search" id="g-search" type="search" placeholder="Search terms and definitions" aria-label="Search the glossary">
        <div class="g-chips">{chips}</div>
        <div class="g-count" id="g-count"></div>
      </div>

{scope_html}

      <dl class="glossary">
{chr(10).join(blocks)}
      </dl>"""
    return standalone_page(f"Glossary · {SITE}", "glossary", body, '<script src="assets/glossary.js"></script>\n')


def convert_page(src: str, ph: dict, p: dict, last_n: str, linker: Linker) -> str:
    where = f'{ph["slug"]}/{p["file"]}'
    out = src

    def sub_once(pattern: str, repl: str, text: str, flags=0) -> str:
        new, n = re.subn(pattern, lambda _m: repl, text, count=1, flags=flags)
        if n != 1:
            raise SystemExit(f"{where}: expected exactly one match for {pattern!r}")
        return new

    out = sub_once(r"<title>.*?</title>", f"<title>{html.escape(page_title(ph, p), quote=False)}</title>", out, re.S)
    out = sub_once(r'href="assets/style\.css"', 'href="../assets/style.css"', out)
    out = sub_once(r"<body>", f'<body data-page="{ph["id"]}/{p["n"]}">', out)
    out = sub_once(r'<nav class="sidebar">.*?</nav>', sidebar_placeholder("../"), out, re.S)
    out = sub_once(
        r'<div class="pagenav">.*?</div>',
        '<div class="pagenav" id="pagenav"></div>\n'
        '      <noscript><p><a class="inline-link" href="../index.html">Back to the course map</a></p></noscript>',
        out,
        re.S,
    )
    out = sub_once(r"</body>", scripts("../") + "</body>", out)

    if p["n"] == "00":
        out = sub_once(r'(<p class="eyebrow">).*?(</p>)', f'<p class="eyebrow">Phase {ph["id"]} · Overview</p>', out, re.S)
        for heading in ("Reading order", "How this folder teaches the implementation half", "How to use this alongside the Phase"):
            out = re.sub(rf'\s*<h2>{re.escape(heading)}[^<]*</h2>.*?(?=\n\s*<h2>|\n\s*<div class="pagenav")', "", out, flags=re.S)
    else:
        out = sub_once(
            r'<p class="eyebrow">Page (\d+) / \d+ — ',
            f'<p class="eyebrow">Phase {ph["id"]} · Page {p["n"]} of {last_n} — ',
            out,
        )

    # a raw "<" followed by a space, "=" or a digit is never a tag: it is code or maths
    out = re.sub(r"<(?=[\s=\d])", "&lt;", out)

    a, b = out.index('<div class="doc">'), out.index('<div class="pagenav"')
    out = out[:a] + linker.link_html(out[a:b], ph["id"], ph["id"], where) + out[b:]
    return out


def migrate() -> None:
    if any(ROOT.glob("phase-*/00-overview.html")):
        raise SystemExit("already migrated: 00-overview.html exists. Use `check` or `hub`.")

    for rel, old, new in TEXT_FIXES:
        path = ROOT / rel
        text = path.read_text(encoding="utf-8")
        if old not in text:
            raise SystemExit(f"{rel}: text fix target not found: {old!r}")
        path.write_text(text.replace(old, new), encoding="utf-8", newline="\n")

    course = bootstrap_manifest()
    linker = Linker(course)

    glossary_html = build_glossary(course, linker)

    for ph in course["phases"]:
        folder = ROOT / ph["slug"]
        last_n = ph["pages"][-1]["n"]
        for p in ph["pages"]:
            source = folder / ("index.html" if p["n"] == "00" else p["file"])
            converted = convert_page(source.read_text(encoding="utf-8"), ph, p, last_n, linker)
            (folder / p["file"]).write_text(converted, encoding="utf-8", newline="\n")
        (folder / "index.html").unlink()
        for old in folder.glob("*-glossary.html"):
            old.unlink()
        shutil.rmtree(folder / "assets")

    save_manifest(course)
    (ROOT / "assets" / "progress.js").write_text(
        "// Lab pass state. Regenerated by the lab tracker; this stub keeps pages working before any lab exists.\n"
        "window.LAB_PROGRESS = {};\n",
        encoding="utf-8",
        newline="\n",
    )
    (ROOT / "glossary.html").write_text(glossary_html, encoding="utf-8", newline="\n")
    (ROOT / "index.html").write_text(render_hub(course), encoding="utf-8", newline="\n")

    report = Path(__file__).resolve().parent / "xref_report.txt"
    lines = [f"LINKED {len(linker.linked)}", *(f"  {w} | {t} -> {h}" for w, t, h in linker.linked)]
    lines += [f"UNRESOLVED {len(linker.unresolved)}", *(f"  {w} | {t} | missing: {h}" for w, t, h in linker.unresolved)]
    report.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(f"migrated. linked {len(linker.linked)} references, {len(linker.unresolved)} unresolved. Report: {report}")


# --------------------------------------------------------------------------- check


REDIRECTS = {
    "phase-1-rl-prerequisites/06-this-project-as-mdp.html": "06-back-to-the-plan.html",
    "phase-1-rl-prerequisites/07-code-walkthrough.html": "06-back-to-the-plan.html",
    "phase-3.5-dp-oracle-prerequisites/06-this-project-as-dp.html": "06-back-to-the-plan.html",
    "phase-3.5-dp-oracle-prerequisites/07-code-walkthrough.html": "06-back-to-the-plan.html",
    "phase-4-q-learning-prerequisites/08-this-project-formalized.html": "08-back-to-the-plan.html",
    "phase-4-q-learning-prerequisites/09-code-walkthrough.html": "08-back-to-the-plan.html",
    "phase-5-dqn-prerequisites/10-this-project-formalized.html": "10-back-to-the-plan.html",
    "phase-5-dqn-prerequisites/11-code-walkthrough.html": "10-back-to-the-plan.html",
    "phase-6-multi-car-prerequisites/09-this-project-formalized.html": "09-back-to-the-plan.html",
    "phase-6-multi-car-prerequisites/10-reading-the-plan.html": "09-back-to-the-plan.html",
    "phase-8-self-play-prerequisites/09-this-project-formalized.html": "09-back-to-the-plan.html",
    "phase-8-self-play-prerequisites/10-reading-the-plan.html": "09-back-to-the-plan.html",
    "phase-9-ppo-prerequisites/10-this-project-formalized.html": "10-back-to-the-plan.html",
    "phase-9-ppo-prerequisites/11-reading-the-plan.html": "10-back-to-the-plan.html",
}


def check() -> int:
    course = load_manifest()
    errors: list[str] = []
    listed = {"index.html", "glossary.html", "pitwall.html"}
    # old URLs kept as redirect stubs after pages were merged: (file, where it now points)
    for rel, target in REDIRECTS.items():
        listed.add(rel)
        path = ROOT / rel
        if path.exists() and f'url={target}' not in path.read_text(encoding="utf-8"):
            errors.append(f"{rel}: redirect stub does not point to {target}")

    for ph in course["phases"]:
        numbers = [p["n"] for p in ph["pages"]]
        if numbers != sorted(numbers):
            errors.append(f'{ph["slug"]}: pages are not in numeric order')
        for p in ph["pages"]:
            rel = f'{ph["slug"]}/{p["file"]}'
            listed.add(rel)
            path = ROOT / rel
            if not path.exists():
                errors.append(f"{rel}: in the manifest but missing on disk")
                continue
            text = path.read_text(encoding="utf-8")
            if not p["file"].startswith(p["n"] + "-"):
                errors.append(f'{rel}: file name does not start with its page number {p["n"]}')
            want = html.escape(page_title(ph, p), quote=False)
            got = re.search(r"<title>(.*?)</title>", text, re.S)
            if not got or got.group(1) != want:
                errors.append(f"{rel}: <title> is not {want!r}")
            if f'data-page="{ph["id"]}/{p["n"]}"' not in text:
                errors.append(f"{rel}: missing or wrong data-page")
            if 'id="sidebar"' not in text or 'id="pagenav"' not in text:
                errors.append(f"{rel}: missing sidebar or pagenav placeholder")
            if '<ul class="nav-list">' in text:
                errors.append(f"{rel}: still contains a hardcoded sidebar")
            if "assets/nav.js" not in text or "assets/course.js" not in text:
                errors.append(f"{rel}: navigation scripts not loaded")
            lab = p.get("lab")
            if lab and f'data-lab-id="{lab["id"]}"' not in text:
                errors.append(f'{rel}: manifest lists lab {lab["id"]} but the page has no matching lab block')

    titles: dict[str, str] = {}
    for path in sorted(ROOT.rglob("*.html")):
        rel = path.relative_to(ROOT).as_posix()
        if rel not in listed:
            errors.append(f"{rel}: on disk but not in the manifest")
        text = path.read_text(encoding="utf-8")
        t = re.search(r"<title>(.*?)</title>", text, re.S)
        if t:
            if t.group(1) in titles:
                errors.append(f"{rel}: duplicate <title> (same as {titles[t.group(1)]})")
            titles[t.group(1)] = rel
        for href in re.findall(r'(?:href|src)="([^"]+)"', text):
            if re.match(r"(https?:|mailto:|#|data:)", href):
                continue
            target = (path.parent / href.split("#")[0]).resolve()
            if not target.exists():
                errors.append(f"{rel}: broken link {href}")

    for folder in ROOT.glob("phase-*"):
        if (folder / "assets").exists():
            errors.append(f"{folder.name}/assets: per-phase stylesheet copy should not exist")

    total = sum(len(ph["pages"]) for ph in course["phases"])
    for e in errors:
        print("ERROR", e)
    print(f'{len(course["phases"])} phases, {total} pages, {len(errors)} problem(s)')
    return 1 if errors else 0



# --------------------------------------------------------------------------- style (redesign plan, section 6 and 7.2)

BANNED = ["genuinely", "precisely", "exactly", "load-bearing", "crucially", "essentially", "notably",
          "in practice", "simply", "just"]
WORD_LIMIT, EARLY = 900, 400


def core_text(page_html: str) -> tuple[str, str]:
    """The core path of a page as plain text: the .doc body without the lab, collapsed boxes (deep dives,
    hints, snippets), code blocks and scripts. Also returns the text before the first interactive."""
    start = page_html.find('<div class="doc')
    body = page_html[start:] if start >= 0 else page_html
    body = body.split('<div class="pagenav"')[0]
    body = re.sub(r'<section class="lab".*?</section>', " ", body, flags=re.S)
    body = re.sub(r"<details\b.*?</details>", " ", body, flags=re.S)
    body = re.sub(r"<(pre|script|noscript)\b.*?</\1>", " ", body, flags=re.S)
    first = re.search(r'class="cold-open"|data-widget=', body)
    def plain(h):
        return html.unescape(re.sub(r"\s+", " ", re.sub(r"<[^>]+>", " ", h))).strip()
    return plain(body), plain(body[: first.start()]) if first else plain(body)


def words(text: str) -> int:
    return len(re.findall(r"[A-Za-z0-9][A-Za-z0-9'’.,−\-/]*", text))


def style(args: list[str]) -> int:
    course = load_manifest()
    if args and not args[0].endswith(".html"):  # a git revision: count that revision's pages
        import subprocess
        rev = args[0]
        for ph in course["phases"]:
            repo = ROOT.parents[1]
            listing = subprocess.run(["git", "ls-tree", "--name-only", rev, f"prerequisites/site/{ph['slug']}/"],
                                     capture_output=True, text=True, cwd=repo)
            total = 0
            for name in sorted(listing.stdout.split()):
                if not name.endswith(".html"):
                    continue
                src = subprocess.run(["git", "show", f"{rev}:{name}"],
                                     capture_output=True, text=True, encoding="utf-8", cwd=repo).stdout
                if 'http-equiv="refresh"' in src:
                    continue
                total += words(core_text(src)[0])
            print(f"{rev} Phase {ph['id']}: {total} core-path words")
        return 0
    warnings, totals = [], {}
    for ph in course["phases"]:
        for p in ph["pages"]:
            rel = f'{ph["slug"]}/{p["file"]}'
            if args and rel not in args:
                continue
            src = (ROOT / rel).read_text(encoding="utf-8")
            core, before = core_text(src)
            n = words(core)
            totals[ph["id"]] = totals.get(ph["id"], 0) + n
            if '<div class="doc v2' not in src:
                continue  # not rewritten yet: counted, not judged
            print(f"  {rel}: {n} core words, first interactive after {words(before)}")
            if n > WORD_LIMIT:
                warnings.append(f"{rel}: core path is {n} words (target {WORD_LIMIT})")
            if words(before) > EARLY:
                warnings.append(f"{rel}: first interactive after {words(before)} words (target {EARLY})")
            calls = re.findall(r'class="cold-open" data-call="([^"]+)"', src)
            if p.get("group") in ("concepts", "project"):
                if not calls:
                    warnings.append(f"{rel}: content page without a cold open")
                if p.get("call") and p["call"] not in calls:
                    warnings.append(f'{rel}: manifest call {p["call"]} not on the page')
            for c in calls:
                if f'class="reveal closed" data-for="{c}"' not in src and f'class="reveal" data-for="{c}"' not in src:
                    warnings.append(f"{rel}: cold open {c} has no reveal")
            low = core.lower()
            for w in BANNED:
                k = len(re.findall(r"\b" + re.escape(w) + r"\b", low))
                if k:
                    warnings.append(f"{rel}: banned word '{w}' x{k}")
    for pid, t in totals.items():
        print(f"Phase {pid}: {t} core-path words")
    for w in warnings:
        print("WARN", w)
    print(f"{len(warnings)} style warning(s)")
    return 0


def main() -> int:
    cmd = sys.argv[1] if len(sys.argv) > 1 else ""
    if cmd == "check":
        return check()
    if cmd == "style":
        return style(sys.argv[2:])
    if cmd == "hub":
        (ROOT / "index.html").write_text(render_hub(load_manifest()), encoding="utf-8", newline="\n")
        print("index.html regenerated")
        return 0
    if cmd == "migrate":
        migrate()
        return check()
    print(__doc__)
    return 2


if __name__ == "__main__":
    sys.exit(main())
