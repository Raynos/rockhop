"""Add event review controls without replacing or recompressing any media."""
from pathlib import Path
import hashlib,json
R=Path('/Users/raynos/projects/games/rockhop');S=R/'harness/out/hero-remaster/rider-review-site';H=R/'assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind11/sitting-multiangle01/review.html';E=R/'docs/evidence/hero-remaster/one-rider-v2/gallery171';E.mkdir(parents=True,exist_ok=True)
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
original=H.read_text();assert original==(S/'dist/index.html').read_text() and original.count('<video ')==29 and 'rider-review-events'not in original
media={str(p.relative_to(S/'dist')):sha(p)for p in (S/'dist/media').rglob('*')if p.is_file()}
note='''<p class="note">The riding A/B shows source34 with the C19 rig on the left and
the V5 clothing control on the right. Both still intersect the saddle in the
mid-ride pose. The sleeve and hip folds remain unacceptable. Tap a moment below
either riding video to loop it, or choose Full clip. These phone copies show broad
movement; fine surface detail is judged from the original recordings.</p>
'''
anchor='<section class="gameplay"><article class="card"><div class="label"><h3>12 basic pose families'
assert original.count(anchor)==1
html=original.replace(anchor,note+anchor,1)
style='''<style>.review-controls{display:flex;flex-wrap:wrap;gap:8px;padding:12px 16px}
.review-controls button{font:inherit;min-height:44px;padding:8px 12px;border-radius:6px;border:1px solid #716044;background:#25292c;color:#f0c374;cursor:pointer}
.review-controls button[aria-pressed="true"]{background:#e4b965;color:#171a1c}
.review-controls button:focus-visible{outline:2px solid #f0c374;outline-offset:3px}
.review-status{margin:0;padding:0 16px 16px;font-size:.875rem;color:#c6cdd1}</style>'''
assert '</head>'in html;html=html.replace('</head>',style+'</head>',1)
script='''<script id="rider-review-events">
(() => {
  const events = [
    ['Maximum forward lean', 29 / 12, 42 / 12],
    ['Saddle crossing', 174 / 12, 199 / 12],
    ['Maximum back lean', 420 / 12, 433 / 12],
    ['Landing and recovery', 440 / 12, 453 / 12]
  ];
  const videos = document.querySelectorAll('#structural-gate video');
  for (const video of videos) {
    if (!/physical157-(side|rear-three-quarter)\\.mp4$/.test(video.getAttribute('src') || '')) continue;
    const card = video.closest('.card');
    const controls = document.createElement('div');
    controls.className = 'review-controls';
    controls.setAttribute('role', 'group');
    controls.setAttribute('aria-label', 'Loop riding review moments');
    const status = document.createElement('p');
    status.className = 'review-status';
    status.setAttribute('role', 'status');
    status.textContent = 'Full clip · structural repair still in progress';
    let range = null;
    let generation = 0;
    const reset = () => {
      range = null;
      for (const button of controls.children) button.setAttribute('aria-pressed', 'false');
      status.textContent = 'Full clip · structural repair still in progress';
      delete video.dataset.reviewStart;
      delete video.dataset.reviewEnd;
      video.dataset.reviewEvent = 'Full clip';
    };
    const checkLoop = () => {
      if (range && !video.paused && video.currentTime >= range[1]) {
        video.currentTime = range[0];
        video.dataset.reviewLoops = String(Number(video.dataset.reviewLoops || 0) + 1);
      }
    };
    if ('requestVideoFrameCallback' in video) {
      const frame = () => { checkLoop(); video.requestVideoFrameCallback(frame); };
      video.requestVideoFrameCallback(frame);
    } else video.addEventListener('timeupdate', checkLoop);
    video.addEventListener('seeking', () => {
      if (range && (video.currentTime < range[0] - .05 || video.currentTime > range[1] + .35)) reset();
    });
    for (const [label, start, end] of [...events, ['Full clip', 0, null]]) {
      const button = document.createElement('button');
      button.type = 'button';
      button.textContent = label;
      button.setAttribute('aria-pressed', 'false');
      button.addEventListener('click', async () => {
        const ticket = ++generation;
        video.muted = true;
        reset();
        try {
          if (video.readyState < 1) await new Promise((resolve, reject) => {
            const timer = setTimeout(() => { cleanup(); reject(new Error('Video is still loading')); }, 10000);
            const done = () => { cleanup(); resolve(); };
            const failed = () => { cleanup(); reject(new Error('Video could not load')); };
            const cleanup = () => { clearTimeout(timer); video.removeEventListener('loadedmetadata', done); video.removeEventListener('error', failed); };
            video.addEventListener('loadedmetadata', done, {once:true});
            video.addEventListener('error', failed, {once:true});
            video.load();
          });
          if (ticket !== generation) return;
          if (end !== null) {
            range = [start, Math.min(end, video.duration)];
            video.dataset.reviewStart = String(range[0]);
            video.dataset.reviewEnd = String(range[1]);
          }
          video.dataset.reviewEvent = label;
          video.dataset.reviewLoops = '0';
          video.currentTime = start;
          button.setAttribute('aria-pressed', 'true');
          status.textContent = end === null ? 'Full clip · structural repair still in progress' : label + ' · looped original recording';
          await video.play();
        } catch (error) {
          if (ticket === generation) status.textContent = 'Tap the video play control to continue.';
        }
      });
      controls.append(button);
    }
    card.append(controls, status);
  }
})();
</script>'''
assert '</body>'in html;html=html.replace('</body>',script+'</body>',1)
H.write_text(html);(S/'dist/index.html').write_text(html)
assert html.count('<video ')==29 and all(sha(S/'dist'/p)==digest for p,digest in media.items())
(E/'source-manifest.json').write_text(json.dumps({'oldMediaHashes':media,'mediaUnchanged':True,'totalVideos':29,'htmlSHA256':sha(H),'events':[{'name':n,'framesInclusive':[a,b-1],'startSeconds':a/12,'endSeconds':b/12}for n,a,b in [('maximum-forward',29,42),('saddle-crossing',174,199),('maximum-back',420,433),('landing-recovery',440,453)]],'limits':'Review seek/loop controls over unchanged phone copies, not newly captured or improved character motion. Browser loop timing is not a continuous collision certificate.'},indent=2)+'\n')
print(json.dumps({'videos':29,'unchangedMediaFiles':len(media)}))
