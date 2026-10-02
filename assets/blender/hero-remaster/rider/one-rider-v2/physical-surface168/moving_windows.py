"""Retain consecutive matched played frames, without rendering new poses."""
from pathlib import Path
import hashlib, json, subprocess, io
from PIL import Image, ImageDraw

ROOT = Path('/Users/raynos/projects/games/rockhop')
OUT = ROOT/'docs/evidence/hero-remaster/one-rider-v2/physical-surface168'
SOURCE = ROOT/'docs/evidence/hero-remaster/one-rider-v2/garment-rebuild01/physical-v5-control157/played/matched'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
records = []
for name, start, end in [('maximum-forward',29,42), ('maximum-back',420,433), ('landing-recovery',440,453)]:
    for view in ['side','rear-three-quarter']:
        for material in ['gray','textured']:
            source = SOURCE/f'{view}-{material}-before-after.mp4'
            output = OUT/f'{name}-{view}-{material}.mp4'
            command = ['ffmpeg','-v','error','-i',str(source),'-vf',f'trim=start_frame={start}:end_frame={end},setpts=PTS-STARTPTS','-c:v','libx264','-threads','2','-filter_threads','2','-crf','18','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(output)]
            assert not output.exists()
            subprocess.run(command,check=True)
            probe = json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames','-of','json',str(output)],text=True))
            stream = probe['streams'][0]
            assert int(stream['nb_frames']) == end-start and stream['r_frame_rate']=='12/1'
            records.append({'event':name,'view':view,'material':material,'source':str(source),'sourceSHA256':sha(source),'destination':output.name,'sha256':sha(output),'framesInclusive':[start,end-1],'command':command,'probe':probe})
    # Every consecutive side-gray AB frame is included, in playback order.
    # A contact sheet supports partial moving review; it cannot accept a movie.
    movie = OUT/f'{name}-side-gray.mp4'
    board = Image.new('RGB',(1440,5*180),(22,22,22))
    draw = ImageDraw.Draw(board)
    for k in range(end-start):
        raw = subprocess.check_output(['ffmpeg','-v','error','-threads','2','-filter_threads','2','-i',str(movie),'-vf',f'select=eq(n\,{k})','-frames:v','1','-f','image2pipe','-vcodec','png','-'])
        frame = Image.open(io.BytesIO(raw)).convert('RGB').resize((480,145))
        x,y = (k%3)*480,(k//3)*180
        board.paste(frame,(x,y+25));draw.text((x+8,y+7),f'Actual frame {start+k}; source34 left / V5 right',fill='white')
    path = OUT/f'{name}-ordered-side-gray.png'
    board.save(path)
(OUT/'moving-windows.json').write_text(json.dumps({'movies':records,'scope':'13 consecutive original actual recorded frames per event, same cameras/poses and 12fps. Timing-preserving excerpts, no new rendering.','limits':'No full-film, anatomy, all-contact or device pass; ordered sheets only support partial event review.'},indent=2)+'\n')
print(json.dumps({'movies':len(records),'events':3,'framesPerMovie':13}))
