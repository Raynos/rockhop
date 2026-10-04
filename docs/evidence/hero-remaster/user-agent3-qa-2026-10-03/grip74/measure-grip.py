"""Read-only CPU diagnosis; rider-implied chassis is not a recorded bike matrix."""
import gzip,hashlib,json,struct,itertools
from pathlib import Path
import numpy as np
out=Path(__file__).resolve().parent;qa=out.parent;root=Path.cwd();sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();prep=json.loads((qa/'grip73/preparation.json').read_text())
for p,h in prep['pins'].items():assert sha(root/p)==h['sha256'],p
p=root/'harness/out/user-agent3-2026-10-03/constructed37/rider.glb';b=p.read_bytes();l=struct.unpack_from('<I',b,12)[0];g=json.loads(b[20:20+l]);binary=b[28+l:]
def acc(i):
 a=g['accessors'][i];v=g['bufferViews'][a['bufferView']];assert 'extensions' not in v and 'sparse' not in a;d=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5121:'<u1'}[a['componentType']]);n={'SCALAR':1,'VEC3':3,'VEC4':4,'MAT4':16,'VEC2':2}[a['type']];x=np.ndarray((a['count'],n),dtype=d,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',n*d.itemsize),d.itemsize)).copy();return x.astype(float)/np.iinfo(d).max if a.get('normalized') else x
norm=lambda s:s.replace('.','').replace('_','');skin=g['skins'][0];names=[g['nodes'][i]['name'] for i in skin['joints']];ib=acc(skin['inverseBindMatrices']).reshape(51,4,4).transpose(0,2,1).astype(float);rest=np.linalg.inv(ib);ns=list(map(norm,names));idx=lambda s:ns.index(norm(s));parents={c:i for i,n in enumerate(g['nodes']) for c in n.get('children',[])};jp=[skin['joints'].index(parents[i]) if parents.get(i) in skin['joints'] else -1 for i in skin['joints']]
pr=next(m for m in g['meshes'] if 'gloves' in m['name'])['primitives'][0];xyz=acc(pr['attributes']['POSITION']).astype(float);j=acc(pr['attributes']['JOINTS_0']).astype(int);w=acc(pr['attributes']['WEIGHTS_0']).astype(float);w/=w.sum(1)[:,None];dense=np.zeros((len(xyz),51));
for k in range(4):np.add.at(dense,(np.arange(len(xyz)),j[:,k]),w[:,k])
np.savez_compressed(out/'export-hand-fields.npz',gloveXYZ=xyz,gloveTriangles=acc(pr['indices']).reshape(-1,3),weights=dense,inverseBinds=ib,jointNames=np.array(names))
h=np.column_stack([xyz,np.ones(len(xyz))]);sockets={s:np.array(next(n for n in g['nodes'] if n.get('name')=='gripSocket.'+s)['translation']+[1.]) for s in ['L','R']}
finite=json.loads((out/'finite-grips.json').read_text())
def point_query(points,t):
 # All triangle interiors plus all clamped finite edges, no cylinder substitution.
 p=np.asarray(points)[:,None,:];a=t[:,0];b=t[:,1];c=t[:,2];ab=b-a;ac=c-a;n=np.cross(ab,ac);n2=(n*n).sum(1);projection=p-((p-a)*n).sum(2)[:,:,None]/n2[None,:,None]*n;v=projection-a;d00=(ab*ab).sum(1);d01=(ab*ac).sum(1);d11=(ac*ac).sum(1);den=d00*d11-d01*d01;u=((v*ab).sum(2)*d11-(v*ac).sum(2)*d01)/den;vv=((v*ac).sum(2)*d00-(v*ab).sum(2)*d01)/den;dist=((p-projection)**2).sum(2);dist[(u<0)|(vv<0)|(u+vv>1)]=np.inf;nearest=projection.copy()
 for x,y in [(a,b),(b,c),(c,a)]:
  e=y-x;f=np.clip(((p-x)*e).sum(2)/(e*e).sum(1),0,1);q=x+f[:,:,None]*e;d=((p-q)**2).sum(2);mask=d<dist;dist[mask]=d[mask];nearest[mask]=q[mask]
 choose=dist.argmin(1);q=nearest[np.arange(len(points)),choose];vec=t[None,:,:,:]-np.asarray(points)[:,None,None,:];v0,v1,v2=vec[:,:,0],vec[:,:,1],vec[:,:,2];r0=np.linalg.norm(v0,axis=2);r1=np.linalg.norm(v1,axis=2);r2=np.linalg.norm(v2,axis=2);num=(v0*np.cross(v1,v2)).sum(2);den=r0*r1*r2+(v0*v1).sum(2)*r2+(v1*v2).sum(2)*r0+(v2*v0).sum(2)*r1;winding=(2*np.arctan2(num,den)).sum(1)/(4*np.pi);return np.sqrt(dist.min(1)),np.abs(winding)>.5,choose,q
# Native rest ancestry: nearest matching coordinates may be UV split aliases; validate all tied fields.
native=np.load(out/'native26.npz');C=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1]],float);N=list(native['boneNames']);no=[N.index(n) for n in names];nr=C@native['rigWorld']@native['rigRest'][no];assert np.max(np.abs(nr-rest))<5e-6
npworld=(np.column_stack([native['gloveXYZ'],np.ones(len(native['gloveXYZ']))])@(C@native['gloveWorld']).T)[:,:3];cell=3e-7;bins={}
for i,q in enumerate(np.floor(npworld/cell).astype(int)):bins.setdefault(tuple(q),[]).append(i)
gap=[];wg=[];ambiguous=0
for i,p in enumerate(xyz):
 q=np.floor(p/cell).astype(int);cand=[v for off in itertools.product([-1,0,1],repeat=3) for v in bins.get(tuple(q+off),[])];assert cand;d=np.linalg.norm(npworld[cand]-p,axis=1);ties=np.array(cand)[d<=d.min()+1e-12];gap.append(float(d.min()));ambiguous+=len(ties)>1;nw=native['gloveWeights'][ties][:,no];nw/=nw.sum(1)[:,None];wg.append(float(np.abs(nw-dense[i]).max()))
print('ANCESTRY',max(gap),max(wg),'NATIVE_SLOTS',int((native['gloveWeights']>0).sum(1).max()),flush=True);assert max(gap)<2e-7
film=json.loads(gzip.decompress((qa/'presentation50/report.json.gz').read_bytes()));streams=[]
for case in film['cases']:
 samples=case['samples'][:176];world=np.array([[np.array(row[1:]).reshape(4,4).T for row in s['matrices']] for s in samples]);order=list(map(norm,[r[0] for r in samples[0]['matrices']]));world=world[:,[order.index(n) for n in ns]];ticks=[int(s['label'].split('input ')[1].split('/')[0]) for s in samples];streams.append((case['mode'],ticks,world))
with gzip.open(qa/'garment47/first.weights.ndjson.gz','rt') as f:rows=[json.loads(line) for line in f]
K=np.array([r['matrices'] for r in rows]).reshape(703,51,4,4).transpose(0,1,3,2);streams.append(('numeric47_separate',list(range(1,704)),K@np.linalg.inv(ib)))
# Relative local bone transformation residual proves whether fingers articulate.
def angle(a,b):
 u=a/np.linalg.norm(a);v=b/np.linalg.norm(b);return float(np.degrees(np.arccos(np.clip(np.dot(u,v),-1,1))))
results=[]
for label,ticks,W in streams:
 row={'stream':label,'samples':len(ticks),'fingerLocalRestMaxAbs':{},'wristToForearmAngleDeg':{},'impliedChassis':{}};maxq=0.;maxtrans=0.;griprows=[];Bs={}
 for s in ['L','R']:
  hi=idx('hand.'+s);R=W[:,hi,:3,:3]@rest[hi,:3,:3].T;socket=np.einsum('nab,b->na',W[:,hi],sockets[s])[:,:3];target=np.array([.27,.78,.33 if s=='L' else -.33]);B=np.tile(np.eye(4),(len(ticks),1,1));B[:,:3,:3]=R;B[:,:3,3]=socket-np.einsum('nab,b->na',R,target);Bs[s]=B
  wrist=[]
  for ti in range(len(ticks)):wrist.append(angle(W[ti,idx('forearm.'+s),:3,1],W[ti,hi,:3,1]))
  imin=int(np.argmin(wrist));imax=int(np.argmax(wrist));row['wristToForearmAngleDeg'][s]={'min':min(wrist),'max':max(wrist),'minimumInputTick':ticks[imin],'maximumInputTick':ticks[imax],'definition':'Acute-or-obtuse angle between each bone local +Y longitudinal axis; not an anatomical medical angle.'}
  for finger in ['index','middle','pinky','ring','thumb']:
   for seg in ['01','02','03']:
    bi=idx(finger+'_'+seg+'.'+s);pi=jp[bi];local=np.linalg.inv(W[:,pi])@W[:,bi];lrest=np.linalg.inv(rest[pi])@rest[bi];delta=np.max(np.abs(local-lrest),axis=(1,2));row['fingerLocalRestMaxAbs'][names[bi]]={'max':float(delta.max()),'inputTick':ticks[int(delta.argmax())]}
  # Skin glove in the explicitly implied frame. This is a conditional reconstruction, not captured bike.
  for bike in finite['bikes']:
   gr=next(z for z in bike['grips'] if z['side']==s);tri=np.array(gr['trianglesBikeFrame']);d,inside,which,near=point_query([target],tri);griprow={'bike':bike['file'],'side':s,'markerToActualFiniteSurfaceMm':float(d[0]*1000),'markerInsideClosedGrip':bool(inside[0]),'markerClosestSourceTriangleOrdinal':gr['sourceTriangleOrdinals'][int(which[0])],'markerClosestPointBikeFrameM':near[0].tolist(),'conditionalOnRiderImpliedChassis':True,'fingers':{}}
   if bike['file']=='bike-rookie.glb':
    # Closest actual outer-glove triangle to old body centroid marker at immutable rest.
    restmarker=(rest[hi]@sockets[s])[:3];gtri=acc(pr['indices']).astype(int).reshape(-1,3);gd,gin,gw,gnear=point_query([restmarker],xyz[gtri]);palm=gnear[0]+target-restmarker;pd,pin,pw,pnear=point_query([palm],tri);griprow['outerGlovePalmWitness']={'definition':'Nearest actual glove triangle point to immutable body-derived palm centroid; point witness only','sourceGloveTriangleOrdinal':int(gw[0]),'centroidToGloveSurfaceMm':float(gd[0]*1000),'conditionalGlovePointBikeFrameM':palm.tolist(),'conditionalPointInsideGrip':bool(pin[0]),'conditionalPointToFiniteGripSurfaceMm':float(pd[0]*1000)}
    D=np.linalg.inv(B)[:,None]@W@ib
    for finger in ['index','middle','pinky','ring','thumb']:
     fi=idx(finger+'_03.'+s);ids=np.flatnonzero(dense[:,fi]>0);bi=N.index(finger+'_03.'+s);tiplocal=np.linalg.inv(native['rigRest'][bi])@np.r_[native['tails'][bi],1.];tipworld=np.einsum('nab,b->na',W[:,fi],tiplocal);tip=np.einsum('nab,nb->na',np.linalg.inv(B),tipworld)[:,:3];td,tin,tw,tnear=point_query(tip,tri);tm=int(td.argmax());data={'skeletalTerminalBoneTailToFiniteSurfaceMmMin':float(td.min()*1000),'skeletalTerminalBoneTailToFiniteSurfaceMmMax':float(td.max()*1000),'maxTailWitnessInputTick':ticks[tm],'maxTailWitnessBikeFrameM':tip[tm].tolist(),'distalGlovePositiveWeightRows':len(ids),'maximumDistalGloveWeight':float(dense[:,fi].max()),'definition':'Skeletal terminal tail is not outer skin. Semantic-weight centroid below uses all positive distal memberships, not inferred finger segmentation.'}
     if len(ids):
      posed=np.zeros((len(ticks),len(ids),3))
      for slot in range(4):posed+=np.einsum('nvab,vb->nva',D[:,j[ids,slot]],h[ids])[:,:,:3]*w[ids,slot][None,:,None]
      center=np.einsum('nva,v->na',posed,dense[ids,fi])/dense[ids,fi].sum();dd,inn,wh,near=point_query(center,tri);imin=int(dd.argmin());imax=int(dd.argmax());data.update({'semanticGloveCentroidFiniteSurfaceMmMin':float(dd.min()*1000),'semanticGloveCentroidFiniteSurfaceMmMax':float(dd.max()*1000),'minInputTick':ticks[imin],'maxInputTick':ticks[imax],'maxCentroidWitnessBikeFrameM':center[imax].tolist(),'insideSamples':int(inn.sum()),'centroidMotionInImpliedChassisMm':float(np.linalg.norm(center-center[0],axis=1).max()*1000)})
     griprow['fingers'][finger]=data
   griprows.append(griprow)
 diff=np.abs(Bs['L']-Bs['R']);row['impliedChassis']={'leftRightMaxAbsResidual':float(diff.max()),'description':'Both chassis transforms inferred from rest-oriented hand and commanded socket targets. Agreement is internal consistency only; film stores no independent bike.frame matrix.'};row['gripGeometryInImpliedFrame']=griprows;results.append(row)
# Native archived motion uses object-local skin matrices, no actual bike target.
witness=np.load(root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/neck-interface99/pose-witnesses.npz');nW=witness['rigLocalSkinMatrices']@native['rigRest'];native_res={}
for bi,n in enumerate(N):
 if any(n.startswith(f+'_') for f in ['index','middle','pinky','ring','thumb']):
  pi=int(native['parents'][bi]);local=np.linalg.inv(nW[:,pi])@nW[:,bi];lr=np.linalg.inv(native['rigRest'][pi])@native['rigRest'][bi];delta=np.max(np.abs(local-lr),axis=(1,2));i=int(delta.argmax());native_res[n]={'maxAbsLocalRestResidual':float(delta[i]),'witnessIndex':i,'domain':str(witness['domains'][i]),'sourceIndex':int(witness['sourceIndices'][i])}
r={'status':'UNACCEPTED_SOURCE_PINNED_GRIP_DIAGNOSIS','recipeSHA256':sha(__file__),'preparationCommit':'a3f3f4c1ca56e6b2a8f7eeb65909c2278bf9d968','exportSourceSHA256':prep['pins']['harness/out/user-agent3-2026-10-03/constructed37/rider.glb']['sha256'],'sourceAnimationCount':len(g.get('animations',[])),'nativeAncestry':{'rigMaxAbsResidual':float(np.max(np.abs(nr-rest))),'gloveMaximumPositionResidualM':max(gap),'gloveMaximumMembershipResidual':max(wg),'membershipByteExact':False,'nativeGloveMaximumInfluences':int((native['gloveWeights']>0).sum(1).max()),'exportRows':len(xyz),'nativeVertices':len(npworld),'ambiguousAliases':ambiguous,'allTiedMembershipFieldsTested':True},'streams':results,'native99FingerLocalRestResiduals':native_res,'distalGloveMembershipNativeVsExport':{n:{'nativePositiveRows':int((native['gloveWeights'][:,N.index(n)]>0).sum()),'exportPositiveRows':int((dense[:,i]>0).sum())} for i,n in enumerate(names) if '_03.' in n},'pinsUnchangedAfter':True,'limits':['Rider-implied frame is an internal controller reconstruction. No independent per-frame bike transform exists in film50 receipt; no full actual-contact certificate.','Actual47 numeric poses differ from film50. Metrics are separate, not a pixel synchronization claim.','Native26/29 glove/rest fields match oldsource37 within export roundoff; native99 lacks matching actual bike/engine played contact.','Semantic glove centroids and skeletal terminal tails are explicit articulation/gap witnesses, not complete finger surface wrap, collision or palm pressure certification. Missing distal memberships prevent interpreting bone tips as visible finger motion.','No candidate, solve, geometry/rig/weight/pose/controller edits, native save, render/capture, delivery or admission. Root alone judges; M0-M5 open.']}
for q,hsh in prep['pins'].items():assert sha(root/q)==hsh['sha256'],q
(out/'measurements.json').write_text(json.dumps(r,indent=2)+'\n');print(json.dumps({'ancestry':r['nativeAncestry'],'streams':[{k:z[k] for k in ['stream','samples','wristToForearmAngleDeg','impliedChassis']} for z in results],'nativeFingerMaxAbs':max(z['maxAbsLocalRestResidual'] for z in native_res.values())}),flush=True)
