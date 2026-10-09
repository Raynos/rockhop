#!/usr/bin/env python3
"""Compile an admitted source correction into fresh private delivery files."""
import argparse
import copy
import hashlib
import json
import re
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
BASE = ROOT / 'harness/out/rider-rebuild/mobile-delivery02/stage04'
BASELINE = '585ae314e2b354768a1385e5a85828c142d542b47f8d9fe948f46c7478c112ef'
RAW = '36bc9a83454f6e885bb0a5d6d90b76d2bbe6658d93144d2da55ce068f627d4ff'
RUNTIME = '50b9bad4b983e24e9aa946bdfaa1009f2a98b3578bd4c1788e672bc7fdfcf94c'
MANIFEST = '04a31cb69541c92f2f69bb2f6320599107a51ea94d0255a08175e20045050532'
PROFILE = '659ff94c1611e0ce95310ab090e94637832ac2bbfbac7f9554f903595bd05972'
AUTHORING = 'f814b8d7cde87b1e41b45eec75cd55fdea89b915bf9acae0e5a18b40d3a156af'
AUTHORING_CONTRACT = '0301087649f7e2b2c442299bb21f61dc1e325c6b5b84afbc3ac5c4a594b72813'
TRANSFER = ROOT / 'docs/evidence/rider-rebuild/mobile-textures02/combined01/decoded-parity.json'
TRANSFER_HASH = '2e9aa3ec652ac5a2732d9a66122bf9ae898bed6a914edb73d143e6c0bc77c3bc'


def encoded(value):
    return (json.dumps(value, indent=2) + '\n').encode()


def sha(data):
    return hashlib.sha256(data).hexdigest()


def pin(path):
    data = path.read_bytes()
    return {'path': str(path), 'sha256': sha(data), 'bytes': len(data)}


def read_bases():
    values = []
    for name, expected in [('rider-contract.json', RAW), ('rider-remaster-contract.json', RUNTIME),
                           ('rider-remaster-source.json', MANIFEST)]:
        data = (BASE / name).read_bytes()
        assert sha(data) == expected, ('Exact stage04 baseline bytes required', name)
        values.append(json.loads(data))
    raw, runtime, manifest = values
    assert raw['glbSHA256'] == runtime['sourceSHA256'] == manifest['sha256'] == BASELINE
    assert runtime['metadataSHA256'] == manifest['contractSHA256'] == RAW
    assert raw['driver'] == runtime['driver'] and raw['specification'] == runtime['specification']
    assert len(raw['specification']['jointNames']) == 75
    assert raw['driver']['gripProfileHash'] == PROFILE
    assert raw['driver']['forearmPronation'] == {'schema': 'native-segment-twist-v1', 'gripProfileHash': PROFILE}
    profile_bytes = (ROOT / 'docs/evidence/rider-rebuild/selected-grip-kinematic02/thumbplane05/runtime-profile.json').read_bytes()
    assert sha(profile_bytes) == PROFILE
    profile = json.loads(profile_bytes)
    assert profile['source']['sha256'] == AUTHORING and profile['contractSHA256'] == AUTHORING_CONTRACT
    assert raw['driver']['selectedGripProfile']['authoringSourceSHA256'] == AUTHORING
    assert raw['driver']['selectedGripProfile']['appliesToSourceSHA256'] == BASELINE
    for side in ['left', 'right']:
        for key in ['digitFlex', 'gripSocketPositionBike', 'gripSocketQuaternionBike']:
            assert raw['driver'][key][side] == profile['hands'][side][key]
    return values


def assemble(raw, runtime, manifest, upload, parity, parity_bytes, facts, selected_template):
    """Pure deterministic serializer; main verifies admitted source before calling."""
    assert upload['sha256'] == parity['candidate']['sha256'] == facts['sourceSHA256']
    assert upload['bytes'] == parity['candidate']['bytes']
    assert upload['sha256'] != BASELINE and re.fullmatch('[a-f0-9]{64}', upload['sha256'])
    assert upload['pathname'] == 'rider-remaster/' + upload['sha256'] + '/rider.glb'
    host = manifest['url'].split('/rider-remaster/')[0]
    assert upload['url'] == host + '/' + upload['pathname'], 'Exact immutable upload URL'
    assert upload['contentType'] == 'model/gltf-binary'
    assert facts['pass'] and facts['actualDecodedAccessorHashesChecked']
    assert facts['actualOriginalBINPrefixChecked'] and facts['actualImagePayloadHashesChecked']
    raw, runtime, manifest = copy.deepcopy((raw, runtime, manifest))
    original_driver = copy.deepcopy(raw['driver'])
    original_rest = copy.deepcopy(runtime['nativeRest'])
    original_spec = copy.deepcopy(runtime['specification'])
    transfer = {'schema': 'selected-cuff-profile-transfer-v1', 'accepted': False, 'pass': True,
        'baseline': {'sha256': BASELINE, 'rawContractSHA256': RAW, 'normalizedRuntimeSHA256': RUNTIME},
        'candidate': copy.deepcopy(parity['candidate']),
        'profileAuthoring': {'sourceSHA256': AUTHORING, 'contractSHA256': AUTHORING_CONTRACT, 'profileSHA256': PROFILE},
        'baselineProfileTransferReceipt': {'path': str(TRANSFER), 'sha256': TRANSFER_HASH,
            'scope': 'Historical authoring-to-baseline graft proof; changed corrected sleeve streams are not protected-exact claims.'},
        'parityReceipt': {'path': 'source-parity.json', 'sha256': sha(parity_bytes)}, 'parityReceiptBytes': parity_bytes.decode(),
        'parity': parity, 'sourcePatch': parity['sourcePatch'],
        'verification': facts, 'limits': 'Parent new-source movie and replay required. Exact gloves/native rig/driver allow inherited finite-bar measurement only; cuff appearance and phone FPS remain open.'}
    transfer_bytes = encoded(transfer)
    lineage = {'accepted': False, 'baselineSourceSHA256': BASELINE, 'baselineRawContractSHA256': RAW,
        'baselineNormalizedRuntimeSHA256': RUNTIME, 'profileAuthoringSourceSHA256': AUTHORING,
        'profileAuthoringContractSHA256': AUTHORING_CONTRACT, 'profileSHA256': PROFILE,
        'appliesToSourceSHA256': upload['sha256'], 'transferReceiptSHA256': sha(transfer_bytes),
        'sourcePatch': parity['sourcePatch'], 'changedAccessors': parity['changedAccessors'],
        'limits': 'Only enumerated hoodie streams changed. All other streams/maps/native records remain exact; parent source correction and moving-art judgment are pending.'}
    raw['glbSHA256'] = upload['sha256']
    raw['driver']['selectedGripProfile'].update(authoringContractSHA256=AUTHORING_CONTRACT,
        baselineApplicationSourceSHA256=BASELINE, appliesToSourceSHA256=upload['sha256'],
        applicationTransferSHA256=sha(transfer_bytes),
        limits='Exact native/glove controls inherited through declared sleeve correction; new-source played/replay and cuff acceptance required.')
    raw['selectedCuffCorrection07'] = lineage
    raw_bytes = encoded(raw)
    runtime['sourceSHA256'] = upload['sha256']
    runtime['metadataSHA256'] = sha(raw_bytes)
    runtime['driver'] = copy.deepcopy(raw['driver'])
    runtime['selectedRiderSource'].update(sourceSHA256=upload['sha256'],
        geometryPolicy='Declared selected hoodie cuff POSITION/NORMAL/TANGENT and any explicitly declared native-field correction; all glove/native rig/map streams remain exact to measured baseline')
    assert runtime['nativeRest'] == original_rest and runtime['specification'] == original_spec
    semantic_driver = copy.deepcopy(raw['driver']); semantic_driver.pop('selectedGripProfile')
    baseline_driver = copy.deepcopy(original_driver); baseline_driver.pop('selectedGripProfile')
    assert semantic_driver == baseline_driver, 'Every actual pose/contact control stays exact'
    manifest.update({key: upload[key] for key in ['url', 'pathname', 'bytes', 'sha256', 'contentType']})
    manifest.update(contractSHA256=sha(raw_bytes),
        acceptance='Unaccepted corrected cuff private staging; parent new-source movie/replay and physical iPhone performance pending')
    selected = re.sub(r'SELECTED_RIDER_BYTES = \d+;', 'SELECTED_RIDER_BYTES = %d;' % upload['bytes'], selected_template)
    for key, value in [('url', upload['url']), ('sha256', upload['sha256']), ('contractSHA256', sha(raw_bytes))]:
        selected, count = re.subn(key + r": '[^']+'", key + ": '" + value + "'", selected)
        assert count == 1, ('Exact selectedAsset template pin count', key)
    packet = {'rider-contract.json': raw_bytes, 'rider-remaster-contract.json': encoded(runtime),
        'rider-remaster-source.json': encoded(manifest), 'selectedAsset.ts': selected.encode(),
        'profile-transfer.json': transfer_bytes, 'source-parity.json': parity_bytes}
    stage = {'accepted': False, 'status': 'PRIVATE_CORRECTED_SOURCE_STAGING_ONLY', 'workingTreeApplied': False,
        'sourceSHA256': upload['sha256'], 'sourceBytes': upload['bytes'], 'contractSHA256': sha(raw_bytes),
        'normalizedRuntimeSHA256': sha(packet['rider-remaster-contract.json']), 'profileSHA256': PROFILE,
        'normalizedRuntimeNativeRestExact': True, 'native75SpecificationExact': True,
        'poseAndContactDriverExactExceptSourceDeclaration': True, 'changedAccessors': parity['changedAccessors'],
        'inheritedFiniteBarEvidence': ['docs/evidence/rider-rebuild/fixed-grip-engine04/rookie01-contact05/receipt.json',
            'docs/evidence/rider-rebuild/fixed-grip-engine04/pro01-contact05/receipt.json'],
        'limits': 'Inherited finite-bar interaction only. Parent new-source moving judgment, replay/ship gate/checked deploy and physical iPhone performance remain required.',
        'files': {name: {'sha256': sha(data), 'bytes': len(data)} for name, data in packet.items()}}
    packet['stage.json'] = encoded(stage)
    return packet


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--candidate', type=Path, required=True)
    parser.add_argument('--source-receipt', type=Path, required=True)
    parser.add_argument('--parity', type=Path, required=True)
    parser.add_argument('--out', type=Path, required=True)
    args = parser.parse_args()
    out = args.out.resolve()
    assert out.is_relative_to(ROOT / 'harness/out/rider-rebuild/focused-delivery07'), 'Private owned staging output only'
    assert not out.exists(), 'Never overwrite a staged packet'
    raw, runtime, manifest = read_bases()
    assert pin(TRANSFER)['sha256'] == TRANSFER_HASH
    historical = json.loads(TRANSFER.read_bytes())
    assert historical['pass'] and historical['candidate']['sha256'] == BASELINE
    assert historical['selectedCheckpointReference']['sha256'] == AUTHORING
    parity_bytes = args.parity.read_bytes(); parity = json.loads(parity_bytes)
    for record in parity['sourcePatch'].values():
        assert pin(Path(record['path'])) == record, 'Exact source patch/fit receipt required'
    assert len(parity['sourcePatch']) == 2 and set(parity['sourcePatch']) == {'report', 'patch'}
    # This parent-admitted invocation checks source bytes; no browser or production writes.
    facts = json.loads(subprocess.check_output(['node', str(Path(__file__).with_name('verify-parity.mjs')),
        str(args.parity), str(args.candidate)], cwd=ROOT, text=True))
    upload = json.loads(args.source_receipt.read_bytes())
    packet = assemble(raw, runtime, manifest, upload, parity, parity_bytes, facts,
        (ROOT / 'src/render/hero/selectedAsset.ts').read_text())
    out.mkdir(parents=True)
    for name, data in packet.items(): (out / name).write_bytes(data)
    print((out / 'stage.json').read_text())


if __name__ == '__main__':
    main()
