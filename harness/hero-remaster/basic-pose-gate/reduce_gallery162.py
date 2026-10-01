"""Meet hosting input limit; retain every old comparison and full-quality masters."""
from pathlib import Path
import json,hashlib,subprocess,shutil
repo=Path('/Users/raynos/projects/games/rockhop');site=repo/'harness/out/hero-remaster/rider-review-site'
out=repo/'docs/evidence/hero-remaster/one-rider-v2/gallery162';media=site/'dist/media'
original=json.loads((out/'site-media.json').read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
private=Path('/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/gallery162-before-reduction');assert not private.exists();private.mkdir(parents=True)
rows=[]
for row in original['rows']:
 if not row['movie'].startswith('physical157-'):continue
 p=media/row['movie'];assert sha(p)==row['movieSHA256'];shutil.copy2(p,private/p.name)
 temp=media/(p.stem+'-reduced.mp4')
 command=['ffmpeg','-v','error','-i',str(p),'-vf','scale=960:-2','-c:v','libx264','-threads','2','-filter_threads','2','-b:v','150k','-maxrate','170k','-bufsize','300k','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(temp)]
 subprocess.run(command,check=True)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,nb_frames,r_frame_rate:format=duration','-of','json',str(temp)],text=True))
 assert int(probe['streams'][0]['nb_frames'])==480 and float(probe['format']['duration'])==40
 assert temp.stat().st_size<1000000
 temp.replace(p)
 rows.append({'movie':p.name,'beforeSHA256':row['movieSHA256'],'retainedFullerReview':str(private/p.name),'afterSHA256':sha(p),'bytes':p.stat().st_size,'ffmpeg':command,'ffprobe':probe,'limits':'Low-bandwidth phone comparison, reduced spatial detail. Original source and fuller encode retained; not appearance-grade evidence.'})
recipe=repo/'assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind11/sitting-multiangle01/review.html'
html=recipe.read_text().replace('Actual riding A/B · side','Low-bandwidth riding A/B · side').replace('Actual riding A/B · rear-three-quarter','Low-bandwidth riding A/B · rear-three-quarter')
html=html.replace('The last two are\nmatched actual physics-driven riding comparisons, including leaning and landing.','The last two are\nmatched actual physics-driven riding comparisons, including leaning and landing.\nThose phone copies have reduced detail to meet the hosting size limit; full-quality\nrecordings remain in the repository evidence and are used for appearance review.')
recipe.write_text(html);(site/'dist/index.html').write_text(html)
assert all(sha(media/p)==h for p,h in original['oldMediaHashes'].items())
(out/'hosting-size-recovery.json').write_text(json.dumps({'failedArchiveBytes':282771635,'limitBytes':256*1024**2,'mechanism':'Reduce only two new gameplay phone encodes; preserve all23old comparisons, source movies and four new pose videos exact.','rows':rows,'oldMediaPreservedExact':True},indent=2)+'\n')
print(json.dumps({'reducedGameplayBytes':sum(r['bytes']for r in rows)}))
