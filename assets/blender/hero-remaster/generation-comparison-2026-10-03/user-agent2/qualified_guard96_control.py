"""Bounded CPU-only boundary/ownership probes; synthetic memory, no model."""
import argparse
import importlib.util
import json
import os
from pathlib import Path
import sys


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', required=True)
    args = parser.parse_args()
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID') == str(os.getppid())
    out = Path(args.out).resolve()
    out.mkdir(parents=True, exist_ok=False)
    source = Path(__file__).with_name('run_bounded96.py')
    spec = importlib.util.spec_from_file_location('future_guard', source)
    guard = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(guard)
    original_stop = guard.stop_owned
    cases = []
    for name, samples, expected, status, limit, child_seconds in (
        ('anonymous-admission55', [(55,0)], 75, 'refused headroom', 5, .05),
        ('combined-admission68', [(54,14)], 75, 'refused headroom', 5, .05),
        ('combined95-allowed', [(1,1),(64,31)], 0, 'worker returned', 5, .05),
        ('combined96-stopped', [(1,1),(64,32)], 74, 'stopped owned child at memory bound', 5, 10),
        ('anonymous65-stopped', [(1,1),(65,0)], 74, 'stopped owned child at memory bound', 5, 10),
        ('time-bound-retained', [(1,1)], 74, 'stopped owned child at time bound', .001, 10)):
        cursor = 0
        terminated = []
        def memory():
            nonlocal cursor
            anonymous, wired = samples[min(cursor, len(samples)-1)]
            cursor += 1
            return {'anonymousGiB': anonymous, 'wiredGiB': wired, 'freeGiB': 10}
        def stop_owned(child):
            terminated.append(child.pid)
            original_stop(child)
        guard.memory = memory
        guard.stop_owned = stop_owned
        case_out = out / name
        # Already beneath the real shared locked controller. Nested probes
        # exercise owned process groups only, with synthetic measurements.
        sys.argv = [str(source), '--locked', '--out', str(case_out),
                    '--limit-seconds', str(limit), '--', sys.executable,
                    '-c', f'import time; time.sleep({child_seconds})']
        result = guard.main()
        report = json.loads((case_out/'guard.json').read_text())
        assert result == expected and report['status'].startswith(status), report
        if terminated:
            assert terminated == [report['ownedChildPID']]
        else:
            assert result in (0,75)
        if result == 75:
            assert 'ownedChildPID' not in report
        assert report['physicalMemoryBytes'] == 137438953472
        assert report['startAnonymousBelowGiB'] == 55 and report['stopAnonymousGiB'] == 65
        assert report['stopAnonymousPlusWiredGiB'] == 96 and report['pollSeconds'] == 1
        cases.append({'case': name, 'syntheticMemory': True, 'result': result,
                      'status': report['status'], 'onlyOwnedGroupTerminated': True})
        (out/'receipt.json').write_text(json.dumps({'accepted': False, 'modelRuns': 0,
                                                  'cases': cases, 'physicalMemoryBytes': 137438953472,
                                                  'limits': 'Synthetic thresholds, real CPU children; no high-memory stress or hard allocation ceiling proof.'}, indent=2)+'\n')
    sys.argv = [str(source), '--locked', '--out', str(out/'invalid-time'),
                '--limit-seconds', '1791', '--', sys.executable, '-c', 'pass']
    try:
        guard.main()
    except AssertionError:
        assert not (out/'invalid-time').exists()
    else:
        raise AssertionError('Maximum1790seconds must remain enforced')
    print('Six boundary/ownership probes and maximum time rejection pass; no model run.')


if __name__ == '__main__':
    main()
