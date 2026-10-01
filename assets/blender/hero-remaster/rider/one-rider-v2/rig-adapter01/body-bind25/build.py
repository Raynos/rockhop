"""Append four measured sleeve morphs to untouched current11. CPU only."""
from pathlib import Path
import copy,json,struct,hashlib
import numpy as np
np.seterr(all='raise')
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
SOURCE=ROOT/'body-bind11/guarded-correction01/rider.glb'
RUN=ROOT/'body-bind25/morph01'
OUT=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind25/morph01')
TARGET=OUT.parent.parent/'body-bind23'
BASE=OUT.parent.parent/'body-bind21/baseline-cpu'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(rec,lanes):
 path=Path(rec['privatePath']) if 'privatePath' in rec else ROOT/'body-bind21/baseline-cpu'/rec['file']
 raw=path.read_bytes();assert sha(raw)==rec['sha256'];return np.frombuffer(raw,dtype='<f8').reshape(-1,lanes).copy()
def quaternion(mat):
 # Exact Three Matrix4.decompose column normalization and trace formula.
 r=mat[:3,:3].copy();r/=np.linalg.norm(r,axis=0)[None,:];trace=np.trace(r)
 if trace>0:
  s=.5/np.sqrt(trace+1);q=np.array([(r[2,1]-r[1,2])*s,(r[0,2]-r[2,0])*s,(r[1,0]-r[0,1])*s,.25/s])
 else:
  k=np.argmax(np.diag(r));k1=(k+1)%3;k2=(k+2)%3;s=2*np.sqrt(1+r[k,k]-r[k1,k1]-r[k2,k2]);q=np.zeros(4);q[k]=.25*s;q[k1]=(r[k,k1]+r[k1,k])/s;q[k2]=(r[k,k2]+r[k2,k])/s;q[3]=(r[k2,k1]-r[k1,k2])/s
 return q/np.linalg.norm(q)
def multiply(a,b):return np.r_[a[3]*b[:3]+b[3]*a[:3]+np.cross(a[:3],b[:3]),a[3]*b[3]-a[:3]@b[:3]]
raw=SOURCE.read_bytes();assert sha(raw)=='b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
length=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+length]);originalJSON=copy.deepcopy(j);binary=bytearray(raw[28+length:]);originalBIN=bytes(binary);originalAccessorCount=len(j['accessors']);originalViewCount=len(j['bufferViews'])
m=json.loads((TARGET/'pose-manifest.json').read_text());baseline=json.loads((BASE/'pose-manifest.json').read_text());assert m['sourceSHA256']==baseline['sourceSHA256']==sha(raw)
mesh=j['meshes'][0];assert len(mesh['primitives'])==3
assert mesh['extras']['targetNames']==['gripClosed.R','gripClosed.L'];assert len(mesh['weights'])==2
bones=m['primitives'][0]['bones'];jointNames=['chest','upperArm.L','forearm.L','upperArm.R','forearm.R'];jointIds=[bones.index(name.replace('.','')) for name in jointNames]
def add(values):
 a=np.asarray(values,dtype='<f4');assert np.isfinite(a).all();assert a.ndim==2 and a.shape[1]==3
 at=len(binary);assert at%4==0;binary.extend(a.tobytes());view=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':at,'byteLength':a.nbytes,'target':34962});ix=len(j['accessors']);j['accessors'].append({'bufferView':view,'componentType':5126,'count':len(a),'type':'VEC3','min':a.min(0).tolist(),'max':a.max(0).tolist()});return ix
keys=[]
for row,base in zip(m['rows'],baseline['rows']):
 assert row['i']==base['i'];sample=row['i'];assert sample in [114,186,304,426]
 delta=read(row['dump'][0]['correctiveDelta'],3);normalDelta=read(row['dump'][0]['normalCorrectiveDelta'],3);assert len(delta)==j['accessors'][mesh['primitives'][0]['attributes']['POSITION']]['count']
 name=f'sleeveCorrective.sample{sample}'
 for pi,primitive in enumerate(mesh['primitives']):
  count=j['accessors'][primitive['attributes']['POSITION']]['count'];assert len(primitive['targets'])==len(mesh['weights'])
  primitive['targets'].append({'POSITION':add(delta if pi==0 else np.zeros((count,3))),'NORMAL':add(normalDelta if pi==0 else np.zeros((count,3)))})
 mesh['extras']['targetNames'].append(name);mesh['weights'].append(0)
 mats=read(base['dump'][0]['jointTransforms'],16).reshape(-1,4,4).transpose(0,2,1);reference=quaternion(mats[jointIds[0]]);reference[:3]*=-1
 features=[]
 for joint in jointIds[1:]:
  q=multiply(reference,quaternion(mats[joint]));q/=np.linalg.norm(q);features.append(q.tolist())
 keys.append({'sample':sample,'name':name,'relativeSkinQuaternions':features,'positionDeltaSHA256':sha(delta.astype('<f4').tobytes()),'normalDeltaSHA256':sha(normalDelta.astype('<f4').tobytes()),'changedExportVertices':int(np.any(delta!=0,axis=1).sum())})
metadata={'version':1,'sourceSHA256':sha(raw),'keys':keys,'jointNames':jointNames,'reference':'chest skin quaternion; four arm skin quaternions relative to chest','metric':'sqrt(sum of four squared quaternion geodesic angles)','interpolation':'positive normalized inverse squared distance; epsilon1e-6rad; nearest smooth full-to-zero fade .15.. .35rad','nearestFullRadiusRad':.15,'nearestZeroRadiusRad':.35,'epsilonRad':1e-6,'runtimeAmplitude':'1-Garage stageBlend, zero when ragdoll active','baseline':'All added morphs zero without explicit private driver; zero outside trained pose support','scope':'Unaccepted private sleeve-corrective hypothesis; actual continuous-motion art judgment pending'}
node=next(n for n in j['nodes'] if n.get('mesh')==0);node.setdefault('extras',{})['rockhopSleeveCorrective']=json.dumps(metadata,separators=(',',':'))
assert all(len(p['targets'])==6 for p in mesh['primitives']);assert not any(c['target']['path']=='weights' for a in j.get('animations',[]) for c in a['channels']);assert bytes(binary[:len(originalBIN)])==originalBIN;assert SOURCE.read_bytes()==raw
# Prove all JSON differences are append-only accessor/views/targets/names/weights,
# the explicit new node metadata and total buffer length.
restored=copy.deepcopy(j);restored['accessors']=restored['accessors'][:originalAccessorCount];restored['bufferViews']=restored['bufferViews'][:originalViewCount]
restored['buffers']=copy.deepcopy(originalJSON['buffers']);restored['meshes'][0]['weights']=restored['meshes'][0]['weights'][:2];restored['meshes'][0]['extras']['targetNames']=restored['meshes'][0]['extras']['targetNames'][:2]
for p in restored['meshes'][0]['primitives']:p['targets']=p['targets'][:2]
restoredNode=next(n for n in restored['nodes'] if n.get('mesh')==0);del restoredNode['extras']['rockhopSleeveCorrective']
if not restoredNode['extras'] and 'extras' not in next(n for n in originalJSON['nodes'] if n.get('mesh')==0):del restoredNode['extras']
assert restored==originalJSON,'Unexpected original JSON mutation'
j['buffers'][0]['byteLength']=len(binary);js=json.dumps(j,separators=(',',':')).encode();js+=b' '*((-len(js))%4);result=struct.pack('<III',0x46546c67,2,28+len(js)+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary
RUN.mkdir(parents=True,exist_ok=True);OUT.mkdir(parents=True,exist_ok=True);candidate=RUN/'rider.glb'
if candidate.exists():assert candidate.read_bytes()==result,'Frozen candidate may not be overwritten'
else:candidate.write_bytes(result)
report={'source':str(SOURCE),'sourceSHA256':sha(raw),'candidate':str(candidate),'candidateSHA256':sha(result),'candidateBytes':len(result),'originalBinaryBytesExact':len(originalBIN),'originalBinarySHA256':sha(originalBIN),'originalGeometrySkinMaterialsTexturesBindsAnimationsSocketsRetained':True,'originalJSONRetainedExceptExplicitAppendFields':True,'originalTwoGripTargetsAndWeightsRetained':True,'zeroTargetsOnOtherTwoBodyPrimitives':True,'sourceUnchanged':True,'addedTargets':keys,'metadata':metadata,'limits':'Private rigged morph prototype only; no continuous-motion, collision or art acceptance. Source body23 contains up23.27cm posed and38.44cm source displacement.'}
(OUT/'build-report.json').write_text(json.dumps(report,indent=2)+'\n');(OUT/'metadata.json').write_text(json.dumps(metadata,indent=2)+'\n');(OUT/'model-map.json').write_text(json.dumps({'models/rider-street-mustard.glb':str(candidate),'models/rider-street-mustard-lod.glb':str(candidate)},indent=2)+'\n');print(json.dumps({'candidateSHA256':sha(result),'candidateBytes':len(result),'originalBINExact':len(originalBIN),'keys':len(keys)}))
