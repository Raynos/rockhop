"""Rockhop local SFX generation, adapted from Wildshard gen_sfx_moss.py.
No remote API calls; local weights only. Run only after other ML jobs stop.
Each call computes a fixed 30 s latent even for short effects. Resumable.
Raw WAV and source metadata belong outside version control.
"""

from __future__ import annotations

import argparse
import gc
import hashlib
import json
import os
import re
import subprocess
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
W = Path(os.environ.get("MOSS_WEIGHTS", Path.home() / "projects/weights/manual/OpenMOSS-Team/MOSS-SoundEffect-v2.0"))
MOSS = Path.home() / "ml/music/sfx/MOSS-TTS"
METER = Path.home() / 'projects/localai/bin/mem-gb.sh'
MEMORY_LIMIT_GIB = 70
LOAD_RESERVE_GIB = 22  # Wildshard's 153 MOSS takes: 19.8 decimal GB driver; conservative headroom.


def pending_takes(families: dict, seeds: list[int], out: Path, selected: list[str], max_takes: int, rerender: set[tuple[str, int]] | None = None) -> list[tuple[str, int, Path]]:
    """Seed-first batches cover all families before spending a second take."""
    takes = []
    for seed in seeds:
        for family in selected:
            dest = out / "moss" / family / f"{seed}.wav"
            if dest.is_file() and dest.with_suffix('.json').is_file() and (family, seed) not in (rerender or set()):
                continue
            takes.append((family, seed, dest))
            if len(takes) >= max_takes:
                return takes
    return takes


def memory_gate(reserve_gib: float = 0) -> dict:
    """Current shared policy: pressure normal, projected anonymous <70 GiB, no other >15 GB process.

    Historical allocated swap is not current pressure. A failed gate exits 75,
    releasing our model lock and any loaded model; completed takes remain resumable.
    """
    anon, wired, free = map(float, subprocess.check_output(['bash', str(METER)], text=True).split())
    pressure = int(subprocess.check_output(['sysctl', '-n', 'kern.memorystatus_vm_pressure_level'], text=True))
    top = subprocess.check_output(['top', '-l', '1', '-o', 'mem', '-n', '5', '-stats', 'pid,command,mem'], text=True)
    others = []
    for line in top.splitlines():
        match = re.match(r'^\s*(\d+)\s+(.+?)\s+(\d+(?:\.\d+)?)G[+-]?\s*$', line)
        if match and int(match[1]) != os.getpid() and float(match[3]) > 15:
            others.append({'pid':int(match[1]), 'memory_gb':float(match[3])})
    snapshot = {'pressure':pressure, 'anonymous_gib':anon, 'wired_gib':wired, 'free_gib':free, 'reserve_gib':reserve_gib, 'other_over_15gb':others}
    print(f'[gen_sfx_moss] memory gate {json.dumps(snapshot)}', flush=True)
    if pressure != 1 or anon + reserve_gib >= MEMORY_LIMIT_GIB or others:
        print('[gen_sfx_moss] memory unavailable; yielding lock with exit75, do not evict other services', flush=True)
        raise SystemExit(75)
    return snapshot


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--seeds", default="1,2")
    ap.add_argument("--families", default="")
    ap.add_argument("--steps", type=int, default=50)
    ap.add_argument("--cfg", type=float, default=4.0)
    ap.add_argument("--out", required=True)
    ap.add_argument("--jobs", default="sfx_jobs.json", help="Rockhop families file in this folder")
    ap.add_argument("--max-takes", type=int, default=9, help="New takes per model batch (1..9); rerun to resume")
    ap.add_argument('--rerender', default='', help='Explicit family:seed pairs to replace, preserving old masters by content hash')
    ap.add_argument('--vae-fp32', action='store_true', help='Disable outer bf16 autocast only during DAC waveform decode')
    ap.add_argument('--compare-decode', action='store_true', help='Compare both decoder precisions on the identical first-take latent tensor')
    args = ap.parse_args()
    if not 1 <= args.max_takes <= 9:
        ap.error('--max-takes must be between 1 and 9')
    if args.compare_decode and not args.vae_fp32:
        ap.error('--compare-decode requires --vae-fp32')
    fams = json.loads((HERE / args.jobs).read_text())["families"]
    selected = [f for f in args.families.split(",") if f] or list(fams)
    if any(f not in fams for f in selected):
        ap.error('Unknown family in --families')
    seeds = [int(s) for s in args.seeds.split(',')]
    rerender = {(family, int(seed)) for family, seed in (pair.rsplit(':', 1) for pair in args.rerender.split(',') if pair)}
    if any(family not in selected or seed not in seeds for family, seed in rerender):
        ap.error('--rerender pairs must be included in --families/--seeds')
    takes = pending_takes(fams, seeds, Path(args.out), selected, args.max_takes, rerender)
    if not takes:
        print('[gen_sfx_moss] all requested takes already have WAV + provenance; no model loaded', flush=True)
        return
    print(f'[gen_sfx_moss] bounded batch: {len(takes)} new takes; invoke through lockf -k ~/projects/localai/.model.lock', flush=True)

    if not W.is_dir():
        raise SystemExit(f"Local weights missing: {W}")
    if not METER.is_file():
        raise SystemExit(f"Shared anonymous-memory meter missing: {METER}")
    before_load = memory_gate(LOAD_RESERVE_GIB)
    import soundfile as sf
    import numpy as np
    import torch
    from moss_soundeffect_v2 import MossSoundEffectPipeline  # installed editable in the venv
    from moss_soundeffect_v2.diffsynth.models import wan_audio_dit, wan_video_dit
    from moss_soundeffect_v2.diffsynth.pipelines import wan_audio

    # MPS has no float64: the timestep embedding is computed in float64 on the tensor's device. Same maths on the CPU.
    def sinusoidal_embedding_1d(dim, position):
        pos = position.detach().cpu().to(torch.float64)
        sinusoid = torch.outer(pos, torch.pow(10000, -torch.arange(dim // 2, dtype=torch.float64).div(dim // 2)))
        x = torch.cat([torch.cos(sinusoid), torch.sin(sinusoid)], dim=1)
        return x.to(device=position.device, dtype=position.dtype)

    wan_video_dit.sinusoidal_embedding_1d = sinusoidal_embedding_1d
    wan_audio_dit.sinusoidal_embedding_1d = sinusoidal_embedding_1d
    wan_audio.sinusoidal_embedding_1d = sinusoidal_embedding_1d  # imported by name there

    # the RoPE tables are complex128 buffers (polar of float64) - MPS has no complex128. Compute in float64 on the CPU
    # and store complex64, which is what rope_apply reads anyway (.real / .imag cast to float32).
    orig_freqs = wan_audio_dit.precompute_freqs_cis

    def precompute_freqs_cis(*a, **k):
        return orig_freqs(*a, **k).to(torch.complex64)

    wan_audio_dit.precompute_freqs_cis = precompute_freqs_cis
    wan_video_dit.precompute_freqs_cis = precompute_freqs_cis

    dev = "mps" if torch.backends.mps.is_available() else "cpu"
    t0 = time.time()
    pipe = MossSoundEffectPipeline.from_pretrained(str(W), torch_dtype=torch.bfloat16, device=dev)
    precision_comparison = None
    comparison_pending = args.compare_decode
    comparison_samples = 0
    if args.vae_fp32:
        # The upstream decode uses a CUDA autocast scope. On MPS that does not
        # disable the outer bf16 scope, so DAC's final tanh rounds peaks to 1.
        # Reload original checkpoint tensors: casting the bf16-loaded module
        # upward alone would retain rounded weights. Diffusion stays bf16.
        decoder_path = W / 'vae/vae_128d_48k.pth'
        decoder_state = torch.load(decoder_path, map_location='cpu', weights_only=False, mmap=True)['state_dict']
        decoder_dtypes = sorted({str(v.dtype) for v in decoder_state.values() if isinstance(v, torch.Tensor)})
        if decoder_dtypes != ['torch.float32']:
            raise RuntimeError(f'Unexpected original DAC checkpoint dtypes: {decoder_dtypes}')

        def restore_original_decoder():
            pipe.engine.vae.to(dtype=torch.float32)
            pipe.engine.vae.load_state_dict(decoder_state, strict=True)

        restore_original_decoder()
        original_decode = pipe.engine.vae.decode

        def decode_fp32(latents, *decode_args, **decode_kwargs):
            nonlocal precision_comparison, comparison_pending
            reference = None
            if comparison_pending:
                latent_sha = hashlib.sha256(latents.detach().float().cpu().numpy().tobytes()).hexdigest()
                pipe.engine.vae.to(dtype=torch.bfloat16)
                with torch.autocast(dev, dtype=torch.bfloat16):
                    reference = original_decode(latents, *decode_args, **decode_kwargs).detach().float().cpu().numpy()[..., :comparison_samples]
                # The bf16 reference irreversibly rounds module weights;
                # restore checkpoint FP32 values before production decode.
                restore_original_decoder()
            with torch.autocast(dev, enabled=False):
                decoded = original_decode(latents.to(torch.float32), *decode_args, **decode_kwargs)
            if reference is not None:
                precise = decoded.detach().float().cpu().numpy()[..., :comparison_samples]
                error = precise.astype(np.float64) - reference
                rms_error = float(np.sqrt(np.mean(error**2)))
                rms_signal = float(np.sqrt(np.mean(precise.astype(np.float64)**2)))
                precision_comparison = {'same_latent_sha256':latent_sha, 'samples':int(precise.size),
                    'bf16_unique_values':int(np.unique(reference).size), 'fp32_unique_values':int(np.unique(precise).size),
                    'bf16_grid_fraction':float(((reference.view(np.uint32) & 0xffff)==0).mean()),
                    'fp32_bf16_grid_fraction':float(((precise.view(np.uint32) & 0xffff)==0).mean()),
                    'rms_error':rms_error, 'relative_snr_db':float(20*np.log10(rms_signal/max(rms_error, 1e-30))),
                    'bf16_fullscale_values':int((np.abs(reference)>=1).sum()), 'fp32_fullscale_values':int((np.abs(precise)>=1).sum()),
                    'fp32_peak':float(np.abs(precise).max()), 'note':'Identical latent; FP32 decode reloads original float32 DAC checkpoint weights after bf16 reference. Fullscale tanh rounding is not a hard-clipping diagnosis.'}
                comparison_pending = False
            return decoded

        pipe.engine.vae.decode = decode_fp32
    load_s = round(time.time() - t0, 1)
    rev = subprocess.run(["git", "-C", str(MOSS), "rev-parse", "--short", "HEAD"], capture_output=True, text=True).stdout.strip()
    print(f"[gen_sfx_moss] loaded on {dev} in {load_s}s", flush=True)

    for fam, seed, dest in takes:
        j = fams[fam]
        secs = min(float(j["duration"]), 30.0)
        comparison_samples = int(secs * pipe.sample_rate)
        precision_comparison = None
        dest.parent.mkdir(parents=True, exist_ok=True)
        before_take = memory_gate()
        t1 = time.time()
        audio = pipe(prompt=j["prompt"], seconds=secs, num_inference_steps=args.steps, cfg_scale=args.cfg, seed=seed,
                     progress_bar_cmd=lambda x: x)
        wav = audio[0].float().cpu().numpy().T
        partial_wav = dest.with_suffix('.partial.wav')
        sf.write(str(partial_wav), wav, pipe.sample_rate, subtype='FLOAT')
        replaced = None
        if (fam, seed) in rerender and dest.exists():
            old_sha = hashlib.sha256(dest.read_bytes()).hexdigest()
            archive = Path(args.out) / 'before-float' / fam
            archive.mkdir(parents=True, exist_ok=True)
            dest.replace(archive / f'{seed}-{old_sha[:12]}.wav')
            if dest.with_suffix('.json').exists():
                dest.with_suffix('.json').replace(archive / f'{seed}-{old_sha[:12]}.json')
            replaced = {'prior_sha256':old_sha, 'reason':'Preserve prior decoder/storage precision master before explicit rerender'}
        partial_wav.replace(dest)
        dt = round(time.time() - t1, 2)
        side = {"model": "MOSS-SoundEffect v2.0", "repo": "OpenMOSS-Team/MOSS-SoundEffect-v2.0",
                "code_commit": f"MOSS-TTS {rev}, torch {torch.__version__}", "backend": f"PyTorch {dev} bf16",
                "family": fam, "kind": j["kind"], "seed": seed, "prompt": j["prompt"], "desc": j["desc"], "licence": "Apache-2.0",
                "model_source": "https://huggingface.co/OpenMOSS-Team/MOSS-SoundEffect-v2.0",
                "duration_s": secs, "steps": args.steps, "cfg": args.cfg, "gen_time_s": dt, "model_load_s": load_s,
                "master_format": "float32 WAV", "waveform_decode": "float32" if args.vae_fp32 else "bf16 inherited outer autocast", "replaced_master": replaced,
                "decoder_checkpoint_dtypes": decoder_dtypes if args.vae_fp32 else None,
                "decoder_weights": "original float32 checkpoint reloaded" if args.vae_fp32 else "bf16 checkpoint conversion",
                "precision_comparison": precision_comparison,
                "resource_policy": {"anonymous_limit_gib": MEMORY_LIMIT_GIB, "load_reserve_gib": LOAD_RESERVE_GIB, "load_snapshot": before_load, "take_snapshot": before_take},
                "mps_driver_gb": round(torch.mps.driver_allocated_memory() / 1e9, 2) if dev == "mps" else None}
        partial_json = dest.with_suffix('.partial.json')
        partial_json.write_text(json.dumps(side, indent=2))
        partial_json.replace(dest.with_suffix('.json'))
        print(f"[gen_sfx_moss] {fam} seed={seed} {dt}s", flush=True)
        del audio, wav
        gc.collect()
        if dev == 'mps':
            torch.mps.empty_cache()
    print(f'[gen_sfx_moss] yielded after {len(takes)} takes; rerun the same locked command to resume', flush=True)


if __name__ == "__main__":
    main()
