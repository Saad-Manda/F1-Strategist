import pytest

from src.env.dynamics import (
    FITTABLE,
    Action,
    Compound,
    Weather,
    action_compound,
    compute_action_mask,
    update_rule,
)

S, M, H, I, W = Compound
DRY, DAMP, WET = Weather
LETTERS = "oSMHIW"


def legal(compound, weather, laps_to_go, rule_met):
    mask = compute_action_mask(compound, weather, laps_to_go, rule_met)
    return "".join(letter for letter, valid in zip(LETTERS, mask) if valid)


@pytest.mark.parametrize(
    "compound, weather, laps_to_go, rule_met, expected",
    [
        (M, DRY, 8, False, "oSMH"),  # fails if rain tyres are offered in the dry
        (M, DAMP, 8, False, "oSMHI"),  # fails if WET is offered in the damp
        (M, WET, 8, False, "oIW"),  # fails if slicks are offered in the wet
        (M, DRY, 3, False, "oSMH"),  # fails if the last chance comes a lap early
        (M, DRY, 2, False, "SH"),  # fails if a car may skip the rule or refit MEDIUM
        (H, DAMP, 2, False, "SMI"),  # fails if INTER does not satisfy the rule
        (S, WET, 2, False, "IW"),  # fails if the wet last chance has no action
        (M, DRY, 2, True, "oSMH"),  # fails if the last chance ignores the rule bit
        (M, DRY, 1, False, "o"),  # fails if a stop at the flag is allowed
        (I, WET, 1, True, "o"),
        (I, DRY, 5, True, "oSMH"),  # fails if a car must leave a wrong tyre
    ],
)
def test_mask(compound, weather, laps_to_go, rule_met, expected):
    assert legal(compound, weather, laps_to_go, rule_met) == expected


@pytest.mark.parametrize(
    "rule_met, current, new, expected",
    [
        (False, M, M, False),  # fails if any stop counts
        (False, M, H, True),
        (False, M, I, True),  # fails if INTER does not waive the rule
        (False, M, W, True),
        (True, M, M, True),  # fails if the rule can be lost
    ],
)
def test_rule(rule_met, current, new, expected):
    assert update_rule(rule_met, current, new) is expected


def test_actions_and_compounds_line_up():
    # Fails if the action order changes.
    assert [action_compound(a) for a in Action] == [None, S, M, H, I, W]


def test_every_legal_path_meets_the_rule(toy_params):
    # Fails if any reachable state has no legal action, or a legal race ends with the rule unmet.
    states = {
        (compound, compound in (I, W)) for weather in Weather for compound in FITTABLE[weather]
    }
    for laps_to_go in range(toy_params["total_laps"], 0, -1):
        following = set()
        for compound, rule_met in states:
            for weather in Weather:
                mask = compute_action_mask(compound, weather, laps_to_go, rule_met)
                assert mask.any()
                for action in Action:
                    if not mask[action]:
                        continue
                    new = action_compound(action)
                    if new is None:
                        following.add((compound, rule_met))
                    else:
                        following.add((new, update_rule(rule_met, compound, new)))
        states = following
    assert all(rule_met for _, rule_met in states)
