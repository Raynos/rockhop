# Same-asset Garage lighting probes

Parent diagnostic review, 2026-09-30. [Moving comparison](comparison.mp4):
left current V6, centre authored emission restored without the stage lift,
right neutral fill without the lift. All three use the identical frozen
actual-game build, all eighteen model hashes, phone viewport, resolution and
camera orbit. They enter through Menu→Garage; no mesh or bone pose is injected.
Ordered moving views cover both sides, front and back.

The current lift whitens skin and weakens surface contrast. Removing it alone
darkens the hero too far. The neutral probe improves that balance but brightens
the entire workshop floor. Neither removes the authored grey/white forearm
patches. Keep production lighting unchanged while the skin/head candidates are
finished; recalibrate against their accepted materials before promotion.

The Garage's proposed warm key currently depends on the loaded biome having a
pooled lamp spot. The Coast world used here creates none: its Garage has only
the directional and hemisphere lights. This dependency needs resolution in
M3 rather than assuming the documented work lamp always illuminates the hero.

[Review](review.json) records consumed model hashes, exact light settings,
resource counters, camera/AA settings and presentation/physics samples. The
neutral probe changes existing light and environment uniforms; no light,
texture, shadow map or post pass is added. It is a diagnostic, not an accepted
production replacement or an AAA claim. The changing Garage host clock means
movie cadence does not prove idle speed or frame pacing. Sustained physical
iPhone and human art acceptance remain open. The comparison is rescaled to
one CSS pixel per pixel for each phone view; source captures used DPR2.

Replay: `review.mts --build=harness/out/hero-remaster/wrist-final-build
--out=NEW_DIRECTORY --size=874x330 --dpr=3 --frames=60
--lighting=baseline|no-lift|neutral-fill`. The retained source build is ignored;
these reports and moving comparison preserve its exact consumed assets.
