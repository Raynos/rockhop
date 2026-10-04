"""Correct split-ngon internal chords without changing the neck27 field.

Only previously declared boundary-edge-subdivided polygons are replaced.
Each fan uses an existing non-seam corner. No positions/weights/new vertices,
outside polygons, original controls or 51-joint frames change.
"""
import hashlib
import json
from pathlib import Path

import bpy
import numpy as np

root = Path(__file__).resolve().parents[6]
owned = Path(__file__).resolve().parent
evbase = root / 'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1'
out = evbase / 'neck-interface98'
out.mkdir(parents=True, exist_ok=True)
auth = json.loads((evbase / 'neck-interface97/authoring.json').read_text())
source = root / auth['native']
native = source.with_name('bounded-neck-join-triangulated.blend')
field_source = source.parent / 'authored-neck-fields.npz'
field_out = source.parent / 'triangulated-neck-fields.npz'
assert not native.exists() and not field_out.exists()
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(source) == auth['nativeSHA256'] and sha(field_source) == auth['fieldsSHA256']
fields = dict(np.load(field_source))
helper_path = owned / 'verify_extended_protected_data.py'
text = helper_path.read_text()
helpers = dict(bpy=bpy, np=np, hashlib=hashlib, json=json)
exec(compile(text[text.index('def value('):text.index('before=snapshot(original)')], str(helper_path), 'exec'), helpers)
def state(obj):
    result = {'object': helpers['object_state'](obj)}
    if obj.type == 'MESH':
        result.update(mesh=helpers['mesh_extra'](obj.data), positions=helpers['array_digest'](obj.data.vertices, 'co', 3),
            polygons=[list(f.vertices) for f in obj.data.polygons],
            weights=[[[obj.vertex_groups[g.group].name, float(g.weight)] for g in v.groups] for v in obj.data.vertices])
    return result

bpy.ops.wm.open_mainfile(filepath=str(source))
names = [o.name for o in bpy.data.objects]
before = {name: state(bpy.data.objects[name]) for name in names}
objects = []
rows = []
types = {'FLOAT': ('value', 1, np.float32), 'INT': ('value', 1, np.int32), 'BOOLEAN': ('value', 1, np.bool_),
    'FLOAT2': ('vector', 2, np.float32), 'FLOAT_VECTOR': ('vector', 3, np.float32),
    'FLOAT_COLOR': ('color', 4, np.float32), 'BYTE_COLOR': ('color', 4, np.float32),
    'INT32_2D': ('value', 2, np.int32), 'INT16_2D': ('value', 2, np.int32)}
proposal = json.loads((root / 'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/body59/proposal.json').read_text())['preciseInitialAuthoringMargin']
for part in auth['parts']:
    key = part['part']
    original = bpy.data.objects['Bounded neck27 ' + key + ' four, unaccepted']
    mesh = original.data
    positions = fields[key + 'RestXYZ']
    split = set(part['splitOriginalPolygonIDs'])
    sid = fields[key + 'SeamPhysicalIDs']
    polygons = []; corner_refs = []; face_refs = []; replacements = []; retained_seam_only = []
    for face in mesh.polygons:
        ids, loops = list(face.vertices), list(face.loop_indices)
        if face.index not in split:
            polygons.append(ids); corner_refs.extend(loops); face_refs.append(face.index)
        else:
            pivots = [i for i, v in enumerate(ids) if sid[v] < 0]
            if not pivots:
                # Original head stair-cut ears can contain only seam corners.
                # Preserve these unchanged; the opposed body fan supplies no
                # coincident seam-only chord, so no added centroid is needed.
                assert key == 'head'
                polygons.append(ids); corner_refs.extend(loops); face_refs.append(face.index)
                retained_seam_only.append(face.index)
                continue
            pivot = pivots[0]
            ids = ids[pivot:] + ids[:pivot]; loops = loops[pivot:] + loops[:pivot]
            new_ids = []
            for i in range(1, len(ids) - 1):
                new_ids.append(len(polygons)); polygons.append([ids[0], ids[i], ids[i + 1]])
                corner_refs.extend([loops[0], loops[i], loops[i + 1]]); face_refs.append(face.index)
            replacements.append({'checkpointPolygon': face.index, 'existingFanPivotVertex': ids[0], 'newPolygonIDs': new_ids})
    new = bpy.data.meshes.new('Unaccepted neck27 explicitly triangulated ' + key)
    new.from_pydata(positions.tolist(), [], polygons); new.update()
    for material in mesh.materials: new.materials.append(material)
    for i, face in enumerate(new.polygons):
        old = mesh.polygons[face_refs[i]]; face.material_index = old.material_index; face.use_smooth = old.use_smooth
    for attr in mesh.attributes:
        if attr.name in ['position', '.corner_vert', '.corner_edge', '.edge_verts']: continue
        prop, width, dtype = types[attr.data_type]
        values = np.empty(len(attr.data) * width, dtype=dtype); attr.data.foreach_get(prop, values); values = values.reshape(-1, width)
        dest = new.attributes.get(attr.name) or new.attributes.new(attr.name, attr.data_type, attr.domain)
        if attr.domain == 'POINT': result = values
        elif attr.domain == 'CORNER': result = values[corner_refs]
        elif attr.domain == 'FACE': result = values[face_refs]
        elif attr.domain == 'EDGE':
            old_edges = {tuple(sorted(e.vertices)): e.index for e in mesh.edges}
            result = np.zeros((len(dest.data), width), dtype=dtype)
            for edge in new.edges:
                i = old_edges.get(tuple(sorted(edge.vertices)))
                if i is not None: result[edge.index] = values[i]
        else: raise AssertionError(attr.domain)
        dest.data.foreach_set(prop, result.ravel())
    new.update(); new.calc_loop_triangles()
    triangles = np.array([t.vertices[:] for t in new.loop_triangles], dtype=np.int32)
    mapping = np.array(face_refs, dtype=np.int32)
    # New faces still report their original source polygon separately from
    # the replaced checkpoint polygon and explicit corner-copy ancestry.
    cap_faces = set(part['newInwardCapPolygonIDs'])
    old_face_count = 9008 if key == 'body' else 71826
    original_source_polygon = np.array([face_refs[t.polygon_index] if face_refs[t.polygon_index] not in cap_faces else -1 for t in new.loop_triangles], dtype=np.int32)
    allowed = proposal['bodyExistingRenderedNativeVertices' if key == 'body' else 'headInitialBoundaryLedNativeVertexIDs']
    local = np.array([t.index for t in new.loop_triangles if face_refs[t.polygon_index] in cap_faces or any(v >= part['originalVertices'] or v in allowed for v in t.vertices)], dtype=np.int32)
    fields[key + 'Triangles'] = triangles
    fields[key + 'LocalTriangleIDs'] = local
    fields[key + 'TriangleSourcePolygonIDs'] = original_source_polygon
    fields[key + 'CandidatePolygonToCheckpointPolygon'] = mapping
    fields[key + 'CandidateCornerToCheckpointCorner'] = np.array(corner_refs, dtype=np.int32)
    fields[key + 'CornerAttributeEdgeSources'] = fields[key + 'CornerAttributeEdgeSources'][corner_refs]
    rows.append({'part': key, 'replacedCheckpointPolygons': replacements, 'candidatePolygons': len(polygons),
        'retainedSeamOnlyCheckpointPolygons': retained_seam_only,
        'candidateTriangles': len(triangles), 'localTrianglesIncludingOneCorner': len(local),
        'positionsAndBothWeightArraysUnchanged': True})
    for label in ['full', 'four']:
        old_obj = bpy.data.objects['Bounded neck27 ' + key + ' ' + label + ', unaccepted']
        candidate = old_obj.copy(); candidate.data = new.copy(); candidate.name = 'Bounded neck27 triangulated ' + key + ' ' + label + ', unaccepted'
        bpy.context.collection.objects.link(candidate)
        candidate.vertex_groups.clear()
        for name in fields['boneNames'].tolist(): candidate.vertex_groups.new(name=name)
        weights = fields[key + label.title() + 'Weights']
        for i, row in enumerate(weights):
            for j in np.flatnonzero(row > 0): candidate.vertex_groups[fields['boneNames'][j]].add([i], float(row[j]), 'REPLACE')
        candidate.hide_render = True; candidate.hide_set(True); objects.append(candidate.name)
for name in names: assert before[name] == state(bpy.data.objects[name]), name
for key in ['body', 'head']:
    original_fields = np.load(field_source)
    for suffix in ['RestXYZ', 'FullWeights', 'FourWeights', 'SeamPhysicalIDs']:
        assert np.array_equal(fields[key + suffix], original_fields[key + suffix])
np.savez_compressed(field_out, **fields)
bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
report = {'status': 'UNACCEPTED_SAME_FIELD_DETERMINISTIC_LOCAL_TRIANGULATION', 'sourceNativeSHA256': sha(source),
    'sourceFieldsSHA256': sha(field_source), 'recipeSHA256': sha(__file__), 'native': str(native.relative_to(root)),
    'nativeSHA256': sha(native), 'fieldsSHA256': sha(field_out), 'objects': objects,
    'originalAndFailedCheckpointObjectsExact': len(names), 'parts': rows,
    'scope': 'Only42body/54head previously declared split polygons; existing non-seam corner fans, explicit corner attribute copies. All positions/weights/registry and51bind remain unchanged, no additional vertices. Failed native27 remains immutable.',
    'limits': ['Reopen/rest topology/contact/collapse and all529native/703actual47 remain pending.',
        'Same one bounded neck trial, not a new shape/field experiment. All M0-M5/art/device/player-promotion gates open.']}
(out / 'triangulation.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k: report[k] for k in ['status', 'nativeSHA256', 'fieldsSHA256', 'originalAndFailedCheckpointObjectsExact']}, indent=2))
