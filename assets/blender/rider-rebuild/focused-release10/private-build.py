"""Build exact private delivery pins, restoring player files on every exit."""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[4]
OWNED = ROOT / 'harness/out/rider-rebuild/focused-release10'
EVIDENCE = ROOT / 'docs/evidence/rider-rebuild/focused-release10'
PINS = {
    'rider-remaster-source.json': 'public/rider-remaster-source.json',
    'rider-remaster-contract.json': 'public/rider-remaster-contract.json',
    'selectedAsset.ts': 'src/render/hero/selectedAsset.ts',
}


def digest(data):
    return hashlib.sha256(data).hexdigest()


def main(stage_arg, name):
    assert name.isalnum(), 'Fresh alphanumeric build identifier required'
    stage = Path(stage_arg).resolve()
    assert stage.is_relative_to(ROOT / 'harness/out/rider-rebuild/focused-delivery07')
    receipt = json.loads((stage / 'stage.json').read_bytes())
    assert receipt['status'] == 'PRIVATE_CORRECTED_SOURCE_STAGING_ONLY'
    assert receipt['normalizedRuntimeNativeRestExact'] and receipt['native75SpecificationExact']
    packet = {file: (stage / file).read_bytes() for file in PINS}
    for file, data in packet.items():
        assert digest(data) == receipt['files'][file]['sha256'], file
    source = json.loads(packet['rider-remaster-source.json'])
    runtime = json.loads(packet['rider-remaster-contract.json'])
    assert source['sha256'] == runtime['sourceSHA256'] == receipt['sourceSHA256']
    assert source['contractSHA256'] == runtime['metadataSHA256'] == receipt['contractSHA256']
    destination = OWNED / name
    guard = EVIDENCE / (name + '-guard')
    telemetry = EVIDENCE / (name + '-telemetry.jsonl')
    assert not destination.exists() and not guard.exists() and not telemetry.exists()
    EVIDENCE.mkdir(parents=True, exist_ok=True)
    original = {file: (ROOT / target).read_bytes() for file, target in PINS.items()}
    try:
        for file, target in PINS.items():
            (ROOT / target).write_bytes(packet[file])
        subprocess.run(['python3', '/tmp/rockhop-gameplay-telemetry-queuefast.py',
            str(telemetry), str(guard / 'guard.json'), 'python3',
            'assets/blender/hero-remaster/generation-comparison-2026-10-03/user-agent2/run_bounded96.py',
            '--out', str(guard), '--limit-seconds', '420', '--',
            'pnpm', 'exec', 'vite', 'build', '--outDir', str(destination)],
            cwd=ROOT, env=dict(os.environ), check=True)
        for file in ['rider-remaster-source.json', 'rider-remaster-contract.json']:
            assert (destination / file).read_bytes() == packet[file], file
        state = json.loads((guard / 'guard.json').read_bytes())
        assert state['exitCode'] == 0
    finally:
        # Never overwrite a concurrent owner's edit. No other worker owns these pins.
        for file, target in PINS.items():
            current = (ROOT / target).read_bytes()
            assert current in [packet[file], original[file]], ('Concurrent pin edit', target)
            if current == packet[file]:
                (ROOT / target).write_bytes(original[file])
    result = {'accepted': False, 'build': str(destination), 'sourceSHA256': source['sha256'],
        'contractSHA256': source['contractSHA256'], 'playerPinsRestored': True,
        'limits': 'Private exact compiled build only. Parent moving, replay and device gates remain.'}
    (EVIDENCE / (name + '-build.json')).write_text(json.dumps(result, indent=2) + '\n')
    print(json.dumps(result))


if __name__ == '__main__':
    main(*sys.argv[1:])
