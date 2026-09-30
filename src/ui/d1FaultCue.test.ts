// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest';
import type { GameEvent, PhysicsState, RunInfo } from '../core/types';
import { getTrack } from '../tracks';
import { d1FaultCue } from './d1FaultCue';
import { DomHud } from './hud';
import { resetLive } from './live';

const state = (x: number): PhysicsState => ({ bike: { pos: { x }, angle: 0 }, checkpoint: 1 } as PhysicsState);
const run = (hud: DomHud, phase: RunInfo['phase'], simTime: number): void => {
  hud.setRun({ phase, simTime, runTime: simTime, faults: 1, checkpoint: 1, checkpointCount: 3 } as RunInfo);
};

afterEach(() => { resetLive(); document.body.innerHTML = ''; });

describe('D1 terrace retry lesson', () => {
  it('names the two recorded faulting cuts without claiming later quarry faults', () => {
    expect(d1FaultCue(98.8195, 1)?.title).toBe('FIRST TERRACE');
    expect(d1FaultCue(103.3104, 1)?.title).toBe('SECOND TERRACE');
    expect(d1FaultCue(97.204, 1)?.title).toBe('FIRST TERRACE');
    expect(d1FaultCue(110, 1)).toBeNull();
    expect(d1FaultCue(98.8195, 2)).toBeNull();
  });

  it('keeps the correction over checkpoint retry, then restores the approach cue', () => {
    const hud = new DomHud(document.body);
    hud.setTrack(getTrack('d1-dust-devil')!);
    run(hud, 'riding', 9.3);
    hud.onEvent({ type: 'fault', reason: 'crash', tick: 1123, time: 9.358 } as GameEvent);
    run(hud, 'crashed', 9.36);
    hud.update(state(98.8195));
    const cue = hud.root.querySelector('.skill-cue')!;
    expect(cue.textContent).toContain('FIRST TERRACE');
    expect(cue.classList.contains('fault')).toBe(true);

    hud.onEvent({ type: 'restart', checkpoint: 1, tick: 1243 } as GameEvent);
    run(hud, 'riding', 10.36);
    hud.update(state(76.492));
    expect(cue.textContent).toContain('FIRST TERRACE');
    run(hud, 'riding', 12.6);
    hud.update(state(80));
    expect(cue.textContent).toContain('LIFT BEFORE THE CUT');
    expect(cue.classList.contains('fault')).toBe(false);
  });
});
