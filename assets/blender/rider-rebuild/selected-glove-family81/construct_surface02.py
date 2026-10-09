"""One RIGHT candidate from reviewed actual-plane/rim source fans; no retries.

construct_surface02.py CPU_CHECK_JSON R full|lod FRESH_OUT
The independent LEFT singular-normal recipe is not invoked by this entry point.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

from extract import ROOT, BASE, RECEIPT, checked, pin

HERE = Path(__file__).resolve().parent
SURFACE_PROOF = {'path': 'docs/evidence/rider-rebuild/selected-glove-family81/surface-landmarks02.json',
                 'sha256': '8d82e318265c4798fad634902f8f67af3c4818c276595fb2420094647caef0f1'}


def main(cpu_file, side, level, output):
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID'), 'Original parent guard required'
    assert side == 'R' and level in ('full', 'lod')
    output = Path(output).resolve(); assert output.is_relative_to(BASE) and output != BASE and not output.exists()
    cpu_file = Path(cpu_file).resolve(); cpu = json.loads(cpu_file.read_text())
    assert cpu['status'] == 'INDEPENDENT_CPU_ACTUAL41_CACHE_IDENTITY_PASSED_UNACCEPTED' and not cpu['acceptedArt']
    assert checked(cpu['checker']) == HERE/'check.py'
    e = json.loads(checked(cpu['extraction']).read_text()); assert e['sourceReceipt'] == RECEIPT
    qualified = json.loads(checked(RECEIPT).read_text()); assert e['native'] == qualified['native']
    assert checked(e['recipe']) == HERE/'extract.py' and e['sourceWitnessUnchanged'] and e['dependencyWitnessUnchanged']
    proof = json.loads(checked(SURFACE_PROOF).read_text())
    assert proof['status'] == 'ACTUAL41_BILATERAL_SURFACE_LANDMARK_SOURCE_CHECK_PASSED_UNACCEPTED'
    assert proof['acceptedArt'] is False and proof['candidateAttempts'] == 0 and proof['extraction'] == cpu['extraction']
    for key in ('recipe', 'selector', 'frozenPriorSelector'): checked(proof[key])
    name = 'ActualSelectedGlove.R'; row = e['objects'][name]; selected = proof['sides'][side]
    assert selected['sourceArrays'] == row['arrays'] and selected['sourceAncestry'] == row['ancestry']
    witness = e['sourceWitness']['sources'][name]
    assert witness['matrixWorld'] == np.eye(4).tolist() and e['sourceWitness']['rig']['matrixWorld'] == np.eye(4).tolist()
    output.mkdir(parents=True)
    with np.load(checked(row['arrays']), allow_pickle=False) as source:
        arrays = {key: source[key] for key in ('positions', 'triangles', 'triangleLoopIds', 'vertexNormals',
                  'cornerNormals', 'faceMaterialIds', 'fieldIndices', 'fieldWeights')}
        arrays.update({f'uvLayer{i}': source[f'uvLayer{i}'] for i in range(len(row['uvLayerNames']))})
        offsets = source['fieldOffsets']; assert offsets.max() < 2**32
        arrays['fieldOffsets'] = offsets.astype(np.uint32); names = row['groupNames']; assert len(names) == 75
        fields = np.zeros((len(arrays['positions']), len(names)), np.float32)
        fields[np.repeat(np.arange(len(fields)), np.diff(offsets)), arrays['fieldIndices']] = arrays['fieldWeights']
        arrays['namedWeights'] = fields
        arrays['centerOriginalVertexIds'] = np.asarray(selected['centerOriginalVertexIds'], np.uint32)
        fan_faces = np.isin(arrays['triangles'], arrays['centerOriginalVertexIds']).any(axis=1)
        assert int(fan_faces.sum()) == selected['requiredSourceFanFaces']
        layout = {}; binary = output/'source.bin'
        with binary.open('xb') as stream:
            for key, values in arrays.items():
                layout[key] = {'dtype': values.dtype.str, 'shape': list(values.shape), 'byteOffset': stream.tell(),
                               'byteLength': values.nbytes, 'sha256': hashlib.sha256(values.tobytes()).hexdigest()}
                stream.write(values.tobytes())
    prepared = {'status': 'ACTUAL41_SURFACE_LANDMARKS_PREPARED_UNACCEPTED', 'acceptedArt': False, 'side': side, 'level': level,
        'recipe': pin(__file__), 'sourceSurfaceLandmarks': SURFACE_PROOF, 'sourceSelectorRecipe': proof['selector'],
        'cpuAdmission': pin(cpu_file), 'extraction': cpu['extraction'], 'sourceReceipt': RECEIPT, 'native': e['native'],
        'sourceObject': name, 'sourceGeometry': row['geometry'], 'sourceArrays': row['arrays'],
        'groupNames': names, 'uvLayerNames': row['uvLayerNames'], 'materialWitness': e['sourceWitness']['materials'],
        'sourceWitness': witness, 'rest': e['rest'], 'arrays': dict(pin(binary), layout=layout),
        'semanticSourceFans': selected['landmarks'], 'requiredSemanticSourceFanFaces': selected['requiredSourceFanFaces'],
        'policy': {'targetTriangles': 8000 if level == 'full' else 3500, 'maximumSurfaceErrorM': .0005,
                   'cageM': .001, 'minimumNormalDot': .25, 'maximumSkinWeightL1': .3, 'maximumAttempts': 1}}
    manifest = output/'prepared.json'; manifest.write_text(json.dumps(prepared, indent=2)+'\n')
    raise SystemExit(subprocess.run(['node', str(HERE/'construct_surface02.mjs'), str(manifest)], cwd=ROOT).returncode)


if __name__ == '__main__':
    assert len(sys.argv) == 5
    main(*sys.argv[1:])
