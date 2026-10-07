from pathlib import Path
import json,subprocess,sys
root=Path('harness/out/rider-finish/agent2-audit-media-serial02');root.mkdir(exist_ok=False,parents=True)
movies=json.load(open('docs/evidence/hero-remaster/audit-2026-10-07-agent2/media-inputs.json'))['movies']
records=[]
for i,row in enumerate(movies[5:],5):
 cmd=['node','docs/evidence/hero-remaster/audit-2026-10-07-agent2/play-film-sampled.mjs',str(root/str(i)),row['path']]
 r=subprocess.run(cmd,capture_output=True,text=True)
 record={'index':i,'source':row,'command':cmd,'exitCode':r.returncode,'stderr':r.stderr,'stdout':r.stdout}
 records.append(record);(root/'execution.json').write_text(json.dumps(records,indent=2)+'\n')
 print('PLAYBACK',i,'exit',r.returncode,flush=True)
 if r.returncode:sys.exit(r.returncode)
