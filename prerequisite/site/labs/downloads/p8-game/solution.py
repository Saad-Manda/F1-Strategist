"""Standalone M5 exercise. Optional reference; see README.md."""
from exercise_common import *

def payoff(learner, opponent):
    action(learner);action(opponent)
    return MATRIX[learner][opponent]
def expected_payoff(policy, opponent):
    validate_policy(policy);validate_policy(opponent)
    return sum(policy[i]*opponent[j]*payoff(i,j) for i in range(3) for j in range(3))
def action_update(values, action, reward, alpha):
    validate_action(action)
    if len(values)!=3 or any(not math.isfinite(v) for v in [*values,reward,alpha]) or not 0<=alpha<=1:raise ValueError("finite values and alpha in [0,1] required")
    result=list(values);result[action]+=alpha*(reward-result[action])
    return result
def best_response(opponent):
    policy(opponent)
    values=[sum(MATRIX[i][j]*opponent[j] for j in range(3)) for i in range(3)]
    return [i for i,v in enumerate(values) if math.isclose(v,max(values),abs_tol=1e-12)]

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
