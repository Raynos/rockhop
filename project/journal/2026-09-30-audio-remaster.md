# Audio remaster — 2026-09-30

Finding: The old bank reused Coast for Snowline and lacked recorded crowd,
rider and outdoor layers. Seven original MiniMax score cues, qualified MOSS
layers and rebuilt procedural families now share bounded scene, pause,
restart, load/retry and cache behavior. Float32 waveform decoders repair
amplitude quantization; a stereo reaction atlas avoids WebKit’s 12 ms mono
MP3 priming offset and is averaged back to mono for live panning.

Validation: Final candidate checks are recorded in
[the evidence](../../docs/evidence/audio-remaster/README.md). Typecheck, lint, production build, 95 audio tests and 13 pipeline tests
pass. The whole suite passes 1,490 tests with two skipped after serial timing
checks and the store-build export environment correction. All twelve
assets decode in Chromium and WebKit with zero alignment offset and zero
live AudioContexts. The same Low Tide input clears at exactly 30.35 s with
finish hash `2bfe061963ffb058`; two offline renders are byte identical.
Played clear and fault/restart mixes accompany manual before/after controls.
All nine recorded SFX families qualify; delivered audio totals 4,494,012 B.

Limits: Software-browser, semantic and offline mix proxies cannot establish
musical taste, phone speaker balance, physical-device performance or
stranger attempts-to-clear. Human listening/device acceptance remains
[HR-22](../human-in-the-loop/QUEUE.md); the user requires landing and checked deployment directly from main.
[Ask 193](../../docs/tasks/ASKS.md) and
[the indexed plan](../../docs/plans/sol-6.1-2026-09-30-AUDIO_REMASTER.md)
record delivery and remaining acceptance.

Main landing correction: The user requires main-only work. The temporary
review branch is retired after landing. Audio decoder regressions declare
FFmpeg/FFprobe in CI; four committed Alpine tooling lint errors are repaired
without changing the generated forest or other agents’ pending art.
