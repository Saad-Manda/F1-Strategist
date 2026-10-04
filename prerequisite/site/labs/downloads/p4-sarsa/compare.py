"""Run your candidate with visible training/evaluation budgets; no solution import."""
import argparse
import json
from checks import load_candidate
from exercise_common import comparison, validate_settings

def main():
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate',default='starter.py')
    parser.add_argument('--episodes',type=int,default=1000)
    parser.add_argument('--seeds',default='7,31,89')
    parser.add_argument('--epsilon',type=float,default=0.2)
    parser.add_argument('--alpha',type=float,default=0.1)
    args=parser.parse_args()
    try:
        seeds=[int(x) for x in args.seeds.split(',')]
        if not 2<=len(seeds)<=10 or len(set(seeds))!=len(seeds) or any(not 0<=s<=4294967295 for s in seeds):
            raise ValueError('use 2–10 distinct uint32 seeds')
        validate_settings(args.episodes,args.epsilon,args.alpha)
        print(json.dumps(comparison(load_candidate(args.candidate),seeds,args.episodes,args.epsilon,args.alpha),indent=2))
    except (ValueError,NotImplementedError) as error:
        print(f'Exercise incomplete or invalid settings: {error}')
        raise SystemExit(1)

if __name__=='__main__':main()
