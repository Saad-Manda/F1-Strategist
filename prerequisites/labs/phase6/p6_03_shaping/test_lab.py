"""Checks for lab p6-03. Given code: nothing to edit here."""

import pathlib
import sys

import numpy as np
import pytest

HERE = pathlib.Path(__file__).resolve().parent
sys.path.insert(0, str(HERE))
sys.path.insert(0, str(next(p for p in HERE.parents if (p / "labs" / "labkit").exists())))

import shaping  # noqa: E402
from labs.labkit import gridshape as g  # noqa: E402

GAMMA = 0.95


def potentials(grid):
    """Three different potentials: distance to the exit, an arbitrary table, a constant."""
    dist = grid.distance("".join(grid.exits))
    rng = np.random.default_rng(6)
    table = {s: float(rng.uniform(-20, 20)) for s in grid.cells}
    return {
        "minus the distance to the exit": lambda s: -float(dist[s]),
        "an arbitrary random table": lambda s: table[s],
        "a constant 7": lambda s: 7.0,
    }


def differing_cells(a, b):
    return sorted(s for s in a if a[s] != b[s])


# ---------------------------------------------------------------- task 1: the term


def test_term_by_hand():
    assert shaping.shaping_term(2.0, 5.0, 0.9, False) == pytest.approx(2.5), "F = γ·Φ(s') − Φ(s) = 0.9 × 5 − 2 = 2.5."
    assert shaping.shaping_term(2.0, 5.0, 1.0, False) == pytest.approx(3.0)
    assert shaping.shaping_term(2.0, 5.0, 0.9, True) == pytest.approx(-2.0), (
        "When s' ends the episode its potential counts as 0, so F = −Φ(s) = −2, whatever Φ(s') says."
    )


def test_page_03_chain():
    """Page 03's chain at γ = 1, then the warm-up's potential."""

    def returns(phi):
        F = lambda a, b, end: shaping.shaping_term(phi[a], phi[b], 1.0, end)  # noqa: E731
        via_b = (-3 + F("A", "B", False)) + (-1 + F("B", "C", True))
        direct = -10 + F("A", "C", True)
        return via_b, direct

    assert returns({"A": 5, "B": 2, "C": 0}) == pytest.approx((-9, -15)), "Page 03's worked example: −9 via B, −15 direct."
    via_b, direct = returns({"A": 3, "B": 4, "C": 0})
    assert (via_b, direct) == pytest.approx((-7, -13)), f"The warm-up's potential (3, 4, 0): −7 via B and −13 direct. Got {via_b}, {direct}."
    assert via_b - direct == pytest.approx(6), "The gap between the two routes is the unshaped one, 6, whatever the potential."


# ---------------------------------------------------------------- task 2: invariance, exactly


def test_shaping_keeps_every_optimal_action():
    grid = g.OPEN
    _, plain = g.solve(grid, gamma=GAMMA)
    for name, phi in potentials(grid).items():
        _, best = g.solve(grid, shaping.shaped(grid.reward, phi, GAMMA), gamma=GAMMA)
        wrong = differing_cells(plain, best)
        assert not wrong, f"With Φ = {name}, the optimal actions changed in {len(wrong)} cells, e.g. {wrong[:3]}. Potential-based shaping must leave all of them alone."


def test_values_shift_by_minus_phi():
    grid = g.OPEN
    V, _ = g.solve(grid, gamma=GAMMA)
    for name, phi in potentials(grid).items():
        V2, _ = g.solve(grid, shaping.shaped(grid.reward, phi, GAMMA), gamma=GAMMA)
        worst = max(abs(V2[s] - (V[s] - phi(s))) for s in grid.states)
        assert worst < 1e-6, f"Page 03: V'(s) = V(s) − Φ(s) in every cell. With Φ = {name} the largest miss was {worst:.3g}."


def test_a_flat_tile_bonus_is_not_safe():
    """(given) The contrast: +1 every time the tile is entered changes the optimal actions."""
    tiled = g.Grid(["".join(r) for r in g.OPEN.rows], g.OPEN.exits, tile_bonus=1.0)
    _, plain = g.solve(g.OPEN, gamma=GAMMA)
    _, best = g.solve(tiled, gamma=GAMMA)
    assert differing_cells(plain, best), "(given) a flat bonus on one tile should change some optimal actions"


# ---------------------------------------------------------------- the trap: the zero at the end


def exit_reached(grid, best):
    return grid.char(g.greedy_path(grid, best)[-1])


def test_trap_your_prediction():
    if shaping.TRAP_EXIT is None:
        raise NotImplementedError("TODO p6-03: set TRAP_EXIT to 'N' or 'F'")
    grid = g.TWO_EXITS
    phi = lambda s: 5.0 if grid.char(s) == "N" else 0.0  # noqa: E731
    _, best = g.solve(grid, shaping.unzeroed(grid.reward, phi, GAMMA), gamma=GAMMA)
    reached = exit_reached(grid, best)
    assert shaping.TRAP_EXIT == reached, (
        f"Unzeroed, the policy heads for {reached}. The leftover γ^T·Φ(s_T) − Φ(s_0) is a bonus of about 5·γ^T paid only for finishing at N."
    )


def test_trap_zeroed_shaping_is_safe_even_with_potentials_on_the_exits():
    grid = g.TWO_EXITS
    _, plain = g.solve(grid, gamma=GAMMA)
    assert exit_reached(grid, plain) == "F", "(given) unshaped, the far exit worth 10 is best"
    for pN, pF in ((5.0, 0.0), (0.0, -6.0), (3.0, -3.0)):
        phi = lambda s, pN=pN, pF=pF: {"N": pN, "F": pF}.get(grid.char(s), 0.0)  # noqa: E731
        _, best = g.solve(grid, shaping.shaped(grid.reward, phi, GAMMA), gamma=GAMMA)
        wrong = differing_cells(plain, best)
        assert not wrong, (
            f"With Φ(N) = {pN} and Φ(F) = {pF}, your shaping changed the optimal actions in {len(wrong)} cells. "
            "The exits end the episode: their potential must count as 0 in the shaping term."
        )
        _, trap = g.solve(grid, shaping.unzeroed(grid.reward, phi, GAMMA), gamma=GAMMA)
        assert exit_reached(grid, trap) == "N", "(given) without the zero, these potentials pull the policy to N"


# ---------------------------------------------------------------- page 02's farming grid, revisited


def test_a_potential_hint_cannot_be_farmed():
    tile = g.farming(tile_bonus=2.0)
    _, farm = g.solve(tile, gamma=GAMMA)
    assert tile.char(g.greedy_path(tile, farm)[-1]) != "G", "(given) with a +2 tile the optimal policy loops on the tile and never finishes"

    plain = g.farming(tile_bonus=0.0)
    dist = plain.distance("G")
    hint = lambda s: -2.0 * dist[s]  # noqa: E731  "closer to the goal is better", as a potential
    _, best = g.solve(plain, shaping.shaped(plain.reward, hint, GAMMA), gamma=GAMMA)
    path = g.greedy_path(plain, best)
    assert plain.char(path[-1]) == "G" and len(path) - 1 == 8, (
        f"The same hint written as a potential should still take the shortest route to G, 8 steps. The path ended at {path[-1]} after {len(path) - 1} steps."
    )
