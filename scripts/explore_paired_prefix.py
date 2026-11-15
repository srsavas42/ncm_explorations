"""Paired edit sensitivity from saved codes; explicitly exploratory, no inference."""
import argparse
from collections import Counter
import csv
import json
from pathlib import Path
import numpy as np
from ncm_probe.analysis import read_index,write_csv
from ncm_probe.storage import atomic_json,digest,file_hash,now
from scripts.explore_codes_competitor import compare_codes

CATEGORIES = ('neither','only_A','only_C','both')

def category(first_a,first_c,level):
    a = first_a is not None and first_a <= level
    c = first_c is not None and first_c <= level
    return 'both' if a and c else 'only_A' if a else 'only_C' if c else 'neither'

def aggregate(rows,k=12):
    levels = []
    for level in range(1,k+1):
        counts = Counter(category(r['first_AB'],r['first_CB'],level) for r in rows)
        levels.append({'level':level,'n':len(rows),**{name:counts[name] for name in CATEGORIES}})
    histograms = {pair:{str(level):sum(r['first_'+pair] == level for r in rows) for level in range(1,k+1)}
                  for pair in ('AB','CB')}
    for pair in histograms:
        histograms[pair]['never'] = sum(r['first_'+pair] is None for r in rows)
    ordering = Counter()
    for r in rows:
        a,c = r['first_AB'] or k+1,r['first_CB'] or k+1
        ordering['A_earlier' if a<c else 'C_earlier' if c<a else 'same_first_level_or_both_never'] += 1
    decomposition = []
    for name in CATEGORIES:
        selected = [r for r in rows if category(r['first_AB'],r['first_CB'],6) == name]
        values = [r['specificity'] for r in selected]
        decomposition.append({'category':name,'n':len(values),
                              'same_AC_prefix_through_6':sum(r['same_AC_through_6'] for r in selected),
                              'mean_specificity':float(np.mean(values)) if values else None,
                              'contribution_to_overall_mean':float(sum(values)/len(rows)) if rows else None})
    return {'n':len(rows),'four_way_by_level':levels,'first_divergence_counts':histograms,
            'first_divergence_ordering':dict(ordering),'primary_decomposition_by_level6_group':decomposition}

def run(root,output):
    output.mkdir(parents=True,exist_ok=True)
    results,all_rows,all_levels,inputs = {},[],[],{}
    for cohort in ('pilot-v1','confirmation-v1'):
        source = root/'outputs'/cohort
        manifest = json.loads((source/'families.json').read_text())
        index = json.loads((source/'trace-index.json').read_text())
        traces,errors = read_index(source,index,digest(manifest))
        if errors:
            raise ValueError(f'Incomplete input traces: {errors}')
        lengths = json.loads((source/'run-plan.json').read_text())['identity']['level_lengths']
        with (source/'family-analysis.csv').open(newline='') as stream:
            primary_rows = {(r['family_id'],r['transform']):r for r in csv.DictReader(stream)}
        original = json.loads((source/'analysis.json').read_text())
        results[cohort] = {'frozen_primary':original['results']['original']['specificity'],'transforms':{}}
        for transform in ('original','renamed'):
            rows = []
            for f in manifest['families']:
                t = {a:traces[(f['family_id'],transform,a)] for a in 'ABC'}
                ab,first_a = compare_codes(t['A']['code_ids'],t['B']['code_ids'],lengths)
                cb,first_c = compare_codes(t['C']['code_ids'],t['B']['code_ids'],lengths)
                ac,_ = compare_codes(t['A']['code_ids'],t['C']['code_ids'],lengths)
                p = primary_rows[(f['family_id'],transform)]
                if p['missing'].lower() != 'false':
                    raise ValueError('Primary table marks complete input traces as missing')
                value = float(p['specificity'])
                if ac[5]['same_prefix'] and value != 0:
                    raise AssertionError('Equal A/C prefix did not give zero primary contrast')
                rows.append({'cohort':cohort,'transform':transform,'family_id':f['family_id'],
                             'first_AB':first_a,'first_CB':first_c,
                             'level6_category':category(first_a,first_c,6),
                             'same_AC_through_6':ac[5]['same_prefix'],
                             'enabling':float(p['enabling']),'control':float(p['control']),
                             'specificity':value})
            result = aggregate(rows,len(lengths))
            expected = original['results'][transform]['specificity']
            if not len(rows) == expected['n'] or float(np.mean([r['specificity'] for r in rows])) != expected['mean']:
                raise AssertionError('Primary rows do not reconcile with frozen estimate')
            results[cohort]['transforms'][transform] = result
            all_rows.extend(rows)
            all_levels.extend(dict(row,cohort=cohort,transform=transform) for row in result['four_way_by_level'])
        inputs[cohort] = {name:file_hash(source/name) for name in
                         ('trace-index.json','families.json','family-analysis.csv','analysis.json')}
    provenance = {'created_at':now(),'kind':'post-hoc exploratory on existing cohorts',
                  'model_reruns':0,'primary_endpoint_unchanged':True,'paired_unit':'solved-grid family',
                  'changed_through_level':'any differing selected code in the cumulative prefix up to and including that level',
                  'first_divergence':'one-based level; never means no selected code differs through level 12',
                  'ordering':'never treated as 13 for descriptive ordering; same first level does not imply same codes',
                  'script_sha256':file_hash(__file__),
                  'code_comparison_helper_sha256':file_hash(Path(__file__).with_name('explore_codes_competitor.py')),
                  'source_artifacts':inputs}
    atomic_json(output/'analysis.json',{'provenance':provenance,'cohorts':results})
    write_csv(output/'paired-family-prefixes.csv',all_rows)
    write_csv(output/'four-way-by-level.csv',all_levels)
    write_report(output,results)
    return results

def write_report(output,results):
    primary = results['confirmation-v1']['frozen_primary']
    main = results['confirmation-v1']['transforms']['original']
    six = main['four_way_by_level'][5]
    lines = ['# Paired prefix sensitivity · exploratory','',
             f"The frozen confirmation primary A−C estimate is {primary['mean']:.4f}, "
             f"95% family bootstrap interval [{primary['ci95'][0]:.4f}, {primary['ci95'][1]:.4f}] (n={primary['n']}). "
             'It does not support the predicted positive early target preference. This remains the primary result.','',
             'The following analysis was requested after observing those outcomes. It reuses saved traces, '
             'runs no inference, and does not modify the frozen primary analysis.','',
             '## Paired counts through level 6 · 100 original confirmation families','',
             '| Prefix differs from B | Families |','|---|---:|',
             f"| Neither edit | {six['neither']} |",f"| Only A | {six['only_A']} |",
             f"| Only C | {six['only_C']} |",f"| Both | {six['both']} |",'',
             f"A differs from B in {six['only_A']+six['both']} families; C differs from B in {six['only_C']+six['both']}. "
             'These are paired observations, not independent samples. Earlier code divergence measures sensitivity to a clue edit, '
             'not whether its consequence is expressed in the predicted direction.','',
             '## First selected-code divergence from B','',
             '| Level | A versus B | C versus B |','|---|---:|---:|']
    for k in [str(i) for i in range(1,13)]+['never']:
        lines.append(f"| {k} | {main['first_divergence_counts']['AB'][k]} | {main['first_divergence_counts']['CB'][k]} |")
    o = main['first_divergence_ordering']
    lines += ['',f"A diverges earlier in {o.get('A_earlier',0)} families, C earlier in {o.get('C_earlier',0)}, "
              f"and first-divergence times tie in {o.get('same_first_level_or_both_never',0)}. "
              'For this descriptive comparison, no divergence through level 12 is treated as level 13. '
              'Equal first-divergence times do not imply equal selected prefixes.','',
              '## Relation to the primary estimate','',
              '| Level-6 group | n | A/C prefixes identical | Mean A−C target margin | Contribution to overall mean |',
              '|---|---:|---:|---:|---:|']
    for row in main['primary_decomposition_by_level6_group']:
        mean = f"{row['mean_specificity']:+.6f}" if row['mean_specificity'] is not None else 'unavailable'
        lines.append(f"| {row['category']} | {row['n']} | {row['same_AC_prefix_through_6']} | {mean} | "
                     f"{row['contribution_to_overall_mean']:+.6f} |")
    both = next(r for r in main['primary_decomposition_by_level6_group'] if r['category'] == 'both')
    lines += ['',f"In {both['same_AC_prefix_through_6']} of the {both['n']} families where both edits change the prefix, "
              'A and C select the same changed prefix. Their primary contrast is therefore zero. '
              'The 72 unchanged A/B prefixes alone cannot establish the A−C result: C changes in the only-C group, '
              'and other groups can contribute effects of either sign. Group contributions sum to the unchanged full-cohort estimate.','',
              'The existing target/competitor readout directions remain the relevant check on resemblance to the deduction. '
              'The separately reported exploratory competitor interval spans zero. These descriptive prefix counts do not resolve that direction. '
              'No code-selection probabilities were collected or inferred from decoder scores.','',
              'All 12 paired cumulative counts, pilot results and renamed repeats are available in analysis.json and the CSV tables. '
              'Original families remain primary; renamed repeats do not increase the independent sample size.']
    (output/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    destination = args.output or args.root/'outputs/exploratory-paired-prefix-v1'
    result = run(args.root.resolve(),destination.resolve())
    print(json.dumps(result['confirmation-v1']['transforms']['original'],indent=2))
