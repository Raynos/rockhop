"""Run isolated NEW-rider preprocessing and actual UniMate under caller lockf -k."""
from pathlib import Path
import os,subprocess,json,time,signal,hashlib
import numpy as np
A=Path('/Users/raynos/projects/localai');U=A/'runtime/unimate';P=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/unimate-new01');E=Path('/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/unimate-new01')
start=time.monotonic();env=os.environ.copy()
for d in ['config','scripts','extensions','tmp']:(P/'environment'/d).mkdir(parents=True,exist_ok=True)
env.update(BLENDER_USER_CONFIG=str(P/'environment/config'),BLENDER_USER_SCRIPTS=str(P/'environment/scripts'),BLENDER_USER_EXTENSIONS=str(P/'environment/extensions'),TMPDIR=str(P/'environment/tmp'),OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2',HF_HOME=str(A.parent/'weights/hf'),HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',UNIMATE_ODE_STEPS='50')
def memory():
 s=subprocess.check_output(['vm_stat'],text=True);page=int(s.split('page size of ')[1].split(' bytes')[0]);return int(next(l for l in s.splitlines() if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))*page
records=[]
def run(label,command,seconds,cwd):
 assert time.monotonic()-start<1790;assert memory()<70*10**9
 log=E/(label+'-log.txt');ts=time.monotonic();peak=memory();failure=None
 with log.open('x') as f:
  child=subprocess.Popen(command,cwd=cwd,env=env,stdout=f,stderr=subprocess.STDOUT,start_new_session=True)
  while child.poll() is None:
   peak=max(peak,memory())
   if peak>=70*10**9 or time.monotonic()-ts>seconds or time.monotonic()-start>1790:
    failure='anonymousmemory70GB' if peak>=70*10**9 else 'ownjobdeadline';os.killpg(child.pid,signal.SIGTERM)
    try:child.wait(timeout=5)
    except subprocess.TimeoutExpired:os.killpg(child.pid,signal.SIGKILL);child.wait()
    break
   time.sleep(1)
 records.append({'label':label,'command':command,'exitCode':child.returncode,'wallSeconds':time.monotonic()-ts,'anonymousPeakBytes':peak,'failure':failure});(E/'process.json').write_text(json.dumps({'lock':'lockf -k /Users/raynos/projects/localai/.model.lock','limitSeconds':1800,'records':records},indent=2)+'\n');assert child.returncode==0 and failure is None
blender='/Applications/Blender.app/Contents/MacOS/Blender';pre=P/'preprocessed'
run('preprocess',[blender,'-b','--factory-startup','--threads','2','--python-exit-code','1','-P',str(A/'bin/unimate/blender_preprocess.py'),'--','--char_path',str(P/'input/RockhopWhiteRider.glb'),'--output_dir',str(pre),'--face_r','thigh.R','--face_l','thigh.L','--formats','glb','--keep_intermediate'],600,U/'code')
clips=list((pre/'motions').glob('*.npz'));assert len(clips)==1
c=np.load(clips[0]);info={k:list(c[k].shape) for k in c.files};(E/'preprocessing-shapes.json').write_text(json.dumps({'clip':str(clips[0]),'arrays':info},indent=2)+'\n')
weights=A.parent/'weights/manual/Linzhan/UniMate/unimate_uniml3d_f60_v2';exp=P/'experiment';exp.mkdir();cfg=json.loads((weights/'config.json').read_text());cfg['dataset']['dataset_list']=['objaverse'];cfg['objaverse']['path']=str(pre);cfg['sampling']['device']='mps'
for option in ['use_addition_aug','use_removal_aug','use_pooling_aug','use_perturbation_aug']:cfg['dataset'][option]=False
(exp/'config.json').write_text(json.dumps(cfg,indent=2)+'\n')
for name in ['dataset_stats.npy','checkpoints']:(exp/name).symlink_to(weights/name)
prompt='A person starts standing upright, bends slightly forward at the hips and knees, lowers onto a low bench behind them, then settles upright seated with both hands resting on the thighs. Both feet remain planted on the floor throughout. Natural smooth whole-body motion, no walking or waving.'
cases=exp/'sitting-cases.json';cases.write_text(json.dumps({clips[0].stem:prompt},indent=2)+'\n');out=P/'sample';out.mkdir();command=[str(U/'.venv/bin/python'),str(A/'bin/unimate/inference_entry.py'),'--exp-dir',str(exp),'--output-dir',str(out),'--test-cases-json',str(cases),'--seed','42','--batch-size','1','--num-repetitions','1','--cfg-scale','3.0','--only-save-motion','--motion-edit','--keep-joints','foot.L,foot.R','--gt-start-frame','0']
(E/'sampling-settings.json').write_text(json.dumps({'prompt':prompt,'device':'mps','seed':42,'ODEsteps':50,'keptFeatureJoints':['foot.L','foot.R'],'source':'body-bind04 NEW white rider','limits':'Feature masking is not decoded contact proof; no production idle or historical source substituted','upstreamRevision':'5d6aabedd947297b5ba6706d8e9113e68c0c3e4f'},indent=2)+'\n')
run('inference',command,420,U/'code')
outputs=[]
for p in sorted(out.rglob('*.npy')):
 a=np.load(p);outputs.append({'path':str(p),'shape':list(a.shape),'finite':bool(np.isfinite(a).all()),'SHA256':hashlib.sha256(p.read_bytes()).hexdigest()})
(E/'sampling-result.json').write_text(json.dumps({'outputs':outputs,'wallSeconds':time.monotonic()-start,'limits':'Inference only; real motion/contact/render comparison pending'},indent=2)+'\n');assert outputs and all(a['finite'] for a in outputs)
print('NEW_RIDER_UNIMATE_COMPLETE',json.dumps(outputs),flush=True)
