# Waist skin improves; shoulder repair remains unaccepted

Same improved WHITE character,19-bone contract, explicit private adapter and
physics. Local hip smoothstep now finishes before switching to pure pelvis.
Actual PBR/gray played evidence shows a cleaner hem. At tick4210 maximum
waist edge stretch drops22.280 to4.804times; armpit stretch stays11.490times.
At1210 no conditioned triangle exceeds4times. Shoulder hole remains visible.

The height-only shoulder taper creates a discontinuity where the protected
NEW hood meets the original body; unconditioned stretch worsens to118.286
at4210. Runtime smoothing hides that new defect but does not fix the visible
shoulder hole. Reject that part. Keep the waist correction, reset shoulder
weights to body05, then test constrained smoothing along connected mesh edges.
Blender's weight Smooth uses adjacent vertices; adapt that mechanism with
explicit frozen hood/cuff/body-boundary anchors and four influence export.
No claim a global remesh, new body or texture repaint is needed.

A first setup edit also changed NEW hood weights; the parity guard rejected
it. Corrected semantic material protection passes: finalGLB JSON and every
binary byte outside original-body skin accessors are exact body05. Face,
hood/glove weights, materials/images, rest positions/normals/UVs/topology,
both held morphs, inversebinds, sockets, adapter and original clips unchanged.
Untouched source/private failed setup retained with receipts.

Actual40s480samples retain allhand/foot socket contacts, grip<=.190µm and
sole<=1.840µm. Lean reachesboth-1/+1 through landings. Silent third-round
coldboot/clear/crash/restart passes both tiers: finish40.083333333333336,
hash368f1ca5bd9e830a, exact Float64bytes, crash103, restart1/2ms, errors0.
Fullsamecandidate underbothLODnames is diagnostic, not a realLOD pass.
Body6.7/face6.5 under unmatched engine lighting remain below appearance bar.
Garage, Pro, actual surfaces, face8 and checkpoint2/3 are still open.

Primary method reference: [Blender weight Smooth and normalization](https://docs.blender.org/manual/en/4.4/sculpt_paint/weight_paint/editing.html). Connected-edge smoothing here is our bounded implementation, not a claimed biharmonic solver.
