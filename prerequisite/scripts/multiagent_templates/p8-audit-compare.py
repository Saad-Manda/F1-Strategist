"""Actual PettingZoo drivers plus official API checks, no hosted Python needed."""
import argparse,json,platform,importlib.metadata
from checks import load_candidate
from exercise_common import demo,OneRound,parallel_to_aec
from pettingzoo.test import api_test,parallel_api_test

if __name__=='__main__':
    p=argparse.ArgumentParser();p.add_argument('--candidate',default='starter.py');a=p.parse_args()
    report=demo(load_candidate(a.candidate))
    report['versions']={name:importlib.metadata.version(name) for name in ('pettingzoo','gymnasium','numpy')}
    report['versions']['python']=platform.python_version()
    print(json.dumps(report,indent=2))
    parallel_api_test(OneRound(),num_cycles=10)
    api_test(parallel_to_aec(OneRound()),num_cycles=10)
    print('Official Parallel and AEC checks passed; hidden commitments and cleanup checked separately by checks.py.')
