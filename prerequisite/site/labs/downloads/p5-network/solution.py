"""Standalone CPU exercise. See README.md."""
from exercise_common import *

def predict(x, weight, bias):
    if x.ndim!=2 or weight.ndim!=2 or bias.ndim!=1 or x.shape[1]!=weight.shape[1] or weight.shape[0]!=len(bias):
        raise ValueError("expected x[B,D], weight[A,D], bias[A]")
    if not all(finite(t) for t in (x,weight,bias)): raise ValueError("finite inputs required")
    return x @ weight.T + bias
def mse(prediction, labels):
    if prediction.shape!=labels.shape or not prediction.numel() or not all(finite(t) for t in (prediction,labels)):
        raise ValueError("matching nonempty finite tensors required")
    return ((prediction-labels)**2).mean()
def train_step(model, optimizer, x, labels):
    optimizer.zero_grad()
    loss=mse(model(x),labels)
    loss.backward()
    optimizer.step()
    return float(loss.detach())

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
