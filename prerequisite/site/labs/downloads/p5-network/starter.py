"""Standalone CPU exercise. See README.md."""
from exercise_common import *

def predict(x, weight, bias):
    # TODO: follow README.md.
    raise NotImplementedError("Complete predict")

def mse(prediction, labels):
    # TODO: follow README.md.
    raise NotImplementedError("Complete mse")

def train_step(model, optimizer, x, labels):
    # TODO: follow README.md.
    raise NotImplementedError("Complete train_step")

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
