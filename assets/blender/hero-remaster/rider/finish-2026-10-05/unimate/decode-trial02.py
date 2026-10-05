"""Decode frozen same51 UniMate raw/GT features and measure bounded control.

Run only under the existing nonblocking lease and run_bounded96 controller.
No original native geometry/rest or runtime adapters are changed.
"""
import argparse
import hashlib
import json
import os
import subprocess
from pathlib import Path
import numpy as np

p = argparse.ArgumentParser(description=__doc__)
p.add_argument('--out', required=True)
p.add_argument('--evidence', required=True)
a = p.parse_args()
assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID')
out, evidence = Path(a.out).resolve(), Path(a.evidence).resolve()
assert not out.exists() and not evidence.exists()
out.mkdir(parents=True); evidence.mkdir(parents=True)
sha = lambda p: hashlib.sha256(Path(p).read_bytes()).hexdigest()
base = Path(__file__).resolve().parent
receipt = json.loads((Path.cwd()/'docs/evidence/hero-remaster/finish-2026-10-05/unimate/trial02/result.json').read_text())
local = Path('/Users/raynos/projects/localai')
python = local/'runtime/unimate/.venv/bin/python'
cond = base/'data/trial02/preprocessed/cond.npy'
rows = []
for row in receipt['outputs']:
    source = Path(row['path'])
    assert sha(source) == row['sha256']
    label = 'gt' if '-gt_' in source.name else 'raw'
    command = [str(python), str(local/'bin/unimate/decode_motion.py'), str(source), str(cond), str(out/(label+'.npz'))]
    result = subprocess.run(command, capture_output=True, text=True, timeout=60)
    (evidence/(label+'.txt')).write_text(result.stdout+result.stderr)
    assert result.returncode == 0
    rows.append({'label':label,'command':command,'exitCode':result.returncode,'sourceSHA256':sha(source),'decodedSHA256':sha(out/(label+'.npz'))})
command = [str(python), str(local/'bin/unimate/prepare_candidate.py'),str(out/'raw.npz'),str(out/'gt.npz'),str(out/'bounded.npz'),'--cap-degrees','3.5']
result = subprocess.run(command,capture_output=True,text=True,timeout=60)
(evidence/'bounded.txt').write_text(result.stdout+result.stderr)
assert result.returncode == 0
control = json.loads((out/'bounded.json').read_text())
raw, gt, bounded = [dict(np.load(out/(x+'.npz'))) for x in ['raw','gt','bounded']]
names=raw['names'].tolist(); assert len(names)==51 and names==gt['names'].tolist()==bounded['names'].tolist()
for data in [raw,gt,bounded]:
    assert data['rotations'].shape==(60,51,4)
    assert all(np.isfinite(data[k]).all() for k in ['rotations','positions','global_positions'])
protected=[i for i,n in enumerate(names) if n not in ['neck','head']]
contacts=[names.index(n) for n in ['hand.L','hand.R','foot.L','foot.R']]
assert np.array_equal(bounded['rotations'][:,protected],gt['rotations'][:,protected])
assert np.array_equal(bounded['positions'],gt['positions'])
assert np.array_equal(bounded['global_positions'][:,contacts],gt['global_positions'][:,contacts])
head_angles={}
for name in ['neck','head']:
    j=names.index(name)
    dot=np.abs((bounded['rotations'][:,j]*gt['rotations'][:,j]).sum(-1))
    head_angles[name]=float(np.degrees(2*np.arccos(np.clip(dot,0,1))).max())
    assert head_angles[name]<=3.50001
report={'accepted':False,'status':'DECODED_CONTROL_UNACCEPTED_NATIVE_RETARGET_PENDING','records':rows,'condSHA256':sha(cond),'recipeSHA256':sha(__file__),'control':control,'independentHeadMaxDegrees':head_angles,'protectedLocalQuatAndPositionsExact':True,'decodedContactsExactToGT':True,'candidateSHA256':sha(out/'bounded.npz'),'decodedGTFirstLastQuatError':float(np.abs(gt['rotations'][-1]-gt['rotations'][0]).max()),'decodedGTFirstLastPositionError':float(np.abs(gt['positions'][-1]-gt['positions'][0]).max()),'timing':'60 decoded features cover original source rows0..59 at30Hz; source row60 exact end is outside T-1. Adapter restores last GT row, not exact native closed endpoint.','limits':['Canonical decoded contacts only; source native support may already move.','Exact native endpoint/rest roundtrip, correct rotational coordinate retarget, native skin/contact and parent played review are required.','Raw neural features remain rejected as player motion.']}
(evidence/'measurement.json').write_text(json.dumps(report,indent=2)+'\n')
print(json.dumps(report),flush=True)
