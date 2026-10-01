"""JSON-only explicit contact/name adapter for preserved freshC19, no new skin/shape."""
from pathlib import Path
import json,struct,hashlib
import numpy as np
from scipy.spatial.transform import Rotation
SOURCE=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb')
OLD=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind11/guarded-correction01/rider.glb')
RUN=OLD.parent.parent.parent/'body-bind34';OUT=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind34');RUN.mkdir(exist_ok=True);OUT.mkdir(exist_ok=True)
sha=lambda b:hashlib.sha256(b).hexdigest()
def glb(path):
 raw=path.read_bytes();n=struct.unpack_from('<I',raw,12)[0];return raw,json.loads(raw[20:20+n]),raw[28+n:]
r,j,b=glb(SOURCE);o,k,ob=glb(OLD)
assert sha(r)=='186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e' and sha(o)=='b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754'
original=json.loads(json.dumps(j));assert len(j['skins'])==1 and len(j['skins'][0]['joints'])==19
canonical=['pelvis','spine','chest','neck','head','shoulder.L','upperArm.L','forearm.L','hand.L','shoulder.R','upperArm.R','forearm.R','hand.R','thigh.L','shin.L','foot.L','thigh.R','shin.R','foot.R']
assert [j['nodes'][n]['name'] for n in j['skins'][0]['joints']]==['fresh.'+n for n in canonical]
def worlds(doc):
 parents={c:i for i,n in enumerate(doc['nodes']) for c in n.get('children',[])};cache={}
 def world(i):
  if i in cache:return cache[i]
  n=doc['nodes'][i]
  if 'matrix' in n:m=np.array(n['matrix']).reshape(4,4).T
  else:
   m=np.eye(4);m[:3,:3]=Rotation.from_quat(n.get('rotation',[0,0,0,1])).as_matrix()@np.diag(n.get('scale',[1,1,1]));m[:3,3]=n.get('translation',[0,0,0])
  cache[i]=world(parents[i])@m if i in parents else m;return cache[i]
 return [world(i) for i in range(len(doc['nodes']))]
ow=worlds(k);nw=worlds(j);oldnodes={n.get('name'):i for i,n in enumerate(k['nodes'])};newnodes={name:n for name,n in zip(canonical,j['skins'][0]['joints'])}
def rotation(m):
 u,s,v=np.linalg.svd(m[:3,:3]);q=u@v;assert np.linalg.det(q)>0;return Rotation.from_matrix(q)
metadata=next(json.loads(n['extras']['rockhopRiderContactAdapter']) for n in k['nodes'] if 'rockhopRiderContactAdapter' in n.get('extras',{}))
newmetadata=json.loads(json.dumps(metadata));mapping=[];sockets=[]
for name,i in newnodes.items():
 j['nodes'][i]['name']=name;mapping.append({'sourceName':'fresh.'+name,'targetContractName':name,'node':i})
for side in ['L','R']:
 oldhand=oldnodes['hand.'+side];newhand=newnodes['hand.'+side]
 oldrest=rotation(ow[oldhand]);newrest=rotation(nw[newhand])
 deformation=Rotation.from_quat(metadata['hands'][side]['targetWorldQuaternion'])*oldrest.inv()
 newmetadata['hands'][side]['targetWorldQuaternion']=(deformation*newrest).as_quat().tolist()
 for socket,parent in [('gripSocket.','hand.'),('soleSocket.','foot.')]:
  name=socket+side;assert name in oldnodes and not any(n.get('name')==name for n in j['nodes'])
  targetWorld=ow[oldnodes[name]];p=newnodes[parent+side];local=np.linalg.inv(nw[p])@targetWorld
  ni=len(j['nodes']);j['nodes'].append({'name':name,'matrix':local.T.reshape(-1).tolist()});j['nodes'][p].setdefault('children',[]).append(ni)
  error=float(np.max(abs(nw[p]@local-targetWorld)));assert error<1e-12
  sockets.append({'socket':name,'newParent':parent+side,'node':ni,'sourceRestWorldMatrix':targetWorld.T.reshape(-1).tolist(),'reconstructedRestMatrixMaxError':error})
rigNode=next(i for i,n in enumerate(j['nodes']) if n.get('extras',{}).get('freshRigComparison'))
j['nodes'][rigNode].setdefault('extras',{}).update({'rockhopRiderSkinConditioned':1,'rockhopRiderContactAdapter':json.dumps(newmetadata,separators=(',',':')),'rockhopFreshC19RestAxes':'WORLD_ALIGNED_EXPLICIT_CHILD_DIRECTIONS','privateFreshC19AdapterUnaccepted':True})
# World-alignedC19local+Y is NOT the anatomical child direction for limbs.
child={'pelvis':'spine','spine':'chest','chest':'neck','neck':'head'}
for side in ['L','R']:
 child.update({'shoulder.'+side:'upperArm.'+side,'upperArm.'+side:'forearm.'+side,'forearm.'+side:'hand.'+side,'thigh.'+side:'shin.'+side,'shin.'+side:'foot.'+side})
axes=[]
for name,end in child.items():
 a=nw[newnodes[name]][:3,3];v=nw[newnodes[end]][:3,3]-a;v/=np.linalg.norm(v)
 conventional=rotation(nw[newnodes[name]]).apply([0,1,0]);angle=float(np.degrees(np.arccos(np.clip(v@conventional,-1,1))))
 axes.append({'bone':name,'child':end,'anatomicalWorldDirection':v.tolist(),'conventionalLocalYWorldDirection':conventional.tolist(),'angleDifferenceDegrees':angle})
assert max(x['angleDifferenceDegrees'] for x in axes)>150
assert j['meshes']==original['meshes'] and j['skins']==original['skins'] and j.get('animations')==original.get('animations')
for key in ['accessors','bufferViews','buffers','materials','images','textures','samplers']:assert j.get(key)==original.get(key)
encoded=json.dumps(j,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
result=struct.pack('<III',0x46546c67,2,28+len(encoded)+len(b))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(b),0x004e4942)+b
path=RUN/'rider.glb'
if path.exists():assert path.read_bytes()==result
else:path.write_bytes(result)
assert SOURCE.read_bytes()==r and OLD.read_bytes()==o
report={'status':'Unaccepted JSON-only explicit freshC19name/contact mapping; runtime anatomical-axis adapter REQUIRED','source':str(SOURCE),'sourceSHA256':sha(r),'candidate':str(path),'candidateSHA256':sha(result),'candidateBytes':len(result),'sourceC19AllBINBytesExact':True,'sourceC19GeometryUVNormalsWeightsRigInverseBindsMaterialsImagesMorphsAnimationsExact':True,'names':mapping,'sockets':sockets,'handMapping':'newTargetQ = oldDesiredDeformation * freshRestQ, oldDesiredDeformation = oldTargetQ * inverse(oldRestQ). Original contact surface rest position/orientation retained under fresh parent.','newContactMetadata':newmetadata,'restAxes':axes,'requiredDriverChange':'FreshC19uses world-aligned bone coordinate bases. The existing d0=local+Y transformed by q0 assumption is invalid for fresh limbs (about180degrees). Use explicit child anatomical rest vectors, preserving q0 and fresh binds. No copying local animated rotations between rigs.','conditioning':'Explicitly baked freshskin bypass remains required after canonical name mapping; do not run legacy conditionSleeveSkin on renamedfreshgeometry.','limits':['No GPU or moving gameplay/bench/Garage evidence yet.','Sockets match rest frames, not proof skinned fingertip/sole pads maintain contact in motion.','C19authored clips are diagnostic, not game sit_cruise/idle/additive contract; Garage blending remains open.','No production or face/fullbody quality pass; historical source files untouched.']}
(OUT/'mapping-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'candidateSHA256':sha(result),'candidateBytes':len(result),'axes':axes},indent=2))
