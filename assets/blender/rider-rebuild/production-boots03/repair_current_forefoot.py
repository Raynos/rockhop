"""One local upper-flank repair of the exact saved selected dense sculpt02.

Parent CPU2 lease required; source-only until that lease. No lattice, global
scale, vertical lift, reflection blend, solver, projection, bake or decimation.
blender -b -t 2 --python-exit-code 1 --python THIS -- FRESH_OUTPUT
"""
import hashlib
import importlib.util
import json
from pathlib import Path
import sys

import bpy
import numpy as np

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[3]
CONTROLS = HERE/'repair-controls.json'
CONFIG = json.loads(CONTROLS.read_text())
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()


def load_helpers():
    spec = CONFIG['inputs']['frozenAuthorHelpers']
    path = ROOT/spec['path']
    assert sha(path) == spec['sha256']
    module_spec = importlib.util.spec_from_file_location('selected_boot_sculpt02_helpers', path)
    module = importlib.util.module_from_spec(module_spec)
    module_spec.loader.exec_module(module)
    # Reuse the exact selected materials, UV/winding, affine/native75 binding and
    # render operations. Original forefoot authoring function is never called.
    module.CONFIG = CONFIG
    return module


def grab_upper(current, original, side, smooth):
    spec = CONFIG['sides'][side]
    signed_scale = np.array(spec['scales'])*[1., 1., spec['mirrorWidth']]
    local = current*signed_scale + np.array(spec['offset'])
    guards = CONFIG['selection']
    upper = smooth((local[:, 1]-guards['heldSoleWeltBelowHeightM']) /
                   (guards['fullUpperAboveHeightM']-guards['heldSoleWeltBelowHeightM']))
    forefoot = smooth((guards['heldRearAfterLongitudinalM']-local[:, 0]) /
                      (guards['heldRearAfterLongitudinalM']-guards['fullForefootBeforeLongitudinalM']))
    selection = upper*forefoot
    delta = np.zeros(len(local), dtype=np.float64)
    brush_receipts = []
    for brush in CONFIG['grabs'][side]:
        relative = (local-np.array(brush['centerLongHeightTransverseM']))/np.array(brush['radiusM'])
        falloff = np.exp(-np.sum(relative*relative, axis=1))*selection
        displacement = brush['transverseDeltaM']*falloff
        delta += displacement
        brush_receipts.append({'name': brush['name'], 'requestedPeakTransverseM': brush['transverseDeltaM'],
                               'actualMaximumAbsoluteTransverseM': float(np.max(abs(displacement)))})
    edited = current.copy()
    edited[:, 2] += delta/signed_scale[2]
    # Sole/welt datum and complete selected rear remain byte-identical vertices.
    held = ((local[:, 1] <= guards['heldSoleWeltBelowHeightM']) |
            (local[:, 0] >= guards['heldRearAfterLongitudinalM']))
    assert np.array_equal(edited[held], current[held])
    assert np.array_equal(edited[:, :2], current[:, :2]), 'No longitudinal or vertical edit'
    retained_rear = original[:, 0] >= -.16
    assert np.array_equal(edited[retained_rear], current[retained_rear])
    return edited, {'originalDenseVertices': len(current), 'heldVertices': int(held.sum()),
                    'retainedRearVertices': int(retained_rear.sum()), 'heldMaximumSourceDelta': 0.,
                    'maximumTransverseDeltaM': float(np.max(abs(delta))), 'brushes': brush_receipts}


def main():
    arguments = sys.argv[sys.argv.index('--')+1:]
    assert len(arguments) == 1
    out = Path(arguments[0]).resolve()
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/production-boots03')
    helpers = load_helpers()
    paths = {k: helpers.pinned(k) for k in CONFIG['inputs']}
    dense = dict(np.load(paths['dense']))
    body_arrays = dict(np.load(paths['bodyArrays']))
    currents = {s: dict(np.load(paths['currentSculpt'+s])) for s in ['R', 'L']}
    for current in currents.values():
        assert np.array_equal(current['originalDenseVertexRows'], np.arange(len(dense['vertices'])))
        assert np.array_equal(current['originalDenseTriangleRows'], np.arange(len(dense['faces'])))
    out.mkdir(parents=True)
    report = {'accepted': False, 'status': 'CURRENT_SELECTED_DENSE_LOCAL_UPPER_REPAIR_IN_PROGRESS',
              'recipeSHA256': sha(__file__), 'controlsSHA256': sha(CONTROLS),
              'inputs': CONFIG['inputs'], 'sides': {}, 'noVerticalLift': True}
    save_report = lambda: (out/'report.json').write_text(json.dumps(report, indent=2)+'\n')
    save_report()
    bpy.ops.wm.open_mainfile(filepath=str(paths['wearer']))
    body, rig = bpy.data.objects['RiderBody'], bpy.data.objects['RiderSkeleton']
    before = helpers.wearer_snapshot(body, rig)
    assert len(rig.data.bones) == 75 and len(body.data.vertices) == 10582
    assert not body.hide_render and not body.hide_viewport
    mat = helpers.material()
    targets, originals, frames = {}, {}, {}
    for side in ['R', 'L']:
        edited, receipt = grab_upper(currents[side]['editedOriginalDenseVertices'], dense['vertices'], side, helpers.smooth)
        target, vertices, frame, ankle, reverse = helpers.mesh_object('LocallyRepairedSelectedDenseBoot.'+side,
                                                                     edited, dense, body_arrays, side, mat)
        helpers.weight_boot(target, vertices, frame, ankle, side, rig)
        receipt.update({'faces': len(dense['faces']), 'reflectedFaceAndUVCornerOrderTogether': bool(reverse),
                        'nativeBounds': [vertices.min(0).tolist(), vertices.max(0).tolist()]})
        report['sides'][side] = receipt
        np.savez_compressed(out/('locally-repaired-source-'+side+'.npz'),
                            editedOriginalDenseVertices=edited,
                            originalDenseVertexRows=np.arange(len(edited)),
                            originalDenseTriangleRows=np.arange(len(dense['faces'])))
        targets[side], frames[side] = target, (frame, ankle)
        original, _, _, _, _ = helpers.mesh_object('UnchangedOriginalSelectedBoot.'+side,
                                                   dense['vertices'], dense, body_arrays, side, mat)
        original.hide_render = True
        original.hide_set(True)
        originals[side] = original
        save_report()
    assert helpers.wearer_snapshot(body, rig) == before
    report.update(status='UNACCEPTED_CURRENT_SOURCE_LOCAL_REPAIR_REST_REVIEW_PENDING',
                  bodyAndRest75Unchanged=True, denseTopologyPreserved=True,
                  uvPolicy='Raw corner UV unchanged; copied Blender V flip; reflected L face/UV corners reverse together',
                  selectedMaterials='Unchanged byte-exact original 4K albedo + metallicRoughness')
    save_report()
    native = out/'local-upper-repair-selected-source.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native))
    for side in ['R', 'L']:
        view_dir = out/side
        view_dir.mkdir()
        helpers.render_comparison(bpy.context.scene, view_dir, originals[side], [targets[side]],
                                  body, *frames[side])
        if side == 'R':
            # Give each side the same two-light setup; no doubled second-side
            # lighting or tiny partner boot is substituted for a separate view.
            for obj in list(bpy.data.objects):
                if obj.name.startswith(('Sculpt comparison light ', 'Unchanged full-foot selected source comparison')):
                    bpy.data.objects.remove(obj, do_unlink=True)
    for target in targets.values():
        target.hide_render = False
        target.hide_set(False)
    for original in originals.values():
        original.hide_render = True
        original.hide_set(True)
    assert helpers.wearer_snapshot(body, rig) == before
    bpy.ops.wm.save_as_mainfile(filepath=str(native))
    assert all(sha(paths[k]) == CONFIG['inputs'][k]['sha256'] for k in paths)
    report['native'] = {'path': str(native.relative_to(ROOT)), 'sha256': sha(native)}
    report['views'] = [str(p.relative_to(out)) for p in sorted(out.glob('*/*.png'))]
    save_report()
    print(json.dumps({'status': report['status'], 'native': report['native'], 'views': report['views']}))


if __name__ == '__main__':
    main()
