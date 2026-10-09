"""One guarded actual41 side/level: anatomical source fans, then index-only37/59.

Python with NumPy: construct.py CPU_CHECK_JSON L|R full|lod FRESH_OUT
No Blender, source movement, surface replacement, field normalization or retry.
"""
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
sys.path.insert(0, str(HERE))
from extract import BASE, RECEIPT, checked, pin


def unit(vector):
    vector = np.asarray(vector, np.float64)
    length = np.linalg.norm(vector)
    assert length > 0
    return vector/length


def landmarks(points, fields, names, used, rest, side):
    bones = {row[0]: row for row in rest}
    bone = lambda stem: bones[stem+'.'+side]
    weight = lambda stems: fields[:, [names.index(stem+'.'+side) for stem in stems]].sum(axis=1)
    selected, records = [], []

    def save(label, ids, center, policy):
        ids = np.asarray(ids, np.uint32)
        assert len(ids) and used[ids].all(), label
        selected.extend(ids.tolist())
        records.append({'landmark': label, 'centerM': np.asarray(center).tolist(),
                        'originalVertexIds': ids.tolist(), 'sourcePositionsM': points[ids].tolist(), 'policy': policy})

    def ring(label, center, axis, preferred, mask, band):
        axis = unit(axis); x = unit(preferred-np.dot(preferred, axis)*axis); z = np.cross(axis, x)
        relative = points.astype(np.float64)-center
        axial, rx, rz = relative@axis, relative@x, relative@z
        radius2 = rx*rx+rz*rz
        eligible = used & mask & (np.abs(axial) <= band) & (radius2 > 0)
        sectors = np.floor((np.arctan2(rz, rx)+np.pi)*(8/(2*np.pi))).astype(np.int32) % 8
        ids = []
        for sector in range(8):
            group = np.flatnonzero(eligible & (sectors == sector))
            assert len(group), ('Missing actual source sector; no weaker fallback', label, sector)
            # Existing vertices nearest the real anatomical cross-section center;
            # sectors prevent all locks landing on one side of a joint or cuff.
            score = axial[group]**2+radius2[group]
            ids.append(int(group[np.argmin(score)]))
        save(label, ids, center, 'Eight real source sectors; complete incident fans; no invented target points.')

    for digit in ('thumb', 'f_index', 'f_middle', 'f_ring', 'f_pinky'):
        stems = [f'DEF-{digit}.{index:02}' for index in (1, 2, 3)]
        support = weight(stems) >= .2
        for index, stem in enumerate(stems, 1):
            b = bone(stem); head, tail = np.asarray(b[2]), np.asarray(b[3]); axis = tail-head
            preferred = np.asarray(b[4])[:3, 0]
            ring(f'{digit}-joint{index}', head, axis, preferred, support, np.linalg.norm(axis)*.35)
        tip = bone(stems[-1]); head, tail = np.asarray(tip[2]), np.asarray(tip[3]); axis = unit(tail-head)
        distal = used & (weight([stems[-1]]) >= .2)
        candidates = np.flatnonzero(distal); assert len(candidates)
        apex = candidates[np.argmax((points[candidates]-tail)@axis)]
        save(digit+'-tip-apex', [apex], tail, 'Distal semantic field longitudinal extreme from this side only.')
        ring(digit+'-tip-rim', tail, axis, np.asarray(tip[4])[:3, 0], distal,
             max(.002, np.linalg.norm(tail-head)*.6))

    hand = bone('DEF-hand'); wrist, palm_end = np.asarray(hand[2]), np.asarray(hand[3])
    across = unit(np.asarray(bone('DEF-f_pinky.01')[2])-bone('DEF-f_index.01')[2])
    palm_normal = unit(np.cross(unit(palm_end-wrist), across))
    web_pairs = [('thumb', 'f_index'), ('f_index', 'f_middle'), ('f_middle', 'f_ring'), ('f_ring', 'f_pinky')]
    for first, second in web_pairs:
        a, b = bone('DEF-'+first+'.01'), bone('DEF-'+second+'.01')
        center = (np.asarray(a[3] if first == 'thumb' else a[2])+b[2])/2
        mask = used & (weight(['DEF-'+first+'.01', 'DEF-'+second+'.01']) >= .2)
        relative = points-center; dorsal, transverse = relative@palm_normal, relative@across
        ids = []
        for sign_d in (-1, 1):
            for sign_t in (-1, 1):
                group = np.flatnonzero(mask & (dorsal*sign_d >= 0) & (transverse*sign_t >= 0))
                assert len(group), ('Missing real web quadrant', first, second, sign_d, sign_t)
                ids.append(int(group[np.argmin(np.einsum('ij,ij->i', relative[group], relative[group]))]))
        save(first+'-'+second+'-web', ids, center, 'Both actual adjacent digit fields, dorsal/palmar and both transverse halves.')

    forearm = bones['DEF-forearm.'+side+'.001']; axis = unit(np.asarray(forearm[3])-forearm[2])
    cuff_names = ['DEF-hand.'+side, 'DEF-forearm.'+side, 'DEF-forearm.'+side+'.001']
    cuff_mask = used & (fields[:, [names.index(name) for name in cuff_names]].sum(axis=1) >= .2)
    assert cuff_mask.any()
    preferred = np.asarray(forearm[4])[:3, 0]
    band = max(.003, np.linalg.norm(np.asarray(forearm[3])-forearm[2])*.1)
    ring('wrist-cuff-junction', wrist, axis, preferred, cuff_mask, band)
    proximal = float(((points[cuff_mask]-wrist)@axis).min())
    ring('proximal-cuff-lip', wrist+proximal*axis, axis, preferred, cuff_mask, band)
    return np.unique(np.asarray(selected, np.uint32)), records


def main(cpu_file, side, level, output):
    assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID'), 'Original parent guard required'
    assert side in ('L', 'R') and level in ('full', 'lod')
    output = Path(output).resolve(); assert output.is_relative_to(BASE) and output != BASE and not output.exists()
    cpu_file = Path(cpu_file).resolve(); cpu = json.loads(cpu_file.read_text())
    assert cpu['status'] == 'INDEPENDENT_CPU_ACTUAL41_CACHE_IDENTITY_PASSED_UNACCEPTED' and not cpu['acceptedArt']
    assert checked(cpu['checker']) == HERE/'check.py'
    report = json.loads(checked(cpu['extraction']).read_text()); assert report['sourceReceipt'] == RECEIPT
    receipt = json.loads(checked(RECEIPT).read_text()); assert report['native'] == receipt['native']
    assert checked(report['recipe']) == HERE/'extract.py'
    assert report['sourceWitnessUnchanged'] and report['dependencyWitnessUnchanged']
    name = 'ActualSelectedGlove.'+side; row = report['objects'][name]
    witness = report['sourceWitness']['sources'][name]
    assert witness['matrixWorld'] == np.eye(4).tolist() and len(row['groupNames']) == 75
    assert report['sourceWitness']['rig']['matrixWorld'] == np.eye(4).tolist(), 'Rest landmarks require the exact identity source frame'
    output.mkdir(parents=True)
    with np.load(checked(row['arrays']), allow_pickle=False) as source:
        arrays = {key: source[key] for key in ('positions', 'triangles', 'triangleLoopIds', 'vertexNormals',
                  'cornerNormals', 'faceMaterialIds', 'fieldIndices', 'fieldWeights')}
        arrays.update({f'uvLayer{i}': source[f'uvLayer{i}'] for i in range(len(row['uvLayerNames']))})
        offsets = source['fieldOffsets']; assert offsets.max() < 2**32
        arrays['fieldOffsets'] = offsets.astype(np.uint32)
        count = len(arrays['positions']); names = row['groupNames']; fields = np.zeros((count, len(names)), np.float32)
        vertex_ids = np.repeat(np.arange(count), np.diff(offsets))
        fields[vertex_ids, arrays['fieldIndices']] = arrays['fieldWeights']; arrays['namedWeights'] = fields
        used = np.zeros(count, bool); used[arrays['triangles'].ravel()] = True
        centers, semantic = landmarks(arrays['positions'], fields, names, used, report['rest'], side)
        arrays['centerOriginalVertexIds'] = centers
        layout = {}; binary = output/'source.bin'
        with binary.open('xb') as stream:
            for key, values in arrays.items():
                layout[key] = {'dtype': values.dtype.str, 'shape': list(values.shape), 'byteOffset': stream.tell(),
                               'byteLength': values.nbytes, 'sha256': hashlib.sha256(values.tobytes()).hexdigest()}
                stream.write(values.tobytes())
    prepared = {'status': 'ACTUAL41_ANATOMICAL_FANS_PREPARED_UNACCEPTED', 'acceptedArt': False, 'side': side, 'level': level,
        'recipe': pin(__file__), 'cpuAdmission': pin(cpu_file), 'extraction': cpu['extraction'], 'sourceReceipt': RECEIPT,
        'native': report['native'], 'sourceObject': name, 'sourceGeometry': row['geometry'], 'sourceArrays': row['arrays'],
        'groupNames': names, 'uvLayerNames': row['uvLayerNames'], 'materialWitness': report['sourceWitness']['materials'],
        'sourceWitness': witness, 'rest': report['rest'], 'arrays': dict(pin(binary), layout=layout),
        'semanticSourceFans': semantic, 'unreferencedSourceVertices': int((~used).sum()),
        'policy': {'targetTriangles': 8000 if level == 'full' else 3500, 'maximumSurfaceErrorM': .0005,
                   'cageM': .001, 'minimumNormalDot': .25, 'maximumSkinWeightL1': .3, 'maximumAttempts': 1}}
    manifest = output/'prepared.json'; manifest.write_text(json.dumps(prepared, indent=2)+'\n')
    result = subprocess.run(['node', str(HERE/'construct.mjs'), str(manifest)], cwd=ROOT)
    raise SystemExit(result.returncode)


if __name__ == '__main__':
    assert len(sys.argv) == 5
    main(*sys.argv[1:])
