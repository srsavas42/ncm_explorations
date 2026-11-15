import json
from pathlib import Path
import numpy as np
import pytest
from ncm_probe import runner
from ncm_probe.adapter import OFFSETS
from ncm_probe.sudoku import load_fixture
from ncm_probe.storage import atomic_json

def trace_data():
    full = np.zeros((12,89,12),dtype=np.float32)
    return {'full_logits':full,'digit_logits':full[:,OFFSETS][:,:,1:10],
            'raw_tokens':full.argmax(-1),'winners':np.zeros((12,81),dtype=int),
            'code_ids':np.zeros(322,dtype=int),'seconds':np.array(.01),'peak_memory_bytes':np.array(123)}

@pytest.mark.parametrize('corrupt_bytes',[b'incomplete npz',b'PK\x03\x04truncated zip'])
def test_resume_reuses_all_completed_traces_and_recovers_corruption(tmp_path,monkeypatch,corrupt_bytes):
    class FakeAdapter:
        calls = 0
        identity = {'adapter_version':'synthetic-test-only'}
        levels = list(range(12))
        def __init__(self,cfg):
            pass
        def validate_parity(self,path):
            atomic_json(path,{'passed':True})
        def trace(self,board):
            type(self).calls += 1
            return trace_data()
    monkeypatch.setattr(runner,'CPUAdapter',FakeAdapter)
    cfg = {'study':{'compute_budget_seconds':30}}
    f = load_fixture()
    first = runner.run_families(cfg,[f],tmp_path,'fixed-manifest',True)
    assert FakeAdapter.calls == 3
    second = runner.run_families(cfg,[f],tmp_path,'fixed-manifest',True)
    assert FakeAdapter.calls == 3 and first == second
    cost = json.loads((tmp_path/'run-cost.json').read_text())
    assert cost['cache_hits'] == 3 and cost['new_model_calls'] == 0
    bad = tmp_path/first['boards'][0]['path']
    bad.write_bytes(corrupt_bytes)
    third = runner.run_families(cfg,[f],tmp_path,'fixed-manifest',True)
    assert FakeAdapter.calls == 4
    assert all(r['status'] == 'complete' for r in third['boards'])

def test_engineering_failure_is_reported_and_other_arms_continue(tmp_path,monkeypatch):
    class FailingAdapter:
        identity = {'adapter_version':'synthetic-failure-test-only'}
        levels = list(range(12))
        def __init__(self,cfg):
            self.calls = 0
        def validate_parity(self,path):
            pass
        def trace(self,board):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError('test interruption')
            return trace_data()
    monkeypatch.setattr(runner,'CPUAdapter',FailingAdapter)
    index = runner.run_families({'study':{'compute_budget_seconds':30}},[load_fixture()],tmp_path,'fixed',True)
    assert [r['status'] for r in index['boards']] == ['engineering_failure','complete','complete']
    assert 'test interruption' in index['boards'][0]['error']
    assert len((tmp_path/'failures.jsonl').read_text().splitlines()) == 1
