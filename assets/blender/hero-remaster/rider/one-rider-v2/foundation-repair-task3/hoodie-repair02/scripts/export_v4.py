from base import *
import hashlib
b=np.load(OUT/'v4-bind.npz');g=GLB(ROOT/'deliverables/C19.glb');prs=[p for m in g.j['meshes']for p in m['primitives']]
def add(a,typ,comp=5126):
 a=np.ascontiguousarray(a,dtype={5126:'<f4',5125:'<u4',5123:'<u2'}[comp]);g.bin.extend(b'\0'*((-len(g.bin))%4));vi=len(g.j['bufferViews']);g.j['bufferViews'].append({'buffer':0,'byteOffset':len(g.bin),'byteLength':a.nbytes});g.bin.extend(a.tobytes());ai=len(g.j['accessors']);ac={'bufferView':vi,'componentType':comp,'count':len(a),'type':typ}
 if comp==5126:ac.update(min=np.min(a,axis=0).reshape(-1).tolist(),max=np.max(a,axis=0).reshape(-1).tolist())
 g.j['accessors'].append(ac);return ai
for i,p in enumerate(prs):
 ps=b[f'p{i}'];ws=b[f'W{i}'];tr=b[f'tr{i}']
 if i in [0,2]:p['attributes']['POSITION']=add(ps,'VEC3');p['attributes']['NORMAL']=add(normals(ps,tr),'VEC3');p['indices']=add(tr.reshape(-1,1),'SCALAR',5125)
 ix=np.argsort(ws,axis=1)[:,-4:][:,::-1];w=np.take_along_axis(ws,ix,axis=1);w/=w.sum(1)[:,None];p['attributes']['JOINTS_0']=add(ix,'VEC4',5123);p['attributes']['WEIGHTS_0']=add(w,'VEC4')
ids=g.j['skins'][0]['joints'];parents={c:i for i,n in enumerate(g.j['nodes'])for c in n.get('children',[])};rest=np.repeat(np.eye(4)[None],N,axis=0);rest[:,:3,3]=P
Ds=[np.load(OUT/'poses'/f'v4-movie-candidate-{k:03d}.npz')['matrices']for k in range(49)];world=np.array(Ds)@rest;ti=add(np.linspace(0,2,49)[:,None],'SCALAR');clip={'name':'foundation_stand_to_sit','samplers':[],'channels':[]}
def channel(node,path,a,typ):
 clip['samplers'].append({'input':ti,'output':add(a,typ),'interpolation':'LINEAR'});clip['channels'].append({'sampler':len(clip['samplers'])-1,'target':{'node':node,'path':path}})
for j,node in enumerate(ids):
 par=parents.get(node);local=world[:,j]if par not in ids else np.linalg.inv(world[:,ids.index(par)])@world[:,j];q=R.from_matrix(local[:,:3,:3]).as_quat()
 for k in range(1,len(q)):
  if np.dot(q[k-1],q[k])<0:q[k]*=-1
 channel(node,'translation',local[:,:3,3],'VEC3');channel(node,'rotation',q,'VEC4');channel(node,'scale',np.ones((49,3)),'VEC3')
for node in [2]:
 channel(node,'translation',np.zeros((49,3)),'VEC3');channel(node,'rotation',np.tile([0,0,0,1],(49,1)),'VEC4');channel(node,'scale',np.ones((49,3)),'VEC3')
channel(0,'weights',np.ones((98,1)),'SCALAR')
g.j['animations'].append(clip)
extra=g.j['asset'].setdefault('extras',{});extra['hoodieFoundationExperiment']={'controlSHA256':hashlib.sha256(G.raw).hexdigest(),'variant':'v4','joints':19,'retopology':'23 UV-safe local diagonal flips','chestMaxCorrectionM':.03,'sameUVAndTextureBytes':True,'headAndHandPositionsExact':True,'weights':'bounded soft-anchor strain-aware LS; 500 iterations','runtime':'ordinary glTF LBS and original hand morphs','correctives':False,'productionApproved':False,'scope':'Partial foundation repair; raised arms, hips and seat support not accepted'}
# Inform isolated adapters that the seam-consistent baked field must not be reconditioned.
extra['hoodieFoundationExperiment']['weightsAlreadyConditioned']=True
for m in g.j['meshes']:m.setdefault('extras',{})['skipRuntimeWeightConditioning']=True
g.j['buffers'][0]['byteLength']=len(g.bin);out=OUT/'deliverables/rider-foundation-v4.glb';g.write(out);(OUT/'deliverables/rider-foundation-v4.sha256').write_text(hashlib.sha256(out.read_bytes()).hexdigest()+'  '+out.name+'\n');print(out)
