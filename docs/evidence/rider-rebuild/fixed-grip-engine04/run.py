"""Unaccepted actual fixed-engine movies/contact. Fresh outputs; shared guard intact."""
import hashlib, json, subprocess, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
SOURCE = ROOT / 'harness/out/rider-rebuild/mobile-textures02/combined01/rider.glb'
CONTRACT = ROOT / 'harness/out/rider-rebuild/mobile-delivery02/stage04/rider-contract.json'
PROFILE = ROOT / 'docs/evidence/rider-rebuild/selected-grip-kinematic02/thumbplane05/runtime-profile.json'
TRANSFER = ROOT / 'docs/evidence/rider-rebuild/mobile-textures02/combined01/decoded-parity.json'
EVIDENCE = ROOT / 'docs/evidence/rider-rebuild/fixed-grip-engine04'
OUT = ROOT / 'harness/out/rider-rebuild/fixed-grip-engine04'
PINS = {
    'source': '585ae314e2b354768a1385e5a85828c142d542b47f8d9fe948f46c7478c112ef',
    'contract': '36bc9a83454f6e885bb0a5d6d90b76d2bbe6658d93144d2da55ce068f627d4ff',
    'profile': '659ff94c1611e0ce95310ab090e94637832ac2bbfbac7f9554f903595bd05972',
    'normalizedRuntimeContract': '50b9bad4b983e24e9aa946bdfaa1009f2a98b3578bd4c1788e672bc7fdfcf94c',
}
def digest(p):
    h = hashlib.sha256()
    with p.open('rb') as f:
        for block in iter(lambda: f.read(1024 * 1024), b''): h.update(block)
    return h.hexdigest()

def guarded(name, command):
    guard = EVIDENCE / (name + '-guard')
    telemetry = EVIDENCE / (name + '-telemetry.jsonl')
    assert not guard.exists() and not telemetry.exists(), 'Fresh named experiment required'
    command = ['python3', '/tmp/rockhop-gameplay-telemetry-queuefast.py', str(telemetry),
        str(guard / 'guard.json'), 'python3',
        'assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py',
        '--out', str(guard), '--limit-seconds', '420', '--', *command]
    receipt = {'accepted': False, 'name': name, 'command': command,
        'limits': 'Actual Mac diagnostic/played evidence only; no phone FPS or art acceptance.'}
    (EVIDENCE / (name + '-command.json')).write_text(json.dumps(receipt, indent=2) + '\n')
    subprocess.run(command, cwd=ROOT, check=True, env=dict(__import__('os').environ, TRIALS_BROWSER_BACKEND='metal'))
    state = json.loads((guard / 'guard.json').read_text())
    assert state['exitCode'] == 0 and state['status'] == 'worker returned; review pending'

def main():
    assert len(sys.argv) == 2, 'Exact parent-approved compiled build directory required'
    build = Path(sys.argv[1]).resolve()
    assert build == ROOT / 'harness/out/rider-rebuild/mobile-delivery02/build02'
    gate = json.loads((ROOT / 'docs/evidence/rider-rebuild/mobile-delivery02/build03-guard/guard.json').read_text())
    assert gate['exitCode'] == 0 and gate['status'] == 'worker returned; review pending'
    built = json.loads((build / 'rider-remaster-source.json').read_text())
    assert built['sha256'] == PINS['source'] and built['bytes'] == 74833728
    for name, p in [('source', SOURCE), ('contract', CONTRACT), ('profile', PROFILE)]:
        assert digest(p) == PINS[name], (name, 'Pinned input differs')
    assert built['contractSHA256'] == PINS['contract']
    assert digest(build / 'rider-remaster-contract.json') == PINS['normalizedRuntimeContract']
    runtime = json.loads((build / 'rider-remaster-contract.json').read_text())
    assert runtime['sourceSHA256'] == PINS['source'] and runtime['metadataSHA256'] == PINS['contract']
    OUT.mkdir(parents=True, exist_ok=True)
    contract = json.loads(CONTRACT.read_text())
    assert all(runtime[key] == contract[key] for key in ['driver', 'specification'])
    staged_runtime = json.loads((CONTRACT.parent / 'rider-remaster-contract.json').read_text())
    assert runtime == staged_runtime, 'Exact staged normalized rest/metadata required'
    declaration = contract['driver']['forearmPronation']
    assert declaration == {'schema': 'native-segment-twist-v1', 'gripProfileHash': PINS['profile']}
    assert contract['driver']['gripProfileHash'] == PINS['profile']
    for mode, bike, name, yaw in [('lean', 'rookie', 'rookie01', '.8'),
        ('lean', 'pro', 'pro01', '2.35'), ('garage', 'rookie', 'garage-rookie01', '.8'),
        ('garage', 'pro', 'garage-pro01', '2.35')]:
        target = OUT / name
        assert not target.exists(), 'Never overwrite an earlier movie'
        guarded(name, ['node', 'harness/rider-rebuild/selected-grip-review.mjs',
            '--build=' + str(build), '--source=' + str(SOURCE), '--contract=' + str(CONTRACT),
            '--profile=' + str(PROFILE), '--profile-sha256=' + PINS['profile'],
            '--transfer=' + str(TRANSFER), '--out=' + str(target), '--mode=' + mode,
            '--bike=' + bike, '--backend=metal', '--camera-yaw=' + yaw, '--review-zoom=2.2'])
        report = json.loads((target / 'report.json').read_text())
        assert report['captureChecksCompleted'] and not report.get('failure') and not report['errors']
        assert report['identity']['driver']['forearmPronation'] == declaration
        if mode == 'lean':
            poses = report['played']['motionSamples']
            assert len(poses) == 241 and all(len(p['joints']) == 75 for p in poses)
            assert all(len(p['debug']['forearmPronation']) == 2 and
                all(__import__('math').isfinite(s['radians']) for s in p['debug']['forearmPronation']) for p in poses)
        else:
            assert len(report['garageEnd']['debug']['forearmPronation']) == 2
        print(json.dumps({'accepted': False, 'saved': name, 'report': str(target / 'report.json')}), flush=True)
    for name in ['rookie01', 'pro01']:
        guarded(name + '-contact', ['node',
            'assets/blender/rider-rebuild/mobile-mesh02/verify-played-grip.mjs',
            str(SOURCE), str(CONTRACT), str(OUT / name / 'report.json'), str(OUT / (name + '-contact'))])

if __name__ == '__main__': main()
