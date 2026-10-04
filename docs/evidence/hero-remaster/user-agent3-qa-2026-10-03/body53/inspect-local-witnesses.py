"""Inspect strict witnesses from selected existing samples, never pose a scene."""
import ast,collections,gzip,hashlib,json
from pathlib import Path
import numpy as np
from mathutils import Vector
from mathutils.bvhtree import BVHTree
root=Path.cwd();out=Path(__file__).resolve().parent;n=np.load(out.parent/'body52/native-fields.npz');e=np.load(out.parent/'body52/export-fields.npz');assessment=json.loads((out/'assessment.json').read_text());recipe=out/'assess-existing-streams.py';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(recipe)==assessment['recipeSHA256']
# Reuse only these frozen pure CPU methods; never execute its stream loops.
module=ast.parse(recipe.read_text());selected=ast.Module(body=[x for x in module.body if isinstance(x,ast.FunctionDef) and x.name in ['sat','crossing','detect']],type_ignores=[]);exec(compile(selected,str(recipe),'exec'))
tri=n['canonicalFourTriangles'];names=n['boneNames'].tolist();norm=lambda s:s.replace('.','').replace('_','');order=[list(map(norm,names)).index(norm(s)) for s in e['jointNames']];C=np.array([[1,0,0,0],[0,0,1,0],[0,-1,0,0],[0,0,0,1.]])
rest=(np.column_stack([n['canonicalFourXYZ'],np.ones(13380)])@(C@n['canonicalFourWorld']).T)[:,:3];H=np.ptp(rest[:,1]);jworld=np.einsum('ab,jbc->jac',C@n['rigWorld'],n['rigRest']);rois={k:np.linalg.norm(rest-jworld[names.index(j),:3,3],axis=1)<H*.08 for k,j in [('shoulder.L','upperArm.L'),('shoulder.R','upperArm.R'),('hip.L','thigh.L'),('hip.R','thigh.R')]};dom=np.argmax(n['canonicalFourWeights'],axis=1)
old=root/'docs/evidence/hero-remaster/anatomical-foundation-2026-10-03/user-agent1/diagnostic02';four=np.memmap(old/'body-native-four.f64',mode='r',dtype='<f8',shape=(529,13380,3));driver=json.loads((old/'driver.json').read_text())
with gzip.open(out.parent/'garment47/first.weights.ndjson.gz','rt') as f:actual=[json.loads(line) for line in f]
def actualpos(tick):
 K=np.array(actual[tick-1]['matrices']).reshape(51,4,4).transpose(0,2,1);p=np.column_stack([rest,np.ones(len(rest))]);w=n['canonicalFourWeights'][:,order];w/=w.sum(1)[:,None];return np.einsum('vj,jab,vb->va',w,K,p,optimize=True)[:,:3]
def excursion(a,b):
 best=0.
 for x,y in [(a,b),(b,a)]:
  u=y[1]-y[0];v=y[2]-y[0];normal=np.cross(u,v);normal/=np.linalg.norm(normal);uu=np.dot(u,u);vv=np.dot(v,v);uv=np.dot(u,v);det=uu*vv-uv*uv
  for i in range(3):
   p=x[i];q=x[(i+1)%3];d0=np.dot(p-y[0],normal);d1=np.dot(q-y[0],normal)
   if d0*d1>=0 or min(abs(d0),abs(d1))<=2e-6:continue
   hit=p+(d0/(d0-d1))*(q-p)-y[0];beta=(vv*np.dot(hit,u)-uv*np.dot(hit,v))/det;gamma=(uu*np.dot(hit,v)-uv*np.dot(hit,u))/det
   if beta>1e-6 and gamma>1e-6 and beta+gamma<1-1e-6:best=max(best,min(abs(d0),abs(d1)))
 return float(best)
results=[]
for domain in ['syntheticFour','actual47Four']:
 rows=[x for x in assessment['records'] if x['domain']==domain]
 for region,mask in rois.items():
  row=max(rows,key=lambda x:x['regionStrictPairs'][region]);frame=row['frame'];pos=four[frame] if domain=='syntheticFour' else actualpos(frame);pairs,proper,_=detect(pos,tri,np.arange(len(pos)));pairs=pairs[proper];pairs=pairs[np.any(mask[tri[pairs]].reshape(len(pairs),-1),axis=1)];assert len(pairs)==row['regionStrictPairs'][region]
  candidates=[(excursion(pos[tri[a]],pos[tri[b]]),int(a),int(b)) for a,b in pairs];value,a,b=max(candidates)
  labels=lambda face:dict(collections.Counter(names[dom[v]] for v in tri[face]))
  results.append({'domain':domain,'frameOrInputTick':frame,'timeS':driver['frames'][frame]['timeS'] if domain=='syntheticFour' else frame/120,'region':region,'strictPairs':len(pairs),'maximumStrictPlaneEndpointExcursionM':value,'triangleA':a,'triangleB':b,'nativeIDsA':tri[a].tolist(),'nativeIDsB':tri[b].tolist(),'dominantVertexBoneLabelsA':labels(a),'dominantVertexBoneLabelsB':labels(b),'XYZ_A':pos[tri[a]].tolist(),'XYZ_B':pos[tri[b]].tolist()})
weights=n['originalFullWeights'][931];report={'status':'UNACCEPTED_SELECTED_EXISTING_BODY_WITNESSES','recipeSHA256':sha(Path(__file__)),'frozenMethodsSHA256':sha(recipe),'assessmentSHA256':sha(out/'assessment.json'),'witnesses':results,'fullVsFourWorstNativeVertex931':{'restFileWorldM':rest[931].tolist(),'originalMembership':{names[j]:float(w) for j,w in enumerate(weights) if w>0}},'limits':['Strict plane endpoint excursion is a local geometric crossing witness, not closed-volume penetration depth or injury/anatomical severity.','Sphere regions overlap nearby torso surfaces; dominant bone labels are proxies, not anatomical segmentation.','Numeric triangles are analysis diagrams from existing stream fields; no new model/rig/export/render capture. Dressed films conceal naked folds.']};(out/'local-witnesses.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps([{k:v for k,v in x.items() if not k.startswith('XYZ')} for x in results]))
