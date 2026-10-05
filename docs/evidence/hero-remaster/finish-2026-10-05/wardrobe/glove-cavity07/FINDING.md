# The secondary cuff boundary belongs to one isolated retained triangle

Read-only graph explanation of the proposed glove-cavity05 mask. Original
source/mask arrays remain byte-identical. No face removal, surface construction,
fit, skin, model, native Blender or render job occurred.

The hypothetical retained face adjacency graph has exactly two components.
The main component contains 14,543 faces, 7,306 vertices and 21,850 edges, Euler
characteristic -1; it owns the 71-edge cuff-area boundary. The other component
contains only original triangle 5167, three vertices and three edges, Euler +1;
it owns the secondary three-edge boundary shown white in the classification film.

In the unmodified source graph, triangle 5167 neighbors triangles 5087, 5417 and
5250 across its three edges. All three neighbors lie in the proposed candidate
mask. Triangle 5167 is retained because none of the five cavity-anchor or five
external-view first-hit tests selected it. It has no protected distal membership.
Its centroid is approximately source (-0.2964,-0.5448,+0.0761).

Thus the three-edge loop is the border of an isolated retained source face,
not another mouth on the main component. This explains a limitation of visibility
sampling; it does not grant semantic permission to remove that face, any of the
209 ambiguous faces or the whole proposed lining. The main component's topology
also does not establish palm/finger enclosure or intended rim/exterior scope.

`graph.json` records exact neighbors, component topology, boundary incident
face IDs and source/mask hashes. The ignored graph contract preserves every
source face row and its predicted retained component ID, with original arrays.
Root alone interprets the previously played source classification film and
approves any future scope. The removal mask remains unadmitted.
