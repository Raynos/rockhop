#!/usr/bin/env python3
"""Stage one source-preserving delivery and fitted native controls for private review."""
import argparse, copy, hashlib, json, re
from pathlib import Path

parser = argparse.ArgumentParser()
parser.add_argument('--source-receipt', type=Path, required=True)
parser.add_argument('--composition', type=Path, required=True)
parser.add_argument('--profile', type=Path, required=True)
parser.add_argument('--base-contract', type=Path, default=Path('harness/out/rider-rebuild/download-opt01/delivery01/rider-contract.json'))
parser.add_argument('--out', type=Path, required=True)
parser.add_argument('--apply-private', action='store_true')
parser.add_argument('--forearm-pronation', action='store_true')
args = parser.parse_args()
sha = lambda data: hashlib.sha256(data).hexdigest()
encoded = lambda value: (json.dumps(value, indent=2) + '\n').encode()
base_bytes = args.base_contract.read_bytes()
base = json.loads(base_bytes)
runtime = json.loads(Path('public/rider-remaster-contract.json').read_bytes())
manifest = json.loads(Path('public/rider-remaster-source.json').read_bytes())
assert runtime['metadataSHA256'] == manifest['contractSHA256'] == sha(base_bytes)
assert runtime['sourceSHA256'] == manifest['sha256'] == base['glbSHA256']
assert runtime['driver'] == base['driver'] and runtime['specification'] == base['specification']
profile_bytes = args.profile.read_bytes()
profile = json.loads(profile_bytes)
assert profile['schema'] == 'rockhop-selected-grip-kinematic-v2'
assert profile['source']['sha256'] == base['glbSHA256'] and profile['contractSHA256'] == sha(base_bytes)
receipt = json.loads(args.source_receipt.read_bytes())
composition = json.loads(args.composition.read_bytes())
assert composition['selectedSourceSHA256'] == base['glbSHA256']
assert composition['candidate']['sha256'] == receipt['sha256']
assert composition['candidate']['bytes'] == receipt['bytes']
assert composition['nativeRigAndAnimationJSONExact'] and composition['nativeJoints'] == 75
assert receipt['pathname'] == 'rider-remaster/' + receipt['sha256'] + '/rider.glb'
assert receipt['url'].endswith('/' + receipt['pathname'])
original_native_rest = copy.deepcopy(runtime['nativeRest'])
for side in ['left', 'right']:
    hand = profile['hands'][side]
    assert set(hand['digitFlex']) == set(base['driver']['digitFlex'][side])
    for joint, control in hand['digitFlex'].items():
        assert joint in base['specification']['jointNames']
        assert len(control['axisLocal']) == 3 and abs(sum(x*x for x in control['axisLocal']) - 1) < 1e-6
        assert 0 <= control['maxRadians'] <= 3.141592653589793
    base['driver']['digitFlex'][side] = hand['digitFlex']
    for key in ['gripSocketPositionBike', 'gripSocketQuaternionBike']:
        base['driver'].setdefault(key, {})[side] = hand[key]
base['driver']['gripProfileHash'] = sha(profile_bytes)
if args.forearm_pronation:
    base['driver']['forearmPronation'] = {
        'schema': 'native-segment-twist-v1', 'gripProfileHash': sha(profile_bytes)}
base['driver']['selectedGripProfile'] = {
    'accepted': False, 'profileSHA256': sha(profile_bytes),
    'authoringSourceSHA256': profile['source']['sha256'],
    'appliesToSourceSHA256': receipt['sha256'],
    'limits': 'Parent full-arm/cuff, both-bike motion and new reduced-surface contact qualification required.'}
base['glbSHA256'] = receipt['sha256']
base['mobileDelivery02'] = {'accepted': False, 'compositionReceiptSHA256': sha(args.composition.read_bytes()),
    'profileSHA256': sha(profile_bytes), 'parentContractSHA256': sha(base_bytes),
    'limits': 'Unaccepted private review. Source native75 and normalized runtime rest retained.'}
contract_bytes = encoded(base)
contract_sha = sha(contract_bytes)
runtime['driver'] = copy.deepcopy(base['driver'])
runtime['sourceSHA256'] = receipt['sha256']
runtime['metadataSHA256'] = contract_sha
runtime['selectedRiderSource'].update(sourceSHA256=receipt['sha256'],
    geometryPolicy='Selected original boot/glove fields retained on simplified meshes with source-detail bake; protected parts unchanged',
    texturePolicy='Protected hoodie/face/hair maps retained; jeans ORM2K and component2K UASTC/RDO0.5')
assert runtime['nativeRest'] == original_native_rest
manifest.update({k:receipt[k] for k in ['url', 'pathname', 'bytes', 'sha256', 'contentType']})
manifest.update(contractSHA256=contract_sha, texturePolicy=runtime['selectedRiderSource']['texturePolicy'],
    acceptance='Unaccepted private moving review; phone performance and final art gates remain open')
args.out.mkdir(parents=True, exist_ok=False)
(args.out/'rider-contract.json').write_bytes(contract_bytes)
(args.out/'rider-remaster-contract.json').write_bytes(encoded(runtime))
(args.out/'rider-remaster-source.json').write_bytes(encoded(manifest))
report = {'accepted': False, 'sourceSHA256': receipt['sha256'], 'bytes': receipt['bytes'],
    'contractSHA256': contract_sha, 'profileSHA256': sha(profile_bytes),
    'normalizedRuntimeNativeRestUnchanged': True, 'originalMasterSHA256': manifest['originalMasterSHA256'],
    'status': 'PRIVATE_STAGING_ONLY', 'workingTreeApplied': args.apply_private,
    'nativeForearmPronationOptIn': args.forearm_pronation}
(args.out/'stage.json').write_bytes(encoded(report))
if args.apply_private:
    Path('public/rider-remaster-source.json').write_bytes(encoded(manifest))
    Path('public/rider-remaster-contract.json').write_bytes(encoded(runtime))
    ts = Path('src/render/hero/selectedAsset.ts').read_text()
    ts = re.sub(r'SELECTED_RIDER_BYTES = \d+;', f"SELECTED_RIDER_BYTES = {receipt['bytes']};", ts)
    for key, value in [('url',receipt['url']),('sha256',receipt['sha256']),('contractSHA256',contract_sha)]:
        ts, count = re.subn(key + r": '[^']+'", f"{key}: '{value}'", ts)
        assert count == 1
    Path('src/render/hero/selectedAsset.ts').write_text(ts)
print(json.dumps(report))
