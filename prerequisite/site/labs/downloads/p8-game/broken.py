"""Standalone M5 exercise. Optional reference; see README.md."""
from exercise_common import *

def payoff(learner, opponent):return MATRIX[opponent][learner]
def expected_payoff(policy, opponent):return sum(policy[i]*opponent[j]*payoff(i,j) for i in range(3) for j in range(3))
def action_update(values, action, reward, alpha):return [v+alpha*(reward-v) for v in values]
def best_response(opponent):return [0]

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
