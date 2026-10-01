"""Decode the actual neural/GT outputs and measure all-joint/contact drift."""
from pathlib import Path
import json,subprocess,hashlib
import numpy as np
A=Path('/Users/raynos/projects/localai');P=A/'runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/unimate-new01';E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/unimate-new01');cond=P/'preprocessed/cond.npy';motions=P/'sample/motion_edit/motions';outputs={}
for kind,pattern in [('gt','*-gt_rep_0-0.npy'),('raw','*-000-rep_0-0.npy')]:
 files=list(motions.glob(pattern));assert len(files)==1
 out=P/(kind+'-decoded.npz');subprocess.run([str(A/'runtime/unimate/.venv/bin/python'),str(A/'bin/unimate/decode_motion.py'),str(files[0]),str(cond),str(out)],check=True);outputs[kind]=np.load(out)
g,r=outputs['gt'],outputs['raw'];assert g['names'].tolist()==r['names'].tolist();assert g['global_positions'].shape==r['global_positions'].shape
names=g['names'].tolist();body=json.loads((E.parent/'body-bind04/report.json').read_text());j=body['jointDefinitions']['thigh.L'];worldThigh=np.linalg.norm(np.array(j['tail'])-j['head'])*1.015;c=next(iter(np.load(cond,allow_pickle=True).item().values()));canonThigh=np.linalg.norm(c['tpos_offsets'][names.index('shin.L')]);factor=worldThigh/canonThigh
rows=[];gp=g['global_positions'];rp=r['global_positions'];frames=len(rp)
for k,name in enumerate(names):
 delta=np.linalg.norm(rp[:,k]-gp[:,k],axis=-1)*factor;drift=np.linalg.norm(rp[:,k]-rp[0,k],axis=-1)*factor;gtDrift=np.linalg.norm(gp[:,k]-gp[0,k],axis=-1)*factor;q=np.sum(r['rotations'][:,k]*g['rotations'][:,k],axis=-1);angle=2*np.arccos(np.clip(np.abs(q),0,1))
 rows.append({'joint':name,'maxRawVsGTPositionM':float(delta.max()),'worstRawVsGTFrame':int(delta.argmax()),'rawStartToFrameMaxDriftM':float(drift.max()),'gtStartToFrameMaxDriftM':float(gtDrift.max()),'maxLocalRotationVsGTDeg':float(np.degrees(angle).max())})
report={'frames':frames,'joints':len(names),'finite':all(np.isfinite(d[k]).all() for d in outputs.values() for k in ['rotations','positions','global_positions']),'metresPerCanonicalUnitFromSameNewThigh':float(factor),'rows':rows,'footFeatureMaskIsNotDecodedContactCertificate':True,'sourceHashes':{kind:hashlib.sha256((P/(kind+'-decoded.npz')).read_bytes()).hexdigest() for kind in outputs},'limits':'Actual decoded bone transforms only; sole vertices/shape/canonical restore and played visual judgment remain separate gates'}
(E/'decoded-audit.json').write_text(json.dumps(report,indent=2)+'\n');print(json.dumps({'frames':frames,'metresPerCanonicalUnit':float(factor),'footRows':[r for r in rows if r['joint'].startswith('foot.')],'pelvis':rows[0]}))
