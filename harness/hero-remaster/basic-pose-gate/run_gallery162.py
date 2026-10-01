"""Silent local gallery playback + third-round game gate, under canonical lockf."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
from functools import partial
import json,os,signal,subprocess,threading,time,hashlib,sys
repo=Path('/Users/raynos/projects/games/rockhop');out=repo/'docs/evidence/hero-remaster/one-rider-v2/gallery162'
if '--reduced' in sys.argv:out=out/'reduced'
out.mkdir(parents=True,exist_ok=True)
assert not (out/'local-site-check.json').exists(), 'Preserve each completed playback receipt'
site=repo/'harness/out/hero-remaster/rider-review-site/dist';assert (site/'index.html').read_text().count('<video ')==29
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),partial(Quiet,directory=str(site)));threading.Thread(target=server.serve_forever,daemon=True).start()
def anonymous():
 vm=subprocess.check_output(['vm_stat'],text=True);size=int(vm.split('page size of ')[1].split(' bytes')[0]);return int(next(l for l in vm.splitlines() if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))*size
start=time.monotonic();peak=anonymous();assert peak<70*10**9;rows=[]
commands=[['pnpm','exec','tsx','harness/hero-remaster/basic-pose-gate/check_gallery162.mts',str(out),f'http://127.0.0.1:{server.server_port}/'],['pnpm','exec','tsx','harness/hero-remaster/replay.mts','--build=harness/out/hero-remaster/new-rider-body34-overlay',f'--out={out}/ship-gate162.json','--recording=docs/evidence/hero-remaster/rider-search-v1/gameplay-inputs/recordings/b1-first-ride-bot-3.json']]
if '--gallery-only' in sys.argv: commands=commands[:1]
try:
 for command in commands:
  begin=time.monotonic();p=subprocess.Popen(command,cwd=repo,start_new_session=True)
  while p.poll() is None:
   peak=max(peak,anonymous())
   if peak>=70*10**9 or time.monotonic()-start>=1700:
    os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);raise RuntimeError('Stopped own batch at memory/time bound')
   time.sleep(1)
  rows.append({'command':command,'status':p.returncode,'seconds':time.monotonic()-begin});assert p.returncode==0
finally:
 server.shutdown();server.server_close();(out/('checks-process-reduced.json' if '--gallery-only' in sys.argv else 'checks-process.json')).write_text(json.dumps({'commands':rows,'seconds':time.monotonic()-start,'peakAnonymousBytes':peak,'lock':'lockf -k /Users/raynos/projects/localai/.model.lock','memoryLimitBytes':70*10**9,'timeLimitSeconds':1700,'limits':'Headless390/1200 playback and unchanged retained34 ship gate; no physical iPhone or new candidate acceptance.'},indent=2)+'\n')
