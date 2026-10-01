"""CPU source/fit object inventory; complete rider assembly is not accepted."""
import bpy,json,numpy as np
from pathlib import Path
repo=Path('/Users/raynos/projects/games/rockhop');out=repo/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/gray-fixture01';out.mkdir(exist_ok=True)
bpy.ops.wm.read_factory_settings(use_empty=True)
source=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind34/rider.glb');bpy.ops.import_scene.gltf(filepath=str(source))
rows=[]
for o in bpy.data.objects:
 if o.type=='MESH':
  rows.append({'name':o.name,'vertices':len(o.data.vertices),'polygons':len(o.data.polygons),'materials':list(o.data.materials.keys()),'materialPolygonCounts':{str(i):sum(p.material_index==i for p in o.data.polygons) for i in range(len(o.data.materials))},'matrixWorld':[list(row) for row in o.matrix_world]})
(out/'source-object-inventory.json').write_text(json.dumps(rows,indent=2)+'\n');print(json.dumps(rows))
