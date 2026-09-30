# Current native map-to-ride handoff

Same clean debug bundle **3f6b5662db973f87aa61c02088911e3f2bb7b00c**
as the [twelve-course native gate](../20260930-200644/README.md).
Command under shared GPU lock: `TRIALS_BROWSER_BACKEND=metal pnpm exec
tsx harness/native/map-flow.ts`. Android emulator stayed off.

[Report](report.json), [output](output.txt), [actual silent iOS flow](ios-clip.mp4)
and [clip index](ios-sheet.jpg) show Menu→3D map→C1→map→Menu.
Both web Metal and iOS pass: map alone owns one active context; gameplay
restores before C1 riding and again on map exit. No crash/error or
AudioContext is reported. Parent reviewed consecutive actual transition
frames, including returned map and final Menu.

Limits: simulator/context compatibility only. This does not establish
physical touch/pacing, map art fidelity or twelve-course human completion.
