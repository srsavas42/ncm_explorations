import numpy as np
import pytest
from scripts.explore_codes_competitor import compare_codes,probability

def test_first_divergence_and_prefix_persists_after_matching_later_level():
    a = np.array([1,2,3,4,5,6])
    b = np.array([1,9,3,4,5,6])
    rows,first = compare_codes(a,b,[1,2,3])
    assert first == 2
    assert [r['different_codes'] for r in rows] == [0,1,0]
    assert [r['same_prefix'] for r in rows] == [True,False,False]
    assert compare_codes(a,a,[1,2,3])[1] is None

def test_incomplete_code_trace_rejected():
    with pytest.raises(ValueError):
        compare_codes(np.array([1]),np.array([1]),[1,2])

def test_competitor_probability_includes_special_tokens_and_is_shift_invariant():
    scores = np.zeros((12,89,12))
    scores[:,60,11] = 100
    trace = {'full_logits':scores}
    # Cell r7c1 maps to token offset 60.
    p = probability(trace,54,7)
    assert np.all(p < 1e-40)
    assert np.allclose(p,probability({'full_logits':scores+500},54,7),rtol=1e-12,atol=0)
