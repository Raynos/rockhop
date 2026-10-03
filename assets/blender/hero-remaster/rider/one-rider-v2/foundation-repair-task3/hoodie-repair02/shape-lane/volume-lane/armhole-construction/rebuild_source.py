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
 dist=metric_distance(ct[sleeve[s]],loops[s]);beta=smooth((.08-dist)/.08);beta[np.isin(np.arange(len(U)),c.cuff)]=0;target=np.zeros_like(c.uw);arm=c.uw[:,a:a+3].sum(1);target[:,a:a+3]=np.divide(c.uw[:,a:a+3],arm[:,None],out=np.zeros((len(U),3)),where=arm[:,None]>1e-10);target[arm<1e-10,a]=1;armWeight[s]=c.uw*(1-beta[:,None])+target*beta[:,None];armBeta[s]=beta;armPosition[s]=c.unique.copy();armPosition[s][:,2]+=sg*.012*beta

pos=[p.copy().tolist()for p in c.pos];weights=[w.copy().tolist()for w in c.w];uv=[p.copy().tolist()for p in uvSource];tri=[t.copy()for t in c.tri];remap=[list(range(len(p)))for p in c.pos];patchKind=[['original']*len(p)for p in c.pos];sourceFaceOff=np.r_[0,np.cumsum([len(c.tri[0]),len(c.tri[2])])]
# Remap old cut-ring sleeve vertices into separate authored arm copies.
for i,partOff in [(0,0),(2,len(c.tri[0]))]:
 alias=INV[OFF[i]:OFF[i+1]];faceArm={s:sleeve[s][partOff:partOff+len(tri[i])]for s in ['L','R']};duplicates={}
 for s in ['L','R']:
  ring=set(loops[s].tolist());armVerts=np.unique(tri[i][faceArm[s]]);bodyVerts=set(np.unique(tri[i][~(faceArm['L']|faceArm['R'])]).tolist())
  for old in armVerts:
   u=int(alias[old]);point=armPosition[s][u];ww=armWeight[s][u]
   if u in ring or old in bodyVerts:
    new=len(pos[i]);pos[i].append(point.tolist());weights[i].append(ww.tolist());uv[i].append(uvSource[i][old].tolist());remap[i].append(int(old));patchKind[i].append(f'detached-{s}');duplicates[(s,int(old))]=new
   else:
    pos[i][old]=point.tolist();weights[i][old]=ww.tolist()
  for f in np.flatnonzero(faceArm[s]):tri[i][f]=[duplicates.get((s,int(v)),int(v))for v in tri[i][f]]
 # Shared source body UV aliases receive the same authored body-margin weights.
 for old in np.unique(c.tri[i][~(faceArm['L']|faceArm['R'])]):weights[i][old]=bodyWeight[alias[old]].tolist()

def append(point,weight,kind,sourceOld=-1,tex=None):
 k=len(pos[0]);pos[0].append(np.asarray(point).tolist());weights[0].append(np.asarray(weight).tolist());uv[0].append((patch_uv(np.asarray(point)[None])[0]if tex is None else np.asarray(tex)).tolist());remap[0].append(int(sourceOld));patchKind[0].append(kind);return k

newFaces=[];faceKind=[];rows=[]
for sg,s,a in [(1,'L',6),(-1,'R',10)]:
 loop=loops[s];outer=c.unique[loop].copy();area=np.cross(outer[:-1,:2],outer[1:,:2]).sum()+np.cross(outer[-1,:2],outer[0,:2])
 if area*sg<0:loop=loop[::-1];outer=c.unique[loop].copy()
 n=len(loop);arc=np.r_[0,np.cumsum(np.linalg.norm(np.diff(np.r_[outer[:,:2],outer[None,0,:2]],axis=0),axis=1))][:-1];phase=np.arctan2((outer[0,1]-1.385)/.072,(outer[0,0]-.627)/.070);angle=phase+sg*arc/arc[-1]*2*np.pi # use full perimeter below, not last sample
 perimeter=np.linalg.norm(outer[:,:2]-np.roll(outer[:,:2],-1,axis=0),axis=1).sum();angle=phase+sg*arc/perimeter*2*np.pi;holeXY=np.c_[.627+.070*np.cos(angle),1.385+.072*np.sin(angle)];assert inside(holeXY,outer[:,:2]).all(),'New higher opening escapes source cut boundary'
 fit=RBFInterpolator(outer[:,:2],outer[:,2],kernel='thin_plate_spline',smoothing=1e-10);hole=np.c_[holeXY,fit(holeXY)];chest=np.zeros(N);chest[2]=1
 outerIds=[append(c.unique[u],bodyWeight[u],f'body-boundary-{s}')for u in loop];holeIds=[append(x,chest,f'higher-opening-{s}')for x in hole]
 tess=earcut(outer[:,:2],holeXY[::-1]);lookup=np.r_[outerIds,holeIds[::-1]];bodyTri=lookup[tess];pp=np.asarray(pos[0]);cross=np.cross(pp[bodyTri[:,1],:2]-pp[bodyTri[:,0],:2],pp[bodyTri[:,2],:2]-pp[bodyTri[:,0],:2]);bodyTri[cross*sg<0]=bodyTri[cross*sg<0][:,[0,2,1]]
 newFaces.extend(bodyTri.tolist());faceKind.extend([f'body-closure-{s}']*len(bodyTri))
 grid=[holeIds];layers=16
 for j in range(1,layers):
  t=j/layers;xy=holeXY*(1-t)+outer[:,:2]*t;z=fit(xy)+sg*(.012*t+.020*np.sin(np.pi*t));points=np.c_[xy,z];ring=[]
  for k,u in enumerate(loop):
   w=chest*(1-t)+armWeight[s][u]*t;ring.append(append(points[k],w,f'sewn-insert-{s}'))
  grid.append(ring)
 # Endpoints are exact detached source arm points and share exact weight values.
 grid.append([append(armPosition[s][u],armWeight[s][u],f'sleeve-boundary-{s}')for u in loop])
 loft=[]
 for j in range(layers):
  for k in range(n):
   kn=(k+1)%n;loft.extend([[grid[j][k],grid[j+1][k],grid[j][kn]],[grid[j][kn],grid[j+1][k],grid[j+1][kn]]])
 loft=np.array(loft,int);pp=np.asarray(pos[0]);cross=np.cross(pp[loft[:,1],:2]-pp[loft[:,0],:2],pp[loft[:,2],:2]-pp[loft[:,0],:2]);loft[cross*sg>0]=loft[cross*sg>0][:,[0,2,1]]
 newFaces.extend(loft.tolist());faceKind.extend([f'sewn-insert-{s}']*len(loft));rows.append({'side':s,'sourceLoopVertices':n,'oldBottomY':float(outer[:,1].min()),'newOpeningBottomY':float(hole[:,1].min()),'newOpeningTopY':float(hole[:,1].max()),'newBodyClosureFaces':len(bodyTri),'newInsertFaces':len(loft),'newOpeningInsideSourceCut':True,'sourceSleeveMarginMaxShiftM':.012,'surgeryGeodesicMarginM':.08})
tri[0]=np.concatenate([tri[0],np.asarray(newFaces,int)]);pos=[np.array(p,float)for p in pos];weights=[np.array(w,float)for w in weights];uv=[np.array(q,float)for q in uv]
# Restore exact outside arrays for glove/head primitives, then recompute clothing
# normals consistently over sewn exact-position aliases for this candidate.
sourceShape=np.load(ROOT/'hoodie-repair02/v7-shape-input.npz');normal=[sourceShape[f'n{i}'].copy()for i in range(5)];allpos=np.concatenate(pos);unique,alias=np.unique(allpos,axis=0,return_inverse=True);offset=np.r_[0,np.cumsum([len(p)for p in pos])];n=np.zeros_like(unique)
for i in [0,2]:
 q=pos[i][tri[i]];face=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);ids=alias[offset[i]:offset[i+1]][tri[i]]
 for j in range(3):np.add.at(n,ids[:,j],face)
n=unit(n)
for i in [0,2]:normal[i]=n[alias[offset[i]:offset[i+1]]]
out={}
for i in range(5):out.update({f'p{i}':pos[i],f'W{i}':weights[i],f'uv{i}':uv[i],f'tr{i}':tri[i],f'n{i}':normal[i],f'oldVertex{i}':np.array(remap[i],int)})
out.update(sourceAliasNew=alias,primitiveOffsetsNew=offset,newFacesPrimitive0=np.arange(len(c.tri[0]),len(tri[0])),newFaceKind=np.array(faceKind),newVertexKind0=np.array(patchKind[0]));np.savez(HERE/'armhole-reconstructed.npz',**out)
(HERE/'armhole-reconstructed-provenance.json').write_text(json.dumps({'status':'UNACCEPTED source topology reconstruction; rest/pose/render gates pending','sourceV7SHA256':hashlib.sha256(c.input.read_bytes()).hexdigest(),'candidateSHA256':hashlib.sha256((HERE/'armhole-reconstructed.npz').read_bytes()).hexdigest(),'method':'Cut actual cuff-connected sleeve off torso on original sewn mesh; fill lower old torso opening while leaving higher anatomical opening; sew detached source sleeve to new opening with additional locally sampled fabric. Source outer material retained; no external body panel or garment generation.','rows':rows,'vertexCountsBefore':[len(p)for p in c.pos],'vertexCountsAfter':[len(p)for p in pos],'sourceImagesUnchanged':True,'UVDonor':{'primitive':0,'sourceFace':int(donorFace),'sourcePixelCentre':[int(donorX),int(donorY)],'hoodieClothSafeFraction':float(donor[0]),'uvHalfExtent':.009,'sourceAtlasSHA256':hashlib.sha256(bytes(G.bin[bv.get('byteOffset',0):bv.get('byteOffset',0)+bv['byteLength']])).hexdigest()},'weightsChanged':'Source body/sleeve weights normalized only within declared80mm source-geodesic construction margin; new body opening chest-rigid, added insert linearly distributed chest-to-source-arm margins. All new/source rows keep19-bone contract, head/glove original.','compatibilityCost':'New vertex/face counts and local UV islands require regenerated GLB buffers, morph arrays and exact alias metadata; old frozenV7 morph offsets cannot be copied blindly. No runtime export yet.'},indent=2))
print(json.dumps(rows,indent=2));print('candidate vertexcounts',[len(p)for p in pos],flush=True)
