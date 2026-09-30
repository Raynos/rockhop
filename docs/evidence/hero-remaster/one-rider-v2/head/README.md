# Approved new buzz-cut bust

Status: attempt1 stopped; no accepted bust or assembly.

The installed 1024-cascade worker completed texture-latent sampling but
anonymous memory rose from the last sample to82.2GiB during the following
decode window. The guard terminated our process at342.099s. No raw mesh or
GLB was written. Relevant source hashes are unchanged; unrelated jobs were
not evicted and the canonical lock was released after worker termination.
[Actual report](attempt1/generation.json), [last log](attempt1/last-log.txt).
The10-second poll did not prevent a transient overshoot; do not claim the
first batch stayed below70GiB. This is one failed bounded bust batch.

## Specific second approach

Use the installed stage-cache hooks and release our MPS cache before decoding.
Retain sampled shape/texture latents before decode, and decoded dense geometry
before texture decode. Tighten polling to1second with a65GiB stop threshold.
Keep the1024-cascade generator: its CLI does not support512 shape generation.
Reduce only the export atlas from2048 to1024; this reduces later export work,
not the failed decode allocation. The owned import shim changes no shared
port sources and does not alter textures cosmetically. One second attempt;
a second memory failure stops this MPS bust-generation technique. Subsequent
work must use retained stages with a specific CPU-decoding alternative, or
another documented head method, rather than a third identical sample.

No anatomical cut, neck assembly, skinning or player change has occurred.

## Second outcome — this sampling approach is stopped

Attempt2 terminated at263.747s, exit-15, anonymous66.7GiB. Source hashes
unchanged; no mesh/GLB or latent checkpoint was reached. The threshold
stopped work before70GiB, but sampling still failed. [Report](attempt2/generation.json).
Two failures end fresh Pixal MPS bust sampling here; no third request queued.

Recorded alternative under ask233: inspect the preserved NEW task-2 Pixal
bust, then targeted compact-scalp retopology while preserving its facial and
neck geometry. This source is a generated comparison bust, never historical
production. Its untouched10,163,546-face dense shape and89,653-face PBR export
are retained. Porous hair, patchy beard and soft eye detail remain defects;
the source is not accepted. This is a method change, not a successful new
buzz-reference sample or a silent reset of the two failures. If neutral gray
shows unacceptable face geometry, reject before polishing textures.

[Third-round unchanged-player check](round3-player-baseline/player-baseline-round-check.json)
passes fresh silent WebKit low/high boot, clear40.083333333333336s with exact
Node state/Float64 finish bytes, crash and one-tick restart2ms render submission,
zero page errors. Current normal player only; no new rider/contact/device pass.
