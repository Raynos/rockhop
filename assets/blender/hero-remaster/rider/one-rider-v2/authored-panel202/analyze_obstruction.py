"""Read-only202 authored-layout obstruction, never a geometry constructor.

This measures frozen source boundaries and full referenced whole-cloth incidence.
It does not claim these conditions mathematically prevent a valid new annulus.
"""
from pathlib import Path
from collections import defaultdict,Counter
import ast,hashlib,json,struct,time,subprocess,re
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop')
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E=R/'docs/evidence/hero-remaster/one-rider-v2/authored-panel202'
sha=lambda b:hashlib.sha256(b).hexdigest()
start=time.monotonic();pins={}
def pin(p,h=None):
 p=Path(p);b=p.read_bytes();s=sha(b);assert h is None or s==h;(pins.setdefault(str(p),{'sha256':s,'bytes':len(b)}));return b
def save(n,x):(E/n).write_text(json.dumps(x,indent=2)+'\n')
def check():
 v=subprocess.check_output(['vm_stat'],text=True);page=int(re.search(r'page size of (\d+)',v).group(1));anonymous=int(re.search(r'Anonymous pages:\s+(\d+)',v).group(1))*page;assert anonymous<70_000_000_000 and time.monotonic()-start<1200;return anonymous
mem=[check()];base=R/'docs/evidence/hero-remaster/one-rider-v2/local-retopology-design200'
contract=json.loads(pin(base/'parent-construction-contract202.json'))
d=json.loads(pin(base/'source-domain-boundaries.json'));whole=json.loads(pin(base/'whole-cloth-extension.json'));pin(base/'WHOLE_CLOTH_ADDENDUM.md')
for n in ['current-construction03-checkpoint.txt','Sculpt179-bounded-repair-guidance.txt','Construction21-current-status.txt']:pin(R/'docs/evidence/hero-remaster/one-rider-v2/foundation-repair-task3'/n)
reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/source-preserving-garment185/operator.py';t=ast.parse(pin(reader));cl=next(n for n in t.body if isinstance(n,ast.ClassDef)and n.name=='GLB');exec(compile(ast.Module(body=[cl],type_ignores=[]),str(reader),'exec'),globals())
src=B/'source-preserving-garment185/operator/rider.glb';pin(src,contract['source185SHA256']);g=GLB(src,contract['source185SHA256']);a,F=g.primitive(0,0);U,q=np.unique(a['POSITION'],axis=0,return_inverse=True);T=q[F];scope=set(d['proposedSourceFaceIDs']);assert len(scope)==1235
physical=[];faces=[];prim=[]
for pi in range(3):
 aa,ff=g.primitive(0,pi);offset=len(physical);physical.extend(aa['POSITION'].tolist());use=ff if pi else ff[[i for i in range(len(ff))if i not in scope]];faces.extend((use+offset).tolist());prim.extend([pi]*len(use))
W,aliases=np.unique(np.array(physical,np.float32),axis=0,return_inverse=True);G=aliases[np.array(faces,np.int64)];graph=defaultdict(set)
for t in G:
 for k in range(3):i,j=map(int,[t[k],t[(k+1)%3]]);graph[i].add(j);graph[j].add(i)
unseen=set(graph);comp=[];labels={}
while unseen:
 stack=[min(unseen)];seen=set()
 while stack:
  i=stack.pop()
  if i in seen:continue
  seen.add(i);stack.extend(graph[i]-seen)
 unseen-=seen;label=len(comp)
 for i in seen:labels[i]=label
 pos=W[sorted(seen)];comp.append({'nodeCount':len(seen),'axisBoundsM':[pos.min(0).tolist(),pos.max(0).tolist()]})
lookup={tuple(p):i for i,p in enumerate(W)};rings=[]
for c in d['orderedBoundaryRings']:
 ids=c['orderedPhysicalIDs'];P=U[ids].astype(float);assert np.array_equal(P,np.array(c['positionsM']));labs={labels[lookup[tuple(U[i])]]for i in ids};assert len(labs)==1
 rings.append({'nodes':len(ids),'orderedSourcePhysicalIDs':ids,'wholeComponent':next(iter(labs)),'YRangeM':[float(P[:,1].min()),float(P[:,1].max())],'allBelow1_30':bool((P[:,1]<1.30).all()),'exactFixedPositionsM':P.tolist(),'fixedHalfedges':c['directedHalfedges']})
assert len(comp)==2 and sorted(c['nodeCount']for c in comp)==[3058,19000];assert rings[0]['wholeComponent']!=rings[1]['wholeComponent']
# Compute nearest literal point pair at the sleeve maximum-height source vertex
# versus every >=1.30 central-ring vertex. This is a point diagnostic, not a
# surface-clearance or feasibility bound (edges/faces may lie closer).
central=U[rings[0]['orderedSourcePhysicalIDs']].astype(float);sleeve=U[rings[1]['orderedSourcePhysicalIDs']].astype(float);si=int(np.argmax(sleeve[:,1]));ci=np.flatnonzero(central[:,1]>=1.30);dist=np.linalg.norm(central[ci]-sleeve[si],axis=1);j=int(ci[np.argmin(dist)])
seam=d['original45NodeSeamReference'];sp=np.array(seam['positionsM']);star_min=int(np.argmin(sp[:,1]));seam_minY=float(sp[star_min,1]);delayed=[]
for r in rings:
 p=np.array(r['exactFixedPositionsM']);s=Counter(str(e['removedSourceChartID'])for e in r['fixedHalfedges']);delayed.append({'nodes':r['nodes'],'distinctRemovedBoundaryChartIDs':sorted(int(k)for k in s),'counts':dict(s)})
mem.append(check());report={'status':'BOUNDED_AUTHORING_OBSTRUCTION_NO_CANDIDATE_NOT_INFEASIBILITY_PROOF','sourceSHA256':contract['source185SHA256'],'geometryAttempts':0,'newWeights':0,'solverRuns':0,'exports':0,'GPUWork':False,'actualFinalCandidates':0,'wholeClothRetainedComponents':comp,'rings':rings,'retainedHighShoulderPath':False,'sleeveRingMinimumVerticalRiseTo1_30M':1.30-rings[1]['YRangeM'][1],'sleeveRingMinimumVerticalRiseTo1_32M':1.32-rings[1]['YRangeM'][1],'highestSleeveBoundaryToHighCentralBoundaryPointDiagnostic':{'sleevePhysicalID':rings[1]['orderedSourcePhysicalIDs'][si],'centralPhysicalID':rings[0]['orderedSourcePhysicalIDs'][j],'euclideanPointDistanceM':float(dist.min()),'notASurfaceOrFeasibilityBound':True},'originalFusedSeamMinimumY_M':seam_minY,'originalFusedSeamMinimumPhysicalID':seam['orderedPhysicalIDs'][star_min],'minimumOriginalSeamRiseTo1_30M':1.30-seam_minY,'boundaryChartFacts':delayed,'sourceIdentityHeadHoodGlovesBonesFieldsUnchanged':True,'whyNoCredibleLayoutWasRegistered':['The exact annular rings are folds of two different retained components, not anatomically paired planar sections. All62 sleeve nodes are below1.30; sewing both separate cap disks leaves two components.','The current source topology includes a low cross-channel web; merely subdividing and displacing the542 original interior nodes inherits that structural construction instead of authoring distinct medial returns.','Independent arc zipper, source-star lifting, full circular tube and whole-shell fitting are already rejected mechanisms. I did not register a renamed instance of those families.','A credible new multi-panel layout needs explicit3D ownership/fold curves and chart transport that turn both retained low channels up to one high saddle without a low connecting edge. I did not succeed in specifying those literal controls under this bounded attempt.'],'limits':['This is an authoring failure to supply a credible recipe; it is NOT proof that the registered1235 annulus is geometrically impossible.','No new triangles, candidate coordinates, donor transfers, static rest gate, appearance result, rig qualification or motion acceptance were produced.','The three CPU projection drawings are source geometry diagnostics, not render/mockup quality evidence.'],'specificAlternative':{'mechanism':'Change the literal domain so an existing high shoulder connection is retained; author medial torso/sleeve returns as separate local disks sharing only the existing high bridge, instead of inventing an all-new connecting annulus.','readOnlyFirst':True,'requiredMeasurements':['Choose source-owned central/left rooted anchors and find a retained central-to-left minimax path whose lowest necessary attachment lies1.30–1.32.','Declare exact new face IDs, fixed halfedges, source chart/normal ownership and visible front/back protection before any construction.','Confirm both low rooted channels remain separate and the whole cloth stays connected through the retained bridge.'],'conditional':True,'notAlreadyRegistered':True},'inputPins':pins,'timing':{'elapsedSeconds':time.monotonic()-start,'anonymousBytesSamples':mem,'CPUThreads':2,'GPU':False}}
save('report.json',report)
print(json.dumps({k:report[k]for k in ['status','geometryAttempts','wholeClothRetainedComponents','sleeveRingMinimumVerticalRiseTo1_30M','highestSleeveBoundaryToHighCentralBoundaryPointDiagnostic','timing']}))
