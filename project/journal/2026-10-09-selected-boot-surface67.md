# Joint boot vertex and face closure

Finding: The full-source CPU tree compares all 26,528 native63 queries in
4.18 seconds. Recorded native dots reproduce exactly; shared-edge/vertex
bearing checks catch all 94 new-face native failures and one additional
edge ambiguity. The constructor now requires complete vertex and face
censuses on every immutable-source reduction, adding all failing fans at
once. Initial constraints protect 931 source fans.

Validation: Six CPU fixture groups pass, including brute-force nearest
comparisons, all 78 tiny positive source facets and no-progress rejection.
Synthetic proof mutation checks pass; actual proof has not run. See
[handoff](../../docs/evidence/rider-rebuild/selected-boot-surface67/source-handoff.json).

Limits: No simplifier or Blender job ran. Native67 proof, actual joint fixed
point, independent native qualification, PBR bake, motion and allocation
remain required. The 1 mm/0.25 thresholds and selected source are unchanged.
