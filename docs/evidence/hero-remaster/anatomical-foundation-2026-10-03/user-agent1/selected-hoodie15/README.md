# Matched donor transfer isolation — unaccepted

Root rejected source14's played appearance. This unit isolates rest material
transfer before further rig/collision work. Source13 and failed source14 stay
frozen. Source15 is an **unrigged material test on exact source13 geometry**,
not an accepted replacement hoodie or wearing handoff.

`material-inspection.json` finds matching PBR wiring and color spaces:
base sRGB, roughness/metallic Non-Color, original Principled defaults.
No channel/color-space fault explains the played appearance. The source10
ray bake mapped fitted vertices back into original donor space before casting
bake rays. This can change correspondence inside each reconstructed face.
The direct test queries actual registered donor triangles separately for each
occupied atlas texel and samples their original UVs, without source-island
interpolation. Original donor images and material graph supply every color;
there is no recolor or uniform-shirt substitution.

Of 1,457,341 occupied atlas texels, only five have both black old color and
zero roughness. Ordinary missing bake coverage does not explain mottling.
Direct-vs-old base-color linear L2 discrepancy p95 is0.463. The direct test
can still select an inappropriate folded/interior donor surface, especially
where the fitted cloth diverges from the actual donor; source distance p95
is39.605 mm and maximum77.466 mm. These values diagnose correspondence and
shape loss, not art acceptance or a proven complete texture repair.

`native-preservation.json` independently verifies all22 original mesh data,
18 material graphs,17 images and51 rest/pose bones unchanged. The derivative
has identical source13 positions, polygon cycles and UVs. Protected body/head
and all failed controls remain intact. Actual direct-source correspondences
are pinned in the compressed atlas archive under the owned source directory.

Play `review/matched-donor-transfer.mp4`: four synchronized columns show the
original donor with uniform unit/frame placement, the actual donor after the
existing piecewise registration, frozen fitted source13, and source15's direct
UV test. Same camera/light settings throughout48 orbit frames,6fps,8seconds,
2560×640, no audio, full FFmpeg decode with zero errors. Source13 geometry is
unchanged between the last two columns, so silhouette differences from the
donor cannot be repaired by this texture-only test. Donor display derivatives
recompute geometric normals after mapping; original native inputs stay frozen.

Root alone judges this played comparison. The next construction decision
must recover recognizable selected hood, cuffs, sleeve volume and hem before
another broad native motion iteration. Future rig/export uses explicit native
four-influence contract with full-versus-four loss reported. All M0–M5 and
iOS/wearing/consumed collision gates remain open. No Library duplicate,
inference, worker, normal-player promotion or publication is authorized.
