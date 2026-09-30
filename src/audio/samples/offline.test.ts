import { describe, expect, it } from 'vitest';
import { createParams, pushTransient, TK } from '../params';
import { OfflineSampleMixer, type SamplePCM } from './offline';
import type { SampleManifest } from './player';
const manifest: SampleManifest = { oneshots: { grunt: [{ file: 'voice', start: .1, duration: .2, gain: .5 }] }, beds: { coast: { file: 'bed', start: 0, duration: 1, gain: .7 } } };
const pcm = new Map<string, SamplePCM>([['voice', { sampleRate: 1000, channels: [new Float32Array(1000).fill(.25)] }], ['bed', { sampleRate: 1000, channels: [new Float32Array(1000).fill(.1), new Float32Array(1000).fill(.2)] }]]);
function render(): Float32Array {
  const mixer = new OfflineSampleMixer(1000, manifest, pcm);
  const p = createParams();
  p.ambientGain = 0; pushTransient(p, TK.grunt, 1, 0, 0, .1);
  mixer.consume(p);
  const left = new Float32Array(400), right = new Float32Array(400);
  mixer.process(left, right, 0, 200);
  p.transientCount = 0; mixer.consume(p); mixer.process(left, right, 200, 200);
  return left;
}
describe('offline recorded sample mixer', () => {
  it('emits byte-identical PCM and honors delayed attack/atlas offset/finite duration', () => {
    expect(new Uint8Array(render().buffer)).toEqual(new Uint8Array(render().buffer));
    const result = render();
    expect(result.slice(0, 101).every((n) => n === 0)).toBe(true);
    expect(result[110]).toBeCloseTo(.25 * .5 * Math.SQRT1_2, 6);
    expect(result.slice(300).every((n) => n === 0)).toBe(true);
  });
  it('retains every unavailable procedural family and suppresses only decoded clips', () => {
    const mixer = new OfflineSampleMixer(1000, manifest, pcm);
    const p = createParams(); pushTransient(p, TK.grunt, 1); pushTransient(p, TK.crowdCheer, 1); pushTransient(p, TK.landing, 1);
    expect(mixer.consume(p).map((t) => t.kind)).toEqual([TK.crowdCheer, TK.landing]);
    const noVoice = new OfflineSampleMixer(1000, manifest, new Map());
    expect(noVoice.consume(p)).toHaveLength(3);
    expect(noVoice.ambienceCovered).toBe(false);
  });
  it('purges a pending reaction at restart and master mute', () => {
    const mixer = new OfflineSampleMixer(1000, manifest, pcm);
    const p = createParams(); p.ambientGain = 0; pushTransient(p, TK.grunt, 1, 0, 0, .3); mixer.consume(p);
    p.transientCount = 0; pushTransient(p, TK.restart, 1); expect(mixer.consume(p)[0]?.kind).toBe(TK.restart);
    const left = new Float32Array(800), right = new Float32Array(800); mixer.process(left, right, 0, 400);
    p.transientCount = 0; pushTransient(p, TK.grunt, 1); mixer.consume(p); mixer.process(left, right, 400, 200, 0); mixer.process(left, right, 600, 200);
    expect(left.every((n) => n === 0)).toBe(true);
  });
  it('uses both bed channels and returns ambience coverage on leaving run or absent zones', () => {
    const mixer = new OfflineSampleMixer(1000, manifest, pcm);
    const p = createParams(); p.ambientGain = 1; mixer.consume(p);
    const l = new Float32Array(100), r = new Float32Array(100); mixer.process(l, r, 0, 100);
    expect(mixer.ambienceCovered).toBe(true); expect(r[99]).toBeCloseTo(l[99]! * 2, 6);
    mixer.setScene('menu'); expect(mixer.ambienceCovered).toBe(false);
    mixer.setScene('run'); mixer.setZone('alpine'); expect(mixer.ambienceCovered).toBe(false);
  });
});
