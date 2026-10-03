# Source-file frame alignment — diagnostic only

Changing only the private rider wrapper x from -0.65 to0 removes the measured
650 mm displacement. Source GLB v3, all17local pose/morph values, source times,
actual Rookie bike and physics state remain identical to the negative control.
The legacy wrapper is correct for the normal physics adapter; no normal player
code is changed. The cloud-authored trajectory uses the retained source-file
frame, so this explicit diagnostic mapping is recorded separately.

The actual Garage aligned movie plays to completion muted:4.25s/17frames,
no errors. All17source world matrices match GLB track values within5.56e-16;
morph error zero. Capture harness repo60042670; actual game buildcb2e008e.
This is authored pose playback in the actual engine, not physics-driven riding.

At t=2s the grip socket point residual is below0.0002mm on both sides.
Sole socket offsets remain 91.076/41.620mm; these named socket points are
not the authored full shoe surfaces, and do not establish visible contact.
All real grip/shoe/saddle surface checks remain open. T/A underarm webs, hood,
cuff/normal faults, dense interpolation and physical iOS remain unaccepted.

Run capture with `--wrapper=source-file --step-only=1`; omit the wrapper flag to
reproduce the original negative control. Use verifier capture directory argument
`aligned-step01` to retain source-frame provenance separately.
Exact Library artifact IDs and versions are in `library-receipts.json`.
