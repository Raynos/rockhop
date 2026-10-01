"""Two-thread480frame CPU stress of frozen single cuff transition155.
Source bind/matrix law explicitly verified for actual primitive endpoints.
"""
from pathlib import Path
import hashlib,json,numpy as np
REPO=Path('/Users/raynos/projects/games/rockhop');ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');OUT=REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/cuff-ankle-transition155';RUN=ROOT/'garment-rebuild01/cuff-ankle-transition155';sha=lambda b:hashlib.sha256(b).hexdigest()
report=json.loads((OUT/'construction-report.json').read_bytes());path=RUN/'transition155.npz';assert sha(path.read_bytes())==report['artifactSHA256'];f=np.load(path);P=f['native_positions'];W=f['native_weights19'];oldW=f['native_weights19_before'];Q=f['native_retained_quads'];tri=np.concatenate([Q[:,[0,1,2]],Q[:,[0,2,3]]]);N=f['native_normals'];BP=f['bridge_positions'];BW=f['bridge_weights19'];BN=f['bridge_normals'];BT=f['bridge_triangles'];BR=f['bridge_endpoint_reference'];beforeBW=np.array([oldW[i] if ns==0 else f[f'source{ns-1}_weights19'][i] for ns,i,_ in BR])
motionPath=REPO/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/full-motion155/report.json';motion=json.loads(motionPath.read_bytes());matRoot=ROOT/'garment-rebuild01/full-motion155';body=motion['outputs'][0];glove=motion['outputs'][1];assert body['mesh']=='Protected_body_NEW_hood_joined_garment' and glove['mesh']=='Protected_body_NEW_hood_joined_garment_1';assert body['bones']==glove['bones'];assert body['sourceBindMatrix']==glove['sourceBindMatrix']==np.eye(4).T.reshape(-1).tolist();br=(matRoot/body['file']).read_bytes();gr=(matRoot/glove['file']).read_bytes();assert sha(br)==body['sha256'] and sha(gr)==glove['sha256'] and br==gr;matrices=np.frombuffer(br,dtype='<f8').reshape(480,19,4,4).transpose(0,1,3,2)
# All source raw attributes checked against construction digests; no contacts edited.
for key,rec in report['sourceArrays'].items():assert sha(f[key].tobytes())==rec['sha256']
def unit(a):return a/np.maximum(np.linalg.norm(a,axis=-1,keepdims=True),1e-20)
def measure(pos,weight,faces,normals,M):
 q=pos[faces];posed=np.einsum('vj,jab,vb->va',weight,M[:,:3,:],np.c_[pos,np.ones(len(pos))]);p=posed[faces];rc=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);pc=np.cross(p[:,1]-p[:,0],p[:,2]-p[:,0]);re=np.linalg.norm(q-np.roll(q,-1,axis=1),axis=2);pe=np.linalg.norm(p-np.roll(p,-1,axis=1),axis=2);stretch=pe/np.maximum(re,1e-20);area=np.linalg.norm(pc,axis=1)/np.maximum(np.linalg.norm(rc,axis=1),1e-20);skinned=unit(np.einsum('vj,jab,vb->va',weight,M[:,:3,:3],normals));rd=np.einsum('ti,ti->t',unit(rc),unit(normals[faces].mean(1)));pd=np.einsum('ti,ti->t',unit(pc),unit(skinned[faces].mean(1)));flags=(rd>.2)&(pd<-.2)
 return {'triangles':len(faces),'maximumEdgeStretch':float(stretch.max()),'edgeStretchP99':float(np.quantile(stretch,.99)),'areaRatioMinimum':float(area.min()),'areaCollapsedBelow25Percent':int((area<.25).sum()),'normalOppositionFlags':int(flags.sum())}
scopes=[]
for side in ['L','R']:
 mask=(f['native_cuff_'+side+'_blend_alpha'][tri]>0).any(1);scopes.append(('native sleeve.'+side,P,oldW,W,tri[mask],N))
for s in report['bridgeRows']:
 a,z=s['triangleRange'];scopes.append((s['name'],BP,beforeBW,BW,BT[a:z],BN))
scopes.append(('whole retained clean garment',P,oldW,W,tri,N));rows=[]
for i,M in enumerate(matrices):
 row={'frame':i,'tick':motion['framesChecked'][i]['tick'],'scopes':{}}
 for name,pos,before,after,faces,normals in scopes:row['scopes'][name]={'before':measure(pos,before,faces,normals,M),'after':measure(pos,after,faces,normals,M)}
 rows.append(row)
summary={}
for name,*_ in scopes:
 summary[name]={}
 for version in ['before','after']:
  values=[r['scopes'][name][version] for r in rows];summary[name][version]={'triangles':values[0]['triangles'],'maximumEdgeStretch':max(v['maximumEdgeStretch'] for v in values),'worstStretchFrame':max(range(480),key=lambda i:values[i]['maximumEdgeStretch']),'minimumAreaRatio':min(v['areaRatioMinimum'] for v in values),'maximumAreaCollapsedBelow25PercentPerFrame':max(v['areaCollapsedBelow25Percent'] for v in values),'sumAreaCollapseFlagsAcrossFrames':sum(v['areaCollapsedBelow25Percent'] for v in values),'framesWithAreaCollapse':sum(v['areaCollapsedBelow25Percent']>0 for v in values),'maximumNormalOppositionFlagsPerFrame':max(v['normalOppositionFlags'] for v in values),'sumNormalOppositionFlagsAcrossFrames':sum(v['normalOppositionFlags'] for v in values),'framesWithNormalOpposition':sum(v['normalOppositionFlags']>0 for v in values)}
result={'kind':'Frozen single cuff transition155 across all480 actual34riding matrices; CPU regional test only','candidateArtifactSHA256':report['artifactSHA256'],'sourceGLBSHA256':report['sourceGLBSHA256'],'fullMotionManifestSHA256':sha(motionPath.read_bytes()),'bodyMatrixSHA256':sha(br),'gloveMatrixSHA256':sha(gr),'endpointBindProof':{'bodyAndGloveCanonicalBoneOrderEqual':True,'sourceBodyAndGloveBindMatricesIdentity':True,'bodyAndGloveFull480JointMatricesByteIdentical':True,'CartesianSkinLaw':'sumWj*(jointAffineMatrix_j*sourcePosition4). Matrices already include runtime prefix*boneWorld*inverseBind*bindMatrix; raw source weights preserved, no homogeneous divide.'},'sourceAllFiveRawAttributesVerifiedExact':True,'sourceContactGeometryWeightFieldsUntouched':True,'summary':summary,'rows':rows,'limits':['No actual GPU surface renders, source/native selfintersection, saddle support, face/body quality or gameplay contact acceptance.','Mapped actual recorded C19motion only; does not cover standing-to-seating/Garage or unobserved states.','Whole retained garment flags outside modified cuff region remain unresolved; cuff improvement is not a fullcharacter success.']}
(OUT/'full-motion-audit.json').write_text(json.dumps(result,separators=(',',':'))+'\n');print(json.dumps(summary,indent=2))
