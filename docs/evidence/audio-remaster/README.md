# Audio remaster evidence

Ask 193. The [manual audition](audition/index.html) compares the old score and
sound fixtures with the delivered remaster. Nothing auto-plays. The
[played Low Tide ride](ride-remaster.mp4) combines archived moving visuals
with newly rendered audio driven by the identical recorded input. The
[crash and restart mix](crash-restart-remaster.mp3) uses actual simulated
fault/restart events. Their provenance is in `played-mixes.json`.

## Scope and method

Wildshard Singleplayer supplied the local generation, semantic screening,
beat-aligned loop, mastering and lifecycle method. Rockhop uses fresh music
and sound prompts; no Wildshard audio is copied. Six MiniMax-Music3 scores
cover Menu, Map, Coast, Alpine, Quarry and Snowline. A title excerpt becomes
the recorded results sting. MOSS-SoundEffect adds five crowd/rider families
and four environment beds; authored synthesis remains the loading fallback.
Engine/drivetrain, eight contact materials, landings, crashes/debris,
countdown/checkpoint/restart/finish, menu controls and procedural music are
also remastered. Outdoor fallback beds now recognize the actual game zones.

The first generated bank exposed reduced-precision waveform amplitudes.
Float32 storage alone did not repair that. Final generation retains bf16
language/diffusion components but loads original waveform decoder weights
and executes waveform decoding at float32. Identical latent comparisons,
raw source hashes, prompts/seeds, actual duration, memory and framework
versions accompany the delivered manifests. Raw sources, saved music
latents, model weights and discarded takes stay outside git.

Music masters are measured after MP3 decode, with loops targeting -18 LUFS,
results -16 LUFS and true peak at or below -1 dBTP. Both physical channels
must pass the normal and 2112-sample-offset wrap checks. Effects use strict
CLAP family/negative qualification; environmental beds must lead their own
zone descriptions. Encoded peaks, atlas offsets and guarded loop seams are
checked. Generated environment sources are mono; stereo delivery is dual
mono, complemented by authored stereo wind.

## Runtime behavior

Slow music loads retain the previous cue and synthesized fallback until a
new source starts. Music/sample caches and reaction voices are bounded.
Pause mutes gameplay while recorded music continues; restart cancels delayed
reactions. Unavailable recordings leave synthesis active and can retry on
run/restart edges. The shared gameplay/music compressor bounds summed
levels. Hashed music and effect files use the permanent audio cache, with
old hashes pruned within their cue namespace.

## Measured validation

The isolated audio candidate passes typecheck, repository lint and the
production build (689,599 B player bundle gzip, below 700 KiB). All **95
sound/cache/decoder tests** and **13 pipeline regressions** pass. Across the
whole suite, **1,490 tests pass and two are skipped**. Serial execution
resolves two unchanged physics timing benchmarks that exceeded their bars
under parallel contention. The 17 store-build tests pass separately after
supplying the frozen export's build SHA environment variable.
[Validation provenance](validation.json) records the tested runtime hashes
and both initial failures and their corrected reruns.

All **12 delivered files** decode in Chromium 151 and WebKit 26.5, with
zero live AudioContexts, zero sample alignment offset, correlation above
0.9999997 and at most 0.000212 dB measured decoder gain difference.
[Native measurements](native-decode.json) include every reaction/loop window.
Stereo reaction delivery followed by a live mono average corrects the
576-sample WebKit priming offset found in the preliminary mono atlas.
All nine recorded families lead their intended semantic description;
these rankings remain proxies for human recognition.

[The same-input ride](c1-ride-events.json) clears Low Tide at **30.35 s**,
zero faults, finish hash `2bfe061963ffb058` and end hash `23adcf3b771bcd0a`.
Two renders produce byte-identical PCM and event data. Its results transition
follows the actual run-rule panel delay; the offline music assumes decoded
cues. [The crash witness](c1-crash-restart-events.json) contains an actual
fault and auto-restart. Both final encoded mixes peak below -6 dBTP.

[The headless cold-boot/clear/crash/restart probe](runtime-smoke.json)
clears the flat golden in 8.591666666667 s, reaches a real crash and returns
to riding at tick zero before `restart()` returns (0.12 ms in-page call;
2.82 ms command includes the crash replay and browser IPC). Cold boot is
1,262 ms in software Chromium. These are software lifecycle measurements,
not physical-phone latency or performance passes.
[Pause evidence](pause.json) holds physics/model state unchanged for 150 ms
and resumes in the input frame; both probes open zero live AudioContexts
and report no page errors.

[Sound fixture measurements](dsp-measurements.json) cover 35 before/after
WAVs and the fixed workload. Median DSP cost is 0.335 ms per 60 Hz audio
frame (previous 0.310 ms); this is a Node CPU proxy. The
[outdoor fallback check](dsp-outdoor-world-check.json) verifies appended
Coast/Alpine/Quarry IDs while preserving the five legacy remaster beds.
The seven scores total 3,609,435 B and five recorded SFX files 884,577 B.

## Limits

The ride's visuals are the archived baseline film, not a new graphics claim.
Its new audio is an offline audition proxy using delivered assets and model
envelopes; it does not record the native compressor or physical speakers.
Silent software-browser checks cannot establish taste, audible intelligibility,
phone mix, sustained physical-device performance or stranger attempts to
clear. Those listening/device judgments remain in HR-22; stranger play is
tracked separately by HR-21. The audio implementation lands directly on main and publishes through the
checked CI deployment, as the user requires; listening remains HR-22.
