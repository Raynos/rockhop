# Paired PBR cuff-source context is ready for played review

Builder checkpoint only. One admitted CPU2 native render passed in 190.206
seconds, followed by one silent CPU2 encode in 0.917152 seconds and a complete
file decode. No retry or source experiment occurred. The canonical nonblocking
lease was released when rendering completed; peak sampled anonymous memory was
28.4 GiB, anonymous plus wired 35.2 GiB.

All 14543 retained source08 faces, all source XYZ, Float32 display UV and original
maps passed native before/after assertions. Source08 remains SHA
`8379004e394bbae110f495c13bfc12a205977061d13cefdcc8ee24c6e5343782`.
The prototype UV projection remains a bake/seam proxy; its Float64-to-Float32
display residual is 2.9802322388e-8. Original maps/material channels were used;
actual triangle normals were flat because the donor declares no NORMAL.

The driver produced 60 continuous moving camera poses: whole-source orbit,
travel toward the negative-Z cuff neighborhood and a close arc. Each unmarked
and marked panel shares an exact actual native camera matrix. Readback verified
all 120 frame hashes, assigned-versus-native translation residual at most
1.2318643208e-7 donor units, aim residual 2.9863218063e-7 and rotation
orthogonality residual 6.8395099362e-8. Thin semitransparent cyan/orange guides
follow the two exact source-edge cycles only in the marked panel. The left
unmarked panel remains available for unobscured source interpretation.

`paired-pbr-source-context.mp4` is 719455 bytes, SHA
`96e0a00b35c602dd0e35ce4d0c2db32d6a30f468fbc9970b41bbbe679acd5a83`,
1536x768, 60 frames at 12 fps, duration 5 seconds, one video stream, zero audio
streams. Probe and full decode passed; actual played review is pending and is
owned by the parent after checkpoint41.

The native process emitted two `Material.use_nodes` deprecation warnings for
future Blender 6.0 removal, at renderer lines 79 and 119. They are disclosed in
`execution.json`; no warning was suppressed or rerun. Current rendering and all
scope assertions passed.

Limits: no builder art/source-feature interpretation. Genus 1 may describe a
legitimate cuff strap/detail/passage; it is not automatically a defect. The film
does not certify free cavity volume, mouth traversal, finger enclosure, fit,
skin, grip, source edits, additional removal, engine or device acceptance.
