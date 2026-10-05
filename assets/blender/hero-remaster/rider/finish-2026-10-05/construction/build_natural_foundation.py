"""One bounded unaccepted outer-neck join, separate inward-shell closure.

Ordered arclength correspondence moves only the admitted body cut boundary
onto the unchanged donor outer loop. Shared edge splits preserve UV seams.
Original objects and all 51 rest/bind/pose fields stay untouched. No nearest
projection, contact-ID deletion, global transform or garment modification.
"""
import hashlib
import json
from collections import deque
from pathlib import Path

import bpy
import numpy as np

root = Path(__file__).resolve().parents[6]
legacy = root / 'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1'
qa = root / 'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03'
owned = Path(__file__).resolve().parent
evidence = root / 'docs/evidence/hero-remaster/finish-2026-10-05/construction/body01'
out = owned / 'body01'
out.mkdir(parents=True, exist_ok=True)
evidence.mkdir(parents=True, exist_ok=True)
native = out / 'natural-foundation.blend'
assert not native.exists(), 'Frozen candidate must not be overwritten'
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
proposal_path = qa / 'body59/proposal.json'
assert sha(proposal_path) == '5f563c032791a9426c0447a2b8c818b140fd62e56a621fd4b81efd461cfdefa6'
scope = json.loads(proposal_path.read_text())['preciseInitialAuthoringMargin']
f0=np.load(evidence.parent/'foundation-source.npz')
scope['headInitialBoundaryLedNativeVertexIDs']=f0['headEditableIDs'].tolist()
n = np.load(qa / 'body52/native-fields.npz')
registry_path = root / 'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/neck-interface96/ordered-boundaries.npz'
r = np.load(registry_path)
source = legacy / 'selected-hoodie26/native-four-with-full-control.blend'
assert sha(source) == '4a0904b94a507f35590d1ec4ebfe763237fa5fb21fa189573842309cb776a0ad'
bpy.ops.wm.open_mainfile(filepath=str(source))
rig = bpy.data.objects['Independent anatomical foundation rig']
names = [b.name for b in rig.data.bones]
assert names == n['boneNames'].tolist()
helper_path = legacy / 'verify_extended_protected_data.py'
definitions = helper_path.read_text()
helpers = dict(bpy=bpy, np=np, hashlib=hashlib, json=json)
exec(compile(definitions[definitions.index('def value('):definitions.index('before=snapshot(original)')], str(helper_path), 'exec'), helpers)

def snapshot(obj):
    if obj.type == 'MESH':
        return {'object': helpers['object_state'](obj), 'mesh': helpers['mesh_extra'](obj.data),
            'positions': helpers['array_digest'](obj.data.vertices, 'co', 3),
            'polygons': [list(f.vertices) for f in obj.data.polygons],
            'weights': [[[obj.vertex_groups[g.group].name, float(g.weight)] for g in v.groups] for v in obj.data.vertices]}
    return helpers['object_state'](obj)

original_names = [o.name for o in bpy.data.objects]
before = {name: snapshot(bpy.data.objects[name]) for name in original_names}
rig_before = {'bones': {b.name: np.array(b.matrix_local).tolist() for b in rig.data.bones},
    'pose': {b.name: {'matrix': np.array(b.matrix).tolist(), 'basis': np.array(b.matrix_basis).tolist()} for b in rig.pose.bones}}
body = bpy.data.objects['Canonical body with hidden head interface']
head = bpy.data.objects['Protected textured head above hidden neck interface']
for obj, key in [(body, 'renderedBody'), (head, 'protectedHead')]:
    p = np.array([v.co[:] for v in obj.data.vertices])
    obj.data.calc_loop_triangles()
    t = np.array([f.vertices[:] for f in obj.data.loop_triangles])
    assert np.array_equal(p, n[key + 'XYZ']) and np.array_equal(t, n[key + 'Triangles'])
    assert not obj.data.shape_keys

def front_start(ids, p):
    return np.roll(ids, -int(np.argmax(p[ids, 0])))

bp, hp = n['renderedBodyXYZ'].copy(), n['protectedHeadXYZ'].copy()
# Native body boundary is clockwise; donor outer boundary is counterclockwise.
body_order = front_start(r['bodyCutOrderedNativeIDs'][::-1], bp)
head_order = front_start(r['outerHeadOrderedNativeRepresentatives'], hp)
def knots(ids, p):
    length = np.linalg.norm((np.roll(p[ids], -1, axis=0) - p[ids])[:, :2], axis=1)
    assert np.min(length) > 0
    return np.r_[0., np.cumsum(length[:-1])] / length.sum()

bu, hu = knots(body_order, bp), knots(head_order, hp)
common_u = np.unique(np.r_[bu, hu])
def segment(u, source_u):
    j = np.searchsorted(source_u, u, side='right') - 1
    j = max(int(j), 0)
    endpoint = float(source_u[j + 1]) if j + 1 < len(source_u) else 1.
    return j, (float(u) - float(source_u[j])) / (endpoint - float(source_u[j]))

shared_positions = []
for u in common_u:
    j, f = segment(u, bu)
    shared_positions.append((1 - f) * bp[body_order[j]] + f * bp[body_order[(j + 1) % len(bu)]])
shared_positions = np.array(shared_positions, dtype=np.float32)
seam_weights = np.zeros(51, dtype=np.float32)
seam_weights[names.index('neck')] = 1.0
# Canonical anatomical body is authority; source body boundary does not move.
# Derive lower-head topology/positions within admitted aliases.
canonical=f0['canonicalXYZ'].astype(float);canonical_tri=f0['canonicalTriangles']
canonical_w=f0['canonicalWeights']
from mathutils import Vector
from mathutils.bvhtree import BVHTree
necktri=canonical_tri[np.all((canonical[canonical_tri,2]>1.49)&(canonical[canonical_tri,2]<1.62),axis=1)]
necktree=BVHTree.FromPolygons([Vector(x) for x in canonical],necktri.tolist(),all_triangles=True)
def canonical_sample(point):
 q,normal,ti,d=necktree.find_nearest(Vector(point)); ids=necktri[ti]
 a,b,c=canonical[ids];v0=b-a;v1=c-a;v2=np.array(q)-a
 d00=v0@v0;d01=v0@v1;d11=v1@v1;d20=v2@v0;d21=v2@v1;den=d00*d11-d01*d01
 bb=(d11*d20-d01*d21)/den;cc=(d00*d21-d01*d20)/den
 bary=np.array([1-bb-cc,bb,cc]);w=bary@canonical_w[ids];w=np.maximum(w,0);w/=w.sum()
 return np.array(q),w
def canonical_radius(z,theta):
 origin=Vector((.035,0,z));direction=Vector((np.cos(theta),np.sin(theta),0))
 q,nn,ti,d=necktree.ray_cast(origin,direction,1.)
 assert q is not None,(z,theta)
 return np.array(q)
# Distance labels across the lower open shell explicitly distinguish outer/inner.
alias=r['headPositionAlias']; adj=[set() for _ in range(int(alias.max())+1)]
for tri in alias[n['protectedHeadTriangles']]:
 for a,b in zip(tri,np.roll(tri,-1)):adj[int(a)].add(int(b));adj[int(b)].add(int(a))
from collections import deque
def layer_distance(seed):
 dd=np.full(len(adj),100000,np.int32);queue=deque(map(int,seed));dd[list(seed)]=0
 while queue:
  v=queue.popleft()
  for other in adj[v]:
   if dd[other]>dd[v]+1:dd[other]=dd[v]+1;queue.append(other)
 return dd[alias]
outer_d=layer_distance(r['outerHeadOrderedVirtualIDs']);inner_d=layer_distance(r['innerHeadOrderedVirtualIDs'])
head_layer=(inner_d<outer_d).astype(np.int32)
allowed=set(scope['headInitialBoundaryLedNativeVertexIDs'])
# C2 compact blend ends at1.585m, leaving a geometric safety collar below face.
head_shape_changed=[]
for v in sorted(allowed):
 x=hp[v].astype(float);z=float(x[2])
 if z>=1.585:continue
 t=np.clip((z-1.525)/.060,0,1);alpha=1-(6*t**5-15*t**4+10*t**3)
 theta=np.arctan2(x[1],x[0]+.017)
 newz=z+alpha*.012
 q=canonical_radius(newz,theta)
 direction=q-np.array([.035,0,newz]);direction[2]=0;direction/=np.linalg.norm(direction)
 if head_layer[v]:q-=.004*direction
 hp[v]=(alpha*q+(1-alpha)*x).astype(np.float32);head_shape_changed.append(v)
# All original position aliases derive one Float32 physical point.
for virtual in np.unique(alias[list(allowed)]):
 ids=np.flatnonzero(alias==virtual)
 if set(ids)<=allowed:hp[ids]=hp[ids[0]]
shared_full=[]
for p in shared_positions:
 _,w=canonical_sample(p);shared_full.append(w)
shared_full=np.array(shared_full,np.float32)
shared_four=shared_full.copy()
for i,w in enumerate(shared_full):
 keep=sorted(np.flatnonzero(w>0),key=lambda j:(-float(w[j]),int(j)))[:4];shared_four[i]=0;shared_four[i,keep]=w[keep]/w[keep].sum()

def distances(triangles, seeds):
    adj = [set() for _ in range(int(triangles.max()) + 1)]
    for a, b, c in triangles:
        adj[a].update([int(b), int(c)]); adj[b].update([int(a), int(c)]); adj[c].update([int(a), int(b)])
    d = np.full(len(adj), 100000, dtype=np.int32)
    queue = deque(map(int, seeds))
    for v in seeds: d[v] = 0
    while queue:
        v = queue.popleft()
        if d[v] >= 2: continue
        for other in adj[v]:
            if d[other] > d[v] + 1:
                d[other] = d[v] + 1; queue.append(other)
    return d

body_dist = distances(n['renderedBodyTriangles'], body_order)
alias = r['headPositionAlias']
head_seeds = np.r_[r['outerHeadOrderedVirtualIDs'], r['innerHeadOrderedVirtualIDs']]
head_dist = distances(alias[n['protectedHeadTriangles']], head_seeds)[alias]
body_full = n['originalFullWeights'][n['renderedBodySourceIDs'].astype(int)].copy()
body_four = n['renderedBodyWeights'].copy()
head_full = n['protectedHeadWeights'].copy()
changed = {'headShapeNativeIDs':head_shape_changed}
# Canonical weights drive the authored lower neck; upper source fields remain exact.
for v in head_shape_changed:
 _,w=canonical_sample(hp[v]); t=np.clip((n['protectedHeadXYZ'][v,2]-1.55)/.035,0,1)
 blend=6*t**5-15*t**4+10*t**3
 head_full[v]=(1-blend)*w+blend*head_full[v]/head_full[v].sum()
head_four=head_full.copy()
for i,w in enumerate(head_full):
 if i not in allowed:continue
 keep=sorted(np.flatnonzero(w>0),key=lambda j:(-float(w[j]),int(j)))[:4]
 head_four[i]=0;head_four[i,keep]=w[keep]/w[keep].sum()

type_info = {'FLOAT': ('value', 1, np.float32), 'INT': ('value', 1, np.int32),
    'BOOLEAN': ('value', 1, np.bool_), 'FLOAT2': ('vector', 2, np.float32),
    'FLOAT_VECTOR': ('vector', 3, np.float32), 'FLOAT_COLOR': ('color', 4, np.float32),
    'BYTE_COLOR': ('color', 4, np.float32), 'INT32_2D': ('value', 2, np.int32),
    'INT16_2D': ('value', 2, np.int32)}
arrays = {'commonU': common_u, 'sharedRestFloat32XYZ': shared_positions, 'sharedSemanticWeights': seam_weights,
    'bodyOriginalFrontOrderedIDs': body_order, 'headOriginalFrontOrderedIDs': head_order,
    'bodyOriginalKnots': bu, 'headOriginalKnots': hu}
rows = []
objects = []
for obj, key, order, old_u, field_full, field_four, admitted in [
    (body, 'body', body_order, bu, body_full, body_four, scope['bodyExistingRenderedNativeVertices']),
    (head, 'head', head_order, hu, head_full, head_four, scope['headInitialBoundaryLedNativeVertexIDs'])]:
    mesh = obj.data
    positions = (hp if key=='head' else bp).tolist()
    old_count = len(positions)
    vf, v4 = list(field_full), list(field_four)
    point_sources = [(i, i, 0.) for i in range(old_count)]
    seam_id = np.full(old_count, -1, dtype=np.int32).tolist()
    edge_splits = {}
    by_virtual = {int(alias[v]): i for i, v in enumerate(order)} if key == 'head' else {int(v): i for i, v in enumerate(order)}
    # Each raw UV edge receives its own aliases, but one physical shared knot.
    boundary_edges = set()
    for f in mesh.polygons:
        ids = list(f.vertices)
        for a, b in zip(ids, ids[1:] + ids[:1]):
            va, vb = (int(alias[a]), int(alias[b])) if key == 'head' else (a, b)
            if va in by_virtual and vb in by_virtual:
                ia, ib = by_virtual[va], by_virtual[vb]
                if (ia + 1) % len(order) == ib or (ib + 1) % len(order) == ia:
                    boundary_edges.add(tuple(sorted((a, b))))
    for v in range(old_count):
        virtual = int(alias[v]) if key == 'head' else v
        if virtual in by_virtual:
            i = by_virtual[virtual]; sid = int(np.searchsorted(common_u, old_u[i]))
            positions[v] = shared_positions[sid].tolist(); vf[v] = shared_full[sid].copy(); v4[v] = shared_four[sid].copy(); seam_id[v] = sid
    for a, b in sorted(boundary_edges):
        va, vb = (int(alias[a]), int(alias[b])) if key == 'head' else (a, b)
        ia, ib = by_virtual[va], by_virtual[vb]
        start, end = (ia, ib) if (ia + 1) % len(order) == ib else (ib, ia)
        raw_start, raw_end = (a, b) if start == ia else (b, a)
        lo = float(old_u[start]); hi = float(old_u[end]) if end else 1.
        inserted = []
        for sid in np.flatnonzero((common_u > lo) & (common_u < hi)):
            fraction = (float(common_u[sid]) - lo) / (hi - lo)
            vertex = len(positions); positions.append(shared_positions[sid].tolist())
            vf.append(shared_full[sid].copy()); v4.append(shared_four[sid].copy()); seam_id.append(int(sid))
            point_sources.append((raw_start, raw_end, fraction)); inserted.append((vertex, fraction))
        edge_splits[(raw_start, raw_end)] = inserted
        edge_splits[(raw_end, raw_start)] = [(v, 1 - f) for v, f in reversed(inserted)]
    polygons = []; corner_sources = []; changed_polygons = []
    for poly in mesh.polygons:
        ids = list(poly.vertices); loops = list(poly.loop_indices); face = []
        for i, a in enumerate(ids):
            b = ids[(i + 1) % len(ids)]; la, lb = loops[i], loops[(i + 1) % len(ids)]
            face.append(a); corner_sources.append((la, la, 0.))
            for v, factor in edge_splits.get((a, b), []):
                face.append(v); corner_sources.append((la, lb, factor))
        polygons.append(face)
        if face != ids: changed_polygons.append(poly.index)
    # Close only the inward shell, oppositely oriented to its open rim.
    cap_faces = []
    if key == 'head':
        inner_order = r['innerHeadOrderedNativeRepresentatives']
        center = len(positions); positions.append(hp[inner_order].mean(axis=0).astype(np.float32).tolist())
        vf.append(np.mean(head_full[inner_order],axis=0)); v4.append(np.mean(head_four[inner_order],axis=0)); seam_id.append(-1)
        point_sources.append((-1, -1, 0.))
        # Explicitly condition the derived cap field; all old corners remain
        # inherited. A mean of four-slot rows is not itself four-slot.
        keep=sorted(np.flatnonzero(v4[-1]>0),key=lambda j:(-float(v4[-1][j]),int(j)))[:4]
        oldrow=v4[-1].copy();v4[-1]=np.zeros(51,np.float32);v4[-1][keep]=oldrow[keep]/oldrow[keep].sum()
        for a, b in zip(inner_order, np.roll(inner_order, -1)):
            cap_faces.append(len(polygons)); polygons.append([int(b), int(a), center])
            corner_sources.extend([(-1, -1, 0.)] * 3)
    new = bpy.data.meshes.new('Finish natural ' + key)
    new.from_pydata(positions, [], polygons); new.update()
    for material in mesh.materials: new.materials.append(material)
    for i, poly in enumerate(new.polygons):
        if i < len(mesh.polygons):
            poly.material_index = mesh.polygons[i].material_index; poly.use_smooth = mesh.polygons[i].use_smooth
        else: poly.material_index = 0; poly.use_smooth = True
    # Preserve original attributes on unchanged old domains, and record edge
    # interpolation as attribute ancestry rather than claiming source identity.
    unsupported = []
    for attr in mesh.attributes:
        if attr.name in ['position', '.corner_vert', '.corner_edge', '.edge_verts']:
            continue
        if attr.data_type not in type_info:
            unsupported.append([attr.name, attr.data_type, attr.domain]); continue
        prop, width, dtype = type_info[attr.data_type]
        values = np.empty(len(attr.data) * width, dtype=dtype); attr.data.foreach_get(prop, values); values = values.reshape(-1, width)
        dest = new.attributes.get(attr.name) or new.attributes.new(attr.name, attr.data_type, attr.domain)
        dv = np.zeros((len(dest.data), width), dtype=dtype)
        if attr.domain in ['POINT', 'CORNER']:
            refs = point_sources if attr.domain == 'POINT' else corner_sources
            for i, (a, b, f) in enumerate(refs):
                if a >= 0:
                    dv[i] = (1 - f) * values[a] + f * values[b] if np.issubdtype(dtype, np.floating) else values[a]
                elif np.issubdtype(dtype, np.integer): dv[i] = -1
        elif attr.domain == 'FACE': dv[:len(values)] = values
        elif attr.domain == 'EDGE':
            old_edges = {tuple(sorted(e.vertices)): e.index for e in mesh.edges}
            for e in new.edges:
                j = old_edges.get(tuple(sorted(e.vertices)))
                if j is not None: dv[e.index] = values[j]
        else: raise AssertionError(attr.domain)
        dest.data.foreach_set(prop, dv.ravel())
    assert not unsupported, unsupported
    new.update(); new.calc_loop_triangles()
    triangles = np.array([t.vertices[:] for t in new.loop_triangles], dtype=np.int32)
    local_tri = np.array([t.index for t in new.loop_triangles if t.polygon_index in cap_faces or any(v >= old_count or v in admitted for v in t.vertices)], dtype=np.int32)
    # Existing fields outside the admitted lists retain original values.
    outside = np.setdiff1d(np.arange(old_count), admitted)
    assert np.array_equal(np.array(positions, dtype=np.float32)[outside], np.array([v.co[:] for v in mesh.vertices], dtype=np.float32)[outside])
    baseline_four = n['renderedBodyWeights'] if key == 'body' else n['protectedHeadWeights']
    assert np.array_equal(np.array(v4)[outside], baseline_four[outside])
    assert len(positions) == len(point_sources) == len(seam_id)
    for label, field in [('full', vf), ('four', v4)]:
        candidate = obj.copy(); candidate.data = new.copy(); candidate.name = 'Finish ' + key + ' ' + label.upper()
        bpy.context.collection.objects.link(candidate)
        candidate.vertex_groups.clear()
        for group in obj.vertex_groups:candidate.vertex_groups.new(name=group.name)
        for name in names:
            if candidate.vertex_groups.get(name) is None:candidate.vertex_groups.new(name=name)
        for i,v in enumerate(obj.data.vertices):
            for g in v.groups:
                groupname=obj.vertex_groups[g.group].name
                if groupname not in names:candidate.vertex_groups[groupname].add([i],g.weight,'REPLACE')
        for i, weight in enumerate(field):
            for j in np.flatnonzero(weight > 0): candidate.vertex_groups[names[j]].add([i], float(weight[j]), 'REPLACE')
        candidate.hide_render = True; candidate.hide_set(True)
        objects.append(candidate.name)
        assert label != 'four' or np.max((np.array(field) > 0).sum(axis=1)) <= 4
    arrays.update({key + 'RestXYZ': np.array(positions, dtype=np.float32), key + 'Triangles': triangles,
        key + 'FullWeights': np.array(vf, dtype=np.float32), key + 'FourWeights': np.array(v4, dtype=np.float32),
        key + 'SeamPhysicalIDs': np.array(seam_id, dtype=np.int32), key + 'AttributeEdgeSources': np.array(point_sources),
        key + 'CornerAttributeEdgeSources': np.array(corner_sources), key + 'LocalTriangleIDs': local_tri,
        key + 'TriangleSourcePolygonIDs': np.array([t.polygon_index if t.polygon_index < len(mesh.polygons) else -1 for t in new.loop_triangles], dtype=np.int32)})
    if key == 'head':
        closure_ids = np.full(len(positions), -1, dtype=np.int32)
        for i, v in enumerate(r['innerHeadOrderedNativeRepresentatives']):
            closure_ids[np.flatnonzero(alias == alias[v])] = i
        closure_ids[center] = len(r['innerHeadOrderedNativeRepresentatives'])
        arrays['headInnerClosurePhysicalIDs'] = closure_ids
    changed_ids = np.flatnonzero(np.linalg.norm(np.array(positions[:old_count]) - np.array([v.co[:] for v in mesh.vertices]), axis=1) > 0)
    assert set(changed_ids) <= set(admitted)
    rows.append({'part': key, 'originalVertices': old_count, 'candidateVertices': len(positions), 'newVertices': len(positions) - old_count,
        'changedExistingPositionIDs': changed_ids.tolist(), 'splitOriginalPolygonIDs': changed_polygons, 'newInwardCapPolygonIDs': cap_faces,
        'localTrianglesIncludingOneCorner': len(local_tri), 'outsidePositionAndFourWeightExact': True,
        'innerClosure': 'Original inward boundary, reverse-oriented190triangle fan to a new centroid; no body join.' if key == 'head' else None})
for key in ['body', 'head']:
    sid = arrays[key + 'SeamPhysicalIDs']; mask = sid >= 0
    assert np.array_equal(arrays[key + 'RestXYZ'][mask], shared_positions[sid[mask]])
    assert np.array_equal(arrays[key + 'FourWeights'][mask], shared_four[sid[mask]])
    assert set(sid[mask]) == set(range(len(common_u)))
for name in original_names: assert before[name] == snapshot(bpy.data.objects[name]), name
assert rig_before == {'bones': {b.name: np.array(b.matrix_local).tolist() for b in rig.data.bones},
    'pose': {b.name: {'matrix': np.array(b.matrix).tolist(), 'basis': np.array(b.matrix_basis).tolist()} for b in rig.pose.bones}}

# Every new derivative uses an exact-bind copied animation rig.
finish_rig=rig.copy();finish_rig.data=rig.data.copy();finish_rig.name='Finish rig';bpy.context.collection.objects.link(finish_rig)
finish_rig.animation_data_clear()
for pb in finish_rig.pose.bones:pb.matrix_basis.identity()
for name in objects:
 candidate=bpy.data.objects[name]
 for mod in candidate.modifiers:
  if mod.type=='ARMATURE':mod.object=finish_rig;mod.use_deform_preserve_volume=False
 for attrname,values in [('_NATIVE_ID',np.arange(len(candidate.data.vertices),dtype=np.int32)),('_SOURCE_ID',np.r_[np.arange(len(body.data.vertices) if 'body' in name else len(head.data.vertices),dtype=np.int32),np.full(len(candidate.data.vertices)-(len(body.data.vertices) if 'body' in name else len(head.data.vertices)),-1,dtype=np.int32)])]:
  attr=candidate.data.attributes.get(attrname) or candidate.data.attributes.new(attrname,'INT','POINT');attr.data.foreach_set('value',values)
 for attrname,values in [('_CORNER_ID',np.arange(len(candidate.data.loops),dtype=np.int32))]:
  attr=candidate.data.attributes.new(attrname,'INT','CORNER');attr.data.foreach_set('value',values)
# Opaque boxer is a new conservative canonical-surface shell; same skeletal field
# as skin prevents independent pelvis/thigh attachment jumps.
import bmesh
box_source=bpy.data.objects['Canonical anatomical body, baked adult hm08']
for label in ['FULL','FOUR']:
 boxer=box_source.copy();boxer.data=box_source.data.copy();boxer.name='Finish boxer '+label;bpy.context.collection.objects.link(boxer)
 bm=bmesh.new();bm.from_mesh(boxer.data)
 kill=[v for v in bm.verts if v.co.z<.665 or v.co.z>1.06]
 bmesh.ops.delete(bm,geom=kill,context='VERTS');bm.normal_update()
 for v in bm.verts:v.co+=v.normal*.009
 bm.to_mesh(boxer.data);bm.free()
 for mod in boxer.modifiers:
  if mod.type=='ARMATURE':mod.object=finish_rig;mod.use_deform_preserve_volume=False
 boxer.data.materials.clear();boxer.data.materials.append(bpy.data.objects['Opaque boxer fitting garment'].data.materials[0])
 # Preserve auxiliary memberships but normalize only the51 bone field.
 for v in boxer.data.vertices:
  ww={boxer.vertex_groups[g.group].name:g.weight for g in v.groups if boxer.vertex_groups[g.group].name in names and g.weight>0}
  keep=sorted(ww,key=lambda x:(-ww[x],names.index(x)))[:4] if label=='FOUR' else list(ww)
  for gn in ww:boxer.vertex_groups[gn].remove([v.index])
  total=sum(ww[gn] for gn in keep)
  for gn in keep:boxer.vertex_groups[gn].add([v.index],ww[gn]/total,'REPLACE')
 for attrname in ['_NATIVE_ID','_SOURCE_ID']:
  attr=boxer.data.attributes.get(attrname) or boxer.data.attributes.new(attrname,'INT','POINT');attr.data.foreach_set('value',np.arange(len(boxer.data.vertices),dtype=np.int32))
 boxer.hide_render=True;boxer.hide_set(True);objects.append(boxer.name)
# Cheek source copy is untouched in geometry/material/UV/normals/field.
cheek=bpy.data.objects['Protected coherent cheek patch'].copy();cheek.data=cheek.data.copy();cheek.name='Finish coherent cheek';bpy.context.collection.objects.link(cheek)
for mod in cheek.modifiers:
 if mod.type=='ARMATURE':mod.object=finish_rig
cheek.hide_render=True;cheek.hide_set(True);objects.append(cheek.name)
for name in objects:
 ob=bpy.data.objects[name]
 if 'FOUR' in name or name==cheek.name:ob.hide_set(False);ob.hide_render=False
bpy.context.view_layer.update()
normal_report={}
for key in ['head']:
 candidate=bpy.data.objects['Finish '+key+' FOUR'];mesh=candidate.data
 refs=arrays['headCornerAttributeEdgeSources'];source_corner=refs[:,0].astype(int)
 valid=source_corner>=0;mask=valid.copy();mask[valid]=np.isin(f0[key+'CornerVertexIDs'][source_corner[valid]],f0['headProtectedIDs'])
 decoded=np.array([v.vector[:] for v in mesh.corner_normals],dtype=np.float32)
 expected=np.zeros_like(decoded);expected[valid]=f0[key+'CornerNormals'][source_corner[valid]];difference=np.linalg.norm(decoded-expected,axis=1)
 normal_report={'protectedCorners':int(mask.sum()),'changedProtectedCorners':int(np.count_nonzero(np.any(decoded[mask]!=expected[mask],axis=1))),'maximumProtectedDelta':float(difference[mask].max()),'upperPositionsExact':bool(np.array_equal(np.array([v.co[:] for v in mesh.vertices],np.float32)[f0['headProtectedIDs']],f0['headXYZ'][f0['headProtectedIDs']]))}
(evidence/'pre-save-normal-check.json').write_text(json.dumps(normal_report,indent=2)+'\n')
print('PROTECTED_NORMAL_CHECK',normal_report,flush=True)
# New scene displays only derivatives; original source scene/object flags stay
# unchanged. Shared file-frame coordinate convention is copied without rebinding.
newscene=bpy.data.scenes.new('Finish natural wearer diagnostic')
frame=bpy.data.objects['Foundation file frame, game x0.65'].copy();frame.name='Finish file frame, game x0.65';newscene.collection.objects.link(frame)
finish_rig.parent=frame;newscene.collection.objects.link(finish_rig)
for name in objects:
 ob=bpy.data.objects[name];ob.parent=frame;newscene.collection.objects.link(ob)
bpy.context.window.scene=newscene
np.savez_compressed(out / 'authored-neck-fields.npz', **arrays, boneNames=np.array(names), rigRest=n['rigRest'], rigWorld=n['rigWorld'])
bpy.ops.wm.save_as_mainfile(filepath=str(native), compress=True)
report = {'status': 'UNACCEPTED_NATURAL_FOUNDATION_FIRST_CONSTRUCTION_REQUIRES_QA', 'sourceSHA256': sha(source), 'proposalSHA256': sha(proposal_path),
    'recipeSHA256': sha(__file__), 'registrySHA256': sha(registry_path), 'native': str(native.relative_to(root)), 'nativeSHA256': sha(native),
    'fieldsSHA256': sha(out / 'authored-neck-fields.npz'), 'objects': objects, 'physicalSeamKnots': len(common_u),
    'seamField': {'chest': float(seam_weights[names.index('chest')]), 'neck': float(seam_weights[names.index('neck')])},
    'parts': rows, 'weightEdits': changed, 'originalObjectsExact': len(original_names), 'original51RestBindPoseExact': True,
    'protectedNormals':normal_report,
    'method':'Canonical shoulder boundary remains original. Lower head uses canonical neck ray sections and compact C2 fade ending1.585m; outer seam follows ordered canonical boundary. Separate inner layer and cap; anatomical local neck barycentric fields with upper field fade, full/four controls. Original face/cheek protected. Derived boxer canonical surface shell9mm with inherited semantic skin.',
    'ancestry':'Body original coordinates unchanged except derived edge splits; lower head derived canonical anatomical contour. Full source originals retained; source/edge ancestry explicit. New cap and boxer shell derived; native IDs distinct.',
    'limits': ['Rest topology, local collisions/collapse, all529native/703actual47, reopen and full/four loss remain unverified.',
        'Source26 garment unchanged and failed;490head contacts not waived. All M0-M5/art/device/promotion gates open.']}
(evidence / 'authoring.json').write_text(json.dumps(report, indent=2) + '\n')
print(json.dumps({k:report[k] for k in ['status','physicalSeamKnots','nativeSHA256','objects']},indent=2))
