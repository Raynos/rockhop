from pathlib import Path
import sys,json,hashlib
import numpy as np
from PIL import Image
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');Q=ROOT/'hoodie-repair02/qa-lane';OUT=Q/'screenshot01';sys.path.insert(0,str(ROOT/'hoodie-repair02/scripts'));import base
from glb import GLB
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01/physical-v5-control157/candidate-cpu');j=json.loads((B/'pose-manifest.json').read_text());r=next(r for r in j['rows']if r['i']==304);g=GLB(j['source']);assert hashlib.sha256(g.raw).hexdigest()==j['sourceSHA256'];pr=[p for m in g.j['meshes']for p in m['primitives']];P=[g.array(p['attributes']['POSITION']).astype(float)for p in pr];W=[];receipts=[]
for p in pr:
 ix=g.array(p['attributes']['JOINTS_0']);sw=g.array(p['attributes']['WEIGHTS_0']);w=np.zeros((len(ix),19));np.add.at(w,(np.arange(len(ix))[:,None],ix.astype(int)),sw);W.append(w)
rawW=[w.copy()for w in W];data={f'tr{i}':g.array(p['indices']).astype(int).reshape(-1,3)for i,p in enumerate(pr)};rows=[]
def read(rc,k):
 f=B/rc['file'];assert hashlib.sha256(f.read_bytes()).hexdigest()==rc['sha256'];receipts.append({'key':k,'path':str(f),'sha256':rc['sha256']});return np.fromfile(f,dtype='<f8')
for mi,pi in [(0,0),(1,2)]:
 ix=read(j['primitives'][mi]['attributes']['skinIndex'],f'J{pi}').reshape(-1,4).astype(int);sw=read(j['primitives'][mi]['attributes']['skinWeight'],f'weights{pi}').reshape(-1,4);w=np.zeros_like(W[pi]);np.add.at(w,(np.arange(len(ix))[:,None],ix),sw);W[pi]=w
 data[f'actual_positions{pi}']=read(r['dump'][mi]['positions'],f'p{pi}').reshape(-1,3);data[f'actual_normals{pi}']=read(r['dump'][mi]['gpuRuleSkinnedNormals'],f'n{pi}').reshape(-1,3);D=read(r['dump'][mi]['jointTransforms'],f'D{pi}').reshape(-1,4,4).transpose(0,2,1)
 diff=W[pi]-rawW[pi];rows.append({'primitive':pi,'runtime_raw_weight_max_difference':float(abs(diff).max()),'changed_vertices_above_1e_7':int(np.any(abs(diff)>1e-7,axis=1).sum())})
assert np.array_equal(D,np.load(OUT/'body34-reference-sample304.npz')['joint_transforms0']);assert np.array_equal(g.array(g.j['skins'][0]['inverseBindMatrices']),base.G.array(base.G.j['skins'][0]['inverseBindMatrices']))
CLOSE=[p.copy()for p in P];oldG=base.G;base.G=g
for i,p in enumerate(pr):
 assert len(p.get('targets',[]))<=2
 for t in p.get('targets',[]):CLOSE[i]+=base.source_morph(i,t['POSITION'])
base.G=oldG
posed=base.deform(CLOSE,W,D,closed=False)
for i in [0,2]:rows[[0,2].index(i)]['dense_reconstruction_max_error_m']=float(np.linalg.norm(posed[i]-data[f'actual_positions{i}'],axis=1).max());posed[i]=data[f'actual_positions{i}'].copy()
np.savez_compressed(OUT/'physical-v5-actual-sample304.npz',**data,**{f'p{i}':p for i,p in enumerate(posed)},**{f'W{i}':w for i,w in enumerate(W)},matrices=D)
np.savez(Q/'physicalv5-bind.npz',**{f'p{i}':p for i,p in enumerate(P)})
imagepath=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01/physical-v5-control157/played/original/side/textured/0304.png');userpath=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/screenshot-defects01/user-defects.jpeg');u=np.array(Image.open(userpath).convert('RGB')).astype(float);a=np.array(Image.open(imagepath).convert('RGB')).astype(float);diff=u-a
meta={'status':'SCREENSHOT SOURCE IDENTIFIED: physical-v5-control157 side original sample304','source':j['source'],'source_sha256':j['sourceSHA256'],'image':str(imagepath),'image_sha256':hashlib.sha256(imagepath.read_bytes()).hexdigest(),'user_image_sha256':hashlib.sha256(userpath.read_bytes()).hexdigest(),'full_1280x720_rgb_mse':float(np.mean(diff**2)),'mean_absolute_channel_difference':float(abs(diff).mean()),'rms':float(np.sqrt(np.mean(diff**2))),'same_runtime_D_as_body34':True,'same_inverse_bind_as_C19':True,'weight_audit':rows,'raw_receipts':receipts,'materials':[{'name':m.get('name'),'doubleSided':m.get('doubleSided',False),'alphaMode':m.get('alphaMode','OPAQUE')}for m in g.j['materials']],'camera_ref':str(OUT/'body34-reference-literal-diagnostic.json'),'limits':['JPEG compression residual precludes byte-exact image claim; visual holes and strong unique pixelmatch identify this recordedframe.','Actual measured garment positions/normals0/2 exact; protected otherprimitives reconstructed with rawsourceweights+closedoriginalmorphs and sameD.','Exact topology from identified candidate, not assumed V7 triangles.']};(OUT/'physical-v5-source-identification.json').write_text(json.dumps(meta,indent=2));(Q/'physical-v5-manifest.json').write_text(json.dumps({'topology_path':str(OUT/'physical-v5-actual-sample304.npz'),'rows':[{'variant':'physicalv5','probe':'actual-identified-screenshot-source-sample304','fraction':1,'path':str(OUT/'physical-v5-actual-sample304.npz')}]},indent=2));print({k:v for k,v in meta.items()if k in ['status','source_sha256','full_1280x720_rgb_mse','mean_absolute_channel_difference','same_runtime_D_as_body34','weight_audit']})
