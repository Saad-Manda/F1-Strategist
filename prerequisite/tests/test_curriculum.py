"""Reject curriculum defects that would strand learners or break static hosting."""

from copy import deepcopy
import importlib.util
from pathlib import Path
import sys

SCRIPTS = Path(__file__).resolve().parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))
spec = importlib.util.spec_from_file_location("validate_labs", SCRIPTS / "validate_labs.py")
validator = importlib.util.module_from_spec(spec)
spec.loader.exec_module(validator)


def test_declared_curriculum_is_connected_and_sources_exist():
    assert validator.validate_registry(validator.load_registry()) == []


def test_cycles_cannot_be_published_as_learning_paths():
    data = deepcopy(validator.load_registry())
    data["labs"][0]["prerequisites"] = ["p1-state"]
    assert any("Dependency cycle" in error for error in validator.validate_registry(data))


def test_typo_in_prerequisite_is_reported():
    data = deepcopy(validator.load_registry())
    data["labs"][1]["prerequisites"] = ["p1-looop"]
    assert any("unknown prerequisite p1-looop" in error for error in validator.validate_registry(data))


def test_missing_reference_and_premature_ready_status_are_rejected():
    data = deepcopy(validator.load_registry())
    data["labs"][0]["id"] = "p1-unpublished"
    data["labs"][0]["route"] = "phase-1/p1-unpublished.html"
    data["labs"][0]["references"] = ["phase-1-rl-prerequisites/unwritten-reference.html"]
    data["labs"][0]["status"] = "ready"
    errors = validator.validate_registry(data)
    assert any("missing/outside reference" in error for error in errors)
    assert any("ready lesson has no page" in error for error in errors)


def test_ppo_does_not_require_self_play():
    data = deepcopy(validator.load_registry())
    next(lab for lab in data["labs"] if lab["id"] == "p9-reinforce")["prerequisites"].append("p8-game")
    assert any("PPO unnecessarily depends" in error for error in validator.validate_registry(data))


def test_catalog_links_and_generated_files_are_valid():
    assert validator.validate_page(validator.LABS / "index.html") == []
    for path, content in validator.outputs(validator.load_registry()).items():
        assert path.read_text(encoding="utf-8") == content
