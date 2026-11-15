"""Predeclared analysis for the separate opposite-answer experiment."""
import json
from pathlib import Path
import numpy as np
from .analysis import margin,stable_level,grid_metrics,summary,write_csv,pyplot,read_index
from .opposite_puzzles import ARMS,transformed
from .opposite_prepare import load_manifest,output_dir
from .storage import digest,atomic_json
from .sudoku import parse

def assignment_curve(trace,f):
    p,q = f['locations']
    d,e = f['digit'],f['rival']
    return .5*(margin(trace,p,d,e)-margin(trace,q,d,e))

def family_metrics(f,traces,early):
    ix = np.array(early)-1
    row = {'family_id':f['family_id'],'source_row':f.get('source_row'),'missing':False,
           'digit':f['digit'],'rival':f['rival'],'P':f['locations'][0],'Q':f['locations'][1],
           'trade_size':len(f['trade_cells'])}
    curves,levels = {},[]
    for arm in ARMS:
        trace = traces[arm]
        curve = assignment_curve(trace,f)
        curves[arm] = curve
        row['early_'+arm] = float(curve[ix].mean())
        sol = parse(f['solution_P' if arm.endswith('_P') else 'solution_Q'])
        p,q = f['locations']
        pair_correct = (trace['winners'][:,p] == sol[p]) & (trace['winners'][:,q] == sol[q])
        row['stable_'+arm] = stable_level(pair_correct,True)
        grid = grid_metrics(trace,f['boards'][arm],''.join(map(str,sol)))
        row['final_valid_'+arm] = grid[-1]['valid']
        changed = np.array(f['trade_cells'])
        for k,value in enumerate(curve):
            levels.append({'family_id':f['family_id'],'arm':arm,'level':k+1,
                           'assignment_preference':float(value),
                           'winner_P':int(trace['winners'][k,p]),'winner_Q':int(trace['winners'][k,q]),
                           'pair_correct':bool(pair_correct[k]),
                           'trade_accuracy':float((trace['winners'][k,changed] == np.array(sol)[changed]).mean()),
                           **grid[k]})
    row['D_rule'] = row['early_rule_P']-row['early_rule_Q']
    row['D_control'] = row['early_control_P']-row['early_control_Q']
    row['specificity'] = row['D_rule']-row['D_control']
    return row,curves,levels

def report(cfg,split):
    manifest = load_manifest(cfg)
    families = [f for f in manifest['families'] if f['split'] == split]
    output = output_dir(cfg)/split
    index = json.loads((output/'trace-index.json').read_text())
    traces,errors = read_index(output,index,digest(manifest))
    rows,level_rows,missing,balance = [],[],[],[]
    for f in families:
        for transform,g in [('original',f),('renamed',transformed(f))]:
            absent = [a for a in ARMS if (f['family_id'],transform,a) not in traces]
            if absent:
                missing.append({'family_id':f['family_id'],'transform':transform,'arms':absent,
                                'causes':{a:errors.get((f['family_id'],transform,a),'not run') for a in absent}})
                rows.append({'family_id':f['family_id'],'transform':transform,'missing':True,'missing_arms':','.join(absent)})
                continue
            t = {a:traces[(f['family_id'],transform,a)] for a in ARMS}
            row,_,levels = family_metrics(g,t,cfg['study']['early_levels'])
            row['transform'] = transform
            rows.append(row)
            level_rows.extend(dict(r,transform=transform) for r in levels)
        for arm in ARMS:
            balance.append({'family_id':f['family_id'],'source_row':f['source_row'],'arm':arm,
                            'clue_endpoint':f['endpoints'][arm],'geometry':json.dumps(f['geometry'][arm]),
                            **f['matching'],**{k:v for k,v in f['checks'][arm].items() if k != 'candidate_masks'}})
    results = {}
    for transform in ('original','renamed'):
        selected = [r for r in rows if r['transform'] == transform and not r['missing']]
        results[transform] = {name:summary([r[name] for r in selected],cfg['study']['seed'],10000)
                              for name in ('D_rule','D_control','specificity')}
        results[transform]['final_valid_counts'] = {a:sum(r['final_valid_'+a] for r in selected) for a in ARMS}
        results[transform]['pair_stability'] = {
            a:{'mean_level':float(np.mean([r['stable_'+a] for r in selected])) if selected else None,
               'never_stable':sum(r['stable_'+a] == 13 for r in selected)} for a in ARMS}
    times = [float(t['seconds']) for t in traces.values()]
    planned = cfg['study']['pilot_n' if split == 'pilot' else 'confirmation_n']
    costs = {'trajectories':len(traces),'selected_planned_trajectories':8*len(families),
             'median_board_seconds':float(np.median(times)) if times else None,
             'total_inference_seconds':float(sum(times)),
             'peak_memory_bytes':max((int(t['peak_memory_bytes']) for t in traces.values()),default=None),
             'cache_bytes':sum((output/r['path']).stat().st_size for r in index['boards'] if r['status'] == 'complete')}
    result = {'split':split,'study':'opposite-answer-v1','manifest_hash':digest(manifest),
              'primary':'D_rule; predeclared positive','secondary':'D_rule minus D_control',
              'results':results,'missing':missing,'costs':costs,'source_yield':manifest['counts'],
              'status':'complete' if not missing and results['original']['D_rule']['n'] == planned else 'feasibility/exploratory',
              'renamed_primary_sign_flip':bool(results['original']['D_rule']['n'] and results['renamed']['D_rule']['n'] and
                  results['original']['D_rule']['mean']*results['renamed']['D_rule']['mean'] < 0)}
    atomic_json(output/'analysis.json',result)
    write_csv(output/'family-analysis.csv',rows)
    write_csv(output/'level-metrics.csv',level_rows)
    write_csv(output/'balance.csv',balance)
    figure(output,rows,level_rows)
    write_report(output,result)
    print(json.dumps(result,indent=2))
    return result

def figure(output,rows,levels):
    if not levels:
        return
    plt = pyplot()
    fig,axes = plt.subplots(1,2,figsize=(11,4))
    for arm in ARMS:
        means = [np.mean([r['assignment_preference'] for r in levels if r.get('transform','original') == 'original'
                          and r['arm'] == arm and r['level'] == k]) for k in range(1,13)]
        axes[0].plot(range(1,13),means,marker='o',label=arm)
    axes[0].axvspan(.5,6.5,color='grey',alpha=.12)
    axes[0].axhline(0,color='grey',linewidth=.7)
    axes[0].set(xlabel='Generated level',ylabel='Assignment preference (P versus Q)',title='Opposite-answer readouts')
    axes[0].legend(fontsize=8)
    for transform,marker in [('original','o'),('renamed','x')]:
        selected = [r for r in rows if r.get('transform','original') == transform and not r.get('missing',False)]
        if selected:
            axes[1].scatter([r['D_control'] for r in selected],[r['D_rule'] for r in selected],marker=marker,label=transform,alpha=.65)
    axes[1].axhline(0,color='grey',linewidth=.7)
    axes[1].axvline(0,color='grey',linewidth=.7)
    axes[1].set(xlabel='Control directional shift',ylabel='Rule directional shift',title='Early window · one point per family')
    axes[1].legend(fontsize=8)
    fig.tight_layout()
    fig.savefig(output/'opposite-effects.png',dpi=170)
    fig.savefig(output/'opposite-effects.svg')
    plt.close(fig)

def write_report(output,result):
    def effect(transform,name):
        r = result['results'][transform][name]
        return f"{r['mean']:+.4f} [{r['ci95'][0]:+.4f}, {r['ci95'][1]:+.4f}], n={r['n']}" if r['n'] else 'unavailable'
    lines = [f"# Opposite-answer follow-up · {result['split']}",'',
             f"Status: {result['status']}. The predeclared primary is the directional rule shift, with positive predicted. "
             'Intervals below are 95% percentile resamples of whole families.','',
             '| Transform | Primary rule shift | Control shift | Secondary rule−control |','|---|---|---|---|']
    for transform in ('original','renamed'):
        lines.append('| '+transform+' | '+' | '.join(effect(transform,name) for name in ('D_rule','D_control','specificity'))+' |')
    lines += ['',
              'Positive rule shift means the early decoder readout moves toward d at whichever of P/Q the box rule forces. '
              'A similar positive control shift means solution-changing remote clues also produce appropriate directional sensitivity. '
              'The secondary difference tests a relative early advantage, not an internal mechanism. '
              'These endpoints must not be substituted for the original same-solution study result.','',
              f"Renamed primary sign reversal: {result['renamed_primary_sign_flip']}. "
              f"Missing engineering trajectories: {result['missing']}. Final Sudoku failures remain included.",'',
              f"Final valid-grid counts: {json.dumps({t:r['final_valid_counts'] for t,r in result['results'].items()})}.",
              f"Pair stability: {json.dumps({t:r['pair_stability'] for t,r in result['results'].items()})}.",'',
              f"Observed costs: {json.dumps(result['costs'])}.",
              f"Construction denominators: {json.dumps(result['source_yield'])}.",'',
              'The four arms share a 34-clue scaffold with exactly two completions, then one same-digit clue selects each unique answer. '
              'Controls preserve both target cells’ local candidates and the target box’s d/e candidate positions. '
              'Row/column hidden-single alternatives at the forced location are excluded. '
              'Rule and control edit displacements and pooled band/stack relations match exactly. '
              'Necessary adjacency differences and residual center-distance/difficulty mismatches remain; balance.csv reports them. '
              'This selected connected-swap population differs from the original medium puzzles. '
              'Unknown Sudoku symmetries may remain beyond digit renaming and square dihedral grouping.','',
              'Reproduce the primary mean from family-analysis.csv: keep original complete families and average D_rule. '
              'No generator probabilities were recorded, no weights changed, and every inference used the full hierarchy.']
    (output/'report.md').write_text('\n'.join(lines)+'\n',encoding='utf-8')
