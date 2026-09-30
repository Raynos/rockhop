import { describe, expect, it } from 'vitest';
import { CareerEconomy, ECONOMY_KEY, PRO_PRICE, SCRAP_REWARD } from './economy';

class MemoryStorage implements Storage {
  private readonly values = new Map<string, string>();
  get length(): number { return this.values.size; }
  clear(): void { this.values.clear(); }
  getItem(key: string): string | null { return this.values.get(key) ?? null; }
  key(index: number): string | null { return [...this.values.keys()][index] ?? null; }
  removeItem(key: string): void { this.values.delete(key); }
  setItem(key: string, value: string): void { this.values.set(key, value); }
}

const FIRST = 'c1-low-tide';
const SECOND = 'c2-crane-hop';
const MAIN = ['c1-low-tide', 'c2-crane-hop', 'c3-hull-breach', 'a1-sawdust', 'a2-log-jam', 'a3-timberline', 'd1-dust-devil', 'd2-conveyor', 'd3-rope-walk', 's1-lift-line', 's2-cornice', 's3-whiteout'];

describe('CareerEconomy', () => {
  it('pays the medal-total difference once per campaign track, across reloads and bike classes', () => {
    const store = new MemoryStorage();
    const economy = new CareerEconomy(store);
    expect(economy.award(FIRST, 'bronze')).toMatchObject({ delta: 100, wallet: 100, previous: null, current: 'bronze' });
    expect(economy.award(FIRST, 'bronze').delta).toBe(0);
    expect(economy.award(FIRST, 'gold')).toMatchObject({ delta: 120, wallet: 220, previous: 'bronze', current: 'gold' });
    expect(economy.award(FIRST, 'silver').delta).toBe(0);
    expect(new CareerEconomy(store).award(FIRST, 'platinum')).toMatchObject({ delta: 80, wallet: 300, current: 'platinum' });
    expect(new CareerEconomy(store).award(FIRST, 'platinum').delta).toBe(0);
    expect(SCRAP_REWARD).toEqual({ bronze: 100, silver: 160, gold: 220, platinum: 300 });
  });

  it('ignores lab, old curriculum, and unknown tracks', () => {
    const economy = new CareerEconomy(new MemoryStorage());
    for (const id of ['lab-flat-200', 'b1-first-ride', 'p-coast', 'not-a-track']) expect(economy.award(id, 'platinum').delta).toBe(0);
    expect(economy.snapshot().lifetimeEarned).toBe(0);
  });

  it('requires medal improvements: eight Bronze cannot buy, seven Gold plus one Diamond buys once at 1,840', () => {
    const store = new MemoryStorage();
    const economy = new CareerEconomy(store);
    expect(economy.equip('pro')).toBe(false);
    expect(economy.purchasePro()).toBe('insufficient-scrap');
    MAIN.slice(0, 8).forEach((id) => economy.award(id, 'bronze'));
    expect(economy.snapshot().wallet).toBe(800);
    expect(economy.purchasePro()).toBe('insufficient-scrap');
    MAIN.slice(0, 7).forEach((id) => economy.award(id, 'gold'));
    expect(economy.snapshot().wallet).toBe(1640);
    expect(economy.purchasePro()).toBe('insufficient-scrap');
    economy.award(MAIN[7]!, 'platinum');
    expect(economy.snapshot().wallet).toBe(PRO_PRICE);
    expect(economy.purchasePro()).toBe('purchased');
    expect(economy.snapshot()).toMatchObject({ wallet: 0, lifetimeEarned: 1840, proOwned: true, equipped: 'rookie' });
    expect(economy.purchasePro()).toBe('already-owned');
    expect(economy.equip('pro')).toBe(true);
    expect(store.getItem('rockhop.bikeClass')).toBe('pro');
    expect(new CareerEconomy(store).snapshot()).toMatchObject({ wallet: 0, proOwned: true, equipped: 'pro' });
    expect(economy.award(FIRST, 'platinum').delta).toBe(80);
    expect(economy.snapshot().wallet).toBe(80);
  });

  it('also buys at four Silver plus four Diamond, including across a reload', () => {
    const store = new MemoryStorage();
    const economy = new CareerEconomy(store);
    MAIN.slice(0, 4).forEach((id) => economy.award(id, 'silver'));
    MAIN.slice(4, 8).forEach((id) => economy.award(id, 'platinum'));
    expect(economy.snapshot()).toMatchObject({ wallet: 1840, lifetimeEarned: 1840, proOwned: false });
    const reloaded = new CareerEconomy(store);
    expect(reloaded.purchasePro()).toBe('purchased');
    expect(reloaded.purchasePro()).toBe('already-owned');
    expect(new CareerEconomy(store).snapshot()).toMatchObject({ wallet: 0, lifetimeEarned: 1840, proOwned: true });
  });

  it('backfills the highest stored career medal and preserves old Pro usage without paying twice', () => {
    const store = new MemoryStorage();
    store.setItem(`rockhop.best.${FIRST}`, JSON.stringify({ time: 29, faults: 0, medal: 'silver', bestMedal: 'gold' }));
    store.setItem(`rockhop.best.${FIRST}@pro`, JSON.stringify({ time: 27, faults: 0, medal: 'platinum' }));
    store.setItem(`rockhop.best.${SECOND}`, JSON.stringify({ time: 35, faults: 0, medal: 'bronze' }));
    store.setItem('rockhop.bikeClass', 'pro');
    const economy = new CareerEconomy(store);
    expect(economy.snapshot()).toMatchObject({ wallet: 400, lifetimeEarned: 400, proOwned: true, equipped: 'pro' });
    expect(economy.award(FIRST, 'platinum').delta).toBe(0);
    expect(new CareerEconomy(store).snapshot().wallet).toBe(400);
    store.setItem(`rockhop.best.${SECOND}`, JSON.stringify({ time: 30, faults: 0, medal: 'gold' }));
    expect(new CareerEconomy(store).snapshot()).toMatchObject({ wallet: 520, lifetimeEarned: 520 });
    expect(new CareerEconomy(store).snapshot().wallet).toBe(520);
  });

  it('grandfathers a saved Pro selection even without a Pro PB', () => {
    const store = new MemoryStorage();
    store.setItem('rockhop.bikeClass', 'pro');
    expect(new CareerEconomy(store).snapshot()).toMatchObject({ wallet: 0, proOwned: true, equipped: 'pro' });
  });

  it('does not turn malformed PBs or ledger values into free Scrap', () => {
    const store = new MemoryStorage();
    store.setItem(ECONOMY_KEY, '{broken');
    store.setItem(`rockhop.best.${FIRST}`, JSON.stringify({ time: 'fast', faults: 0, medal: 'platinum' }));
    store.setItem(`rockhop.best.${SECOND}`, '{broken');
    expect(new CareerEconomy(store).snapshot()).toMatchObject({ wallet: 0, lifetimeEarned: 0, proOwned: false });
    store.setItem(ECONOMY_KEY, JSON.stringify({ version: 1, wallet: 999999999, medals: { [FIRST]: 'bronze', evil: 'platinum' }, proOwned: false, equipped: 'pro' }));
    expect(new CareerEconomy(store).snapshot()).toMatchObject({ wallet: 100, lifetimeEarned: 100, proOwned: false, equipped: 'rookie' });
  });

  it('survives unavailable storage in memory and resets career ownership with medals', () => {
    const economy = new CareerEconomy(null);
    expect(economy.award(FIRST, 'gold').wallet).toBe(220);
    expect(economy.snapshot().wallet).toBe(220);
    economy.clear();
    expect(economy.snapshot()).toMatchObject({ wallet: 0, lifetimeEarned: 0, proOwned: false, equipped: 'rookie' });
    const store = new MemoryStorage();
    const saved = new CareerEconomy(store);
    MAIN.slice(0, 7).forEach((id) => saved.award(id, 'gold'));
    saved.award(MAIN[7]!, 'platinum');
    expect(saved.purchasePro()).toBe('purchased');
    saved.equip('pro');
    saved.clear();
    expect(store.getItem(ECONOMY_KEY)).toBeNull();
    expect(store.getItem('rockhop.bikeClass')).toBeNull();
    expect(new CareerEconomy(store).snapshot()).toMatchObject({ wallet: 0, proOwned: false, equipped: 'rookie' });
  });
});
