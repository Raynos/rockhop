"""One conforming selected cap and bounded anatomical linear field extension.

SOURCE ONLY until the parent freezes this recipe. No native, contact, baking,
production-four or motion claim. The selected dense47 donor remains authority.
"""
from collections import defaultdict
import json
from pathlib import Path
import runpy
import sys

import numpy as np

HERE = Path(__file__).resolve().parent
A = runpy.run_path(str(HERE/'author.py'))
ROOT, pin, checked = (A[k] for k in ('ROOT', 'pin', 'checked'))
INPUT = {'path': 'harness/out/rider-rebuild/selected-hoodie-joints77/receiver12/receiver.json',
         'sha256': '115aeff06087f24ca0fac029846e8f492aed699273fdc2d08f7b8cc13ba85139'}
PRIOR = {'path': 'assets/blender/rider-rebuild/selected-hoodie-joints77/whole_anatomical_fields.py',
         'sha256': '22aab060a8bab553c15c0d7f0f22e088eebad2a270d443d54192c63c104e5ed1'}
BODY = {'path': 'harness/out/rider-rebuild/selected-hoodie-joints77/body-guide01/actual-body-fields.json',
        'sha256': '8fb18ac1722439375e3fa30a3b72b9696fb8d2459d4747892d3a454e6f2be6e3'}
GRAPH = {'path': 'assets/blender/rider-rebuild/selected-hoodie-joints77/field_repair.py',
         'sha256': 'ce027c64927dfb571bf8c1b1edb5502b619daf9749f78af8ae845a68b14f26e4'}
CAP_U = (.06, .15, .30, .50, .72, .88, 1.)
TRUNK = ('DEF-spine', 'DEF-spine.001', 'DEF-spine.002', 'DEF-spine.003')
SOURCE_ROLES = ('selected_original', 'armhole_seam')


def inputs():
    prior = runpy.run_path(str(checked(PRIOR)))['verify'](checked(INPUT))
    body = json.loads(checked(BODY).read_text())
    assert body['sourceReceipt'] == prior['source47Receipt'] and body['nativeMutation'] is False
    rest = json.loads(checked(prior['source47Receipt']).read_text())['expectedRest']
    assert body['rest'] == rest and len(rest) == 75
    return prior, dict(np.load(checked(prior['receiver']))), body, np.load(checked(body['arrays'])), rest


def seam_loops(a):
    """Walk real retained polygon edges; never sort a replacement seam."""
    edges = defaultdict(list); seams = set(np.flatnonzero(a['vertexRoles'] == 'armhole_seam'))
    for start, count, role in zip(a['polygonStarts'], a['polygonCounts'], a['faceRoles']):
        if role != 'selected_retained':
            continue
        face = a['cornerVertexIds'][start:start+count].tolist()
        for i, j in zip(face, face[1:]+face[:1]):
            if i in seams and j in seams:
                edges[tuple(sorted((i, j)))].append((i, j))
    adjacent = defaultdict(list)
    for (i, j), rows in edges.items():
        if len(rows) == 1:
            adjacent[i].append(j); adjacent[j].append(i)
    assert set(adjacent) == seams and all(len(v) == 2 for v in adjacent.values())
    loops, seen = [], set()
    for first in sorted(adjacent):
        if first in seen:
            continue
        loop, previous, current = [], None, first
        while current not in seen:
            seen.add(current); loop.append(current)
            previous, current = current, next(v for v in adjacent[current] if v != previous)
        assert current == first
        loops.append(np.asarray(loop, np.int32))
    assert sorted(map(len, loops)) == [94, 96, 97, 102]
    return loops


def increasing_loop(loop, a, frame):
    origin, _, forward, outward = frame(0)
    p = a['referencePositions'][loop]-origin
    angles = np.arctan2(p@outward, p@forward) % (2*np.pi)
    increments = (np.roll(angles, -1)-angles) % (2*np.pi)
    if increments.sum() > 3*np.pi:
        loop = loop[::-1]; angles = angles[::-1]
    first = int(np.argmin(angles)); loop = np.roll(loop, -first); angles = np.roll(angles, -first)
    assert np.all(np.diff(angles) > 0), 'Retained seam is not a single angular chart'
    return loop, angles


def torso12(points, names, rest):
    # Evaluate the frozen12 trunk field at new model vertices, not a new paint.
    count = len(points)
    stub = {'positions': points, 'groupNames': np.asarray(names),
            'vertexRoles': np.full(count, 'selected_original'), 'authoredSkinBlend': np.zeros(count),
            'authoredCapSeamParents': np.full((count, 2), -1), 'authoredCapSeamFraction': np.zeros(count)}
    return runpy.run_path(str(checked(PRIOR)))['paint'](stub, rest)[1]


def body_boundary(point, side, kind, frame, bones, body, surface, names, trunk):
    """First outward wall from the anatomical interior selects the body sheet.

    Torso seams originate on the native spine centerline; the terminal ring
    originates on the native arm centerline. No nearest-surface query is used.
    Only own arm/clavicle ownership is transferred. The body's residual torso
    share uses12 spine proportions, so no pelvic, head or opposite-arm control
    becomes an attachment anchor. This is an explicit anatomical field design.
    """
    if kind == 'torso':
        spine = np.asarray([bones[n][2] for n in (*TRUNK, 'DEF-spine.004')])
        origin = np.array([0., np.interp(point[2], spine[:, 2], spine[:, 1]), point[2]])
    else:
        assert kind == 'arm'
        origin = frame(.145)[0]
    direction = A['unit'](point-origin)
    hits = surface.ray(origin, direction)
    assert hits and hits[0][1] > 0, ('Anatomical origin must be inside its body sheet', side, kind)
    distance, _, face, bary = hits[0]
    assert np.all(body['regionIds'][body['triangles'][face]] == 1), 'Head cannot own this garment patch'
    raw = bary@body['normalizedNamedFields'][body['triangles'][face]]
    body_names = body['groupNames'].tolist()
    own = ['DEF-shoulder.'+side]+['DEF-'+part+'.'+side+suffix
        for part in ('upper_arm', 'forearm') for suffix in ('', '.001')]
    result = np.zeros(len(names))
    for name in own:
        result[names.index(name)] = raw[body_names.index(name)]
    spine_ids = [names.index(n) for n in TRUNK]; spine = trunk[spine_ids]
    assert spine.sum() > 0 and result.sum() <= 1+1e-12
    result[spine_ids] = (1-result.sum())*spine/spine.sum()
    witness = {'kind': kind, 'bodyTriangle': int(face), 'barycentric': bary.tolist(),
               'rayOrigin': origin.tolist(), 'rayDirection': direction.tolist(), 'rayDistanceM': distance,
               'bodyPoint': (origin+direction*distance).tolist(), 'rawNamedFields': raw.tolist(),
               'ownArmAndClavicleTransferred': own, 'residualTorsoAuthority': 'Exact12 spine proportions'}
    return result, witness


def raw_appearance(a, prior, new_points):
    """Retain literal selected ancestry for preview; NOT a same-wall bake cage."""
    compact = np.load(checked(prior['sourceReceiver']))
    triangles, triangle_uv, _ = A['triangulate'](compact)
    surface = A['Surface'](compact['positions'], triangles)
    guides = np.load(checked(json.loads(checked(prior['actualGuides']).read_text())['arrays']))
    dense_faces = np.load(checked(prior['original47Geometry']))['faces']
    source_fields = np.zeros((len(compact['positions']), len(a['groupNames'])))
    offsets, indices, weights = (guides[k] for k in ('fieldOffsets', 'fieldIndices', 'fieldWeights'))
    for i, (face, bary) in enumerate(zip(compact['sourceTriangle'], compact['sourceBarycentric'])):
        for vertex, coefficient in zip(dense_faces[face], bary):
            lo, hi = offsets[vertex:vertex+2]
            source_fields[i, indices[lo:hi]] += coefficient*weights[lo:hi]
    parents, coefficients, points, uv, fields = [], [], [], [], []
    for p in new_points:
        face, bary, q, _, _ = surface.nearest(p)
        parents.append(triangles[face]); coefficients.append(bary); points.append(q)
        uv.append(bary@triangle_uv[face]); fields.append(bary@source_fields[triangles[face]])
    return compact, np.asarray(parents), np.asarray(coefficients), np.asarray(points), np.asarray(uv), np.asarray(fields)


def construct(prior, a, body, rest):
    names = a['groupNames'].tolist(); assert len(names) == 71
    bones = {r[0]: r for r in rest}; old_count = len(a['positions'])
    mesh = A['Mesh'](a); mesh.reference_positions = a['referencePositions'].tolist()
    mesh.roles = a['vertexRoles'].tolist(); mesh.faces = []; mesh.uvs = []; mesh.ancestry = []; mesh.face_roles = []
    wall_keys = []; prior_faces = []; remove = set(); old_rows = {}; loops = seam_loops(a); specifications = []
    for side in ('L', 'R'):
        ids = np.flatnonzero(np.char.endswith(a['vertexRoles'].astype(str), '_'+side))
        ids = ids[np.argsort(a['constructionVertexIds'][ids])]
        assert len(ids) == 63*48 and np.all(np.diff(a['constructionVertexIds'][ids]) == 1)
        old_rows[side] = ids.reshape(63, 48)
        # Remove the old six cap rows and first ordinary row on each wall.
        remove.update(ids.reshape(63, 48)[np.r_[0:7, 30:37]].ravel().tolist())
    old_wall = np.full(old_count, 'retained', dtype='<U12')
    for side, rows in old_rows.items():
        old_wall[rows[:30]] = side+':outer'; old_wall[rows[30:60]] = side+':inner'; old_wall[rows[60:]] = side+':rim'
    for fi, (start, count) in enumerate(zip(a['polygonStarts'], a['polygonCounts'])):
        ids = a['cornerVertexIds'][start:start+count]
        if any(int(v) in remove for v in ids):
            continue
        mesh.face(ids.tolist(), a['cornerUV'][start:start+count], int(a['sourceCompactFace'][fi]), str(a['faceRoles'][fi]))
        prior_faces.append(fi)
        wall_keys.append('retained' if a['faceRoles'][fi] == 'selected_retained' else str(old_wall[ids[-1]]))
    new_seams, new_us, new_wall = [], [], []
    def face(ids, role, wall):
        mesh.face(ids, np.zeros((len(ids), 2)), -1, role); wall_keys.append(wall); prior_faces.append(-1)
    for side, sign in (('L', 1), ('R', -1)):
        frame, _ = A['bone_frame'](rest, side)
        side_loops = [loop for loop in loops if np.all(a['positions'][loop, 0]*sign > 0)]
        assert len(side_loops) == 2
        # Actual old zipper incidences identify which retained loop owns each wall.
        for layer, label in enumerate(('outer', 'inner')):
            old_first = set(old_rows[side][layer*30].tolist()); joined = set()
            for start, count, role in zip(a['polygonStarts'], a['polygonCounts'], a['faceRoles']):
                if role != 'authored_armhole_'+side:
                    continue
                ids = a['cornerVertexIds'][start:start+count]
                if old_first.intersection(ids):
                    joined.update(int(v) for v in ids if a['vertexRoles'][v] == 'armhole_seam')
            loop = next(loop for loop in side_loops if set(loop.tolist()) == joined)
            loop, angles = increasing_loop(loop, a, frame); seam = a['positions'][loop]
            regular = old_rows[side][layer*30+6]
            columns = angles/(2*np.pi)*48; left = np.floor(columns).astype(int) % 48; fraction = columns-np.floor(columns)
            end = (1-fraction[:, None])*a['positions'][regular[left]]+fraction[:, None]*a['positions'][regular[(left+1)%48]]
            # Keep the actual fitted12 cap as a shape guide. Reparameterize
            # each existing ring in the real seam chart, then apply the cubic
            # endpoint correction that makes row0 the literal selected seam.
            # No new nearest-body projection or untested sculpt envelope.
            theta = np.arange(48)*2*np.pi/48
            extended = np.r_[angles[-1]-2*np.pi, angles, angles[0]+2*np.pi]
            xyz = np.concatenate((seam[-1:], seam, seam[:1]))
            sampled_seam = np.stack([np.interp(theta, extended, xyz[:, k]) for k in range(3)], axis=1)
            approximate = (1-fraction[:, None])*sampled_seam[left]+fraction[:, None]*sampled_seam[(left+1)%48]
            endpoint_correction = seam-approximate
            rows = [loop.tolist()]; wall = side+':'+label
            for ri, u in enumerate(CAP_U):
                old_ring = a['positions'][old_rows[side][layer*30+ri]]
                points = (1-fraction[:, None])*old_ring[left]+fraction[:, None]*old_ring[(left+1)%48]
                points += (2*u**3-3*u*u+1)*endpoint_correction
                if u == 1.:
                    assert np.array_equal(points, end)
                row = []
                for i, p in enumerate(points):
                    row.append(mesh.append(p, ('shoulder_cap_' if np.sin(angles[i]) > .15 else 'axilla_')+side))
                    new_seams.append(int(loop[i])); new_us.append(u); new_wall.append(wall)
                rows.append(row)
            for lo, hi in zip(rows, rows[1:]):
                for i in range(len(loop)):
                    j = (i+1) % len(loop)
                    face([lo[i], lo[j], hi[j], hi[i]], 'connected_cap_'+side, wall)
            # Zipper lives in a real23mm ordinary sleeve interval, not against
            # a separately resampled seam or a coincident duplicate ring.
            regular = old_rows[side][layer*30+7]
            theta = np.arange(48)*2*np.pi/48; i = j = 0
            while i < len(loop) or j < 48:
                ai, bj = rows[-1][i % len(loop)], int(regular[j % 48])
                na = angles[i+1] if i+1 < len(loop) else angles[0]+2*np.pi if i < len(loop) else np.inf
                nb = theta[j+1] if j+1 < 48 else 2*np.pi if j < 48 else np.inf
                if na < nb:
                    face([ai, rows[-1][(i+1) % len(loop)], bj], 'connected_arm_zipper_'+side, wall); i += 1
                else:
                    face([ai, int(regular[(j+1) % 48]), bj], 'connected_arm_zipper_'+side, wall); j += 1
            specifications.append({'side': side, 'wall': wall, 'prior12SeamLoop': loop.tolist(),
                'capRowsBeforeCompaction': rows[1:], 'ordinaryBoundaryBeforeCompaction': regular.tolist(),
                'terminalStationM': .145, 'ordinaryBoundaryStationM': .168, 'capParameters': CAP_U})
    mesh.orient_and_measure()
    new_points = np.asarray(mesh.positions[old_count:]); trunk = torso12(np.asarray(mesh.positions), names, rest)
    compact, parents, coefficients, appearance, preview, raw_fields = raw_appearance(a, prior, new_points)
    retained_uv = {}
    for ids, uv, role in zip(mesh.faces, mesh.uvs, mesh.face_roles):
        if role == 'selected_retained':
            for vi, value in zip(ids, uv):
                retained_uv.setdefault(vi, value)
    for fi, ids in enumerate(mesh.faces):
        if mesh.face_roles[fi].startswith('connected_'):
            # Retained source cornerUV remains exact. These new UVs are only
            # an actual selected-source preview, never atlas/cage evidence.
            mesh.uvs[fi] = [preview[v-old_count].tolist() if v >= old_count else retained_uv[v]
                           if v in retained_uv else a['cornerUV'][np.flatnonzero(a['cornerVertexIds'] == v)[0]].tolist()
                           for v in ids]
    fields = np.concatenate((a['namedFields'].astype(float), trunk[old_count:]))
    unknown = np.zeros(len(fields), bool); source = np.isin(np.asarray(mesh.roles), SOURCE_ROLES)
    p = np.asarray(mesh.positions); lower = float(bones['DEF-spine.002'][2][2]); collar = float(bones['DEF-spine.004'][2][2])
    for side, sign in (('L', 1), ('R', -1)):
        medial = float(sign*bones['DEF-shoulder.'+side][2][0])
        unknown |= source & (p[:, 0]*sign > medial) & (p[:, 2] > lower) & (p[:, 2] < collar)
        for row in old_rows[side][np.r_[7:30, 37:63]]:
            for vi in row:
                if a['authoredSkinBlend'][vi] < 1:
                    fields[vi] = A['limb_fields'](p[vi], side, rest, names)
    # Restrict the anatomical source box to actual retained surface components
    # that reach this shared seam; isolated source fragments stay exactly12.
    adjacent = defaultdict(set)
    for ids in mesh.faces:
        for i, j in zip(ids, ids[1:]+ids[:1]):
            if unknown[i] and unknown[j]:
                adjacent[i].add(j); adjacent[j].add(i)
    reached = set(); stack = [int(v) for loop in loops for v in loop if unknown[v]]
    while stack:
        vi = stack.pop()
        if vi in reached:
            continue
        reached.add(vi); stack.extend(adjacent[vi]-reached)
    unknown[:] = False; unknown[list(reached)] = True
    unknown[old_count:] = True
    surface = A['Surface'](body['positions'], body['triangles']); body_witness = []
    for spec in specifications:
        side = spec['side']; frame, _ = A['bone_frame'](rest, side); origin, axis, _, _ = frame(0)
        for vi in spec['prior12SeamLoop']:
            # The lower seam arc lies on the actual torso/arm attachment.
            # The upper shoulder continues through the same bounded solve.
            if unknown[vi] and (p[vi]-origin)@axis >= 0:
                fields[vi], witness = body_boundary(p[vi], side, 'torso', frame, bones, body, surface, names, trunk[vi])
                unknown[vi] = False; body_witness.append(dict(witness, vertexBeforeCompaction=vi))
        for vi in spec['capRowsBeforeCompaction'][-1]:
            fields[vi], witness = body_boundary(p[vi], side, 'arm', frame, bones, body, surface, names, trunk[vi])
            unknown[vi] = False; body_witness.append(dict(witness, vertexBeforeCompaction=vi))
    used = np.asarray(sorted({v for face in mesh.faces for v in face}), np.int32)
    remap = np.full(len(fields), -1, np.int32); remap[used] = np.arange(len(used))
    assert all(remap[v] >= 0 for v in (832, 1124)) and not unknown[832] and not unknown[1124]
    starts, counts, corners, uvs, corner_walls = [], [], [], [], []
    for ids, uv, wall in zip(mesh.faces, mesh.uvs, wall_keys):
        starts.append(len(corners)); counts.append(len(ids)); corners.extend(remap[ids]); uvs.extend(uv); corner_walls.extend([wall]*len(ids))
    result = {'positions': p[used], 'polygonStarts': np.asarray(starts, np.int32),
        'polygonCounts': np.asarray(counts, np.int32), 'cornerVertexIds': np.asarray(corners, np.int32),
        'cornerUV': np.asarray(uvs), 'polygonMaterialIds': np.asarray([a['polygonMaterialIds'][fi] if fi >= 0 else 0 for fi in prior_faces], np.int32),
        'prior12PolygonIds': np.asarray(prior_faces, np.int32),
        'sourceCompactFace': np.asarray(mesh.ancestry, np.int32), 'faceRoles': np.asarray(mesh.face_roles),
        'faceWallKey': np.asarray(wall_keys), 'cornerWallKey': np.asarray(corner_walls),
        'vertexRoles': np.asarray(mesh.roles)[used], 'groupNames': np.asarray(names),
        'referencePositions': np.asarray(mesh.reference_positions)[used],
        'sourceReceiverVertexIds': np.concatenate((a['sourceReceiverVertexIds'], parents))[used],
        'sourceReceiverCoefficients': np.concatenate((a['sourceReceiverCoefficients'], coefficients))[used],
        'sourceAppearancePoints': np.concatenate((a['sourceAppearancePoints'], appearance))[used],
        'selectedToReceiverDistanceM': np.concatenate((a['selectedToReceiverDistanceM'], np.linalg.norm(new_points-appearance, axis=1)))[used],
        'sourceOnlyNamedFields': np.concatenate((a['sourceOnlyNamedFields'], raw_fields.astype(np.float32)))[used],
        'authoredSkinBlend': np.concatenate((a['authoredSkinBlend'], np.asarray(new_us)))[used],
        'constructionVertexIds': np.concatenate((a['constructionVertexIds'], np.arange(len(new_points))+a['constructionVertexIds'].max()+1))[used],
        'prior12VertexIds': np.concatenate((np.arange(old_count), np.full(len(new_points), -1)))[used],
        'capSeamPrior12Vertex': np.concatenate((np.full(old_count, -1), new_seams))[used],
        'capParameter': np.concatenate((np.zeros(old_count), new_us))[used],
        'fieldUnknown': unknown[used], 'fieldBoundaryValues': fields[used].copy(),
        'vertexWallKey': np.concatenate((old_wall, new_wall))[used]}
    for spec in specifications:
        spec['capRows'] = remap[spec.pop('capRowsBeforeCompaction')].tolist()
        spec['ordinaryBoundary'] = remap[spec.pop('ordinaryBoundaryBeforeCompaction')].tolist()
        spec['seamLoop'] = remap[spec['prior12SeamLoop']].tolist()
    for witness in body_witness:
        witness['vertex'] = int(remap[witness.pop('vertexBeforeCompaction')])
    # Literal seam ancestry is independent from provisional new-cap nearest
    # appearance sampling. It can seed an independently qualified donor wall.
    seam_ids = np.asarray(new_seams); cap_ids = remap[np.arange(old_count, len(fields))]
    result['capVertexIds'] = cap_ids
    result['capSeamCompactParents'] = a['sourceReceiverVertexIds'][seam_ids]
    result['capSeamCompactCoefficients'] = a['sourceReceiverCoefficients'][seam_ids]
    result['capSeamDenseTriangles'] = compact['sourceTriangle'][result['capSeamCompactParents']]
    result['capSeamDenseBarycentric'] = compact['sourceBarycentric'][result['capSeamCompactParents']]
    return result, {'strips': specifications, 'bodyBoundarySamples': body_witness,
        'anatomicalBoundary': {'lowerChestZ': lower, 'collarZ': collar,
            'medialX': {s: abs(float(bones['DEF-shoulder.'+s][2][0])) for s in ('L', 'R')}},
        'topology': mesh.decisions[-1]['actualTopology'], 'original12VerticesRemoved': sorted(remove)}


def extend_fields(a):
    """One positive linear Dirichlet solve; no tuning loop or field diffusion family."""
    sys.path.insert(0, str(ROOT/'harness/out/rider-rebuild/selected-anatomical-hoodie-fit73/python'))
    from scipy.sparse import coo_matrix
    from scipy.sparse.linalg import spsolve
    _, _, neighbors = runpy.run_path(str(checked(GRAPH)))['graph'](a)
    active = a['fieldUnknown']; ids = np.flatnonzero(active); index = np.full(len(active), -1, np.int32); index[ids] = np.arange(len(ids))
    rows, columns, values = [], [], []; rhs = np.zeros((len(ids), len(a['groupNames'])))
    for i in ids:
        total = 0.
        for j, length in neighbors[i]:
            weight = 1/length; total += weight
            if active[j]:
                rows.append(index[i]); columns.append(index[j]); values.append(-weight)
            else:
                rhs[index[i]] += weight*a['fieldBoundaryValues'][j]
        rows.append(index[i]); columns.append(index[i]); values.append(total)
    matrix = coo_matrix((values, (rows, columns)), shape=(len(ids), len(ids))).tocsc()
    solved = spsolve(matrix, rhs)
    assert np.isfinite(solved).all() and solved.min() > -1e-12 and np.max(abs(solved.sum(1)-1)) < 2e-6
    residual = float(abs(matrix@solved-rhs).max())
    solved = np.maximum(solved, 0.); solved /= solved.sum(1)[:, None]
    fields = a['fieldBoundaryValues'].astype(np.float32); fields[ids] = solved.astype(np.float32)
    assert np.max(abs(fields.sum(1)-1)) < 3e-7
    for side, sign in (('L', 1), ('R', -1)):
        allowed = set(TRUNK)|{'DEF-shoulder.'+side}|{'DEF-'+p+'.'+side+t for p in ('upper_arm', 'forearm') for t in ('', '.001')}
        forbidden = [i for i, n in enumerate(a['groupNames']) if n not in allowed]
        assert np.all(fields[np.ix_(np.flatnonzero(a['positions'][:, 0]*sign > 0), forbidden)] == 0)
    a['namedFields'] = fields
    return {'linearSolveCount': 1, 'unknownVertices': len(ids), 'maximumLinearResidual': residual,
            'conductance': 'Positive inverse actual edge length; all71 fields share one matrix',
            'fieldMinimum': float(fields.min()), 'maximumRowSumError': float(abs(fields.sum(1)-1).max())}


def verify(receipt_path):
    row = json.loads(Path(receipt_path).read_text()); binding = row['connectedCapBinding']
    assert binding['recipe'] == pin(__file__) and binding['input'] == INPUT and binding['bodyGuide'] == BODY
    assert row['acceptedArt'] is False and binding['status'] == 'CONNECTED_CAP_ANATOMICAL_LINEAR_FIELD_UNACCEPTED'
    before = np.load(checked(json.loads(checked(INPUT).read_text())['receiver'])); after = np.load(checked(row['receiver']))
    retained = after['prior12VertexIds'] >= 0; ids = after['prior12VertexIds'][retained]
    assert np.array_equal(after['positions'][retained], before['positions'][ids])
    assert np.array_equal(after['sourceReceiverVertexIds'][retained], before['sourceReceiverVertexIds'][ids])
    for fi, old in enumerate(after['prior12PolygonIds']):
        if old < 0:
            continue
        start, count = after['polygonStarts'][fi], after['polygonCounts'][fi]
        old_start, old_count = before['polygonStarts'][old], before['polygonCounts'][old]
        assert count == old_count
        assert np.array_equal(after['prior12VertexIds'][after['cornerVertexIds'][start:start+count]],
                              before['cornerVertexIds'][old_start:old_start+old_count])
        assert np.array_equal(after['cornerUV'][start:start+count], before['cornerUV'][old_start:old_start+old_count])
        assert after['polygonMaterialIds'][fi] == before['polygonMaterialIds'][old]
    assert np.isfinite(after['namedFields']).all() and after['namedFields'].min() >= 0
    assert after['namedFields'].dtype == np.float32 and len(after['groupNames']) == 71
    assert np.max(abs(after['namedFields'].sum(1)-1)) < 3e-7
    fixed = ~after['fieldUnknown']
    assert np.array_equal(after['namedFields'][fixed], after['fieldBoundaryValues'][fixed].astype(np.float32))
    for vi in (832, 1124):
        new = int(np.flatnonzero(after['prior12VertexIds'] == vi)[0])
        assert np.array_equal(after['namedFields'][new], before['namedFields'][vi])
    hood = before['wholeAnatomicalHoodCollar'][ids]
    assert np.array_equal(after['namedFields'][retained][hood], before['namedFields'][ids[hood]])
    checked(binding['construction']); checked(row['editableOBJ'])
    return row


def main(output):
    output = Path(output).resolve()
    assert output.is_relative_to(ROOT/'harness/out/rider-rebuild/selected-hoodie-joints77') and not output.exists()
    prior, before, body_receipt, body, rest = inputs()
    arrays, construction = construct(prior, before, body, rest)
    construction['linearField'] = extend_fields(arrays)
    construction.update(recipe=pin(__file__), input=INPUT, bodyGuide=BODY, acceptedArt=False,
        sourceWallDomainsQualified=False, genuineBakeAtlasPresent=False,
        appearance='New cap raw nearest selected76 samples are preview provenance only; NOT qualified same-wall cage correspondence.',
        anatomicalField='Actual47 spine-origin seam and arm-origin terminal first-wall ownership;12 torso residual; one bounded positive full-field extension.')
    output.mkdir(parents=True); np.savez(output/'receiver.npz', **arrays)
    (output/'connected-cap.json').write_text(json.dumps(construction, indent=2)+'\n')
    with (output/'selected-hoodie-connected-cap.obj').open('w') as stream:
        stream.write('# UNACCEPTED selected connected cap; native/contact/bake/motion pending\n')
        for p in arrays['positions']: stream.write('v %.10g %.10g %.10g\n'%tuple(p))
        for uv in arrays['cornerUV']: stream.write('vt %.10g %.10g\n'%tuple(uv))
        for start, count in zip(arrays['polygonStarts'], arrays['polygonCounts']):
            stream.write('f '+' '.join(f'{arrays["cornerVertexIds"][i]+1}/{i+1}' for i in range(start, start+count))+'\n')
    row = {k: prior[k] for k in ('status', 'acceptedArt', 'recipe', 'sourceReceiver', 'source47Receipt', 'fullBody', 'original47Geometry', 'actualGuides')}
    row.update(receiver=pin(output/'receiver.npz'), editableOBJ=pin(output/'selected-hoodie-connected-cap.obj'),
        construction=pin(output/'connected-cap.json'), topology=construction['topology'],
        connectedCapBinding={'status': 'CONNECTED_CAP_ANATOMICAL_LINEAR_FIELD_UNACCEPTED', 'recipe': pin(__file__),
            'input': INPUT, 'bodyGuide': BODY, 'construction': pin(output/'connected-cap.json')},
        correspondenceAndSkin={'fullNamedFieldCount': 71, 'healthyFieldsExactBeforeFloat32': False,
            'sourceFarFieldAnchorsExact': False, 'farTrunk12FieldsExact': True,
            'skinStatus': construction['anatomicalField'], 'productionFourConditioned': False},
        detailBakePassed=False, posedContactPassed=False, nativeSaved=False, movingArtPassed=False, genuineBakeAtlasPresent=False,
        limitations=['New conforming cap geometry and one field solve are unaccepted; whole482/native finite contact and played review remain required.',
            'Original12 retained positions/cornerUV and far trunk/down hood are preserved. Old cap vertices are retired with explicit prior identity.',
            'Raw selected appearance samples are not same-wall bake authority; genuine atlas, independently identified dense wall domains and bake remain pending.'])
    (output/'receiver.json').write_text(json.dumps(row, indent=2)+'\n'); verify(output/'receiver.json')
    print(json.dumps({'status': row['connectedCapBinding']['status'], 'vertices': len(arrays['positions']),
        'topology': row['topology'], 'linearField': construction['linearField']}), flush=True)


if __name__ == '__main__':
    main(sys.argv[1])
