"""Transfer exported weights into original GLB, preserving every other byte."""
from pathlib import Path
import json,struct,hashlib
BASE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind07')
def read(p):
 raw=p.read_bytes();length,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
 j=json.loads(raw[20:20+length]);n,k=struct.unpack_from('<II',raw,20+length);assert k==0x004e4942
 return j,bytearray(raw[28+length:28+length+n]),raw
sizes={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16};components={5121:1,5123:2,5125:4,5126:4}
def locations(j,i):
 a=j['accessors'][i];assert 'sparse' not in a;v=j['bufferViews'][a['bufferView']];size=sizes[a['type']]*components[a['componentType']];stride=v.get('byteStride',size);start=v.get('byteOffset',0)+a.get('byteOffset',0)
 return [(start+t*stride,size) for t in range(a['count'])]
def accessor(j,b,i):return b''.join(b[start:start+size] for start,size in locations(j,i))
a,ab,raw=read(BASE/'body-bind05/rider.glb');c,cb,_=read(BASE/'body-bind07/rider-export.glb');patched=bytearray(ab);rows=[];allowed=set()
assert len(a['meshes'])==len(c['meshes'])
for sa,sc in zip(a['skins'],c['skins']):
 assert [a['nodes'][i]['name'] for i in sa['joints']]==[c['nodes'][i]['name'] for i in sc['joints']]
 assert accessor(a,ab,sa['inverseBindMatrices'])==accessor(c,cb,sc['inverseBindMatrices'])
for ma,mc in zip(a['meshes'],c['meshes']):
 assert ma['name']==mc['name'];assert len(ma['primitives'])==len(mc['primitives'])
 for pa,pc in zip(ma['primitives'],mc['primitives']):
  assert accessor(a,ab,pa['attributes']['POSITION'])==accessor(c,cb,pc['attributes']['POSITION']),ma['name']
  assert accessor(a,ab,pa['attributes']['TEXCOORD_0'])==accessor(c,cb,pc['attributes']['TEXCOORD_0'])
  assert accessor(a,ab,pa['indices'])==accessor(c,cb,pc['indices'])
  for name in ['JOINTS_0','WEIGHTS_0']:
   av=accessor(a,ab,pa['attributes'][name]);cv=accessor(c,cb,pc['attributes'][name]);assert len(av)==len(cv)
   rows.append({'mesh':ma['name'],'material':pa['material'],'attribute':name,'changedBytes':sum(x!=y for x,y in zip(av,cv))})
   loc=locations(a,pa['attributes'][name]);cursor=0
   for start,size in loc:
    patched[start:start+size]=cv[cursor:cursor+size];cursor+=size;allowed.update(range(start,start+size))
for i,(x,y) in enumerate(zip(ab,patched)):
 if x!=y:assert i in allowed
# Reuse the source JSON chunk verbatim, including all nodes, material/image,
# animation, morph, bind/socket and explicit contact-adapter definitions.
length=struct.unpack_from('<I',raw,12)[0];result=raw[:28+length]+patched
assert len(result)==len(raw);dest=BASE/'body-bind07/rider.glb'
changes=[r for r in rows if r['changedBytes']]
assert changes and all(r['mesh'].startswith('Protected') and r['material']==0 for r in changes),changes
dest.write_bytes(result)
(OUT/'export-parity.json').write_text(json.dumps({'sourceSHA256':hashlib.sha256(raw).hexdigest(),'candidateSHA256':hashlib.sha256(result).hexdigest(),'sourceJSONByteExact':True,'allBytesOutsideSkinAccessorsExact':True,'onlyOriginalBodyMaterial0WeightsChanged':True,'changes':changes,'protected':'Rest positions, normals, UVs, indices, all morphs, NEWhood/gloves/head, images/materials, inversebinds, animation, sockets and adapter are byte-exact body05','limits':'No appearance, full-body deformation or contact acceptance implied'},indent=2)+'\n')
print('WEIGHTS_ONLY_GLBF_PATCH_PASS',changes)
