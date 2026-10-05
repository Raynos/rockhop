"""One bounded SAME51 idle edit using the installed pinned UniMate.

Invoke only under canonical lockf -k -n -t 0 plus the existing run_bounded96 guard.
This does not promote its canonical rebind, install packages, or change sources.
"""
import argparse, hashlib, json, os, shutil, struct, subprocess, time
from pathlib import Path
import numpy as np

p=argparse.ArgumentParser(description=__doc__)
p.add_argument('--input',required=True);p.add_argument('--input-sha256',required=True)
p.add_argument('--contract',required=True);p.add_argument('--out',required=True)
p.add_argument('--evidence',required=True)
a=p.parse_args();source=Path(a.input).resolve();contract_path=Path(a.contract).resolve()
out,evidence=Path(a.out).resolve(),Path(a.evidence).resolve()
assert not out.exists() and not evidence.exists(), 'Fresh trial directories required'
assert os.environ.get('ROCKHOP_GENERATION_CONTROLLER_PID'), 'Use the existing bounded controller under the canonical lease'
sha=lambda x:hashlib.sha256(Path(x).read_bytes()).hexdigest()
assert sha(source)==a.input_sha256
contract=json.loads(contract_path.read_text());expected=contract['boneNames'];assert len(expected)==51
raw=source.read_bytes();size,kind=struct.unpack_from('<II',raw,12);assert kind==0x4e4f534a
gltf=json.loads(raw[20:20+size]);assert len(gltf.get('skins',[]))==1
joints=gltf['skins'][0]['joints'];names=[gltf['nodes'][i]['name'] for i in joints]
assert len(joints)==51 and set(names)==set(expected) and len(set(names))==51
assert len(gltf.get('animations',[]))==1 and gltf['skins'][0].get('inverseBindMatrices') is not None
parent={child:i for i,n in enumerate(gltf['nodes']) for child in n.get('children',[])}
for row in contract['hierarchy']:
 i=joints[names.index(row['name'])];j=parent.get(i)
 while j is not None and j not in joints:j=parent.get(j)
 assert (gltf['nodes'][j]['name'] if j is not None else None)==row['parent']
local=Path('/Users/raynos/projects/localai');runtime=local/'runtime/unimate'
revision=subprocess.check_output(['git','-C',str(runtime/'code'),'rev-parse','HEAD'],text=True).strip()
assert revision=='5d6aabedd947297b5ba6706d8e9113e68c0c3e4f', 'Changed backend requires review'
weights=local.parent/'weights/manual/Linzhan/UniMate/unimate_uniml3d_f60_v2'
config_path=weights/'config.json';config=json.loads(config_path.read_text())
assert len(joints)<=config['dataset']['max_joints']
out.mkdir(parents=True);evidence.mkdir(parents=True)
input_path=out/'input/RiderFinishIdle.glb';input_path.parent.mkdir();input_path.write_bytes(raw)
assert sha(input_path)==sha(source)
env=dict(os.environ,HF_HUB_OFFLINE='1',TRANSFORMERS_OFFLINE='1',TOKENIZERS_PARALLELISM='false',UNIMATE_ODE_STEPS='50',OMP_NUM_THREADS='2',OPENBLAS_NUM_THREADS='2')
for key,sub in [('BLENDER_USER_CONFIG','config'),('BLENDER_USER_SCRIPTS','scripts'),('BLENDER_USER_EXTENSIONS','extensions'),('TMPDIR','tmp')]:
 directory=out/'environment'/sub;directory.mkdir(parents=True);env[key]=str(directory)
records=[];started=time.monotonic()
def run(label,command,timeout):
 t=time.monotonic()
 with (evidence/(label+'.txt')).open('x') as f:
  result=subprocess.run(command,cwd=runtime/'code',env=env,stdout=f,stderr=subprocess.STDOUT,timeout=timeout)
 records.append({'label':label,'command':command,'exitCode':result.returncode,'wallSeconds':time.monotonic()-t,'logSHA256':sha(evidence/(label+'.txt'))})
 (evidence/'process.json').write_text(json.dumps({'records':records,'wallSeconds':time.monotonic()-started},indent=2)+'\n')
 assert result.returncode==0, label
pre=out/'preprocessed'
run('preprocess',['/Applications/Blender.app/Contents/MacOS/Blender','-b','--factory-startup','--threads','2','--python-exit-code','1','-P',str(Path(__file__).resolve().with_name('blender-preprocess-idle.py')),'--','--char_path',str(input_path),'--output_dir',str(pre),'--face_r','thigh.R','--face_l','thigh.L','--formats','glb','--keep_intermediate'],180)
conds=np.load(pre/'cond.npy',allow_pickle=True).item();assert len(conds)==1
cond=next(iter(conds.values()));cn=cond['joint_names'].tolist() if isinstance(cond['joint_names'],np.ndarray) else list(cond['joint_names'])
assert len(cn)==51 and set(cn)==set(expected)
parents=np.asarray(cond['parents']);depths=[]
for i in range(len(cn)):
 seen=set();j=i;depth=0
 while parents[j]>=0:
  assert j not in seen;seen.add(j);j=int(parents[j]);depth+=1
 depths.append(depth)
assert max(depths)<=config['dataset']['max_depth']
for row in contract['hierarchy']:
 i=cn.index(row['name']);assert (cn[int(parents[i])] if parents[i]>=0 else None)==row['parent']
clips=list((pre/'motions').glob('*.npz'));assert len(clips)==1
clip=np.load(clips[0]);raw_frames=len(clip['global_positions'])
# Dataset motion_utils.extract_unimate_feat consumes T-1 position frames.
# Do not repeat the historical58raw/57decoded mismatch.
admission={'inputSHA256':sha(source),'contractSHA256':sha(contract_path),'backendRevision':revision,'configSHA256':sha(config_path),'maxJoints':config['dataset']['max_joints'],'maxDepth':config['dataset']['max_depth'],'sourceJoints':len(cn),'observedDepth':max(depths),'preprocessedRawFrames':raw_frames,'requiredRawFrames':61,'featureFrameRule':'T-1','boneNames':cn,'scaleFactor':float(cond['scale_factor']),'clipShapes':{k:list(clip[k].shape) for k in clip.files},'canonicalAssetPolicy':'Model-only review rebind; never replaces original51 native/engine rest or geometry.'}
(evidence/'admission.json').write_text(json.dumps(admission,indent=2)+'\n')
assert raw_frames>=61, 'Insufficient raw frames; freeze failed input before adding explicit endpoint hold'
assert all(np.isfinite(clip[k]).all() for k in ['global_positions','local_rotations','root_facing_quat'])
experiment=out/'experiment';experiment.mkdir();config['dataset']['dataset_list']=['objaverse'];config['objaverse']['path']=str(pre);config['sampling']['device']='mps'
for option in ['use_addition_aug','use_removal_aug','use_pooling_aug','use_perturbation_aug']:config['dataset'][option]=False
(experiment/'config.json').write_text(json.dumps(config,indent=2)+'\n')
for name in ['dataset_stats.npy','checkpoints']:(experiment/name).symlink_to(weights/name)
prompt='A person stands calmly and looks gently slightly left then slightly right with relaxed natural neck and head motion. The torso, hands and planted feet stay exactly as the reference. Small movements, no walking or arm gestures.'
cases=out/'cases.json';cases.write_text(json.dumps({clips[0].stem:prompt},indent=2)+'\n')
kept=[n for n in cn if n not in ['neck','head']]
settings={'prompt':prompt,'seed':42,'device':'mps','steps':50,'cfgScale':3,'batch':1,'jointFeatureMask':kept,'purpose':'Optional small idle detail, not generic gait or supported bike animation','limits':['Decoded parent motion can move feature-masked contacts; decoded protection and original-native retarget/readback are required.','No source/canonical rig or normal player asset promotion.']}
(evidence/'settings.json').write_text(json.dumps(settings,indent=2)+'\n')
python=str(runtime/'.venv/bin/python');sample=out/'sample'
run('inference',[python,str(local/'bin/unimate/inference_entry.py'),'--exp-dir',str(experiment),'--output-dir',str(sample),'--test-cases-json',str(cases),'--seed','42','--batch-size','1','--num-repetitions','1','--cfg-scale','3.0','--only-save-motion','--motion-edit','--keep-joints',','.join(kept),'--gt-start-frame','0'],420)
files=sorted(sample.rglob('*.npy'));assert files
outputs=[]
for f in files:
 arr=np.load(f);assert np.isfinite(arr).all();outputs.append({'path':str(f),'sha256':sha(f),'shape':list(arr.shape)})
(evidence/'result.json').write_text(json.dumps({'status':'RAW_NEURAL_MOTION_ONLY_UNACCEPTED','outputs':outputs,'inputUnchanged':sha(source)==a.input_sha256,'recipeSHA256':sha(__file__),'limits':['Official decoded motion/GT comparison, native retarget, support/head/cloth clearance and parent played judgment remain required.','No generated feature is admitted as gameplay motion.']},indent=2)+'\n')
print(json.dumps({'rawOutputs':outputs,'wallSeconds':time.monotonic()-started}),flush=True)
