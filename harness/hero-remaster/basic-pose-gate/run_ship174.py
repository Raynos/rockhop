"""Current ordinary-source third-round gate; canonical lockf -k required."""
from pathlib import Path
import hashlib,json,signal,subprocess,time
R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/ship174';E.mkdir(parents=True,exist_ok=True)
build=R/'harness/out/hero-remaster/conditioning174-control';assert not build.exists() and not(E/'process.json').exists(),'Preserve completed builds/receipts'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
inputs=['src/render/hero/gltfRider.ts','src/render/hero/sleeveSkin.ts','harness/hero-remaster/build.mts','harness/hero-remaster/replay.mts']
hashes={p:sha(R/p)for p in inputs}
commands=[['pnpm','exec','tsx','harness/hero-remaster/build.mts','--out='+str(build)],['pnpm','exec','tsx','harness/hero-remaster/replay.mts','--build='+str(build),'--out='+str(E/'ship-gate.json'),'--recording=docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json']]
def anonymous():
 s=subprocess.check_output(['vm_stat'],text=True);page=int(s.split('page size of ')[1].split(' bytes')[0]);return page*int(next(l for l in s.splitlines()if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))
start=time.monotonic();peak=anonymous();rows=[];assert peak<70*10**9
try:
 for command in commands:
  step=time.monotonic();p=subprocess.Popen(command,cwd=R,start_new_session=True)
  while p.poll()is None:
   peak=max(peak,anonymous())
   if peak>=70*10**9 or time.monotonic()-start>=1700:
    os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);raise RuntimeError('Stopped own batch at resource bound')
   time.sleep(.5)
  rows.append({'command':command,'status':p.returncode,'seconds':time.monotonic()-step});assert p.returncode==0
 assert hashes=={p:sha(R/p)for p in inputs}
 review=json.loads((build/'hero-review.json').read_text());assert not review['mapping'] and not review['newRiderAdapter']
 (E/'build.json').write_text(json.dumps({'build':str(build),'inputSHA256':hashes,'publicCatalogModels':len(review['models']),'modelReplacements':0,'privatePoseOverlay':False,'limits':'Private build of current ordinary code; no rejected candidate or normal player asset promotion.'},indent=2)+'\n')
finally:
 (E/'process.json').write_text(json.dumps({'commands':rows,'seconds':time.monotonic()-start,'peakAnonymousBytes':peak,'memoryLimitBytes':70*10**9,'timeLimitSeconds':1700,'lock':'lockf -k /Users/raynos/projects/localai/.model.lock'},indent=2)+'\n')
