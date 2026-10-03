from base import *
import hashlib
G5=GLB(OUT/'deliverables/rider-foundation-v5.glb');g=G5;prs=[p for m in g.j['meshes']for p in m['primitives']];b=np.load(OUT/'v5-bind.npz');pos=[b[f'p{i}']for i in range(5)];ww=[b[f'W{i}']for i in range(5)];tri=[b[f'tr{i}']for i in range(5)]
def add(a,typ,comp=5126):
 a=np.ascontiguousarray(a,dtype={5126:'<f4',5125:'<u4'}[comp]);g.bin.extend(b'\0'*((-len(g.bin))%4));vi=len(g.j['bufferViews']);g.j['bufferViews'].append({'buffer':0,'byteOffset':len(g.bin),'byteLength':a.nbytes});g.bin.extend(a.tobytes());ai=len(g.j['accessors']);ac={'bufferView':vi,'componentType':comp,'count':len(a),'type':typ}
 if typ=='SCALAR'and comp==5126:ac.update(min=[float(a.min())],max=[float(a.max())])
 g.j['accessors'].append(ac);return ai

def sparse(a):
 a=np.asarray(a,dtype='<f4');ix=np.flatnonzero(np.any(abs(a)>1e-9,axis=1)).astype('<u4');ac={'componentType':5126,'count':len(a),'type':'VEC3'}
 if len(ix):
  vs=[]
  for v in [ix,a[ix]]:
   g.bin.extend(b'\0'*((-len(g.bin))%4));vs.append(len(g.j['bufferViews']));g.j['bufferViews'].append({'buffer':0,'byteOffset':len(g.bin),'byteLength':v.nbytes});g.bin.extend(v.tobytes())
  ac['sparse']={'count':len(ix),'indices':{'bufferView':vs[0],'componentType':5125},'values':{'bufferView':vs[1]}}
 ai=len(g.j['accessors']);g.j['accessors'].append(ac);return ai

def accessor(ai):
 ac=g.j['accessors'][ai];a=g.array(ai).astype(float)if'bufferView'in ac else np.zeros((ac['count'],3))
 if'sparse'in ac:
  s=ac['sparse'];bv=g.j['bufferViews'][s['indices']['bufferView']];ix=np.frombuffer(g.bin,dtype={5125:'<u4',5123:'<u2',5121:'u1'}[s['indices']['componentType']],count=s['count'],offset=bv.get('byteOffset',0)+s['indices'].get('byteOffset',0));bv=g.j['bufferViews'][s['values']['bufferView']];a[ix]=np.frombuffer(g.bin,dtype='<f4',count=s['count']*3,offset=bv.get('byteOffset',0)+s['values'].get('byteOffset',0)).reshape(-1,3)
 return a
base_norm=[accessor(p['attributes']['NORMAL'])for p in prs];closed_norm=[n.copy()for n in base_norm]
for i,p in enumerate(prs):
 for ta in p.get('targets',[]):
  if'NORMAL'in ta:closed_norm[i]+=accessor(ta['NORMAL'])
maxcond=0;worlds=[]
for k in range(49):
 data=np.load(OUT/'poses'/f'v6-movie-candidate-{k:03d}.npz');D=data['matrices'];worlds.append(D)
 skin=deform(pos,ww,D,True)
 for pi in range(3):
  L=np.einsum('vj,jab->vab',ww[pi],D[:,:3,:3]);t=np.einsum('vj,ja->va',ww[pi],D[:,:3,3]);maxcond=max(maxcond,float(np.linalg.cond(L).max()));desired=data[f'p{pi}'];inv=np.linalg.solve(L,(desired-t)[...,None])[...,0];delta=inv-pos[pi]-MORPH[pi];n=closed_norm[pi].copy();changed=np.linalg.norm(desired-skin[pi],axis=1)>1e-9
  if changed.any():
   a=normals(skin[pi],tri[pi]);q=normals(desired,tri[pi]);axis=np.cross(a,q);cos=np.einsum('ij,ij->i',a,q);current=np.einsum('vij,vj->vi',L,n);rot=current+np.cross(axis,current)+np.cross(axis,np.cross(axis,current))/np.maximum(1+cos[:,None],1e-8);nn=np.linalg.solve(L,rot[...,None])[...,0];n[changed]=nn[changed]
  prs[pi]['targets'].append({'POSITION':sparse(delta),'NORMAL':sparse(n-closed_norm[pi])})
weights=[0]*51;g.j['meshes'][0]['weights']=weights;g.j['meshes'][0]['extras']['targetNames']=['gripOriginalL','gripOriginalR']+[f'hoodieCompression_{k:03d}'for k in range(49)]
ids=g.j['skins'][0]['joints'];parents={c:i for i,n in enumerate(g.j['nodes'])for c in n.get('children',[])};rest=np.repeat(np.eye(4)[None],N,axis=0);rest[:,:3,3]=P;worlds=np.array(worlds)@rest
clip={'name':'hoodie_compression_stand_to_sit','samplers':[],'channels':[]};ti=add(np.linspace(0,2,49)[:,None],'SCALAR')
def channel(node,path,a,typ):
 clip['samplers'].append({'input':ti,'output':add(a,typ),'interpolation':'LINEAR'});clip['channels'].append({'sampler':len(clip['samplers'])-1,'target':{'node':node,'path':path}})
for j,node in enumerate(ids):
 par=parents.get(node);local=worlds[:,j]if par not in ids else np.linalg.inv(worlds[:,ids.index(par)])@worlds[:,j];q=R.from_matrix(local[:,:3,:3]).as_quat()
 for k in range(1,len(q)):
  if np.dot(q[k-1],q[k])<0:q[k]*=-1
 channel(node,'translation',local[:,:3,3],'VEC3');channel(node,'rotation',q,'VEC4');channel(node,'scale',np.ones((49,3)),'VEC3')
for path,a,typ in [('translation',np.zeros((49,3)),'VEC3'),('rotation',np.tile([0,0,0,1],(49,1)),'VEC4'),('scale',np.ones((49,3)),'VEC3')]:channel(2,path,a,typ)
channel(0,'weights',np.c_[np.ones((49,2)),np.eye(49)].reshape(-1,1),'SCALAR')
restore=next(a for a in g.j['animations']if a['name']=='bind_restore');restore['channels']=[c for c in restore['channels']if c['target']['path']!='weights'];restore['samplers'].append({'input':add(np.array([0,2])[:,None],'SCALAR'),'output':add(np.zeros((102,1)),'SCALAR'),'interpolation':'LINEAR'});restore['channels'].append({'sampler':len(restore['samplers'])-1,'target':{'node':0,'path':'weights'}})
g.j['animations']=[clip,restore];g.j['asset']['extras']['hoodieCompressionExperiment']={'controlSHA256':hashlib.sha256(G.raw).hexdigest(),'foundationSHA256':hashlib.sha256((OUT/'deliverables/rider-foundation-v5.glb').read_bytes()).hexdigest(),'targets':49,'maximumActiveTargets':4,'originalGripTargets':2,'maxBlendCondition':maxcond,'offlineMethod':'bounded differential cage then literal local triangle separating corrective','neckHeadFraction':.2,'runtime':'standard morph-before-LBS; testedclip only; no arbitrary pose or physics certificate','productionApproved':False,'support':'unchanged; unresolved hipcrossings and saddlehover'};g.j['buffers'][0]['byteLength']=len(g.bin);out=OUT/'deliverables/rider-compression-v6.glb';g.write(out);(OUT/'v6-export.json').write_text(json.dumps({'sha256':hashlib.sha256(out.read_bytes()).hexdigest(),'bytes':out.stat().st_size,'maxBlendCondition':maxcond,'clips':[a['name']for a in g.j['animations']]},indent=2));print(out)
