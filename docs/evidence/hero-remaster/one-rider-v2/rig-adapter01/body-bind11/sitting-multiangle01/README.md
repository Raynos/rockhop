# Current rider standing-to-sitting clips and phone gallery

Use **fixture02**, the actual unmodified current body11 GLB/action
`stand_to_sit_probe`. Blender5.2.1 LTS CPU,2 threads,96.77s, no GPU. SourceSHA
b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754.
Three fixed cameras front/side/rear-three-quarter,24 actual samples per view,
12fps/2s MP4. Half-speed presents the same samples more slowly; no new poses.

Parent reviewed all72 decoded frames. Source head/hood join retained; hip,
upper-leg, sleeves and face quality still open. This delivers diagnostic motion,
not checkpoint2 acceptance or a game-ready rider. Actual in-game clips on the
gallery remain separate from the authored bench motion.

Initial fixture was misplaced because imported motion has a translated root.
It is retained as unaccepted setup evidence. fixture02 places the bench using
the actual pelvis/root origin. Both sets of original lossless frames and all
decoded frames are privately archived with SHA receipts. The first24-frame
boards were too short; export_review_site.py reconstructs complete six-row
boards from all24 decoded frames, plus nine-sample boards for the gallery.

Private phone review: https://rockhop-rider-review.raynos.chatgpt.site
Site deployment succeeded; site-deployment.json retains IDs/sourceSHA without
credentials. Source-only review checkout lives under ignored harness/out,
on its own main, pushed solely to Sites. Game repository remains main with
normal player assets unchanged. No game deploy/push was requested or performed.

Silent headless WebKit390px/1200px: all5 embedded videos advance, all4 images
decode, no overflow/page errors. Physical iPhone playback is not yet verified.
The Sites bundle lacks the documented site-workflow helper; the supplied
package-site.sh validates/packages static output, while push_review_site.py
pushes exact main HEAD and verifies remote SHA. Credential is stdin/memory
only, never arguments/config/files. Owner-private audience remains unchanged.

Ship gate111: coldboot/track clear/crash/restart both logical FULL tiers,
byte-identical40.083333333333336s/hash368f1ca5bd9e830a;103 crash ticks,
restart2ms both;0 errors. Shared lock13.12s/38.529GB anonymous. The first guard
referenced an unhashed model path and stopped before work; corrected actual
build model path verifies body11 SHA. No altered input/physics or quality pass.
