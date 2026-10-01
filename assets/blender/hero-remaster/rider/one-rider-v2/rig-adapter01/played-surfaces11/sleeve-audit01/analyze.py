"""Read-only sleeve topology, skin-fold and source-albedo diagnosis; no render/GPU."""
from pathlib import Path
import json,io,struct,hashlib,sys
import numpy as np
from PIL import Image
np.seterr(all='raise')
repo=Path('/Users/raynos/projects/games/rockhop');out=Path(sys.argv[1]) if len(sys.argv)>1 else repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/played-surfaces11/sleeve-audit01';manifest=json.loads((out/'pose-manifest.json').read_text());raw=Path(manifest['source']).read_bytes();jl=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+jl]);binary=raw[28+jl:]
def read(record,lanes):
 p=out/record['file']
 if not p.exists():p=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/played-surfaces11/sleeve-audit01')/record['file']
 assert hashlib.sha256(p.read_bytes()).hexdigest()==record['sha256']
 return np.fromfile(p,dtype='<f8').reshape(-1,lanes)
def unit(v):return v/np.maximum(np.linalg.norm(v,axis=-1,keepdims=True),1e-30)
def sample(image,uv):
 h,w=image.shape[:2];x=np.clip(uv[:,0]*w-.5,0,w-1);y=np.clip(uv[:,1]*h-.5,0,h-1);ix=np.floor(x).astype(int);iy=np.floor(y).astype(int);jx=np.minimum(ix+1,w-1);jy=np.minimum(iy+1,h-1);fx=(x-ix)[:,None];fy=(y-iy)[:,None]
 return ((image[iy,ix]*(1-fx)+image[iy,jx]*fx)*(1-fy)+(image[jy,ix]*(1-fx)+image[jy,jx]*fx)*fy)
sourceRows=[];poseRows=[]
for mi,p in enumerate(manifest['primitives']):
 a=p['attributes'];rest=read(a['position'],3);normal=read(a['normal'],3);uv=read(a['uv'],2);si=read(a['skinIndex'],4).astype(int);sw=read(a['skinWeight'],4);tri=read(p['index'],3).astype(int);r=rest[tri];cross=np.cross(r[:,1]-r[:,0],r[:,2]-r[:,0]);area=np.linalg.norm(cross,axis=1)/2;sourceDots=np.einsum('ti,ti->t',unit(cross),unit(normal[tri].mean(1)));armBones=[i for i,b in enumerate(p['bones']) if b.startswith(('upperArm','forearm'))];aw=np.where(np.isin(si,armBones),sw,0).sum(1);roi=(aw[tri].mean(1)>.3)&(rest[tri,1].mean(1)>.9)&(np.abs(rest[tri,2]).mean(1)>.13);sleeve=np.flatnonzero(roi)
 # Exact-position welding removes exporter UV/normal duplicate edges only.
 keys=[tuple(v) for v in rest];canonical={};weld=[]
 for key in keys:
  if key not in canonical:canonical[key]=len(canonical)
  weld.append(canonical[key])
 welded=np.array(weld)[tri];edges={}
 for ti,t in enumerate(welded):
  for i in range(3):edges.setdefault(tuple(sorted([int(t[i]),int(t[(i+1)%3])])),[]).append(ti)
 boundary=[(edge,ts) for edge,ts in edges.items() if len(ts)==1];nonmanifold=[(edge,ts) for edge,ts in edges.items() if len(ts)>2];sleeveBoundary=[{'triangle':ts[0],'canonicalEdge':list(edge)} for edge,ts in boundary if roi[ts[0]]];sleeveNonmanifold=[{'triangles':ts,'canonicalEdge':list(edge)} for edge,ts in nonmanifold if any(roi[t] for t in ts)]
 parent=np.arange(len(rest))
 def find(i):
  while parent[i]!=i:parent[i]=parent[parent[i]];i=int(parent[i])
  return i
 firstAliases={}
 for i,key in enumerate(keys):
  if key in firstAliases:parent[find(i)]=find(firstAliases[key])
  else:firstAliases[key]=i
 for t in tri:
  rt=find(int(t[0]));
  for v in t[1:]:parent[find(int(v))]=rt
 roots=np.array([find(i) for i in range(len(rest))]);components=[]
 for root in sorted(set(roots[tri[sleeve]].ravel())):
  ids=np.flatnonzero(roots==root);ts=np.flatnonzero(roots[tri[:,0]]==root);components.append({'vertices':len(ids),'triangles':len(ts),'sleeveTriangles':int(roi[ts].sum()),'sourceBounds':{'min':rest[ids].min(0).tolist(),'max':rest[ids].max(0).tolist()},'totalAreaM2':float(area[ts].sum())})
 # CPU decoder retains material indices, but images are inspected directly
 # from immutable GLB, independent of lighting, normal maps and shader code.
 material=0 if mi==0 else 2;mat=doc['materials'][material];texture=mat['pbrMetallicRoughness']['baseColorTexture']['index'];imageIndex=doc['textures'][texture]['source'];view=doc['bufferViews'][doc['images'][imageIndex]['bufferView']];image=np.array(Image.open(io.BytesIO(binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']])).convert('RGB'));factor=np.array(mat['pbrMetallicRoughness'].get('baseColorFactor',[1,1,1,1]))[:3];colors=[]
 for bary in [[1/3,1/3,1/3],[.6,.2,.2],[.2,.6,.2],[.2,.2,.6]]:colors.append(sample(image,np.einsum('tvi,v->ti',uv[tri],bary))*factor)
 color=np.mean(colors,axis=0);assert np.isfinite(color).all();luma=np.einsum('vi,i->v',color,np.array([.2126,.7152,.0722]));dark=roi&(luma<55);darkIds=np.flatnonzero(dark)
 coincident={}
 for i,key in enumerate(keys):coincident.setdefault(key,[]).append(i)
 aliasGroups=[ids for ids in coincident.values() if len(ids)>1 and np.any(aw[ids]>.3) and rest[ids[0],1]>.9 and abs(rest[ids[0],2])>.13]
 W=np.zeros((len(rest),len(p['bones'])))
 for i in range(len(rest)):
  for b,w in zip(si[i],sw[i]):W[i,b]+=w
 aliasWeightDiff=[float(np.max(np.abs(W[ids,None,:]-W[None,ids,:]))) for ids in aliasGroups]
 sourceRows.append({'mesh':p['mesh'],'vertices':len(rest),'triangles':len(tri),'sleeveTriangles':len(sleeve),'sleeveSourceFaceAgainstVertexNormal':int((roi&(sourceDots<-.2)).sum()),'sleeveSourceDegenerateTriangles':int((roi&(area<1e-10)).sum()),'sleeveBoundaryEdges':len(sleeveBoundary),'sleeveBoundaryWitnesses':sleeveBoundary[:40],'sleeveNonmanifoldEdges':len(sleeveNonmanifold),'sleeveNonmanifoldWitnesses':sleeveNonmanifold[:40],'componentsTouchingSleeve':components,'exactCoincidentSleeveGroups':len(aliasGroups),'maximumCoincidentSourceBoneWeightDifference':max(aliasWeightDiff,default=0),'sourceBaseColorImage':imageIndex,'sourceBaseColorSize':list(image.shape[:2][::-1]),'sleeveBaseColorLumaRange':([float(luma[roi].min()),float(np.median(luma[roi])),float(luma[roi].max())] if roi.any() else []),'darkAlbedoSleeveTriangles':len(darkIds),'darkAlbedoWitnesses':[{'triangle':int(i),'RGB':color[i].tolist(),'sourcePositions':rest[tri[i]].tolist()} for i in darkIds[:20]]})
 for row in manifest['rows']:
  posed=read(row['dump'][mi]['positions'],3);norm=read(row['dump'][mi]['gpuRuleSkinnedNormals'],3);q=posed[tri];pcross=np.cross(q[:,1]-q[:,0],q[:,2]-q[:,0]);pa=np.linalg.norm(pcross,axis=1)/2;dots=np.einsum('ti,ti->t',unit(pcross),unit(norm[tri].mean(1)));edgesR=np.linalg.norm(r-np.roll(r,-1,axis=1),axis=2);edgesP=np.linalg.norm(q-np.roll(q,-1,axis=1),axis=2);stretch=(edgesP/np.maximum(edgesR,1e-30)).max(1);ratio=pa/np.maximum(area,1e-30);flipped=roi&(sourceDots>.2)&(dots<-.2);ids=np.flatnonzero(flipped);worst=sorted(sleeve,key=lambda i:dots[i])[:25]
  separations=[float(np.linalg.norm(posed[ids,None,:]-posed[None,ids,:],axis=2).max()) for ids in aliasGroups]
  poseRows.append({'sample':row['i'],'mesh':p['mesh'],'sleeveTriangles':len(sleeve),'newFaceAgainstSkinnedNormalTriangles':len(ids),'areaBelowQuarterTriangles':int((roi&(ratio<.25)).sum()),'maxSleeveEdgeStretch':float(stretch[roi].max()) if roi.any() else None,'minimumSleeveNormalDot':float(dots[roi].min()) if roi.any() else None,'flippedDarkAlbedoTriangles':int((flipped&dark).sum()),'maximumCoincidentSleeveSeparationM':max(separations,default=0),'coincidentSleeveGroupsOver1mm':sum(d>.001 for d in separations),'worst':[{'triangle':int(i),'indices':tri[i].tolist(),'normalDot':float(dots[i]),'sourceNormalDot':float(sourceDots[i]),'areaRatio':float(ratio[i]),'edgeStretch':float(stretch[i]),'RGB':color[i].tolist(),'sourcePositions':rest[tri[i]].tolist(),'posedBikeFramePositions':posed[tri[i]].tolist(),'weights':[[{'bone':p['bones'][bone],'weight':float(w)} for bone,w in zip(si[v],sw[v]) if w>1e-5] for v in tri[i]]} for i in worst]})
report={'sourceSHA256':manifest['sourceSHA256'],'sourceUnchanged':hashlib.sha256(raw).hexdigest()==manifest['sourceSHA256'],'cpuPoseVsRetainedActualContactMaximumErrorM':max(c['maximumCPUvsActualPlayedSurfaceM'] for row in manifest['rows'] for c in row['contacts']),'source':sourceRows,'poses':poseRows,'limits':['CPU geometry/albedo diagnosis only; no rendering, asset editing or appearance score.','Sleeve ROI: mean upperArm/forearm weight >.3, source y>.9m and mean absolute z>.13m.','Face-versus-skinned-normal diagnostics identify local fold/normal disagreement; they are not alone a watertight volume or self-intersection proof.','Topology components and boundaries weld exact source positions to ignore normal/UV exporter splits.','Four recorded states reconstruct physical pose; actual retained palm/sole points independently match within float32 serialization error.']};(out/'report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'source':[{k:v for k,v in x.items() if k not in ['sleeveBoundaryWitnesses','sleeveNonmanifoldWitnesses','componentsTouchingSleeve','darkAlbedoWitnesses']} for x in sourceRows],'poses':[{k:v for k,v in x.items() if k!='worst'} for x in poseRows]}))
