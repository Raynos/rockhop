from pathlib import Path
import json,hashlib
import numpy as np
root=Path.cwd();src=root/'harness/out/rider-rebuild/production-boots01/authored02';boots={s:dict(np.load(src/('production-boot-'+s+'.npz'))) for s in ('L','R')};body=np.load(root/'docs/evidence/rider-rebuild/native-hand-repair01/native02/native-body.npz');n=body['jointNames'].tolist();spec=json.loads((root/'assets/blender/rider-rebuild/production-boots01/controls.json').read_text())['authoring']['targetSides']
aff={};rows={}
for side in ('L','R'):
 ankle=body['jointHeads'][n.index('DEF-foot.'+side)];toe=body['jointHeads'][n.index('DEF-toe.'+side)];u=np.r_[toe[:2]-ankle[:2],0.];u/=np.linalg.norm(u);frame=np.column_stack([-u,[0.,0.,1.],np.cross(-u,[0.,0.,1.])]);scale=np.array(spec[side]['scales']);scale[2]*=spec[side]['mirrorWidth'];m=np.eye(4);m[:3,:3]=frame*scale[None,:];m[:3,3]=np.r_[ankle[:2],0.]+np.einsum('ij,j->i',frame,spec[side]['offset']);aff[side]=m
 a=boots[side];names=a['jointNames'].tolist();used=np.flatnonzero(a['coefficients'].sum(0)>0);opposite='R' if side=='L' else 'L';assert all(names[i].endswith('.'+side) or names[i].endswith('.'+side+'.001') for i in used)
 rows[side]={'vertices':len(a['vertices']),'triangles':len(a['faces']),'bounds':[a['vertices'].min(0).tolist(),a['vertices'].max(0).tolist()],'sourceToNativeDeterminant':float(np.linalg.det(m[:3,:3])),'usedJoints':[names[i] for i in used]}
transform=np.einsum('ij,jk->ik',aff['L'],np.linalg.inv(aff['R']));expect=np.einsum('ni,ji->nj',boots['R']['vertices'],transform[:3,:3])+transform[:3,3];error=float(abs(expect-boots['L']['vertices']).max());assert error<1e-6 and np.linalg.det(transform[:3,:3])<0
right=boots['R']['faces'];left=boots['L']['faces'];assert right.shape==left.shape
# Mirrored polygons reverse winding; saved loop triangles preserve source vertex identity.
winding_reversed=all(tuple(l) in (tuple(r[::-1]),tuple(np.roll(r[::-1],1)),tuple(np.roll(r[::-1],2))) for r,l in zip(right,left));assert winding_reversed
handrows={}
inputs=json.loads((root/'assets/blender/rider-rebuild/production-gloves01/inputs.json').read_text())
for side in ('L','R'):
 record=inputs['hand'+side];p=root/record['path'];assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256'];a=np.load(p);handrows[side]={'path':record['path'],'sha256':record['sha256'],'vertices':len(a['vertices']),'triangles':len(a['faces']),'bounds':[a['vertices'].min(0).tolist(),a['vertices'].max(0).tolist()]}
result={'acceptedArt':False,'boots':{'savedPair':True,'oneSelectedSourceMirroredToOppositeHandedness':True,'mirrorDeterminant':float(np.linalg.det(transform[:3,:3])),'maximumSavedMirrorErrorM':error,'triangleWindingReversed':winding_reversed,'sideSpecificSkin':True,'sides':rows,'limits':['Current toe fit is rejected. Reflection proves opposite handedness, not correct asymmetrical shoe last or fit to each foot.']},'gloves':{'distinctActualLeftRightHandTargets':True,'targets':handrows,'construction':'Each actual hand separately; left appearance donor reflected and winding reversed; side-specific digit bones.','completeSavedMeshes':False,'limits':['Latest author02 failed on R before complete bilateral glove meshes were saved. Final thumb placement/fit and skin require actual saved and played verification.']}}
(root/'docs/evidence/rider-rebuild/handedness01/receipt.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps(result,indent=2))
