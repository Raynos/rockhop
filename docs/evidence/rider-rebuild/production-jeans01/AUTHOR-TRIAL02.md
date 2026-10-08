# Named-group cleanup fails before a master save

Parent checkpoint50ab61488 and the silent Metal11/11 baseline admitted one
repaired CPU2 author stage. Script SHA b54c69f7b6a3e4dc310f67a906e78079485aa36795b03075e8f882dc670f48f2
and recipe SHA66c1f4084e806eb465cd5201e9821b4de43c2c7f1ee8f87b92366fcb17e0753b
matched both current files and checkpoints before launch. Nonblocking lockf and
the canonical180second guard returned exit1 after6.273seconds. The process
handle exited, and the heavy lease is released.

The first handle-reacquisition repair does not resolve group setup: after
modifier application, `target.vertex_groups['SelectedSculptProjection']`
raises KeyError because that name is absent. The earlier stale-RNA-only diagnosis
was incomplete. The source assigns the modifier group property before creating
that named group; Blender may clear a nonexistent group selection before the
following creation reads its name. This setup-order explanation is an inference
from the actual code/trace, not a separately executed probe.

The trial stopped before body-field initialization, identity assertion, output
directory creation and master save. No native candidate/report exists. No fitted
geometry, unchanged-body/rest receipt, bake, moving art or phone pass is claimed.
The complete guard and byte-identical worker.txt are retained in author-guard02.
No warning filter, further edit, parameter change, probe or retry has run.

Parent reviews this repeated concrete source failure before authorizing any
next work. Original sources and fitting controls remain unchanged; all gates
remain open.

## Source diagnosis correction, checkpoint pending

The first stale-handle-only diagnosis was incomplete. Actual code bound a
modifier group before that named group existed, then used the validated setter
value to name its new group. The corrected frozen source creates the explicitly
named group first, asserts its exact name, binds the modifier, and asserts exact
binding before apply. It then reacquires the group and asserts presence after
apply; it never silently skips a missing group.

This is the only modifier vertex_group setter in the owned source. Skin groups
are explicitly created before population; lattice and armature object setters
point to existing objects. No other equivalent setup ordering is present.
Fitting controls, source pins, silhouette thresholds and author/bake separation
remain unchanged. The source parses; the correction has not run. Parent must
checkpoint it before admitting a fresh single author stage.
