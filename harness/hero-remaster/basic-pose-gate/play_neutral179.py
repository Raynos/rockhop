"""Play explicit frozen neutral movie paths under the canonical shared lock."""
from pathlib import Path
import argparse,json,os,signal,subprocess,time
parser=argparse.ArgumentParser();parser.add_argument('--out',type=Path,required=True);parser.add_argument('movies',type=Path,nargs='+');args=parser.parse_args()
R=Path('/Users/raynos/projects/games/rockhop');args.out.mkdir(parents=True,exist_ok=True)
assert not(args.out/'process.json').exists(),'Do not overwrite completed playback evidence'
def anonymous():
    s=subprocess.check_output(['vm_stat'],text=True);page=int(s.split('page size of ')[1].split(' bytes')[0]);return page*int(next(l for l in s.splitlines()if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))
start=time.monotonic();peak=anonymous();rows=[];assert peak<70*10**9
try:
    for i,movie in enumerate(args.movies):
        assert movie.is_file()
        command=['pnpm','exec','tsx','harness/hero-remaster/basic-pose-gate/play_tube173.mts',str(movie.resolve()),str(args.out/f'played-{i}.json')]
        p=subprocess.Popen(command,cwd=R,start_new_session=True)
        while p.poll()is None:
            peak=max(peak,anonymous())
            if peak>=70*10**9 or time.monotonic()-start>=120:
                os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);raise RuntimeError('Stopped own playback at bounds')
            time.sleep(.25)
        rows.append({'command':command,'exitCode':p.returncode});assert p.returncode==0
finally:
    (args.out/'process.json').write_text(json.dumps({'commands':rows,'seconds':time.monotonic()-start,'peakAnonymousBytes':peak,'limits':'Muted full neutral orbit playback, no animation/anatomy/contact pass. Canonical lockf -k /Users/raynos/projects/localai/.model.lock; <70GB/120s.'},indent=2)+'\n')
