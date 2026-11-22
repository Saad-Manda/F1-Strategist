"""Author tool: put a phase's lab blocks into the doc pages and the course manifest.

    python -m labs.tools.site phase1

* Code labs: the block is generated from labs/solutions/<phase>/<lab>/lab.yaml
  (title, goal, environment, files, hints).
* In-page labs: the block body is labs/tools/site_src/<phase>/<lab-id>.html, whose first line is
  a header comment:  <!-- page: <folder/file.html> | title: ... | format: paper | minutes: 15 | scripts: widgets/x.js -->

* A code lab that also has a site_src file gets that file as an in-page warm-up, placed after
  the goal. Its questions are checked in the browser; the lab's status still comes from the code.

Re-running replaces existing blocks in place, so it is safe to run after every edit.
"""

from __future__ import annotations

import html
import json
import re
import sys
from pathlib import Path

import yaml

LABS = Path(__file__).resolve().parents[1]
SITE = LABS.parent / "site"
MANIFEST = SITE / "assets" / "course.js"
KIND = {"notebook": "Notebook", "pytest": "Code + tests", "paper": "In page", "quiz": "In page", "widget": "In page"}
BLOCK = re.compile(r'[ \t]*<section class="lab".*?</section>\n', re.S)
LAB_SCRIPTS = re.compile(r'<script src="\.\./assets/(?:labs|widgets/[^"]+)\.js"></script>\n')


def code_block(meta: dict, folder: str) -> str:
    rel = f"labs/{folder}/{Path(meta['_dir']).name}"
    files = ", ".join(f"<code>{rel}/{name}</code>" for name in (meta.get("files") or ["lab.ipynb"]))
    hints = "\n".join(
        f"        <details><summary>Hint {i}</summary><p>{html.escape(h)}</p></details>" for i, h in enumerate(meta.get("hints", []), 1)
    )
    stage = (
        f'\n          <div><span>Stage</span><code>python -m labs check {meta["id"]} 1</code></div>' if meta["id"].endswith("-cap") else ""
    )
    return f"""        <p class="lab-goal">{meta["goal"]}</p>
        <p><strong>Environment:</strong> {meta["environment"]}</p>
        <div class="lab-cmds">
          <div><span>Open</span><code>python -m labs open {meta["id"]}</code></div>
          <div><span>Check</span><code>python -m labs check {meta["id"]}</code></div>{stage}
          <div><span>Hint</span><code>python -m labs hint {meta["id"]}</code></div>
        </div>
        <p class="lab-files">Run the commands from inside the <code>prerequisites/</code> folder. Files: {files}. Reference solution, for afterwards: <code>labs/solutions/{folder}/{Path(meta['_dir']).name}/</code>.</p>
{hints}"""


def wrap(lab_id: str, title: str, fmt: str, minutes: int, body: str) -> str:
    return f"""      <section class="lab" id="lab" data-lab-id="{lab_id}" data-lab-format="{fmt}">
        <span class="lab-kicker">Lab {lab_id} · {KIND[fmt]} · about {minutes} min</span>
        <h2>{html.escape(title)}</h2>
{body.rstrip()}
        <p class="lab-status"></p>
      </section>
"""


def read_src(path: Path) -> tuple[dict, str]:
    """An in-page lab source: (header fields, body). `scripts` comes back as a list."""
    head, _, body = path.read_text(encoding="utf-8").partition("-->")
    fields = dict(part.strip().split(": ", 1) for part in head.replace("<!--", "").split("|"))
    fields["scripts"] = [s for s in fields.get("scripts", "").split(",") if s.strip()]
    return fields, body.strip("\n")


def collect(phase: str) -> list[dict]:
    labs = []
    for path in sorted((LABS / "solutions" / phase).glob("*/lab.yaml")):
        meta = yaml.safe_load(path.read_text(encoding="utf-8"))
        meta["_dir"] = str(path.parent)
        body, scripts = code_block(meta, phase), []
        warmup = LABS / "tools" / "site_src" / phase / f'{meta["id"]}.html'
        if warmup.exists():  # an in-page warm-up that goes with this code lab: placed right after the goal
            fields, extra = read_src(warmup)
            goal, _, rest = body.partition("\n")
            body = goal + "\n\n" + extra + "\n" + rest
            scripts = fields["scripts"]
        labs.append({"id": meta["id"], "title": meta["title"], "format": meta["format"], "minutes": meta["minutes"],
                     "page": meta["page"], "body": body, "scripts": scripts})
    code_ids = {lab["id"] for lab in labs}
    for path in sorted((LABS / "tools" / "site_src" / phase).glob("*.html")):
        if path.stem in code_ids:
            continue
        fields, body = read_src(path)
        labs.append({"id": path.stem, "title": fields["title"], "format": fields["format"], "minutes": int(fields["minutes"]),
                     "page": fields["page"], "body": body, "scripts": fields["scripts"]})
    return labs


def main(phase: str) -> None:
    text = MANIFEST.read_text(encoding="utf-8")
    course = json.loads(text[text.index("{") : text.rindex("}") + 1])
    pages = {f'{ph["slug"]}/{p["file"]}': p for ph in course["phases"] for p in ph["pages"]}

    for lab in collect(phase):
        page = SITE / lab["page"]
        src = page.read_text(encoding="utf-8")
        block = wrap(lab["id"], lab["title"], lab["format"], lab["minutes"], lab["body"])
        if BLOCK.search(src):
            src = BLOCK.sub(lambda _m: block, src, count=1)
        else:
            marker = '      <div class="pagenav"'
            assert marker in src, f"{lab['page']}: no pagenav placeholder to insert before"
            src = src.replace(marker, block + "\n" + marker, 1)
        tags = "".join(f'<script src="../assets/{s.strip()}"></script>\n' for s in lab["scripts"])
        tags += '<script src="../assets/labs.js"></script>\n'
        src = LAB_SCRIPTS.sub("", src).replace("</body>", tags + "</body>", 1)
        page.write_text(src, encoding="utf-8", newline="\n")
        pages[lab["page"]]["lab"] = {"id": lab["id"], "title": lab["title"], "format": lab["format"], "minutes": lab["minutes"]}
        print(f'{lab["id"]:<7} -> {lab["page"]}')

    MANIFEST.write_text(
        "// Course manifest: the single source of truth for navigation. The value is pure JSON.\n"
        "window.COURSE = " + json.dumps(course, indent=2, ensure_ascii=False) + ";\n",
        encoding="utf-8",
        newline="\n",
    )


if __name__ == "__main__":
    main(sys.argv[1])
