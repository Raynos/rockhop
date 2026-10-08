"""One check-only integration, under the parent's CPU2 guard; no renders.

Use controls.json's command. Saves an editable derivative, never canonical
native02 or player assets. The genuine face construction is reused unchanged.
"""
import hashlib
import json
from pathlib import Path
import runpy
import sys

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CONFIG = json.loads((HERE / 'controls.json').read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def pinned(name):
    row = CONFIG['inputs'][name]
    path = ROOT / row['path']
    assert sha(path) == row['sha256'], ('Changed source', name)
    return path


def rest(rig):
    return [{'name': b.name, 'parent': b.parent.name if b.parent else None,
             'head': list(b.head_local), 'tail': list(b.tail_local),
             'matrix': [list(row) for row in b.matrix_local],
             'useConnect': b.use_connect, 'useDeform': b.use_deform}
            for b in rig.data.bones]


def lower_rows(body, protected_ids):
    ids = body.data.attributes['_SOURCE_VERTEX_ID'].data
    groups = {g.index: g.name for g in body.vertex_groups}
    result = {}
    for v in body.data.vertices:
        identity = ids[v.index].value
        if identity not in protected_ids:
            continue
        assert identity not in result
        result[identity] = (tuple(v.co), sorted((groups[g.group], g.weight) for g in v.groups))
    assert set(result) == protected_ids, 'Lost an original protected body row'
    return result


def main():
    args = sys.argv[sys.argv.index('--') + 1:]
    assert len(args) == 1
    out = Path(args[0]).resolve()
    assert out == ROOT / CONFIG['execution']['out'] and not out.exists()
    inputs = {name: pinned(name) for name in CONFIG['inputs']}
    out.mkdir(parents=True)
    receipt = {'accepted': False, 'status': 'CHECK_ONLY_NO_RENDER',
               'inputs': CONFIG['inputs'],
               'recipes': [{'path': str(p.relative_to(ROOT)), 'sha256': sha(p)}
                           for p in (Path(__file__), HERE / 'controls.json', HERE / 'verify_selected_face.py')]}
    (out / 'input-receipt.json').write_text(json.dumps(receipt, indent=2) + '\n')
    bpy.ops.wm.open_mainfile(filepath=str(inputs['native']))
    body, rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    assert set(bpy.data.objects.keys()) == {'RiderBody', 'RiderSkeleton'}
    assert len(body.data.vertices) == 10582 and len(rig.data.bones) == 75
    assert body.matrix_world.is_identity and rig.matrix_world.is_identity
    assert not rig.constraints and all(not b.constraints for b in rig.pose.bones)
    assert rig.animation_data is None
    assert all(b.matrix_basis.is_identity for b in rig.pose.bones)
    arrays = dict(np.load(inputs['arrays']))
    protected_ids = set(map(int, arrays['nativeSourceVertexIds'][arrays['vertices'][:, 2] < CONFIG['construction']['bodyCutNativeZ']]))
    assert len(protected_ids) == 6933 and min(protected_ids) >= 0 and max(protected_ids) < 10582
    before_rest, before_rows = rest(rig), lower_rows(body, protected_ids)
    assert np.array_equal(arrays['vertices'], np.array([list(v.co) for v in body.data.vertices], dtype=np.float32))
    result = runpy.run_path(str(inputs['builder']))['buildFace'](body, rig, out)
    candidate = out / 'selected-face-native75.blend'
    # The actual editable candidate is saved before any later review process.
    bpy.ops.wm.save_as_mainfile(filepath=str(candidate))
    assert rest(rig) == before_rest, 'Actual master75 rest changed'
    assert lower_rows(body, protected_ids) == before_rows, 'Actual below-cut body/source-ID/field row changed'
    assert result['report']['protectedSourceTriangles'] == 66364
    for name in CONFIG['inputs']:
        pinned(name)
    report = {'accepted': False, 'status': 'SAVED_NATIVE_DERIVATIVE_INDEPENDENT_CHECK_PENDING',
              'candidate': {'path': str(candidate.relative_to(ROOT)), 'sha256': sha(candidate)},
              'originalNativeUnchangedSHA256': CONFIG['inputs']['native']['sha256'],
              'all75RestRecordsExactlyRetainedInMemory': True,
              'belowCutRowsExactlyRetainedInMemory': len(before_rows),
              'selectedFace': result['report'], 'contract': CONFIG['contract']}
    (out / 'report.json').write_text(json.dumps(report, indent=2) + '\n')
    print(json.dumps({'status': report['status'], 'candidate': report['candidate']}))


if __name__ == '__main__':
    main()
