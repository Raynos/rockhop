"""Exact selected boot/glove only: local-coordinate reduction, fresh UV, actual bake.

Native GLB coordinates remain unchanged; this does not import or export a rig.
The source corner normals, material images and source skin joint order are read
from the pinned GLB extraction. Outputs are experiments, never player assets.
"""
import bpy, numpy as np, json, sys, time, math, hashlib
from pathlib import Path
from mathutils import Vector
from mathutils.bvhtree import BVHTree
MODE,IN,OUT=sys.argv[sys.argv.index('--')+1:]
IN,OUT=Path(IN).resolve(),Path(OUT).resolve();OUT.mkdir(parents=True,exist_ok=True)

def log(s): print(s,flush=True)
def read(name,dtype,width):return np.fromfile(IN/(name+'.bin'),dtype=dtype).reshape(-1,width)
def arr(items,field,width,dtype=np.float32):
 a=np.empty((len(items),width),dtype);items.foreach_get(field,a.ravel());return a

def bary(p,a,b,c):
 v0=b-a;v1=c-a;v2=p-a;d00=v0@v0;d01=v0@v1;d11=v1@v1;d20=v2@v0;d21=v2@v1
 den=d00*d11-d01*d01
 if abs(den)<1e-30:return np.array([1,0,0],np.float64)
 v=(d11*d20-d01*d21)/den;w=(d00*d21-d01*d20)/den
 q=np.clip([1-v-w,v,w],0,1);return q/q.sum()
def stats(a):
 a=np.asarray(a);return dict(mean=float(a.mean()),p95=float(np.quantile(a,.95)),p99=float(np.quantile(a,.99)),max=float(a.max()))
def mesh_object(name,pos,tri):
 m=bpy.data.meshes.new(name);m.from_pydata(pos.tolist(),[],tri.tolist());m.update()
 o=bpy.data.objects.new(name,m);bpy.context.collection.objects.link(o);return o

def audit_fields(high,low,images,OUT):
 mat=high.data.materials[0];nodes=mat.node_tree.nodes
 # Quantify actual atlas fields at deterministic low triangle centroids.
 # This reports observed errors, including thin-wall/ray pairing and texel filtering.
 low.data.calc_loop_triangles();low.data.calc_tangents(uvmap='SelectedComponentNewAtlas')
 def pixels(image):
  a=np.empty(image.size[0]*image.size[1]*4,np.float32);image.pixels.foreach_get(a);return a.reshape(image.size[1],image.size[0],4)
 def sample(a,uv):
  h,w=a.shape[:2];q=np.asarray(uv)*[w,h]-.5;q%=np.array([w,h]);x,y=np.floor(q).astype(int);dx,dy=q-[x,y]
  return ((a[y%h,x%w]*(1-dx)+a[y%h,(x+1)%w]*dx)*(1-dy)+(a[(y+1)%h,x%w]*(1-dx)+a[(y+1)%h,(x+1)%w]*dx)*dy)[:3]
 hp=arr(high.data.vertices,'co',3);hf=arr(high.data.loop_triangles,'vertices',3,np.int32) if len(high.data.loop_triangles) else None
 high.data.calc_loop_triangles();hf=arr(high.data.loop_triangles,'vertices',3,np.int32);hl=arr(high.data.loop_triangles,'loops',3,np.int32)
 hn=arr(high.data.corner_normals,'vector',3);hu=arr(high.data.uv_layers.active.data,'uv',2)
 lp=arr(low.data.vertices,'co',3);lf=arr(low.data.loop_triangles,'vertices',3,np.int32);ll=arr(low.data.loop_triangles,'loops',3,np.int32)
 ln=arr(low.data.corner_normals,'vector',3);lu=arr(low.data.uv_layers.active.data,'uv',2);lt=arr(low.data.loops,'tangent',3);lb=arr(low.data.loops,'bitangent_sign',1)
 tree=BVHTree.FromPolygons(hp.tolist(),hf.tolist(),all_triangles=True)
 baked={k:pixels(v) for k,v in images.items()};original={k:pixels(nodes[k].image) for k in ('albedo','orm')}
 errors={'albedo':[],'orm':[],'normalDegrees':[]};ray_errors={'albedo':[],'orm':[],'normalDegrees':[]};probes=[];ray_misses=0
 for f in np.random.default_rng(20261009).choice(len(lf),min(30000,len(lf)),replace=False):
  pos=lp[lf[f]].mean(0);hit,_,face,d=tree.find_nearest(Vector(pos));bc=bary(np.asarray(hit),*hp[hf[face]])
  srcuv=(hu[hl[face]]*bc[:,None]).sum(0);dstuv=lu[ll[f]].mean(0)
  for kind in ('albedo','orm'):errors[kind].append(float(np.abs(sample(original[kind],srcuv)-sample(baked[kind],dstuv)).mean()))
  normal=ln[ll[f]].mean(0);normal/=np.linalg.norm(normal);tangent=lt[ll[f]].mean(0);tangent-=normal*(normal@tangent);tangent/=np.linalg.norm(tangent)
  sign=np.sign(lb[ll[f]].mean());bitangent=np.cross(normal,tangent)*sign
  nm=sample(baked['normal'],dstuv)*2-1;world=tangent*nm[0]+bitangent*nm[1]+normal*nm[2];world/=np.linalg.norm(world)
  expected=(hn[hl[face]]*bc[:,None]).sum(0);expected/=np.linalg.norm(expected)
  angle=math.degrees(math.acos(float(np.clip(world@expected,-1,1))));errors['normalDegrees'].append(angle)
  # Independently measure the actual source surface selected by the declared
  # bake cage. Nearest-face evidence remains intact; neither distribution is
  # silently discarded when near-coincident source walls disagree.
  rayhit,_,rayface,raydistance=tree.ray_cast(Vector(pos+normal*.003),Vector(-normal),.01)
  rayangle=None
  if rayhit is not None:
   raybc=bary(np.asarray(rayhit),*hp[hf[rayface]]);raynormal=(hn[hl[rayface]]*raybc[:,None]).sum(0);raynormal/=np.linalg.norm(raynormal)
   rayuv=(hu[hl[rayface]]*raybc[:,None]).sum(0)
   rayangle=math.degrees(math.acos(float(np.clip(world@raynormal,-1,1))));ray_errors['normalDegrees'].append(rayangle)
   for kind in ('albedo','orm'):ray_errors[kind].append(float(np.abs(sample(original[kind],rayuv)-sample(baked[kind],dstuv)).mean()))
  else:ray_misses+=1
  if angle>15 or errors['albedo'][-1]>.05 or (rayangle is not None and rayangle>15):
   probes.append({'targetFace':int(f),'nearestSourceFace':int(face),'rayFirstSourceFace':None if rayhit is None else int(rayface),'rayDistanceMeters':raydistance,'localPosition':pos.tolist(),'nearestDistanceMeters':d,'sourceUV':srcuv.tolist(),'atlasUV':dstuv.tolist(),'normalToNearestDegrees':angle,'normalToRayFirstDegrees':rayangle,'albedoMeanAbsoluteError':errors['albedo'][-1],'ormMeanAbsoluteError':errors['orm'][-1]})
 field={'samples':30000,'method':'Deterministic low-face centroids, nearest exact source face barycentric source field versus bilinear actual baked2K atlas; includes source facets and filtered texels','errors':{k:stats(v) for k,v in errors.items()},'firstBakeRay':{'method':'Every same receiver centroid ray from +3mm along interpolated receiver normal, -normal direction,10mm max; exactly declared bake-cage starting surface, separate from nearest-face evidence. Not a moving-camera acceptance.', 'hits':len(ray_errors['normalDegrees']),'misses':ray_misses,'errors':{k:stats(v) for k,v in ray_errors.items()},'normalThresholdCounts':{str(q):int((np.asarray(ray_errors['normalDegrees'])>q).sum()) for q in [15,45,90]},'worstLocations':sorted([p for p in probes if p['normalToRayFirstDegrees'] is not None],key=lambda p:p['normalToRayFirstDegrees'],reverse=True)[:30]},'thresholdCounts':{'normalDegrees':{str(q):int((np.asarray(errors['normalDegrees'])>q).sum()) for q in [15,45,90]},'albedoMeanAbsoluteError':{str(q):int((np.asarray(errors['albedo'])>q).sum()) for q in [.05,.1]}},'worstNormalLocations':sorted(probes,key=lambda r:r['normalToNearestDegrees'],reverse=True)[:30],'worstAlbedoLocations':sorted(probes,key=lambda r:r['albedoMeanAbsoluteError'],reverse=True)[:30],'accepted':False}
 (OUT/'field.json').write_text(json.dumps(field,indent=2)+'\n');log(field)


assert MODE=='audit'
bpy.ops.wm.open_mainfile(filepath=str(IN/'prepared.blend'),use_scripts=False)
images={}
for kind in ('albedo','orm','normal'):
 images[kind]=bpy.data.images.load(str(OUT/(kind+'.png')),check_existing=False)
 images[kind].colorspace_settings.name='sRGB' if kind=='albedo' else 'Non-Color'
audit_fields(bpy.data.objects['ExactSelectedComponentDense'],bpy.data.objects['AtlasReducedComponent'],images,OUT)
