import { afterEach, describe, expect, it, vi } from 'vitest';
import { UiSfx } from '../../ui/sfx';
import { ROCKHOP_ZONE_BIOME } from '../../tracks/rockhop/zones';
import { BIOMES, PACKED_LENGTH, TK, TRANSIENT_KINDS, biomeIndex, createParams, packParams } from '../params';
import { Ambience } from './ambience';
import { Crowd } from './crowd';
import { RockhopSynth } from './synth';
import { renderMenuCue, type MenuCue } from './ui';
import { Biquad, bandLimitedSaw, sineCycle } from './util';
import { VoicePool } from './voices';

function energy(x: Float32Array): number {
  return x.reduce((s, v) => s + v * v, 0) / x.length;
}

function band(x: Float32Array, sr: number, center: number, q: number): number {
  const filter = new Biquad(sr);
  filter.bandpass(center, q);
  let sum = 0;
  for (const sample of x) { const v = filter.process(sample); sum += v * v; }
  return sum / x.length;
}

function shot(kind: number, sr: number, pitch = 0): Float32Array {
  const n = Math.round(sr * 0.75);
  const buses: [Float32Array, Float32Array][] = Array.from({ length: 3 }, () => [new Float32Array(n), new Float32Array(n)]);
  if (kind >= TK.crowdRoar && kind <= TK.crowdApplause) {
    const crowd = new Crowd(sr, 49);
    crowd.trigger(kind - TK.crowdRoar + 1, 0.8, 0);
    crowd.process(buses[2]![0], buses[2]![1], 0, n);
  } else {
    const pool = new VoicePool(sr, 49);
    pool.trigger({ kind, gain: 0.8, pitch, pan: 0, delay: 0 });
    pool.process(buses, 0, n);
  }
  const out = new Float32Array(n);
  for (const [l, r] of buses) for (let i = 0; i < n; i++) out[i] = out[i]! + (l[i]! + r[i]!) * 0.5;
  return out;
}

afterEach(() => vi.unstubAllGlobals());

describe('remastered sound bank, offline only', () => {
  it('actual Rockhop zones keep legacy wire IDs and have distinct seeded outdoor fallback beds', () => {
    expect(BIOMES.slice(0, 5)).toEqual(['industrial', 'canyon', 'snow', 'nightCity', 'foundry']);
    const indices = ['coast', 'alpine', 'quarry', 'snowline'].map((zone) => biomeIndex(ROCKHOP_ZONE_BIOME[zone as keyof typeof ROCKHOP_ZONE_BIOME]));
    expect(indices).toEqual([5, 6, 7, 2]);
    const render = (biome: number, sr: number, bedEnabled = true, wind = 0) => {
      const ambience = new Ambience(sr, 19);
      ambience.setBedEnabled(bedEnabled);
      const pool = new VoicePool(sr, 19);
      const events = vi.spyOn(pool, 'trigger');
      const count = sr * 12;
      const buses: [Float32Array, Float32Array][] = Array.from({ length: 3 }, () => [new Float32Array(count), new Float32Array(count)]);
      ambience.set(biome, 1, wind, false);
      for (let off = 0; off < count; off += 800) {
        const n = Math.min(800, count - off);
        ambience.process(buses[2]![0], buses[2]![1], off, n, pool);
        pool.process(buses, off, n);
      }
      return { pcm: buses[2]![0], kinds: events.mock.calls.map(([event]) => event.kind) };
    };
    for (const sr of [44100, 48000]) {
      const beds = indices.slice(0, 3).map((biome) => render(biome, sr));
      for (let i = 0; i < beds.length; i++) {
        const bed = beds[i]!;
        expect(bed.pcm.every(Number.isFinite)).toBe(true);
        const rms = 10 * Math.log10(energy(bed.pcm));
        expect(rms).toBeGreaterThan(-45);
        expect(rms).toBeLessThan(-20);
        expect(Buffer.from(bed.pcm.buffer).equals(Buffer.from(render(indices[i]!, sr).pcm.buffer))).toBe(true);
        expect(bed.kinds.length).toBeGreaterThan(0);
        expect(bed.kinds.some((kind) => [100, 102, 103, 104, 107].includes(kind))).toBe(false);
      }
      expect(beds[0]!.kinds).toContain(108);
      expect(beds[1]!.kinds.some((kind) => kind === 101 || kind === 109)).toBe(true);
      expect(beds[2]!.kinds).toContain(110);
      expect(Buffer.from(beds[0]!.pcm.buffer).equals(Buffer.from(beds[1]!.pcm.buffer))).toBe(false);
      expect(Buffer.from(beds[1]!.pcm.buffer).equals(Buffer.from(beds[2]!.pcm.buffer))).toBe(false);
      for (const biome of indices.slice(0, 3)) {
        const replaced = render(biome, sr, false);
        expect(energy(replaced.pcm)).toBe(0);
        expect(replaced.kinds).toHaveLength(0);
        expect(energy(render(biome, sr, false, 1).pcm)).toBeGreaterThan(1e-5);
      }
    }
  });

  it('every one-shot and crowd family is finite, audible and seeded at Safari and desktop sample rates', () => {
    for (const sr of [44100, 48000]) for (let kind = 0; kind < TRANSIENT_KINDS.length; kind++) {
      const a = shot(kind, sr);
      const b = shot(kind, sr);
      expect(Buffer.from(a.buffer).equals(Buffer.from(b.buffer)), `${TRANSIENT_KINDS[kind]} @ ${sr}`).toBe(true);
      expect(a.every(Number.isFinite)).toBe(true);
      if (kind === TK.kill) expect(energy(a)).toBe(0);
      else expect(energy(a), TRANSIENT_KINDS[kind]).toBeGreaterThan(1e-10);
    }
  });

  it('material landings have distinct contact signatures: metal rings above rubber, wood keeps its body', () => {
    const sr = 48000;
    const metal = shot(TK.landing, sr, 2 / 8);
    const rubber = shot(TK.landing, sr, 4 / 8);
    const wood = shot(TK.landing, sr, 1 / 8);
    expect(band(metal, sr, 2130, 6) / band(rubber, sr, 2130, 6)).toBeGreaterThan(3);
    expect(band(wood, sr, 423, 5) / band(rubber, sr, 423, 5)).toBeGreaterThan(2);
    for (let surface = 0; surface < 8; surface++) {
      for (let other = surface + 1; other < 8; other++) {
        expect(Buffer.from(shot(TK.landing, sr, surface / 8).buffer).equals(Buffer.from(shot(TK.landing, sr, other / 8).buffer))).toBe(false);
      }
    }
  });

  it('band-limited oscillators suppress folded high harmonics without losing the fundamental', () => {
    const sr = 48000;
    const f = 9000;
    const raw = new Float32Array(sr / 4);
    const clean = new Float32Array(raw.length);
    let phase = 0;
    for (let i = 0; i < raw.length; i++) {
      phase = (phase + f / sr) % 1;
      raw[i] = phase * 2 - 1;
      clean[i] = bandLimitedSaw(phase, f / sr);
    }
    // Third harmonic 27 kHz folds to 21 kHz on a naive 9 kHz saw.
    expect(band(clean, sr, 21000, 25) / band(raw, sr, 21000, 25)).toBeLessThan(0.2);
    expect(band(clean, sr, 9000, 25) / band(raw, sr, 9000, 25)).toBeGreaterThan(0.7);
    for (let i = 0; i < 17000; i++) {
      const p = i / 17000;
      expect(Math.abs(sineCycle(p) - Math.sin(p * Math.PI * 2))).toBeLessThan(0.0000003);
    }
  });

  it('menu cues have tactile and tonal variety, deterministic tails and no automation AudioContext', () => {
    const cues: MenuCue[] = ['menuFocus', 'menuConfirm', 'menuBack', 'menuLaunch'];
    const pcm = cues.map((cue) => renderMenuCue(cue, 48000)[0]);
    expect(pcm[0]!.length).toBeLessThan(pcm[2]!.length);
    expect(pcm[3]!.length).toBeGreaterThan(pcm[1]!.length);
    for (let i = 0; i < cues.length; i++) {
      expect(energy(pcm[i]!)).toBeGreaterThan(1e-7);
      expect(Buffer.from(pcm[i]!.buffer).equals(Buffer.from(renderMenuCue(cues[i]!, 48000)[0].buffer))).toBe(true);
      expect(Math.abs(pcm[i]![pcm[i]!.length - 1]!)).toBeLessThan(1e-5);
    }
    const context = vi.fn();
    vi.stubGlobal('navigator', { webdriver: true });
    vi.stubGlobal('AudioContext', context);
    const ui = new UiSfx();
    ui.tick(); ui.confirm(); ui.back(); ui.launch();
    expect(context).not.toHaveBeenCalled();
  });

  it('fresh muted synths emit exactly zero; replacing environmental beds preserves helmet wind', () => {
    const p = createParams();
    p.scene = 1;
    const packed = packParams(p, new Float32Array(PACKED_LENGTH));
    const muted = new RockhopSynth(48000);
    muted.setMaster(0, true);
    muted.setParams(packed);
    const l = new Float32Array(48000);
    const r = new Float32Array(48000);
    muted.process(l, r, 0, l.length);
    expect(energy(l) + energy(r)).toBe(0);
    const music = new RockhopSynth(48000, { solo: 'music' });
    music.setMusicVolume(0, true);
    music.setParams(packed);
    music.process(l, r, 0, l.length);
    expect(energy(l) + energy(r)).toBe(0);
    const wind = new RockhopSynth(48000, { solo: 'ambient' });
    wind.setAmbienceEnabled(false);
    p.scene = 0;
    p.wind = 1;
    wind.setParams(packParams(p, packed));
    wind.process(l, r, 0, l.length);
    expect(energy(l) + energy(r)).toBeGreaterThan(1e-5);
  });

  it('menu/results scene edges immediately gate the stale engine and restore it in a run', () => {
    const p = createParams();
    p.scene = 1;
    p.engineGain = 0;
    const packed = packParams(p, new Float32Array(PACKED_LENGTH));
    const synth = new RockhopSynth(48000, { solo: 'engine' });
    const l = new Float32Array(48000);
    const r = new Float32Array(48000);
    synth.setParams(packed);
    synth.process(l, r, 0, 256);
    expect(energy(l) + energy(r)).toBe(0);
    p.scene = 0;
    p.engineGain = 1;
    synth.setParams(packParams(p, packed));
    synth.process(l, r, 0, l.length);
    expect(energy(l) + energy(r)).toBeGreaterThan(1e-5);
    synth.setScene(2);
    synth.process(l, r, 0, l.length);
    expect(energy(l) + energy(r)).toBe(0);
  });
});
