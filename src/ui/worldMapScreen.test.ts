// @vitest-environment jsdom
import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import type { Medal, TrackDef } from '../core/types';
import { ROCKHOP_ALL } from '../tracks';
import type { ArtManifest } from './art';
import type { BestEntry } from './best';
import type { FrontCallbacks, FrontState } from './front';
import type { UiSfx } from './sfx';
import { WorldMapScreen } from './worldMapScreen';

const mounts = vi.hoisted(() => ({ calls: [] as Array<{ root: HTMLElement; select: (index: number) => void; scene: { dispose: ReturnType<typeof vi.fn>; selectStage: ReturnType<typeof vi.fn>; setProgress: ReturnType<typeof vi.fn>; resize: ReturnType<typeof vi.fn> } }> }));
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

function fixture(options: { seeded?: boolean; lastPlayed?: string | null; recording?: boolean; gpu?: { before3d(): Promise<boolean>; after3d(): Promise<boolean> | boolean } } = {}) {
  const bestOf = (id: string): BestEntry | null => {
    const medal = options.seeded ? SEEDED[id] : undefined;
    if (!medal) return null;
    return { time: 41.2, faults: 0, medal, bike: 'rookie', ...(options.recording ? { recording: '{}' } : {}) } as BestEntry;
  };
  const state = { dev: false, lastPlayed: options.lastPlayed ?? null, ghost: true, bikeClass: 'rookie' } as FrontState;
  const cb = { play: vi.fn(), goto: vi.fn(), watchPb: vi.fn() } as unknown as FrontCallbacks;
  const sfx = { tick: vi.fn(), confirm: vi.fn(), back: vi.fn(), launch: vi.fn() } as unknown as UiSfx;
  const screen = new WorldMapScreen(document.body, sfx, {} as ArtManifest, cb, bestOf, () => state, () => [], options.gpu);
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
    mounts.calls[0]!.select(6);
    expect(document.querySelector<HTMLButtonElement>('.wm-ride')?.disabled).toBe(true);
    expect(document.querySelector('.wm3d-detail .rule')?.textContent).toContain('Medal every Alpine track');
    screen.confirm();
    expect(cb.play).not.toHaveBeenCalled();
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
