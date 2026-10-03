"""Read-only source/rest/coordinate/export contract for one future shell owner."""
from pathlib import Path
import sys,json,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
sys.dont_write_bytecode=True
R=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3');sys.path.insert(0,str(R/'scripts'));from glb import GLB
source=R/'deliverables/C19.glb';reference=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/garment-rebuild01/physical-v5-control157/rider.glb');g=GLB(source);ref=GLB(reference)
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def worlds(doc):
 parent={c:i for i,n in enumerate(doc['nodes']) for c in n.get('children',[])};cache={};local=[]
 for n in doc['nodes']:
  if 'matrix'in n:a=np.array(n['matrix']).reshape(4,4).T
  else:
   a=np.eye(4);a[:3,:3]=Rotation.from_quat(n.get('rotation',[0,0,0,1])).as_matrix()@np.diag(n.get('scale',[1,1,1]));a[:3,3]=n.get('translation',[0,0,0])
  local.append(a)
 def w(i):
  if i not in cache:cache[i]=w(parent[i])@local[i] if i in parent else local[i]
  return cache[i]
 return parent,local,[w(i) for i in range(len(doc['nodes']))]
parent,local,world=worlds(g.j);rp,rl,rw=worlds(ref.j);skin=g.j['skins'][0];rskin=ref.j['skins'][0];ib=g.array(skin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1);rib=ref.array(rskin['inverseBindMatrices']).reshape(-1,4,4).transpose(0,2,1);assert len(skin['joints'])==19
slots={n:i for i,n in enumerate(skin['joints'])};bones=[]
for slot,(node,rnode)in enumerate(zip(skin['joints'],rskin['joints'])):
 bones.append({'slot':slot,'sourceNode':node,'sourceName':g.j['nodes'][node].get('name'),'canonicalName':ref.j['nodes'][rnode].get('name'),'parentSlot':slots.get(parent.get(node)),'localMatrixRowMajor':local[node].tolist(),'worldMatrixRowMajor':world[node].tolist(),'inverseBindMatrixRowMajor':ib[slot].tolist(),'restCentreM':world[node][:3,3].tolist(),'referenceWorldMatrixMaximumError':float(abs(world[node]-rw[rnode]).max()),'referenceInverseBindMaximumError':float(abs(ib[slot]-rib[slot]).max())})
prims=[]
for mi,m in enumerate(g.j['meshes']):
 for pi,p in enumerate(m['primitives']):
  flat=len(prims);attrs={}
  for name,ai in p['attributes'].items():
   a=g.array(ai);ac=g.j['accessors'][ai];attrs[name]={'count':len(a),'componentType':ac['componentType'],'normalized':ac.get('normalized',False),'type':ac['type'],'decodedStoredArraySHA256':hashlib.sha256(a.tobytes()).hexdigest()}
  prims.append({'flatPrimitive':flat,'mesh':mi,'primitive':pi,'meshName':m.get('name'),'vertices':len(g.array(p['attributes']['POSITION'])),'triangles':len(g.array(p['indices']))//3,'protected170':flat in [1,3],'attributes':attrs,'material':p.get('material'),'morphTargetCount':len(p.get('targets',[])),'semanticCaution':'Primitive namespace alone is not a semantic garment mask; resolve component/source-face inventory before deletion.'})
report={'status':'READONLY PRECONSTRUCTION CONTRACT; construction ownership pending parent relay. No shell built here.','source':{'path':str(source),'SHA256':sha(source)},'mappedReference':{'path':str(reference),'SHA256':sha(reference)},'architecture':'Parent cf28df1f clean continuous hoodie torso/shoulder/proximal sleeve. Old tube/cap and source23 salvage retired; defective old topology reference only. Do not duplicate original shell edits.','coordinates':{'glTF':'X forward, Y height/up, Z lateral; source metre units','BlenderFromSourceRowMajor':[[1,0,0],[0,0,-1],[0,1,0]],'meaning':'Source(x,y,z) -> Blender(x,-z,y); proper rotation determinant+1','sceneTransforms':'Use exact node local/world transforms below. Historical declaredUniformScale1.015 is inert metadata; applied scale1.0.'},'bones':bones,'meshNodes':[{'node':i,'mesh':n['mesh'],'skin':n.get('skin'),'worldMatrixRowMajor':world[i].tolist()}for i,n in enumerate(g.j['nodes'])if'mesh'in n],'primitives':prims,'runtimeContract':{'orderedSlots':19,'conditionerFlag':'Owning container numeric rockhopRiderSkinConditioned:1; verified actual loader conditioning174 commit2d1d357e','axesFlag':'WORLD_ALIGNED_EXPLICIT_CHILD_DIRECTIONS','anatomy':'Exact170 adapter permits C19 rest/hierarchy/inversebind only. Changed joints or namespaces require explicit reviewed adapter, not silent relabeling. Ordinary constructor still needs anatomy/contact control.','influences':'Stock Three shader four per vertex. Require actual-positive count<=4 and no lost mass; no implicit JOINTS_1, truncation, or DQ.','materialAdapter':'Any nonlinear postbone deformation requires explicit runtime P+N driver and parity/performance proof; cannot be encoded by stock-four GLB alone.','sewing':'One physical cloth identity across seam/UV aliases; exact P and matched W on shared groups. Preserve intended hard N differences; keep shader flags. New shell joins are rebuilt actual sewn edges, not overlapping donor sheets.','protected':'Head and glove all attrs/morphs/indices/PBR/image semantics protected under170; preserve liked identity. Hood/cuffs need explicit component masks and viable matched rebuilt joins; old shoulder boundaries retired.'},'authoritativeControls':{'path':str(R/'hoodie-repair03/inputs/source34-authoritative168-matrices.npz'),'SHA256':sha(R/'hoodie-repair03/inputs/source34-authoritative168-matrices.npz'),'frames':480,'meaning':'Matrices D already contain prefix, boneworld, inversebind and bind. Do not multiply prefix twice. Different bone bases compare endpoint/world displacement rather than copied local quaternions.'},'nextGate':'One owner neutral manifold/winding/intentional openings/literal triangles + inspected front/side/back continuous gray/PBR turntable. Only selected shell gets bind and bounded sit/overhead transition, then continuous holdouts and parent5404fixture/contact/Garage. No failed tube/embedding broad renders.'}
out=Path('deliverables/Continuous-shell-source-coordinate-bone-contract.json');out.write_text(json.dumps(report,indent=2)+'\n');print('Exact19 rig/coordinate/attribute source contract frozen',sha(out))
