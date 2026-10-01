"""Missing factorial control: fresh34binds with original11scalar skin weights."""
from pathlib import Path
import json,struct,hashlib,numpy as np
root=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01');out=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind36');out.mkdir(parents=True,exist_ok=True)
def load(p):
 raw=p.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return raw,json.loads(raw[20:20+n]),bytearray(raw[28+n:]),n
sha=lambda b:hashlib.sha256(b).hexdigest()
f,j,b,n=load(root/'body-bind34/rider.glb');old,k,ob,on=load(root/'body-bind11/guarded-correction01/rider.glb')
assert sha(f)=='adbac6f2949cec0f32a8e0cfa4cfabd02cce61e58dab4022209e23a605f31df7' and sha(old)=='b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
assert [j['nodes'][i]['name'] for i in j['skins'][0]['joints']]==[k['nodes'][i]['name'] for i in k['skins'][0]['joints']]
def accessor(doc,blob,ai):
 a=doc['accessors'][ai];v=doc['bufferViews'][a['bufferView']];assert 'sparse' not in a and 'byteStride' not in v
 width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];size={5121:1,5123:2,5125:4,5126:4}[a['componentType']];start=v.get('byteOffset',0)+a.get('byteOffset',0);length=width*size*a['count'];return a,start,length,bytes(blob[start:start+length])
changes=[];ranges=[]
for mi,(m,om) in enumerate(zip(j['meshes'],k['meshes'])):
 assert len(m['primitives'])==len(om['primitives'])
 for pi,(p,op) in enumerate(zip(m['primitives'],om['primitives'])):
  for name in ['POSITION','NORMAL','TEXCOORD_0']:
   assert accessor(j,b,p['attributes'][name])[3]==accessor(k,ob,op['attributes'][name])[3]
  assert accessor(j,b,p['indices'])[3]==accessor(k,ob,op['indices'])[3]
  for name in ['JOINTS_0','WEIGHTS_0']:
   a,start,length,before=accessor(j,b,p['attributes'][name]);oa,_,olen,replacement=accessor(k,ob,op['attributes'][name]);assert all(a.get(s)==oa.get(s) for s in ['count','type','normalized'])
   if name=='JOINTS_0':
    dtype={5121:'u1',5123:'<u2'};values=np.frombuffer(replacement,dtype=dtype[oa['componentType']]);replacement=values.astype(dtype[a['componentType']]).tobytes();assert np.array_equal(np.frombuffer(replacement,dtype=dtype[a['componentType']]),values)
   else:assert a['componentType']==oa['componentType']
   assert len(replacement)==length
   b[start:start+length]=replacement;ranges.append((start,start+length));changes.append({'mesh':mi,'primitive':pi,'attribute':name,'bytes':length,'old11FieldSHA256':sha(replacement),'fresh34FieldSHA256':sha(before),'changedBytes':sum(x!=y for x,y in zip(before,replacement))})
allow=np.zeros(len(b),dtype=bool)
for a,z in ranges:allow[a:z]=True
original=f[28+n:];changed=np.frombuffer(bytes(b),dtype='u1')!=np.frombuffer(original,dtype='u1');assert not (changed&~allow).any()
result=f[:28+n]+bytes(b);run=root/'body-bind36';run.mkdir(exist_ok=True);path=run/'rider.glb'
if path.exists():assert path.read_bytes()==result
else:path.write_bytes(result)
assert (root/'body-bind34/rider.glb').read_bytes()==f and (root/'body-bind11/guarded-correction01/rider.glb').read_bytes()==old
report={'status':'Unaccepted missing factorial causal control; no blend or threshold tuning','candidate':str(path),'candidateSHA256':sha(result),'candidateBytes':len(result),'sourceFresh34SHA256':sha(f),'sourceOriginal11SHA256':sha(old),'allFresh34JSONExact':True,'allFresh34NonSkinBINBytesExact':True,'original11AllFivePrimitiveSkinValuesExact':True,'original11AllFiveWeightBytesExact':True,'jointEncoding':'Original11uint8joint indices widened losslessly to fresh34uint16; original34JSON stays exact.','freshRigBindsAxesContactMetadataAndClipsExact':True,'changedBytes':int(changed.sum()),'fields':changes,'limits':['No geometry edits, weight blend, parameter sweep or original anatomy restoration.','Fresh skeleton with original scalar skin roles; CPU actual driver and moving appearance remain to be tested.','Not an accepted mixed asset or production source.']}
(out/'control-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'SHA':sha(result),'changedBytes':int(changed.sum())}))
