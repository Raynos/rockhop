"""Native08: native07 construction with wrist-conditioned finite bearings.

Run only after parent review/checkpoint, under unchanged CPU2/96GiB guard.
The original source meshes remain immutable. This is an unaccepted candidate.
"""
import hashlib
import importlib.util
import json
import runpy
import sys
from collections import defaultdict
from pathlib import Path

import bpy
import numpy as np
from mathutils import Vector
from mathutils.geometry import delaunay_2d_cdt

ROOT = Path(__file__).resolve().parents[4]
HERE = Path(__file__).resolve().parent
B = None
Q = None


def sha(path):
    h = hashlib.sha256()
    with Path(path).open('rb') as stream:
        while block := stream.read(1048576):
            h.update(block)
    return h.hexdigest()


def pin(row):
    p = ROOT/row['path']
    assert sha(p) == row['sha256'], row['path']
    return p


def boundary(surgery, face_ids=None):
    """Actual-position incidence distinguishes new lining from its source parent."""
    world = np.asarray(surgery.world)
    _, weld = np.unique(np.round(world, 9), axis=0, return_inverse=True)
    edge_faces = defaultdict(list)
    for i in range(len(surgery.faces)) if face_ids is None else face_ids:
        face = surgery.faces[i]
        for k, (a, b) in enumerate(zip(face, face[1:]+face[:1])):
            key = tuple(sorted((int(weld[a]), int(weld[b]))))
            if key[0] != key[1]:
                edge_faces[key].append((i, k, a, b))
    return [rows[0] for rows in edge_faces.values() if len(rows) == 1]


def bridge(surgery, edges, planar):
    """CDT annulus; topology parametrization need not flatten the actual vertices."""
    ids = sorted({v for _, _, a, b in edges for v in (a, b)})
    world = np.asarray(surgery.world)
    _, inverse = np.unique(np.round(world[ids], 9), axis=0, return_inverse=True)
    representatives = {}
    for vertex, group in zip(ids, inverse):
        representatives.setdefault(int(group), vertex)
    native = np.array([representatives[i] for i in range(len(representatives))], dtype=int)
    lookup = {v: int(group) for v, group in zip(ids, inverse)}
    graph = defaultdict(list); desired = {}; uv = {}; materials = []
    for face_id, corner, a, b in edges:
        x, y = lookup[a], lookup[b]
        if x == y:
            continue
        key = tuple(sorted((x, y)))
        assert key not in desired
        desired[key] = (y, x)
        graph[x].append(y); graph[y].append(x)
        uv.setdefault(x, surgery.uv[face_id][corner]); uv.setdefault(y, surgery.uv[face_id][(corner+1) % 3])
        materials.append(surgery.material[face_id])
    assert all(len(row) == 2 for row in graph.values())
    unseen = set(graph); loops = []
    while unseen:
        first = min(unseen); chain = [first]; old, at = None, first
        while True:
            nxt = next(n for n in graph[at] if n != old)
            if nxt == first:
                break
            assert nxt not in chain
            chain.append(nxt); old, at = at, nxt
        unseen.difference_update(chain); loops.append(chain)
    assert len(loops) == 2, ('Join requires exactly two rings', len(loops))
    p = np.asarray(planar)[native]
    areas = [abs(np.sum(p[loop, 0]*np.roll(p[loop, 1], -1)-p[loop, 1]*np.roll(p[loop, 0], -1)))/2 for loop in loops]
    outer = loops[int(np.argmax(areas))]; inner = loops[1-int(np.argmax(areas))]
    assert all(B.point_inside(point, p[outer]) for point in p[inner]), 'Join contours are not nested'
    vertices, _, triangles, origins, _, _ = delaunay_2d_cdt([Vector(x) for x in p], list(desired), [], 0, 1e-10, True)
    remap = []
    for origin in origins:
        assert len(origin) == 1, 'Join boundary crossed or merged distinct authored vertices'
        remap.append(int(origin[0]))
    faces = []
    for t in triangles:
        face = [remap[i] for i in t]; center = p[face].mean(axis=0)
        if B.point_inside(center, p[outer]) and not B.point_inside(center, p[inner]):
            faces.append(face)
    incidence = defaultdict(list)
    for i, face in enumerate(faces):
        for a, b in zip(face, face[1:]+face[:1]):
            incidence[tuple(sorted((a, b)))].append((i, a, b))
    exterior = {key: rows[0] for key, rows in incidence.items() if len(rows) == 1}
    assert set(exterior) == set(desired) and all(len(rows) <= 2 for rows in incidence.values())
    orientations = {1 if (row[1], row[2]) == desired[key] else -1 for key, row in exterior.items()}
    assert len(orientations) == 1, 'Join winding is inconsistent with its attached walls'
    flip = next(iter(orientations)) == -1
    for face in faces:
        if flip:
            face.reverse()
        surgery.add_face(native[face].tolist(), [uv[i] for i in face], materials[0])
    return {'boundaryVertices': len(native), 'newFaces': len(faces), 'bothBoundaryLoopsPreserved': True,
            'parameterizationAreas': areas, 'actualVerticesFlattened': False}


def body_tree(points, faces, profile):
    d = points-profile.wrist; axial = np.sum(d*profile.axis, axis=1)
    radius = np.linalg.norm(d-axial[:, None]*profile.axis, axis=1)
    own = points[:, 0] > 0 if profile.wrist[0] > 0 else points[:, 0] < 0
    mask = own & (axial > -.035) & (axial < .23) & (radius < .12)
    return Q['tree'](points, faces[np.any(mask[faces], axis=1)], profile.wrist, profile.axis, 'wearer.'+('L' if profile.wrist[0] > 0 else 'R'))


def full_cuff(surgery, dump, placement, profile, wearer, settings):
    edge, report = B.floor_cut(surgery, dump, settings['gloveFloorCutY'])
    scale, x_basis, z_basis = B.V['cuff_frame'](dump, placement)
    source = np.asarray(surgery.source); before = np.asarray(surgery.world)
    axial, x, z = B.V['source_cuff'](source, dump, settings['sourceWrist'], scale, x_basis, z_basis)
    unscaled = profile.wrist+axial[:, None]*profile.axis+x[:, None]*x_basis+z[:, None]*z_basis
    faces = np.asarray(surgery.faces, dtype=int)
    cuff = faces[np.all(source[faces, 1] <= settings['gloveFloorCutY']+1e-8, axis=1)]
    shell = Q['tree'](unscaled, faces, profile.wrist, profile.axis, 'sourceCuff.'+('L' if profile.wrist[0] > 0 else 'R'))
    # Every retained dense cuff triangle contributes four interior bearings.
    # This spans the actual cuff, including the old missed sourceY ~-.94..-.97.
    barycentric = np.array([[1/3, 1/3, 1/3], [.9, .05, .05], [.05, .9, .05], [.05, .05, .9]])
    required = 1.; witness = None; probes = 0; grazing = 0
    axial_range = [float('inf'), -float('inf')]
    for face in cuff:
        tri = unscaled[face]
        normal = np.cross(tri[1]-tri[0], tri[2]-tri[0]); length = np.linalg.norm(normal)
        if length < 1e-14:
            continue
        normal /= length
        for bary in barycentric:
            p = np.sum(tri*bary[:, None], axis=0); station = float(np.sum((p-profile.wrist)*profile.axis))
            origin = profile.wrist+station*profile.axis; vector = p-origin; radius = np.linalg.norm(vector)
            if radius < 1e-8:
                raise AssertionError('Actual cuff reaches wearer centerline')
            direction = vector/radius
            if abs(float(np.sum(normal*direction))) < 1e-8:
                grazing += 1
                continue
            hit = B.hit_radius(shell, origin, direction)
            body = B.hit_radius(wearer, origin, direction)
            assert hit is not None and body is not None, ('Dense cuff bearing missing actual triangle surface', face.tolist(), bary.tolist())
            need = (body+settings['gloveCavityEaseM'])/hit
            if need > required:
                required = float(need)
                witness = {'sourceParentVertexIds': face.tolist(), 'barycentric': bary.tolist(),
                           'sourceY': float(np.sum(source[face, 1]*bary)), 'nativeAxialM': station,
                           'cavityRadiusM': hit, 'wearerRadiusM': body}
            axial_range[0] = min(axial_range[0], station); axial_range[1] = max(axial_range[1], station); probes += 1
    assert probes > 1000
    assert required <= settings['maximumCuffScale'], ('Full dense cuff fit exceeds selected identity bound', required, witness)
    proposed = profile.wrist+axial[:, None]*profile.axis+required*x[:, None]*x_basis+required*z[:, None]*z_basis
    alpha = B.smooth((settings['gloveJoinY']-source[:, 1])/(settings['gloveJoinY']-settings['gloveFullY']))
    surgery.move(before+alpha[:, None]*(proposed-before), np.flatnonzero(alpha > 0))
    inner = B.lining(surgery, edge, profile.axis, profile.wrist, .0008, -settings['gloveLiningLengthM'], profile=profile)
    report.update(sourceTransverseUniformScale=required, newLining=inner,
                  actualDenseCuffTriangles=len(cuff), actualTriangleInteriorBearings=probes,
                  radialGrazingBearings=grazing, actualAxialRangeM=axial_range, controllingSourceBearing=witness,
                  limits='Full axial source cuff is sampled on every actual triangle; finite bearings are not containment proof. Actual triangle/body/cloth checks remain mandatory.')
    return report


def fit_exterior(surgery, face_ids, source_scalar, lower, upper, profile, wearer, glove_tree, settings):
    faces = np.asarray(surgery.faces, dtype=int)[face_ids]
    native = np.unique(faces)
    source = np.asarray(surgery.source); world = np.asarray(surgery.world)
    # Source UV seams share a position DOF, but retain their original native IDs.
    _, first, group = np.unique(np.round(source[native], 10), axis=0, return_index=True, return_inverse=True)
    chosen = native[first]; old = world[chosen].copy(); s = source_scalar[chosen]
    axial = np.sum((old-profile.wrist)*profile.axis, axis=1)
    terminal = abs(s-upper) < 1e-8; proximal = abs(s-lower) < 1e-8
    assert terminal.sum() > 20 and proximal.sum() > 20
    # A monotone axial taper moves the shortened source opening into the actual
    # gauntlet overlap, preserving the proximal source boundary exactly.
    old_end = float(np.mean(axial[terminal])); end_delta = settings['sleeveEndpointM']-old_end
    old_span = float(np.mean(axial[proximal])-old_end)
    assert old_span > end_delta > 0, ('Axial retargeting would reverse the selected sleeve', old_span, end_delta)
    t = np.clip((s-lower)/(upper-lower), 0, 1)
    tailored = old+t[:, None]*end_delta*profile.axis
    axial = np.sum((tailored-profile.wrist)*profile.axis, axis=1)
    centers = profile.wrist+axial[:, None]*profile.axis
    radial = tailored-centers; radius = np.linalg.norm(radial, axis=1)
    direction = radial/radius[:, None]
    lo = np.empty(len(chosen)); hi = np.full(len(chosen), np.inf)
    cuff_hits = 0
    for i in range(len(chosen)):
        b = B.hit_radius(wearer, centers[i], direction[i]); assert b is not None, ('Wearer bearing missing', int(chosen[i]))
        lo[i] = b+settings['sleeveLiningM']+settings['sleeveSkinEaseM']-radius[i]
        g = B.hit_radius(glove_tree, centers[i], direction[i])
        if g is not None:
            hi[i] = g-settings['garmentGapM']-radius[i]; cuff_hits += 1
    assert np.all(lo <= hi), ('No room for actual cloth wall', int(chosen[np.argmax(lo-hi)]), float(np.max(lo-hi)))
    # Projected Jacobi minimizes displacement Dirichlet energy plus a position
    # penalty under the actual contact bounds. The original inner wall is absent;
    # no radial min/max source chart or whole-volume compression is involved.
    inverse = np.full(len(source), -1, dtype=int); inverse[native] = group
    f = inverse[faces]; edges = np.unique(np.sort(np.concatenate([f[:, [0, 1]], f[:, [1, 2]], f[:, [2, 0]]]), axis=1), axis=0)
    edges = edges[edges[:, 0] != edges[:, 1]]
    a, b = edges[:, 0], edges[:, 1]
    degree = np.bincount(np.r_[a, b], minlength=len(chosen)).astype(float)
    required = (lo > 0) | (hi < 0)
    active = required.copy()
    for _ in range(settings['contactNeighborRings']):
        next_active = active.copy(); next_active[a[active[b]]] = True; next_active[b[active[a]]] = True; active = next_active
    active &= ~proximal
    assert np.all((lo[~active] <= 1e-8) & (hi[~active] >= -1e-8)), 'A fixed preserved exterior vertex violates contact'
    displacement = np.clip(np.zeros(len(chosen)), lo, hi); displacement[~active] = 0
    penalty = settings['contactPositionPenalty']; converged = False; delta = float('inf')
    for iteration in range(settings['contactIterations']):
        sums = np.bincount(np.r_[a, b], weights=np.r_[displacement[b], displacement[a]], minlength=len(chosen))
        target = sums/(degree+penalty)
        target = np.clip(target, lo, hi); target[~active] = 0
        following = .5*displacement+.5*target
        delta = float(np.max(abs(following-displacement))); displacement = following
        if delta < settings['contactConvergenceM']:
            converged = True; break
    assert converged, ('Actual contact solve did not converge', delta)
    moved = tailored+displacement[:, None]*direction
    result = world.copy(); result[native] = moved[group]
    changed = native[np.any(result[native] != world[native], axis=1)]
    surgery.move(result, changed)
    return {'outerSourceVertices': len(native), 'positionDOFs': len(chosen), 'originalContactViolationDOFs': int(required.sum()),
            'contactNeighborhoodDOFs': int(active.sum()), 'actualCavityBearingDOFs': cuff_hits,
            'radialDisplacementRangeM': [float(displacement.min()), float(displacement.max())],
            'solverIterations': iteration+1, 'lastUpdateM': delta, 'sourceProximalBoundaryFixed': True,
            'axialEndTranslationM': end_delta, 'axialDerivativeRatio': (old_span-end_delta)/old_span,
            'limits': 'Contact displacement and axial taper are a construction candidate. Self-intersection and actual wearer/glove triangle checks are required; finite contact constraints are not a passing-art claim.'}


def sleeve(surgery, controls, side, profile, wearer, glove_tree, settings, owned):
    source = np.asarray(surgery.source)
    _, head, axis, u, v, scalar, selected = B.source_sleeve_frame(source, controls, side)
    source_tip = float(scalar[selected].max())
    lower, upper = owned['lowerSourceAxialM'], owned['upperSourceAxialM']
    data = np.load(pin(owned['arrays']))
    outer_ids, inner_ids = data['outerSourceFaceIds'], data['innerSourceFaceIds']
    excluded = set(data['excludedPositionDegenerateSourceFaceIds'].tolist())
    surgery.delete([i for i, source_id in enumerate(surgery.face_sources) if source_id in excluded])
    candidates = np.isin(surgery.face_sources, np.r_[outer_ids, inner_ids])
    surgery.cut(scalar-lower, candidates, keep_both=True)
    source = np.asarray(surgery.source)
    xyz, head, axis, u, v, scalar, selected = B.source_sleeve_frame(source, controls, side)
    f = np.asarray(surgery.faces)
    own_side = xyz[:, 0] > 0 if side == 'L' else xyz[:, 0] < 0
    distal = np.all(own_side[f], axis=1) & (scalar[f].max(axis=1) > upper)
    surgery.edge_cache.clear()
    surgery.cut(scalar-upper, distal)
    source = np.asarray(surgery.source)
    xyz, head, axis, u, v, scalar, selected = B.source_sleeve_frame(source, controls, side)
    f = np.asarray(surgery.faces)
    inside = (scalar[f].mean(axis=1) > lower+1e-9) & (scalar[f].mean(axis=1) < upper-1e-9)
    removal = np.flatnonzero(inside & np.isin(surgery.face_sources, inner_ids))
    removed = np.asarray(surgery.face_sources)[removal].copy()
    surgery.delete(removal)
    f = np.asarray(surgery.faces)
    band = (scalar[f].mean(axis=1) > lower+1e-9) & (scalar[f].mean(axis=1) < upper-1e-9)
    exterior = np.flatnonzero(band & np.isin(surgery.face_sources, outer_ids))
    assert len(exterior) > 10000 and len(removal) > 10000
    original_boundaries = boundary(surgery)
    proximal = [e for e in original_boundaries if abs(scalar[e[2]]-lower) < 1e-8 and abs(scalar[e[3]]-lower) < 1e-8]
    distal = [e for e in original_boundaries if abs(scalar[e[2]]-upper) < 1e-8 and abs(scalar[e[3]]-upper) < 1e-8]
    assert len(proximal) > 20 and len(distal) > 20
    fitting = fit_exterior(surgery, exterior, scalar, lower, upper, profile, wearer, glove_tree, settings)
    world = np.asarray(surgery.world)
    duplicate = {}
    for vertex in np.unique(np.asarray(surgery.faces)[exterior]):
        p = world[vertex]; axial = float(np.sum((p-profile.wrist)*profile.axis)); radial = p-profile.wrist-axial*profile.axis
        radius = np.linalg.norm(radial); assert radius > settings['sleeveLiningM']
        inside = p-settings['sleeveLiningM']*radial/radius
        duplicate[int(vertex)] = surgery.add(surgery.source[vertex], inside, surgery.parents[vertex], surgery.coefficients[vertex], 3)
    lining_faces = []
    for i in exterior:
        lining_faces.append(len(surgery.faces))
        surgery.add_face([duplicate[v] for v in surgery.faces[i][::-1]], surgery.uv[i][::-1], surgery.material[i])
    lining_edges = boundary(surgery, lining_faces)
    source = np.asarray(surgery.source)
    xyz, _, _, _, _, scalar, _ = B.source_sleeve_frame(source, controls, side)
    line_proximal = [e for e in lining_edges if abs(scalar[e[2]]-lower) < 1e-8 and abs(scalar[e[3]]-lower) < 1e-8]
    line_distal = [e for e in lining_edges if abs(scalar[e[2]]-upper) < 1e-8 and abs(scalar[e[3]]-upper) < 1e-8]
    source_planar = np.column_stack((np.sum((xyz-head)*u, axis=1), np.sum((xyz-head)*v, axis=1)))
    proximal_join = bridge(surgery, proximal+line_proximal, source_planar)
    world = np.asarray(surgery.world)
    actual_planar = np.column_stack((np.sum((world-profile.wrist)*profile.x, axis=1), np.sum((world-profile.wrist)*profile.z, axis=1)))
    distal_join = bridge(surgery, distal+line_distal, actual_planar)
    return {'ownership': owned['arrays'], 'removedOwnedInnerBandTriangles': len(removal),
            'removedBandSourceFaceCount': len(set(int(i) for i in removed)),
            'removedBandAncestry': 'innerSourceFaceIds in the pinned ownership NPZ, restricted between the two source cuts; clipped portions outside the band remain.',
            'retainedOuterBandTriangles': len(exterior),
            'newLiningVertices': len(duplicate), 'newLiningTriangles': len(lining_faces), 'liningWallM': settings['sleeveLiningM'],
            'newLiningAncestry': 'Each lining vertex copies its retained exterior source-parent interpolation; each reversed face copies that exterior UV triangle/material. This is authored hidden lining, not a retained source interior.',
            'sourceCutAxialM': [lower, upper], 'sourceTipAxialM': source_tip, 'removedSourceAxialLengthM': source_tip-upper, 'distalDetailLoss': 'Original source material beyond the section7 plane is removed, including its turned/oblique lip. No claim that this selected detail is preserved.',
            'contactFit': fitting, 'proximalJoin': proximal_join, 'distalHem': distal_join}


def remove_inherited_local_degenerates(surgery, profiles):
    p = np.asarray(surgery.world); f = np.asarray(surgery.faces, dtype=int)
    area = np.linalg.norm(np.cross(p[f[:, 1]]-p[f[:, 0]], p[f[:, 2]]-p[f[:, 0]]), axis=1)
    bad = np.flatnonzero(area <= 1e-14); removed = []; retained = []
    for i in bad:
        source_id = surgery.face_sources[i]
        inherited = False
        if source_id >= 0:
            old = surgery.base_world[surgery.base_faces[source_id]]
            inherited = np.linalg.norm(np.cross(old[1]-old[0], old[2]-old[0])) <= 1e-14
        local = False
        for profile in profiles.values():
            d = p[f[i]]-profile.wrist; s = np.sum(d*profile.axis, axis=1)
            r = np.linalg.norm(d-s[:, None]*profile.axis, axis=1)
            local |= bool(np.any((s > -.02) & (s < .20) & (r < .10)))
        if inherited and local:
            removed.append(int(i))
        else:
            retained.append({'triangle': int(i), 'sourceFace': int(source_id), 'inherited': bool(inherited)})
    source_ids = sorted({int(surgery.face_sources[i]) for i in removed})
    surgery.delete(removed)
    return {'removedInheritedLocalTriangles': len(removed), 'removedSourceFaceIds': source_ids,
            'retainedDegenerates': retained, 'newDegeneratesAreNeverDeletedToPass': True}


def main():
    global B, Q
    args = sys.argv[sys.argv.index('--')+1:]
    assert len(args) == 1
    out = Path(args[0]).resolve()
    assert out.is_relative_to(ROOT/'harness/out/rider-rebuild/astra-cuff-bearing18') and not out.exists()
    config = json.loads((HERE/'input08.json').read_text())
    pin(config['failedConstructor'])
    pin(config['failedInput'])
    Q = runpy.run_path(str(pin(config['finiteBearingHelper'])))
    base_path = pin(config['baseConstructor'])
    spec = importlib.util.spec_from_file_location('selected_construction06_base', base_path)
    B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
    # Keep the existing caller signature; condition BEFORE mathutils.Vector.
    B.hit_radius = Q['hit_radius']
    base_config = json.loads(pin(config['baseInput']).read_text())
    B.V = runpy.run_path(str(pin(base_config['volumeHelper'])))
    B.A = runpy.run_path(str(pin(base_config['intersectionHelper'])))
    prior = json.loads(pin(base_config['priorInputs']).read_text())
    for name in ('master', 'originalGloveDense', 'originalHoodie', 'placement', 'hoodieSourceFrames', 'restHelper', 'geometryHelper'):
        pin(prior[name])
    ownership = json.loads(pin(config['ownership']).read_text())
    for row in ownership['hands'].values():
        pin(row['arrays'])
    source_glove = np.load(pin(prior['originalGloveDense']))['vertices']
    source_hoodie = B.V['read_hoodie'](pin(prior['originalHoodie']))
    placement = json.loads(pin(prior['placement']).read_text())
    controls = json.loads(pin(prior['hoodieSourceFrames']).read_text())
    bpy.ops.wm.open_mainfile(filepath=str(pin(prior['master'])))
    rig = bpy.data.objects['RiderSkeleton']
    assert len(rig.data.bones) == 75 and all(b.matrix_basis.is_identity for b in rig.pose.bones)
    assert {o.name for o in bpy.context.scene.objects if o.type == 'MESH' and not o.hide_render} == B.VISIBLE
    rest = runpy.run_path(str(pin(prior['restHelper'])))['rest']
    geometry = runpy.run_path(str(pin(prior['geometryHelper'])))['geometry']
    protected = [bpy.data.objects[n] for n in (B.VISIBLE-set(B.EDITED)) | {'RiderBody__FullAnatomyReference'}]
    protected_before = {o.name: geometry(o) for o in protected}; rest_before = rest(rig)
    settings = dict(base_config['settings']); settings.update(config['settings'])
    settings['sourceWrist'] = placement['sourceRest']['wrist']
    _, bp = B.A['points'](bpy.data.objects['RiderBody__FullAnatomyReference'])
    bf = B.A['faces'](bpy.data.objects['RiderBody__FullAnatomyReference'])
    profiles, wearers, dumps = {}, {}, {}
    for side in ('L', 'R'):
        dump = np.load(pin(prior['guideArrays'][side])); dumps[side] = dump
        _, x, z = B.V['cuff_frame'](dump, placement['hands'][side])
        profile = B.V['BodyProfile'](bp, bf, dump['wristWorld'], dump['forearmAxisWorld'], x, z,
                                    {'bodyProfileStations': 49, 'bodyProfileAngles': 96})
        profiles[side] = profile; wearers[side] = body_tree(bp, bf, profile)
    out.mkdir(parents=True)
    report = {'acceptedArt': False, 'status': 'UNACCEPTED_SOURCE_OWNED_INTERIOR_RECONSTRUCTION',
              'sourceMaster': prior['master'], 'visibleMeshes': sorted(B.VISIBLE), 'objects': {}, 'hands': {},
              'recipeSHA256': sha(__file__), 'failedConstructor': config['failedConstructor'],
              'finiteBearingHelper': config['finiteBearingHelper'], 'conditionedRayQueries': Q['receipts'], 'inputSHA256': sha(HERE/'input08.json'), 'ownership': config['ownership'],
              'newTopology': 'Proven inner sleeve bands removed between two cuts; retained selected exteriors minimally tailored to actual contact bounds; explicitly authored thin lining and annular joins. Full dense original glove cuff fitted as one positive transverse scale.',
              'geometryGatesPassed': False, 'localGeometryGatesPassed': False, 'movingReviewPassed': False}
    actual, glove_trees = {}, {}
    for side in ('L', 'R'):
        print('CONSTRUCT full dense cuff '+side, flush=True)
        surgery = B.Surgery(bpy.data.objects['ActualSelectedGlove.'+side], source_glove)
        row = full_cuff(surgery, dumps[side], placement['hands'][side], profiles[side], wearers[side], settings)
        cleanup = remove_inherited_local_degenerates(surgery, {side: profiles[side]})
        gp, gf, ancestry = surgery.finish(out); report['objects'][surgery.obj.name] = ancestry
        actual[side] = (gp, gf)
        glove_trees[side] = Q['tree'](gp, gf, profiles[side].wrist, profiles[side].axis, 'finishedCuff.'+side)
        report['hands'][side] = {'glove': row, 'gloveDegenerates': cleanup}
    hoodie = B.Surgery(bpy.data.objects['RiderHoodie'], source_hoodie)
    for side in ('L', 'R'):
        print('CONSTRUCT owned inner sleeve '+side, flush=True)
        report['hands'][side]['sleeve'] = sleeve(hoodie, controls, side, profiles[side], wearers[side], glove_trees[side], settings, ownership['hands'][side])
    report['sleeveDegenerates'] = remove_inherited_local_degenerates(hoodie, profiles)
    hp, hf, row = hoodie.finish(out); report['objects']['RiderHoodie'] = row
    assert protected_before == {o.name: geometry(o) for o in protected}
    assert rest_before == rest(rig)
    report.update(exact75RestUnchanged=True, protectedGeometryUnchanged=protected_before)
    native = out/'UNACCEPTED-complete-selected-rider.blend'
    bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
    report['native'] = {'path': str(native.relative_to(ROOT)), 'sha256': sha(native)}
    report_path = out/'construction.json'; report_path.write_text(json.dumps(report, indent=2)+'\n')
    _, vp = B.A['points'](bpy.data.objects['RiderBody']); vf = B.A['faces'](bpy.data.objects['RiderBody'])
    for side in ('L', 'R'):
        profile = profiles[side]; gp, gf = actual[side]
        def region(points, faces, lower, upper, radial=None):
            d = points-profile.wrist; s = np.sum(d*profile.axis, axis=1)
            r = np.linalg.norm(d-s[:, None]*profile.axis, axis=1)
            own = points[:, 0] > 0 if side == 'L' else points[:, 0] < 0
            selected = own & (s > lower) & (s < upper)
            if radial is not None:
                selected &= r < radial
            ids = np.flatnonzero(np.any(selected[faces], axis=1))
            return faces[ids], ids
        gc, gi = region(gp, gf, -.018, .1, .12)
        hc, hi = region(hp, hf, -.005, .195, .12)
        vc, vi = region(vp, vf, -.02, .20, .12)
        wide_hc, wide_hi = region(hp, hf, -.005, .195)
        wide_vc, wide_vi = region(vp, vf, -.02, .20)
        check = B.A['intersections']
        checks = [('gloveSelf', lambda: check(gp, gc, face_ids_a=gi)),
                  ('sleeveSelf', lambda: check(hp, hc, face_ids_a=hi)),
                  ('gloveSleeve', lambda: check(gp, gc, hp, hc, face_ids_a=gi, face_ids_b=hi)),
                  ('gloveVisibleWearer', lambda: check(gp, gc, vp, vc, face_ids_a=gi, face_ids_b=vi)),
                  ('sleeveVisibleWearer', lambda: check(hp, hc, vp, vc, face_ids_a=hi, face_ids_b=vi)),
                  ('wideCropVisibleWearerIncludingRemoteTorso', lambda: check(hp, wide_hc, vp, wide_vc, face_ids_a=wide_hi, face_ids_b=wide_vi))]
        report['hands'][side]['geometry'] = {}
        for name, function in checks:
            print('CHECK '+side+' '+name, flush=True)
            report['hands'][side]['geometry'][name] = function()
            report_path.write_text(json.dumps(report, indent=2)+'\n')
    report['localGeometryGatesPassed'] = all(row['passed'] for h in report['hands'].values() for name, row in h['geometry'].items() if name != 'wideCropVisibleWearerIncludingRemoteTorso')
    report['geometryGatesPassed'] = all(row['passed'] for h in report['hands'].values() for row in h['geometry'].values())
    report['status'] = 'UNACCEPTED_MOVING_REVIEW_PENDING' if report['geometryGatesPassed'] else 'REJECTED_GEOMETRY_REQUIRES_CORRECTION'
    report['scope'] = 'Local forearm/cuff checks have explicit radial ownership; inherited remote torso/body crossings remain separately checked and still prevent geometryGatesPassed. No mask waiver.'
    report_path.write_text(json.dumps(report, indent=2)+'\n')
    print(json.dumps({'native': report['native'], 'status': report['status'], 'localGeometryGatesPassed': report['localGeometryGatesPassed']}), flush=True)


if __name__ == '__main__':
    main()
