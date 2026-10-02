"""Silent headless candidate identity smoke; not an appearance or motion gate."""
from pathlib import Path
import hashlib,json,subprocess,os,time,signal
R=Path('/Users/raynos/projects/games/rockhop')
B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E=R/'docs/evidence/hero-remaster/one-rider-v2/candidate-handoff170'
P=B/'candidate-handoff170/identity-smoke'
assert not P.exists(),'Preserve frozen smoke outputs'
P.mkdir(parents=True);E.mkdir(parents=True,exist_ok=True)
fixture=B/'basic-pose-gate158/fixture-v4-asymmetric-halfsteps.json'
d=json.loads(fixture.read_text());d['frames']=d['frames'][:3];d['families']=sorted(set(r['family']for r in d['frames']))
smoke=P/'fixture-three-frames.json';smoke.write_text(json.dumps(d,separators=(',',':'))+'\n')
source=B/'garment-rebuild01/physical-v5-control157/rider.glb'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
def anonymous():
 s=subprocess.check_output(['vm_stat'],text=True);page=int(s.split('page size of ')[1].split(' bytes')[0]);return page*int(next(l for l in s.splitlines()if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))
cmd=['pnpm','exec','tsx','harness/hero-remaster/basic-pose-gate/capture.mts','--source='+str(source),'--fixture='+str(smoke),'--out='+str(P/'capture')]
start=time.monotonic();peak=anonymous();assert peak<70*10**9
process=subprocess.Popen(cmd,cwd=R,start_new_session=True,env=dict(os.environ,OMP_NUM_THREADS='2',UV_THREADPOOL_SIZE='2'))
try:
 while process.poll()is None:
  peak=max(peak,anonymous())
  if peak>=70*10**9 or time.monotonic()-start>=1700:
   os.killpg(process.pid,signal.SIGTERM);process.wait(timeout=20);raise RuntimeError('Own job stopped at resource bound')
  time.sleep(.25)
 assert process.returncode==0
 capture=json.loads((P/'capture/report.json').read_text());assert len(capture['frames'])==3 and not capture['errors'] and 'failure'not in capture
 assert capture['sourceSHA256']==sha(source) and capture['loaded']==[sha(source)]
 assert capture['fixtureSHA256']==sha(smoke)
 result={'status':'CANDIDATE_IDENTITY_SMOKE_ONLY','sourceSHA256':sha(source),'source':str(source),'fixtureSource':str(fixture),'fixtureSourceSHA256':sha(fixture),'subsetFrames':3,'captureReport':str(P/'capture/report.json'),'captureReportSHA256':sha(P/'capture/report.json'),'capture':capture,'command':cmd,'seconds':time.monotonic()-start,'peakAnonymousBytes':peak,'canonicalLock':'lockf -k /Users/raynos/projects/localai/.model.lock','limits':['Three-frame smoke only; no continuous pose, character repair, garment or appearance pass.','Uses retained V5 control; next construction candidate has not passed export/integration gates.','Silent headless WebKit; no physical mobile or actual gameplay measurement.']}
 (E/'identity-smoke.json').write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items()if k in ['status','subsetFrames','seconds','peakAnonymousBytes']}))
finally:
 (E/'identity-process.json').write_text(json.dumps({'status':process.returncode,'seconds':time.monotonic()-start,'peakAnonymousBytes':peak,'memoryLimitBytes':70*10**9,'timeLimitSeconds':1700,'canonicalLock':'lockf -k /Users/raynos/projects/localai/.model.lock'},indent=2)+'\n')
