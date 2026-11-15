import copy
import json
from importlib.resources import files
from collections import Counter
import random
import numpy as np
import pytest
from ncm_probe.opposite_puzzles import (ARMS,validate,transformed,base_labels,components,
                                       swapped,make_base,delta)
from ncm_probe.opposite_analysis import assignment_curve,family_metrics
from ncm_probe.sudoku import parse,solutions,eligible,candidates,rename,BOXES
from ncm_probe.adapter import OFFSETS,DIGIT_IDS

def fixture():
    return json.loads(files('ncm_probe').joinpath('fixtures/opposite-engineering.json').read_text())

def test_opposite_fixture_has_distinct_unique_answers_and_rule_free_controls():
    f = fixture()
    checks = validate(f)
    assert checks == f['checks']
    p,q = f['locations']
    d,e = f['digit'],f['rival']
    assert len(solutions(parse(f['base']),3)) == 2
    assert f['solution_P'] != f['solution_Q']
    counts = []
    for arm in ARMS:
        board = f['boards'][arm]
        assert len(solutions(parse(board))) == 1
        assert sum(bool(v) for v in parse(board)) == 35
        counts.append(Counter(v for v in parse(board) if v))
    assert counts[0] == counts[1] == counts[2] == counts[3]
    assert set(eligible(f['boards']['rule_P'],p,d)[2]) == {p}
    assert set(eligible(f['boards']['rule_Q'],q,d)[2]) == {q}
    for arm in ('control_P','control_Q'):
        assert base_labels(f['boards'][arm],p,q,d,e)
        assert candidates(f['boards'][arm])[p] == candidates(f['boards'][arm])[q] == {d,e}
        box = BOXES[(p//27)*3+(p%9)//3]
        assert all(candidates(f['boards'][arm])[i] == candidates(f['base'])[i] for i in box)
    ep = f['endpoints']
    assert delta(ep['rule_P'],ep['rule_Q']) == delta(ep['control_P'],ep['control_Q'])

def test_opposite_rename_and_inverse_preserve_labels():
    f = fixture()
    g = transformed(f)
    validate(g)
    inv = [f['permutation'].index(d)+1 for d in range(1,10)]
    for arm in ARMS:
        assert rename(g['boards'][arm],inv) == f['boards'][arm]

def test_connected_swap_preserves_solution_and_scaffold_is_seeded():
    f = fixture()
    comp = tuple(f['trade_cells'])
    assert comp in components(f['solution_P'],f['digit'],f['rival'])
    assert swapped(f['solution_P'],comp,f['digit'],f['rival']) == f['solution_Q']
    a = make_base(f,random.Random(123),3,Counter())
    b = make_base(f,random.Random(123),3,Counter())
    assert a == b
    assert a is not None and sum(bool(x) for x in parse(a)) == 34

def test_fake_control_and_corrupt_trade_rejected():
    f = fixture()
    bad = copy.deepcopy(f)
    bad['boards']['control_P'] = f['boards']['rule_P']
    bad['endpoints']['control_P'] = f['endpoints']['rule_P']
    with pytest.raises(ValueError):
        validate(bad)
    bad = copy.deepcopy(f)
    bad['trade_cells'] = bad['trade_cells'][:-1]
    with pytest.raises(ValueError):
        validate(bad)

def synthetic(q,f):
    full = np.zeros((12,89,12),dtype=np.float32)
    p,u = f['locations']
    d,e = f['digit'],f['rival']
    for cell,sign in ((p,1),(u,-1)):
        full[:,OFFSETS[cell],d] = sign*q/2
        full[:,OFFSETS[cell],e] = -sign*q/2
    raw = full.argmax(-1)
    return {'full_logits':full,'digit_logits':full[:,OFFSETS][:,:,DIGIT_IDS],
            'winners':raw[:,OFFSETS],'raw_tokens':raw,'code_ids':np.zeros(322,dtype=int),
            'seconds':np.array(1.),'peak_memory_bytes':np.array(100)}

def test_directional_primary_control_interaction_and_final_failures_retained():
    f = fixture()
    traces = {arm:synthetic(q,f) for arm,q in zip(ARMS,[2,-2,1,-1])}
    row,_,_ = family_metrics(f,traces,list(range(1,7)))
    assert row['D_rule'] == 4
    assert row['D_control'] == 2
    assert row['specificity'] == 2
    assert not row['final_valid_rule_P']
    swapped_traces = dict(traces,rule_P=traces['rule_Q'],rule_Q=traces['rule_P'])
    altered,_,_ = family_metrics(f,swapped_traces,list(range(1,7)))
    assert altered['D_rule'] == -4
    assert altered['specificity'] == -6
    equal,_,_ = family_metrics(f,{a:synthetic(1,f) for a in ARMS},list(range(1,7)))
    assert equal['D_rule'] == equal['D_control'] == equal['specificity'] == 0

def test_assignment_preference_invariant_to_cellwise_logit_offsets():
    f = fixture()
    trace = synthetic(2,f)
    shifted = copy.deepcopy(trace)
    rng = np.random.default_rng(13)
    shifted['full_logits'] = shifted['full_logits'].astype(float)+rng.normal(size=(12,89,1))*5
    shifted['digit_logits'] = shifted['full_logits'][:,OFFSETS][:,:,DIGIT_IDS]
    assert np.allclose(assignment_curve(trace,f),assignment_curve(shifted,f),rtol=0,atol=1e-12)

def test_special_token_prevents_permanent_pair_correctness():
    f = fixture()
    traces = {arm:synthetic(q,f) for arm,q in zip(ARMS,[2,-2,1,-1])}
    traces['rule_P']['winners'][-1,f['locations'][0]] = 11
    row,_,_ = family_metrics(f,traces,list(range(1,7)))
    assert row['stable_rule_P'] == 13
    assert row['D_rule'] == 4
