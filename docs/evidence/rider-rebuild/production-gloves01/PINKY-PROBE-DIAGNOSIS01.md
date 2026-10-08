# Proximal pinky probe rejected a real exit hit

The frozen source and all eleven input pins remain unchanged. This diagnosis
uses cheap direct Möller–Trumbore triangle arithmetic on the actual target and
exact reconstructed nonuniform scaffold; no Blender run or source repair ran.

The failed plus ray starts at the bone midpoint plus60mm along the authored
radial direction. Complete1484tri and weight-filtered276tri both intersect the
same face1313 at69.349500mm, point
`[-0.4277359124,-0.0569676444,0.8381125633]` meters. Its normal dot requested
outward is **-0.962882809**. The author rejects that exit hit as a “miss.”
The reverse ray intersects the same face at50.650500mm with normal dot
**+0.962882809**, which passes the facing condition.

The extended same geometric line enters a complete-hand interval at face508,
5.731421mm before the original plus-ray origin, and exits at face1313,
69.349500mm after it. The original origin is inside that interval. The broader
line also intersects an earlier separate index interval. Thus this cross-digit
probe does not start outside an isolated proximal pinky tube. Its normal-facing
assumption is false near the connected palm/web. It does not establish that the
bone itself is wrong. Weight filtering excludes the upstream entry geometry,
but does not drop the identical forward exit hit that caused this failure.
A skin coefficient threshold cannot define the finger's production surface.

A narrow conventional repair is to tailor the rounded proximal pinky panel on
actual dorsal-surface landmarks, with an explicitly modeled outline and width,
keeping the native bone/rest unchanged. Dorsal stencil probes on the unchanged
skin at across offsets -4,0,+4mm hit faces599,1164,425 respectively, with outward
normal dots0.750245,0.988321,0.983570. These provide actual geometric support for
an initial8mm-wide panel strip at this station; they do not certify its full
length, glove clearance, finger identity or movement. The broad cross-palm
plus/minus width probe should not be used to invent an isolated finger radius.
The coefficient-filtered BVH should not own panel surface queries; keep semantic
coefficients for skinning and tailor each actual geometric panel separately.

The parent chooses any repair after inspecting this evidence. No rerun,
weight-derived replacement chart, correspondence solver or bone move is proposed.
Exact hits and limited dorsal samples: `pinky-probe-diagnosis01.json`.
