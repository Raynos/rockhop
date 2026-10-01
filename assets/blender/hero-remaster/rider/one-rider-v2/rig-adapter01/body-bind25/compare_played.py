"""Verify actual candidate byte load and all matched gameplay presentation records."""
from pathlib import Path
import json,math
out=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind25/morph01/played');build=json.loads((out.parent/'build-report.json').read_text());rows=[]
for angle in ['side','rear-three-quarter']:
 for surface in ['textured','gray']:
  a=json.loads((out/'baseline'/angle/surface/'report.json').read_text());b=json.loads((out/'candidate'/angle/surface/'report.json').read_text());assert not a.get('failure') and not b.get('failure');assert len(a['samples'])==len(b['samples'])==480
  assert b['sourceSHA256']==build['candidateSHA256'];assert any(r['sha256']==build['candidateSHA256'] and r['status']==200 for r in b['loaded'])
  for x,y in zip(a['samples'],b['samples']):
   for key in ['state','hash','debug','bones','orbit','camera','anchor']:assert x[key]==y[key],(angle,surface,x['i'],key)
   d=y['sleeveCorrective'];assert all(math.isfinite(w) for w in d['weights']);assert abs(sum(d['weights'])-d['strength'])<1e-12
  rows.append({'angle':angle,'surface':surface,'frames':480,'stateHashDebugBonesCameraAnchorExact':True,'sourceCandidateBytesActuallyLoaded':True,'correctiveActiveFrames':sum(s['sleeveCorrective']['strength']>0 for s in b['samples']),'strengthRange':[min(s['sleeveCorrective']['strength'] for s in b['samples']),max(s['sleeveCorrective']['strength'] for s in b['samples'])]})
(out/'matched-validation.json').write_text(json.dumps({'rows':rows,'limits':'Diagnostic frozen-renderer overlay, no release bundle or appearance acceptance. Surface morph is expected to change pixels.'},indent=2)+'\n');print(json.dumps(rows))
