"""Shared lock, one-second memory guard, and termination of owned children only."""
import argparse
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import sys
import time

LOCALAI = Path('/Users/raynos/projects/localai')
LOCK = LOCALAI / '.model.lock'


def memory():
    result = subprocess.check_output(['bash', str(LOCALAI / 'bin/mem-gb.sh')], text=True)
    return dict(zip(('anonymousGiB', 'wiredGiB', 'freeGiB'), map(float, result.split())))


def stop_owned(child):
    try:
        os.killpg(child.pid, signal.SIGTERM)
    except ProcessLookupError:
        pass
    try:
        child.wait(timeout=5)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=3)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--locked', action='store_true', help=argparse.SUPPRESS)
    parser.add_argument('--out', required=True)
    parser.add_argument('--limit-seconds', type=float, default=1790)
    parser.add_argument('command', nargs=argparse.REMAINDER)
    args = parser.parse_args()
    assert 0 < args.limit_seconds <= 1790
    command = args.command[1:] if args.command[:1] == ['--'] else args.command
    assert command, 'Provide one owned worker command'
    if not args.locked:
        os.execvp('lockf', ['lockf', '-k', str(LOCK), sys.executable,
                           str(Path(__file__).resolve()), '--locked',
                           '--out', args.out, '--limit-seconds', str(args.limit_seconds),
                           '--', *command])
    output = Path(args.out).resolve()
    output.mkdir(parents=True, exist_ok=True)
    report = output / 'guard.json'
    assert not report.exists(), 'Fresh numbered experiment required'
    started = time.monotonic()
    record = {'accepted': False, 'lock': str(LOCK), 'method': 'lockf -k',
              'command': command, 'controllerPID': os.getpid(), 'pollSeconds': 1,
              'startAnonymousBelowGiB': 55, 'stopAnonymousGiB': 65,
              'stopAnonymousPlusWiredGiB': 78, 'limitSeconds': args.limit_seconds,
              'guardSHA256': hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),
              'status': 'preflight', 'samples': []}
    def save():
        report.write_text(json.dumps(record, indent=2) + '\n')
    first = memory()
    record['samples'].append({'seconds': 0, **first})
    if first['anonymousGiB'] >= 55 or first['anonymousGiB'] + first['wiredGiB'] >= 68:
        record['status'] = 'refused headroom; no child launched'
        save()
        return 75
    env = os.environ.copy()
    env.update(HF_HUB_OFFLINE='1', TRANSFORMERS_OFFLINE='1',
               PYTORCH_ENABLE_MPS_FALLBACK='1',
               ROCKHOP_GENERATION_CONTROLLER_PID=str(os.getpid()))
    with (output / 'worker.log').open('w') as log:
        child = subprocess.Popen(command, env=env, stdout=log,
                                 stderr=subprocess.STDOUT, start_new_session=True)
        record.update(status='running', ownedChildPID=child.pid)
        save()
        try:
            while child.poll() is None:
                sample = {'seconds': round(time.monotonic() - started, 3), **memory()}
                record['samples'].append(sample)
                if sample['anonymousGiB'] >= 65 or sample['anonymousGiB'] + sample['wiredGiB'] >= 78:
                    record['status'] = 'stopped owned child at memory bound'
                    stop_owned(child)
                    break
                if time.monotonic() - started >= args.limit_seconds:
                    record['status'] = 'stopped owned child at time bound'
                    stop_owned(child)
                    break
                save()
                try:
                    child.wait(timeout=1)
                except subprocess.TimeoutExpired:
                    pass
        except BaseException:
            record['status'] = 'controller interrupted; owned child stopped'
            stop_owned(child)
            raise
        finally:
            record['exitCode'] = child.returncode
            record['elapsedSeconds'] = round(time.monotonic() - started, 3)
            if record['status'] == 'running':
                record['status'] = 'worker returned; review pending'
            save()
    print(json.dumps({k: record[k] for k in ('status', 'exitCode', 'elapsedSeconds')}))
    return child.returncode if record['status'] == 'worker returned; review pending' else 74


if __name__ == '__main__':
    sys.exit(main())
