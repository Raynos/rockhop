// @vitest-environment jsdom
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { RunResult } from '../core/types';
import { getTrack } from '../tracks';
import { DomHud } from './hud';
import { resetLive } from './live';

const first: RunResult = {
  trackId: 'c1-low-tide', time: 30.35, faults: 0, medal: 'platinum',
  personalBest: true, previousBest: null, targetTimeS: 36, bike: 'rookie',
};
function setup() {
  const hud = new DomHud(document.body);
  hud.setTrack(getTrack('c1-low-tide')!);
  return hud;
}
function copy(hud: DomHud, selector: string): string {
  return hud.root.querySelector(selector)?.textContent?.trim() ?? '';
}
afterEach(() => { resetLive(); document.body.innerHTML = ''; });

describe('production finish report', () => {
  it('shows real first clear, earned Diamond, time and one-time Scrap', () => {
    const hud = setup();
    hud.showResults(first);
    hud.setScrapReward(300, 300, false, 800, null);
    expect(copy(hud, '.fr-tag')).toBe('NEW COURSE CLEAR');
    expect(copy(hud, '.fr-headline')).toBe('YOU FOUND THE LINE');
    expect(copy(hud, '.fr-medal-name')).toBe('Diamond');
    expect(copy(hud, '.time')).toBe('0:30.350');
    expect(copy(hud, '.tk-reward')).toBe('+300');
    expect(copy(hud, '.fr-wallet')).toBe('300');
    expect(copy(hud, '.fr-goal-title')).toBe('YOUR NEXT LINE · 500 TO PRO');
  });

  it('distinguishes a faster PB, a career medal upgrade and a no-gain clear', () => {
    const hud = setup();
    hud.showResults({ ...first, time: 29.4, previousBest: 31, medal: 'gold' });
    hud.setScrapReward(0, 520, false, 800, 'gold');
    expect(copy(hud, '.fr-tag')).toBe('NEW PERSONAL BEST');
    expect(copy(hud, '.pb')).toBe('−0:01.600');
    expect(copy(hud, '.fr-goal-title')).toBe('NEXT MEDAL: DIAMOND · 280 TO PRO');

    hud.showResults({ ...first, previousBest: 31, time: 31.2, personalBest: false });
    hud.setScrapReward(140, 660, false, 800, 'silver');
    expect(copy(hud, '.fr-tag')).toBe('MEDAL UPGRADED');
    expect(copy(hud, '.fr-kicker')).toBe('SILVER → DIAMOND');
    expect(copy(hud, '.tk-reward')).toBe('+140');

    hud.showResults({ ...first, time: 42, faults: 2, medal: 'gold', previousBest: 39, personalBest: false });
    hud.setScrapReward(0, 660, false, 800, 'gold');
    expect(copy(hud, '.fr-tag')).toBe('COURSE CLEARED');
    expect(copy(hud, '.fr-headline')).toBe('ONE MORE RUN?');
    expect(copy(hud, '.tk-reward')).toBe('No new Scrap');
    expect(copy(hud, '.pb')).toBe('0:39.000');
    expect(copy(hud, '.fr-goal-title')).toBe('NEXT MEDAL: DIAMOND · 140 TO PRO');
    hud.setScrapReward(0, 800, false, 800, 'gold');
    expect(copy(hud, '.fr-goal-title')).toBe('NEXT MEDAL: DIAMOND · BUY PRO');
  });

  it('keeps all four real destinations and gates selection until reveal stage 3', () => {
    const hud = setup();
    const action = vi.fn();
    hud.onAction = action;
    hud.showResults(first);
    expect([...hud.root.querySelectorAll('.results .tile')].map(x => x.getAttribute('data-id'))).toEqual(['retry', 'next', 'menu', 'replay']);
    hud.resultsConfirm();
    expect(action).not.toHaveBeenCalled();
    hud.setRun({ phase: 'finished', simTime: 1, runTime: 30.35, faults: 0 } as Parameters<DomHud['setRun']>[0]);
    hud.showResults(first);
    hud.setRun({ phase: 'finished', simTime: 1.7, runTime: 30.35, faults: 0 } as Parameters<DomHud['setRun']>[0]);
    hud.resultsConfirm();
    expect(action).toHaveBeenLastCalledWith('retry');
    hud.resultsMove(1);
    hud.resultsConfirm();
    expect(action).toHaveBeenLastCalledWith('next');
  });
});
