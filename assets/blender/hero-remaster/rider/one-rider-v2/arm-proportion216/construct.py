"""ONE212-admitted longitudinal arm trial, saved before quality decisions."""
from pathlib import Path
import json,hashlib,struct,ast,time,resource,numpy as np
from scipy.sparse import coo_matrix
from scipy.sparse.csgraph import connected_components
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2');R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/arm-proportion216';D=B/'arm-proportion216'
def pin(p):return {'sha256':hashlib.sha256(p.read_bytes()).hexdigest(),'bytes':p.stat().st_size}
def h5(t):t=np.clip(t,0,1);return 6*t**5-15*t**4+10*t**3
def h5prime(t):return np.where((t>0)&(t<1),30*t**2*(t-1)**2,0)
pre=json.loads((E/'preflight-freeze.json').read_text());assert pre['status']=='OWNERSHIP_ADMITTED_LITERAL_PREREQUISITES_ONLY'
for p,q in pre['inputPins'].items():assert pin(Path(p))==q
assert pin(D/'ownership.npz')==pre['ownershipPin']
recipePin=pin(Path(__file__));(E/'construction-contract-freeze.json').write_text(json.dumps({'status':'REGISTERED_ONE_GEOMETRY_ATTEMPT_BEFORE_EDIT','preflightFreeze':pin(E/'preflight-freeze.json'),'recipe':recipePin,'source':pre['inputPins'][str(B/'finite-cleanup210/ancestry.npz')],'maximumDisplacementM':.26,'outputNativeCoordinates':True,'Float32ExportRigidResidualToleranceM':2e-7,'noTriangleEdits':True},indent=2)+'\n')
start=time.monotonic();z=np.load(B/'finite-cleanup210/ancestry.npz');O=np.load(D/'ownership.npz');M=O['matrixNativeToCanonical'];P=z['positions'].astype(float);F=z['faces'];Q=P@M[:3,:3].T+M[:3,3];Qnew=Q.copy();delta=np.zeros(len(P));J=np.repeat(np.eye(3)[None],len(P),axis=0)
spec=json.loads((R/'docs/evidence/hero-remaster/one-rider-v2/tpose-rig-adapter212/proposal.json').read_text())
for side,s in enumerate(spec['armTrial']):
    sign=1 if side==0 else -1;ids=O['leftOwned' if side==0 else 'rightOwned'];r=sign*Q[ids,2];y=Q[ids,1];du=s['outwardDisplacementAtKnotsM'][1];df=s['secondIncrementM'];u=(r-.18)/.16;v=(r-.34)/.16
    d=du*h5(u)+df*h5(v);dr=(du*h5prime(u)+df*h5prime(v))/.16;gate=h5((y-1.30)/.04);gy=h5prime((y-1.30)/.04)/.04;distal=r>=.50;gate[distal]=1;gy[distal]=0
    delta[ids]=sign*d*gate;Qnew[ids,2]+=delta[ids];J[ids,2,2]=1+dr*gate;J[ids,2,1]=sign*d*gy
# Only nativeX changes; nativeY/Z remain source exact. No inverse-transform rounding.
PN=P.copy();PN[:,0]-=delta/M[1,1];PF=PN.astype(np.float32);protected=O['protected'];assert np.array_equal(PF[protected],z['positions'][protected]);assert np.array_equal(PF[:,1:],z['positions'][:,1:])
assert not (D/'candidate-native.glb').exists()
np.savez_compressed(D/'construction.npz',sourcePositionsNative=z['positions'],candidatePositionsNativeFloat64=PN,candidatePositionsNativeFloat32=PF,faces=F,sourceRowToOutput=z['sourceRowToOutput'],representativeSourceRows=z['representativeSourceRows'],sourceFaceRows=z['sourceFaceRows'],sourceNativeVertexIDs=z['sourceNativeVertexIDs'],sourceNativeFaceIDs=z['sourceNativeFaceIDs'],deltaCanonicalZ=delta,matrixNativeToCanonical=M,fieldJacobiansCanonical=J)
# Literal source-display document: same index bytes, positions only replaced.
source=B/'finite-cleanup210/clean-native.glb';raw=source.read_bytes();ln,typ=struct.unpack_from('<II',raw,12);doc=json.loads(raw[20:20+ln]);offset=20+ln;bn,typ=struct.unpack_from('<II',raw,offset);binary=bytearray(raw[offset+8:offset+8+bn]);primitive=doc['meshes'][0]['primitives'][0];a=doc['accessors'][primitive['attributes']['POSITION']];bv=doc['bufferViews'][a['bufferView']];posoff=bv.get('byteOffset',0)+a.get('byteOffset',0);binary[posoff:posoff+PF.nbytes]=PF.astype('<f4').tobytes();a['min']=PF.min(0).tolist();a['max']=PF.max(0).tolist();doc['asset']['generator']='Rockhop admitted212 arm-proportion216 unaccepted'
js=json.dumps(doc,separators=(',',':')).encode();js+=b' '*((-len(js))%4);out=struct.pack('<III',0x46546c67,2,12+8+len(js)+8+len(binary))+struct.pack('<II',len(js),0x4e4f534a)+js+struct.pack('<II',len(binary),0x004e4942)+binary;(D/'candidate-native.glb').write_bytes(out)
read=out[20+len(js)+8:];back=np.frombuffer(read,dtype='<f4',count=PF.size,offset=posoff).reshape(PF.shape);assert np.array_equal(back,PF)
sourceIndexAccessor=doc['accessors'][primitive['indices']];ibv=doc['bufferViews'][sourceIndexAccessor['bufferView']];inds=np.frombuffer(read,dtype='<u4',count=F.size,offset=ibv.get('byteOffset',0)+sourceIndexAccessor.get('byteOffset',0)).reshape(-1,3);assert np.array_equal(inds,F[:,::-1])
# Reuse only the frozen pure topology function; never execute cleanup210 authoring.
helper=R/'assets/blender/hero-remaster/rider/one-rider-v2/finite-cleanup210/clean.py';tree=ast.parse(helper.read_text());fn=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='topology');env={'np':np,'coo_matrix':coo_matrix,'connected_components':connected_components};exec(compile(ast.Module(body=[fn],type_ignores=[]),str(helper),'exec'),env);audit=env['topology'](PF,F)
T0=P[F];T1=PF[F].astype(float);e0=T0[:,1]-T0[:,0];e1=T0[:,2]-T0[:,0];u=e0/np.linalg.norm(e0,axis=1)[:,None];normal=np.cross(e0,e1);area0=np.linalg.norm(normal,axis=1)/2;normal/=np.linalg.norm(normal,axis=1)[:,None];v=np.cross(normal,u);L=np.linalg.norm(e0,axis=1);a2=np.einsum('ij,ij->i',e1,u);b2=np.einsum('ij,ij->i',e1,v);f0=T1[:,1]-T1[:,0];f1=T1[:,2]-T1[:,0];column0=f0/L[:,None];column1=(f1-column0*a2[:,None])/b2[:,None];G=np.stack((column0,column1),axis=-1);stretch=np.linalg.svd(G,compute_uv=False);area1=np.linalg.norm(np.cross(f0,f1),axis=1)/2
hands=[]
for name in ('leftRigidHand','rightRigidHand'):
    ids=O[name];displacement64=PN[ids]-P[ids];residual64=np.max(np.abs(displacement64-displacement64[0]));floatResidualM=np.max(np.linalg.norm((PF[ids].astype(float)-P[ids])-displacement64[0],axis=1))*M[1,1];hands.append({'side':name,'vertices':len(ids),'exactFieldTranslationNative':displacement64[0].tolist(),'maximumFloat64RigidTranslationResidualNative':float(residual64),'maximumFloat32RigidTranslationResidualM':float(floatResidualM)})
fails=[]
for k in ('boundaryEdges','nonmanifoldEdges','windingConflictEdges','zeroAreaFaces'):
    if audit[k]:fails.append(k)
if audit['vertexLinkFailures']:fails.append('vertexLinkFailures')
aliases=len(PF)-len(np.unique(PF,axis=0))
if aliases:fails.append('newFloat32PositionAliases')
if np.max(abs(delta))>.26:fails.append('260mm displacement cap')
if not np.isfinite(PF).all():fails.append('nonfinite output')
if any(h['maximumFloat32RigidTranslationResidualM']>2e-7 for h in hands):fails.append('rigidhand export bound')
report={'status':'STRUCTURAL_PREREQUISITES_CLEAR_COLLISION_PENDING' if not fails else 'REJECTED_SAVED_PARTIAL_CANDIDATE','failures':fails,'geometryAttempts':1,'protectedPositionsExact':True,'hoodHeadChestPantsShoesTinyProtected':True,'nativeYZExactEverywhere':True,'sourceFacesIndicesAndMultiplicityExact':True,'GLBRoundTripExact':True,'maximumCanonicalDisplacementM':float(np.max(abs(delta))),'fieldDerivativeMaximum':float(J[:,2,2].max()),'fieldYShearMaximum':float(abs(J[:,2,1]).max()),'fieldJacobianMinimumDeterminant':float(np.linalg.det(J).min()),'fieldJacobianSingularValuesMinMax':[float(np.linalg.svd(J,compute_uv=False).min()),float(np.linalg.svd(J,compute_uv=False).max())],'triangleStretchSingularValuesPercentiles':np.percentile(stretch,[0,1,50,99,100],axis=0).tolist(),'triangleAreaRatioPercentiles':np.percentile(area1/area0,[0,1,50,99,100]).tolist(),'Float32PositionAliases':aliases,'hands':hands,'topology':audit,'elapsedSeconds':time.monotonic()-start,'peakRSSBytes':resource.getrusage(resource.RUSAGE_SELF).ru_maxrss,'outputs':{str(p):pin(p) for p in D.iterdir() if p.is_file()},'limits':['No visual, rigging, contact or player acceptance.','Native generated head remains provisional; liked head donor is not joined by this operation.','Globalcollision, allcoplanar and continuousfield-to-outputmotion checks still pending.','AnalyticpositivefieldJacobian does not establish finite-trianglecollision freedom.']}
(E/'construction-report.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report,indent=2))
