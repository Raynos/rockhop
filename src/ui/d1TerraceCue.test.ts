// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest';
import type { PhysicsState, RunInfo } from '../core/types';
import { getTrack } from '../tracks';
import { DomHud } from './hud';
import { resetLive } from './live';

afterEach(() => { resetLive(); document.body.innerHTML = ''; });

describe('D1 first terrace approach', () => {
  it('warns before both faulting cuts and clears before the first contact', () => {
    const hud = new DomHud(document.body);
    hud.setTrack(getTrack('d1-dust-devil')!);
    hud.setRun({ phase: 'riding', simTime: 6, runTime: 6, faults: 0, checkpoint: 0, checkpointCount: 3 } as RunInfo);
    const at = (x: number) => hud.update({ bike: { pos: { x } }, checkpoint: 0 } as PhysicsState);
    const cue = hud.root.querySelector('.skill-cue')!;

    at(75.9);
    expect(cue.classList.contains('show')).toBe(false);
    at(76);
    expect(cue.classList.contains('show')).toBe(true);
    expect(cue.textContent).toContain('LIFT BEFORE THE CUT');
    expect(cue.textContent).toContain('LEVEL FOR THE NEXT STEP');
    at(96.9);
    expect(cue.classList.contains('show')).toBe(true);
    at(97);
    expect(cue.classList.contains('show')).toBe(false);
    hud.setTrack(getTrack('c1-low-tide')!);
    expect(cue.textContent).toContain('EASE OFF');
  });
});
