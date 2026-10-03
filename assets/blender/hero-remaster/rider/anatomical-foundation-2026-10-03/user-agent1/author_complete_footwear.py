"""Author complete canonical-foot uppers/soles/ankle openings, not donor fragments."""
import argparse
import hashlib
import json
import math
import sys
from pathlib import Path
import bpy
import bmesh
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap = argparse.ArgumentParser(description=__doc__)
for n in ['source', 'out', 'evidence']:
    ap.add_argument('--' + n, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:]); source, out, evidence = [Path(getattr(a, n)).resolve() for n in ['source', 'out', 'evidence']]
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest(); source_pin = sha(source)
out.mkdir(parents=True, exist_ok=True); evidence.mkdir(parents=True, exist_ok=True)
if (out / 'rider.blend').exists():
    raise RuntimeError('Frozen footwear successor exists')
bpy.ops.wm.open_mainfile(filepath=str(source))
body = bpy.data.objects['Canonical anatomical body, baked adult hm08']; rig = bpy.data.objects['Independent anatomical foundation rig']; root = bpy.data.objects['Foundation file frame, game x0.65']
old_boot = bpy.data.objects['Registered boots from bounded foot accessory regions']; old_boot.hide_render = True
body.data.calc_loop_triangles(); bv = np.array([v.co[:] for v in body.data.vertices]); bf = np.array([t.vertices[:] for t in body.data.loop_triangles])
body_tree = BVHTree.FromPolygons([Vector(p) for p in bv], bf.tolist(), all_triangles=True)
body_weights = [{body.vertex_groups[g.group].name: g.weight for g in v.groups if g.weight > 0 and body.vertex_groups[g.group].name in rig.data.bones} for v in body.data.vertices]
vertices = []; faces = []; slots = []; weight_rows = []; foot_records = []
def bary(p, ids):
    q = bv[ids]; matrix = np.column_stack([q[1]-q[0], q[2]-q[0]]); yz = np.linalg.lstsq(matrix, p-q[0], rcond=None)[0]
    w = np.clip([1-sum(yz), yz[0], yz[1]], 0, 1); return w / sum(w)
def skin_weights(p):
    q, n, face, distance = body_tree.find_nearest(Vector(p)); ids = bf[face]; factors = bary(np.array(q), ids); weights = {}
    for old, factor in zip(ids, factors):
        for name, value in body_weights[old].items():
            weights[name] = weights.get(name, 0) + factor * value
    weights = sorted(weights.items(), key=lambda p: -p[1])[:4]; total = sum(v for n, v in weights)
    return {n: v/total for n, v in weights}
def add_geometry(v, f, material):
    offset = len(vertices); vertices.extend(v); weight_rows.extend(skin_weights(p) for p in v)
    faces.extend([[offset+i for i in row] for row in f]); slots.extend([material]*len(f))
for side, sign in [('L', -1), ('R', 1)]:
    selected = np.where((bv[:, 2] < .195) & (bv[:, 1] * sign > .075))[0]
    assert len(selected) > 100
    raw = bv[selected]; cuff = .165; floor = float(raw[:, 2].min() - .010); points = []
    # A complete eased foot envelope: a fixed Minkowski box around all foot
    # and lower ankle points. No appearance donor mask or registration fit.
    for p in raw:
        for dx in [-.008, .008]:
            for dy in [-.008, .008]:
                for dz in [-.005, .005]:
                    points.append(p + np.array([dx, dy, dz]))
        if p[2] < .100:
            for dx in [-.010, .010]:
                for dy in [-.009, .009]:
                    points.append(np.array([p[0]+dx, p[1]+dy, floor]))
    bm = bmesh.new()
    for p in points:
        bm.verts.new(p.tolist())
    bmesh.ops.convex_hull(bm, input=list(bm.verts), use_existing_faces=False)
    bmesh.ops.delete(bm, geom=[v for v in bm.verts if not v.link_faces], context='VERTS')
    bmesh.ops.bisect_plane(bm, geom=list(bm.verts)+list(bm.edges)+list(bm.faces), dist=1e-7,
        plane_co=(0, 0, cuff), plane_no=(0, 0, 1), clear_outer=True, clear_inner=False)
    bmesh.ops.triangulate(bm, faces=list(bm.faces)); bm.normal_update(); bm.verts.ensure_lookup_table(); bm.verts.index_update()
    inside = Vector(raw[raw[:, 2] < .10].mean(0))
    for f in bm.faces:
        if (f.calc_center_median()-inside).dot(f.normal) < 0:
            f.normal_flip()
    bm.normal_update()
    local_v = np.array([v.co[:] for v in bm.verts]); local_f = [[v.index for v in f.verts] for f in bm.faces]
    boundary = [e for e in bm.edges if len(e.link_faces) == 1]; boundary_ids = sorted({v.index for e in boundary for v in e.verts})
    assert boundary and all(abs(local_v[i, 2]-cuff) < 2e-6 for i in boundary_ids)
    # Convex upper's half-space enclosure is a rest-only proof below the open
    # collar. Include a virtual cuff cap only for the interior test.
    target_ids = selected[bv[selected, 2] < cuff-.010]; violations = []
    for i in target_ids:
        maximum = max((Vector(bv[i])-f.verts[0].co).dot(f.normal) for f in bm.faces)
        if maximum > -1e-4:
            violations.append({'bodyVertexID': int(i), 'maximumOutwardHalfspaceM': maximum})
    upper_offset = len(vertices); add_geometry(local_v.tolist(), local_f, 0)
    bottom_ids = [i for i, p in enumerate(local_v) if abs(p[2]-floor) < 2e-6]
    assert len(bottom_ids) >= 6
    center = local_v[bottom_ids, :2].mean(0); outline = sorted(bottom_ids, key=lambda i: math.atan2(local_v[i, 1]-center[1], local_v[i, 0]-center[0]))
    sole_v = []
    for z in [floor-.004, floor+.014]:
        for i in outline:
            xy = local_v[i, :2]; delta = xy-center; delta /= np.linalg.norm(delta); xy = xy+delta*.003
            sole_v.append([float(xy[0]), float(xy[1]), z])
    count = len(outline); sole_f = [list(range(count-1, -1, -1)), list(range(count, 2*count))]
    for i in range(count):
        j = (i+1)%count; sole_f.append([i, j, j+count, i+count])
    sole_offset = len(vertices); add_geometry(sole_v, sole_f, 1)
    upper_tree = BVHTree.FromPolygons([Vector(p) for p in local_v], local_f, all_triangles=True)
    body_pairs = upper_tree.overlap(body_tree)
    foot_records.append({'side': side, 'bodyFitSourceVertexIDs': selected.tolist(), 'enclosureTestVertexIDs': target_ids.tolist(),
        'upperVertexRange': [upper_offset, upper_offset+len(local_v)], 'soleVertexRange': [sole_offset, sole_offset+len(sole_v)],
        'ankleOpeningNativeVertexIDs': [upper_offset+i for i in boundary_ids], 'ankleOpeningPlaneNativeZ': cuff,
        'ankleBoundaryEdges': len(boundary), 'upperVertices': len(local_v), 'upperTriangles': len(local_f), 'soleOutlineVertices': count,
        'soleBottomNativeZ': floor-.004, 'soleTopNativeZ': floor+.014, 'restBodyUpperTrianglePairs': len(body_pairs),
        'footVertexEnclosureFailures': violations, 'enclosureTestVertices': len(target_ids), 'rawFootBoundsNativeM': [raw.min(0).tolist(), raw.max(0).tolist()],
        'upperBoundsNativeM': [local_v.min(0).tolist(), local_v.max(0).tolist()]})
    bm.free()
mesh = bpy.data.meshes.new('Complete canonical fitted boot uppers soles and ankle openings'); mesh.from_pydata(vertices, [], faces); mesh.update()
boots = bpy.data.objects.new('Complete worn boot volume on own canonical feet', mesh); bpy.context.collection.objects.link(boots); boots.parent = root
for b in rig.data.bones:
    boots.vertex_groups.new(name=b.name)
for i, row in enumerate(weight_rows):
    for name, value in row.items():
        boots.vertex_groups[name].add([i], value, 'REPLACE')
uv = mesh.uv_layers.new(name='UVMap')
for poly in mesh.polygons:
    normal = poly.normal; axis = int(np.argmax(np.abs(normal))); pair = [i for i in range(3) if i != axis]
    for loop in poly.loop_indices:
        p = mesh.vertices[mesh.loops[loop].vertex_index].co; uv.data[loop].uv = (p[pair[0]]*6, p[pair[1]]*6)
for name, color, roughness in [('Black leather complete upper', (.018, .014, .012), .72), ('Rubber outsole separate volume', (.009, .009, .009), .88)]:
    mat = bpy.data.materials.new(name); mat.use_nodes = True; bs = mat.node_tree.nodes['Principled BSDF']; bs.inputs['Base Color'].default_value = (*color, 1)
    bs.inputs['Roughness'].default_value = roughness; bs.inputs['Metallic'].default_value = 0; bs.inputs['Specular IOR Level'].default_value = .125
    mesh.materials.append(mat)
for poly, slot in zip(mesh.polygons, slots):
    poly.material_index = slot; poly.use_smooth = slot == 0
armature = boots.modifiers.new('Own unchanged canonical51joint bind', 'ARMATURE'); armature.object = rig
boots['appearanceConstruction'] = 'Unaccepted07 complete eased uppers, geometric rubber sole, real ankle openings; old partial fragments hidden'
root['rockhopAppearanceCandidate'] = 'unaccepted appearance07 complete fitted footwear volumes'
for o in bpy.data.objects:
    o.select_set(False)
for o in [o for o in bpy.data.objects if o.type == 'MESH' and not o.hide_render] + [root, rig]:
    o.select_set(True)
bpy.context.view_layer.objects.active = rig
bpy.ops.wm.save_as_mainfile(filepath=str(out/'rider.blend'), compress=True)
bpy.ops.export_scene.gltf(filepath=str(out/'rider.glb'), export_format='GLB', use_selection=True, export_yup=True,
    export_animations=False, export_attributes=True, export_extras=True, export_morph=True)
controller = json.loads((source.parent/'source-normals-controller.json').read_text()); controller.update(status='UNACCEPTED07 complete footwear volume; clothing still rejected',
    candidateMasterSHA256=sha(out/'rider.blend'), candidateGLBSHA256=sha(out/'rider.glb'), parentAppearanceMasterSHA256=source_pin)
(out/'corrective-driver.json').write_text(json.dumps(controller, indent=2)+'\n')
assert sha(source) == source_pin
report = {'status': 'UNACCEPTED complete footwear source checkpoint; rest enclosure is not moving wearable-fit acceptance', 'sourceMasterSHA256': source_pin,
    'masterSHA256': sha(out/'rider.blend'), 'quantizedGLBSHA256': sha(out/'rider.glb'), 'recipeSHA256': sha(__file__), 'nativeVertices': len(vertices), 'nativePolygons': len(faces),
    'feet': foot_records, 'skin': 'Nearest actual native-body triangle barycentric original own weights, top4 normalized; no donor registration or global solver',
    'limits': ['Footwear has complete upper volume and geometric18mm outsole with real open ankle collar; source style/detail/UV/PBR remain unaccepted.',
        'Enclosure is convex half-space rest test on canonical foot vertices below cuff minus10mm; virtual cuff plane does not close wearable opening.',
        'Rest body upper contacts can include the collar zone and must be located; continuous ankle/foot motion and actual engine collision/constraint fit remain required.',
        'Protected body/head/bind/source05 and existing rejected garment controls remain; old partial donor boots hidden rather than repaired or promoted.',
        'Protected raw NORMAL derivative, independent fullfield verification and moving footage follow before engine handoff; no fullart/device/player acceptance.']}
(evidence/'construction.json').write_text(json.dumps(report, indent=2)+'\n')
print('COMPLETE_FOOTWEAR_READY', report['masterSHA256'], [(f['side'], f['enclosureTestVertices'], len(f['footVertexEnclosureFailures']), f['restBodyUpperTrianglePairs']) for f in foot_records], flush=True)
