/**
 * The recorded-music loader on a mocked AudioContext (tests are silent: no real context ever opens).
 * Covers: scene → cue mapping, zone fallback, lazy fetch + decode, the loop window, the sting hand-off,
 * the procedural bed hand-back on a failed fetch, the engine duck law, and the automation rule
 * (WebAudioSystem never constructs an AudioContext under navigator.webdriver).
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import { MusicPlayer, MUSIC_LEVELS } from './player';
import type { CueFile, MusicCue } from './cues';
import { MUSIC_CUES } from './cues';
import { zoneOf } from './zone';
import { P_HEADER, P_TRANSIENT_COUNT, P_ENGINE_GAIN, P_TYRE_SPEED, TK, pushTransient } from '../params';
import { blankState } from '../tools/fixture';
import { WebAudioSystem, engineDuckDb } from '../graph/webAudio';

class MockParam {
  value = 1;
  events: string[] = [];
  setValueAtTime(v: number, t: number): this {
    this.events.push(`set ${v.toFixed(3)}@${t}`);
    this.value = v;
    return this;
  }
  linearRampToValueAtTime(v: number, t: number): this {
    this.events.push(`ramp ${v.toFixed(3)}@${t}`);
    this.value = v;
    return this;
  }
  setTargetAtTime(v: number, t: number, tau: number): this {
    this.events.push(`target ${v.toFixed(3)}@${t}/${tau}`);
    this.value = v;
    return this;
  }
  exponentialRampToValueAtTime(v: number, t: number): this {
    return this.linearRampToValueAtTime(v, t);
  }
  cancelScheduledValues(): this {
    return this;
  }
}

class MockNode {
  outputs: unknown[] = [];
  connect(n: unknown): unknown {
    this.outputs.push(n);
    return n;
  }
  disconnect(): void {
    this.outputs = [];
  }
}

class MockGain extends MockNode {
  gain = new MockParam();
}

class MockSource extends MockNode {
  buffer: MockBuffer | null = null;
  loop = false;
  loopStart = 0;
  loopEnd = 0;
  started: [number, number] | null = null;
  stopped: number | null = null;
  onended: (() => void) | null = null;
  start(t: number, off: number): void {
    this.started = [t, off];
  }
  stop(t = 10): void {
    this.stopped = t;
  }
}

class MockBuffer {
  duration = 100;
  constructor(readonly tag: string) {}
}

class MockFilter extends MockNode {
  type = '';
  frequency = new MockParam();
  Q = new MockParam();
  threshold = new MockParam();
  knee = new MockParam();
  ratio = new MockParam();
  attack = new MockParam();
  release = new MockParam();
  stopped: number | null = null;
  start(): void {}
  stop(t: number): void {
    this.stopped = t;
  }
}

class MockCtx {
  currentTime = 10;
  sampleRate = 48000;
  state = 'running';
  async resume(): Promise<void> {}
  compressors: MockFilter[] = [];
  createDynamicsCompressor(): MockFilter {
    const node = new MockFilter();
    this.compressors.push(node);
    return node;
  }
  createBiquadFilter(): MockFilter {
    return new MockFilter();
  }
  oscillators: MockFilter[] = [];
  createOscillator(): MockFilter {
    const o = new MockFilter();
    this.oscillators.push(o);
    return o;
  }
  createBuffer(_c: number, n: number): { getChannelData(): Float32Array } {
    const d = new Float32Array(n);
    return { getChannelData: () => d };
  }
  sources: MockSource[] = [];
  decodes: number[] = [];
  destination = new MockNode();
  createGain(): MockGain {
    return new MockGain();
  }
  createBufferSource(): MockSource {
    const s = new MockSource();
    this.sources.push(s);
    return s;
  }
  decodeAudioData(b: ArrayBuffer): Promise<MockBuffer> {
    this.decodes.push(b.byteLength);
    const tag = new TextDecoder().decode(new Uint8Array(b));
    if (tag === 'garbage') return Promise.reject(new Error('EncodingError'));
    return Promise.resolve(new MockBuffer(tag));
  }
}

const CUES: Partial<Record<MusicCue, CueFile>> = {
  menu: { file: 'menu-aaaa.m4a', loop: true, pre: 0.5, len: 64, gainDb: 0, bpm: 120, bytes: 4 },
  map: { file: 'map-bbbb.m4a', loop: true, pre: 0.5, len: 48, gainDb: -1, bpm: 96, bytes: 3 },
  coast: { file: 'coast-cccc.m4a', loop: true, pre: 0.5, len: 60, gainDb: 0, bpm: 128, bytes: 5 },
  alpine: { file: 'alpine-dddd.m4a', loop: true, pre: 0.5, len: 60, gainDb: 0, bpm: 118, bytes: 6 },
  results: { file: 'results-eeee.m4a', loop: false, pre: 0, len: 9, gainDb: 0, bpm: 120, bytes: 7 },
};

const flush = async (): Promise<void> => {
  for (let i = 0; i < 12; i++) await Promise.resolve();
};

function setup(cues = CUES, bodies: Record<string, string> = {}) {
  const ctx = new MockCtx();
  const fetched: string[] = [];
  const bed: boolean[] = [];
  const player = new MusicPlayer(ctx as unknown as AudioContext, ctx.destination as unknown as AudioNode, {
    cues,
    fetchBytes: async (url) => {
      fetched.push(url);
      const name = url.replace('./audio/', '');
      if (bodies[name] === '404') throw new Error('404');
      return new TextEncoder().encode(bodies[name] ?? name).buffer as ArrayBuffer;
    },
    onBed: (on) => bed.push(on),
  });
  return { ctx, player, fetched, bed };
}

describe('MusicPlayer', () => {
  it('fetches nothing until a scene asks, then fetches + decodes lazily and loops the padded window', async () => {
    const { ctx, player, fetched, bed } = setup();
    expect(fetched).toEqual([]);
    player.setScene('menu', 'coast');
    expect(bed).toEqual([true]); // delivery may be slow: keep the procedural fallback available
    await flush();
    expect(fetched[0]).toBe('./audio/menu-aaaa.m4a');
    const src = ctx.sources[0]!;
    expect(src.buffer?.tag).toBe('menu-aaaa.m4a');
    expect(src.loop).toBe(true);
    expect(src.loopStart).toBe(0.5);
    expect(src.loopEnd).toBe(64.5);
    expect(src.started).toEqual([10, 0.5]);
    expect(player.playing).toBe('menu');
    expect(bed).toEqual([true, false]);
    // menu prefetches the map and the zone (bytes only — nothing else decoded)
    expect(fetched).toContain('./audio/map-bbbb.m4a');
    expect(fetched).toContain('./audio/coast-cccc.m4a');
    expect(ctx.decodes.length).toBe(1);
  });

  it('keeps the procedural bed through a delayed first fetch and yields exactly once after start', async () => {
    const ctx = new MockCtx();
    const bed: boolean[] = [];
    let resolve: ((bytes: ArrayBuffer) => void) | undefined;
    const player = new MusicPlayer(ctx as unknown as AudioContext, ctx.destination as unknown as AudioNode, {
      cues: { menu: CUES.menu! },
      fetchBytes: () => new Promise<ArrayBuffer>((done) => { resolve = done; }),
      onBed: (on) => bed.push(on),
    });
    player.setScene('menu');
    await flush();
    player.setScene('menu');
    expect(player.playing).toBeNull();
    expect(ctx.sources).toHaveLength(0);
    expect(bed).toEqual([true]);
    resolve!(new TextEncoder().encode('menu').buffer as ArrayBuffer);
    await flush();
    expect(ctx.sources).toHaveLength(1);
    expect(ctx.sources[0]!.started).toEqual([10, 0.5]);
    expect(bed).toEqual([true, false]);
    player.setScene('menu');
    expect(bed).toEqual([true, false]);
    player.dispose();
    expect(bed).toEqual([true, false, true]);
  });

  it('ignores a delayed first fetch after disposal without withdrawing the fallback', async () => {
    const ctx = new MockCtx();
    const bed: boolean[] = [];
    let resolve: ((bytes: ArrayBuffer) => void) | undefined;
    const player = new MusicPlayer(ctx as unknown as AudioContext, ctx.destination as unknown as AudioNode, {
      cues: { menu: CUES.menu! },
      fetchBytes: () => new Promise<ArrayBuffer>((done) => { resolve = done; }),
      onBed: (on) => bed.push(on),
    });
    player.setScene('menu');
    player.dispose();
    resolve!(new TextEncoder().encode('menu').buffer as ArrayBuffer);
    await flush();
    expect(ctx.sources).toHaveLength(0);
    expect(ctx.decodes).toHaveLength(0);
    expect(bed).toEqual([true]);
  });

  it('crossfades menu → map → the zone ride loop; a restart (same scene) never re-cues', async () => {
    const { ctx, player } = setup();
    player.setScene('menu', 'alpine');
    await flush();
    player.setScene('map');
    await flush();
    expect(ctx.sources[0]!.stopped).not.toBeNull();
    expect(player.playing).toBe('map');
    player.setScene('run');
    await flush();
    expect(player.playing).toBe('alpine');
    const n = ctx.sources.length;
    player.setScene('run'); // retry / checkpoint restart
    player.setZone('alpine');
    await flush();
    expect(ctx.sources.length).toBe(n);
    expect(player.log).toEqual(['menu:menu', 'map:map', 'run:alpine']);
  });

  it('keeps the original cue playing while a replacement decodes; returning cancels the pending switch', async () => {
    const ctx = new MockCtx();
    let resolveMap: ((buffer: ArrayBuffer) => void) | undefined;
    const player = new MusicPlayer(ctx as unknown as AudioContext, ctx.destination as unknown as AudioNode, {
      cues: CUES,
      fetchBytes: async (url) => url.includes('map-')
        ? new Promise<ArrayBuffer>((resolve) => { resolveMap = resolve; })
        : new TextEncoder().encode(url).buffer as ArrayBuffer,
    });
    player.setScene('menu');
    await flush();
    const original = ctx.sources[0]!;
    player.setScene('map');
    await flush();
    expect(player.playing).toBe('menu');
    expect(original.stopped).toBeNull();
    player.setScene('menu');
    resolveMap!(new TextEncoder().encode('map').buffer as ArrayBuffer);
    await flush();
    expect(player.playing).toBe('menu');
    expect(ctx.sources).toHaveLength(1);
    player.setScene('map');
    await flush();
    expect(player.playing).toBe('map');
    expect(original.stopped).toBeCloseTo(10.96);
  });

  it('disconnects every active and fading voice on dispose, with no stale cue after loading', async () => {
    const { ctx, player } = setup();
    player.setScene('menu');
    await flush();
    player.setScene('map');
    await flush();
    player.setScene('run');
    player.dispose();
    await flush();
    expect(player.playing).toBeNull();
    for (const source of ctx.sources) {
      expect(source.stopped).toBe(10);
      expect(source.outputs).toHaveLength(0);
      expect(source.onended).toBeNull();
    }
  });

  it('releases ended sting nodes before starting the low results bed', async () => {
    const { ctx, player } = setup();
    player.setScene('results');
    await flush();
    const sting = ctx.sources[0]!;
    sting.onended!();
    await flush();
    expect(sting.outputs).toHaveLength(0);
    expect(sting.onended).toBeNull();
    expect(player.playing).toBe('menu');
  });

  it('a new zone while riding re-cues; a zone without its own loop rides its neighbour', async () => {
    const { player } = setup();
    player.setScene('run', 'coast');
    await flush();
    expect(player.playing).toBe('coast');
    player.setZone('snowline'); // no snowline file in this manifest → the alpine loop
    await flush();
    expect(player.playing).toBe('alpine');
    player.setZone('quarry'); // no quarry file → coast
    await flush();
    expect(player.playing).toBe('coast');
  });

  it('with no ride loop at all a run is silent (the procedural bed never plays in a run)', async () => {
    const { player, bed } = setup({ menu: CUES.menu! });
    player.setScene('run', 'snowline');
    await flush();
    expect(player.playing).toBeNull();
    expect(bed.at(-1)).toBe(true);
  });

  it('results: the sting plays once, then the menu theme comes up low under the panel', async () => {
    const { ctx, player } = setup();
    player.setScene('run', 'coast');
    await flush();
    player.setScene('results');
    await flush();
    const sting = ctx.sources.at(-1)!;
    expect(sting.buffer?.tag).toBe('results-eeee.m4a');
    expect(sting.loop).toBe(false);
    sting.onended?.();
    await flush();
    expect(player.playing).toBe('menu');
    expect(player.log.at(-1)).toBe('results:menu');
  });

  it('hands the scene back to the procedural bed when the fetch fails or the decode throws', async () => {
    const a = setup(CUES, { 'menu-aaaa.m4a': '404' });
    a.player.setScene('menu');
    await flush();
    expect(a.bed).toEqual([true]);
    expect(a.player.playing).toBeNull();
    const b = setup(CUES, { 'map-bbbb.m4a': 'garbage' });
    b.player.setScene('map');
    await flush();
    expect(b.bed).toEqual([true]);
  });

  it('retries a transient network failure when the same scene is requested again', async () => {
    const ctx = new MockCtx();
    let attempts = 0;
    const player = new MusicPlayer(ctx as unknown as AudioContext, ctx.destination as unknown as AudioNode, {
      cues: { menu: CUES.menu! },
      fetchBytes: async () => {
        if (++attempts === 1) throw new Error('offline');
        return new TextEncoder().encode('menu').buffer as ArrayBuffer;
      },
    });
    player.setScene('menu');
    await flush();
    expect(player.playing).toBeNull();
    player.setScene('menu');
    await flush();
    expect(player.playing).toBe('menu');
    expect(attempts).toBe(2);
  });

  it('bounds decoded and compressed caches through all seven cues and every zone', async () => {
    const { player } = setup({
      ...CUES,
      quarry: { ...CUES.coast!, file: 'quarry.m4a' },
      snowline: { ...CUES.alpine!, file: 'snowline.m4a' },
    });
    const caches = player as unknown as { decoded: Map<string, unknown>; bytes: Map<string, unknown> };
    for (const scene of ['menu', 'map', 'run', 'results', 'run'] as const) {
      player.setScene(scene);
      await flush();
      for (const zone of ['coast', 'alpine', 'quarry', 'snowline'] as const) {
        player.setZone(zone);
        await flush();
        expect(caches.decoded.size).toBeLessThanOrEqual(3);
        expect(caches.bytes.size).toBeLessThanOrEqual(3);
      }
    }
  });

  it('with an empty manifest it is inert: the bed carries every scene', async () => {
    const { ctx, player, fetched, bed } = setup({});
    for (const s of ['menu', 'map', 'run', 'results'] as const) player.setScene(s);
    await flush();
    expect(fetched).toEqual([]);
    expect(ctx.sources.length).toBe(0);
    expect(bed).toEqual([true]);
  });

  it('levels: ride sits under the front end; the sting stands up', () => {
    expect(MUSIC_LEVELS.ride).toBeLessThan(MUSIC_LEVELS.front);
    expect(MUSIC_LEVELS.sting).toBeGreaterThan(MUSIC_LEVELS.ride);
  });

  it('keeps at most three cues decoded', async () => {
    const { player } = setup();
    for (const s of ['menu', 'map', 'run', 'results'] as const) {
      player.setScene(s, 'coast');
      await flush();
    }
    player.setZone('alpine');
    await flush();
    // decoded map is private: count through a probe — every scene played, so eviction must have run
    expect((player as unknown as { decoded: Map<string, unknown> }).decoded.size).toBeLessThanOrEqual(3);
  });
});

describe('engine duck law', () => {
  it('is 0 with the engine silent, 1 dB closed, 4 dB wide open', () => {
    expect(engineDuckDb(0, 1)).toBe(0);
    expect(engineDuckDb(1, 0)).toBeCloseTo(1);
    expect(engineDuckDb(1, 1)).toBeCloseTo(4);
  });
});

describe('zoneOf', () => {
  const t = (meta: Record<string, unknown>) => ({ def: { meta } }) as unknown as Parameters<typeof zoneOf>[0];
  it('zone wins, then the biome, then coast', () => {
    expect(zoneOf(t({ zone: 'snowline', biome: 'coast' }))).toBe('snowline');
    expect(zoneOf(t({ biome: 'alpine' }))).toBe('alpine');
    expect(zoneOf(t({ biome: 'quarry' }))).toBe('quarry');
    expect(zoneOf(t({ biome: 'snow' }))).toBe('snowline');
    expect(zoneOf(t({ biome: 'canyon' }))).toBe('quarry');
    expect(zoneOf(t({ biome: 'somethingNew' }))).toBe('coast');
    expect(zoneOf(null)).toBe('coast');
  });
});

describe('shipped manifest', () => {
  it('every cue file is compressed audio under public/audio with a loop window inside the file', () => {
    for (const [cue, f] of Object.entries(MUSIC_CUES)) {
      expect(f!.file, cue).toMatch(/^[a-z]+-[0-9a-f]{8}\.(?:m4a|mp3)$/);
      if (f!.loop) expect(f!.pre, cue).toBeGreaterThanOrEqual(0.1);
      expect(f!.len, cue).toBeGreaterThan(f!.loop ? 20 : 3);
    }
  });
});

describe('automation stays silent', () => {
  const g = globalThis as Record<string, unknown>;
  afterEach(() => {
    delete g.navigator;
    delete g.AudioContext;
    delete g.location;
  });

  it('never constructs an AudioContext under navigator.webdriver, so no music loads', async () => {
    Object.defineProperty(globalThis, 'navigator', { value: { webdriver: true }, configurable: true });
    const ctor = vi.fn();
    g.AudioContext = ctor;
    const sys = new WebAudioSystem();
    await sys.unlock();
    sys.setScene('menu');
    expect(ctor).not.toHaveBeenCalled();
    expect(sys.context).toBeNull();
    expect(sys.musicPlayer).toBeNull();
  });

  it('ignores an audible URL override under webdriver', async () => {
    Object.defineProperty(globalThis, 'navigator', { value: { webdriver: true }, configurable: true });
    g.location = { search: '?audible=1' };
    const ctor = vi.fn();
    g.AudioContext = ctor;
    await new WebAudioSystem().unlock();
    expect(ctor).not.toHaveBeenCalled();
  });

  it('suppresses only a successfully scheduled recorded transient and clears delayed voices on restart', async () => {
    const ctx = new MockCtx();
    const sys = new WebAudioSystem({
      context: ctx as unknown as AudioContext, forceFallback: true, music: false,
      samples: {
        manifest: { oneshots: { grunt: [{ file: 'atlas.m4a', start: 0, duration: 0.5, gain: 0.5 }] }, beds: {} },
        fetchBytes: async () => new TextEncoder().encode('atlas').buffer as ArrayBuffer,
      },
    });
    sys.setScene('run');
    await sys.unlock();
    await flush();
    pushTransient(sys.driver.params, TK.grunt, 1, 0, 0, 0.08);
    pushTransient(sys.driver.params, TK.checkpoint, 1);
    sys.update(blankState(), 1 / 60);
    expect(sys.driver.packed[P_TRANSIENT_COUNT]).toBe(1);
    expect(sys.driver.packed[P_HEADER]).toBe(TK.checkpoint);
    const voice = ctx.sources.find((source) => source.buffer?.tag === 'atlas')!;
    expect(voice.started?.[0]).toBeCloseTo(10.08);
    sys.setPaused(true);
    expect(voice.stopped).toBe(10);
    expect(voice.outputs).toHaveLength(0);
    sys.setPaused(false);
    pushTransient(sys.driver.params, TK.grunt, 1, 0, 0, 0.08);
    sys.update(blankState(), 1 / 60);
    const resumedVoice = ctx.sources.at(-1)!;
    sys.onEvent({ type: 'restart', checkpoint: -1, tick: 0 });
    expect(resumedVoice.stopped).toBe(10);
    expect(voice.stopped).toBe(10);
    expect(voice.outputs).toHaveLength(0);
    sys.dispose();
    expect(sys.samplePlayer).toBeNull();
  });

  it('pauses gameplay and model time while recorded music retains its source and phase', async () => {
    const ctx = new MockCtx();
    const sys = new WebAudioSystem({ context: ctx as unknown as AudioContext, forceFallback: true,
      music: { cues: CUES, fetchBytes: async (url) => new TextEncoder().encode(url).buffer as ArrayBuffer }, samples: false });
    sys.setScene('run');
    await sys.unlock();
    await flush();
    const state = blankState();
    state.bike.vel.x = 8;
    state.wheels.rear.spinVel = 20;
    sys.update(state, 1 / 60);
    const gameplay = (sys as unknown as { gameplay: MockGain }).gameplay;
    const musicSource = ctx.sources.at(-1)!;
    const time = sys.driver.scratch.time;
    const updates = sys.driver.scratch.updates;
    sys.setPaused(true);
    expect(gameplay.gain.value).toBe(0);
    for (let i = 0; i < 60; i++) sys.update(state, 1 / 120);
    expect(sys.driver.scratch.time).toBe(time);
    expect(sys.driver.scratch.updates).toBe(updates);
    expect(musicSource.stopped).toBeNull();
    expect(sys.musicPlayer!.playing).toBe('coast');
    sys.setPaused(false);
    sys.update(state, 1 / 60);
    expect(gameplay.gain.value).toBe(1);
    expect(sys.driver.scratch.updates).toBe(updates + 1);
    expect(musicSource.stopped).toBeNull();
    sys.setPaused(true);
    sys.setScene('menu'); // quitting pause restores the procedural front fallback path
    expect(gameplay.gain.value).toBe(1);
    expect(sys.driver.packed[P_ENGINE_GAIN]).toBe(0);
    expect(sys.driver.packed[P_TYRE_SPEED]).toBe(0);
    sys.update(state, 1 / 60);
    expect(sys.driver.packed[P_ENGINE_GAIN]).toBe(0);
    expect(sys.driver.packed[P_TYRE_SPEED]).toBe(0);
    sys.dispose();
  });

  it('with an injected (mock) context the loader path still runs: scene → fetch → decode → loop', async () => {
    Object.defineProperty(globalThis, 'navigator', { value: { webdriver: true }, configurable: true });
    const ctx = new MockCtx();
    const fetched: string[] = [];
    const sys = new WebAudioSystem({
      context: ctx as unknown as AudioContext,
      forceFallback: true,
      music: { cues: CUES, fetchBytes: async (u) => (fetched.push(u), new TextEncoder().encode(u).buffer as ArrayBuffer) },
    });
    sys.setScene('map');
    await sys.unlock();
    await flush();
    expect(sys.musicPlayer).not.toBeNull();
    expect(fetched[0]).toBe('./audio/map-bbbb.m4a');
    expect(sys.musicPlayer!.playing).toBe('map');
    const mix = ctx.compressors[0]!;
    expect(mix.threshold.value).toBe(-2.5);
    expect(mix.outputs).toEqual([ctx.destination]);
    expect((sys.musicPlayer!.output as unknown as MockGain).outputs).toEqual([mix]);
    const gameplay = (sys as unknown as { gameplay: MockGain }).gameplay;
    expect((sys.samplePlayer!.output as unknown as MockGain).outputs).toEqual([gameplay]);
    expect(ctx.compressors[1]!.outputs).toEqual([gameplay]);
    expect(gameplay.outputs).toEqual([mix]);
    sys.setMasterVolume(0.5);
    expect(sys.musicPlayer!.output.gain.value).toBeCloseTo(0.25);
    sys.setMusicVolume(0);
    expect(sys.musicPlayer!.output.gain.value).toBe(0);
    sys.dispose();
    expect(sys.musicPlayer).toBeNull();
    expect(ctx.sources[0]!.stopped).toBe(10); // fallback noise bed stops too
    for (const osc of ctx.oscillators) expect(osc.stopped).toBe(10);
    expect(mix.outputs).toHaveLength(0);
  });
});
