import { beforeEach, describe, expect, it, vi } from 'vitest';
import type { GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js';
import type { loadGltf as loadGltfSignature } from './gltf';
import { SELECTED_RIDER_ASSET } from './selectedAsset';

const { load, prepare, native, textures } = vi.hoisted(() => ({ load: vi.fn(), prepare: vi.fn(), native: vi.fn(), textures: vi.fn() }));
vi.mock('three/examples/jsm/loaders/GLTFLoader.js', () => ({
  GLTFLoader: class { setMeshoptDecoder() { return this; } load = load; },
}));
vi.mock('./lod', () => ({ prepareHero: prepare }));
vi.mock('./selectedDriver', () => ({ loadSelectedRiderClass: native }));
vi.mock('./selectedTextures', () => ({ configureSelectedTextures: textures }));

let loadGltf: typeof loadGltfSignature;
beforeEach(async () => {
  vi.resetModules();
  load.mockReset(); prepare.mockReset().mockResolvedValue(undefined);
  native.mockReset().mockResolvedValue(undefined); textures.mockReset().mockResolvedValue(undefined);
  loadGltf = (await import('./gltf')).loadGltf;
});
const selectedDocument = (): GLTF => ({ scene: { userData: {}, traverse: () => undefined } } as unknown as GLTF);
const flush = async (): Promise<void> => { for (let i = 0; i < 12; i++) await Promise.resolve(); };

describe('model download retries', () => {
  it('rejects incomplete preparation of an original outfit and retries it', async () => {
    prepare.mockRejectedValueOnce(new Error('incomplete'));
    load.mockImplementation((_url, success) => success(selectedDocument()));
    const failed = loadGltf('models/rider-street-mustard.glb', true);
    expect(await failed).toBeNull();
    const retry = loadGltf('models/rider-street-mustard.glb', true);
    expect(retry).not.toBe(failed);
    expect(await retry).not.toBeNull();
    expect(load).toHaveBeenCalledTimes(2);
  });

  it('shares an in-flight request, evicts a failure, and retains a successful document', async () => {
    let fail!: (error: Error) => void;
    load.mockImplementationOnce((_url, _success, _progress, onError) => { fail = onError; });
    const first = loadGltf('models/rider-race-bluewhite.glb', true);
    expect(loadGltf('models/rider-race-bluewhite.glb', true)).toBe(first);
    expect(load).toHaveBeenCalledTimes(1);
    fail(new Error('offline'));
    expect(await first).toBeNull();
    const document = { scene: { traverse: () => undefined } } as unknown as GLTF;
    load.mockImplementationOnce((_url, onSuccess) => { onSuccess(document); });
    const retry = loadGltf('models/rider-race-bluewhite.glb', true);
    expect(retry).not.toBe(first);
    expect(await retry).toBe(document);
    expect(loadGltf('models/rider-race-bluewhite.glb', true)).toBe(retry);
    expect(load).toHaveBeenCalledTimes(2);
    expect(textures).not.toHaveBeenCalled();
  });

  it('awaits selected texture setup, parse preparation, and native readiness before caching one shared full/LOD document', async () => {
    let setup!: () => void, prepared!: () => void, ready!: () => void;
    textures.mockImplementationOnce(() => new Promise<void>((resolve) => { setup = resolve; }));
    prepare.mockImplementationOnce(() => new Promise<void>((resolve) => { prepared = resolve; }));
    native.mockImplementationOnce(() => new Promise<void>((resolve) => { ready = resolve; }));
    const document = selectedDocument();
    load.mockImplementationOnce((url, onSuccess, onProgress) => {
      expect(url).toBe(SELECTED_RIDER_ASSET.url);
      onProgress({ loaded: 20, total: 100 }); onProgress({ loaded: 100, total: 100 });
      onSuccess(document);
    });
    const bytes = { add: vi.fn() };
    const first = loadGltf('models/rider-street-remastered.glb', true, bytes);
    expect(loadGltf('models/rider-street-remastered-lod.glb', true, bytes)).toBe(first);
    expect(load).not.toHaveBeenCalled();
    let settled = false;
    void first.then(() => { settled = true; });
    setup(); await flush();
    expect(load).toHaveBeenCalledTimes(1);
    expect(document.scene.userData.selectedRemaster).toBe(true);
    expect(native).not.toHaveBeenCalled();
    expect(settled).toBe(false);
    prepared(); await flush();
    expect(native).toHaveBeenCalledTimes(1);
    expect(settled).toBe(false);
    ready();
    expect(await first).toBe(document);
    expect(loadGltf('models/rider-street-remastered-lod.glb', true, bytes)).toBe(first);
    expect(bytes.add.mock.calls).toEqual([[20], [80]]);
    expect(textures).toHaveBeenCalledTimes(1);
  });

  it.each(['texture', 'prepare', 'native'] as const)('evicts a selected %s failure and permits a fresh explicit retry', async (failure) => {
    ({ texture: textures, prepare, native }[failure]).mockRejectedValueOnce(new Error('transient'));
    load.mockImplementation((_url, success) => success(selectedDocument()));
    const failed = loadGltf('models/rider-street-remastered.glb', true);
    expect(await failed).toBeNull();
    const retry = loadGltf('models/rider-street-remastered-lod.glb', true);
    expect(retry).not.toBe(failed);
    expect(await retry).not.toBeNull();
    expect(textures).toHaveBeenCalledTimes(2);
    expect(load).toHaveBeenCalledTimes(failure === 'texture' ? 1 : 2);
  });
});
