# Preserve the physical pelvis carrier during spine control

Unaccepted private checkpoint. The author trunk role includes its pelvis ID.
Exclude that explicit ID from upper-spine aiming so a second torso solve cannot
overwrite the physical pelvis carrier. Source IDs, parents, lengths, weights,
input frame and physical COM are unchanged. No palm angle or nonzero spine
flex is selected for the runtime in this checkpoint.

Validation: ten actual CPU tests pass, including explicit ±.3rad spine-flex carrier preservation. Combined02 default target sweep now has
maximum COM residual 0.415 micrometers; actual hand gap remains 61.34 mm and
sole gap 21.82 mm. A diagnostic sweep of six explicit palm orientations,
seven input leans and thirteen signed spine angles cannot close every old-source
contact. All extra-flex samples keep the physical carrier fixed. The sweep
selects its lowest numerical gap, not an approved motion or preferred angle.

Evidence: [fixed carrier baseline](combined02-fixed-carrier-com.json),
[diagnostic sweep](combined02-spine-palm.json), [reproduction](spine-probe.mts).
Limits: no moving, bar-surface, device or native04 qualification is implied.
