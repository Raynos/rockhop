"""Pin the immutable foundation and expose precise production repair scope."""
from pathlib import Path
import hashlib,json
import bpy
import numpy as np

ROOT=Path(__file__).resolve().parents[6]
OUT=ROOT/'docs/evidence/hero-remaster/finish-2026-10-05/construction'
OUT.mkdir(parents=True,exist_ok=True)
SOURCE=ROOT/'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1/selected-hoodie26/native-four-with-full-control.blend'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
assert sha(SOURCE)=='4a0904b94a507f35590d1ec4ebfe763237fa5fb21fa189573842309cb776a0ad'
bpy.ops.wm.open_mainfile(filepath=str(SOURCE))
rig=bpy.data.objects['Independent anatomical foundation rig']
rows=[]
arrays={}
for obj in bpy.data.objects:
 if obj.type!='MESH':continue
 p=np.array([v.co[:] for v in obj.data.vertices],dtype=np.float32)
 obj.data.calc_loop_triangles()
 t=np.array([t.vertices[:] for t in obj.data.loop_triangles],dtype=np.int32)
 rows.append({'name':obj.name,'vertices':len(p),'triangles':len(t),'localBounds':[p.min(0).tolist(),p.max(0).tolist()], 'world':np.array(obj.matrix_world).tolist(),'hideRender':obj.hide_render,'hideViewport':obj.hide_viewport,'groups':[g.name for g in obj.vertex_groups]})
 if obj.name in ['Canonical anatomical body, baked adult hm08','Canonical body with hidden head interface','Protected textured head above hidden neck interface','Opaque boxer fitting garment','Protected coherent cheek patch']:
  key={'Canonical anatomical body, baked adult hm08':'canonical','Canonical body with hidden head interface':'displayBody','Protected textured head above hidden neck interface':'head','Opaque boxer fitting garment':'boxers','Protected coherent cheek patch':'cheek'}[obj.name]
  arrays[key+'XYZ']=p;arrays[key+'Triangles']=t
  w=np.zeros((len(p),51),dtype=np.float32)
  names=[b.name for b in rig.data.bones]
  for v in obj.data.vertices:
   for g in v.groups:
    name=obj.vertex_groups[g.group].name
    if name in names:w[v.index,names.index(name)]=g.weight
  arrays[key+'Weights']=w
  arrays[key+'CornerNormals']=np.array([v.vector[:] for v in obj.data.corner_normals],dtype=np.float32)
  arrays[key+'CornerVertexIDs']=np.array([v.vertex_index for v in obj.data.loops],dtype=np.int32)
  for ui,uv in enumerate(obj.data.uv_layers):arrays[key+f'UV{ui}']=np.array([v.uv[:] for v in uv.data],dtype=np.float32)
  if obj.data.attributes.get('custom_normal'):
   attr=obj.data.attributes['custom_normal'];raw=np.empty(len(attr.data)*2,dtype=np.int32);attr.data.foreach_get('value',raw)
   arrays[key+'RawCustomNormals']=raw.reshape(-1,2)
  if key=='canonical':
   shoulder=[names.index(x) for x in ['shoulder.L','shoulder.R','upperArm.L','upperArm.R','chest','neck']]
   hip=[names.index(x) for x in ['pelvis','thigh.L','thigh.R']]
   arrays['bodyShoulderWeightScopeIDs']=np.flatnonzero((p[:,2]>=1.25)&(p[:,2]<=1.60)&(w[:,shoulder].sum(1)>0)).astype(np.int32)
   arrays['bodyHipWeightScopeIDs']=np.flatnonzero((p[:,2]>=.62)&(p[:,2]<=1.08)&(w[:,hip].sum(1)>0)).astype(np.int32)
  if key=='head':
   # All corners sharing protected upper geometry stay protected. A neck
   # transition may alter only complete position-alias classes below 1.60m.
   p64=p.astype(float); alias={}
   for i,x in enumerate(p64):alias.setdefault(tuple(x),[]).append(i)
   protected=set()
   for tri in t:
    if np.any(p[tri,2]>=1.60):protected.update(map(int,tri))
   for tri in t:
    if np.any(p[tri,2]>=1.60):
     for v in tri:protected.update(alias[tuple(p64[v])])
   editable=sorted(set(range(len(p)))-protected)
   arrays['headEditableIDs']=np.array(editable,dtype=np.int32)
   arrays['headProtectedIDs']=np.array(sorted(protected),dtype=np.int32)
   arrays['headUpperIncidentTriangles']=np.flatnonzero(np.any(p[t,2]>=1.60,axis=1)).astype(np.int32)
arrays['boneNames']=np.array([b.name for b in rig.data.bones])
arrays['boneRest']=np.array([np.array(b.matrix_local) for b in rig.data.bones])
arrays['boneSavedPoseBasis']=np.array([np.array(b.matrix_basis) for b in rig.pose.bones])
np.savez_compressed(OUT/'foundation-source.npz',**arrays)
report={'status':'F0 immutable source classification; root admitted derived lower interface; candidate not built','source':str(SOURCE),'sourceSHA256':sha(SOURCE),'nativeCandidate':str(ROOT/'assets/blender/hero-remaster/rider/finish-2026-10-05/construction/body01/natural-foundation.blend'),'rig':rig.name,'derivativeRig':'Finish rig','boneNames':arrays['boneNames'].tolist(),'hierarchy':[{ 'name':b.name,'parent':b.parent.name if b.parent else None,'rest':np.array(b.matrix_local).tolist()}for b in rig.data.bones],'rigWorld':np.array(rig.matrix_world).tolist(),'rigScale':list(rig.scale),'sourceMeshes':rows,'scope':{'headEditableCompleteAliasIDs':arrays['headEditableIDs'].tolist(),'headProtectedCompleteAliasIDs':arrays['headProtectedIDs'].tolist(),'protectedCutoffNativeZ':1.60,'protectedCornerNormalScope':'All source corners incident to protected vertices; original decoded vectors and raw packed fields captured before edits','protectedUVPBR':'All inherited head UV layers and original material/image bytes exact; original coherent cheek geometry/UV/PBR/weights/normals exact','purpose':'Replace malformed lower bust/neck transition in new derivative; protected face/ears/scalp/cheek untouched','body':'Restore original canonical shoulder/neck surface; semantic weight scope IDs in NPZ bodyShoulderWeightScopeIDs and bodyHipWeightScopeIDs','underwear':'Derived opaque fitted boxer construction; original preserved','derivedLowerNormalsAuthorized':True,'newVertexIdentity':'_NATIVE_ID unique derivative row, _SOURCE_ID original source vertex or -1 with ancestry arrays'},'axes':{'native':'+Xforward/+Zup/-Yleft metres','gltf':'+Xforward/+Yup/+Zleft metres','fileRootX':.65,'runtimeWrapperX':-.65},'fieldsSHA256':sha(OUT/'foundation-source.npz'),'recipeSHA256':sha(__file__)}
(OUT/'foundation-contract.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'sourceSHA256':report['sourceSHA256'],'meshNames':[r['name'] for r in rows],'headEditable':len(arrays['headEditableIDs']),'headProtected':len(arrays['headProtectedIDs'])}),flush=True)
