# Keep gameplay fingers above the iOS system edge

Ask331 shares [Disable Siri Gesture Web Game](https://chatgpt.com/share/6ac6d653-c548-83e8-b9ad-3bbe584da3ab).
Apple documents double-tapping the bottom edge for Type to Siri:
https://support.apple.com/en-us/105020 . WebKit documents CSS safe-area insets:
https://webkit.org/blog/7929/designing-websites-for-iphone-x/ .

The former key caps were about 6 CSS pixels above the bottom safe area while
input quarter-columns still extended to the physical bottom. The touch layer
now ends at safe-area-inset-bottom + 20 CSS pixels. Its keys retain the 6 pixel
internal padding, putting them about 26 pixels above the safe area. HUD hints
move with the strip; its noninteractive background still fills the bottom.

The existing coordinate bounds reject a captured finger that slides into
the reserved strip. It must lift before engaging a zone again. Normal
quarter-column controls and top pause/restart positions remain intact.

## Validation

- `pnpm exec tsx harness/e2e/touch-edge.mts`:24/24 cases pass in headless
  Chromium and WebKit:667×375, 844×390, 932×430, 390×844; injected bottom
  insets 0/21/34 pixels. [Raw input/layout results](boundary.json).
- Real DOM hit testing checks all four drawn keys and the reserved strip.
  Pointer events check per-key actions, simultaneous GAS+LEAN, cancellation,
  captured drag into the edge and no re-engagement until lift.
- Typecheck, 18 touch/orientation unit tests, changed-file lint and build pass.
- Default `harness:e2e --only=run --jobs=1` stops before gameplay:
  29/36 checks pass, 7 fail on menu text/tile floors and obsolete map selector.
  [Full log](game-run.txt). These are outside the changed gameplay layer.
- `harness:e2e --only=run --run-entry=hook --jobs=1`: 64/64 checks pass
  across 844×390 and 932×430 landscape contexts through the real App play
  entry. Actual GAS/LEAN/BRAKE finger streams, movement, release, settled
  controls, pause/resume and restart pass. [Log](game-touch.txt).

## Limits

No browser code disables iOS system gestures. This is a layout/input
mitigation, not a measured Siri suppression claim. Emulated safe-area values
are deliberate injected CSS fixtures; they do not measure a physical iPhone.
HR-26 retains rapid-tap/hold review with Type to Siri enabled, in landscape
Safari and a Home Screen launch. No push or deployment is requested here.
