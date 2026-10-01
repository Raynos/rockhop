from pathlib import Path
import json,subprocess,time,os,signal,hashlib
repo=Path('/Users/raynos/projects/games/rockhop');out=repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind10/played01';out.mkdir(parents=True,exist_ok=True)
master='/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind10/rider.glb'
mapping={n:master for n in ['models/rider-street-mustard.glb','models/rider-street-mustard-lod.glb']};mappingfile=out/'mapping-full-diagnostic.json';mappingfile.write_text(json.dumps(mapping,indent=2)+'\n');build=repo/'harness/out/hero-remaster/new-rider-body10-build'
commands=[['pnpm','exec','tsx','harness/hero-remaster/build.mts',f'--out={build}',f'--models={mappingfile}','--new-rider-adapter=1'],['pnpm','exec','tsx','harness/hero-remaster/replay.mts',f'--build={build}',f'--out={out}/replay.json','--recording=docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json']]
for surface in ['textured','gray']:
 commands.append(['pnpm','exec','tsx','harness/hero-remaster/new-rider-played-capture.mts',f'--build={build}',f'--out={out}/{surface}','--mode=ride','--tier=high','--seconds=6','--fps=12','--focus=face','--detail-zoom=3',f'--surface={surface}','--recording=docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json'])
def anon():
 vm=subprocess.check_output(['vm_stat'],text=True);size=int(vm.split('page size of ')[1].split(' bytes')[0]);return int(next(l for l in vm.splitlines() if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))*size
start=time.monotonic();peak=anon();assert peak<70*10**9;rows=[]
try:
 for command in commands:
  p=subprocess.Popen(command,cwd=repo,start_new_session=True);begin=time.monotonic()
  while p.poll() is None:
   peak=max(peak,anon())
   if peak>=70*10**9 or time.monotonic()-start>1700:
    os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);raise RuntimeError('Stopped OWN workload: memory/batch bound')
   time.sleep(1)
  rows.append({'command':command,'status':p.returncode,'seconds':time.monotonic()-begin});assert p.returncode==0
finally:
 (out/'process.json').write_text(json.dumps({'privateOverlaySHA256':hashlib.sha256((repo/'harness/hero-remaster/new-rider-private-adapter.mts').read_bytes()).hexdigest(),'commands':rows,'wallSeconds':time.monotonic()-start,'peakAnonymousBytes':peak,'lock':'lockf -k /Users/raynos/projects/localai/.model.lock','limits':'Both tier names use FULL; diagnostic face camera/PBR-gray capture, not real LOD. Face maps read-only, physics/pose/assets unchanged.'},indent=2)+'\n')
 if (build/'hero-review.json').exists():(out/'build-manifest.json').write_bytes((build/'hero-review.json').read_bytes())
