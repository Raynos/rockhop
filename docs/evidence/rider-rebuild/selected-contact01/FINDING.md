# Selected sole surface differs from inherited socket

Actual Garage05 reports sole socket errors2.58/2.60µm and both footOnPeg flags true. That diagnostic measures the inherited canonical75 helper, not the original selected outer sole. On exact7d826b83 rider and e55919d6 rookie bike, all measured sole support triangles are rigid own-side DEF-foot weight1.

The finite decoded peg tops at the sampled support are Y.025981444865465, while the adapter targets the inherited helper at Y.031. Actual selected soles penetrate those finite surfaces by11.927mmL/11.757mmR at the existing center and up to13.546mmL/13.669mmR over nine finite support samples. This is a genuine selected-surface mismatch despite near-zero helper errors.

`source02.json` preserves actual triangles, current native vertex IDs, barycentrics, coordinates, normals and fields. `driver-proposal.json` supplies explicit selectedSoleInFoot matrices and matching finite peg targets. Matching horizontal witness offsets cancel: this isolated proposal translates the feet upward by the measured mismatch. The selected sole normals oppose the peg normals by dot.99638/.99858; existing orientation is retained only as an unaccepted baseline. No bone, socket or rest-frame changes are proposed.

The adapter should consume the explicit source-bound matrix instead of inherited helper local coordinates, solve against the measured finite peg target, and diagnose footWorld×selectedSoleInFoot. Keep inherited helper error separately. A source-pin change requires checking the same boot witness IDs/barycentrics/fields against that actual output. Parent must judge actual Garage/game movement; nine sampled support points are not a full finite collision proof.

The palm ray intersects the selected thumb web, with substantial thumb.01 weights, at41.6mm from the inherited palm helper. It is not a rigid palm pad witness and must not drive a hand shift. The actual bar upper surface is14.63/14.71mm above the grip axis at the inherited target. Fixed digit curls and glove/bar finite contacts remain unqualified.

Validation: deterministic binary/meshopt GLB reads executed successfully; Node source syntax check passed. No browser, Blender, renderer, shared adapter, rig, contract or normal player asset changes.
