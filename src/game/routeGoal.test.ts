import { describe, expect, it } from 'vitest';
import { decodeJSON, encodeJSON } from '../core/replay';
import type { CompiledTrack, TrackDef } from '../core/types';
import type { GameRenderer } from '../render';
import { createBikePhysicsV2 } from '../physics';
import { compileTrack, registerTrack, TrackCompileError } from '../tracks';
import { Game } from './game';
import { hashRouteRunState } from './routeGoal';
import { medalFor } from './rules';

function track(id: string, upper: boolean): TrackDef {
  return {
    id, name: 'Route proof', tier: 'beginner', seed: 712,
    profile: [{ x: -10, y: 0 }, { x: 120, y: 0 }],
    obstacles: [{ kind: 'open-platform', pos: { x: 20, y: 0 }, params: { length: 30, height: 2.5, thickness: 0.18, surface: 'wood' } }],
    checkpoints: [], start: { pos: upper ? { x: 21, y: 2.5 } : { x: 0, y: 0 }, angle: 0 }, finishX: 65,
    diamondGoal: { id: 'upper-deck', platformObstacleIndex: 0, x: 35, minRearY: 2.7 },
    meta: { biome: 'industrial', technique: 'cross the upper deck', targetTimeS: 90 },
  };
}

const upper = track('route-goal-test-upper', true);
const lower = track('route-goal-test-lower', false);
registerTrack(upper);
registerTrack(lower);

function game(): Game {
  const renderer = {
    setTrack(_track: CompiledTrack) {}, setRunInfo() {}, onEvent() {},
    render() { return 0; }, finish() {}, resize() {}, dispose() {}, setQuality() {},
    stats() { return { calls: 0, triangles: 0, points: 0, lines: 0, geometries: 0, textures: 0, programs: 0, texturesMB: 0, renderer: 'stub', contextKind: 'none' }; },
  } as unknown as GameRenderer;
  return new Game({ physics: createBikePhysicsV2(120), renderer, autoSkipCountdown: true, autoRecord: true, physicsVersion: 'v2' });
}

describe('opt-in Diamond route engine', () => {
  it('keeps the historical hash on ordinary tracks and hashes opt-in route state', () => {
    const physicsHash = 'old-physics-hash';
    expect(hashRouteRunState(physicsHash, undefined, false)).toBe(physicsHash);
    expect(hashRouteRunState(physicsHash, upper.diamondGoal, true)).not.toBe(hashRouteRunState(physicsHash, upper.diamondGoal, false));
  });

  it('compiles an open upper deck and rejects malformed goal/clearance', () => {
    const compiled = compileTrack(upper);
    const deck = compiled.colliders.find((c) => c.obstacleIndex === 0);
    expect(deck).toMatchObject({ kind: 'polyline', oneWay: true, points: [{ x: 20, y: 2.5 }, { x: 50, y: 2.5 }] });
    expect(compiled.colliders[0]).toMatchObject({ kind: 'polyline', obstacleIndex: -1 });
    expect(() => compileTrack({ ...upper, diamondGoal: { ...upper.diamondGoal!, platformObstacleIndex: 1 } })).toThrow(TrackCompileError);
    expect(() => compileTrack({ ...upper, obstacles: [{ ...upper.obstacles[0]!, params: { ...upper.obstacles[0]!.params, height: 1 } }] })).toThrow(/clearance/);
    expect(() => compileTrack({ ...upper, obstacles: [...upper.obstacles, { kind: 'box', pos: { x: 33, y: 0 }, params: { width: 2, height: 3 } }] })).toThrow(/intersects obstacle/);
  });

  it('caps a fast lower clear at Gold and saves a grounded upper crossing in result and JSON replay', () => {
    for (const [def, expectedMedal, expectedProof] of [[upper, 'platinum', true], [lower, 'gold', false]] as const) {
      const live = game();
      expect(live.loadTrack(def.id)).toBe(true);
      for (let tick = 0; tick < 2400 && live.phase() !== 'finished'; tick++) {
        live.setInput({ throttle: 0.65, lean: 0.2 });
        live.step(1);
      }
      expect(live.phase()).toBe('finished');
      const finishHash = live.hashState();
      live.step(48);
      expect(live.faults()).toBe(0);
      expect(live.counters().diamondRouteCrossed).toBe(expectedProof);
      expect(live.result()).toMatchObject({ medal: expectedMedal, routeProof: { goalId: 'upper-deck', crossed: expectedProof } });
      const saved = live.lastRunRecording();
      expect(saved).not.toBeNull();
      expect(decodeJSON(saved!.json).header.routeProof).toEqual({ goalId: 'upper-deck', crossed: expectedProof });
      const replay = game();
      const tampered = decodeJSON(saved!.json);
      tampered.header.routeProof = { goalId: 'upper-deck', crossed: !expectedProof };
      replay.runRecording(encodeJSON(tampered)); // stored claim is audit metadata; traversal is recomputed
      expect(replay.hashState()).toBe(finishHash);
      expect(replay.runTime()).toBe(live.runTime());
      expect(replay.counters().diamondRouteCrossed).toBe(expectedProof);
    }
    expect(medalFor(10, 0, 90, 'rookie')).toBe('platinum'); // ordinary track behavior
  });
});
