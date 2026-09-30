/** Exercise the actual browser evaluator with fake decoded PCM, without opening any audio context. */
import fs from 'node:fs';
import vm from 'node:vm';
import { describe, expect, it } from 'vitest';

const file = fs.readFileSync('harness/audio-remaster/decode.ts', 'utf8');
const evaluator = file.match(/const decodeSource = String\.raw`([\s\S]+?)`;/)?.[1];
if (!evaluator) throw new Error('Missing decoder evaluator');
interface Alignment { nativeOffsetSamples: number; correlation: number; nativeRmsGainDb: number }
interface Job { file: string; bytes: number; windows: never[]; alignment: { name: string; startSample: number; stride: number; samples: number[] }[] }

async function measure(gain: number, delay: number, dc: number): Promise<Alignment> {
  const rate = 48000;
  const frames = 24000;
  const reference = [new Float32Array(frames), new Float32Array(frames)];
  let seed = 19;
  const random = (): number => {
    seed = (Math.imul(seed, 1664525) + 1013904223) >>> 0;
    return seed / 4294967296 - 0.5;
  };
  for (const channel of reference) {
    let previous = 0;
    for (let i = 0; i < frames; i++) {
      previous = previous * 0.85 + random() * 0.15;
      channel[i] = previous;
    }
  }
  const native = [new Float32Array(frames), new Float32Array(frames)];
  for (let channel = 0; channel < 2; channel++) {
    for (let i = 0; i < frames; i++) {
      const target = i + delay;
      if (target >= 0 && target < frames) native[channel]![target] = gain * reference[channel]![i]! + dc;
    }
  }
  const buffer = { sampleRate: rate, numberOfChannels: 2, length: frames, duration: frames / rate,
    getChannelData: (channel: number) => native[channel]! };
  class FakeOfflineContext {
    decodeAudioData(_bytes: ArrayBuffer, resolve: (pcm: typeof buffer) => void): Promise<typeof buffer> {
      resolve(buffer);
      return Promise.resolve(buffer);
    }
  }
  const decode = vm.runInNewContext(`(${evaluator})`, {
    OfflineAudioContext: FakeOfflineContext,
    fetch: async () => ({ ok: true, arrayBuffer: async () => new ArrayBuffer(4) }),
  }) as (job: Job) => Promise<{ alignment: Alignment[] }>;
  const start = 10000;
  const stride = 6;
  const samples = Array.from({ length: 1200 }, (_, i) => (reference[0]![start + i * stride]! + reference[1]![start + i * stride]!) / 2);
  const result = await decode({ file: 'synthetic.mp3', bytes: 4, windows: [], alignment: [{ name: 'stereo-probe', startSample: start, stride, samples }] });
  return result.alignment[0]!;
}

describe('native decoder alignment and gain measurements', () => {
  it('finds positive codec delay and measures extra gain despite perfect correlation and DC shift', async () => {
    const result = await measure(1.75, 73, 0.1);
    expect(result.nativeOffsetSamples).toBe(73);
    expect(result.correlation).toBeCloseTo(1, 6);
    expect(result.nativeRmsGainDb).toBeCloseTo(20 * Math.log10(1.75), 5);
  });

  it('finds earlier native samples and reports attenuation with the correct dB sign', async () => {
    const result = await measure(0.5, -41, -0.05);
    expect(result.nativeOffsetSamples).toBe(-41);
    expect(result.correlation).toBeCloseTo(1, 6);
    expect(result.nativeRmsGainDb).toBeCloseTo(20 * Math.log10(0.5), 5);
  });
});
