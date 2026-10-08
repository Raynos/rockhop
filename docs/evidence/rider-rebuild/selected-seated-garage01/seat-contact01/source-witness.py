import json, struct, hashlib
from pathlib import Path
root=Path('/Users/raynos/projects/games/rockhop')
report_path=root/'harness/out/rider-rebuild/selected-seated-garage01/seat-contact01.json'
report=json.loads(report_path.read_text());source=root/report['inputs']['source']['path']
contract_path=Path(report['inputs']['contract']['path']);contract_path=contract_path if contract_path.is_absolute() else root/contract_path
contract_bytes=contract_path.read_bytes();assert hashlib.sha256(contract_bytes).hexdigest()==report['inputs']['contract']['sha256']
contract=json.loads(contract_bytes);assert contract['glbSHA256']==report['inputs']['source']['sha256']
bones={r['name']:r for r in contract['nativeRest']['bones']};axis=bones['DEF-thigh.R.001'];a,b=axis['head'],axis['tail'];delta=[q-p for p,q in zip(a,b)];length2=sum(x*x for x in delta)
with source.open('rb') as f:
 assert f.read(4)==b'glTF';f.seek(12);n=struct.unpack('<I',f.read(4))[0];assert f.read(4)==b'JSON';header=f.read(n);d=json.loads(header);base=28+n
 node=next(n for n in d['nodes'] if n.get('name')=='RiderJeans');assert node.get('translation',[0,0,0])==[0,0,0] and node.get('rotation',[0,0,0,1])==[0,0,0,1] and node.get('scale',[1,1,1])==[1,1,1] and 'matrix' not in node
 p=d['meshes'][node['mesh']]['primitives'][0];skin=d['skins'][node['skin']]
 def read(name,row):
  ac=d['accessors'][p['attributes'][name]];v=d['bufferViews'][ac['bufferView']];assert not v.get('extensions')
  fmt,width,denom={5126:('f',4,1),5125:('I',4,4294967295),5123:('H',2,65535),5121:('B',1,255)}[ac['componentType']];count={'SCALAR':1,'VEC3':3,'VEC4':4}[ac['type']]
  f.seek(base+v.get('byteOffset',0)+ac.get('byteOffset',0)+row*v.get('byteStride',width*count));values=struct.unpack('<'+fmt*count,f.read(width*count))
  return [x/denom if ac.get('normalized') else x for x in values]
 witness=report['bikes'][0]['snapshots'][0]['witness'];rows=[]
 for row,native in zip(witness['jeansDecodedVertexRows'],witness['jeansNativeVertexIDs']):
  assert read('_NATIVE_ID',row)[0]==native
  xyz=read('POSITION',row);point=[xyz[0],-xyz[2],xyz[1]];t=sum((x-y)*z for x,y,z in zip(point,a,delta))/length2;closest=[x+t*y for x,y in zip(a,delta)]
  fields=[[d['nodes'][skin['joints'][j]]['name'],w] for j,w in zip(read('JOINTS_0',row),read('WEIGHTS_0',row)) if w>0]
  rows.append({'decodedRow':row,'nativeID':native,'restGLB':xyz,'restNative':point,'namedFOUR':fields,'thigh001AxisProgress':t,'thigh001AxisClosest':closest,'radialDistanceFromThigh001M':sum((x-y)**2 for x,y in zip(point,closest))**.5,'nativePelvisHeightAboveVertexM':bones['DEF-spine']['head'][2]-point[2]})
result={'accepted':False,'recipeSHA256':hashlib.sha256(Path(__file__).read_bytes()).hexdigest(),'measurement':{'path':str(report_path.relative_to(root)),'sha256':hashlib.sha256(report_path.read_bytes()).hexdigest()},'source':report['inputs']['source'],'sourceIdentity':'Inherited exact served-source pin from played/measurement receipts; this focused job does not rehash or scan the full350MB source. Direct accessor seeks verify the3 native IDs, fields and positions.','sourceJSONSHA256':hashlib.sha256(header).hexdigest(),'contract':report['inputs']['contract'],'nativeRightThigh001':axis,'nativePelvis':bones['DEF-spine'],'vertices':rows,'minimumWitness':witness,'interpretation':'All3 source vertices are medial to and within the distal right thigh001 segment, about0.32–0.34m below native pelvis; this minimum is not a posterior/buttock-floor witness. Opposing sloping saddle-nose side faces and tiny projected overlap do not establish signed solid penetration or load-bearing saddle support.','limits':['No posterior patch or seating pass. No full-source scan, geometry/pose/runtime edit, or global closed-volume claim.']}
out=root/'harness/out/rider-rebuild/selected-seated-garage01/seat-witness01.json';assert not out.exists();out.write_text(json.dumps(result,indent=2)+'\n');print(json.dumps({'output':str(out),'vertices':rows,'accepted':False}))
