import type { TrackDef } from '../core/types';

export interface DiamondRouteCue {
  goalId: string;
  x0: number;
  x1: number;
  title: string;
  action: string;
  secondBeat?: { x0: number; action: string };
}

/** Short approach windows for the four optional high lines; no bike-class medal lock. */
const CUES: Readonly<Record<string, DiamondRouteCue>> = {
  'd3-rope-walk': { goalId: 'd3-high-bridge', x0: 384, x1: 400, title: 'HIGH BRIDGE', action: 'DIAMOND · LAND ON THE UPPER DECK' },
  's1-lift-line': { goalId: 's1-station-shelf', x0: 245, x1: 294, title: 'LIFT BRIDGE',
    action: 'DIAMOND · SETTLE AT LIP', secondBeat: { x0: 275, action: 'DIAMOND · LEVEL FOR DECK' } },
  's2-cornice': { goalId: 's2-wind-shelf', x0: 130, x1: 166, title: 'WIND SHELF', action: 'DIAMOND · CARRY SPEED OFF THE LIP' },
  's3-whiteout': { goalId: 's3-snowcat-shelf', x0: 108, x1: 149, title: 'SNOWCAT SHELF', action: 'DIAMOND · LIFT ONTO UPPER DECK' },
};

export function diamondRouteCue(track: Pick<TrackDef, 'id' | 'diamondGoal'>): DiamondRouteCue | null {
  const cue = CUES[track.id];
  return cue && track.diamondGoal?.id === cue.goalId ? cue : null;
}
