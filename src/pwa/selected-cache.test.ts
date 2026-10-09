/** Exercise the actual worker in Node; no browser or AudioContext is created. */
import fs from 'node:fs';
import vm from 'node:vm';
import { describe, expect, it, vi } from 'vitest';

const origin = 'https://rockhop.invalid';
const blobOrigin = 'https://example.public.blob.vercel-storage.com';
const selected = `${blobOrigin}/rider-remaster/${'a'.repeat(64)}/rider.glb`;
const stale = `${blobOrigin}/rider-remaster/${'b'.repeat(64)}/rider.glb`;
const source = fs.readFileSync('src/pwa/sw.js', 'utf8');
type Key = Request | string;
const urlOf = (key: Key): string => typeof key === 'string' ? new URL(key, origin).href : key.url;

class MemoryCache {
  readonly entries = new Map<string, Response>();
  beforePut: () => Promise<void> = async () => undefined;
  beforeMatch: () => Promise<void> = async () => undefined;
  async match(key: Key): Promise<Response | undefined> { await this.beforeMatch(); return this.entries.get(urlOf(key))?.clone(); }
  async put(key: Key, response: Response): Promise<void> { await this.beforePut(); this.entries.set(urlOf(key), response.clone()); }
  async keys(): Promise<Request[]> { return [...this.entries.keys()].map(url => new Request(url)); }
  async delete(key: Key): Promise<boolean> { return this.entries.delete(urlOf(key)); }
}

interface WorkerEvent {
  request: Request;
  respondWith(response: Promise<Response>): void;
  waitUntil(work: Promise<unknown>): void;
}

function worker(pin = selected) {
  const handlers = new Map<string, (event: WorkerEvent) => void>();
  const stores = new Map<string, MemoryCache>();
  const fetch = vi.fn(async (request: Request) => new Response(`bytes:${request.url}`, { status: 200 }));
  const open = async (name: string): Promise<MemoryCache> => {
    let cache = stores.get(name);
    if (!cache) { cache = new MemoryCache(); stores.set(name, cache); }
    return cache;
  };
  vm.runInNewContext(source.replaceAll('__SELECTED_RIDER_URL__', pin), {
    self: { location: { origin }, registration: { scope: origin + '/' }, clients: { claim: async () => undefined }, addEventListener: (name: string, handler: (event: WorkerEvent) => void) => handlers.set(name, handler) },
    caches: { open, has: async (name: string) => stores.has(name), keys: async () => [...stores.keys()], delete: async (name: string) => stores.delete(name) },
    fetch, URL, Response, Request,
  });
  const request = async (url: string) => {
    let response: Promise<Response> | undefined;
    const pending: Promise<unknown>[] = [];
    handlers.get('fetch')!({ request: new Request(url), respondWith: work => { response = work; }, waitUntil: work => pending.push(work) });
    return { response: response ? await response : undefined, pending };
  };
  const activate = async (): Promise<void> => {
    const pending: Promise<unknown>[] = [];
    handlers.get('activate')!({ request: new Request(origin), respondWith: () => undefined, waitUntil: work => { pending.push(work); } });
    await Promise.all(pending);
  };
  return { request, activate, fetch, open, stores };
}

describe('required selected rider service-worker cache', () => {
  it('loads the reachable source when Cache Storage access fails', async () => {
    const { request, fetch, open } = worker();
    (await open('rockhop-immutable')).beforeMatch = async () => { throw new Error('storage unavailable'); };
    const result = await request(selected);
    expect(await result.response!.text()).toBe(`bytes:${selected}`);
    expect(result.pending).toHaveLength(0);
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it('streams the first response while waitUntil completes its cache write, then boots offline without another fetch', async () => {
    const { request, fetch, open } = worker();
    const cache = await open('rockhop-immutable');
    let release!: () => void;
    cache.beforePut = () => new Promise<void>(resolve => { release = resolve; });
    const first = await request(selected);
    expect(await first.response!.text()).toBe(`bytes:${selected}`);
    expect(first.pending).toHaveLength(1);
    expect(cache.entries.has(selected)).toBe(false);
    release(); await Promise.all(first.pending);
    expect(cache.entries.has(selected)).toBe(true);
    fetch.mockImplementation(async () => { throw new Error('offline'); });
    const repeat = await request(selected);
    expect(await repeat.response!.text()).toBe(`bytes:${selected}`);
    expect(repeat.pending).toHaveLength(0);
    expect(fetch).toHaveBeenCalledTimes(1);
  });

  it('leaves unrelated, stale, query-modified and invalid-pin cross-origin requests untouched', async () => {
    const { request, fetch } = worker();
    for (const url of [stale, selected + '?different=1', 'https://other.invalid/model.glb', selected.replace(blobOrigin, 'https://other.public.blob.vercel-storage.com')]) {
      expect((await request(url)).response).toBeUndefined();
    }
    expect(fetch).not.toHaveBeenCalled();
    const invalid = worker('https://example.public.blob.vercel-storage.com/rider-remaster/not-a-hash/rider.glb');
    expect((await invalid.request(selected)).response).toBeUndefined();
    expect(invalid.fetch).not.toHaveBeenCalled();
  });

  it('does not cache an unsuccessful CORS response and permits an explicit retry', async () => {
    const { request, fetch, open } = worker();
    fetch.mockResolvedValueOnce(new Response('unavailable', { status: 503 }));
    const failed = await request(selected);
    expect(failed.response!.status).toBe(503);
    expect(failed.pending).toHaveLength(0);
    expect((await open('rockhop-immutable')).entries.size).toBe(0);
    const retry = await request(selected);
    await Promise.all(retry.pending);
    expect(retry.response!.ok).toBe(true);
    expect(fetch).toHaveBeenCalledTimes(2);
  });

  it.each([false, true])('prunes only old selected sources on the pinned host (manifest present: %s)', async (manifest) => {
    const { activate, open } = worker();
    const cache = await open('rockhop-immutable');
    const otherHost = stale.replace(blobOrigin, 'https://other.public.blob.vercel-storage.com');
    const unrelated = blobOrigin + '/other-file.glb';
    for (const url of [selected, stale, otherHost, unrelated]) await cache.put(url, new Response('cached'));
    if (manifest) await (await open('rockhop-shell-__BUILD_ID__')).put(origin + '/load-manifest.json', new Response(JSON.stringify({ items: [{ path: selected }] })));
    await activate();
    expect([...cache.entries.keys()]).toEqual([selected, otherHost, unrelated]);
  });
});
