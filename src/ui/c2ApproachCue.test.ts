// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest';
import type { PhysicsState, RunInfo } from '../core/types';
import { getTrack } from '../tracks';
import { DomHud } from './hud';
import { resetLive } from './live';

afterEach(() => { resetLive(); document.body.innerHTML = ''; });

describe('C2 approach cues', () => {
  it('teaches the Pier 2 front lift before the fall, then changes to the crane flight cue', () => {
    const hud = new DomHud(document.body);
    hud.setTrack(getTrack('c2-crane-hop')!);
    hud.setRun({ phase: 'riding', simTime: 9, runTime: 9, faults: 0, checkpoint: 0, checkpointCount: 3 } as RunInfo);
    const at = (x: number) => hud.update({ bike: { pos: { x } }, checkpoint: 0 } as PhysicsState);

    at(86);
    expect(hud.root.querySelector('.skill-cue')?.classList.contains('show')).toBe(false);
    at(88);
    const cue = hud.root.querySelector('.skill-cue')!;
    expect(cue.classList.contains('show')).toBe(true);
    expect(cue.textContent).toContain('EASE BEFORE LIP');
    expect(cue.textContent).toContain('LIFT BRIEFLY');
    expect(cue.getAttribute('aria-label')).toContain('coast onto the down ramp');
    expect(cue.textContent).not.toContain('LEAN FORWARD');

    at(140);
    expect(cue.classList.contains('show')).toBe(false);
    at(300);
    expect(cue.classList.contains('show')).toBe(true);
    expect(cue.textContent).toContain('LEVEL THE BIKE');
    at(104); // Checkpoint retry can return to Pier 2.
    expect(cue.textContent).toContain('EASE BEFORE LIP');
  });
});
