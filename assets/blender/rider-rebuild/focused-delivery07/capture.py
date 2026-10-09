#!/usr/bin/env python3
"""Capture an explicitly supplied corrected private build under original guards."""
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
PROFILE = ROOT / 'docs/evidence/rider-rebuild/selected-grip-kinematic02/thumbplane05/runtime-profile.json'
PROFILE_HASH = '659ff94c1611e0ce95310ab090e94637832ac2bbfbac7f9554f903595bd05972'
QUEUE = Path('/tmp/rockhop-gameplay-telemetry-queuefast.py')
GUARD = ROOT / 'assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py'


def pin(path):
    digest = hashlib.sha256()
    with path.open('rb') as stream:
        for chunk in iter(lambda: stream.read(1024 * 1024), b''): digest.update(chunk)
    return {'path': str(path), 'sha256': digest.hexdigest(), 'bytes': path.stat().st_size}


def save(path, value):
    assert not path.exists(), 'Never overwrite experiment evidence'
    path.write_text(json.dumps(value, indent=2) + '\n')


def build_inventory(build):
    return [pin(path) for path in sorted(build.rglob('*')) if path.is_file()
        and (path.suffix in ['.js', '.wasm', '.html'] or path.name in
            ['version.json', 'rider-remaster-source.json', 'rider-remaster-contract.json', 'model-catalog.json'])]


def validate_inputs(packet, source, build):
    stage = json.loads((packet / 'stage.json').read_text())
    assert stage['accepted'] is False and stage['status'] == 'PRIVATE_CORRECTED_SOURCE_STAGING_ONLY'
    for name, expected in stage['files'].items():
        actual = pin(packet / name)
        assert actual['sha256'] == expected['sha256'] and actual['bytes'] == expected['bytes'], name
    assert stage['profileSHA256'] == pin(PROFILE)['sha256'] == PROFILE_HASH
    source_pin = pin(source)
    assert source_pin['sha256'] == stage['sourceSHA256'] and source_pin['bytes'] == stage['sourceBytes']
    assert source_pin['sha256'] != '585ae314e2b354768a1385e5a85828c142d542b47f8d9fe948f46c7478c112ef'
    for name in ['rider-remaster-source.json', 'rider-remaster-contract.json']:
        assert pin(build / name)['sha256'] == pin(packet / name)['sha256'], 'Exact supplied packet must be compiled'
    raw = json.loads((packet / 'rider-contract.json').read_text())
    runtime = json.loads((packet / 'rider-remaster-contract.json').read_text())
    assert runtime['driver'] == raw['driver'] and runtime['specification'] == raw['specification']
    assert runtime['metadataSHA256'] == stage['contractSHA256'] == pin(packet / 'rider-contract.json')['sha256']
    assert len(runtime['specification']['jointNames']) == 75
    assert runtime['driver']['forearmPronation'] == {'schema': 'native-segment-twist-v1', 'gripProfileHash': PROFILE_HASH}
    transfer_pin = pin(packet / 'profile-transfer.json')
    assert raw['driver']['selectedGripProfile']['applicationTransferSHA256'] == transfer_pin['sha256']
    return stage, source_pin, transfer_pin


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    for name in ['packet', 'source', 'build', 'out', 'evidence']:
        parser.add_argument('--' + name, type=Path, required=True)
    parser.add_argument('--garage-bike', choices=['rookie', 'pro'], default='rookie')
    args = parser.parse_args()
    packet, source, build, out, evidence = [getattr(args, name).resolve()
        for name in ['packet', 'source', 'build', 'out', 'evidence']]
    assert out.is_relative_to(ROOT / 'harness/out/rider-rebuild/focused-delivery07')
    assert evidence.is_relative_to(ROOT / 'docs/evidence/rider-rebuild/focused-delivery07')
    assert build.is_relative_to(ROOT / 'harness/out'), 'Supplied private build only'
    assert not out.exists() and not evidence.exists(), 'Fresh experiment directories required'
    stage, source_pin, transfer_pin = validate_inputs(packet, source, build)
    assert QUEUE.is_file() and GUARD.is_file(), 'Original guard and unchanged admission helper required'
    inventory = build_inventory(build)
    out.mkdir(parents=True); evidence.mkdir(parents=True)
    save(evidence / 'launch-pins.json', {'accepted': False, 'source': source_pin, 'stage': pin(packet / 'stage.json'),
        'rawContract': pin(packet / 'rider-contract.json'), 'runtimeContract': pin(packet / 'rider-remaster-contract.json'),
        'transfer': transfer_pin, 'profile': pin(PROFILE), 'guard': pin(GUARD), 'admissionHelper': pin(QUEUE),
        'buildRuntimeFiles': inventory,
        'limits': 'Compiled bytes pinned before captures; version metadata is not compiled-source revision proof. Parent owns freeze/provenance. Mac CPU render submissions and movie cadence do not establish GPU completion or iPhone FPS.'})
    jobs = [('lean', 'rookie', 'rookie01', '.8'), ('lean', 'pro', 'pro01', '2.35'),
        ('garage', args.garage_bike, 'garage01', '.8')]
    for mode, bike, name, yaw in jobs:
        assert build_inventory(build) == inventory, 'Supplied compiled bytes changed'
        target = out / name; guard = evidence / (name + '-guard')
        command = ['node', 'harness/rider-rebuild/selected-grip-review.mjs', '--build=' + str(build),
            '--source=' + str(source), '--contract=' + str(packet / 'rider-contract.json'),
            '--profile=' + str(PROFILE), '--profile-sha256=' + PROFILE_HASH,
            '--transfer=' + str(packet / 'profile-transfer.json'), '--out=' + str(target),
            '--mode=' + mode, '--bike=' + bike, '--backend=metal', '--camera-yaw=' + yaw,
            '--camera-distance=' + ('3' if mode == 'lean' else '6'),
            '--review-zoom=' + ('2.2' if mode == 'lean' else '1.6'),
            '--garage-wheel-delta=120', '--orbit-seconds=18']
        guarded = ['python3', str(QUEUE), str(evidence / (name + '-telemetry.jsonl')),
            str(guard / 'guard.json'), 'python3', str(GUARD), '--out', str(guard),
            '--limit-seconds', '420', '--', *command]
        save(evidence / (name + '-command.json'), {'accepted': False, 'command': guarded,
            'framing': 'Diagnostic lean matches prior3m/zoom2.2/yaws; Garage wide trusted outward wheel/full orbit. Parent verifies full head/boots in Garage movie.',
            'limits': 'Silent actual Mac capture only. Render FPS is CPU submission measurement; phone and moving-art acceptance remain open.'})
        code = subprocess.call(guarded, cwd=ROOT, env=dict(os.environ, TRIALS_BROWSER_BACKEND='metal'))
        state = json.loads((guard / 'guard.json').read_text()) if (guard / 'guard.json').exists() else None
        if code != 0:
            save(evidence / (name + '-incomplete.json'), {'accepted': False, 'exitCode': code,
                'guard': state, 'limits': 'Incomplete result retained. No repeat, sparse waiver or source promotion.'})
            raise SystemExit(code)
        assert state['exitCode'] == 0 and state['status'] == 'worker returned; review pending'
        report = json.loads((target / 'report.json').read_text())
        assert report['captureChecksCompleted'] and not report.get('failure') and not report['errors']
        assert report['source']['sha256'] == stage['sourceSHA256']
        assert report['presence']['invalidFrames'] == 0 and report['encoding']['exitCode'] == 0
        if mode == 'lean':
            samples = report['played']['motionSamples']
            assert len(samples) == 241 and report['played']['ticks'] == 1200
            assert all(len(sample['joints']) == 75 for sample in samples)
        else:
            assert report['orbit']['wallSeconds'] >= 18 and report['orbit']['fullTurnPixels'] == 640
        assert build_inventory(build) == inventory, 'Compiled bytes changed during actual capture'
        save(evidence / (name + '-result.json'), {'accepted': False, 'report': pin(target / 'report.json'),
            'movie': pin(Path(report['encoding']['encodedPath'])), 'sourceSHA256': stage['sourceSHA256'],
            'compiledBytesBeforeAfterExact': True, 'parentPlayedJudgment': 'PENDING',
            'limits': 'No full contact rerun. Exact native/glove/driver transfer carries prior finite-bar measurement only.'})
        print(json.dumps({'accepted': False, 'saved': name, 'report': str(target / 'report.json')}), flush=True)


if __name__ == '__main__':
    main()
