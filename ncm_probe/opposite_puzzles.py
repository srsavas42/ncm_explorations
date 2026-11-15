"""Model-blind construction of opposite-answer box-hidden-single quadruplets.

No changes to the original experiment's selection modules or frozen outputs.
"""
from collections import Counter
import itertools
import random
from .sudoku import (parse,string,UNITS,BOXES,PEERS,candidates,eligible,solutions,unique,
                     difficulty,rename)
from .cohort import group_key

ARMS = ('rule_P','rule_Q','control_P','control_Q')

def components(solution,d,e):
    s = parse(solution)
    nodes = {i for i,v in enumerate(s) if v in (d,e)}
    graph = {i:set() for i in nodes}
    for unit in UNITS:
        a,b = [i for i in unit if i in nodes]
        graph[a].add(b)
        graph[b].add(a)
    remaining = set(nodes)
    result = []
    while remaining:
        stack,comp = [min(remaining)],set()
        while stack:
            i = stack.pop()
            if i not in comp:
                comp.add(i)
                stack.extend(sorted(graph[i]-comp,reverse=True))
        remaining -= comp
        result.append(tuple(sorted(comp)))
    return result

def swapped(solution,comp,d,e):
    s = list(parse(solution))
    for i in comp:
        if s[i] not in (d,e):
            raise ValueError('Invalid trade component')
        s[i] = e if s[i] == d else d
    return string(parse(s))

def delta(a,b):
    ar,ac = divmod(a,9)
    br,bc = divmod(b,9)
    return [abs(ar-br),abs(ac-bc)]

def endpoint_geometry(i,p):
    r,c = divmod(i,9)
    br,bc = (p//27)*3+1,((p%9)//3)*3+1
    return [int(r//3 == br//3),int(c//3 == bc//3),abs(r-br),abs(c-bc)]

def endpoint_options(sp,sq,comp,p,q,d):
    forbidden = PEERS[p] | PEERS[q] | {p,q}
    box = set(BOXES[(p//27)*3+(p%9)//3])
    return {
        'rule_P':[i for i in comp if sp[i] == d and i in PEERS[q] and i not in PEERS[p] and i not in box],
        'rule_Q':[i for i in comp if sq[i] == d and i in PEERS[p] and i not in PEERS[q] and i not in box],
        'control_P':[i for i in comp if sp[i] == d and i not in forbidden],
        'control_Q':[i for i in comp if sq[i] == d and i not in forbidden],
    }

def matched_endpoints(options,p):
    matches = []
    for values in itertools.product(*(options[a] for a in ARMS)):
        rp,rq,cp,cq = values
        if delta(rp,rq) != delta(cp,cq):
            continue
        gs = [endpoint_geometry(i,p) for i in values]
        if sorted(g[:2] for g in gs[:2]) != sorted(g[:2] for g in gs[2:]):
            continue
        # Required adjacency to the eliminated cell is the intervention; do not match it away.
        mismatch = sum(abs(a-b) for g,h in zip(gs[:2],gs[2:]) for a,b in zip(g[2:],h[2:]))
        matches.append({'endpoints':dict(zip(ARMS,values)),
                        'geometry':dict(zip(ARMS,gs)),
                        'matching':{'row_col_displacement':delta(rp,rq),
                                    'pooled_band_stack_exact':True,'box_center_distance_l1':mismatch}})
    return matches

def enumerate_candidates(solution,allowed_sizes):
    source = parse(solution)
    results = []
    for x,y in itertools.combinations(range(1,10),2):
        for comp in components(source,x,y):
            if len(comp) not in allowed_sizes:
                continue
            alt = parse(swapped(source,comp,x,y))
            for box in BOXES:
                pair = sorted(set(box)&set(comp))
                if len(pair) != 2:
                    continue
                p,q = pair
                for d,e in ((x,y),(y,x)):
                    sp,sq = (source,alt) if source[p] == d else (alt,source)
                    if sp[q] != e or sq[p] != e or sq[q] != d:
                        raise AssertionError('Trade target assignment')
                    options = endpoint_options(sp,sq,comp,p,q,d)
                    matches = matched_endpoints(options,p)
                    if matches:
                        results.append({'solution_P':string(sp),'solution_Q':string(sq),
                                        'trade_cells':list(comp),'locations':[p,q],'digit':d,'rival':e,
                                        'endpoint_matches':matches})
    return results

def base_labels(board,p,q,d,e):
    cs = candidates(board)
    return cs[p] == cs[q] == {d,e} and all(set(eligible(board,p,v)[2]) == {p,q} for v in (d,e))

def make_base(candidate,rng,orders,counts):
    p,q = candidate['locations']
    d,e = candidate['digit'],candidate['rival']
    sp,sq = parse(candidate['solution_P']),parse(candidate['solution_Q'])
    common = [v if v == w else 0 for v,w in zip(sp,sq)]
    expected = {sp,sq}
    assert set(solutions(tuple(common),3)) == expected
    for _ in range(orders):
        b = list(common)
        order = [i for i,v in enumerate(b) if v]
        rng.shuffle(order)
        for i in order:
            if sum(bool(v) for v in b) == 34:
                break
            old,b[i] = b[i],0
            if not base_labels(b,p,q,d,e):
                b[i] = old
                counts['removal_local_labels_rejected'] += 1
            elif set(solutions(tuple(b),3)) != expected:
                b[i] = old
                counts['removal_extra_solutions_rejected'] += 1
        if sum(bool(v) for v in b) == 34:
            return string(b)
        counts['deletion_order_above_34'] += 1
    return None

def add_clue(base,endpoint,d):
    b = list(parse(base))
    if b[endpoint]:
        raise ValueError('Clue endpoint is not blank')
    b[endpoint] = d
    return string(parse(b))

def validate(f):
    p,q = f['locations']
    d,e = f['digit'],f['rival']
    sp,sq = parse(f['solution_P']),parse(f['solution_Q'])
    changed = {i for i,(x,y) in enumerate(zip(sp,sq)) if x != y}
    if changed != set(f['trade_cells']) or len(changed) not in (6,8,10,12,14):
        raise ValueError('Trade component metadata')
    if any({sp[i],sq[i]} != {d,e} for i in changed):
        raise ValueError('Trade is not a d/e swap')
    if tuple(sorted(changed)) not in components(sp,d,e):
        raise ValueError('Trade is not one connected component')
    b = parse(f['base'])
    if sum(bool(v) for v in b) != 34 or not base_labels(b,p,q,d,e):
        raise ValueError('Base clue count or initial labels')
    if set(solutions(b,3)) != {sp,sq}:
        raise ValueError('Base must have exactly the two specified completions')
    if not (sp[p] == sq[q] == d and sp[q] == sq[p] == e):
        raise ValueError('Solutions do not force opposite target assignments')
    details = {}
    for arm in ARMS:
        board = f['boards'][arm]
        sol = sp if arm.endswith('_P') else sq
        forced,other = (p,q) if arm.endswith('_P') else (q,p)
        endpoint = f['endpoints'][arm]
        a = parse(board)
        if add_clue(f['base'],endpoint,d) != board or not unique(board,string(sol)):
            raise ValueError('Arm reconstruction or unique solution')
        if sum(bool(v) for v in a) != 35:
            raise ValueError('Arm clue count')
        cs = candidates(a)
        row,col,box = eligible(a,forced,d)
        if len(row) < 2 or len(col) < 2:
            raise ValueError('Target row/column also forces d')
        if arm.startswith('rule'):
            if set(box) != {forced} or cs[forced] != {d,e}:
                raise ValueError('Rule arm must force d by box while forced cell is not naked')
            if endpoint not in PEERS[other] or endpoint in PEERS[forced]:
                raise ValueError('Enabling clue adjacency')
        else:
            if not base_labels(a,p,q,d,e):
                raise ValueError('Control creates target-box d/e deduction or changes local candidates')
            if endpoint in PEERS[p] | PEERS[q] | {p,q}:
                raise ValueError('Control touches target peers')
        details[arm] = {'unique_solutions':1,'target_row_count':len(row),'target_col_count':len(col),
                        'digit_box_locations':list(box),'candidate_masks':[
                            sum(1 << (v-1) for v in c) for c in cs],**difficulty(a)}
    digit_counts = [Counter(v for v in parse(f['boards'][arm]) if v) for arm in ARMS]
    if any(c != digit_counts[0] for c in digit_counts):
        raise ValueError('Digit-frequency mismatch')
    ep = f['endpoints']
    if delta(ep['rule_P'],ep['rule_Q']) != delta(ep['control_P'],ep['control_Q']):
        raise ValueError('Edit displacement mismatch')
    geometry = {arm:endpoint_geometry(i,p) for arm,i in ep.items()}
    if sorted(geometry[a][:2] for a in ('rule_P','rule_Q')) != sorted(geometry[a][:2] for a in ('control_P','control_Q')):
        raise ValueError('Pooled band/stack mismatch')
    return details

def build(candidate,base,rng,counts):
    alternatives = []
    for match in candidate['endpoint_matches']:
        f = {k:v for k,v in candidate.items() if k != 'endpoint_matches'}
        f.update(match)
        f['base'] = base
        f['boards'] = {arm:add_clue(base,f['endpoints'][arm],f['digit']) for arm in ARMS}
        try:
            f['checks'] = validate(f)
        except ValueError as exc:
            counts[str(exc)] += 1
            continue
        difficulty_mismatch = sum(abs(f['checks']['rule_'+orientation]['initial_forced_cells']-
                                      f['checks']['control_'+orientation]['initial_forced_cells']) for orientation in 'PQ')
        f['matching']['forced_cells_l1'] = difficulty_mismatch
        rank = [f['matching']['box_center_distance_l1'],difficulty_mismatch]
        f['matching_rank'] = rank
        alternatives.append((rank,rng.random(),f))
    return min(alternatives,key=lambda v:(v[0],v[1]))[2] if alternatives else None

def transformed(f):
    g = dict(f)
    permutation = f['permutation']
    for name in ('base','solution_P','solution_Q'):
        g[name] = rename(f[name],permutation)
    g['boards'] = {arm:rename(board,permutation) for arm,board in f['boards'].items()}
    for name in ('digit','rival'):
        g[name] = permutation[f[name]-1]
    return g
