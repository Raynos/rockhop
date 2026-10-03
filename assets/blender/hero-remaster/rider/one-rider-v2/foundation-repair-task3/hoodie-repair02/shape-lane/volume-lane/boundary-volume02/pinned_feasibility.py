"""Necessary fixed-boundary feasibility check before collision optimization."""
from pathlib import Path
import numpy as np,json
HERE=Path(__file__).resolve().parent;H=HERE.parents[2];f=np.load(HERE.parent/'armhole-construction/armhole-chart-outward.npz');d=np.load(H/'rig-lane/construction-weights/poses/shape_control-actual_source34-304.npz');q=np.r_[d['p0'],d['p2']];tr=np.r_[f['tr0'],f['tr2']+len(f['p0'])];T=q[tr];source=np.r_[np.ones(33968,bool),np.zeros(len(f['newFaceKind']),bool),np.ones(len(f['tr2']),bool)];pin=np.zeros(len(q),bool)
for side in ['L','R']:
 for key in ['bodyBoundaryVertices','bodyOpeningVertices','sleeveBoundaryVertices']:pin[f[key+side]]=True
hits=json.loads((HERE/'shape_control-actual_source34-304-all-pairs.json').read_text())['crossingPairs'];proof=[]
for a,b in hits:
 if source[a]==source[b]:continue
 nf,sf=(b,a)if source[a]else(a,b);verts=tr[nf]
 for e in [[0,1],[1,2],[2,0]]:
  v0,v1=verts[e]
  if not(pin[v0]and pin[v1]):continue
  s0=q[v0];delta=q[v1]-s0;t=T[sf];normal=np.cross(t[1]-t[0],t[2]-t[0]);den=np.dot(normal,delta)
  if abs(den)<1e-12:continue
  along=np.dot(normal,t[0]-s0)/den
  if along<=1e-8 or along>=1-1e-8:continue
  p=s0+along*delta;a0=t[1]-t[0];b0=t[2]-t[0];x=p-t[0];aa=np.dot(a0,a0);ab=np.dot(a0,b0);bb=np.dot(b0,b0);det=aa*bb-ab*ab
  if det<1e-22:continue
  u=(np.dot(x,a0)*bb-np.dot(x,b0)*ab)/det;v=(np.dot(x,b0)*aa-np.dot(x,a0)*ab)/det
  if min(u,v,1-u-v)>1e-8:proof.append({'newFace':int(nf),'fixedSourceFace':int(sf),'pinnedVertexEdge':[int(v0),int(v1)],'edgeInteriorFraction':float(along),'triangleBarycentric':[float(1-u-v),float(u),float(v)],'hitWorldPosition':p.tolist(),'edgeLengthM':float(np.linalg.norm(delta))})
proof=list({(x['fixedSourceFace'],*sorted(x['pinnedVertexEdge'])):x for x in proof}.values());r={'status':'Necessary feasibility only; not a solved surface','sample':304,'fixedBoundarySegmentsStrictlyPiercingRetainedSourceTriangles':len(proof),'method':'Complete literal crossing pairs, test each newfabric pinned-pinned segment through each fixed retained triangle with strict segment parameter and strictly interior barycentric coordinates; independent of interior newfabric vertex positions.','conclusion':'Any witness persists for every interior-only material/volume transport with these sewn boundaries and retained source positions held. Local cut boundary/source margin must change to attain zero upper crossings.'if proof else'No pinned-segment witness found; source-source residual still prevents whole-upper zero.','witnesses':proof};(HERE/'actual304-pinned-feasibility.json').write_text(json.dumps(r,indent=2));print(json.dumps({k:v for k,v in r.items()if k!='witnesses'},indent=2));print(json.dumps(proof[:5],indent=2))
