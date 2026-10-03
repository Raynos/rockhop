"""Exact neutral/deformed surface snapshot for CPU visual inspection.
This GLB deliberately has no skin/morph/animation contract. DenseNPZ remains
canonical; no five-influence field is silently truncated to stock skinning.
"""
from pathlib import Path
import numpy as np,sys,json,hashlib
sys.dont_write_bytecode=True
R=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');sys.path.insert(0,str(R/'scripts'));from glb import GLB
source=Path(sys.argv[1]);output=Path(sys.argv[2]);state=sys.argv[3];assert state in ['rest','304'];z=np.load(source);g=GLB(R/'deliverables/C19.glb');prims=[p for m in g.j['meshes']for p in m['primitives']];controls=np.load(R/'hoodie-repair03/inputs/source34-authoritative168-matrices.npz');D=np.repeat(np.eye(4)[None],19,axis=0)if state=='rest'else controls['D'][304];posed=[];normals=[]
for i in range(5):
 posed.append(np.einsum('vj,jab,vb->va',z[f'W{i}'],D[:,:3,:],np.c_[z[f'p{i}'],np.ones(len(z[f'p{i}']))],optimize=False));n=np.einsum('vj,jab,vb->va',z[f'W{i}'],D[:,:3,:3],z[f'n{i}'],optimize=False);n/=np.maximum(np.linalg.norm(n,axis=1,keepdims=True),1e-20);normals.append(n)
if state=='rest':
 # Neutral snapshots preserve literal standing attributes, including harmless
 # authored float32 weight/normal roundoff; skinning is irrelevant to rest.
 posed=[z[f'p{i}'].copy()for i in range(5)];normals=[z[f'n{i}'].copy()for i in range(5)]
if state=='304':posed[1]=np.load(R/'hoodie-repair03/poses/game304-v7-plain.npz')['p1']
# Optional explicit material-driver output; never reinterpret it as skinning.
# The driver caller must supply all five positions and normals in this space.
explicitPose=Path(sys.argv[4])if len(sys.argv)>4 else None
if explicitPose is not None:
 direct=np.load(explicitPose)
 for i in range(5):
  assert direct[f'p{i}'].shape==posed[i].shape
  assert direct[f'n{i}'].shape==normals[i].shape
  assert np.isfinite(direct[f'p{i}']).all()and np.isfinite(direct[f'n{i}']).all()
 posed=[direct[f'p{i}'].copy()for i in range(5)];normals=[direct[f'n{i}'].copy()for i in range(5)]
DT={5126:'<f4',5125:'<u4',5123:'<u2',5121:'u1'}
def add(a,typ,component=5126,normalized=None):
 a=np.ascontiguousarray(a,dtype=DT[component]);g.bin.extend(b'\0'*(-len(g.bin)%4));bv=len(g.j['bufferViews']);g.j['bufferViews'].append({'buffer':0,'byteOffset':len(g.bin),'byteLength':a.nbytes});g.bin.extend(a.tobytes());ac={'bufferView':bv,'componentType':component,'count':len(a),'type':typ}
 if normalized is not None:ac['normalized']=normalized
 if component==5126:ac.update(min=a.min(0).tolist(),max=a.max(0).tolist())
 ai=len(g.j['accessors']);g.j['accessors'].append(ac);return ai
for i,p in enumerate(prims):
 attrs={};parents=z.get(f'sourceVertexParents{i}');bary=z.get(f'sourceVertexBarycentric{i}');old=z[f'oldVertex{i}'];valid=old>=0
 for name,ai in p['attributes'].items():
  if name.startswith('JOINTS')or name.startswith('WEIGHTS'):continue
  ac=g.j['accessors'][ai];a=g.array(ai);v=np.zeros((len(old),a.shape[1]),a.dtype);v[valid]=a[old[valid]]
  if name.startswith('COLOR'):
   v[~valid]=np.median(a,axis=0)
   if parents is not None:
    ids=np.flatnonzero((parents[:,0]>=0)&(parents[:,1]>=0));v[ids]=np.rint((a[parents[ids]]*bary[ids,:,None]).sum(1)).astype(a.dtype)
  if name=='POSITION':v=posed[i]
  elif name=='NORMAL':v=normals[i]
  elif name=='TEXCOORD_0':v=z[f'uv{i}']
  attrs[name]=add(v,ac['type'],ac['componentType'],ac.get('normalized'))
 p['attributes']=attrs;p['indices']=add(z[f'tr{i}'].reshape(-1,1),'SCALAR',5125);p.pop('targets',None)
for m in g.j['meshes']:m.pop('weights',None);m.get('extras',{}).pop('targetNames',None)
g.j['nodes']=[{'name':'Exact dense CPU surface snapshot '+state,'mesh':i,'extras':{'unacceptedDiagnostic':True,'canonicalDenseNPZSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'noSkinContract':True}}for i in range(len(g.j['meshes']))];g.j['scenes']=[{'nodes':list(range(len(g.j['nodes'])))}];g.j['scene']=0;g.j.pop('skins',None);g.j.pop('animations',None);output.parent.mkdir(parents=True,exist_ok=True);g.j['buffers'][0]['byteLength']=len(g.bin);g.write(output)
output.with_suffix('.json').write_text(json.dumps({'status':'Exact unskinned CPU snapshot; visual diagnostic only','sourceNPZ':str(source),'candidateSHA256':hashlib.sha256(source.read_bytes()).hexdigest(),'snapshotSHA256':hashlib.sha256(output.read_bytes()).hexdigest(),'state':state,'maxDenseInfluences':max(int((z[f'W{i}']>1e-8).sum(1).max())for i in range(5)),'allDenseInfluencesApplied':explicitPose is None,'explicitMaterialPose':None if explicitPose is None else{'path':str(explicitPose),'sha256':hashlib.sha256(explicitPose.read_bytes()).hexdigest()},'originalImagesAndNormalizedColorFlagsPreserved':True,'normals':'Normalized weighted rest normals, declared; new rows authored welded normal from candidate.'if explicitPose is None else'Explicit supplied material-driver normals; see pose provenance.','limits':'No runtime skin/morph/driver acceptance. No top4 truncation. Recorded hands held to original closed control.'},indent=2)+'\n');print(output)
