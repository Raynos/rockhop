"""Inventory/export frozen selected wearable for independent skin/game work.

No source edit. Static garment-only GLB is explicitly unrigged, preserving
selected-source PBR; native file remains original51bind authority.
"""
import argparse,collections,hashlib,json,struct,sys
from pathlib import Path
import bpy,bmesh,numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for k in ['source','preflight','out','evidence']:ap.add_argument('--'+k,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,preflight,out,evidence=[Path(getattr(a,k)).resolve() for k in ['source','preflight','out','evidence']]
out.mkdir(parents=True,exist_ok=True);evidence.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();source_sha=sha(source)
assert source_sha=='6ef79e38e3dc86b635977ba17a2f2f6100721715b002c4e831b8bcce90ed4e93'
assert not (out/'garment-rest.glb').exists(),'Preserve frozen export'
bpy.ops.wm.open_mainfile(filepath=str(source));g=bpy.data.objects['Selected Hunyuan underarm fitted wearable, unrigged']
body=bpy.data.objects['Canonical anatomical body, baked adult hm08'];rig=bpy.data.objects['Independent anatomical foundation rig']
audit=json.loads(preflight.read_text());assert audit['bodyTrianglePairs']==0 and audit['nonAdjacentSelfTrianglePairs']==0
g.data.calc_loop_triangles();f=[tuple(t.vertices) for t in g.data.loop_triangles];p=np.array([list(v.co) for v in g.data.vertices]);gt=BVHTree.FromPolygons([Vector(x) for x in p],f,all_triangles=True)
coverage=[]
for record in audit['coverageMisses']:
    vertex=body.data.vertices[record['bodyVertex']];weights={body.vertex_groups[m.group].name:float(m.weight) for m in vertex.groups if body.vertex_groups[m.group].name in rig.data.bones}
    q,n,tri,distance=gt.find_nearest(vertex.co)
    coverage.append({'bodyVertex':vertex.index,'nativeXYZ':list(vertex.co),'normalNative':list(body.data.vertex_normals[vertex.index].vector),
                     'deformWeights':weights,'dominantJoint':max(weights,key=weights.get),'closestGarmentTriangle':int(tri),
                     'closestGarmentPointNative':list(q),'unsignedClosestDistanceM':float(distance)})
bm=bmesh.new();bm.from_mesh(g.data);bm.verts.ensure_lookup_table();bm.verts.index_update();boundary={e for e in bm.edges if e.is_boundary};openings=[]
while boundary:
    e=boundary.pop();found={e};stack=[e]
    while stack:
        for vertex in stack.pop().verts:
            for other in vertex.link_edges:
                if other in boundary:boundary.remove(other);found.add(other);stack.append(other)
    ids=sorted({v.index for e in found for v in e.verts});xyz=np.array([list(bm.verts[i].co) for i in ids]);center=xyz.mean(0)
    label='right-cuff' if center[1]>.3 else 'left-cuff' if center[1]<-.3 else 'hem' if center[2]<1.3 else 'neck-and-free-hood-mouth'
    openings.append({'role':label,'edges':len(found),'vertices':ids,'centroidNativeM':center.tolist(),'boundsNativeM':[xyz.min(0).tolist(),xyz.max(0).tolist()]})
nonmanifold=sum(not e.is_manifold and not e.is_boundary for e in bm.edges);bm.free();assert len(openings)==4 and nonmanifold==0
textures=[]
for node in g.data.materials[0].node_tree.nodes:
    if node.type=='TEX_IMAGE' and node.image and node.outputs['Color'].is_linked:
        im=node.image;path=Path(bpy.path.abspath(im.filepath)).resolve();assert path.is_file()
        textures.append({'node':node.name,'image':im.name,'path':str(path),'SHA256':sha(path),'pixels':list(im.size),'colorSpace':im.colorspace_settings.name,
                         'destinations':[link.to_socket.name for link in node.outputs['Color'].links]})
assert len(textures)==3
for o in bpy.data.objects:o.select_set(False)
g.hide_set(False);g.select_set(True);bpy.context.view_layer.objects.active=g
glb=out/'garment-rest.glb'
bpy.ops.export_scene.gltf(filepath=str(glb),export_format='GLB',use_selection=True,export_yup=True,
                          export_animations=False,export_skins=False,export_morph=False,export_cameras=False,export_lights=False)
raw=glb.read_bytes();assert raw[:4]==b'glTF';length,kind=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+length]);offset=20+length
binlength,binkind=struct.unpack_from('<II',raw,offset);buffer=raw[offset+8:offset+8+binlength]
assert len(doc['meshes'])==1 and not doc.get('skins') and not doc.get('animations')
def accessor(i):
    a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[a['componentType']]
    size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];start=v.get('byteOffset',0)+a.get('byteOffset',0)
    assert v.get('byteStride',np.dtype(dtype).itemsize*size)==np.dtype(dtype).itemsize*size
    return np.frombuffer(buffer,dtype=dtype,count=a['count']*size,offset=start).reshape(a['count'],size)
primitive=doc['meshes'][0]['primitives'][0];xyz=accessor(primitive['attributes']['POSITION']);indices=accessor(primitive['indices']).ravel()
expected=np.column_stack([p[:,0],p[:,2],-p[:,1]])
# Render rows can split at UV/normals. Every row must remain on an exact native
# vertex, independently of nearest-surface metrics and baked image lineage.
from mathutils.kdtree import KDTree
kd=KDTree(len(expected))
for i,x in enumerate(expected):kd.insert(Vector(x),i)
kd.balance();errors=[];mapping=[]
for x in xyz:
    q,i,d=kd.find(Vector(x));errors.append(float(d));mapping.append(i)
assert max(errors)<1e-7,max(errors)
assert len(indices)==len(f)*3
normals=accessor(primitive['attributes']['NORMAL']);uv=accessor(primitive['attributes']['TEXCOORD_0'])
assert np.isfinite(xyz).all() and np.isfinite(normals).all() and np.isfinite(uv).all()
assert len(doc.get('images',[]))>=2
bones=[{'name':bone.name,'parent':bone.parent.name if bone.parent else None,'headNativeM':list(bone.head_local),
        'tailNativeM':list(bone.tail_local),'restNativeRows':[list(row) for row in bone.matrix_local],
        'poseBasisRows':[list(row) for row in rig.pose.bones[bone.name].matrix_basis]} for bone in rig.data.bones]
assert len(bones)==51
report={'status':'UNACCEPTED frozen selected wearable source for independent skin/game/moving-art qualification',
        'recipeSHA256':sha(__file__),'native':{'path':str(source),'SHA256':source_sha,'garmentObject':g.name,'bodyObject':body.name,'rigObject':rig.name,
                  'vertices':len(p),'triangles':len(f),'garmentWeightsAssigned':len(g.vertex_groups),'garmentWorldRows':[list(row) for row in g.matrix_world]},
        'restExport':{'path':str(glb),'SHA256':sha(glb),'bytes':len(raw),'renderRows':len(xyz),'triangles':len(indices)//3,
                      'nativeVertexMaxErrorM':max(errors),'nodes':doc['nodes'],'scenes':doc['scenes'],'skins':0,'animations':0,
                      'material':doc['materials'][primitive['material']]},
        'axes':'Native local rest metres +Xforward/+Zup/-Yleft; GLB local XYZ=(nativeX,nativeZ,-nativeY). Source garment world includes exactly+.65X file frame; runtime body wrapper-.65X once, do not bake/reapply both.',
        'openings':openings,'nonBoundaryNonManifoldEdges':nonmanifold,'textures':textures,'original51BindAndPose':bones,
        'restPreflight':{'path':str(preflight),'SHA256':sha(preflight),'bodyPairs':0,'selfPairs':0,'coverageRays':1937,'coverageMisses':coverage},
        'limits':['Garment-only GLB is unskinned/no animation, not a normal-player ready asset; native51bind remains authority.',
                  'Static intersections0/fouropenings do not qualify coverage/arbitrary poses/live collisions/root played appearance/iOS. Preserve all12coverage witnesses, no mask relaxation.',
                  'Selected-source10atlas is actual generated PBR; source13fitting modifies donor geometry. Root alone judges likeness/wearing, all M0-M5 open.',
                  'Agent3 independently constructs skin/game/contact/collision derivatives; do not modify frozen native/export/field/textures. No Library duplicate/player promotion.']}
assert sha(source)==source_sha and all(sha(t['path'])==t['SHA256'] for t in textures)
(evidence/'handoff.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'rows':len(xyz),'tris':len(indices)//3,'positionErrorM':max(errors),'openings':[(o['role'],o['edges']) for o in openings],
                  'coverageJoints':dict(collections.Counter(r['dominantJoint'] for r in coverage)),'GLB':sha(glb)}),flush=True)
