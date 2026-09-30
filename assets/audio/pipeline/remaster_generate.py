"""Serial MiniMax Music 3 renders; adapted from Wildshard's gen_minimax.py.

Run in ~/ml/music/minimax-music3/.venv. Weights, views and raw output stay
outside git. No playback, downloads, ACE-Step, or concurrent model workers.
"""
from __future__ import annotations

import argparse
import gc
import json
import os
import re
import subprocess
import time
from pathlib import Path


def local_view(source: Path, view: Path) -> Path:
    view.mkdir(parents=True, exist_ok=True)
    for path in source.rglob('*'):
        if path.is_dir() or path.name == 'modular_model_index.json' or 'qwen_7B' in path.parts:
            continue
        dst = view / path.relative_to(source)
        dst.parent.mkdir(parents=True, exist_ok=True)
        if not dst.exists():
            dst.symlink_to(path)
    index = json.loads((source / 'modular_model_index.json').read_text())
    for value in index.values():
        if isinstance(value, list) and len(value) == 3 and isinstance(value[2], dict):
            if 'pretrained_model_name_or_path' in value[2]:
                value[2]['pretrained_model_name_or_path'] = str(view)
    (view / 'modular_model_index.json').write_text(json.dumps(index, indent=2))
    return view


def memory_gate(reserve_gib: float = 0) -> dict:
    # The shared model queue measures anonymous pages, rather than stale swap
    # or reclaimable file cache. Reserve the measured model footprint before
    # loading across anonymous + wired RAM (MPS allocations can be wired);
    # between takes the loaded model already appears in those measurements.
    meter = Path.home() / 'projects/localai/bin/mem-gb.sh'
    anon, wired, free = map(float, subprocess.check_output(['bash', str(meter)], text=True).split())
    pressure = int(subprocess.check_output(['sysctl', '-n', 'kern.memorystatus_vm_pressure_level'], text=True))
    top = subprocess.check_output(['top', '-l', '1', '-o', 'mem', '-n', '5', '-stats', 'pid,command,mem'], text=True)
    other = []
    for row in top.splitlines():
        fields = row.split()
        if len(fields) >= 3 and fields[0].isdigit() and int(fields[0]) != os.getpid():
            match = re.fullmatch(r'([0-9.]+)G[+-]?', fields[-1])
            if match and float(match[1]) > 15:
                other.append(fields[0])
    snapshot = dict(pressure=pressure, anonymous_gib=anon, wired_gib=wired, free_gib=free,
                    reserve_gib=reserve_gib, other_large_pids=other)
    if pressure != 1 or anon >= 70 or anon+wired+reserve_gib >= 100 or other:
        print(f'Memory gate busy: {snapshot}; yielding model queue', flush=True)
        raise SystemExit(75)
    print(f'Memory gate: {snapshot}', flush=True)
    return snapshot


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument('--out', type=Path, required=True)
    parser.add_argument('--cues', default='')
    parser.add_argument('--seeds', default='')
    parser.add_argument('--compare-decoder', action='store_true',
                        help='Measure fp32 versus bf16 decoding of the first identical latent chunk')
    parser.add_argument('--max-takes', type=int, default=2,
                        help='Yield the machine-wide model lock after a short batch')
    args = parser.parse_args()
    if not 1 <= args.max_takes <= 2:
        parser.error('--max-takes must be 1 or 2 to yield the shared model queue')
    os.environ.setdefault('HF_HUB_OFFLINE', '1')
    os.environ.setdefault('PYTORCH_MPS_HIGH_WATERMARK_RATIO', '0.5')
    os.environ.setdefault('PYTORCH_MPS_LOW_WATERMARK_RATIO', '0.4')
    import diffusers
    import numpy as np
    import soundfile as sf
    import torch
    from diffusers import ModularPipeline

    config = json.loads(Path(__file__).with_name('remaster-jobs.json').read_text())
    weights = Path.home() / 'projects/weights/manual/MiniMaxAI/MiniMax-Music3'
    view = local_view(weights, Path.home() / 'ml/music/minimax-music3/rockhop-view')
    initial_memory = memory_gate(30)
    device = 'mps' if torch.backends.mps.is_available() else 'cpu'
    started = time.monotonic()
    pipe = ModularPipeline.from_pretrained(str(view))
    pipe.load_components(dtype={'vocoder': torch.float32, 'default': torch.bfloat16})
    pipe.to(device)
    print(f'MiniMax loaded on {device} in {time.monotonic() - started:.1f}s', flush=True)
    args.out.mkdir(parents=True, exist_ok=True)
    seeds = [int(s) for s in args.seeds.split(',')] if args.seeds else config['seeds']
    # Finish one candidate for every cue first, then the second comparison set.
    finished = 0
    for seed in seeds:
        for cue, job in config['jobs'].items():
            if args.cues and cue not in args.cues.split(','):
                continue
            dest = args.out / f'{cue}-minimax-s{seed}.wav'
            if dest.exists() and dest.with_suffix('.json').exists():
                continue
            take_memory = memory_gate()
            started = time.monotonic()
            result = pipe(prompt=job['caption'], lyrics=job['lyrics'], audio_duration=job['duration'],
                         num_inference_steps=config['steps'],
                         generator=torch.Generator('cpu').manual_seed(seed),
                         output=['audios', 'latent_chunks'])
            audio = result['audios'][0]
            # Latents are small, local-only recovery artifacts: codec precision
            # can be repaired without rerunning language/flow generation.
            torch.save([chunk.cpu() for chunk in result['latent_chunks']], dest.with_suffix('.latents.pt'))
            comparison = None
            if args.compare_decoder and finished == 0:
                latent = result['latent_chunks'][0]
                with torch.no_grad():
                    precise = pipe.vocoder(latent.to(torch.float32)).float().cpu().numpy()
                    pipe.vocoder.to(dtype=torch.bfloat16)
                    rounded = pipe.vocoder(latent.to(torch.bfloat16)).float().cpu().numpy()
                error = float(np.sqrt(np.mean((precise-rounded)**2)))
                comparison = dict(same_latent=True, samples=int(precise.size),
                                  fp32_unique=int(np.unique(precise).size),
                                  bf16_unique=int(np.unique(rounded).size), rms_error=error,
                                  snr_db=float(20*np.log10(np.sqrt(np.mean(precise**2))/(error+1e-12))))
                # Casting back cannot recover original weights; reload fp32
                # directly from the local source for subsequent takes.
                pipe.load_components('vocoder', dtype=torch.float32)
                pipe.vocoder.to(device)
                del precise, rounded, latent
                print(f'Same-latent decoder comparison: {comparison}', flush=True)
            wav = np.asarray(audio.float().cpu().numpy() if hasattr(audio, 'cpu') else audio, dtype=np.float32)
            if wav.ndim == 2 and wav.shape[0] in (1, 2):
                wav = wav.T
            sf.write(str(dest), wav, pipe.sampling_rate, subtype='FLOAT')
            side = {**job, 'cue': cue, 'seed': seed, 'model': config['model'], 'dit': 'MiniMax-Music3',
                    'lm': 'Qwen3-8B + 0.6B local LM', 'steps': config['steps'],
                    'license': 'MiniMax-Music3 Community License',
                    'backend': f'PyTorch {device}, bf16 generation / fp32 vocoder',
                    'decoder_precision': 'float32', 'decoder_comparison': comparison,
                    'code': f'diffusers {diffusers.__version__}, torch {torch.__version__}',
                    'sample_rate': pipe.sampling_rate, 'gen_time_s': round(time.monotonic() - started, 2),
                    'duration_requested_s': job['duration'], 'duration_actual_s': round(len(wav)/pipe.sampling_rate, 6),
                    'memory_before_load': initial_memory, 'memory_before_take': take_memory,
                    'mps_driver_gb': round(torch.mps.driver_allocated_memory() / 1e9, 2) if device == 'mps' else None}
            dest.with_suffix('.json').write_text(json.dumps(side, indent=2) + '\n')
            print(f'{cue} seed {seed}: {side["gen_time_s"]}s, {side["mps_driver_gb"]} GB -> {dest}', flush=True)
            del result, audio, wav
            gc.collect()
            if device == 'mps':
                torch.mps.empty_cache()
            finished += 1
            if finished >= args.max_takes:
                print('Batch complete; releasing model memory for other agents', flush=True)
                return


if __name__ == '__main__':
    main()
