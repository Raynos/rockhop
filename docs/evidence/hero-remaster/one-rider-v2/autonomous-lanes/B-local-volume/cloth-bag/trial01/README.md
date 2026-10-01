# Genuine sewn hood bag: first actual cloth result, unaccepted

This is one bounded distinct CPU cloth-drape experiment, started 2026-10-01 03:03:26 UTC with a 03:33:26 UTC ceiling. The 15 failures in the old cut/strip/lining repair lineage remain retired. The preceding NEW wholehood cape-form appearance failure remains 1. Parent rejects the first front rim: paper-like crumpling, an open dark center-neck gap and a pinched lower-left notch. The back gravity bag improves on the earlier cape. Successful simulation and UV counts do not accept the character.

## Actual mechanism

Two mirrored hood-bag panels share 21 rear-center seam vertices. Blender used an explicit flat textile rest shape key and gravity, self-collision, torso collision and head collision over 48 frames at 24 fps, with 49 pinned neck vertices. Sewing is shared topology before simulation; a sewing-spring solver is not claimed. The cloth has 1,029 vertices and 960 quads. Quality, stiffness, mass, collision distances and all coordinates are frozen in the recipe and settings.

Measured movement at frame 48 was 54.6 mm mean and 218.6 mm maximum; 978 vertices moved more than 1 mm. Pinned movement stayed below 0.000051 mm. The simulation took 7.6 seconds and used about 886 MB maximum RSS, CPU only with two threads. Before gravity, 54 free vertices received a bounded collider-normal correction, maximum 23.2 mm; this correction is recorded separately and is not presented as simulation deformation.

The two outer panels were actually simulated. The two lining panels were offset 1.5 mm from the measured exterior drape; the lining was NOT independently simulated. The pinned lining hem extends 12 mm downward. The free face rim joins exterior and lining with explicit triangles and a nonzero-width UV strip. Contact/intersection quality of this derived lining remains unaccepted.

## Preserved source and UV guards

The accepted isolated-correction01 body source is untouched. The same previously declared complete hood/head plus central-yoke exclusion is the body guard. The rejected cape panel coordinates are not inputs; neither are the retired 142/194/43/23 cut seams. All 40,386 original retained triangles, original vertex coordinates, both source UV arrays and original material indices are exact. Existing sleeves, lower body and hands remain unchanged. The shared Blender binary is 5.2.1 LTS with isolated lane configuration, scripts and temporary roots; no model environments or global packages were modified.

All seven new material charts have nonzero UV triangle area, including neck binding and free-rim roll. Source chart arrays are preserved. Different new material slots have their own coherent charts; this is not a packed single-atlas bake. No texture was baked, no PBR appearance was accepted, and no new garment weights were assigned.

The native head is neutral gray SIZING CONTROL ONLY. Its source geometry, UVs and bytes are unchanged. The finished rider must be WHITE; the new H21 white buzz-face source and final identity are parent-owned. This fixture does not select or replace that direction.

## Actual GLB renders and visible limitations

`gray-neck-front.png`, `gray-neck-profile.png`, `gray-neck-rear.png` and `gray-neck-three-quarter.png` are actual CPU renders after importing the exported GLB. `gray-full-front.png` and `gray-full-rear.png` show the unchanged full body. Face views are sizing-fixture diagnostics, not new face proposals. Render camera/light recipes and GLB material/UV reimport proof are in `reimport-and-renders.json`.

The first views show a real gravity-drooped back hood bag. They also show a crumpled front rim, a dark center-front neck opening and a pinched/notched left lower rim. The parent judges the form against the approved reference and the >=7/10 face/full-character bar. Static coverage, neck rotation/bending, rigging and gameplay contacts remain UNMEASURED. There is no promotion into player assets.

## Reproduction

Use the lane's isolated CPU environment with OMP/BLAS/VECLIB thread count 2 and its Blender config/scripts/extensions/TMPDIR. `settings-trial01.json` records exact master paths, fitting transform, mask and deadline. Source export and the body guard originate in the frozen `clean-construction/trial01` checkpoint; fresh input copies and their hashes are preserved in the ignored runtime directory. Run `build_simulate_trial01.py`, then `render_neutral_trial01.py`, then read-only `audit_trial01.py`. Existing evidence is intentionally write-once for review; use a new versioned trial for another experiment.

Runtime masters and initial/rest/frame snapshots remain under `/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/autonomous-lanes/B-local-volume/cloth-bag/trial01/`. `frozen-manifest.json` records exact source, evidence and large-output hashes.

Parent review: actual rear, three-quarter and full-front renders were inspected
as well as front/profile. Cloth-bag appearance failure1; retain the real bag
mechanism, correct fleece stiffness/stable binding and use actual new white
bust landmarks before any bake. Old15 retired repairs remain stopped.
