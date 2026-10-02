"""Independent frozen Q182 topology and provenance; no builder/extractor invocation."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,json,struct,hashlib,numpy as np
from scipy.spatial.transform import Rotation
R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/source-guided-cage182';O=E/'independent-qa';A=R/'assets/blender/hero-remaster/rider/one-rider-v2/clean-upper-shell01/source-guided-cage182';pins={};sha=lambda b:hashlib.sha256(b).hexdigest()
def pin(p,expected=None):
 p=Path(p);b=p.read_bytes();h=sha(b)
 if expected:assert h==expected
 pins[str(p)]={'path':str(p),'SHA256':h,'bytes':len(b)};return b
manifest=json.loads(pin(E/'manifest.json'));M=Path(manifest['masters'])
for p,x in manifest['files'].items():pin(p,x['sha256'])
source=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb');reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167/prepare.py';tree=ast.parse(pin(reader).decode());cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='GLB');env={'Path':Path,'json':json,'struct':struct,'np':np,'Rotation':Rotation,'sha':sha};exec(compile(ast.Module(body=[cls],type_ignores=[]),str(reader),'exec'),env);GLB=env['GLB'];C=GLB(source,manifest['sourceDonorSHA256']);pin(source,C.h);G=GLB(M/'neutral-assembly01.glb',manifest['files'][str(M/'neutral-assembly01.glb')]['sha256']);data=np.load(M/'bodydata01.npz');cage=np.load(M/'cage01.npz');tags=json.loads((M/'quad-face-tags.json').read_text());sourceattrs,sourceT=C.primitive(0,0)
assert G.bin[:len(C.bin)]==C.bin;assert G.d['meshes'][1]==C.d['meshes'][1];assert G.d['meshes'][0]['primitives'][1:]==C.d['meshes'][0]['primitives'][1:]
for k in ['materials','images','textures','samplers']:
 assert G.d.get(k,[])[:len(C.d.get(k,[]))]==C.d.get(k,[])
parts=[];comparison=[]
for pi in range(3):
 ga,gt=G.primitive(0,pi);assert np.array_equal(ga['POSITION'],data['p'+str(pi)])and np.array_equal(gt,data['f'+str(pi)]);comparison.append({'primitive':pi,'exportedPositionAndIndexArraysExactAgainstBodydata':True,'attributeCounts':{k:len(v)for k,v in ga.items()}})
 if pi==0:
  for k,x in ga.items():assert np.array_equal(x,data['p0attribute_'+k])and np.array_equal(x[:len(sourceattrs[k])],sourceattrs[k])
 else:
  ca,ct=C.primitive(0,pi);assert all(np.array_equal(v,ca[k])for k,v in ga.items())and np.array_equal(gt,ct)
 parts.append((ga['POSITION'],gt))
mesh=next(i for i,m in enumerate(G.d['meshes'])if m.get('name')=='UNACCEPTED_CAGE182');ga,gt=G.primitive(mesh,0);assert np.array_equal(ga['POSITION'],data['newShellP'])and np.array_equal(ga['NORMAL'],data['newShellN'])and np.array_equal(gt,data['newShellF']);parts.append((ga['POSITION'],gt));V=data['newShellP'];F=data['newShellF'];assert np.array_equal(cage['p'],V)and np.array_equal(cage['f'],F)
# Map authored face tags to literal final triangles independently: quads fan to two, triangles to one.
quadTag=iter(data['authoredQuads']);triangleTags=[];qi=0
for tag in tags:
 if tag.endswith(' triangle'):triangleTags.append(tag)
 else:triangleTags.extend([tag,tag]);qi+=1
assert qi==len(data['authoredQuads'])and len(triangleTags)==len(F)
# Body-only final REFERENCED physical counts. Unused source position storage is excluded.
PP=[];FF=[];offset=0;faceOffsets=[];faceTotal=0
for P,T in parts:PP.append(P);FF.append(T+offset);offset+=len(P);faceOffsets.append(faceTotal);faceTotal+=len(T)
PP=np.concatenate(PP);FF=np.concatenate(FF);referencedRows=np.unique(FF);U,rinv=np.unique(PP[referencedRows],axis=0,return_inverse=True);rowmap=np.full(len(PP),-1,dtype=int);rowmap[referencedRows]=rinv;physical=rowmap[FF];edges=defaultdict(list)
for fi,t in enumerate(physical):
 for k in range(3):
  a,b=map(int,[t[k],t[(k+1)%3]]);edges[tuple(sorted([a,b]))].append({'face':fi,'direction':1 if a<b else -1})
T=PP[FF].astype(float);area=np.linalg.norm(np.cross(T[:,1]-T[:,0],T[:,2]-T[:,0]),axis=1)*.5;ST=V[F].astype(float);shellArea=np.linalg.norm(np.cross(ST[:,1]-ST[:,0],ST[:,2]-ST[:,0]),axis=1)*.5;deg=np.flatnonzero(shellArea<1e-12);wrong=[(e,v)for e,v in edges.items()if len(v)==2 and v[0]['direction']==v[1]['direction']];non=[(e,v)for e,v in edges.items()if len(v)>2];boundary=[e for e,v in edges.items()if len(v)==1]
shellU,shellInv=np.unique(V[np.unique(F)],axis=0,return_inverse=True);repeat=[]
for i,t in enumerate(F):
 if len(set(map(tuple,V[t])))<3:repeat.append(i)
seams=[];key={tuple(p):i for i,p in enumerate(U)}
for name in ['hoodIDs','hemIDs','cuffLIDs','cuffRIDs']:
 ids=data[name];position=V[ids];rows=[]
 for i,(a,b)in enumerate(zip(position,np.roll(position,-1,axis=0))):
  edge=tuple(sorted([key[tuple(a)],key[tuple(b)]]));inc=edges[edge];paired=len(inc)==2 and inc[0]['direction']!=inc[1]['direction'];rows.append({'cycleEdgeID':i,'physicalIDs':list(edge),'positions':[a.tolist(),b.tolist()],'incidentFaces':inc,'pairedOpposite':paired})
 incidence=Counter(len(r['incidentFaces'])for r in rows);seams.append({'cycle':name,'nodes':len(ids),'distinctFloat32Positions':len(np.unique(position,axis=0)),'edgeIncidenceHistogram':dict(incidence),'pairedOpposite':sum(r['pairedOpposite']for r in rows),'sameDirectionTwoFaceEdges':sum(len(r['incidentFaces'])==2 and r['incidentFaces'][0]['direction']==r['incidentFaces'][1]['direction']for r in rows),'nonmanifoldEdges':sum(len(r['incidentFaces'])>2 for r in rows),'literalFailedWitnesses':[r for r in rows if not r['pairedOpposite']][:6]})
# Literal herm ring coincidence: exact cage inner torso0 is the64sample resampling of same outer hem curve.
hemP=V[data['hemIDs']];coarse=V[:64];dists=[];nearest=[]
for p in coarse:
 a=hemP.astype(float);b=np.roll(a,-1,axis=0);v=b-a;t=np.clip(((p-a)*v).sum(1)/(v*v).sum(1),0,1);q=a+t[:,None]*v;distance=np.linalg.norm(q-p,axis=1);i=int(np.argmin(distance));dists.append(float(distance[i]));nearest.append({'coarseVertexID':len(dists)-1,'exactHemEdgeIDs':[i,(i+1)%len(hemP)],'edgeParameter':float(t[i]),'distanceM':float(distance[i])})
# All active glTF physical referenced position count, including protected head and cheek.
activePositions=[];nodeParts=[]
for ni,node in enumerate(G.d['nodes']):
 if 'mesh'not in node:continue
 for pi,p in enumerate(G.d['meshes'][node['mesh']]['primitives']):
  a,t=G.primitive(node['mesh'],pi);ids=np.unique(t);P=a['POSITION'][ids].astype(float);world=G.world(ni);assert np.isfinite(P).all()and np.isfinite(world).all();P=np.einsum('ab,vb->va',world,np.c_[P,np.ones(len(P))],optimize=False)[:,:3];assert np.isfinite(P).all();activePositions.append(P);nodeParts.append({'node':ni,'mesh':node['mesh'],'primitive':pi,'referencedAttributeRows':len(ids),'worldMatrix':world.tolist()})
fullPhysical=len(np.unique(np.concatenate(activePositions),axis=0));refShell=len(np.unique(F));tagStats=Counter(triangleTags[i]for i in deg);wrongTags=Counter()
for e,v in wrong:
 for inc in v:
  i=inc['face']-faceOffsets[-1]
  if 0<=i<len(triangleTags):wrongTags[triangleTags[i]]+=1
literal=[{'shellTriangleID':int(i),'tag':triangleTags[i],'vertexIDs':F[i].tolist(),'positions':V[F[i]].tolist(),'areaM2':float(shellArea[i]),'distinctFloat32Positions':len(set(map(tuple,V[F[i]])))}for i in deg[:15]]
ringStats=[]
for ring in range(6):
 q=V[ring*64:(ring+1)*64];ringStats.append({'ring':ring,'sourceBuildRole':'hemResample'if ring==0 else 'innerCollar'if ring==5 else 'nearest8AngularSourceSelector','nodes':len(q),'distinctFloat32Positions':len(np.unique(q,axis=0)),'coincidentAdjacentEdges':int((q==np.roll(q,-1,axis=0)).all(1).sum())})
morphCounts=[]
for mi,m in enumerate(G.d['meshes']):
 for pi,p in enumerate(m['primitives']):
  baseCount=G.d['accessors'][p['attributes']['POSITION']]['count']
  for ti,target in enumerate(p.get('targets',[])):
   for semantic,ai in target.items():morphCounts.append({'mesh':mi,'primitive':pi,'target':ti,'semantic':semantic,'baseVertexCount':baseCount,'targetVertexCount':G.d['accessors'][ai]['count'],'countMatches':baseCount==G.d['accessors'][ai]['count']})
hemStats=[]
for label in ['hem transition','hem transition triangle']:
 ids=[i for i,t in enumerate(triangleTags)if t==label];hemStats.append({'tag':label,'triangles':len(ids),'areaMinimumM2':float(shellArea[ids].min()),'areaMedianM2':float(np.median(shellArea[ids])),'areaMaximumM2':float(shellArea[ids].max())})
res={'status':'Q182_REJECTED_INDEPENDENT_LITERAL_EXPORT_QA_NO_REPAIR','sourceSHA256':C.h,'exportSHA256':G.h,'protectedIdentity':{'originalBINPrefixExact':True,'headCheekMeshDefinitionsAndActiveAttributesExact':True,'hoodGlovePrimitiveDefinitionsAndActiveAttributesExact':True,'originalPBRMaterialImageTextureSamplerDefinitionPrefixesExact':True,'originalReferencedImageBytesExactViaBINPrefix':True,'allOriginalBodyAttributeRowsExactInDerivedActiveArrays':True,'limits':'All skins and clips removed deliberately; retaining source rig nodes/attributes is not an attached animated rig. Newshell unrigged/untextured;319designcut rows arederived, not exactnewsourceidentity.'},'exportVsBodydata':comparison+ [{'primitive':'newShell','positionsNormalsIndicesExact':True}],'finalReferencedCounts':{'bodyClothAttributeRows':len(referencedRows),'bodyClothExactPositionPhysicalVertices':len(U),'bodyClothFaces':len(FF),'shellReferencedAttributeRows':refShell,'shellExactPositionPhysicalVertices':len(shellU),'allActiveGLTFWorldPhysicalVertices':fullPhysical,'activeNodes':nodeParts,'warning':'Counts exclude unreferenced source rows. Exact position quotient is topology analysis, never a broad tolerance weld.'},'topology':{'shellDegenerateAreaBelow1e12':len(deg),'combinedDegenerateAreaBelow1e12':int((area<1e-12).sum()),'physicalRepeatedVertexShellTriangles':len(repeat),'combinedNonmanifoldEdges':len(non),'combinedWrongWindingEdges':len(wrong),'combinedBoundaryEdges':len(boundary),'degenerateTags':dict(tagStats),'wrongEdgeIncidentShellTags':dict(wrongTags),'degenerateLiteralWitnesses':literal},'seams':seams,'torsoRingDuplicateCoordinates':ringStats,'activeMorphAccessorCounts':morphCounts,'hemTransitionAreaObservations':hemStats,'hemCoincidentInnerRing':{'coarseTorso0Vertices':64,'maximumDistanceToExactOuterHemPolylineM':max(dists),'minimumDistanceM':min(dists),'literalWitnesses':nearest[:8],'interpretation':'grid[0]=samples(hem,64), both rings lie on same source polyline before Float32; this is not a distinct hemwall. zipper uses normalized index fractions, whereas64samples are by geometric arclength; miscorrespondence can span curve corners/create coplanar foldovers instead of every triangle simply being collinear. Exact duplicates add incidence. Preserve actual area observations rather than claiming allhem triangles zero.'},'inputs':list(pins.values()),'recipeSHA256':sha(Path(__file__).read_bytes()),'limits':['No render, repair, source edits, animation/gameplay, full selfintersection retest or visual acceptance.','Parent crossingaudit826strictpairs is separatelypinned and not rerun; topologyfailuresalone reject.','Source donorbindings/PBR identity preservation cannotaccept malformed newgeometry ornewcutsemanticownership.']}
for p,x in pins.items():assert sha(Path(p).read_bytes())==x['SHA256']
(O/'report.json').write_text(json.dumps(res,indent=2)+'\n');print(json.dumps({'counts':res['finalReferencedCounts']|{'activeNodes':'see report'},'topology':{k:v for k,v in res['topology'].items()if 'Witnesses'not in k},'seams':[{k:r[k]for k in ['cycle','nodes','distinctFloat32Positions','edgeIncidenceHistogram','pairedOpposite','sameDirectionTwoFaceEdges','nonmanifoldEdges']}for r in seams],'hemMaxDistance':max(dists)}))
