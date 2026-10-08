"""Parent serial CPU2 constructor: complete source cloth field, rebuilt lining.

This consumes the actual glove-only checkpoint and actual full-reference Basis
witness. It preserves selected outward UV/PBR/source fields and records new
lining ancestry. Saved candidates are explicitly unaccepted; no export occurs.
"""
import hashlib
import importlib.util
import json
import runpy
import sys
import time
from collections import defaultdict, deque
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while chunk := stream.read(1048576): h.update(chunk)
    return h.hexdigest()


def pin(row):
    path = ROOT/row['path']; assert sha(path) == row['sha256'], row
    return path


def load(path, name):
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec); spec.loader.exec_module(module)
    return module


def actual_nearest(points, triangles):
    origin = (points.min(0)+points.max(0))*.5
    tree = BVHTree.FromPolygons([Vector(p) for p in points-origin], triangles.tolist(), all_triangles=True)
    def nearest(query):
        unique, inverse = np.unique(query, axis=0, return_inverse=True)
        gap = np.empty(len(unique)); normal = np.empty_like(unique)
        for i, point in enumerate(unique):
            q, n, triangle, distance = tree.find_nearest(Vector(point-origin))
            assert triangle is not None and distance is not None
            delta = point-origin-np.asarray(q)
            face_normal = np.asarray(n)
            # Complete outward-oriented full-reference triangles are queried;
            # original masked render-body faces never define this distance.
            sign = 1 if np.sum(delta*face_normal) >= 0 else -1
            gap[i] = float(distance)*sign
            length = np.linalg.norm(delta)
            normal[i] = sign*delta/length if length > 1e-12 else face_normal
        return gap[inverse], normal[inverse]
    return nearest


def two_ring_bridge(helper, surgery, edges, unused_planar):
    ids = sorted({v for _, _, a, b in edges for v in (a, b)})
    _, groups = np.unique(np.round(np.asarray(surgery.world)[ids], 9), axis=0, return_inverse=True)
    weld = dict(zip(ids, map(int, groups))); adjacency = defaultdict(list)
    for i, (_, _, a, b) in enumerate(edges):
        adjacency[weld[a]].append(i); adjacency[weld[b]].append(i)
    unseen = set(range(len(edges))); components = []
    while unseen:
        first = min(unseen); found = {first}; queue = deque([first])
        while queue:
            i = queue.popleft()
            for native in edges[i][2:]:
                for j in adjacency[weld[native]]:
                    if j not in found: found.add(j); queue.append(j)
        unseen.difference_update(found); components.append([edges[i] for i in sorted(found)])
    assert len(components) == 2, ('Actual sleeve join must have two rings', len(components))
    return helper['bridge'](surgery, *components)


def main():
    args = sys.argv[sys.argv.index('--')+1:]; assert len(args) == 2
    config_path, out = [Path(a).resolve() for a in args]
    assert not out.exists() and out.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-sleeve-rebuild28')
    config = json.loads(config_path.read_text()); assert config['acceptedArt'] is False
    for row in config['pins'].values(): pin(row)
    started = time.monotonic()
    def progress(message):
        print(message, flush=True)
        assert time.monotonic()-started < config['constructionBudgetSeconds'], 'Finite construction budget expired'
    prior = json.loads(pin(config['pins']['priorInputs']).read_text())
    cfg = json.loads(pin(config['pins']['cuffInput']).read_text())
    checkpoint = json.loads(pin(config['pins']['gloveReceipt']).read_text())
    assert checkpoint['native'] == config['pins']['gloveNative']
    assert checkpoint['originalHoodieUnchangedBeforeSave'] and checkpoint['exact75RestUnchanged']
    assert checkpoint['sourceMaster'] == prior['master']
    reference = np.load(pin(config['pins']['referenceSamples']))
    for row in checkpoint['gloveObjects'].values(): pin(row)
    engine = load(pin(config['pins']['cuffEngine']), 'sleeve28_unchanged_engine')
    engine.Q = runpy.run_path(str(pin(cfg['finiteBearingHelper'])))
    engine.B = load(pin(cfg['baseConstructor']), 'sleeve28_unchanged_surgery')
    B = engine.B
    base_config = json.loads(pin(cfg['baseInput']).read_text())
    B.V = runpy.run_path(str(pin(base_config['volumeHelper'])))
    B.A = runpy.run_path(str(pin(base_config['intersectionHelper'])))
    B.hit_radius = engine.Q['hit_radius']
    bridge = runpy.run_path(str(pin(config['pins']['bridgeHelper'])))
    engine.bridge = lambda surgery, edges, planar: two_ring_bridge(bridge, surgery, edges, planar)
    field_helper = load(pin(config['pins']['fieldHelper']), 'sleeve28_continuous_field')
    source = B.V['read_hoodie'](pin(prior['originalHoodie']))
    controls = json.loads(pin(prior['hoodieSourceFrames']).read_text())
    placement = json.loads(pin(prior['placement']).read_text())
    ownership = json.loads(pin(cfg['ownership']).read_text())
    for row in ownership['hands'].values(): pin(row['arrays'])
    settings = dict(base_config['settings']); settings.update(cfg['settings'])
    settings['sourceWrist'] = placement['sourceRest']['wrist']
    bpy.ops.wm.open_mainfile(filepath=str(pin(config['pins']['gloveNative'])), use_scripts=False)
    rig = bpy.data.objects['RiderSkeleton']; hoodie = bpy.data.objects['RiderHoodie']
    assert len(rig.data.bones) == 75 and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    assert not hoodie.data.shape_keys and hoodie.matrix_world.is_identity
    assert {o.name for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render} == B.VISIBLE
    geometry = runpy.run_path(str(pin(prior['geometryHelper'])))['geometry']
    rest = runpy.run_path(str(pin(prior['restHelper'])))['rest']
    protected = [bpy.data.objects[n] for n in B.VISIBLE-{'RiderHoodie'} | {'RiderBody__FullAnatomyReference'}]
    before = {o.name: geometry(o) for o in protected}; rest_before = rest(rig)
    wearer = bpy.data.objects['RiderBody__FullAnatomyReference']
    _, bp = B.A['points'](wearer); bf = B.A['faces'](wearer)
    key = 'RiderBody__FullAnatomyReference'
    assert np.array_equal(bp, reference[key+'_basis']), 'Actual full-reference Basis differs from witness'
    assert np.array_equal(bf, reference[key+'_triangles']), 'Actual full-reference triangles differ from witness'
    surgery = B.Surgery(hoodie, source)
    world = np.asarray(surgery.world); faces = np.asarray(surgery.faces, dtype=np.int32)
    groups = {g.index: g.name for g in hoodie.vertex_groups}
    arm_groups = {i for i, n in groups.items() if n.startswith(('DEF-shoulder.', 'DEF-upper_arm.', 'DEF-forearm.', 'DEF-hand.'))}
    seeds = np.array([sum(w for g, w in row.items() if g in arm_groups) > .5 for row in surgery.old_weights])
    assert seeds.sum() > 20000, 'Missing actual selected sleeve native field'
    # Do not fit original terminal caps or inward bands that the frozen cuff10
    # construction explicitly replaces. Crossing cut faces are handled by that
    # local exact cutter/contact fitter after the complete proximal cloth fit.
    retained = np.ones(len(faces), bool); removed_constraint_counts = {}
    for side in ('L', 'R'):
        xyz, _, _, _, _, scalar, _ = B.source_sleeve_frame(source, controls, side)
        owned = ownership['hands'][side]; data = np.load(pin(owned['arrays']))
        own_side = xyz[:, 0] > 0 if side == 'L' else xyz[:, 0] < 0
        terminal = np.all(own_side[faces], axis=1) & (scalar[faces].max(1) > owned['upperSourceAxialM'])
        inward = np.isin(np.arange(len(faces)), data['innerSourceFaceIds'])
        inward &= (scalar[faces].min(1) > owned['lowerSourceAxialM']) & (scalar[faces].max(1) < owned['upperSourceAxialM'])
        retained &= ~(terminal | inward)
        removed_constraint_counts[side] = {'terminalCutFaces': int(terminal.sum()), 'replacedInwardFaces': int(inward.sum())}
    progress('FIT complete selected sleeve volume against actual full wearer')
    moved, changed, field, fit_report = field_helper.fit(world, faces[retained], seeds, actual_nearest(bp, bf), config['field'], progress)
    fit_report['alreadyScheduledSourceRemovalExcludedFromConstraints'] = removed_constraint_counts
    surgery.move(moved, changed)
    profiles = {}; actual_gloves = {}; glove_trees = {}; sleeve_reports = {}
    for side in ('L', 'R'):
        dump = np.load(pin(prior['guideArrays'][side]))
        _, x, z = B.V['cuff_frame'](dump, placement['hands'][side])
        profile = B.V['BodyProfile'](bp, bf, dump['wristWorld'], dump['forearmAxisWorld'], x, z,
                                    {'bodyProfileStations': 49, 'bodyProfileAngles': 96})
        profiles[side] = profile
        gp = B.A['points'](bpy.data.objects['ActualSelectedGlove.'+side])[1]
        gf = B.A['faces'](bpy.data.objects['ActualSelectedGlove.'+side]); actual_gloves[side] = (gp, gf)
        glove_trees[side] = engine.Q['tree'](gp, gf, profile.wrist, profile.axis, 'actualCheckpointGlove.'+side)
        progress('REBUILD selected inward sleeve '+side)
        sleeve_reports[side] = engine.sleeve(surgery, controls, side, profile, engine.body_tree(bp, bf, profile),
                                             glove_trees[side], settings, ownership['hands'][side])
    cleanup = engine.remove_inherited_local_degenerates(surgery, profiles)
    out.mkdir(parents=True)
    np.savez_compressed(out/'complete-sleeve-field.npz', origin=field.origin, shape=field.shape,
                        spacing=field.spacing, values=field.values, active=field.active,
                        changedOriginalNativeIds=changed)
    progress('SAVE selected source cloth, rebuilt lining and named field ancestry')
    hp, hf, ancestry = surgery.finish(out)
    assert before == {o.name: geometry(o) for o in protected}
    assert rest_before == rest(rig)
    native = out/'UNACCEPTED-selected-sleeve-rebuild28.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
    report = {'acceptedArt': False, 'status': 'UNACCEPTED_CONSTRUCTION_DENSE_AND_MOTION_PENDING',
              'geometryGatesPassed': False, 'poseEnclosurePassed': False, 'movingReviewPassed': False,
              'recipeSHA256': sha(__file__), 'inputSHA256': sha(config_path), 'sourcePins': config['pins'],
              'actualFullReferenceExactToSavedBasisAndTriangles': True,
              'native': {'path': str(native.relative_to(ROOT)), 'sha256': sha(native)},
              'continuousClothFit': fit_report, 'sleeves': sleeve_reports, 'ancestry': ancestry,
              'inheritedDegenerateCleanup': cleanup, 'protectedGeometryUnchanged': before,
              'exact75RestUnchanged': True, 'field': {'path': str((out/'complete-sleeve-field.npz').relative_to(ROOT)),
                  'sha256': sha(out/'complete-sleeve-field.npz')},
              'limits': ['Rest contact and continuous-field injectivity are construction checks only.',
                         'Actual dense self/body/glove triangle checks and independent generic/bike arm motion remain required.',
                         'Existing source-prefix named skin fields remain exact; this does not assert their moving enclosure.',
                         'Selected distal turned lip is replaced as in cuff10; original outward PBR and retained UVs preserved.']}
    (out/'construction.json').write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'native': report['native'], 'status': report['status']}), flush=True)


if __name__ == '__main__': main()
