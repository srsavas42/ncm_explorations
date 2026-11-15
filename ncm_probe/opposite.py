"""Separate CLI for opposite-answer follow-up; original ncm_probe CLI is frozen."""
import argparse
import json
from pathlib import Path
import tomllib

def config(path):
    path = Path(path).resolve()
    cfg = tomllib.loads(path.read_text())
    cfg['_root'] = str(path.parent.parent)
    s = cfg['study']
    if s['early_levels'] != list(range(1,7)) or s['bootstrap_draws'] != 10000:
        raise ValueError('Unsupported endpoint/window')
    if s['base_clues'] != 34 or s['arm_clues'] != 35:
        raise ValueError('This constructor requires 34/35 clues')
    if s['pilot_n'] < 1 or s['confirmation_n'] < 1 or s['source_budget'] < 1:
        raise ValueError('Invalid sample/search budget')
    if cfg['model']['precision'] != 'float32' or cfg['model']['threads'] < 1:
        raise ValueError('CPU float32 with positive threads is required')
    return cfg

def main():
    parser = argparse.ArgumentParser(description='Opposite-answer Sudoku follow-up')
    parser.add_argument('command',choices=['verify-fixture','prepare','audit','trace','run','report'])
    parser.add_argument('--config',default='configs/opposite.toml')
    parser.add_argument('--split',choices=['pilot','confirmation'],default='pilot')
    parser.add_argument('--resume',action='store_true')
    args = parser.parse_args()
    cfg = config(args.config)
    if args.command == 'verify-fixture':
        from .opposite_puzzles import validate,transformed
        f = json.loads((Path(cfg['_root'])/'ncm_probe/fixtures/opposite-engineering.json').read_text())
        validate(f)
        validate(transformed(f))
        print('Opposite-answer fixture: two scaffold completions, four unique arms, matched edits, and rename verified.')
    elif args.command == 'prepare':
        from .opposite_prepare import prepare
        prepare(cfg)
    elif args.command == 'audit':
        from .opposite_prepare import audit
        print(json.dumps(audit(cfg),indent=2))
    elif args.command == 'trace':
        from .opposite_run import fixture
        fixture(cfg)
    elif args.command == 'run':
        from .opposite_run import run
        run(cfg,args.split,args.resume)
    elif args.command == 'report':
        from .opposite_analysis import report
        report(cfg,args.split)

if __name__ == '__main__':
    main()
