"""Independent finite-pair universe and selected exact polynomial checks."""
from pathlib import Path
from fractions import Fraction as F
import hashlib,json,itertools
import numpy as np
out=Path(__file__).resolve().parent;qa=out.parent;root=Path.cwd();ev=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1';src=ev/'neck-interface103';sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((qa/'neck76/preparation.json').read_text());a=np.load(src/'path-geometry-and-candidates.npz');f=np.load(ev/'neck-interface102/candidate-fields-ancestry-corrected.npz');w=np.load(ev/'neck-interface102/solve-witnesses.npz');P0=a['P0'];P1=a['P1'];D=P1-P0;NB=len(f['bodyRestXYZ']);mp={'body':a['rawPhysicalMap'][:NB],'head':a['rawPhysicalMap'][NB:]};raw={p:a[p+'ReferenceTriangles'] for p in mp};t={p:mp[p][raw[p]] for p in mp};scope={p:set(map(int,f[p+'LocalTriangleIDs'])) for p in mp};owner=json.loads((src/'chord-events.json').read_text());path=json.loads((src/'path-samples.json').read_text());exact=json.loads((src/'exact-path-witnesses.json').read_text());families={'bodySelf':('body','body'),'headSelf':('head','head'),'bodyHead':('body','head')}
# Only own pure classifier definition is reused; no Blender or file-write body executes.
text=(out/'read-endpoints-normals.py').read_text();n={'np':np};exec(compile(text[text.index('def proper(A,B):'):text.index("families={'bodySelf'")],'independent-proper-query','exec'),n);proper=n['proper'];U=owner['pathUpperAlpha'];boxes={}
for p in mp:
 A=P0[t[p]];B=(P0+U*D)[t[p]];boxes[p]=(np.minimum(A.min(1),B.min(1)),np.maximum(A.max(1),B.max(1)))
universes={}
for kind,(p,q) in families.items():
 found=set()
 for i in scope[p]:
  lo,hi=boxes[p];ql,qh=boxes[q];ids=np.flatnonzero((ql<=hi[i]).all(1)&(qh>=lo[i]).all(1));found.update((min(i,int(j)),max(i,int(j))) if p==q else (i,int(j)) for j in ids if p!=q or i!=j)
 if p!=q:
  for j in scope[q]:
   lo,hi=boxes[p];ql,qh=boxes[q];ids=np.flatnonzero((lo<=qh[j]).all(1)&(hi>=ql[j]).all(1));found.update((int(i),j) for i in ids)
 starting=set(map(tuple,path['startingReferenceProperPairs'][kind]));found={z for z in found if z not in starting and not set(t[p][z[0]])&set(t[q][z[1]]) and np.any(D[np.r_[t[p][z[0]],t[q][z[1]]]])};arch=set(map(tuple,a[kind+'SweptNewPairs']));assert found==arch;universes[kind]={'independentPairs':len(found),'archivedPairIDsExact':True};print('SWEPT_UNIVERSE_EXACT',kind,len(found),flush=True)
# Independent degree<=3 determinant coefficient expansion, all numeric roots.
# Persistent-coplanar features are not silently resolved; archive asserts none.
def poly(v):
 c=np.zeros(4)
 for choices in itertools.product([0,1],repeat=3):c[sum(choices)]+=np.dot(v[0][choices[0]],np.cross(v[1][choices[1]],v[2][choices[2]]))
 return c
def features(i,j,p,q):
 A,AD,B,BD=P0[t[p][i]],D[t[p][i]],P0[t[q][j]],D[t[q][j]];vec=[]
 for X,XD,Y,YD in [(A,AD,B,BD),(B,BD,A,AD)]:
  for vi in range(3):vec.append([(X[vi]-Y[0],XD[vi]-YD[0]),(Y[1]-Y[0],YD[1]-YD[0]),(Y[2]-Y[0],YD[2]-YD[0])])
 for x,y in [(0,1),(1,2),(2,0)]:
  for u,v in [(0,1),(1,2),(2,0)]:vec.append([(A[y]-A[x],AD[y]-AD[x]),(B[v]-B[u],BD[v]-BD[u]),(B[u]-A[x],BD[u]-AD[x])])
 return A,AD,B,BD,vec
numeric=[];persistent=0
for kind,(p,q) in families.items():
 count=0
 for i,j in a[kind+'SweptNewPairs']:
  A,AD,B,BD,v=features(int(i),int(j),p,q);times=[0.,U]
  for feature in v:
   c=poly(feature);nz=np.flatnonzero(c!=0)
   if not len(nz):persistent+=1;continue
   roots=np.polynomial.polynomial.polyroots(c[:nz[-1]+1]);times.extend(float(r.real) for r in roots if abs(r.imag)<1e-8 and 0<=r.real<=U)
  times=sorted(set(times))
  for left,right in zip(times[:-1],times[1:]):
   if right-left<=1e-14:continue
   mid=(left+right)/2
   if proper(A+mid*AD,B+mid*BD):numeric.append({'kind':kind,'triangleIDs':[int(i),int(j)],'onsetAlpha':left,'nextAlpha':right,'interiorAlpha':mid});count+=1;break
 print('INDEPENDENT_NUMERIC_ENTRIES',kind,count,flush=True)
assert persistent==0;numeric.sort(key=lambda z:z['onsetAlpha']);assert len(numeric)==len(owner['numericEntries'])==9
for r,z in zip(numeric,owner['numericEntries']):assert r['kind']==z['kind'] and r['triangleIDs']==z['triangleIDs'];assert abs(r['onsetAlpha']-z['onsetRootAlpha'])<1e-12
# Exact binary rational coefficient reconstruction from both rounded vector
# differences and exact original-coordinate subtraction. Compare explicitly.
def cross(a,b):return [a[1]*b[2]-a[2]*b[1],a[2]*b[0]-a[0]*b[2],a[0]*b[1]-a[1]*b[0]]
def det(a,b,c):return sum(x*y for x,y in zip(a,cross(b,c)))
def exactpoly(v):
 c=[F(0)]*4
 for k in itertools.product([0,1],repeat=3):c[sum(k)]+=det(v[0][k[0]],v[1][k[1]],v[2][k[2]])
 return c
r=owner['earliestNumericEntry'];i,j=r['triangleIDs'];A,AD,B,BD,v=features(i,j,'body','head');brackets=[]
for z in exact['selectedRootExactBinaryBracket']:
 (x,y),(u,vv)=z['edges'];vf=[(A[y]-A[x],AD[y]-AD[x]),(B[vv]-B[u],BD[vv]-BD[u]),(B[u]-A[x],BD[u]-AD[x])];rounded=[[[F.from_float(float(n)) for n in row] for row in pair] for pair in vf];c=exactpoly(rounded);assert [str(v) for v in c]==z['exactBinaryRationalCoefficients'];fr=lambda row:[F.from_float(float(n)) for n in row];sub=lambda a,b:[x-y for x,y in zip(a,b)];direct=[(sub(fr(A[y]),fr(A[x])),sub(fr(AD[y]),fr(AD[x]))),(sub(fr(B[vv]),fr(B[u])),sub(fr(BD[vv]),fr(BD[u]))),(sub(fr(B[u]),fr(A[x])),sub(fr(BD[u]),fr(AD[x])))];dc=exactpoly(direct);lo,hi=map(F.from_float,z['bracketAlpha']);values=[sum(co*t**k for k,co in enumerate(c)) for t in [lo,hi]];directValues=[sum(co*t**k for k,co in enumerate(dc)) for t in [lo,hi]];sign=lambda n:1 if n>0 else -1 if n<0 else 0;assert values[0]*values[1]<0 and directValues[0]*directValues[1]<0;assert [sign(n) for n in values]==z['exactPolynomialSigns'];brackets.append({'triangleIDs':[i,j],'edges':z['edges'],'roundedVectorCoefficientsExactToOwner':True,'exactOriginalCoordinateSubtractionCoefficientsIdentical':dc==c,'roundedVectorSigns':[sign(n) for n in values],'exactCoordinateSigns':[sign(n) for n in directValues],'bracketAlpha':z['bracketAlpha']})
alpha=r['onsetRootAlpha'];before=proper(A+(alpha-1e-6)*AD,B+(alpha-1e-6)*BD);after=proper(A+(alpha+1e-6)*AD,B+(alpha+1e-6)*BD);assert not before and after
noncap=[];dof=np.zeros(len(P0),int);np.add.at(dof,w['freePhysicalNodes'][w['variableOwner']],1)
for z in exact['selectedNonCapDOFExamples']:
 p,q=families[z['kind']];i,j=z['finalNativeTriangleIDs'];assert np.array_equal(raw[p][i],f[p+'Triangles'][i]) and np.array_equal(raw[q][j],f[q+'Triangles'][j]);A,AD,B,BD,v=features(i,j,p,q);assert dof[t[p][i]].tolist()==z['tangentDOFByCorner'][0] and dof[t[q][j]].tolist()==z['tangentDOFByCorner'][1];r=z['onsetRootAlpha'];assert not proper(A+(r-1e-6)*AD,B+(r-1e-6)*BD) and proper(A+(r+1e-6)*AD,B+(r+1e-6)*BD);assert not proper(A,B);noncap.append({'kind':z['kind'],'triangleIDs':[i,j],'sourcePolygonIDs':[int(f[p+'TriangleSourcePolygonIDs'][i]),int(f[q+'TriangleSourcePolygonIDs'][j])],'allCornersArchivedTangentDOF3':True,'properBeforeOnsetMinus1e_6':False,'properAfterOnsetPlus1e_6':True,'reportedNumericOnsetAlpha':r})
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
result={'status':'INDEPENDENT_NUMERIC_UNIVERSE_AND_SELECTED_BINARY_ROOT_AUDIT','recipeSHA256':sha(__file__),'sweptPairUniverse':universes,'independentNumericEntries':numeric,'persistentCoplanarFeatures':persistent,'selectedExactRootBrackets':brackets,'selectedFiniteCrossingBefore':before,'selectedFiniteCrossingAfter':after,'nonCapWitnesses':noncap,'inputPinsUnchangedAfter':True,'limits':['Independent all-pair numeric enumeration corroborates9entries and numeric ordering only. One exact selected polynomial sign bracket does not certify global first-event ordering, finite-contact instant, root completeness or solver chronology.','Selected noncap probes corroborate finite crossing on either side of the supplied numeric onset; they are not exact onset/global earliest certificates.','No new candidate, path, fit/seed/operator solve, source edit/save, pose/render/capture or admission.']};(out/'event-audit.json').write_text(json.dumps(result,indent=2)+'\n');print('EXACT_BINARY_BRACKETS',brackets,flush=True)
