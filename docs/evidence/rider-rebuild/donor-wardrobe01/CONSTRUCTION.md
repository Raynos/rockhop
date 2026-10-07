# Actual selected hoodie and jeans construction

The user rejected the procedural replacement clothes. This helper derives the
candidate from the selected hoodie25 native mesh and the original painted jeans
source. It never uses a wearer surface as garment geometry or garment UVs.

`assets/blender/rider-rebuild/donor-wardrobe01/build-wardrobe.py` is invoked by the
native owner as `buildWardrobe(body, rig, out)`. Source hashes are in
`source-pins.json`; all twenty original and prepared wardrobe pins were rehashed
and matched on October7. This is a source checkpoint, not moving acceptance.

- Hoodie: retain12430 source points, original polygon cycles, exact loop UVs,
  material graphs, smooth flags and sharp edges. The old rig supplies measured
  anatomical coordinates only; all old weights and modifiers are discarded.
- Fit the old front/lateral/Z frame by a proper rotation, then map the actual
  shoulder/elbow/wrist controls into the current75-bone wearer's joint heads.
  Source historical side names are explicitly remapped by spatial laterality.
- Jeans: retain the original7978-point/16000-triangle compact geometry. Every
  corner uses an inward query to identify its original dense source UV side;
  the actual corner is projected to that source triangle and its original loop
  UVs are interpolated. A sidecar records original triangle row, source UV face,
  barycentric coordinate and actual projection distance. No UV extrapolation
  from a single tiny triangle across a whole compact face remains.
- Preserve exact original extracted jeans base-color and metallic/roughness
  maps. Waist dimensions come from the actual body cross-section. Leg center
  lines follow hip, knee and ankle joint heads, preserving the donor pattern.
- New skin fields interpolate normalized wearer fields within torso, pelvis,
  left/right arm or left/right leg scopes, including all `.001` twist segments.
  Actual ports share consistent endpoint fields with two neighboring-row fades.
  Hem fields stay on the pelvis; sleeve fields stay on arm chains.

Validation before native execution: Python syntax passes and source pins match.
The guarded job must write its actual dimensions, anatomical controls, original
port classifications, source UV projection diagnostics and construction report.
The parent must inspect the whole outfit moving in the actual game before
claiming fit, appearance, collisions, export or device qualification. No body
faces are hidden by this helper and no original source master is edited.
