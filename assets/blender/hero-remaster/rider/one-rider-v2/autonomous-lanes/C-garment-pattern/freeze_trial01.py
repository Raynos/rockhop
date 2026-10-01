"""Freeze one rejected trial and all actual evidence; no asset mutation."""
from pathlib import Path
import hashlib,json,datetime,sys
P=Path('/Users/raynos/projects/games/rockhop');R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/C-garment-pattern');O=P/'docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern'
assert not (O/'freeze-manifest.json').exists(),'Frozen trial manifest already exists'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
paths=[p for root in [O,P/'assets/blender/hero-remaster/rider/one-rider-v2/autonomous-lanes/C-garment-pattern',R/'trial01'] for p in root.rglob('*') if p.is_file()]
report={'status':'REJECTED parent appearance; full body5/10 face3/10, no rig/contact/player acceptance','deadlineUTC':'2026-10-01 02:17:00 UTC','finishedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'approachAppearanceFailures':1,'sixHistoricalNeckFailuresRetained':True,'measurementError':'Initial defaultUV0 audit retained; corrected materialUV1 raw-corner proof separate','sourcesUntouched':True,'CPUThreadCap':2,'noLiveBlenderJobs':True,'files':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(paths)}}
(O/'freeze-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('FROZEN',report['finishedUTC'],len(paths))
