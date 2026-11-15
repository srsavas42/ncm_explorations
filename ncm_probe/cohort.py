"""Seeded, model-blind selection. Only forward (source=B) search is allowed."""
from collections import Counter
import hashlib
import io
import json
import pickle
import random
import time
from .sudoku import (parse,string,candidates,eligible,unique,move,geometry,difficulty,
                     validate_triplet,control_cells,load_fixture,rename,canonical)
from .storage import (root,outdir,digest,immutable_json,atomic_json,now,frozen_config)
from .assets import verify_assets

class PlainUnpickler(pickle.Unpickler):
    def find_class(self,module,name):
        raise pickle.UnpicklingError('Dataset must contain plain lists and integers')

def read_rows(path):
    return PlainUnpickler(io.BytesIO(path.read_bytes())).load()

def decode_source(tokens):
    if len(tokens) == 91:
        if tokens[0] != 11 or tokens[-1] != 11:
            raise ValueError('Invalid prefix framing')
        tokens = tokens[1:-1]
    if len(tokens) != 89 or any(tokens[i] != 10 for i in range(9,89,10)):
        raise ValueError('Invalid source tokenization')
    return string(parse([tokens[10*r+c] for r in range(9) for c in range(9)]))

def group_key(solution):
    # First-occurrence digit canonicalization plus all 8 square dihedral symmetries.
    b = parse(solution)
    variants = []
    for flip in (False,True):
        for turns in range(4):
            cells = []
            for r in range(9):
                for c in range(9):
                    rr,cc = r,8-c if flip else c
                    for _ in range(turns):
                        rr,cc = 8-cc,rr
                    cells.append(b[9*rr+cc])
            variants.append(canonical(cells))
    return hashlib.sha256(min(variants).encode()).hexdigest()[:20]

def split_for(key,seed):
    # Independent of input order, model behavior, and source/search budget.
    return 'pilot' if int(digest([seed,key])[:8],16)%5 == 0 else 'confirmation'

def mismatch(t,a,c,checks):
    ga = [geometry(t,i) for i in a]
    gc = [geometry(t,i) for i in c]
    components = {
        'different_removed_clue':int(a[0] != c[0]),
        'geometry_l1':sum(abs(x-y) for u,v in zip(ga,gc) for x,y in zip(u,v)),
        'target_count_l1':sum(abs(checks['A'][k]-checks['C'][k]) for k in ('row','col')),
        'forced_cells_abs':abs(checks['A']['forced']-checks['C']['forced']),
    }
    return components,list(components.values())

def find_triplet(board,solution,rng,counts):
    b,s = parse(board),parse(solution)
    cs = candidates(b)
    targets = [i for i,c in enumerate(cs) if len(c) == 2 and s[i] in c]
    rng.shuffle(targets)
    counts['two_candidate_targets'] += len(targets)
    for t in targets:
        d = s[t]
        row,col,box = eligible(b,t,d)
        if len(box) != 2 or len(row) < 2 or len(col) < 2:
            counts['target_rule_rejected'] += 1
            continue
        counts['eligible_starting_targets'] += 1
        u = next(i for i in box if i != t)
        from .sudoku import PEERS
        forbidden = PEERS[t] | {t}
        removed = [i for i,x in enumerate(b) if x == d and i not in forbidden]
        revealed = [i for i,x in enumerate(b) if not x and s[i] == d and i not in forbidden]
        choices = {'A':[],'C':[]}
        for old in removed:
            for new in revealed:
                edited = move(b,old,new,d)
                er,ec,eb = eligible(edited,t,d)
                if len(er) < 2 or len(ec) < 2:
                    counts['edit_row_column_rejected'] += 1
                    continue
                arm = 'A' if set(eb) == {t} else 'C' if set(eb) == {t,u} else None
                if arm is None:
                    counts['edit_box_rejected'] += 1
                    continue
                if not unique(edited,solution):
                    counts['edit_nonunique_rejected'] += 1
                    continue
                choices[arm].append((edited,[old,new],{'row':len(er),'col':len(ec),
                                       'forced':difficulty(edited)['initial_forced_cells']}))
        counts['eligible_A_moves'] += len(choices['A'])
        counts['eligible_C_moves'] += len(choices['C'])
        if not choices['A']:
            counts['target_no_A'] += 1
            continue
        counts['eligible_AB_targets'] += 1
        if not choices['C']:
            counts['target_AB_only'] += 1
            continue
        counts['eligible_triplet_targets'] += 1
        ranked = []
        for a,ae,ac in choices['A']:
            for c,ce,cc in choices['C']:
                components,rank = mismatch(t,ae,ce,{'A':ac,'C':cc})
                ranked.append((rank,rng.random(),a,ae,c,ce,components))
        rank,_,a,ae,c,ce,components = min(ranked)
        f = {'boards':{'A':a,'B':board,'C':c},'solution':solution,'target':t,'digit':d,
             'rival':next(iter(cs[t]-{d})),'competitor':u,'edits':{'A':ae,'C':ce},
             'matching':components,'matching_rank':rank,
             'geometry':{'A':[geometry(t,i) for i in ae],'C':[geometry(t,i) for i in ce]},
             'excludes_competitor':ae[1], 'source_role':'B'}
        f['checks'] = validate_triplet(f)
        f['control_cells'] = control_cells(f)
        return f
    return None

def transformed(f):
    result = dict(f)
    permutation = f['permutation']
    result['boards'] = {a:rename(b,permutation) for a,b in f['boards'].items()}
    result['solution'] = rename(f['solution'],permutation)
    for key in ('digit','rival'):
        result[key] = permutation[f[key]-1]
    result['control_cells'] = [dict(c,digit=permutation[c['digit']-1],rival=permutation[c['rival']-1])
                               for c in f['control_cells']]
    return result

def prepare(cfg):
    start = time.perf_counter()
    lock = verify_assets(cfg)
    if cfg['study']['search_direction'] != 'B-only':
        raise ValueError('Only predeclared forward search is implemented')
    output = outdir(cfg)
    protocol_path = output/'protocol.json'
    if protocol_path.exists():
        protocol = json.loads(protocol_path.read_text())
        if protocol['config'] != frozen_config(cfg) or protocol['assets'] != lock:
            raise ValueError('Frozen protocol changed; select a new version/output')
    else:
        protocol = {'frozen_at':now(),'config':frozen_config(cfg),'assets':lock,
                    'primary':'mean over families of M(A)-M(C)',
                    'selection':'seeded source order; first qualifying shuffled target; lexicographic A/C ranking',
                    'matching_order':['same removed clue','geometry L1','target row/column counts L1','forced cells absolute'],
                    'split_rule':'SHA256(seed,family) first 32 bits modulo 5: 0 pilot, others confirmation',
                    'grouping':'digit first occurrence + D4; other unknown Sudoku automorphisms not detected',
                    'search_stopping':'stop at planned eligible n or fixed source-row budget; no outcome-dependent search',
                    'selection_software_sha256':selection_hash(cfg)}
        immutable_json(protocol_path,protocol)
    puzzles = read_rows(root(cfg)/'assets/dataset/puzzles.pickle')
    solutions = read_rows(root(cfg)/'assets/dataset/solutions.pickle')
    if len(puzzles) != len(solutions):
        raise ValueError('Input and solution row counts differ')
    groups,rows,failures = {},[],Counter()
    for i,(p,s) in enumerate(zip(puzzles,solutions)):
        try:
            board,solution = decode_source(p),decode_source(s)
            key = group_key(solution)
            groups.setdefault(key,[]).append(i)
            rows.append((i,board,solution,key))
        except ValueError:
            failures['malformed_source'] += 1
    fixture_key = group_key(load_fixture()['solution'])
    membership = [{'family_id':k,'source_rows':v,'split':'fixture' if k == fixture_key else split_for(k,cfg['study']['seed'])}
                  for k,v in sorted(groups.items())]
    immutable_json(output/'split-membership.json',membership)
    rng = random.Random(cfg['study']['seed'])
    rng.shuffle(rows)
    selected,seen,scanned_log = [],set(),[]
    counts = Counter(failures)
    for row,board,solution,key in rows:
        if counts['source_rows_scanned'] >= cfg['study']['source_budget'] or len(selected) >= cfg['study']['planned_n']:
            break
        counts['source_rows_scanned'] += 1
        reason = None
        if key == fixture_key:
            reason = 'fixture_family'
        elif split_for(key,cfg['study']['seed']) != cfg['study']['split']:
            reason = 'other_split'
        elif key in seen:
            reason = 'duplicate_family'
        else:
            seen.add(key)
            counts['unique_families_scanned'] += 1
            if sum(x != 0 for x in parse(board)) != 35:
                reason = 'not_35_clues'
            elif not unique(board,solution):
                reason = 'source_not_unique_shared_solution'
            else:
                f = find_triplet(board,solution,rng,counts)
                if f is None:
                    reason = 'no_triplet'
                else:
                    permutation = list(range(1,10))
                    prng = random.Random(digest([cfg['study']['seed'],key,'rename']))
                    while permutation == list(range(1,10)):
                        prng.shuffle(permutation)
                    f.update(family_id=key,source_row=row,source_rows=groups[key],
                             split=cfg['study']['split'],permutation=permutation)
                    renamed = transformed(f)
                    validate_triplet(renamed)
                    inverse = [permutation.index(d)+1 for d in range(1,10)]
                    assert all(rename(renamed['boards'][a],inverse) == f['boards'][a] for a in 'ABC')
                    selected.append(f)
                    reason = 'accepted'
        counts[reason] += 1
        scanned_log.append({'source_row':row,'family_id':key,'reason':reason})
        if counts['source_rows_scanned']%100 == 0:
            print(f'Scanned {counts["source_rows_scanned"]} rows: {len(selected)} triplets',flush=True)
    counts['total_source_rows'] = len(puzzles)
    counts['total_unique_families'] = len(groups)
    counts['selected_triplets'] = len(selected)
    counts['eligible_per_100_scanned_rows'] = 100*len(selected)/max(1,counts['source_rows_scanned'])
    manifest = {'protocol_hash':digest(protocol),'split_membership_hash':digest(membership),
                'families':selected,'counts':dict(counts),'source_scan':scanned_log}
    immutable_json(output/'families.json',manifest)
    immutable_json(output/'families.sha256.json',{'sha256':digest(manifest)})
    atomic_json(output/'prepare-timing.json',{'seconds':time.perf_counter()-start})
    print(json.dumps(dict(counts),indent=2),flush=True)
    return manifest

def load_manifest(cfg):
    output = outdir(cfg)
    protocol = json.loads((output/'protocol.json').read_text())
    if protocol['config'] != frozen_config(cfg):
        raise ValueError('Config differs from frozen protocol')
    manifest = json.loads((output/'families.json').read_text())
    expected = json.loads((output/'families.sha256.json').read_text())['sha256']
    if digest(manifest) != expected or manifest['protocol_hash'] != digest(protocol):
        raise ValueError('Immutable manifest or protocol changed')
    membership = json.loads((output/'split-membership.json').read_text())
    if digest(membership) != manifest['split_membership_hash']:
        raise ValueError('Split membership changed')
    # Source code changes after selection must receive a new protocol version.
    if selection_hash(cfg) != protocol['selection_software_sha256']:
        raise ValueError('Selection software changed since preparation; version the study output')
    return manifest

def selection_hash(cfg):
    return digest({name:(root(cfg)/'ncm_probe'/name).read_text() for name in ('cohort.py','sudoku.py')})
