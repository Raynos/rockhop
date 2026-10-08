# Glove checkpoint scratch lifetime

Finding: The unchanged first glove checkpoint hit the existing anonymous-memory
guard during the right glove and saved only left ancestry. Its caller retained
completed left construction scratch while creating right scratch, and would
also build unused full hoodie scratch before the glove-only save callback. The
new wrapper releases completed glove scratch after native finish and substitutes
an unchanged-hoodie object sentinel. It changes no construction method, source,
geometry, skin, maps, rig, profile, threshold or Blender datablock.

Validation: Five source files parse. Four fixtures execute the actual lifetime
helper: successful finish releases scratch, returned arrays/report survive,
failed finish retains diagnostics and propagates failure, and the hoodie
sentinel bypasses allocation without changing the native object. Pins and the
fresh invocation are in [the handoff](../../docs/evidence/rider-rebuild/selected-sleeve-rebuild28/gloves-memory02-handoff.json).

Limits: Native retry and measured peak-memory reduction remain unrun. The
original CPU2, 300-second and 65 GiB anonymous-memory guards remain required;
no saved candidate or passing geometry/art claim exists from the failed run.
