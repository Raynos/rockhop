"""Scoped lower-neck replacement with separate planar inner closure.

The original upper polygons, UV/PBR and protected decoded/raw normal frames
remain exact. Lower source triangles are clipped at 1.575 m; a ring loft meets
an unchanged canonical body seam. Original objects and body03 boxer are kept.
This is an unaccepted experiment, not a player-asset promotion.
"""
import hashlib
import json
from collections import defaultdict
from pathlib import Path
import bpy
import numpy as np
from mathutils import Vector
from mathutils.geometry import tessellate_polygon
from mathutils.bvhtree import BVHTree

owned = Path(__file__).resolve().parent
root = owned.parents[5]
out = owned / 'body04b'
evidence = root / 'docs/evidence/hero-remaster/finish-2026-10-05/construction/body04b'
native = out / 'natural-foundation.blend'
assert not native.exists(), 'Never overwrite an executed candidate'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
source = owned / 'body03/natural-foundation.blend'
assert sha(source) == '9709c203595940b0ed2498c762639237605dd33228d867c0de0d8100f8b61190'
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
    polygons.append(clipped)
    corner_refs.extend(refs)
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

def ordered(ids, xyz):
    p = np.asarray(xyz)[ids]
    area = .5 * np.sum(p[:, 0] * np.roll(p[:, 1], -1) - p[:, 1] * np.roll(p[:, 0], -1))
    if area < 0:
        ids = ids[::-1]
    return np.roll(ids, -int(np.argmax(np.asarray(xyz)[ids, 0])))

def knots(ids, xyz):
    p = np.asarray(xyz)[ids]
    length = np.linalg.norm((np.roll(p, -1, axis=0) - p)[:, :2], axis=1)
    assert np.min(length) > 0
    return np.r_[0., np.cumsum(length[:-1])] / length.sum()

def segment(u, source_u):
    i = max(int(np.searchsorted(source_u, u, side='right') - 1), 0)
    hi = source_u[i + 1] if i + 1 < len(source_u) else 1.
    return i, (float(u) - source_u[i]) / (hi - source_u[i])

outer = ordered(outer, positions)
body_order = ordered(r['bodyCutOrderedNativeIDs'], bp)
hu, bu = knots(outer, positions), knots(body_order, bp)
common = np.unique(np.r_[hu, bu])
upper = np.array(positions)[outer]
base, tops, base_weights = [], [], []
for u in common:
    i, f = segment(u, bu)
    p = ((1 - f) * bp[body_order[i]] + f * bp[body_order[(i + 1) % len(body_order)]]).astype(np.float32)
    base.append(p)
    raw = (1 - f) * f0['displayBodyWeights'][body_order[i]] + f * f0['displayBodyWeights'][body_order[(i + 1) % len(body_order)]]
    side = 'R' if p[1] >= 0 else 'L'
    w = np.zeros(51, np.float32)
    for name in ['chest', 'neck', 'shoulder.' + side, 'upperArm.' + side]:
        w[names.index(name)] = raw[names.index(name)]
    # Side semantic restriction is explicit; no strongest-four truncation.
    w[names.index('neck')] += raw[names.index('head')]
    w /= w.sum()
    base_weights.append(w)
    i, f = segment(u, hu)
    tops.append((1 - f) * upper[i] + f * upper[(i + 1) % len(upper)])
base, tops, base_weights = np.array(base, np.float32), np.array(tops, np.float32), np.array(base_weights, np.float32)
head_full = list(f0['headWeights'].copy())
head_four = list(f0['headWeights'].copy())
for a, b, f in point_refs[len(hp):]:
    w = ((1 - f) * f0['headWeights'][a] + f * f0['headWeights'][b]).astype(np.float32)
    assert set(np.flatnonzero(w)) <= {names.index('head'), names.index('neck')}
    w /= w.sum()
    head_full.append(w); head_four.append(w.copy())
head_seam = [-1] * len(positions)
top_weights = []
for u in common:
    i, f = segment(u, hu)
    w = (1 - f) * head_four[int(outer[i])] + f * head_four[int(outer[(i + 1) % len(outer)])]
    top_weights.append(w / w.sum())
top_weights = np.array(top_weights, np.float32)
# Nine monotone-height outer rings. Arm fields vanish before head fields start,
# giving at most four intended fields without discarded full-control mass.
canonical = f0['canonicalXYZ']
canonical_tri = f0['canonicalTriangles']
neck_tri = canonical_tri[np.all((canonical[canonical_tri, 2] > 1.49) & (canonical[canonical_tri, 2] < 1.62), axis=1)]
neck_tree = BVHTree.FromPolygons([Vector(x) for x in canonical], neck_tri.tolist(), all_triangles=True)
def canonical_ring_point(z, reference):
    direction = Vector((float(reference[0] - .035), float(reference[1]), 0.))
    direction.normalize()
    q, normal, index, distance = neck_tree.ray_cast(Vector((.035, 0., float(z))), direction, 1.)
    assert q is not None, (z, list(reference))
    return np.array(q, np.float32)
def smooth5(t):
    return t ** 3 * (10 - 15 * t + 6 * t ** 2)
canonical_top = np.array([canonical_ring_point(float(cut), top) for top in tops])
canonical_base = np.array([canonical_ring_point(float(bottom[2]), bottom) for bottom in base])
loft = []
loft_uv_refs = {}
for s in np.linspace(0., 1., 9)[1:]:
    ids = []
    for sid, (top, bottom, bw) in enumerate(zip(tops, base, base_weights)):
        reference = (1 - s) * top + s * bottom
        z = (1 - s) * float(cut) + s * float(bottom[2])
        q = canonical_ring_point(z, reference)
        p = (q + (1 - smooth5(s)) * (top - canonical_top[sid]) + smooth5(s) * (bottom - canonical_base[sid])).astype(np.float32)
        p[2] = np.float32(z)
        if s == 1:
            p = bottom.copy()
        vid = len(positions); ids.append(vid); positions.append(p.tolist())
        i, f = segment(common[sid], hu)
        loft_uv_refs[vid] = (int(outer[i]), int(outer[(i + 1) % len(outer)]), float(f))
        point_refs.append((-1, -1, 0.)); head_seam.append(sid if s == 1 else -1)
        arm_fade = np.clip((s - .55) / .45, 0, 1)
        arm_fade = arm_fade ** 3 * (10 - 15 * arm_fade + 6 * arm_fade ** 2)
        w = bw.copy()
        for name in ['shoulder.R', 'shoulder.L', 'upperArm.R', 'upperArm.L']:
            w[names.index('neck')] += w[names.index(name)] * (1 - arm_fade)
            w[names.index(name)] *= arm_fade
        h = np.clip((.55 - s) / .55, 0, 1)
        h = h ** 3 * (10 - 15 * h + 6 * h ** 2)
        w *= 1 - h; w += h * top_weights[sid]
        w /= w.sum()
        assert np.count_nonzero(w) <= 4
        head_full.append(w); head_four.append(w.copy())
    loft.append(np.array(ids, np.int32))
# Zipper triangles retain the exact source cut without splitting upper faces.
def bridge(a, au, b, b_u):
    i = j = 0
    while i < len(a) or j < len(b):
        na = au[i + 1] if i + 1 < len(a) else 1.
        nb = b_u[j + 1] if j + 1 < len(b) else 1.
        aa, bb = int(a[i % len(a)]), int(b[j % len(b)])
        if i < len(a) and (j >= len(b) or na <= nb):
            face = [aa, int(a[(i + 1) % len(a)]), bb]; i += 1
        else:
            face = [aa, int(b[(j + 1) % len(b)]), bb]; j += 1
        polygons.append(face[::-1]); corner_refs.extend([(-1, -1, 0.)] * 3); polygon_sources.append(-1)
bridge(outer, hu, loft[0], common)
for a, b in zip(loft, loft[1:]):
    bridge(a, common, b, common)
# Inner closure remains at Z=1.575, above all derived outer loft/body seam.
inner = ordered(inner, positions)
inner_vectors = [Vector(positions[i]) for i in inner]
lookup = {tuple(v): int(i) for v, i in zip(inner_vectors, inner)}
for tri in tessellate_polygon([inner_vectors]):
    face = [lookup[tuple(v)] for v in tri]
    polygons.append(face); corner_refs.extend([(-1, -1, 0.)] * 3); polygon_sources.append(-1)

# Body seam edge splits keep every source position and all unrelated fields.
bpositions = bp.tolist(); bpoint_refs = [(i, i, 0.) for i in range(len(bp))]
bweights_four = list(f0['displayBodyWeights'].copy())
canonical_source = bpy.data.objects['Canonical anatomical body, baked adult hm08']
body_source_ids = np.empty(len(body.data.vertices), np.int32)
body.data.attributes['_SOURCE_ID'].data.foreach_get('value', body_source_ids)
bweights_full = list(f0['canonicalWeights'][body_source_ids].copy())
bseam = [-1] * len(bp); splits = {}
for i, v in enumerate(body_order):
    sid = int(np.searchsorted(common, bu[i]))
    bseam[v] = sid; bweights_full[v] = base_weights[sid].copy(); bweights_four[v] = base_weights[sid].copy()
    w = int(body_order[(i + 1) % len(body_order)])
    lo, hi = bu[i], bu[i + 1] if i + 1 < len(bu) else 1.
    inserted = []
    for sid in np.flatnonzero((common > lo) & (common < hi)):
        fraction = float((common[sid] - lo) / (hi - lo))
        vid = len(bpositions); bpositions.append(base[sid].tolist())
        bpoint_refs.append((int(v), w, fraction)); bweights_full.append(base_weights[sid].copy()); bweights_four.append(base_weights[sid].copy()); bseam.append(int(sid))
        inserted.append((vid, fraction))
    splits[(int(v), w)] = inserted; splits[(w, int(v))] = [(vid, 1 - f) for vid, f in reversed(inserted)]
bpolygons, bcorner_refs, bpoly_sources = [], [], []
for poly in body.data.polygons:
    ids, loops = list(poly.vertices), list(poly.loop_indices); face = []
    for i, v in enumerate(ids):
        w, lv, lw = ids[(i + 1) % len(ids)], loops[i], loops[(i + 1) % len(ids)]
        face.append(v); bcorner_refs.append((lv, lv, 0.))
        for vid, fraction in splits.get((v, w), []):
            face.append(vid); bcorner_refs.append((lv, lw, fraction))
    bpolygons.append(face); bpoly_sources.append(poly.index)

TYPE = {'FLOAT': ('value', 1, np.float32), 'INT': ('value', 1, np.int32), 'BOOLEAN': ('value', 1, np.bool_), 'FLOAT2': ('vector', 2, np.float32), 'FLOAT_VECTOR': ('vector', 3, np.float32), 'FLOAT_COLOR': ('color', 4, np.float32), 'BYTE_COLOR': ('color', 4, np.float32), 'INT32_2D': ('value', 2, np.int32), 'INT16_2D': ('value', 2, np.int32)}
arrays = {'boneNames': np.array(names), 'commonU': common, 'sharedRestFloat32XYZ': base, 'sharedProductionWeights': base_weights, 'outerCutOriginalEdgeAncestry': np.array([point_refs[i] for i in outer]), 'innerCutOriginalEdgeAncestry': np.array([point_refs[i] for i in inner]), 'removedOriginalHeadPolygonIDs': np.array(removed), 'clippedOriginalHeadPolygonIDs': np.array(touched)}
normal_report = {}
for key, src, pos, faces, pr, cr, ps, full, four, seam in [
    ('head', head, positions, polygons, point_refs, corner_refs, polygon_sources, head_full, head_four, head_seam),
    ('body', body, bpositions, bpolygons, bpoint_refs, bcorner_refs, bpoly_sources, bweights_full, bweights_four, bseam)]:
    mesh = bpy.data.meshes.new('Finish clipped ' + key)
    mesh.from_pydata(pos, [], faces); mesh.update()
    for material in src.data.materials: mesh.materials.append(material)
    for poly, source_poly in zip(mesh.polygons, ps):
        poly.material_index = src.data.polygons[source_poly].material_index if source_poly >= 0 else 0
        poly.use_smooth = src.data.polygons[source_poly].use_smooth if source_poly >= 0 else True
    for attr in src.data.attributes:
        if attr.name in ['position', '.corner_vert', '.corner_edge', '.edge_verts'] or (key == 'head' and attr.name == 'custom_normal'):
            continue
        assert attr.data_type in TYPE, (attr.name, attr.data_type)
        prop, width, dtype = TYPE[attr.data_type]
        values = np.empty(len(attr.data) * width, dtype); attr.data.foreach_get(prop, values); values = values.reshape(-1, width)
        dest = mesh.attributes.get(attr.name) or mesh.attributes.new(attr.name, attr.data_type, attr.domain)
        dv = np.zeros((len(dest.data), width), dtype)
        if attr.domain in ['POINT', 'CORNER']:
            for i, (a, b, f) in enumerate(pr if attr.domain == 'POINT' else cr):
                if a >= 0: dv[i] = (1 - f) * values[a] + f * values[b] if np.issubdtype(dtype, np.floating) else values[a]
                elif np.issubdtype(dtype, np.integer): dv[i] = -1
        elif attr.domain == 'FACE':
            for i, a in enumerate(ps):
                if a >= 0: dv[i] = values[a]
        elif attr.domain == 'EDGE':
            edges = {tuple(sorted(e.vertices)): e.index for e in src.data.edges}
            for e in mesh.edges:
                a = edges.get(tuple(sorted(e.vertices)))
                if a is not None: dv[e.index] = values[a]
        else: raise AssertionError(attr.domain)
        if key == 'head' and attr.domain == 'CORNER' and attr.data_type == 'FLOAT2':
            # Explicit derived lower UV, separate from source-corner identity.
            point_uv = np.zeros((len(pos), 2), np.float32)
            first_corner = {}
            for loop in src.data.loops:
                first_corner.setdefault(loop.vertex_index, loop.index)
            for i in range(len(src.data.vertices)):
                point_uv[i] = values[first_corner[i]]
            for i, (a, b, f) in enumerate(pr[len(src.data.vertices):], len(src.data.vertices)):
                if a >= 0:
                    point_uv[i] = (1 - f) * point_uv[a] + f * point_uv[b]
            for i, (a, b, f) in loft_uv_refs.items():
                point_uv[i] = (1 - f) * point_uv[a] + f * point_uv[b]
            for loop in mesh.loops:
                if cr[loop.index][0] < 0:
                    dv[loop.index] = point_uv[loop.vertex_index]
            arrays['headDerivedCornerUV_' + attr.name] = dv.copy()
        dest.data.foreach_set(prop, dv.ravel())
    mesh.update()
    if key == 'head':
        desired = np.array([x.vector[:] for x in mesh.corner_normals], np.float32)
        source_c = np.array(cr)[:, 0].astype(int); valid = source_c >= 0
        keep = valid.copy(); keep[valid] = np.isin(f0['headCornerVertexIDs'][source_c[valid]], f0['headProtectedIDs'])
        desired[keep] = f0['headCornerNormals'][source_c[keep]]
        mesh.normals_split_custom_set(desired.tolist())
        attr = mesh.attributes['custom_normal']; packed = np.empty(len(attr.data) * 2, np.int32); attr.data.foreach_get('value', packed); packed = packed.reshape(-1, 2)
        packed[keep] = f0['headRawCustomNormals'][source_c[keep]]; attr.data.foreach_set('value', packed.ravel()); mesh.update()
        decoded = np.array([x.vector[:] for x in mesh.corner_normals], np.float32)
        normal_report = {'protectedCorners': int(keep.sum()), 'changedProtectedCorners': int(np.any(decoded[keep] != f0['headCornerNormals'][source_c[keep]], axis=1).sum()), 'maximumProtectedDelta': float(np.max(np.linalg.norm(decoded[keep] - f0['headCornerNormals'][source_c[keep]], axis=1)))}
        evidence.mkdir(parents=True, exist_ok=True)
        (evidence / 'pre-save-normal-check.json').write_text(json.dumps(dict(normal_report, recipeSHA256=sha(__file__)), indent=2) + '\n')
        assert normal_report['changedProtectedCorners'] == 0, normal_report
    for label, field in [('FULL', full), ('FOUR', four)]:
        candidate = bpy.data.objects['Finish ' + key + ' ' + label]
        candidate.data = mesh.copy(); candidate.vertex_groups.clear()
        for group in src.vertex_groups: candidate.vertex_groups.new(name=group.name)
        for i, row in enumerate(field):
            for j in np.flatnonzero(np.array(row) > 0): candidate.vertex_groups[names[j]].add([i], float(row[j]), 'REPLACE')
        for name, values in [('_NATIVE_ID', np.arange(len(pos), dtype=np.int32)), ('_SOURCE_ID', np.r_[np.arange(len(src.data.vertices), dtype=np.int32), np.full(len(pos) - len(src.data.vertices), -1, np.int32)])]:
            attr = candidate.data.attributes.get(name) or candidate.data.attributes.new(name, 'INT', 'POINT'); attr.data.foreach_set('value', values)
        candidate.data.update()
    mesh.calc_loop_triangles()
    arrays.update({key + 'RestXYZ': np.array(pos, np.float32), key + 'Triangles': np.array([t.vertices[:] for t in mesh.loop_triangles], np.int32), key + 'FullWeights': np.array(full, np.float32), key + 'FourWeights': np.array(four, np.float32), key + 'SeamPhysicalIDs': np.array(seam, np.int32), key + 'AttributeEdgeSources': np.array(pr), key + 'CornerAttributeEdgeSources': np.array(cr), key + 'TriangleSourcePolygonIDs': np.array([ps[t.polygon_index] for t in mesh.loop_triangles], np.int32), key + 'UnusedOriginalNativeIDs': np.setdiff1d(np.arange(len(src.data.vertices)), np.unique(np.concatenate([np.array(f) for f in faces])))})
    assert np.max((np.array(four) > 0).sum(axis=1)) <= 4
    assert np.array_equal(np.array(pos, np.float32)[:len(src.data.vertices)], np.array([v.co[:] for v in src.data.vertices], np.float32))
out.mkdir(parents=True, exist_ok=True); evidence.mkdir(parents=True, exist_ok=True)
np.savez_compressed(out / 'authored-neck-fields.npz', **arrays)
bpy.context.view_layer.update()
bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
report = {'status': 'UNACCEPTED_BODY04B_SCOPED_TOPOLOGY_REPLACEMENT_REQUIRES_INDEPENDENT_QA', 'source': str(source.relative_to(root)), 'sourceSHA256': sha(source), 'native': str(native.relative_to(root)), 'nativeSHA256': sha(native), 'recipeSHA256': sha(__file__), 'fieldsSHA256': sha(out / 'authored-neck-fields.npz'), 'cutNativeZ': float(cut), 'cutRingVertices': [len(outer), len(inner)], 'removedOriginalHeadPolygons': len(removed), 'clippedOriginalHeadPolygons': len(touched) - len(removed), 'sharedSeamKnots': len(common), 'outerGeometry': 'Coherent canonical neck cross-sections plus compact quintic endpoint displacements; original cut and body seam exact. Inner cap remains at the upper cut plane.', 'protectedNormals': normal_report, 'semanticFields': 'At most four intended fields: chest/neck/ipsilateral shoulder/upperArm near base; arms vanish before head blend starts. New neck full and four are identical authored fields.', 'ancestry': 'Original upper source vertices retain indexes and exact positions; removed lower points remain unused diagnostic rows. Clipped cut points have source-edge ancestry; loft points SOURCE_ID=-1. Original upper corner/UV/PBR preserved; new lower surface has derived UV ancestry.', 'limits': ['No finite topology/self/body contacts or motion acceptance yet.', 'Body03 boxer clearance failures retained unchanged, shoulder/hip field repair remains a separate next unit.', 'New lower loft UV extends the original cut-edge skin UV vertically; original protected appearance exact. Derived lower texture stretch/seam still needs played PBR review.', 'Retained unused original rows are diagnostic ancestry, not final phone production topology.']}
(evidence / 'authoring.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps(report, indent=2), flush=True)
