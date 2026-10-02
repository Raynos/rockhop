"""Play both actual failed neutral films silently; canonical lockf -k required."""
from pathlib import Path
import json,os,subprocess,signal,time
R=Path('/Users/raynos/projects/games/rockhop');E=R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/drafted-raglan';O=E/'parent-playback';O.mkdir(parents=True,exist_ok=True);assert not(O/'process.json').exists()
def anonymous():
 s=subprocess.check_output(['vm_stat'],text=True);page=int(s.split('page size of ')[1].split(' bytes')[0]);return page*int(next(l for l in s.splitlines()if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))
start=time.monotonic();peak=anonymous();assert peak<70*10**9;receipts=[]
try:
 for mode in['pbr','gray']:
  cmd=['pnpm','exec','tsx','harness/hero-remaster/basic-pose-gate/play_tube173.mts',str(E/f'FAILED-neutral-{mode}-turntable.mp4'),str(O/f'{mode}.json')];p=subprocess.Popen(cmd,cwd=R,start_new_session=True)
  while p.poll()is None:
   peak=max(peak,anonymous())
   if peak>=70*10**9 or time.monotonic()-start>=60:
    os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);raise RuntimeError('Stopped own batch at resource bound')
   time.sleep(.25)
  receipts.append({'command':cmd,'status':p.returncode});assert p.returncode==0
finally:
 (O/'process.json').write_text(json.dumps({'commands':receipts,'seconds':time.monotonic()-start,'peakAnonymousBytes':peak,'memoryLimitBytes':70*10**9,'timeLimitSeconds':60,'lock':'lockf -k /Users/raynos/projects/localai/.model.lock','limits':'Neutral orbit decoder only; not animated anatomy/pose/contact acceptance.'},indent=2)+'\n')
