// @vitest-environment jsdom
/**
 * The native storage mirror (src/platform/storage.ts): progress survives a WebView that evicted its localStorage,
 * writes land in the durable store in order, and the web keeps plain localStorage.
 */
import { afterEach, beforeEach, describe, expect, it } from 'vitest';
import { durableFlushed, hydrateStorage, persistentStorage, resetStorageForTests, type DurableKV } from './storage';

/** An in-memory stand-in for @capacitor/preferences, async like the real bridge. */
function memoryKV(seed: Record<string, string> = {}): DurableKV & { data: Map<string, string> } {
  const data = new Map(Object.entries(seed));
  const tick = (): Promise<void> => new Promise((r) => setTimeout(r, 0));
  return {
    data,
    keys: async () => (await tick(), [...data.keys()]),
    get: async (k) => (await tick(), data.get(k) ?? null),
    set: async (k, v) => {
      await tick();
      data.set(k, v);
    },
    remove: async (k) => {
      await tick();
      data.delete(k);
    },
    clear: async () => {
      await tick();
      data.clear();
    },
  };
}

beforeEach(() => {
  localStorage.clear();
  resetStorageForTests();
});
afterEach(() => resetStorageForTests());

describe('persistentStorage', () => {
  it('is plain localStorage on the web (no durable store)', () => {
    expect(persistentStorage()).toBe(localStorage);
  });

  it('restores progress the WebView evicted, from the durable store', async () => {
    const kv = memoryKV({ 'rockhop.best.b1': '41.2', 'rockhop.volume': '0.8' });
    const r = await hydrateStorage(kv);
    expect(r.restored).toBe(2);
    expect(localStorage.getItem('rockhop.best.b1')).toBe('41.2');
    expect(persistentStorage()!.getItem('rockhop.volume')).toBe('0.8');
  });

  it('pushes keys only localStorage holds (first native launch) into the durable store', async () => {
    localStorage.setItem('rockhop.onboarded', '1');
    const kv = memoryKV();
    const r = await hydrateStorage(kv);
    expect(r.pushed).toBe(1);
    expect(kv.data.get('rockhop.onboarded')).toBe('1');
  });

  it('writes through in order: the last write of a key wins, removes and clear reach the durable store', async () => {
    const kv = memoryKV();
    await hydrateStorage(kv);
    const s = persistentStorage()!;
    expect(s).not.toBe(localStorage);
    for (let i = 0; i < 20; i++) s.setItem('rockhop.best.e1', String(60 - i));
    s.setItem('rockhop.gone', 'x');
    s.removeItem('rockhop.gone');
    await durableFlushed();
    expect(kv.data.get('rockhop.best.e1')).toBe('41');
    expect(kv.data.has('rockhop.gone')).toBe(false);
    expect(s.getItem('rockhop.best.e1')).toBe('41');
    s.clear();
    await durableFlushed();
    expect(kv.data.size).toBe(0);
    expect(localStorage.length).toBe(0);
  });

  it('a failing durable write is logged, never thrown, and localStorage still has the value', async () => {
    const kv = memoryKV();
    await hydrateStorage(kv);
    kv.set = () => Promise.reject(new Error('disk full'));
    const s = persistentStorage()!;
    expect(() => s.setItem('rockhop.x', '1')).not.toThrow();
    await durableFlushed();
    expect(localStorage.getItem('rockhop.x')).toBe('1');
  });

  it('recovers a newer medal after the app exits before the durable write finishes', async () => {
    const kv = memoryKV({ 'rockhop.medal.c1': 'bronze' });
    await hydrateStorage(kv);
    const set = kv.set;
    kv.set = () => new Promise<void>(() => undefined);
    persistentStorage()!.setItem('rockhop.medal.c1', 'diamond');
    resetStorageForTests(); // new WebView process; its unfinished bridge request is gone
    kv.set = set;
    await hydrateStorage(kv);
    expect(localStorage.getItem('rockhop.medal.c1')).toBe('diamond');
    expect(kv.data.get('rockhop.medal.c1')).toBe('diamond');
  });

  it('recovers a pending removal and clear after the app exits', async () => {
    const kv = memoryKV({ 'rockhop.best.c1': '30', 'rockhop.scrap': '800' });
    await hydrateStorage(kv);
    const remove = kv.remove;
    kv.remove = () => new Promise<void>(() => undefined);
    persistentStorage()!.removeItem('rockhop.best.c1');
    resetStorageForTests();
    kv.remove = remove;
    await hydrateStorage(kv);
    expect(localStorage.getItem('rockhop.best.c1')).toBeNull();
    expect(kv.data.has('rockhop.best.c1')).toBe(false);

    const clear = kv.clear;
    kv.clear = () => new Promise<void>(() => undefined);
    persistentStorage()!.clear();
    resetStorageForTests();
    kv.clear = clear;
    await hydrateStorage(kv);
    expect(localStorage.getItem('rockhop.scrap')).toBeNull();
    expect(kv.data.size).toBe(0);
  });
});
