# Apply the existing contact precision policy during construction

Finding: Actual60 stopped before cage fitting or raw save because its fixed left apex
measured2.5999972131103277mm against an exact2.6mm comparison. The difference is
2.786889672nm. The same pinned fullbody triangles and pair produce2.600004211mm
in the independent float64 CPU query; both agree within native float32 coordinate
precision. The healthy fixed endpoint measures6.945411675mm.

Constructor64 uses the already pinned20µm numerical contact tolerance for measured
fixed-pair and target-gap comparisons, matching independent saved qualification.
It keeps the measured endpoint eases as evidence and separately clamps prescribed
construction eases to at least nominal2.6mm. Fixed paired endpoints stay exact.
The analytic interval solver, original source sections, C2 map mathematics and
saved full-contact qualification are unchanged. No clearance or tolerance value
is reduced or expanded. Coarse healthy50 anchor selection is unchanged.

Validation: parent reproduces all15 existing CPU fixture groups and five additional precision
groups reproduce actual60 rejection, admit that actual case under the existing
policy, retain exact endpoints, keep all33 interpolated construction eases at
or above nominal, and reject the first representable value below the existing
tolerance boundary. Full source60 target preflight remains pinned; no broad
geometry preflight is repeated for this numeric-comparison-only change.

Limits: Source/input64 are frozen and unaccepted. This builder launched no Blender,
native job or commit. Parent construction, saved reopen, actual contact/tangent
qualification, original witness faces, distal integration and played full rider
review remain required. Frozen60 remains unchanged.
