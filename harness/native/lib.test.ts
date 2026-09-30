import { afterEach, describe, expect, it } from 'vitest';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { ROCKHOP_TRACKS } from '../../src/tracks/rockhop';
import careerGate from './career-gate.json';
import { armFor, type GateManifest } from './lib';

const dirs: string[] = [];
const fixture = (): string => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'rockhop-native-gate-'));
  dirs.push(dir);
  fs.mkdirSync(path.join(dir, 'gate'));
  return dir;
};
const recording = (dir: string, name: string, trackId?: string): string => {
  const file = `gate/${name}.json`;
  fs.writeFileSync(path.join(dir, file), JSON.stringify({ header: { trackId } }));
  return file;
};

afterEach(() => {
  for (const dir of dirs.splice(0)) fs.rmSync(dir, { recursive: true, force: true });
});

describe('native debug career gate', () => {
  it('defaults to exactly the shipping Rookie 1–8 and Pro 9–12 recordings plus a C1 crash', () => {
    expect(careerGate.clear).toEqual(ROCKHOP_TRACKS.map(({ id }, index) =>
      `harness/inputs/${id}/${index < 8 ? 'bot-3' : 'bot-3-pro'}.json`));
    expect(careerGate.crash).toBe('harness/inputs/c1-low-tide/crash.json');
    for (const [index, file] of careerGate.clear.entries()) {
      const { header } = JSON.parse(fs.readFileSync(file, 'utf8')) as { header: { trackId: string; bike: string } };
      expect([header.trackId, header.bike]).toEqual([ROCKHOP_TRACKS[index]?.id, index < 8 ? 'rookie' : 'pro']);
    }
    const { header } = JSON.parse(fs.readFileSync(careerGate.crash, 'utf8')) as { header: { trackId: string; bike: string } };
    expect([header.trackId, header.bike]).toEqual(['c1-low-tide', 'rookie']);
  });

  it('boots and restarts on the first selected bundled clear, including an overridden set', () => {
    const dir = fixture();
    const c1 = recording(dir, 'c1', 'c1-low-tide');
    const d3 = recording(dir, 'd3', 'd3-rope-walk');
    const m: GateManifest = { clear: [c1, d3], crash: 'gate/c1-crash.json', sources: [] };
    expect(armFor(m, {}, dir)).toMatchObject({ clear: [c1, d3], track: 'c1-low-tide', crash: m.crash });
    expect(armFor(m, { clear: [d3] }, dir)).toMatchObject({ clear: [d3], track: 'd3-rope-walk' });
    expect(armFor(m, { track: 'flat-test' }, dir).track).toBe('flat-test');
  });

  it('rejects missing or malformed selected recordings unless a legacy track is explicit', () => {
    const dir = fixture();
    const bad = recording(dir, 'bad');
    const m: GateManifest = { clear: [bad], crash: 'gate/crash.json', sources: [] };
    expect(() => armFor(m, {}, dir)).toThrow(/header\.trackId/);
    expect(() => armFor({ ...m, clear: [] }, {}, dir)).toThrow(/clear recording/);
    expect(armFor(m, { track: 'flat-test' }, dir).track).toBe('flat-test');
  });
});
