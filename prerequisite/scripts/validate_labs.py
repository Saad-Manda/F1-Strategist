"""Check curriculum integrity, generated-file drift, and publish-folder links."""

from __future__ import annotations

import argparse
from collections import Counter
from html.parser import HTMLParser
from pathlib import Path
import re
from urllib.parse import unquote, urlsplit

from build_catalog import LABS, ROOT, SITE, load_registry, outputs


def normalize(text):
    return re.sub(r"[^a-z0-9]+", " ", text.lower()).strip()


def headings(path):
    return [normalize(line.lstrip('#').strip()) for line in path.read_text(encoding="utf-8").splitlines()
            if line.startswith('#')]


def validate_registry(data, require_local_plans=False, plans_directory=None):
    errors = []
    if data.get("schemaVersion") != 1:
        errors.append("Unsupported schema version.")
    phases = {p["id"]: p for p in data["phases"]}
    labs = data["labs"]
    by_id = {lab["id"]: lab for lab in labs}
    if len(by_id) != len(labs):
        errors.append("Duplicate lab IDs.")
    if len(phases) != len(data["phases"]):
        errors.append("Duplicate phase IDs.")
    for field in ("route",):
        if len({lab[field] for lab in labs}) != len(labs):
            errors.append(f"Duplicate {field}s.")
    model_fields = {"state", "observation", "actions", "transitions", "reward", "boundary", "randomness"}
    for key, model in data["models"].items():
        if model_fields - model.keys() or any(not isinstance(model.get(f), str) or not model.get(f).strip() for f in model_fields):
            errors.append(f"Incomplete model {key}.")
    plans = Path(plans_directory).resolve() if plans_directory else None
    audit_path = plans / "phases-2-9-audit.md" if plans else None
    audit = headings(audit_path) if audit_path and audit_path.is_file() else None
    if require_local_plans and audit is None:
        errors.append("Missing local audit plan.")
    for lab in labs:
        key = lab["id"]
        if not re.fullmatch(r"p(?:1|35|4|5|6|8|9)-[a-z-]+", key):
            errors.append(f"Invalid lab ID {key}.")
        if lab["phase"] not in phases:
            errors.append(f"{key}: unknown phase.")
            continue
        if lab["mode"] not in {"build", "debug"} or lab["status"] not in {"planned", "ready"}:
            errors.append(f"{key}: unsupported mode/status.")
        route = lab["route"]
        if route != f"phase-{lab['phase']}/{key}.html":
            errors.append(f"{key}: route must use its stable phase/ID.")
        if lab["status"] == "ready" and not (LABS / route).is_file():
            errors.append(f"{key}: ready lesson has no page.")
        for field in ("title", "objective", "browser", "localTask", "misconception", "transfer", "milestone"):
            if not isinstance(lab.get(field), str) or not lab[field].strip():
                errors.append(f"{key}: missing {field}.")
        for field in ("background", "acceptance", "references", "planSections"):
            if not lab.get(field) or not all(isinstance(v, str) and v.strip() for v in lab[field]):
                errors.append(f"{key}: incomplete {field}.")
        if not isinstance(lab.get("minutes"), int) or lab["minutes"] <= 0:
            errors.append(f"{key}: invalid session estimate.")
        if lab["model"] not in data["models"]:
            errors.append(f"{key}: unknown model.")
        if len(lab["prerequisites"]) != len(set(lab["prerequisites"])):
            errors.append(f"{key}: duplicate prerequisite.")
        for dependency in lab["prerequisites"]:
            if dependency not in by_id:
                errors.append(f"{key}: unknown prerequisite {dependency}.")
        for reference in lab["references"]:
            target = (SITE / reference).resolve()
            if not target.is_relative_to(SITE.resolve()) or not target.is_file():
                errors.append(f"{key}: missing/outside reference {reference}.")
        plan = plans / phases[lab["phase"]]["plan"] if plans else None
        if (not plan or not plan.is_file()) and require_local_plans:
            errors.append(f"{key}: missing local implementation plan.")
        elif plan and plan.is_file():
            plan_headings = headings(plan)
            for section in lab["planSections"]:
                if not any(normalize(section) in h for h in plan_headings):
                    errors.append(f"{key}: unmapped plan section {section}.")
        for section in lab["audit"]:
            prefix = normalize(section)
            if audit is not None and not any(h == prefix or h.startswith(prefix + " ") for h in audit):
                errors.append(f"{key}: unmapped audit section {section}.")

    visiting, visited = set(), set()

    def visit(key):
        if key in visiting:
            errors.append(f"Dependency cycle includes {key}.")
            return
        if key in visited or key not in by_id:
            return
        visiting.add(key)
        for dependency in by_id[key]["prerequisites"]:
            visit(dependency)
        visiting.remove(key)
        visited.add(key)

    for key in by_id:
        visit(key)

    def ancestors(key, seen=None):
        seen = set() if seen is None else seen
        for dependency in by_id[key]["prerequisites"]:
            if dependency in by_id and dependency not in seen:
                seen.add(dependency)
                ancestors(dependency, seen)
        return seen

    for lab in labs:
        if lab["phase"] == "9" and any(by_id[key]["phase"] in {"6", "8"} for key in ancestors(lab["id"])):
            errors.append(f"{lab['id']}: PPO unnecessarily depends on the multi-agent/self-play branch.")
    return errors


class PageAssets(HTMLParser):
    def __init__(self):
        super().__init__()
        self.ids = []
        self.links = []

    def handle_starttag(self, tag, attrs):
        for key, value in attrs:
            if key == "id":
                self.ids.append(value)
            if value and ((tag in {"a", "link"} and key == "href") or (tag in {"script", "img"} and key == "src")):
                self.links.append(value)


def validate_page(path, site=SITE, cache=None):
    cache = {} if cache is None else cache
    publish_root = site.resolve()
    routes = cache.setdefault('resolved_routes', {})
    asset_paths = cache.setdefault('resolved_asset_paths', {})
    def assets(target):
        # Many sidebar links revisit the same anchored page. Resolve each path
        # once per audit while retaining symlink-aware containment checks.
        if target not in asset_paths:
            asset_paths[target] = target.resolve()
        target = asset_paths[target]
        if target not in cache:
            parsed=PageAssets();parsed.feed(target.read_text(encoding="utf-8"));cache[target]=parsed
        return cache[target]
    parser = assets(path)
    errors = [f"{path.name}: duplicate element ID {key}." for key, number in Counter(parser.ids).items() if number > 1]
    for link in parser.links:
        url = urlsplit(link)
        if url.scheme or url.netloc:
            continue
        key = (publish_root, path.parent, url.path)
        if key not in routes:
            target = (path.parent / unquote(url.path)).resolve() if url.path else path.resolve()
            routes[key] = (target, target.is_relative_to(publish_root) and target.is_file())
        target, valid = routes[key]
        if not valid:
            errors.append(f"{path.name}: missing/outside publish-folder link {link}.")
        elif url.fragment:
            other = assets(target)
            if unquote(url.fragment) not in other.ids:
                errors.append(f"{path.name}: missing anchor {link}.")
    return errors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check-local-plans", action="store_true", help="Require ignored implementation plans and verify their section mappings")
    parser.add_argument("--plans-directory", type=Path, help="Explicit external project-plan directory; optional for standalone checks")
    args = parser.parse_args()
    data = load_registry()
    errors = validate_registry(data, require_local_plans=args.check_local_plans, plans_directory=args.plans_directory)
    if not errors:
        for path, content in outputs(data).items():
            if not path.exists() or path.read_text(encoding="utf-8") != content:
                errors.append(f"Stale generated file: {path.relative_to(ROOT)}")
        page_cache = {}
        for path in SITE.rglob('*.html'):
            errors.extend(validate_page(path, cache=page_cache))
        catalog_source = (LABS / "index.html").read_text(encoding="utf-8")
        for lab in data["labs"]:
            if f'data-lab-id="{lab["id"]}"' not in catalog_source:
                errors.append(f"{lab['id']}: absent from catalog.")
            if lab["status"] == "planned" and f'href="{lab["route"]}"' in catalog_source:
                errors.append(f"{lab['id']}: planned lesson emitted as a live link.")
    if errors:
        raise SystemExit('\n'.join(errors))
    print(f"Validated {len(data['labs'])} labs, {len(data['phases'])} phases, and {len(data['models'])} toy models.")
    print("Dependency graph, source mappings, generated files, and new publish-folder links passed.")
    print("All publish-folder HTML pages and ready lesson links passed.")
    if args.plans_directory is None:
        print("Standalone validation: external project-plan checks skipped.")


if __name__ == "__main__":
    main()
