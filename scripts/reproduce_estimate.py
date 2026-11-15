"""Independently reconstruct the paired point estimate from the released CSV."""
import argparse
import csv
import json
import numpy as np

def reconstruct(path,transform='original',seed=20261114,draws=10000):
    with open(path,newline='',encoding='utf-8') as stream:
        rows = [r for r in csv.DictReader(stream) if r['transform'] == transform
                and r['missing'].lower() == 'false']
    values = []
    for row in rows:
        a,b,c = (float(row['M_'+arm]) for arm in 'ABC')
        assert np.isclose(a-b,float(row['enabling']),rtol=0,atol=1e-12)
        assert np.isclose(c-b,float(row['control']),rtol=0,atol=1e-12)
        assert np.isclose(a-c,float(row['specificity']),rtol=0,atol=1e-12)
        values.append(a-c)
    if not values:
        raise ValueError('No complete families for this transform')
    v = np.array(values)
    rng = np.random.default_rng(seed)
    bootstrap = np.empty(draws)
    for start in range(0,draws,1000):
        n = min(1000,draws-start)
        bootstrap[start:start+n] = v[rng.integers(0,len(v),(n,len(v)))].mean(axis=1)
    return {'transform':transform,'n':len(v),'mean':float(v.mean()),
            'ci95':np.percentile(bootstrap,[2.5,97.5]).tolist(),
            'mean_enabling':float(np.mean([float(r['enabling']) for r in rows])),
            'mean_control':float(np.mean([float(r['control']) for r in rows]))}

if __name__ == '__main__':
    p = argparse.ArgumentParser()
    p.add_argument('csv')
    p.add_argument('--transform',choices=['original','renamed'],default='original')
    p.add_argument('--seed',type=int,default=20261114)
    args = p.parse_args()
    print(json.dumps(reconstruct(args.csv,args.transform,args.seed),indent=2))
