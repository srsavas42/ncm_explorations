"""Initial-clue labels and a bounded exact solver. Coordinates are zero-based."""
from collections import Counter
from functools import lru_cache
import hashlib
import json
from importlib.resources import files

DIGITS = frozenset(range(1, 10))
ROWS = tuple(tuple(9*r+c for c in range(9)) for r in range(9))
COLS = tuple(tuple(9*r+c for r in range(9)) for c in range(9))
BOXES = tuple(tuple(9*(3*br+r)+3*bc+c for r in range(3) for c in range(3))
              for br in range(3) for bc in range(3))
UNITS = ROWS + COLS + BOXES

def units(t):
    return ROWS[t//9], COLS[t%9], BOXES[(t//27)*3+(t%9)//3]

PEERS = tuple(frozenset().union(*units(t)) - {t} for t in range(81))

def parse(board):
    if isinstance(board, str):
        board = [0 if x in '._0' else int(x) for x in board if not x.isspace()]
    board = tuple(int(x) for x in board)
    if len(board) != 81 or any(x not in range(10) for x in board):
        raise ValueError('A board must contain 81 digits or blanks')
    for unit in UNITS:
        givens = [board[i] for i in unit if board[i]]
        if len(givens) != len(set(givens)):
            raise ValueError('Conflicting givens')
    return board

def string(board):
    return ''.join(str(x) if x else '.' for x in board)

def candidates(board):
    b = parse(board)
    return tuple(DIGITS - {b[j] for j in PEERS[i]} if not b[i] else frozenset()
                 for i in range(81))

def eligible(board, t, d):
    cs = candidates(board)
    return tuple(tuple(i for i in u if d in cs[i]) for u in units(t))

@lru_cache(maxsize=40000)
def solutions(board, limit=2):
    b = list(parse(board))
    found = []
    def search():
        best, opts = -1, None
        for i, value in enumerate(b):
            if not value:
                ds = DIGITS - {b[j] for j in PEERS[i]}
                if not ds:
                    return
                if opts is None or len(ds) < len(opts):
                    best, opts = i, ds
                    if len(ds) == 1:
                        break
        if best == -1:
            found.append(tuple(b))
            return
        for d in sorted(opts):
            b[best] = d
            search()
            if len(found) >= limit:
                break
        b[best] = 0
    search()
    return tuple(found)

def unique(board, solution):
    b, s = parse(board), parse(solution)
    if 0 in s or any(x and x != y for x, y in zip(b, s)):
        return False
    return solutions(b) == (s,)

def rename(board, permutation):
    if sorted(permutation) != list(range(1, 10)):
        raise ValueError('Invalid digit bijection')
    return string([permutation[x-1] if x else 0 for x in parse(board)])

def canonical(solution):
    mapping = {}
    return ''.join(str(mapping.setdefault(x, len(mapping)+1)) for x in parse(solution))

def family_id(solution):
    return hashlib.sha256(canonical(solution).encode()).hexdigest()[:20]

def move(board, removed, revealed, digit):
    b = list(parse(board))
    if b[removed] != digit or b[revealed] != 0:
        raise ValueError('Invalid move endpoints')
    b[removed], b[revealed] = 0, digit
    return string(b)

def difficulty(board):
    cs = candidates(board)
    forced = {i for i, c in enumerate(cs) if len(c) == 1}
    for unit in UNITS:
        for d in range(1, 10):
            positions = [i for i in unit if d in cs[i]]
            if len(positions) == 1:
                forced.add(positions[0])
    return {'initial_forced_cells': len(forced),
            'candidate_total': sum(map(len, cs))}

def geometry(t, endpoint):
    r, c = divmod(t, 9)
    er, ec = divmod(endpoint, 9)
    return [int(r//3 == er//3), int(c//3 == ec//3), abs(r-er), abs(c-ec)]

def validate_triplet(f):
    t, d, e, u = (f[k] for k in ('target','digit','rival','competitor'))
    b = parse(f['boards']['B'])
    details = {}
    for arm in 'ABC':
        board = parse(f['boards'][arm])
        assert sum(x != 0 for x in board) == 35, 'clue count'
        assert candidates(board)[t] == {d,e}, 'target candidates'
        assert all(board[i] == b[i] for i in PEERS[t] | {t}), 'direct clues'
        row, col, box = eligible(board,t,d)
        assert len(row) > 1 and len(col) > 1, 'row/column exclusion'
        assert set(box) == ({t} if arm == 'A' else {t,u}), 'box label'
        assert unique(f['boards'][arm],f['solution']), 'unique shared solution'
        assert Counter(x for x in board if x) == Counter(x for x in b if x), 'digit counts'
        if arm != 'B':
            removed, revealed = f['edits'][arm]
            assert removed not in PEERS[t] | {t} and revealed not in PEERS[t] | {t}
            assert move(b, removed, revealed, d) == f['boards'][arm], 'edit reconstruction'
            assert sum(x != y for x,y in zip(board,b)) == 2
        details[arm] = {'candidate_masks': [sum(1 << (v-1) for v in c) for c in candidates(board)],
                        'target_row_count': len(row), 'target_col_count': len(col),
                        'target_box_positions': list(box), 'unique_solutions': 1,
                        **difficulty(board)}
    assert parse(f['solution'])[t] == d
    return details

def control_cells(f):
    bs = {arm: parse(b) for arm,b in f['boards'].items()}
    cs = {arm: candidates(b) for arm,b in bs.items()}
    sol = parse(f['solution'])
    result = []
    for t in range(81):
        if t == f['target'] or any(bs[a][t] for a in 'ABC'):
            continue
        if len(cs['B'][t]) != 2 or any(cs[a][t] != cs['B'][t] for a in 'AC'):
            continue
        labels = [tuple(len(p) == 1 for p in eligible(bs[a],t,sol[t])) for a in 'ABC']
        if labels[0] == labels[1] == labels[2]:
            result.append({'cell': t,'digit': sol[t], 'rival': next(iter(cs['B'][t]-{sol[t]}))})
    return result

def load_fixture():
    f = json.loads(files('ncm_probe').joinpath('fixtures/worked-triplet.json').read_text())
    f['checks'] = validate_triplet(f)
    f['control_cells'] = control_cells(f)
    return f
