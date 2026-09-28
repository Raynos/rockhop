/** Pure upper-deck crossing check shared by the live game and Node replay rules. */
import { StateHasher } from '../core/hash';
import type { DiamondRouteGoal, PhysicsState, TrackDef } from '../core/types';
import { resolveParams } from '../tracks/kinds';

export function crossedDiamondRouteGoal(track: TrackDef | null | undefined, before: PhysicsState, after: PhysicsState): boolean {
  const goal = track?.diamondGoal;
  if (!goal) return false;
  const deck = track.obstacles[goal.platformObstacleIndex];
  if (!deck || deck.kind !== 'open-platform') return false; // compileTrack rejects malformed authoring
  const p = resolveParams('open-platform', deck.params);
  const top = deck.pos.y + p.height;
  const rear = after.wheels.rear;
  return before.wheels.rear.pos.x < goal.x && rear.pos.x >= goal.x
    && rear.grounded && after.contacts.rear === p.surface
    && rear.pos.y >= goal.minRearY && rear.pos.y >= top + 0.2 && rear.pos.y <= top + 0.5;
}

/** Route proof enters the opt-in run hash; ordinary tracks retain their exact historical physics hash. */
export function hashRouteRunState(physicsHash: string, goal: DiamondRouteGoal | undefined, crossed: boolean): string {
  return goal ? new StateHasher().string(physicsHash).string(goal.id).bool(crossed).digest() : physicsHash;
}
