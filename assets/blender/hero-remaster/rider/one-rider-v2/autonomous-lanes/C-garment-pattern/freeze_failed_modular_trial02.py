"""Freeze one source-mask failure with complete evidence before any correction."""
from pathlib import Path
import hashlib,json,datetime
P=Path('/Users/raynos/projects/games/rockhop');R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/C-garment-pattern');O=P/'docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/C-garment-pattern/trial02';A=P/'assets/blender/hero-remaster/rider/one-rider-v2/autonomous-lanes/C-garment-pattern'
assert not (O/'freeze-manifest.json').exists()
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
prior=json.loads((O.parent/'freeze-manifest.json').read_text());changed=[p for p,meta in prior['files'].items() if sha(Path(p))!=meta['sha256']];assert not changed,'Trial01 must remain byte-identical'
files=[p for root in [O,R/'trial02'] for p in root.rglob('*') if p.is_file()]+[p for p in A.glob('*trial02.py') if p.is_file()]
report={'status':'FAILED C modular source-mask setup; no new cloth constructed','originalStartUTC':'2026-10-01 01:56:30 UTC','originalDeadlineUTC':'2026-10-01 02:26:30 UTC','finishedUTC':datetime.datetime.now(datetime.timezone.utc).isoformat(),'trial01ByteIdentical':True,'CApproachAppearanceFailures':1,'CModularSourceMaskSetupFailures':1,'priorSixNeckFailuresRetained':True,'exactPinchSourceFaceIds':[19285,19904],'nextCorrectionNotExecuted':True,'liveJobs':[],'files':{str(p):{'sha256':sha(p),'bytes':p.stat().st_size} for p in sorted(files)}}
(O/'freeze-manifest.json').write_text(json.dumps(report,indent=2)+'\n');print('MODULAR_FAILURE_FROZEN',report['finishedUTC'],len(files))
