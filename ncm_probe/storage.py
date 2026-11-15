import hashlib
import json
import os
from pathlib import Path
import tomllib
from datetime import datetime, timezone

def digest(obj):
    return hashlib.sha256(json.dumps(obj, sort_keys=True, separators=(',',':'), allow_nan=False).encode()).hexdigest()

def file_hash(path):
    h = hashlib.sha256()
    with open(path,'rb') as stream:
        for block in iter(lambda: stream.read(1024*1024), b''):
            h.update(block)
    return h.hexdigest()

def atomic_json(path, value):
    path = Path(path)
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    tmp.write_text(json.dumps(value,indent=2,sort_keys=True,allow_nan=False)+'\n',encoding='utf-8')
    os.replace(tmp,path)

def immutable_json(path, value):
    path = Path(path)
    if path.exists():
        if json.loads(path.read_text()) != value:
            raise ValueError(f'Frozen artifact differs: {path}. Use a new output directory.')
        return
    atomic_json(path,value)

def config(path):
    path = Path(path).resolve()
    cfg = tomllib.loads(path.read_text())
    cfg['_root'] = str(path.parent.parent)
    if cfg['study']['split'] not in ('pilot','confirmation'):
        raise ValueError('Unknown split')
    if cfg['study']['early_levels'] != list(range(1,7)):
        raise ValueError('Changing the early window requires a versioned protocol change')
    if cfg['model']['precision'] != 'float32' or cfg['model']['threads'] < 1:
        raise ValueError('This adapter requires CPU float32 and positive thread count')
    study = cfg['study']
    if not 1 <= study['planned_n'] <= study['sample_cap']:
        raise ValueError('Planned sample must be positive and within its fixed cap')
    if study['source_budget'] < 1 or study['precision_goal'] <= 0 or study['compute_budget_seconds'] <= 0:
        raise ValueError('Source, precision, and compute budgets must be positive')
    if study['bootstrap_draws'] != 10000:
        raise ValueError('The frozen analysis requires 10,000 family bootstrap draws')
    return cfg

def root(cfg):
    return Path(cfg['_root'])

def outdir(cfg):
    return root(cfg)/cfg['study']['output']

def frozen_config(cfg):
    return {k:v for k,v in cfg.items() if not k.startswith('_')}

def now():
    return datetime.now(timezone.utc).isoformat()
