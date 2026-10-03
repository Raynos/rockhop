"""Independently audit sewn donor construction, source preservation and rest fit."""
import bpy,numpy as np,json,hashlib,sys,argparse
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
ap=argparse.ArgumentParser(description=__doc__)
for n in ['source','candidate','out']:ap.add_argument('--'+n,required=True)
a=ap.parse_args(sys.argv[sys.argv.index('--')+1:]);source,candidate,out=[Path(getattr(a,n)).resolve() for n in ['source','candidate','out']]
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
digest=lambda v:hashlib.sha256(json.dumps(v,sort_keys=True,separators=(',',':')).encode()).hexdigest()
def field(data,prop,count,typ):
 arr=np.empty(len(data)*count,dtype=typ);data.foreach_get(prop,arr);return hashlib.sha256(arr.tobytes()).hexdigest()
def default(v):
 try:return list(v)
 except TypeError:return v
def state():
 meshes={}
 for o in bpy.data.objects:
  if o.type!='MESH':continue
  m=o.data
  meshes[o.name]={'positions':field(m.vertices,'co',3,np.float32),'cornerVertices':field(m.loops,'vertex_index',1,np.int32),
   'polygonSizes':field(m.polygons,'loop_total',1,np.int32),'customNormals':m.has_custom_normals,
   'cornerNormals':field(m.corner_normals,'vector',3,np.float32),'uv':{u.name:field(u.data,'uv',2,np.float32) for u in m.uv_layers},
   'weights':digest([[ [o.vertex_groups[g.group].name,float(g.weight)] for g in v.groups] for v in m.vertices]),
   'keys':None if m.shape_keys is None else {k.name:[k.value,field(k.data,'co',3,np.float32)] for k in m.shape_keys.key_blocks},
   'materials':[x.name for x in m.materials],'matrix':[list(r) for r in o.matrix_world]}
 mats={}
 for m in bpy.data.materials:
  if not m.use_nodes:continue
  mats[m.name]={'nodes':sorted([(n.name,n.type,n.image.name if n.type=='TEX_IMAGE' and n.image else None,
    [(i.name,default(i.default_value)) for i in n.inputs if hasattr(i,'default_value')]) for n in m.node_tree.nodes]),
   'links':sorted([(l.from_node.name,l.from_socket.name,l.to_node.name,l.to_socket.name) for l in m.node_tree.links])}
 images={}
 for im in bpy.data.images:
  if im.packed_file:images[im.name]=hashlib.sha256(im.packed_file.data).hexdigest()
  elif im.filepath:
   p=Path(bpy.path.abspath(im.filepath))
   if p.is_file():images[im.name]=sha(p)
 rig=bpy.data.objects['Independent anatomical foundation rig']
 bones={b.name:{'parent':b.parent.name if b.parent else None,'rest':[list(r) for r in b.matrix_local],
  'poseBasis':[list(r) for r in rig.pose.bones[b.name].matrix_basis]} for b in rig.data.bones}
 return meshes,mats,images,bones
bpy.ops.wm.open_mainfile(filepath=str(source));original=state()
bpy.ops.wm.open_mainfile(filepath=str(candidate));current=state()
for label,before,after in zip(['meshes','materials','images','bones'],original,current):
 differences=[n for n,r in before.items() if n not in after or r!=after[n]]
 assert not differences,(label,differences)
garment=bpy.data.objects['Selected Hunyuan sewn wearable, unrigged construction'];body=bpy.data.objects['Canonical anatomical body, baked adult hm08']
def tree(o):
 o.data.calc_loop_triangles();p=[v.co.copy() for v in o.data.vertices];f=[tuple(t.vertices) for t in o.data.loop_triangles]
 return BVHTree.FromPolygons(p,f,all_triangles=True),p,f
gt,gp,gf=tree(garment);bt,bp,bf=tree(body)
pairs=gt.overlap(bt);selfpairs=[(i,j) for i,j in gt.overlap(gt) if i<j and not set(gf[i])&set(gf[j])]
gaps=[]
for p in gp+[sum((gp[i] for i in t),Vector())/3 for t in gf]:
 q,n,tri,distance=bt.find_nearest(p);gaps.append(float((p-q).dot(n)))
coverage=[]
for v,n in zip(body.data.vertices,body.data.vertex_normals):
 w={body.vertex_groups[g.group].name:g.weight for g in v.groups};arm=sum(value for name,value in w.items() if name.startswith(('upperArm.','forearm.')))
 torso=sum(w.get(name,0) for name in ['spine','chest','pelvis'])
 if (arm>.8 or torso>.8) and v.co.z>1.04:
  p,normal,tri,d=gt.ray_cast(v.co+n.vector*1e-6,n.vector,.20)
  coverage.append({'bodyVertex':v.index,'hit':p is not None,'distanceM':float(d) if p is not None else None})
report={'status':'UNACCEPTED independent source/rest geometry preflight; no rig/game/art pass',
 'pins':{str(p):sha(p) for p in [source,candidate]},'recipeSHA256':sha(__file__),
 'originalMeshesExact':len(original[0]),'originalNodeMaterialsExact':len(original[1]),'originalImagesExact':len(original[2]),
 'originalBindAndPoseExact':len(original[3]),'garmentVertices':len(gp),'garmentTriangles':len(gf),
 'bodyTrianglePairs':len(pairs),'nonAdjacentSelfTrianglePairs':len(selfpairs),
 'vertexAndTriangleCentroidLocalSignedNormalGapM':{'min':min(gaps),'p01':float(np.percentile(gaps,1)),'p50':float(np.percentile(gaps,50))},
 'coverageRays':len(coverage),'coverageMisses':[r for r in coverage if not r['hit']],
 'limits':['Local closest-triangle normal is not a global signed-distance/whole-surface thickness guarantee.',
 'Body ray region excludes intended bare hands/head/lower body but masks are proxies, not finished wear/load-bearing acceptance.',
 'Static unrigged construction; arbitrary pose/consumed collision/actual game/mobile/PBR/played art require independent tests and root judgment.']}
out.write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({k:v for k,v in report.items() if k not in ['coverageMisses','limits']}),len(report['coverageMisses']),flush=True)
