import { afterEach, describe, expect, it } from 'vitest';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import { ROCKHOP_TRACKS } from '../../src/tracks/rockhop';
import { srcFingerprint } from '../lib/metrics';
import { campaignBikeForTrack, REFLEX_TRACKS, reflexRows, STRANGER_TRACKS, strangerRows } from './ship-gate';

const tempDirs: string[] = [];
const fixtureDir = (): string => {
  const dir = fs.mkdtempSync(path.join(os.tmpdir(), 'rockhop-gate-rows-'));
  tempDirs.push(dir);
  return dir;
};
const write = (dir: string, name: string, data: unknown): void => {
  fs.writeFileSync(path.join(dir, name), `${JSON.stringify(data)}\n`);
};

afterEach(() => {
  for (const dir of tempDirs.splice(0)) fs.rmSync(dir, { recursive: true, force: true });
});

describe('ship gate G10 campaign rows', () => {
  it('judges exactly the twelve shipped courses on Rookie 1–8 and Pro 9–12', () => {
    const ids = ROCKHOP_TRACKS.map((track) => track.id);
    expect(ids).toHaveLength(12);
    expect(STRANGER_TRACKS).toEqual(ids);
    expect(REFLEX_TRACKS).toEqual(ids);
    expect(ids.map(campaignBikeForTrack)).toEqual([...Array(8).fill('rookie'), ...Array(4).fill('pro')]);
    expect(() => campaignBikeForTrack('b1-first-ride')).toThrow(/Not a shipped/);
  });

  it('arms only fresh sessions on the authored career bike, regardless of an old report header', () => {
    const dir = fixtureDir();
    const fresh = srcFingerprint();
    const session = (sessionId: string, bike: 'rookie' | 'pro', strangerAttempts: number, stamp = fresh, status = 'done') =>
      ({ sessionId, bike, strangerAttempts, srcFingerprint: stamp, status, cleared: true });
    write(dir, 'c1-low-tide.stranger.json', {
      attemptsBand: [1, 3], bike: 'pro', sessions: [
        session('rookie-1', 'rookie', 1), session('rookie-2', 'rookie', 2),
        session('wrong-bike', 'pro', 9), session('stale', 'rookie', 9, '00000000'),
        session('still-playing', 'rookie', 9, fresh, 'in-progress'),
      ],
    });
    write(dir, 'd3-rope-walk.stranger.json', {
      attemptsBand: [2, 4], bike: 'rookie', sessions: [
        session('pro-1', 'pro', 8), session('pro-2', 'pro', 10),
        session('wrong-bike', 'rookie', 1), session('stale', 'pro', 20, '00000000'),
      ],
    });
    write(dir, 's3-whiteout.stranger.json', {
      attemptsBand: [2, 4], bike: 'rookie', sessions: [
        session('wrong-bike', 'rookie', 1), session('stale', 'pro', 2, '00000000'),
      ],
    });
    const rows = strangerRows(['c1-low-tide', 'd3-rope-walk', 's3-whiteout'], 1.5, dir);
    expect(rows.map((row) => [row.trackId, row.bike, row.completedFresh, row.medianAttempts, row.pass])).toEqual([
      ['c1-low-tide', 'rookie', 2, 1.5, true],
      ['d3-rope-walk', 'pro', 2, 9, false],
      ['s3-whiteout', 'pro', 0, null, null],
    ]);
    expect(rows[0]?.censored).toBe(1);
    expect(rows[1]?.sessions).toEqual(['pro-1', 'pro-2']);
    expect(rows.filter((row) => row.completedFresh >= 2).map((row) => row.trackId))
      .toEqual(['c1-low-tide', 'd3-rope-walk']);
  });

  it('selects current-career-bike reflex files and leaves stale or mislabeled seeds unarmed', () => {
    const dir = fixtureDir();
    const fresh = srcFingerprint();
    const report = (trackId: string, bike: 'rookie' | 'pro', stamp = fresh) => ({
      trackId, bike, srcFingerprint: stamp, attemptsBand: [2, 4],
      bySkill: [{ skill: 'average', seeds: [1, 2, 3], medianAttempts: 3, medianFinishTime: 36,
        clears: 3, deaths: [] }],
    });
    write(dir, 'c1-low-tide.reflex.json', report('c1-low-tide', 'rookie'));
    write(dir, 'd3-rope-walk.reflex.json', report('d3-rope-walk', 'rookie'));
    write(dir, 'd3-rope-walk.pro.reflex.json', report('d3-rope-walk', 'pro'));
    write(dir, 's3-whiteout.pro.reflex.json', report('s3-whiteout', 'pro', '00000000'));
    write(dir, 's2-cornice.pro.reflex.json', report('s2-cornice', 'rookie'));
    const rows = reflexRows(['c1-low-tide', 'd3-rope-walk', 's3-whiteout', 's2-cornice'], 1.5, 'average', undefined, dir);
    expect(rows.map((row) => [row.trackId, row.seedsFresh, row.pass])).toEqual([
      ['c1-low-tide', 3, true], ['d3-rope-walk', 3, true],
      ['s3-whiteout', 0, null], ['s2-cornice', 0, null],
    ]);
    expect(reflexRows(['c1-low-tide', 'd3-rope-walk'], 1.5, 'average', 'pro', dir)
      .map((row) => row.trackId)).toEqual(['d3-rope-walk']);
  });
});
