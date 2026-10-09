#!/usr/bin/env python3
"""Collect one fixed component family's verified encoding checkpoint."""
import argparse, json, shutil
from pathlib import Path

p = argparse.ArgumentParser()
p.add_argument('component')
p.add_argument('--baker-checkpoint', required=True)
p.add_argument('--directory', type=Path)
p.add_argument('--evidence', type=Path)
args = p.parse_args()
base = args.directory or Path('harness/out/rider-rebuild/mobile-textures02/components01') / args.component
evidence = args.evidence or Path('docs/evidence/rider-rebuild/mobile-textures02/components01') / args.component
assert not evidence.exists(), 'Use a fresh evidence directory'
def read(name):
    return json.loads((base / name).read_text())
inventory = read('inventory.json')
encoded = read('uastc-rdo05-encode.json')
runtime = read('uastc-rdo05-runtime-transcode.json')
proof = read('uastc-rdo05-astc-proof.json')
metrics = read('uastc-rdo05-astc-decoded-difference.json')
outliers = read('normal-outliers.json')
assert inventory['component'] == args.component
assert len(encoded) == len(runtime) == len(proof) == len(metrics) == 3
assert all(f['allLevelsSucceeded'] for row in runtime for f in row['formats'])
assert all(row['astcSoftwareDecodedRGBAIdenticalToRuntimeRGBA'] and all(level['nativeBlocksByteIdentical'] for level in row['levels']) for row in proof)
guards = sorted(base.glob('encode-guard*/guard.json'))
guard_rows = [json.loads(path.read_text()) for path in guards]
assert guard_rows and any(row.get('exitCode') == 0 for row in guard_rows), 'Successful original guarded encoding required'
assert all(row['startAnonymousBelowGiB'] == 55 and row['stopAnonymousGiB'] == 65 and row['stopAnonymousPlusWiredGiB'] == 96 for row in guard_rows)
gpu = {f['name']: sum(next(x['totalMipBytes'] for x in row['formats'] if x['name'] == f['name']) for row in runtime) for f in runtime[0]['formats']}
summary = {'accepted': False, 'component': args.component, 'sourceBakerCheckpoint': args.baker_checkpoint,
           'sourceOriginalMasterSHA256': inventory['sourceOriginalSelectedSHA256'],
           'sourceBakeMetadataSHA256': inventory['sourceSha256'], 'sourcePNGBytes': inventory['originalTextureBytes'],
           'KTX2Bytes': sum(row['bytes'] for row in encoded), 'textureGPUBytesFullMip': gpu,
           'transcodes': sum(row['levels'] * len(row['formats']) for row in runtime),
           'alphaChangedPixels': sum(row['alpha']['changedPixels'] for row in metrics),
           'nativeASTCAndPinnedRuntimeBlockPixelProof': True, 'normalAngularDegrees': metrics[2]['normalAngularDegrees'],
           'normalOutliers': outliers, 'guardAdmissionAndStopLimitsUnchanged': True,
           'guardResults': [{'path': str(path), 'status': row['status'], 'exitCode': row.get('exitCode'), 'samples': len(row['samples'])} for path,row in zip(guards,guard_rows)],
           'limits': ['Compression compares to this new baked PNG; source-field/native posed witnesses are independent builder evidence.',
                      'Normal outliers include every source pixel; no UV occupancy mask or short-vector exclusions.',
                      'Software ASTC linear pixels do not prove sRGB GPU filtering or moving appearance. BC7 pixels not measured.',
                      'Combined appearance and phone memory/FPS remain unqualified. No production pin/deployment.']}
evidence.mkdir(parents=True)
for name in ['inventory.json','uastc-rdo05-encode.json','uastc-rdo05-runtime-transcode.json','uastc-rdo05-astc-proof.json','uastc-rdo05-astc-decoded-difference.json','normal-outliers.json']:
    shutil.copyfile(base / name, evidence / name)
for path in guards:
    shutil.copyfile(path, evidence / (path.parent.name + '.json'))
(evidence / 'summary.json').write_text(json.dumps(summary, indent=2) + '\n')
print(json.dumps({'component':args.component,'KTX2Bytes':summary['KTX2Bytes'],'GPU':gpu,'alphaChangedPixels':summary['alphaChangedPixels'],'evidence':str(evidence)}))
