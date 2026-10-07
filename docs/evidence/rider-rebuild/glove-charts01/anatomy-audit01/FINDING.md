# Actual mesh branches confirm bilateral pinky and middle-PIP placement defects

The audit derives finger branches from actual hand topology before consulting
joint or weight names. Hand-surface PCA supplies a distal scalar; crossing every
actual vertex critical level finds four disconnected long-digit components.
Their spatial ordering identifies pinky, ring, middle and index. An earlier
two-component split isolates the thumb while the other component contains all
four long-digit descendants. No heat-weight field selects these components.

The first four-component cuts occur 147.983 mm and 148.007 mm along the measured
distal axes from the right and left cuff centroids. Thumb separation occurs at
98.416 mm and 98.394 mm. The exact hand vertex sets, source faces and axes are
saved. Eight transverse actual-surface contours qualify per long digit and six
per thumb, 76 total. Each contour has at least 95 percent triangle support from
its independently identified branch. Its area centroid is inside the actual
hand. Source hand triangle IDs, exact intersected edges and edge fractions
remain available for every contour; no existing field defines these centers.

All 15 named segments per hand are then sampled at 33 fractions, 990 occupancy
queries total. The right pinky proximal segment has 19 exterior samples, with
maximum exterior distance 1.901 mm; the left has 18, maximum 1.898 mm. The right
middle PIP junction is 0.411 mm outside and the left is 0.595 mm outside. Adjacent
samples on both incident segments confirm these are segment-placement defects,
not only coincident endpoint bookkeeping. Other sampled segments stay inside;
finite samples do not prove continuous segment clearance.

The thumb labels explicitly distinguish `.01` metacarpal/CMC, `.02` proper
MCP/proximal phalanx and `.03` IP/distal phalanx. All rest frames have proper
rotation determinants, local Y agrees with the segment direction to native
float precision, and the current driver flex axes are perpendicular to their
bones. Those numerical facts do not establish anatomically appropriate roll,
opposition or played hand movement.

There are two separate corrections. First, center the actual bilateral pinky
MCP and middle PIP joints in their source geometry. Second, derive garment
surface roots from geometric web/branch separation, not from an assumption that
an MCP joint already lies inside an isolated surface cylinder. Increasing the
failed root-search range does not resolve these semantic distinctions.

The report includes transverse centerline proposals so their limitations are
visible. **Do not apply the proximal extrapolations as joint positions.** The
distal curve does not observe the proximal knuckle: some extrapolations span
41–62 mm; the thumb metacarpal extrapolation itself exits the skin. These are
counterexamples to silently deriving the entire skeleton from distal curves.
The measured middle-PIP surface centers are directly supported, but the pinky
MCP requires a local connected-palm/knuckle medial-section measurement.

Validation: the read-only NumPy/SciPy audit completes under `-W error` with all
76 retained contour centroids inside and no ambiguous winding in the 990 joint
samples. One initial source-code unpacking error occurred before any output or
geometry calculation; it was corrected, and the same audit then passed. No
native rig, body position, original FULL/FOUR field, driver, source glove or
geometry threshold changed. All proposed joint coordinates remain unaccepted.
