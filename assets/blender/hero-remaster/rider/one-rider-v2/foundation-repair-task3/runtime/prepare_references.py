"""Independent raw-glTF LBS/interpolation check plus parent keyed array comparisons.

Does not import the experiment rig generator or Three.js. Only writes runtime/.
"""
from pathlib import Path
import struct, json, copy, hashlib
import numpy as np

ROOT=Path(__file__).resolve().parent
parent=json.loads((ROOT.parent/'evidence/manifest.json').read_text())
out=ROOT/'references';out.mkdir(exist_ok=True)
def decode(p):
 raw=Path(p).read_bytes();n=struct.unpack_from('<I',raw,12)[0]
 return json.loads(raw[20:20+n]),raw[28+n:],hashlib.sha256(raw).hexdigest()
def array(doc,bin,i):
 a=doc['accessors'][i];k={'SCALAR':1,'VEC2':2,'VEC3':3,'VEC4':4,'MAT4':16}[a['type']]
 dt=np.dtype({5126:'<f4',5125:'<u4',5123:'<u2',5122:'<i2',5121:'u1',5120:'i1'}[a['componentType']])
 if 'bufferView'in a:
  v=doc['bufferViews'][a['bufferView']]
  result=np.ndarray((a['count'],k),dtype=dt,buffer=bin,offset=v.get('byteOffset',0)+a.get('byteOffset',0),strides=(v.get('byteStride',dt.itemsize*k),dt.itemsize)).astype(float)
 else: result=np.zeros((a['count'],k))
 if a.get('normalized'):
  result=result/np.iinfo(dt).max
  if dt.kind=='i':result=np.maximum(result,-1)
 if 'sparse'in a:
  s=a['sparse'];d=s['indices'];v=doc['bufferViews'][d['bufferView']]
  ids=np.frombuffer(bin,dtype={5121:'u1',5123:'<u2',5125:'<u4'}[d['componentType']],count=s['count'],offset=v.get('byteOffset',0)+d.get('byteOffset',0))
  d=s['values'];v=doc['bufferViews'][d['bufferView']]
  vals=np.frombuffer(bin,dtype=dt,count=s['count']*k,offset=v.get('byteOffset',0)+d.get('byteOffset',0)).reshape(-1,k)
  result[ids]=vals
 return result
def qmat(q):
 x,y,z,w=q/np.linalg.norm(q)
 return np.array([[1-2*(y*y+z*z),2*(x*y-z*w),2*(x*z+y*w)],[2*(x*y+z*w),1-2*(x*x+z*z),2*(y*z-x*w)],[2*(x*z-y*w),2*(y*z+x*w),1-2*(x*x+y*y)]])
def slerp(a,b,t):
 a=a/np.linalg.norm(a);b=b/np.linalg.norm(b);dot=np.dot(a,b)
 if dot<0:b=-b;dot=-dot
 if dot>.9995:result=(1-t)*a+t*b;return result/np.linalg.norm(result)
 angle=np.arccos(np.clip(dot,-1,1));return (np.sin((1-t)*angle)*a+np.sin(t*angle)*b)/np.sin(angle)
def interp(doc,bin,s,t,prop):
 times=array(doc,bin,s['input']).ravel();values=array(doc,bin,s['output']).reshape(len(times),-1)
 kind=s.get('interpolation','LINEAR')
 if kind=='CUBICSPLINE':raise ValueError('CUBICSPLINE requires independent Hermite evaluator, not present in this isolated comparison')
 if t<=times[0]:return values[0]
 if t>=times[-1]:return values[-1]
 i=np.searchsorted(times,t,side='right')-1;u=(t-times[i])/(times[i+1]-times[i])
 if kind=='STEP':return values[i]
 return slerp(values[i],values[i+1],u)if prop=='rotation'else (1-u)*values[i]+u*values[i+1]
def pose(doc,bin,clip,t):
 nodes=copy.deepcopy(doc['nodes'])
 for ch in clip['channels']:
  target=ch['target'];prop=target['path'];nodes[target['node']][prop]=interp(doc,bin,clip['samplers'][ch['sampler']],t,prop).tolist()
 parents={c:i for i,n in enumerate(nodes)for c in n.get('children',[])};world={}
 def evaluate(i):
  if i in world:return world[i]
  n=nodes[i]
  if 'matrix'in n:local=np.array(n['matrix']).reshape(4,4).T
  else:
   local=np.eye(4);local[:3,:3]=qmat(np.array(n.get('rotation',[0,0,0,1]),float))@np.diag(n.get('scale',[1,1,1]));local[:3,3]=n.get('translation',[0,0,0])
  world[i]=evaluate(parents[i])@local if i in parents else local
  return world[i]
 for i in range(len(nodes)):evaluate(i)
 return nodes,world
def vertices(doc,bin,nodes,world):
 result=[]
 for mi,mesh in enumerate(doc['meshes']):
  candidates=[(ni,n)for ni,n in enumerate(nodes)if n.get('mesh')==mi and 'skin'in n]
  if len(candidates)!=1:raise ValueError('One skinned instance required per raw mesh')
  ni,node=candidates[0];skin=doc['skins'][node['skin']]
  inv=array(doc,bin,skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1)
  matrices=np.array([world[j]for j in skin['joints']])@inv
  for pi,p in enumerate(mesh['primitives']):
   positions=array(doc,bin,p['attributes']['POSITION']);weights=node.get('weights',mesh.get('weights',[0]*len(p.get('targets',[]))))
   for wi,tar in enumerate(p.get('targets',[])):
    if 'POSITION'in tar:positions+=weights[wi]*array(doc,bin,tar['POSITION'])
   joints=array(doc,bin,p['attributes']['JOINTS_0']).astype(int);influence=array(doc,bin,p['attributes']['WEIGHTS_0'])
   hom=np.c_[positions,np.ones(len(positions))];answer=np.zeros((len(positions),3))
   for k in range(4):answer+=influence[:,k,None]*np.einsum('vab,vb->va',matrices[joints[:,k],:3,:],hom,optimize=False)
   result.append((mi,pi,answer))
 return result
manifest={'tolerance_m':.00002,'variants':[]}
for v in parent['variants']:
 doc,bin,sha=decode(v['glb']);refs=[]
 for clip in doc['animations']:
  if clip['name']not in v['clips']:continue
  times=sorted(set(float(t)for s in clip['samplers']for t in array(doc,bin,s['input']).ravel()))
  duration=times[-1];holdouts=[duration*f for f in [.137,.371,.613,.887]]
  for key,t in enumerate(times):
   expected=np.load(Path(v['expectedFolder'])/v['keyExpectedPattern'].replace('{clip}',clip['name']).replace('{key:03d}',f'{key:03d}'))
   for pnum,(mi,pi,_)in enumerate(vertices(doc,bin,*pose(doc,bin,clip,t))):
    name=f'{v["name"]}-{clip["name"]}-key{key:03d}-p{pnum}.f32';expected[f'p{pnum}'].astype('<f4').tofile(out/name)
    refs.append({'clip':clip['name'],'time':t,'mesh_index':mi,'primitive_index':pi,'path':'references/'+name,'format':'float32le','reference_origin':'parent independently authored pose + dense weight field'})
  for hi,t in enumerate(holdouts):
   for pnum,(mi,pi,p)in enumerate(vertices(doc,bin,*pose(doc,bin,clip,t))):
    name=f'{v["name"]}-{clip["name"]}-holdout{hi}-p{pnum}.f32';p.astype('<f4').tofile(out/name)
    refs.append({'clip':clip['name'],'time':t,'mesh_index':mi,'primitive_index':pi,'path':'references/'+name,'format':'float32le','reference_origin':'independent raw glTF linear TRS + SLERP + sparse morph + matrix LBS'})
 manifest['variants'].append({'id':v['name'],'path':v['glb'],'sha256_reference_source':sha,'clips':v['clips'],'expected':refs})
 print(v['name'],sha,len(refs),'reference primitive arrays',flush=True)
(ROOT/'comparison-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n')
