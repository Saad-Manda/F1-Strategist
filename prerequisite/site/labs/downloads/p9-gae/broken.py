from exercise_common import *

def gae(rewards, values, next_values, terminated, trace_continue, gamma=.9, lam=1):
    r,v,n=np.asarray(rewards),np.asarray(values),np.asarray(next_values)
    delta=r+gamma*n-v;a=np.zeros(len(r));tail=0.
    for i in range(len(r)-1,-1,-1):tail=delta[i]+gamma*lam*tail;a[i]=tail
    return a,a+v

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
