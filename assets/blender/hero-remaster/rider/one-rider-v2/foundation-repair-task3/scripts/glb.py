import struct,json,numpy as np
from pathlib import Path
class GLB:
 def __init__(self,p):
  self.path=Path(p);self.raw=self.path.read_bytes(); n=struct.unpack_from('<I',self.raw,12)[0];self.j=json.loads(self.raw[20:20+n]);self.bin=bytearray(self.raw[28+n:])
 def array(self,i):
  a=self.j['accessors'][i];v=self.j['bufferViews'][a['bufferView']];dt={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']]; k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']];return np.ndarray((a['count'],k),dtype=dt,buffer=self.bin,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',np.dtype(dt).itemsize*k),np.dtype(dt).itemsize))
 def write(self,p):
  j=json.dumps(self.j,separators=(',',':')).encode();j+=b' '*((-len(j))%4);b=bytes(self.bin);b+=b'\0'*((-len(b))%4);Path(p).write_bytes(struct.pack('<III',0x46546c67,2,28+len(j)+len(b))+struct.pack('<II',len(j),0x4e4f534a)+j+struct.pack('<II',len(b),0x004e4942)+b)
if __name__=='__main__':
 g=GLB('baseline/rider.glb');print([(m['name'],[(g.array(p['attributes']['POSITION']).shape,p['attributes']) for p in m['primitives']]) for m in g.j['meshes']]);print([(i,g.j['nodes'][n]['name']) for i,n in enumerate(g.j['skins'][0]['joints'])])
