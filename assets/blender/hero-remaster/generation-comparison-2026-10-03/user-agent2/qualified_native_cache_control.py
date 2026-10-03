"""Replay actual first self-attention across process-local inactive cache release."""
import argparse
import gc
import hashlib
import json
import os
from pathlib import Path
import time

import numpy as np
import torch
import torch.nn.functional as functional


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--actual-qkv', required=True)
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    assert sha(args.actual_qkv) == 'd4799a8b76df1ed746297a868aaf08311510bf9e2a770223533ceabeabc470a0'
    assert torch.version.git_version == '08187d9e0fba026dc8217405802ab5381dc88d90'
    assert os.environ.get('PYTORCH_MPS_DISABLE_PREFILL_ATTENTION') in (None, '0')
    torch.set_num_threads(4)
    out = Path(args.out)
    assert not out.exists()
    out.mkdir(parents=True)
    started = time.monotonic()
    report = {'accepted': False, 'newModelRuns': 0, 'torch': torch.__version__,
              'torchGitVersion': torch.version.git_version, 'recipeSHA256': sha(__file__),
              'actualQKVArchiveSHA256': sha(args.actual_qkv), 'phase': 'load actual tensors',
              'limits': ['Recorded learned QKV from paint03, not full UNet or texture quality.',
                         'One GiB synthetic inactive allocation, not the real convolution-workspace allocation trace.',
                         'Cache release is process-local, no foreign eviction or shared installation edit.']}
    def save():
        (out / 'receipt.json').write_text(json.dumps(report, indent=2) + '\n')
    def memory():
        return {'allocatedBytes': torch.mps.current_allocated_memory(),
                'driverBytes': torch.mps.driver_allocated_memory()}
    with np.load(args.actual_qkv, allow_pickle=False) as archive:
        arrays = [archive['actual-first-large-attention-inputs-00.' + name].copy()
                  for name in ('query', 'key', 'value')]
    assert all(a.shape == (24, 5, 9216, 64) and a.dtype == np.float16 and np.isfinite(a).all() for a in arrays)
    cpu = [torch.from_numpy(a) for a in arrays]
    # Restore the exact actual processor head-transpose stride from paint04.
    query, key, value = [t.transpose(1, 2).contiguous().to('mps').transpose(1, 2) for t in cpu]
    assert all(list(t.stride()) == [2949120, 64, 320, 1] for t in (query, key, value))
    selected = torch.tensor([0, 4608, 9215])
    qc, kc, vc = cpu[0][:, :, selected].float(), cpu[1].float(), cpu[2].float()
    expected = (torch.softmax(qc @ kc.transpose(-1, -2) / 8, dim=-1) @ vc).half()
    del qc, kc, vc
    report['phase'] = 'native actual QKV before cache release'
    report['beforeNative'] = memory()
    save()
    with torch.inference_mode():
        before = functional.scaled_dot_product_attention(query, key, value, dropout_p=0., is_causal=False).cpu()
    assert torch.isfinite(before).all()
    report['nativeSelectedCPUError'] = float((before[:, :, selected].float() - expected.float()).abs().max())
    assert report['nativeSelectedCPUError'] <= .002
    # Keep every actual Q/K/V tensor live while creating and releasing unused cache.
    scratch = torch.ones(256 * 1024 * 1024, device='mps', dtype=torch.float32)
    torch.mps.synchronize()
    del scratch
    gc.collect()
    torch.mps.synchronize()
    report['beforeCacheRelease'] = memory()
    report['phase'] = 'release only unoccupied process cache'
    save()
    torch.mps.empty_cache()
    report['afterCacheRelease'] = memory()
    report['activeQKVBytesIdentical'] = all(np.array_equal(t.cpu().numpy(), a)
                                          for t, a in zip((query, key, value), arrays))
    with torch.inference_mode():
        after = functional.scaled_dot_product_attention(query, key, value, dropout_p=0., is_causal=False).cpu()
    report['nativeBeforeAfterByteIdentical'] = bool(torch.equal(before, after))
    report['nativeBeforeAfterMaxError'] = float((before.float() - after.float()).abs().max())
    report['driverReleasedBytes'] = report['beforeCacheRelease']['driverBytes'] - report['afterCacheRelease']['driverBytes']
    report['activeAllocationUnchanged'] = report['beforeCacheRelease']['allocatedBytes'] == report['afterCacheRelease']['allocatedBytes']
    report['phase'] = 'cache and actual native attention controls passed'
    report['elapsedSeconds'] = time.monotonic() - started
    save()
    assert report['activeQKVBytesIdentical'] and report['nativeBeforeAfterByteIdentical']
    assert report['activeAllocationUnchanged'] and report['driverReleasedBytes'] >= 1024 ** 3


if __name__ == '__main__':
    main()
