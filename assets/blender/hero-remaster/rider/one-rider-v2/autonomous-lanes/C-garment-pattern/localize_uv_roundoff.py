"""Localize the four reimport rounding witnesses; inspect actual raw corners."""
import bpy,json,numpy as np,hashlib
from pathlib import Path
from mathutils.kdtree import KDTree
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/trial01')
def capture(o,protected=False):
 m=o.data;m.calc_loop_triangles();u=m.uv_layers.get('NativeGloveAtlas') or (m.uv_layers[1] if len(m.uv_layers)>1 else m.uv_layers.active);out=[]
 for tri in m.loop_triangles:
  p=m.polygons[tri.polygon_index]
  if protected and min(m.vertices[i].co.z for i in p.vertices)>1.45:continue
  pos=np.array([list(o.matrix_world@m.vertices[m.loops[i].vertex_index].co) for i in tri.loops]);uv=np.array([list(u.data[i].uv) for i in tri.loops]);out.append((m.materials[tri.material_index].name,pos,uv))
 return out
bpy.ops.wm.open_mainfile(filepath=str(R/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend'));s=next(o for o in bpy.context.scene.objects if o.type=='MESH');before=capture(s,True)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'autonomous-lanes/C-garment-pattern/trial01/character.glb'));bpy.context.view_layer.update();after=[]
for o in bpy.context.scene.objects:
 if o.type=='MESH':after.extend(capture(o))
tree=KDTree(len(after))
for i,(mat,p,u) in enumerate(after):tree.insert(p.mean(0),i)
tree.balance();position_max=uv_max=0.;bad=[];round_witness=[]
for mat,p,u in before:
 candidates=[]
 for center,i,d in tree.find_range(p.mean(0),2e-6):
  am,ap,au=after[i]
  if am!=mat:continue
  order=np.argmin(np.linalg.norm(p[:,None]-ap[None,:],axis=2),axis=1)
  if len(set(order.tolist()))<3:continue
  pe=float(np.max(np.linalg.norm(p-ap[order],axis=1)));ue=float(np.max(np.linalg.norm(u-au[order],axis=1)));candidates.append((pe+ue,pe,ue,p,ap[order],u,au[order]))
 if not candidates:bad.append({'material':mat,'center':p.mean(0).tolist(),'reason':'No corresponding actual triangle'});continue
 _,pe,ue,p,ap,u,au=min(candidates,key=lambda x:x[0]);position_max=max(position_max,pe);uv_max=max(uv_max,ue)
 if pe>2e-6 or ue>2e-6:bad.append({'material':mat,'center':p.mean(0).tolist(),'positionErrorM':pe,'UVError':ue})
 if sorted(tuple(x) for x in np.round(np.c_[p,u],6))!=sorted(tuple(x) for x in np.round(np.c_[ap,au],6)):round_witness.append({'material':mat,'positionErrorM':pe,'UVError':ue,'sourcePosition':p.tolist(),'reimportPosition':ap.tolist(),'sourceUV':u.tolist(),'reimportUV':au.tolist()})
report={'status':'Read-only raw protected corner localization; not appearance or normal continuity pass','protectedSourceTriangles':len(before),'maximumActualCornerPositionErrorM':position_max,'maximumActualCornerUVError':uv_max,'unmatchedOrAbove2MicrometerTriangles':bad,'rounded1e6Witnesses':round_witness,'measurementUsesMaterialUV1':True}
(O/'raw-corner-localization.json').write_text(json.dumps(report,indent=2)+'\n');print('RAW_CORNERS',json.dumps({k:v for k,v in report.items() if k not in ['rounded1e6Witnesses','unmatchedOrAbove2MicrometerTriangles']}),len(bad),flush=True)
