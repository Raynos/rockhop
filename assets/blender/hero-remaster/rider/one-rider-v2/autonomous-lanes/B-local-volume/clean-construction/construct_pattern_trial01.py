"""NEW whole four-panel hood and binding. No retired strip/collar input.
Fresh body source full-hood exclusion, new pattern UVs and authored complete panels.
"""
from pathlib import Path
import numpy as np,json,time,resource,hashlib,traceback
from scipy.interpolate import CubicSpline
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/B-local-volume/clean-construction/trial01');cfg=json.loads((R/'settings.json').read_text());t=time.monotonic();rep={'status':'UNACCEPTED new wholehood trial01','oldLineageFailuresRetired':15,'newLineagePriorFailures':0,'threads':2,'method':'Fresh complete outer/lining left/right textile panels plus explicit rolled neck binding; new wholehood exclusion only','inputs':{},'temporarySizingSkinNotFinalIdentity':True}
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def loops(f):
 ed=np.concatenate((f[:,[0,1]],f[:,[1,2]],f[:,[2,0]]));u,c=np.unique(np.sort(ed,axis=1),axis=0,return_counts=True);g={}
 for a,b in u[c==1]:g.setdefault(int(a),[]).append(int(b));g.setdefault(int(b),[]).append(int(a))
 if any(len(x)!=2 for x in g.values()):raise ValueError('Fresh body boundary branch: '+str({k:len(x) for k,x in g.items() if len(x)!=2}))
 ls=[];seen=set()
 for a in g:
  if a in seen:continue
  seq=[];last=-1;cur=a
  while cur not in seen:
   seq.append(cur);seen.add(cur);ns=g[cur];nx=ns[0] if ns[0]!=last else ns[1];last,cur=cur,nx
  if cur!=a:raise ValueError('Nonclosed fresh extraction seam')
  q=np.array(seq)
  if not np.any(np.all(ed==q[:2],axis=1)):q=q[::-1]
  ls.append(q)
 return ls,{'boundaryEdges':sum(len(x) for x in ls),'nonmanifoldEdges':int(np.sum(c>2))}
try:
 d=np.load(R/'body-source.npz');v=d['vertices'];f=d['faces'];uv=d['allTriangleUV'];mi=d['materialIndex'];m=cfg['wholeHoodMask'];front=m['frontFloorZ'];rear=m['rearFloorZ'];a,b=m['rearTransitionY'];floor=front+(rear-front)*np.clip((v[:,1]-a)/(b-a),0,1);scalar=np.maximum(np.abs(v[:,0])-m['centralHalfWidth'],floor-v[:,2]);verts=list(v.astype(float));nf=[];nu=[];nm=[];origin=[];edgecache={};interp={};removed=0
 for fi,face in enumerate(f):
  if np.all(scalar[face]>=0):nf.append(face.tolist());nu.append(uv[:,fi]);nm.append(int(mi[fi]));origin.append(fi);continue
  if np.all(scalar[face]<0):removed+=1;continue
  nodes=[(int(x),uv[:,fi,k]) for k,x in enumerate(face)];out=[]
  for (aa,ua),(bb,ub) in zip(nodes,nodes[1:]+nodes[:1]):
   if scalar[aa]>=0:out.append((aa,ua))
   if (scalar[aa]>=0)!=(scalar[bb]>=0):
    frac=float(scalar[aa]/(scalar[aa]-scalar[bb]));key=tuple(sorted((aa,bb)))
    if key not in edgecache:edgecache[key]=len(verts);verts.append(v[aa]+frac*(v[bb]-v[aa]));interp[str(edgecache[key])]=[aa,bb,frac]
    out.append((edgecache[key],ua+frac*(ub-ua)))
  for k in range(1,len(out)-1):tri=[out[0],out[k],out[k+1]];nf.append([x[0] for x in tri]);nu.append(np.stack([x[1] for x in tri],axis=1));nm.append(int(mi[fi]));origin.append(-1)
 vv=np.array(verts);ff=np.array(nf,np.int32);uu=np.stack(nu,axis=1);mm=np.array(nm);orig=np.array(origin);ls,top=loops(ff);rep.update(wholeHoodMask=m,removedWholeHoodAndSourceHeadTriangles=removed,newAttachmentLoopLengths=[len(x) for x in ls],extractionTopology=top,preservedOriginalTriangles=int(np.sum(orig>=0)))
 np.savez(R/'fresh-wholehood-exclusion.npz',vertices=vv,faces=ff,allTriangleUV=uu,materialIndex=mm,faceOrigin=orig,originalVertexCount=len(v))
 if len(ls)!=1:raise ValueError('Fresh fullhood extraction must expose one body-yoke attachment, got '+str([len(x) for x in ls]))
 rim=ls[0];hem=vv[rim];N=len(rim);p=cfg['pattern'];rows=p['rows'];center=np.array(p['neckOpeningCenterXY']);theta=np.arctan2(hem[:,0]-center[0],-(hem[:,1]-center[1]));co=np.cos(theta);si=np.sin(theta);direction=np.sign(np.sum(hem[:,0]*np.roll(hem[:,1],-1)-hem[:,1]*np.roll(hem[:,0],-1)))
 # New authored complete hood drape, independent of old sourcehood/collar topology.
 opening=np.column_stack((si*p['neckOpeningRadii'][0],center[1]-co*p['neckOpeningRadii'][1],np.where(co>=0,p['sideOpeningZ']+(p['frontOpeningZ']-p['sideOpeningZ'])*co,p['sideOpeningZ']+(p['rearOpeningZ']-p['sideOpeningZ'])*(-co))))
 belly=np.column_stack((si*p['sideCowlRadius'],center[1]-co*np.where(co>=0,.130,.161),np.where(co>=0,1.545-.050*co,1.545-.140*(-co))))
 ridge=np.column_stack((si*.148,center[1]-co*np.where(co>=0,.135,.133),1.603-.091*np.maximum(co,0)))
 spline=CubicSpline([0,.40,.76,1],np.stack((hem,belly,ridge,opening)),axis=0,bc_type='natural');outer=[rim.tolist()];allv=verts;faces=nf.copy();alluv=nu.copy();material=nm.copy();origins=origin.copy();pattern=[np.zeros((3,2),np.float32) for x in nf];patchfaces=[]
 def makechart(j0,j1,t0,t1,lining=False):
  # Distinct left/right pattern islands; corner coordinates never sample body atlas.
  ang=np.mod(theta,2*np.pi)/(2*np.pi);half=0 if ang[j0]<.5 else 1;u0=(ang[j0]*2-half)*.44+.03+half*.50;u1=(ang[j1]*2-half)*.44+.03+half*.50
  if abs(u1-u0)>.25:u1=u0+.004
  base=.52 if lining else .03;return np.array([[u0,base+t0*.43],[u1,base+t0*.43],[u1,base+t1*.43],[u0,base+t1*.43]],np.float32)
 def addface(ids,chart,matid):
  # Explicit triangulation so original corner UVs remain reproducible.
  for tri in [(0,1,2),(0,2,3)]:faces.append([ids[x] for x in tri]);alluv.append(np.zeros((uv.shape[0],3,2),np.float32));pattern.append(chart[list(tri)]);material.append(matid);origins.append(-2);patchfaces.append(len(faces)-1)
 for r in range(1,rows+1):
  z=r/rows;q=spline(z);q[:,2]+=.0025*np.sin(theta*4+z*3)*np.sin(np.pi*z);idx=[]
  for point in q:idx.append(len(allv));allv.append(point)
  outer.append(idx)
 for r in range(rows):
  for j in range(N):jn=(j+1)%N;ids=[outer[r][jn],outer[r][j],outer[r+1][j],outer[r+1][jn]];ch=makechart(jn,j,r/rows,(r+1)/rows);addface(ids,ch,2 if np.sin(theta[j])>=0 else 3)
 # Lining is sewn to the rolled opening; its separate hem sits below/inside body.
 inner=[]
 for r in range(rows+1):
  z=r/rows;q=spline(z);rad=q[:,:2]-center;rad/=np.maximum(np.linalg.norm(rad,axis=1)[:,None],1e-8);q[:,:2]-=rad*p['liningOffset'];q[:,2]-=p['hiddenLiningHemDrop']*(1-z)+p['neckBindingDrop']*z
  if r==rows:q[:,:2]-=rad*p['neckBindingWidth']
  ids=[]
  for point in q:ids.append(len(allv));allv.append(point)
  inner.append(ids)
 for r in range(rows):
  for j in range(N):jn=(j+1)%N;ids=[inner[r][j],inner[r][jn],inner[r+1][jn],inner[r+1][j]];ch=makechart(j,jn,r/rows,(r+1)/rows,True);addface(ids,ch,4 if np.sin(theta[j])>=0 else 5)
 for j in range(N):jn=(j+1)%N;ids=[outer[-1][jn],outer[-1][j],inner[-1][j],inner[-1][jn]];ch=makechart(jn,j,1,1,True);addface(ids,ch,6)
 av=np.array(allv);af=np.array(faces,np.int32);au=np.stack(alluv,axis=1);am=np.array(material);ao=np.array(origins);pu=np.array(pattern);fl,ft=loops(af);rep.update(newTopology=ft,newBoundaryLoopLengths=[len(x) for x in fl],hiddenLiningHemVertices=N,liningHemExplicitlyOpen=True,oldSourceHoodGeometryNotGenerationInput=True,outerPanelVertices=N*rows,liningPanelVertices=N*(rows+1),patternPanelCount=4,neckBindingTriangles=N*2,wholeSkinNotModified=True,newUVChart='CleanHoodPatternUV: left/right outer and left/right lining islands, new explicit corner atlas, no donor-nearest-corner UV')
 valid=ao>=0;assert np.array_equal(af[valid],f[ao[valid]]);assert np.array_equal(au[:,valid],uv[:,ao[valid]]);assert np.array_equal(am[valid],mi[ao[valid]])
 np.savez(R/'new-wholehood.npz',vertices=av,faces=af,allTriangleUV=au,materialIndex=am,faceOrigin=ao,patternUV=pu,originalVertexCount=len(v));(R/'interpolated-source-weights.json').write_text(json.dumps(interp));rep['status']='UNACCEPTED wholehood neutral construction; requires actual parent review, lining hem coverage unmeasured';rep['inputs']={str(R/'body-source.npz'):sha(R/'body-source.npz'),str(R/'settings.json'):sha(R/'settings.json')}
except Exception as e:rep['status']='FAILED new wholehood construction gate';rep['error']=str(e);rep['traceback']=traceback.format_exc()
finally:
 rep['elapsedSeconds']=time.monotonic()-t;rep['peakRSSBytes']=resource.getrusage(resource.RUSAGE_SELF).ru_maxrss;rep['recipeSHA']=sha(__file__);(R/'construction-report.json').write_text(json.dumps(rep,indent=2)+'\n');print(json.dumps(rep),flush=True)
