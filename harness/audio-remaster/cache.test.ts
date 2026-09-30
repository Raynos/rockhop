/** Execute the actual service-worker fetch handler; no browser or audio context is created. */
import fs from 'node:fs';
import vm from 'node:vm';
import { describe, expect, it, vi } from 'vitest';

const origin = 'https://rockhop.invalid';
const source = fs.readFileSync('src/pwa/sw.js', 'utf8');
type Key = Request | string;
const urlOf = (key: Key): string => typeof key === 'string' ? new URL(key, origin).href : key.url;

class MemoryCache {
  readonly entries = new Map<string, Response>();
  async match(key: Key): Promise<Response | undefined> { return this.entries.get(urlOf(key))?.clone(); }
  async put(key: Key, response: Response): Promise<void> { this.entries.set(urlOf(key), response.clone()); }
  async keys(): Promise<Request[]> { return [...this.entries.keys()].map(url => new Request(url)); }
  async delete(key: Key): Promise<boolean> { return this.entries.delete(urlOf(key)); }
}

interface FetchEvent { request: Request; respondWith(response: Promise<Response>): void }

function worker() {
  const handlers = new Map<string, (event: FetchEvent) => void>();
  const stores = new Map<string, MemoryCache>();
  const fetch = vi.fn(async (request: Request) => new Response(`bytes:${request.url}`, { status: 200 }));
  vm.runInNewContext(source, {
    self: { location: { origin }, addEventListener: (name: string, handler: (event: FetchEvent) => void) => handlers.set(name, handler) },
    caches: { open: async (name: string) => {
      let cache = stores.get(name);
      if (!cache) { cache = new MemoryCache(); stores.set(name, cache); }
      return cache;
    } },
    fetch, URL, Response, Request,
  });
  const request = async (pathname: string): Promise<Response> => {
    let response: Promise<Response> | undefined;
    handlers.get('fetch')!({ request: new Request(origin + pathname), respondWith: promise => { response = promise; } });
    if (!response) throw new Error('Service worker did not handle request');
    const result = await response;
    // The real handler writes/prunes asynchronously after returning the fetched response.
    for (let turn = 0; turn < 12; turn++) await Promise.resolve();
    return result;
  };
  return { request, fetch, stores };
}

describe('remastered audio service-worker cache', () => {
  it('serves MP3 music, SFX atlas and zone beds from the permanent cache with the network unavailable', async () => {
    const { request, fetch, stores } = worker();
    const files = ['/audio/menu-1234abcd.mp3', '/audio/sfx/reactions-123456abcdef.mp3', '/audio/sfx/bed-coast-abcdef123456.mp3'];
    for (const file of files) expect(await (await request(file)).text()).toBe(`bytes:${origin}${file}`);
    expect(stores.get('rockhop-audio')!.entries.size).toBe(3);
    expect(stores.has('rockhop-static-__ASSET_ID__')).toBe(false);
    fetch.mockImplementation(async () => { throw new Error('offline'); });
    for (const file of files) expect(await (await request(file)).text()).toBe(`bytes:${origin}${file}`);
    expect(fetch).toHaveBeenCalledTimes(3); // no radio wait or retry on repeat play
  });

  it('replaces old M4A/MP3 hashes only within the same music or SFX namespace', async () => {
    const { request, fetch, stores } = worker();
    await request('/audio/menu-11111111.m4a');
    await request('/audio/sfx/menu-111111111111.mp3');
    await request('/audio/menu-22222222.mp3');
    const cache = stores.get('rockhop-audio')!;
    expect([...cache.entries.keys()]).toEqual([origin + '/audio/sfx/menu-111111111111.mp3', origin + '/audio/menu-22222222.mp3']);
    await request('/audio/sfx/menu-222222222222.mp3');
    expect([...cache.entries.keys()]).toEqual([origin + '/audio/menu-22222222.mp3', origin + '/audio/sfx/menu-222222222222.mp3']);
    fetch.mockImplementation(async () => { throw new Error('offline'); });
    expect(await (await request('/audio/menu-22222222.mp3')).text()).toBe(`bytes:${origin}/audio/menu-22222222.mp3`);
    expect(await (await request('/audio/sfx/menu-222222222222.mp3')).text()).toBe(`bytes:${origin}/audio/sfx/menu-222222222222.mp3`);
  });

  it('keeps unhashed audio on the existing network-first static path', async () => {
    const { request, fetch, stores } = worker();
    await request('/audio/menu.mp3');
    await request('/audio/menu.mp3');
    expect(fetch).toHaveBeenCalledTimes(2);
    expect(stores.has('rockhop-audio')).toBe(false);
    expect(stores.get('rockhop-static-__ASSET_ID__')!.entries.size).toBe(1);
  });
});
