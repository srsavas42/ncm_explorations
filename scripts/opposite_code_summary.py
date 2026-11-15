"""Predeclared selected-code secondary diagnostics for opposite-answer traces."""
import argparse
import json
from pathlib import Path
from ncm_probe.analysis import read_index,write_csv
from ncm_probe.storage import digest,file_hash,atomic_json,now
from scripts.explore_codes_competitor import compare_codes

PAIRS = [('rule_P','rule_Q'),('control_P','control_Q'),('rule_P','control_P'),('rule_Q','control_Q')]

def run(root,split):
    study = root/'outputs/opposite-v1'
    source = study/split
    manifest = json.loads((study/'families.json').read_text())
    index = json.loads((source/'trace-index.json').read_text())
    traces,errors = read_index(source,index,digest(manifest))
    if errors:
        raise ValueError('Resume incomplete traces before code diagnostics')
    lengths = json.loads((source/'run-plan.json').read_text())['identity']['level_lengths']
    families = [f for f in manifest['families'] if f['split'] == split]
    rows,summary = [],{}
    for transform in ('original','renamed'):
        summary[transform] = {}
        for a,b in PAIRS:
            firsts = []
            for f in families:
                ta = traces[(f['family_id'],transform,a)]
                tb = traces[(f['family_id'],transform,b)]
                details,first = compare_codes(ta['code_ids'],tb['code_ids'],lengths)
                firsts.append(first)
                for r in details:
                    rows.append({'family_id':f['family_id'],'transform':transform,'arm_a':a,'arm_b':b,
                                 'level':r['level'],'different_codes':r['different_codes'],'same_prefix':r['same_prefix']})
            summary[transform][a+'__'+b] = {'n':len(families),
                'first_divergence_counts':{**{str(k):firsts.count(k) for k in range(1,13)},'never':firsts.count(None)},
                'same_prefix_through_6':sum(k is None or k>6 for k in firsts)}
    result = {'kind':'predeclared secondary selected-code readout; not an internal mechanism test',
              'created_at':now(),'split':split,'manifest_hash':digest(manifest),
              'index_sha256':file_hash(source/'trace-index.json'),'script_sha256':file_hash(__file__),
              'model_reruns':0,'results':summary}
    atomic_json(source/'code-analysis.json',result)
    write_csv(source/'level-code-comparisons.csv',rows)
    print(json.dumps(result,indent=2))
    return result

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--split',choices=['pilot','confirmation'],default='pilot')
    args = parser.parse_args()
    run(args.root.resolve(),args.split)
