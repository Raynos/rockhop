"""Numeric continuous collision events on a reconstructed chord, not iterates."""
import hashlib,json,time
from pathlib import Path
import numpy as np
root=Path(__file__).resolve().parents[6];ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';out=ev/'neck-interface103';qa=root/'docs/evidence/hero-remaster/user-agent3-qa-2026-10-03'
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();path=out/'path-samples.json';receipt=json.loads(path.read_text());archive=out/'path-geometry-and-candidates.npz';assert sha(archive)==receipt['archiveSHA256'];data=np.load(archive);P0=data['P0'];D=data['P1']-P0;mapping=data['rawPhysicalMap'];NB=len(data['bodyReferenceTriangles']) if False else 9219;upper=receipt['introducedEventUpperAlpha']
tri={'body':mapping[:NB][data['bodyReferenceTriangles']],'head':mapping[NB:][data['headReferenceTriangles']]};rawtri={'body':data['bodyReferenceTriangles'],'head':data['headReferenceTriangles']};families={'bodySelf':('body','body'),'headSelf':('head','head'),'bodyHead':('body','head')}
def proper(A,B):
 for s,t in [(A,B),(B,A)]:
  a,b,c=t;n=np.cross(b-a,c-a);length=np.linalg.norm(n)
  if length<1e-20:continue
  n/=length;u=b-a;v=c-a;aa=u@u;ab=u@v;bb=v@v;det=aa*bb-ab*ab
  for i,j in [(0,1),(1,2),(2,0)]:
   x,y=s[i],s[j];dx=(x-a)@n;dy=(y-a)@n
   if dx*dy>=0 or min(abs(dx),abs(dy))<=1e-10:continue
   q=x+(y-x)*(dx/(dx-dy));e=q-a;bx=((e@u)*bb-(e@v)*ab)/det;by=((e@v)*aa-(e@u)*ab)/det
   if bx>=-1e-9 and by>=-1e-9 and bx+by<=1+1e-9:return True
 return False
def det(a,b,c):return float(np.dot(a,np.cross(b,c)))
def coefficients(a,b,c):
 a0,ad=a;b0,bd=b;c0,cd=c
 return np.array([det(a0,b0,c0),det(ad,b0,c0)+det(a0,bd,c0)+det(a0,b0,cd),det(ad,bd,c0)+det(ad,b0,cd)+det(a0,bd,cd),det(ad,bd,cd)])
def roots(c):
 last=len(c)-1
 while last>0 and c[last]==0:last-=1
 if not np.any(c):return [],True
 if last==0:return [],False
 vals=np.polynomial.polynomial.polyroots(c[:last+1]);return [float(v.real) for v in vals if abs(v.imag)<1e-8 and -1e-12<=v.real<=upper+1e-12],False
# Persistent coplanar features can enter by endpoint/edge collinearity.
def collinearity(p,a,b):
 u0=p[0]-a[0];ud=p[1]-a[1];v0=b[0]-a[0];vd=b[1]-a[1]
 c=np.array([np.cross(u0,v0),np.cross(ud,v0)+np.cross(u0,vd),np.cross(ud,vd)]).T
 component=int(np.argmax(np.linalg.norm(c,axis=1)));values,zero=roots(c[component])
 if zero:
  # Always-collinear endpoint events; static coincidences are explicit.
  events=[]
  for endpoint in [a,b]:
   e0=p[0]-endpoint[0];ed=p[1]-endpoint[1];k=int(np.argmax(np.abs(ed)))
   if ed[k]!=0:
    t=-e0[k]/ed[k]
    if -1e-12<=t<=upper+1e-12:events.append(float(t))
  return events,True
 return values,False

def pair_events(ap,ad,bp,bd):
 pointsA=[(ap[i],ad[i]) for i in range(3)];pointsB=[(bp[i],bd[i]) for i in range(3)];events=[0.,upper];zero_features=0;unresolved=False
 for S,T in [(pointsA,pointsB),(pointsB,pointsA)]:
  for p in S:
   a=(p[0]-T[0][0],p[1]-T[0][1]);b=(T[1][0]-T[0][0],T[1][1]-T[0][1]);c=(T[2][0]-T[0][0],T[2][1]-T[0][1]);vals,zero=roots(coefficients(a,b,c));events.extend(vals)
   if zero:
    zero_features+=1
    for i,j in [(0,1),(1,2),(2,0)]:
     vals,always=collinearity(p,T[i],T[j]);events.extend(vals)
     if always:unresolved=True
 for i,j in [(0,1),(1,2),(2,0)]:
  for k,l in [(0,1),(1,2),(2,0)]:
   a=(ap[j]-ap[i],ad[j]-ad[i]);b=(bp[l]-bp[k],bd[l]-bd[k]);c=(bp[k]-ap[i],bd[k]-ad[i]);vals,zero=roots(coefficients(a,b,c));events.extend(vals)
   if zero:
    zero_features+=1
    for p,s,t in [(pointsA[i],pointsB[k],pointsB[l]),(pointsA[j],pointsB[k],pointsB[l]),(pointsB[k],pointsA[i],pointsA[j]),(pointsB[l],pointsA[i],pointsA[j])]:
     vals,always=collinearity(p,s,t);events.extend(vals)
     if always:unresolved=True
 events=sorted(set(max(0.,min(upper,t)) for t in events));return events,zero_features,unresolved
start=time.monotonic();summary={};all_entries=[];unresolved_rows=[]
for kind,(a,b) in families.items():
 rows=data[kind+'SweptNewPairs'];entries=[];zero_count=0;unresolved_count=0
 for index,(i,j) in enumerate(rows):
  ai,bj=tri[a][i],tri[b][j];ap,ad,bp,bd=P0[ai],D[ai],P0[bj],D[bj];events,zero,unresolved=pair_events(ap,ad,bp,bd);zero_count+=zero
  if unresolved:unresolved_count+=1;unresolved_rows.append({'kind':kind,'triangleIDs':[int(i),int(j)]})
  for left,right in zip(events[:-1],events[1:]):
   if right<=left+1e-14:continue
   mid=(left+right)/2
   if proper(ap+mid*ad,bp+mid*bd):
    row={'kind':kind,'triangleIDs':[int(i),int(j)],'onsetRootAlpha':left,'nextEventAlpha':right,'properInteriorWitnessAlpha':mid,'physicalNodesByFace':[ai.tolist(),bj.tolist()],'nativeVerticesByFace':[rawtri[a][i].tolist(),rawtri[b][j].tolist()],'persistentCoplanarFeatureCount':zero,'alwaysCollinearFeaturePresent':unresolved};entries.append(row);all_entries.append(row);break
  if index%2000==0:print('CCD_PROGRESS',kind,index,len(rows),flush=True)
 entries.sort(key=lambda r:r['onsetRootAlpha']);summary[kind]={'sweptNonStartingPairs':len(rows),'numericIntroducedEntriesThroughUpperBound':len(entries),'persistentCoplanarFeatures':zero_count,'pairsWithAlwaysCollinearFeatures':unresolved_count,'earliestNumericEntry':entries[0] if entries else None}
all_entries.sort(key=lambda r:r['onsetRootAlpha']);earliest=all_entries[0] if all_entries else None
# Candidate onset is geometric contact; retained proper classifier has strict1e-10m plane distances.
report={'status':'NUMERIC_CHORD_EVENT_DIAGNOSTIC_NOT_SOLVER_CHRONOLOGY_OR_GLOBAL_FEASIBILITY_PROOF','recipeSHA256':sha(__file__),'pathReceiptSHA256':sha(path),'archiveSHA256':sha(archive),'pathUpperAlpha':upper,'elapsedS':time.monotonic()-start,'methods':['Swept endpoint AABBs enumerate local-versus-whole potential pairs through the first positive sampled bound; sharedphysical aliases/startingproper/static pairs excluded.','All6vertex-face and9edge-edge coplanarity polynomials (degree<=3); persistentcoplanar endpoint/edge collinearity polynomials and endpoint events retained. Adjacent polynomialevent intervals tested for archived properfinite crossing.','Float64 numeric polynomialroots and finiteclassifiers, not interval/exactrational certification. No contact tolerances changed from frozen102.'],'kinds':summary,'earliestNumericEntry':earliest,'numericEntries':all_entries,'unresolvedAlwaysCollinearPairs':unresolved_rows,'limits':['Always-collinear features and finite precision leave uncertified event completeness/ordering. Earliest numeric entry is not certified global earliest geometric contact.','Most importantly: archived data have no executed geometry iterates/line-search/tessellation history. The affine path is reconstructed. No claim about the first actual fitting execution event.','No new fitting/skin solve, native candidate/source save/render/capture/scope expansion/threshold waiver. Protecteddecoded normals independently reject this chord. AllM0-M5open.']}
(out/'chord-events.json').write_text(json.dumps(report,indent=2)+'\n');print('CCD_EARLIEST',earliest,flush=True);print('CCD_COUNTS',summary,flush=True)
