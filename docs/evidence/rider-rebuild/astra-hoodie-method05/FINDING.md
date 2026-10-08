# Restore selected sleeve shape; stop rectangular patch joins

Fresh independent gpt-6-astra/high adviser inspected actual selected original
PBR, current four-view PBR, saved arrays and authoring code. Parent independently
recomputed the corner errors below and rejected actual profile/rear form.

The repair, not the selected design, introduced the plates. `cloth_surface()`
uses constant front/rear depth across each cross-panel row. Its perimeter misses
actual sleeve anchors by centimetres; a one-strip zipper fills that mismatch
with the visible walls. The independent bridge height adds a high arch rather
than preserving the selected sloping shoulder. Clean body-point/fan checks did
not establish a useful garment silhouette.

Keep original selected hood/chest/sleeve detail and immutable stock. Stop this
rectangular ruled-depth/zipper method; do not tune depth, bridge, density or
smoothing. Use actual selected rounded sleeve-cap/armhole as the shape reference.
Tailor a broad continuous shoulder, chest/back support, axilla and upper-arm
region with explicit editable lattice/cage controls. Preserve source geometry,
UV and PBR where useful. Restore actual boundary positions and cloth directions;
malformed derivative boundaries are free to change. Author outside cloth first,
derive inside thickness afterward, and transfer detail after shape is credible.

Parent delegated concrete selected-original B-spline cage authoring to the
hoodie owner. Actual original sleeve-center sections replace guessed landmarks.
No new generic appearance or patch placeholders. Next visible result: rounded
selected shoulders in complete dressed master, then neutral→forward reach→raised
arm→return played clip. Rest images can reject only.

Primary ordinary methods: [Lattice](https://docs.blender.org/manual/en/4.4/modeling/modifiers/deform/lattice.html),
[Mesh Deform](https://docs.staging.blender.org/manual/en/latest/modeling/modifiers/deform/mesh_deform.html).
