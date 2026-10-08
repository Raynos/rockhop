"""Reuse the two pinned original rig actions on an explicitly pinned new target."""
import argparse
import copy
import hashlib
import importlib.util
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
ORIGINAL = {
    'input': {
        'path': 'assets/blender/rider-rebuild/selected-garage-actions01/input.json',
        'sha256': '8ca1d9d938019740fde7e17f073309b9ad6c31dc33d636420541b28308d54db7',
    },
    'appendHelper': {
        'path': 'assets/blender/rider-rebuild/selected-garage-actions01/append_actions.py',
        'sha256': 'a5cee1272e81ada241f38c66ab370949a7deb6ef5eea5088ba4d610a8e1959e8',
    },
}
OUTPUT_ROOT = ROOT / 'harness/out/rider-rebuild/selected-action-transport02'


def sha(path):
    digest = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024 * 1024):
            digest.update(block)
    return digest.hexdigest()


def pin(row):
    assert set(row) == {'path', 'sha256'}, 'Expected an explicit path/SHA256 pin'
    assert isinstance(row['path'], str) and row['path'], 'Target path is unset'
    assert isinstance(row['sha256'], str) and len(row['sha256']) == 64
    assert all(char in '0123456789abcdef' for char in row['sha256'])
    path = (ROOT / row['path']).resolve()
    assert path.is_relative_to(ROOT), 'Pins must stay inside the repository'
    assert sha(path) == row['sha256'], ('Changed source', row)
    return path


def original_actions(config):
    assert config['accepted'] is False and config['sourceReady'] is True
    assert config['originalActionProvenance'] == ORIGINAL, 'Original action provenance changed'
    original = json.loads(pin(ORIGINAL['input']).read_text())
    helper_path = pin(ORIGINAL['appendHelper'])
    assert original['accepted'] is False and original['ready'] is True
    assert original['appendHelperSHA256'] == ORIGINAL['appendHelper']['sha256']
    provenance = original['resumeInputs']
    receipt = json.loads(pin(provenance['rigReceipt']).read_text())
    assert receipt['accepted'] is False and receipt['rigOnlyNoMeshes'] and receipt['exact75Rest']
    assert receipt['inputSHA256'] == provenance['originalInputSHA256']
    reconstructed = copy.deepcopy(original)
    reconstructed.pop('resumeInputs')
    reconstructed['appendHelperSHA256'] = provenance['originalAppendHelperSHA256']
    encoded = (json.dumps(reconstructed, indent=2) + '\n').encode()
    assert hashlib.sha256(encoded).hexdigest() == receipt['inputSHA256'], 'Original config reconstruction failed'
    rig_dir = pin(provenance['rigReceipt']).parent
    for key, filename in [('rigGLB', 'rig-actions.glb'), ('nativeMatrices', 'native-action-matrices.npz'),
                          ('editableNative', 'native75-two-original-actions.blend')]:
        assert pin(provenance[key]) == rig_dir / filename
    assert receipt['native'] == provenance['editableNative']
    assert len(original['actions']) == len(receipt['actions']) == 2
    for expected, actual in zip(original['actions'], receipt['actions']):
        for key in ('name', 'slot', 'frameRange'):
            assert expected[key] == actual[key], ('Original action changed', key)
    return original, receipt, rig_dir, helper_path


def transport(config_path, out, config, original, receipt, rig_dir, helper_path):
    target = config['futureTarget']
    assert target['ready'] is True, 'Future target is unset; source readiness is not execution'
    assert set(target) == {'ready', 'sourceGLB', 'contract', 'calibration'}
    paths = {key: pin(target[key]) for key in ('sourceGLB', 'contract', 'calibration')}
    for key in paths:
        assert paths[key] != (ROOT / original[key]['path']).resolve(), ('Requires a NEW target pin', key)
    assert target['sourceGLB']['sha256'] != original['sourceGLB']['sha256'], 'Requires corrected target geometry'
    contract = json.loads(paths['contract'].read_text())
    calibration = json.loads(paths['calibration'].read_text())
    assert contract['glbSHA256'] == contract['sourceSHA256'] == target['sourceGLB']['sha256']
    assert calibration['sourceSHA256'] == target['sourceGLB']['sha256']
    original_contract = json.loads(pin(original['contract']).read_text())
    assert contract['nativeRest'] == original_contract['nativeRest'], 'Target canonical75/rest contract changed'
    out = out.resolve()
    assert out.is_relative_to(OUTPUT_ROOT) and out != OUTPUT_ROOT and not out.exists(), 'Use a fresh output child'
    # Keep the original config immutable. Only this separate target replaces its
    # three surface/contract/calibration inputs; original action lineage remains.
    run_config = copy.deepcopy(original)
    for key in paths:
        run_config[key] = target[key]
    spec = importlib.util.spec_from_file_location('original_selected_append', helper_path)
    helper = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(helper)
    helper.append(run_config, config_path, out, receipt, rig_source_dir=rig_dir)
    report = {
        'accepted': False,
        'status': 'ORIGINAL_ACTIONS_APPENDED_TO_NEW_TARGET_GARAGE_REVIEW_PENDING',
        'originalActionProvenance': ORIGINAL,
        'originalRigExport': original['resumeInputs'],
        'target': target,
        'recipeSHA256': sha(__file__),
        'inputSHA256': sha(config_path),
        'delegatedExport': {'path': str((out / 'export.json').relative_to(ROOT)),
                            'sha256': sha(out / 'export.json')},
        'noBlenderRerun': True,
        'normalPlayerAssetsChanged': False,
        'limits': ['Actual Garage playback, moving art, contacts and device acceptance remain pending.'],
    }
    (out / 'transport.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'out': str(out), 'accepted': False, 'noBlenderRerun': True}))


def main():
    if not __debug__:
        raise RuntimeError('Do not disable validation with Python -O')
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('config', type=Path)
    parser.add_argument('out', type=Path, nargs='?')
    parser.add_argument('--check-original', action='store_true', help='Check small original provenance only; write nothing')
    args = parser.parse_args()
    if args.check_original == (args.out is not None):
        parser.error('Supply either --check-original or a fresh output path')
    config_path = args.config.resolve()
    config = json.loads(config_path.read_text())
    original, receipt, rig_dir, helper_path = original_actions(config)
    if args.check_original:
        print(json.dumps({'originalProvenanceVerified': True, 'targetChecked': False,
                          'executed': False, 'accepted': False}))
        return
    transport(config_path, args.out, config, original, receipt, rig_dir, helper_path)


if __name__ == '__main__':
    main()
