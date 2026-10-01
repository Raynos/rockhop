# Body-bind17: frozen anatomical graft construction

This is an **unaccepted, pre-export CPU construction**. Current white rider
body11 is unchanged. No candidate GLB, render, model workload or player asset
was produced. The parent stopped this lane after the first anatomical graft
trial and one diagnostic replay. Do not resume construction or relax the
unchanged 8 mm eye-registration bound from this checkpoint.

## Actual mechanism

The recipe clips both existing front/inward face sheets locally, retaining
source attributes barycentrically and conforming source subdivisions. It uses
the frozen CC0 MakeHuman native anatomical patch from
`anatomical-eye-donor01/standalone01`: 168 actual quads and 200 vertices per eye.
The native inner aperture is unchanged. Only its outer boundary and one adjacent
row are registered to the source face; the native surface is connected to the
front sheet and a separate inward wall connects the inner aperture to the
source inward sheet. Actual retained CC0 eye geometry is fitted behind it.
The retired visible sampled lid rings are absent.

The first construction stopped at a raw-index seam guard. Original head UV and
normal splits require exact-position physical edge identities; that guard was
corrected without changing the geometry. Its receipt is preserved separately
in `construction01/initial-join-guard-failure.json`.

## Frozen failure and independent audit

The guarded construction then rejected the negative-Z eye (native L, actual
eye R). The diagnostic replay added probe evidence without changing the fit:

| Tested category | Maximum behind-cornea-front distance |
| --- | ---: |
| Native anatomical lid | 3.767 mm |
| Front skin join | 0 mm |
| Inward wall | 9.178 mm |

Including the fixed 0.25 mm clearance, the wall would force a 9.428 mm backward
eye translation, exceeding the 8 mm bound. The worst wall vertex is
`[0.731222928, 1.688882470, -0.040922794]` m. The independently recomputed
corneal front hit at that Y/Z is `X = 0.740401392` m, triangle 218.

The independent audit found **one corneal ray hit**, not a closed-sphere pair.
Therefore this guard proves the front-clearance rejection; it does **not**
prove an actual triangle intersection or closed globe interior. Applying the
same front-ray clearance rule to a deliberately inward wall may be too
conservative. Parent review must distinguish guard applicability from an
unsound anatomical fit before choosing a different construction.

Positive-Z local construction ran before the negative-Z stop. Whole-graft
export, source conservation, final manifold checks, texture baking, normals,
moving rig evidence and appearance judgment were never reached. They are not
passes. The native aperture positions independently remain byte-exact.

The native base-human helper sphere center agrees with its native eye joint.
At the measured scale, its forward extent is 12.335 mm; the actual retained
corneal donor extends 15.236 mm from its target center, a 2.900 mm discrepancy.
This is source-frame evidence, not a demonstrated explanation or repair.

## Reproducible retained evidence

- Recipe: `assets/blender/hero-remaster/rider/one-rider-v2/rig-adapter01/body-bind17/`
  (`prepare_recipe.py`, generated `build_graft.py`, `graft_fragment.py`).
- Independent read-only diagnostic: `audit_failure.py`. Running this script
  reads frozen data and recomputes the audit; it performs no construction.
- Receipts: `construction01/clearance-registration-failure.json` and
  `construction01/failure-audit.json`.
- Private diagnostic geometry:
  `/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind17/construction01/clearance-registration-failure.npz`.
  This preserves clipped source geometry, the native patch before and after
  registration, actual donor eyes, the front join and the rejected inward wall.
- Untouched current11 SHA256:
  `b7f4f22790124c664f9907104e5b17b77775b4c5c995f715d62be640bbcc8754`.
- Private diagnostic NPZ SHA256:
  `e137447c05ec223edf78cae4e187385477baabbcbd44fe06365fd80c2d3e583a`.

Validation: the independent audit exited 0, confirmed finite saved positions,
exact worst triangle/probe coordinates, the actual corneal ray, unchanged
native aperture, unchanged current11 hash and zero body17 GLB exports. The
construction exited 1 at its explicit clearance rejection. No GPU was used.
