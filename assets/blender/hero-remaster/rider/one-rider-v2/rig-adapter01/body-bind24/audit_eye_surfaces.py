"""Read-only CPU geometry/texture distinction; never a visual grade or a new fit."""
from pathlib import Path
import hashlib,io,json,struct
import numpy as np
from PIL import Image
ROOT=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01')
OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind24')
source=ROOT/'body-bind22/skin-field01/rider.glb';raw=source.read_bytes();n=struct.unpack_from('<I',raw,12)[0];doc=json.loads(raw[20:20+n]);binary=raw[28+n:]
assert hashlib.sha256(raw).hexdigest()=='cc20ab813669b628c8e5d21596b655188d7188770adc374377cebf40769232ff'
def arr(index):
 a=doc['accessors'][index];v=doc['bufferViews'][a['bufferView']];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4}[a['type']];dtype={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}[a['componentType']];size=np.dtype(dtype).itemsize
 return np.ndarray((a['count'],width),dtype=dtype,buffer=binary,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',width*size),size)).copy()
rows=[]
for eye,cornea,opaque,cy,cz in [('negativeZ',3,4,1.697,-.0332),('positiveZ',5,6,1.6965,.032)]:
 surfaces={}
 for name,index in [('cornea',cornea),('irisSclera',opaque)]:
  p=doc['meshes'][1]['primitives'][index];pos=arr(p['attributes']['POSITION']).astype(float);normal=arr(p['attributes']['NORMAL']).astype(float);tri=arr(p['indices']).reshape(-1,3);joints=arr(p['attributes']['JOINTS_0']);weights=arr(p['attributes']['WEIGHTS_0'])
  assert np.isfinite(pos).all() and np.isfinite(normal).all()
  assert (joints[:,0]==4).all() and (weights[:,0]==1).all() and (weights[:,1:]==0).all()
  radius=np.linalg.norm(pos[:,1:]-[cy,cz],axis=1)
  ids=np.flatnonzero((radius<.0045)&(normal[:,0]>0))
  tilt=np.degrees(np.arctan2(np.linalg.norm(normal[ids,1:],axis=1),normal[ids,0]))
  surfaces[name]={'primitive':index,'materialIndex':p['material'],'renderVertices':len(pos),'triangles':len(tri),'centralProbeRadiusMM':4.5,'centralFrontFacingVertices':len(ids),'centralNormalTiltDegrees':np.percentile(tilt,[0,25,50,75,100]).tolist() if len(ids) else [],'centralXRange':np.percentile(pos[ids,0],[0,50,100]).tolist() if len(ids) else [],'normalLengthRange':np.percentile(np.linalg.norm(normal,axis=1),[0,100]).tolist(),'source19BoneHeadWeightExact':True}
 rows.append({'eye':eye,'probeCentreYZ':[cy,cz],'surfaces':surfaces,'centralAxialGapOfMaximaMM':(surfaces['cornea']['centralXRange'][-1]-surfaces['irisSclera']['centralXRange'][-1])*1000})
mat=doc['materials'][6];tex=doc['textures'][mat['pbrMetallicRoughness']['baseColorTexture']['index']];image=doc['images'][tex['source']];view=doc['bufferViews'][image['bufferView']];png=binary[view.get('byteOffset',0):view.get('byteOffset',0)+view['byteLength']]
bitmap=np.array(Image.open(io.BytesIO(png)).convert('RGBA'))
report={'status':'PASS read-only actual donor geometry and image census; aperture/fit unchanged and ungraded','sourceSHA256':hashlib.sha256(raw).hexdigest(),'eyes':rows,'opaqueEyeImage':{'imageIndex':tex['source'],'dimensions':list(bitmap.shape[:2][::-1]),'PNG_SHA256':hashlib.sha256(png).hexdigest(),'alphaRange':[int(bitmap[:,:,3].min()),int(bitmap[:,:,3].max())]},'inspectedActualFrames':['body22/played01/actual-before-after-textured.jpg','body22/played01/actual-before-after-gray.jpg','body22/played01/textured/decoded-001.jpg','body22/played01/textured/decoded-002.jpg'],'distinction':['Actual corneal surface has varying front normals and sits ahead of opaque donor surfaces; it is not a flat decal.','Runtime discards that surface, so its actual curved optical response is missing.','The remaining exposed iris/aperture impression can still reflect fixed geometry/placement, which this trial does not change.','Central vertex axial maxima are measurements, not triangle/ray clearance proofs; prior body20 actual-export aperture and clearance receipts remain the geometric authority.'],'limits':['No model, GPU, render or production changes.','4.5mm central probes describe existing geometry only; no cut/fit size was swept.','This does not establish that restoring cornea will reach7/10.']}
assert source.read_bytes()==raw
(OUT/'source-eye-surface-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
