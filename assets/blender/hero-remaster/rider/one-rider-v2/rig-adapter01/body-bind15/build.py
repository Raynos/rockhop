"""One connected anatomy-anchored weight trial; immutable non-skin GLB bytes."""
import json,sys
import numpy as np
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import spsolve
from common import SOURCE,RUN,OUT,load,accessor,sha
RUN=next((__import__('pathlib').Path(a[6:]) for a in sys.argv[1:] if a.startswith('--run=')),RUN);OUT=next((__import__('pathlib').Path(a[6:]) for a in sys.argv[1:] if a.startswith('--out=')),OUT);OUT.mkdir(parents=True,exist_ok=True)
np.seterr(all='raise');raw,j,b,p,start=load();RUN.mkdir(exist_ok=True);assert not (RUN/'rider.glb').exists(),'Existing trial must remain frozen'
rest,_,_=accessor(j,b,p['attributes']['POSITION']);ix,_,_=accessor(j,b,p['indices']);tri=ix.reshape(-1,3);si,siat,sistride=accessor(j,b,p['attributes']['JOINTS_0']);sw,swat,swstride=accessor(j,b,p['attributes']['WEIGHTS_0']);assert si.dtype==np.dtype('u1') and sw.dtype==np.dtype('<f4')
skin=j['skins'][0];bones=[j['nodes'][n]['name'].replace('.','') for n in skin['joints']];assert len(bones)==19;idx={b:i for i,b in enumerate(bones)};assert all(n in idx for n in ['pelvis','thighL','thighR']);W=np.zeros((len(rest),19));
for lane in range(4):np.add.at(W,(np.arange(len(rest)),si[:,lane]),sw[:,lane])
# Exact source aliases are a single physical unknown, including normal/UV splits.
unique,inverse=np.unique(rest,axis=0,return_inverse=True);first=np.array([np.flatnonzero(inverse==i)[0] for i in range(len(unique))]);UW=W[first];assert np.max(np.abs(W-UW[inverse]))<1e-7
ut= inverse[tri];edges=np.unique(np.sort(np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]),axis=1),axis=0);edges=edges[edges[:,0]!=edges[:,1]];length=np.linalg.norm(unique[edges[:,0]]-unique[edges[:,1]],axis=1);ew=1/np.maximum(length,1e-6);adj=coo_matrix((np.r_[ew,ew],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(unique),len(unique))).tocsr();L=diags(np.asarray(adj.sum(1)).ravel())-adj
pelvis=idx['pelvis'];legBones=[idx['thighL'],idx['thighR']];leg=UW[:,[pelvis,*legBones]].sum(1)
# Source inspection puts the bind hip within the hoodie hem. Visible gluteal
# lobes are lower; do not blindly put the visible pants blend at that joint.
hipX=.634775;hipY=.959175;active=(unique[:,1]>.72)&(unique[:,1]<hipY)&(np.abs(unique[:,2])<.235)&(leg>.99999)
# Boundaries keep current weights exact. Pin only anatomically supported source
# gluteal mass, inner groin and top/low thigh support; solve through connected
# surface edges, never across spatially nearby air gaps or a global strip.
outer=np.array((adj@(~active).astype(float))>0).ravel();fixed=(~active)|outer
values=UW[:,pelvis].copy();glute=active&(unique[:,0]<hipX)&(unique[:,1]>=.84)&(np.abs(unique[:,2])>=.045)&(~outer);groin=active&(unique[:,0]>.68)&(unique[:,1]>=.81)&(np.abs(unique[:,2])<.075)&(~outer);upper=active&(unique[:,1]>=.93)&(~outer);lower=active&(unique[:,1]<=.74)&(~outer)
values[glute|groin|upper]=1;values[lower]=0;fixed|=glute|groin|upper|lower;free=active&(~fixed);f=np.flatnonzero(free);k=np.flatnonzero(fixed);values[f]=spsolve(L[f][:,f],-(L[f][:,k]@values[k]));assert np.isfinite(values).all();assert values.min()>-1e-8 and values.max()<1.0000002;values=np.clip(values,0,1)
# Equal aliases and side assignment; current leg ownership dominates, then
# source bind side for previously pure-pelvis vertices. No opposite thigh mix.
side=np.where(UW[:,legBones[0]]+UW[:,legBones[1]]>1e-8,np.where(UW[:,legBones[0]]>=UW[:,legBones[1]],legBones[0],legBones[1]),np.where(unique[:,2]>=0,legBones[0],legBones[1]));candidate=W.copy();changedPhysical=active&(np.abs(values-UW[:,pelvis])>1e-6);physical=np.flatnonzero(changedPhysical)
for i in physical:
 ids=np.flatnonzero(inverse==i);candidate[ids]=0;candidate[ids,pelvis]=values[i];candidate[ids,side[i]]=1-values[i]
changed=np.flatnonzero(np.abs(candidate-W).max(1)>1e-6);assert len(changed)>0;assert np.all((rest[changed,1]>.72)&(rest[changed,1]<hipY));patched=bytearray(raw);allowed=set()
for v in changed:
 for lane,(bone,w) in enumerate([(pelvis,candidate[v,pelvis]),(int(side[inverse[v]]),1-candidate[v,pelvis]),(0,0),(0,0)]):
  at=start+siat+v*sistride+lane;patched[at]=bone;allowed.add(at)
  at=start+swat+v*swstride+lane*4;patched[at:at+4]=np.float32(w).tobytes();allowed.update(range(at,at+4))
result=bytes(patched);changes=[i for i,(a,c) in enumerate(zip(raw,result)) if a!=c];assert all(i in allowed for i in changes);assert result[:start]==raw[:start];assert SOURCE.read_bytes()==raw;(RUN/'rider.glb').write_bytes(result)
settings={'name':'one connected glute/groin support trial','activeBoundsSourceM':{'y':[.72,hipY],'absZBelow':.235},'admissibleBones':['pelvis','thighL','thighR'],'gluteAnchor':{'xBelow':hipX,'yFrom':.84,'absZFrom':.045,'pelvisWeight':1},'innerGroinAnchor':{'xAbove':.68,'yFrom':.81,'absZBelow':.075,'pelvisWeight':1},'upperAnchor':{'yFrom':.93,'pelvisWeight':1},'lowerThighAnchor':{'yThrough':.74,'pelvisWeight':0},'graph':'exact-position welded original triangle edges, inverse edge-length Laplacian Dirichlet solve','boundaries':'all neighbors outside eligible region retain exact current weights','singleTrial':True,'parameterSweep':False}
report={'source':str(SOURCE),'sourceSHA256':sha(raw),'candidate':str(RUN/'rider.glb'),'candidateSHA256':sha(result),'sourceUnchanged':True,'JSONHeaderAndNodesExact':True,'allBytesOutsideChangedBody0SkinEntriesExact':True,'geometryNormalsUVIndicesMorphImagesMaterialsAnimationBindsSocketsExact':True,'changedVertices':len(changed),'changedPhysicalVertices':len(physical),'changedBytes':len(changes),'physicalAnchors':{'glute':int(glute.sum()),'groin':int(groin.sum()),'upper':int(upper.sum()),'lowerThigh':int(lower.sum()),'free':len(f)},'settings':settings,'limits':'CPU-only single weight trial. No rendered or played adoption; normal player assets untouched.'};(OUT/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'settings.json').write_text(json.dumps(settings,indent=2)+'\n');np.savez_compressed(RUN/'weight-field.npz',sourceRest=rest,triangles=tri,originalWeights=W,candidateWeights=candidate,changedVertices=changed,unique=unique,pelvisField=values,gluteAnchors=glute,groinAnchors=groin,upperAnchors=upper,lowerAnchors=lower,active=active);print(json.dumps(report))
