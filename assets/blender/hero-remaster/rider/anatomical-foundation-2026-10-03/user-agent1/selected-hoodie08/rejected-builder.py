"""Correct sewn boundaries and construct an open-front dropped-hood seed.

This is structural qualification, not a replacement appearance. The selected
generated hoodie remains the shape/PBR authority after rest seed qualification.
"""
import argparse, collections, hashlib, heapq, json, math, sys
from pathlib import Path
import bpy, bmesh, numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree

ap = argparse.ArgumentParser(description=__doc__)
for key in ['source', 'out', 'evidence']:
    ap.add_argument('--' + key, required=True)
a = ap.parse_args(sys.argv[sys.argv.index('--') + 1:])
source, out, evidence = [Path(getattr(a, key)).resolve() for key in ['source', 'out', 'evidence']]
out.mkdir(parents=True, exist_ok=True); evidence.mkdir(parents=True, exist_ok=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
source_sha = sha(source)
assert source_sha == 'b644e21722cc71f51713fd12c5122702d4d527d10bd118fc7088a5f854b2a643'
assert not (out / 'open-hood-seed.blend').exists(), 'Preserve frozen candidate'
bpy.ops.wm.open_mainfile(filepath=str(source))
body = bpy.data.objects['Canonical anatomical body, baked adult hm08']
pattern = bpy.data.objects['Separate fitted sweatshirt control, hood not constructed']
rig = bpy.data.objects['Independent anatomical foundation rig']
original = np.array([list(v.co) for v in pattern.data.vertices], dtype=np.float64)
vertices = original.copy(); faces = [list(f.vertices) for f in pattern.data.polygons]
assert len(vertices) == 1250 and len(faces) == 1204
edge_count = collections.Counter(tuple(sorted((i, j))) for f in faces for i, j in zip(f, f[1:] + f[:1]))
boundary = {e for e, count in edge_count.items() if count == 1}; loops = []
while boundary:
    first = boundary.pop(); edges = {first}; stack = [first]
    while stack:
        e = stack.pop()
        adjacent = {other for other in boundary if set(other) & set(e)}
        boundary -= adjacent; edges |= adjacent; stack.extend(adjacent)
    loops.append(sorted({i for e in edges for i in e}))
assert sorted(map(len, loops)) == [20, 20, 20, 36]
neck = next(ids for ids in loops if original[ids, 2].min() > 1.5)
cuffs = [ids for ids in loops if abs(original[ids, 1].mean()) > .4]
adjacency = [[] for _ in original]
for i, j in edge_count:
    length = float(np.linalg.norm(original[i] - original[j]))
    adjacency[i].append((j, length)); adjacency[j].append((i, length))
def distances(ids):
    d = np.full(len(original), np.inf); heap = []
    for i in ids: d[i] = 0; heapq.heappush(heap, (0, i))
    while heap:
        value, i = heapq.heappop(heap)
        if value != d[i]: continue
        for j, length in adjacency[i]:
            candidate = value + length
            if candidate < d[j]: d[j] = candidate; heapq.heappush(heap, (candidate, j))
    return d
def blend(d, width):
    t = np.clip(1 - d / width, 0, 1)
    return t * t * (3 - 2 * t)
neck_center = original[neck].mean(0)
radial = original[:, :2] - neck_center[:2]
radial /= np.maximum(np.linalg.norm(radial, axis=1)[:, None], 1e-12)
neck_field = blend(distances(neck), .07)
vertices[:, :2] += radial * (.018 * neck_field[:, None])
cuff_records = []
for ids in cuffs:
    side = 'R' if original[ids, 1].mean() > 0 else 'L'
    bone = rig.data.bones['forearm.' + side]
    anchor = np.array(bone.head_local); axis = np.array(bone.tail_local) - anchor
    axis /= np.linalg.norm(axis)
    delta = original - anchor; r = delta - (delta @ axis)[:, None] * axis
    r /= np.maximum(np.linalg.norm(r, axis=1)[:, None], 1e-12)
    field = blend(distances(ids), .055)
    vertices += field[:, None] * (-.018 * axis + .005 * r)
    cuff_records.append({'side': side, 'boundaryVertices': ids, 'proximalShorteningM': .018,
                         'radialEaseM': .005, 'geodesicBlendWidthM': .055, 'boneAxisNative': axis.tolist()})
# Attach only consecutive rear/side edges. The original front-neck arc remains
# an opening and connects to the free hood mouth through two side boundaries.
center = vertices[neck].mean(0)
angles = {i: math.atan2(vertices[i, 1]-center[1], vertices[i, 0]-center[0]) % (2*math.pi) for i in neck}
attachment = sorted([i for i in neck if math.pi/4 <= angles[i] <= 7*math.pi/4], key=angles.get)
assert len(attachment) >= 12
assert all(tuple(sorted((i,j))) in edge_count and edge_count[tuple(sorted((i,j)))] == 1
           for i,j in zip(attachment, attachment[1:]))
v = vertices.tolist(); rings = [attachment]; rows = 16
for row in range(1, rows+1):
    t = row/rows; ring = []
    for col, old in enumerate(attachment):
        c = col/(len(attachment)-1); back = math.sin(math.pi*c)
        mouth = np.array([.03-.21*back, .145*math.cos(math.pi*c), 1.58+.025*back])
        q = (1-t)*vertices[old]+t*mouth
        q[0] -= .035*math.sin(math.pi*t)*back
        # Keep the side loft above shoulders. Only the broad rear panel descends;
        # the previous uniform side drop crossed shirt/neck in152body witnesses.
        q[2] += .055*math.sin(math.pi*t) - .135*math.sin(math.pi*t)**2*back**8
        ring.append(len(v)); v.append(q.tolist())
    rings.append(ring)
for row in range(rows):
    for col in range(len(attachment)-1):
        faces.append([rings[row][col],rings[row+1][col],rings[row+1][col+1],rings[row][col+1]])
mesh = bpy.data.meshes.new('Open-front sewn seed, selected-donor fit pending')
mesh.from_pydata(v, [], faces); mesh.update()
parent = mesh.attributes.new('source_parent_polygon', type='INT', domain='FACE')
for i, item in enumerate(parent.data): item.value = i
garment = bpy.data.objects.new('Open-front hood structural seed, unrigged', mesh)
bpy.context.collection.objects.link(garment)
garment.parent=body.parent; garment.matrix_parent_inverse=body.matrix_parent_inverse.copy(); garment.matrix_basis=body.matrix_basis.copy()
for o in bpy.data.objects: o.select_set(False)
garment.select_set(True); bpy.context.view_layer.objects.active=garment
sub = garment.modifiers.new('One sewn pattern refinement', 'SUBSURF'); sub.levels=1; sub.render_levels=1
bpy.ops.object.modifier_apply(modifier=sub.name)
bm=bmesh.new(); bm.from_mesh(garment.data); bmesh.ops.recalc_face_normals(bm, faces=list(bm.faces)); bm.to_mesh(garment.data); bm.free()
garment.data.update()
def tree(o):
    o.data.calc_loop_triangles(); p=[v.co.copy() for v in o.data.vertices]; f=[tuple(t.vertices) for t in o.data.loop_triangles]
    return BVHTree.FromPolygons(p, f, all_triangles=True), p, f
gt,gp,gf=tree(garment); bt,bp,bf=tree(body)
contacts=gt.overlap(bt); selfpairs=[(i,j) for i,j in gt.overlap(gt) if i<j and not set(gf[i])&set(gf[j])]
parents=[v.value for v in garment.data.attributes['source_parent_polygon'].data]
panel=lambda i:'shirt' if parents[garment.data.loop_triangles[i].polygon_index]<1204 else 'hood'
bm=bmesh.new(); bm.from_mesh(garment.data); bm.verts.ensure_lookup_table(); bm.verts.index_update()
boundary={e for e in bm.edges if e.is_boundary}; openings=[]
while boundary:
    e=boundary.pop(); found={e}; stack=[e]
    while stack:
        for vertex in stack.pop().verts:
            for other in vertex.link_edges:
                if other in boundary: boundary.remove(other); found.add(other); stack.append(other)
    ids=sorted({v.index for e in found for v in e.verts}); p=np.array([list(bm.verts[i].co) for i in ids])
    openings.append({'vertices':ids,'edges':len(found),'boundsNativeM':[p.min(0).tolist(),p.max(0).tolist()]})
nonmanifold=sum(not e.is_manifold and not e.is_boundary for e in bm.edges); bm.free()
for p in garment.data.polygons: p.use_smooth=True
garment['accepted']=False; garment['constructionStage']='Structural rest qualification only; selected-donor exterior/UV/PBR still required'
material=bpy.data.materials.new('Diagnostic structural seed only, not player appearance');material.diffuse_color=(.35,.35,.35,1)
garment.data.materials.append(material)
for o in bpy.data.objects:
    if o.name.startswith(('Sewn clean hoodie','Separate fitted sweatshirt','Protected mustard hood','Selected hoodie reconstructed')): o.hide_render=True
bpy.ops.wm.save_as_mainfile(filepath=str(out/'open-hood-seed.blend'),compress=True)
assert sha(source)==source_sha
report={'status':'UNACCEPTED open-front sewn seed; static construction only', 'recipeSHA256':sha(__file__),
        'sourceSHA256':source_sha,'candidateSHA256':sha(out/'open-hood-seed.blend'),
        'neckExpansionM':.018,'neckGeodesicBlendWidthM':.07,'cuffs':cuff_records,
        'hoodAttachmentVertices':attachment,'hoodNewRows':rows,'hoodColumns':len(attachment),
        'vertices':len(gp),'triangles':len(gf),'nonBoundaryNonManifoldEdges':nonmanifold,'openings':openings,
        'bodyTrianglePairs':len(contacts),'bodyPairsByPanel':dict(collections.Counter(panel(i) for i,j in contacts)),
        'selfTrianglePairs':len(selfpairs),'selfPairsByPanel':dict(collections.Counter('/'.join(sorted([panel(i),panel(j)])) for i,j in selfpairs)),
        'bodyContactWitnesses':[{'garmentTriangle':i,'bodyTriangle':j,'panel':panel(i)} for i,j in contacts],
        'selfContactWitnesses':[{'triangles':[i,j],'panels':[panel(i),panel(j)]} for i,j in selfpairs],
        'limits':['Boundary surgery is explicit static construction, not consumed collision or pose qualification.',
                  'Grey material is diagnostic only. Selected Hunyuan shape/PBR remains authority; no plain-shirt fallback.',
                  'Body/head/51bind and original garment controls preserved. Root alone judges played art; all M0-M5 open.']}
(evidence/'construction.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({k:report[k] for k in ['vertices','triangles','bodyTrianglePairs','bodyPairsByPanel','selfTrianglePairs','selfPairsByPanel','nonBoundaryNonManifoldEdges']}),flush=True)
