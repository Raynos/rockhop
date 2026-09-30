import { describe, expect, it } from 'vitest';
import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import { createParams, TK, type Transient } from '../params';
import { SamplePlayer, type SampleManifest } from './player';
import bank from './manifest.json';

class Param {
  value = 1;
  values: number[] = [];
  setValueAtTime(v: number): void { this.values.push(v); }
  linearRampToValueAtTime(v: number): void { this.values.push(v); }
  setTargetAtTime(v: number): void { this.values.push(v); }
}
class Node {
  disconnected = false;
  connect(): void {}
  disconnect(): void { this.disconnected = true; }
}
class Gain extends Node { gain = new Param(); }
class Panner extends Node { pan = new Param(); }
class Source extends Node {
  buffer: unknown;
  loop = false;
  loopStart = 0;
  loopEnd = 0;
  onended: (() => void) | null = null;
  started: number[] | null = null;
  stopped = false;
  fail = false;
  start(...args: number[]): void { if (this.fail) throw new Error('decoder unavailable'); this.started = args; }
  stop(): void { this.stopped = true; }
}
class Context {
  currentTime = 10;
  sources: Source[] = [];
  gains: Gain[] = [];
  panners: Panner[] = [];
  decodedBuffer: AudioBuffer | null = null;
  failStart = false;
  failDecode = false;
  decodes = 0;
  createGain(): Gain { const g = new Gain(); this.gains.push(g); return g; }
  createStereoPanner(): Panner { const p = new Panner(); this.panners.push(p); return p; }
  createBuffer(numberOfChannels: number, length: number, sampleRate: number): AudioBuffer {
    const channels = Array.from({ length: numberOfChannels }, () => new Float32Array(length));
    return { numberOfChannels, length, sampleRate, duration: length / sampleRate, getChannelData: (channel: number) => channels[channel]! } as AudioBuffer;
  }
  createBufferSource(): Source { const s = new Source(); s.fail = this.failStart; this.sources.push(s); return s; }
  decodeAudioData(_bytes: ArrayBuffer, callback: (a: AudioBuffer) => void): Promise<AudioBuffer> {
    this.decodes++;
    if (this.failDecode) return Promise.reject(new Error('decode failed'));
    const buffer = this.decodedBuffer ?? { duration: 12 } as AudioBuffer;
    callback(buffer); return Promise.resolve(buffer);
  }
}
const manifest: SampleManifest = {
  oneshots: { grunt: [{ file: 'atlas.mp3', start: .25, duration: 1, gain: .5 }] },
  beds: { coast: { file: 'coast.mp3', start: .2, duration: 10, gain: .7 } },
};
const transient: Transient = { kind: TK.grunt, gain: 1, delay: .2, pan: 0, pitch: 0 };
const settle = async (): Promise<void> => { for (let n = 0; n < 12; n++) await Promise.resolve(); };
function setup(files = manifest, fetchBytes: (url: string) => Promise<ArrayBuffer> = async () => new ArrayBuffer(1)) {
  const context = new Context();
  const coverage: { kinds: number[]; ambience: boolean }[] = [];
  const player = new SamplePlayer(context as unknown as BaseAudioContext, new Node() as unknown as AudioNode, { manifest: files, fetchBytes, onCoverage: (c) => coverage.push(c) });
  return { context, player, coverage };
}

describe('recorded sample lifecycle', () => {
  it('averages stereo reactions to mono without changing amplitude, metadata or panning; stereo beds stay intact', async () => {
    const { player, context } = setup({
      oneshots: { grunt: [{ file: 'atlas.mp3', start: 0, duration: .1, gain: .5 }] },
      beds: { coast: { file: 'coast.mp3', start: .02, duration: .12, gain: .7 } },
    });
    const stereo = context.createBuffer(2, 5120, 32000);
    const left = stereo.getChannelData(0), right = stereo.getChannelData(1);
    for (let frame = 0; frame < stereo.length; frame++) {
      left[frame] = [.8, -.5, .2][frame % 3]!;
      right[frame] = [.4, .5, -.8][frame % 3]!;
    }
    context.decodedBuffer = stereo;
    player.setScene('run'); await settle();
    const bed = context.sources.find((source) => source.loop)!;
    expect(bed.buffer).toBe(stereo);
    expect((bed.buffer as AudioBuffer).numberOfChannels).toBe(2);
    expect(player.playTransient({ ...transient, pan: .6 })).toBe(true);
    const shot = context.sources.find((source) => !source.loop)!;
    const mono = shot.buffer as AudioBuffer;
    expect(mono.numberOfChannels).toBe(1);
    expect(mono.length).toBe(stereo.length);
    expect(mono.sampleRate).toBe(stereo.sampleRate);
    expect(mono.duration).toBe(stereo.duration);
    for (let frame = 0; frame < mono.length; frame++) {
      expect(mono.getChannelData(0)[frame]).toBe(Math.fround((left[frame]! + right[frame]!) / 2));
    }
    expect(mono.getChannelData(0)[0]).toBeCloseTo(.6, 6); // no stereo summing boost or sqrt(0.5) loss
    expect(mono.getChannelData(0)[1]).toBe(0); // opposite stereo samples cancel in the arithmetic mean
    expect(left[0]).toBeCloseTo(.8, 6);
    expect(right[0]).toBeCloseTo(.4, 6); // the environment's original stereo PCM was not modified
    expect(context.panners.at(-1)!.pan.value).toBeCloseTo(.6);
    expect(context.gains.at(-1)!.gain.values).toContain(.5);
  });
  it('leaves synthesis available while loading or after a failed fetch', async () => {
    const { player, context } = setup(manifest, async () => { throw new Error('offline'); });
    expect(player.playTransient(transient)).toBe(false);
    await settle();
    expect(player.handles(TK.grunt)).toBe(false);
    expect(player.playTransient(transient)).toBe(false);
    expect(context.sources).toHaveLength(0);
  });
  it('retries failed atlas/current bed only on a run entry or explicit restart, preserving fallback until ready', async () => {
    const attempts = new Map<string, number>();
    const { player, coverage } = setup(manifest, async (url) => {
      const count = (attempts.get(url) ?? 0) + 1;
      attempts.set(url, count);
      if (count === 1) throw new Error('temporary network failure');
      return new ArrayBuffer(1);
    });
    const count = (file: string): number => attempts.get('./audio/sfx/' + file) ?? 0;
    await settle();
    expect(count('atlas.mp3')).toBe(1);
    player.update(createParams()); player.setVolume(.6); player.restart();
    await settle();
    expect(count('atlas.mp3')).toBe(1); // menu restarts do not retry
    player.setScene('run'); // entering the run retries the atlas and first-loads its bed
    expect(player.playTransient(transient)).toBe(false);
    expect(coverage.at(-1)?.ambience).toBe(false);
    await settle();
    expect(count('atlas.mp3')).toBe(2);
    expect(count('coast.mp3')).toBe(1);
    expect(player.playTransient(transient)).toBe(true);
    expect(coverage.at(-1)?.ambience).toBe(false);
    for (let frame = 0; frame < 5; frame++) { player.update(createParams()); player.setScene('run'); }
    player.setVolume(0); player.restart(); player.setVolume(1); player.restart(false);
    await settle();
    expect(count('coast.mp3')).toBe(1); // frames, mute/unmute and passive cleanup do not retry
    player.restart(); // active unmuted Retry is the second explicit recovery edge
    expect(coverage.at(-1)?.ambience).toBe(false);
    await settle();
    expect(count('coast.mp3')).toBe(2);
    expect(coverage.at(-1)?.ambience).toBe(true);
    expect(count('atlas.mp3')).toBe(2); // already decoded atlas is never redownloaded
  });
  it('retries a decode failure on reentering the run but stops all retries after disposal', async () => {
    let attempts = 0;
    const { player, context } = setup({ oneshots: manifest.oneshots, beds: {} }, async () => { attempts++; return new ArrayBuffer(1); });
    context.failDecode = true;
    await settle();
    expect(player.handles(TK.grunt)).toBe(false);
    player.setScene('run');
    await settle();
    expect(attempts).toBe(2);
    player.update(createParams()); player.setVolume(.5); player.setScene('run');
    await settle();
    expect(attempts).toBe(2);
    context.failDecode = false;
    player.setScene('map'); player.setScene('run');
    await settle();
    expect(attempts).toBe(3);
    expect(player.playTransient(transient)).toBe(true);
    player.dispose(); player.restart(); player.setScene('map'); player.setScene('run'); player.setVolume(1);
    await settle();
    expect(attempts).toBe(3);
    expect(player.playTransient(transient)).toBe(false);
  });
  it('does not decode an in-flight retry once disposed', async () => {
    let resolve: ((bytes: ArrayBuffer) => void) | undefined;
    let attempts = 0;
    const { player, context } = setup({ oneshots: manifest.oneshots, beds: {} }, async () => {
      attempts++;
      if (attempts === 1) throw new Error('temporary network failure');
      return new Promise<ArrayBuffer>((done) => { resolve = done; });
    });
    await settle(); player.setScene('run'); player.dispose();
    resolve!(new ArrayBuffer(1));
    await settle();
    expect(context.decodes).toBe(0);
    expect(player.handles(TK.grunt)).toBe(false);
    player.restart();
    expect(attempts).toBe(2);
  });
  it('retries only the current zone bed, leaving failures from departed zones alone', async () => {
    const attempts = new Map<string, number>();
    const { player } = setup({ oneshots: {}, beds: {
      coast: manifest.beds.coast!, alpine: { ...manifest.beds.coast!, file: 'alpine.mp3' },
    } }, async (url) => {
      attempts.set(url, (attempts.get(url) ?? 0) + 1);
      throw new Error('offline');
    });
    player.setScene('run'); await settle();
    player.setZone('alpine'); await settle();
    player.restart(); await settle();
    expect(attempts.get('./audio/sfx/coast.mp3')).toBe(1);
    expect(attempts.get('./audio/sfx/alpine.mp3')).toBe(2);
  });
  it('schedules decoded offsets and hard stops all delayed reactions on restart', async () => {
    const { player, context } = setup();
    await settle();
    expect(player.playTransient(transient)).toBe(true);
    expect(context.sources[0]?.started).toEqual([10.2, .25, 1]);
    player.restart();
    expect(context.sources[0]?.stopped).toBe(true);
    expect(context.sources[0]?.disconnected).toBe(true);
  });
  it('caps overlapping reactions, mutes immediately, and does not revive on unmute', async () => {
    const { player, context } = setup();
    await settle();
    for (let n = 0; n < 9; n++) expect(player.playTransient(transient)).toBe(true);
    expect(context.sources.filter((s) => !s.stopped)).toHaveLength(6);
    player.setVolume(0);
    expect(context.sources.every((s) => s.stopped)).toBe(true);
    expect(player.playTransient(transient)).toBe(false);
    player.setVolume(1);
    expect(context.sources).toHaveLength(9);
  });
  it('does not reset a live reaction on repeated run scene updates', async () => {
    const { player, context } = setup({ oneshots: manifest.oneshots, beds: {} });
    await settle(); player.setScene('run'); player.playTransient(transient);
    player.setScene('run');
    expect(context.sources[0]?.stopped).toBe(false);
    player.setScene('menu');
    expect(context.sources[0]?.stopped).toBe(true);
  });
  it('only suppresses ambience after decoding and stops beds on leaving the run', async () => {
    const { player, context, coverage } = setup();
    player.setScene('run');
    expect(coverage.at(-1)?.ambience).toBe(false);
    await settle(); player.update(createParams());
    expect(coverage.at(-1)?.ambience).toBe(true);
    expect(context.sources.find((s) => s.loop)?.started).toEqual([10, .2]);
    player.setScene('map');
    expect(coverage.at(-1)?.ambience).toBe(false);
    expect(context.sources.find((s) => s.loop)?.stopped).toBe(true);
  });
  it('falls back when scheduling throws and does not revive disposed asynchronous loads', async () => {
    const { player, context } = setup();
    await settle(); context.failStart = true;
    expect(player.playTransient(transient)).toBe(false);
    expect(context.sources[0]?.disconnected).toBe(true);
    player.dispose();
    expect(player.handles(TK.grunt)).toBe(false);
    expect(player.playTransient(transient)).toBe(false);
    const later = setup(); later.player.dispose(); await settle();
    expect(later.player.handles(TK.grunt)).toBe(false);
    expect(later.context.sources).toHaveLength(0);
  });
});

describe('new recorded bank delivery', () => {
  it('references only immutable MP3 files with matching content hashes', () => {
    const declared = bank as SampleManifest;
    const clips = [...Object.values(declared.oneshots).flatMap((list) => list ?? []), ...Object.values(declared.beds).filter((clip) => clip !== undefined)];
    const checked = new Set<string>();
    let bytes = 0;
    for (const clip of clips) {
      expect(clip.file).toMatch(/^(?:reactions|bed-(?:coast|alpine|quarry|snowline))-[0-9a-f]{12}\.mp3$/);
      expect(clip.start).toBeGreaterThanOrEqual(0);
      expect(clip.duration).toBeGreaterThan(0);
      expect(Number.isFinite(clip.gain)).toBe(true);
      if (checked.has(clip.file)) continue;
      const data = readFileSync(new URL('../../../public/audio/sfx/' + clip.file, import.meta.url));
      const digest = createHash('sha256').update(data).digest('hex').slice(0, 12);
      expect(clip.file.endsWith(digest + '.mp3')).toBe(true);
      checked.add(clip.file); bytes += data.length;
    }
    expect(bytes).toBeLessThan(1024 * 1024);
  });
});
