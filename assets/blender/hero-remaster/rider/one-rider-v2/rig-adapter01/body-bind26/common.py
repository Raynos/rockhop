"""Byte-conserving GLB access for isolated CPU diagnostic trial."""
from pathlib import Path
import json,struct,hashlib
import numpy as np
SOURCE=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/guarded-correction01/rider.glb')
RUN=SOURCE.parent.parent.parent/'body-bind26'
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind26')
def sha(b):return hashlib.sha256(b).hexdigest()
def load():
 raw=SOURCE.read_bytes();assert sha(raw)=='b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754';n=struct.unpack_from('<I',raw,12)[0];j=json.loads(raw[20:20+n]);start=28+n;binary=raw[start:];p=j['meshes'][0]['primitives'][0];assert p['material']==0;return raw,j,binary,p,start
DT={5121:np.dtype('u1'),5123:np.dtype('<u2'),5125:np.dtype('<u4'),5126:np.dtype('<f4')};LANES={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}
def accessor(j,b,i):
 a=j['accessors'][i];assert 'sparse' not in a;v=j['bufferViews'][a['bufferView']];d=DT[a['componentType']];n=LANES[a['type']];stride=v.get('byteStride',d.itemsize*n);at=v.get('byteOffset',0)+a.get('byteOffset',0);return np.ndarray((a['count'],n),d,b,at,(stride,d.itemsize)).copy(),at,stride
