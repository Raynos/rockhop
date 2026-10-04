"""Read-only reopen and rest registry checks for the single neck27 trial."""
import hashlib
import json
from pathlib import Path

import bpy
import numpy as np

root = Path(__file__).resolve().parents[6]
owned = Path(__file__).resolve().parent
evidence = root / 'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/neck-interface97'
auth = json.loads((evidence / 'authoring.json').read_text())
native = root / auth['native']
source = owned / 'selected-hoodie26/native-four-with-full-control.blend'
field_path = native.parent / 'authored-neck-fields.npz'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(native) == auth['nativeSHA256'] and sha(field_path) == auth['fieldsSHA256']
fields = np.load(field_path)
definitions = (owned / 'verify_extended_protected_data.py').read_text()
helpers = dict(bpy=bpy, np=np, hashlib=hashlib, json=json)
exec(compile(definitions[definitions.index('def value('):definitions.index('before=snapshot(original)')], 'frozen-helper', 'exec'), helpers)

def attr_values(attr):
    prop = 'vector' if attr.data_type in ['FLOAT_VECTOR', 'FLOAT2'] else 'color' if attr.data_type in ['FLOAT_COLOR', 'BYTE_COLOR'] else 'value'
    width = len(getattr(attr.data[0], prop)) if hasattr(getattr(attr.data[0], prop), '__len__') else 1
    dtype = np.float32 if attr.data_type.startswith('FLOAT') or attr.data_type == 'BYTE_COLOR' else np.bool_ if attr.data_type == 'BOOLEAN' else np.int32
    values = np.empty(len(attr.data) * width, dtype=dtype)
    attr.data.foreach_get(prop, values)
    return values.reshape(-1, width)

def snapshot():
    objects = {}
    for o in bpy.data.objects:
        state = {'object': helpers['object_state'](o)}
        if o.type == 'MESH':
            state.update(mesh=helpers['mesh_extra'](o.data), positions=helpers['array_digest'](o.data.vertices, 'co', 3),
                polygons=[list(p.vertices) for p in o.data.polygons],
                weights=[[[o.vertex_groups[g.group].name, float(g.weight)] for g in v.groups] for v in o.data.vertices],
                materials=[m.name if m else None for m in o.data.materials])
        objects[o.name] = state
    rig = bpy.data.objects['Independent anatomical foundation rig']
    return {'objects': objects, 'rig': {b.name: {'rest': np.array(b.bone.matrix_local).tolist(),
        'pose': np.array(b.matrix).tolist(), 'basis': np.array(b.matrix_basis).tolist(),
        'properties': helpers['properties'](b)} for b in rig.pose.bones},
        'images': {im.name: {'packed': hashlib.sha256(bytes(im.packed_file.data)).hexdigest() if im.packed_file else None,
            'colour': im.colorspace_settings.name, 'size': list(im.size)} for im in bpy.data.images}}

bpy.ops.wm.open_mainfile(filepath=str(source))
before = snapshot()
source_domains = {}
for key, name in [('body', 'Canonical body with hidden head interface'), ('head', 'Protected textured head above hidden neck interface')]:
    o = bpy.data.objects[name]
    o.data.calc_loop_triangles()
    source_domains[key] = {'polygons': [list(p.vertices) for p in o.data.polygons],
        'loops': np.array([l.vertex_index for l in o.data.loops]),
        'attrs': {a.name: (a.data_type, a.domain, attr_values(a)) for a in o.data.attributes},
        'triangles': np.array([t.vertices[:] for t in o.data.loop_triangles]),
        'trianglePolygons': np.array([t.polygon_index for t in o.data.loop_triangles])}
bpy.ops.wm.open_mainfile(filepath=str(native))
after = snapshot()
assert before['rig'] == after['rig'] and before['images'] == after['images']
for name, state in before['objects'].items(): assert after['objects'][name] == state, name
proposal = json.loads((root / 'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/body59/proposal.json').read_text())['preciseInitialAuthoringMargin']
outside_results = []
for part in auth['parts']:
    key = part['part']; sd = source_domains[key]
    allowed = proposal['bodyExistingRenderedNativeVertices' if key == 'body' else 'headInitialBoundaryLedNativeVertexIDs']
    allowed_triangles = proposal['bodyExistingRenderedTriangleIDs' if key == 'body' else 'headInitialBoundaryLedNativeTriangleIDs']
    outside = np.setdiff1d(np.arange(part['originalVertices']), allowed)
    for label in ['full', 'four']:
        o = bpy.data.objects['Bounded neck27 ' + key + ' ' + label + ', unaccepted']
        p = np.array([v.co[:] for v in o.data.vertices], dtype=np.float32)
        assert np.array_equal(p, fields[key + 'RestXYZ'])
        w = np.zeros((len(p), 51), dtype=np.float32)
        for v in o.data.vertices:
            for g in v.groups: w[v.index, fields['boneNames'].tolist().index(o.vertex_groups[g.group].name)] = g.weight
        assert np.array_equal(w, fields[key + label.title() + 'Weights'])
        o.data.calc_loop_triangles()
        assert np.array_equal(np.array([t.vertices[:] for t in o.data.loop_triangles]), fields[key + 'Triangles'])
        # Explicitly preserve old polygon cycles outside reported split faces.
        splits = set(part['splitOriginalPolygonIDs'])
        for i, face in enumerate(sd['polygons']):
            if i not in splits: assert list(o.data.polygons[i].vertices) == face
            else:
                incident = np.flatnonzero(sd['trianglePolygons'] == i)
                assert set(incident) <= set(allowed_triangles)
        refs = fields[key + 'CornerAttributeEdgeSources']
        old_corner = (refs[:, 0] >= 0) & (refs[:, 0] == refs[:, 1])
        outside_corner = old_corner.copy()
        outside_corner[old_corner] = np.isin(sd['loops'][refs[old_corner, 0].astype(int)], outside)
        checked = []
        for name, (kind, domain, values) in sd['attrs'].items():
            if name in ['position', '.corner_vert', '.corner_edge', '.edge_verts']: continue
            a = o.data.attributes[name]; assert a.domain == domain and a.data_type == kind
            actual = attr_values(a)
            if domain == 'POINT': assert np.array_equal(actual[outside], values[outside])
            elif domain == 'CORNER': assert np.array_equal(actual[outside_corner], values[refs[outside_corner, 0].astype(int)])
            elif domain == 'FACE': assert np.array_equal(actual[:len(values)], values)
            checked.append([name, domain])
        outside_results.append({'part': key, 'field': label, 'outsideVertices': len(outside),
            'protectedOriginalCornerCopies': int(outside_corner.sum()), 'attributesChecked': checked,
            'reopenedPositionsWeightsAndTrianglesExact': True, 'oldUnsplitPolygonCyclesExact': True})

# Registry-aware triangle topology. Existing head UV quotient is retained
# diagnostically; only the newly declared outer/inner seams are qualified.
registry = np.load(evidence.parent / 'neck-interface96/ordered-boundaries.npz')
seam_count = auth['physicalSeamKnots']
physical = {}; points = {}; triangles = []; offsets = {}; base = seam_count
for key in ['body', 'head']:
    p = fields[key + 'RestXYZ']; ids = np.arange(len(p), dtype=np.int64) + base
    if key == 'head': ids[:len(registry['headPositionAlias'])] = registry['headPositionAlias'] + base
    sid = fields[key + 'SeamPhysicalIDs']; ids[sid >= 0] = sid[sid >= 0]
    physical[key] = ids; offsets[key] = len(triangles)
    triangles.extend(ids[fields[key + 'Triangles']].tolist())
    for i, v in enumerate(ids):
        if int(v) in points: assert np.array_equal(points[int(v)], p[i])
        else: points[int(v)] = p[i]
    base += len(p)
triangles = np.array(triangles)
edges = np.concatenate([triangles[:, [0, 1]], triangles[:, [1, 2]], triangles[:, [2, 0]]])
undirected = np.sort(edges, axis=1)
unique, inv, count = np.unique(undirected, axis=0, return_inverse=True, return_counts=True)
is_seam = (unique < seam_count).all(axis=1) & ((unique[:, 1] - unique[:, 0] == 1) | ((unique[:, 0] == 0) & (unique[:, 1] == seam_count - 1)))
seam_edges = np.flatnonzero(is_seam)
assert len(seam_edges) == seam_count and np.all(count[seam_edges] == 2)
for e in seam_edges:
    pair = edges[inv == e]; assert np.array_equal(pair[0], pair[1][::-1])
area_rows = []
for key in ['body', 'head']:
    p = fields[key + 'RestXYZ'].astype(np.float64); t = fields[key + 'Triangles']; local = fields[key + 'LocalTriangleIDs']
    q = p[t[local]]; area = .5 * np.linalg.norm(np.cross(q[:, 1] - q[:, 0], q[:, 2] - q[:, 0]), axis=1)
    assert (area > 1e-14).all()
    area_rows.append({'part': key, 'localTrianglesIncludingOneCorner': len(local), 'minimumAreaM2': float(area.min()), 'below1e_14M2': int((area <= 1e-14).sum())})
head_ids = physical['head']; inner = fields['headInnerClosurePhysicalIDs']; inner_vertices = set(head_ids[inner >= 0])
inner_edges = np.flatnonzero(np.array([a in inner_vertices and b in inner_vertices for a, b in unique]))
assert np.all(count[inner_edges] == 2)
for e in inner_edges:
    pair = edges[inv == e]; assert np.array_equal(pair[0], pair[1][::-1])
head_remaining = unique[count == 1]
assert len(head_remaining) == 151, 'Only original four mouth-area diagnostic boundaries remain'
nonmanifold = []
for edge in np.flatnonzero(count > 2):
    tri_ids = np.flatnonzero((np.isin(triangles, unique[edge]).sum(axis=1)) == 2)
    witnesses = []
    for i in tri_ids:
        part = 'body' if i < offsets['head'] else 'head'
        local_id = int(i) - offsets[part]
        witnesses.append({'part': part, 'candidateTriangleID': local_id,
            'sourcePolygonID': int(fields[part + 'TriangleSourcePolygonIDs'][local_id])})
    nonmanifold.append({'physicalVertexPair': unique[edge].tolist(), 'triangleIncidence': int(count[edge]), 'witnesses': witnesses})
report = {'status': 'FAILED_REST_INTERNAL_CHORD_INCIDENCE_UNACCEPTED_CHECKPOINT', 'nativeSHA256': sha(native),
    'fieldsSHA256': sha(field_path), 'recipeSHA256': sha(__file__), 'sourceSHA256': sha(source),
    'originalObjectsExactAfterReopen': len(before['objects']), 'original51RestBindPoseExact': True,
    'originalPackedImagesAndColourSpacesExact': len(before['images']), 'outsideChecks': outside_results,
    'physicalOuterSeam': {'knots': seam_count, 'edges': len(seam_edges), 'incidenceExactly2AndOpposed': True,
        'positionsFloat32Identical': True, 'semanticWeightsIdentical': True},
    'innerClosureEdgesExactly2AndOpposed': len(inner_edges), 'remainingOriginalMouthDiagnosticBoundaryEdges': len(head_remaining),
    'nonmanifoldInternalChords': nonmanifold,
    'localRestAreas': area_rows, 'limits': ['Position quotient of unchanged UV seams is diagnostic, not full head containment/watertightness.',
        'Rest FAILS six coincident internal triangulation chords with4incidences. No rest qualification.',
        'Rest collision/quality, all529native/703actual47 motion, full/four loss, garment contacts and played appearance remain unverified.',
        'No native save, source edit, new pose/capture/promotion. All M0-M5 open.']}
assert sha(native) == auth['nativeSHA256'] and sha(field_path) == auth['fieldsSHA256']
(evidence / 'reopen-rest.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['status', 'originalObjectsExactAfterReopen', 'physicalOuterSeam', 'localRestAreas']}, indent=2))
