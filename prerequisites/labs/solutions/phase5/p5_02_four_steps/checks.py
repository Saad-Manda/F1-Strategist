"""Checks for lab p5-02. Given code: read it if you like, but there is nothing to edit here."""

import numpy as np
import torch

from labs.labkit.checks import passed, require

LAB = "p5-02"


def forward(forward_fn, W1, W2, X):
    h_pre, h, y = forward_fn(W1, W2, X)
    require(np.shape(h_pre) == (1, 2) and np.shape(h) == (1, 2), f"For a batch of one and two hidden units, h_pre and h should have shape (1, 2); got {np.shape(h_pre)} and {np.shape(h)}.")
    require(np.allclose(h_pre, [[1.0, 1.5]]), f"Page 02: h_pre = [1.0, 1.5]. Got {np.round(h_pre, 4).tolist()}. W1 multiplies each row of X: X @ W1.T.")
    require(np.shape(y) == (1,), f"y should have one number per example, shape (1,); got {np.shape(y)}.")
    require(np.allclose(y, [0.5]), f"Page 02: y = 0.5. Got {np.round(y, 4).tolist()}.")
    _, h2, y2 = forward_fn(W1, W2, np.array([[-2.0, 1.0], [2.0, 1.0]]))
    require(np.allclose(h2[0], [0.0, 0.0]), f"For x = [-2, 1] both pre-activations are negative (-3 and -0.5), so ReLU must zero them. Got h = {np.round(h2[0], 4).tolist()}.")
    require(np.allclose(y2, [0.0, 0.5]), "Each row of the batch is its own example.")
    passed(LAB, "forward", "TODO 1: your forward pass reproduces page 02 and handles a batch.")


def _torch_grads(W1, W2, X, targets):
    w1 = torch.tensor(W1, dtype=torch.float64, requires_grad=True)
    w2 = torch.tensor(W2, dtype=torch.float64, requires_grad=True)
    x = torch.tensor(X, dtype=torch.float64)
    y = torch.relu(x @ w1.T) @ w2
    loss = ((y - torch.tensor(targets, dtype=torch.float64)) ** 2).mean()
    loss.backward()
    return loss.item(), w1.grad.numpy(), w2.grad.numpy()


def backward(backward_fn, W1, W2, X):
    loss, dW1, dW2 = backward_fn(W1, W2, X, np.array([0.0]))
    require(abs(loss - 0.25) < 1e-9, f"Page 02's loss is (0.5 - 0)² = 0.25; got {loss}.")
    require(np.shape(dW2) == (2,) and np.shape(dW1) == (2, 2), f"Gradients must have their weights' shapes: dW1 (2, 2), dW2 (2,). Got {np.shape(dW1)} and {np.shape(dW2)}.")
    require(abs(dW2[0] - 1.0) < 1e-9, f"Page 02 worked ∂L/∂W2[0] = 1.0. Got {dW2[0]}.")
    rng = np.random.default_rng(7)
    for width, batch in ((2, 1), (3, 5), (8, 16)):
        A, B = rng.normal(size=(width, 2)), rng.normal(size=width)
        Xb, Tb = rng.normal(size=(batch, 2)), rng.normal(size=batch)
        mine = backward_fn(A, B, Xb, Tb)
        ref = _torch_grads(A, B, Xb, Tb)
        require(np.allclose(mine[2], ref[2], atol=1e-8), f"dW2 disagrees with PyTorch for width {width}, batch {batch}: yours {np.round(mine[2], 4).tolist()}, autograd {np.round(ref[2], 4).tolist()}. Is dy divided by the batch size?")
        require(np.allclose(mine[1], ref[1], atol=1e-8), f"dW1 disagrees with PyTorch for width {width}, batch {batch}. Check the ReLU line: the gradient passes only where h_pre > 0.")
    passed(LAB, "backward", "TODO 2: every gradient matches PyTorch's autograd.")


def training(train, init, backward_fn, X, T):
    W1, W2 = init(2, 1)
    start = backward_fn(W1, W2, X, T)[0]
    loss, W1t, W2t = train(2, 1)
    require(not np.allclose(W1t, W1), "The weights did not change: update W1 and W2 inside the loop.")
    require(loss < start, f"Gradient descent should lower the loss; it went from {start:.3f} to {loss:.3f}. Did you add the gradient instead of subtracting it?")
    require(loss < 1e-3, f"From start 1 the network should find |x1 - x2| (loss under 0.001); got {loss:.4f}.")
    passed(LAB, "train", "TODO 3: your own gradient descent trains the network.")


def starts(final):
    solved = sum(v < 1e-3 for v in final.values())
    require(len(final) == 20, "Run the cell as given.")
    require(5 <= solved <= 15, f"Expected around half the starts to solve it; got {solved}.")
    passed(LAB, "C", "Part C: whether a two-unit network learns depends on where it starts.")


def widths(by_width):
    require(by_width[4] >= 19 and by_width[8] >= 19, f"Wider networks should solve it from nearly every start; got {by_width}.")
    require(by_width[2] < by_width[4], "The two-unit network should fail more often than the four-unit one.")
    passed(LAB, "D", "Part D: spare width makes training reliable.")
