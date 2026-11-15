from collections import Counter
import json
import random
import time
from .assets import verify_assets
from .cohort import read_rows,decode_source,group_key
from .sudoku import parse,unique,load_fixture
from .opposite_puzzles import enumerate_candidates,make_base,build,validate,transformed
from .storage import root,digest,file_hash,immutable_json,atomic_json,now

def selection_hash(cfg):
    return digest({name:file_hash(root(cfg)/'ncm_probe'/name) for name in
                   ('opposite_prepare.py','opposite_puzzles.py','sudoku.py','cohort.py')})

def exclusions(cfg,source_solutions):
    excluded = {group_key(load_fixture()['solution'])}
    evidence = {}
    for name in ('pilot-v1','confirmation-v1'):
        path = root(cfg)/'outputs'/name/'families.json'
        manifest = json.loads(path.read_text())
        excluded.update(r['family_id'] for r in manifest['source_scan'])
        excluded.update(f['family_id'] for f in manifest['families'])
        evidence[name] = file_hash(path)
    lo,hi = cfg['study']['engineering_excluded_rows']
    for row in [0,1]+list(range(lo,hi)):
        excluded.add(group_key(decode_source(source_solutions[row])))
    return excluded,evidence

def output_dir(cfg):
    return root(cfg)/cfg['study']['output']

def frozen_config(cfg):
    return {k:v for k,v in cfg.items() if not k.startswith('_')}

def prepare(cfg):
    start = time.perf_counter()
    assets = verify_assets(cfg)
    output = output_dir(cfg)
    pp = output/'protocol.json'
    settings = frozen_config(cfg)
    code = selection_hash(cfg)
    text = (root(cfg)/'docs/opposite-protocol.md').read_text(encoding='utf-8')
    if pp.exists():
        protocol = json.loads(pp.read_text())
        if protocol['config'] != settings or protocol['selection_hash'] != code or protocol['protocol_text'] != text:
            raise ValueError('Frozen follow-up protocol differs; use a new study version')
    else:
        protocol = {'frozen_at':now(),'config':settings,'assets':assets,
                    'selection_hash':code,'protocol_text':text,
                    'primary':'early assignment-preference shift rule_P minus rule_Q; predicted positive',
                    'secondary':'rule shift minus control shift; no promotion to primary'}
        immutable_json(pp,protocol)
    puzzles = read_rows(root(cfg)/'assets/dataset/puzzles.pickle')
    supplied = read_rows(root(cfg)/'assets/dataset/solutions.pickle')
    if len(puzzles) != len(supplied):
        raise ValueError('Source row mismatch')
    excluded,evidence = exclusions(cfg,supplied)
    immutable_json(output/'excluded-families.json',{'family_keys':sorted(excluded),'prior_manifests':evidence,
                   'engineering_source_rows':cfg['study']['engineering_excluded_rows'],'parity_source_rows':[0,1]})
    rng = random.Random(cfg['study']['seed'])
    order = list(range(len(supplied)))
    rng.shuffle(order)
    target = cfg['study']['pilot_n']+cfg['study']['confirmation_n']
    counts = Counter()
    selected,scanned = [],[]
    used,seen = set(),set()
    for row in order[:cfg['study']['source_budget']]:
        if len(selected) >= target:
            break
        counts['source_rows_scanned'] += 1
        s = decode_source(supplied[row])
        key = group_key(s)
        reason = None
        if key in excluded:
            reason = 'prior_or_engineering_family'
        elif key in used or key in seen:
            reason = 'reused_solution_family'
        else:
            seen.add(key)
            counts['fresh_source_families'] += 1
            if not unique(decode_source(puzzles[row]),s):
                reason = 'source_not_unique'
            else:
                options = enumerate_candidates(s,cfg['study']['component_sizes'])
                counts['geometry_eligible_candidates'] += len(options)
                rng.shuffle(options)
                for candidate in options[:cfg['study']['candidate_cap_per_source']]:
                    counts['candidates_attempted'] += 1
                    keys = [group_key(candidate['solution_'+x]) for x in 'PQ']
                    if any(k in excluded or k in used for k in keys):
                        counts['alternate_family_excluded_or_reused'] += 1
                        continue
                    base = make_base(candidate,rng,cfg['study']['deletion_orders'],counts)
                    if base is None:
                        counts['no_34_clue_base'] += 1
                        continue
                    f = build(candidate,base,rng,counts)
                    if f is None:
                        counts['no_valid_quadruplet'] += 1
                        continue
                    permutation = list(range(1,10))
                    prng = random.Random(digest([cfg['study']['seed'],sorted(keys),'rename']))
                    while permutation == list(range(1,10)):
                        prng.shuffle(permutation)
                    split = 'pilot' if len(selected) < cfg['study']['pilot_n'] else 'confirmation'
                    f.update(family_id=digest(sorted(keys))[:20],solution_family_keys=keys,
                             source_row=row,source_family_key=key,source_solution=s,
                             source_puzzle=decode_source(puzzles[row]),split=split,permutation=permutation)
                    validate(transformed(f))
                    used.update(keys)
                    selected.append(f)
                    reason = 'accepted_'+split
                    break
                if reason is None:
                    reason = 'no_eligible_quadruplet'
        counts[reason] += 1
        scanned.append({'source_row':row,'family_key':key,'reason':reason})
        if counts['source_rows_scanned']%100 == 0:
            print(f"Scanned {counts['source_rows_scanned']}: {len(selected)} opposite-answer families",flush=True)
    counts['selected_families'] = len(selected)
    counts['total_source_rows'] = len(supplied)
    manifest = {'protocol_hash':digest(protocol),'selection_hash':code,'exclusion_hash':file_hash(output/'excluded-families.json'),
                'families':selected,'counts':dict(counts),'source_scan':scanned}
    immutable_json(output/'families.json',manifest)
    immutable_json(output/'families.sha256.json',{'sha256':digest(manifest)})
    atomic_json(output/'prepare-timing.json',{'seconds':time.perf_counter()-start})
    print(json.dumps(dict(counts),indent=2))
    return manifest

def load_manifest(cfg):
    output = output_dir(cfg)
    p = json.loads((output/'protocol.json').read_text())
    f = json.loads((output/'families.json').read_text())
    if p['config'] != frozen_config(cfg) or p['selection_hash'] != selection_hash(cfg):
        raise ValueError('Frozen configuration or selection software differs')
    if digest(p) != f['protocol_hash'] or digest(f) != json.loads((output/'families.sha256.json').read_text())['sha256']:
        raise ValueError('Follow-up protocol or manifest integrity failure')
    if file_hash(output/'excluded-families.json') != f['exclusion_hash']:
        raise ValueError('Exclusion list changed')
    return f

def audit(cfg):
    manifest = load_manifest(cfg)
    exclusion = json.loads((output_dir(cfg)/'excluded-families.json').read_text())
    excluded = set(exclusion['family_keys'])
    used = set()
    src = read_rows(root(cfg)/'assets/dataset/solutions.pickle')
    for f in manifest['families']:
        assert decode_source(src[f['source_row']]) == f['source_solution']
        assert f['source_solution'] in (f['solution_P'],f['solution_Q'])
        assert group_key(f['source_solution']) == f['source_family_key']
        keys = {group_key(f['solution_'+x]) for x in 'PQ'}
        assert keys == set(f['solution_family_keys'])
        assert not keys & (used | excluded)
        used.update(keys)
        assert validate(f) == f['checks']
        validate(transformed(f))
    result = {'families_verified':len(manifest['families']),'both_solution_keys_reserved':len(used),
              'freshness_disjoint':True,'pilot_confirmation_disjoint':True,
              'all_unique_arm_solutions_verified':True,'model_calls':0}
    atomic_json(output_dir(cfg)/'structural-audit.json',result)
    return result
