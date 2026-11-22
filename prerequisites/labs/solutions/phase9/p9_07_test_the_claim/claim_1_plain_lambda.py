"""Claim 1, given script: hand a lambda to a plain multiprocessing.Process under spawn.

    python labs/phase9/p9_07_test_the_claim/claim_1_plain_lambda.py
"""

import multiprocessing as mp


def worker(make, queue):
    queue.put(make())


if __name__ == "__main__":
    ctx = mp.get_context("spawn")  # Windows' only start method; forced here so every OS agrees
    queue = ctx.Queue()
    p = ctx.Process(target=worker, args=(lambda: "built in the worker", queue))
    p.start()
    print(queue.get(timeout=30))
    p.join()
    print("OUTCOME: works")
