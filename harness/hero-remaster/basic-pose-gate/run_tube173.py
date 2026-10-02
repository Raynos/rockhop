"""Bounded short continuous exported gate; canonical lockf -k required."""
from pathlib import Path
import hashlib,json,os,signal,subprocess,time
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E=R/'docs/evidence/hero-remaster/one-rider-v2/tube-motion173';P=B/'candidate-export172/short-motion173'
assert not P.exists(),'Preserve completed captures';P.mkdir(parents=True);E.mkdir(parents=True,exist_ok=True)
full=B/'basic-pose-gate158/fixture-v4-asymmetric-halfsteps.json';d=json.loads(full.read_text())
selected=['overhead.L','sit'];d['frames']=[f for family in selected for f in d['frames']if f['family']==family];d['families']=selected
assert len(d['frames'])==386 and d['fps']==48
fixture=P/'fixture-short.json';fixture.write_text(json.dumps(d,separators=(',',':'))+'\n')
source=B/'candidate-handoff170/source06-protocol173/rider.glb';sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(source)=='80387f59dd90aec0176101fff88bb94c7c8756a89f61f66afb233db452fd0932'
(E/'mapping-report.json').write_bytes((source.parent/'mapping-report.json').read_bytes())
cmd=['pnpm','exec','tsx','harness/hero-remaster/basic-pose-gate/capture.mts','--source='+str(source),'--fixture='+str(fixture),'--out='+str(P/'capture')]
def anonymous():
 s=subprocess.check_output(['vm_stat'],text=True);page=int(s.split('page size of ')[1].split(' bytes')[0]);return page*int(next(l for l in s.splitlines()if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))
start=time.monotonic();peak=anonymous();assert peak<70*10**9
p=subprocess.Popen(cmd,cwd=R,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='2',UV_THREADPOOL_SIZE='2'))
try:
 while p.poll()is None:
  peak=max(peak,anonymous())
  if peak>=70*10**9 or time.monotonic()-start>=1700:
   os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);raise RuntimeError('Stopped own batch at resource bound')
  time.sleep(.5)
 assert p.returncode==0
 report=json.loads((P/'capture/report.json').read_text());assert len(report['frames'])==386 and not report.get('failure') and not report['errors']
 assert report['sourceSHA256']==sha(source) and sha(source)in report['loaded']
 (E/'capture-report.json').write_bytes((P/'capture/report.json').read_bytes())
 (E/'manifest.json').write_text(json.dumps({'status':'CAPTURE_ONLY_PARENT_MOVING_JUDGEMENT_PENDING','source':str(source),'sourceSHA256':sha(source),'fixtureSource':str(full),'fixtureSourceSHA256':sha(full),'fixture':str(fixture),'fixtureSHA256':sha(fixture),'families':selected,'frames':386,'fps':48,'movie':str(P/'capture/basic-poses.mp4'),'movieSHA256':sha(P/'capture/basic-poses.mp4'),'limits':'Short authored stress fixture only; no complete5404basic pose/art/actualGarage/physics/contact/mobile pass.'},indent=2)+'\n')
 print(json.dumps({'status':'CAPTURE_ONLY_JUDGEMENT_PENDING','frames':386,'seconds':time.monotonic()-start}))
finally:
 (E/'process.json').write_text(json.dumps({'command':cmd,'status':p.returncode,'seconds':time.monotonic()-start,'peakAnonymousBytes':peak,'memoryLimitBytes':70*10**9,'timeLimitSeconds':1700,'lock':'lockf -k /Users/raynos/projects/localai/.model.lock'},indent=2)+'\n')
