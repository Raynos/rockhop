# Reproducible rejected whole-rider source

Finding: First Blender exports depended on set ordering for material-majority
ties. Freeze that rejected recipe and make semantic ties deterministic. New
revision v1a regenerates from pinned original rig and installed MPFB core;
no hidden old .blend or baseline GLB is required. Art remains rejected.
[Source recipe](../../assets/blender/hero-remaster/rider/restart-v1/README.md).

Validation: Builder repeats full regeneration twice. Full d0a1533a exactly
reproduces the first shape; LOD 92a009ad is a newly named deterministic
revision. Both preserve 19 bones/four sockets/six clips. Evaluated source
contains exactly 13,380 body vertices and no helpers. Runtime duplicate
correspondences have zero gap through seven cases; glove surface is 15.5 mm
from the grip, above the 10 mm target. Source syntax/scoped lint pass.

Limits: Technical continuity does not accept the complete person or visible
contacts. Parent has rejected shoulders/chest, eyes and palms. Original
first LOD e8f426 remains frozen for the captured review, not claimed as a
reproduced deterministic export. No public asset or physical-device pass.
