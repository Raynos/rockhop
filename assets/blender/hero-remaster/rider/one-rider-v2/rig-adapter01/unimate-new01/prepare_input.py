"""Retain the actual NEW mesh/bind and retime only its sitting sampler inputs."""
from pathlib import Path
import copy,hashlib,json,struct
R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
O=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/unimate-new01')
source=R/'body-bind04/rider.glb';raw=source.read_bytes();n,t=struct.unpack_from('<II',raw,12);assert t==0x4e4f534a
j=json.loads(raw[20:20+n]);bn,bt=struct.unpack_from('<II',raw,20+n);assert bt==0x004e4942
binary=raw[28+n:28+n+bn];original=binary;j['animations']=[a for a in j['animations'] if a['name']=='stand_to_sit_probe'];assert len(j['animations'])==1
clip=j['animations'][0];assert len(j['skins'][0]['joints'])==19
old=copy.deepcopy(j);newInputs={};rows=[];end=59/30
for sampler in clip['samplers']:
 i=sampler['input']
 if i not in newInputs:
  a=j['accessors'][i];v=j['bufferViews'][a['bufferView']];assert a['componentType']==5126 and a['type']=='SCALAR' and not a.get('sparse');stride=v.get('byteStride',4);start=v.get('byteOffset',0)+a.get('byteOffset',0)
  times=[struct.unpack_from('<f',binary,start+k*stride)[0] for k in range(a['count'])];factor=end/max(times);scaled=[x*factor for x in times]
  binary+=b'\0'*(-len(binary)%4);view=len(j['bufferViews']);j['bufferViews'].append({'buffer':0,'byteOffset':len(binary),'byteLength':4*len(scaled)})
  binary+=struct.pack('<'+'f'*len(scaled),*scaled);newInputs[i]=len(j['accessors']);j['accessors'].append({'bufferView':view,'componentType':5126,'count':len(scaled),'type':'SCALAR','min':[min(scaled)],'max':[max(scaled)]});rows.append({'oldAccessor':i,'newAccessor':newInputs[i],'sourceEnd':max(times),'newEnd':end,'factor':factor,'samples':len(times)})
 sampler['input']=newInputs[i]
assert binary[:len(original)]==original
for k in ['meshes','skins','nodes','materials','images','textures']:assert j.get(k)==old.get(k)
j['buffers'][0]['byteLength']=len(binary);binary+=b'\0'*(-len(binary)%4);payload=json.dumps(j,separators=(',',':')).encode();payload+=b' '*(-len(payload)%4)
out=struct.pack('<III',0x46546c67,2,28+len(payload)+len(binary))+struct.pack('<II',len(payload),0x4e4f534a)+payload+struct.pack('<II',len(binary),0x004e4942)+binary
p=R/'unimate-new01/input/RockhopWhiteRider.glb';p.parent.mkdir(parents=True,exist_ok=True);assert not p.exists();p.write_bytes(out)
report={'source':str(source),'sourceSHA256':hashlib.sha256(raw).hexdigest(),'input':str(p),'inputSHA256':hashlib.sha256(out).hexdigest(),'meshBindImagesOriginalBinaryPrefixExact':True,'jointCount':19,'clip':'stand_to_sit_probe','retiming':rows,'intendedFrames':60,'intendedFPS':30,'limits':'Only animation time inputs appended; actual preprocessing frame count must be measured, not assumed'}
O.mkdir(exist_ok=True,parents=True);(O/'input-parity.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
