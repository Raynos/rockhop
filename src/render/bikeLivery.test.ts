/**
 * Ask 50: the hero set is resident — `setModels` fetches every hero file once, one instance per document is built
 * once and never disposed, and an outfit / class / tier / garage change is a detach / attach of pooled instances:
 * no fetch, no new instance, no dispose (a disposed instance dropped the hero-only program variants to refcount 0 and
 * the next frame relinked them). A missing file leaves its slot to the other detail and is retried by the next call.
 */
import { afterEach, describe, expect, it, vi } from 'vitest';
import type { GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { ThreeRenderer } from './index';
import { loadGltf } from './hero/gltf';
import { GltfBike } from './hero/gltfBike';
import { GltfRider } from './hero/gltfRider';
import { HERO_FILES_BY_OUTFIT_CLASS } from './hero/urls';
import { HERO_BOOT_FILE_SET, SELECTED_HERO_FILES } from '../boot/asset-totals';

vi.mock('./hero/gltf', async (original) => ({ ...await original<Record<string, unknown>>(), loadGltf: vi.fn() }));
afterEach(() => vi.restoreAllMocks());

const ALL = [...new Set(Object.values(HERO_FILES_BY_OUTFIT_CLASS).flatMap((c) => [...c.rookie, ...c.pro]))];

/** A stub instance standing in for `new GltfBike` / `new GltfRider` (the constructors need decoded geometry). */
function stubInstance(kind: 'bike' | 'rider', doc: GLTF) {
  const proto = kind === 'bike' ? GltfBike.prototype : GltfRider.prototype;
  return Object.assign(Object.create(proto) as object, {
    source: doc, root: { name: `${kind}:gltf` }, materials: [], placer: { copyFrom() {} }, ground: null, contacts: [],
    setLivery: vi.fn(), attach: vi.fn(), detach: vi.fn(), setStage: vi.fn(), dispose: vi.fn(),
  });
}

function fixture(tier: 'high' | 'medium' | 'low' = 'medium', deviceClass: 'phone' | 'desktop' = 'phone') {
  const docs = new Map<string, GLTF>(ALL.map((f) => [f, { name: f } as unknown as GLTF]));
  const selected = { name: SELECTED_HERO_FILES[0] } as unknown as GLTF;
  for (const file of SELECTED_HERO_FILES) docs.set(file, selected);
  const built: string[] = [];
  const scene = { add: vi.fn(), remove: vi.fn() };
  const fields = {
    models: { bikeModel: 'gltf', riderModel: 'gltf' }, tier, deviceClass, stageOn: false, disposed: false, phase: 'menu',
    riderOutfit: 'street-mustard', riderDocumentOutfit: null, bikeClass: 'rookie', bikeDocumentClass: null,
    heroDocs: new Map<string, GLTF>(), heroDocUrl: new Map<GLTF, string>(), heroPool: new Map<GLTF, unknown>(),
    heroLoading: 0, heroPending: Promise.resolve(), invalidate: vi.fn(), resize: vi.fn(), scene, sceneEpoch: 0,
    bike: { root: { name: 'bike:proc' }, placer: {}, ground: null, dispose: vi.fn() }, rider: { root: { name: 'rider:proc' }, detach: vi.fn(), attach: vi.fn(), dispose: vi.fn() },
    bikeRef: null as unknown, riderRef: null as unknown, ghost: null, retireObject: vi.fn(), applyTierVisibility: vi.fn(), swapPendingFrame: null,
    heroSwaps: [] as unknown[],
  };
  fields.bikeRef = fields.bike; fields.riderRef = fields.rider;
  const renderer = Object.assign(Object.create(ThreeRenderer.prototype) as object, fields) as unknown as ThreeRenderer;
  // The pool builds through the real `pooled()`, whose constructors need geometry: intercept at the instance level.
  const r = renderer as unknown as { pooled(doc: GLTF, kind: 'bike' | 'rider'): unknown };
  r.pooled = (doc, kind) => {
    let i = fields.heroPool.get(doc);
    if (!i) { i = stubInstance(kind, doc); fields.heroPool.set(doc, i); built.push((doc as unknown as { name: string }).name); }
    return i;
  };
  vi.mocked(loadGltf).mockImplementation(async (url) => docs.get(url) ?? null);
  vi.spyOn(console, 'warn').mockImplementation(() => undefined);
  return { renderer, state: renderer as unknown as typeof fields, docs, built, scene };
}

const settle = async (renderer: ThreeRenderer): Promise<void> => {
  const r = renderer as unknown as { heroPending: Promise<void> };
  let pending: Promise<void>;
  do { pending = r.heroPending; await pending; } while (pending !== r.heroPending);
};
const drawn = (state: unknown) => { const s = state as { bike: { source?: { name: string } }; rider: { source?: { name: string } } }; return [s.bike.source?.name, s.rider.source?.name]; };

describe('resident hero set', () => {
  it('loads the complete declared hero set with a saved procedural bike', async () => {
    const { renderer, state } = fixture();
    renderer.setModels({ bikeModel: 'proc', riderModel: 'proc' });
    await settle(renderer);
    expect(state.heroDocs.size).toBe(16);
    expect(vi.mocked(loadGltf).mock.calls.map(([url]) => url)).toEqual(HERO_BOOT_FILE_SET);
    expect(state.bike.root.name).toBe('bike:proc');
    expect(state.rider.root.name).toBe('rider:gltf');
    expect(state.riderDocumentOutfit).toBe('street-mustard');
  });

  it('keeps the valid rider when a missing remaster needs retry', async () => {
    const { renderer, state, scene, docs } = fixture();
    renderer.setModels({ bikeModel: 'gltf', riderModel: 'gltf' });
    await settle(renderer);
    const original = state.rider;
    for (const file of SELECTED_HERO_FILES) { docs.delete(file); state.heroDocs.delete(file); }
    scene.remove.mockClear();
    expect(await renderer.setRiderOutfit('street-remastered')).toBe(false);
    expect(state.rider).toBe(original);
    expect(state.riderOutfit).toBe('street-mustard');
    expect(scene.remove).not.toHaveBeenCalled();
  });

  it('fails a default cold boot visibly when the mandatory sixth fails, then retries it alone', async () => {
    const { renderer, state, docs } = fixture();
    for (const file of SELECTED_HERO_FILES) docs.delete(file);
    Object.assign(renderer, { art: { whenSettled: Promise.resolve() }, retirement: { whenIdle: () => Promise.resolve() }, rebuildIfArtLanded: vi.fn() });
    const initial = state.rider;
    renderer.setModels({ bikeModel: 'gltf', riderModel: 'gltf' });
    await settle(renderer);
    await expect(renderer.whenReady()).rejects.toThrow('Remaster load failed. Retry.');
    expect(state.rider).toBe(initial);
    expect(state.riderDocumentOutfit).toBeNull();
    const selected = { name: SELECTED_HERO_FILES[0] } as unknown as GLTF;
    for (const file of SELECTED_HERO_FILES) docs.set(file, selected);
    vi.mocked(loadGltf).mockClear();
    renderer.setModels({ bikeModel: 'gltf', riderModel: 'gltf' });
    await expect(renderer.whenReady()).resolves.toBeUndefined();
    expect(vi.mocked(loadGltf).mock.calls.map(([url]) => url)).toEqual([...SELECTED_HERO_FILES]);
    expect(state.riderDocumentOutfit).toBe('street-mustard');
    expect(state.rider.root.name).toBe('rider:gltf');
  });

  it('prepares the sixth in the same resident pool before its first Garage selection', async () => {
    const { renderer, state, built } = fixture();
    renderer.setModels({ bikeModel: 'gltf', riderModel: 'gltf' });
    await settle(renderer);
    Object.assign(renderer, {
      compileMaterials: vi.fn(async () => undefined), uploadHeroTextures: vi.fn(async () => undefined),
      mirrorCopies: vi.fn(() => ({ mirror: {}, pairs: [] })), syncReflection: vi.fn(), reflectionMats: new Map(),
    });
    await (renderer as unknown as { warmHeroes(report: () => void): Promise<void> }).warmHeroes(() => undefined);
    const selected = state.heroDocs.get(SELECTED_HERO_FILES[0])!;
    expect(state.heroDocs.get(SELECTED_HERO_FILES[1])).toBe(selected);
    const resident = state.heroPool.get(selected);
    expect(resident).toBeDefined();
    expect(built.filter((name) => name === SELECTED_HERO_FILES[0])).toHaveLength(1);
    expect(state.heroPool.size).toBe(15);
    vi.mocked(loadGltf).mockClear();
    const count = built.length;
    expect(await renderer.setRiderOutfit('street-remastered')).toBe(true);
    expect(state.rider).toBe(resident);
    expect(await renderer.setRiderOutfit('street-mustard')).toBe(true);
    expect(await renderer.setRiderOutfit('street-remastered')).toBe(true);
    expect(state.rider).toBe(resident);
    expect(built).toHaveLength(count);
    expect(loadGltf).not.toHaveBeenCalled();
  });

  it('boot fetches all hero logical names and later swaps fetch nothing and build nothing new', async () => {
    const { renderer, state, built } = fixture();
    renderer.setModels({ bikeModel: 'gltf', riderModel: 'gltf' });
    await settle(renderer);
    expect(vi.mocked(loadGltf).mock.calls.map(([url]) => url).sort()).toEqual([...HERO_BOOT_FILE_SET].sort());
    expect(state.heroDocs.size).toBe(16);
    expect(drawn(state)).toEqual(['models/bike-rookie.glb', 'models/rider-street-mustard.glb']); // phone medium: the authored pair in level (ask 60)
    expect(built).toEqual(['models/bike-rookie.glb', 'models/rider-street-mustard.glb']);
    expect(state.retireObject).toHaveBeenCalledTimes(2); // the procedural kit, once
    vi.mocked(loadGltf).mockClear();
    // Outfit, class, garage, tier: detach / attach of pooled instances — no fetch, and a revisited document is the same instance.
    expect(await renderer.setRiderOutfit('race-bluewhite')).toBe(true);
    expect(drawn(state)[1]).toBe('models/rider-race-bluewhite.glb');
    renderer.setBikeClass('pro');
    expect(drawn(state)[0]).toBe('models/bike-pro.glb');
    state.tier = 'low'; // the governor on low: the LOD pair in level
    (renderer as unknown as { applyModels(): void }).applyModels();
    expect(drawn(state)).toEqual(['models/bike-pro-lod.glb', 'models/rider-race-bluewhite-lod.glb']);
    Object.assign(renderer, { applyGarageStage: vi.fn(), clearGarageStage: vi.fn(), dropReflection: vi.fn(), reflectable: () => false });
    renderer.setGarageStage(true);
    expect(drawn(state)).toEqual(['models/bike-pro.glb', 'models/rider-race-bluewhite.glb']); // ask 52: the garage draws the authored bike and rider
    renderer.setGarageStage(false);
    expect(drawn(state)).toEqual(['models/bike-pro-lod.glb', 'models/rider-race-bluewhite-lod.glb']);
    const first = state.heroPool.get(state.heroDocs.get('models/rider-street-mustard-lod.glb')!);
    expect(await renderer.setRiderOutfit('street-mustard')).toBe(true);
    expect(state.rider).not.toBe(first); // low: the LOD instance, built now
    state.tier = 'medium';
    (renderer as unknown as { applyModels(): void }).applyModels();
    expect(state.rider).toBe(state.heroPool.get(state.heroDocs.get('models/rider-street-mustard.glb')!)); // the boot instance, resident
    expect(loadGltf).not.toHaveBeenCalled();
    expect(state.retireObject).toHaveBeenCalledTimes(2); // never a pooled instance
    for (const i of state.heroPool.values()) expect((i as { dispose: ReturnType<typeof vi.fn> }).dispose).not.toHaveBeenCalled();
    expect(state.heroPool.size).toBe(7); // rookie + pro bikes, mustard + bluewhite riders, their LOD twins at low, the authored mustard once
  });

  it('blocks an incomplete original outfit and retries only its missing document', async () => {
    const { renderer, state, docs } = fixture('high', 'desktop');
    docs.delete('models/rider-street-mustard.glb');
    renderer.setModels({ bikeModel: 'gltf', riderModel: 'gltf' });
    await settle(renderer);
    expect(state.heroDocs.size).toBe(15);
    expect(drawn(state)).toEqual([undefined, undefined]);
    expect((state as unknown as { heroLoadError: Error }).heroLoadError.message).toContain('models/rider-street-mustard.glb');
    docs.set('models/rider-street-mustard.glb', { name: 'models/rider-street-mustard.glb' } as unknown as GLTF);
    vi.mocked(loadGltf).mockClear();
    renderer.setModels({ bikeModel: 'gltf', riderModel: 'gltf' });
    await settle(renderer);
    expect(vi.mocked(loadGltf).mock.calls.map(([url]) => url)).toEqual(['models/rider-street-mustard.glb']); // only the missing one
    expect(drawn(state)[1]).toBe('models/rider-street-mustard.glb');
  });

  it('ignores a stale procedural rider preference and keeps the authored outfit', async () => {
    const { renderer, state } = fixture();
    renderer.setModels({ bikeModel: 'gltf', riderModel: 'gltf' });
    renderer.setModels({ bikeModel: 'gltf', riderModel: 'proc' });
    await settle(renderer);
    expect(state.heroDocs.size).toBe(16);
    expect(drawn(state)[0]).toBe('models/bike-rookie.glb');
    expect(state.rider.root.name).toBe('rider:gltf');
    expect(state.riderDocumentOutfit).toBe('street-mustard');
  });
});
