# Fresh adult source checkpoint

Finding: Blender 5.2.1 and installed MPFB 2.0.17 generate a fresh adult
MakeHuman body with native facial, hand and anatomical rig topology.
No rejected rider geometry is imported. This establishes the source for
ask 214's complete restart, not a complete accepted rider.

Validation: Actual headless Blender generation succeeds: 19,158 vertices,
18,486 source polygons including helpers, 163 native bones. Recipe hash
and core base.obj SHA match the
[frozen report](../../docs/evidence/hero-remaster/restart/whole-rider-v1-fresh-base.json).
The local ignored .blend is saved.

Limits: Adult macro selection is not anatomy, dressed silhouette or in-engine
acceptance. The native rig must still be fit to the game's 19-bone contract,
and the complete dressed candidate requires played Garage/ride judgment.
