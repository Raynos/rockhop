"""Matched fixed-baseline review overlay; no production bundle acceptance claim."""
from pathlib import Path
import json,hashlib,shutil
repo=Path('/Users/raynos/projects/games/rockhop');baseline=repo/'harness/out/hero-remaster/new-rider-body11-build';out=repo/'harness/out/hero-remaster/new-rider-body26-overlay'
report=json.loads((repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind26/build-report.json').read_text());candidate=Path(report['candidate']);sha=lambda b:hashlib.sha256(b).hexdigest();assert sha(candidate.read_bytes())==report['candidateSHA256']
assert not out.exists(),'Frozen overlay cannot be overwritten';shutil.copytree(baseline,out)
catalog=json.loads((out/'model-catalog.json').read_text());changes=[]
for model in catalog['models']:
 if model['logical'] not in ['models/rider-street-mustard.glb','models/rider-street-mustard-lod.glb']:continue
 oldurl=model['url'];oldsha=model['sha256'];oldbytes=model['bytes'];newurl=oldurl.replace(oldsha[:16],report['candidateSHA256'][:16]);newurl=newurl.replace(oldsha[:16],report['candidateSHA256'][:16]);newfile=out/newurl;newfile.parent.mkdir(parents=True,exist_ok=True);newfile.write_bytes(candidate.read_bytes())
 for p in out.rglob('*'):
  if p.is_file() and p.suffix in ['.js','.json','.html']:
   s=p.read_text();n=s.replace(oldurl,newurl).replace(oldsha,report['candidateSHA256'])
   if n!=s:p.write_text(n)
 model.update(url=newurl,sha256=report['candidateSHA256'],bytes=candidate.stat().st_size);changes.append({'oldURL':oldurl,'newURL':newurl,'oldBytes':oldbytes,'newBytes':candidate.stat().st_size})
 assert sha(newfile.read_bytes())==report['candidateSHA256']
assert len(changes)==2
(out/'model-catalog.json').write_text(json.dumps(catalog,indent=2)+'\n')
(out/'anatomical-weight-overlay.json').write_text(json.dumps({'kind':'fixed current11 build plus exact new anatomical-weight GLB, no corrective driver','sourceBuild':str(baseline),'candidateSHA256':report['candidateSHA256'],'releaseBuild':False,'productionBundleGate':'Overlay is only matched art evidence, no corrective driver. Current-source bundle/actualLOD qualification remains open.','changes':changes},indent=2)+'\n')
print(json.dumps({'out':str(out),'changes':changes}))
