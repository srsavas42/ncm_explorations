import copy
import numpy as np
import pytest
from ncm_probe.analysis import (contrast,family_metrics,stable_level,summary,grid_metrics)
from ncm_probe.adapter import (OFFSETS,DIGIT_IDS,solution_tokens,prefix,board_from_prefix,validate_trace)
from ncm_probe.runner import (save_trace,read_trace,cache_key)
from ncm_probe.sudoku import load_fixture
from ncm_probe.storage import immutable_json,digest

def synthetic(value=0):
    f = load_fixture()
    full = np.full((12,89,12),-10.,dtype=np.float32)
    for cell,offset in enumerate(OFFSETS):
        full[:,offset,int(f['solution'][cell])] = 1
    full[:,OFFSETS[f['target']],3] = 0
    full[:,OFFSETS[f['target']],7] = value
    raw = full.argmax(-1)
    return {'full_logits':full,'digit_logits':full[:,OFFSETS][:,:,DIGIT_IDS],
            'raw_tokens':raw,'winners':raw[:,OFFSETS],
            'code_ids':np.zeros(322,dtype=np.int64),
            'seconds':np.array(1.),'peak_memory_bytes':np.array(123456)}

def test_primary_numerical_acceptance_and_failed_boards_retained():
    f = load_fixture()
    traces = {a:synthetic(v) for a,v in zip('ABC',[2,.5,.75])}
    # A special-token winner is a miss even if the correct digit has a large margin.
    for trace in traces.values():
        trace['winners'][-1,f['target']] = 11
    row,_,_ = family_metrics(f,traces,list(range(1,7)))
    assert row['enabling'] == 1.5
    assert row['control'] == .25
    assert row['specificity'] == 1.25
    assert row['final_valid_A'] is False
    assert row['stable_A'] == 13
    swapped,_,_ = family_metrics(f,dict(A=traces['C'],B=traces['B'],C=traces['A']),list(range(1,7)))
    assert swapped['specificity'] == -1.25
    equal,_,_ = family_metrics(f,{a:synthetic(.5) for a in 'ABC'},list(range(1,7)))
    assert equal['specificity'] == equal['enabling'] == equal['control'] == 0

def test_signed_change_and_baseline_cancellation():
    assert contrast(2,.5,.75) == {'enabling':1.5,'control':.25,'specificity':1.25}
    assert contrast(2,99,.75)['specificity'] == 1.25
    assert contrast(3,.5,.75)['specificity'] == 2.25

@pytest.mark.parametrize('w,expected',[([7,7,7],1),([7,3,7],3),([7,7,11],4),([0,0,0],4)])
def test_stability_uses_full_vocabulary_winner(w,expected):
    assert stable_level(w,7) == expected

def test_digit_scores_do_not_hide_special_token_winner():
    trace = synthetic(2)
    trace['full_logits'][0,OFFSETS[65],11] = 50
    trace['raw_tokens'] = trace['full_logits'].argmax(-1)
    trace['winners'] = trace['raw_tokens'][:,OFFSETS]
    validate_trace(trace)
    assert trace['winners'][0,65] == 11
    f = load_fixture()
    assert not grid_metrics(trace,f['boards']['A'],f['solution'])[0]['digits_only']

def test_mapping_all_cells_and_boundaries():
    f = load_fixture()
    body = solution_tokens(f['solution'])
    assert len(body) == 89
    assert [body[i] for i in OFFSETS] == list(map(int,f['solution']))
    assert board_from_prefix(prefix(f['solution'])) == f['solution']
    assert OFFSETS[[0,8,9,72,80]].tolist() == [0,8,10,80,88]

def test_seeded_family_bootstrap_and_exact_ties():
    first = summary([1.25,-1.25,0],31,10000)
    assert first == summary([1.25,-1.25,0],31,10000)
    assert first['mean'] == 0 and first['ties'] == 1
    assert first['fraction_positive'] == 1/3
    assert summary([1.25],31,10000)['ci95'] == [1.25,1.25]

def test_cache_round_trip_and_corruption_detection(tmp_path):
    trace = synthetic(2)
    path = tmp_path/'trace.npz'
    board = load_fixture()['boards']['A']
    save_trace(path,trace,{'board':board,'identity_hash':'expected'})
    loaded,_ = read_trace(path,board,'expected')
    assert np.array_equal(loaded['full_logits'],trace['full_logits'])
    with pytest.raises(ValueError):
        read_trace(path,board,'other revision')
    bad = copy.deepcopy(trace)
    bad['digit_logits'][0,0,0] = np.nan
    with pytest.raises(ValueError):
        save_trace(path,bad,{})
    assert read_trace(path,board,'expected')

def test_wrong_winners_and_one_hot_substitution_rejected():
    trace = synthetic(2)
    trace['winners'][0,0] = 11
    with pytest.raises(ValueError):
        validate_trace(trace)
    trace = synthetic(2)
    trace['digit_logits'] = np.ones((12,81,9))
    with pytest.raises(ValueError):
        validate_trace(trace)

def test_cache_identity_and_frozen_manifest(tmp_path):
    assert cache_key('board',{'revision':'a'}) != cache_key('board',{'revision':'b'})
    assert cache_key('a',{}) != cache_key('b',{})
    path = tmp_path/'manifest.json'
    immutable_json(path,{'families':[1]})
    immutable_json(path,{'families':[1]})
    with pytest.raises(ValueError):
        immutable_json(path,{'families':[2]})
