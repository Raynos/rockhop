"""Read-only literal source / frozen194 extrinsic audit. Never generates a mesh."""
from pathlib import Path
from fractions import Fraction as Q
from collections import Counter,defaultdict
import ast,hashlib,json,struct,time,re,subprocess,os
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');E=R/'docs/evidence/hero-remaster/one-rider-v2/extrinsic-seam195';start=time.monotonic();pins={};mem=[]
sha=lambda b:hashlib.sha256(b).hexdigest()
def read(p,expected=None):
 p=Path(p);b=p.read_bytes();h=sha(b);assert expected is None or h==expected;(pins.update({str(p):{'sha256':h,'bytes':len(b)}}));return b
def save(name,v):
 (E/name).write_text(json.dumps(v,indent=2,default=lambda x:x.tolist() if isinstance(x,np.ndarray) else x.item() if isinstance(x,np.generic) else str(x))+'\n')
def check():
 assert time.monotonic()-start<580
 v=subprocess.check_output(['vm_stat'],text=True);p=int(re.search(r'page size of (\d+)',v).group(1));g=int(re.search(r'Anonymous pages:\s+(\d+)',v).group(1))*p/1e9;assert g<70;mem.append(g)
source=B/'source-preserving-garment185/operator/rider.glb';sourceSHA='ffb9ec5acaca7c5e60b732d88e9313b7c337f3058a32dec2fda0170f634281c5';read(source,sourceSHA)
reader=R/'assets/blender/hero-remaster/rider/one-rider-v2/source-preserving-garment185/operator.py';tree=ast.parse(read(reader));exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='GLB'],type_ignores=[]),str(reader),'exec'))
C=GLB(source,sourceSHA);a,F=C.primitive(0,0);U,q=np.unique(a['POSITION'],axis=0,return_inverse=True);PF=q[F];T=U[PF].astype(float)
npz=B/'source-ruled194/construction.npz';read(npz,'ee45bb5e0e9612c9b8a3e7ac433fc02824f5ebff319f8da0217692164dd69777');z=np.load(npz)
pr=json.loads(read(B/'source-ruled194/construction-provenance.json'));witness=json.loads(read(B/'source-ruled194/rest-crossing-evidence.json'));parent194=json.loads(read(R/'docs/evidence/hero-remaster/one-rider-v2/source-ruled194/parent-review.json'));star=json.loads(read(R/'docs/evidence/hero-remaster/one-rider-v2/physical-cut193/parent-review.json'));contract=json.loads(read(R/'docs/evidence/hero-remaster/one-rider-v2/physical-cut193/parent-construction-contract.json'));comparison=json.loads(read(B/'physical-cut193/domain-source-comparison.json'));seam191=json.loads(read(B/'source-seam191/next-construction-contract.json'))
def sub(a,b):return tuple(x-y for x,y in zip(a,b))
def dot(a,b):return sum(x*y for x,y in zip(a,b))
def cross(a,b):return (a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0])
def exact(v):return tuple(Q(float(x)) for x in v)
def addscaled(a,d,t):return tuple(x+t*y for x,y in zip(a,d))
def bary(p,t):
 n=cross(sub(t[1],t[0]),sub(t[2],t[0]));den=dot(n,n);assert den
 return (dot(cross(sub(t[1],p),sub(t[2],p)),n)/den,dot(cross(sub(t[2],p),sub(t[0],p)),n)/den,dot(cross(sub(t[0],p),sub(t[1],p)),n)/den)
def intersect(A,B,tri):
 # Exact arithmetic on literal binary Float32 coordinates. Includes coplanar intervals.
 n=cross(sub(tri[1],tri[0]),sub(tri[2],tri[0]));da=dot(n,sub(A,tri[0]));db=dot(n,sub(B,tri[0]));d=sub(B,A)
 if da!=db:
  t=da/(da-db)
  if not 0<=t<=1:return []
  p=addscaled(A,d,t);bc=bary(p,tri)
  return [(t,t,p,bc)] if min(bc)>=0 else []
 if da:return []
 b0=bary(A,tri);b1=bary(B,tri);lo=Q(0);hi=Q(1)
 for x,y in zip(b0,b1):
  slope=y-x
  if slope>0:lo=max(lo,-x/slope)
  elif slope<0:hi=min(hi,-x/slope)
  elif x<0:return []
 if lo>hi:return []
 t=(lo+hi)/2;p=addscaled(A,d,t);return [(lo,hi,p,bary(p,tri))]
def chord(ids,removed):
 A,B=U[ids].astype(float);keep=[i for i in range(len(F)) if i not in set(removed)];lo=np.minimum(A,B);hi=np.maximum(A,B);near=[i for i in keep if (T[i].max(0)>=lo).all() and (T[i].min(0)<=hi).all()];hits=[]
 for fi in near:
  for t0,t1,p,bc in intersect(exact(A),exact(B),tuple(map(exact,T[fi]))):
   endpoint=t0==t1 and t0 in [0,1];shared=endpoint and ids[int(t0)] in PF[fi]
   kind='shared_endpoint_contact' if shared else 'nonshared_endpoint_contact' if endpoint else 'coplanar_interval' if t0<t1 else 'strict_segment_and_triangle_interior' if min(bc)>0 else 'segment_interior_triangle_edge_contact'
   hits.append({'sourceFace':fi,'kind':kind,'segmentParameterExact':[str(t0),str(t1)],'segmentParameter':[float(t0),float(t1)],'positionM':list(map(float,p)),'triangleBarycentrics':list(map(float,bc))})
 return {'endpointPhysicalIDs':ids,'endpointPositionsM':U[ids].tolist(),'retainedSourceFacesChecked':len(keep),'AABBCandidates':len(near),'counts':dict(Counter(x['kind'] for x in hits)),'intersections':hits}
normalPath=E/'parent-normal-diagnosis.json';normalDiagnosis=json.loads(read(normalPath)) if normalPath.exists() else None
check();chords={'source47_194':chord([1420,13550],contract['exactRemovedSourceFaceIDs']),'sourceStar168':chord([1488,13448],star['removedSourceFaceIDs'])};save('literal-chords.json',chords)
# Existing source polylines only: interpolated arc evaluation is diagnostic, never output geometry.
def arcrecord(ids):
 p=U[ids].astype(float);d=np.diff(p,axis=0);length=np.linalg.norm(d,axis=1);s=np.r_[0,np.cumsum(length)]/sum(length)
 return {'ids':ids,'p':p,'s':s,'length':float(sum(length))}
def serialarc(v):
 d=np.diff(v['p'],axis=0);return {'physicalIDs':v['ids'],'positionsM':v['p'].tolist(),'sourceArcLengthM':v['length'],'normalizedArcStations':v['s'].tolist(),'negativeXSteps':[(i,float(x)) for i,x in enumerate(d[:,0]) if x<0],'axisRangesM':[[float(v['p'][:,i].min()),float(v['p'][:,i].max())] for i in range(3)]}
def evalarc(v,u):return np.array([np.interp(u,v['s'],v['p'][:,i]) for i in range(3)])
loop=star['orientedFillBoundaryPhysicalIDs'];i=loop.index(1488);l=loop[i:]+loop[:i];j=l.index(13448);stararcs=[l[:j+1],[l[0]]+list(reversed(l[j:]))]
# Correct reversed arc includes the far endpoint once.
stararcs[1]=[1488]+list(reversed(l[j:]))
arcs194={k:arcrecord(v['physicalIDs']) for k,v in contract['arcCorrespondence'].items()};arcs168={str(i):arcrecord(ids) for i,ids in enumerate(stararcs)}
def comparearcs(arcs,endpoints):
 vals=list(arcs.values());us=sorted(set(np.r_[vals[0]['s'],vals[1]['s']]));rows=[]
 for u in us:
  p0=evalarc(vals[0],u);p1=evalarc(vals[1],u);ch=(1-u)*U[endpoints[0]]+u*U[endpoints[1]]
  rows.append({'u':float(u),'arc0M':p0.tolist(),'arc1M':p1.tolist(),'sameStationDeltaX_M':float(p1[0]-p0[0]),'sameStationDeltaZ_M':float(p1[2]-p0[2]),'chordMinusArcZ_M':[float(ch[2]-p0[2]),float(ch[2]-p1[2])]})
 valsz=[x['sameStationDeltaZ_M'] for x in rows[1:-1]];valx=[x['sameStationDeltaX_M'] for x in rows[1:-1]]
 return {'arcs':{k:serialarc(v) for k,v in arcs.items()},'sourceStations':rows,'interiorZSideCounts':dict(Counter('positive' if x>0 else 'negative' if x<0 else 'equal' for x in valsz)),'interiorDeltaZRangeM':[min(valsz),max(valsz)],'interiorDeltaXRangeM':[min(valx),max(valx)]}
arcdata={'source47_194':comparearcs(arcs194,[1420,13550]),'sourceStar168':comparearcs(arcs168,[1488,13448]),'sourceSeam191':serialarc(arcrecord(seam191['orderedProspectiveSeamPhysicalIDs']))};save('source-arc-shapes.json',arcdata)
boundary168=set(star['orientedFillBoundaryPhysicalIDs']);faces168=PF[star['removedSourceFaceIDs']];interior168=sorted(set(map(int,faces168.ravel()))-boundary168);loop168=star['orientedFillBoundaryPhysicalIDs'];perimeter168={tuple(sorted((i,j))) for i,j in zip(loop168,loop168[1:]+loop168[:1])};edges168={tuple(sorted((int(t[k]),int(t[(k+1)%3])))) for t in faces168 for k in range(3)};nonperimeter168=[e for e in edges168 if set(e)<=boundary168 and e not in perimeter168];path191=seam191['orderedProspectiveSeamPhysicalIDs'];neighbors4041=sorted({j if i==4041 else i for i,j in edges168 if 4041 in [i,j]});starGraph={'sourceFaces':168,'sourceInteriorPhysicalIDs':interior168,'interiorCount':len(interior168),'interiorEquals45PathPlus4041':set(interior168)==set(path191)|{4041},'boundaryOnlySourceTriangles':[int(fi) for fi in star['removedSourceFaceIDs'] if set(PF[fi])<=boundary168],'nonperimeterBoundaryToBoundaryEdges':nonperimeter168,'source4041NeighborPhysicalIDs':neighbors4041};save('source-star-graph.json',starGraph)
# Literal original Star168 XZ projection, never proposed Y coordinates.
def c2(a,b):return a[0]*b[1]-a[1]*b[0]
def clip2(poly,tri):
 for i in range(3):
  a,b=tri[i],tri[(i+1)%3];edge=sub(b,a);out=[]
  if not poly:break
  for j,P in enumerate(poly):
   V=poly[(j+1)%len(poly)];dP=c2(edge,sub(P,a));dV=c2(edge,sub(V,a));inP=dP>=0;inV=dV>=0
   if inP:out.append(P)
   if inP!=inV:out.append(addscaled(P,sub(V,P),dP/(dP-dV)))
  poly=[]
  for p in out:
   if not poly or p!=poly[-1]:poly.append(p)
  if len(poly)>1 and poly[0]==poly[-1]:poly.pop()
 return poly
projection=[];positive=[];areas=[];p2=[]
for fi in star['removedSourceFaceIDs']:
 tri=tuple(tuple(Q(float(v)) for v in p[[0,2]]) for p in T[fi]);area=c2(sub(tri[1],tri[0]),sub(tri[2],tri[0]))/2;areas.append(area);p2.append(tri if area>=0 else (tri[0],tri[2],tri[1]));projection.append({'sourceFace':fi,'signedOriginalXZAreaM2':float(area),'signedOriginalXZAreaExact':str(area)})
for i in range(168):
 for j in range(i+1,168):
  if areas[i]==0 or areas[j]==0:continue
  aa=T[star['removedSourceFaceIDs'][i]][:,[0,2]];bb=T[star['removedSourceFaceIDs'][j]][:,[0,2]]
  if np.any(aa.max(0)<bb.min(0)) or np.any(bb.max(0)<aa.min(0)):continue
  poly=clip2(list(p2[i]),p2[j]);area=abs(sum(c2(poly[k],poly[(k+1)%len(poly)]) for k in range(len(poly))))/2 if len(poly)>=3 else Q(0)
  if area>0:positive.append({'sourceFaceIDs':[star['removedSourceFaceIDs'][i],star['removedSourceFaceIDs'][j]],'sharedSourcePhysicalVertices':len(set(faces168[i])&set(faces168[j])),'originalXZInteriorOverlapM2':float(area),'originalXZInteriorOverlapExact':str(area)})
 check()
xz={'sourceFaces':168,'signedAreaCounts':{'positive':sum(x>0 for x in areas),'negative':sum(x<0 for x in areas),'zero':sum(x==0 for x in areas)},'absoluteAreaRangeM2':[float(min(abs(x) for x in areas)),float(max(abs(x) for x in areas))],'positiveInteriorOverlapPairs':len(positive),'overlapPairSharedCornerCounts':dict(Counter(x['sharedSourcePhysicalVertices'] for x in positive)),'fixedXZIsSingleValuedGraph':not positive and all(x!=0 for x in areas),'signedOriginalXZAreas':projection,'overlaps':positive,'meaning':'Projection only. Original source may be multilayer in XZ; these overlaps do not prove 3D collisions. No prospective Y coordinates created.'};save('source-star-xz-projection.json',xz)
aliases={str(pid):{'originalSourceAccessorRows':np.flatnonzero(q==pid).tolist(),'removedSourceCornerRows':sorted({int(row) for fi in star['removedSourceFaceIDs'] for row in F[fi] if q[row]==pid}),'incidentRetainedSourceFaceIDs':[int(fi) for fi in range(len(F)) if fi not in set(star['removedSourceFaceIDs']) and pid in PF[fi]]} for pid in interior168};save('source-interior-aliases.json',{'exact46PhysicalIDs':interior168,'sourceRowAliases':aliases,'originalRowsRemainImmutable':True,'newAliasesAppendOnlyNextTrial':True})
# At exact actual triangle-crossing endpoints, recover frozen194 reference coordinates.
fr=pr['fragments'];newT=z['physicalPositions'][z['newPhysicalTriangles']].astype(float)
def param(ti,point):
 bc=np.array(list(map(float,bary(point,tuple(map(exact,newT[ti]))))));corners=np.array([[float(Q(int(n),int(d))) for n,d in p] for p in fr[ti]['referenceCorners']]);uv=bc@corners;arc=arcs194[fr[ti]['panel']];boundaryY=np.interp(uv[0],arc['s'],np.sin(np.pi*arc['s']))*(-1 if fr[ti]['panel']=='central' else 1);radial=1-uv[1]/boundaryY if abs(boundaryY)>1e-14 else None
 sourceBC=bc@np.array(fr[ti]['sourceBarycentrics']);sourcePoint=sourceBC@T[fr[ti]['sourceFace']];normal=np.cross(T[fr[ti]['sourceFace'],1]-T[fr[ti]['sourceFace'],0],T[fr[ti]['sourceFace'],2]-T[fr[ti]['sourceFace'],0]);normal/=np.linalg.norm(normal); displacement=np.array(list(map(float,point)))-sourcePoint
 return {'sourceCorrespondencePositionM':sourcePoint.tolist(),'sourceDisplacementM':float(np.linalg.norm(displacement)),'sourceDisplacementDotFaceNormal_M':float(displacement@normal),'newTriangle':ti,'panel':fr[ti]['panel'],'baseTriangle':fr[ti]['baseTriangle'],'radialBand':pr['baseTriangles'][fr[ti]['baseTriangle']]['radialBand'],'sourceFace':fr[ti]['sourceFace'],'sourceChart':fr[ti]['sourceChart'],'candidateBarycentrics':bc.tolist(),'referenceUV':uv.tolist(),'radialFraction':None if radial is None else float(radial)}
records=[];categories=Counter();bands=defaultdict(Counter);negativeNormal=Counter();deltaNormals=[]
for wi,w in enumerate(witness['strictCrossings']):
 pair=w['ancestry'];tris=np.array(w['trianglesM']);pts=[]
 for rev in [False,True]:
  aa,bb=(tris[1],tris[0]) if rev else (tris[0],tris[1]);qb=tuple(map(exact,bb))
  for k in range(3):
   for _,_,p,bc in intersect(exact(aa[k]),exact(aa[(k+1)%3]),qb):
    if p not in pts:pts.append(p)
 assert pts,(wi,w)
 cls=tuple('retained' if x['newTriangle'] is None else fr[x['newTriangle']]['panel'] for x in pair);key=' / '.join(cls);categories[key]+=1;pars=[]
 for p in pts:
  at=[param(x['newTriangle'],p) for x in pair if x['newTriangle'] is not None];pars.append({'positionM':list(map(float,p)),'candidateParameters':at})
 for x in pair:
  if x['newTriangle'] is not None:bands[key][str(pr['baseTriangles'][fr[x['newTriangle']]['baseTriangle']]['radialBand'])]+=1
 rec={'witness':wi,'pairClass':key,'ancestry':pair,'intersectionEndpoints':pars}
 if 'retained' in cls:
  ri=cls.index('retained');fi=pair[ri]['sourceFace'];n=np.cross(T[fi,1]-T[fi,0],T[fi,2]-T[fi,0]);n/=np.linalg.norm(n);nt=pair[1-ri]['newTriangle'];nf=fr[nt];src=T[nf['sourceFace']];nn=np.cross(src[1]-src[0],src[2]-src[0]);nn/=np.linalg.norm(nn);dotn=float(n@nn);negativeNormal['opposed' if dotn<0 else 'aligned']+=1;deltaNormals.append(dotn);rec['retainedFaceNormal']=n.tolist();rec['newProvenanceSourceFaceNormal']=nn.tolist();rec['sourceNormalDot']=dotn
 records.append(rec)
 check()
save('actual-crossing-parameters.json',{'strictWitnesses':records,'counts':dict(categories),'bands':{k:dict(v) for k,v in bands.items()},'retainedVersusNewProvenanceNormalSigns':dict(negativeNormal),'normalDotRange':[min(deltaNormals),max(deltaNormals)]})
stationGaps=[]
for rec in records:
 if rec['pairClass']=='central / lateral':
  pts=[e['positionM'] for e in rec['intersectionEndpoints']];mid=tuple(Q(float(x)) for x in np.mean(pts,axis=0));pp=[param(x['newTriangle'],mid) for x in rec['ancestry']];stationGaps.append({'witness':rec['witness'],'midpointM':list(map(float,mid)),'centralU':pp[0]['referenceUV'][0],'lateralU':pp[1]['referenceUV'][0],'lateralMinusCentralU':pp[1]['referenceUV'][0]-pp[0]['referenceUV'][0]})
save('panel-station-mismatch.json',{'all30ActualCrossings':stationGaps,'midpointGapRange':[min(x['lateralMinusCentralU'] for x in stationGaps),max(x['lateralMinusCentralU'] for x in stationGaps)],'strictlyPositiveMidpointGaps':sum(x['lateralMinusCentralU']>0 for x in stationGaps)})
summary={}
for cls in categories:
 rr=[r for r in records if r['pairClass']==cls];params=[p for r in rr for e in r['intersectionEndpoints'] for p in e['candidateParameters']];summary[cls]={'pairs':len(rr),'referenceURange':[min(x['referenceUV'][0] for x in params),max(x['referenceUV'][0] for x in params)],'radialRange':[min(x['radialFraction'] for x in params if x['radialFraction'] is not None),max(x['radialFraction'] for x in params if x['radialFraction'] is not None)],'radialBandCounts':dict(bands[cls]),'sourceCorrespondenceDisplacementMRange':[min(x['sourceDisplacementM'] for x in params),max(x['sourceDisplacementM'] for x in params)],'sourceDisplacementDotFaceNormalMRange':[min(x['sourceDisplacementDotFaceNormal_M'] for x in params),max(x['sourceDisplacementDotFaceNormal_M'] for x in params)]}
# Direction of the literal194 chord from each fixed edge midpoint in each retained face normal.
directions=[]
for x in comparison['physicalMincut47']['boundarySourceAncestry']:
 ids=x['removedDirectedPhysicalEdge'];panel=next(k for k,v in arcs194.items() if any(set(ids)==set(e) for e in zip(v['ids'],v['ids'][1:])));v=arcs194[panel];j=next(i for i,e in enumerate(zip(v['ids'],v['ids'][1:])) if set(ids)==set(e));u=float((v['s'][j]+v['s'][j+1])/2);mid=U[ids].astype(float).mean(0);target=(1-u)*U[1420]+u*U[13550];n=np.array(x['retainedSourceNormal']);signed=float((target-mid)@n);directions.append({'panel':panel,'edgePhysicalIDs':ids,'retainedSourceFace':x['retainedSourceFace'],'u':u,'toward194ChordDotRetainedNormal_M':signed})
save('boundary-source-directions.json',{'sourceFaceNormalsNotNormalAttributes':True,'edgeDirections':directions,'countsByPanel':{p:dict(Counter('positive' if x['toward194ChordDotRetainedNormal_M']>0 else 'negative' for x in directions if x['panel']==p)) for p in arcs194}})
check()
report={'status':'READONLY_EXTRINSIC_DIAGNOSIS_NO_NEW_GEOMETRY','geometryAttempts':0,'sourceStarXZProjectionSummary':{k:xz[k] for k in ['signedAreaCounts','absoluteAreaRangeM2','positiveInteriorOverlapPairs','overlapPairSharedCornerCounts','fixedXZIsSingleValuedGraph']},'sourceStarGraph':starGraph,'parentNumericNormalDiagnosisReference':str(normalPath) if normalDiagnosis is not None else None,'source185SHA256':sourceSHA,'frozen194SHA256':pins[str(npz)]['sha256'],'continuousExactChordIntersections':{k:{kk:v[kk] for kk in ['endpointPhysicalIDs','retainedSourceFacesChecked','AABBCandidates','counts']} for k,v in chords.items()},'actual127PairParameterSummary':summary,'arcOrdering':{k:{kk:v[kk] for kk in ['interiorZSideCounts','interiorDeltaZRangeM','interiorDeltaXRangeM']} for k,v in arcdata.items() if k!='sourceSeam191'},'boundaryDirections':{p:dict(Counter('positive' if x['toward194ChordDotRetainedNormal_M']>0 else 'negative' for x in directions if x['panel']==p)) for p in arcs194},'centralLateralStationMidpointGapRange':[min(x['lateralMinusCentralU'] for x in stationGaps),max(x['lateralMinusCentralU'] for x in stationGaps)],'centralLateralStrictlyPositiveStationGaps':sum(x['lateralMinusCentralU']>0 for x in stationGaps),'normalSigns':dict(negativeNormal),'normalDotRange':[min(deltaNormals),max(deltaNormals)],'CPUThreads':2,'GPU':False,'elapsedSeconds':time.monotonic()-start,'anonymousGBSamplesSummary':{'count':len(mem),'minimum':min(mem),'maximum':max(mem)},'inputPins':pins,'limits':['Exact source chord audit and frozen failed triangle diagnosis only; no cap or patch generated','All garment visual/basicpose/gameplay/contact/mobile gates remain OPEN','Normal-source numeric policy is independently owned by parent']}
for p,v in pins.items():assert sha(Path(p).read_bytes())==v['sha256']
save('report.json',report);print(json.dumps(report,indent=2))
