// @vitest-environment jsdom
/**
 * The DOWNLOAD invariant across the ask-59 tier split: what the boot FETCHES and what the loader PROMISES
 * are the same bytes. The list is built at runtime from the shipped manifest; the number is summed by the
 * build into `plan.generated.ts`. Nothing holds them together except `packMembership` — so this test maps
 * every URL in the list back to its row in the byte table and checks the sum.
 *
 * jsdom is DPR 1 at 1024 px, so this is the `1x` device.
 */
import fs from 'node:fs';
import path from 'node:path';
import { describe, expect, it } from 'vitest';
import { offlinePackUrls } from './offline-pack';
import { OFFLINE_PACK_BYTES, PUBLIC_BYTES } from './plan.generated';
import { ArtManifest } from '../ui/art';
import { MODEL_ASSETS, MODEL_RESOURCES } from '../render/hero/models.generated';
import { HERO_FILE_SET } from './asset-totals';

const raw = JSON.parse(fs.readFileSync(path.join(process.cwd(), 'public/art/manifest.json'), 'utf8')) as { assets: { id: string; path: string }[] };
const art = ArtManifest.from(raw);
const urls = offlinePackUrls(art.all());
const table = PUBLIC_BYTES as Readonly<Record<string, number>>;

/** A pack URL → its key in the build's byte table (the `?v=` the manifest adds is not part of the key). */
function tableKey(url: string): string {
  const logical = Object.entries({ ...MODEL_ASSETS, ...MODEL_RESOURCES }).find(([, a]) => a.url === url)?.[0];
  if (logical) return logical;
  const clean = url.split('?')[0]!;
  const e = art.all().find((a) => a.src === url);
  return `art:${e?.id ?? clean}`;
}

describe('the offline pack (ask 59: one tier, no link-preview card)', () => {
  it('warms every authored course model/map once without duplicating hero downloads', () => {
    const heroes = new Set<string>(HERO_FILE_SET);
    const picked = new Map(urls);
    for (const [logical, asset] of Object.entries({ ...MODEL_ASSETS, ...MODEL_RESOURCES })) {
      if (heroes.has(logical)) expect(picked.has(asset.url)).toBe(false);
      else expect(picked.get(asset.url), logical).toBe(asset.bytes);
    }
    expect(picked.size).toBe(urls.length);
  });

  it('fetches exactly the bytes the DOWNLOAD denominator declares for this device', () => {
    const summed = urls.reduce((n, [u]) => n + (table[tableKey(u)] ?? 0), 0);
    for (const [u] of urls) expect(table[tableKey(u)], `${u} is fetched but not in the byte table`).toBeGreaterThan(0);
    expect(summed).toBe(OFFLINE_PACK_BYTES['1x']);
  });

  it('keeps retired Free Ride thumbnails in the source record but out of the shipped pack', () => {
    const full = JSON.parse(fs.readFileSync(path.join(process.cwd(), 'assets/art/manifest.json'), 'utf8')) as { assets: { id: string }[] };
    const runtimeIds = new Set(raw.assets.map((entry) => entry.id));
    const fullIds = new Set(full.assets.map((entry) => entry.id));
    for (const id of ['p-coast', 'p-alpine', 'p-quarry', 'p-snowline']) {
      expect(fullIds.has(`thumb-${id}`)).toBe(true);
      expect(runtimeIds.has(`thumb-${id}`)).toBe(false);
      expect(table[`art:thumb-${id}`]).toBeUndefined();
      expect(urls.some(([url]) => url.includes(`/thumbs/${id}.webp`))).toBe(false);
    }
    expect(raw.assets.filter((entry) => entry.id.startsWith('thumb-'))).toHaveLength(12);
  });

  it('does not download retired painted map plates', () => {
    expect(urls.some(([url]) => url.startsWith('art/worldmap/'))).toBe(false);
  });

  // A variant with no sibling would be fetched by half the devices and drawn by all of them: offline, the
  // other half would have a tinted gradient where the picture belongs. The pack must ship pairs.
  it('ships every resolution variant as a pair', () => {
    const pairs = new Map<string, Set<string>>();
    for (const e of art.all()) {
      if (!e.variant) continue;
      const key = `${e.kind}/${e.biome ?? ''}/${e.bike ?? ''}/${e.medal ?? ''}`;
      const got = pairs.get(key) ?? new Set<string>();
      got.add(e.variant);
      pairs.set(key, got);
    }
    expect(pairs.size).toBeGreaterThan(0);
    for (const [key, got] of pairs) expect([...got].sort(), `${key} ships only ${[...got].join(' + ')}`).toEqual(['1x', '2x']);
  });

  it('takes one variant of every pair and leaves og.jpg on the server', () => {
    const picked = urls.map(([u]) => u);
    expect(picked.some((u) => u.includes('og.jpg'))).toBe(false); // ask 59 item 5: link previews only
    expect(picked.some((u) => u.includes('keyart-harbour-960'))).toBe(true);
    expect(picked.some((u) => u.includes('keyart-harbour-1920'))).toBe(false);
    expect(picked.some((u) => u.includes('medal-gold.png'))).toBe(true);
    expect(picked.some((u) => u.includes('medal-gold-512'))).toBe(false);
    expect(picked.some((u) => u.includes('bike-rookie-768'))).toBe(true);
    expect(picked.some((u) => u.includes('bike-rookie-1536'))).toBe(false);
  });
});
