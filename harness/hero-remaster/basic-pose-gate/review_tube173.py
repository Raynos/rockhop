"""Prepare matched moving evidence; sampled inspection is explicitly not a pass."""
from pathlib import Path
import hashlib,json,subprocess
from PIL import Image,ImageDraw
R=Path('/Users/raynos/projects/games/rockhop');B=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2')
E=R/'docs/evidence/hero-remaster/one-rider-v2/tube-motion173';P=B/'candidate-export172/short-motion173';before=B/'basic-pose-gate164';after=P/'capture'
full=json.loads((B/'basic-pose-gate158/fixture-v4-asymmetric-halfsteps.json').read_text());old=json.loads((before/'report.json').read_text());new=json.loads((after/'report.json').read_text());manifest=json.loads((E/'manifest.json').read_text())
assert old['fixtureSHA256']==manifest['fixtureSourceSHA256'] and old['sourceSHA256']=='2100384b8f2183e98e6e0c78d8b717718b1cc57dd8298e76fab53c1d491c77e9'
indices=[i for family in ['overhead.L','sit'] for i,f in enumerate(full['frames'])if f['family']==family]
assert len(indices)==386 and len(new['frames'])==386
for row,i in enumerate(indices):
 assert old['frames'][i]['family']==new['frames'][row]['family'] and old['frames'][i]['frame']==new['frames'][row]['frame']
 assert old['frames'][i]['jointMatrices']==new['frames'][row]['jointMatrices']
# Before movie uses the same original fixture, cameras and rendering layout.
filter='[0:v]split=2[a][b];[a]trim=start_frame=2702:end_frame=2895,setpts=PTS-STARTPTS[arm];[b]trim=start_frame=1930:end_frame=2123,setpts=PTS-STARTPTS[sit];[arm][sit]concat=n=2:v=1:a=0[v]'
base=P/'baseline-matched.mp4';assert not base.exists()
subprocess.run(['ffmpeg','-v','error','-i',str(before/'basic-poses.mp4'),'-filter_complex',filter,'-map','[v]','-c:v','libx264','-threads','2','-crf','19','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(base)],check=True)
movie=P/'matched-side-gray.mp4'
filter='[0:v]crop=480:480:480:480[a];[1:v]crop=480:480:480:480[b];[a][b]hstack=inputs=2[v]'
subprocess.run(['ffmpeg','-v','error','-i',str(base),'-i',str(after/'basic-poses.mp4'),'-filter_complex',filter,'-map','[v]','-c:v','libx264','-threads','2','-crf','23','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(movie)],check=True)
windows=[('overhead-start',range(0,13)),('overhead-peak',range(90,103)),('overhead-return',range(180,193)),('sit-peak',range(283,296))]
for name,frames in windows:
 frames=list(frames);board=Image.new('RGB',(960,240*len(frames)),(35,37,41));draw=ImageDraw.Draw(board)
 for row,frame in enumerate(frames):
  for col,(directory,idx)in enumerate([(before,indices[frame]),(after,frame)]):
   with Image.open(directory/'frames'/f'{idx:04d}.png')as im:
    # Actual side-gray film frames; crop focuses on head/chest/shoulder/arm.
    tile=im.crop((590,535,850,825)).resize((430,220));board.paste(tile,(col*480+25,row*240+20))
   draw.text((col*480+8,row*240+4),f'{"BEFORE V5"if col==0 else "AFTER TUBE06"} {new["frames"][frame]["family"]} f{new["frames"][frame]["frame"]}',fill='white')
 board.save(E/f'{name}-ordered.jpg',quality=90)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
(E/'matched-evidence.json').write_text(json.dumps({'status':'MATCHED_MOVING_EVIDENCE_NOT_ACCEPTANCE','beforeSourceSHA256':old['sourceSHA256'],'afterSourceSHA256':new['sourceSHA256'],'beforeMovie':str(before/'basic-poses.mp4'),'beforeMovieSHA256':sha(before/'basic-poses.mp4'),'afterMovie':str(after/'basic-poses.mp4'),'afterMovieSHA256':sha(after/'basic-poses.mp4'),'matchedMovie':str(movie),'matchedMovieSHA256':sha(movie),'movieBytes':movie.stat().st_size,'frames':386,'fps':48,'worldJointMatricesExactForAll386':True,'orderedDiagnosticWindows':[{ 'name':n,'frames':list(f)}for n,f in windows],'limits':['Moving evidence is authored stress, not recorded gameplay.','Ordered neighborhoods are inspection aids; no all-frame subjective acceptance or full5404gate.','Gray side crop is limited detail; full six-view source films retained.','No face/body score, Garage/contact/mobile or production-ready claim.']},indent=2)+'\n')
print(json.dumps({'matchedMovie':str(movie),'bytes':movie.stat().st_size,'worldMatrixMatchedFrames':386}))
