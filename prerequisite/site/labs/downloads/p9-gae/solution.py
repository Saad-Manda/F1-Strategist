from exercise_common import *

def gae(rewards, values, next_values, terminated, trace_continue, gamma=.9, lam=1):
    xs=[np.asarray(x) for x in (rewards,values,next_values,terminated,trace_continue)]
    r,v,n,t,c=xs
    if any(x.ndim!=1 or not x.size or x.shape!=r.shape for x in xs):raise ValueError("matching nonempty vectors required")
    if t.dtype!=bool or c.dtype!=bool or np.any(t & c):raise ValueError("invalid boundary flags")
    if not all(np.isfinite(x).all() for x in (r,v,n)) or not all(math.isfinite(x) and 0<=x<=1 for x in (gamma,lam)):raise ValueError("finite data and discounts in [0,1] required")
    delta=r+gamma*np.where(t,0,n)-v
    a=np.zeros(len(r),dtype=float);tail=0.
    for i in range(len(r)-1,-1,-1):
        tail=delta[i]+gamma*lam*c[i]*tail;a[i]=tail
    return a,a+v

if __name__=="__main__":
    import sys
    run(sys.modules[__name__])
