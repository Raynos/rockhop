"""Read-only finite original halfedge fan-scope alternatives; never modifies GLB."""
from pathlib import Path
from collections import defaultdict, Counter
import ast, json, struct, hashlib, os, time
os.environ['OPENBLAS_NUM_THREADS']='2';os.environ['OMP_NUM_THREADS']='2'
import numpy as np
from scipy.spatial.transform import Rotation
R=Path('/Users/raynos/projects/games/rockhop'); B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2'); E=R/'docs/evidence/hero-remaster/one-rider-v2/source-fan190'; S=B/'source-fan190'; start=time.monotonic()
sha=lambda b:hashlib.sha256(b).hexdigest()
def dump(p,x): p.write_text(json.dumps(x,indent=2)+'\n')
def receipt(p): return {'path':str(p),'sha256':sha(p.read_bytes()),'bytes':p.stat().st_size}
pr=E/'preregister.json'; rule=json.loads(pr.read_text()); source=B/'source-preserving-garment185/operator/rider.glb'; reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167/prepare.py'; left=B/'source-axilla189/positiveZ_lateral-proposed-strip.json'; right=B/'source-axilla189/negativeZ_lateral-proposed-strip.json'
assert sha(source.read_bytes())==rule['source185SHA256'];assert sha(left.read_bytes())==rule['left189SHA256'];assert sha(right.read_bytes())==rule['right189SHA256']
inputs=[source,reader,left,right,pr,R/'docs/evidence/hero-remaster/one-rider-v2/source-axilla189/freeze.json',R/'docs/evidence/hero-remaster/one-rider-v2/source-axilla189/parent-review.json']
for entry in json.loads(inputs[-2].read_text())['files']: assert sha(Path(entry['path']).read_bytes())==entry['sha256']
cls=next(x for x in ast.parse(reader.read_text()).body if isinstance(x,ast.ClassDef)and x.name=='GLB'); env={'Path':Path,'json':json,'struct':struct,'np':np,'Rotation':Rotation,'sha':sha};exec(compile(ast.Module(body=[cls],type_ignores=[]),str(reader),'exec'),env);C=env['GLB'](source,rule['source185SHA256']);a,f=C.primitive(0,0);P=a['POSITION'];U,q=np.unique(P,axis=0,return_inverse=True);pf=q[f];v=7392;assert np.flatnonzero(q==v).tolist()==[21088,21089];assert U[v].tolist()==rule['vertex']['positionM'];orig=set(json.loads(right.read_text())['sourceFaceIDs']);lf=set(json.loads(left.read_text())['sourceFaceIDs']);incident=set(np.flatnonzero((pf==v).any(1)).tolist());excluded=incident-orig
# Each original incident face is one edge of the vertex link. Components of
# excluded faces sharing a radial halfedge are exactly the literal notches.
radial=defaultdict(list)
for fi in incident:
 for n in pf[fi]:
  if n!=v:radial[int(n)].append(fi)
adj={i:set() for i in excluded}
for ids in radial.values():
 for i in set(ids)&excluded:adj[i].update((set(ids)&excluded)-{i})
remaining=set(excluded);sectors=[]
while remaining:
 todo=[min(remaining)];seen=set()
 while todo:
  i=todo.pop()
  if i in seen:continue
  seen.add(i);todo.extend(adj[i]-seen)
 remaining-=seen;sectors.append(sorted(seen))
sectors.sort(key=lambda x:x[0]);assert len(sectors)==2
frozen={'status':'FINITE_ALTERNATIVES_FROZEN_BEFORE_EVALUATION','preregisterSHA256':sha(pr.read_bytes()),'allIncidentSourceFaceIDs':sorted(incident),'chosenIncidentSourceFaceIDs':sorted(incident&orig),'excludedLiteralFanSectors':sectors,'originalIncidentLink': [{'faceID':i,'physicalTriangle':pf[i].tolist(),'sourceRows':f[i].tolist(),'included189':i in orig}for i in sorted(incident)],'inputPins':[receipt(p)for p in inputs]};dump(E/'alternatives.json',frozen)
# All ordering is inherited source winding; no sorting changes a triangle.
def topology(chosen):
 pe=defaultdict(list); vertexfaces=defaultdict(list)
 for fi in sorted(chosen):
  t=list(map(int,pf[fi]))
  for x in t:vertexfaces[x].append(fi)
  for k in range(3): x,y=t[k],t[(k+1)%3];pe[tuple(sorted((x,y)))].append([fi,x,y])
 directed=[x[0]for x in pe.values()if len(x)==1];out=defaultdict(list);inn=Counter()
 for fi,x,y in directed:out[x].append((y,fi));inn[y]+=1
 invalid=[{'physicalID':x,'in':inn[x],'out':len(out[x])}for x in sorted(set(out)|set(inn))if inn[x]!=1 or len(out[x])!=1]
 cycles=[];rem=set(out)
 if not invalid:
  while rem:
   x=min(rem);first=x;ids=[];fis=[]
   while x in rem:rem.remove(x);ids.append(x);x,fi=out[x][0];fis.append(fi)
   assert x==first
   cycles.append({'orderedPhysicalP0IDs':ids,'orderedPositionsM':U[ids].tolist(),'sourceRowAliases':[np.flatnonzero(q==i).tolist()for i in ids],'incidentSourceFaces':fis})
 edge_bad=[{'edge':list(e),'halfedges':hs}for e,hs in pe.items()if len(hs)>2 or (len(hs)==2 and hs[0][1:]!=hs[1][1:][::-1])]
 vertex_bad=[]
 for x,fis in vertexfaces.items():
  link=defaultdict(list)
  for fi in fis:
   ns=[int(n)for n in pf[fi]if n!=x]
   if len(ns)!=2:vertex_bad.append({'physicalID':x,'reason':'degenerate'});continue
   link[ns[0]].append(ns[1]);link[ns[1]].append(ns[0])
  seen=set();todo=[min(link)]
  while todo:
   n=todo.pop()
   if n in seen:continue
   seen.add(n);todo.extend(set(link[n])-seen)
  deg=sorted(map(len,link.values()));boundary=x in out or x in inn
  good=len(seen)==len(link) and (deg.count(1)==2 and max(deg)<=2 if boundary else all(d==2 for d in deg))
  if not good:vertex_bad.append({'physicalID':x,'connected':len(seen)==len(link),'linkDegrees':deg})
 faceadj=defaultdict(set)
 for hs in pe.values():
  for h in hs:faceadj[h[0]].update(k[0]for k in hs if k[0]!=h[0])
 seen=set();todo=[min(chosen)]
 while todo:
  i=todo.pop()
  if i in seen:continue
  seen.add(i);todo.extend(faceadj[i]-seen)
 chi=len(vertexfaces)-len(pe)+len(chosen);valid=not invalid and not edge_bad and not vertex_bad and len(seen)==len(chosen) and len(cycles)==2 and chi==0
 return {'faceCount':len(chosen),'physicalVertexCount':len(vertexfaces),'edgeCount':len(pe),'boundaryHalfedges':directed,'invalidBoundaryNodes':invalid,'orderedSourceBoundaryCycles':cycles,'boundaryCycleLengths':[len(c['orderedPhysicalP0IDs'])for c in cycles],'orientationOrManifoldBadEdges':edge_bad,'nonManifoldVertexLinks':vertex_bad,'edgeConnected':len(seen)==len(chosen),'eulerCharacteristic':chi,'validAnnulus':valid}
# Use exact alias source rows, not181physical IDs (different primitive union).
protection={}
for name,file in [('hood',B/'clean-upper-shell01/source-boundaries181/hood_body-aliases.json'),('cuff',B/'clean-upper-shell01/source-boundaries181/cuff_body_glove-aliases.json')]:
 rows={r for item in json.loads(file.read_text())for rec in item['sourceRows']if rec['primitive']==0 for r in rec['rows']};protection[name]=set(q[list(rows)].tolist());inputs.append(file)
base=topology(orig);lefttop=topology(lf);dump(S/'original189-right-topology.json',base);dump(S/'unchanged189-left-topology.json',lefttop)
results=[]
for number,ids in enumerate(sectors):
 add=set(ids);candidate=orig|add;nodes=set(pf[ids].ravel().tolist());newnodes=nodes-set(pf[list(orig)].ravel().tolist());dist={n:float(np.linalg.norm(U[n].astype(float)-U[v].astype(float)))for n in nodes};hood=nodes&protection['hood'];cuff=nodes&protection['cuff'];low=[i for i in ids if np.any(P[f[i],1]<1.16)];top=topology(candidate)
 newmax=max((dist[n]for n in newnodes),default=0.0);constraints=len(add)<=16 and newmax<=.02 and not hood and not cuff and not low
 minimality=[{'omittedFaceID':i,'remainingAddedFaceIDs':sorted(add-{i}),'validAnnulus':topology(orig|(add-{i}))['validAnnulus'],'invalidBoundaryNodes':topology(orig|(add-{i}))['invalidBoundaryNodes']}for i in ids]
 limits={'addedFacesCount':len(add),'addedVerticesAllDistancesM':[{'physicalID':n,'distanceM':dist[n]}for n in sorted(nodes)],'maxAddedFaceVertexDistanceM':max(dist.values()),'maxNewScopeVertexDistanceM':newmax,'newScopeVertexIDs':sorted(newnodes),'hoodAliasPhysicalIntersections':sorted(hood),'cuffAliasPhysicalIntersections':sorted(cuff),'lowerThanInheritedY116FaceIDs':low,'withinFrozenLimits':constraints}
 ancestry=[{'sourceFaceID':i,'sourceRows':f[i].tolist(),'physicalP0IDs':pf[i].tolist(),'sourcePositionsM':P[f[i]].tolist(),'physicalVertexSourceRowAliases':[np.flatnonzero(q==n).tolist()for n in pf[i]],'rowAttributeSHA256':{k:sha(val[f[i]].tobytes())for k,val in a.items()},'originalWindingRetained':True}for i in ids]
 payload={'alternative':number,'addedSourceFaceIDs':ids,'preserved189SourceFaceIDs':sorted(orig),'candidateSourceFaceIDs':sorted(candidate),'candidatePhysicalP0IDs':sorted(set(pf[list(candidate)].ravel().tolist())),'addedFaceAncestry':ancestry,'strictSubsetMinimalityWitnesses':minimality,'constraints':limits,'topology':top,'boundaryDifferenceFrom189':{'removedDirectedPhysicalEdges':sorted(set(tuple(h[1:])for h in base['boundaryHalfedges'])-set(tuple(h[1:])for h in top['boundaryHalfedges'])),'addedDirectedPhysicalEdges':sorted(set(tuple(h[1:])for h in top['boundaryHalfedges'])-set(tuple(h[1:])for h in base['boundaryHalfedges']))},'feasibleScope':constraints and top['validAnnulus']};dest=S/f'alternative-{number}.json';dump(dest,payload);results.append({'alternative':number,'addedSourceFaceIDs':ids,'addedFaces':len(ids),'maxDistanceM':newmax,'boundaryCycleLengths':top['boundaryCycleLengths'],'annulusTopologyValid':top['validAnnulus'],'withinFrozenLimits':constraints,'feasibleScope':payload['feasibleScope'],'raw':receipt(dest)})
# Freeze every primitive source field/index/morph and scene/rig/material metadata.
fieldpins=[]
for mi,mesh in enumerate(C.d['meshes']):
 for pi,p in enumerate(mesh['primitives']):
  at,faces=C.primitive(mi,pi);fieldpins.append({'mesh':mi,'primitive':pi,'faces':len(faces),'indicesSHA256':sha(faces.tobytes()),'attributes':{k:{'shape':list(val.shape),'dtype':str(val.dtype),'sha256':sha(val.tobytes())}for k,val in at.items()},'morphTargets':[{k:sha(C.acc(acc).tobytes())for k,acc in t.items()}for t in p.get('targets',[])]})
outside=set(range(len(f)))-orig-set(x for sector in sectors for x in sector);outside_payload={'outsideBothAlternativeEnvelopeSourceFaceIDs':sorted(outside),'sourceRows':sorted(set(f[list(outside)].ravel().tolist())),'outsideTriangleRowsSHA256':sha(f[sorted(outside)].tobytes()),'allOriginalPrimitiveFieldPins':fieldpins,'sceneRigMaterialJSONSHA256':sha(json.dumps({k:C.d.get(k)for k in ['nodes','skins','scenes','materials','textures','images','samplers','animations']},sort_keys=True).encode()),'allSourceBytesExact':source.read_bytes()==C.raw,'allOldInputsExact':all(sha(Path(i['path']).read_bytes())==i['sha256']for i in frozen['inputPins']),'left189ScopeExact':sha(left.read_bytes())==rule['left189SHA256'],'headHoodGlovesLowerbodyRigUVNormalsPBROutsidePositionsIndicesWeightsUntouched':True,'originalAliasNodeCounts':{k:len(val)for k,val in protection.items()},'addedFaceAliasAssessment':'Both sectors are p0; exact source hood/cuff alias intersections reported per alternative. Geometric locality/lowerY116 is a conservative exclusion test, not a semantic garment mask. No certified semantic face ownership exists here; no anatomy or deformation qualification.'};dump(S/'outside-protection.json',outside_payload)
report={'status':'READONLY_HALFEDGE_SCOPE_CLOSURE_FINDING_NO_GEOMETRY_AUTHORIZATION','sourceSHA256':C.h,'baselineRight':{'faces':len(orig),'invalidBoundaryNodes':base['invalidBoundaryNodes'],'validAnnulus':base['validAnnulus']},'unchangedLeft':{'faces':len(lf),'boundaryCycleLengths':lefttop['boundaryCycleLengths'],'validAnnulus':lefttop['validAnnulus']},'alternatives':results,'feasibleAlternatives':[x['alternative']for x in results if x['feasibleScope']],'all189ChosenFacesPreserved':True,'outsideProtection':receipt(S/'outside-protection.json'),'limits':'No source edit/solver/export/render/GPU. Topology feasibility never implies semantic-mask/anatomy/geometry acceptance. Parent sole judge.','elapsedSeconds':time.monotonic()-start};dump(E/'report.json',report)
files=[p for p in sorted(S.iterdir())if p.is_file()]+[pr,E/'alternatives.json',E/'report.json',Path(__file__)]+([E/'README.md']if(E/'README.md').exists()else[]);dump(E/'freeze.json',{'status':'FROZEN_FINITE_SCOPE_ALTERNATIVES_ONLY','inputs':[receipt(p)for p in inputs],'files':[receipt(p)for p in files]});print(json.dumps({'alternatives':results,'sourceUnchanged':outside_payload['allSourceBytesExact'],'elapsedSeconds':report['elapsedSeconds']}))
