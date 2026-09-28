/** Quarry-only v2 simulator, isolated from concurrent edits to the other biomes. */
import { DEFAULT_PHYSICS_HZ, type BikeClass, type GameEvent, type InputFrame } from '../src/core/types';
import { hashPhysicsState } from '../src/core/hash';
import { createBikePhysicsV2 } from '../src/physics';
import { compileTrack } from '../src/tracks/compile';
import { hashRouteRunState } from '../src/game/routeGoal';
import { D1, D2, D3 } from '../src/tracks/rockhop/quarry';
import { RunRules } from './lib/rules';
import type { Sim } from './lib/sim';

const tracks = [D1, D2, D3];

export async function createQuarrySim(id: string, seed?: number, hz = DEFAULT_PHYSICS_HZ, bike: BikeClass = 'rookie'): Promise<Sim> {
  const track = tracks.find((t) => t.id === id);
  if (!track) throw new Error(`unknown Quarry track ${id}`);
  const compiled = compileTrack(track);
  const world = createBikePhysicsV2(hz);
  const actualSeed = (seed ?? track.seed) >>> 0;
  const rules = new RunRules(world, hz, track);
  const load = (): void => {
    world.loadTrack(compiled, actualSeed, { bike });
    world.drainEvents();
    rules.go();
    rules.drainEvents();
  };
  load();
  let total = 0;
  const step = (input: InputFrame): GameEvent[] => {
    rules.tick(input);
    total++;
    return rules.drainEvents();
  };
  const hash = (): string => hashRouteRunState(hashPhysicsState(world.getState()), track.diamondGoal, rules.counters().diamondRouteCrossed === true);
  return {
    world, rules, track, compiled, hz, seed: actualSeed, bike, physicsName: 'createBikePhysicsV2-v2', physicsVersion: 'v2', step,
    run(frames) {
      const events: GameEvent[] = [];
      let ticks = 0;
      for (const f of frames) { events.push(...step(f)); ticks++; }
      return { state: world.getState(), events, hash: hash(), ticks };
    },
    snap: () => ({ physics: world.snapshot(), counters: rules.counters() }),
    restore: (s) => { world.restore(s.physics); world.drainEvents(); rules.restoreCounters(s.counters); },
    hash, state: () => world.getState(), phase: () => rules.phase(), faults: () => rules.faults(),
    runTicks: () => rules.runTicks(), runTime: () => rules.runTicks() / hz,
    totalTicks: () => total, reload: load,
  };
}
