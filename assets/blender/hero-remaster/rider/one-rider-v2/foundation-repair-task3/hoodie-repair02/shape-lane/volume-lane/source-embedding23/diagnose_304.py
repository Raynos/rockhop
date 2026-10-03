from pathlib import Path
import json,numpy as np
from embedding_driver25 import SourceEmbeddedSleeve
from chart_labels import ROOT,U
from build_embedding import frames
HERE=Path(__file__).resolve().parent;dr=SourceEmbeddedSleeve();f=dr.f;D=np.load(ROOT/'hoodie-repair03/inputs/source34-authoritative168-matrices.npz')['D'][304];dr.deform(D,True);q=np.load(HERE/'source23-embedded-304.npz');plain=np.load(HERE/'source23-plain-304.npz');cage=dr.cage;details={}
for side in ['L','R']:
 faces,slots,lookup=dr.mapping[side];tpose=dr.lastCage[0][cage.f['tr0'][faces]];F,_=frames(tpose);trest=cage.f['p0'][cage.f['tr0'][faces]];start=f['embedCSR'+side][:-1];w=f['embedWeight'+side];b=f['embedBarycentric'+side];off=f['embedLocalOffset'+side];footPose=np.add.reduceat(w[:,None]*np.einsum('rv,rvk->rk',b,tpose[slots]),start);footRest=np.add.reduceat(w[:,None]*np.einsum('rv,rvk->rk',b,trest[slots]),start);offPose=np.add.reduceat(w[:,None]*np.einsum('rij,rj->ri',F[slots],off),start);offRest=np.add.reduceat(w[:,None]*np.einsum('rij,rj->ri',f['embedCageFramesRest'+side][slots],off),start);details[side]=(lookup,footPose-footRest,offPose-offRest,footPose+offPose)
rows=[]
for pi in [0,2]:
 t=f[f'tr{pi}'];e=np.unique(np.sort(np.r_[t[:,[0,1]],t[:,[1,2]],t[:,[2,0]]],axis=1),axis=0);rest=f[f'p{pi}'];len0=np.linalg.norm(rest[e[:,1]]-rest[e[:,0]],axis=1);select=len0>=.005;e=e[select];len0=len0[select];posed=q[f'p{pi}'];len1=np.linalg.norm(posed[e[:,1]]-posed[e[:,0]],axis=1);order=np.argsort(len1/len0)[-10:][::-1]
 for k in order:
  a,b=e[k];ua,ub=f[f'physicalWeld{pi}'][[a,b]];endpoints=[]
  for v,u in [(a,ua),(b,ub)]:
   item={'sourceVertex':int(v),'sourceAlias':int(u),'sourceP':rest[v].tolist(),'plainQ':plain[f'p{pi}'][v].tolist(),'embeddedQ':posed[v].tolist(),'alpha':float(dr.embeddingAlpha[pi][v])}
   for side in ['L','R']:
    lookup,footDelta,offDelta,full=details[side];r=lookup[u]
    if r>=0:
     lo,hi=f['embedCSR'+side][r:r+2];ww=f['embedWeight'+side][lo:hi];cf=f['embedCageFace'+side][lo:hi];ss=np.argsort(ww)[-5:][::-1];item.update({'side':side,'mappedQ':full[r].tolist(),'mappedMinusPlainM':(full[r]-plain[f'p{pi}'][v]).tolist(),'footpointDisplacementM':footDelta[r].tolist(),'frameOffsetDisplacementM':offDelta[r].tolist(),'sourceBoundaryDistanceM':float(f['embedBoundaryDistanceM'+side][r]),'supportComponents':int(f['embedSupportComponents'+side][r]),'supportReferences':int(hi-lo),'offsetMaxM':float(np.linalg.norm(f['embedLocalOffset'+side][lo:hi],axis=1).max()),'dominantControlFaces':[{'face':int(cf[j]),'kind':str(cage.f['faceKind0'][cf[j]]),'weight':float(ww[j])}for j in ss]})
   endpoints.append(item)
  plainEdge=plain[f'p{pi}'][b]-plain[f'p{pi}'][a];extra=(posed[b]-plain[f'p{pi}'][b])-(posed[a]-plain[f'p{pi}'][a]);rows.append({'primitive':pi,'vertices':[int(a),int(b)],'sourceLengthM':float(len0[k]),'posedLengthM':float(len1[k]),'stretch':float(len1[k]/len0[k]),'plainStretch':float(np.linalg.norm(plainEdge)/len0[k]),'extraEmbeddingEdgeVectorM':extra.tolist(),'extraEmbeddingEdgeVectorNormM':float(np.linalg.norm(extra)),'endpoints':endpoints})
r={'status':'READONLY FAILED304 BINDING ATTRIBUTION; no candidate changes','sourceSHA256':f['cageSHA256'].item(),'worstEdges':rows};(HERE/'source23-304-edge-attribution.json').write_text(json.dumps(r,indent=2));print(json.dumps(rows[:3],indent=2))
