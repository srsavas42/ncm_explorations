"""Frozen CPU adapter: the public interface accepts clues alone.

Uses upstream generation unchanged, then reconstructs full-length cumulative
latents. The upstream idx_to_zhats z_hats list aliases its accumulator; its
z_levels are short generation inputs, not 81-cell readouts. Neither is used as
the intermediate measurement. See docs/measurement.md.
"""
import importlib.metadata
import json
import os
import platform
import sys
import time
from pathlib import Path
import numpy as np
from .assets import verify_assets
from .storage import digest, file_hash, root, atomic_json
from .sudoku import parse

OFFSETS = np.array([10*r+c for r in range(9) for c in range(9)],dtype=np.int64)
DIGIT_IDS = np.arange(1,10,dtype=np.int64)
ADAPTER_VERSION = 'full-cumulative-v1'

def solution_tokens(board):
    b = parse(board)
    result = []
    for r in range(9):
        result.extend(b[9*r:9*r+9])
        if r < 8:
            result.append(10)
    return list(result)

def prefix(board):
    return [11]+solution_tokens(board)+[11]

def board_from_prefix(ids):
    if len(ids) != 91 or ids[0] != 11 or ids[-1] != 11:
        raise ValueError('Unexpected Sudoku prefix')
    body = ids[1:-1]
    if any(body[i] != 10 for i in range(9,89,10)):
        raise ValueError('Unexpected row separator')
    return ''.join(str(body[i]) if body[i] else '.' for i in OFFSETS)

def peak_memory_bytes():
    if sys.platform == 'win32':
        import ctypes
        from ctypes import wintypes
        class Counters(ctypes.Structure):
            _fields_ = [('cb',wintypes.DWORD),('faults',wintypes.DWORD)] + [
                (n,ctypes.c_size_t) for n in ('peak','working','quota_peak_paged',
                'quota_paged','quota_peak_nonpaged','quota_nonpaged','pagefile','peak_pagefile')]
        counters = Counters()
        counters.cb = ctypes.sizeof(counters)
        kernel = ctypes.WinDLL('kernel32',use_last_error=True)
        kernel.GetCurrentProcess.restype = wintypes.HANDLE
        getmem = ctypes.WinDLL('psapi',use_last_error=True).GetProcessMemoryInfo
        getmem.argtypes = [wintypes.HANDLE,ctypes.c_void_p,wintypes.DWORD]
        if getmem(kernel.GetCurrentProcess(),ctypes.byref(counters),counters.cb):
            return counters.peak
        return None
    import resource
    return resource.getrusage(resource.RUSAGE_SELF).ru_maxrss * (1 if sys.platform == 'darwin' else 1024)

class CPUAdapter:
    def __init__(self,cfg):
        self.cfg = cfg
        self.assets = verify_assets(cfg)
        sys.path.insert(0,str(root(cfg)/'vendor/ncm'))
        import torch
        from omegaconf import OmegaConf
        from tokenization.vqvae_tokenizer import VQVAETokenizer
        from models.next_concept import NextConceptTransformer
        self.torch = torch
        torch.set_num_threads(cfg['model']['threads'])
        torch.use_deterministic_algorithms(True)
        torch.manual_seed(0)
        ck = root(cfg)/'assets/checkpoint'
        self.upstream_cfg = OmegaConf.load(ck/'config.yaml')
        uc = self.upstream_cfg
        settings = {k:cfg['model'][k] for k in ('temperature','top_k','top_p','cfg_scale')}
        if settings != {'temperature':0.0,'top_k':0,'top_p':1.0,'cfg_scale':0.0}:
            raise ValueError('Only frozen deterministic greedy decoding is supported')
        if any(uc.generation[k] != v for k,v in settings.items()):
            raise ValueError('Released decoding settings differ')
        uc.tokenizer.vqvae.checkpoint_path = str(ck/'tokenizer.pt')
        self.tk = VQVAETokenizer.from_config(uc.tokenizer)
        self.vqvae = self.tk.vqvae.cpu().float().eval()
        self.net = NextConceptTransformer(vqvae_local=self.vqvae,config=uc.model).cpu().float().eval()
        # These are the pinned public release checkpoints, verified before loading.
        self.net.load_state_dict(torch.load(ck/'generator.pt',map_location='cpu',weights_only=False)['model'],strict=True)
        for net in (self.net,self.vqvae):
            net.requires_grad_(False)
        self.levels = list(self.vqvae.vq.levels)
        if self.levels != [1,2,4,6,9,13,18,26,37,50,67,89]:
            raise ValueError('Unreviewed level schedule')
        self.settings = settings
        packages = ('torch','numpy','omegaconf','hydra-core')
        self.identity = {
            'adapter_version':ADAPTER_VERSION,'adapter_sha256':file_hash(__file__),
            'assets':self.assets,'settings':settings,'precision':'float32','device':'cpu',
            'threads':torch.get_num_threads(),'interop_threads':torch.get_num_interop_threads(),
            'python':platform.python_version(),'packages':{p:importlib.metadata.version(p) for p in packages},
            'cpu':platform.processor(),'logical_cpus':os.cpu_count(),'platform':platform.platform(),
            'mapping':{'board_offsets':OFFSETS.tolist(),'digit_ids':DIGIT_IDS.tolist(),
                       'prefix_bos':11,'separator':10,'blank':0},
            'clues_enforced_internally':False,
            'overrides':['CPU instead of CUDA','float32','batch size 1','deterministic algorithms',
                         'fixed threads','evaluation mode','inference mode'],
            'level_lengths':self.levels,
        }
        self.validate_mapping()
        self.parity = None

    def validate_mapping(self):
        # Check each cell separately, including every boundary, through the upstream tokenizer.
        for cell in range(81):
            for digit in range(1,10):
                b = '.'*cell+str(digit)+'.'*(80-cell)
                body = solution_tokens(b)
                text = self.tk.pre_tokenizer.decode(body)
                assert self.tk.pre_tokenizer.encode(text) == body
                assert body[OFFSETS[cell]] == digit
                assert board_from_prefix(prefix(b)) == b

    def _codes(self,board):
        torch = self.torch
        return self.net.generate(None,torch.tensor([prefix(board)],dtype=torch.long),
                                 **self.settings,cfg_null_eos=None)

    def _readouts(self,codes):
        torch = self.torch
        vq = self.vqvae.vq
        z = torch.zeros(1,self.levels[-1],self.vqvae.embed_dim)
        start = 0
        result = []
        for k,length in enumerate(self.levels):
            emb = vq.embeddings[k](codes[:,start:start+length])
            z, _ = vq.get_next_autoregressive_input(k,z,emb)
            # Read now; never keep references to upstream's in-place accumulator.
            result.append(self.vqvae.decoder(z.clone())[0].cpu().numpy().copy())
            start += length
        scores = np.stack(result)
        if scores.shape != (len(self.levels),89,12) or not np.isfinite(scores).all():
            raise ValueError('Malformed decoder score tensor')
        return scores

    def trace(self,board):
        parse(board)
        start = time.perf_counter()
        with self.torch.inference_mode():
            codes = self._codes(board)
            scores = self._readouts(codes)
        raw = scores.argmax(-1)
        result = {'digit_logits':scores[:,OFFSETS][:,:,DIGIT_IDS],
                  'winners':raw[:,OFFSETS], 'raw_tokens':raw,
                  'code_ids':codes[0].cpu().numpy(),
                  # Full decoder scores make the winner audit independent of argmax order.
                  'full_logits':scores,
                  'seconds':np.array(time.perf_counter()-start),
                  'peak_memory_bytes':np.array(peak_memory_bytes() or -1)}
        validate_trace(result,len(self.levels))
        return result

    def validate_parity(self,output):
        fixtures = json.loads((root(self.cfg)/'assets/parity/fixtures.json').read_text())
        metadata = json.loads((root(self.cfg)/'assets/parity/meta.json').read_text())
        assert metadata['levels'] == self.levels and metadata['full_length']
        checks = []
        for f in fixtures:
            board = board_from_prefix(f['prefix'])
            assert prefix(board) == f['prefix']
            instrumented = self.trace(board)
            repeated = self.trace(board)
            with self.torch.inference_mode():
                reference_codes = self._codes(board)
                reference_logits = self.vqvae.decode(reference_codes)[0].numpy()
            assert np.array_equal(instrumented['code_ids'],reference_codes[0].numpy()), 'Generation changed'
            assert np.array_equal(instrumented['raw_tokens'][-1],reference_logits.argmax(-1)), 'Final reference differs'
            assert np.array_equal(instrumented['full_logits'],repeated['full_logits']), 'Nondeterministic trace'
            assert instrumented['code_ids'].tolist() == f['codes'], 'Independent reference code mismatch'
            expected = np.array(f['tokens']).reshape(len(self.levels),89)
            assert np.array_equal(instrumented['raw_tokens'],expected), 'Independent intermediate token mismatch'
            checks.append({'puzzle_sha256':digest(board),'codes_match':True,
                           'all_intermediate_tokens_match':True,'repeat_scores_identical':True,
                           'uninstrumented_final_matches':True})
        self.parity = {'identity_hash':digest(self.identity),'checks':checks,'passed':True}
        atomic_json(output,self.parity)
        return self.parity

def validate_trace(trace,k=12):
    scores = trace['digit_logits']
    if scores.shape != (k,81,9) or not np.isfinite(scores).all():
        raise ValueError('Digit scores missing, nonfinite, or wrong shape')
    full = trace['full_logits']
    if full.shape != (k,89,12) or not np.isfinite(full).all():
        raise ValueError('Full vocabulary audit missing')
    if not np.array_equal(scores,full[:,OFFSETS][:,:,DIGIT_IDS]):
        raise ValueError('Digit mapping disagrees with full logits')
    if not np.array_equal(trace['raw_tokens'],full.argmax(-1)):
        raise ValueError('Full-vocabulary winners disagree')
    if not np.array_equal(trace['winners'],trace['raw_tokens'][:,OFFSETS]):
        raise ValueError('Cell offsets disagree')
    if trace['code_ids'].shape != (sum([1,2,4,6,9,13,18,26,37,50,67,89]),):
        raise ValueError('Code sequence incomplete')
