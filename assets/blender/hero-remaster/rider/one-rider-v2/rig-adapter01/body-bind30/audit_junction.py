"""Read-only complete garment graph and projected rejected26 triangle witnesses."""
from pathlib import Path
import hashlib,json,sys
import numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
from PIL import Image,ImageDraw
repo=Path('/Users/raynos/projects/games/rockhop')
base=repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01'
private=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
out=base/'body-bind30';out.mkdir(exist_ok=True)
sys.path.insert(0,str(Path(__file__).resolve().parent.parent/'body-bind26'))
from common import load,accessor,sha
raw,j,b,p,start=load();field=np.load(private/'body-bind26/weight-field.npz')
manifest=json.loads((out/'candidate-cpu/pose-manifest.json').read_text())
old=json.loads((base/'body-bind25/morph01/baseline-normal01/pose-manifest.json').read_text())
prior=json.loads((base/'body-bind26/candidate-cpu/pose-manifest.json').read_text())
def read(root,rec,lanes):
 f=root/rec['file']
 if not f.exists() and root==out/'candidate-cpu':f=private/'body-bind30/candidate-cpu'/rec['file']
 data=f.read_bytes();assert sha(data)==rec['sha256']
 return np.frombuffer(data,dtype='<f8').reshape(-1,lanes).copy()
prim=manifest['primitives'][0];rest=read(out/'candidate-cpu',prim['attributes']['position'],3)
tri=read(out/'candidate-cpu',prim['index'],3).astype(int)
normal=read(out/'candidate-cpu',prim['attributes']['normal'],3)
assert np.array_equal(rest,field['rest']) and np.array_equal(tri,field['triangles'])
u=field['unique'];inv=field['inverse'];ut=inv[tri]
edges=np.unique(np.sort(np.concatenate([ut[:,[0,1]],ut[:,[1,2]],ut[:,[2,0]]]),axis=1),axis=0)
edges=edges[edges[:,0]!=edges[:,1]]
adj=coo_matrix((np.ones(len(edges)*2),(np.r_[edges[:,0],edges[:,1]],np.r_[edges[:,1],edges[:,0]])),shape=(len(u),len(u))).tocsr()
components,labels=connected_components(adj)
W=field['original'];C=np.zeros_like(W)
encodedIndices=read(out/'candidate-cpu',prim['attributes']['skinIndex'],4).astype(int)
encodedWeights=read(out/'candidate-cpu',prim['attributes']['skinWeight'],4)
for lane in range(4):np.add.at(C,(np.arange(len(rest)),encodedIndices[:,lane]),encodedWeights[:,lane])
assert np.max(abs(C-field['candidate']))<1e-7
first=np.unique(rest,axis=0,return_index=True)[1];uw=W[first];cw=C[first]
changed=np.max(abs(cw-uw),axis=1)>1e-7;pinned=~changed
junction=changed[edges[:,0]]!=changed[edges[:,1]]
length=np.linalg.norm(u[edges[:,0]]-u[edges[:,1]],axis=1)
assert np.all(length>0)
oldjump=np.sum(abs(uw[edges[:,0]]-uw[edges[:,1]]),axis=1)
newjump=np.sum(abs(cw[edges[:,0]]-cw[edges[:,1]]),axis=1)
names=[j['nodes'][i]['name'] for i in j['skins'][0]['joints']]
def weights(v,source):return {n:float(w) for n,w in zip(names,source[v]) if w>0}
def unit(x):return x/np.maximum(np.linalg.norm(x,axis=-1,keepdims=True),1e-30)
sourceq=rest[tri];sourcecross=np.cross(sourceq[:,1]-sourceq[:,0],sourceq[:,2]-sourceq[:,0])
sourcearea=np.linalg.norm(sourcecross,axis=1)
sourceedge=np.linalg.norm(sourceq-np.roll(sourceq,-1,axis=1),axis=2)
sourcedot=np.einsum('ti,ti->t',unit(sourcecross),unit(normal[tri].mean(1)))
selectedTriangle=np.any(field['selected'][ut],axis=1)
mixed=np.any(changed[ut],axis=1)&np.any(pinned[ut],axis=1)
roi=(sourceq[:,:,1].mean(1)>.95)&(np.abs(sourceq[:,:,2]).mean(1)>.13)
rows=[];witnesses=[]
for sample,oldsample,previous in zip(manifest['rows'],old['rows'],prior['rows']):
 key=sample['i'];assert key==oldsample['i']==previous['i']
 # Independent new CPU reconstruction is byte-exact to retained26 CPU states.
 for attr in ['positions','gpuRuleSkinnedNormals','skinMatrices','jointTransforms']:
  assert sample['dump'][0][attr]['sha256']==previous['dump'][0][attr]['sha256']
 ap=read(private/'body-bind25/morph01/baseline-normal01',oldsample['dump'][0]['positions'],3)
 an=read(private/'body-bind25/morph01/baseline-normal01',oldsample['dump'][0]['gpuRuleSkinnedNormals'],3)
 bp=read(out/'candidate-cpu',sample['dump'][0]['positions'],3)
 bn=read(out/'candidate-cpu',sample['dump'][0]['gpuRuleSkinnedNormals'],3)
 measures=[]
 for P,N in [(ap,an),(bp,bn)]:
  q=P[tri];cross=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);dot=np.einsum('ti,ti->t',unit(cross),unit(N[tri].mean(1)))
  stretch=(np.linalg.norm(q-np.roll(q,-1,axis=1),axis=2)/np.maximum(sourceedge,1e-30)).max(1)
  measures.append({'dot':dot,'stretch':stretch,'area':np.linalg.norm(cross,axis=1)/np.maximum(sourcearea,1e-30),'fold':(sourcedot>.2)&(dot<-.2)})
 a,c=measures;newfold=c['fold']&~a['fold']&roi
 worsestretch=roi&(c['stretch']>2)&(c['stretch']>a['stretch']*1.5)
 bad=newfold|worsestretch
 row={'sample':key,'allBodyTriangles':len(tri),'newArmGeometryNormalOpposition':int(newfold.sum()),'newArmStretchRegressionTriangles':int(worsestretch.sum()),'flaggedUnion':int(bad.sum()),'mixedChangedPinnedTrianglesFlagged':int((bad&mixed).sum()),'fullyChangedTrianglesFlagged':int((bad&~mixed&np.any(changed[ut],axis=1)).sum()),'completelyPinnedTrianglesFlagged':int((bad&~np.any(changed[ut],axis=1)).sum())}
 rows.append(row)
 for angle in ['side','rear-three-quarter']:
  ndc=read(out/'candidate-cpu',sample['dump'][0]['projected'][angle],3)
  image=Image.open(private/'body-bind26/played/decoded-evidence/candidate'/angle/'gray/original'/f'{key:04d}.png').convert('RGB')
  width,height=image.size;assert width/height==16/9
  screen=np.c_[(ndc[:,0]+1)*width/2,(1-ndc[:,1])*height/2]
  centre=screen[tri].mean(1);inside=(centre[:,0]>0)&(centre[:,0]<width)&(centre[:,1]>0)&(centre[:,1]<height)&(ndc[tri,2].mean(1)>-1)&(ndc[tri,2].mean(1)<1)
  score=(c['stretch']-a['stretch'])+newfold*8
  ids=np.flatnonzero(bad&inside);ids=ids[np.argsort(-score[ids])][:12]
  image=Image.open(private/'body-bind26/played/decoded-evidence/candidate'/angle/'gray/original'/f'{key:04d}.png').convert('RGB')
  assert image.size==(width,height);draw=ImageDraw.Draw(image)
  for n,t in enumerate(ids):
   points=[tuple(x) for x in screen[tri[t]]];draw.line(points+[points[0]],fill=(255,50,50),width=3)
   x,y=centre[t];draw.text((x,y),str(int(t)),fill=(255,230,30),stroke_width=1,stroke_fill=(0,0,0))
   witnesses.append({'sample':key,'view':angle,'triangle':int(t),'exportVertices':tri[t].tolist(),'sourcePositions':rest[tri[t]].tolist(),'projectedPixels':screen[tri[t]].tolist(),'sourceImageSize':[width,height],'candidateNormalDot':float(c['dot'][t]),'baselineNormalDot':float(a['dot'][t]),'candidateMaximumEdgeStretch':float(c['stretch'][t]),'baselineMaximumEdgeStretch':float(a['stretch'][t]),'changedPhysicalVertices':changed[ut[t]].tolist(),'sharedOtherPrimitiveAliases':field['shared'][ut[t]].tolist(),'graphBoundaryProtected':field['boundary'][ut[t]].tolist(),'sourceWeights':[weights(v,W) for v in tri[t]],'candidateWeights':[weights(v,C) for v in tri[t]]})
  draw.rectangle((0,0,width,45),fill=(0,0,0));draw.text((12,14),f'REJECTED26 sample{key} {angle}: red = ranked normal/stretch regression triangles; projection only, no depth/visibility certificate',fill='white')
  image.save(out/f'projected-{angle}-key{key:03d}.jpg',quality=94)
worst=np.flatnonzero(junction);worst=worst[np.argsort(-newjump[worst])][:12]
report={'status':'READ-ONLY measured complete source garment graph; rejected26 diagnostics, no new asset','sourceSHA256':sha(raw),'candidateSHA256':manifest['sourceSHA256'],'completeGraph':{'exportVertices':len(rest),'physicalVertices':len(u),'triangles':len(tri),'components':components,'componentVertexCounts':np.bincount(labels).tolist(),'sharedOtherPrimitivePhysicalAliases':int(field['shared'].sum()),'changedPhysicalVertices':int(changed.sum()),'changedPinnedInterfaceEdges':int(junction.sum()),'mixedChangedPinnedTriangles':int(mixed.sum()),'junctionL1JumpBeforeAfterP50P90P99':[np.quantile(x[junction],[.5,.9,.99]).tolist() for x in [oldjump,newjump]],'junctionL1GradientPerMetreBeforeAfterP50P90P99':[np.quantile((x/length)[junction],[.5,.9,.99]).tolist() for x in [oldjump,newjump]]},'worstInterfaceEdges':[{'physicalVertices':edges[e].tolist(),'positions':u[edges[e]].tolist(),'edgeLengthM':float(length[e]),'sourceWeightJump':float(oldjump[e]),'candidateWeightJump':float(newjump[e]),'sharedAliases':field['shared'][edges[e]].tolist()} for e in worst],'actualReconstructedRowsExactToPrior26':4,'recordedCameraAnchorProjectionErrorUpperBound':1e-12,'rows':rows,'witnesses':witnesses,'limits':['Flags are normal opposition/stretch; no triangle-intersection or visual grade implied.','Wholebody graph included; arm diagnosis ROI uses geometry only, no source weight eligibility.','Screen overlays use actual retained cameras/input and exact CPU skinning; no depth test, projected triangles may be occluded.','Interface measurements alone cannot prove all visual fans caused by frozen boundary; parent must inspect matched played images.','No new weights/topology/asset or physics change.']}
(out/'junction-audit.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps({'completeGraph':report['completeGraph'],'rows':rows},indent=2))
