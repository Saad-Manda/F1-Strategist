"""Standalone CPU exercise. See README.md."""
from exercise_common import *

def predict(x, weight, bias): return x @ weight.T + bias
def mse(prediction, labels): return ((prediction-labels)**2).sum()
def train_step(model, optimizer, x, labels):
    loss=mse(model(x),labels)
    loss.backward()
    optimizer.step()
    return float(loss.detach())

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
