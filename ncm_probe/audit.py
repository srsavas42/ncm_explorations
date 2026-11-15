"""Rebuild selected puzzles independently from released source rows and edits."""
from .assets import verify_assets
from .cohort import read_rows,decode_source,load_manifest,transformed,group_key,split_for
from .storage import root,digest,atomic_json,outdir
from .sudoku import move,validate_triplet,control_cells,rename

def audit(cfg,other_cfg=None):
    verify_assets(cfg)
    manifest = load_manifest(cfg)
    puzzles = read_rows(root(cfg)/'assets/dataset/puzzles.pickle')
    solutions = read_rows(root(cfg)/'assets/dataset/solutions.pickle')
    for f in manifest['families']:
        source = decode_source(puzzles[f['source_row']])
        assert f['source_role'] == 'B' and source == f['boards']['B']
        assert decode_source(solutions[f['source_row']]) == f['solution']
        assert group_key(f['solution']) == f['family_id']
        assert split_for(f['family_id'],cfg['study']['seed']) == f['split']
        for arm in 'AC':
            assert move(source,*f['edits'][arm],f['digit']) == f['boards'][arm]
        assert validate_triplet(f) == f['checks']
        assert control_cells(f) == f['control_cells']
        validate_triplet(transformed(f))
    disjoint = None
    if other_cfg:
        other = load_manifest(other_cfg)
        assert not ({f['family_id'] for f in manifest['families']} &
                    {f['family_id'] for f in other['families']}), 'Family leakage'
        source_rows = {r for f in manifest['families'] for r in f['source_rows']}
        other_rows = {r for f in other['families'] for r in f['source_rows']}
        assert not source_rows & other_rows, 'Source row leakage'
        disjoint = True
    result = {'manifest_hash':digest(manifest),'families_rebuilt':len(manifest['families']),
              'all_structural_checks_passed':True,'other_cohort_disjoint':disjoint}
    atomic_json(outdir(cfg)/'independent-audit.json',result)
    return result
