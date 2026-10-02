"""CPU-only immutable source-field inventory on literal unsealed 47-face mask."""
from pathlib import Path
from collections import defaultdict, Counter, deque
import ast, gzip, hashlib, json, re, struct, subprocess, time
import numpy as np
from scipy.spatial.transform import Rotation
R=Path('/Users/raynos/projects/games/rockhop')
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E=R/'docs/evidence/hero-remaster/one-rider-v2/source-weight-audit194'
start=time.monotonic(); pins={}; memories=[]
sha=lambda b: hashlib.sha256(b).hexdigest()
def pin(p, expected=None):
 p=Path(p); b=p.read_bytes(); h=sha(b); assert expected is None or h==expected
 pins[str(p)]={'sha256':h,'bytes':len(b)}; return b
def check():
 assert time.monotonic()-start<590
 v=subprocess.check_output(['vm_stat'],text=True)
 pg=int(re.search(r'page size of (\d+)',v).group(1))
 gb=int(re.search(r'Anonymous pages:\s+(\d+)',v).group(1))*pg/1e9
 assert gb<70; memories.append(gb)
def save(name,d):
 (E/name).write_text(json.dumps(d,indent=2,default=lambda v:v.item() if isinstance(v,np.generic) else v.tolist())+'\n')
check()
source=B/'source-preserving-garment185/operator/rider.glb'
h='ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5'
raw=pin(source,h)
reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167/prepare.py'
cls=next(n for n in ast.parse(pin(reader)).body if isinstance(n,ast.ClassDef) and n.name=='GLB')
exec(compile(ast.Module(body=[cls],type_ignores=[]),str(reader),'exec'),globals())
g=GLB(source,h); a,F=g.primitive(0,0); glove,GF=g.primitive(0,1)
P=a['POSITION']; U,q=np.unique(P,axis=0,return_inverse=True); PF=q[F]
assert len(F)==33968 and len(P)==22240
aliases=defaultdict(list)
for i,v in enumerate(q): aliases[int(v)].append(i)
contract=json.loads(pin(R/'docs/evidence/hero-remaster/one-rider-v2/physical-cut193/parent-construction-contract.json'))
sep=json.loads(pin(B/'physical-cut193/literal-separator.json'))
mask=set(contract['exactRemovedSourceFaceIDs']); assert len(mask)==47 and sorted(mask)==sep['finalMaskAudit']['removedFaces']
section=json.loads(pin(B/'source-axilla189/section-fixed-03.json')); assert section['heightY_M']==1.13
roots={}
for loop in section['loops']:
 roots[loop['geometricClass']]={int(i) for s in loop['segments'] for ep in s['endpoints'] for i in ep.get('sourcePhysicalEdge',[]) if U[i,1]<1.13}
assert roots['central_Z0_straddling']==set(sep['roots']['central_Z0_straddling'])
assert roots['positiveZ_lateral']==set(sep['roots']['positiveZ_lateral'])
kept=np.array([fi for fi in range(len(F)) if fi not in mask]); present=set(map(int,PF[kept].ravel()))
low={i for i in present if U[i,1]<1.30}; adj=defaultdict(set); full=defaultdict(set); edgefaces=defaultdict(list)
for fi in kept:
 t=PF[fi]
 for k in range(3):
  i,j=map(int,[t[k],t[(k+1)%3]]); full[i].add(j); full[j].add(i); edgefaces[tuple(sorted((i,j)))].append(int(fi))
  if i in low and j in low: adj[i].add(j); adj[j].add(i)
remaining=set(low); comps=[]; cid={}
while remaining:
 seed=min(remaining); stack=[seed]; seen=set()
 while stack:
  i=stack.pop()
  if i in seen: continue
  seen.add(i); stack.extend(adj[i]-seen)
 remaining-=seen; label=len(comps)
 for i in seen: cid[i]=label
 comps.append(sorted(seen))
rootids={label:sorted({cid[i] for i in rr}) for label,rr in roots.items()}
assert all(len(c)==1 for c in rootids.values())
leftid=rootids['positiveZ_lateral'][0]; centralid=rootids['central_Z0_straddling'][0]
assert leftid!=centralid
actualnames=[g.d['nodes'][i]['name'] for i in g.d['skins'][0]['joints']]
names=[n.removeprefix('fresh.') for n in actualnames]
known=json.loads(pin(R/'docs/evidence/hero-remaster/one-rider-v2/candidate-handoff170/mapping-report.json'))
assert names==[r['name'] for r in known['restHierarchy']]
def dense(attrs):
 j=attrs['JOINTS_0']; w=attrs['WEIGHTS_0']; raw=np.zeros((len(j),len(names)))
 for k in range(4): np.add.at(raw,(np.arange(len(j)),j[:,k]),w[:,k])
 nw=(w.astype(float)/np.abs(w.astype(float)).sum(1,keepdims=True)).astype('f4')
 norm=np.zeros_like(raw)
 for k in range(4): np.add.at(norm,(np.arange(len(j)),j[:,k]),nw[:,k])
 return raw,norm,nw
W,N,N4=dense(a); GW,GN,GN4=dense(glove)
canon=np.array([aliases[i][0] for i in range(len(U))]); PN=N[canon]
centralnames=['pelvis','spine','chest','neck','head']; indices=[names.index(n) for n in centralnames]
def named(v): return {names[i]:float(x) for i,x in enumerate(v) if x!=0}
def rowrec(row):
 i=int(q[row]); return {'sourceRowID':row,'physicalSourceID':i,'positionM':P[row].tolist(),'allP0Aliases':aliases[i], 'sublevelComponentID':cid.get(i),'geometricRootLabels':[k for k,c in rootids.items() if cid.get(i) in c], 'rawJointOrdinals':a['JOINTS_0'][row].tolist(),'rawLaneWeights':a['WEIGHTS_0'][row].tolist(),'rawNamedWeights':named(W[row]),'stockThreeNormalizedNamedWeights':named(N[row]),'retainedIncidentSourceFaces':[int(fi) for fi in kept if row in F[fi]],'removedIncidentSourceFaces':[int(fi) for fi in mask if row in F[fi]]}
physicalrecords=[]; mismatch=[]
for i,rr in aliases.items():
 rawexact=all(a['JOINTS_0'][r].tobytes()==a['JOINTS_0'][rr[0]].tobytes() and a['WEIGHTS_0'][r].tobytes()==a['WEIGHTS_0'][rr[0]].tobytes() for r in rr)
 maxdiff=float(abs(N[rr]-N[rr[0]]).max())
 if not rawexact or maxdiff: mismatch.append({'physicalID':i,'sourceRows':rr,'rawFourLaneBytesExact':rawexact,'normalizedDenseMaxDifference':maxdiff})
 physicalrecords.append({'physicalSourceID':i,'sourceRows':rr,'positionM':U[i].tolist(),'remainingOriginalSublevelComponentID':cid.get(i),'canonicalRawNamedWeights':named(W[rr[0]]),'canonicalNormalizedNamedWeights':named(N[rr[0]])})
# Cross-primitive identity uses literal Float32 POSITION equality, not tolerance or nearest bone.
lookup={tuple(p.tolist()):i for i,p in enumerate(U)}; shared=defaultdict(list)
for r,p in enumerate(glove['POSITION']):
 i=lookup.get(tuple(p.tolist()))
 if i is not None: shared[i].append(r)
cuff=[]
for i,gg in sorted(shared.items()):
 if U[i,2]<=0: continue
 rr=aliases[i]; diffs=[float(abs(N[r]-GN[s]).max()) for r in rr for s in gg]
 cuff.append({'physicalSourceID':i,'p0Rows':rr,'gloveRows':gg,'positionM':U[i].tolist(),'sublevelComponentID':cid.get(i),'p0NamedWeights':[named(N[r]) for r in rr],'gloveNamedWeights':[named(GN[r]) for r in gg],'normalizedDenseMaxDifference':max(diffs),'rawFourLaneBytesExact':all(a['JOINTS_0'][r].tobytes()==glove['JOINTS_0'][s].tobytes() and a['WEIGHTS_0'][r].tobytes()==glove['WEIGHTS_0'][s].tobytes() for r in rr for s in gg)})
assert len(cuff)==65
L=set(comps[leftid]); frontier={i for i in L if any(j not in low for j in full[i])}
boundary=set(contract['fixedOrientedBoundaryPhysicalIDs'])
def grow(seeds,n):
 v=set(seeds)
 for _ in range(n): v|={j for i in v for j in adj[i] if j in L}
 return v&L
cuffIDs={r['physicalSourceID'] for r in cuff}; cuffguard=grow(cuffIDs,2); highguard=grow(frontier|(boundary&L),2)
# A fixed geometric distal band is only a bounded proposal, not an anatomical annotation.
roi=sorted(i for i in L-cuffguard-highguard if 1.0<U[i,1]<1.20)
check()
componentstats=[]
for n,cc in enumerate(comps):
 vv=PN[cc]; total=vv[:,indices].sum(1)
 componentstats.append({'componentID':n,'physicalVertices':len(cc),'originalAliasRows':sum(len(aliases[i]) for i in cc),'rootLabels':[label for label,c in rootids.items() if n in c],'boundsM':[U[cc].min(0).tolist(),U[cc].max(0).tolist()],'centralNamedTotal':{'anyPositive':int((total>0).sum()),'over1percent':int((total>.01).sum()),'over10percent':int((total>.1).sum()),'maximum':float(total.max()),'mean':float(total.mean()),'percentiles':np.percentile(total,[0,25,50,75,90,99,100]).tolist()},'namedJointInventory':{name:{'anyPositive':int((vv[:,k]>0).sum()),'over1percent':int((vv[:,k]>.01).sum()),'maximum':float(vv[:,k].max()),'mean':float(vv[:,k].mean()),'sum':float(vv[:,k].sum())} for k,name in enumerate(names)}})
witness=[rowrec(r) for r in [2030,2172]]
pair=[int(q[r]) for r in [2030,2172]]; edge=tuple(sorted(pair)); length=float(np.linalg.norm(P[2172].astype(float)-P[2030]))
grad=N[2172]-N[2030]
actual=json.loads(pin(R/'docs/evidence/hero-remaster/one-rider-v2/source-rig188/actual-three/report.json'))
parent=json.loads(pin(R/'docs/evidence/hero-remaster/one-rider-v2/source-rig188/parent-review.json'))
rig188=json.loads(pin(R/'docs/evidence/hero-remaster/one-rider-v2/source-rig188/read-only/report.json'))
morphCuff=[]
for ti,(bt,gt) in enumerate(zip(g.d['meshes'][0]['primitives'][0].get('targets',[]),g.d['meshes'][0]['primitives'][1].get('targets',[]))):
 vals={}
 for semantic in ['POSITION','NORMAL']:
  bv=g.acc(bt[semantic]); gv=g.acc(gt[semantic]); diffs=[float(abs(bv[r]-gv[t]).max()) for c in cuff for r in c['p0Rows'] for t in c['gloveRows']]
  vals[semantic]={'maximumComponentDifference':max(diffs),'allSharedRowsExact':max(diffs)==0}
 morphCuff.append({'targetOrdinal':ti,'fields':vals})
leftArmNames=['shoulder.L','upperArm.L','forearm.L','hand.L']; leftArmOrdinals=[names.index(n) for n in leftArmNames]
def fieldsummary(ids,field):
 vv=field[ids]; central=vv[:,indices].sum(1); arm=vv[:,leftArmOrdinals].sum(1)
 return {'uniquePhysicalNodes':len(ids),'centralTotal':{'sum':float(central.sum()),'mean':float(central.mean()),'maximum':float(central.max()),'positiveNodes':int((central>0).sum())},'leftArmTotal':{'sum':float(arm.sum()),'mean':float(arm.mean()),'minimum':float(arm.min()),'zeroNodes':int((arm==0).sum()),'below1e_6Nodes':int((arm<1e-6).sum())},'namedFields':{name:{'positiveNodes':int((vv[:,k]>0).sum()),'sum':float(vv[:,k].sum()),'mean':float(vv[:,k].mean()),'maximum':float(vv[:,k].max())} for k,name in enumerate(names)}}
GU,gq=np.unique(glove['POSITION'],axis=0,return_inverse=True); galias=defaultdict(list)
for r,i in enumerate(gq): galias[int(i)].append(r)
gcanon=np.array([galias[i][0] for i in range(len(GU))]); GPN=GN[gcanon]
gleft=sorted(int(i) for i in range(len(GU)) if GU[i,2]>0)
ginterior=[i for i in gleft if tuple(GU[i].tolist()) not in lookup]
cuffstats=fieldsummary(sorted(cuffIDs),PN); glovestats=fieldsummary(ginterior,GPN)
leftstats=fieldsummary(sorted(L),PN)
zeroLeftArm=[i for i in sorted(L) if PN[i,leftArmOrdinals].sum()==0]
noncentralOrdinals=[k for k in range(len(names)) if k not in indices]
zeroNoncentral=[i for i in sorted(L) if PN[i,noncentralOrdinals].sum()==0]
noncentralOther=[names[k] for k in range(len(names)) if k not in indices+leftArmOrdinals and PN[list(L),k].max()>0]
report={'status':'FROZEN_READONLY_SOURCE_FIELD_INVENTORY_NO_ADAPTATION','sourceSHA256':h,'actualGeometryAttempts':0,'weightsModified':0,'meshesExported':0,'GPUWork':False,'sourceP0':{'rows':len(P),'triangles':len(F),'physicalVertices':len(U),'removedFaces':sorted(mask),'remainingFaces':len(kept)},'method':'Exact Float32 POSITION physical IDs are np.unique lexicographic order, identical source189/193 convention. Graph includes edges incident to at least one retained original face with both endpoints Y<1.30. All retained sublevel physical vertices included, even isolated nodes. Root seeds are exact below1.13 endpoints of fixed-03 literal section edges. Fields reported separately raw and stockThree absolute-sum Float32 normalized lanes. No spatial or nearest-bone anatomical assignment.','rootComponents':rootids,'components':componentstats,'leftGeometricComponentID':leftid,'centralGeometricComponentID':centralid,'rightRootComponentID':rootids['negativeZ_lateral'][0],'centralAndRightStillSameComponent':centralid==rootids['negativeZ_lateral'][0],'witness2030_2172':witness,'witnessEdge':{'physicalIDs':pair,'remainingIncidentSourceFaces':edgefaces[edge],'sourceLengthM':length,'namedNormalizedDelta2172Minus2030':named(grad),'denseL1Delta':float(abs(grad).sum()),'totalVariation':float(abs(grad).sum()/2),'centralNamedDelta':float(grad[indices].sum()),'denseL1GradientPerM':float(abs(grad).sum()/length)},'physicalAliases':{'duplicatedPhysicalVertices':sum(len(rr)>1 for rr in aliases.values()),'mismatchCount':len(mismatch),'mismatches':mismatch},'leftGloveBodyCuff':{'sharedPhysicalVertices':len(cuff),'p0AliasRows':sum(len(r['p0Rows']) for r in cuff),'gloveAliasRows':sum(len(r['gloveRows']) for r in cuff),'mismatchingPhysicalVertices':sum(r['normalizedDenseMaxDifference']!=0 for r in cuff),'maximumNormalizedDenseDifference':max(r['normalizedDenseMaxDifference'] for r in cuff),'crossPrimitiveExactRawFourLanes':all(r['rawFourLaneBytesExact'] for r in cuff),'morphFieldContinuity':morphCuff},'sourceCuffMass':cuffstats,'sourceLeftGloveInteriorMass':glovestats,'sourceLeftGlovePhysicalNodes':len(gleft),'sourceLeftGloveInteriorAliasRows':sum(len(galias[i]) for i in ginterior),'leftArmCoverageAfterCentralExclusion':{'sourceFieldSummary':leftstats,'zeroRemainingLeftArmPhysicalIDs':zeroLeftArm,'zeroAllNoncentralPhysicalIDs':zeroNoncentral,'noncentralNonLeftArmPositiveNamedJoints':noncentralOther,'noWeightsActuallyRemoved':True,'interpretation':'Support inventory only: deleting central influences leaves listed zero-arm nodes with no left-arm support; listed zero-all-noncentral nodes would be completely unassigned and require anatomical field construction, not blind residual renormalization. Existing cuff/glove central influence is measured separately; byte-exact protected cuff fields already have no such leakage.'},'parentProposedNextRegion':{'status':'PROPOSAL_ONLY_AFTER_ACTUAL194_CONSTRUCTION_PASS','remainingOriginalLeftRootedPhysicalVertexIDs':sorted(L),'remainingOriginalLeftNodes':len(L),'newLeftCap':'Canonical-source barycentric fields only from the sole194 builder; no cap generated or adapted here. Exact new physical IDs cannot be preregistered before actual194 construction qualifies.','protection':'Preserve65 shared source cuff nodes and whole p1 glove fields to preserve join/contact baseline. If later explicitly changing any shared physical node, propagate one identical field to ALLp0/p1 UV aliases; changing p0 only breaks join. Hands/cuff/hood/head/right/lowerbody fields and all physical aliases remain protected. Source handphysics remains a motion/adapter gate; field continuity alone is not contact acceptance.','highBoundaryAmbiguity':'Keep high shared seam and crossY1.30 transition as explicit unresolved boundary; geometric root labels are not semantic bone assignments.'},'boundedFutureRegion':{'proposalOnly':True,'definition':'Remaining-original left geometric rooted component, strict 1.0<Y<1.20, excluding two retained-sublevel edge rings from exact65 shared glove/body nodes and from high frontier or original47-face fixed perimeter nodes. New194 cap excluded. Geometric selector requires anatomical review before fitting.','physicalVertexIDs':roi,'physicalVertices':len(roi),'p0AliasRows':sum(len(aliases[i]) for i in roi),'cuffProtectedIDs':sorted(cuffguard),'highBoundaryProtectedIDs':sorted(highguard),'witnessesIncluded':{str(r):int(q[r]) in roi for r in [2030,2172]},'candidateConstraints':'If reviewed as sleeve interior: zero pelvis/spine/chest/neck/head influence within this strict distal region; only shoulder.L/upperArm.L/forearm.L may be adapted, keep hand.L contribution fixed, nonnegative normalized <=4positive lanes. Keep every other physical node byte-exact, including cuff guard, high/boundary guard, glove, hood/head, right, lower body and all cap fields. Share one identical Float32 field across all physical aliases; use reviewed surface elbow/shoulder landmarks and continuous ownership objectives, no nearest-bone assignment. This is a proposed test constraint, not a declaration that geometric roots certify anatomy.','boundaryConstraint':'Fix fields at exterior guard and measure edge ownership gradient/strain across it. If fixed proximal or distal boundary makes constraint incompatible, report infeasibility of this explicit bounded region; do not silently enlarge or zero additional rows.','crossHighBoundaryAmbiguity':'Y>=1.30 is excluded and remains connected across high original attachment; new cap canonical barycentric top4 is transfer only. The central-rooted component contains unchanged right arm. Neither high rows nor whole central component has certified semantic ownership.','motionGate':'Use source2030/2172 exact IDs and guard edges; compare independently held-out asymmetric shoulder elevation/forward/elbow/twist + production lean COM/IK grip/sole contacts and gameplay/Garage blends. Freeze training vs heldout motions before fitting. Existing188 authored probes are baseline evidence, not fresh heldout generalization. Three.js stock LBS must run actual fields; bakedV7 or DQPreserveVolume does not certify stockThree volume.'},'knownRigMapping':{'actualExportedNames':actualnames,'canonicalNames':names,'nameMap':dict(zip(actualnames,names)),'canonicalNamesMatch170':True,'reference':'candidate-handoff170 mapping-report.json known19 rest mapping; source-rig188 frozen exact source185-vs34 rig diagnostic','axes':'Y up; named left positiveZ; X fore/aft in existing adapter. Preserve explicit named local-axis adapter; no nearest inferred segment labels. Existing affine legality and rest equality do not accept anatomical pivots.','existing188Source185RestExactVs34':rig188['source185ExactRestVs34'],'newBindTestsRun':0,'anatomicalAcceptance':'OPEN; choose pivots from anatomical surface evidence. Any changedrest/hierarchy/axis requires explicit bind/contact/physics adapter with named19 mapping and proof of unchanged leanCOM,IK/grip/sole behavior, rather than blindly retaining old bone positions.'},'existingWitnessEvidence':{'actual188Frames':actual['frames'],'actual188Status':actual['status'],'parent188Status':parent['status'],'parent188MinimumNecessaryStrain':parent['minimumNecessaryStrain'],'scope':'Reuse exact frozen188 actual witnesses; no clips, poses or numeric motion rerun in this audit. Tiny fixed40mm patch failure is not global impossibility.'},'limits':['This is the unsealed original-face domain, not a qualified194 reseal.','Geometric rooting and named influence leakage are field evidence, not anatomical groundtruth or a rig acceptance verdict.','No raw source, mesh, rig, weight, normal, UV, morphology, materials, motion or runtime changes. Construction must qualify before subsequent rig/weight/deformation stage; cosmetics paused.','Likedwhitebuzz head protected; three visual checkpoints and mobile/desktop behavior remain parent gates.'],'seconds':time.monotonic()-start,'anonymousGBSamples':memories,'inputs':pins}
save('report.json',report)
save('source-fields.json',{'physicalIDConvention':'np.unique(p0POSITION,axis=0) lexicographic Float32 equality','components':comps,'rootPhysicalIDs':{k:sorted(v) for k,v in roots.items()},'physicalSourceFields':physicalrecords,'leftGloveBodyCuffRecords':cuff,'leftGloveInteriorPhysicalFields':[{'glovePhysicalID':i,'gloveRows':galias[i],'positionM':GU[i].tolist(),'normalizedNamedWeights':named(GPN[i])} for i in ginterior],'remainingOriginalSublevelHighFrontierIDs':sorted(frontier)})
fields=E/'source-fields.json'
(E/'source-fields.json.gz').write_bytes(gzip.compress(fields.read_bytes(),mtime=0)); fields.unlink()
for p,d in pins.items(): assert sha(Path(p).read_bytes())==d['sha256']
print(json.dumps({'seconds':report['seconds'],'components':[(r['componentID'],r['physicalVertices'],r['rootLabels']) for r in componentstats],'leftCentralWeights':{n:componentstats[leftid]['namedJointInventory'][n] for n in centralnames},'witness':witness,'edge':report['witnessEdge'],'aliases':report['physicalAliases'],'cuff':report['leftGloveBodyCuff'],'ROI':{'nodes':len(roi),'witness':report['boundedFutureRegion']['witnessesIncluded']}}))
