"""Fit only six new gallery copies under Sites256MiB; sources/old15 exact."""
from pathlib import Path
import hashlib,json,subprocess
repo=Path('/Users/raynos/projects/games/rockhop');site=repo/'harness/out/hero-remaster/rider-review-site';media=site/'dist/media';out=repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind22/gallery-update129';receipt=out/'site-media.json';d=json.loads(receipt.read_text());sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest();rows=[]
old={str(p.relative_to(media)):sha(p) for p in media.rglob('*') if p.is_file() and p.name not in [r.get('video',r.get('reviewMovie')) for r in d['rows']]}
for row in d['rows']:
 source=Path(row['source']);assert sha(source)==row['sourceMovieSHA256'];dest=media/row.get('video',row.get('reviewMovie'));tmp=dest.with_name(dest.stem+'-reduce.mp4');assert not tmp.exists()
 width=1280 if 'video' in row else 960
 command=['ffmpeg','-v','error','-i',str(source),'-vf',f'scale={width}:-2','-c:v','libx264','-threads','2','-crf','29','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(tmp)];subprocess.run(command,check=True)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,width,height,nb_frames:format=duration','-of','json',str(tmp)],text=True));assert int(probe['streams'][0]['nb_frames'])==(72 if 'video' in row else 480);assert float(probe['format']['duration'])==(6 if 'video' in row else 40)
 previous=sha(dest);tmp.replace(dest);row.update(copiedExact=False,reviewCopyReduced=True,ffmpeg=command,ffprobe=probe,previousReviewSHA256=previous,limits='Size-limited phone review copy; same complete ordered frames/timing. Original source and all15previous gallery movies untouched. Full-size comparison JPG retained.')
 row['videoSHA256' if 'video' in row else 'reviewMovieSHA256']=sha(dest);rows.append({'name':dest.name,'bytes':dest.stat().st_size,'sourceUnchanged':sha(source)==row['sourceMovieSHA256']})
assert all(sha(media/n)==s for n,s in old.items());d['sizeLimitRecovery']={'limitBytes':256*1024**2,'reason':'First exact-source archive exceeded Sites256MiB input limit before any version/deployment was saved. Reduce only six new review copies; no asset repair failure.','newMedia':rows,'old15AndOtherMediaUnchanged':True};receipt.write_text(json.dumps(d,indent=2)+'\n');print(json.dumps({'newReviewBytes':sum(r['bytes'] for r in rows),'staticBytes':sum(p.stat().st_size for p in (site/'dist').rglob('*') if p.is_file())}))
