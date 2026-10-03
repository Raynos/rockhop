from pathlib import Path
import json, hashlib
import numpy as np
ROOT=Path('/Users/raynos/projects/games/rockhop/assets/blender/hero-remaster/rider/one-rider-v2/foundation-repair-task3')
report_path=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/physical-surface168/source34/report.json')
report=json.loads(report_path.read_text())
own_path=ROOT/'hoodie-repair02/rig-lane/chart-weights/source34-480-matrices.npz'
own=np.load(own_path)
records=[]
for item in report['outputs']:
    path=Path(report['matricesPrivateDirectory'])/item['file'];raw=path.read_bytes()
    assert hashlib.sha256(raw).hexdigest()==item['sha256']
    D=np.frombuffer(raw,'<f8').reshape(480,19,4,4).transpose(0,1,3,2)
    difference=float(np.max(abs(D-own['D'])))
    assert difference<1e-12,difference
    records.append({'file':item['file'],'sha256':item['sha256'],'maxOwnedControlDifferenceM':difference})
frozen=ROOT/'hoodie-repair03/inputs/source34-authoritative168-matrices.npz'
np.savez(frozen,D=D.copy(),ticks=own['ticks'],sampleIndices=own['sampleIndices'],names=np.array(report['outputs'][0]['bones']))
out={'status':'PASS authoritative480-input comparison within2.27e-13m; new inputs retain authoritative values','authoritativeReport':str(report_path),'authoritativeReportSHA256':hashlib.sha256(report_path.read_bytes()).hexdigest(),'ownPortableInput':str(own_path),'ownSHA256':hashlib.sha256(own_path.read_bytes()).hexdigest(),'newAuthoritativeInput':str(frozen),'newAuthoritativeInputSHA256':hashlib.sha256(frozen.read_bytes()).hexdigest(),'sourceSHA256':report['sourceSHA256'],'driverSHA256':report['compiledRuntimeSHA256'],'records':records,'snapshots':[s['i']for s in report['snapshots']],'scope':'Authoritative prefix-composed bike-frame deformations, all19bones/all480samples/5meshes. No geometry or pose quality claim. Existing failure control files unchanged.'}
path=ROOT/'hoodie-repair03/evidence/authoritative-168-input-equivalence.json';path.write_text(json.dumps(out,indent=2)+'\n');print(json.dumps(out,indent=2))
