"""Actual local source topology surgery: close low body opening, sew higher rim.
Uses only source-cut boundary and existing sleeve; no external garment, panel
router, whole-shirt generation or coordinate lift. New fabric supplies extra
underarm material span. Original source atlas/images retained; only new UVs.
"""
from pathlib import Path
import sys,json,hashlib,subprocess,io
HERE=Path(__file__).resolve().parent;sys.path.insert(0,str(HERE.parent));from chart_labels import *
from scipy.interpolate import RBFInterpolator
from scipy.sparse.csgraph import dijkstra
from PIL import Image
c=SourceCharts();d=np.load(HERE/'source-armhole-cut.npz');ct=c.ct;loops={s:d[f'cutLoop{s}0'].copy()for s in ['L','R']};sleeve={s:d[f'sleeveFaces{s}']for s in ['L','R']};allSleeve=sleeve['L']|sleeve['R'];bodyFaces=ct[~allSleeve]

def metric_distance(faces,seeds):
 ee=np.unique(np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[0,2]]]),axis=1),axis=0);ll=np.linalg.norm(c.unique[ee[:,0]]-c.unique[ee[:,1]],axis=1);g=coo_matrix((np.r_[ll,ll],(np.r_[ee[:,0],ee[:,1]],np.r_[ee[:,1],ee[:,0]])),shape=(len(U),len(U))).tocsr();return dijkstra(g,directed=False,indices=seeds,min_only=True)
def inside(points,poly):
 out=np.zeros(len(points),bool)
 for a,b in zip(poly,np.roll(poly,-1,axis=0)):
  cond=(a[1]>points[:,1])!=(b[1]>points[:,1]);crossx=a[0]+(points[:,1]-a[1])*(b[0]-a[0])/(b[1]-a[1]+1e-30);out^=cond&(points[:,0]<crossx)
 return out

def earcut(outer,hole):
 script="import{ShapeUtils}from'/Users/raynos/projects/games/rockhop/node_modules/three/src/extras/ShapeUtils.js';import{Vector2}from'/Users/raynos/projects/games/rockhop/node_modules/three/src/math/Vector2.js';let s='';for await(const c of process.stdin)s+=c;const d=JSON.parse(s);console.log(JSON.stringify(ShapeUtils.triangulateShape(d.outer.map(x=>new Vector2(...x)),[d.hole.map(x=>new Vector2(...x))])));"
 r=subprocess.run(['node','--input-type=module','-e',script],input=json.dumps({'outer':outer.tolist(),'hole':hole.tolist()}),text=True,capture_output=True,check=True);return np.array(json.loads(r.stdout),int)

# Pick a verified gold hoodie-cloth donor rectangle from the unchanged source
# body atlas, near real hoodie UVs. No painted pixels or replacement image.
uvSource=[G.array(p['attributes']['TEXCOORD_0']).astype(float)for p in PR];imIndex=G.j['textures'][G.j['materials'][PR[0]['material']]['pbrMetallicRoughness']['baseColorTexture']['index']]['source'];bv=G.j['bufferViews'][G.j['images'][imIndex]['bufferView']];atlas=np.asarray(Image.open(io.BytesIO(bytes(G.bin[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']]))).convert('RGBA'));height,width=atlas.shape[:2];rgb=atlas[:,:,:3].astype(int);safe=(rgb[:,:,0]>110)&(rgb[:,:,1]>70)&(rgb[:,:,2]<rgb[:,:,1]*.75)&(rgb[:,:,0]>rgb[:,:,1]*1.05)&(rgb[:,:,0]<rgb[:,:,1]*2.2)&(atlas[:,:,3]==255)
centres=c.pos[0][c.tri[0]].mean(1);uvCent=uvSource[0][c.tri[0]].mean(1);faceDomain=(centres[:,1]>1.10)&(centres[:,1]<1.45)&(abs(centres[:,2])<.22);candidates=np.flatnonzero(faceDomain);donors=[]
for f in candidates:
 x,y=np.rint(uvCent[f]*np.array([width-1,height-1])).astype(int);rad=18
 if x>=rad and y>=rad and x<width-rad and y<height-rad:
  score=float(safe[y-rad:y+rad,x-rad:x+rad].mean())
  if score>.985:donors.append((score,f,x,y))
assert donors,'No coherent source hoodie atlas donor; do not invent UVs'
donor=max(donors);_,donorFace,donorX,donorY=donor;uvBase=np.array([donorX/width,donorY/height]);uvScale=np.array([.018/.22,.018/.32]);uvCentre=np.array([.63,1.335])
def patch_uv(x):return uvBase+(x[:,:2]-uvCentre)*uvScale

# Anatomy weights change only in an explicitly declared80mm source-geodesic
# construction margin around the cut. Outside positions/UVs/weights stay exact.
bodyDist=metric_distance(bodyFaces,np.r_[loops['L'],loops['R']]);bodyBeta=smooth((.08-bodyDist)/.08);bodyBeta[np.isin(np.arange(len(U)),c.cuff)|(U[:,1]>1.48)]=0
bodyWeight=c.uw.copy();nonarm=bodyWeight.copy();nonarm[:,[6,7,8,10,11,12]]=0;total=nonarm.sum(1);nonarm=np.divide(nonarm,total[:,None],out=np.zeros_like(nonarm),where=total[:,None]>1e-10);nonarm[total<1e-10,2]=1;bodyWeight=bodyWeight*(1-bodyBeta[:,None])+nonarm*bodyBeta[:,None]
armWeight={};armBeta={};armPosition={}
for sg,s,a in [(1,'L',6),(-1,'R',10)]:
 dist=metric_distance(ct[sleeve[s]],loops[s]);beta=smooth((.08-dist)/.08);beta[np.isin(np.arange(len(U)),c.cuff)]=0;target=np.zeros_like(c.uw);arm=c.uw[:,a:a+3].sum(1);target[:,a:a+3]=np.divide(c.uw[:,a:a+3],arm[:,None],out=np.zeros((len(U),3)),where=arm[:,None]>1e-10);target[arm<1e-10,a]=1;armWeight[s]=c.uw*(1-beta[:,None])+target*beta[:,None];armBeta[s]=beta;armPosition[s]=c.unique.copy();armPosition[s][:,2]+=sg*.002*beta

pos=[p.copy().tolist()for p in c.pos];weights=[w.copy().tolist()for w in c.w];uv=[p.copy().tolist()for p in uvSource];tri=[t.copy()for t in c.tri];remap=[list(range(len(p)))for p in c.pos];patchKind=[['original']*len(p)for p in c.pos];vertexWeld=[INV[OFF[i]:OFF[i+1]].tolist()for i in range(5)];sourceUID=[x.copy()for x in vertexWeld];partIds=[[0 if i in[0,2]else 3]*len(pos[i])for i in range(5)];nextWeld=len(U);detachedWeld={}
def weld_for_detached(side,u):
 global nextWeld
 key=(side,int(u))
 if key not in detachedWeld:detachedWeld[key]=nextWeld;nextWeld+=1
 return detachedWeld[key]
sourceFaceOff=np.r_[0,np.cumsum([len(c.tri[0]),len(c.tri[2])])]
# Remap old cut-ring sleeve vertices into separate authored arm copies.
for i,partOff in [(0,0),(2,len(c.tri[0]))]:
 alias=INV[OFF[i]:OFF[i+1]];faceArm={s:sleeve[s][partOff:partOff+len(tri[i])]for s in ['L','R']};duplicates={}
 for s in ['L','R']:
  ring=set(loops[s].tolist());armVerts=np.unique(tri[i][faceArm[s]]);bodyVerts=set(np.unique(tri[i][~(faceArm['L']|faceArm['R'])]).tolist())
  for old in armVerts:
   u=int(alias[old]);point=armPosition[s][u];ww=armWeight[s][u]
   if u in ring or old in bodyVerts:
    new=len(pos[i]);pos[i].append(point.tolist());weights[i].append(ww.tolist());uv[i].append(uvSource[i][old].tolist());remap[i].append(int(old));patchKind[i].append(f'detached-{s}');vertexWeld[i].append(weld_for_detached(s,u));sourceUID[i].append(u);partIds[i].append(1 if s=='L'else 2);duplicates[(s,int(old))]=new
   else:
    
    if armBeta[s][u]>1e-12:pos[i][old]=point.tolist();weights[i][old]=ww.tolist()
  for f in np.flatnonzero(faceArm[s]):tri[i][f]=[duplicates.get((s,int(v)),int(v))for v in tri[i][f]]
 # Shared source body UV aliases receive the same authored body-margin weights.
 for old in np.unique(c.tri[i][~(faceArm['L']|faceArm['R'])]):
  if bodyBeta[alias[old]]>1e-12:weights[i][old]=bodyWeight[alias[old]].tolist()

def append(point,weight,kind,sourceOld=-1,tex=None,sourceU=-1,weld=None,part=0):
 global nextWeld
 k=len(pos[0]);pos[0].append(np.asarray(point).tolist());weights[0].append(np.asarray(weight).tolist());uv[0].append((patch_uv(np.asarray(point)[None])[0]if tex is None else np.asarray(tex)).tolist());remap[0].append(int(sourceOld));patchKind[0].append(kind);sourceUID[0].append(int(sourceU));partIds[0].append(part)
 if weld is None:weld=nextWeld;nextWeld+=1
 vertexWeld[0].append(int(weld));return k

from scipy.spatial import cKDTree

def refine_chart(points,faces,boundaryEdges,maxLength=.007):
 points=points.tolist();faces=np.array(faces,int);boundary={tuple(sorted(e))for e in boundaryEdges}
 for iteration in range(12):
  xy=np.array(points);ee=np.unique(np.sort(np.concatenate([faces[:,[0,1]],faces[:,[1,2]],faces[:,[0,2]]]),axis=1),axis=0);ll=np.linalg.norm(xy[ee[:,0]]-xy[ee[:,1]],axis=1);marked=[tuple(e)for e,l in zip(ee,ll)if l>maxLength and tuple(e)not in boundary]
  if not marked:break
  mids={}
  for a,b in marked:mids[(a,b)]=len(points);points.append(((xy[a]+xy[b])*.5).tolist())
  out=[]
  for v in faces:
   ms=[mids.get(tuple(sorted((int(v[j]),int(v[(j+1)%3])))))for j in range(3)];count=sum(m is not None for m in ms)
   if count==0:out.append(v.tolist())
   elif count==1:
    k=next(j for j in range(3)if ms[j]is not None);a,b,z=v[k],v[(k+1)%3],v[(k+2)%3];m=ms[k];out.extend([[a,m,z],[m,b,z]])
   elif count==2:
    missing=next(j for j in range(3)if ms[j]is None);j=(missing+2)%3;a,b,z=v[(j-1)%3],v[j],v[(j+1)%3];ma,mb=ms[(j-1)%3],ms[j];out.extend([[b,mb,ma],[a,ma,z],[ma,mb,z]])
   else:
    a,b,z=v;ma,mb,mz=ms;out.extend([[a,ma,mz],[ma,b,mb],[mz,mb,z],[ma,mb,mz]])
  faces=np.array(out,int)
 return np.array(points),faces

def arm_corridor(xy,bodyZ,armTriangles,sg):
 T=armTriangles;C=T[:,:,:2].mean(1);radius=np.linalg.norm(T[:,:,:2]-C[:,None],axis=2).max(1);tree=cKDTree(C);near=tree.query_ball_point(xy,float(radius.max())+1e-6);pi=np.repeat(np.arange(len(xy)),[len(x)for x in near]);ti=np.concatenate(near).astype(int);A=T[ti,0,:2];B=T[ti,1,:2]-A;D=T[ti,2,:2]-A;X=xy[pi]-A;det=B[:,0]*D[:,1]-B[:,1]*D[:,0];valid=abs(det)>1e-14;inv=np.divide(1,det,out=np.zeros_like(det),where=valid);u=(X[:,0]*D[:,1]-X[:,1]*D[:,0])*inv;v=(B[:,0]*X[:,1]-B[:,1]*X[:,0])*inv;valid&=(u>=-1e-9)&(v>=-1e-9)&(u+v<=1+1e-9);Z=T[ti,0,2]+u*(T[ti,1,2]-T[ti,0,2])+v*(T[ti,2,2]-T[ti,0,2]);gap=sg*(Z-bodyZ[pi]);valid&=gap>1e-6;result=np.full(len(xy),np.inf);np.minimum.at(result,pi[valid],gap[valid]);missing=~np.isfinite(result);result[missing]=.003;return result,int(missing.sum())

newFaces=[];faceKind=[];rows=[];construction={}
for sg,s,a in [(1,'L',6),(-1,'R',10)]:
 loop=loops[s];outer=c.unique[loop].copy();area=(outer[:,0]*np.roll(outer[:,1],-1)-outer[:,1]*np.roll(outer[:,0],-1)).sum()
 if area*sg<0:loop=loop[::-1];outer=c.unique[loop].copy()
 n=len(loop);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(np.r_[outer[:,:2],outer[None,0,:2]],axis=0),axis=1))][:-1];perimeter=np.linalg.norm(outer[:,:2]-np.roll(outer[:,:2],-1,axis=0),axis=1).sum();phase=np.arctan2((outer[0,1]-1.385)/.072,(outer[0,0]-.627)/.070);angle=phase+sg*arc/perimeter*2*np.pi;holeXY=np.c_[.627+.070*np.cos(angle),1.385+.072*np.sin(angle)];assert inside(holeXY,outer[:,:2]).all()
 fit=RBFInterpolator(outer[:,:2],outer[:,2],kernel='thin_plate_spline',smoothing=1e-10);xy=np.r_[outer[:,:2],holeXY];tess=earcut(outer[:,:2],holeXY[::-1]);lookup=np.r_[np.arange(n),np.arange(n,2*n)[::-1]];tess=lookup[tess];signed=(xy[tess[:,1],0]-xy[tess[:,0],0])*(xy[tess[:,2],1]-xy[tess[:,0],1])-(xy[tess[:,1],1]-xy[tess[:,0],1])*(xy[tess[:,2],0]-xy[tess[:,0],0]);tess[signed*sg<0]=tess[signed*sg<0][:,[0,2,1]]
 boundary=np.r_[np.c_[np.arange(n),np.roll(np.arange(n),-1)],np.c_[np.arange(n,2*n),np.roll(np.arange(n,2*n),-1)]];xy,tess=refine_chart(xy,tess,boundary);count=len(xy);bodyZ=fit(xy);bodyZ[:n]=outer[:,2];bodyPoints=np.c_[xy,bodyZ];chest=np.zeros(N);chest[2]=1
 ee=np.unique(np.sort(np.concatenate([tess[:,[0,1]],tess[:,[1,2]],tess[:,[0,2]]]),axis=1),axis=0);ll=np.linalg.norm(xy[ee[:,0]]-xy[ee[:,1]],axis=1);ew=1/np.maximum(ll,.001)**2;graph=coo_matrix((np.r_[ew,ew],(np.r_[ee[:,0],ee[:,1]],np.r_[ee[:,1],ee[:,0]])),shape=(count,count)).tocsr();L=diags(np.asarray(graph.sum(1)).ravel())-graph;fixed=np.arange(2*n);free=np.arange(2*n,count);solve=factorized(L[free][:,free].tocsc());scalar=np.zeros(count);scalar[:n]=1;scalar[free]=solve(-L[free][:,fixed]@scalar[fixed]);scalar=np.clip(scalar,0,1)
 # Added torso closure has source body boundary weights and chest hole weights;
 # solve the same nonoverlapping chart rather than use a radial correspondence.
 bodyW=np.zeros((count,N));bodyW[:n]=bodyWeight[loop];bodyW[n:2*n]=chest
 for bone in range(N):bodyW[free,bone]=solve(-L[free][:,fixed]@bodyW[fixed,bone])
 armW=np.zeros((count,N));armW[:n]=armWeight[s][loop];armW[n:2*n]=chest
 for bone in range(N):armW[free,bone]=solve(-L[free][:,fixed]@armW[fixed,bone])
 # Existing exact-boundary bones can union above4; record rather than silently
 # truncate. The rig worker owns fresh weight qualification for this candidate.
 bodyW=np.maximum(bodyW,0);bodyW/=bodyW.sum(1)[:,None];armW=np.maximum(armW,0);armW/=armW.sum(1)[:,None]
 bodyIds=[]
 for k in range(count):bodyIds.append(append(bodyPoints[k],bodyW[k],f'body-closure-{s}',sourceU=int(loop[k])if k<n else-1,weld=int(loop[k])if k<n else None,part=0))
 bodyTri=np.array(bodyIds)[tess];bodyFaceStart=len(c.tri[0])+len(newFaces);newFaces.extend(bodyTri.tolist());faceKind.extend([f'body-closure-{s}']*len(bodyTri))
 armT=armPosition[s][ct[sleeve[s]]];gap,missing=arm_corridor(xy,bodyZ,armT,sg);gap[:n]=sg*(armPosition[s][loop,2]-bodyZ[:n]);assert(gap[:n]>0).all();armPoints=np.c_[xy,bodyZ+sg*gap*scalar];armPoints[:n]=armPosition[s][loop];armPoints[n:2*n]=bodyPoints[n:2*n]
 armIds=[]
 for k in range(count):
  if n<=k<2*n:armIds.append(bodyIds[k])
  else:armIds.append(append(armPoints[k],armW[k],f'sewn-insert-{s}',sourceU=int(loop[k])if k<n else-1,weld=weld_for_detached(s,int(loop[k]))if k<n else None,part=1 if sg==1 else 2))
 insertTri=np.array(armIds)[tess][:,[0,2,1]];insertFaceStart=len(c.tri[0])+len(newFaces);newFaces.extend(insertTri.tolist());faceKind.extend([f'sewn-insert-{s}']*len(insertTri))
 construction.update({f'oldCutSourceAlias{s}':loop,f'bodyBoundaryVertices{s}':np.array(bodyIds[:n]),f'bodyOpeningVertices{s}':np.array(bodyIds[n:2*n]),f'sleeveBoundaryVertices{s}':np.array(armIds[:n]),f'insertChartVertices{s}':np.array(armIds),f'insertChartTriangles{s}':tess[:,[0,2,1]],f'insertHarmonicCoordinate{s}':scalar,f'bodyClosureFaceIDs{s}':np.arange(bodyFaceStart,bodyFaceStart+len(bodyTri)),f'sleeveInsertFaceIDs{s}':np.arange(insertFaceStart,insertFaceStart+len(insertTri)),f'chartXY{s}':xy})
 rows.append({'side':s,'sourceLoopVertices':n,'oldBottomY':float(outer[:,1].min()),'newOpeningBottomY':float(holeXY[:,1].min()),'newOpeningTopY':float(holeXY[:,1].max()),'newBodyClosureFaces':len(bodyTri),'newInsertFaces':len(insertTri),'newOpeningInsideSourceCut':True,'sourceSleeveMarginMaxShiftM':.002,'surgeryGeodesicMarginM':.08,'insertRestCorridorMinM':float(gap.min()),'insertRestCorridorMaxM':float(gap.max()),'armRayMissingChartNodes':missing,'construction':'Same nonoverlapping constrained source-boundary chart for torso closure and new insert; harmonic chest-to-arm attachment and source-surface clearance corridor, no twisted radial rows.'})

tri[0]=np.concatenate([tri[0],np.asarray(newFaces,int)]);pos=[np.array(p,float)for p in pos];weights=[np.array(w,float)for w in weights];uv=[np.array(q,float)for q in uv]
# Restore exact outside arrays for glove/head primitives, then recompute clothing
# normals consistently over sewn exact-position aliases for this candidate.
sourceShape=np.load(ROOT/'hoodie-repair02/v7-shape-input.npz');normal=[sourceShape[f'n{i}'].copy()for i in range(5)];allpos=np.concatenate(pos);unique,alias=np.unique(allpos,axis=0,return_inverse=True);offset=np.r_[0,np.cumsum([len(p)for p in pos])];n=np.zeros_like(unique)
for i in [0,2]:
 q=pos[i][tri[i]];face=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);ids=alias[offset[i]:offset[i+1]][tri[i]]
 for j in range(3):np.add.at(n,ids[:,j],face)
n=unit(n)
for i in [0,2]:
 normal[i]=n[alias[offset[i]:offset[i+1]]]
 oldlen=len(c.pos[i]);oldU=INV[OFF[i]:OFF[i+1]];margin=(bodyBeta>1e-12)|(armBeta['L']>1e-12)|(armBeta['R']>1e-12);margin[c.cuff]=False;margin[U[:,1]>1.48]=False;protected=~margin[oldU];normal[i][:oldlen][protected]=sourceShape[f'n{i}'][protected]
out={}
for i in range(5):out.update({f'p{i}':pos[i],f'W{i}':weights[i],f'uv{i}':uv[i],f'tr{i}':tri[i],f'n{i}':normal[i],f'oldVertex{i}':np.array(remap[i],int)})
for i in range(5):
 out[f'physicalWeld{i}']=np.array(vertexWeld[i],int);out[f'sourceUniqueVertex{i}']=np.array(sourceUID[i],int);out[f'semanticPart{i}']=np.array(partIds[i],int);out[f'physicalGarment{i}']=np.full(len(pos[i]),0 if i in[0,2]else 1 if i==1 else 2,int);out[f'sourceFaceAncestry{i}']=np.r_[np.arange(len(c.tri[i])),np.full(len(tri[i])-len(c.tri[i]),-1,int)];f=pos[i][tri[i]];out[f'restDoubleArea{i}']=np.linalg.norm(np.cross(f[:,1]-f[:,0],f[:,2]-f[:,0]),axis=1)
out.update(construction)
for i in range(5):
 oldU=INV[OFF[i]:OFF[i+1]];out[f'sourceConstructionMargin{i}']=margin[oldU] if i in [0,2] else np.zeros(len(c.pos[i]),bool)
 out[f'sourceDoubleArea{i}']=np.r_[np.linalg.norm(np.cross(c.pos[i][c.tri[i]][:,1]-c.pos[i][c.tri[i]][:,0],c.pos[i][c.tri[i]][:,2]-c.pos[i][c.tri[i]][:,0]),axis=1),np.full(len(tri[i])-len(c.tri[i]),np.nan)]
out.update(sourceAliasNew=alias,primitiveOffsetsNew=offset,newFacesPrimitive0=np.arange(len(c.tri[0]),len(tri[0])),newFaceKind=np.array(faceKind),newVertexKind0=np.array(patchKind[0]));np.savez(HERE/'armhole-reconstructed.npz',**out)
(HERE/'armhole-reconstructed-provenance.json').write_text(json.dumps({'status':'UNACCEPTED source topology reconstruction; rest/pose/render gates pending','sourceV7SHA256':hashlib.sha256(c.input.read_bytes()).hexdigest(),'candidateSHA256':hashlib.sha256((HERE/'armhole-reconstructed.npz').read_bytes()).hexdigest(),'method':'Cut actual cuff-connected sleeve off torso on original sewn mesh; fill lower old torso opening while leaving higher anatomical opening; sew detached source sleeve to new opening with additional locally sampled fabric. Source outer material retained; no external body panel or garment generation.','rows':rows,'vertexCountsBefore':[len(p)for p in c.pos],'vertexCountsAfter':[len(p)for p in pos],'sourceImagesUnchanged':True,'UVDonor':{'primitive':0,'sourceFace':int(donorFace),'sourcePixelCentre':[int(donorX),int(donorY)],'hoodieClothSafeFraction':float(donor[0]),'uvHalfExtent':.009,'sourceAtlasSHA256':hashlib.sha256(bytes(G.bin[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']])).hexdigest()},'weightsChanged':'Source body/sleeve weights normalized only within declared80mm source-geodesic construction margin; new body opening chest-rigid, added insert harmonic chart attachment from chest to source-arm boundary. All new/source rows keep19-bone contract, head/glove original.','compatibilityCost':'New vertex/face counts and local UV islands require regenerated GLB buffers, morph arrays and exact alias metadata; old frozenV7 morph offsets cannot be copied blindly. No runtime export yet.'},indent=2))
print(json.dumps(rows,indent=2));print('candidate vertexcounts',[len(p)for p in pos],flush=True)
