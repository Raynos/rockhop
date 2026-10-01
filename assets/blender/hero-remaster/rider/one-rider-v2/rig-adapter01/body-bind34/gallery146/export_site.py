"""Publish latest mapped fresh rig without replacing earlier21comparison films."""
from pathlib import Path
import hashlib,json,subprocess,shutil
from PIL import Image
repo=Path('/Users/raynos/projects/games/rockhop');base=repo/'docs/evidence/hero-remaster/one-rider-v2/rig-adapter01';site=repo/'harness/out/hero-remaster/rider-review-site';media=site/'dist/media';recipe=repo/'assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind11/sitting-multiangle01/review.html';out=base/'body-bind34/gallery146';out.mkdir(exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
html=recipe.read_text();assert html.count('<video ')==21 and 'id="fresh-rig34"' not in html
original={str(p.relative_to(media)):sha(p) for p in media.rglob('*') if p.is_file()};rows=[];cards=[]
for angle,title in [('side','Side'),('rear-three-quarter','Rear three-quarter')]:
 folder=base/'body-bind34/played/candidate'/angle/'textured';report=json.loads((folder/'report.json').read_text());assert report['sourceSHA256']=='adbac6f2949cec0f32a8e0cfa4cfabd02cce61e58dab4022209e23a605f31df7' and len(report['samples'])==480 and not report.get('failure') and not report['errors']
 stem=f'fresh34-{angle}';video=media/f'{stem}.mp4';assert not video.exists();command=['ffmpeg','-v','error','-i',str(folder/'played.mp4'),'-vf','scale=960:540','-c:v','libx264','-threads','2','-crf','29','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(video)];subprocess.run(command,check=True)
 archive=json.loads((folder/'frames-archive.json').read_text());Image.open(Path(archive['privateDecodedFrames'])/'0305.png').convert('RGB').save(media/f'{stem}.jpg',quality=93)
 board=f'{stem}-comparison.jpg';shutil.copy2(base/'body-bind34/played/matched-boards'/f'{angle}-textured-key304.jpg',media/board)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=codec_name,width,height,r_frame_rate,nb_frames:format=duration','-of','json',str(video)],text=True));assert int(probe['streams'][0]['nb_frames'])==480 and float(probe['format']['duration'])==40
 baseline=f'sleeve25-baseline-{angle}-review.mp4';assert (media/baseline).exists()
 cards.append(f'<article class="card"><div class="label"><h3>{title} · NEW C19 skeleton / body34</h3><p>1 October · tested in the game · unaccepted trial</p></div><video controls muted playsinline loop preload="metadata" poster="media/{stem}.jpg" src="media/{stem}.mp4"></video><div class="links"><a href="media/{stem}.mp4">Open new 40-second video</a><a href="media/{baseline}">Earlier rider, matched camera</a><a href="media/{board}">Earlier vs new frame sequence</a></div></article>')
 rows.append({'source':str(folder/'played.mp4'),'sourceSHA256':sha(folder/'played.mp4'),'modelSHA256':report['sourceSHA256'],'reviewMovie':video.name,'reviewSHA256':sha(video),'ffmpeg':command,'ffprobe':probe,'limits':'Phone copy960x540of actual1280x720movie, all480frames/40seconds preserved. No retiming or reframing. Original quality retained in source evidence.'})
section='<section id="fresh-rig34"><h2>Latest: the NEW skeleton in the game</h2><p>This is the fresh C19 rig adapted to the existing physics, leaning and hand/foot targets. The hips are fuller and less collapsed than the earlier rider. The hoodie still has severe underarm folds, and clean sitting, leg deformation and saddle support remain unfinished. This is progress, not an accepted repair.</p><section class="gameplay">'+''.join(cards)+'</section><p>The standing-to-sitting studio films below use the earlier body11 rig. They have not been replaced by a new C19 sitting animation. All earlier comparisons remain available below.</p></section>'
anchor='<p>Standing to sitting, from three angles.';assert html.count(anchor)==1
html=html.replace(anchor,section+'<h2>Earlier rig: standing-to-sitting studio test</h2>'+anchor);assert html.count('<video ')==23
recipe.write_text(html);(site/'dist/index.html').write_text(html)
assert all(sha(media/p)==h for p,h in original.items())
(out/'site-media.json').write_text(json.dumps({'previousVideosRetained':21,'addedVideos':2,'totalVideos':23,'oldMediaFilesPreservedExact':len(original),'oldMediaHashes':original,'rows':rows},indent=2)+'\n');print(json.dumps({'totalVideos':23,'addedReviewBytes':sum((media/r['reviewMovie']).stat().st_size for r in rows)}))
