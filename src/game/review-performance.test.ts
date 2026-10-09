// @vitest-environment jsdom
import { describe, expect, it, vi } from 'vitest';
import { App } from './app';
import { ReviewPerformanceWindow, reviewPerformanceEnabled } from './review-performance';
import type { FrameSplit } from './bench';
const context = { trackId: 'c1-low-tide', outfit: 'street-remastered', bike: 'rookie', quality: 'low' as const, cap: 60 };
const split: FrameSplit = { totalMs: 3, physicsMs: .2, submitMs: 2, hudMs: .1, audioMs: .1, pollMs: .1, advanceMs: 2.2, otherMs: .5, ticks: 2 };

/** Synthetic inputs verify the instrument; they are never a device FPS result. */
describe('opt-in review riding frame receipt', () => {
  it('uses only the existing review opt-in', () => {
    expect(reviewPerformanceEnabled('', null)).toBe(false);
    expect(reviewPerformanceEnabled('?review=10', null)).toBe(false);
    expect(reviewPerformanceEnabled('?review=1', null)).toBe(true);
    expect(reviewPerformanceEnabled('', 'stored-password')).toBe(true);
  });

  it('counts submitted frames and retains 20 continuous seconds without per-frame snapshots', () => {
    const win = new ReviewPerformanceWindow();
    for (let i = 0; i <= 1500; i++) win.frame(1000 + i * 20, context, true, true, split);
    const r = win.snapshot(31_000)!;
    expect(r).toMatchObject({ trackId: context.trackId, phase: 'riding', ready: true, windowMs: 20_000, frames: 1000, fps: 50, sampleAgeMs: 0, dropped: 0 });
    expect(r.frameMs).toEqual({ p50: 20, p95: 20, max: 20 });
    expect(r.cpuMs).toEqual({ p50: 3, p95: 3, max: 3 });
    expect(win.snapshot(32_001)?.ready).toBe(false);
  });

  it('does not count calls that skipped submission and never clamps a slow wall interval', () => {
    const win = new ReviewPerformanceWindow();
    win.frame(1000, context, true, true, split);
    win.frame(1100, context, true, false, split);
    win.frame(1400, context, true, true, split);
    expect(win.snapshot(1400)).toMatchObject({ frames: 1, fps: 2.5, ready: false, frameMs: { p50: 400, p95: 400, max: 400 }, dropped: 1 });
  });

  it('drops Garage, crash, pause and hidden discontinuities instead of joining windows', () => {
    for (const discontinuity of ['garage', 'crash', 'pause', 'hidden']) {
      const win = new ReviewPerformanceWindow();
      win.frame(1000, context, true, true, split);
      win.frame(1100, context, true, true, split);
      expect(win.snapshot(1100)?.frames).toBe(1);
      win.frame(1200, context, false, true, split);
      expect(win.snapshot(1200), discontinuity).toBeNull();
      win.frame(30_000, context, true, true, split);
      win.frame(30_100, context, true, true, split);
      expect(win.snapshot(30_100)).toMatchObject({ frames: 1, windowMs: 100, ready: false });
    }
  });

  it('starts fresh after track, outfit, bike, tier or cap changes', () => {
    for (const patch of [{ trackId: 'c2' }, { outfit: 'street-mustard' }, { bike: 'pro' }, { quality: 'high' as const }, { cap: 30 }]) {
      const win = new ReviewPerformanceWindow();
      win.frame(1000, context, true, true, split);
      win.frame(1100, context, true, true, split);
      win.frame(30_000, { ...context, ...patch }, true, true, split);
      expect(win.snapshot(30_000)).toBeNull();
    }
  });

  it('exposes notes only for the current active ride, never stale Garage or paused samples', () => {
    const win = new ReviewPerformanceWindow();
    const selectedTextures = { method: 'selected-rider-material-typed-array-payloads' as const, textureCount: 0, mapReferences: 0, payloadBytes: 0, compressedTextures: 0, unavailableTextures: 0, incompleteTextures: 0, textures: [] };
    const textureSnapshot = vi.fn(() => selectedTextures);
    const game = { phase: () => 'riding', paused: () => false, currentTrack: { id: context.trackId }, currentBike: context.bike, qualityTier: context.quality, rendererRef: { selectedTextureReceipt: textureSnapshot } };
    const app = Object.create(App.prototype) as App;
    Object.assign(app, { reviewPerformance: win, screen: 'run', game, riderOutfit: context.outfit, frameCapHz: () => 60 });
    const hidden = vi.spyOn(document, 'hidden', 'get').mockReturnValue(false);
    const clock = vi.spyOn(performance, 'now').mockReturnValue(31_000);
    try {
      const notes = app.testApi().reviewPerformance!;
      expect(notes()).toBeNull();
      for (let i = 0; i <= 1500; i++) win.frame(1000 + i * 20, context, true, true, split);
      expect(textureSnapshot).not.toHaveBeenCalled();
      expect(notes()).toMatchObject({ ready: true, trackId: context.trackId, fps: 50, selectedTextures });
      expect(textureSnapshot).toHaveBeenCalledTimes(1);
      game.currentTrack = { id: 'c2' }; expect(notes()).toBeNull();
      game.currentTrack = { id: context.trackId }; game.paused = () => true; expect(notes()).toBeNull();
      game.paused = () => false; hidden.mockReturnValue(true); expect(notes()).toBeNull();
      hidden.mockReturnValue(false); Object.assign(app, { screen: 'garage' }); expect(notes()).toBeNull();
      expect(textureSnapshot).toHaveBeenCalledTimes(1); // No traversal on invalid/paused samples.
      Object.assign(app, { screen: 'run' });
      Object.assign(game, { rendererRef: {} });
      expect(notes()?.selectedTextures).toBeUndefined(); // Scaffold renderers keep the optional shape.
    } finally { hidden.mockRestore(); clock.mockRestore(); }
  });

  it('remains bounded over a long ride and supports zero as its first timestamp', () => {
    const win = new ReviewPerformanceWindow();
    for (let i = 0; i <= 10_000; i++) win.frame(i * 20, context, true, true, split);
    expect(win.snapshot(200_000)).toMatchObject({ frames: 1000, windowMs: 20_000, fps: 50, ready: true });
    win.reset();
    win.frame(0, context, true, true, split);
    win.frame(20, context, true, true, split);
    expect(win.snapshot(20)).toMatchObject({ frames: 1, windowMs: 20, fps: 50 });
  });
});
