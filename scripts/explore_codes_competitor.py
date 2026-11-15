"""Post-hoc diagnostics of existing traces; never loads or calls the model.

Preserves the frozen primary analysis. Competitor outcomes are exploratory,
including on the already-analyzed confirmation cohort; they are not fresh tests.
"""
import argparse
import json
from pathlib import Path
import numpy as np

from ncm_probe.analysis import read_index,margin,stable_level,summary,write_csv,pyplot
from ncm_probe.storage import atomic_json,file_hash,digest,now


def compare_codes(a,b,lengths):
    lengths = [int(x) for x in lengths]
    if len(a) != sum(lengths) or len(b) != sum(lengths):
        raise ValueError('Code lengths do not match the saved hierarchy')
    rows = []
    start = 0
    for k,n in enumerate(lengths):
        end = start+n
        positions = np.flatnonzero(a[start:end] != b[start:end])
        rows.append({'level':k+1,'length':n,
                     'different_codes':len(positions),
                     'differing_level_positions_0based':positions.tolist(),
                     'a_codes_at_differences':np.asarray(a[start:end])[positions].tolist(),
                     'b_codes_at_differences':np.asarray(b[start:end])[positions].tolist(),
                     'same_prefix':bool(np.array_equal(a[:end],b[:end]))})
        start = end
    first = next((r['level'] for r in rows if not r['same_prefix']),None)
    return rows,first


def probability(trace,cell,digit):
    # Normalize over the full 12-token output vocabulary, preserving special tokens.
    offset = 10*(cell//9)+cell%9
    scores = trace['full_logits'][:,offset,:].astype(np.float64)
    exp = np.exp(scores-scores.max(axis=1,keepdims=True))
    return exp[:,digit]/exp.sum(axis=1)


def analyze_family(f,traces,lengths,transform):
    t,u,d,e = (f[k] for k in ('target','competitor','digit','rival'))
    actual_u = int(f['solution'][u])
    assert actual_u != d
    early = slice(0,6)
    code_rows,readout_rows,pair_rows = [],[],[]
    code_firsts = {}
    for a,b in [('A','B'),('C','B'),('A','C')]:
        details,first = compare_codes(traces[a]['code_ids'],traces[b]['code_ids'],lengths)
        code_firsts[a+b] = first
        for detail in details:
            k = detail['level']-1
            equal = np.array_equal(traces[a]['full_logits'][k],traces[b]['full_logits'][k])
            if detail['same_prefix'] and not equal:
                raise AssertionError('Identical codes produced different decoder scores')
            code_rows.append({'family_id':f['family_id'],'transform':transform,'pair':a+b,
                              **detail,'full_decoder_scores_equal':equal})
        target_delta = margin(traces[a],t,d,e)-margin(traces[b],t,d,e)
        # At the competitor, positive means favoring its true digit over the ruled-out d.
        elimination_delta = margin(traces[a],u,actual_u,d)-margin(traces[b],u,actual_u,d)
        raw_delta = traces[a]['digit_logits'][:,u,d-1].astype(float)-traces[b]['digit_logits'][:,u,d-1].astype(float)
        prob_delta = probability(traces[a],u,d)-probability(traces[b],u,d)
        target_changed = bool(np.any(target_delta[early] != 0))
        competitor_changed = bool(np.any(elimination_delta[early] != 0))
        category = ('both' if target_changed and competitor_changed else
                    'target_only' if target_changed else
                    'competitor_only' if competitor_changed else 'neither')
        pair_rows.append({'family_id':f['family_id'],'transform':transform,'pair':a+b,
                          'first_code_difference':first,'same_codes_through_6':bool(details[5]['same_prefix']),
                          # Match the frozen primary's order: difference of early arm means.
                          'target_early_margin_change':float(margin(traces[a],t,d,e)[early].mean())-float(margin(traces[b],t,d,e)[early].mean()),
                          'competitor_early_elimination_margin_change':float(elimination_delta[early].mean()),
                          'competitor_early_d_score_change':float(raw_delta[early].mean()),
                          'competitor_early_d_probability_change':float(prob_delta[early].mean()),
                          'early_readout_change_category':category,'competitor_true_digit':actual_u,
                          'digit_ruled_out':d,'target':t,'competitor':u})
        for k in range(len(lengths)):
            readout_rows.append({'family_id':f['family_id'],'transform':transform,'pair':a+b,'level':k+1,
                                 'target_margin_change':float(target_delta[k]),
                                 'competitor_elimination_margin_change':float(elimination_delta[k]),
                                 'competitor_d_score_change':float(raw_delta[k]),
                                 'competitor_d_probability_change':float(prob_delta[k])})
    return code_rows,readout_rows,pair_rows,code_firsts


def cohort(root,name):
    from ncm_probe.cohort import transformed
    output = root/'outputs'/name
    manifest = json.loads((output/'families.json').read_text())
    index = json.loads((output/'trace-index.json').read_text())
    traces,errors = read_index(output,index,digest(manifest))
    lengths = json.loads((output/'run-plan.json').read_text())['identity']['level_lengths']
    codes,readouts,pairs,missing = [],[],[],[]
    for f in manifest['families']:
        for transform,g in [('original',f),('renamed',transformed(f))]:
            absent = [a for a in 'ABC' if (f['family_id'],transform,a) not in traces]
            if absent:
                missing.append({'family_id':f['family_id'],'transform':transform,'arms':absent})
                continue
            selected = {a:traces[(f['family_id'],transform,a)] for a in 'ABC'}
            c,r,p,_ = analyze_family(g,selected,lengths,transform)
            codes.extend(dict(row,cohort=name) for row in c)
            readouts.extend(dict(row,cohort=name) for row in r)
            pairs.extend(dict(row,cohort=name) for row in p)
    result = {'missing':missing,'indexed_engineering_errors':len(errors),'transforms':{}}
    for transform in ('original','renamed'):
        result['transforms'][transform] = {}
        for pair in ('AB','CB','AC'):
            selected = [r for r in pairs if r['transform'] == transform and r['pair'] == pair]
            result['transforms'][transform][pair] = {
                'n':len(selected),
                'same_code_prefix_through_6':sum(r['same_codes_through_6'] for r in selected),
                'readout_change_categories':{category:sum(r['early_readout_change_category'] == category for r in selected)
                    for category in ('both','target_only','competitor_only','neither')},
                **{metric:summary([r[metric] for r in selected],20261114,10000) for metric in (
                    'target_early_margin_change','competitor_early_elimination_margin_change',
                    'competitor_early_d_score_change','competitor_early_d_probability_change')}}
    return codes,readouts,pairs,result


def run(root,output):
    from ncm_probe.sudoku import load_fixture
    output.mkdir(parents=True,exist_ok=True)
    fixture_dir = root/'outputs/fixture'
    index = json.loads((fixture_dir/'trace-index.json').read_text())
    traces,errors = read_index(fixture_dir,index)
    if errors:
        raise ValueError(errors)
    f = load_fixture()
    t = {a:traces[(f['family_id'],'original',a)] for a in 'ABC'}
    lengths = json.loads((fixture_dir/'run-plan.json').read_text())['identity']['level_lengths']
    codes,readouts,pairs,firsts = analyze_family(f,t,lengths,'original')
    write_csv(output/'fixture-codes.csv',codes)
    write_csv(output/'fixture-readout-changes.csv',readouts)
    fixture = {'first_code_difference':firsts,'comparisons':pairs,
               'target_winners':{a:t[a]['winners'][:,65].tolist() for a in 'ABC'},
               'target_stable_level':{a:stable_level(t[a]['winners'][:,65],7) for a in 'ABC'},
               'code_selection_probabilities_saved':False}
    all_codes,all_readouts,all_pairs = [],[],[]
    results = {}
    for name in ('pilot-v1','confirmation-v1'):
        c,r,p,s = cohort(root,name)
        all_codes.extend(c)
        all_readouts.extend(r)
        all_pairs.extend(p)
        results[name] = s
    write_csv(output/'family-comparisons.csv',all_pairs)
    write_csv(output/'level-code-comparisons.csv',all_codes)
    write_csv(output/'level-readout-changes.csv',all_readouts)
    provenance = {'analysis_kind':'post-hoc exploratory; existing pilot and already-analyzed confirmation',
                  'created_at':now(),'script_sha256':file_hash(__file__),
                  'early_window':[1,2,3,4,5,6],'model_reruns':0,'primary_analysis_modified':False,
                  'competitor_metric':'score(true digit at competitor) minus score(digit ruled out by enabling clue)',
                  'probability_normalization':'full 12-token output vocabulary',
                  'direction':'positive elimination-margin response / negative ruled-out-digit probability response is predicted',
                  'categories':'whether any of six level-wise target/competitor margin changes is nonzero; not evidence of rule use',
                  'bootstrap':'10,000 seeded whole-family percentile resamples; exploratory, no multiplicity correction',
                  'inputs':{name:{'index_sha256':file_hash(root/'outputs'/name/'trace-index.json'),
                                  'manifest_sha256':file_hash(root/'outputs'/name/'families.json')}
                            for name in ('pilot-v1','confirmation-v1')}}
    atomic_json(output/'analysis.json',{'provenance':provenance,'fixture':fixture,'cohorts':results})
    report(output,fixture,results)
    return fixture,results


def report(output,fixture,results):
    lines = ['# Exploratory code and competitor check','',
             'These checks reuse existing traces after inspecting the primary results. '
             'They do not change the frozen target-cell primary endpoint and are not an independent confirmation of a competitor hypothesis.','',
             '## Worked fixture','',
             'A, B and C have identical code prefixes through level 7 and identical full decoder scores across every cell through those levels. '
             'A first differs from B at level 8 (one of 26 code positions). C first differs from B at level 10. '
             'The early A−B and C−B changes are exactly zero at both target and competitor.','',
             'All arms first select 7 at the target at level 4, switch to 1 at levels 7–8, '
             'and remain correct from level 9 onward. A third digit did not give A an earlier selection advantage.','',
             'At the first A/B divergence, the competitor’s raw score for 7 increases by about 0.046 in A. '
             'This is not the proposed raw-score drop. Later changes vary in direction. '
             'The full-vocabulary probability and true-digit-versus-7 margin are also saved, because raw logits can shift together.','',
             'Code-selection probabilities were not stored. Decoder logits are saved, but they describe different predictions '
             'and cannot be used as code-selection probabilities. Inspecting subtler generator responses would require a new, separately logged instrumented replay.','',
             '## Existing cohorts (exploratory)','',
             '| Cohort / transform | A/B prefixes identical through 6 | Both readouts change | Target only | Competitor only | Neither |',
             '|---|---:|---:|---:|---:|---:|']
    for name,s in results.items():
        for transform,table in s['transforms'].items():
            r = table['AB']
            cats = r['readout_change_categories']
            lines.append(f"| {name} / {transform} | {r['same_code_prefix_through_6']}/{r['n']} | "
                         f"{cats['both']} | {cats['target_only']} | {cats['competitor_only']} | {cats['neither']} |")
    lines += ['','A change means any nonzero level-wise change in the early window, regardless of direction. '
              'Different selected codes or a shifted readout do not identify use of a hidden-single rule.','',
              '| Cohort / original | A−B competitor elimination margin | C−B competitor elimination margin | A−C competitor elimination margin |',
              '|---|---|---|---|']
    def format_effect(s):
        return f"{s['mean']:+.4f} [{s['ci95'][0]:+.4f}, {s['ci95'][1]:+.4f}]" if s['n'] else 'unavailable'
    for name,s in results.items():
        table = s['transforms']['original']
        lines.append('| '+name+' | '+' | '.join(format_effect(table[p]['competitor_early_elimination_margin_change'])
                                               for p in ('AB','CB','AC'))+' |')
    lines += ['','Values are means with exploratory 95% family bootstrap intervals. Positive means stronger preference '
              'for the competitor’s actual solution digit over the ruled-out digit. A−B and C−B are shown separately '
              'so a control-edit effect cannot masquerade as an enabling effect. Renamed effects and probability changes are in analysis.json.','',
              'The output tables include all 12 levels, all three pair comparisons, original and renamed families, '
              'and exact prefix equality. The next inferential test should define competitor endpoints before looking at fresh puzzle outcomes.']
    (output/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--root',type=Path,default=Path(__file__).resolve().parents[1])
    parser.add_argument('--output',type=Path)
    args = parser.parse_args()
    destination = args.output or args.root/'outputs/exploratory-code-competitor-v1'
    fixture,results = run(args.root.resolve(),destination.resolve())
    print(json.dumps({'fixture_first_code_difference':fixture['first_code_difference'],
                      'output':str(destination)},indent=2))
