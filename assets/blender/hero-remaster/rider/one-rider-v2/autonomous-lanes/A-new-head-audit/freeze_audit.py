"""Freeze source/evidence/reference/dry-run proof; no model imports or execution."""
from pathlib import Path
import json,hashlib,ast,subprocess,shutil,sys
from PIL import Image
P=Path('/Users/raynos/projects/games/rockhop');S=P/'assets/blender/hero-remaster/rider/one-rider-v2/autonomous-lanes/A-new-head-audit';O=P/'docs/evidence/hero-remaster/one-rider-v2/autonomous-lanes/A-new-head-audit';R=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/A-new-head-audit')
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
if (O/'checkpoint-manifest.json').exists():raise RuntimeError('Frozen checkpoint exists')
ref=P/'assets/design/hero-remaster/one-rider-v2/head/buzz-bust-reference.png';im=Image.open(ref);assert im.mode=='RGBA';alpha=im.getchannel('A');assert alpha.getextrema()==(0,255)
reference={'path':str(ref),'SHA256':sha(ref),'mode':im.mode,'dimensions':list(im.size),'alphaExtrema':list(alpha.getextrema()),'opaquePixels':alpha.histogram()[255],'transparentPixels':alpha.histogram()[0]}
command=[sys.executable,str(S/'queued_model_worker.py'),'--tag','h21-buzz-native01','--','/Users/raynos/ml/img2mesh/Hunyuan3D-2.1/.venv/bin/python','-u',str(S/'hunyuan21-head-preserve.py'),'--image',str(ref),'--out',str(R/'generation/h21-buzz-native01'),'--seed','42','--shape-steps','24','--octree','320','--target-faces','100000']
dry=json.loads(subprocess.check_output(command,text=True));assert dry['status'].startswith('PREPARED ONLY') and not dry['eviction'];(O/'h21-queue-dry-run.json').write_text(json.dumps(dry,indent=2)+'\n')
proof=json.loads((O/'generation-preparation.json').read_text());proof.update(ownedRunnerSHA256=sha(S/'hunyuan21-head-preserve.py'),ownedWrapperSHA256=sha(S/'queued_model_worker.py'),reference=reference,dryRunSHA256=sha(O/'h21-queue-dry-run.json'),actualFullExecutionCommand=[command[0],command[1],'--execute']+command[2:],GPUJobQueued=False,CPUOnlyWrapperTests={'tests':6,'outcome':'PASS; mocked process/lock/memory fixtures, no GPU execution'},hardAnonymousLimitBytes=70e9,preemptiveStopBytes=65e9,pollIntervalSeconds=1)
(O/'generation-preparation.json').write_text(json.dumps(proof,indent=2)+'\n')
for tag in ['faces01','rawshape01','h21aligned01']:shutil.copyfile(R/(tag+'.log'),O/(tag+'-log.txt'))
scripts=list(S.glob('*.py'))
for p in scripts:ast.parse(p.read_text(),filename=str(p))
paths=scripts+[p for p in O.rglob('*') if p.is_file()]
manifest={'status':'Frozen read-only NEW face audit, no accepted rider/head; prepared generation not launched','sourceEvidenceSHA256':{str(p.relative_to(P)):sha(p) for p in paths},'reference':reference,'fullExecutionCommand':proof['actualFullExecutionCommand'],'ASTParsedRecipes':len(scripts),'noLiveProcesses':True,'GPUJobs':[],'effectiveCPUDeadlineUTC':'2026-10-01T02:17:00Z','parentJudges':True,'renderingErrorRetained':'Initial N2 X0 underside frame; corrected read-only X180 in separate output directory','currentRepairLineageCountFromParent':13,'comparisonsAreNotNewGenerationFailures':True,'limit':'Sampled one-second memory guard with5GBheadroom does not prove subsecond peaks absent'}
(O/'checkpoint-manifest.json').write_text(json.dumps(manifest,indent=2)+'\n');print(json.dumps({'ASTParsed':len(scripts),'frozenFiles':len(paths),'sourcePNGAlpha':reference,'wrapperSHA256':proof['ownedWrapperSHA256'],'runnerSHA256':proof['ownedRunnerSHA256']}),flush=True)
