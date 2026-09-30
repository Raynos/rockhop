# Rockhop audio remaster

Ask 193, 2026-09-30. Parent owns audio integration and judgment. Course,
physics and hero agents keep their existing paths in the single checkout.

## Direction and reference

Use Wildshard Singleplayer's local candidate, provenance, vocal screening,
detected-beat loop, mastering and runtime lifecycle workflow. Author new
Rockhop music and sound; preserve the sunny outdoor expedition identity.
MiniMax Music 3 is the retained local music model. ACE-Step stays retired.
Raw renders and model weights remain outside this repository. Generate one
model at a time under the machine-wide `~/projects/localai/.model.lock`
and existing memory gate. Music batches yield after two takes; no playback
during testing.

## Execution

- [x] Render two seeded takes for Menu, Map and all four biome ride cues.
- [x] Rank cue fit and vocal contamination, cut on detected beats, master
  new hashed MP3 files and a finish sting from the selected score.
- [x] Remaster every procedural SFX family: bike engine and drivetrain,
  eight tyre/contact materials, landing/crash/debris, countdown/checkpoint,
  restart, finish, crowd, rider voice, environment and menu controls.
- [x] Deliver qualified recorded crowd/rider/environment layers with procedural
  fallback and bounded memory/voices (all nine families qualify).
- [x] Repair loading transitions, interruption and restart/disposal paths;
  automated browsers must never create an AudioContext.
- [x] Verify decoded peak/loudness/seams, seeded offline SFX output, mute,
  rapid scene changes, cold boot, clear, crash and restart in silent harnesses.
- [x] Deliver an audition surface with before/after excerpts and actual
  played-run mixes, never auto-playing audio on the user's machine.
- [x] Land only audio-owned changes directly on main with provenance,
  journal and checks; human listening remains HR-22.
- [x] Push main and request the checked CI deployment.
  The workflow must pass and production version SHA must match before the
  parent reports the audio shipped.

## Decoder precision correction

The first full bank revealed bf16 amplitude quantization despite float32 WAV
storage. Generation retains bf16 diffusion/language components; selected
sources were rerendered with original waveform decoder weights in float32.
A bounded same-latent comparison records precision, error and memory;
semantic, mastering and native-decode gates passed again on the final sources.
Local music latents now persist outside git for decoder-only recovery.

## Acceptance and limits

All seven music slots have authored source/provenance; Snowline
does not reuse Coast. Loops target -18 LUFS (within 0.5 LU after decode),
decoded true peak <= -1 dBTP, no internal dead air, and a continuous seam
under both normal and 2112-sample decoder-offset windows. Assets stay
within the existing 15 MiB music budget. Shared music/engine balance leaves
traction and impact feedback readable. Loaded samples have silent/mute,
restart and disposal coverage; unavailable samples leave the game playable.

Physics code and input recordings are unchanged by this audio round.
Measurements cannot establish musical taste, intelligibility on the user's
phone or a stranger's attempts-to-clear. Those judgments remain explicit
human/device gates, recorded in the human queue without blocking production
of a reviewable audio candidate. No release readiness claim follows from
offline audio or software-browser success.
