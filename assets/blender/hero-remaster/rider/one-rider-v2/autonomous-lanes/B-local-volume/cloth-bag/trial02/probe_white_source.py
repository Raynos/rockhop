import bpy,numpy as np,json,hashlib,math
from pathlib import Path
from mathutils import Matrix,Vector
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/B-local-volume/cloth-bag/trial02');P=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit/generation/h21-buzz-native01/model.glb');sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();before=sha(P)
bpy.ops.wm.read_factory_settings(use_empty=True);bpy.ops.import_scene.gltf(filepath=str(P));o=max((o for o in bpy.context.scene.objects if o.type=='MESH'),key=lambda o:len(o.data.vertices));s=.2796456551025057;tr=Vector((.0037096450105309486,.0036666744854301214,1.4953868389129639));M=Matrix.Translation(tr)@Matrix.Diagonal((s,s,s,1))@Matrix.Rotation(math.pi,4,'X')@o.matrix_world;v=np.array([M@x.co for x in o.data.vertices]);o.data.calc_loop_triangles();f=np.array([x.vertices[:] for x in o.data.loop_triangles]);np.savez(R/'white-bust-measured.npz',vertices=v,faces=f)
r={'source':str(P),'sourceSHA256':before,'canonicalAdapter':{'XRotationDegrees':180,'scale':s,'translation':list(tr),'purpose':'Existing display normalization, NOT accepted anatomical/rig mapping'},'bounds':[v.min(0).tolist(),v.max(0).tolist()],'slices':[]}
for z in np.arange(1.43,1.771,.01):
 a=v[np.abs(v[:,2]-z)<.001]
 if len(a):r['slices'].append({'z':float(z),'count':len(a),'bounds':[a.min(0).tolist(),a.max(0).tolist()],'frontCenterY':float(a[np.abs(a[:,0])<.010,1].min()) if np.any(np.abs(a[:,0])<.010) else None})
r['sourceSHA256After']=sha(P);assert before==r['sourceSHA256After'];(R/'white-bust-measurement.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps(r),flush=True)
