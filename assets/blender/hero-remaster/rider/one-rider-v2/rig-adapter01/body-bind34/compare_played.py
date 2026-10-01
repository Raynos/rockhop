"""Live freshC19 driver parity, original physics/input and exact reference cameras."""
from pathlib import Path
import json,numpy as np
base=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01');out=base/'body-bind34/played';mapping=json.loads((out.parent/'mapping-report.json').read_text());cpu=json.loads((out.parent/'candidate-cpu/pose-manifest.json').read_text());rows=[];allReports={}
expectedAxes={r['bone']:r['anatomicalWorldDirection'] for r in mapping['restAxes']}
for angle in ['side','rear-three-quarter']:
 for surface in ['textured','gray']:
  a=json.loads((base/'body-bind25/morph01/played/baseline'/angle/surface/'report.json').read_text());b=json.loads((out/'candidate'/angle/surface/'report.json').read_text());allReports[angle,surface]=b
  assert not b.get('failure') and b['errors']==[] and len(a['samples'])==len(b['samples'])==480
  assert b['sourceSHA256']==mapping['candidateSHA256'] and any(r['sha256']==mapping['candidateSHA256'] and r['status']==200 for r in b['loaded'])
  maxAxis=0;maxBone=0;maxResidual=0
  for x,y in zip(a['samples'],b['samples']):
   for key in ['state','hash','phase','orbit','camera']:assert x[key]==y[key],(angle,surface,y['i'],key)
   assert y['sleeveCorrective'] is None and y['debug']['physicalPose'] and y['debug']['bones']==19
   for bone,expected in expectedAxes.items():maxAxis=max(maxAxis,float(np.linalg.norm(np.asarray(y['restAxes'][bone])-expected)))
  for cp in cpu['rows']:
   actual=b['samples'][cp['i']]
   for bone in cp['bonePoints']:maxBone=max(maxBone,float(np.linalg.norm(np.asarray(actual['bonesInBikeFrame'][bone['name']])-bone['bikeFramePosition'])))
   for field,expected in cp['debug'].items():
    if field in ['comResidual','soleErr']:
     error=float(np.max(np.abs(np.asarray(actual['debug'][field])-expected)));maxResidual=max(maxResidual,error);assert error<=1e-12,(angle,surface,cp['i'],field,error)
    else:assert actual['debug'][field]==expected,(angle,surface,cp['i'],field)
  assert maxAxis<1e-6 and maxBone<1e-5
  rows.append({'angle':angle,'surface':surface,'frames':480,'stateHashPhaseOrbitCameraExact':True,'actualSourceSHA256':mapping['candidateSHA256'],'anatomicalAxisMaximumError':maxAxis,'fourCPUStateBoneBikeFrameMaximumErrorM':maxBone,'fourCPUStateOtherDebugFieldsExact':True,'fourCPUStateComAndSoleResidualMaximumErrorM':maxResidual,'fourCPUStateComAndSoleResidualToleranceM':1e-12,'allFramesPhysicalPoseAnd19Bones':True,'correctiveDriver':False})
for angle in ['side','rear-three-quarter']:
 for a,b in zip(allReports[angle,'textured']['samples'],allReports[angle,'gray']['samples']):
  for key in ['state','hash','debug','bones','bonesInBikeFrame','restAxes','orbit','camera','anchor']:assert a[key]==b[key],(angle,a['i'],key)
(out/'matched-validation.json').write_text(json.dumps({'rows':rows,'pairedPBRGrayStateBonesAxesCameraExactFrames':960,'limits':'Body/bone positions intentionally change with new binds/weights; exact fixed baseline cameras, state and live CPU/browser driver parity proven. No rendered appearance, stage/LOD/device pass implied.'},indent=2)+'\n');print(json.dumps(rows,indent=2))
