"""Build a byte-preserved NEW C19 neutral control and render matched CPU orbits."""
from pathlib import Path
import copy,hashlib,json,os,signal,struct,subprocess,time
R=Path('/Users/raynos/projects/games/rockhop')
S=Path('/Users/raynos/Documents/Codex/2026-10-01/task-3/deliverables/C19.glb')
M=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/clean-upper-shell01/neutral-control179')
E=R/'docs/evidence/hero-remaster/one-rider-v2/clean-upper-shell01/neutral-control179'
M.mkdir(parents=True,exist_ok=True);E.mkdir(parents=True,exist_ok=True)
assert not(E/'process.json').exists(),'Freeze controls; never overwrite a completed render'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
sourceSHA=sha(S);assert sourceSHA=='186d0f86ae62722689be3c194f7437f623799c837e7ba515358680db12a1382e'
raw=S.read_bytes();n=struct.unpack_from('<I',raw,12)[0];original=json.loads(raw[20:20+n]);j=copy.deepcopy(original);binary=raw[28+n:]
for node in j['nodes']:node.pop('skin',None)
j.pop('skins',None);j.pop('animations',None)
encoded=json.dumps(j,separators=(',',':')).encode();encoded+=b' '*((-len(encoded))%4)
out=struct.pack('<III',0x46546c67,2,28+len(encoded)+len(binary))+struct.pack('<II',len(encoded),0x4e4f534a)+encoded+struct.pack('<II',len(binary),0x004e4942)+binary
control=M/'neutral-assembly01.glb';control.write_bytes(out)
assert j['meshes']==original['meshes'] and out[-len(binary):]==binary
for key in ['accessors','bufferViews','materials','images','textures','samplers']:assert j.get(key)==original.get(key)
recipe=R/'assets/blender/hero-remaster/rider/one-rider-v2/clean-upper-shell01/drafted-raglan/render.py'
render=recipe.read_text().replace('/clean-upper-shell01/drafted-raglan','/clean-upper-shell01/neutral-control179')
privateRecipe=M/'matched-render179.py';privateRecipe.write_text(render)
attempt={'id':'parent-neutral-control179','recordedBeforeRun':True,'stage':'CPU neutral comparison render','sourceSHA256':sourceSHA,'method':'Original NEW C19 mesh/attributes/PBR/BIN exact, skins/animations removed explicitly. Exact178 camera/light/gray/material/CPU settings, only namespace changed.','status':'PREREGISTERED','noGeometryTrial':True,'recipeOriginalSHA256':sha(recipe),'renderRecipeSHA256':sha(privateRecipe)}
(E/'attempt.json').write_text(json.dumps(attempt,indent=2)+'\n')
def anonymous():
    s=subprocess.check_output(['vm_stat'],text=True);page=int(s.split('page size of ')[1].split(' bytes')[0]);return page*int(next(l for l in s.splitlines()if l.startswith('Anonymous pages:')).split(':')[1].strip().rstrip('.'))
start=time.monotonic();peak=anonymous();assert peak<70*10**9
command=['/Applications/Blender.app/Contents/MacOS/Blender','--background','--threads','2','--python',str(privateRecipe)]
status=None
with (M/'render.log').open('wb') as log:
    p=subprocess.Popen(command,cwd=R,stdout=log,stderr=subprocess.STDOUT,start_new_session=True)
    try:
        while p.poll()is None:
            peak=max(peak,anonymous())
            if peak>=70*10**9 or time.monotonic()-start>=180:
                os.killpg(p.pid,signal.SIGTERM);p.wait(timeout=20);raise RuntimeError('Stopped own CPU batch at resource bound')
            time.sleep(.25)
        status=p.returncode;assert status==0
    finally:
        (E/'process.json').write_text(json.dumps({'command':command,'exitCode':status,'seconds':time.monotonic()-start,'peakAnonymousBytes':peak,'limits':'Cycles CPU only2threads4samples; no GPU/model/Metal export. Neutral orbit not rig/pose/game acceptance.'},indent=2)+'\n')
movies=[]
for mode in ['pbr','gray']:
    movie=E/f'CONTROL-neutral-{mode}-turntable.mp4'
    subprocess.run(['ffmpeg','-v','error','-threads','2','-framerate','6','-i',str(M/'frames'/f'{mode}-%03d.png'),'-c:v','libx264','-threads','2','-pix_fmt','yuv420p','-crf','19',str(movie)],check=True)
    movies.append({'path':str(movie),'sha256':sha(movie),'bytes':movie.stat().st_size})
assert sha(S)==sourceSHA
attempt['status']='COMPLETED_FROZEN_UNRIGGED_CONTROL_NO_CHARACTER_ACCEPTANCE';(E/'attempt.json').write_text(json.dumps(attempt,indent=2)+'\n')
(E/'manifest.json').write_text(json.dumps({'source':str(S),'sourceSHA256':sourceSHA,'originalMeshesBINAccessorPBRExact':True,'control':str(control),'controlSHA256':sha(control),'renderRecipe':str(privateRecipe),'renderRecipeSHA256':sha(privateRecipe),'matchedOriginalRecipeSHA256':sha(recipe),'movies':movies,'limits':'Only skin/animation bindings removed. NEW C19 inherited construction/hips remain failed baseline, not historical production model or approved before asset.'},indent=2)+'\n')
print(json.dumps({'sourceExact':True,'movies':2,'renderSeconds':time.monotonic()-start}))
