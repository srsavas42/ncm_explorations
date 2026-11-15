"""Reconstruct follow-up effects from the family CSV, without model imports."""
import argparse
import csv
import json
import numpy as np

def reconstruct(path,transform='original',seed=2026111402):
    with open(path,newline='',encoding='utf-8') as stream:
        rows = [r for r in csv.DictReader(stream) if r['transform'] == transform and r['missing'].lower() == 'false']
    values = {'D_rule':[],'D_control':[],'specificity':[]}
    for r in rows:
        rule = float(r['early_rule_P'])-float(r['early_rule_Q'])
        control = float(r['early_control_P'])-float(r['early_control_Q'])
        effects = {'D_rule':rule,'D_control':control,'specificity':rule-control}
        for key,value in effects.items():
            if value != float(r[key]):
                raise ValueError('Saved component arithmetic disagrees with reconstructed effect')
            values[key].append(value)
    if not rows:
        raise ValueError('No complete families')
    result = {'transform':transform,'n':len(rows),'metrics':{}}
    for key,items in values.items():
        v = np.array(items,dtype=float)
        rng = np.random.default_rng(seed)
        bootstrap = np.empty(10000)
        for start in range(0,10000,1000):
            bootstrap[start:start+1000] = v[rng.integers(0,len(v),(1000,len(v)))].mean(axis=1)
        result['metrics'][key] = {'mean':float(v.mean()),'median':float(np.median(v)),
                                 'fraction_positive':float((v>0).mean()),'ties':int((v==0).sum()),
                                 'ci95':np.percentile(bootstrap,[2.5,97.5]).tolist()}
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('csv')
    parser.add_argument('--transform',choices=['original','renamed'],default='original')
    parser.add_argument('--seed',type=int,default=2026111402)
    args = parser.parse_args()
    print(json.dumps(reconstruct(args.csv,args.transform,args.seed),indent=2))
