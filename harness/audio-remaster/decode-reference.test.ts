/** Real FFmpeg calibration, silent PCM only; never opens a browser or audio context. */
import { spawnSync } from 'node:child_process';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { decodeStereoReference } from './decode-reference';

function calibration(channels: 1 | 2, check: (file: string, original: Buffer) => void): void {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'rockhop-audio-reference-'));
  try {
    const original = Buffer.alloc(4800 * channels * 4);
    for (let frame = 0; frame < 4800; frame++) {
      original.writeFloatLE(.5 * Math.sin(frame * 2 * Math.PI * 997 / 48000), frame * channels * 4);
      if (channels === 2) original.writeFloatLE(.23 * Math.sin(frame * 2 * Math.PI * 1823 / 48000 + .7), (frame * 2 + 1) * 4);
    }
    const file = path.join(directory, 'calibration.wav');
    const encoded = spawnSync('ffmpeg', ['-v', 'error', '-f', 'f32le', '-ac', String(channels), '-ar', '48000', '-i', 'pipe:0', '-c:a', 'pcm_f32le', file], { input: original });
    expect(encoded.status, encoded.stderr.toString()).toBe(0);
    check(file, original);
  } finally { fs.rmSync(directory, { recursive: true, force: true }); }
}

function meanEnergy(stereo: Buffer): number {
  let energy = 0;
  for (let offset = 0; offset < stereo.length; offset += 8) {
    const mean = (stereo.readFloatLE(offset) + stereo.readFloatLE(offset + 4)) / 2;
    energy += mean * mean;
  }
  return energy;
}

describe('FFmpeg channel mapping calibration', () => {
  it('corrects the default -3.01 dB mono upmix and preserves each original sample at unity gain', () => {
    calibration(1, (file, original) => {
      const reference = decodeStereoReference(file);
      const control = spawnSync('ffmpeg', ['-v', 'error', '-i', file, '-f', 'f32le', '-ac', '2', '-ar', '48000', 'pipe:1']);
      expect(control.status).toBe(0);
      expect(reference.sourceChannels).toBe(1);
      expect(reference.pcm.length).toBe(original.length * 2);
      let sourceEnergy = 0;
      for (let offset = 0; offset < original.length; offset += 4) {
        const sample = original.readFloatLE(offset);
        sourceEnergy += sample * sample;
        expect(reference.pcm.readFloatLE(offset * 2)).toBe(sample);
        expect(reference.pcm.readFloatLE(offset * 2 + 4)).toBe(sample);
      }
      expect(10 * Math.log10(meanEnergy(control.stdout) / sourceEnergy)).toBeCloseTo(-3.0102999566, 5);
      expect(10 * Math.log10(meanEnergy(reference.pcm) / sourceEnergy)).toBeCloseTo(0, 7);
    });
  });

  it('preserves distinct stereo L/R samples without any upmix attenuation', () => {
    calibration(2, (file, original) => {
      const reference = decodeStereoReference(file);
      expect(reference.sourceChannels).toBe(2);
      expect(reference.pcm.equals(original)).toBe(true);
      expect(10 * Math.log10(meanEnergy(reference.pcm) / meanEnergy(original))).toBe(0);
    });
  });
});
