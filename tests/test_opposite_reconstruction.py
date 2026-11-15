import csv
from scripts.reproduce_opposite_estimate import reconstruct

def test_independent_opposite_reconstruction_and_missing_row(tmp_path):
    path = tmp_path/'families.csv'
    rows = [
        dict(transform='original',missing=False,early_rule_P=2.,early_rule_Q=-2.,
             early_control_P=1.,early_control_Q=-1.,D_rule=4.,D_control=2.,specificity=2.),
        dict(transform='original',missing=False,early_rule_P=1.,early_rule_Q=1.,
             early_control_P=0.,early_control_Q=0.,D_rule=0.,D_control=0.,specificity=0.),
        dict(transform='original',missing=True),
    ]
    with path.open('w',newline='') as stream:
        writer = csv.DictWriter(stream,fieldnames=list(rows[0]))
        writer.writeheader()
        writer.writerows(rows)
    result = reconstruct(path)
    assert result['n'] == 2
    assert result['metrics']['D_rule']['mean'] == 2.
    assert result['metrics']['D_rule']['ci95'] == [0.,4.]
    assert result['metrics']['D_control']['mean'] == result['metrics']['specificity']['mean'] == 1.
