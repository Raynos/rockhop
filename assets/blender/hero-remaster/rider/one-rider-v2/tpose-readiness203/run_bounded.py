"""Proposed controller; lock queue is outside one <=30-minute model batch.

No eviction, lock stealing, dependency installation, or unrelated process kill.
--preflight is CPU-only and does not create model output or import Torch.
"""
import argparse
import json
import os
from pathlib import Path
import re
import signal
import subprocess
import sys
import time

LOCK = '/Users/raynos/projects/localai/.model.lock'
PYTHON = '/Users/raynos/ml/img2mesh/Hunyuan3D-2.1/.venv/bin/python'
CPU = '/Users/raynos/projects/localai/runtime/unimate/.venv/bin/python'
PRIVATE = Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
WORKER = Path(__file__).with_name('shape_only_worker.py')


def anonymous_bytes():
    value = subprocess.check_output(['/usr/bin/vm_stat'], text=True)
    page = int(re.search(r'page size of (\d+)', value).group(1))
    return int(re.search(r'Anonymous pages:\s+(\d+)', value).group(1)) * page


def stop_owned(process):
    os.killpg(process.pid, signal.SIGTERM)
    try:
        process.wait(timeout=3)
    except subprocess.TimeoutExpired:
        os.killpg(process.pid, signal.SIGKILL)
        process.wait(timeout=3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--preflight', action='store_true')
    parser.add_argument('--inside-lock', action='store_true')
    parser.add_argument('--image', required=True)
    parser.add_argument('--image-sha256', required=True)
    parser.add_argument('--out', required=True)
    parser.add_argument('--seed', type=int, default=42)
    args = parser.parse_args()
    output = Path(args.out).resolve()
    assert output.is_relative_to(PRIVATE) and output != PRIVATE and not output.exists()
    assert Path(args.image).is_file() and Path(PYTHON).is_file() and WORKER.is_file()
    worker_args = ['--image', args.image, '--image-sha256', args.image_sha256,
                   '--out', str(output), '--seed', str(args.seed)]
    command = [PYTHON, '-u', str(WORKER), *worker_args]
    if args.preflight:
        print(json.dumps({'status': 'CPU_ONLY_PREFLIGHT_NO_MODEL', 'command': command,
                          'lock': LOCK, 'lockMethod': 'lockf -k',
                          'anonymousBytes': anonymous_bytes(), 'limitBytes': 70_000_000_000,
                          'timeoutSeconds': 1800, 'terminateAtSeconds': 1790,
                          'memoryPollSeconds': 1, 'eviction': False}, indent=2))
        return
    if not args.inside_lock:
        os.execvp('lockf', ['lockf', '-k', LOCK, CPU, '-u', str(Path(__file__).resolve()),
                            '--inside-lock', *worker_args])
    started = time.monotonic()
    env = os.environ.copy()
    env.update(ROCKHOP_TPOSE_LOCK_CONTROLLER_PID=str(os.getpid()),
               OPENBLAS_NUM_THREADS='2', OMP_NUM_THREADS='2', PYTHONDONTWRITEBYTECODE='1')
    receipt_path = output.with_name(output.name + '-process.json')
    log_path = output.with_name(output.name + '-process.log')
    assert not receipt_path.exists() and not log_path.exists(), 'Preserve prior evidence'
    first = anonymous_bytes()
    receipt = {'status': 'LOCK_ACQUIRED', 'command': command,
               'lock': LOCK, 'lockMethod': 'lockf -k', 'accepted': False,
               'limitBytes': 70_000_000_000, 'timeoutSeconds': 1800,
               'memorySamples': [{'seconds': 0, 'anonymousBytes': first}],
               'GPUUsed': False, 'eviction': False, 'queueOutsideBatch': True}
    if first >= 70_000_000_000:
        receipt.update(status='MEMORY_REFUSED_NO_MODEL', exitCode=75)
        receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
        sys.exit(75)
    with log_path.open('x') as log:
        process = subprocess.Popen(command, env=env, stdout=log, stderr=subprocess.STDOUT,
                                   start_new_session=True)
        receipt['GPUUsed'] = True
        reason = None
        while process.poll() is None:
            now, memory = time.monotonic(), anonymous_bytes()
            receipt['memorySamples'].append({'seconds': now - started, 'anonymousBytes': memory})
            if memory >= 70_000_000_000 or now - started >= 1790:
                reason = 'ANONYMOUS_70GB' if memory >= 70_000_000_000 else 'BATCH_1790SECONDS'
                stop_owned(process)
                break
            try:
                process.wait(timeout=1)
            except subprocess.TimeoutExpired:
                pass
        receipt.update(status='WORKER_EXITED_UNACCEPTED' if reason is None else 'STOPPED_AT_BOUND',
                       stopReason=reason, exitCode=process.returncode,
                       wallSeconds=time.monotonic() - started)
    receipt_path.write_text(json.dumps(receipt, indent=2) + '\n')
    print(json.dumps({k: receipt[k] for k in ['status', 'exitCode', 'wallSeconds', 'stopReason']}))
    sys.exit(process.returncode if reason is None else 75)


if __name__ == '__main__':
    main()
