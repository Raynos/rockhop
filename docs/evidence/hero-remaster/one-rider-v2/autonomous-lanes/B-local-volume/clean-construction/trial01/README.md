# NEW whole-hood construction — trial 01 rejected

**Parent rejected actual neutral front/rear appearance.** The new garment reads
as a tall, flat armored collar/cape with a squared rear block, rather than a
relaxed folded hood. The skin transition is cleaner, but the form is worse than
the user's best-so-far rider. This is the new construction lineage's first
appearance failure. The exhausted original 15 source-hood repair failures remain
retired and unchanged. No texture bake or production promotion occurred.

This trial independently exported the untouched accepted body master, then
replaced the whole source hood/head and declared central yoke using a new mask:
X ±0.190 m, front floor Z1.445 m, declining to rear Z1.335 m over Y0.03–0.12 m.
It used none of the retired collar masks or 142/194/43/23 seam inputs. The new
exclusion removed 18,887 complete triangles and produced a new 307-edge body-yoke
attachment. 40,386 complete source triangles retain exact original vertices,
both UV corner arrays and material indices. Sleeves, hands, legs, shoes, lower
body and drawstrings outside the declared mask are preserved. Original source
bytes have matching before/after SHA-256 hashes.

Four newly constructed outer/lining left/right panels and a rolled neck binding
were joined to that body attachment. Panels use an explicit new pattern chart,
not nearest-corner sampling of the original atlas. The cloth inner hem is a
separate open 307-edge lining hem intended to sit inside/below the body; its
concealment remains unmeasured. Zero nonmanifold edges did not accept the shape.
The construction recipe's radial/cubic drape controls produced the rejected
cape-like form and must not receive minor parameter churn as a substitute for a
true hood-bag pattern or actual cloth drape.

The chart is **unaccepted**: read-only audit finds all 614 binding triangles have
degenerate UV area because its roll chart has no width coordinate. Outer/lining
panels have finite nonzero triangle UV areas; distortion and seam tangent quality
were not accepted or baked. `new-chart-audit.json` discloses this plainly. Future
new source/pattern work requires a real width coordinate for binding UVs.

Actual `gray-neck-{front,profile,rear,three-quarter}.png`, full front/rear and face
front/profile views come from independent GLB reimport, with matched 640 px
cameras, Cycles CPU, two threads and 16 samples. The entire native skin/neck/
clavicle and eyes are unchanged **neutral sizing controls**, not a final identity.
The finished rider must be WHITE per the latest human instruction. Parent is
separately reviewing a fresh H21 white buzz-face source; the editable scale,
rotation and translation adapter is in `trial01-settings.json`. No identity or
skin-palette replacement is claimed by these gray views.

The original 163 source group names and weights are restored, and 307 split-edge
weights are interpolated. Newly authored garment weights are unassigned pending
explicit rig adaptation. No neck movement, 19-bone rig, Garage/gameplay leaning,
contacts or final appearance has passed.

The isolated CPU batch began 02:39:08 UTC with deadline 03:09:08 UTC. External
construction peak RSS was 153,993,216 bytes; Blender export peak 756,121,600 bytes.
No GPU, Metal, model job, global environment change or expensive bake occurred.
Settings, source guards, build/export and actual reimport records are preserved
with exact hashes in `frozen-manifest.json`. Runtime masters live under the lane's
`clean-construction/trial01/`, outside production assets. A materially different
next route requires actual cloth drape/true hood-bag panels or a NEW whole-hood
donor; it has not been attempted by this builder.
