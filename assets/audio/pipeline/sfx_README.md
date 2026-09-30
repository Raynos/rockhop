# Rockhop recorded SFX

Wildshard's `gen_sfx_moss.py` and `sfx_build.py` supplied the local model,
MPS compatibility patches, semantic ranking, levels and encoded-audio workflow.
Rockhop uses new prompts, raw takes and a short shared reaction atlas.

Generation is serial with every other local ML job. Batch 1, local weights,
bfloat16, a measured memory-pressure gate and resume-by-existing-file remain.
Raw masters live outside the repository; no model weights are shipped.

```bash
cd ~/ml/music/sfx/MOSS-TTS/moss_soundeffect_v2
lockf -k ~/projects/localai/.model.lock env TORCHDYNAMO_DISABLE=1 PYTORCH_MPS_HIGH_WATERMARK_RATIO=0.5 PYTORCH_MPS_LOW_WATERMARK_RATIO=0.4 .venv/bin/python /Users/raynos/projects/games/rockhop/assets/audio/pipeline/sfx_generate.py --steps 50 --seeds 1,2 --max-takes 9 --vae-fp32 --out /Users/raynos/ml/music/rockhop-sfx-2026-09-30
lockf -k ~/projects/localai/.model.lock ~/ml/music/analysis/.venv/bin/python /Users/raynos/projects/games/rockhop/assets/audio/pipeline/sfx_build.py /Users/raynos/ml/music/rockhop-sfx-2026-09-30 --require-fp32-decoder
```

The nine families require eighteen fixed-latent model calls. Each batch
yields after at most nine new takes; rerun the identical command to resume.
Seed-first order covers every family in the first batch. WAV without its
provenance sidecar is incomplete and regenerated. All model runs use the
shared localai lock, including CLAP mastering. Wildshard's
100-step calls took about 46–70 seconds; the planned 50-step run has a
10–15 minute estimate plus model load and memory waits, zero API spend.
The actual times and MPS memory are recorded per take, never inferred.

Build uses the local `laion/clap-htsat-fused` semantic proxy; beds must lead the biome descriptions and rank at most two; crowds rank
at most three and rider grunts at most two. A music, spoken-words or silence
winner always rejects. Failed families keep the procedural voice and need a
focused retry. One-shot levels target −18 LUFS,
beds −26 LUFS; true peak constrains the gain and may lower those targets.
New delivery uses MP3: dual-mono 128 kb/s reactions and stereo 128 kb/s beds.
The reaction atlas averages back to mono before runtime panning. Native
WebKit left 576 priming samples in the preliminary mono MP3 atlas, while
stereo MP3 aligned with Chromium and ffmpeg; final native probes must
confirm zero reaction offset in both browsers.
The decoded MP3 must remain at or below −1 dBTP, with zero clipped samples.
Atlas offsets and bed loop ends are checked against decoded durations.
Beds use the actual best ten-second window, with 200 ms cyclic codec guards;
decoded wrap derivative ratio must be at most three and the 50 ms RMS step
at most 6 dB. A second qualified reaction take within 80% of the best score
becomes a deterministic variant in the atlas.
Every take's source SHA, seed, prompt, steps, model/code provenance and
semantic scores accompany the public files. Filenames are content hashed.
`--require-fp32-decoder` excludes all preliminary rounded-decoder sources
from production selection, even if their semantic score is slightly higher.
`--skip-clap` exists for a technical smoke build only.

The model card identifies [Apache-2.0](https://huggingface.co/OpenMOSS-Team/MOSS-SoundEffect-v2.0)
and the code has the same [license](https://github.com/OpenMOSS/MOSS-TTS/blob/main/LICENSE),
checked 2026-09-30. Those are model/code licenses; weights are not redistributed.
Generated audio carries clear model attribution and provenance.

`SamplePlayer` joins the unlocked context; it opens none itself. It loads
one reaction atlas and at most two decoded environmental beds. Pending,
failed or unavailable samples leave procedural fallback. Six reaction
voices bound overlap; restart clears delayed reactions; master mute and
disposal hard stop voices. Loaded beds replace ambience only while the
run's bed is active. Runtime integration remains silent under webdriver.

Objective scores and loop deltas do not certify natural human voices,
absence of intelligible words or a perceptually clean seam. Review played
clips plus physical iPhone Safari playback before treating them as passed.

New MP3 assets need the native headless decoder harness after generation:
FFmpeg offsets are a reference, not a WebKit alignment claim. Parent
measures each declared reaction window and loop in both native engines.
Only raw/local review uses WAV. Build replaces its manifest/provenance and
never deletes unrelated assets. Original AAC before-evidence stays intact.

Resource gate follows the current shared anonymous-memory policy rather
than Wildshard's historical 8 GB swap threshold. Before MOSS load it requires
normal pressure, anonymous + 22 GiB reserve below 70 GiB and no other process
over 15 GB. The reserve exceeds Wildshard's measured 19.8 GB driver footprint.
Between takes the loaded model already counts in RAM; reserve becomes zero
and only this worker is excluded from the other-process check. A failed gate
exits 75 and releases its own model/lock; it never evicts another service.
Gate snapshots travel in every generated take's provenance.

Initial 18-take screening accepted all five reaction families and snowline.
Coast was rank 4; alpine/quarry were rank 2 but the snowy-wind description
led their biome competitors, so all three were rejected. Focused seeds 3/4
use `sfx_retry_jobs.json` for clearer surf, birdsong and industrial-fan cues,
plus an alternate nonverbal small-group cheer. Scoring still uses the
original descriptions and strict bars. Qualified sources remain candidates
when the bank is rebuilt; rejected sources remain documented fallback.

MOSS returns mono source PCM. The 128 kb/s two-channel bed delivery is dual
mono; it is not an original stereo field recording. The live procedural
helmet wind keeps its existing spatial layer. Native engine decoding and
human listening remain separate checks from the model/FFmpeg proxies.

The inherited decoder ran under MPS bf16 autocast, despite an upstream
CUDA-only float32 scope. Its waveform amplitudes occupy the bf16 grid,
including isolated final-Tanh values rounded to full scale. Those counts
alone do not establish hard clipping. Changing WAV storage from PCM16 to
float32 preserved the same rounded model values and did not fix precision.
`--vae-fp32` keeps bf16 diffusion but explicitly disables MPS autocast for
the DAC waveform decoder and writes float32 WAV. The original DAC checkpoint
stores all 298 tensors at float32. The final renderer reloads that component
directly from the checkpoint at FP32, retaining its original weight values.
Diffusion remains bf16. After a bf16 comparison, production decoder weights
are reloaded again so the reference cannot irreversibly round them.

A preliminary pilot with bf16-rounded weights cast upward measured 2,959 versus 143,811 unique waveform
values in 144,000 samples; RMS difference was .002906, relative SNR 44.87 dB.
Only .00347% of FP32 output values remained on the bf16 grid. Driver memory
was 22.08 decimal GB, within the 22 GiB load reserve, with normal pressure.
`--compare-decode` additionally decodes the identical first-take latent tensor
through both precisions and records its SHA, grid fractions, error and counts.
The preliminary direct comparison with those rounded weights measured 2,967 versus 143,825 unique values, bf16-grid
fractions 1.0 versus .0000069444, RMS error .00303412 and relative SNR 44.49 dB.
Its driver footprint was 22.64 decimal GB, still below the 23.62 GB reserve.
Both decodes used latent SHA `b00fe678411b79e6805163f7ef910737cee6bc90fe61b1105a838af7c04357bf`.
Those are preliminary precision measurements; the final selected-take
provenance records a separate comparison using original FP32 decoder weights.
Selected sources are rerendered explicitly, never the entire candidate pool;
prior masters remain archived locally under `before-float/` by SHA.
No old delivered assets are removed while replacements are being qualified.

The final original-weight identical-latent check measured 2,967 versus
143,811 unique values, RMS error .00346484 and relative SNR 43.35 dB.
FP32 output occupied the bf16 grid at .00347%; its peak was .999427.
It used the same latent SHA above and reloaded original FP32 weights
before production decode. Final selected-source metadata contains the full
measurement; full-scale sample counts remain descriptive, not a clipping verdict.

Final delivery qualifies all nine families at semantic rank one and totals
884,577 bytes. Chromium 151 and WebKit 26.5 decode every final reaction and
bed at zero alignment offset; measured gain error stays below .000212 dB.
The evidence and manual audition remain under `docs/evidence/audio-remaster/`;
human recognition and phone balance remain HR-22.
