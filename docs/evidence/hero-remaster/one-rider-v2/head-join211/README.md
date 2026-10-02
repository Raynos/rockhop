# Selective head/neck join 211: contract only

The approved **NEW head** in source185 mesh1 primitives0/1 remains the face donor. Native208’s generated head is explicitly discarded by this proposed recipe. Historical production is never a donor. No assembled mesh, rig, bake or game export was produced.

Native208 is a finite diagnostic subset of an invalid native generation; this contract does not qualify that source. Its original positions and indices remain immutable. `join-contract.json` pins the input GLBs and the private literal-cut NPZ, including exact original triangle ordinals, boundary POSITION-row edge IDs, interpolation parameters and cut positions.

## Concrete cut and reconstruction

At native Y0.76, the neck forms one closed231-edge circuit separate from two hood circuits. Remove only the15,735-face head-connected component and split only the231 literal neck-crossed triangles. Retain the lower parts of those triangles. The other622 plane-crossed hood triangles and2,688 hood triangles above the plane remain exactly intact. A global plane cut would clip those hood surfaces; this selective topological separation avoids that earlier error.

The approved donor is a thin two-sheet bust, not a single solid neck surface. At canonical Y1.55 its outer neck circuit has318 edges and its inner circuit306. Remove only lower bust geometry, retain original face geometry/materials/UVs above1.58 and the complete repaired mouth primitive. Use one coherent radial displacement field on both donor sheets in the1.55–1.58 neck band, then close the internal lower ring by a wound, nested ear-clipped cap. Sew the **outer** ring to the retained native skin using boundary subdivision, exact shared physical positions and original per-corner material/UV ancestry. An overlapping closed bust is not this recipe.

The parent-authored anatomical normalization anchors the actual sole surface to ground and the native neck circuit to the unchanged donor circuit. It uses scale0.8805751157835033, native+Z → game+X(front), native+Y → game+Y, and native+X → game−Z(right). The full4×4 matrix is in the contract. The donor transform is identity. This is an explicit authoring choice requiring proportion review, not a skeleton pass or a bounding-box face fit.

## Admission remains bounded

All318 donor-to-native angular rays intersect the target contour uniquely. Their boundary displacement has median8.18mm and maximum24.07mm. That exceeds the proposed20mm bound: **do not construct under that bound**. Parent may register an explicit25mm maximum after reviewing this evidence, or choose a distinct local neck retopology. This reconnaissance made zero geometry edits and is not a failed constructed join attempt.

The actual bridge/subdivision, thickness preservation, internal cap, surface intersections and continuous deformation remain unproved. Require gray/PBR front, profile, rear and three-quarter closeups, a turntable, then continuous ±45° neck yaw,20° flexion,15° extension and spine bends in Blender and the actual Three.js export. Verify literal protected-head/hood ancestry, winding, connected physical outer skin, new holes and full triangle intersections; screenshots and distance thresholds alone are insufficient.

## Prior and independent work inspected

Read `inspect_neck.py`, `neck-native/probe.py`, `neck-native/build_trial02.py`, `parent-assembly/donor-fit04/build.py`, `donor-fit05/build.py` and their actual geometry approach before designing this contract. The earlier donor-fit workflow attached a new hood to the shirt with exact boundary subdivision, while the bust remained a separate closed object. Its garment seam is useful construction evidence, not proof of this new skin join. The new source cannot reuse the historical body04 normalization.

Read the independent task3 `hoodie-repair02/neck-probe-manifest.json` without modifying its paths. It tests inherited neck poses and provides no equivalent selective raw-Tpose neck construction. Ownership remains separate.

CPU NumPy/SciPy only, two-thread limits. No Blender, GPU/Metal export, model inference, source mutation, acceptance score, player asset promotion or normal-player release. Geometry projection and section diagrams are diagnostic point/contour plots, not render quality evidence.
