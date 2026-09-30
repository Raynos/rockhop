// @vitest-environment jsdom
import { describe, expect, it } from 'vitest';
import { resolveBoot } from './flow';
import { resultNextAction } from './app';
import { ROCKHOP_ALL } from '../tracks';
import { CareerEconomy } from '../ui/economy';
import { STARTER_COURSE_IDS } from '../ui/progress';

const has = (id: string): boolean => id === 'b1-first-ride' || id === 'e1-uphill-weight';

describe('boot routing', () => {
  it('?harness=1 bypasses the menu entirely (hook-only mode)', () => {
    expect(resolveBoot(new URLSearchParams('harness=1'), has).mode).toBe('harness');
    expect(resolveBoot(new URLSearchParams('harness=1&track=e1-uphill-weight'), has)).toMatchObject({ mode: 'harness', track: 'e1-uphill-weight' });
    // Even with dev / countdown flags the harness never gets a front end.
    expect(resolveBoot(new URLSearchParams('harness=1&dev=1&countdown=1'), has).mode).toBe('harness');
  });

  it('?track= goes straight into that track when it exists', () => {
    expect(resolveBoot(new URLSearchParams('track=e1-uphill-weight'), has)).toMatchObject({ mode: 'run', track: 'e1-uphill-weight' });
    expect(resolveBoot(new URLSearchParams('track=nope'), has).mode).toBe('front');
  });

  it('a plain visit opens the main menu with the harbour backdrop', () => {
    const r = resolveBoot(new URLSearchParams(''), has);
    expect(r).toMatchObject({ mode: 'front', track: null, dev: false, backdrop: 'c1-low-tide' });
  });

  it('?dev=1 is carried for the unlock-all rule', () => {
    expect(resolveBoot(new URLSearchParams('dev=1'), has).dev).toBe(true);
  });
});


describe('D2 earned-bike result continuation', () => {
  it('changes from improving medals to explicit purchase, equip and the real D3 launch', () => {
    const economy = new CareerEconomy(null);
    STARTER_COURSE_IDS.forEach((id) => economy.award(id, 'bronze'));
    const action = () => {
      const state = economy.snapshot();
      return resultNextAction(ROCKHOP_ALL, 'd2-conveyor', (id) => state.medals[id] ?? null, state, state.equipped);
    };
    expect(action()).toMatchObject({ enabled: true, label: 'Improve medals', destination: 'map', detail: '1040 Scrap to Pro' });
    STARTER_COURSE_IDS.slice(0, 7).forEach((id) => economy.award(id, 'gold'));
    economy.award(STARTER_COURSE_IDS[7]!, 'platinum');
    expect(action()).toMatchObject({ enabled: true, label: 'Buy Pro', destination: 'garage', detail: 'Garage · 1840 Scrap' });
    expect(economy.snapshot()).toMatchObject({ wallet: 1840, proOwned: false, equipped: 'rookie' });
    economy.purchasePro();
    expect(action()).toMatchObject({ enabled: true, label: 'Equip Pro', destination: 'garage' });
    economy.equip('pro');
    expect(action()).toMatchObject({ enabled: true, label: 'Next track', destination: 'track', trackId: 'd3-rope-walk' });
    economy.equip('rookie');
    expect(action()).toMatchObject({ label: 'Equip Pro', destination: 'garage' });
  });

  it('does not turn missing-medal locks or the final course into a purchase or loop', () => {
    const state = { wallet: 1840, proOwned: false };
    expect(resultNextAction(ROCKHOP_ALL, 'd2-conveyor', () => null, state, 'rookie')).toMatchObject({ enabled: false, label: 'Next track', destination: 'track' });
    expect(resultNextAction(ROCKHOP_ALL, 'c3-hull-breach', () => null, state, 'rookie').enabled).toBe(false);
    expect(resultNextAction(ROCKHOP_ALL, 's3-whiteout', () => 'gold', { wallet: 0, proOwned: true }, 'pro')).toMatchObject({ enabled: false, trackId: null });
    expect(resultNextAction(ROCKHOP_ALL, 'd2-conveyor', () => null, state, 'rookie', true)).toMatchObject({ enabled: true, label: 'Next track', destination: 'track', trackId: 'd3-rope-walk' });
  });
});
