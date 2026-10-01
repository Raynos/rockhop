"""Read-only diagnosis of atlas interpolation across new cloth faces."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');RUN=R/'autonomous-lanes/C-garment-pattern/trial04';O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/trial04')
def key(o,p):return (p.material_index,tuple(sorted(tuple(float(x) for x in o.data.vertices[i].co) for i in p.vertices)))
source=R/'glove-cleanup/glove-material/isolated-correction01/bodyPBR.blend';master=RUN/'character.blend';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();inputs={str(p):sha(p) for p in [source,master]}
bpy.ops.wm.open_mainfile(filepath=str(source));s=next(o for o in bpy.context.scene.objects if o.type=='MESH');source_keys={key(s,p) for p in s.data.polygons}
bpy.ops.wm.open_mainfile(filepath=str(master));body=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o.name.startswith('UNACCEPTED C modular'));bs=next(n for n in body.data.materials[0].node_tree.nodes if n.type=='BSDF_PRINCIPLED');pending=[l.from_node for l in bs.inputs['Base Color'].links];image=None;seen=set()
while pending:
 n=pending.pop()
 if n in seen:continue
 seen.add(n)
 if n.type=='TEX_IMAGE' and n.image:image=n.image;break
 pending.extend(l.from_node for i in n.inputs for l in i.links)
width,height=image.size;pixels=np.asarray(image.pixels[:],np.float32).reshape(height,width,4);uv=body.data.uv_layers.get('NativeGloveAtlas');newfaces=[p for p in body.data.polygons if key(body,p) not in source_keys];warm=nonwarm=0;examples=[]
for p in newfaces:
 u=np.array([uv.data[i].uv for i in p.loop_indices]);mean=u.mean(0);samples=[mean]+[(mean+co)/2 for co in u]
 for si,co in enumerate(samples):
  rgb=pixels[int(co[1]*height)%height,int(co[0]*width)%width,:3];valid=rgb[0]>.035 and rgb[0]>1.12*rgb[1] and rgb[2]<.85*rgb[1]
  if valid:warm+=1
  else:
   nonwarm+=1
   if len(examples)<20:examples.append({'polygon':p.index,'sample':si,'atlasUV':co.tolist(),'actualRGB':rgb.tolist(),'faceUV':u.tolist()})
report={'status':'FAILED visible cloth UV compatibility; this diagnosis does not change texture or geometry','actualNewClothPolygons':len(newfaces),'actualAtlasImage':image.name,'materialUV':'NativeGloveAtlas exported as materialUV1','warmClothInteriorSamples':warm,'nonWarmInteriorSamples':nonwarm,'nonWarmInteriorExamples':examples,'interpretation':'Independent nearest-cloth vertex projections can land on different original atlas charts. Interpolating a NEW face across those UV coordinates can cross unrelated atlas content, despite each source reference triangle being warm cloth. The visible corrupted patches therefore invalidate any claim of compatible PBR transfer. No generator fault is inferred.','sourceGeometryVsTexture':'Separate from actual cloth/skin penetration and exposed folded lining; both require new construction after old-lineage retirement, not another atlas tweak.','inputs':inputs,'inputsAfter':{p:sha(p) for p in inputs}}
assert inputs==report['inputsAfter'];(O/'uv-interior-failure-audit.json').write_text(json.dumps(report,indent=2)+'\n');print('UV_INTERIOR_AUDIT',len(newfaces),warm,nonwarm,flush=True)
