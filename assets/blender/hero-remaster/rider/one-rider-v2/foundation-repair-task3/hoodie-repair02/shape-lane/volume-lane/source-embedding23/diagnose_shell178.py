"""Read-only authored sewing/panel diagnosis. No original builder mutations."""
from pathlib import Path
import json,hashlib,sys,numpy as np
from collections import defaultdict,Counter
HERE=Path(__file__).resolve().parent;LANE=HERE.parent;sys.path.insert(0,str(LANE));from chart_labels import ROOT,POS,U,SourceCharts
SRC=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/drafted-raglan');CODE=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/clean-upper-shell01/drafted-raglan');EVID=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/drafted-raglan');raw=np.load(SRC/'drafted-shell01.npz');P=raw['p'];T=raw['f'];panels=raw['panel'];Q=P[T];area=np.linalg.norm(np.cross(Q[:,1]-Q[:,0],Q[:,2]-Q[:,0]),axis=1);edges=defaultdict(list)
for fi,t in enumerate(T):
 for a,b in zip(t,np.roll(t,-1)):edges[tuple(sorted((int(a),int(b))))].append(fi)
non=[]
for e,faces in edges.items():
 if len(faces)>2:non.append({'edgeVertices':list(e),'positionsBlenderM':P[list(e)].tolist(),'lengthM':float(np.linalg.norm(P[e[1]]-P[e[0]])),'incidence':len(faces),'faces':faces,'panels':[str(panels[i])for i in faces],'doubleAreaM2':[float(area[i])for i in faces]})
deg=np.flatnonzero(area<1e-12);degParents={}
for i in deg:degParents.setdefault(int(i//25),[]).append(int(i))
# Exact boundary nodes lying strictly inside another indexed boundary edge:
# these are hanging seam nodes even when coordinate-round weld finds noID.
boundary=[e for e,fs in edges.items()if len(fs)==1];boundaryIDs=np.unique(boundary);hang=[]
for a,b in boundary:
 ab=P[b]-P[a];ll=float(ab@ab)
 if ll<1e-16:continue
 par=np.einsum('ij,j->i',P[boundaryIDs]-P[a],ab)/ll;perp=np.linalg.norm(P[boundaryIDs]-(P[a]+par[:,None]*ab),axis=1);ids=boundaryIDs[(par>1e-5)&(par<1-1e-5)&(perp<2e-7)]
 if len(ids):hang.append({'boundaryEdge':[int(a),int(b)],'panel':str(panels[edges[(a,b)][0]]),'strictInteriorNodes':ids.tolist(),'maxPerpendicularDistanceM':float(perp[np.isin(boundaryIDs,ids)].max()),'edgeLengthM':float(np.sqrt(ll))})
# Original literal witnesses are attribution input, not rerun here.
literal=json.loads((EVID/'literal-audit.json').read_text());print('literalkeys',list(literal),flush=True)
# Read existing 8pairs regardless nested schema, preserve sourcewitness fields.
def lists(d):
 if isinstance(d,dict):
  for k,v in d.items():
   if isinstance(v,list)and any(x in k.lower()for x in ['cross','pair','witness']):yield k,v
   yield from lists(v)
 elif isinstance(d,list):
  for v in d:yield from lists(v)
existing=list(lists(literal));crossSummary=[]
for key,v in existing:
 if v:crossSummary.append({'field':key,'count':len(v),'firstRecords':v[:8]})
c=SourceCharts();sourcePrimitive2Bounds={'minGLTF':POS[2].min(0).tolist(),'maxGLTF':POS[2].max(0).tolist()};cuffStats=[]
for sg,side in [(1,'L'),(-1,'R')]:
 ids=c.cuff[U[c.cuff,2]*sg>0];p=U[ids];cuffStats.append({'side':side,'sourceAliasCount':len(ids),'sourceBoundsGLTFM':{'min':p.min(0).tolist(),'max':p.max(0).tolist()},'newDraftCuffGLTFM':'Y=.925, lateralZ in[.315,.385] forboth sides; forwardX=.72front/.555back. New ring is a rectangular draftedopening; source ring is irregular. No explicitsource correspondence or physicalsew.'})
rows={'status':'READONLY AUTHORED PANEL DIAGNOSIS; sole builder remains original clean_shell_draft178','sourceHashes':{str(p):hashlib.sha256(p.read_bytes()).hexdigest()for p in [SRC/'drafted-shell01.npz',SRC/'shell01.glb',CODE/'build.py',CODE/'assemble.py',EVID/'construction.json',EVID/'literal-audit.json']},'authoredCounts':{'vertices':len(P),'triangles':len(T),'boundaryEdges':len(boundary),'nonmanifoldEdges':len(non),'zeroAreaBelow1e-12':len(deg),'zeroAreaPanels':dict(Counter(str(panels[i])for i in deg))},'nonmanifoldWitnesses':non,'degenerateFaces':deg.tolist(),'degenerate25SubtriangleParentGroups':degParents,'hangingBoundaryNodeWitnesses':hang,'existingLiteralCrossingAttributionInput':crossSummary,'sewingMechanism':'build.panel independently subdivides every tessellated parent triangle withn=5 then welds by rounded3D coordinates. It has noexplicitglobal seam edge parameterization/split registry. Any collinear parent ear creates25degenerate child triangles and coincidentedgefans; mismatchedfloat-rounding/subdivision can leave seam Tjunctions despite visualsharedpoints. Diagnose exactwitnesses above, no blanketrigging/normalfix.','fixDirection':'Remove collinear boundary vertices or reject zero-area tessellation ears BEFORE subdivision. Shareexplicit seam node arrays betweenpanels, triangulate against constrainedsourceoftruth splits, then manifold/winding/area/literalgate. Do notweld arbitrarynearby cloth layers to hide crossings.','semanticRisks':{'primitive2NotHoodOnly':sourcePrimitive2Bounds,'assemblyRetainsEntirePrimitive2':'assemble.py retains primitive2 wholesale while callinghood. Sourceprimitive2 includes sewncloth/bodyinsert belowhood; its whole lowerY range and originaltriangles mustbechecked againstnewshirt/lowerretainedmesh. Protect actualhoodfaces using semanticgeometric/topologicalinventory, notprimitive-numbername.','originalCuffAttachment':cuffStats,'hem':'assembly.py keepsprimitive0 triangles allcornersY<=.965, a flatheightmask. Existing actualhoodie/jeans interface is fragmented and nonplanar; this leaves indexedboundary thatrequiresorderedreviewedcycle and explicitnewhemattachment/cap, not assumedphysicallyjoined.','neck':'Front neckline isnotchcentreheight1.435 vsback1.490, oldheadincludesrigidlowerneck andprotectedhoodprimitive2separate. No physicalhoodjoin oractualsourceedgecorrespondence authoredyet.','namespace':'Blender sourcepanel coordinatesXforward/Ylateral/Zheight export toglTF Xforward/Yheight/Z−lateral. Preserve explicitnode transforms inrest export before 19bone attachment; unriggedshell has no skin contract.'},'limits':'No originaledits/buildexecution/renders, no newweights orrigging. IndependentQA owns actualGLB strictcrossings/gaps/protectedassembly; this reportonlyauthoredpanelandseam witnessdiagnosis.'}
(HERE/'continuous-shell178-readonly-diagnosis.json').write_text(json.dumps(rows,indent=2));print(json.dumps({'nonmanifold':non,'degeneratePanels':rows['authoredCounts']['zeroAreaPanels'],'degenerateParents':degParents,'hangingBoundaryNodeEdges':len(hang),'sourcePrimitive2':sourcePrimitive2Bounds,'sourceCuffs':cuffStats,'crossInput':crossSummary},indent=2))
