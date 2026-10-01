from pathlib import Path
import json,subprocess,time,os,signal
repo=Path('/Users/raynos/projects/games/rockhop');out=repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind05/played02';out.mkdir(parents=True,exist_ok=True)
master='/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind05/rider.glb'
mapping={n:master for n in ['models/rider-street-mustard.glb','models/rider-street-mustard-lod.glb']};mappingfile=out/'mapping-full-diagnostic.json';mappingfile.write_text(json.dumps(mapping,indent=2)+'\n');build=repo/'harness/out/hero-remaster/new-rider-body05-build'
commands=[['pnpm','exec','tsx','harness/hero-remaster/new-rider-played-capture.mts',f'--build={build}',f'--out={out}/{focus}','--mode=ride','--tier=high','--seconds=40','--fps=12',f'--focus={focus}','--recording=docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json'] for focus in ['body','hands','feet']]
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
 (out/'process.json').write_text(json.dumps({'commands':rows,'wallSeconds':time.monotonic()-start,'peakAnonymousBytes':peak,'lock':'lockf -k /Users/raynos/projects/localai/.model.lock','limits':'Both tier modelnames explicitly use the SAME FULL candidate for contact diagnostics; real LOD gate remains unmeasured. Private build only, physics and bikes unchanged.'},indent=2)+'\n')
 if (build/'hero-review.json').exists():(out/'build-manifest.json').write_bytes((build/'hero-review.json').read_bytes())
