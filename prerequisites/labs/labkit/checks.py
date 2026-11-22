"""Small vocabulary for lab checks, so every lab reports the same way."""

from __future__ import annotations

from . import record


class LabTodo(NotImplementedError):
    """Raised where the learner still has something to fill in."""


def todo(lab_id: str, what: str) -> LabTodo:
    return LabTodo(f"TODO {lab_id}: {what}")


def require(condition: bool, message: str) -> None:
    """Fail a check with a message that names the property, not the fix."""
    if not condition:
        raise AssertionError(message)


def close(a: float, b: float, tol: float = 1e-6) -> bool:
    return abs(float(a) - float(b)) <= tol


def passed(lab_id: str, task: str, message: str) -> None:
    record.task_passed(lab_id, task)
    print(f"✓ {message}")
