# Proposed parent edits recompute six unchanged descendant matrices

The read-only diagnosticf22d6d14a4f07785c5dcb40d3a2a94b89f7c2e28451df554f0058ff3ad4d9091
loads the pinned original twice in one serialized60second/two-thread process.
The guard exits0 after1.59seconds. No bind, master save, export or field edit runs.

The no-op edit roundtrip preserves all75head, tail, matrix, parent, connection
and deformation records exactly, both native float32 bytes and promoted double
bytes. Applying only the proposed four heads/four tails/eight rolls changes
14native rest records. The physical endpoint scope is exactly as intended;
every other native head and tail remains byte-identical.

Six descendants retain exact edit-entry/edit-exit heads, tails, matrix and roll,
but their resulting `Bone.matrix_local` changes when Blender recomputes the
changed parent hierarchy:

| Descendant | Largest matrix component delta |
| --- | ---: |
| DEF-f_middle.03.L | 2.980232239e-7 |
| DEF-f_pinky.02.L | 2.384185791e-7 |
| DEF-f_pinky.03.L | 1.788139344e-7 |
| DEF-f_middle.03.R | 1.639127732e-7 |
| DEF-f_pinky.02.R | 4.172325134e-7 |
| DEF-f_pinky.03.R | 4.172325134e-7 |

This establishes the native01failure cause as actual descendant matrix
recomputation after changed parents. The first failing middle DIP record did
not acquire a new endpoint or authored roll. A new derivative must explicitly
record all14actual native rest changes and derive controls/inverse binds from
that authority; it cannot claim eight-frame byte preservation. No blanket
tolerance relaxation or anatomical acceptance follows from these measurements.

`edit-roundtrip.json` preserves every75source/result record, component deltas,
source/result float32 byte strings and actual edit records. The NPZ preserves
source/result float32 and double arrays independently. `guard.json` and
`worker.txt` retain actual command and terminal result. Original geometry,
UVs, polygons, source IDs and native fields remain exact after each load; the
original master SHA remains26cd01d4ba02be3fbf0f3a5b290c99445ef34d7d18d90012d2ef44913ef06d1d.
