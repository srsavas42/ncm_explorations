import json
import os
from pathlib import Path
import time
import traceback
import zipfile
import numpy as np
from .adapter import CPUAdapter, validate_trace
from .cohort import load_manifest, transformed
from .sudoku import load_fixture
from .storage import root,outdir,digest,atomic_json,immutable_json,now,file_hash

def cache_key(board,identity):
    return digest({'board':board,'identity':identity})

def save_trace(path,trace,metadata):
    validate_trace(trace)
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp = path.with_suffix('.tmp')
    with tmp.open('wb') as stream:
        np.savez_compressed(stream,**trace,metadata=np.array(json.dumps(metadata,sort_keys=True)))
        stream.flush()
        os.fsync(stream.fileno())
    os.replace(tmp,path)

def read_trace(path,board=None,identity_hash=None):
    with np.load(path,allow_pickle=False) as z:
        result = {key:z[key] for key in z.files if key != 'metadata'}
        metadata = json.loads(str(z['metadata']))
    validate_trace(result)
    if board is not None and metadata['board'] != board:
        raise ValueError('Cached puzzle differs')
    if identity_hash is not None and metadata['identity_hash'] != identity_hash:
        raise ValueError('Cached adapter identity differs')
    return result,metadata

def run_families(cfg,families,output,manifest_hash,resume=True):
    start = time.perf_counter()
    output = Path(output)
    output.mkdir(parents=True,exist_ok=True)
    adapter = CPUAdapter(cfg)
    adapter.validate_parity(output/'parity.json')
    identity_hash = digest(adapter.identity)
    plan = {'manifest_hash':manifest_hash,'identity':adapter.identity,'identity_hash':identity_hash}
    immutable_json(output/'run-plan.json',plan)
    index_path = output/'trace-index.json'
    index = {'manifest_hash':manifest_hash,'identity_hash':identity_hash,'boards':[]}
    calls,hits = 0,0
    for f in families:
        for transform,variant in [('original',f),('renamed',transformed(f))] if 'permutation' in f else [('original',f)]:
            for arm in 'ABC':
                board = variant['boards'][arm]
                key = cache_key(board,adapter.identity)
                path = output/'cache'/f'{key}.npz'
                record = {'family_id':f['family_id'],'transform':transform,'arm':arm,'board':board,
                          'key':key,'path':str(path.relative_to(output)).replace('\\','/')}
                try:
                    cached = False
                    if resume and path.exists():
                        try:
                            trace,_ = read_trace(path,board,identity_hash)
                            cached = True
                            hits += 1
                        except (ValueError,OSError,KeyError,EOFError,zipfile.BadZipFile):
                            pass
                    if not cached:
                        if time.perf_counter()-start >= cfg['study']['compute_budget_seconds']:
                            raise TimeoutError('Predeclared compute budget reached; resume engineering run')
                        trace = adapter.trace(board)
                        save_trace(path,trace,{'board':board,'board_id':key,'identity_hash':identity_hash,
                                              'level_lengths':adapter.levels,'created_at':now()})
                        calls += 1
                    record.update(status='complete',seconds=float(trace['seconds']),
                                  peak_memory_bytes=int(trace['peak_memory_bytes']),sha256=file_hash(path))
                except Exception as exc:
                    record.update(status='engineering_failure',error=f'{type(exc).__name__}: {exc}')
                    with (output/'failures.jsonl').open('a',encoding='utf-8') as log:
                        log.write(json.dumps(dict(record,traceback=traceback.format_exc()))+'\n')
                index['boards'].append(record)
                atomic_json(index_path,index)
            print(f'{f["family_id"]} {transform}: {len(index["boards"])} trajectories recorded',flush=True)
    atomic_json(output/'run-cost.json',{'wall_seconds':time.perf_counter()-start,
                'new_model_calls':calls,'cache_hits':hits,'finished_at':now(),
                'parity_reference_boards':2,'parity_trajectories_per_reference':3})
    return index

def run(cfg,resume=False):
    manifest = load_manifest(cfg)
    if not manifest['families']:
        raise ValueError('No selected families; report feasibility before inference')
    return run_families(cfg,manifest['families'],outdir(cfg),digest(manifest),resume)

def trace_fixture(cfg):
    from .analysis import fixture_figure
    f = load_fixture()
    output = root(cfg)/'outputs/fixture'
    index = run_families(cfg,[f],output,digest(f),True)
    fixture_figure(f,index,output)
    return index
