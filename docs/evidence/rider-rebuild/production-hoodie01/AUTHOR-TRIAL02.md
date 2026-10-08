# Hoodie grid operation created zero faces

Actual author02 exits1 after1.629 seconds. Its 72-vertex left boundary reaches a Grid Fill call reporting FINISHED, but actual polygon-cycle diagnostics count zero added faces and twelve selected existing triangles. The correction proves selection state was misleading; it does not produce an authored patch.

The selected proportional fit remains saved, SHA `d04701f0c3fdaa270e8a30c62da7c707a1a9ed99e466003f4bd3cddc1fa655b2`. No completed rigged hoodie or bake exists. The next API correction must select the actual boundary in Edit Mode through BMesh and witness real returned/new faces, preserving the existing fit. No shape failure is established by a zero-face operation.

Validation: parent reviewed exact terminal log and zero-face diagnostics, rehashed the saved fit, and copied receipts/worker without alteration. Shape controls/source4bd21f23 unchanged.
