from pathlib import Path
import json,struct,math,hashlib
P=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind02/rider.glb');O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind02')
b=P.read_bytes();n=struct.unpack_from('<I',b,12)[0];j=json.loads(b[20:20+n]);blob=b[28+n:];types={5126:('f',4),5123:('H',2),5121:('B',1),5125:('I',4)};counts={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def values(i):
 a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];fmt,size=types[a['componentType']];c=counts[a['type']];start=v.get('byteOffset',0)+a.get('byteOffset',0);stride=v.get('byteStride',size*c)
 return [struct.unpack_from('<'+fmt*c,blob,start+k*stride) for k in range(a['count'])]
s=j['skins'];assert len(s)==1 and len(s[0]['joints'])==19
names=[j['nodes'][i]['name'] for i in s[0]['joints']];assert len(set(names))==19
rows=[]
for m in j['meshes']:
 for p in m['primitives']:
  w=values(p['attributes']['WEIGHTS_0']);ids=values(p['attributes']['JOINTS_0']);maxerr=max(abs(sum(a)-1) for a in w);assert maxerr<1e-6 and all(0<=i<19 for q in ids for i in q) and all(math.isfinite(x) and x>=0 for q in w for x in q)
  rows.append({'mesh':m['name'],'vertices':len(w),'weightSumMaxError':maxerr,'maxInfluences':max(sum(x>0 for x in q) for q in w)})
assert [a['name'] for a in j['animations']]==['stand_to_sit_probe']
(O/'export-validation.json').write_text(json.dumps({'GLBSHA256':hashlib.sha256(b).hexdigest(),'boneCount':19,'jointNames':names,'skins':1,'animationNames':['stand_to_sit_probe'],'primitives':rows,'limits':'Byte structure/weights only; inverse bind/moving production load and contact quality remain separate checks'},indent=2)+'\n')
print('VALID_NEW19_EXPORT',len(rows))
