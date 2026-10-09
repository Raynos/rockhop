import { afterEach, expect, it, vi } from 'vitest';
import { warmOfflineCode } from './offline-pack';

afterEach(() => vi.unstubAllGlobals());

it('overlaps four requests and waits for bodies before freeing a slot or finishing', async () => {
  const finish: (() => void)[] = [];
  const paths: string[] = [];
  const manifest = { items: Array.from({ length: 6 }, (_, i) => ({ path: `/lazy-${i}`, phase: 'other' })) };
  const fetcher = vi.fn(async (path: string) => {
    if (path === './load-manifest.json') return { ok: true, json: async () => manifest };
    paths.push(path);
    return { arrayBuffer: () => new Promise<ArrayBuffer>(resolve => finish.push(() => resolve(new ArrayBuffer(0)))) };
  });
  vi.stubGlobal('fetch', fetcher);
  let complete = false;
  const warm = warmOfflineCode().then(() => { complete = true; });
  await vi.waitFor(() => expect(finish).toHaveLength(4));
  expect(paths).toHaveLength(4); expect(complete).toBe(false);
  finish[0]!(); finish[1]!();
  await vi.waitFor(() => expect(finish).toHaveLength(6));
  expect(complete).toBe(false);
  for (const done of finish.slice(2)) done();
  await warm;
  expect(complete).toBe(true); expect(new Set(paths).size).toBe(6);
});

it('warms only lazy offline phases and keeps going after a body or fetch failure', async () => {
  const items = ['core', 'worldmap', 'other', 'audio-worklet', 'hero'].map(phase => ({ path: `/${phase}`, phase }));
  const read = vi.fn().mockResolvedValue(new ArrayBuffer(0));
  const fetcher = vi.fn(async (path: string) => {
    if (path === './load-manifest.json') return { ok: true, json: async () => ({ items }) };
    if (path === '/other') throw new Error('offline');
    if (path === '/worldmap') return { arrayBuffer: () => Promise.reject(new Error('lost body')) };
    return { arrayBuffer: read };
  });
  vi.stubGlobal('fetch', fetcher);
  await warmOfflineCode();
  expect(fetcher.mock.calls.map(([path]) => path).sort()).toEqual(['./load-manifest.json', '/audio-worklet', '/other', '/worldmap']);
  expect(read).toHaveBeenCalledTimes(1);
});
