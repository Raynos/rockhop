# Glove trial1 — stopped during construction

No cleaned character was exported. The source body remains unchanged. The
CPU-only local authored glove trial failed before export when copying a face
from the local voxel-union/trimmed glove into the source-body BMesh. Blender
raised `ValueError: faces.new(...): face already exists`.

The first correction welded coincident positions and dissolved degenerate
edges on the **new glove patch only**. The identical duplicate-face error
persisted. Both failures are preserved in the setup-failure JSON files. No
third retry, bake, rigging or anatomy acceptance was attempted.

The source body cut and proposed bridge existed only in process memory and
were discarded on exit. No source GLB, dense NPZ, historical rider, hood,
garment, knees or shoes were changed. There is no derivative/master, camera
evidence or deformation video to present as successful work.

The next specific alternative is an explicit ring-loft palm/finger branch
mesh assembled from stable indexed vertices/faces, avoiding the failed local
voxel-union/decimation face-copy path. This needs the parent’s delegated
choice before a new technique is built. Its eventual sewn wrist would still
use the actual source closed loop below intact cuffs, and it must establish
one connected manifold body rather than overlapping glove shells.

## Planned explicit branch topology — not executed

Construct one rounded palm envelope with a distal quad grid. Leave four
eight-edge outlet loops in that grid, separated by actual webbing faces.
Each finger starts from its outlet’s **same vertex indices**, then adds
successive curved eight-vertex rings, inter-ring quads and a closed fingertip.
The palm underside contains a fifth deliberately reserved outlet for the
thumb, whose successive rings likewise share the outlet vertices. Finger
and thumb roots have no cap face, so none can be a closed tube merely
intersecting a closed palm. Webbing belongs to the shared manifold surface.

Round the new authored surface by a local subdivision/smoothing operation
before the final source wrist seam is attached. Keep the wrist outlet open;
sew its loop to the actual retained source boundary using explicit shared
indices and bridge faces, then recalculate the derivative normals. Validate
that each seam edge has exactly two incident faces and that all retained
body/glove triangles are in one connected component. Reject intersecting
fingers/thumbs rather than mistaking manifold edge counts for absence of
self-intersections. This is a proposal; no replacement mesh has been built.

[failure-manifest.json](failure-manifest.json) freezes both failing recipe
snapshots, their hashes, captured actual tool stdout and exit1 outcomes.
The first snapshot is reconstructed exactly by removing the four-line
patch that created attempt2; attempt2 matches the current failing script.
No failure is presented as visual hand progress or anatomy acceptance.
