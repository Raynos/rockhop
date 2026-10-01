"""Append actual unaccepted structural movies; preserve all previous media."""
from pathlib import Path
import hashlib,json,shutil,subprocess
from PIL import Image
repo=Path('/Users/raynos/projects/games/rockhop')
site=repo/'harness/out/hero-remaster/rider-review-site';media=site/'dist/media'
recipe=repo/'assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind11/sitting-multiangle01/review.html'
out=repo/'docs/evidence/hero-remaster/one-rider-v2/gallery162';out.mkdir(parents=True,exist_ok=True)
html=recipe.read_text();assert html==(site/'dist/index.html').read_text()
assert html.count('<video ')==23 and 'id="structural-gate"' not in html
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
old={str(p.relative_to(media)):sha(p)for p in media.rglob('*')if p.is_file()}
sources=repo/'docs/evidence/hero-remaster/one-rider-v2';studio=sources/'basic-pose-gate160'
rows=[];cards=[]
def movie(stem,source,caption,filters=None,poster=None):
 dest=media/(stem+'.mp4');assert not dest.exists()
 if filters is None:shutil.copy2(source,dest);command=None
 else:
  command=['ffmpeg','-v','error','-i',str(source),'-vf',filters,'-c:v','libx264','-threads','2','-filter_threads','2','-crf','25','-pix_fmt','yuv420p','-an','-movflags','+faststart',str(dest)]
  subprocess.run(command,check=True)
 probe=json.loads(subprocess.check_output(['ffprobe','-v','error','-select_streams','v:0','-show_entries','stream=width,height,r_frame_rate,nb_frames:format=duration','-of','json',str(dest)],text=True))
 expected=1164 if source==studio/'basic-poses.mp4' else 480
 assert int(probe['streams'][0]['nb_frames'])==expected
 if poster:
  Image.open(poster).convert('RGB').save(media/(stem+'.jpg'),quality=92)
  posterAttr=' poster="media/'+stem+'.jpg"'
 else:posterAttr=''
 cards.append('<article class="card"><div class="label"><h3>'+caption+'</h3><p>1 October · unaccepted structural evidence</p></div><video controls muted playsinline loop preload="metadata"'+posterAttr+' src="media/'+stem+'.mp4"></video><div class="links"><a href="media/'+stem+'.mp4">Open video full size</a></div></article>')
 rows.append({'source':str(source),'sourceSHA256':sha(source),'movie':dest.name,'movieSHA256':sha(dest),'ffmpeg':command,'ffprobe':probe,'scope':'Source timing/allframes retained; static pixel crop or downscale only. No model/pose or cosmetic editing.'})
movie('structural160-six-view',studio/'basic-poses.mp4','12 basic pose families · front / side / back · textured + gray',poster=studio/'source-frame-0242.jpg')
for i,name in enumerate(['front','side','back']):
 movie('structural160-'+name,studio/'basic-poses.mp4',name.title()+' close view · same exported motion',filters=f'crop=480:480:{i*480}:0')
matched=sources/'garment-rebuild01/physical-v5-control157/played/matched'
for name in ['side','rear-three-quarter']:
 movie('physical157-'+name,matched/(name+'-textured-before-after.mp4'),'Actual riding A/B · '+name,filters='scale=1280:-2',poster=matched/(name+'-textured-304.jpg'))
section='''<section id="structural-gate"><h2>Latest structural tests: cloth still fails</h2>
<p>We are fixing garment construction first, then rig and weights, then deformation.
Cosmetic polish is paused. The liked head is preserved. The rider below is still
unaccepted: raised arms distort the hoodie, hips and supported sitting remain
unfinished. Apparent blue tears in sampled gameplay pixels hit opaque cloth
with wrong atlas texels; a sampled black patch hits folded geometry with an
opposing skinned normal. Those findings do not clear broader cloth failures.</p>
<p>The first four videos show the exported V5 character in an authored stress
fixture, not the Garage or a supported sitting animation. The last two are
matched actual physics-driven riding comparisons, including leaning and landing.
The new CPU gate also covers unilateral arms and intermediate frames; these
videos cover the earlier bilateral 24fps fixture. No 8/10 appearance pass.</p>
<section class="gameplay">'''+''.join(cards)+'''</section>
<p>Every earlier comparison remains below. No candidate has been promoted into
the normal game. Surface contacts, actual Garage, Blender matching and mobile
performance remain open.</p></section>'''
anchor='<section id="fresh-rig34">';assert html.count(anchor)==1
html=html.replace(anchor,section+anchor);assert html.count('<video ')==29
recipe.write_text(html);(site/'dist/index.html').write_text(html)
assert all(sha(media/p)==h for p,h in old.items())
(out/'site-media.json').write_text(json.dumps({'previousVideosRetained':23,'addedVideos':6,'totalVideos':29,'oldMediaHashes':old,'rows':rows,'siteHTMLSHA256':sha(site/'dist/index.html')},indent=2)+'\n')
print(json.dumps({'videos':29,'addedBytes':sum((media/r['movie']).stat().st_size for r in rows)}))
