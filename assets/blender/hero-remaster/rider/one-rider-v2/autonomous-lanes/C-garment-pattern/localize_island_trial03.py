"""Read-only exact original IDs of the disconnected four-face nape remnant."""
import bpy,bmesh,json,hashlib
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/trial03')
def key(points):return tuple(sorted(tuple(round(float(x),6) for x in p) for p in points))
bpy.ops.wm.open_mainfile(filepath=str(R/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend'));s=next(o for o in bpy.context.scene.objects if o.type=='MESH');lookup={key([s.data.vertices[i].co for i in q.vertices]):q.index for q in s.data.polygons}
bpy.ops.wm.open_mainfile(filepath=str(R/'autonomous-lanes/C-garment-pattern/trial03/failed-mask-witness.blend'));w=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('FAILED C'));b=bmesh.new();b.from_mesh(w.data);remaining=set(b.faces);parts=[]
while remaining:
 seed=remaining.pop();stack=[seed];part=[seed]
 while stack:
  q=stack.pop()
  for e in q.edges:
   for other in e.link_faces:
    if other in remaining:remaining.remove(other);stack.append(other);part.append(other)
 parts.append(part)
small=min(parts,key=len);assert len(small)==4;ids=sorted(lookup[key([v.co for v in q.verts])] for q in small)
report={'status':'Read-only isolated source-remnant localization; no removal applied','componentFaceCounts':sorted([len(p) for p in parts]),'isolatedFourOriginalSourceFaceIds':ids,'exactTriangleCoordinates':[[list(v.co) for v in q.verts] for q in small],'proposedAlternative':'If still allowed by parent global15-failure count AFTER checkpoint, remove only this disconnected4triangle remnant. No main garment topology widening; original explicit strip unchanged. Otherwise retire source-strip lineage and clean reconstruct from known-simple lower boundary.'}
(O/'isolated-source-remnant.json').write_text(json.dumps(report,indent=2)+'\n');print('ISOLATED_FOUR_IDS',ids,flush=True)
