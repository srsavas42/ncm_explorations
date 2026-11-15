from scripts.explore_paired_prefix import category,aggregate

def test_four_way_counts_preserve_pairing_and_include_level_six():
    rows = [
        {'first_AB':None,'first_CB':None,'specificity':0.,'same_AC_through_6':True},
        {'first_AB':6,'first_CB':7,'specificity':2.,'same_AC_through_6':False},
        {'first_AB':8,'first_CB':1,'specificity':-1.,'same_AC_through_6':False},
        {'first_AB':2,'first_CB':3,'specificity':3.,'same_AC_through_6':False},
        {'first_AB':2,'first_CB':2,'specificity':0.,'same_AC_through_6':True},
    ]
    result = aggregate(rows)
    level = result['four_way_by_level'][5]
    assert [level[k] for k in ('neither','only_A','only_C','both')] == [1,1,1,2]
    assert result['first_divergence_counts']['AB']['never'] == 1
    assert result['first_divergence_counts']['CB']['never'] == 1
    assert result['first_divergence_ordering'] == {
        'A_earlier':2,'C_earlier':1,'same_first_level_or_both_never':2}
    contributions = result['primary_decomposition_by_level6_group']
    assert sum(r['contribution_to_overall_mean'] for r in contributions) == .8
    assert next(r for r in contributions if r['category'] == 'both')['same_AC_prefix_through_6'] == 1

def test_later_changes_do_not_count_as_early_and_never_is_distinct():
    assert category(7,None,6) == 'neither'
    assert category(7,None,7) == 'only_A'
    assert category(None,6,6) == 'only_C'
    result = aggregate([{'first_AB':12,'first_CB':None,'specificity':0.,'same_AC_through_6':True}])
    assert result['first_divergence_counts']['AB']['12'] == 1
    assert result['first_divergence_counts']['AB']['never'] == 0
