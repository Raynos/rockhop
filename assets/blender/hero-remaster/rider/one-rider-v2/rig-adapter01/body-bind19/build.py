"""Append measured local hip morphs, retaining all current11 source BIN bytes."""
from pathlib import Path
import json,struct,hashlib
import numpy as np
np.seterr(all='raise')
root=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
source=root/'body-bind11/guarded-correction01/rider.glb';run=root/'body-bind19/morph01';run.mkdir(parents=True,exist_ok=True)
out=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind19/morph01');out.mkdir(parents=True,exist_ok=True)
raw=source.read_bytes();sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(raw)=='b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);binary=bytearray(raw[28+n:]);original=bytes(binary)
m=json.loads(Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind19/arap-cpu/pose-manifest.json').read_text())
bm=json.loads(Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind16/baseline-cpu-affine02/pose-manifest.json').read_text())
p=m['primitives'][0];boneNames=p['bones'];pelvis=boneNames.index('pelvis');thighs=[boneNames.index('thighL'),boneNames.index('thighR')]
def read(rec,n,folder):
 raw=(root/folder/rec['file']).read_bytes();assert sha(raw)==rec['sha256'];return np.frombuffer(raw,dtype='<f8').reshape(-1,n).copy()
def quat(mat):
 # Same column normalization and trace formula as Three Matrix4.decompose.
 r=mat[:3,:3].copy();r/=np.linalg.norm(r,axis=0)[None,:];trace=np.trace(r)
 if trace>0:
  s=.5/np.sqrt(trace+1);q=np.array([(r[2,1]-r[1,2])*s,(r[0,2]-r[2,0])*s,(r[1,0]-r[0,1])*s,.25/s])
 else:
  k=np.argmax(np.diag(r));k1=(k+1)%3;k2=(k+2)%3;s=2*np.sqrt(1+r[k,k]-r[k1,k1]-r[k2,k2]);q=np.zeros(4);q[k]=.25*s;q[k1]=(r[k,k1]+r[k1,k])/s;q[k2]=(r[k,k2]+r[k2,k])/s;q[3]=(r[k2,k1]-r[k1,k2])/s
 return q/np.linalg.norm(q)
def mul(a,b):return np.r_[a[3]*b[:3]+b[3]*a[:3]+np.cross(a[:3],b[:3]),a[3]*b[3]-a[:3]@b[:3]]
def add(values):
 a=np.asarray(values,dtype='<f4');assert np.isfinite(a).all();at=len(binary);assert at%4==0;binary.extend(a.tobytes());view=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':at,'byteLength':a.nbytes,'target':34962});ix=len(j['accessors']);j['accessors'].append({'bufferView':view,'componentType':5126,'count':len(a),'type':'VEC3','min':a.min(0).tolist(),'max':a.max(0).tolist()});return ix
normal=read(p['attributes']['normal'],3,'body-bind19/arap-cpu');keys=[]
mesh=j['meshes'][0];originalTargets=len(mesh['primitives'][0]['targets']);assert originalTargets==2
for row,base in zip(m['rows'],bm['rows']):
 assert row['i']==base['i'];i=row['i'];path=root/'body-bind19/arap-cpu'/f'sample{i}-mesh0-corrective-delta.f64';delta=np.fromfile(path,dtype='<f8').reshape(-1,3);assert len(delta)==p['attributes']['position']['count']
 F=read(base['dump'][0]['skinMatrices'],16,'body-bind16/baseline-cpu-affine02').reshape(-1,4,4).transpose(0,2,1)
 posedNormals=read(row['dump'][0]['gpuRuleSkinnedNormals'],3,'body-bind19/arap-cpu');changed=np.linalg.norm(delta,axis=1)>0
 sourceN=normal.copy();sourceN[changed]=np.linalg.solve(F[changed,:3,:3],posedNormals[changed,:,None])[:,:,0];sourceN[changed]/=np.linalg.norm(sourceN[changed],axis=1,keepdims=True)
 normalDelta=sourceN-normal;assert np.array_equal(normalDelta[~changed],np.zeros_like(normalDelta[~changed]))
 for pi,primitive in enumerate(mesh['primitives']):
  count=j['accessors'][primitive['attributes']['POSITION']]['count']
  primitive['targets'].append({'POSITION':add(delta if pi==0 else np.zeros((count,3))), 'NORMAL':add(normalDelta if pi==0 else np.zeros((count,3)))})
 name=f'hipCorrective.sample{i}';mesh['extras']['targetNames'].append(name);mesh['weights'].append(0)
 mats=read(base['dump'][0]['jointTransforms'],16,'body-bind16/baseline-cpu-affine02').reshape(-1,4,4).transpose(0,2,1)
 qp=quat(mats[pelvis]);qp[:3]*=-1;features=[mul(qp,quat(mats[k])).tolist() for k in thighs]
 keys.append({'sample':i,'name':name,'relativeSkinQuaternions':features,'deltaSHA256':sha(delta.astype('<f4').tobytes()),'changedVertices':int(changed.sum())})
metadata={'version':1,'sourceSHA256':sha(raw),'keys':keys,'jointNames':['pelvis','thigh.L','thigh.R'],'metric':'sum of squared relative skin quaternion geodesic angles','interpolation':'positive normalized inverse squared distance, epsilon1e-6rad; compact support nearest .15.. .35rad','nearestFullRadiusRad':.15,'nearestZeroRadiusRad':.35,'epsilonRad':1e-6,'baseline':'zero outside trained pose region; physics bones never modified','scope':'unaccepted measured private hip corrective prototype'}
meshNode=next(x for x in j['nodes'] if x.get('mesh')==0);meshNode.setdefault('extras',{})['rockhopHipCorrective']=json.dumps(metadata,separators=(',',':'))
assert bytes(binary[:len(original)])==original and source.read_bytes()==raw
assert all(len(p['targets'])==8 for p in mesh['primitives'])
assert not any(channel['target']['path']=='weights' for animation in j.get('animations',[]) for channel in animation['channels'])
j['buffers'][0]['byteLength']=len(binary);js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((-len(js))%4);result=struct.pack('<III',0x46546c67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
candidate=run/'rider.glb'
if candidate.exists():assert candidate.read_bytes()==result,'Frozen candidate must reproduce exactly'
else:candidate.write_bytes(result)
report={'sourceSHA256':sha(raw),'candidateSHA256':sha(result),'candidate':str(candidate),'originalBinaryBytesExact':len(original),'originalBinarySHA256':sha(original),'originalGeometrySkinMaterialsTexturesBindsAnimationsSocketsRetained':True,'addedTargets':keys,'metadata':metadata,'sourceUnchanged':True,'limits':'Rigged private morph prototype, no continuous motion/silhouette gate yet. All added targets remain zero without explicit private rig driver.'}
(out/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');(out/'model-map.json').write_text(json.dumps({'models/rider-street-mustard.glb':str(candidate),'models/rider-street-mustard-lod.glb':str(candidate)},indent=2)+'\n')
print(json.dumps({'candidateSHA256':sha(result),'targets':len(keys),'originalBINExact':len(original)}))
