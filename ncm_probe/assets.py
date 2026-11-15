"""Download public assets once at immutable revisions and verify cached bytes."""
import json
from pathlib import Path
import subprocess
import urllib.request
from .storage import atomic_json, file_hash, root, immutable_json

def download(url,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    tmp = path.with_suffix(path.suffix+'.tmp')
    with urllib.request.urlopen(url, timeout=120) as response, tmp.open('wb') as output:
        while data := response.read(1024*1024):
            output.write(data)
    tmp.replace(path)

def acquire(cfg):
    base = root(cfg)/'assets'
    lockpath = base/'assets.lock.json'
    published = root(cfg)/'asset-lock.json'
    oldpath = published if published.exists() else lockpath
    old = json.loads(oldpath.read_text()) if oldpath.exists() else None
    revision = cfg['model']['upstream_revision']
    vendor = root(cfg)/'vendor/ncm'
    if not vendor.exists():
        subprocess.run(['git','-c','http.sslBackend=openssl','clone','https://github.com/HazyResearch/ncm.git',str(vendor)],check=True)
    actual = subprocess.check_output(['git','-C',str(vendor),'rev-parse','HEAD'],text=True).strip()
    if actual != revision:
        subprocess.run(['git','-C',str(vendor),'checkout',revision],check=True)
    # Keep the independent reference revision fixed after first use.
    if old:
        parity_revision = old['parity_revision']
    else:
        with urllib.request.urlopen('https://huggingface.co/api/models/mrfakename/ncm-webgpu-weights',timeout=30) as response:
            parity_revision = json.load(response)['sha']
    records = []
    groups = [('hazyresearch/ncm-checkpoints',cfg['model']['checkpoint_revision'],False,
               ['config.yaml','generator.pt','tokenizer.pt'],'sudoku/medium','checkpoint'),
              ('hazyresearch/ncm-datasets',cfg['model']['dataset_revision'],True,
               ['puzzles.pickle','solutions.pickle'],'sudoku/medium','dataset'),
              ('mrfakename/ncm-webgpu-weights',parity_revision,False,
               ['meta.json','fixtures.json'],'sudoku-medium','parity')]
    for repo, rev, dataset, names, folder, local in groups:
        for name in names:
            url = f'https://huggingface.co/{"datasets/" if dataset else ""}{repo}/resolve/{rev}/{folder}/{name}'
            path = base/local/name
            if not path.exists():
                print(f'Downloading {local}/{name}',flush=True)
                download(url,path)
            record = {'repo':repo,'revision':rev,'source_filename':f'{folder}/{name}',
                      'path':str(path.relative_to(root(cfg))).replace('\\','/'),
                      'sha256':file_hash(path),'bytes':path.stat().st_size,'license':'MIT','url':url}
            records.append(record)
    lock = {'upstream_revision':revision,'parity_revision':parity_revision,
            'upstream_license':'MIT','files':records}
    immutable_json(lockpath,lock)
    immutable_json(published,lock)
    return lock

def verify_assets(cfg):
    path = root(cfg)/'assets/assets.lock.json'
    if not path.exists():
        return acquire(cfg)
    lock = json.loads(path.read_text())
    published = root(cfg)/'asset-lock.json'
    if published.exists() and json.loads(published.read_text()) != lock:
        raise ValueError('Local assets differ from published acquisition lock')
    expected = cfg['model']
    if lock['upstream_revision'] != expected['upstream_revision']:
        raise ValueError('Source revision mismatch')
    for record in lock['files']:
        key = 'dataset_revision' if record['repo'].endswith('ncm-datasets') else 'checkpoint_revision'
        if record['repo'].startswith('hazyresearch/') and record['revision'] != expected[key]:
            raise ValueError('Asset revision mismatch')
        if file_hash(root(cfg)/record['path']) != record['sha256']:
            raise ValueError(f'Asset hash mismatch: {record["path"]}')
    vendor = root(cfg)/'vendor/ncm'
    if subprocess.check_output(['git','-C',str(vendor),'rev-parse','HEAD'],text=True).strip() != lock['upstream_revision']:
        raise ValueError('Upstream checkout revision mismatch')
    if subprocess.check_output(['git','-C',str(vendor),'status','--porcelain','--untracked-files=no'],text=True).strip():
        raise ValueError('Upstream source is modified')
    return lock
