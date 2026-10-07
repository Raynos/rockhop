import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import { privateEnginePlugin, selectedRiderAliases } from './private-engine-plugin.mjs';

const outfits = ['street-mustard', 'street-charcoal', 'street-openface', 'race-bluewhite', 'race-charcoalyellow'];
const modelSlots = outfits.flatMap(outfit => [`models/rider-${outfit}.glb`, `models/rider-${outfit}-lod.glb`]);
const sha = 'a'.repeat(64);
const metadata = {
  sourceSHA256: sha,
  selectedRiderSource: { sourceSHA256: sha, modelSlots, canonicalLogical: modelSlots[0] },
};

test('ten declared identical rider slots share one parsed document and its textures; bikes stay distinct', async () => {
  const source = fs.readFileSync(new URL('../../src/render/hero/gltf.ts', import.meta.url), 'utf8');
  const transformed = privateEnginePlugin(metadata).transform(source, '/src/render/hero/gltf.ts').code;
  const resolution = transformed.split('\n').find(line => line.includes('url = modelAssetUrl('));
  assert.ok(resolution);
  const resolve = new Function('url', 'modelAssetUrl', `${resolution}\nreturn url;`);
  const cache = new Map(), fetched = [];
  const load = logical => {
    const url = resolve(logical, name => `snapshots/${name}`);
    if (!cache.has(url)) {
      fetched.push(url);
      cache.set(url, Promise.resolve({ url, texture: { originalSource: true } }));
    }
    return cache.get(url);
  };
  const documents = await Promise.all(modelSlots.map(load));
  assert.equal(fetched.length, 1);
  assert.ok(documents.every(doc => doc === documents[0] && doc.texture === documents[0].texture));
  const bikeFull = await load('models/bike-rookie.glb');
  const bikeLod = await load('models/bike-rookie-lod.glb');
  assert.notEqual(bikeFull, bikeLod);
  assert.notEqual(bikeFull, documents[0]);
  assert.equal(fetched.length, 3);
  assert.equal(resolve('models/rider-unlisted.glb', name => name), 'models/rider-unlisted.glb');
  assert.ok(transformed.includes('          shrinkTextures(g.scene);'), 'Existing measured texture derivative policy remains');
});

test('private aliases require exact declared rider slots, a declared canonical slot and identical source SHA', () => {
  assert.deepEqual(selectedRiderAliases({}), {});
  assert.equal(Object.keys(selectedRiderAliases(metadata)).length, 10);
  for (const selectedRiderSource of [
    { ...metadata.selectedRiderSource, modelSlots: [...modelSlots, modelSlots[0]] },
    { ...metadata.selectedRiderSource, modelSlots: [...modelSlots, 'models/bike-rookie.glb'] },
    { ...metadata.selectedRiderSource, canonicalLogical: 'models/rider-unlisted.glb' },
    { ...metadata.selectedRiderSource, sourceSHA256: 'b'.repeat(64) },
  ]) assert.throws(() => selectedRiderAliases({ ...metadata, selectedRiderSource }), /Private rider:/);
  assert.throws(() => privateEnginePlugin(metadata).transform('              resolve(g);', '/src/render/hero/gltf.ts'), /logical model resolution changed/);
});
