# Preserve selected face UVs in the production derivative

Finding: The actual selected face, cheek and neck already use 1024, 1024 and
256 pixel albedo maps. Keeping their UV charts and four original materials
avoids re-atlasing the face and uses approximately 11 MiB including RGBA8 mip
chains, inside the planned 60 MiB rider texture allowance. A skin-only wrapper
reuses the frozen geometry/FOUR-field construction while requiring exact
material/UV chart boundaries, UV coverage and original packed material/maps.
The normal family bake now rejects explicitly preserved material families.

Validation: Wrapper, math, fixtures and bake source parse. UV fixtures accept
an equivalent retriangulation and reject scaled charts, changed material
ownership and reversed winding. Exact mip arithmetic passes. Frozen production
input and bilateral-boots geometry source are unchanged; pins and actual GLB
metadata are in [the handoff](../../docs/evidence/rider-rebuild/selected-skin-preserve29/source-handoff.json).

Limits: No actual derivative or bake ran. Planned rider allocation is about
59 MiB and ten material primitives; native material/UV checks, real GPU memory,
whole-scene timing, moving appearance and device qualification remain pending.
