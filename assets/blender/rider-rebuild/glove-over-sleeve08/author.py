"""One original gauntlet + tailored sleeve candidate, parent CPU2 lease only.

blender -b -t 2 --python-exit-code 1 --python author.py -- FRESH_OUT
No binds, remasking, reweighting, image editing, topology or UV replacement.
"""
import hashlib
import json
import runpy
import sys
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
V = runpy.run_path(str(HERE/'volume.py'))
EXPECTED = {'RiderBody', 'RiderHoodie', 'RiderJeans', 'ActualSelectedGlove.L',
            'ActualSelectedGlove.R', 'ActualSelectedBoot.L', 'ActualSelectedBoot.R'}


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1024*1024):
            h.update(block)
    return h.hexdigest()


def pin(row):
    path = ROOT/row['path']
    assert sha(path) == row['sha256'], ('Changed source', row)
    return path


def points(obj):
    local = np.empty((len(obj.data.vertices), 3), dtype=np.float32)
    obj.data.vertices.foreach_get('co', local.ravel())
    return local, V['apply'](local, np.asarray(obj.matrix_world, dtype=float))


def faces(obj):
    obj.data.calc_loop_triangles()
    result = np.empty((len(obj.data.loop_triangles), 3), dtype=np.int32)
    obj.data.loop_triangles.foreach_get('vertices', result.ravel())
    return result


def set_world(obj, world):
    inverse = np.linalg.inv(np.asarray(obj.matrix_world, dtype=float))
    local = V['apply'](world, inverse).astype(np.float32)
    obj.data.vertices.foreach_set('co', local.ravel())
    obj.data.update()
    return points(obj)[1]


def strict_cross(a, b):
    na, nb = np.cross(a[1]-a[0], a[2]-a[0]), np.cross(b[1]-b[0], b[2]-b[0])
    na /= np.linalg.norm(na)
    nb /= np.linalg.norm(nb)
    if np.linalg.norm(np.cross(na, nb)) < 1e-8 and abs(np.sum((a[0]-b[0])*nb)) < 1e-9:
        drop = int(np.argmax(np.abs(na)))
        aa, bb = np.delete(a, drop, axis=1), np.delete(b, drop, axis=1)
        for triangle in (aa, bb):
            for i in range(3):
                edge = triangle[(i+1) % 3]-triangle[i]
                axis = np.array([-edge[1], edge[0]])
                pa, pb = np.sum(aa*axis, axis=1), np.sum(bb*axis, axis=1)
                if min(pa.max(), pb.max())-max(pa.min(), pb.min()) <= 1e-14:
                    return False
        return True
    for first, second in ((a, b), (b, a)):
        normal = np.cross(second[1]-second[0], second[2]-second[0])
        denominator = np.linalg.norm(normal)
        distances = np.sum((first-second[0])*normal, axis=1)/denominator
        if np.all(distances >= 1e-10) or np.all(distances <= -1e-10):
            continue
        for i in range(3):
            edge = first[(i+1) % 3]-first[i]
            matrix = np.column_stack((edge, -(second[1]-second[0]), -(second[2]-second[0])))
            if abs(np.linalg.det(matrix)) < 1e-20:
                continue
            t, u, v = np.linalg.solve(matrix, second[0]-first[i])
            if 1e-7 < t < 1-1e-7 and u > 1e-7 and v > 1e-7 and u+v < 1-1e-7:
                return True
    return False


def intersections(a, af, b=None, bf=None, changed_vertices=None):
    self_test = b is None
    assert changed_vertices is None or self_test
    if self_test:
        b, bf = a, af
    assert np.isfinite(a).all() and np.isfinite(b).all()
    for p, f in ((a, af), (b, bf)):
        areas = np.linalg.norm(np.cross(p[f[:, 1]]-p[f[:, 0]], p[f[:, 2]]-p[f[:, 0]]), axis=1)
        assert np.all(areas > 1e-14), 'A constructed face degenerates'
    tree_a = BVHTree.FromPolygons([Vector(p) for p in a], af.tolist(), all_triangles=True)
    tree_b = tree_a if self_test else BVHTree.FromPolygons([Vector(p) for p in b], bf.tolist(), all_triangles=True)
    tested, inherited_count, construction_count = 0, 0, 0
    first_inherited, first_construction = None, None
    for i, j in tree_a.overlap(tree_b):
        if self_test and i >= j:
            continue
        tested += 1
        if strict_cross(a[af[i]], b[bf[j]]):
            witness = {'triangles': [int(i), int(j)], 'firstTriangleVertexIds': af[i].tolist(),
                       'secondTriangleVertexIds': bf[j].tolist()}
            if changed_vertices is None:
                return {'passed': False, 'firstStrictCrossingTriangles': witness['triangles'],
                        'firstTriangleVertexIds': witness['firstTriangleVertexIds'],
                        'secondTriangleVertexIds': witness['secondTriangleVertexIds'],
                        'testedBroadphasePairs': tested}
            # Inspect the whole control mesh. A moved cuff versus any retained
            # wrist/finger face fails; only unchanged/unchanged pairs are
            # reported as inherited failures rather than new construction.
            touches_construction = (np.any(changed_vertices[af[i]])
                                    or np.any(changed_vertices[bf[j]]))
            if touches_construction:
                construction_count += 1
                if first_construction is None:
                    first_construction = witness
            else:
                inherited_count += 1
                if first_inherited is None:
                    first_inherited = witness
    if changed_vertices is not None:
        return {'passed': construction_count == 0,
                'scope': 'Construction gate on every pair touching a changed vertex; inherited retained-hand failures remain open',
                'fullGuideHasNoStrictCrossings': construction_count+inherited_count == 0,
                'constructionStrictCrossings': construction_count,
                'firstConstructionStrictCrossing': first_construction,
                'inheritedUnchangedStrictCrossings': inherited_count,
                'firstInheritedUnchangedStrictCrossing': first_inherited,
                'allBroadphasePairsInspected': True, 'testedBroadphasePairs': tested}
    return {'passed': True, 'testedBroadphasePairs': tested, 'strictCrossings': 0}


def main():
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 1
    out = Path(args[0]).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/glove-over-sleeve08') and not out.exists()
    control = json.loads((HERE/'input.json').read_text())
    for value in control.values():
        if isinstance(value, dict) and 'path' in value and 'sha256' in value:
            pin(value)
    for row in control['guideArrays'].values():
        pin(row)
    placement = json.loads(pin(control['placement']).read_text())
    source_frames = json.loads(pin(control['hoodieSourceFrames']).read_text())
    original_glove = np.load(pin(control['originalGloveDense']))
    original_guide = np.load(pin(control['originalGloveGuide']))
    original_hoodie = V['read_hoodie'](pin(control['originalHoodie']))
    fixed = runpy.run_path(str(pin(control['fixedHelper'])))['fixed']
    geometry = runpy.run_path(str(pin(control['geometryHelper'])))['geometry']
    rest = runpy.run_path(str(pin(control['restHelper'])))['rest']
    bpy.ops.wm.open_mainfile(filepath=str(pin(control['master'])))
    rig = bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    assert {o.name for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render} == EXPECTED
    unchanged = [bpy.data.objects[n] for n in EXPECTED-{
        'RiderHoodie', 'ActualSelectedGlove.L', 'ActualSelectedGlove.R'}]
    unchanged.append(bpy.data.objects['RiderBody__FullAnatomyReference'])
    protected = {o.name: geometry(o) for o in unchanged}
    rest_before = rest(rig)
    edited = [bpy.data.objects[n] for n in ('RiderHoodie', 'ActualSelectedGlove.L', 'ActualSelectedGlove.R')]
    fixed_before = {o.name: fixed(o) for o in edited}
    body = bpy.data.objects['RiderBody__FullAnatomyReference']
    _, body_world = points(body)
    body_faces = faces(body)
    hoodie = bpy.data.objects['RiderHoodie']
    _, hoodie_world = points(hoodie)
    assert len(hoodie_world) == len(original_hoodie)
    hoodie_faces = faces(hoodie)
    settings = control['authoring']
    out.mkdir(parents=True)
    report = {'acceptedArt': False, 'operation': control['operation'], 'master': control['master'],
              'sourceMaster': control['master'], 'visibleMeshes': sorted(EXPECTED),
              'recipeSHA256': sha(__file__), 'volumeRecipeSHA256': sha(HERE/'volume.py'),
              'inputSHA256': sha(HERE/'input.json'), 'newBindings': 0, 'newCorrespondences': 0,
              'newWeightComputations': 0, 'bakes': 0, 'hands': {}, 'limits': control['limits']}
    guides, pending = [], {}
    for side in ('L', 'R'):
        dump = np.load(pin(control['guideArrays'][side]))
        scale, basis_x, basis_z = V['cuff_frame'](dump, placement['hands'][side])
        profile = V['BodyProfile'](body_world, body_faces, dump['wristWorld'],
            dump['forearmAxisWorld'], basis_x, basis_z, settings)
        # The open source full-annulus section at Y=-.65 seats the sleeve;
        # the proximal oblique selected gauntlet lip stays source authored.
        endpoint = (placement['sourceRest']['wrist'][1]-settings['gloveFullSourceY'])*scale
        hoodie_after, hood_ids, cloth = V['construct_sleeve'](
            original_hoodie, hoodie_world, source_frames, side, profile, settings, endpoint)
        assert np.array_equal(hoodie_after[np.setdiff1d(np.arange(len(hoodie_world)), hood_ids)],
                              hoodie_world[np.setdiff1d(np.arange(len(hoodie_world)), hood_ids)])
        hoodie_world = hoodie_after
        transverse = V['seat_cuff'](original_guide['vertices'], original_guide['faces'],
            dump, placement['sourceRest']['wrist'], scale, basis_x, basis_z,
            profile, cloth['maximumActualClothReserveM'], settings)
        if max(transverse['scale']) > settings['maximumTransverseSourceScale']:
            report.update(status='REJECTED_EXCESSIVE_CUFF_VOLUME_SCALE', rejectedSide=side,
                          requiredTransverseFrame=transverse)
            (out/'construction.json').write_text(json.dumps(report, indent=2)+'\n')
            raise AssertionError('Required opening scale exceeds declared source-identity bound; no giant cuff produced')
        candidate, alpha = V['construct_cuff'](original_guide['vertices'], dump['currentWorldXYZ'],
            dump, placement['sourceRest']['wrist'], scale, basis_x, basis_z, transverse, settings)
        old = bpy.data.objects[control['sourceObjects']['guides'][side]]
        guide = old.copy()
        guide.data = old.data.copy()
        bpy.context.scene.collection.objects.link(guide)
        guide.name = 'Gloves__OriginalGauntletOverSleeve08Guide.'+side
        candidate = set_world(guide, candidate)
        guide.hide_render = True
        guide.hide_set(True)
        guide['sourceAuthority'] = control['originalGloveGuide']['sha256']
        guide['construction'] = 'Original entire gauntlet volume plus anatomical wrist join; unaccepted'
        guides.append(guide)
        # Full control mesh includes cuff versus retained wrist/finger pairs.
        gf = faces(guide)
        arrays = out/f'actual-guide-{side}.npz'
        np.savez_compressed(arrays, worldXYZ=candidate, faces=gf, alpha=alpha)
        gate = intersections(candidate, gf, changed_vertices=alpha > 0)
        report['hands'][side] = {'hoodie': cloth, 'transverseSourceVolumeAffine': transverse,
            'sourceCuffScaleMPerSourceUnit': scale, 'guideSelfIntersection': gate,
            'actualGuideArrays': {'path': str(arrays.relative_to(ROOT)), 'sha256': sha(arrays)},
            'guideChangedVertices': int(np.sum(alpha > 0)), 'originalCuffWallsBandLipTopologyRetained': True}
        pending[side] = (dump, profile, scale, basis_x, basis_z, transverse, hood_ids)
    # Preserve a genuinely editable source even if a control geometry gate
    # fails. A failed gate stops before dense transport, never becomes a pass.
    checkpoint = out/'editable-original-gauntlet-guides.blend'
    bpy.data.libraries.write(str(checkpoint), set(guides), fake_user=True, compress=True)
    report['guideNative'] = {'path': str(checkpoint.relative_to(ROOT)), 'sha256': sha(checkpoint)}
    (out/'construction.json').write_text(json.dumps(report, indent=2)+'\n')
    assert all(r['guideSelfIntersection']['passed'] for r in report['hands'].values()), 'Control cuff self-crossing; stop before dense transport'
    hoodie_actual = set_world(hoodie, hoodie_world)
    for side in ('L', 'R'):
        dump, profile, scale, basis_x, basis_z, transverse, hood_ids = pending[side]
        glove = bpy.data.objects['ActualSelectedGlove.'+side]
        _, before = points(glove)
        assert len(before) == len(original_glove['vertices'])
        after, alpha = V['construct_cuff'](original_glove['vertices'], before, dump,
            placement['sourceRest']['wrist'], scale, basis_x, basis_z, transverse, settings)
        actual = set_world(glove, after)
        full = bpy.data.objects[control['sourceObjects']['fullFields'][side]]
        reference = full.copy()
        reference.data = full.data.copy()
        bpy.context.scene.collection.objects.link(reference)
        reference.name = 'Gloves__OverSleeve08FullFieldReference.'+side
        set_world(reference, actual)
        reference.hide_render = True
        reference.hide_set(True)
        gf = faces(glove)
        # Include retained proximal neighbours beyond the changed join. This
        # local dense check does not qualify distant unchanged finger pairs.
        gf = gf[np.any(original_glove['vertices'][gf, 1]
                       < settings['gloveAnatomicalJoinY']+.03, axis=1)]
        hf = hoodie_faces[np.any(np.isin(hoodie_faces, hood_ids), axis=1)]
        axial = np.sum((body_world-profile.wrist)*profile.axis, axis=1)
        bf = body_faces[np.any((axial[body_faces] >= 0) & (axial[body_faces] <= .1), axis=1)]
        cuff_axial = np.sum((actual-profile.wrist)*profile.axis, axis=1)
        proximal_faces = gf[np.all(cuff_axial[gf] >= 0, axis=1)]
        report['hands'][side].update(denseSelfIntersection=intersections(actual, gf),
            sleeveSelfIntersection=intersections(hoodie_actual, hf),
            gloveSleeveIntersection=intersections(actual, gf, hoodie_actual, hf),
            cuffWearerIntersection=intersections(actual, proximal_faces, body_world, bf),
            sleeveWearerIntersection=intersections(hoodie_actual, hf, body_world, bf),
            denseChangedVertices=int(np.sum(alpha > 0)))
    assert protected == {o.name: geometry(o) for o in unchanged}
    assert rest(rig) == rest_before
    assert fixed_before == {o.name: fixed(o) for o in edited}
    assert {o.name for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render} == EXPECTED
    report.update(exact75RestUnchanged=True, protectedGeometry=protected,
                  editedTopologyUVPBRAndAllSkinFieldsUnchanged=fixed_before)
    gates = [r[k]['passed'] for r in report['hands'].values() for k in (
        'denseSelfIntersection', 'sleeveSelfIntersection', 'gloveSleeveIntersection',
        'cuffWearerIntersection', 'sleeveWearerIntersection')]
    report['geometryGatesPassed'] = all(gates)
    report['status'] = 'UNACCEPTED_COMBINED_MODEL_MOVING_REVIEW_PENDING' if all(gates) else 'REJECTED_COMBINED_MODEL_REQUIRES_GEOMETRY_CORRECTION'
    native = out/'editable-selected-gauntlet-over-sleeve.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
    report['native'] = {'path': str(native.relative_to(ROOT)), 'sha256': sha(native)}
    (out/'construction.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'native': report['native'], 'status': report['status'], 'hands': report['hands']}), flush=True)
    assert all(gates), 'Saved explicitly rejected geometry; do not export or promote'


if __name__ == '__main__':
    main()
