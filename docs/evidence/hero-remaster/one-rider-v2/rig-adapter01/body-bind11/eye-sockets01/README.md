# Inspect the eye geometry before component fitting

Read-only CPU projection includes both original head and reconstructed cheeks:
61,393 vertices,99,914 triangles. The head SHA remains exact. Gray rendering
and depth expose shallow, asymmetric fused eye surfaces. Each anterior eye ROI
contains1,657/1,587 vertices but no position-welded boundary edge: there is no
existing open aperture to receive a separate eyeball. Overlaying a donor could
hide this surface from one view and intersect it elsewhere.

Approximate source eye framing centres are Y1.694m/Z±.033m. At that row,
frontX is.745351m on negativeZ and.747311m on positiveZ. These are sampled
surface depths, not clinically defined eye centres or an accepted fitting.
See report.json and private depth/triangle data for reproducibility.

The installed CC0 MakeHuman high-poly eye donor has1,064 vertices/1,020 polygons
and four components, two per eye. Its source licence header and exact hash are
retained. Raw donor units/axes and layered surfaces need a measured fit; no
donor is assembled here. Two fresh CPU teammates independently audit topology
and produce a normalized eye donor in separate owned directories.

Parent reviewed the gray/textured source projection. Next reconstruct a local
continuous lid aperture around fitted eyes, keeping external face identity,
hood, body, neck, UV detail and19-bone mapping. No global remeshing or anatomy
changes to limbs. Static CPU projection is causal inspection; the current
played PBR/gray evidence remains the appearance authority and face6.8 stays
below7/target8. No gate or source asset is promoted.

The first inspection omitted the cheek primitive and consequently showed
holes where that separate repaired surface belongs. That diagnostic omission
was corrected before this checkpoint; it is not a new source defect. The
2D-cross NumPy deprecation warning was removed using scalar determinant math.
CPU-only, no GPU workload or new dependencies. Geometry remains byte-exact.
