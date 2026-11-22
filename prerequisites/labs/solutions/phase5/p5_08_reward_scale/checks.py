"""Checks for lab p5-08. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np
import torch

from labs.labkit.checks import LabTodo, passed, require

LAB = "p5-08"


def limits(huber_slope, clip_by_norm):
    got = [float(huber_slope(e)) for e in (0.5, 250, 5000, -0.3, -40)]
    require(np.allclose(got, [0.5, 1, 1, -0.3, -1]), f"Huber slopes for errors 0.5, 250, 5000, -0.3, -40 should be 0.5, 1, 1, -0.3, -1. Got {got}.")
    grads, norm = clip_by_norm([np.array([24.0, 0.0]), np.array([[0.0, 32.0]])], 10.0)
    require(abs(norm - 40.0) < 1e-9, f"The norm of all entries together, sqrt(24² + 32²), is 40. Got {norm}.")
    require(np.allclose(grads[0], [6.0, 0.0]) and np.allclose(grads[1], [[0.0, 8.0]]), "Page 08: norm 40, limit 10, so every gradient is multiplied by 0.25.")
    small, n2 = clip_by_norm([np.array([3.0, 4.0])], 10.0)
    require(abs(n2 - 5.0) < 1e-9 and np.allclose(small[0], [3.0, 4.0]), "A norm below the limit is left alone.")
    rng = np.random.default_rng(0)
    raw = [rng.normal(size=(4, 3)) * 5, rng.normal(size=3) * 5]
    params = [torch.nn.Parameter(torch.zeros(g.shape, dtype=torch.float64)) for g in raw]
    for p, g in zip(params, raw):
        p.grad = torch.tensor(g)
    torch.nn.utils.clip_grad_norm_(params, 2.0)
    mine, _ = clip_by_norm(raw, 2.0)
    require(all(np.allclose(m, p.grad.numpy()) for m, p in zip(mine, params)), "Your clip disagrees with torch.nn.utils.clip_grad_norm_, the call the real agent uses.")
    passed(LAB, "limits", "TODO 1 and 2: the Huber slope and the norm clip match page 08 and PyTorch.")


def distance(runs, arrive):
    near, far = arrive[-250.0], arrive[-4940.0]
    require(near is not None and far is not None, "Both runs should have arrived within 1 s at some point. Run the cell as given.")
    require(1.5 < far / near < 10, f"Expected the uncentred run to take a few times as many updates; the ratio was {far / near:.1f}.")
    require(runs[-4940.0][-300:].max() > 5 * runs[-250.0][-300:].max(), "At the end the uncentred run should wobble far more than the centred one.")
    passed(LAB, "B", "Part B: the larger scale cost several times the updates and never sat still.")


def diagnosis(answers, rows):
    for name, answer in answers.items():
        if answer is None:
            raise LabTodo(f"TODO {LAB}: choose a row for {name}: one of {', '.join(rows)}")
        require(answer in rows, f"{name}: '{answer}' is not one of {', '.join(rows)}.")
    want = {"run 1": "broken", "run 2": "travelling", "run 3": "runaway", "run 4": "differences"}
    why = {
        "run 1": "Its average Q-value sits near 0, where a fresh network starts, and never moves toward -250.",
        "run 2": "Its average Q-value moves steadily toward -250 and is not there yet.",
        "run 3": "Its average Q-value has gone far past -250 and is still growing.",
        "run 4": "Its average Q-value has reached -250; the scale is learned, the decisions are not.",
    }
    wrong = [n for n in want if answers[n] != want[n]]
    require(not wrong, " ".join(f"{n}: not '{answers[n]}'. {why[n]}" for n in wrong))
    passed(LAB, "C", "Part C: four flat reward curves, four different diagnoses.")
