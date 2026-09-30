// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { BikeClass, Medal, TrackDef } from '../core/types';
import { ROCKHOP_ALL } from '../tracks';
import type { ArtManifest } from './art';
import type { BestEntry } from './best';
import type { FrontCallbacks, FrontState } from './front';
import type { UiSfx } from './sfx';
import type { EconomySnapshot } from './economy';
import { WorldMapScreen } from './worldMapScreen';

const mounts = vi.hoisted(() => ({ calls: [] as Array<{ root: HTMLElement; select: (index: number) => void; scene: { dispose: ReturnType<typeof vi.fn>; selectStage: ReturnType<typeof vi.fn>; setProgress: ReturnType<typeof vi.fn>; setDragMode: ReturnType<typeof vi.fn>; resize: ReturnType<typeof vi.fn> } }> }));
vi.mock('./worldMap3dScene', () => ({
  mountWorldMap3DShell: vi.fn((root: HTMLElement, select: (index: number) => void) => {
    const host = document.createElement('div');
    host.className = 'wm3d-host';
    host.dataset.ready = '1';
    root.append(host);
    const scene = {
      dispose: vi.fn(() => host.remove()),
      selectStage: vi.fn(),
      setProgress: vi.fn(),
      setDragMode: vi.fn(),
      resize: vi.fn(),
    };
    mounts.calls.push({ root, select, scene });
    return scene;
  }),
}));

const ALL: TrackDef[] = [...ROCKHOP_ALL];
const SEEDED: Record<string, Medal> = { 'c1-low-tide': 'gold', 'c2-crane-hop': 'silver', 'c3-hull-breach': 'bronze' };

beforeEach(() => {
  mounts.calls.length = 0;
  Object.defineProperty(window, 'innerWidth', { configurable: true, value: 900 });
  Object.defineProperty(window, 'innerHeight', { configurable: true, value: 400 });
});
afterEach(() => {
  vi.useRealTimers();
  document.body.innerHTML = '';
  document.head.innerHTML = '';
});

function fixture(options: { seeded?: boolean; medals?: Record<string, Medal>; proOwned?: boolean; bikeClass?: BikeClass; wallet?: number; lastPlayed?: string | null; recording?: boolean; gpu?: { before3d(): Promise<boolean>; after3d(): Promise<boolean> | boolean } } = {}) {
  const bestOf = (id: string): BestEntry | null => {
    const medal = options.medals?.[id] ?? (options.seeded ? SEEDED[id] : undefined);
    if (!medal) return null;
    return { time: 41.2, faults: 0, medal, bike: 'rookie', ...(options.recording ? { recording: '{}' } : {}) } as BestEntry;
  };
  const state = { dev: false, lastPlayed: options.lastPlayed ?? null, ghost: true, bikeClass: options.bikeClass ?? 'rookie' } as FrontState;
  const cb = { play: vi.fn(), goto: vi.fn(), openProGarage: vi.fn(), watchPb: vi.fn() } as unknown as FrontCallbacks;
  const sfx = { tick: vi.fn(), confirm: vi.fn(), back: vi.fn(), launch: vi.fn() } as unknown as UiSfx;
  const career = () => ({ proOwned: options.proOwned ?? false, equipped: options.bikeClass ?? 'rookie', wallet: options.wallet ?? 0 }) as EconomySnapshot;
  const screen = new WorldMapScreen(document.body, sfx, {} as ArtManifest, cb, bestOf, () => state, () => [], options.gpu, career);
  screen.build(ALL);
  screen.show();
  return { screen, cb, sfx };
}

describe('shipped 3D island level select', () => {
  it('opens the twelve-course island by default, with no painted scene or plate request', async () => {
    const { screen } = fixture();
    await vi.waitFor(() => expect(mounts.calls).toHaveLength(1));
    expect(document.querySelector('.wm-view')).toBeNull();
    expect(document.querySelector('.wm-world')).toBeNull();
    expect(document.querySelector('.wm3d-host')).not.toBeNull();
    expect(document.querySelector('.wm3d-detail')?.getAttribute('data-track')).toBe('c1-low-tide');
    expect(document.querySelector('.wm-progress')?.textContent).toContain('0 / 12 cleared');
    expect(document.querySelectorAll('style#worldmap-css')).toHaveLength(1);
    screen.hide();
    expect(mounts.calls[0]!.scene.dispose).toHaveBeenCalledOnce();
    expect(document.querySelector('.wm3d-host')).toBeNull();
  });

  it('towers select courses in route order, lock rules and medals follow campaign state', async () => {
    const { screen, cb } = fixture({ seeded: true });
    await vi.waitFor(() => expect(mounts.calls).toHaveLength(1));
    expect(document.querySelector('.wm3d-detail')?.getAttribute('data-track')).toBe('a1-sawdust');
    expect(document.querySelector('.wm-progress')?.textContent).toContain('3 / 12 cleared');
    for (let index = 0; index < 12; index++) {
      mounts.calls[0]!.select(index);
      expect(document.querySelector('.wm3d-detail')?.getAttribute('data-track')).toBe(ALL[index]!.id);
    }
    mounts.calls[0]!.select(0);
    expect(document.querySelectorAll('.wm-ride .wm-medal-ladder i:not(.unearned)')).toHaveLength(3);
    expect(document.querySelector('.wm-ride .wm-medal-ladder i.gold')).not.toBeNull();
    mounts.calls[0]!.select(3);
    expect(document.querySelectorAll('.wm-ride .wm-medal-ladder i.unearned')).toHaveLength(4);
    mounts.calls[0]!.select(6);
    expect(document.querySelector<HTMLButtonElement>('.wm-ride')?.disabled).toBe(true);
    expect(document.querySelector('.wm-ride .wm-medal-ladder')).toBeNull();
    expect(document.querySelector('.wm3d-detail .rule')?.textContent).toContain('Medal every Alpine track');
    screen.confirm();
    expect(cb.play).not.toHaveBeenCalled();
    screen.hide();
  });

  it('keeps Play Next one tap away even when a different level is selected', async () => {
    const { screen, cb } = fixture({ seeded: true, lastPlayed: 'c1-low-tide' });
    await vi.waitFor(() => expect(mounts.calls).toHaveLength(1));
    expect(document.querySelector('.wm3d-detail')?.getAttribute('data-track')).toBe('c1-low-tide');
    const quick = document.querySelector<HTMLButtonElement>('.wm-quick')!;
    expect(quick.getAttribute('aria-label')).toContain('A1 Sawdust');
    document.querySelector<HTMLButtonElement>('.wm-next')!.click();
    expect(document.querySelector('.wm3d-detail')?.getAttribute('data-track')).toBe('c2-crane-hop');
    document.querySelector<HTMLButtonElement>('.wm-previous')!.click();
    expect(document.querySelector('.wm3d-detail')?.getAttribute('data-track')).toBe('c1-low-tide');
    vi.useFakeTimers();
    quick.click();
    vi.advanceTimersByTime(200);
    expect(cb.play).toHaveBeenCalledWith('a1-sawdust');
    vi.advanceTimersByTime(300);
    expect(screen.visible).toBe(false);
  });

  it('turns the course 9 quick action into a Garage path until Pro is bought and equipped', async () => {
    const eight = Object.fromEntries(ALL.slice(0, 8).map((track) => [track.id, 'bronze'])) as Record<string, Medal>;
    const earn = fixture({ medals: eight, wallet: 800 });
    expect(document.querySelector('.wm3d-detail')?.getAttribute('data-track')).toBe('d3-rope-walk');
    expect(document.querySelector('.wm-progress')?.textContent).toContain('800 Scrap');
    expect(document.querySelector<HTMLButtonElement>('.wm-ride')?.disabled).toBe(false);
    expect(document.querySelector('.wm-quick')?.textContent).toContain('Earn Scrap');
    expect(document.querySelector('.wm-quick')?.textContent).toContain('1040 more Scrap');
    document.querySelector<HTMLButtonElement>('.wm-quick')!.click();
    expect(earn.cb.openProGarage).toHaveBeenCalledOnce();
    expect(earn.cb.goto).not.toHaveBeenCalled();
    expect(earn.cb.play).not.toHaveBeenCalled();
    earn.screen.hide();
    earn.screen.root.remove();

    const improved = Object.fromEntries(ALL.slice(0, 8).map((track, index) => [track.id, index === 7 ? 'platinum' : 'gold'])) as Record<string, Medal>;
    const buy = fixture({ medals: improved, wallet: 1840 });
    expect(document.querySelector('.wm-quick')?.textContent).toContain('Buy Pro');
    buy.screen.hide();
    buy.screen.root.remove();

    const equip = fixture({ medals: eight, proOwned: true, bikeClass: 'rookie' });
    expect(document.querySelector('.wm-quick')?.textContent).toContain('Equip Pro');
    document.querySelector<HTMLButtonElement>('.wm-ride')!.click();
    expect(equip.cb.openProGarage).toHaveBeenCalledOnce();
    expect(equip.cb.goto).not.toHaveBeenCalled();
    expect(equip.cb.play).not.toHaveBeenCalled();
    equip.screen.hide();
    equip.screen.root.remove();

    const ride = fixture({ medals: eight, proOwned: true, bikeClass: 'pro' });
    expect(document.querySelector('.wm-quick')?.textContent).toContain('Play next');
    vi.useFakeTimers();
    document.querySelector<HTMLButtonElement>('.wm-quick')!.click();
    vi.advanceTimersByTime(200);
    expect(ride.cb.play).toHaveBeenCalledWith('d3-rope-walk');
    vi.advanceTimersByTime(300);
    ride.screen.hide();
  });

  it('focuses a rejected direct launch on its locked tower and explains the missing medals', () => {
    const { screen } = fixture();
    screen.preferTrack('d3-rope-walk');
    screen.build(ALL);
    expect(document.querySelector('.wm3d-detail')?.getAttribute('data-track')).toBe('d3-rope-walk');
    expect(document.querySelector('.wm3d-detail .rule')?.textContent).toContain('Medal levels 01–08');
    expect(document.querySelector<HTMLButtonElement>('.wm-ride')?.disabled).toBe(true);
    screen.hide();
  });

  it('opens all twelve courses directly and explains locks without losing Quick Play', async () => {
    const { screen, cb } = fixture({ seeded: true });
    await vi.waitFor(() => expect(mounts.calls).toHaveLength(1));
    const levels = document.querySelector<HTMLButtonElement>('.wm-levels')!;
    levels.click();
    expect(levels.getAttribute('aria-expanded')).toBe('true');
    expect(document.querySelectorAll('.wm-level-grid .wm-level')).toHaveLength(12);
    document.querySelector<HTMLButtonElement>('.wm-level[data-index="6"]')!.click();
    expect(levels.getAttribute('aria-expanded')).toBe('false');
    expect(document.querySelector('.wm3d-detail')?.getAttribute('data-track')).toBe('d1-dust-devil');
    expect(document.querySelector<HTMLButtonElement>('.wm-ride')!.disabled).toBe(true);
    expect(document.querySelector('.wm-ride')?.textContent).toContain('Medal every Alpine track');
    levels.click();
    screen.back();
    expect(levels.getAttribute('aria-expanded')).toBe('false');
    expect(cb.goto).not.toHaveBeenCalled();
    expect(document.querySelector<HTMLButtonElement>('.wm-quick')!.disabled).toBe(false);
    screen.hide();
  });

  it('starts with map movement and gives rotation an explicit reversible control', async () => {
    const { screen } = fixture({ seeded: true });
    await vi.waitFor(() => expect(mounts.calls).toHaveLength(1));
    const scene = mounts.calls[0]!.scene;
    expect(scene.setDragMode).toHaveBeenCalledWith('pan');
    const orbit = document.querySelector<HTMLButtonElement>('.wm-orbit')!;
    expect(orbit.getAttribute('aria-pressed')).toBe('false');
    orbit.click();
    expect(scene.setDragMode).toHaveBeenLastCalledWith('orbit');
    expect(orbit.getAttribute('aria-pressed')).toBe('true');
    screen.hide();
    expect(orbit.getAttribute('aria-pressed')).toBe('false');
    screen.show();
    await vi.waitFor(() => expect(mounts.calls).toHaveLength(2));
    expect(mounts.calls[1]!.scene.setDragMode).toHaveBeenCalledWith('pan');
    orbit.click();
    expect(mounts.calls[1]!.scene.setDragMode).toHaveBeenLastCalledWith('orbit');
    orbit.click();
    expect(mounts.calls[1]!.scene.setDragMode).toHaveBeenLastCalledWith('pan');
    expect(orbit.getAttribute('aria-pressed')).toBe('false');
    mounts.calls[1]!.select(0);
    expect(document.querySelector('.wm3d-state')?.textContent).toContain('Gold cleared');
    mounts.calls[1]!.select(3);
    expect(document.querySelector('.wm3d-state')?.textContent).toContain('Ready to ride');
    mounts.calls[1]!.select(6);
    expect(document.querySelector('.wm3d-state')?.textContent).toContain('Locked');
    screen.hide();
  });

  it('keyboard and touch-selected tower launch the same course; Menu and Ghost retain callbacks', async () => {
    const { screen, cb } = fixture({ seeded: true, recording: true, lastPlayed: 'c1-low-tide' });
    await vi.waitFor(() => expect(mounts.calls).toHaveLength(1));
    screen.nav(1, 0);
    expect(document.querySelector('.wm3d-detail')?.getAttribute('data-track')).toBe('c2-crane-hop');
    screen.nav(-1, 0);
    screen.alt();
    expect(cb.watchPb).toHaveBeenCalledWith('c1-low-tide');
    vi.useFakeTimers();
    screen.confirm();
    vi.advanceTimersByTime(200);
    expect(cb.play).toHaveBeenCalledWith('c1-low-tide');
    vi.advanceTimersByTime(300);
    expect(screen.visible).toBe(false);
    const next = fixture();
    next.screen.back();
    expect(next.cb.goto).toHaveBeenCalledWith('menu');
    next.screen.hide();
  });

  it('portrait shows rotate prompt without mounting WebGL, then landscape mounts once', async () => {
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: 390 });
    Object.defineProperty(window, 'innerHeight', { configurable: true, value: 844 });
    const before3d = vi.fn(async () => true);
    const after3d = vi.fn(async () => true);
    const { screen } = fixture({ gpu: { before3d, after3d } });
    expect(document.querySelector('.wm3d-rotate.show')?.textContent).toContain('Rotate your phone');
    expect(mounts.calls).toHaveLength(0);
    expect(before3d).not.toHaveBeenCalled();
    Object.defineProperty(window, 'innerWidth', { configurable: true, value: 900 });
    Object.defineProperty(window, 'innerHeight', { configurable: true, value: 400 });
    window.dispatchEvent(new Event('resize'));
    await vi.waitFor(() => expect(mounts.calls).toHaveLength(1));
    expect(before3d).toHaveBeenCalledOnce();
    screen.hide();
    expect(after3d).toHaveBeenCalledOnce();
  });
});
