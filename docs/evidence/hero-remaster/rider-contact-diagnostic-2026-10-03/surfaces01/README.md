# Exact STEP triangle-surface audit — unaccepted

This read-only audit reconstructs the17 aligned actual-Garage observations
from the same Library GLB v3 and production GLTF decoder. All61source STEP
channels include the non-bone authored root; omitting that root was caught by
the matrix assertion and its first distances were rejected. Every reconstructed
bone and mesh world matrix now matches the recorded engine values exactly.
All5raw/body11 and repaired base position, normal, index and skin arrays are
byte-identical. Morphs remain the exact captured source values.

The historical hand mask has3312native triangles per side, but native-local
index mapping differs from590left/610right actual exported faces. Only the
explicit `actualExportedTriangleSourceVertices` field is authoritative here;
each face is verified against the actual unchanged exported mesh index buffer.
The shoe regions include every complete triangle with any positive named
foot-bone weight:2682left/2667right, including all67/77literal sole faces.
They are shoe/ankle supersets, not a reviewed sole-pad classification. Targets
are44literal grip faces per side,272peg faces per side, and48upward saddle faces.
The broad hip patch includes6776complete pelvis/thigh/fold faces.

Whole finite triangle unsigned distance evaluates face/edge crossings,
vertex-to-face and edge-to-edge separation, with conservative AABB pruning.
Known parallel-one-metre and transverse-crossing controls pass. Both hands
and shoe regions have zero minimum separation at all17observations. At t=2s,
zero-distance face-pair counts are59left-hand/55right-hand and8left-shoe/4right-shoe.
Zero means touching or crossing. It cannot certify grasp, support, penetration
depth, friction, palmar or plantar normals, or anatomical quality.

The broad hip patch approaches from49.577mm at t=0 to zero near t=1s and
has39zero-distance pairs at t=2s. This includes folds and upper thighs. Its
minimum cannot establish posterior support or refute the cloud6–9mm
posterior-hover observation. Cloud posterior classification remains open.

No player paths, GLB bytes, physics or runtime pose driver changed. The source
clip remains `diagnostic_contact_observations_STEP`; engine buildcb2e008e and
capture harness60042670 are retained. Dense interpolation, physics-driven
rider posture, garment/normal quality, LOD, physical iOS and stranger gates
remain open. The aligned played movie/still/fixture are in `../aligned01/`.

Third-round ordinary-source ship gate: silent headless Chromium/Metal clears
4810recorded ticks in40.083333333333336s with every physics/counter byte matching
Node, zero mismatches/errors, crash at103ticks, and restart to riding/state0
in one tick. Command0.170ms; submitted frame3.130ms; motion after1tick.
Cold boot2730.183ms. These are desktop proxy times, not iOS presentation.
The same frozen20-model ordinary build has no candidate mapping/adapter.
WebKit mechanically clears/restarts with identical bytes but its strict gate
returns false for an unused Three preload warning; the complete warning report
is preserved. Existing ship harness and allowlist are unchanged.

Run `node --import tsx harness/rider-contact-diagnostic/surfaces.mjs` against
the retained exact aligned capture. Report hashes, masks, per-time witnesses,
coverage and limits are in `full-surface-residuals.json`.
