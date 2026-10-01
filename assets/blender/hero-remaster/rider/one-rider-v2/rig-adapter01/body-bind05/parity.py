"""Compare exported source data before private contact morphs, without editing."""
from pathlib import Path
import hashlib,json,struct
BASE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
OUT=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind05')
def read(p):
 raw=p.read_bytes();length,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
 j=json.loads(raw[20:20+length]);n,k=struct.unpack_from('<II',raw,20+length);assert k==0x004e4942
 return j,raw[28+length:28+length+n]
def view(j,b,i):
 v=j['bufferViews'][i];start=v.get('byteOffset',0);return b[start:start+v['byteLength']]
def accessor(j,b,i):
 a=j['accessors'][i];assert 'sparse' not in a
 v=j['bufferViews'][a['bufferView']];size={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]*{5121:1,5123:2,5125:4,5126:4}[a['componentType']]
 stride=v.get('byteStride',size);start=v.get('byteOffset',0)+a.get('byteOffset',0)
 return b''.join(b[start+t*stride:start+t*stride+size] for t in range(a['count']))
a,ab=read(BASE/'body-bind04/rider.glb');c,cb=read(BASE/'body-bind05/rider.glb');rows=[]
assert len(a['meshes'])==len(c['meshes'])
for ma,mc in zip(a['meshes'],c['meshes']):
 assert ma['name']==mc['name'] and len(ma['primitives'])==len(mc['primitives'])
 for pa,pc in zip(ma['primitives'],mc['primitives']):
  assert pa['attributes'].keys()==pc['attributes'].keys()
  for name,ai in pa['attributes'].items():
   av=accessor(a,ab,ai);cv=accessor(c,cb,pc['attributes'][name]);exact=av==cv;error=0.0
   if not exact:
    assert name=='NORMAL' and len(av)==len(cv),(ma['name'],name)
    va=struct.unpack('<'+'f'*(len(av)//4),av);vc=struct.unpack('<'+'f'*(len(cv)//4),cv);error=max(abs(x-y) for x,y in zip(va,vc));assert error<1e-3,error
   rows.append({'mesh':ma['name'],'attribute':name,'byteExact':exact,'maxComponentError':error})
  assert accessor(a,ab,pa['indices'])==accessor(c,cb,pc['indices'])
assert len(a['skins'])==len(c['skins'])
for sa,sc in zip(a['skins'],c['skins']):
 assert [a['nodes'][i]['name'] for i in sa['joints']]==[c['nodes'][i]['name'] for i in sc['joints']]
 assert accessor(a,ab,sa['inverseBindMatrices'])==accessor(c,cb,sc['inverseBindMatrices'])
assert a['materials']==c['materials']
assert len(a['images'])==len(c['images'])
for ia,ic in zip(a['images'],c['images']):assert view(a,ab,ia['bufferView'])==view(c,cb,ic['bufferView'])
for aa,ac in zip(a['animations'],c['animations']):
 assert aa['name']==ac['name'];assert len(aa['samplers'])==len(ac['samplers'])
 for sa,sc in zip(aa['samplers'],ac['samplers']):
  for name in ['input','output']:assert accessor(a,ab,sa[name])==accessor(c,cb,sc[name])
report={'sourceSHA256':hashlib.sha256((BASE/'body-bind04/rider.glb').read_bytes()).hexdigest(),'rows':rows,'indicesByteExact':True,'inverseBindsByteExact':True,'materialsAndImageBytesExact':True,'originalAnimationAccessorBytesExact':True,'limits':'Morph targets, virtual grip socket positions and explicit adapter metadata deliberately added. No rendered acceptance implied.'}
(OUT/'source-export-parity.json').write_text(json.dumps(report,indent=2)+'\n');print('SOURCE_EXPORT_PARITY_PASS')
