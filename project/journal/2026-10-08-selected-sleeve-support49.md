Finding: Frozen sleeve28 support is selected before affected triangles add
their complete corners and centroids. Component47 fails at its first solve,
before any displacement, because at least one deficient constraint has zero
effective active interpolation weight. The logged global minimum does not
identify that sample. A read-only wrapper captures the exact first-solve
state and reports native ancestry, source inward membership and full-body
nearest-face/skin labels without changing the frozen input or fit.

Validation: Five bounded CPU fixture/source checks pass, including an exact
field28 unsupported vertex/centroid reproduction and confirmation that no
projection or mesh mutation occurs. Source handoff:
`docs/evidence/rider-rebuild/selected-sleeve-support49/source-handoff.json`.

Limits: Actual parent-guarded diagnostic execution remains pending. No
support expansion, ease change, native asset or moving-art pass is claimed.
