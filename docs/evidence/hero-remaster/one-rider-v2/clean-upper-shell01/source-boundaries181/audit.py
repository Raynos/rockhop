"""Read-only exact-position source boundary quotient and section measurements."""
from pathlib import Path
from collections import Counter,defaultdict
import ast,json,struct,hashlib,numpy as np
from scipy.spatial.transform import Rotation
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');O=R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/source-boundaries181';S=B/'clean-upper-shell01/source-boundaries181';sha=lambda b:hashlib.sha256(b).hexdigest();pins={}
def pin(p,role):
 p=Path(p);b=p.read_bytes();pins[str(p)]={'path':str(p),'SHA256':sha(b),'bytes':len(b),'role':role};return b
reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167/prepare.py';tree=ast.parse(pin(reader,'pinned raw reader').decode());cls=next(x for x in tree.body if isinstance(x,ast.ClassDef)and x.name=='GLB');env={'Path':Path,'json':json,'struct':struct,'np':np,'Rotation':Rotation,'sha':sha};exec(compile(ast.Module(body=[cls],type_ignores=[]),str(reader),'exec'),env);GLB=env['GLB'];C=GLB(Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb'),'186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e');G=GLB(B/'rig-adapter01/body-bind34/rider.glb','adbac6f2949cec0f32a8e0cfa4cfabd02cce61e58dab4022209e23a605f31df7');pin(C.p,'immutable raw C19');pin(G.p,'mapped34');assert C.bin==G.bin
T3=R/'assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3';E=T3/'hoodie-repair02/shape-lane/volume-lane/source-embedding23';H=json.loads(pin(E/'continuous-shell-handoff.json','task3 handoff read before reproduction'));pin(E/'continuous-shell-source-maps.npz','task3 source maps read before reproduction');maps=np.load(E/'continuous-shell-source-maps.npz');hem=json.loads(pin(T3/'hoodie-repair02/qa-lane/uv-lower01/hoodie-jeans-topology.json','existing semantic hem topology QA'));pin(T3/'hoodie-repair02/qa-lane/uv-lower01/lower-seam-support-witnesses.json','existing lower seam witnesses');proposal=json.loads(pin(T3/'hoodie-repair03/lower-foundation/seam-proposals/geometry.json','existing unaccepted intrinsic hem proposal'));pin(R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/rig-contract179/report.json','existing rig baseline audit');pin(R/'docs/evidence/hero-remaster/one-rider-v2/basic-pose-seams163/incident-edge-coverage.json','existing cuff topology QA')
attrs=[];rawT=[];start=[0]
for pi in range(3):
 a,t=C.primitive(0,pi);ga,gt=G.primitive(0,pi);assert all(np.array_equal(v,ga[k])for k,v in a.items())and np.array_equal(t,gt);attrs.append(a);rawT.append(t);start.append(start[-1]+len(a['POSITION']))
allP=np.concatenate([a['POSITION']for a in attrs]);U,inv=np.unique(allP,axis=0,return_inverse=True);Q=[inv[start[i]:start[i+1]]for i in range(3)];sets=[set(q.tolist())for q in Q];edges=[];faceMaps=[]
for pi in range(3):
 tris=Q[pi][rawT[pi]];ed=defaultdict(list)
 for ti,t in enumerate(tris):
  for i in range(3):ed[tuple(sorted([int(t[i]),int(t[(i+1)%3])]))].append(ti)
 edges.append(ed);faceMaps.append(tris)
def graph(vertices,ed):
 vertices=set(map(int,vertices));adj={v:set()for v in vertices}
 for a,b in ed:adj[a].add(b);adj[b].add(a)
 todo=set(vertices);comps=[]
 while todo:
  root=min(todo);stack=[root];seen=set()
  while stack:
   v=stack.pop()
   if v in seen:continue
   seen.add(v);stack.extend(adj[v]-seen)
  todo-=seen;degrees=Counter(len(adj[v])for v in seen);cycle=all(len(adj[v])==2 for v in seen);order=[]
  if cycle:
   prev=None;cur=min(seen)
   while cur not in order:
    order.append(cur);nxt=next(n for n in sorted(adj[cur])if n!=prev);prev,cur=cur,nxt
   assert cur==order[0]and len(order)==len(seen)
  comps.append({'vertices':len(seen),'edges':sum(len(adj[v])for v in seen)//2,'degreeHistogram':dict(degrees),'oneSimpleClosedCycle':cycle,'orderedCyclePhysicalIDs':order,'physicalIDs':sorted(seen)})
 for c in comps:
  pts=U[c['physicalIDs']];c['positionBoundsM']=[pts.min(0).tolist(),pts.max(0).tolist()];c['positionCentreM']=pts.mean(0).tolist()
 return comps
reports=[];payload={'allPhysicalFloat32Positions':U,'sourcePrimitive0RowsToPhysical':Q[0],'sourcePrimitive1RowsToPhysical':Q[1],'sourcePrimitive2RowsToPhysical':Q[2]}
for label,a,b,expected in [('hood_body',0,2,307),('cuff_body_glove',0,1,127)]:
 common=sets[a]&sets[b];assert len(common)==expected;inducedA={e for e in edges[a]if set(e)<=common};inducedB={e for e in edges[b]if set(e)<=common};shared=inducedA&inducedB;paired={e for e in shared if len(edges[a][e])==1 and len(edges[b][e])==1};components=graph(common,paired);sharedComponents=graph(common,shared);aliases=[];aliasmax=0
 for p in sorted(common):
  row=[];weights=[]
  for pi in [a,b]:
   ids=np.flatnonzero(Q[pi]==p);row.append({'primitive':pi,'rows':ids.tolist()});W=np.zeros((len(ids),19))
   for k in range(4):np.add.at(W,(np.arange(len(ids)),attrs[pi]['JOINTS_0'][ids,k]),attrs[pi]['WEIGHTS_0'][ids,k])
   weights.extend(W)
  gap=float(np.ptp(weights,axis=0).max());aliasmax=max(aliasmax,gap);aliases.append({'physicalID':p,'sourceFloat32Position':U[p].tolist(),'sourceRows':row,'maximumCanonicalWeightDifference':gap})
 def oriented(pi,e):
  face=faceMaps[pi][edges[pi][e][0]]
  return next(1 if (int(face[i]),int(face[(i+1)%3]))==e else -1 for i in range(3)if set([int(face[i]),int(face[(i+1)%3])])==set(e))
 orientation=Counter('opposite'if oriented(a,e)*oriented(b,e)==-1 else'same'for e in paired)
 incidence=Counter(f'{len(edges[a][e])}:{len(edges[b][e])}'for e in shared);r={'label':label,'primitiveNamespaces':[a,b],'physicalCommonGroups':len(common),'inducedEdgesA':len(inducedA),'inducedEdgesB':len(inducedB),'commonIndexedEdges':len(shared),'sharedEdgeIncidentFaceCounts':dict(incidence),'pairedOpenBoundaryEdges':len(paired),'pairedBoundaryWindingHistogram':dict(orientation),'pairedBoundaryComponents':components,'allSharedEdgeComponents':sharedComponents,'maximumAliasWeightDifference':aliasmax,'firstAliasWitnesses':aliases[:3]};reports.append(r)
 payload[label+'CommonPhysicalIDs']=np.array(sorted(common));payload[label+'SharedIndexedEdges']=np.array(sorted(shared));payload[label+'PairedBoundaryEdges']=np.array(sorted(paired))
 for i,c in enumerate(components):
  if c['oneSimpleClosedCycle']:payload[label+f'Cycle{i}PhysicalIDs']=np.array(c['orderedCyclePhysicalIDs']);payload[label+f'Cycle{i}Float32Positions']=U[c['orderedCyclePhysicalIDs']]
 (S/(label+'-aliases.json')).write_text(json.dumps(aliases,separators=(',',':'))+'\n')
# All physical open hood boundary cycles, without treating an upper ring as a semantic neck by height.
hoodOpen={e for e,f in edges[2].items()if len(f)==1};hoodVertices={v for e in hoodOpen for v in e};hoodGraphs=graph(hoodVertices,hoodOpen)
for i,c in enumerate(hoodGraphs):
 if c['oneSimpleClosedCycle']:payload[f'hoodOpenCycle{i}PhysicalIDs']=np.array(c['orderedCyclePhysicalIDs']);payload[f'hoodOpenCycle{i}Float32Positions']=U[c['orderedCyclePhysicalIDs']]
# Exact cross sections; generated intersections are measurements, not mesh vertices or proposed cuts.
sections=[];heights=[.94,.98,1.08,1.18,1.28,1.37,1.43,1.49]
for height in heights:
 for pi in [0,2]:
  P=attrs[pi]['POSITION'].astype(float);T=rawT[pi];candidates=np.flatnonzero((P[T][:,:,1].min(1)<height)&(P[T][:,:,1].max(1)>height));segments=[];faces=[];barys=[]
  for ti in candidates:
   tr=P[T[ti]];out=[];bs=[]
   for i in range(3):
    j=(i+1)%3;dy0=tr[i,1]-height;dy1=tr[j,1]-height
    if dy0*dy1<0:
     t=(height-tr[i,1])/(tr[j,1]-tr[i,1]);p=tr[i]+t*(tr[j]-tr[i]);w=np.zeros(3);w[i]=1-t;w[j]=t;out.append(p);bs.append(w)
   if len(out)==2:segments.append(out);faces.append(ti);barys.append(bs)
  seg=np.array(segments).reshape(-1,2,3);bar=np.array(barys).reshape(-1,2,3);fi=np.array(faces,dtype=int);prefix=f'y{height:.2f}_p{pi}';payload[prefix+'SegmentsM']=seg;payload[prefix+'SourceTriangleIDs']=fi;payload[prefix+'EndpointSourceTriangleBarycentric']=bar
  regions=[]
  for name,width in [('central',.18),('central_plus_lateral',.24)]:
   kept=[]
   for a,b in seg:
    dz=b[2]-a[2];lo=0.;hi=1.
    if abs(dz)<1e-15:
     if abs(a[2])>width:continue
    else:
     cuts=sorted([(-width-a[2])/dz,(width-a[2])/dz]);lo=max(lo,cuts[0]);hi=min(hi,cuts[1])
     if lo>hi:continue
    kept.extend([a+lo*(b-a),a+hi*(b-a)])
   pts=np.array(kept).reshape(-1,3);regions.append({'region':name,'ZabsMaxM':width,'sourceCrossingTriangles':len(seg),'clippedEndpointCount':len(pts),'boundsM':[pts.min(0).tolist(),pts.max(0).tolist()]if len(pts)else None,'frontMaxXPointM':pts[np.argmax(pts[:,0])].tolist()if len(pts)else None,'backMinXPointM':pts[np.argmin(pts[:,0])].tolist()if len(pts)else None,'widthZ':float(np.ptp(pts[:,2]))if len(pts)else None,'depthX':float(np.ptp(pts[:,0]))if len(pts)else None})
  sections.append({'heightM':height,'primitive':pi,'profiles':regions,'limits':'Only p0/p2 source surface at exactY clipped to declaredZwindows; sleeves/hood/skin/denim may still share region. No certified torso or semantic hem segmentation; no invented contour ellipse.'})
combined=[]
for height in heights:
 per=[x for x in sections if x['heightM']==height]
 for region in ['central','central_plus_lateral']:
  profiles=[next(q for q in x['profiles']if q['region']==region)for x in per];bounds=[q['boundsM']for q in profiles if q['boundsM']is not None]
  combined.append({'heightM':height,'region':region,'sourcePrimitives':[0,2],'combinedBoundsM':[np.min([b[0]for b in bounds],axis=0).tolist(),np.max([b[1]for b in bounds],axis=0).tolist()]if bounds else None,'frontMaxXPointM':max([q['frontMaxXPointM']for q in profiles if q['frontMaxXPointM']is not None],key=lambda p:p[0])if bounds else None,'backMinXPointM':min([q['backMinXPointM']for q in profiles if q['backMinXPointM']is not None],key=lambda p:p[0])if bounds else None,'warning':'Combined p0+p2 bounds measure fullcloth sourceprofile, not a connected/semantic torso contour. Atupperheights p0alone maybeonly shoulderstrips whilep2provideshoodvolume.'})
np.savez_compressed(S/'source-boundary-profiles.npz',**payload)
# Verify external cuff source position maps independently.
for side in ['L','R']:
 common=sets[0]&sets[1];ps=np.array([U[p]for p in common if (U[p,2]>0)==(side=='L')]);assert set(map(tuple,ps))==set(map(tuple,maps['cuffPositions'+side]))
result={'status':'READ_ONLY_BOUNDARY_PROFILE_BASELINE; NO CAGE_GEOMETRY_OR_ACCEPTANCE','declaredReadOnlyMethod':'Exact final float32 POSITION equality across declared source p0/p2 and sourcegloves p1. Build indexed edge incidence on physical position quotient, classify matching one-face primitive boundaries separately from internal shared vertices. No proximity welding, UV-component substitution or invented loops. Analytical source sections only, no semantic cut or source modification.','sourceHashes':{'rawC19':C.h,'mapped34':G.h},'sourceBINExact':True,'coordinates':'X forward estimate, Y up, Z lateral namedL+; existing game metres. Exact sourcefloat32 positions retained, no unit/basis reset.','interfaces':reports,'allHoodPhysicalOpenBoundaryComponents':hoodGraphs,'sourceProfiles':sections,'combinedClothProfiles':combined,'hemExistingQA':{'rawReport':hem,'handoffSemanticWarning':H['oldGarmentSeams']['fusedHoodieJeans'],'posteriorIndexedWitness':H['oldGarmentSeams']['posteriorHemWitness'],'existingIntrinsicGeometryProposal':proposal,'verdict':'Colourinterface23fragments is not a physical complete hem loop. Separate77edge intrinsic proposal is explicitlyUNACCEPTED and geometry alone does not establish gold/denim ownership. Neither flatheight cut nor primitiveID can pass semantic segmentation.'},'limits':['All graphIDs are exact-position quotient IDs, private CSR/row mappings include original primitive rows. Material numbers not used for semantics.','A boundary cycle is indexed topology evidence, not anatomy, selfintersection, visible join or motion acceptance.','Allsourcefloat32 positions retained; crosssection points are float64 analytic interpolants with literal source triangle/barycentric provenance.','No source weights, head/hood/glove/lower identity, physics, rig, paint or LOD changed.','If hoodbody graph is not one completepaired degree2cycle, do not force a falsejoin; parent can select continuous torso+hood reconstruction preserving sourcehood silhouette rather than overlapping shells.'],'inputHashes':list(pins.values()),'privateOutputs':[{'path':str(p),'SHA256':sha(p.read_bytes())}for p in S.glob('*')],'recipeSHA256':sha(Path(__file__).read_bytes())}
for p,r in pins.items():assert sha(Path(p).read_bytes())==r['SHA256']
(O/'report.json').write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'interfaces':[{k:r[k]for k in ['label','physicalCommonGroups','commonIndexedEdges','sharedEdgeIncidentFaceCounts','pairedOpenBoundaryEdges']}|{'pairedComponents':[{k:c[k]for k in ['vertices','edges','degreeHistogram','oneSimpleClosedCycle']}for c in r['pairedBoundaryComponents']]}for r in reports],'hoodOpen':[{k:c[k]for k in ['vertices','edges','degreeHistogram','oneSimpleClosedCycle']}for c in hoodGraphs]}))
