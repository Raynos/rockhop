"""Extract actual pre/post-export corner arrays for independent CPU audit."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/neck-native/trial01')
if (R/'export-corners.npz').exists():raise RuntimeError('Frozen corner audit exists')
def extract():
 points=[];uvs=[];materials=[]
 for o in bpy.context.scene.objects:
  if o.type!='MESH':continue
  m=o.data;m.calc_loop_triangles();co=np.empty(len(m.vertices)*3,np.float32);m.vertices.foreach_get('co',co);co=co.reshape(-1,3)
  matrix=np.array(o.matrix_world,dtype=np.float64);co=co@matrix[:3,:3].T+matrix[:3,3]
  ids=np.empty(len(m.loop_triangles)*3,np.int32);loops=np.empty_like(ids);m.loop_triangles.foreach_get('vertices',ids);m.loop_triangles.foreach_get('loops',loops)
  uv=np.empty(len(m.loops)*2,np.float32);m.uv_layers.active.data.foreach_get('uv',uv);uv=uv.reshape(-1,2)
  mat=np.empty(len(m.loop_triangles),np.int32);m.loop_triangles.foreach_get('material_index',mat)
  names=np.array([a.name if a else '' for a in m.materials]);points.append(co[ids].reshape(-1,3,3));uvs.append(uv[loops].reshape(-1,3,2));materials.append(names[mat])
 return np.concatenate(points),np.concatenate(uvs),np.concatenate(materials)
bpy.ops.wm.open_mainfile(filepath=str(R/'body-head.blend'));a=extract();bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'body-head.glb'));bpy.context.view_layer.update();b=extract()
np.savez(R/'export-corners.npz',beforePoints=a[0],beforeUV=a[1],beforeMaterials=a[2],afterPoints=b[0],afterUV=b[1],afterMaterials=b[2])
print('CORNER_ARRAYS',len(a[0]),len(b[0]),flush=True)
