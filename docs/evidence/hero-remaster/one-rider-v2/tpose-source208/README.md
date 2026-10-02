# Retained native T-pose source — unaccepted diagnostic

Actual2.1 retry saved raw arrays and exact diagnostics before memory watchdog
terminated its own batch54.706s. Observed anonymous jumped56.966→82.017GB within
one-second samples. No further380 GPU repeat under this baseline. Watchdog is an
observed stop rule, not a hard allocation cap; next job needs conservative headroom.
First206 true observed peak was67.110GB; earlier63.298GB prose was incorrect.

Native254431 vertices/508842 faces contain107176 nonfinite vertices. All indices
valid. No triangle mixes finite/nonfinite rows:214336 entirely nonfinite faces,
294506 entirely finite faces. Literal finite isolation preserves147255 original
rows and every finite face, reversed winding only for separate display. No merge,
remesh, decimation or repair. Parent actualGLB ancestry exact. Finite subset has
zero open/nonmanifold edges,147249+6 component sizes, two zero-area triangles and
one position alias. The entire invalid native source remains untouched.

This permits gray diagnostic inspection, not promotion or a native-output pass.
No topology check proves fidelity to the whole field; no art/rig/pose/contact pass.
CPU synthetic audit independently shows NaN volume extraction can lose surfaces
under default Trimesh cleanup. Its applicability is supported by actual NaN rows,
but latent/grid data were not retained; complete extraction causality is unproved.
Dense-only256 is a separately declared conditional fallback, not same-resolution
or same-latent207 reconstruction. No new job is admitted yet.
