from pathlib import Path
import subprocess,json,hashlib,time
root=Path('/Users/raynos/projects/games/rockhop');out=root/'harness/out/rider-finish-2026-10-05/round51';out.mkdir(parents=True,exist_ok=False)
inputs=['src/render/hero/gltfRider.ts','src/render/hero/sleeveSkin.ts','harness/hero-remaster/build.mts','harness/hero-remaster/replay.mts']
sha=lambda p:hashlib.sha256(Path(p).read_bytes()).hexdigest();pins={p:sha(root/p) for p in inputs};start=time.monotonic();rows=[]
for cmd in [['pnpm','exec','tsx','harness/hero-remaster/build.mts','--out='+str(out/'build')],['pnpm','exec','tsx','harness/hero-remaster/replay.mts','--build='+str(out/'build'),'--out='+str(out/'ship-gate.json'),'--recording=harness/inputs/b1-first-ride/bot-3.json']]:
 t=time.monotonic();r=subprocess.run(cmd,cwd=root,check=True,stdout=subprocess.PIPE,stderr=subprocess.STDOUT,text=True,timeout=180);rows.append({'command':cmd,'exitCode':r.returncode,'wallSeconds':time.monotonic()-t});(out/'process.log').open('a').write(r.stdout)
assert pins=={p:sha(root/p) for p in inputs};review=json.loads((out/'build/hero-review.json').read_text());assert not review['mapping'] and not review['newRiderAdapter'];g=json.loads((out/'ship-gate.json').read_text());assert len(g['runs'])==2 and not g['errors'];assert len({r['finishTimeFloat64LE'] for r in g['runs']})==1
report={'status':'NORMAL_LEGACY_SHIP_GATE_PASS','sourceHEAD':subprocess.check_output(['git','rev-parse','HEAD'],cwd=root,text=True).strip(),'sourcePins':pins,'commands':rows,'wallSeconds':time.monotonic()-start,'lease':'lockf -k -n -t 0 /Users/raynos/projects/localai/.model.lock','modelReplacements':0,'finishFloat64LE':g['runs'][0]['finishTimeFloat64LE'],'runs':g['runs'],'errors':g['errors'],'limits':['Normal legacy player gate only; new rider is not promoted or qualified.','Headless automated restart latency is not physical phone or stranger evidence.']}
(out/'receipt.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps(report))
