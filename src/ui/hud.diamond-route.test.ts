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
});
