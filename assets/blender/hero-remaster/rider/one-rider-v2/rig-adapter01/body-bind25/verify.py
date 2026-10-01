"""Read-only append-only GLB and actual Three.js four-key target verification."""
from pathlib import Path
import json,hashlib,struct,copy,sys
import numpy as np
sys.path.insert(0,str(Path(__file__).parent.parent/'body-bind21'))
from common import SOURCE,load,accessor
np.seterr(all='raise')
OUT=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind25/morph01');ROOT=SOURCE.parent.parent.parent
BASE=OUT.parent.parent/'body-bind21/baseline-cpu';AUTH=OUT.parent.parent/'body-bind23'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def read(rec,lanes,folder):
 if 'privatePath' in rec:path=Path(rec['privatePath'])
 else:
  path=folder/rec['file']
  if not path.exists():path=ROOT/(('body-bind25/morph01/'+folder.name) if folder.parent==OUT else 'body-bind21/baseline-cpu')/rec['file']
 raw=path.read_bytes();assert sha(raw)==rec['sha256'];return np.frombuffer(raw,dtype='<f8').reshape(-1,lanes).copy()
report=json.loads((OUT/'build-report.json').read_text());src,sj,sb,sp,_=load();raw=Path(report['candidate']).read_bytes();assert sha(raw)==report['candidateSHA256'];assert sha(src)==report['sourceSHA256'];n=struct.unpack_from('<I',raw,12)[0];cj=json.loads(raw[20:20+n]);cb=raw[28+n:];assert cb[:len(sb)]==sb;assert SOURCE.read_bytes()==src;assert struct.unpack_from('<I',raw,8)[0]==len(raw)
restored=copy.deepcopy(cj);restored['accessors']=restored['accessors'][:len(sj['accessors'])];restored['bufferViews']=restored['bufferViews'][:len(sj['bufferViews'])];restored['buffers']=copy.deepcopy(sj['buffers']);restored['meshes'][0]['weights']=restored['meshes'][0]['weights'][:2];restored['meshes'][0]['extras']['targetNames']=restored['meshes'][0]['extras']['targetNames'][:2]
for p in restored['meshes'][0]['primitives']:p['targets']=p['targets'][:2]
node=next(n for n in restored['nodes'] if n.get('mesh')==0);del node['extras']['rockhopSleeveCorrective']
if not node['extras'] and 'extras' not in next(n for n in sj['nodes'] if n.get('mesh')==0):del node['extras']
assert restored==sj
assert len(cj['skins'][0]['joints'])==19;meta=json.loads(next(n for n in cj['nodes'] if n.get('mesh')==0)['extras']['rockhopSleeveCorrective']);assert meta==report['metadata'];assert meta['jointNames']==['chest','upperArm.L','forearm.L','upperArm.R','forearm.R']
# Four arm-chain quaternion features, not recorded sample numbers, select targets.
assert [k['name'] for k in meta['keys']]==[f'sleeveCorrective.sample{i}' for i in [114,186,304,426]]
for pi,p in enumerate(cj['meshes'][0]['primitives']):
 assert p['targets'][:2]==sj['meshes'][0]['primitives'][pi]['targets'];assert len(p['targets'])==6
 for ti,k in enumerate(meta['keys']):
  delta=accessor(cj,cb,p['targets'][ti+2]['POSITION'])[0];norm=accessor(cj,cb,p['targets'][ti+2]['NORMAL'])[0]
  if pi==0:assert sha(delta.astype('<f4').tobytes())==k['positionDeltaSHA256'];assert sha(norm.astype('<f4').tobytes())==k['normalDeltaSHA256']
  else:assert not np.any(delta);assert not np.any(norm)
base=json.loads((BASE/'pose-manifest.json').read_text());auth=json.loads((AUTH/'pose-manifest.json').read_text());actual=json.loads((OUT/'cpu/pose-manifest.json').read_text());normalBaseline=json.loads((OUT/'baseline-normal01/pose-manifest.json').read_text());assert normalBaseline['sourceSHA256']==report['sourceSHA256'];assert actual['sourceSHA256']==report['candidateSHA256'];rows=[]
for key,(b,a,c) in enumerate(zip(base['rows'],auth['rows'],actual['rows'])):
 assert b['i']==a['i']==c['i'];assert b['debug']==c['debug'];assert b['contacts']==c['contacts'];assert b['bonePoints']==c['bonePoints'];assert b['bodyworkBikeFrame']==c['bodyworkBikeFrame']
 normalRow=normalBaseline['rows'][key];assert normalRow['i']==b['i'];assert normalRow['debug']==b['debug'];assert normalRow['contacts']==b['contacts'];assert normalRow['bonePoints']==b['bonePoints'];assert normalRow['bodyworkBikeFrame']==b['bodyworkBikeFrame']
 diag=c['sleeveCorrective'];assert diag['nearestRad']<1e-6;assert diag['strength']==1;assert abs(diag['weights'][key]-1)<1e-9;assert abs(sum(diag['weights'])-1)<1e-12;assert len(diag['features'])==4
 d=read(a['dump'][0]['correctiveDelta'],3,AUTH);free=np.any(d!=0,axis=1);errors=[];normalErrors=[]
 for mi,(bd,ad,cd) in enumerate(zip(b['dump'],a['dump'],c['dump'])):
  old=read(bd['positions'],3,BASE);target=read(ad['positions'],3,AUTH);pos=read(cd['positions'],3,OUT/'cpu');oldn=read(normalBaseline['rows'][key]['dump'][mi]['gpuRuleSkinnedNormals'],3,OUT/'baseline-normal01');targetn=read(ad['gpuRuleSkinnedNormals'],3,AUTH);norm=read(cd['gpuRuleSkinnedNormals'],3,OUT/'cpu');errors.append(float(np.linalg.norm(pos-target,axis=1).max()));normalErrors.append(float(np.linalg.norm(norm-targetn,axis=1).max()))
  assert np.array_equal(old,read(normalRow['dump'][mi]['positions'],3,OUT/'baseline-normal01'));assert np.array_equal(read(bd['skinMatrices'],16,BASE),read(normalRow['dump'][mi]['skinMatrices'],16,OUT/'baseline-normal01'));assert np.array_equal(read(bd['skinMatrices'],16,BASE),read(cd['skinMatrices'],16,OUT/'cpu'));assert np.array_equal(read(bd['jointTransforms'],16,BASE),read(cd['jointTransforms'],16,OUT/'cpu'))
  if mi==0:assert np.array_equal(old[~free],pos[~free]);assert np.array_equal(oldn[~free],norm[~free])
  else:assert np.array_equal(old,pos);assert np.array_equal(oldn,norm)
 assert max(errors)<1e-7;assert max(normalErrors)<1e-6
 rows.append({'sample':b['i'],'maximumActualThreeMorphVsAuthoredPositionErrorM':max(errors),'maximumActualThreeMorphVsAuthoredNormalError':max(normalErrors),'driver':diag,'outsideCorrectedSleevePositionsNormalsExact':True,'otherCapturedPrimitivePositionsNormalsExact':True,'actualSkinJointTransformsDebugBonesContactsExact':True,'maximumContactVsRetainedPlayedM':max(r['maximumCPUvsActualPlayedSurfaceM'] for r in c['contacts'])})
summary={'sourceSHA256':sha(src),'candidateSHA256':sha(raw),'originalBINPrefixExactBytes':len(sb),'allOriginalJSONExceptExplicitMorphAppendsExact':True,'originalTwoGripTargetsExact':True,'all19BonesBindsSocketsAndPhysicsContractRetained':True,'bothOtherBodyPrimitivesAddedTargetsZero':True,'actualRuntimeFeatureFormula':'quaternion decompose(normalize) of bone.matrixWorld * boneInverse * mesh.bindMatrix; inverse chest quaternion * each of four upperArm/forearm quaternions','fourActualKeysReproduced':True,'normalBaselineCorrection':'Original body21 GPU normal diagnostic omitted retained grip NORMAL morphs; source11 baseline-normal01 includes them. Old baseline positions/matrices/debug/contacts are unchanged. Protected runtime normals are compared against this corrected baseline.','rows':rows,'limits':'Four recorded keys only. Large source/body23 displacements remain a hypothesis; no interpolation, collision, moving silhouette or art score acceptance.'}
print(json.dumps(summary,indent=2))
