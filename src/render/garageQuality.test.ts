import { afterEach, expect, it, vi } from 'vitest';
import { garagePixelRatio } from './garageQuality';
import { ThreeRenderer } from './index';

afterEach(() => vi.unstubAllGlobals());

it('supersamples desktop and raises the captured phone resolution within the inspection cap', () => {
  expect(garagePixelRatio(1, 1280, 720)).toBe(1.5);
  expect(garagePixelRatio(3, 874, 330)).toBe(2);
  expect(garagePixelRatio(2, 1280, 720)).toBe(2);
});

it('uses native phone DPR for real Garage resize and restores the capped host DPR for riding', () => {
  vi.stubGlobal('window', { devicePixelRatio: 3 });
  const gl = { drawingBufferWidth: 0, drawingBufferHeight: 0 };
  let gpuRatio = 1;
  const gpu = {
    setPixelRatio: vi.fn((ratio: number) => { gpuRatio = ratio; }),
    setSize: vi.fn((width: number, height: number) => {
      gl.drawingBufferWidth = Math.floor(width * gpuRatio);
      gl.drawingBufferHeight = Math.floor(height * gpuRatio);
    }),
  };
  const post = { setSize: vi.fn() };
  const rig = { setAspect: vi.fn() };
  const fields = {
    disposed: false, stageOn: false, tier: 'low', deviceClass: 'phone',
    devicePixelRatio: 1, pixelRatio: 1, width: 0, height: 0, frameDirty: false,
    renderer: gpu, postRef: post, rig, canvas: { style: { width: '', height: '' } },
  };
  const renderer = Object.assign(Object.create(ThreeRenderer.prototype) as object, fields) as unknown as ThreeRenderer;
  const state = renderer as unknown as typeof fields;
  renderer.resize(874, 330, 1.5); // app.fit() has already capped the native DPR of 3.
  expect(gl).toEqual({ drawingBufferWidth: 1311, drawingBufferHeight: 495 });
  state.stageOn = true;
  renderer.resize(874, 330);
  expect(gl).toEqual({ drawingBufferWidth: 1748, drawingBufferHeight: 660 });
  expect(state.devicePixelRatio).toBe(1.5); // inspection must retain the riding cap for exit.
  expect(post.setSize).toHaveBeenLastCalledWith(874, 330, 2);
  expect(rig.setAspect).toHaveBeenLastCalledWith(874 / 330);
  expect(state.canvas.style).toEqual({ width: '874px', height: '330px' });
  expect(state.frameDirty).toBe(true);
  renderer.resize(2800, 1600, 1.5);
  expect(gl).toEqual({ drawingBufferWidth: 2520, drawingBufferHeight: 1440 });
  expect(post.setSize).toHaveBeenLastCalledWith(2800, 1600, 0.9);
  state.stageOn = false;
  renderer.resize(874, 330);
  expect(gl).toEqual({ drawingBufferWidth: 1311, drawingBufferHeight: 495 });
  expect(post.setSize).toHaveBeenLastCalledWith(874, 330, 1.5);
});

it('bounds both axes even when the target budget overrides the supersampling floor', () => {
  for (const [dpr, width, height] of [[1, 1920, 1080], [3, 3000, 900], [2, 1024, 1366], [3, 874, 9000]]) {
    const ratio = garagePixelRatio(dpr!, width!, height!);
    expect(width! * ratio).toBeLessThanOrEqual(2560);
    expect(height! * ratio).toBeLessThanOrEqual(1440);
    expect(ratio).toBeLessThanOrEqual(2);
  }
  expect(garagePixelRatio(1, 1920, 1080)).toBeCloseTo(4 / 3);
  expect(garagePixelRatio(2, 1024, 1366)).toBeCloseTo(1440 / 1366);
  expect(garagePixelRatio(1, 0, 0)).toBe(1.5);
});
