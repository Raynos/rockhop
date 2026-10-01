"""Freeze the exact authorized correction failure and immutable prior evidence."""
from pathlib import Path
import hashlib,json,datetime
P=Path('/Users/raynos/projects/games/rockhop');R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/C-garment-pattern');O=P/'docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/trial03';A=P/'assets/blender/hero-remaster/rider/one-rider-v2/autonomous-lanes/C-garment-pattern'
assert not (O/'freeze-manifest.json').exists();sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
for prior in [O.parent/'freeze-manifest.json',O.parent/'trial02/freeze-manifest.json']:
 d=json.loads(prior.read_text());assert all(sha(Path(p))==m['sha256'] for p,m in d['files'].items()),'Earlier frozen trial changed'
files=[p for root in [O,R/'trial03'] for p in root.rglob('*') if p.is_file()]+[p for p in A.glob('*trial03.py') if p.is_file()]
report={'status':'FAILED C modular source-mask multiple circuits; no new cloth constructed','originalStartUTC':'2026-10-01 01:56:30 UTC','originalDeadlineUTC':'2026-10-01 02:26:30 UTC','finishedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'trial01AndTrial02ByteIdentical':True,'CApproachAppearanceFailures':1,'CModularSourceMaskSetupFailures':2,'authorizedRemovedExtraFaces':[19285,19904],'identifiedUnremovedIslandFaces':[26265,26268,26649,26650],'priorSixNeckFailuresRetained':True,'nextCorrectionNotExecuted':True,'liveJobs':[],'files':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)}}
(O/'freeze-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('CORRECTION_FAILURE_FROZEN',report['finishedUTC'],len(files))
