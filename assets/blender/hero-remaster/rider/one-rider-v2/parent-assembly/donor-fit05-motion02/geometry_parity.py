"""Compare exported geometry arrays; account for declared bake blend colors."""
from pathlib import Path
import json,struct,hashlib
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/parent-assembly')
def arrays(path):
 raw=path.read_bytes();length=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+length]);start=20+length;size=struct.unpack_from('<I',raw,start)[0];binary=raw[start+8:start+8+size];sizes={5120:1,5121:1,5122:2,5123:2,5125:4,5126:4};width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16};rows=[];aux=[]
 for mesh in doc['meshes']:
  for primitive in mesh['primitives']:
   row={'mesh':mesh['name'],'attributes':{}}
   for key,index in dict(primitive['attributes'],indices=primitive['indices']).items():
    if key.startswith('COLOR_'):aux.append(key);continue
    a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];offset=v.get('byteOffset',0)+a.get('byteOffset',0);w=sizes[a['componentType']]*width[a['type']];stride=v.get('byteStride',w);data=b''.join(binary[offset+i*stride:offset+i*stride+w] for i in range(a['count']));row['attributes'][key]={'SHA256':hashlib.sha256(data).hexdigest(),'count':a['count'],'type':a['type'],'componentType':a['componentType']}
   rows.append(row)
 return rows,sorted(set(aux))
old,oldColor=arrays(ROOT/'donor-fit04-correction01/rider.glb');new,newColor=arrays(ROOT/'donor-fit05/rider.glb');assert old==new
report={'allPrimitivePositionNormalUVIndexArraysExact':True,'addedAuxiliaryColorAttributes':sorted(set(newColor)-set(oldColor)),'diagnosticCorrection':'Initial all-attribute equality included newlydeclared bake blend COLOR_2; geometric parity correctly separates auxiliary colors','source04':old,'source05':new,'limits':'Texture/materialdata and auxiliaryCOLOR_2 differ; gray04 applies toexact geometric arrays, not05PBR'}
Path('docs/evidence/hero-remaster/one-rider-v2/parent-assembly/donor-fit05-motion02/geometry-parity04-05.json').write_text(json.dumps(report,indent=2)+'\n')
