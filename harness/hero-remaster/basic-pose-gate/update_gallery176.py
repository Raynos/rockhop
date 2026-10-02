"""Append the actual rejected matched film; preserve every earlier media byte."""
from pathlib import Path
import hashlib,json,shutil
R=Path('/Users/raynos/projects/games/rockhop');S=R/'harness/out/hero-remaster/rider-review-site'
H=R/'assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind11/sitting-multiangle01/review.html'
E=R/'docs/evidence/hero-remaster/one-rider-v2/gallery176';E.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original=H.read_text();assert original==(S/'dist/index.html').read_text()
assert original.count('<video ')==29 and 'sleeve-rebuild173'not in original
old={str(p.relative_to(S/'dist')):sha(p)for p in(S/'dist/media').rglob('*')if p.is_file()}
assert len(old)==81
m=json.loads((R/'docs/evidence/hero-remaster/one-rider-v2/tube-motion173/matched-evidence.json').read_text())
source=Path(m['matchedMovie']);assert sha(source)==m['matchedMovieSHA256'] and source.stat().st_size==144949
dest=S/'dist/media/sleeve-rebuild173-matched-side-gray.mp4';assert not dest.exists();shutil.copyfile(source,dest)
section='''<section id="sleeve-rebuild173"><h2>Sleeve rebuild motion test · still rejected</h2>
<p>Left: the V5 clothing control. Right: the first skinned sleeve rebuild.
Both use the same joint transforms, camera and light. The first half raises
and lowers the left arm; the second sits and returns to standing. This gray
view exposes the shape: the rebuilt underarm stays too flat and rigid, and the
shoulder still looks like an insert. It has not passed our basic pose gate.</p>
<article class="card"><div class="label"><h3>Matched overhead arm and sitting · before / after</h3>
<p>386 actual Three.js frames · 48fps · 8 seconds · unaccepted experiment</p></div>
<video controls muted playsinline loop preload="metadata" style="aspect-ratio:2/1" src="media/sleeve-rebuild173-matched-side-gray.mp4"></video>
<div class="links"><a href="media/sleeve-rebuild173-matched-side-gray.mp4">Open matched video full size</a></div></article>
<p>The independent team is rebuilding the resting sleeve and shoulder.
This is an authored stress test, not a supported sitting animation or Garage
capture. The liked head is preserved. No candidate has been accepted into the game.</p></section>
'''
anchor='<section id="structural-gate">';assert original.count(anchor)==1
html=original.replace(anchor,section+anchor,1)
H.write_text(html);(S/'dist/index.html').write_text(html)
assert html.count('<video ')==30 and all(sha(S/'dist'/p)==h for p,h in old.items())
(E/'source-manifest.json').write_text(json.dumps({'oldMediaHashes':old,'mediaFilesPreserved':81,'oldVideosPreserved':29,'videos':30,'htmlSHA256':sha(H),'addedMedia':{'relativePath':str(dest.relative_to(S/'dist')),'source':str(source),'SHA256':sha(dest),'bytes':dest.stat().st_size},'sourceEvidence':m['afterSourceSHA256'],'beforeSourceEvidence':m['beforeSourceSHA256'],'frames':386,'fps':48,'worldJointMatricesExact':m['worldJointMatricesExactForAll386'],'status':'REJECTED_EXPERIMENT_REVIEW_ONLY','limits':'Existing173encoded clip copied exactly; no new render, model repair or appearance acceptance.'},indent=2)+'\n')
print(json.dumps({'videos':30,'oldMediaPreserved':81,'addedBytes':dest.stat().st_size}))
