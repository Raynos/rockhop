"""Read-only immutable rig foundation inventory and conservative torso diagnostic."""
from pathlib import Path
import json,struct,hashlib,numpy as np
from scipy.spatial.transform import Rotation
R=Path('/Users/raynos/projects/games/rockhop'); B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2'); A=R/'assets/blender/hero-remaster/rider/one-rider-v2/rig-foundation167'; O=R/'docs/evidence/hero-remaster/one-rider-v2/rig-foundation167'; S=B/'rig-foundation167'
sha=lambda x:hashlib.sha256(x).hexdigest()
class GLB:
 def __init__(self,p,h):
  self.p=p;self.raw=p.read_bytes();assert sha(self.raw)==h;self.h=h;n=struct.unpack_from('<I',self.raw,12)[0];self.d=json.loads(self.raw[20:20+n]);self.bin=self.raw[28+n:];self.parents={c:i for i,v in enumerate(self.d['nodes']) for c in v.get('children',[])};self.cache={}
 def acc(self,i):
  a=self.d['accessors'][i];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];dt={5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']]
  def read(vi,off,n,w,d):
   v=self.d['bufferViews'][vi];t=np.dtype(d);return np.ndarray((n,w),dtype=t,buffer=self.bin,offset=v.get('byteOffset',0)+off,strides=(v.get('byteStride',w*t.itemsize),t.itemsize)).copy()
  x=read(a['bufferView'],a.get('byteOffset',0),a['count'],width,dt) if 'bufferView'in a else np.zeros((a['count'],width),dtype=dt)
  if 'sparse'in a:
   s=a['sparse'];ids=s['indices'];vs=s['values'];ix=read(ids['bufferView'],ids.get('byteOffset',0),s['count'],1,{5121:'u1',5123:'<u2',5125:'<u4'}[ids['componentType']]).ravel();x[ix]=read(vs['bufferView'],vs.get('byteOffset',0),s['count'],width,dt)
  return x
 def world(self,i):
  if i in self.cache:return self.cache[i]
  n=self.d['nodes'][i]
  if 'matrix'in n:m=np.array(n['matrix']).reshape(4,4).T
  else:m=np.eye(4);m[:3,:3]=Rotation.from_quat(n.get('rotation',[0,0,0,1])).as_matrix()@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
  self.cache[i]=self.world(self.parents[i])@m if i in self.parents else m;return self.cache[i]
 def primitive(self,mi,pi):
  p=self.d['meshes'][mi]['primitives'][pi];return {k:self.acc(a) for k,a in p['attributes'].items()}, self.acc(p['indices']).reshape(-1,3)
 def rest(self):return np.array([self.world(i) for i in self.d['skins'][0]['joints']])
 def ib(self):return self.acc(self.d['skins'][0]['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
V=GLB(B/'garment-rebuild01/physical-v5-control157/rider.glb','2100384b8f2183e98e6e0c78d8b717718b1cc57dd8298e76fab53c1d491c77e9'); C=GLB(Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb'),'186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e'); G=GLB(B/'rig-adapter01/body-bind34/rider.glb','adbac6f2949cec0f32a8e0cfa4cfabd02cce61e58dab4022209e23a605f31df7')
F=B/'basic-pose-gate158/fixture-v4-asymmetric-halfsteps.json';fb=F.read_bytes();assert sha(fb)=='78732965343f6eba40ae68ca99ffa949f6718910eb7b930b67d4a48d0083afab';fixture=json.loads(fb);names=[V.d['nodes'][i]['name'] for i in V.d['skins'][0]['joints']];assert names==fixture['jointNames'];rest=V.rest();ib=V.ib();P,T=V.primitive(0,0);a=P;pos=a['POSITION'];centres=rest[:,:3,3];idx={n:i for i,n in enumerate(names)}
mid=(centres[idx['upperArm.L'],2]+centres[idx['upperArm.R'],2])/2;half=.45*min(abs(centres[idx['upperArm.L'],2]-mid),abs(centres[idx['upperArm.R'],2]-mid));low=centres[idx['pelvis'],1]+.05;high=min(centres[idx['neck'],1]-.060,centres[idx['shoulder.L'],1]-.030,centres[idx['shoulder.R'],1]-.030)
mask=(pos[:,1]>low)&(pos[:,1]<high)&(abs(pos[:,2]-mid)<half);ids=np.flatnonzero(mask);inside=np.flatnonzero(mask[T].all(1));incident=np.flatnonzero(mask[T].any(1));assert len(ids)>0
W=np.zeros((len(pos),19));J=a['JOINTS_0'];rawW=a['WEIGHTS_0'];runtimeW=(rawW.astype(float)/abs(rawW.astype(float)).sum(1,keepdims=True)).astype('f4');
for k in range(4):np.add.at(W,(np.arange(len(pos)),J[:,k]),rawW[:,k])
arm=[idx[n] for n in names if n.startswith(('shoulder.','upperArm.','forearm.','hand.'))];armW=W[:,arm].sum(1);witness=ids[np.argsort(armW[ids])[-20:][::-1]]
children={'pelvis':'spine','spine':'chest','chest':'neck','neck':'head','shoulder.L':'upperArm.L','upperArm.L':'forearm.L','forearm.L':'hand.L','shoulder.R':'upperArm.R','upperArm.R':'forearm.R','forearm.R':'hand.R','thigh.L':'shin.L','shin.L':'foot.L','thigh.R':'shin.R','shin.R':'foot.R'}
axes=[]
for n,ch in children.items():
 v=centres[idx[ch]]-centres[idx[n]];direction=v/np.linalg.norm(v);basis=rest[idx[n],:3,:3]@np.array([0,1,0]);basis/=np.linalg.norm(basis);axes.append({'bone':n,'child':ch,'restJointPosition':centres[idx[n]].tolist(),'childVector':v.tolist(),'lengthM':float(np.linalg.norm(v)),'explicitChildDirection':direction.tolist(),'worldPlusYBasis':basis.tolist(),'dotBasisVsChild':float(basis@direction)})
pivots=[]
for name in ['pelvis','spine','chest','neck','head','shoulder.L','upperArm.L','shoulder.R','upperArm.R']:
 bone=centres[idx[name]];r=[]
 for mi,pi in [(0,0),(0,2),(1,0)]:
  attrs,tr=V.primitive(mi,pi);dist=np.linalg.norm(attrs['POSITION']-bone,axis=1);order=np.argsort(dist)[:4];band=abs(attrs['POSITION'][:,1]-bone[1])<.015
  r.append({'mesh':mi,'primitive':pi,'nearestVertexWitnesses':[{'id':int(i),'position':attrs['POSITION'][i].tolist(),'distanceM':float(dist[i])}for i in order],'surfaceBandVertexCount':int(band.sum()),'surfaceBandBounds':np.stack([attrs['POSITION'][band].min(0),attrs['POSITION'][band].max(0)]).tolist() if band.any() else None})
 pivots.append({'bone':name,'worldPosition':bone.tolist(),'surfaces':r})
compare=[]
for mi,mesh in enumerate(V.d['meshes']):
 for pi,p in enumerate(mesh['primitives']):
  va,vt=V.primitive(mi,pi);ga,gt=G.primitive(mi,pi);ca,ct=C.primitive(mi,pi)
  compare.append({'mesh':mi,'primitive':pi,'attributes':{k:{'V5vs34ChangedRows':int(np.any(v!=ga[k],axis=1).sum()),'C19vs34Exact':bool(np.array_equal(ca[k],ga[k])),'accessorNormalized':V.d['accessors'][p['attributes'][k]].get('normalized',False),'V5ArraySHA256':sha(v.tobytes()),'source34ArraySHA256':sha(ga[k].tobytes())}for k,v in va.items()},'V5vs34ChangedTriangleRows':int(np.any(vt!=gt,axis=1).sum()),'C19vs34TrianglesExact':bool(np.array_equal(ct,gt))})
rig=[]
for g in [C,G,V]:
 sk=g.d['skins'][0];rr=g.rest();ii=g.ib();rig.append({'source':str(g.p),'SHA256':g.h,'sceneRoots':g.d['scenes'][g.d.get('scene',0)]['nodes'],'skin':sk,'jointNames':[g.d['nodes'][i]['name']for i in sk['joints']],'worldRestColumnMajor':rr.transpose(0,2,1).reshape(19,16).tolist(),'inverseBindColumnMajor':ii.transpose(0,2,1).reshape(19,16).tolist(),'restInverseBindMaxIdentityError':float(abs(rr@ii-np.eye(4)).max()),'determinants':np.linalg.det(rr[:,:3,:3]).tolist(),'meshAttachments':[{'node':i,'name':n.get('name'),'skin':n.get('skin'),'mesh':n['mesh'],'parent':g.parents.get(i),'worldColumnMajor':g.world(i).T.reshape(16).tolist(),'extras':n.get('extras',{})}for i,n in enumerate(g.d['nodes'])if 'mesh'in n],'nodes':[{'id':i,'name':n.get('name'),'parent':g.parents.get(i),'children':n.get('children',[]),'translation':n.get('translation'),'rotation':n.get('rotation'),'scale':n.get('scale'),'matrix':n.get('matrix'),'extras':n.get('extras',{})}for i,n in enumerate(g.d['nodes'])],'asset':g.d['asset']})
roi={'definition':'Frozen V5 mesh0 primitive0 POSITION: pelvisY+0.050 < Y < min(neckY-0.060, shoulderLY-0.030, shoulderRY-0.030); |Z-upperArmMidline| < 0.45*min(left/right upperArm lateral distance). All X included. Conservative central-core diagnostic only; shoulders excluded by construction, not forbidden weighting.','limits':{'Ylow':float(low),'Yhigh':float(high),'Zmid':float(mid),'Zhalfwidth':float(half)},'vertexIDs':ids.tolist(),'whollyInsideTriangleIDs':inside.tolist(),'whollyInsideTriangles':T[inside].tolist(),'incidentTriangleIDs':incident.tolist(),'armJointNames':[names[i]for i in arm],'armInfluenceSummary':{'vertices':len(ids),'anyPositiveVertices':int((armW[ids]>0).sum()),'over1percentVertices':int((armW[ids]>.01).sum()),'maximum':float(armW[ids].max()),'mean':float(armW[ids].mean()),'percentiles':np.percentile(armW[ids],[0,50,90,99,100]).tolist()},'largestArmWeightWitnesses':[{'vertexID':int(i),'position':pos[i].tolist(),'weights19':W[i].tolist(),'armInfluence':float(armW[i]),'incidentTriangleIDs':np.flatnonzero((T==i).any(1)).tolist()}for i in witness]}
report={'sources':rig,'bindingComparisons':{'V5vs34WorldRestExact':bool(np.array_equal(rest,G.rest())),'V5vsC19WorldRestExact':bool(np.array_equal(rest,C.rest())),'V5vs34InverseBindExact':bool(np.array_equal(ib,G.ib())),'V5vsC19InverseBindExact':bool(np.array_equal(ib,C.ib()))},'fieldComparison':compare,'explicitChildAxes':axes,'pivotSurfaceEvidence':pivots,'centralTorsoROI':roi,'unitsAndHandedness':{'sourceSceneHasUnitTag':False,'coordinateConventionEvidence':'Existing game rider pose utilities express contacts/segments in metres; source rest pelvisY~0.92 and headY~1.65, identity mesh scale and determinant+1. glTF convention right-handed, Y-up. Left named limb has positive Z; X is fore/aft by existing game adapter. No scale or basis reset performed.','bodyBounds':np.stack([pos.min(0),pos.max(0)]).tolist(),'warning':'Legal affine transforms and measured surface proximity do not establish anatomical pivot placement, skeletal naturalness, head-neck clearance or moving appearance.'}}
(O/'raw-foundation.json').write_text(json.dumps(report,indent=2)+'\n')
payload={'source':str(V.p),'sourceSHA256':V.h,'fixture':str(F),'fixtureSHA256':sha(fb),'jointNames':names,'restColumnMajor':rest.transpose(0,2,1).reshape(19,16).tolist(),'inverseBindColumnMajor':ib.transpose(0,2,1).reshape(19,16).tolist(),'ROI':roi,'meshes':[]}
for mi,mesh in enumerate(V.d['meshes']):
 for pi,p in enumerate(mesh['primitives']):
  attrs,tr=V.primitive(mi,pi);payload['meshes'].append({'mesh':mi,'primitive':pi,'attrs':{k:v.tolist()for k,v in attrs.items()},'indices':tr.ravel().tolist()})
(S/'raw-input.json').write_text(json.dumps(payload,separators=(',',':'))+'\n');np.savez_compressed(S/'raw-core.npz',positions=pos[ids],joints=J[ids],weights=runtimeW[ids],vertexIDs=ids,rest=rest,inverseBind=ib)
for g in [C,G,V]:assert g.p.read_bytes()==g.raw
print(json.dumps({'roi':roi['armInfluenceSummary'],'binding':report['bindingComparisons'],'axisLengths':[(x['bone'],x['lengthM'])for x in axes]}))
ga,gt=G.primitive(0,0);sourceW=np.zeros((len(ga['POSITION']),19))
for k in range(4):np.add.at(sourceW,(np.arange(len(sourceW)),ga['JOINTS_0'][:,k]),ga['WEIGHTS_0'][:,k])
sourceArm=sourceW[:,arm].sum(1)
(O/'source34-core-comparison.json').write_text(json.dumps({'source34CoreArmInfluenceMax':float(sourceArm[ids].max()),'source34CorePositiveCount':int((sourceArm[ids]>0).sum()),'V5CorePositionsChangedVs34':int(np.any(ga['POSITION'][ids]!=pos[ids],1).sum()),'source34ArmInfluenceOutsideCorePositiveCount':int((sourceArm>0).sum()),'V5ArmInfluenceOutsideCorePositiveCount':int((armW>0).sum()),'coreBounds':roi['limits'],'pivotNote':'Nearest mesh surface distance measures relation to cloth, not joint inside skin or anatomical pivot correctness.'},indent=2)+'\n')

metadata=json.loads(V.d['nodes'][2]['extras']['rockhopRiderContactAdapter']);contact=[]
for side,h in metadata['hands'].items():
 ancestral=np.array(h['sourceHandRestMatrix']);current=rest[idx['hand.'+side]];contact.append({'side':side,'targetWorldQuaternion':h['targetWorldQuaternion'],'targetQuaternionLength':float(np.linalg.norm(h['targetWorldQuaternion'])),'ancestralSourceHandRestMatrixVsActualCurrentMaximumComponentDifference':float(abs(ancestral-current).max()),'currentHandRestColumnMajor':current.T.reshape(16).tolist(),'gripMorphName':h['gripMorphName']})
(O/'contact-metadata-provenance.json').write_text(json.dumps({'sourceSHA256':V.h,'metadataSource':metadata['source'],'metadataDeclaredUniformScale':metadata['declaredUniformScale'],'actualMeshWorldUniformScale':1.0,'hands':contact,'interpretation':'Ancestor sourceHandRestMatrix/native axis/declaredScale fields are retained provenance; they are not current exported binding. Inspected private adapter reads version/hands.targetWorldQuaternion/gripMorphName/legacyAnkleToSoleDisplacement, and captures current q0/inverse binds. Do not feed ancestral sourceHandRestMatrix into fresh C19 binding or reapply declaredUniformScale. Semantic contact acceptance requires parent production physics playback.'},indent=2)+'\n')
