"""Read-only source, geometry ROI, protected buffers and inverse-delta verifier."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
sys.path.insert(0,str(Path(__file__).parent.parent/'body-bind21'))
from common import SOURCE,load,accessor
np.seterr(all='raise')
OUT=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind23')
BASE=OUT.parent/'body-bind21/baseline-cpu'
PRIVATE=SOURCE.parent.parent.parent/'body-bind21/baseline-cpu'
def sha(a):return hashlib.sha256(a).hexdigest()
def read(rec,n):
 p=Path(rec['privatePath']) if 'privatePath' in rec else BASE/rec['file']
 if not p.exists():p=PRIVATE/rec['file']
 raw=p.read_bytes();assert sha(raw)==rec['sha256'];return np.frombuffer(raw,dtype='<f8').reshape(-1,n).copy()
def unit(a):return a/np.maximum(np.linalg.norm(a,axis=-1,keepdims=True),1e-30)
report=json.loads((OUT/'report.json').read_text());m=json.loads((OUT/'pose-manifest.json').read_text());base=json.loads((BASE/'pose-manifest.json').read_text());proof=json.loads((OUT/'roi-proof.json').read_text());raw,j,b,p,start=load();assert sha(raw)==report['sourceSHA256']==m['sourceSHA256']==base['sourceSHA256'];assert SOURCE.read_bytes()==raw
r=read(base['primitives'][0]['attributes']['position'],3);normal=read(base['primitives'][0]['attributes']['normal'],3);tri=read(base['primitives'][0]['index'],3).astype(int);u,first,inv=np.unique(r,axis=0,return_index=True,return_inverse=True);ut=inv[tri];edges=np.unique(np.sort(np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]),1),axis=0);edges=edges[edges[:,0]!=edges[:,1]];adj=coo_matrix((np.ones(len(edges)*2),(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(u),len(u))).tocsr();shared=np.zeros(len(u),bool);lookup={tuple(q):i for i,q in enumerate(u)}
for mesh in j['meshes']:
 for other in mesh['primitives']:
  if other is p:continue
  for q in accessor(j,b,other['attributes']['POSITION'])[0]:
   if tuple(q) in lookup:shared[lookup[tuple(q)]]=True
names=[j['nodes'][n]['name'] for n in j['skins'][0]['joints']];ib=accessor(j,b,j['skins'][0]['inverseBindMatrices'])[0].astype(float);origins=np.linalg.inv(ib.reshape(-1,4,4).transpose(0,2,1))[:,:3,3];active=np.zeros(len(u),bool)
for side,sign in [('L',1),('R',-1)]:
 sh,el,wr=[origins[names.index(n+'.'+side)] for n in ['upperArm','forearm','hand']]
 def dist(a,b):
  d=b-a;t=np.clip(np.einsum('vi,i->v',u-a,d)/np.dot(d,d),0,1);return np.linalg.norm(u-(a+t[:,None]*d),axis=1)
 selected=(u[:,1]>.95)&(u[:,1]<1.38)&(sign*u[:,2]>.18)&(np.minimum(dist(sh,el),dist(el,wr))<.14)&~shared
 ids=np.flatnonzero(selected);assert connected_components(adj[ids][:,ids])[0]==1;active|=selected
boundary=active&((adj@(~active).astype(float))>0);free=active&~boundary;exportFree=free[inv];assert int(free.sum())==proof['freePhysicalVertices'];assert np.all(free[inv[tri[3789]]]);assert not np.any(free&shared)
sourceEdges=np.linalg.norm(r[tri]-np.roll(r[tri],-1,axis=1),axis=2);details=[]
for a,c,rpt in zip(base['rows'],m['rows'],report['rows']):
 assert a['i']==c['i']==rpt['sample'];assert {k:v for k,v in a.items() if k!='dump'}=={k:v for k,v in c.items() if k!='dump'};assert a['dump'][1:]==c['dump'][1:];original=a['dump'][0];candidate=c['dump'][0];assert all(candidate[k]==v for k,v in original.items() if k not in ['positions','gpuRuleSkinnedNormals'])
 old=read(original['positions'],3);new=read(candidate['positions'],3);oldn=read(original['gpuRuleSkinnedNormals'],3);newn=read(candidate['gpuRuleSkinnedNormals'],3);delta=read(candidate['correctiveDelta'],3);nd=read(candidate['normalCorrectiveDelta'],3);F=read(original['skinMatrices'],16).reshape(-1,4,4).transpose(0,2,1)
 assert np.array_equal(old[~exportFree],new[~exportFree]);assert np.array_equal(oldn[~exportFree],newn[~exportFree]);assert not np.any(delta[~exportFree]);assert not np.any(nd[~exportFree]);assert np.max(np.abs(delta-delta[first][inv]))<1e-7
 actual=old+np.einsum('vkl,vl->vk',F[:,:3,:3],delta);error=float(np.linalg.norm(actual-new,axis=1).max());assert error<1e-12;normalError=float(np.linalg.norm(unit(np.einsum('vkl,vl->vk',F[exportFree,:3,:3],(normal+nd)[exportFree]))-newn[exportFree],axis=1).max());assert normalError<1e-12
 # Identify retained worst stretch, not merely the changed patch average.
 Q=new[tri];stretch=(np.linalg.norm(Q-np.roll(Q,-1,axis=1),axis=2)/np.maximum(sourceEdges,1e-30)).max(1)
 si=read(base['primitives'][0]['attributes']['skinIndex'],4).astype(int);sw=read(base['primitives'][0]['attributes']['skinWeight'],4);bones=base['primitives'][0]['bones'];armIds=[i for i,n in enumerate(bones) if n.startswith(('upperArm','forearm'))];arm=np.where(np.isin(si,armIds),sw,0).sum(1);historical=(arm[tri].mean(1)>.3)&(r[tri,1].mean(1)>.9)&(np.abs(r[tri,2]).mean(1)>.13)
 ids=np.flatnonzero(historical);worst=int(ids[np.argmax(stretch[ids])]);entireFree=np.all(exportFree[tri],axis=1);touches=np.any(exportFree[tri],axis=1);worstId=int(np.argmax(np.linalg.norm(new-old,axis=1)))
 details.append({'sample':a['i'],'sourcePositionRoundtripErrorM':error,'sourceNormalRoundtripError':normalError,'lastIterationMaximumMoveM':rpt['iterationMaximumDisplacementM'][-1],'protectedActualBonesPhysicsContactsExact':True,'maximumPosedMovementExportVertex':worstId,'maximumPosedMovementSourcePosition':r[worstId].tolist(),'worstRetainedHistoricalStretch':{'triangle':worst,'stretch':float(stretch[worst]),'exportVertices':tri[worst].tolist(),'sourcePositions':r[tri[worst]].tolist(),'freeCorrectiveVertices':exportFree[tri[worst]].tolist(),'sourceGraphBoundaryVertices':boundary[inv[tri[worst]]].tolist()},'maximumEdgeStretchAllFreeTriangles':float(stretch[entireFree].max()),'maximumEdgeStretchTrianglesTouchingFree':float(stretch[touches].max())})
for rec in json.loads((OUT/'buffer-archive.json').read_text())['buffers']:assert sha(Path(rec['privatePath']).read_bytes())==rec['sha256']
print(json.dumps({'sourceSHA256':sha(raw),'geometryROIUsesNoSkinWeightEligibility':True,'bothSourceROIsConnected':True,'allThreeWitnessVerticesFree':True,'allSource11BytesUnchanged':True,'allOtherPrimitiveAndProtectedSurfaceBuffersUnchanged':True,'fourRetainedActualDebugBonesContactsExact':True,'rows':details,'limits':'Read-only CPU verification, no moving art acceptance, garment collision certificate or asset export.'},indent=2))
