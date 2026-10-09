"""Preserve completed exhaustive finite-bar results without rerunning contact."""
import gzip
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
EVIDENCE = Path(__file__).resolve().parent
OUT = ROOT / 'harness/out/rider-rebuild/fixed-grip-engine04'


def pin(path):
    data = path.read_bytes()
    return {'path': str(path.relative_to(ROOT)), 'sha256': hashlib.sha256(data).hexdigest(), 'bytes': len(data)}


def archive(name):
    target = EVIDENCE / (name + '-contact05')
    assert not target.exists(), 'Never overwrite earlier contact evidence'
    source = OUT / (name + '-contact')
    report = json.loads((OUT / name / 'report.json').read_text())
    summary = json.loads((source / 'summary.json').read_text())
    guard = json.loads((EVIDENCE / (name + '-contact-guard/guard.json')).read_text())
    assert guard['exitCode'] == 0 and guard['status'] == 'worker returned; review pending'
    assert summary['poses'] == 241 and summary['playedReportSHA256'] == pin(OUT / name / 'report.json')['sha256']
    assert summary['sourceSHA256'] == report['source']['sha256']
    assert summary['contractSHA256'] == report['contract']['sha256']
    assert summary['profileSHA256'] == report['requestedGripProfileSHA256']
    assert summary['finiteBikeGeometrySHA256'] == report['bikeAsset']['sha256']
    target.mkdir()
    receipt = {'accepted': False, 'measurement': summary, 'guardElapsedSeconds': guard['elapsedSeconds'],
        'verifier': pin(ROOT / 'assets/blender/rider-rebuild/mobile-mesh02/verify-played-grip.mjs'),
        'archives': [], 'declaredPulpGapRangesMeters': {},
        'limits': 'Exhaustive finite-bar interaction only. Declared source-normal pulp buckets are not independent anatomy certification. Cuff appearance, final corrected-source replay/deploy and sustained physical iPhone FPS remain parent gates.'}
    for side in ['left', 'right']:
        data = (source / (side + '.json')).read_bytes()
        result = json.loads(data)
        assert len(result['samples']) == 241
        gaps = {digit: [] for digit in ['thumb', 'index', 'middle', 'ring', 'pinky']}
        for index, sample in enumerate(result['samples']):
            assert sample['tick'] == index * 5
            surface = sample['fullSurface']
            assert surface['ownedVertices'] == result['vertices']
            assert surface['ownedTriangles'] == result['triangles']
            assert surface['insideCount'] == surface['maxPenetrationM'] == surface['crossingPairs'] == 0
            for digit in gaps:
                bucket = sample['semantic'][digit + '/declared-pulp-facing']
                assert bucket['nearBarVertices'] > 0 and bucket['inside'] == 0
                gaps[digit].append(bucket['minimumGapMeters'])
        receipt['declaredPulpGapRangesMeters'][side] = {
            digit: {'minimum': min(values), 'maximum': max(values), 'samples': len(values)}
            for digit, values in gaps.items()}
        archive_path = target / (side + '.json.gz')
        archive_path.write_bytes(gzip.compress(data, mtime=0))
        assert gzip.decompress(archive_path.read_bytes()) == data
        receipt['archives'].append({'original': pin(source / (side + '.json')), 'compressed': pin(archive_path)})
    (target / 'receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    (target / 'summary.json').write_bytes((source / 'summary.json').read_bytes())
    print(json.dumps({'accepted': False, 'name': name, 'gapRanges': receipt['declaredPulpGapRangesMeters']}))


if __name__ == '__main__':
    archive('rookie01')
    archive('pro01')
    reports = [json.loads((OUT / name / 'report.json').read_text()) for name in
        ['rookie01', 'pro01', 'garage-rookie01', 'garage-pro01']]
    assert all(r['sourcePinsAtCapture'] == reports[0]['sourcePinsAtCapture'] for r in reports)
    build = ROOT / 'harness/out/rider-rebuild/mobile-delivery02/build02'
    inventory = {'accepted': False, 'scope': 'Post-capture inventory of retained compiled bytes, not a build-source snapshot or physics replay.',
        'sourcePinsAtCaptureIdenticalAcrossFourCaptures': reports[0]['sourcePinsAtCapture'],
        'leanPhysicsHz': [r['camera']['info']['physicsHz'] for r in reports[:2]],
        'buildGuard': pin(EVIDENCE.parent / 'mobile-delivery02/build03-guard/guard.json'),
        'buildVersion': json.loads((build / 'version.json').read_text()),
        'runtimeFiles': [pin(p) for p in sorted(build.rglob('*')) if p.is_file()
            and (p.suffix in ['.js', '.wasm', '.html'] or p.name in
                ['version.json', 'rider-remaster-source.json', 'rider-remaster-contract.json'])],
        'limits': 'Working-tree capture source hashes do not independently identify the compiled source revision. The build02-guard private receipt names older build01 and is not a receipt for this capture build. No acceptance or replay claim.'}
    path = EVIDENCE / 'compiled-byte-inventory05.json'
    assert not path.exists()
    path.write_text(json.dumps(inventory, indent=2) + '\n')
