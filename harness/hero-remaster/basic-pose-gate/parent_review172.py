"""Read-only parent source/raw contract audit; no motion or art acceptance."""
import os
os.environ.setdefault('OPENBLAS_NUM_THREADS','2')
os.environ.setdefault('OMP_NUM_THREADS','2')
from pathlib import Path
import hashlib,json,struct
import numpy as np
R=Path('/Users/raynos/projects/games/rockhop')
E=R/'docs/evidence/hero-remaster/one-rider-v2/candidate-export172'
d=json.loads((E/'export-report.json').read_text())
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest()
def read(path):
 b=Path(path).read_bytes();magic,version,size=struct.unpack_from('<III',b)
 assert (magic,version,size)==(0x46546c67,2,len(b))
 n,k=struct.unpack_from('<II',b,12);assert k==0x4e4f534a
 j=json.loads(b[20:20+n]);m,k=struct.unpack_from('<II',b,20+n)
 assert k==0x004e4942 and 28+n+m==len(b)
 return j,b[28+n:]
def inventory(j):return [p for mesh in j['meshes'] for p in mesh['primitives']]
def array(j,b,i):
 a=j['accessors'][i];width={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 dtype=np.dtype({5120:'i1',5121:'u1',5122:'<i2',5123:'<u2',5125:'<u4',5126:'<f4'}[a['componentType']])
 def direct(vi,offset,count,w,dt):
  v=j['bufferViews'][vi];assert not v.get('extensions') and v.get('buffer',0)==0
  return np.ndarray((count,w),dtype=dt,buffer=b,offset=v.get('byteOffset',0)+offset,strides=(v.get('byteStride',dt.itemsize*w),dt.itemsize)).copy()
 x=direct(a['bufferView'],a.get('byteOffset',0),a['count'],width,dtype) if 'bufferView'in a else np.zeros((a['count'],width),dtype=dtype)
 if 'sparse'in a:
  s=a['sparse'];i=s['indices'];v=s['values'];ids=direct(i['bufferView'],i.get('byteOffset',0),s['count'],1,np.dtype({5121:'u1',5123:'<u2',5125:'<u4'}[i['componentType']])).ravel()
  x[ids]=direct(v['bufferView'],v.get('byteOffset',0),s['count'],width,dtype)
 return x
assert sha(d['source'])==d['sourceSHA256'] and sha(d['npz'])==d['npzSHA256'] and sha(d['output'])==d['outputSHA256']
s,sb=read(d['source']);o,ob=read(d['output']);sp,op=inventory(s),inventory(o)
assert len(sp)==len(op)==5 and len(s['skins'][0]['joints'])==19
assert ob[:len(sb)]==sb
for key in ['nodes','skins','materials','images','textures','samplers','animations']:assert s.get(key)==o.get(key),key
for p in [1,3,4]:assert sp[p]==op[p]
z=np.load(d['npz'],allow_pickle=False);rows=[]
for p in [0,2]:
 src,new=sp[p],op[p];old=len(array(s,sb,src['attributes']['POSITION']))
 for sem,key in [('POSITION','p'),('NORMAL','n'),('TEXCOORD_0','uv')]:assert np.array_equal(array(o,ob,new['attributes'][sem]),z[f'{key}{p}'].astype(np.float32))
 assert np.array_equal(array(o,ob,new['indices']).reshape(-1,3),z[f'tr{p}'])
 weights=array(o,ob,new['attributes']['WEIGHTS_0']);joints=array(o,ob,new['attributes']['JOINTS_0']);dense=np.zeros((len(weights),19),dtype=np.float32)
 assert np.isfinite(weights).all() and (weights>=0).all() and (joints<19).all()
 np.add.at(dense,(np.arange(len(weights))[:,None],joints),weights)
 assert np.array_equal(dense,z[f'W{p}'].astype(np.float32))
 for sem,ai in src['attributes'].items():
  for flag in ['componentType','type','normalized']:assert s['accessors'][ai].get(flag)==o['accessors'][new['attributes'][sem]].get(flag)
  if sem not in ['POSITION','NORMAL','TEXCOORD_0','JOINTS_0','WEIGHTS_0']:assert np.array_equal(array(s,sb,ai),array(o,ob,new['attributes'][sem])[:old])
 for st,nt in zip(src.get('targets',[]),new.get('targets',[])):
  for sem,ai in st.items():
   actual=array(o,ob,nt[sem]);assert np.array_equal(array(s,sb,ai),actual[:old])
   assert not np.any(actual[old:])
 if len(weights)>old:
  assert np.array_equal(array(o,ob,new['attributes']['TEXCOORD_1'])[old:],array(o,ob,new['attributes']['TEXCOORD_0'])[old:])
  assert not np.any(array(o,ob,new['attributes']['COLOR_2'])[old:])
 rows.append({'primitive':p,'oldRows':old,'totalRows':len(weights),'denseFloat32ReadbackExact':True,'originalAuxiliaryAndMorphRowsExact':True,'explicitNewGripMorphZeroAndUnusedColor2':True})
result={'status':'PARENT_RAW_AND_ARRAY_EXPORT_AUDIT_PASS_NO_MOTION_ACCEPTANCE','inputHashes':{d[k]:sha(d[k])for k in ['source','npz','output']},'sourceBINPrefixExact':True,'originalNodesSkins19BindPBRImagesAnimationsExact':True,'protectedGloveHeadCheekPrimitiveReferencesExact':[1,3,4],'rows':rows,'limits':['New clothing auxiliary/grip fields are explicitly authored definitions, not source-exact information.','Frozen06 diagnostic; latest07 construction not silently substituted.','No stock Three pose parity, moving garment/basic-pose, contact, Garage or mobile pass.']}
(E/'parent-review.json').write_text(json.dumps(result,indent=2)+'\n')
print(json.dumps({'status':result['status'],'rows':sum(r['totalRows']for r in rows)}))
