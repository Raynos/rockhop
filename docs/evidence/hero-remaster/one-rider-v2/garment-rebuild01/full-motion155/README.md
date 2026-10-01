# Full actual C19 motion reconstruction — round155

The CPU reconstruction reproduces all480 actual played fresh34 riding states,
using the retained physical COM/lean/contact driver and explicit19bone adapter.
Every bone's world position, world quaternion and bike-frame position is checked
against the previously captured in-engine side film. Maximum world-position error
is5.83e-14m; quaternion-component error4.50e-14; prior four-key matrix delta8.13e-14.
All frames use physical posing; the recorded lean range includes both−1 and+1.

Five primitive matrix histories are byte-identical, and their19bone orders are
retained. Float64 little-endian layout is frame×bone×column-major4×4. Private files
are in LocalAI `one-rider-v2/garment-rebuild01/full-motion155/`; report.json retains
hashes, source/bundle dependency hashes and all480 parity receipts. Raw GLB bytes
are unchanged. The geometry/texture source has not been edited or promoted.

Run the owned `dump.mts` with `pnpm exec tsx`. Frozen matrix outputs cannot be
overwritten; a reconstruction requires a new explicitly owned output directory.
The reporter provenance fields were enriched after capture without changing any
matrix bytes. The consuming full-motion cuff audit was rerun with that manifest.

This is a transform-validation foundation, not a new moving render, appearance
score, sitting/Garage action, surface contact or device pass. Socket booleans do
not certify visible grip/sole contact. New construction must still be judged in
matched rendered clips and the actual game before acceptance.
