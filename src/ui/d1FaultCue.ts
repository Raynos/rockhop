import type { FaultCue } from './c1FaultCue';

/** Bike-centre windows measured from the played blind D1 faults; the two true lips are x98.4 and x104.4. */
export function d1FaultCue(x: number, checkpoint: number): FaultCue | null {
  if (checkpoint !== 1) return null;
  if (x >= 96 && x < 101.5) return {
    title: 'FIRST TERRACE',
    action: 'LIFT EARLY · LEVEL ON TOP',
    accessible: 'First terrace. Lift the front before the step, then level the bike on top.',
  };
  if (x >= 101.5 && x < 107.5) return {
    title: 'SECOND TERRACE',
    action: 'LEVEL BETWEEN STEPS · LIFT AGAIN',
    accessible: 'Second terrace. Recenter after the first step, then lift the front again.',
  };
  return null;
}
