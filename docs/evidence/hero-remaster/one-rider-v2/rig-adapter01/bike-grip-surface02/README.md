# Actual rubber grip surfaces recovered

CPU production decoder reads unchanged Rookie and Pro. Weld exact decoded
positions at one micrometre for connectivity (UV/normal duplicates only),
then find the single44-triangle rubber-grip island near each grip marker.
The actual two bikes have byte-identical grip island reports. Source hashes
before and after remain unchanged. Real vertices and all44triangles retained.

The existing build_bike.py recipe endpoints are(.932,.779,±.260) to
(.915,.780,±.425). Actual decoded circumradii15.880–17.103mm match its17→16mm
taper within0.139mm quantization error. Grip markers are4.797mm off the rod
axis. Polygon faces lie inside those circumradii. Neither18mm cylinder nor
marker-distance minimum from mixed rod/lever sections is adequate proof.

Next native held-shape experiment should use actual triangle surface and
slanted axis/taper, converting target dimensions through declared1.015
character scale. Explicit virtual socket/rod-axis alignment must preserve
existing physics grip targets. Parent still judges actual rendered fingers,
thumb, wrist and played lean/landing contacts. No bike or player edits.

Run pnpm exec tsx harness/hero-remaster/new-rider-bike-grip-components.mts.
Lint and complete harness typecheck pass. CPU measurement only; not a
visible-contact or game-ready certificate.
