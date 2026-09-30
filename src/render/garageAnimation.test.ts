import { describe, expect, it } from 'vitest';
import { ThreeRenderer } from './index';
import { GltfRider } from './hero/gltfRider';

function fixture(on = true, moving = true) {
  const rider = Object.assign(Object.create(GltfRider.prototype) as object, { clips: new Map(moving ? [['idle_breathe', {}]] : []) });
  const fields = { stageOn: on, stageTime: 0, frameDirty: false, riderRef: rider, bikeRef: {} };
  const renderer = Object.assign(Object.create(ThreeRenderer.prototype) as object, fields) as unknown as ThreeRenderer;
  return { renderer, state: renderer as unknown as typeof fields };
}

describe('Garage presentation clock', () => {
  it('advances by explicit elapsed time across different render cadences', () => {
    const a = fixture(), b = fixture();
    for (let i = 0; i < 60; i++) a.renderer.advancePresentation(1 / 60);
    for (let i = 0; i < 30; i++) b.renderer.advancePresentation(1 / 30);
    expect(a.state.stageTime).toBeCloseTo(1, 12);
    expect(b.state.stageTime).toBeCloseTo(a.state.stageTime, 12);
    expect(a.state.frameDirty).toBe(true);
  });
  it('keeps riding and static Garage documents eligible for unchanged-frame skips', () => {
    for (const f of [fixture(false), fixture(true, false)]) {
      f.renderer.advancePresentation(1 / 60);
      expect(f.state.stageTime).toBe(0);
      expect(f.state.frameDirty).toBe(false);
    }
  });
  it('rejects invalid elapsed values and bounds resume after backgrounding', () => {
    const f = fixture();
    for (const dt of [NaN, Infinity, -1, 0]) f.renderer.advancePresentation(dt);
    expect(f.state.stageTime).toBe(0);
    f.renderer.advancePresentation(30);
    expect(f.state.stageTime).toBe(0.1);
  });
});
