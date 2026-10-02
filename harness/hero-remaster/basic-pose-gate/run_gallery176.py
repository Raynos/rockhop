"""Canonical-lock bounded local or authenticated hosted review checks."""
from pathlib import Path
from http.server import ThreadingHTTPServer,SimpleHTTPRequestHandler
import functools,threading,json,os,signal,subprocess,time,sys,termios
R=Path('/Users/raynos/projects/games/rockhop');hosted='--hosted'in sys.argv;matched_only='--matched-only'in sys.argv
assert not matched_only or hosted,'Matched-only retry is scoped to hosted evidence'
E=R/'docs/evidence/hero-remaster/one-rider-v2/gallery176'/('hosted-matched-retry02'if matched_only else'hosted'if hosted else'local');E.mkdir(parents=True,exist_ok=True)
assert not(E/'process.json').exists(),'Preserve prior receipts'
auth=None;server=None
if hosted:
 state=termios.tcgetattr(sys.stdin);quiet=list(state);quiet[3]&=~termios.ECHO;termios.tcsetattr(sys.stdin,termios.TCSANOW,quiet)
 try:
  print('READY_FOR_EPHEMERAL_SITE_PLAYBACK_TOKEN',flush=True);auth=json.loads(sys.stdin.readline());assert isinstance(auth.get('token'),str)and auth['token']
 finally:termios.tcsetattr(sys.stdin,termios.TCSANOW,state)
 url='https://rockhop-rider-review.raynos.chatgpt.site/#sleeve-rebuild173'
else:
 class Quiet(SimpleHTTPRequestHandler):
  def log_message(self,*args):pass
 server=ThreadingHTTPServer(('127.0.0.1',0),functools.partial(Quiet,directory=str(R/'harness/out/hero-remaster/rider-review-site/dist')));threading.Thread(target=server.serve_forever,daemon=True).start();url=f'http://127.0.0.1:{server.server_port}/#sleeve-rebuild173'
def anonymous():
 s=subprocess.check_output(['vm_stat'],text=True);page=int(s.split('page size of ')[1].split(' bytes')[0]);return page*int(next(l for l in s.splitlines()if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))
start=time.monotonic();peak=anonymous();assert peak<70*10**9;receipts=[]
try:
 for script in(['check_gallery176.mts']if matched_only else['check_events171.mts','check_gallery176.mts']):
  cmd=['pnpm','exec','tsx','harness/hero-remaster/basic-pose-gate/'+script,str(E),url,'--expected-videos=30']+(['--auth-stdin']if hosted else[])
  p=subprocess.Popen(cmd,cwd=R,stdin=subprocess.PIPE if hosted else subprocess.DEVNULL,start_new_session=True)
  if auth:p.stdin.write((json.dumps(auth)+'\n').encode());p.stdin.close()
  while p.poll()is None:
   peak=max(peak,anonymous())
   if peak>=70*10**9 or time.monotonic()-start>=1700:
    os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);raise RuntimeError('Stopped own batch at resource bound')
   time.sleep(.5)
  receipts.append({'command':cmd,'status':p.returncode});assert p.returncode==0
finally:
 auth=None
 if server:server.shutdown();server.server_close()
 (E/'process.json').write_text(json.dumps({'commands':receipts,'seconds':time.monotonic()-start,'peakAnonymousBytes':peak,'memoryLimitBytes':70*10**9,'timeLimitSeconds':1700,'lock':'lockf -k /Users/raynos/projects/localai/.model.lock','credentialHandling':'Non-echo stdin; same-origin header only; no credentials persisted'},indent=2)+'\n')
