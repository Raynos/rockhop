"""Independent NumPy raw-rest/inversebind alias deformation crosscheck, all5404."""
from pathlib import Path
import json,hashlib,struct,numpy as np
from scipy.spatial.transform import Rotation
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');RUN=ROOT/'basic-pose-seams163';OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/basic-pose-seams163');rawInput=(RUN/'raw-seam-input.json').read_bytes();x=json.loads(rawInput);raw=Path(x['source']).read_bytes();fr=Path(x['fixture']).read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(raw)==x['sourceSHA256'] and sha(fr)==x['fixtureSHA256'];n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);fixture=json.loads(fr);nodes=j['nodes'];parents={c:i for i,no in enumerate(nodes) for c in no.get('children',[])};cache={}
def world(i):
 if i in cache:return cache[i]
 no=nodes[i]
 if 'matrix'in no:m=np.array(no['matrix']).reshape(4,4).T
 else:m=np.eye(4);m[:3,:3]=Rotation.from_quat(no.get('rotation',[0,0,0,1])).as_matrix()@np.diag(no.get('scale',[1,1,1]));m[:3,3]=no.get('translation',[0,0,0])
 cache[i]=world(parents[i])@m if i in parents else m;return cache[i]
rest=np.array([world(i) for i in j['skins'][0]['joints']]);ib=np.array(x['inverseBindsColumnMajor']).reshape(19,4,4).transpose(0,2,1);D=np.array([f['deformationWorldColumnMajor'] for f in fixture['frames']]).reshape(5404,19,4,4).transpose(0,1,3,2);M=D@rest@ib;matricesFile=RUN/'independent-raw-deltas.f64';assert not matricesFile.exists(),'Preserve frozen math receipt';M.astype('<f8').tofile(matricesFile)
rawPointSets=[];normalRows=[];grip=np.array([f['closedGrip'] for f in fixture['frames']]);side=[f.get('gripSide') for f in fixture['frames']];names=x['meshes'][0]['targetNames'];weights=[]
for mi,key in [(0,'bodyVertexIDs'),(1,'gloveVertexIDs')]:
 r=x['meshes'][mi];ids=np.array([g[key][0] for g in x['groups']]);P=np.array(r['attrs']['POSITION'])[ids];J=np.array(r['attrs']['JOINTS_0'])[ids];rawW=np.array(r['attrs']['WEIGHTS_0'])[ids];normalized=(rawW/abs(rawW).sum(1,keepdims=True)).astype('f4').astype(float);W=np.zeros((127,19))
 for lane in range(4):np.add.at(W,(np.arange(127),J[:,lane]),normalized[:,lane])
 points=np.broadcast_to(P,(5404,127,3)).copy()
 for target,name in enumerate(names):
  isgrip='grip'in name.lower();targetSide=name[-1] if name.endswith(('.L','.R','_L','_R')) else None;activation=np.array([g if isgrip and (s is None or s==targetSide) else 0 for g,s in zip(grip,side)]);points+=activation[:,None,None]*np.array(r['targets'][target]['POSITION'])[ids][None,:,:]
 posed=np.einsum('gj,fjab,fgb->fga',W,M[:,:,:3,:],np.concatenate([points,np.ones((5404,127,1))],axis=2),optimize=True);rawPointSets.append(posed);weights.append(W)
 assert all(g['maximumAliasWeightComponentDifference']==0 and g['morphPositions']['maximumSharedDeltaComponentGap']==0 for g in x['groups'])
 for gi,g in enumerate(x['groups']):
  bodyNormal=np.array(x['meshes'][0]['attrs']['NORMAL'])[g['bodyVertexIDs']];gloveNormal=np.array(x['meshes'][1]['attrs']['NORMAL'])[g['gloveVertexIDs']];bodyNormal/=np.linalg.norm(bodyNormal,axis=1,keepdims=True);gloveNormal/=np.linalg.norm(gloveNormal,axis=1,keepdims=True);normalRows.append({'group':gi,'side':g['side'],'minimumRestSourceBodyGloveNormalDot':float((bodyNormal@gloveNormal.T).min()),'UVSourceBody':np.array(x['meshes'][0]['attrs']['TEXCOORD_0'])[g['bodyVertexIDs']].tolist(),'UVSourceGlove':np.array(x['meshes'][1]['attrs']['TEXCOORD_0'])[g['gloveVertexIDs']].tolist()})
 # Normal/UV observations are static source measurements, not shader continuity acceptance.
 break
# Repeat glove independently; loop above stops to avoid duplicate normal inventory.
r=x['meshes'][1];ids=np.array([g['gloveVertexIDs'][0] for g in x['groups']]);P=np.array(r['attrs']['POSITION'])[ids];J=np.array(r['attrs']['JOINTS_0'])[ids];rawW=np.array(r['attrs']['WEIGHTS_0'])[ids];normalized=(rawW/abs(rawW).sum(1,keepdims=True)).astype('f4').astype(float);W=np.zeros((127,19))
for lane in range(4):np.add.at(W,(np.arange(127),J[:,lane]),normalized[:,lane])
points=np.broadcast_to(P,(5404,127,3)).copy()
for target,name in enumerate(r['targetNames']):
 targetSide=name[-1] if name.endswith(('.L','.R','_L','_R')) else None;activation=np.array([g if 'grip'in name.lower() and (s is None or s==targetSide) else 0 for g,s in zip(grip,side)]);points+=activation[:,None,None]*np.array(r['targets'][target]['POSITION'])[ids][None,:,:]
glovePosed=np.einsum('gj,fjab,fgb->fga',W,M[:,:,:3,:],np.concatenate([points,np.ones((5404,127,1))],axis=2),optimize=True);gap=np.linalg.norm(rawPointSets[0]-glovePosed,axis=2);assert gap.max()==0
normalFile=OUT/'source-normal-uv-observations.json';normalFile.write_text(json.dumps({'kind':'Static source boundary shading data; no shader appearance pass','rows':normalRows,'minimumDotAcrossSourceAliases':min(r['minimumRestSourceBodyGloveNormalDot'] for r in normalRows),'limits':['Different garment/leather normals and atlases may be intentional. Raw UV/normal observations neither prove nor reject rendered continuity.','Actual morph+skinned shader normal directions/normalmap/PBR textures unmeasured; CPU surface endpoints are distinct checks.']},separators=(',',':'))+'\n')
report={'kind':'Independent rawGLB rest hierarchy + inversebind + fixture affine alias check','sourceSHA256':x['sourceSHA256'],'fixtureSHA256':x['fixtureSHA256'],'rawInputSHA256':sha(rawInput),'samples':5404,'aliasGroups':127,'sourceHierarchyRestCentresMaximumFixtureDeltaM':float(np.linalg.norm(rest[:,:3,3]-np.array(fixture['referenceCentresWorld']),axis=1).max()),'rawRestInverseBindMaximumIdentityError':float(abs(rest@ib-np.eye(4)).max()),'maximumBodyGloveAliasGapM':float(gap.max()),'maximumCanonicalWeightGapAfterLoaderRule':float(abs(weights[0]-W).max()),'independentMatrixStorage':'frame,joint,row-major4x4Float64LE,5404x19x4x4','independentMatrixFile':str(matricesFile),'independentMatrixSHA256':sha(matricesFile.read_bytes()),'groupGapProof':'Both endpoint alias families have identical rawrest positions/canonical19weights and both sourcePOSITIONgripdelta vectors. They remain equal under this affine law. This is not a collision or appearance proof.','limits':['Python math does not render. ActualThree comparison is separate5404sample report with explicit rawaffine parity.','Source double-node hierarchy and float32inversebind cause small neutral residuals retained, not silently replaced with identity.','Static two-ring cuff scope does not certify fullforearm/sleeve or handgrip.']};assert Path(x['source']).read_bytes()==raw and Path(x['fixture']).read_bytes()==fr;(OUT/'independent-math.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
