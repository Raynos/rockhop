/**
 * Local per-track leaderboard (docs/design/game.md § leaderboard): top 5 per track per class in
 * `rockhop.best.<id>[@pro]#board`, seeded from a pre-board PB, additive to the PB entries.
 */
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import type { RunResult } from '../core/types';
import { registerTrack } from '../tracks';
import { BOARD_SIZE, BestTimes, bestKey, boardKey } from './best';

const ROUTE_TRACK_ID = 'best-route-proof-test';
registerTrack({ id: ROUTE_TRACK_ID, name: 'Route proof', tier: 'hard', seed: 1,
  profile: [{ x: 0, y: 0 }, { x: 100, y: 0 }], obstacles: [{ kind: 'open-platform', pos: { x: 30, y: 0 }, params: { length: 20, height: 2.5 } }],
  checkpoints: [], start: { pos: { x: 0, y: 0 }, angle: 0 }, finishX: 80,
  diamondGoal: { id: 'bridge', platformObstacleIndex: 0, x: 40, minRearY: 2.7 } });

class MemStorage implements Storage {
  private m = new Map<string, string>();
  get length(): number {
    return this.m.size;
  }
  clear(): void {
    this.m.clear();
  }
  getItem(k: string): string | null {
    return this.m.get(k) ?? null;
  }
  key(i: number): string | null {
    return [...this.m.keys()][i] ?? null;
  }
  removeItem(k: string): void {
    this.m.delete(k);
  }
  setItem(k: string, v: string): void {
    this.m.set(k, v);
  }
}

const run = (time: number, faults = 0, bike: 'rookie' | 'pro' = 'rookie'): RunResult => ({
  trackId: 'b1',
  time,
  faults,
  medal: faults === 0 && time < 20 ? 'gold' : 'bronze',
  personalBest: false,
  previousBest: null,
  targetTimeS: 20,
  bike,
});

describe('BestTimes.board', () => {
  const g = globalThis as { localStorage?: Storage | undefined };
  let saved: Storage | undefined;
  beforeEach(() => {
    saved = g.localStorage;
    g.localStorage = new MemStorage();
  });
  afterEach(() => {
    if (saved) g.localStorage = saved;
    else delete g.localStorage;
  });

  it('keeps the best five per track per class, fastest first, and returns the rank', () => {
    const b = new BestTimes();
    expect(b.board('b1', 'rookie')).toEqual([]);
    expect(b.record('b1', run(30))).toBe(1);
    expect(b.record('b1', run(25))).toBe(1);
    expect(b.record('b1', run(35))).toBe(3);
    expect(b.record('b1', run(31))).toBe(3);
    expect(b.record('b1', run(40))).toBe(5);
    expect(b.record('b1', run(41))).toBeNull(); // outside the top 5
    expect(b.record('b1', run(19))).toBe(1);
    const rows = b.board('b1', 'rookie');
    expect(rows.map((r) => r.time)).toEqual([19, 25, 30, 31, 35]);
    expect(rows).toHaveLength(BOARD_SIZE);
    expect(rows[0]!.medal).toBe('gold');
    // Pro is its own board.
    expect(b.board('b1', 'pro')).toEqual([]);
    expect(b.record('b1', run(50, 2, 'pro'))).toBe(1);
    expect(b.board('b1', 'rookie').map((r) => r.time)).toEqual([19, 25, 30, 31, 35]);
    // Persisted under the best-times prefix; a fresh store reads the same rows.
    expect(JSON.parse(localStorage.getItem(boardKey('b1', 'rookie'))!)).toHaveLength(5);
    expect(new BestTimes().board('b1', 'pro').map((r) => r.time)).toEqual([50]);
  });

  it('a pre-board PB seeds the board with one row and is not duplicated by the run that beats it', () => {
    localStorage.setItem(bestKey('b1', 'rookie'), JSON.stringify({ time: 28, faults: 1, medal: 'silver' }));
    const b = new BestTimes();
    expect(b.board('b1', 'rookie')).toEqual([{ time: 28, faults: 1, medal: 'silver', at: '' }]);
    // The game records before it stores the new PB (game.ts publishResults).
    const r = { ...run(27), personalBest: true, previousBest: 28 };
    expect(b.record('b1', r)).toBe(1);
    b.put('b1', r, { splits: [], recording: null });
    expect(b.board('b1', 'rookie').map((x) => x.time)).toEqual([27, 28]);
    expect(b.get('b1', 'rookie')?.time).toBe(27);
  });

  it('ties keep the earlier run ahead unless the new one has fewer faults; reset progress clears the board', () => {
    const b = new BestTimes();
    b.record('b1', run(30, 2));
    expect(b.record('b1', run(30, 2))).toBe(2);
    expect(b.record('b1', run(30, 0))).toBe(1);
    b.clear();
    expect(b.board('b1', 'rookie')).toEqual([]);
    expect(localStorage.getItem(boardKey('b1', 'rookie'))).toBeNull();
  });

  it('a corrupt board is an empty board, never a throw', () => {
    localStorage.setItem(boardKey('b1', 'rookie'), '{not json');
    expect(new BestTimes().board('b1', 'rookie')).toEqual([]);
    localStorage.setItem(boardKey('b1', 'rookie'), JSON.stringify([{ time: 'x' }, { time: 12, faults: 0, medal: 'nope' }]));
    expect(new BestTimes().board('b1', 'rookie')).toEqual([{ time: 12, faults: 0, medal: 'bronze', at: '' }]);
  });

  it('keeps a slower clean run\'s higher medal without replacing the PB ghost or its board medal', () => {
    const b = new BestTimes();
    const fast = { ...run(25, 1), medal: 'gold' as const };
    b.record('b1', fast);
    b.put('b1', fast, { splits: [12], recording: 'fast-input' });
    const clean = { ...run(27), medal: 'platinum' as const };
    b.record('b1', clean);
    b.recordMedal('b1', clean.medal, 'rookie');

    expect(b.get('b1', 'rookie')).toMatchObject({ time: 25, medal: 'gold', bestMedal: 'platinum', splits: [12], recording: 'fast-input' });
    expect(b.get('b1')).toMatchObject({ time: 25, medal: 'platinum' });
    expect(b.board('b1', 'rookie').map((r) => [r.time, r.medal])).toEqual([[25, 'gold'], [27, 'platinum']]);

    const faster = { ...run(24, 2), medal: 'bronze' as const };
    b.put('b1', faster, { splits: [11], recording: 'faster-input' });
    expect(new BestTimes().get('b1', 'rookie')).toMatchObject({ time: 24, medal: 'bronze', bestMedal: 'platinum', recording: 'faster-input' });
    expect(new BestTimes().get('b1')?.medal).toBe('platinum');
  });

  it('migrates a legacy PB medal into the career maximum when a slower run improves it', () => {
    localStorage.setItem(bestKey('b1', 'rookie'), JSON.stringify({ time: 28, faults: 1, medal: 'silver', recording: 'legacy' }));
    const b = new BestTimes();
    b.recordMedal('b1', 'gold', 'rookie');
    expect(new BestTimes().get('b1', 'rookie')).toMatchObject({ time: 28, medal: 'silver', bestMedal: 'gold', recording: 'legacy' });
    expect(new BestTimes().get('b1')?.medal).toBe('gold');
    expect(new BestTimes().board('b1', 'rookie')[0]?.medal).toBe('silver');
  });

  it('grandfathers old route medals and stores proof plus replay for a slower new top-medal run', () => {
    localStorage.setItem(bestKey(ROUTE_TRACK_ID, 'rookie'), JSON.stringify({ time: 20, faults: 0, medal: 'platinum', recording: 'legacy' }));
    localStorage.setItem(boardKey(ROUTE_TRACK_ID, 'rookie'), JSON.stringify([{ time: 20, faults: 0, medal: 'platinum', at: '' }]));
    const b = new BestTimes();
    expect(b.get(ROUTE_TRACK_ID, 'rookie')).toMatchObject({ medal: 'platinum', legacyRouteMedal: true });
    expect(b.board(ROUTE_TRACK_ID, 'rookie')[0]).toMatchObject({ medal: 'platinum', legacyRouteMedal: true });
    const proof = { goalId: 'bridge', crossed: true };
    b.recordMedal(ROUTE_TRACK_ID, 'platinum', 'rookie', proof, 'proved-input');
    expect(b.get(ROUTE_TRACK_ID, 'rookie')).toMatchObject({ time: 20, medal: 'platinum', legacyRouteMedal: true, bestMedal: 'platinum', bestMedalRouteProof: proof, bestMedalRecording: 'proved-input', recording: 'legacy' });
    expect(new BestTimes().get(ROUTE_TRACK_ID, 'rookie')).toMatchObject({ time: 20, medal: 'platinum', legacyRouteMedal: true, bestMedal: 'platinum', bestMedalRouteProof: proof, bestMedalRecording: 'proved-input', recording: 'legacy' });
    expect(new BestTimes().get(ROUTE_TRACK_ID)?.medal).toBe('platinum');
    b.record(ROUTE_TRACK_ID, { ...run(23), trackId: ROUTE_TRACK_ID, medal: 'platinum' });
    expect(b.board(ROUTE_TRACK_ID, 'rookie')[1]?.medal).toBe('gold'); // a new unproved claim is capped
    const slower = { ...run(24), trackId: ROUTE_TRACK_ID, medal: 'platinum' as const, routeProof: proof };
    b.record(ROUTE_TRACK_ID, slower);
    expect(new BestTimes().board(ROUTE_TRACK_ID, 'rookie')[2]).toMatchObject({ medal: 'platinum', routeProof: proof });
  });

  it('requires proof for fresh PB and career writes, while retaining a slower proved medal replay', () => {
    const b = new BestTimes();
    const unproved = { ...run(20), trackId: ROUTE_TRACK_ID, medal: 'platinum' as const };
    b.put(ROUTE_TRACK_ID, unproved, { splits: [], recording: 'fast-input' });
    b.recordMedal(ROUTE_TRACK_ID, 'platinum', 'rookie');
    expect(b.get(ROUTE_TRACK_ID, 'rookie')).toMatchObject({ medal: 'gold', bestMedal: 'gold', recording: 'fast-input' });

    const proof = { goalId: 'bridge', crossed: true };
    b.recordMedal(ROUTE_TRACK_ID, 'platinum', 'rookie', proof, 'slower-proved-input');
    expect(new BestTimes().get(ROUTE_TRACK_ID, 'rookie')).toMatchObject({
      time: 20, medal: 'gold', bestMedal: 'platinum', recording: 'fast-input',
      bestMedalRouteProof: proof, bestMedalRecording: 'slower-proved-input',
    });
  });
});
