# Observe actual IK influence after mode dependency refresh

Finding: Actual conditioned04 analysis stopped at Rookie frame 51, source tick 250.
Requested FK and IK produced identical 1.1842075575 mm all75 affine error.
Changing a custom property and calling the view-layer update did not establish
that a driven IK influence had actually changed. The failure is preserved;
frozen04 remains unchanged, and complete-master integration is paused.

Adapter05 calls the exact frozen04 mode setter, observes the current source
constraint influences, explicitly tags the rig, and updates the dependency
graph. It then reads the evaluated rig and requires all four IK influences to
equal the requested modes exactly, with live mode one and constraints unmuted.
Each request writes its before/after influence witness before asserting, so a
failure cannot masquerade as a sampled FK pose. The native run must establish
whether this resolves the actual dependency-propagation mechanism.

All frozen04 construction, source pins, branch policy, native rest, solver
settings and 0.1 mm affine gates stay intact. Analysis still requires every
captured FK branch and selected IK branch to pass; saved replay, generic action
activation, mode boundaries and fresh native bake remain mandatory. The adapter
names its own actual recipe/input and the original04 recipe/input in every
written output. It never claims an adapter run used the original executor.

Validation: four Python 3.9 source fixtures pass for tag-before-update ordering,
per-limb requests and return to IK, stale-driver rejection with an emitted
witness, and muted-constraint rejection. Both Python sources parse under 3.9;
the original-guard wrapper passes bash syntax. Complete actual05 input ancestry
validates against frozen04 and its actual failure. These fixtures exercise the
adapter contract, not Blender's dependency graph; no native05 pass is claimed.

The parent owns source review, checkpoint commits and serial original-guard
execution. No Blender, browser, geometry or solver experiment was launched by
this lead. Complete dressed integration resumes only after an actual conditioned
package passes and the native10/qualifier11 master is actually qualified.

Limits: Native05 dependency propagation, FK branch preservation, all-key replay and complete dressed integration remain unexecuted. Parent reviewed sources and reran four fixtures, syntax and actual input ancestry; these prove source behavior only.
