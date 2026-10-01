import bpy,numpy as np,json,collections
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/parent-assembly/donor-fit03')
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/parent-assembly/donor-fit03')
bpy.ops.wm.open_mainfile(filepath=str(R/'rider.blend'));m=next(o.data for o in bpy.context.scene.objects if o.type=='MESH' and 'protected' in o.name)
v=np.asarray([x.co[:] for x in m.vertices]);f=np.asarray([p.vertices[:] for p in m.polygons]);mi=np.asarray([p.material_index for p in m.polygons]);u,c=np.unique(np.sort(f,axis=1),axis=0,return_counts=True);dup=u[c>1];ed=np.concatenate([f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]]);ue,ec=np.unique(np.sort(ed,axis=1),axis=0,return_counts=True);bad=ue[ec>2];w=np.linalg.norm(np.cross(v[f[:,1]]-v[f[:,0]],v[f[:,2]]-v[f[:,0]]),axis=1)
copy=m.copy();n=len(copy.polygons);changed=copy.validate(verbose=True);after=len(copy.polygons)
report={'faces':len(f),'materialCounts':dict(collections.Counter(map(int,mi))),'duplicateFaces':len(dup),'duplicateMaterialCounts':dict(collections.Counter(map(int,mi[[i for i,x in enumerate(np.sort(f,axis=1)) if any(np.array_equal(x,d) for d in dup)]]))),'nonmanifoldEdges':len(bad),'boundaryEdges':int(sum(ec==1)),'zeroAreaFaces':int(sum(w<1e-12)),'validationCopyChanged':changed,'validationCopyRemovedFaces':n-after,'limits':'Diagnostic copy only; exported/source masters unchanged'}
(O/'mesh-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
