"""Original source-surface embedding in frozen21 hidden material cage.
Rest-only inventory; moving cage22 is a known failed control.
"""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial import cKDTree
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import dijkstra,connected_components
HERE=Path(__file__).resolve().parent;LANE=HERE.parent;CAGE=LANE/'sleeve-tube03';sys.path.insert(0,str(LANE));from chart_labels import ROOT,G,PR,POS,NOR,TRI,U,INV,OFF,SourceCharts,smooth

def closest(p,T):
 a=T[:,0];ab=T[:,1]-a;ac=T[:,2]-a;ap=p-a;aa=np.einsum('ij,ij->i',ab,ab);bb=np.einsum('ij,ij->i',ab,ac);cc=np.einsum('ij,ij->i',ac,ac);ad=np.einsum('ij,ij->i',ap,ab);cd=np.einsum('ij,ij->i',ap,ac);den=aa*cc-bb*bb;v=(cc*ad-bb*cd)/np.maximum(den,1e-30);w=(aa*cd-bb*ad)/np.maximum(den,1e-30);b=np.c_[1-v-w,v,w];q=np.einsum('tv,tvk->tk',b,T);inside=(b>=0).all(1);best=np.full(len(T),np.inf);out=np.zeros_like(b)
 best[inside]=np.einsum('ij,ij->i',(q-p)[inside],(q-p)[inside]);out[inside]=b[inside]
 for i,j in [(0,1),(1,2),(2,0)]:
  e=T[:,j]-T[:,i];t=np.clip(np.einsum('ij,ij->i',p-T[:,i],e)/np.maximum(np.einsum('ij,ij->i',e,e),1e-30),0,1);foot=T[:,i]+t[:,None]*e;d=np.einsum('ij,ij->i',foot-p,foot-p);take=d<best;bb=np.zeros_like(b);bb[:,i]=1-t;bb[:,j]=t;best[take]=d[take];out[take]=bb[take]
 return out,np.sqrt(best)

def frames(T):
 e=T[:,1]-T[:,0];e/=np.maximum(np.linalg.norm(e,axis=1)[:,None],1e-30);n=np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]);area=np.linalg.norm(n,axis=1);n/=np.maximum(area[:,None],1e-30);return np.stack([e,np.cross(n,e),n],axis=-1),area

if __name__=='__main__':
 cagePath=CAGE/'source-sleeve-tube-rest21-uvchart.npz';f=np.load(cagePath);c=SourceCharts();cut=np.load(CAGE/'sleeve-cut-inventory.npz');exp=np.load(CAGE/'expanded-torso-cut-inventory.npz');sourceCT=c.ct;clothIDs=np.unique(sourceCT);edges=c.edges;length=np.linalg.norm(U[edges[:,0]]-U[edges[:,1]],axis=1);sourceG=coo_matrix((np.r_[length,length],(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(U),len(U))).tocsr();counts=np.bincount(sourceCT.ravel(),minlength=len(U));out={};maps=[];report=[]
 # Preserve original high-resolution C19/body11 P/N/UV/tr byte values;
 # source-control W is frozen V7, an explicitly distinct baseline.
 for pi in range(5):
  p=POS[pi].copy();tr=TRI[pi].copy();out.update({f'p{pi}':p,f'n{pi}':NOR[pi].copy(),f'uv{pi}':G.array(PR[pi]['attributes']['TEXCOORD_0']).astype(float),f'W{pi}':c.w[pi].copy(),f'tr{pi}':tr,f'physicalWeld{pi}':INV[OFF[pi]:OFF[pi+1]].copy(),f'physicalGarment{pi}':np.full(len(p),0 if pi in[0,2]else pi,int),f'oldVertex{pi}':np.arange(len(p)),f'sourceUniqueVertex{pi}':INV[OFF[pi]:OFF[pi+1]].copy(),f'sourceVertexParents{pi}':np.c_[np.arange(len(p)),np.full(len(p),-1)],f'sourceVertexBarycentric{pi}':np.c_[np.ones(len(p)),np.zeros(len(p))],f'sourceFaceAncestry{pi}':np.arange(len(tr)),f'faceKind{pi}':np.full(len(tr),'original-visible-source')});q=p[tr];out[f'restDoubleArea{pi}']=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)
 for sg,side in [(1,'L'),(-1,'R')]:
  removed=exp['deletedSourceFaces'+side].copy();removed[cut['clippedTubeFaceIDs'+side]]=True;regionCount=np.bincount(sourceCT[removed].ravel(),minlength=len(U));domain=regionCount>0;boundary=domain&(regionCount<counts);boundary|=domain&(U[:,1]<=float(cut['clipPlaneY']));boundary[c.cuff]=True;dist=dijkstra(sourceG,indices=np.flatnonzero(boundary),min_only=True);alpha=np.zeros(len(U));alpha[domain]=smooth(dist[domain]/.020);alpha[boundary]=0;ids=np.flatnonzero(alpha>0);assert(U[ids,2]*sg>0).all();faces=np.r_[f['bodyCapFaceIDs'+side],f['newTubeFaceIDs'+side]];T=f['p0'][f['tr0'][faces]];F,area=frames(T);centres=T.mean(1);radii=np.linalg.norm(T-centres[:,None],axis=2).max(1);tree=cKDTree(centres);maxR=radii.max();starts=[0];allFace=[];allBary=[];allOffset=[];allWeight=[];supports=[];nearestDistances=[];supportComponents=[];reconstructed=[];normalSpreads=[]
  # Physical triangle adjacency lets us diagnose accidentally mixed sheets.
  weld=f['physicalWeld0'][f['tr0'][faces]];edgeFaces={}
  for j,t in enumerate(weld):
   for a,b in [(t[0],t[1]),(t[1],t[2]),(t[2],t[0])]:edgeFaces.setdefault(tuple(sorted((int(a),int(b)))),[]).append(j)
  adjacent=set()
  for group in edgeFaces.values():
   for a in group:
    for b in group:
     if a!=b:adjacent.add((a,b))
  adjlist={i:[] for i in range(len(faces))}
  for a,b in adjacent:adjlist[a].append(b)
  for idx,uid in enumerate(ids):
   p=U[uid];_,first=tree.query(p,k=min(32,len(T)));b,d=closest(p,T[np.atleast_1d(first)]);guess=d.min();candidate=np.array(tree.query_ball_point(p,guess+maxR+1e-10),int);bc,dc=closest(p,T[candidate]);minimum=dc.min();radius=minimum+.025;candidate=np.array(tree.query_ball_point(p,radius+maxR+1e-10),int);bc,dc=closest(p,T[candidate]);keep=dc<radius;candidate=candidate[keep];bc=bc[keep];dc=dc[keep];r=dc/radius;weight=area[candidate]*(1-r)**4*(4*r+1);weight/=weight.sum();foot=np.einsum('tv,tvk->tk',bc,T[candidate]);offset=np.einsum('tji,tj->ti',F[candidate],p-foot);rec=foot+np.einsum('tij,tj->ti',F[candidate],offset);reconstructed.append(np.einsum('t,ti->i',weight,rec));allFace.extend(faces[candidate]);allBary.extend(bc);allOffset.extend(offset);allWeight.extend(weight);starts.append(len(allFace));supports.append(len(candidate));nearestDistances.append(minimum)
   # Number of support components is diagnostic, not silently filtered.
   selected=set(candidate.tolist());seen=set();ncomp=0
   for seed in selected:
    if seed in seen:continue
    ncomp+=1;stack=[seed];seen.add(seed)
    while stack:
     for nb in adjlist[stack.pop()]:
      if nb in selected and nb not in seen:seen.add(nb);stack.append(nb)
   supportComponents.append(ncomp);normals=F[candidate,:,2];mean=np.einsum('t,ti->i',weight,normals);normalSpreads.append(float(np.linalg.norm(mean)))
   if idx%500==0:print(side,idx,'/',len(ids),'support references',len(allFace),flush=True)
  starts=np.array(starts,int);allFace=np.array(allFace,int);allBary=np.array(allBary);allOffset=np.array(allOffset);allWeight=np.array(allWeight);reconstructed=np.array(reconstructed);assert np.max(abs(reconstructed-U[ids]))<1e-12
  maps.append((side,ids));out.update({f'embedSourceAliases{side}':ids,f'embedAlpha{side}':alpha[ids],f'embedCSR{side}':starts,f'embedCageFace{side}':allFace,f'embedBarycentric{side}':allBary,f'embedLocalOffset{side}':allOffset,f'embedWeight{side}':allWeight,f'embedBoundaryAliases{side}':np.flatnonzero(boundary&domain),f'embedAffectedSourceFaces{side}':np.flatnonzero(removed),f'embedBoundaryDistanceM{side}':dist[ids],f'embedCageFaceIDs{side}':faces,f'embedCageFramesRest{side}':F,f'embedSupportComponents{side}':np.array(supportComponents),f'embedSupportRadiusPaddingM{side}':np.array(.025)})
  report.append({'side':side,'affectedSourceFaces':int(removed.sum()),'mappedAliases':len(ids),'boundaryAliases':int((boundary&domain).sum()),'mappedReferences':len(allFace),'supportCountMaximum':max(supports),'supportCountP99':float(np.percentile(supports,99)),'nearestDistanceMaxM':max(nearestDistances),'nearestDistanceP99M':float(np.percentile(nearestDistances,99)),'offsetMaximumM':float(np.linalg.norm(allOffset,axis=1).max()),'offsetP99M':float(np.percentile(np.linalg.norm(allOffset,axis=1),99)),'disconnectedSupports':int((np.array(supportComponents)>1).sum()),'maximumSupportComponents':max(supportComponents),'minimumWeightedNormalCoherence':min(normalSpreads),'neutralReconstructionMaximumM':float(np.max(abs(reconstructed-U[ids]))),'sourceBoundaryMarginM':.020})
 assert not np.intersect1d(maps[0][1],maps[1][1]).size
 out['sourceAlias']=INV;out['sourceOffsets']=OFF;out['cagePath']=np.array(str(cagePath));out['cageSHA256']=np.array(hashlib.sha256(cagePath.read_bytes()).hexdigest());target=HERE/'original-source-embedded-rest23.npz';np.savez_compressed(target,**out)
 r={'status':'STATIC_EMBEDDING_INVENTORY_ONLY; no motion qualification','candidateSHA256':hashlib.sha256(target.read_bytes()).hexdigest(),'hiddenCageSHA256':out['cageSHA256'].item(),'sourceC19SHA256':hashlib.sha256((ROOT/'deliverables/C19.glb').read_bytes()).hexdigest(),'method':'One source-physical-alias binding. Exact closest-triangle barycentric footpoints plus orthonormal rest-frame offsets. All nearby cage triangles receive positive area-weighted WendlandC2 support inside nearest-distance+25mm compact radius; no runtime donor switches or semantic weight labels. Exact original source LBS at declared20mm source-geodesic region boundary/cuffs, smooth alpha blend inside. Original highresolution source P/N/UV/tr and images retained, frozenV7 source-prefix W causalcontrol.','rows':report,'originalRestAttributesExact':all(np.array_equal(out[f'{k}{pi}'],arr[pi])for pi in range(5)for k,arr in [('p',POS),('n',NOR),('tr',TRI)]),'baselineRestCrossings':'Original C19/body11 inherited11 thin-source crossings in prior widerupper source audit; no fake0 baseline. Source mesh unchanged.','knownCageFailure':'21restpassed butstandingrejected; driver22 exact304914+104 crossings/81newfabriccollapse,4.915xmax meaningfulstretch. This transfer is an unqualified filter hypothesis.','runtime':'Explicit postbone geometry adapter; mapstorage/CPUcost measured separately. No stockskin-only equivalence or productionpromotion.'};(HERE/'embedding23-provenance.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
