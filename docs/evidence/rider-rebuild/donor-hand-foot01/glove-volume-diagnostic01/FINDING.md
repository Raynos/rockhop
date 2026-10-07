# Thumb bone influence does not identify the donor surface chart

All 36 section profiles were measured on the exact failed source registration.
The source palm/wrist and four long fingers stay inside the original 2.5 ease
limit. Only three proximal thumb stations fail: required scales 5.190, 3.206 and
2.663. At the first station the selected thumb lateral radius is 7.738 mm, while
samples assigned from thumb bone influence extend 36.657 mm from that centerline.

This is evidence of a surface-domain mismatch. The target thumb metacarpal
influences the broad thenar/palm surface; the donor's thumb label is a distal
connectivity chart whose original classification explicitly leaves proximal
palm/web attachment unclassified. Expanding the entire thumb 5x would copy that
classification error into the selected exterior. The proposed correction must
separate thenar/palm from digit using actual MCP geometry, while keeping every
original deformation influence. Source geometric section stations are not
proven anatomical joints; their registration also requires explicit review.
The [source station readback](thumb-domain-review.json) records that the first
isolated donor thumb section was mapped to the target metacarpal head. The
actual MCP lies 52.336 mm downstream. This is an anatomical mapping hypothesis
to review, not proof that a donor section center is an annotated joint.

Validation: a diagnostic of frozen recipe 3c67ed27 exited 0 in 1.954 s and recorded
all region/station/source-radius/skin-radius/scale witnesses before stopping.
The original production limit remains 2.5, original wearer fields/positions are
unchanged, and projection, cavity construction and atlas bake did not execute.
No production candidate was retried or saved.
