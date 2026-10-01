"""Read-only exact failed selection witness; no selection/patch correction."""
import bpy,json,struct,copy,numpy as np,hashlib,collections,math
from pathlib import Path
from mathutils import Vector,Matrix
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit');source=R/'generation/h21-buzz-native01/model.glb';T=R/'cheek-retopo02'
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit/generation-evidence/h21-buzz-native01/cheek-retopo02')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();prefix=json.loads((O/'unsafe-prefix.json').read_text());removed=set(i for r in prefix['regions'] for i in r['selectedSourceFaceIndices']);data=source.read_bytes();length=struct.unpack_from('<I',data,12)[0];doc=json.loads(data[20:20+length]);binary=bytearray(data[20+length+8:]);prim=doc['meshes'][0]['primitives'][0];a=doc['accessors'][prim['indices']];bv=doc['bufferViews'][a['bufferView']];tri=np.frombuffer(binary,dtype={5125:'<u4',5123:'<u2'}[a['componentType']],offset=bv.get('byteOffset',0)+a.get('byteOffset',0),count=a['count']).copy().reshape(-1,3);kept=tri[[i for i in range(len(tri)) if i not in removed]].astype('<u4').reshape(-1)
while len(binary)%4:binary.append(0)
view=len(doc['bufferViews']);doc['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':kept.nbytes});binary.extend(kept.tobytes());index=len(doc['accessors']);doc['accessors'].append({'bufferView':view,'componentType':5125,'count':len(kept),'type':'SCALAR'});prim['indices']=index;doc['buffers'][0]['byteLength']=len(binary);encoded=json.dumps(doc,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4);binary+=b'\0'*((-len(binary))%4);out=T/'failed-prefix.glb';out.open('xb').write(struct.pack('<III',0x46546c67,2,12+8+len(encoded)+8+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(source));original=next(o for o in bpy.context.scene.objects if o.type=='MESH');points=[tuple(v.co) for v in original.data.vertices];ids={};mapping=[]
for p in points:
 if p not in ids:ids[p]=len(ids)
 mapping.append(ids[p])
edges=collections.defaultdict(list);incident=collections.defaultdict(list)
for p in original.data.polygons:
 physical=[mapping[v] for v in p.vertices]
 for v in physical:incident[v].append(p.index)
 if p.index in removed:continue
 for k in range(3):edges[tuple(sorted((physical[k],physical[(k+1)%3])))].append(p.index)
adj=collections.defaultdict(list)
for edge,faces in edges.items():
 if len(faces)==1:
  a,b=edge;adj[a].append(b);adj[b].append(a)
pinches=[{'physicalVertex':v,'sourceVertexIndices':[i for i,n in enumerate(mapping) if n==v],'retainedBoundaryNeighbors':neighbors,'incidentFaces':[{'sourceFace':i,'removed':i in removed,'sourceVertices':list(original.data.polygons[i].vertices)} for i in incident[v]]} for v,neighbors in adj.items() if len(neighbors)!=2]
unseen={e for e,f in edges.items() if len(f)==1};circuits=[]
physicalPoints={n:list(p) for p,n in ids.items()}
while unseen:
 seed=next(iter(unseen));walk=[seed[0]];current=seed[0];previous=None
 for _ in range(len(unseen)+len(adj)+1):
  nxt=next(v for v in adj[current] if v!=previous);unseen.discard(tuple(sorted((current,nxt))));previous,current=current,nxt
  if current==walk[0]:break
  walk.append(current)
 coords=np.array([physicalPoints[v] for v in walk]);faceIDs=sorted({f for v in walk for f in incident[v] if f not in removed});normals=np.array([tuple(original.data.polygons[i].normal) for i in faceIDs]);circuits.append({'physicalVertexIDs':walk,'vertexCount':len(walk),'sourceLocalBounds':[coords.min(0).tolist(),coords.max(0).tolist()],'meanAdjacentFaceNormalLocal':normals.mean(0).tolist(),'adjacentRetainedSourceFaceIDs':faceIDs})
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(out));scene=bpy.context.scene;meshes=[o for o in scene.objects if o.type=='MESH'];roots=[o for o in scene.objects if o.parent is None];w=json.loads((O.parent/'painted-orientation-witness01/manifest.json').read_text());f=next(v for v in w['views'] if v['label']=='X180');parent=bpy.data.objects.new('Frozen rejected source selection only',None);scene.collection.objects.link(parent)
for obj in roots:matrix=obj.matrix_world.copy();obj.parent=parent;obj.matrix_world=matrix
parent.matrix_world=Matrix.Translation(Vector(f['translation']))@Matrix.Diagonal((f['displayScale'],)*3+(1,))@Matrix.Rotation(math.pi,4,'X')
mat=bpy.data.materials.new('Rejected prefix neutral gray');mat.use_nodes=True;bs=mat.node_tree.nodes['Principled BSDF'];bs.inputs['Base Color'].default_value=(.42,.42,.42,1);bs.inputs['Roughness'].default_value=.65
for obj in meshes:
 obj.data.materials.append(mat);index=len(obj.data.materials)-1
 for p in obj.data.polygons:p.material_index=index
world=bpy.data.worlds.new('Common neutral studio');world.use_nodes=True;world.node_tree.nodes['Background'].inputs[0].default_value=(.16,.16,.16,1);world.node_tree.nodes['Background'].inputs[1].default_value=.65;scene.world=world;target=Vector((0,0,1.5))
for name,pos,power,size in [('Key',(3,-4,4),600,4),('Fill',(-3,-2,2.5),350,4),('Rim',(1,3,3),450,3)]:
 d=bpy.data.lights.new(name,'AREA');d.energy=power;d.shape='DISK';d.size=size;o=bpy.data.objects.new(name,d);scene.collection.objects.link(o);o.location=pos;o.rotation_euler=(target-o.location).to_track_quat('-Z','Y').to_euler()
d=bpy.data.cameras.new('Rejected prefix witness');cam=bpy.data.objects.new(d.name,d);scene.collection.objects.link(cam);scene.camera=cam;d.type='ORTHO';d.ortho_scale=.46;target=Vector((0,0,1.6));scene.render.engine='CYCLES';scene.cycles.device='CPU';scene.cycles.samples=24;scene.cycles.use_denoising=True;scene.render.threads_mode='FIXED';scene.render.threads=2;scene.render.resolution_x=640;scene.render.resolution_y=640;scene.render.resolution_percentage=100;scene.render.image_settings.file_format='PNG';scene.view_settings.view_transform='AgX';views=[]
for name,yaw in [('front',0),('profile',90),('three-quarter',45)]:
 a=math.radians(yaw);cam.location=target+Vector((4*math.sin(a),-4*math.cos(a),0));cam.rotation_euler=(target-cam.location).to_track_quat('-Z','Y').to_euler();p=O/('rejected-prefix-'+name+'.png');scene.render.filepath=str(p);bpy.ops.render.render(write_still=True);views.append({'path':str(p),'SHA256':sha(p)})
(O/'failed-prefix-forensic.json').open('x').write(json.dumps({'status':'REJECTED exact failed selection, no correction/no patch','sourceSHA256':sha(source),'recipeSHA256':sha(Path(__file__)),'originalSelectionFaceIDsUnchanged':True,'removedSourceFaces':len(removed),'retainedSourceFaces':len(tri)-len(removed),'runtimePrefix':str(out),'runtimePrefixSHA256':sha(out),'pinches':pinches,'remainingPhysicalCircuits':circuits,'views':views,'proposedAlternative':'Retire centroid/fan tweak; classify four sheets and deliberately clip/reconstruct exterior skin within explicit anatomical landmarks. No executed correction.','limitations':['Failed prefix is open and unaccepted; not an improved face.','No patch, UV change, texture bake, rig or production modification.']},indent=2)+'\n')
