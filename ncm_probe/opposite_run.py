import json
import time
import traceback
import zipfile
from pathlib import Path
from .storage import atomic_json,immutable_json,digest,file_hash,now
from .opposite_puzzles import ARMS,transformed
from .opposite_prepare import load_manifest,output_dir

def run_families(cfg,families,output,manifest_hash,resume=True):
    start = time.perf_counter()
    from .adapter import CPUAdapter
    from .runner import cache_key,read_trace,save_trace
    adapter = CPUAdapter(cfg)
    output.mkdir(parents=True,exist_ok=True)
    adapter.validate_parity(output/'parity.json')
    identity = digest(adapter.identity)
    plan = {'manifest_hash':manifest_hash,'identity':adapter.identity,'identity_hash':identity,
            'analysis_source_sha256':file_hash(Path(__file__).with_name('opposite_analysis.py')),
            'runner_source_sha256':file_hash(__file__)}
    immutable_json(output/'run-plan.json',plan)
    index = {'manifest_hash':manifest_hash,'identity_hash':identity,'boards':[]}
    calls,hits = 0,0
    for f in families:
        for transform,g in [('original',f),('renamed',transformed(f))]:
            for arm in ARMS:
                board = g['boards'][arm]
                key = cache_key(board,adapter.identity)
                path = output/'cache'/f'{key}.npz'
                row = {'family_id':f['family_id'],'transform':transform,'arm':arm,'board':board,
                       'key':key,'path':str(path.relative_to(output)).replace('\\','/')}
                try:
                    trace = None
                    if resume and path.exists():
                        try:
                            trace,_ = read_trace(path,board,identity)
                            hits += 1
                        except (OSError,ValueError,KeyError,EOFError,zipfile.BadZipFile):
                            pass
                    if trace is None:
                        if time.perf_counter()-start >= cfg['study']['compute_budget_seconds']:
                            raise TimeoutError('Predeclared CPU budget reached')
                        trace = adapter.trace(board)
                        save_trace(path,trace,{'board':board,'identity_hash':identity,'created_at':now(),
                                             'level_lengths':adapter.levels,'study':'opposite-answer-v1'})
                        calls += 1
                    row.update(status='complete',seconds=float(trace['seconds']),
                               peak_memory_bytes=int(trace['peak_memory_bytes']),sha256=file_hash(path))
                except Exception as exc:
                    row.update(status='engineering_failure',error=f'{type(exc).__name__}: {exc}')
                    with (output/'failures.jsonl').open('a',encoding='utf-8') as stream:
                        stream.write(json.dumps(dict(row,traceback=traceback.format_exc()))+'\n')
                index['boards'].append(row)
                atomic_json(output/'trace-index.json',index)
            print(f"{f['family_id']} {transform}: {len(index['boards'])} follow-up trajectories",flush=True)
    atomic_json(output/'run-cost.json',{'wall_seconds':time.perf_counter()-start,'new_model_calls':calls,
                'cache_hits':hits,'finished_at':now(),'parity_examples':2})
    if any(r['status'] != 'complete' for r in index['boards']):
        raise RuntimeError('Engineering failures remain; inspect failures.jsonl and resume')
    return index

def run(cfg,split,resume=True):
    manifest = load_manifest(cfg)
    families = [f for f in manifest['families'] if f['split'] == split]
    if not families:
        raise ValueError('No selected families for this split')
    return run_families(cfg,families,output_dir(cfg)/split,digest(manifest),resume)

def fixture(cfg):
    from .storage import root
    from .analysis import read_index,write_csv
    from .opposite_analysis import family_metrics,figure
    f = json.loads((root(cfg)/'ncm_probe/fixtures/opposite-engineering.json').read_text())
    output = output_dir(cfg)/'fixture'
    index = run_families(cfg,[f],output,digest(f),True)
    traces,errors = read_index(output,index,digest(f))
    assert not errors
    rows,levels = [],[]
    for transform,g in [('original',f),('renamed',transformed(f))]:
        t = {a:traces[(f['family_id'],transform,a)] for a in ARMS}
        row,_,ls = family_metrics(g,t,cfg['study']['early_levels'])
        rows.append(dict(row,transform=transform))
        levels.extend(dict(r,transform=transform) for r in ls)
    write_csv(output/'family-analysis.csv',rows)
    write_csv(output/'level-metrics.csv',levels)
    figure(output,rows,levels)
