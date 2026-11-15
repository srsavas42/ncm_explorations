import argparse
import json
from .storage import config

def main():
    parser = argparse.ArgumentParser(description='Frozen NCM hidden-single experiment')
    sub = parser.add_subparsers(dest='command',required=True)
    sub.add_parser('verify-fixture')
    for name in ('fetch','trace','prepare','run','report','audit'):
        p = sub.add_parser(name)
        p.add_argument('--config',default='configs/pilot.toml')
        if name == 'trace':
            p.add_argument('--fixture',choices=['worked-triplet'],default='worked-triplet')
        if name == 'run':
            p.add_argument('--resume',action='store_true')
        if name == 'audit':
            p.add_argument('--other-config')
    args = parser.parse_args()
    if args.command == 'verify-fixture':
        from .sudoku import load_fixture,rename,validate_triplet,parse,solutions
        f = load_fixture()
        from .cohort import transformed
        f['permutation'] = [2,3,4,5,6,7,8,9,1]
        validate_triplet(transformed(f))
        for invalid in ('11'+'.'*79,f['solution'][:-1]+'1'):
            try:
                parse(invalid)
            except ValueError:
                pass
            else:
                raise AssertionError('Corrupt board accepted')
        assert len(solutions(parse('.'*81))) == 2
        print(json.dumps({'passed':True,'fixture':'worked-triplet','target':'r8c3',
                          'candidates':[3,7],'oracle':{'A':1,'B':0,'C':0},
                          'local_baseline_contrast':0,'permutation_verified':True}))
        return
    cfg = config(args.config)
    if args.command == 'fetch':
        from .assets import acquire
        acquire(cfg)
    elif args.command == 'prepare':
        from .cohort import prepare
        prepare(cfg)
    elif args.command == 'trace':
        from .runner import trace_fixture
        trace_fixture(cfg)
    elif args.command == 'run':
        from .runner import run
        index = run(cfg,args.resume)
        if any(r['status'] != 'complete' for r in index['boards']):
            parser.exit(1,'Engineering failures remain; inspect failures.jsonl and resume.\n')
    elif args.command == 'report':
        from .analysis import report
        report(cfg)
    elif args.command == 'audit':
        from .audit import audit
        print(json.dumps(audit(cfg,config(args.other_config) if args.other_config else None),indent=2))

if __name__ == '__main__':
    main()
