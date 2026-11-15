import copy
import random
import pytest
from ncm_probe.sudoku import (parse,load_fixture,candidates,eligible,solutions,unique,
                             rename,move,validate_triplet,PEERS)
from ncm_probe.cohort import (transformed,group_key,split_for,find_triplet,decode_source,
                             mismatch,read_rows)
from collections import Counter

def test_fixture_assertions_and_exclusion_geometry():
    f = load_fixture()
    for arm in 'ABC':
        assert candidates(f['boards'][arm])[65] == {3,7}
        assert sum(bool(x) for x in parse(f['boards'][arm])) == 35
    assert eligible(f['boards']['B'],65,7)[2] == (56,65)
    assert eligible(f['boards']['A'],65,7)[2] == (65,)
    assert f['checks']['A']['target_col_count'] > f['checks']['B']['target_col_count'] > 1
    assert move(f['boards']['B'],10,59,7) == f['boards']['A']
    assert move(f['boards']['B'],30,4,7) == f['boards']['C']

@pytest.mark.parametrize('board',['11'+'.'*79,'x'*81,'1'*80,'0'*82])
def test_reject_malformed_and_conflicting(board):
    with pytest.raises(ValueError):
        parse(board)

def test_exact_solver_nonunique_unsatisfiable_and_corrupt_solution():
    f = load_fixture()
    assert len(solutions(parse('.'*81))) == 2
    assert not unique('.'*81,f['solution'])
    corrupt = f['solution'][:-1]+'1'
    with pytest.raises(ValueError):
        parse(corrupt)
    # Locally legal wrong clue: unique completion is destroyed, not a givens conflict.
    b = list(parse(f['boards']['B']))
    wrong = next((i,d) for i,cs in enumerate(candidates(b)) for d in sorted(cs)
                 if d != int(f['solution'][i]) and not solutions(tuple(b[:i]+[d]+b[i+1:])))
    i,d = wrong
    assert not solutions(tuple(b[:i]+[d]+b[i+1:]))

def test_permutation_invariants_and_round_trip():
    f = load_fixture()
    f['permutation'] = [9,1,6,4,5,2,3,8,7]
    g = transformed(f)
    validate_triplet(g)
    inverse = [f['permutation'].index(i)+1 for i in range(1,10)]
    for arm in 'ABC':
        assert rename(g['boards'][arm],inverse) == f['boards'][arm]
    assert group_key(g['solution']) == group_key(f['solution'])
    assert split_for(group_key(g['solution']),42) == split_for(group_key(f['solution']),42)

def test_symmetry_grouping_transpose():
    f = load_fixture()
    s = f['solution']
    transpose = ''.join(s[9*c+r] for r in range(9) for c in range(9))
    assert group_key(s) == group_key(transpose)

def test_builder_is_deterministic_and_model_blind():
    f = load_fixture()
    results = [find_triplet(f['boards']['B'],f['solution'],random.Random(7),Counter()) for _ in range(2)]
    assert results[0] == results[1]
    assert results[0] is not None
    validate_triplet(results[0])
    assert all(i not in PEERS[results[0]['target']] for e in results[0]['edits'].values() for i in e)

def test_clue_change_fails_validation():
    f = load_fixture()
    f['boards']['A'] = f['boards']['B']
    with pytest.raises(AssertionError):
        validate_triplet(f)

def test_matching_prefers_shared_removed_clue():
    checks = {'A':{'row':2,'col':3,'forced':6},'C':{'row':2,'col':3,'forced':6}}
    _,shared = mismatch(65,[10,59],[10,4],checks)
    _,other = mismatch(65,[10,59],[30,4],checks)
    assert shared < other

def test_pickle_rejects_code_objects(tmp_path):
    import pickle
    path = tmp_path/'bad.pickle'
    path.write_bytes(pickle.dumps(eval))
    with pytest.raises(pickle.UnpicklingError):
        read_rows(path)
