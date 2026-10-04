"""Supplied CLI scaffolding. No RL implementation or reference answer here."""
import argparse
import json
import random

import gymnasium as gym


def run_demo(env_class, collector):
    parser = argparse.ArgumentParser(description="Run one small chain episode.")
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--limit", type=int, default=6)
    parser.add_argument("--actions", help="Optional comma-separated script, e.g. RIGHT,RIGHT or LEFT")
    args = parser.parse_args()
    if not 1 <= args.limit <= 20:
        parser.error("--limit must be between 1 and 20")
    rng = random.Random(args.seed)
    if args.actions:
        labels = args.actions.upper().split(',')
        if any(label not in {'LEFT', 'RIGHT'} for label in labels):
            parser.error("--actions accepts only LEFT and RIGHT")
        script = [0 if label == 'LEFT' else 1 for label in labels]
        index = 0

        def policy(observation):
            nonlocal index
            action = script[min(index, len(script) - 1)]
            index += 1
            return action
    else:
        def policy(observation):
            return rng.randrange(2)
    env = gym.wrappers.TimeLimit(env_class(), max_episode_steps=args.limit)
    try:
        trace = collector(env, policy, seed=args.seed)
        print(json.dumps(trace, indent=2))
        print(f"Steps: {len(trace)}; total reward: {sum(row['reward'] for row in trace)}")
    except NotImplementedError as error:
        print(f"Exercise incomplete: {error}")
        raise SystemExit(1) from error
    finally:
        env.close()
