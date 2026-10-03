from pathlib import Path
import numpy as np,json,hashlib
HERE=Path(__file__).resolve().parent;src=HERE/'source-sleeve-tube-rest06-envelope.npz';f=dict(np.load(src));parent=np.load(src);report=[]
# Original donor-centred gold rectangle; the map is a proper rectangular
# cylindrical chart, while physical seam IDs remain identical.
uvcentre=f['uv0'][f['tubeRowsL'][6]].mean(0)
for side in ['L','R']:
 rows=f['tubeRows'+side].copy();N=rows.shape[1];n=len(f['p0']);keys=[k for k,v in f.items()if k.endswith('0')and v.ndim>0 and len(v)==n and k not in ['tr0','restDoubleArea0','faceKind0','sourceFaceAncestry0']]
 root=rows[0].copy();newroot=np.arange(n,n+N)
 for k in keys:f[k]=np.concatenate([f[k],f[k][root]])
 rows[0]=newroot;n=len(f['p0']);keys=[k for k,v in f.items()if k.endswith('0')and v.ndim>0 and len(v)==n and k not in ['tr0','restDoubleArea0','faceKind0','sourceFaceAncestry0']];duplicate=np.arange(n,n+len(rows))
 for k in keys:f[k]=np.concatenate([f[k],f[k][rows[:,0]]])
 grid=np.c_[rows,duplicate];rest=f['p0'][rows];edge=np.linalg.norm(rest[0]-np.roll(rest[0],-1,axis=0),axis=1);u=np.r_[0,np.cumsum(edge)];u/=u[-1];centre=rest.mean(1);v=np.r_[0,np.cumsum(np.linalg.norm(np.diff(centre,axis=0),axis=1))];v/=v[-1]
 for r in range(len(rows)):f['uv0'][grid[r]]=uvcentre+[0,(v[r]-.5)*.018]+np.c_[(u-.5)*.018,np.zeros(len(u))]
 tt=[]
 for r in range(len(rows)-1):
  for j in range(N):tt.extend([[grid[r,j],grid[r,j+1],grid[r+1,j]],[grid[r,j+1],grid[r+1,j+1],grid[r+1,j]]])
 f['tr0'][f['newTubeFaceIDs'+side]]=tt;f['tubeRows'+side]=rows;f['tubeUVRows'+side]=grid;f['tubeUVRootSourceCapVertices'+side]=root;report.append({'side':side,'newRootUVOwnedRows':N,'longitudinalUVSeamRows':len(rows),'circumferenceAndArcLength':True})
# Right cap uses actual nonoverlap tilted chart, not its XY projection.
for side in ['L','R']:
 ids=np.unique(f['tr0'][f['bodyCapFaceIDs'+side]]);q=f['p0'][ids];chart=q[:,:2].copy()
 if side=='R':chart[:,1]+=.2*q[:,2]
 f['uv0'][ids]=uvcentre+(chart-[.627,1.410])*[.018/.22,.018/.35]
checks={}
for i in range(5):
 checks[str(i)]={k:bool(np.array_equal(f[f'{k}{i}'][f[f'tr{i}']],parent[f'{k}{i}'][parent[f'tr{i}']]))for k in ['p','W','n']}
 for k in ['p','W','n']:assert checks[str(i)][k],(i,k)
uv=[]
for side in ['L','R']:
 for label in ['bodyCapFaceIDs','newTubeFaceIDs']:
  q=f['uv0'][f['tr0'][f[label+side]]];a=(q[:,1,0]-q[:,0,0])*(q[:,2,1]-q[:,0,1])-(q[:,1,1]-q[:,0,1])*(q[:,2,0]-q[:,0,0]);uv.append({'region':label+side,'negative':int((a<-1e-14).sum()),'positive':int((a>1e-14).sum()),'zero':int((abs(a)<=1e-14).sum())})
out=HERE/'source-sleeve-tube-rest07-uvchart.npz';np.savez_compressed(out,**f);r={'status':'UV_CHART_ONLY_CLONE; source-shaped standing/render/runtime still pending','candidateSHA256':hashlib.sha256(out.read_bytes()).hexdigest(),'parentSHA256':hashlib.sha256(src.read_bytes()).hexdigest(),'method':'Tube circumferential arc-length x centreline arc-length rectangular UV island with13-row longitudinal seam duplicate. Tube root rows duplicated to keep cap UV island separate. Right cap uses its verified tilted2D chart. PhysicalWeld/P/n/W/sourceclipUV/images unchanged.','allTrianglePWNExact':checks,'newRows':report,'signedUVAreas':uv};(HERE/'source-sleeve-tube-rest07-uvchart-provenance.json').write_text(json.dumps(r,indent=2));print(json.dumps(r,indent=2))
