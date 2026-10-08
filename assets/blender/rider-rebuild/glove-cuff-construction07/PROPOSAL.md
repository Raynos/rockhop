# Inspect the selected cuff layers before reconnecting them

This directory is an inspection handoff, not a reconstructed glove. The actual
cuff06 crossing is sufficient to retire its deformation. Neither a fixed-frame
normal dot nor this inspection proves the original source globally inverted.

Read-only NumPy inspection of both current cuff05 guides finds 8,000 vertices,
16,000 triangles and 24,000 edges, each incident to two faces. The source is
closed and has Euler characteristic zero. That alone does not identify its
physical layers. Its immutable source-Y sections have these loop counts:

| Source Y | Loops | Intersected-edge counts |
| --- | --- | --- |
| −0.52 | 1 | 184 |
| −0.58 | 2 | 181, 122 |
| −0.65 | 2 | 175, 118 |
| −0.70 | 3 | 174, 123, 19 |
| −0.75 | 2 | 245, 34 |
| −0.80 | 2 | 212, 37 |
| −0.95 | 2 | 87, 59 |

The original dorsal and palm views show the selected cuff opening, wall and
strap/rib details. The section components merge or terminate within this region.
Their meaning cannot be assigned safely from vertex Y or radius alone. Joining
two guessed section loops would risk connecting an inner layer to an outer
layer or removing selected strap geometry. These planes are diagnostics only;
they are not proposed reconstruction cuts.

The next required inspection is the actual fitted left and right control
surface together with the current sleeve, wearer, full cuff skin fields and UVs.
The parent can run `dump_current.py` once with Blender under the shared CPU2 lease.
It opens the pinned engine05 master and writes only a fresh ignored inspection
directory. It performs no bind, modifier evaluation, geometry edit, render or
native save. The arrays retain native vertex/triangle ancestry and actual world
transforms. Ordered section loops retain exact source edges and interpolation
fractions, including their fitted world positions. Anatomical edit IDs and good
lip anchors are explicit. Dense cuff arrays include actual corner UVs and every
authored skin contribution. The broad sleeve/wearer crop is for inspection only.

After inspecting these arrays, identify the outer wall, inner return, cuff lip
and strap connections in the selected source. Choose a connected physical patch
whose boundary does not cross a preserved hand feature. Retain usable existing
edges and construct circumferential rows only where the wall needs rebuilding;
axial and tangential displacement are allowed. Independently fit each hand to
its actual sleeve. Check welded connectivity, nondegenerate elements, actual
self-intersections, local folds and sleeve clearance before any dense transfer.

If the dense cuff itself must be reconnected, identify the changed local faces,
UV interpolation and skin-field ancestry honestly. A fresh local correspondence
may follow the passed control surface. Keep original fingers, palms, pads, ribs,
major strap appearance, original 4K materials, shared75 rest, other five parts
and equipped body mask. Parent moving review remains the art authority.

Validation: both Python files parse; the section helper was exercised against
the pinned existing left and right guide arrays, reproducing the counts above
without writing meshes. The Blender inspection has not been run. No corrected
cuff, correspondence, native or accepted art is claimed.
