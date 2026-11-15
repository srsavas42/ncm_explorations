import json
from importlib.resources import files
import numpy as np
import pytest
from ncm_probe import adapter
from ncm_probe.adapter import OFFSETS,DIGIT_IDS
from ncm_probe.opposite_run import run_families
from ncm_probe.storage import atomic_json

def data():
    full = np.zeros((12,89,12),dtype=np.float32)
    raw = full.argmax(-1)
    return {'full_logits':full,'digit_logits':full[:,OFFSETS][:,:,DIGIT_IDS],
            'winners':raw[:,OFFSETS],'raw_tokens':raw,'code_ids':np.zeros(322,dtype=int),
            'seconds':np.array(.01),'peak_memory_bytes':np.array(10)}

def fixture():
    return json.loads(files('ncm_probe').joinpath('fixtures/opposite-engineering.json').read_text())

def test_quadruplet_runner_resumes_eight_trajectories(tmp_path,monkeypatch):
    class Fake:
        identity = {'test':'opposite-only'}
        levels = [1,2,4,6,9,13,18,26,37,50,67,89]
        calls = 0
        def __init__(self,cfg): pass
        def validate_parity(self,path): atomic_json(path,{'passed':True})
        def trace(self,board):
            type(self).calls += 1
            return data()
    monkeypatch.setattr(adapter,'CPUAdapter',Fake)
    cfg = {'study':{'compute_budget_seconds':30}}
    first = run_families(cfg,[fixture()],tmp_path,'manifest',True)
    assert len(first['boards']) == Fake.calls == 8
    second = run_families(cfg,[fixture()],tmp_path,'manifest',True)
    assert Fake.calls == 8 and first == second
    assert json.loads((tmp_path/'run-cost.json').read_text())['cache_hits'] == 8

def test_missing_arm_is_engineering_failure_not_sudoku_failure(tmp_path,monkeypatch):
    class Fake:
        identity = {'test':'opposite-failure'}
        levels = [1,2,4,6,9,13,18,26,37,50,67,89]
        def __init__(self,cfg): self.calls = 0
        def validate_parity(self,path): pass
        def trace(self,board):
            self.calls += 1
            if self.calls == 1: raise RuntimeError('test failure')
            return data()
    monkeypatch.setattr(adapter,'CPUAdapter',Fake)
    with pytest.raises(RuntimeError,match='Engineering failures remain'):
        run_families({'study':{'compute_budget_seconds':30}},[fixture()],tmp_path,'manifest',True)
    rows = json.loads((tmp_path/'trace-index.json').read_text())['boards']
    assert len(rows) == 8
    assert sum(r['status'] == 'engineering_failure' for r in rows) == 1
