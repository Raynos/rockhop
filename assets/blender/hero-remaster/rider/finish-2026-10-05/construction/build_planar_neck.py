"""One canonical neck restoration and planar monotone-angle join.

Explicit source triangles avoid n-gon caches. No source original, rig, facial,
shoulder/hip or boxer change; an unaccepted source construction only.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.geometry import tessellate_polygon

owned = Path(__file__).resolve().parent
root = owned.parents[5]
out = owned / 'body05'
evidence = root / 'docs/evidence/hero-remaster/finish-2026-10-05/construction/body05'
native = out / 'natural-foundation.blend'
assert not native.exists(), 'Never overwrite an executed candidate'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
source = owned / 'body04d/natural-foundation.blend'
assert sha(source) == '7c364bea92384c5562b28088454afcc208fe4f3dc46a5ffd98c4a51588543d66'
f0_path = evidence.parent / 'foundation-source.npz'
assert sha(f0_path) == 'b6eaa2ccee77a9e6f6395daa1fc473da3f6099f26f79895f288e1300b3fba3ae'
f0 = np.load(f0_path)
registry = root / 'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/neck-interface96/ordered-boundaries.npz'
r = np.load(registry)
bpy.ops.wm.open_mainfile(filepath=str(source))
bpy.context.window.scene = bpy.data.scenes['Finish natural wearer diagnostic']
rig = bpy.data.objects['Finish rig']
names = [b.name for b in rig.data.bones]
assert names == f0['boneNames'].tolist()
head = bpy.data.objects['Protected textured head above hidden neck interface']
body = bpy.data.objects['Canonical body with hidden head interface']
hp, bp = f0['headXYZ'], f0['displayBodyXYZ']
alias = r['headPositionAlias']
cut = np.float32(1.575)
allowed = set(map(int, f0['headEditableIDs']))
upper_incident = set(map(int, f0['headUpperIncidentTriangles']))
positions = hp.tolist()
point_refs = [(i, i, 0.) for i in range(len(hp))]
cut_keys = {}
physical_cut = {}
polygons, corner_refs, polygon_sources = [], [], []
boundary = {}
touched, removed = [], []

def intersection(v, w):
    rawkey = tuple(sorted((int(v), int(w))))
    if rawkey not in cut_keys:
        a, b = rawkey
        fraction = float((float(cut) - hp[a, 2]) / (hp[b, 2] - hp[a, 2]))
        virtualkey = tuple(sorted((int(alias[a]), int(alias[b]))))
        if virtualkey not in physical_cut:
            p = ((1 - fraction) * hp[a].astype(float) + fraction * hp[b].astype(float)).astype(np.float32)
            p[2] = cut
            physical_cut[virtualkey] = p
        vid = len(positions)
        positions.append(physical_cut[virtualkey].tolist())
        point_refs.append((a, b, fraction))
        cut_keys[rawkey] = (vid, virtualkey)
    return cut_keys[rawkey][0]

for poly in head.data.polygons:
    ids, loops = list(poly.vertices), list(poly.loop_indices)
    assert len(ids) == 3
    lower = hp[ids, 2] < cut
    if not np.any(lower):
        polygons.append(ids)
        corner_refs.extend((i, i, 0.) for i in loops)
        polygon_sources.append(poly.index)
        continue
    assert set(ids) <= allowed and poly.index not in upper_incident
    touched.append(poly.index)
    if np.all(lower):
        removed.append(poly.index)
        continue
    clipped, refs = [], []
    for i, v in enumerate(ids):
        w = ids[(i + 1) % 3]
        lv, lw = loops[i], loops[(i + 1) % 3]
        if hp[v, 2] >= cut:
            clipped.append(v)
            refs.append((lv, lv, 0.))
        if (hp[v, 2] < cut) != (hp[w, 2] < cut):
            fraction = float((float(cut) - hp[v, 2]) / (hp[w, 2] - hp[v, 2]))
            clipped.append(intersection(v, w))
            refs.append((lv, lw, fraction))
    assert len(clipped) in [3, 4]
    # Explicit source-triangle fan; no four-corner cache is authoritative.
    anchor = next(i for i, v in enumerate(clipped) if v < len(hp))
    clipped = clipped[anchor:] + clipped[:anchor]
    refs = refs[anchor:] + refs[:anchor]
    for i in range(1, len(clipped) - 1):
        polygons.append([clipped[0], clipped[i], clipped[i + 1]])
        corner_refs.extend([refs[0], refs[i], refs[i + 1]])
        polygon_sources.append(poly.index)
    for v, w in zip(clipped, clipped[1:] + clipped[:1]):
        if v >= len(hp) and w >= len(hp):
            kv = tuple(sorted(map(int, alias[list(point_refs[v][:2])])) )
            kw = tuple(sorted(map(int, alias[list(point_refs[w][:2])])) )
            boundary.setdefault(kv, []).append((kw, v, w))
# Geometrically welded cut loops; source UV aliases remain separate native IDs.
adj = defaultdict(set)
representative = {}
for v, edges in boundary.items():
    for w, rawv, raww in edges:
        adj[v].add(w); adj[w].add(v)
        representative.setdefault(v, rawv); representative.setdefault(w, raww)
assert len(adj) == 616 and all(len(v) == 2 for v in adj.values())
seen, rings = set(), []
for first in adj:
    if first in seen:
        continue
    ring, previous, current = [], None, first
    while current not in seen:
        seen.add(current); ring.append(representative[current])
        nxt = sorted(adj[current] - ({previous} if previous else set()))[0]
        previous, current = current, nxt
    assert current == first
    rings.append(np.array(ring, np.int32))
assert sorted(map(len, rings)) == [303, 313]
# Outer ring encloses the inner at this declared cut; no nearest-shell guessing.
ring_area = lambda ids: .5 * np.sum(np.array(positions)[ids, 0] * np.roll(np.array(positions)[ids, 1], -1) - np.array(positions)[ids, 1] * np.roll(np.array(positions)[ids, 0], -1))
rings.sort(key=lambda ids: abs(ring_area(ids)), reverse=True)
outer, inner = rings
assert len(outer) == 313 and len(inner) == 303

contract_path = evidence / 'planar-neck-contract.json'
assert sha(contract_path) == 'c2d1faface9db788098bdac4f3d8a4f52cd3ceceec830150be47fdf0e1b07394'
contract = json.loads(contract_path.read_text())
for path, digest in contract['sourcePins'].items():
    assert sha(root / path) == digest, path
full_path = root / 'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/body52/native-fields.npz'
full_source = np.load(full_path)
canonical = bpy.data.objects['Canonical anatomical body, baked adult hm08']
cp = f0['canonicalXYZ']
ct = f0['canonicalTriangles']
source_ids = full_source['renderedBodySourceIDs'].astype(int)
assert np.array_equal(cp, full_source['originalFullXYZ'])
assert np.array_equal(bp, cp[source_ids])
canonical.data.calc_loop_triangles()
actual_ct = np.array([t.vertices[:] for t in canonical.data.loop_triangles], np.int32)
assert np.array_equal(actual_ct, ct), 'Canonical source evaluated triangle diagonal contract changed'
canonical_loops = np.array([t.loops[:] for t in canonical.data.loop_triangles], np.int32)
canonical_polys = np.array([t.polygon_index for t in canonical.data.loop_triangles], np.int32)
canonical_map = {tuple(sorted(map(int, x))): i for i, x in enumerate(ct)}
body_original_ctids = np.array([canonical_map[tuple(sorted(map(int, x)))] for x in source_ids[f0['displayBodyTriangles']]], int)
body_cut = np.float32(contract['repairGeometry']['bodyCutNativeZ'])
bpositions = bp.tolist()
bpoint_refs = [(int(v), int(v), 0.) for v in source_ids]
canonical_to_body = {int(v): i for i, v in enumerate(source_ids)}
bfull = list(full_source['originalFullWeights'][source_ids].copy())
bfour = list(f0['displayBodyWeights'].copy())
breference_full = list(np.array(bfull).copy())
breference_four = list(np.array(bfour).copy())
bpolygons, bcorner_refs, bpoly_sources, btriangle_sources = [], [], [], []
bcut_edges, bcut_points, badj = {}, {}, defaultdict(set)

def body_vertex(v):
    v = int(v)
    if v not in canonical_to_body:
        index = len(bpositions); canonical_to_body[v] = index
        bpositions.append(cp[v].tolist()); bpoint_refs.append((v, v, 0.))
        bfull.append(full_source['originalFullWeights'][v].copy())
        bfour.append(f0['canonicalWeights'][v].copy())
        breference_full.append(bfull[-1].copy()); breference_four.append(bfour[-1].copy())
    return canonical_to_body[v]

def semantic_base(raw, p):
    side = 'R' if p[1] >= 0 else 'L'
    w = np.zeros(51, np.float32)
    for name in ['chest', 'neck', 'shoulder.' + side, 'upperArm.' + side]:
        w[names.index(name)] = raw[names.index(name)]
    # All unselected attachment mass is explicitly routed into chest/neck,
    # rather than discarded by a strongest-four list.
    w[names.index('neck')] += raw[names.index('head')]
    accounted = w.sum()
    w[names.index('chest')] += max(0., float(raw.sum() - accounted))
    w /= w.sum()
    assert np.count_nonzero(w) <= 4
    return w

def body_intersection(a, b):
    key = tuple(sorted((int(a), int(b))))
    if key not in bcut_edges:
        a, b = key
        t = float((float(body_cut) - cp[a, 2]) / (cp[b, 2] - cp[a, 2]))
        p = ((1 - t) * cp[a].astype(float) + t * cp[b].astype(float)).astype(np.float32)
        p[2] = body_cut
        index = len(bpositions); bpositions.append(p.tolist()); bpoint_refs.append((a, b, t))
        rwf = ((1 - t) * full_source['originalFullWeights'][a] + t * full_source['originalFullWeights'][b]).astype(np.float32)
        rw4 = ((1 - t) * f0['canonicalWeights'][a] + t * f0['canonicalWeights'][b]).astype(np.float32)
        w = semantic_base(rw4, p)
        bfull.append(w.copy()); bfour.append(w.copy())
        breference_full.append(rwf); breference_four.append(rw4)
        bcut_edges[key] = index; bcut_points[index] = key
    return bcut_edges[key]

included = list(body_original_ctids) + contract['repairGeometry']['additionalWholeCanonicalTriangleIDs'] + contract['repairGeometry']['additionalCrossPlaneCanonicalTriangleIDs']
for tid in included:
    ids, loops = ct[tid], canonical_loops[tid]
    above = cp[ids, 2] > body_cut
    if not np.any(above):
        face = [body_vertex(v) for v in ids]
        bpolygons.append(face); bcorner_refs.extend((int(i), int(i), 0.) for i in loops)
        bpoly_sources.append(int(canonical_polys[tid])); btriangle_sources.append(int(tid))
        continue
    assert not np.all(above)
    clipped, refs = [], []
    for i, v in enumerate(ids):
        w = ids[(i + 1) % 3]; lv, lw = int(loops[i]), int(loops[(i + 1) % 3])
        if cp[v, 2] <= body_cut:
            clipped.append(body_vertex(v)); refs.append((lv, lv, 0.))
        if (cp[v, 2] > body_cut) != (cp[w, 2] > body_cut):
            t = float((float(body_cut) - cp[v, 2]) / (cp[w, 2] - cp[v, 2]))
            clipped.append(body_intersection(v, w)); refs.append((lv, lw, t))
    cut_ids = [v for v in clipped if v in bcut_points]
    assert len(cut_ids) == 2
    a, b = cut_ids; badj[a].add(b); badj[b].add(a)
    anchor = next(i for i, v in enumerate(clipped) if v not in bcut_points)
    clipped = clipped[anchor:] + clipped[:anchor]; refs = refs[anchor:] + refs[:anchor]
    for i in range(1, len(clipped) - 1):
        bpolygons.append([clipped[0], clipped[i], clipped[i + 1]])
        bcorner_refs.extend([refs[0], refs[i], refs[i + 1]])
        bpoly_sources.append(int(canonical_polys[tid])); btriangle_sources.append(int(tid))
assert len(badj) == 104 and all(len(x) == 2 for x in badj.values())
first = next(iter(badj)); seen = set(); body_ring = []; previous = None; current = first
while current not in seen:
    seen.add(current); body_ring.append(current)
    nxt = sorted(badj[current] - ({previous} if previous is not None else set()))[0]
    previous, current = current, nxt
assert current == first and len(seen) == len(badj)

origin = np.array([.035, 0.])
def angle_order(ids, xyz):
    ids = np.array(ids, np.int32); xy = np.array(xyz)[ids, :2]
    area = np.sum(xy[:, 0] * np.roll(xy[:, 1], -1) - xy[:, 1] * np.roll(xy[:, 0], -1))
    if area < 0: ids = ids[::-1]
    angles = np.mod(np.arctan2(np.array(xyz)[ids, 1], np.array(xyz)[ids, 0] - origin[0]), 2 * np.pi)
    k = int(np.argmin(angles)); ids = np.roll(ids, -k); angles = np.roll(angles, -k)
    assert np.all(np.diff(np.r_[angles, angles[0] + 2 * np.pi]) > 0), 'Section must be strictly star-shaped about frozen origin'
    return ids, angles

outer, ha = angle_order(outer, positions)
body_ring, ba = angle_order(body_ring, bpositions)
common = np.unique(np.r_[ha, ba])

def ray_segment(theta, ring, angles, xyz):
    i = int(np.searchsorted(angles, theta, side='right') - 1) % len(ring)
    a, b = int(ring[i]), int(ring[(i + 1) % len(ring)])
    xy = np.array(xyz, float)[[a, b], :2]
    direction = np.array([np.cos(theta), np.sin(theta)])
    edge = xy[1] - xy[0]
    cross2 = lambda u, v: u[0] * v[1] - u[1] * v[0]
    fraction = cross2(origin - xy[0], direction) / cross2(edge, direction)
    assert -1e-10 <= fraction <= 1 + 1e-10, (theta, fraction)
    fraction = min(max(float(fraction), 0.), 1.)
    point = (1 - fraction) * np.array(xyz[a], float) + fraction * np.array(xyz[b], float)
    return point, a, b, fraction

head_full, head_four = list(f0['headWeights'].copy()), list(f0['headWeights'].copy())
for a, b, t in point_refs[len(hp):]:
    w = ((1 - t) * f0['headWeights'][a] + t * f0['headWeights'][b]).astype(np.float32)
    assert set(np.flatnonzero(w)) <= {names.index('head'), names.index('neck')}
    w /= w.sum(); head_full.append(w.copy()); head_four.append(w.copy())
head_seam = [-1] * len(positions)
loft_uv_refs = {}
loft = []
for level in np.linspace(0., 1., 7)[1:-1]:
    ids = []
    for theta in common:
        top, a, b, t = ray_segment(theta, outer, ha, positions)
        bottom, c, d, u = ray_segment(theta, body_ring, ba, bpositions)
        point = ((1 - level) * top + level * bottom).astype(np.float32)
        point[2] = np.float32((1 - level) * float(cut) + level * float(body_cut))
        index = len(positions); positions.append(point.tolist()); point_refs.append((-1, -1, 0.)); head_seam.append(-1); ids.append(index)
        loft_uv_refs[index] = (a, b, t)
        base_w = semantic_base(((1 - u) * bfour[c] + u * bfour[d]).astype(np.float32), bottom)
        arm = np.clip((level - .55) / .45, 0., 1.); arm = arm ** 3 * (10 - 15 * arm + 6 * arm ** 2)
        w = base_w.copy()
        for name in ['shoulder.R', 'shoulder.L', 'upperArm.R', 'upperArm.L']:
            w[names.index('neck')] += w[names.index(name)] * (1 - arm)
            w[names.index(name)] *= arm
        h = np.clip((.55 - level) / .55, 0., 1.); h = h ** 3 * (10 - 15 * h + 6 * h ** 2)
        w = (1 - h) * w + h * ((1 - t) * head_four[a] + t * head_four[b])
        w /= w.sum(); assert np.count_nonzero(w) <= 4
        head_full.append(w.copy()); head_four.append(w.copy())
    loft.append(np.array(ids, np.int32))
# The final head ring uses the actual body104 vertices, with exact seam fields.
last = []
for sid, v in enumerate(body_ring):
    index = len(positions); positions.append(bpositions[v]); point_refs.append((-1, -1, 0.)); head_seam.append(sid); last.append(index)
    top, a, b, t = ray_segment(ba[sid], outer, ha, positions)
    loft_uv_refs[index] = (a, b, t)
    head_full.append(bfour[v].copy()); head_four.append(bfour[v].copy())
loft.append(np.array(last, np.int32))

def bridge(a, aa, b, bb):
    i = j = 0
    while i < len(a) or j < len(b):
        theta_a = aa[i + 1] if i + 1 < len(a) else aa[0] + 2 * np.pi
        theta_b = bb[j + 1] if j + 1 < len(b) else bb[0] + 2 * np.pi
        va, vb = int(a[i % len(a)]), int(b[j % len(b)])
        if i < len(a) and (j >= len(b) or theta_a <= theta_b):
            face = [va, vb, int(a[(i + 1) % len(a)])]; i += 1
        else:
            face = [va, vb, int(b[(j + 1) % len(b)])]; j += 1
        polygons.append(face); corner_refs.extend([(-1, -1, 0.)] * 3); polygon_sources.append(-1)
bridge(outer, ha, loft[0], common)
for a, b in zip(loft[:-1], loft[1:-1]): bridge(a, common, b, common)
bridge(loft[-2], common, loft[-1], ba)
if ring_area(inner) < 0: inner = inner[::-1]
inner_vectors = [Vector(positions[i]) for i in inner]
# Explicit integer-index triangles from the verified installed Blender API.
for triangle in tessellate_polygon([inner_vectors]):
    polygons.append([int(inner[int(v)]) for v in triangle]); corner_refs.extend([(-1, -1, 0.)] * 3); polygon_sources.append(-1)

# Every intended section has positive angular increments and a fixed Z plane.
sections = []
for ids in loft:
    ordered_ids, angles = angle_order(ids, positions)
    assert np.array_equal(ordered_ids, ids)
    p = np.array(positions, np.float32)[ids]
    assert np.ptp(p[:, 2]) == 0
    sections.append({'vertices': len(ids), 'z': float(p[0, 2]), 'minimumAngularIncrement': float(np.diff(np.r_[angles, angles[0] + 2 * np.pi]).min())})
assert np.max(np.array(bpositions, np.float32)[np.unique(np.array(bpolygons)), 2]) <= body_cut
assert np.min(np.array(positions, np.float32)[np.unique(np.array(polygons)), 2]) >= body_cut

TYPE = {'FLOAT': ('value', 1, np.float32), 'INT': ('value', 1, np.int32), 'BOOLEAN': ('value', 1, np.bool_), 'FLOAT2': ('vector', 2, np.float32), 'FLOAT_VECTOR': ('vector', 3, np.float32), 'FLOAT_COLOR': ('color', 4, np.float32), 'BYTE_COLOR': ('color', 4, np.float32), 'INT32_2D': ('value', 2, np.int32), 'INT16_2D': ('value', 2, np.int32)}
arrays = {'boneNames': np.array(names), 'commonTheta': common, 'bodyPlaneCutNativeIDs': body_ring, 'headOuterCutNativeIDs': outer, 'headInnerCutNativeIDs': inner,
          'bodyCanonicalReferenceFullWeights': np.array(breference_full, np.float32), 'bodyCanonicalReferenceFourWeights': np.array(breference_four, np.float32),
          'bodyOriginalDisplayCanonicalIDs': source_ids, 'bodyCanonicalOriginalTriangleIDs': body_original_ctids,
          'bodyWholeRestorationCanonicalTriangleIDs': np.array(contract['repairGeometry']['additionalWholeCanonicalTriangleIDs']),
          'bodyClippedRestorationCanonicalTriangleIDs': np.array(contract['repairGeometry']['additionalCrossPlaneCanonicalTriangleIDs'])}
normal_report = {}
for key, src, pos, faces, pr, cr, ps, wf, w4 in [
    ('head', head, positions, polygons, point_refs, corner_refs, polygon_sources, head_full, head_four),
    ('body', canonical, bpositions, bpolygons, bpoint_refs, bcorner_refs, bpoly_sources, bfull, bfour)]:
    assert all(len(face) == 3 for face in faces)
    xyz = np.array(pos, np.float32); triangles = np.array(faces, np.int32)
    area2 = np.linalg.norm(np.cross(xyz[triangles[:, 1]].astype(float) - xyz[triangles[:, 0]], xyz[triangles[:, 2]].astype(float) - xyz[triangles[:, 0]]), axis=1)
    assert np.all(area2 > 1e-14), (key, 'Degenerate explicit triangle', np.flatnonzero(area2 <= 1e-14).tolist())
    mesh = bpy.data.meshes.new('Finish planar ' + key)
    mesh.from_pydata(pos, [], faces); mesh.update()
    for material in src.data.materials: mesh.materials.append(material)
    for poly, source_poly in zip(mesh.polygons, ps):
        poly.material_index = src.data.polygons[source_poly].material_index if source_poly >= 0 else 0
        poly.use_smooth = src.data.polygons[source_poly].use_smooth if source_poly >= 0 else True
    for attr in src.data.attributes:
        if attr.name in ['position', '.corner_vert', '.corner_edge', '.edge_verts', 'custom_normal']:
            continue
        assert attr.data_type in TYPE, (attr.name, attr.data_type)
        prop, width, dtype = TYPE[attr.data_type]
        values = np.empty(len(attr.data) * width, dtype); attr.data.foreach_get(prop, values); values = values.reshape(-1, width)
        dest = mesh.attributes.get(attr.name) or mesh.attributes.new(attr.name, attr.data_type, attr.domain)
        dv = np.zeros((len(dest.data), width), dtype)
        if attr.domain in ['POINT', 'CORNER']:
            for i, (a, b, t) in enumerate(pr if attr.domain == 'POINT' else cr):
                if a >= 0:
                    dv[i] = (1 - t) * values[a] + t * values[b] if np.issubdtype(dtype, np.floating) else values[a]
                elif np.issubdtype(dtype, np.integer): dv[i] = -1
        elif attr.domain == 'FACE':
            for i, source_poly in enumerate(ps):
                if source_poly >= 0: dv[i] = values[source_poly]
        elif attr.domain == 'EDGE':
            # Derivative edge flags are explicit defaults. Source EDGE identity
            # is not claimed across canonical/source index maps.
            pass
        else: raise AssertionError(attr.domain)
        if key == 'head' and attr.domain == 'CORNER' and attr.data_type == 'FLOAT2':
            point_uv = np.zeros((len(pos), 2), np.float32)
            first_corner = {}
            for loop in src.data.loops: first_corner.setdefault(loop.vertex_index, loop.index)
            for i in range(len(src.data.vertices)): point_uv[i] = values[first_corner[i]]
            for i, (a, b, t) in enumerate(pr[len(src.data.vertices):], len(src.data.vertices)):
                if a >= 0: point_uv[i] = (1 - t) * point_uv[a] + t * point_uv[b]
            for i, (a, b, t) in loft_uv_refs.items(): point_uv[i] = (1 - t) * point_uv[a] + t * point_uv[b]
            for loop in mesh.loops:
                if cr[loop.index][0] < 0: dv[loop.index] = point_uv[loop.vertex_index]
            arrays['headDerivedCornerUV_' + attr.name] = dv.copy()
        dest.data.foreach_set(prop, dv.ravel())
    mesh.update()
    src_normals = np.array([x.vector[:] for x in src.data.corner_normals], np.float32)
    desired = np.array([x.vector[:] for x in mesh.corner_normals], np.float32)
    refs = np.array(cr); source_corner = refs[:, 0].astype(int); valid = source_corner >= 0
    for i in np.flatnonzero(valid):
        a, b, t = cr[i]; vector = (1 - t) * src_normals[a] + t * src_normals[b]
        desired[i] = vector / np.linalg.norm(vector)
    protected_mask = valid.copy()
    if key == 'head':
        protected_mask[valid] = np.isin(f0['headCornerVertexIDs'][source_corner[valid]], f0['headProtectedIDs'])
        desired[protected_mask] = f0['headCornerNormals'][source_corner[protected_mask]]
    mesh.normals_split_custom_set(desired.tolist())
    if key == 'head':
        attr = mesh.attributes['custom_normal']; packed = np.empty(len(attr.data) * 2, np.int32); attr.data.foreach_get('value', packed); packed = packed.reshape(-1, 2)
        packed[protected_mask] = f0['headRawCustomNormals'][source_corner[protected_mask]]
        attr.data.foreach_set('value', packed.ravel()); mesh.update()
        decoded = np.array([x.vector[:] for x in mesh.corner_normals], np.float32)
        source_protected = np.flatnonzero(np.isin(f0['headCornerVertexIDs'], f0['headProtectedIDs']))
        assert np.array_equal(np.sort(source_corner[protected_mask]), source_protected)
        normal_report = {'protectedCorners': int(protected_mask.sum()), 'everyOriginalProtectedCornerExactlyOnce': True,
                         'changedProtectedCorners': int(np.any(decoded[protected_mask] != f0['headCornerNormals'][source_corner[protected_mask]], axis=1).sum()),
                         'maximumProtectedDelta': float(np.max(np.linalg.norm(decoded[protected_mask] - f0['headCornerNormals'][source_corner[protected_mask]], axis=1))),
                         'protectedRawPackedExact': bool(np.array_equal(packed[protected_mask], f0['headRawCustomNormals'][source_corner[protected_mask]]))}
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / 'pre-save-normal-check.json').write_text(json.dumps(normal_report, indent=2) + '\n')
        assert normal_report['changedProtectedCorners'] == 0 and normal_report['protectedRawPackedExact']
    for label, field in [('FULL', wf), ('FOUR', w4)]:
        candidate = bpy.data.objects['Finish ' + key + ' ' + label]
        candidate.data = mesh.copy(); candidate.vertex_groups.clear()
        for group in src.vertex_groups: candidate.vertex_groups.new(name=group.name)
        for name in names:
            if candidate.vertex_groups.get(name) is None: candidate.vertex_groups.new(name=name)
        for i, (a, b, t) in enumerate(pr):
            if a >= 0:
                for group in src.data.vertices[a].groups:
                    name = src.vertex_groups[group.group].name
                    if name not in names: candidate.vertex_groups[name].add([i], group.weight, 'REPLACE')
        for i, row in enumerate(field):
            for j in np.flatnonzero(np.array(row) > 0): candidate.vertex_groups[names[j]].add([i], float(row[j]), 'REPLACE')
        read = np.zeros((len(pos), 51), np.float32)
        for vertex in candidate.data.vertices:
            for group in vertex.groups:
                name = candidate.vertex_groups[group.group].name
                if name in names: read[vertex.index, names.index(name)] = group.weight
        assert np.array_equal(read, np.array(field, np.float32))
        for name, values in [('_NATIVE_ID', np.arange(len(pos), dtype=np.int32)), ('_SOURCE_ID', np.array([a if a == b and a >= 0 else -1 for a, b, t in pr], np.int32))]:
            if candidate.data.attributes.get(name): candidate.data.attributes.remove(candidate.data.attributes[name])
            attr = candidate.data.attributes.new(name, 'INT', 'POINT'); attr.data.foreach_set('value', values)
        candidate.data.update(); candidate.data.calc_loop_triangles()
        actual = np.array([t.vertices[:] for t in candidate.data.loop_triangles], np.int32)
        assert np.array_equal(actual, triangles), (key, label, 'Explicit triangle parity')
    arrays.update({key + 'RestXYZ': xyz, key + 'Triangles': triangles, key + 'FullWeights': np.array(wf, np.float32), key + 'FourWeights': np.array(w4, np.float32),
                   key + 'AttributeEdgeSources': np.array(pr), key + 'CornerAttributeEdgeSources': np.array(cr), key + 'TriangleSourcePolygonIDs': np.array(ps, np.int32),
                   key + 'MinimumTriangleArea2': np.array(area2.min()), key + 'UnusedNativeIDs': np.setdiff1d(np.arange(len(xyz)), np.unique(triangles))})
    assert np.max((np.array(w4) > 0).sum(axis=1)) <= 4
    assert np.max(np.abs(np.array(w4).sum(axis=1) - 1.)) <= 1e-6
arrays['bodyCanonicalTriangleAncestry'] = np.array(btriangle_sources, np.int32)
arrays['bodySeamPhysicalIDs'] = np.full(len(bpositions), -1, np.int32)
arrays['bodySeamPhysicalIDs'][body_ring] = np.arange(len(body_ring))
arrays['headSeamPhysicalIDs'] = np.array(head_seam, np.int32)
assert np.array_equal(arrays['bodyRestXYZ'][:len(bp)], bp)
assert np.array_equal(arrays['bodyFullWeights'][:len(bp)], full_source['originalFullWeights'][source_ids])
assert np.array_equal(arrays['bodyFourWeights'][:len(bp)], f0['displayBodyWeights'])
assert np.array_equal(arrays['headRestXYZ'][:len(hp)], hp)
out.mkdir(parents=True, exist_ok=True); evidence.mkdir(parents=True, exist_ok=True)
np.savez_compressed(out / 'authored-neck-fields.npz', **arrays)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
report = {'status': 'UNACCEPTED_BODY05_PLANAR_NECK_REQUIRES_QA', 'sourceSHA256': sha(source), 'contractSHA256': sha(contract_path), 'recipeSHA256': sha(__file__),
          'native': str(native.relative_to(root)), 'nativeSHA256': sha(native), 'fieldsSHA256': sha(out / 'authored-neck-fields.npz'), 'fullSourceSHA256': sha(full_path),
          'canonicalRestoreWholeTriangles': 88, 'canonicalClippedTriangles': 104, 'canonicalAddedOriginalVertices': 42, 'bodyOriginal9037XYZFullFourExact': True,
          'headOriginal43707XYZExact': True, 'planarBodyCut': float(body_cut), 'planarHeadCut': float(cut), 'bodyCutVertices': len(body_ring), 'headOuterCutVertices': len(outer),
          'headInnerCutVertices': len(inner), 'sections': sections, 'protectedNormals': normal_report,
          'explicitTriangleCounts': {key: len(arrays[key + 'Triangles']) for key in ['body', 'head']}, 'minimumTriangleArea2M2': {key: float(arrays[key + 'MinimumTriangleArea2']) for key in ['body', 'head']},
          'fieldLineage': 'All original body FULL rows come from the pinned raw diagnostic FULL field, FOUR from original conditioned source. New body plane104 and head loft use declared <=4 semantic fields, with original canonical raw and FOUR references retained separately.',
          'normalLineage': 'Body explicit source triangle corners carry canonical source decoded vectors/UVs. Original protected head corners retain exact decoded/raw data; moving native/export normals remain pending.',
          'limits': ['Independent save/reopen/actual evaluated triangle and original34/51 verification pending.', 'Finite rest/raised/grounded contacts and native/manual full/four loss pending; no topology or art pass.', 'Lower neck UV extends source cut UV; actual moving PBR review required.', 'Body03 boxer clearance and source shoulder/hip failures retained unchanged.', 'No facial, wardrobe, mobile, gameplay or promotion qualification.']}
(evidence / 'authoring.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2), flush=True)
