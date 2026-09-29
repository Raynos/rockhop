// @vitest-environment jsdom
import { afterEach, describe, expect, it } from 'vitest';
import type { PhysicsState, RunInfo } from '../core/types';
import { getTrack } from '../tracks';
import { diamondRouteCue } from './diamondRouteCue';
import { DomHud } from './hud';
import { resetLive } from './live';

const highLines = ['d3-rope-walk', 's1-lift-line', 's2-cornice', 's3-whiteout'];
const riding = { phase: 'riding', simTime: 2, runTime: 1, faults: 0 } as RunInfo;
const at = (x: number): PhysicsState => ({ bike: { pos: { x } }, checkpoint: -1 } as PhysicsState);

afterEach(() => { resetLive(); document.body.innerHTML = ''; });

describe('late Diamond high-line guidance', () => {
  it('appears on each real approach, leaves after its landing, and clears when changing course', () => {
    const hud = new DomHud(document.body);
    for (const id of highLines) {
      const track = getTrack(id)!;
      const cue = diamondRouteCue(track)!;
      expect(cue).toBeTruthy();
      if (id === 's1-lift-line') expect(cue.title).toBe('LIFT BRIDGE');
      hud.setTrack(track);
      hud.setRun(riding);
      const element = hud.root.querySelector('.skill-cue')!;
      expect(element.classList.contains('route')).toBe(true);
      expect(element.textContent).toContain(cue.title);
      expect(element.textContent).toContain('DIAMOND');
      hud.update(at(cue.x0 - 1));
      expect(element.classList.contains('show')).toBe(false);
      hud.update(at(cue.x0 + 1));
      expect(element.classList.contains('show')).toBe(true);
      hud.update(at(cue.x1 + 1));
      expect(element.classList.contains('show')).toBe(false);
    }
    hud.setTrack(getTrack('c1-low-tide')!);
    expect(hud.root.querySelector('.skill-cue')?.classList.contains('route')).toBe(false);
    expect(hud.root.querySelector('.skill-cue')?.textContent).toContain('EASE OFF');
  });

  it('gives Lift Line an early settle beat, then a level beat without moving its fixed HUD box', () => {
    const hud = new DomHud(document.body);
    const route = diamondRouteCue(getTrack('s1-lift-line')!)!;
    expect(route.x0).toBe(245);
    expect(route.secondBeat?.x0).toBe(275);
    hud.setTrack(getTrack('s1-lift-line')!);
    hud.setRun(riding);
    const cue = hud.root.querySelector('.skill-cue')!;
    hud.update(at(244.9));
    expect(cue.classList.contains('show')).toBe(false);
    hud.update(at(245));
    expect(cue.classList.contains('show')).toBe(true);
    expect(cue.textContent).toContain('SETTLE AT LIP');
    expect(cue.getAttribute('aria-label')).toContain('SETTLE AT LIP');
    hud.update(at(274.9));
    expect(cue.textContent).toContain('SETTLE AT LIP');
    hud.update(at(275));
    expect(cue.textContent).toContain('LEVEL FOR DECK');
    expect(cue.getAttribute('aria-label')).toContain('LEVEL FOR DECK');
    expect(cue.classList.contains('route')).toBe(true);
    hud.update(at(274));
    expect(cue.textContent).toContain('SETTLE AT LIP');
    hud.update(at(294));
    expect(cue.classList.contains('show')).toBe(false);
    hud.setTrack(getTrack('s2-cornice')!);
    expect(cue.textContent).toContain('WIND SHELF');
    expect(cue.textContent).not.toContain('SETTLE');
    for (const id of ['d3-rope-walk', 's2-cornice', 's3-whiteout']) {
      const track = getTrack(id)!;
      const other = diamondRouteCue(track)!;
      expect(other.secondBeat).toBeUndefined();
      hud.setTrack(track);
      hud.setRun(riding);
      hud.update(at((other.x0 + other.x1) / 2));
      expect(cue.textContent).toContain(other.action);
    }
  });

  it('keeps an active retry lesson over the route beat and restores the beat when it expires', () => {
    const hud = new DomHud(document.body);
    hud.setTrack(getTrack('s1-lift-line')!);
    hud.setRun(riding);
    const cue = hud.root.querySelector('.skill-cue')!;
    hud.update(at(274));
    expect(cue.textContent).toContain('SETTLE AT LIP');
    // A future route-specific fault lesson shares this HUD slot. Simulate it here
    // until a track author supplies the fault trigger, then cross the beat boundary.
    const fault = hud as unknown as { faultCue: object | null; faultCueUntil: number };
    fault.faultCue = {};
    fault.faultCueUntil = 4;
    cue.innerHTML = '<strong>RETRY THE LANDING</strong>';
    cue.classList.add('fault');
    hud.update(at(275));
    expect(cue.textContent).toContain('RETRY THE LANDING');
    hud.setRun({ ...riding, simTime: 5 });
    hud.update(at(275));
    expect(cue.textContent).toContain('LEVEL FOR DECK');
    expect(cue.classList.contains('fault')).toBe(false);
  });

  it('teaches the first Whiteout shelf before the gap, then restores the earlier upper-route prompt', () => {
    const hud = new DomHud(document.body);
    const track = getTrack('s3-whiteout')!;
    const route = diamondRouteCue(track)!;
    hud.setTrack(track);
    hud.setRun({ ...riding, phase: 'countdown' });
    expect(hud.root.querySelector('.hints')?.textContent).toContain('first shelf');
    hud.setRun(riding);
    const cue = hud.root.querySelector('.skill-cue')!;
    hud.update(at(27.9));
    expect(cue.classList.contains('show')).toBe(false);
    hud.update(at(28));
    expect(cue.classList.contains('show')).toBe(true);
    expect(cue.classList.contains('route')).toBe(false);
    expect(cue.textContent).toContain('LIFT TO THE SHELF');
    hud.update(at(52.9));
    expect(cue.classList.contains('show')).toBe(true);
    hud.update(at(53));
    expect(cue.classList.contains('show')).toBe(false);
    expect(cue.classList.contains('route')).toBe(true);
    expect(cue.textContent).toContain('SNOWCAT SHELF');
    expect(route.x0).toBe(108);
    hud.update(at(route.x0));
    expect(cue.classList.contains('show')).toBe(true);
    expect(cue.textContent).toContain('UPPER DECK');
    hud.update(at(route.x1));
    expect(cue.classList.contains('show')).toBe(false);
    hud.setTrack(getTrack('d1-dust-devil')!);
    expect(cue.classList.contains('route')).toBe(false);
    expect(cue.textContent).not.toContain('SNOWCAT');
  });
});
