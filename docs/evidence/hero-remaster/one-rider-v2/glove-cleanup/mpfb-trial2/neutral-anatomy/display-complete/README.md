# Complete neutral anatomical cages — parent review pending

[Six-view board](neutral-anatomy-board.jpg) shows both fresh neutral hands
from front, profile and rear in matched gray lighting. Each cage retains all
**1,656 original polygons**, including the two wrist-cut n-gons absent from
the earlier tri/quad-only export. Its 1,668 vertex positions match the frozen
partial NPZ exactly within 10 nm; native weights are copied unchanged and
sum to one within 1.3e-7. Each has one intentional 22-edge open wrist loop,
with no additional nonmanifold edges. The new render meshes have no inherited
shape keys and preserve the original neutral anatomy.

The original unposed full-body source, canonical neutral master and both
partial NPZs remain untouched. Complete NPZs use flat polygon indices and
polygon offsets, preserving every polygon without pickled arrays. Native
bone names and dense per-vertex weights are retained in both complete NPZs
and Blender vertex groups. The complete display master and NPZs are in
`/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/glove-cleanup/mpfb-trial2/neutral-anatomy/display-complete/`.

Six frames were rendered on Cycles CPU with four threads. Subdivision level 1
is a nondestructive display modifier. The neutral smoothed display has zero
nonadjacent BVH overlap candidates; shared-vertex triangle neighbors are
excluded. That scope establishes no gripping pose, deforming collision or
actual bike contact pass. This is neutral model evidence for parent judgment,
with no bake, glove texture detail, sewn neutral body or final runtime rig.
