"""One bounded positions-fixed source hood index pass. CPU only; no Blender."""
from pathlib import Path
from collections import defaultdict, Counter
from fractions import Fraction as Q
from datetime import datetime, timezone
import ast, copy, hashlib, json, os, re, struct, subprocess, sys, time
import numpy as np
from scipy.spatial import cKDTree

R=Path('/Users/raynos/projects/games/rockhop')
O=R/'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment185/operator'
S=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/source-preserving-garment185/operator')
P184=R/'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment184'
COP=R/'docs/evidence/hero-remaster/one-rider-v2/source-preserving-garment185/coplanar-source'
SOURCE=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb')
SOURCE_SHA='186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e'
REG_SHA='61b142704e656ea1b9a45d8bed4c467436ed1f76f3c435498f5b74df2b9993b5'
sha=lambda b:hashlib.sha256(b).hexdigest()
utc=lambda:datetime.now(timezone.utc).isoformat()
pins={}
def pin(p,expected=None):
 b=Path(p).read_bytes();h=sha(b)
 if expected:assert h==expected,(str(p),h,expected)
 pins[str(p)]={'sha256':h,'bytes':len(b)};return b
def save(p,x):Path(p).write_text(json.dumps(x,indent=2)+'\n')
def memory():
 v=subprocess.check_output(['vm_stat'],text=True);p=int(re.search(r'page size of (\d+)',v).group(1));n=int(re.search(r'Anonymous pages:\s+(\d+)',v).group(1));g=p*n/1e9;assert g<70,g;return g

class GLB:
 def __init__(self,p,expected=None):
  self.raw=Path(p).read_bytes()
  if expected:assert sha(self.raw)==expected
  magic,ver,total=struct.unpack_from('<III',self.raw);assert magic==0x46546c67 and ver==2 and total==len(self.raw)
  n,typ=struct.unpack_from('<II',self.raw,12);assert typ==0x4e4f534a
  self.d=json.loads(self.raw[20:20+n]);bn,bt=struct.unpack_from('<II',self.raw,20+n);assert bt==0x004e4942
  self.bin=self.raw[28+n:28+n+bn];assert len(self.bin)==bn
 def acc(self,i):
  a=self.d['accessors'][i];w={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];dt={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
  def read(vi,off,n,width,dtype):
   v=self.d['bufferViews'][vi];t=np.dtype(dtype);assert v.get('buffer',0)==0
   return np.ndarray((n,width),dtype=t,buffer=self.bin,offset=v.get('byteOffset',0)+off,strides=(v.get('byteStride',width*t.itemsize),t.itemsize)).copy()
  x=read(a['bufferView'],a.get('byteOffset',0),a['count'],w,dt)if 'bufferView'in a else np.zeros((a['count'],w),dtype=dt)
  if 'sparse'in a:
   s=a['sparse'];ix=s['indices'];v=s['values'];ids=read(ix['bufferView'],ix.get('byteOffset',0),s['count'],1,{5121:'u1',5123:'<u2',5125:'<u4'}[ix['componentType']]).ravel();x[ids]=read(v['bufferView'],v.get('byteOffset',0),s['count'],w,dt)
  return x
 def primitive(self,mi,pi):
  p=self.d['meshes'][mi]['primitives'][pi];return {k:self.acc(v)for k,v in p['attributes'].items()},self.acc(p['indices']).reshape(-1,3)

def strict(A,B):
 hit=np.zeros(len(A),bool)
 for rev in (False,True):
  a,b=(B,A)if rev else(A,B);e1=b[:,1]-b[:,0];e2=b[:,2]-b[:,0]
  for k in range(3):
   d=a[:,(k+1)%3]-a[:,k];h=np.cross(d,e2);det=np.einsum('ij,ij->i',e1,h);valid=abs(det)>1e-12;den=np.where(valid,det,1);s=a[:,k]-b[:,0];u=np.einsum('ij,ij->i',s,h)/den;q=np.cross(s,e1);v=np.einsum('ij,ij->i',d,q)/den;t=np.einsum('ij,ij->i',e2,q)/den
   hit|=valid&(u>1e-7)&(v>1e-7)&(u+v<1-1e-7)&(t>1e-7)&(t<1-1e-7)
 return hit

def edges(pf):
 e=defaultdict(list)
 for i,t in enumerate(pf):
  for k in range(3):
   a,b=map(int,(t[k],t[(k+1)%3]));e[tuple(sorted((a,b)))].append((i,a<b))
 return e

def topology(f):
 pf=quotient[f];e=edges(pf);t=positions[f].astype(float);n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);ar=np.linalg.norm(n,axis=1)/2
 return {'degenerate':int((ar<=1e-12).sum()),'nonmanifold':sum(len(v)>2 for v in e.values()),'winding':sum(len(v)==2 and v[0][1]==v[1][1]for v in e.values()),'duplicateFaces':len(pf)-len({tuple(sorted(map(int,x)))for x in pf}),'boundary':sorted(k for k,v in e.items()if len(v)==1),'minAreaM2':float(ar.min())},e

def projected(A,B):
 n=np.cross(A[1]-A[0],A[2]-A[0]);m=np.cross(B[1]-B[0],B[2]-B[0]);un=n/np.linalg.norm(n);um=m/np.linalg.norm(m);near=np.linalg.norm(np.cross(un,um))<1e-8 and abs((B[0]-A[0])@un)<1e-8
 qa,qb=rational_triangle(A),rational_triangle(B);qn=c3(sub(qa[1],qa[0]),sub(qa[2],qa[0]));exact=all(dot(qn,sub(p,qa[0]))==0 for p in qb);axis=int(np.argmax(abs(n)));keep=[k for k in range(3)if k!=axis];aa=[tuple(p[k]for k in keep)for p in qa];bb=[tuple(p[k]for k in keep)for p in qb];poly=clip_exact(aa,bb);area=abs(sum(c2(poly[k],poly[(k+1)%len(poly)])for k in range(len(poly))))/2 if len(poly)>=3 else Q(0)
 return {'exactCoplanar':exact,'nearPlane':bool(near),'projectedAreaM2':float(area),'normalDot':float(un@um),'positiveOverlap':bool((exact or near)and area>0)}

def audit(f,full=False):
 t=positions[f].astype(float);pf=quotient[f];cent=t.mean(1);rad=np.linalg.norm(t-cent[:,None],axis=2).max(1);lo=t.min(1);hi=t.max(1);tree=cKDTree(cent);rmax=float(rad.max());pairs=set();adjhits=set();cop=[]
 # Candidate audits whole hood against body/gloves and hood-self; final additionally whole body-self/body-gloves.
 src=np.arange(len(t))if full else np.arange(hoodbase,len(t));aa=[];bb=[];shares=[]
 for begin in range(0,len(src),256):
  ids=src[begin:begin+256];neigh=tree.query_ball_point(cent[ids],rad[ids]+rmax+1e-12,workers=2)
  for i,ns in zip(ids,neigh):
   js=np.array(ns,dtype=int)
   if full:js=js[(js>i)&(((primitive[i]==0)&np.isin(primitive[js],[0,1,2]))|((primitive[i]==1)&(primitive[js]==2))|((primitive[i]==2)&(primitive[js]==2)))]
   else:js=js[(js<i)|((js>i)&(primitive[js]==2))]
   if not len(js):continue
   js=js[np.linalg.norm(cent[js]-cent[i],axis=1)<=rad[js]+rad[i]+1e-12];js=js[(hi[i]>=lo[js]-1e-12).all(1)&(lo[i]<=hi[js]+1e-12).all(1)]
   for j in js:aa.append(int(i));bb.append(int(j));shares.append(len(set(pf[i])&set(pf[j])))
 aa=np.array(aa,dtype=int);bb=np.array(bb,dtype=int);shares=np.array(shares);hit=strict(t[aa],t[bb])
 for k in np.flatnonzero(hit):
  pair=tuple(sorted((int(aa[k]),int(bb[k]))))
  (pairs if shares[k]<2 else adjhits).add(pair)
 n=np.cross(t[:,1]-t[:,0],t[:,2]-t[:,0]);un=n/np.linalg.norm(n,axis=1)[:,None];near=(np.linalg.norm(np.cross(un[aa],un[bb]),axis=1)<1e-8)&(abs(np.einsum('ij,ij->i',t[bb,0]-t[aa,0],un[aa]))<1e-8)
 for k in np.flatnonzero(near):
  i,j=int(aa[k]),int(bb[k]);cl=projected(t[i],t[j]);cop.append({'globalFacePair':sorted((i,j)),'shared':int(shares[k]),**cl})
 # All adjacent edge neighbors incident to changed-scope hood slots, including outside the halo.
 ee=edges(pf);fold=[]
 for ev in ee.values():
  if len(ev)!=2:continue
  i,j=ev[0][0],ev[1][0]
  if not ((i>=hoodbase and i-hoodbase in slots)or(j>=hoodbase and j-hoodbase in slots)):continue
  cl=projected(t[i],t[j]);fold.append({'globalFacePair':sorted((i,j)),**cl})
 return {'strictPairs':sorted(pairs),'adjacentStrictPairs':sorted(adjhits),'coplanar':cop,'folds':fold,'foldPositiveProjected':sum(x['projectedAreaM2']>0 for x in fold),'foldMinimumNormalDot':min(x['normalDot']for x in fold),'candidatePairCount':len(aa)}

def candidate_edges(f):
 hf=f[hoodbase:]-hoodoffset;he=edges(quotient[f[hoodbase:]]);result=[]
 for physical,owners in he.items():
  if len(owners)!=2:continue
  fs=sorted(i for i,d in owners)
  if not set(fs)<=slots:continue
  x,y=hf[fs];common=set(map(int,x))&set(map(int,y))
  if len(common)!=2 or len(set(quotient[f[hoodbase+np.array(fs)]].ravel()))!=4:continue
  result.append((tuple(sorted(common)),tuple(fs),physical))
 return sorted(result)

def evaluate(f,cand,current,baseline):
 edge,fs,physical=cand;i,j=(hoodbase+x for x in fs);x=list(map(int,f[i]));y=list(map(int,f[j]));a,b=[hoodoffset+r for r in edge]
 for k in range(3):
  if {x[k],x[(k+1)%3]}=={a,b}:a,b,c=x[k],x[(k+1)%3],x[(k+2)%3];break
 d=next(z for z in y if z not in (a,b));new=np.array([[c,a,d],[c,d,b]],dtype=f.dtype);g=f.copy();g[[i,j]]=new
 reason=[];top,ee=topology(g)
 nd=tuple(sorted(map(int,quotient[[c,d]])));old_edges=edges(quotient[f]);
 if nd in old_edges:reason.append('alternative diagonal already exists')
 if any(top[k]for k in ('degenerate','nonmanifold','winding','duplicateFaces'))or top['boundary']!=source_top['boundary']:reason.append('literal topology/boundary failure')
 if reason:return None,{'edgeRows':list(edge),'faceSlots':list(fs),'reasons':reason,'topology':{k:v for k,v in top.items()if k!='boundary'}}
 au=audit(g);newpairs=set(map(tuple,au['strictPairs']));oldpairs=set(map(tuple,current['strictPairs']));bodynew=[p for p in newpairs-old_source_pairs if primitive[p[0]]!=2 or primitive[p[1]]!=2]
 if len(newpairs)>=len(oldpairs):reason.append('no strict-count decrease')
 if bodynew:reason.append('new hood/body or hood/glove pair')
 if set(map(tuple,au['adjacentStrictPairs']))-set(map(tuple,baseline['adjacentStrictPairs'])):reason.append('new adjacent strict interior crossing')
 if any(x['positiveOverlap']for x in au['coplanar']):reason.append('positive near/exact coplanar overlap')
 if au['foldPositiveProjected']>baseline['foldPositiveProjected']or au['foldMinimumNormalDot']<baseline['foldMinimumNormalDot']-1e-12:reason.append('adjacent fold baseline worsened')
 record={'edgeRows':list(edge),'faceSlots':list(fs),'physicalEdgeIDs':list(physical),'oldIndices':(f[[i,j]]-hoodoffset).tolist(),'newIndices':(new-hoodoffset).tolist(),'oldPhysical':quotient[f[[i,j]]].tolist(),'newPhysical':quotient[new].tolist(),'strictBefore':len(oldpairs),'strictAfter':len(newpairs),'reasons':reason,'foldPositiveProjected':au['foldPositiveProjected'],'foldMinimumNormalDot':au['foldMinimumNormalDot'],'areaQuality':top['minAreaM2'],'topology':{k:v for k,v in top.items()if k!='boundary'}}
 return (None if reason else(g,au)),record

def export(f):
 d=copy.deepcopy(C.d);hood=d['meshes'][0]['primitives'][2];oldacc=d['accessors'][hood['indices']];dt={5121:'u1',5123:'<u2',5125:'<u4'}[oldacc['componentType']];buf=(f[hoodbase:]-hoodoffset).astype(dt).ravel().tobytes();prefix=C.bin;off=len(prefix);vi=len(d['bufferViews']);ai=len(d['accessors']);d['bufferViews'].append({'buffer':0,'byteOffset':off,'byteLength':len(buf),'target':34963});a={'bufferView':vi,'componentType':oldacc['componentType'],'count':len(f[hoodbase:])*3,'type':'SCALAR'};d['accessors'].append(a);hood['indices']=ai;binchunk=prefix+buf;binchunk+=b'\0'*((-len(binchunk))%4);d['buffers'][0]['byteLength']=len(prefix)+len(buf);js=json.dumps(d,separators=(',',':')).encode();js+=b' '*((-len(js))%4);out=struct.pack('<III',0x46546c67,2,28+len(js)+len(binchunk))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binchunk),0x004e4942)+binchunk;p=S/'rider.glb';p.write_bytes(out);E=GLB(p);assert E.bin[:len(C.bin)]==C.bin
 check=copy.deepcopy(E.d);check['buffers'][0]['byteLength']=C.d['buffers'][0]['byteLength'];check['bufferViews']=check['bufferViews'][:-1];check['accessors']=check['accessors'][:-1];check['meshes'][0]['primitives'][2]['indices']=C.d['meshes'][0]['primitives'][2]['indices'];assert check==C.d
 assert all(np.array_equal(C.acc(i),E.acc(i))for i in range(len(C.d['accessors'])))
 ef=[];offp=0
 for k in range(3):a,tr=E.primitive(0,k);ef.append(tr+offp);offp+=len(a['POSITION'])
 ef=np.concatenate(ef);assert np.array_equal(ef,f)
 np.savez_compressed(S/'hood-index-ancestry.npz',sourceHoodIndices=source_f[hoodbase:]-hoodoffset,finalHoodIndices=f[hoodbase:]-hoodoffset,changedSourceFaceSlots=np.flatnonzero(np.any(f[hoodbase:]!=source_f[hoodbase:],axis=1)),sourcePhysicalQuotient=quotient,allowedSourceFaceSlots=np.array(sorted(slots)))
 return E,ef,{'sourceBINPrefixExact':True,'allOriginalAccessorsExact':True,'protectedJSONFieldsExact':True,'sourcePositionsDisplacementM':0,'originalJointCount':len(C.d['skins'][0]['joints']),'sourceMorphCountsByPrimitive':[[len(p.get('targets',[]))for p in m['primitives']]for m in C.d['meshes']],'changedFaceSlots':np.flatnonzero(np.any(f[hoodbase:]!=source_f[hoodbase:],axis=1)).tolist(),'localInterpolationChanged':True,'unchangedVertexNormalsNotRecomputed':True}

if __name__=='__main__':
 S.mkdir(parents=True,exist_ok=True);attempt=json.loads((O/'attempt.json').read_text());assert not (S/'rider.glb').exists(),'Frozen output cannot be overwritten'
 try:
  memory();pin(SOURCE,SOURCE_SHA);reg=json.loads(pin(P184/'operator-proposal/hood185-candidates.json',REG_SHA));slots=set(reg['allowedSourceFaceSlots']);C=GLB(SOURCE,SOURCE_SHA);parts=[C.primitive(0,k)for k in range(3)];positions=np.concatenate([a['POSITION']for a,f in parts]);_,quotient=np.unique(positions,axis=0,return_inverse=True);ff=[];off=0;primitive=[]
  for k,(a,f)in enumerate(parts):ff.append(f+off);off+=len(a['POSITION']);primitive.extend([k]*len(f))
  source_f=np.concatenate(ff);primitive=np.array(primitive);hoodbase=len(ff[0])+len(ff[1]);hoodoffset=len(parts[0][0]['POSITION'])+len(parts[1][0]['POSITION']);source_top,_=topology(source_f);assert all(source_top[k]==0 for k in ('degenerate','nonmanifold','winding','duplicateFaces'));assert len(source_top['boundary'])==237;assert len(candidate_edges(source_f))==23
  if '--prepare-only'in sys.argv:
   save(O/'preparation.json',{'status':'PARSER_SOURCE_HASH_AND_REGISTRY_VERIFIED_NO_FLIPS','sourceSHA256':SOURCE_SHA,'sourceTopology':{k:v for k,v in source_top.items()if k!='boundary'},'boundaryEdges':237,'hoodFaceCount':4118,'candidateEdges':23,'anonymousGB':memory(),'inputs':pins});print('PREPARATION_VERIFIED_NO_GEOMETRY');sys.exit(0)
  cp=json.loads(pin(COP/'report.json','7847b39eff43c65107c5b89622142d6067fa62dc777f1fcdac1f9f41035328cf'));assert cp['status']=='FROZEN_ORIGINAL_C19_COPLANAR_PREREQUISITE_NO_EDITS'and cp['sourceSHA256']==SOURCE_SHA;assert cp['summary']['originalRegistryPairs']==3 and cp['summary']['originalProjectedAreaOverlapPairs']==0
  pin(COP/'audit.py',cp['recipeSHA256'])
  for x in cp['privateOutputs']:pin(x['path'],x['SHA256'])
  for x in cp['inputHashes']:pin(x['path'],x['SHA256'])
  code=ast.parse((COP/'audit.py').read_text());names={'sub','c2','c3','dot','rational_triangle','clip_exact'};exec(compile(ast.Module(body=[x for x in code.body if isinstance(x,ast.FunctionDef)and x.name in names],type_ignores=[]),str(COP/'audit.py'),'exec'),globals())
  save(O/'frozen-inputs.json',{'coplanarSourceReceiptSha256':pins[str(COP/'report.json')]['sha256'],'sourceSHA256':SOURCE_SHA,'registrySHA256':REG_SHA,'inputs':pins,'UTC':utc(),'geometryConditionalGoSatisfied':True})
  started=time.monotonic();attempt.update(status='RUNNING_ONE_BOUNDED_OPERATOR',operatorStartedUTC=utc(),pid=os.getpid());save(O/'attempt.json',attempt);print(json.dumps({'pid':os.getpid(),'UTC':attempt['operatorStartedUTC'],'coplanarSHA':pins[str(COP/'report.json')]['sha256']}),flush=True)
  baseline=audit(source_f);assert len(baseline['strictPairs'])==11;old_source_pairs=set(map(tuple,baseline['strictPairs']));f=source_f.copy();current=baseline;accepted=[];tests=[];reason='candidate exhaustion';first=True
  while len(tests)<128 and len(accepted)<32 and time.monotonic()-started<720:
   memory();cands=candidate_edges(f)
   if first:cands=[c for c in cands if c[0]==(49,66)and c[1]==(4105,4106)];assert len(cands)==1
   best=None
   for cand in cands:
    if len(tests)>=128 or time.monotonic()-started>=720:break
    result,record=evaluate(f,cand,current,baseline);record.update(testID=len(tests)+1,elapsedSeconds=time.monotonic()-started);tests.append(record);save(O/'candidate-tests.json',tests)
    if result:
     rank=(len(result[1]['strictPairs']),-record['areaQuality'],cand[0],cand[1])
     if best is None or rank<best[0]:best=(rank,result,record)
   if best:
    f,current=best[1];accepted.append(best[2]);save(O/'accepted-flips.json',accepted)
   elif not first:break
   first=False
   if not current['strictPairs']:reason='zero strict pairs';break
  save(O/'baseline-audit.json',baseline);save(O/'final-preexport-audit.json',current)
  E,ef,identity=export(f);final=audit(ef,full=True);top,_=topology(ef);save(O/'final-export-audit.json',final)
  clear=not final['strictPairs']and not final['adjacentStrictPairs']and not any(x['positiveOverlap']for x in final['coplanar'])and all(top[k]==0 for k in ('degenerate','nonmanifold','winding','duplicateFaces'))and top['boundary']==source_top['boundary']
  # Retain every original witness regardless of changed physical shared class.
  oldWitness=[]
  for i,j in baseline['strictPairs']:
   ti=positions[ef[[i,j]]].astype(float);oldWitness.append({'globalFacePair':[i,j],'currentPhysicalShared':len(set(quotient[ef[i]])&set(quotient[ef[j]])),'strictRegardlessSharedClass':bool(strict(ti[:1],ti[1:])[0])})
  result={'status':'LITERAL_EXPORT_GATE_CLEAR_PENDING_PARENT'if clear else'FROZEN_OPERATOR_REJECTION_OR_PARTIAL','sourceSHA256':SOURCE_SHA,'acceptedFlips':len(accepted),'candidateTests':len(tests),'seconds':time.monotonic()-started,'stopReason':reason,'finalStrictPairs':len(final['strictPairs']),'sourceStrictPairs':11,'identity':identity,'finalTopology':{k:v for k,v in top.items()if k!='boundary'},'boundaryEdges':len(top['boundary']),'oldWitnessesRegardlessShared':oldWitness,'coplanarSourceSummary':cp['summary'],'anonymousGB':memory(),'recipeSha256':sha(Path(__file__).read_bytes()),'outputs':{str(p):sha(p.read_bytes())for p in S.glob('*')},'limits':['No render, rig or animation gate','All positions fixed; changed hood indices alter local interpolation','Geometric fold projection is a diagnostic, not moving silhouette acceptance']}
  save(O/'report.json',result);attempt.update(status=result['status'],acceptedFlips=len(accepted),candidateTests=len(tests),geometryFailures=[]if clear else[{'id':'H185-FINAL-GATE-01','strictRemaining':len(final['strictPairs']),'onePassFailure':True}]);save(O/'attempt.json',attempt)
  for p,x in pins.items():assert sha(Path(p).read_bytes())==x['sha256']
  print(json.dumps({'status':result['status'],'accepted':len(accepted),'tests':len(tests),'strict':len(final['strictPairs']),'seconds':result['seconds']}),flush=True)
 except Exception as e:
  attempt.update(status='FROZEN_SETUP_OR_EXECUTION_FAILURE',failureUTC=utc());attempt['setupFailures'].append({'id':'H185-EXEC-ERROR-'+str(len(attempt['setupFailures'])+1),'type':type(e).__name__,'error':str(e)});save(O/'attempt.json',attempt);raise
