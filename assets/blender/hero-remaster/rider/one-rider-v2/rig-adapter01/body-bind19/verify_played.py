from pathlib import Path
import json
import numpy as np
base=Path('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01');out=base/'body-bind19/morph01/played';rows=[]
for angle in ['side','rear-three-quarter']:
 for surface in ['textured','gray']:
  a=json.loads((base/'played-hips11/framed02'/angle/surface/'report.json').read_text());b=json.loads((out/angle/surface/'report.json').read_text());assert len(a['samples'])==len(b['samples'])==264
  for x,y in zip(a['samples'],b['samples']):
   for key in ['state','hash','debug','bones','orbit','camera','anchor']:assert x[key]==y[key],(angle,surface,x['i'],key)
   d=y['hipCorrective'];assert abs(sum(d['weights'])-d['strength'])<1e-12
  rows.append({'angle':angle,'surface':surface,'frames':264,'stateHashDebugBonesCameraAnchorExact':True,'correctiveActiveFrames':sum(s['hipCorrective']['strength']>0 for s in b['samples']),'strengthRange':[min(s['hipCorrective']['strength'] for s in b['samples']),max(s['hipCorrective']['strength'] for s in b['samples'])]})
(out/'matched-validation.json').write_text(json.dumps({'rows':rows,'limits':'Frozen renderer review overlay; release bundle gate still open. Morph shape/normals change, source behavior/camera exact.'},indent=2)+'\n');print(json.dumps(rows))
