def validate_distribution(probabilities):
    import math
    if not probabilities or any(not math.isfinite(p) or not 0 <= p <= 1 for p in probabilities):
        raise ValueError("probabilities must be finite and in [0,1]")
    if abs(sum(probabilities)-1)>1e-10:
        raise ValueError("probabilities must sum to 1 (tolerance 1e-10); no silent normalization")

def rollout(encoder, actions, mode=0, seed=7):
    if mode is None:
        import random
        mode = random.Random(seed).randrange(2)
    trace = []
    for action in actions:
        if action not in ("FLIP", "CLAIM"):
            raise ValueError("unknown action")
        before = encoder(mode)
        if action == "FLIP":
            mode = 1 - mode
            reward, terminated = 0, False
        else:
            reward, terminated = (1 if mode == 1 else -1), True
        trace.append(dict(action=action, before=before, observation=encoder(mode),
                          reward=reward, terminated=terminated))
        if terminated:
            break
    return trace

def demo(module):
    return {"claim": rollout(module.encode_state, ["CLAIM"]),
            "flip_claim": rollout(module.encode_state, ["FLIP", "CLAIM"]),
            "horizon_state": module.encode_state(0, 2),
            "seeded_reset_claim": rollout(module.encode_state,["CLAIM"],mode=None,seed=7)}

def run(module):
    import json
    try:
        print(json.dumps(demo(module),indent=2))
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1)

