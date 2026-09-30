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
