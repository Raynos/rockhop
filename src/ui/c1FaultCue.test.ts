// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest';
import type { GameEvent, PhysicsState, RunInfo } from '../core/types';
import { getTrack } from '../tracks';
import { c1FaultCue } from './c1FaultCue';
import { DomHud } from './hud';
import { resetLive } from './live';

function state(x: number, checkpoint: number): PhysicsState {
  return { bike: { pos: { x } }, checkpoint } as PhysicsState;
}

function run(hud: DomHud, phase: RunInfo['phase'], simTime: number, faults = 1): void {
  hud.setRun({ phase, simTime, faults, runTime: simTime, checkpoint: 1, checkpointCount: 3 } as RunInfo);
}

afterEach(() => { resetLive(); document.body.innerHTML = ''; });

describe('C1 crash learning cue', () => {
  it('names only the authored pallet/deck and causeway windows', () => {
    expect(c1FaultCue(234.31, 1)?.title).toBe('DECK LANDING');
    expect(c1FaultCue(312, 2)?.title).toBe('CAUSEWAY STEPS');
    expect(c1FaultCue(314.676, 2, 169.3 * Math.PI / 180)?.title).toBe('LOOPED ON THE STEPS');
    expect(c1FaultCue(294.202, 2, -138.7 * Math.PI / 180)?.title).toBe('NOSE-DIVED AT A STEP');
    expect(c1FaultCue(170, 1)).toBeNull();
    expect(c1FaultCue(234.31, 2)).toBeNull();
    expect(c1FaultCue(361, 2)).toBeNull();
  });

  it('keeps the corrective action through one-second auto respawn, then restores the approach cue', () => {
    const hud = new DomHud(document.body);
    hud.setTrack(getTrack('c1-low-tide')!);
    run(hud, 'riding', 17);
    hud.onEvent({ type: 'fault', reason: 'crash', tick: 2128, time: 17.733 } as GameEvent);
    run(hud, 'crashed', 17.75);
    hud.update(state(234.31, 1));
    expect(hud.root.querySelector('.skill-cue')?.textContent).toContain('BRAKE BEFORE RAMP');
    expect(hud.root.querySelector('.skill-cue')?.classList.contains('show')).toBe(true);
    hud.onEvent({ type: 'restart', checkpoint: 1, tick: 0 });
    run(hud, 'riding', 18.75);
    hud.update(state(180.69, 1));
    expect(hud.root.querySelector('.skill-cue')?.textContent).toContain('DECK LANDING');
    run(hud, 'riding', 21);
    hud.update(state(190, 1));
    expect(hud.root.querySelector('.skill-cue')?.textContent).toContain('EASE OFF');
  });

  it('does not give C1 advice for manual restarts or other courses', () => {
    const hud = new DomHud(document.body);
    hud.setTrack(getTrack('c1-low-tide')!);
    run(hud, 'riding', 7);
    hud.onEvent({ type: 'fault', reason: 'restart', tick: 1, time: 7 });
    run(hud, 'crashed', 7.01);
    hud.update(state(234.31, 1));
    expect(hud.root.querySelector('.skill-cue')?.classList.contains('fault')).toBe(false);
    hud.setTrack(getTrack('c2-crane-hop')!);
    hud.onEvent({ type: 'fault', reason: 'crash', tick: 1, time: 7 });
    hud.update(state(234.31, 1));
    expect(hud.root.querySelector('.skill-cue')?.classList.contains('fault')).toBe(false);
  });

  it('turns a played causeway loop into a specific control correction', () => {
    const hud = new DomHud(document.body);
    hud.setTrack(getTrack('c1-low-tide')!);
    run(hud, 'riding', 23.25);
    hud.onEvent({ type: 'fault', reason: 'crash', tick: 2791, time: 23.258 } as GameEvent);
    run(hud, 'crashed', 23.3);
    hud.update({ bike: { pos: { x: 314.676 }, angle: 169.3 * Math.PI / 180 }, checkpoint: 2 } as PhysicsState);
    expect(hud.root.querySelector('.skill-cue')?.textContent).toContain('RELEASE LEAN BACK');
    expect(hud.root.querySelector('.skill-cue')?.getAttribute('aria-label')).toContain('Looped on the causeway');
  });
});
