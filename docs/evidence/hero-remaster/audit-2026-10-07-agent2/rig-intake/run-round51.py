"""Prepared serial contacts51/ordinary gate controller; parent admission required.

Run only below canonical nonblocking lockf and pinned run_bounded96 --locked.
This source has been syntax checked only, never executed at preparation.
"""
import hashlib
import json
import os
from pathlib import Path
import signal
import subprocess
import time

root = Path('/Users/raynos/projects/games/rockhop')
here = Path(__file__).resolve().parent
manifest = json.loads((here / 'execution51-manifest.json').read_text())
assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID'), 'Canonical guard required'
assert all(os.environ.get(k) == '2' for k in
           ['OPENBLAS_NUM_THREADS', 'OMP_NUM_THREADS', 'VECLIB_MAXIMUM_THREADS'])
evidence = root / manifest['evidenceDirectory']
output = root / manifest['outputDirectory']
assert not evidence.exists() and not output.exists(), 'Fresh execution paths required'
evidence.mkdir(parents=True)
output.mkdir(parents=True)
started = time.monotonic()
report = {'accepted': False, 'status': 'RUNNING_UNACCEPTED_FINITE_DIAGNOSTICS',
          'sourceHEAD': subprocess.check_output(['git', 'rev-parse', 'HEAD'],
                                                cwd=root, text=True).strip(),
          'modelReplacements': 0, 'records': [], 'errors': [],
          'limits': ['Finite saved-pose contacts only; no art, continuous-time or wardrobe acceptance.',
                     'Ordinary gate tests current normal player assets; candidate remains private.']}
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


class OwnedStop(Exception):
    pass


def interrupted(signum, frame):
    raise OwnedStop('Controller received signal ' + str(signum))


signal.signal(signal.SIGTERM, interrupted)
signal.signal(signal.SIGINT, interrupted)


def stop_owned(child):
    if child.poll() is not None:
        return
    os.killpg(child.pid, signal.SIGTERM)
    try:
        child.wait(timeout=2)
    except subprocess.TimeoutExpired:
        os.killpg(child.pid, signal.SIGKILL)
        child.wait(timeout=1)


def save():
    report['elapsedSeconds'] = time.monotonic() - started
    (evidence / 'execution.json').write_text(json.dumps(report, indent=2) + '\n')


def run(label, command, timeout):
    record = {'label': label, 'command': command, 'timeoutSeconds': timeout}
    report['records'].append(record)
    save()
    tick = time.monotonic()
    log = evidence / (label + '.log')
    child = None
    stopped = None
    try:
        with log.open('x') as stream:
            child = subprocess.Popen(command, cwd=root, stdout=stream,
                                     stderr=subprocess.STDOUT, start_new_session=True)
            record['ownedChildProcessGroup'] = child.pid
            save()
            record['exitCode'] = child.wait(timeout=timeout)
    except BaseException as error:
        if child is not None:
            stop_owned(child)
        if isinstance(error, OwnedStop):
            stopped = error
        record['error'] = type(error).__name__ + ': ' + str(error)
        record['exitCode'] = None
    record['elapsedSeconds'] = time.monotonic() - tick
    if log.exists():
        record['logSHA256'] = sha(log)
    if record['exitCode'] != 0:
        report['errors'].append(label + ' failed; see preserved record/log')
    save()
    if stopped is not None:
        raise stopped
    return record['exitCode'] == 0


try:
    assert sha(Path(__file__)) == manifest['sourceControllerSHA256'], 'Controller pin changed'
    report['pinnedInputsExact'] = all(sha(root / row['path']) == row['sha256']
                                      for row in manifest['sourcePins'])
    assert report['pinnedInputsExact'], 'Input pin changed; no child launched'
    save()
    contacts_ok = run('whole-contacts', manifest['contactsCommand'], 240)
    # Even a failed contact diagnostic owes this round its ordinary player gate.
    build_ok = run('ordinary-build', manifest['ordinaryBuildCommand'], 180)
    replay_ok = build_ok and run('ordinary-replay', manifest['ordinaryReplayCommand'], 180)
    if replay_ok:
        review = json.loads((output / 'build/hero-review.json').read_text())
        assert not review['mapping'] and not review['newRiderAdapter']
        gate = json.loads((output / 'ship-gate.json').read_text())
        assert len(gate['runs']) == 2 and not gate['errors']
        assert {row['tier'] for row in gate['runs']} == {'low', 'high'}
        assert len({row['finishTimeFloat64LE'] for row in gate['runs']}) == 1
        for row in gate['runs']:
            assert row['result']['finishTime'] is not None and row['result']['faults'] == 0
            assert row['crashRestart']['crashed']
            assert row['crashRestart']['restartPhase'] == 'riding'
            assert row['crashRestart']['restartTick'] <= 1
        report['ordinaryGate'] = gate
        report['ordinaryGateStatus'] = 'PASS_NORMAL_PLAYER_ONLY'
    if contacts_ok:
        contact = json.loads((evidence / 'whole-contacts.json').read_text())
        assert len(contact['records']) == 10
        for row in contact['records']:
            for field in ['full', 'four']:
                assert len(row['fields'][field]) == 10, 'All ten four-region pairs required'
        report['contactsStatus'] = contact['status']
        report['contactsSHA256'] = sha(evidence / 'whole-contacts.json')
    report['status'] = 'UNACCEPTED_EXECUTED_REVIEW_REQUIRED' if not report['errors'] else 'FAILED_RETAINED'
except BaseException as error:
    report['errors'].append(type(error).__name__ + ': ' + str(error))
    report['status'] = 'FAILED_RETAINED'
finally:
    try:
        report['postRunPinsExact'] = all(sha(root / row['path']) == row['sha256']
                                         for row in manifest['sourcePins'])
        if not report['postRunPinsExact']:
            report['errors'].append('Post-run source/capture pins changed')
            report['status'] = 'FAILED_RETAINED'
    except BaseException as error:
        report['errors'].append('Post-run pin read failed: ' + str(error))
        report['status'] = 'FAILED_RETAINED'
    save()
print(json.dumps({'status': report['status'], 'errors': report['errors']}), flush=True)
raise SystemExit(0 if not report['errors'] else 1)
