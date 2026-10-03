"""Source-local true sleeve tube and expanded torso rim; unaccepted rest clone."""
from pathlib import Path
import numpy as np,json,sys,ast,hashlib
from scipy.interpolate import RBFInterpolator
from scipy.sparse import coo_matrix,diags
from scipy.sparse.linalg import factorized
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from chart_labels import *
c=SourceCharts();cut=np.load(HERE/'sleeve-cut-inventory.npz');expand=np.load(HERE/'expanded-torso-cut-inventory.npz');old=np.load(HERE.parent/'armhole-construction/source-armhole-cut.npz')
# Reuse only pure installed-Three earcut/refinement helpers, not build side effects.
s=(HERE.parent/'armhole-construction/rebuild_chart_outward.py').read_text();nodes=[n for n in ast.parse(s).body if isinstance(n,ast.FunctionDef)and n.name in ['earcut','refine_chart','inside']];import subprocess
exec(compile(ast.Module(body=nodes,type_ignores=[]),'<pure existing chart helpers>','exec'))
sourceUV=[G.array(pr['attributes']['TEXCOORD_0']).astype(float)for pr in PR];shape=np.load(ROOT/'hoodie-repair02/v7-shape-input.npz');p=[x.copy().tolist()for x in c.pos];uv=[x.tolist()for x in sourceUV];w=[x.copy().tolist()for x in c.w];normal=[shape[f'n{i}'].copy().tolist()for i in range(5)];ancestry=[list(range(len(x)))for x in c.pos];weld=[INV[OFF[i]:OFF[i+1]].tolist()for i in range(5)];sourceUID=[x.copy()for x in weld];sourceParents=[[[j,-1]for j in range(len(x))]for x in c.pos];sourceBary=[[[1.,0.]for _ in x]for x in c.pos];nxt=len(U);clipIDs={};ringIDs={};faceParents=[[]for _ in range(5)];kind=[[]for _ in range(5)];tr=[[]for _ in range(5)]
# Coherent original gold-cloth donor; no image change.
prov=json.loads((HERE.parent/'armhole-construction/armhole-chart-outward-provenance.json').read_text());donorFace=prov['UVDonor']['sourceFace'];donorUV=sourceUV[0][c.tri[0][donorFace]].mean(0)
def patchUV(point):return donorUV+(np.asarray(point)[:2]-[.63,1.335])*[.018/.22,.018/.35]
def append(pi,point,ww,tex,parent=(-1,-1),bary=(0.,0.),physical=None,uid=-1):
 global nxt
 i=len(p[pi]);p[pi].append(np.asarray(point).tolist());w[pi].append(np.asarray(ww).tolist());uv[pi].append(np.asarray(tex).tolist());normal[pi].append([0,0,0]);ancestry[pi].append(-1);sourceParents[pi].append(list(parent));sourceBary[pi].append(list(bary));sourceUID[pi].append(uid)
 if physical is None:physical=nxt;nxt+=1
 weld[pi].append(int(physical));return i
clipEdgePhysical={};clipEdgeNodes={s:{tuple(e):k for k,e in enumerate(cut['ringSourceEdges'+s])}for s in ['L','R']};threshold=float(cut['clipPlaneY']);nodeDirected={s:[]for s in ['L','R']}
for pi in range(5):
 if pi not in [0,2]:tr[pi]=c.tri[pi].tolist();faceParents[pi]=list(range(len(c.tri[pi])));kind[pi]=['protected']*len(tr[pi]);continue
 partoff=0 if pi==0 else len(c.tri[0]);uid=INV[OFF[pi]:OFF[pi+1]]
 for fi,original in enumerate(c.tri[pi]):
  globalf=partoff+fi;side=None
  for ss in ['L','R']:
   if globalf in set(cut['clippedTubeFaceIDs'+ss]):side=ss;break
  if side is not None:
   poly=[]
   for a,b in zip(original,np.roll(original,-1)):
    ia=c.pos[pi][a,1]<=threshold;ib=c.pos[pi][b,1]<=threshold
    if ia:poly.append((int(a),None))
    if ia!=ib:
     edge=tuple(sorted((int(uid[a]),int(uid[b]))));node=clipEdgeNodes[side][edge];key=(pi,side,min(int(a),int(b)),max(int(a),int(b)));t=(threshold-c.pos[pi][a,1])/(c.pos[pi][b,1]-c.pos[pi][a,1])
     if key not in clipIDs:
      physkey=(side,edge)
      if physkey not in clipEdgePhysical:clipEdgePhysical[physkey]=nxt;nxt+=1
      point=c.pos[pi][a]*(1-t)+c.pos[pi][b]*t;ww=c.w[pi][a]*(1-t)+c.w[pi][b]*t;tex=sourceUV[pi][a]*(1-t)+sourceUV[pi][b]*t;clipIDs[key]=append(pi,point,ww,tex,(int(a),int(b)),(1-t,t),clipEdgePhysical[physkey]);ringIDs.setdefault((side,node),(pi,clipIDs[key]))
     poly.append((clipIDs[key],node))
   for a,b in zip(poly,poly[1:]+poly[:1]):
    if a[1]is not None and b[1]is not None:nodeDirected[side].append((a[1],b[1]))
   for j in range(1,len(poly)-1):tr[pi].append([poly[0][0],poly[j][0],poly[j+1][0]]);faceParents[pi].append(fi);kind[pi].append('retained-clipped-'+side)
  elif expand['deletedSourceFacesL'][globalf]or expand['deletedSourceFacesR'][globalf]:continue
  else:tr[pi].append(original.tolist());faceParents[pi].append(fi);kind[pi].append('retained')
construction={};rows=[]
for sg,side,a in [(1,'L',6),(-1,'R',10)]:
 edges=dict(nodeDirected[side]);assert len(edges)==len(cut['ringOrderedNodes'+side]);first=min(edges);endOrder=[];v=first
 while v not in endOrder:endOrder.append(v);v=edges[v]
 assert v==first and len(endOrder)==len(edges);endPos=cut['ringRestPositions'+side][endOrder];endCentre=endPos.mean(0);theta=np.arctan2(endPos[0,2]-endCentre[2],endPos[0,0]-endCentre[0]);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(np.r_[endPos,endPos[None,0]],axis=0),axis=1))][:-1];per=np.linalg.norm(endPos-np.roll(endPos,-1,axis=0),axis=1).sum();Nring=len(endPos);angles=theta+arc/per*2*np.pi
 # The original cuff tube must be oriented around its downwards centreline.
 xz=endPos[:,[0,2]];assert ((xz[:,0]*np.roll(xz[:,1],-1)-xz[:,1]*np.roll(xz[:,0],-1)).sum()>0),('ring orientation',side)
 torsoLoop=expand['rawBoundaryLoop'+side+'0'];outer=c.unique[torsoLoop];slope=0 if sg==1 else .2;outerXY=np.c_[outer[:,0],outer[:,1]+slope*outer[:,2]];area=np.cross(outerXY,np.roll(outerXY,-1,axis=0)).sum()
 if area*sg<0:torsoLoop=torsoLoop[::-1];outer=c.unique[torsoLoop];outerXY=np.c_[outer[:,0],outer[:,1]+slope*outer[:,2]]
 zguess=float(np.median(outer[:,2]));holeXY=np.c_[.627+.070*np.cos(angles),1.385+sg*.072*np.sin(angles)+slope*zguess];assert inside(holeXY,outerXY).all();n=len(outer);fit=RBFInterpolator(outerXY,outer[:,2],kernel='thin_plate_spline',smoothing=1e-10);xy=np.r_[outerXY,holeXY];tess=earcut(outerXY,holeXY[::-1]);lookup=np.r_[np.arange(n),np.arange(n,n+Nring)[::-1]];tess=lookup[tess];q=xy[tess];signed=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);tess[signed*sg<0]=tess[signed*sg<0][:,[0,2,1]];boundary=np.r_[np.c_[np.arange(n),np.roll(np.arange(n),-1)],np.c_[np.arange(n,n+Nring),np.roll(np.arange(n,n+Nring),-1)]];xy,tess=refine_chart(xy,tess,boundary,maxLength=.020);z=fit(xy);z[:n]=outer[:,2];point=np.c_[xy[:,0],xy[:,1]-slope*z,z];ee=np.unique(np.sort(np.r_[tess[:,[0,1]],tess[:,[1,2]],tess[:,[0,2]]],axis=1),axis=0);ll=np.linalg.norm(point[ee[:,0]]-point[ee[:,1]],axis=1);ew=1/np.maximum(ll,.002)**2;g=coo_matrix((np.r_[ew,ew],(np.r_[ee[:,0],ee[:,1]],np.r_[ee[:,1],ee[:,0]])),shape=(len(point),len(point))).tocsr();L=diags(np.asarray(g.sum(1)).ravel())-g;fixed=np.arange(n+Nring);free=np.arange(n+Nring,len(point));solve=factorized(L[free][:,free].tocsc());ww=np.zeros((len(point),19));ww[:n]=c.uw[torsoLoop];ww[n:n+Nring,2]=1
 for bone in range(19):ww[free,bone]=solve(-L[free][:,fixed]@ww[fixed,bone])
 ww=np.maximum(ww,0);ww/=ww.sum(1)[:,None];bodyIds=[]
 for j,q in enumerate(point):bodyIds.append(append(0,q,ww[j],patchUV(q),physical=int(torsoLoop[j])if j<n else None,uid=int(torsoLoop[j])if j<n else-1))
 capStart=len(tr[0]);tr[0].extend(np.array(bodyIds)[tess].tolist());faceParents[0].extend([-1]*len(tess));kind[0].extend(['body-cap-'+side]*len(tess));rootIds=np.array(bodyIds[n:n+Nring]);rootPos=point[n:n+Nring];C0=rootPos.mean(0);C3=endCentre;C1=C0+[0,0,sg*.100];C2=np.array([C3[0],1.345,C3[2]]);srows=np.linspace(0,1,13);tubeRows=[rootIds];tubePositions=[rootPos];endWW=np.array([w[ringIDs[(side,node)][0]][ringIDs[(side,node)][1]]for node in endOrder]);endRadial=np.c_[endPos[:,0]-C3[0],endPos[:,2]-C3[2]];rootProfile=np.c_[.070*np.cos(angles),.072*np.sin(angles)]
 for r in srows[1:-1]:
  centre=(1-r)**3*C0+3*(1-r)**2*r*C1+3*(1-r)*r*r*C2+r**3*C3;T=unit((3*(1-r)**2*(C1-C0)+6*(1-r)*r*(C2-C1)+3*r*r*(C3-C2))[None])[0];e1=np.array([1.,0,0]);e2=unit(np.cross(T,e1)[None])[0];blend=smooth(r);radial=(1-blend)*rootProfile+blend*endRadial;radiusFactor=1-.24*np.sin(np.pi*r);radial[:,1]*=radiusFactor;restResidual=rootPos-(C0+rootProfile[:,0,None]*e1+rootProfile[:,1,None]*np.array([0,sg,0]));row=centre+radial[:,0,None]*e1+radial[:,1,None]*e2+restResidual*(1-r)**2;weight=(1-blend)*np.eye(19)[2]+blend*endWW;ids=[]
  for j,q in enumerate(row):ids.append(append(0,q,weight[j],patchUV(q)))
  tubeRows.append(np.array(ids));tubePositions.append(row)
 endIds=[]
 for node in endOrder:
  pi,idx=ringIDs[(side,node)]
  if pi==0:endIds.append(idx)
  else:endIds.append(append(0,p[pi][idx],w[pi][idx],uv[pi][idx],physical=weld[pi][idx]))
 tubeRows.append(np.array(endIds));tubePositions.append(endPos);tubeRows=np.array(tubeRows);tubeStart=len(tr[0]);newFaces=[]
 for row,nextrow in zip(tubeRows,tubeRows[1:]):
  for j in range(Nring):k=(j+1)%Nring;newFaces.extend([[row[j],row[k],nextrow[j]],[row[k],nextrow[k],nextrow[j]]])
 tr[0].extend(newFaces);faceParents[0].extend([-1]*len(newFaces));kind[0].extend(['new-tube-'+side]*len(newFaces));construction.update({f'torsoSourceBoundary{side}':torsoLoop,f'bodyOpeningVertices{side}':rootIds,f'tubeRows{side}':tubeRows,f'tubeRestRows{side}':np.array(tubePositions),f'tubeEndSourceNodes{side}':np.array(endOrder),f'bodyCapFaceIDs{side}':np.arange(capStart,capStart+len(tess)),f'newTubeFaceIDs{side}':np.arange(tubeStart,tubeStart+len(newFaces)),f'curveControlRest{side}':np.array([C0,C1,C2,C3])});rows.append({'side':side,'expandedTorsoBoundaryVertices':n,'sourceSleeveRingVertices':Nring,'newCapFaces':len(tess),'newTubeFaces':len(newFaces),'torsoChartTiltSlope':slope,'tubeCentreline':'Cubic curve with outward torso normal at root and downwards tube tangent at retained sleeve ring; globalX transverse frame and continuous second frame. Rest radii from source ring and anatomical root ellipse.'})
# Original source normal rows stay exact; new and clipped vertices get welded
# geometric normals. Source shading changes are explicitly inventoried later.
p=[np.array(x)for x in p];w=[np.array(x)for x in w];uv=[np.array(x)for x in uv];tr=[np.array(x,int)for x in tr];fullWeld=np.concatenate(weld);maxw=max(fullWeld)+1;nn=np.zeros((maxw,3))
for pi in [0,2]:
 q=p[pi][tr[pi]];n=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);ids=np.array(weld[pi])[tr[pi]]
 for j in range(3):np.add.at(nn,ids[:,j],n)
nn=unit(nn)
for pi in [0,2]:normal[pi]=np.r_[shape[f'n{pi}'],nn[np.array(weld[pi])[len(c.pos[pi]):]]]
out={}
for pi in range(5):
 out.update({f'p{pi}':p[pi],f'W{pi}':w[pi],f'uv{pi}':uv[pi],f'n{pi}':np.array(normal[pi]),f'tr{pi}':tr[pi],f'physicalWeld{pi}':np.array(weld[pi]),f'physicalGarment{pi}':np.full(len(p[pi]),0 if pi in[0,2]else pi,int),f'oldVertex{pi}':np.array(ancestry[pi]),f'sourceUniqueVertex{pi}':np.array(sourceUID[pi]),f'sourceVertexParents{pi}':np.array(sourceParents[pi]),f'sourceVertexBarycentric{pi}':np.array(sourceBary[pi]),f'sourceFaceAncestry{pi}':np.array(faceParents[pi]),f'faceKind{pi}':np.array(kind[pi])});q=p[pi][tr[pi]];out[f'restDoubleArea{pi}']=np.linalg.norm(np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]),axis=1)
out.update(construction);np.savez_compressed(HERE/'source-sleeve-tube-rest.npz',**out);(HERE/'source-sleeve-tube-rest-provenance.json').write_text(json.dumps({'status':'UNACCEPTED REST CONSTRUCTION; all literal and visual gates pending','sourceV7SHA256':hashlib.sha256(c.input.read_bytes()).hexdigest(),'candidateSHA256':hashlib.sha256((HERE/'source-sleeve-tube-rest.npz').read_bytes()).hexdigest(),'rows':rows,'originalVertexPrefixPositionsWeightsUVNormalsExact':True,'protectedHeadGloveCheekExact':True,'imagesOriginal':True,'removedOriginalSourceFaces':int(expand['deletedSourceFacesL'].sum()+expand['deletedSourceFacesR'].sum()),'newVertexCounts':[len(x)-len(y)for x,y in zip(p,c.pos)],'newTriangleCounts':[len(x)-len(y)for x,y in zip(tr,c.tri)],'maxInfluences':max(int((x>1e-8).sum(1).max())for x in w),'weights':'Rest prototype only; existing originalW rows held, clipped ring barycentric W exact. Added fabric torso-to-arm endpoint interpolation; not qualified. No staticW parameter search.'},indent=2));print(json.dumps(rows,indent=2));print('counts',[len(x)for x in p],[len(x)for x in tr],flush=True)
