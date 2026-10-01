"""Attribute visible rear join artifact to actual GLB triangles/materials."""
import bpy,json
from pathlib import Path
from mathutils import Matrix,Vector
from mathutils.bvhtree import BVHTree
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/parent-assembly/donor-fit03');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/parent-assembly/donor-fit03');bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(R/'rider.glb'));row=next(r for r in json.loads((O/'render-report.json').read_text())['views'] if r['path'].endswith('neck-PBR-rear.png'));matrix=Matrix(row['cameraMatrix']);trees=[]
for obj in bpy.context.scene.objects:
 if obj.type=='MESH':trees.append((obj,BVHTree.FromPolygons([obj.matrix_world@v.co for v in obj.data.vertices],[tuple(p.vertices) for p in obj.data.polygons],all_triangles=False)))
rows=[]
for x,y in [(320,470),(340,470),(380,470),(320,450),(360,450),(410,460),(320,490)]:
 origin=matrix@Vector(((x+.5-320)*.48/640,(320-y-.5)*.48/640,0));direction=matrix.to_3x3()@Vector((0,0,-1));hits=[]
 for obj,tree in trees:
  hit,normal,index,distance=tree.ray_cast(origin,direction)
  if hit is not None:hits.append((distance,obj,index,hit))
 if hits:
  _,obj,index,hit=min(hits,key=lambda r:r[0]);poly=obj.data.polygons[index];mat=obj.data.materials[poly.material_index];rows.append({'pixel':[x,y],'object':obj.name,'polygon':index,'material':mat.name,'hitXYZ':list(hit),'materialIndex':poly.material_index})
(O/'rear-artifact-ray-witness.json').write_text(json.dumps({'readOnly':True,'actualGLB':str(R/'rider.glb'),'rays':rows},indent=2)+'\n')
