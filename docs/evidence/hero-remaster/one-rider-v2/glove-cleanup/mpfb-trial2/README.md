# Fresh anatomical glove correction — unaccepted

This is the second glove appearance direction after the rejected procedural
slab-palm trial. The installed CC0 MPFB base was **freshly instantiated** into
a new unposed source; no historical production mesh or prior failed rider
body was imported as a donor. Only the connected hand/palm/wrist skin surfaces
are used for the glove derivative. Native finger chains are authoring aids;
their fixed curl is collapsed into geometry before source wrist sewing.

The initial anatomical assembly is retained here, but its right-hand curl
had a reflection error: identical signed rotations about mirrored axes
produced different hand lengths. The separate
[mirror-corrected derivative](mirror-corrected/README.md) fixes the right
flexion signs and palm-normal basis. Both source and first derivative remain
frozen. This is the second and last setup correction, following the addon
preference registration correction. No further construction is authorized
inside this bounded trial without the parent’s next decision.

The initial inspection also found 341 nonadjacent triangle overlap/touch
pairs at finger bends. Those results are preserved in inspection.json; they
must not be hidden by the zero boundary-edge count. Its diagnostic framing
clipped the longest fingertips, and the temporary weights did not cover
glove vertices below Z 0.70. The corrected inspection uses full-finger framing
and includes every new glove vertex in the temporary hand weights. These are
diagnostic corrections, not proof of final skinning.

The fresh source master is
`~/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/mpfb-trial2/fresh-anatomical-source.blend`.
Its MPFB base OBJ has an explicit CC0 asset header; provenance/macros/native
chains are recorded in fresh-source.json. The initial assembly and all raw
hand NPZs remain in that same runtime namespace. No baking, final 19-bone rig,
physics posing, Garage or normal player asset promotion occurred.

The earlier 22 mm diameter cage was an unverified target. Inspection of the
actually consumed bikes reports approximately 34 mm diameter rubber grips;
[definitive geometric fits](actual-grip-reference.json) are frozen from the
contact audit. Neither version has accepted palm/finger contact. Existing
bike assets remain unchanged.

[Neutral anatomical evidence](neutral-anatomy/README.md) separates model
quality from the stopped fixed-curl posing failure. No anatomy acceptance or
pose/contact pass is claimed.
