"""Immutable glove/rest bones only. No pose changes, evaluation, save or render."""
import bpy,numpy as np,json,hashlib
from pathlib import Path
out=Path(__file__).resolve().parent;qa=out.parent;root=Path.cwd();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((qa/'grip73/preparation.json').read_text());reports=[]
for tag,rel in [('native26','selected-hoodie26/native-four-with-full-control.blend'),('native29','neck-interface29/geometry-only-feasibility.blend')]:
 p=root/'assets/blender/hero-remaster/rider/anatomical-foundation-2026-10-03/user-agent1'/rel;h=prep['pins'][str(p.relative_to(root))]['sha256'];assert sha(p)==h;bpy.ops.wm.open_mainfile(filepath=str(p));rig=bpy.data.objects['Independent anatomical foundation rig'];names=list(rig.data.bones.keys());glove=bpy.data.objects['Registered black leather gloves on own finger bind'];mesh=glove.data;mesh.calc_loop_triangles();xyz=np.array([v.co[:] for v in mesh.vertices],float);tris=np.array([t.vertices[:] for t in mesh.loop_triangles],int);weights=np.zeros((len(xyz),51));aux=[]
 for v in mesh.vertices:
  for m in v.groups:
   n=glove.vertex_groups[m.group].name
   if n in names:weights[v.index,names.index(n)]=m.weight
   else:aux.append([v.index,n,m.weight])
 arrays={'boneNames':np.array(names),'rigRest':np.array([np.array(b.matrix_local) for b in rig.data.bones]),'rigWorld':np.array(rig.matrix_world),'heads':np.array([b.head_local[:] for b in rig.data.bones]),'tails':np.array([b.tail_local[:] for b in rig.data.bones]),'parents':np.array([names.index(b.parent.name) if b.parent else -1 for b in rig.data.bones]),'gloveXYZ':xyz,'gloveTriangles':tris,'gloveWeights':weights,'gloveWorld':np.array(glove.matrix_world)}
 np.savez_compressed(out/(tag+'.npz'),**arrays);reports.append({'source':str(p.relative_to(root)),'sha256':h,'boneNames':names,'gloveVertices':len(xyz),'gloveTriangles':len(tris),'auxMemberships':aux,'visible':not glove.hide_render,'constraints':{b.name:[c.type for c in rig.pose.bones[b.name].constraints] for b in rig.data.bones},'fieldsSHA256':sha(out/(tag+'.npz'))});assert sha(p)==h
r={'status':'IMMUTABLE_NATIVE_GLOVE_AND_BONE_READ','blender':bpy.app.version_string,'recipeSHA256':sha(__file__),'sources':reports,'native26Vs29ArrayExact':{k:np.array_equal(np.load(out/'native26.npz')[k],np.load(out/'native29.npz')[k]) for k in arrays}};assert all(r['native26Vs29ArrayExact'].values());(out/'native-read.json').write_text(json.dumps(r,indent=2)+'\n');print('NATIVE_GLOVES_AND_51_BONES_EXACT_26_VS_29',flush=True)
