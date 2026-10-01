"""CPU read-only actual shoe and face deformation witnesses on the new skin."""
import bpy,json,hashlib,numpy as np
from pathlib import Path
from mathutils import Matrix
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind04');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind04');source=R/'rider.blend';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(source)
bpy.ops.wm.open_mainfile(filepath=str(source));rig=next(o for o in bpy.context.scene.objects if o.type=='ARMATURE');rig.matrix_world=Matrix.Scale(1.015,4);body=next(o for o in bpy.context.scene.objects if o.type=='MESH' and 'protected' in o.name.lower());head=next(o for o in bpy.context.scene.objects if o.type=='MESH' and o!=body)
b=np.array([v.co[:] for v in body.data.vertices]);h=np.array([v.co[:] for v in head.data.vertices]);soleids=np.flatnonzero(b[:,2]<.0021);assert len(soleids)>100;ids=np.flatnonzero((h[:,2]>=1.55)&(h[:,1]<.015));ids=ids[np.linspace(0,len(ids)-1,256).astype(int)];pairs=np.linalg.norm(h[ids]-h[ids[0]],axis=1)*1.015;rows=[]
for frame in range(1,25):
 bpy.context.scene.frame_set(frame);bpy.context.view_layer.update();dep=bpy.context.evaluated_depsgraph_get();ev=body.evaluated_get(dep);me=ev.to_mesh();p=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear();ev=head.evaluated_get(dep);me=ev.to_mesh();hp=np.array([v.co[:] for v in me.vertices]);ev.to_mesh_clear()
 rows.append({'frame':frame,'soleVertices':len(soleids),'soleSurfaceMaxDriftM':float(np.linalg.norm((p[soleids]-b[soleids])*1.015,axis=1).max()),'soleMinZ':float(p[soleids,2].min()*1.015),'rigidFacePairMaxErrorM':float(np.abs(np.linalg.norm(hp[ids]-hp[ids[0]],axis=1)*1.015-pairs).max())})
assert sha(source)==before
(O/'surface-audit.json').write_text(json.dumps({'sourceSHA256':before,'sourceUnchanged':True,'actualFrames':rows,'scope':'Literal lowest2.1mm source solevertices and256facialpairdistances acrosssameplayedclip; no seat/palmcontact acceptance','maxSoleDriftM':max(r['soleSurfaceMaxDriftM'] for r in rows),'maxFacePairErrorM':max(r['rigidFacePairMaxErrorM'] for r in rows)},indent=2)+'\n');print('ACTUAL_SURFACE_AUDIT',max(r['soleSurfaceMaxDriftM'] for r in rows),max(r['rigidFacePairMaxErrorM'] for r in rows))
