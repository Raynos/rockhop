The failed outer-boundary assertion has a measured numeric cause

The exact original `Surgery.add`, `interpolate_vertex`, and `cut` methods were replayed from the pinned constructor on all 116,289 original triangles incident to source Y ≤ −.64. This is the actual clipping code, including its original float32 arithmetic; no cuff fit, topology replacement, or native save ran.

The 1,809 cut vertices occupy three rounded Y values: −0.6500000357627869,−0.6499999761581421, and−0.6499999165534973. Cuff09 then explicitly converts its source array to float64 and selects whole triangles at Y ≤ −.65 + 1e−8. That selects 109,881 pieces instead of the 112,594 pieces included by the floor cutter's 1e−7 plane tolerance. The resulting two boundary circuits have 513 and 392 vertices and reach Y −.653221: they lie behind the intended floor plane. Their IDs cannot match the 781-vertex measured inner cut that cuff09 subtracts. Calling the remainder an outer boundary therefore retains both circuits and triggers the failure.

Using the floor cutter's own tolerance yields the intended 1,029-vertex exterior and 781-vertex interior circuits. Raw-ID and source-position-welded incidence agree; the sparse source provides no evidence of duplicated UV-seam identity causing this failure. No extra opening, cap, or disconnected ornament is indicated by this replay.

The proposed precise correction is to convert original source coordinates to float64 **before** clipping. Conversion preserves every original float32 coordinate exactly and lets interpolated cuts use the same precision as the ownership predicate. It does not relax a guard, move original donor vertices, change the radius budget, delete a component, or sew a guessed cap. The selected external sheet and the explicitly authorized inner-return reconstruction still require actual native ownership and full dense geometry checks.

Validation: source probe exits 0; both scripts syntax-compile. Pinned original donor and constructor hashes are verified before replay. [Exact source probe](boundary-source-probe.json) retains complete boundary IDs. [Native probe source](../../../../assets/blender/rider-rebuild/selected-cuff-topology10/probe_native.py) is prepared for the parent's guarded execution and has not run here.

Limits: Sparse clipping establishes the numeric inconsistency, not the outcome of the full native floor component deletion. Actual native confirmation remains required before a new construction is justified. No repaired rider, dense-gate result, moving review, or acceptance is claimed.
