# Raw rider comparison renderer

Finding: a shared Blender diagnostic makes exact-yaw source comparisons before
rig fitting. Uniform normalization, common lights/camera and explicit material
changes keep body defects visible; original exports are not rewritten.

Validation: headless Blender5.2.1 loaded Hunyuan01 workingGLB, rendered full
body/front without clipping, and recorded sourceSHA/camera metadata. Cutout
stage preserved all five exact reference bytes. Hunyuan five-body batch passed;
TRELLIS generation passed and reduced review exports are being frozen.

Limits: raw turntables are diagnostic evidence, not gameplay acceptance.
Metallic0 diagnostics differ from native PBR; source remains untouched. Installed
Pixal smoke is feasible but the rider canary is still pending. TRELLIS NPZ holds
decoded geometry/voxel attributes, not sampler latents.
