"""One source-profile quad-dominant cage, literal original-prefix GLB assembly."""
import bpy,numpy as np,json,struct,hashlib,math,copy
from pathlib import Path
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/source-guided-cage182');E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/source-guided-cage182');S=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb')
contract=json.loads((E/'parent-contract.json').read_text());assert contract['parentGeometryGo'];raw=S.read_bytes();assert hashlib.sha256(raw).hexdigest()==contract['sourceSHA256'];n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);buf=bytearray(raw[28+n:]);prefix=bytes(buf)
def acc(i):
 a=doc['accessors'][i];v=doc['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];w={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];return np.ndarray((a['count'],w),dtype=dt,buffer=buf,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(dt).itemsize*w),np.dtype(dt).itemsize)).copy()
body=doc['meshes'][0]['primitives'][0];attrs={k:acc(i) for k,i in body['attributes'].items()};P=attrs['POSITION'];F=acc(body['indices']).reshape(-1,3);unique,physical=np.unique(P,axis=0,return_inverse=True)
# Physical source-edge registry owns shared Float32 cut positions. Attribute aliases remain separate.
cutphysical={};derived={k:[] for k in attrs};positions=P.tolist();lowfaces=[];ancestry=[]
phi=P[:,1]-.940-.20*(P[:,0]-.640)
def cut(a,b):
 pa,pb=int(physical[a]),int(physical[b]);edge=tuple(sorted((pa,pb)));t=float(phi[a]/(phi[a]-phi[b]));key=(min(a,b),max(a,b))
 if key in cutattr:return cutattr[key]
 if edge not in cutphysical:cutphysical[edge]=(P[a].astype(float)*(1-t)+P[b].astype(float)*t).astype('f4')
 pos=cutphysical[edge];idx=len(positions);positions.append(pos.tolist());cutattr[key]=idx
 for k,x in attrs.items():
  if k=='POSITION':v=pos
  elif k.startswith('JOINTS'):v=x[a] if t<.5 else x[b]
  else:v=(x[a].astype(float)*(1-t)+x[b].astype(float)*t).astype(x.dtype)
  derived[k].append(v)
 ancestry.append({'newRow':idx,'sourceEdge':[int(a),int(b)],'physicalEdge':list(edge),'edgeParameter':t});return idx
cutattr={}
for fi,tri in enumerate(F):
 poly=[]
 for a,b in zip(tri,np.roll(tri,-1)):
  if phi[a]<=0:poly.append(int(a))
  if (phi[a]<0<phi[b]) or (phi[b]<0<phi[a]):poly.append(cut(int(a),int(b)))
 for k in range(1,len(poly)-1):lowfaces.append((poly[0],poly[k],poly[k+1]))
LP=np.array(positions,dtype='f4');LF=np.array(lowfaces,dtype=int)
# Select lower-side components using exact position quotient and leg/foot seeds only.
U,inv=np.unique(LP,axis=0,return_inverse=True);uf=np.arange(len(U))
def root(a):
 while uf[a]!=a:uf[a]=uf[uf[a]];a=uf[a]
 return a
for t in inv[LF]:
 a=root(int(t[0]))
 for b in t[1:]:uf[root(int(b))]=a
seed={root(int(i)) for i in np.unique(inv[LF]) if U[i,1]<.8};keep=np.array([root(int(inv[t[0]])) in seed for t in LF]);LF=LF[keep]
def boundary(p,f):
 ids={}
 for ti,t in enumerate(f):
  for a,b in zip(t,np.roll(t,-1)):ids.setdefault(tuple(sorted((int(a),int(b)))),[]).append((int(a),int(b),ti))
 b=[v[0][:2] for v in ids.values() if len(v)==1];adj={}
 for a,c in b:adj.setdefault(a,set()).add(c);adj.setdefault(c,set()).add(a)
 assert all(len(v)==2 for v in adj.values()),'Boundary graph branch'
 seen=set();cycles=[]
 for start in adj:
  if start in seen:continue
  cur=start;prev=None;cycle=[]
  while cur not in seen:
   seen.add(cur);cycle.append(cur);ns=adj[cur]-({prev} if prev is not None else set());nxt=min(ns);prev,cur=cur,nxt
  assert cur==start,'Boundary not closed';cycles.append(cycle)
 return cycles,ids
hemcycles,_=boundary(U,inv[LF]);hem=[c for c in hemcycles if np.max(U[c,1])>.88 and np.ptp(U[c,2])>.30];assert len(hem)==1,'Exactly one actual new lower design-cut rim required';hem=U[hem[0]].astype('f4')
# Immutable source final ordered cycles, not angle/height-selected cuff vertices.
mp=np.load(contract['sourceProfileSections']['path']);hood=mp['hood_bodyCycle0Float32Positions'].astype('f4');cuffs=[mp['cuff_body_gloveCycle0Float32Positions'].astype('f4'),mp['cuff_body_gloveCycle1Float32Positions'].astype('f4')]
verts=[];faces=[];quads=[];tags=[];registry={}
def node(key,p):
 p=tuple(np.asarray(p,dtype='f4').tolist())
 if key in registry:assert verts[registry[key]]==p;return registry[key]
 i=len(verts);registry[key]=i;verts.append(p);return i
def polygon(ids,tag):
 assert len(set(ids))==len(ids);faces.append(tuple(ids));tags.append(tag)
 if len(ids)==4:quads.append(tuple(ids))
def ring(raw,name):return [node((name,i),p) for i,p in enumerate(raw)]
def samples(raw,N):
 # Preserve original cyclic order; align start by actual frontmost source node.
 raw=np.roll(raw,-int(np.argmax(raw[:,0])),axis=0);lens=np.linalg.norm(np.roll(raw,-1,axis=0)-raw,axis=1);ss=np.r_[0,np.cumsum(lens)];vals=[]
 for t in np.arange(N)*ss[-1]/N:
  k=min(len(raw)-1,int(np.searchsorted(ss,t,side='right')-1));v=(t-ss[k])/lens[k];vals.append(raw[k]*(1-v)+raw[(k+1)%len(raw)]*v)
 return np.array(vals),raw
N=64;hco,hood=samples(hood,N);bco,hem=samples(hem,N)
# Match cyclic orientation to front->positive lateral for all sections.
def positive(raw):return raw if raw[1,2]>raw[-1,2] else np.r_[raw[:1],raw[:0:-1]]
hood=positive(hood);hem=positive(hem);hco,_=samples(hood,N);bco,_=samples(hem,N)
# Source samples guide complete lower/mid cross-sections. Avoid sleeve points with declared lateral ROI.
levels=[.98,1.08,1.18,1.28];profiles=[]
for height in levels:
 q=P[(abs(P[:,1]-height)<.007)&(abs(P[:,2])<.225)]
 assert len(q)>30,'Missing measured torso section'
 ang=np.arctan2(q[:,2]/.20,(q[:,0]-.64)/.16);radius=np.sqrt(((q[:,0]-.64)/.16)**2+(q[:,2]/.20)**2);out=[]
 for theta in np.arange(N)*2*math.pi/N:
  dist=abs(np.angle(np.exp(1j*(ang-theta))));near=np.argsort(dist)[:8];chosen=near[np.argmax(radius[near])];p=q[chosen].copy();p[1]=height;out.append(p)
 profiles.append(np.array(out))
# Neckline owns sourcehood shape: smoothly inset only the coarse intermediate row below exact seam.
top=hco.copy();top[:,1]-=.024
rows=[bco,*profiles,top];grid=[ring(q,'torso'+str(i)) for i,q in enumerate(rows)]
# Reserve complete side windows between rows3..5 and angular6-node spans.
windows=[(12,20),(44,52)];deleted=set()
for side,(a,b) in enumerate(windows):
 for r in [3,4]:
  for c in range(a,b):deleted.add((r,c))
for r in range(len(grid)-1):
 for c in range(N):
  if (r,c) not in deleted:polygon([grid[r][c],grid[r][(c+1)%N],grid[r+1][(c+1)%N],grid[r+1][c]],'torso')
# Zipper strips retain every exact donor boundary point and avoid artificial collapsed parity nodes.
def zipper(A,B,tag):
 i=j=0;na=len(A);nb=len(B)
 while i<na or j<nb:
  fa=(i+1)/na if i<na else 2;fb=(j+1)/nb if j<nb else 2
  if abs(fa-fb)<1e-10:polygon([A[i%na],A[(i+1)%na],B[(j+1)%nb],B[j%nb]],tag);i+=1;j+=1
  elif fa<fb:polygon([A[i%na],A[(i+1)%na],B[j%nb]],tag+' triangle');i+=1
  else:polygon([A[i%na],B[(j+1)%nb],B[j%nb]],tag+' triangle');j+=1
hoodids=ring(hood,'exacthood');hemids=ring(hem,'exacthem');zipper(grid[-1],hoodids,'hood transition');zipper(hemids,grid[0],'hem transition')
cuffids=[]
for side,(a,b) in enumerate(windows):
 # Window perimeter is top-right-bottom-left, with physically shared torso IDs.
 rootids=[grid[3][c] for c in range(a,b)]+[grid[r][b] for r in range(3,5)]+[grid[5][c] for c in range(b,a,-1)]+[grid[r][a] for r in range(5,3,-1)]
 pts=np.array([verts[i] for i in rootids]);sign=1 if side==0 else -1;M=len(rootids)
 # Source rest shoulder->elbow->hand centers and measured sleeve dimensions; all new indexed sleeve rows.
 centers=[(.635,1.365,sign*.245),(.627,1.27,sign*.267),(.625,1.15,sign*.289),(.642,1.04,sign*.32),(.664,.945,sign*.351)]
 prev=rootids
 for row,center in enumerate(centers):
  center=np.array(center);angles=np.arctan2(pts[:,1]-pts[:,1].mean(),pts[:,0]-pts[:,0].mean())
  # Fresh source-guided arm controls use radial samples in the corresponding height/lateral sleeve region.
  q=P[(abs(P[:,1]-center[1])<.012)&(P[:,2]*sign>.205)&(P[:,2]*sign<.405)]
  rx=.055 if row>=3 else .068;rz=.047 if row>=3 else .064
  if len(q)>10:rx=min(.085,max(.045,np.ptp(q[:,0])*.5));rz=min(.075,max(.038,np.ptp(q[:,2])*.35))
  pp=[]
  for theta in angles:
   pp.append(center+np.array([rx*math.cos(theta),.018*math.sin(theta),sign*rz*math.sin(theta)]))
  cur=ring(pp,'sleeve'+str(side)+'row'+str(row));zipper(prev,cur,'shared shoulder sleeve'+str(side));prev=cur
 exact=positive(cuffs[side]);_,exact=samples(exact,len(exact));exact=positive(exact);ci=ring(exact,'exactcuff'+str(side));zipper(prev,ci,'cuff transition'+str(side));cuffids.append(ci)
# Final triangulation and float32 topology first; no tolerances/proximity weld.
V=np.array(verts,dtype='f4');T=[]
for f in faces:
 for k in range(1,len(f)-1):T.append((f[0],f[k],f[k+1]))
T=np.array(T,dtype='u4');np.savez(R/'cage01.npz',p=V,f=T,quads=np.array(quads),hoodIDs=hoodids,hemIDs=hemids,cuffLIDs=cuffids[0],cuffRIDs=cuffids[1]);np.savez(R/'lower-cut01.npz',p=LP,f=LF);(R/'lower-cut-ancestry.json').write_text(json.dumps(ancestry));(R/'quad-face-tags.json').write_text(json.dumps(tags))
# Initial winding normalized as one physical fresh mesh only; no garment proximity merges.
bpy.ops.wm.read_factory_settings(use_empty=True);me=bpy.data.meshes.new('Fresh source guided quad cage');me.from_pydata(V.tolist(),[],faces);me.update();ob=bpy.data.objects.new('UNACCEPTED_CAGE182',me);bpy.context.collection.objects.link(ob);bpy.ops.wm.save_as_mainfile(filepath=str(R/'cage01.blend'))
report={'status':'ONE_CAGE_FROZEN_PREEXPORT_AUDIT_REQUIRED','sourceSHA256':hashlib.sha256(raw).hexdigest(),'vertices':len(V),'triangles':len(T),'authoredQuads':len(quads),'authoredTransitionTriangles':len(faces)-len(quads),'lowerRetainedTriangles':len(LF),'newCutAttributeRows':len(ancestry),'hemNodes':len(hemids),'hoodNodes':len(hoodids),'cuffNodes':[len(x) for x in cuffids],'sourceGeometry':'New torso profile controls/cage topology; source exacthood/cuff nodes+newcutrim only, no retiredmesh lineage.','limits':'No normals/winding/export sewing/contact acceptance yet. Onegeometryfreeze, cannotrender beforeliteral gate.'};(E/'construction.json').write_text(json.dumps(report,indent=2));print(json.dumps(report))
