"""Run local event controls under canonical lock and bounded anonymous memory."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import functools,threading,json,subprocess,os,time,signal
R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/gallery171';E.mkdir(parents=True,exist_ok=True)
class Quiet(SimpleHTTPRequestHandler):
 def log_message(self,*args):pass
server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'harness/out/hero-remaster/rider-review-site/dist')))
threading.Thread(target=server.serve_forever,daemon=True).start()
def anonymous():
 s=subprocess.check_output(['vm_stat'],text=True);page=int(s.split('page size of ')[1].split(' bytes')[0]);return page*int(next(l for l in s.splitlines()if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))
cmd=['pnpm','exec','tsx','harness/hero-remaster/basic-pose-gate/check_events171.mts',str(E),f'http://127.0.0.1:{server.server_port}/#structural-gate']
start=time.monotonic();peak=anonymous();assert peak<70*10**9
p=subprocess.Popen(cmd,cwd=R,start_new_session=True)
try:
 while p.poll()is None:
  peak=max(peak,anonymous())
  if peak>=70*10**9 or time.monotonic()-start>=1700:
   os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);raise RuntimeError('Stopped own batch at resource bound')
  time.sleep(.5)
 assert p.returncode==0
finally:
 server.shutdown();server.server_close()
 (E/'process.json').write_text(json.dumps({'command':cmd,'status':p.returncode,'seconds':time.monotonic()-start,'peakAnonymousBytes':peak,'memoryLimitBytes':70*10**9,'timeLimitSeconds':1700,'lock':'lockf -k /Users/raynos/projects/localai/.model.lock'},indent=2)+'\n')
