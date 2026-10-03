"""True cuff-connected sleeve cross-sections before new proximal construction.
Geometry-independent topological cuff component, then exact source edge clips.
No source/rest geometry or skin input is changed by this inventory.
"""
from pathlib import Path
import numpy as np,json,sys,hashlib
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from chart_labels import *
c=SourceCharts();threshold=1.165;ct=c.ct;p=c.unique;edges=c.edges;inside=p[:,1]<=threshold;ee=edges[inside[edges].all(1)];g=coo_matrix((np.ones(2*len(ee)),(np.r_[ee[:,0],ee[:,1]],np.r_[ee[:,1],ee[:,0]])),shape=(len(U),len(U))).tocsr();_,component=connected_components(g);off=np.r_[0,len(c.tri[0]),len(c.tri[0])+len(c.tri[2])];out={'sourceUniqueRest':p,'sourceAlias':INV,'primitiveOffsets':OFF,'sourceClothFacesUnique':ct,'clipPlaneY':np.array(threshold)};rows=[]
for sg,side in [(1,'L'),(-1,'R')]:
 cuff=c.cuff[U[c.cuff,2]*sg>0];labels=np.unique(component[cuff]);tube=inside&np.isin(component,labels);keepFace=tube[ct].all(1);crossFace=tube[ct].any(1)&~keepFace;crossIds=np.flatnonzero(crossFace);pointEdges=[];segments=[];ancestry=[];keyToId={}
 for fi in crossIds:
  tri=ct[fi];hits=[]
  for a,b in zip(tri,np.roll(tri,-1)):
   if inside[a]==inside[b]:continue
   edge=tuple(sorted((int(a),int(b))))
   if edge not in keyToId:keyToId[edge]=len(pointEdges);pointEdges.append(edge)
   hits.append(keyToId[edge])
  assert len(hits)==2,(int(fi),hits);segments.append(hits);ancestry.append(fi)
 segments=np.array(segments,int);pe=np.array(pointEdges,int);t=(threshold-p[pe[:,0],1])/(p[pe[:,1],1]-p[pe[:,0],1]);xyz=p[pe[:,0]]+(p[pe[:,1]]-p[pe[:,0]])*t[:,None];adj={}
 for a,b in segments:adj.setdefault(int(a),[]).append(int(b));adj.setdefault(int(b),[]).append(int(a))
 assert all(len(v)==2 for v in adj.values());first=min(adj);prev=None;v=first;loop=[]
 while v not in loop:loop.append(v);nxt=[x for x in adj[v]if x!=prev][0];prev,v=v,nxt
 assert v==first and len(loop)==len(adj)
 out[f'retainedTubeFaceMask{side}']=keepFace;out[f'clippedTubeFaceIDs{side}']=crossIds;out[f'ringSourceEdges{side}']=pe;out[f'ringSourceBarycentric{side}']=np.c_[1-t,t];out[f'ringRestPositions{side}']=xyz;out[f'ringSegments{side}']=segments;out[f'ringSegmentSourceFace{side}']=np.array(ancestry);out[f'ringOrderedNodes{side}']=np.array(loop);out[f'cuffAliases{side}']=cuff
 # Every edge clip also has literal source-primitive UV/weight ancestry.
 records=[]
 for fi,hits in zip(crossIds,segments):
  pi=0 if fi<off[1]else 2;local=int(fi if pi==0 else fi-off[1]);vi=c.tri[pi][local];uid=INV[vi+OFF[pi]];uv=G.array(PR[pi]['attributes']['TEXCOORD_0'])
  for k in hits:
   a,b=pe[k];ia=vi[np.flatnonzero(uid==a)[0]];ib=vi[np.flatnonzero(uid==b)[0]];tex=uv[ia]*(1-t[k])+uv[ib]*t[k];records.append({'ringNode':int(k),'primitive':pi,'sourceFace':local,'sourceVertexEdge':[int(ia),int(ib)],'sourceUniqueEdge':[int(a),int(b)],'edgeBarycentric':[float(1-t[k]),float(t[k])],'exactInterpolatedUV':tex.tolist()})
 rows.append({'side':side,'clipPlaneY':threshold,'retainedCompleteSourceFaces':int(keepFace.sum()),'clippedSourceFaces':len(crossIds),'closedDegreeTwoRing':True,'ringVertices':len(loop),'rangeMin':xyz.min(0).tolist(),'rangeMax':xyz.max(0).tolist(),'ringPerimeterM':float(np.linalg.norm(xyz[loop]-np.roll(xyz[loop],-1,axis=0),axis=1).sum()),'sourceUVAncestry':records})
np.savez_compressed(HERE/'sleeve-cut-inventory.npz',**out);r={'status':'CUT_INVENTORY_ONLY; no regenerated garment or motion acceptance','sourceV7SHA256':hashlib.sha256(c.input.read_bytes()).hexdigest(),'previousHigherArmholeFreezeSHA256':'10a1c2094726e7ab929b453e07e5f9c072dd06b0673a8557f4f41c6c5e33c2d7','method':'Actual sleeve components containing original exact cuff aliases on source edgegraph restrictedbelow1.165m; intersect original source faces with that plane and order degree-two crossing ring. No face-normal guesses or skin ownership thresholds. Source triangle/edge/UV ancestry stored for every intersection.','protectedInventory':'Primitives1/3/4 unchanged; source cuff and all complete/clipped lower sleeve faces retain exact source attrs with barycentric new cut-edge attrs. Source body outside the declared old underarm bridge/proximal sleeve faces remains protected. This inventory does not yet declare the final removed bridge or body-cap triangles.','rows':rows};(HERE/'sleeve-cut-inventory.json').write_text(json.dumps(r,indent=2));print(json.dumps({**{k:v for k,v in r.items()if k!='rows'},'rows':[{k:v for k,v in x.items()if k!='sourceUVAncestry'}for x in rows]},indent=2))
