"""Predict-then-run: commit to an answer before the cell that reveals the result."""

from __future__ import annotations

from . import record
from .checks import LabTodo

_committed: dict[tuple[str, str], str] = {}


def commit(lab_id: str, key: str, answer, choices: dict[str, str]) -> None:
    """Lock in a prediction. `choices` maps each allowed answer to what it means."""
    if answer not in choices:
        options = "\n".join(f'    "{k}": {v}' for k, v in choices.items())
        raise LabTodo(f"TODO {lab_id}: set your prediction to one of\n{options}")
    _committed[(lab_id, key)] = answer
    record.task_passed(lab_id, f"predict:{key}", note=str(answer))
    print(f'Prediction locked in: "{answer}" — {choices[answer]}')


def reveal(lab_id: str, key: str, outcome: str, correct: str | None = None) -> None:
    """Show what happened next to what was predicted. Being wrong still counts as done."""
    answer = _committed.get((lab_id, key))
    if answer is None:
        raise LabTodo(f"TODO {lab_id}: run the prediction cell for '{key}' first")
    print(f"What happened: {outcome}")
    if correct is not None:
        print("Your prediction matched." if answer == correct else f'Your prediction ("{answer}") did not match. That is the useful case: reread the result above.')
