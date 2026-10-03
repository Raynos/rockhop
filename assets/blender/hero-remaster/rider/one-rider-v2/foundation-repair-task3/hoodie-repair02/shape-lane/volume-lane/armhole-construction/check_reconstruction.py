"""Rest inventory + literal geometry gate for new higher-armhole construction."""
from pathlib import Path
import sys,json,hashlib
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from chart_labels import *
from scipy.spatial import cKDTree
EPS=1e-9
exec('def crossing'+(ROOT/'audit/self_intersections.py').read_text().split('def crossing')[1].split('def audit')[0])
candidate=Path(sys.argv[1]) if len(sys.argv)>1 else HERE/'armhole-reconstructed.npz';d=np.load(candidate);source=np.load(HERE/'frozen-v7-bind.npz');uv=[G.array(p['attributes']['TEXCOORD_0']).astype(float)for p in PR]
def topology(pos,tr,weld=None):
 x=np.concatenate(pos);u,alias=np.unique(x.astype('f4'),axis=0,return_inverse=True);off=np.r_[0,np.cumsum([len(p)for p in pos])]
 if weld is not None:alias=np.concatenate(weld)
 t=np.concatenate([alias[off[i]:off[i+1]][tr[i]]for i in [0,2]])
 directed=np.concatenate([t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]]);ee=np.sort(directed,axis=1);e,inverse,c=np.unique(ee,axis=0,return_inverse=True,return_counts=True);direction=np.where(directed[:,0]<directed[:,1],1,-1);signed=np.bincount(inverse,weights=direction,minlength=len(e));coord={int(a):q for a,q in zip(alias,x)};boundaryPositions=np.array([[*coord[int(a)],*coord[int(b)]]for a,b in e[c==1]])
 return {'boundaryEdges':int((c==1).sum()),'nonmanifoldEdges':int((c>2).sum()),'incoherentSharedEdgeOrientation':int(((c==2)&(signed!=0)).sum()),'degenerateAliasFaces':int(((t[:,0]==t[:,1])|(t[:,0]==t[:,2])|(t[:,1]==t[:,2])).sum()),'boundaryPositions':boundaryPositions.tolist(),'uniqueVertices':len(np.unique(alias))},t,u,alias,off
p=[d[f'p{i}']for i in range(5)];tr=[d[f'tr{i}']for i in range(5)];w=[d[f'W{i}']for i in range(5)];now,t,u,alias,off=topology(p,tr,[d[f'physicalWeld{i}']for i in range(5)]);old,ot,ou,oa,ooff=topology([source[f'p{i}']for i in range(5)],[source[f'tr{i}']for i in range(5)])
oldb=np.array(old.pop('boundaryPositions'));newb=np.array(now.pop('boundaryPositions'));bset=lambda x:{tuple(z)for z in np.sort(x,axis=1)}
rep={'candidateSHA256':hashlib.sha256(candidate.read_bytes()).hexdigest(),'sourceSHA256':hashlib.sha256((HERE/'frozen-v7-bind.npz').read_bytes()).hexdigest(),'topologyBefore':old,'topologyAfter':now,'boundaryPositionSetExact':bset(oldb)==bset(newb),'finiteArrays':all(np.isfinite(x).all()for x in p+w),'maxWeightSumError':max(float(abs(x.sum(1)-1).max())for x in w),'maxInfluences':max(int((x>1e-8).sum(1).max())for x in w),'headHandsGloveGeometryWeightsUVExact':all(np.array_equal(p[i],source[f'p{i}'])and np.array_equal(w[i],source[f'W{i}'])and np.array_equal(d[f'uv{i}'],uv[i])for i in [1,3,4]),'allOriginalUVRowsExact':all(np.array_equal(d[f'uv{i}'][:len(uv[i])],uv[i])for i in range(5)),'newPatchFaces':len(d['newFacesPrimitive0'])}
# Whole-source original-row changed inventory. Normals are explicitly separate
# because recomputation can affect source seam shading beyond moved coordinates.
shape=np.load(ROOT/'hoodie-repair02/v7-shape-input.npz');inventory=[]
for i in [0,2]:
 n=len(source[f'p{i}']);dp=np.linalg.norm(p[i][:n]-source[f'p{i}'],axis=1);dw=abs(w[i][:n]-source[f'W{i}']).max(1);dn=np.linalg.norm(d[f'n{i}'][:n]-shape[f'n{i}'],axis=1);changed=np.flatnonzero((dp>1e-10)|(dw>1e-8));inventory.append({'primitive':i,'changedPositionRows':int((dp>1e-10).sum()),'changedWeightRows':int((dw>1e-8).sum()),'changedNormalRows':int((dn>1e-6).sum()),'maxSourceRowShiftM':float(dp.max()),'changedOriginalRows':changed.tolist()})
rep['inventory']=inventory
rep['outsideConstructionMarginExact']={str(i):all(np.array_equal(d[f'{key}{i}'][:len(source[f'p{i}'])][~d[f'sourceConstructionMargin{i}']], ref[~d[f'sourceConstructionMargin{i}']]) for key,ref in [('p',source[f'p{i}']),('W',source[f'W{i}']),('n',shape[f'n{i}']),('uv',uv[i])])for i in [0,2]}
q=np.concatenate([p[0],p[2]]);ct=np.concatenate([tr[0],tr[2]+len(p[0])]);al=np.r_[d['physicalWeld0'],d['physicalWeld2']];T=q[ct];cent=T.mean(1);rad=np.linalg.norm(T-cent[:,None],axis=2).max(1);roi=(T[:,:,1]>.99).all(1)&(T[:,:,1]<1.51).all(1);ids=np.flatnonzero(roi);T=T[roi];al=al[ct[roi]];cent=T.mean(1);rad=np.linalg.norm(T-cent[:,None],axis=2).max(1);tree=cKDTree(cent);lo=T.min(1);hi=T.max(1);witness=[];nonadj=corner=0
for start in range(0,len(T),64):
 nearby=tree.query_ball_point(cent[start:start+64],rad[start:start+64]+rad.max());pairs=np.array([(start+a,b)for a,rr in enumerate(nearby)for b in rr if start+a<b],int).reshape(-1,2)
 if not len(pairs):continue
 pairs=pairs[((lo[pairs[:,0]]<=hi[pairs[:,1]])&(lo[pairs[:,1]]<=hi[pairs[:,0]])).all(1)];shared=(al[pairs[:,0],:,None]==al[pairs[:,1],None,:]).any(2).sum(1);keep=shared<2;pairs=pairs[keep];shared=shared[keep]
 hit=crossing(T[pairs[:,0]],T[pairs[:,1]]);nonadj+=int((hit&(shared==0)).sum());corner+=int((hit&(shared==1)).sum());witness.extend(ids[pairs[hit]].tolist())
rep['restStrictNonadjacentCrossings']=nonadj;rep['restStrictOneCornerCrossings']=corner;rep['restCrossWitnessCombinedFaces']=witness;rep['restMinimumDoubleFaceAreaM2']=float(np.linalg.norm(np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]),axis=1).min())
from collections import Counter
kinds=np.r_[np.repeat('source0',33968),d['newFaceKind'],np.repeat('source2',len(tr[2]))];rep['crossingClasses']=dict(Counter('|'.join(sorted([str(kinds[a]),str(kinds[b])]))for a,b in witness))
new=d['newFacesPrimitive0'];tp=p[0][tr[0][new]];tex=d['uv0'][tr[0][new]];a=(tex[:,1,0]-tex[:,0,0])*(tex[:,2,1]-tex[:,0,1])-(tex[:,1,1]-tex[:,0,1])*(tex[:,2,0]-tex[:,0,0]);rep['newUVSignedArea']={'min':float(a.min()),'max':float(a.max()),'nearZeroCount':int((abs(a)<1e-12).sum()),'negativeCount':int((a<0).sum()),'groups':{str(k):{'positive':int((a[d['newFaceKind']==k]>0).sum()),'negative':int((a[d['newFaceKind']==k]<0).sum())}for k in np.unique(d['newFaceKind'])}}
candidate.with_suffix('.rest-gate.json').write_text(json.dumps(rep,indent=2));print(json.dumps({k:v for k,v in rep.items()if k not in ['inventory','restCrossWitnessCombinedFaces']},indent=2));print('changed original source rows',[(i['primitive'],i['changedPositionRows'],i['changedWeightRows'],i['changedNormalRows'])for i in inventory],flush=True)
