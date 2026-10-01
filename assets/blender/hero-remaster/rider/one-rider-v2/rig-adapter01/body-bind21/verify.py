"""Read-only SHA-checked four-state sleeve trial verifier. No writes or GPU."""
import json
from pathlib import Path
import numpy as np
from common import SOURCE,RUN,OUT,load,accessor,sha
np.seterr(all='raise')
def read(folder,rec,lanes):
 p=OUT/folder/rec['file']
 if not p.exists():p=RUN/folder/rec['file']
 assert sha(p.read_bytes())==rec['sha256'];return np.fromfile(p,dtype='<f8').reshape(-1,lanes)
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-30)
report=json.loads((OUT/'build-report.json').read_text());assert sha(SOURCE.read_bytes())==report['sourceSHA256'];cr=(RUN/'rider.glb').read_bytes();assert sha(cr)==report['candidateSHA256'];raw,j,b,p,start=load();rest,_,_=accessor(j,b,p['attributes']['POSITION']);tri=accessor(j,b,p['indices'])[0].reshape(-1,3);si,siat,sistride=accessor(j,b,p['attributes']['JOINTS_0']);sw,swat,swstride=accessor(j,b,p['attributes']['WEIGHTS_0']);cb=cr[start:];ci,_,_=accessor(j,cb,p['attributes']['JOINTS_0']);cw,_,_=accessor(j,cb,p['attributes']['WEIGHTS_0']);W=np.zeros((len(rest),19));C=W.copy()
for lane in range(4):np.add.at(W,(np.arange(len(rest)),si[:,lane]),sw[:,lane]);np.add.at(C,(np.arange(len(rest)),ci[:,lane]),cw[:,lane])
changed=np.flatnonzero(np.max(np.abs(C-W),axis=1)>1e-7);allowed=set()
for v in changed:
 allowed.update(range(start+siat+v*sistride,start+siat+v*sistride+4));allowed.update(range(start+swat+v*swstride,start+swat+v*swstride+16))
assert len(cr)==len(raw);assert all(i in allowed for i,(a,c) in enumerate(zip(raw,cr)) if a!=c)
u,first,inv=np.unique(rest,axis=0,return_index=True,return_inverse=True);assert np.max(np.abs(C-C[first][inv]))<1e-7;assert sha((RUN/'weight-field.npz').read_bytes())==report['weightFieldSHA256'];field=np.load(RUN/'weight-field.npz');pinned=field['boundaries']|field['shared'];assert np.array_equal(C[first][pinned],W[first][pinned]);assert np.array_equal(C[first][~field['eligible']],W[first][~field['eligible']]);assert np.array_equal(rest,field['rest']);assert np.array_equal(tri,field['triangles'])
A=json.loads((OUT/'baseline-cpu/pose-manifest.json').read_text());B=json.loads((OUT/'candidate-cpu/pose-manifest.json').read_text());assert A['sourceSHA256']==report['sourceSHA256'];assert B['sourceSHA256']==report['candidateSHA256'];metrics=[]
for mi,primitive in enumerate(A['primitives']):
 a=primitive['attributes'];r=read('baseline-cpu',a['position'],3);n=read('baseline-cpu',a['normal'],3);ids=read('baseline-cpu',primitive['index'],3).astype(int);skin=read('baseline-cpu',a['skinIndex'],4).astype(int);weights=read('baseline-cpu',a['skinWeight'],4);armBones=[i for i,name in enumerate(primitive['bones']) if name.startswith(('upperArm','forearm'))];aw=np.where(np.isin(skin,armBones),weights,0).sum(1);roi=(aw[ids].mean(1)>.3)&(r[ids,1].mean(1)>.9)&(np.abs(r[ids,2]).mean(1)>.13);R=r[ids];srcCross=np.cross(R[:,1]-R[:,0],R[:,2]-R[:,0]);area=np.linalg.norm(srcCross,axis=1)/2;srcDot=np.einsum('ti,ti->t',unit(srcCross),unit(n[ids].mean(1)));sourceEdge=np.linalg.norm(R-np.roll(R,-1,axis=1),axis=2)
 for ar,br in zip(A['rows'],B['rows']):
  assert ar['i']==br['i'];assert ar['debug']==br['debug'];assert ar['contacts']==br['contacts'];assert ar['bonePoints']==br['bonePoints'];assert ar['bodyworkBikeFrame']==br['bodyworkBikeFrame'];ap=read('baseline-cpu',ar['dump'][mi]['positions'],3);bp=read('candidate-cpu',br['dump'][mi]['positions'],3);an=read('baseline-cpu',ar['dump'][mi]['gpuRuleSkinnedNormals'],3);bn=read('candidate-cpu',br['dump'][mi]['gpuRuleSkinnedNormals'],3)
  if mi==0:assert np.array_equal(ap[np.setdiff1d(np.arange(len(r)),changed)],bp[np.setdiff1d(np.arange(len(r)),changed)])
  else:assert np.array_equal(ap,bp);assert np.array_equal(an,bn)
  row={'sample':ar['i'],'mesh':primitive['mesh'],'sourceSleeveTriangles':int(roi.sum()),'maximumPositionChangeM':float(np.linalg.norm(ap-bp,axis=1).max())};foldSets=[]
  for key,P,N in [('baseline',ap,an),('candidate',bp,bn)]:
   Q=P[ids];cross=np.cross(Q[:,1]-Q[:,0],Q[:,2]-Q[:,0]);dot=np.einsum('ti,ti->t',unit(cross),unit(N[ids].mean(1)));ratio=np.linalg.norm(cross,axis=1)/np.maximum(2*area,1e-30);stretch=(np.linalg.norm(Q-np.roll(Q,-1,axis=1),axis=2)/np.maximum(sourceEdge,1e-30)).max(1);fold=roi&(srcDot>.2)&(dot<-.2);foldSets.append(fold);row[key]={'folds':int(fold.sum()),'areaBelowQuarter':int((roi&(ratio<.25)).sum()),'maximumEdgeStretch':float(stretch[roi].max()) if roi.any() else None,'minimumNormalDot':float(dot[roi].min()) if roi.any() else None,'triangle3789':{'normalDot':float(dot[3789]),'areaRatio':float(ratio[3789]),'maximumEdgeStretch':float(stretch[3789])} if mi==0 else None}
  row['newFoldsNotPresentAtBaseline']=int((foldSets[1]&(~foldSets[0])).sum());metrics.append(row)
summary={'sourceSHA256':report['sourceSHA256'],'candidateSHA256':report['candidateSHA256'],'allNonSkinBytesExact':True,'outsideChangedSleevePosedGeometryExact':True,'hoodPrimitivePositionsAndNormalsExact':True,'allFourBonesDebugPhysicsSeatAndPalmSoleErrorValuesExact':True,'maximumCPUvsActualPlayedContactErrorM':max(c['maximumCPUvsActualPlayedSurfaceM'] for row in B['rows'] for c in row['contacts']),'protectedSharedAliasesAndBoundaryExact':True,'rows':metrics,'limits':['Four recorded-state CPU samples only; no moving art score or watertight self-intersection certificate.','Region mask is frozen from source11; candidate arm weights do not enlarge it.','Folds mean new face/transported-normal opposition; area and stretch measured independently.']};print(json.dumps(summary,indent=2))
