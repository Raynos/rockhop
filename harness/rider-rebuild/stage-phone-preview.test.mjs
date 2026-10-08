import test from 'node:test';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { stagePhonePreview } from './stage-phone-preview.mjs';

test('stage the actual comparison outputs with final budget and private-file guards', async t => {
  const base = fs.mkdtempSync(path.join(os.tmpdir(), 'rockhop-phone-stage-'));
  t.after(() => fs.rmSync(base, { recursive: true, force: true }));
  const root = path.join(base, 'fixture-root'), build = path.join(root, 'build');
  const sha = data => crypto.createHash('sha256').update(data).digest('hex');
  const write = (relative, value) => {
    const file = path.join(root, relative); fs.mkdirSync(path.dirname(file), { recursive: true });
    fs.writeFileSync(file, typeof value === 'object' ? JSON.stringify(value) : value);
  };
  const ids = ['street-mustard', 'street-openface', 'race-bluewhite', 'street-charcoal', 'race-charcoalyellow'];
  const slots = ['models/rider-street-remastered.glb', 'models/rider-street-remastered-lod.glb'];
  const logicals = [...ids.flatMap(id => ['', '-lod'].map(s => `models/rider-${id}${s}.glb`)),
    ...['rookie', 'pro'].flatMap(id => ['', '-lod'].map(s => `models/bike-${id}${s}.glb`))];
  const models = logicals.map(logical => {
    const data = 'fixture:' + logical, url = logical.replace('models/', 'models/hash/');
    write('public/' + logical, data); write('build/' + url, data);
    return { logical, url, bytes: Buffer.byteLength(data), sha256: sha(data) };
  });
  const data = 'selected full asset', url = 'models/hash/selected.glb';
  write('build/' + url, data);
  const selected = { url, bytes: data.length, sha256: sha(data) };
  models.push(...slots.map(logical => ({ logical, ...selected })));
  const comparison = { id: 'street-remastered', label: 'Mustard · Remastered', sourceBytes: data.length, lodAliasesFull: true };
  write('build/rider-rebuild-inputs.json', { releaseBuild: false, comparison, modelSlots: slots,
    source: '/Users/private/source.glb', sourceSHA256: sha(data), selectedRiderSource: { canonicalLogical: slots[0],
      modelSlots: slots, texturePolicy: 'preserve-authored-images', sourceSHA256: sha(data) } });
  write('build/hero-review.json', { releaseBuild: false, models, mapping: Object.fromEntries(slots.map(slot => [slot, '/Users/private/source.glb'])) });
  write('build/model-catalog.json', { models, resources: [] });
  const review = 'export const native75 = true;';
  write('build/assets/review.js', review);
  const measurements = { releaseBuild: false, reviewChunk: 'assets/review.js', reviewChunkSHA256: sha(review),
    normalPlayerLimitGzipBytes: 717824, normalPlayerGzipBytes: 717824,
    measurement: 'Final emitted files; PWA worker cost reported separately.' };
  write('build/rider-comparison-js.json', measurements);
  write('build/index.html', '<!doctype html><title>Comparison fixture</title>');
  write('build/sw.js', 'const fixture=true;');
  write('build/version.json', { git: 'fixture' });
  write('build/.inputs/credentials.json', 'must not deploy');
  write('build/.private-build-driver.mts', 'must not deploy');
  write('build/unreferenced-receipt.json', 'must not deploy');
  for (const relative of ['audio/menu.mp3', 'audio/sfx/MODEL-LICENSE.txt', 'bench/b1-bot-3.json']) {
    write('public/' + relative, 'fixture'); write('build/' + relative, 'fixture');
  }
  write('build/audio/sfx/provenance.json', { local: '/Users/private/receipt.json' });
  const loads = { items: [...models.map(row => ({ path: './' + row.url, bytes: row.bytes, sha256: row.sha256 }))
    .filter((row, index, all) => all.findIndex(other => other.path === row.path) === index),
    { path: './assets/review.js', bytes: 1 }, { path: './assets/review.js', bytes: review.length },
    { path: './rider-comparison-js.json', bytes: fs.statSync(path.join(build, 'rider-comparison-js.json')).size }] };
  write('build/load-manifest.json', loads);
  write('.vercel/project.json', { projectId: 'prj_Fixture', orgId: 'team_Fixture', projectName: 'fixture', settings: { buildCommand: 'ignored' } });
  write('vercel.json', JSON.parse(fs.readFileSync(new URL('../../vercel.json', import.meta.url))));
  const out1 = path.join(base, 'stage01'), out2 = path.join(base, 'stage02');
  const rejected = (name, pattern) => assert.rejects(stagePhonePreview({ build, out: path.join(base, name), root }), pattern);

  await t.test('deterministic copies, single selected GLB, and retained original bytes', async () => {
    const first = await stagePhonePreview({ build, out: out1, root });
    assert.deepEqual(first, await stagePhonePreview({ build, out: out2, root }));
    assert.equal(first.files.filter(row => row.sha256 === selected.sha256).length, 1);
    assert.equal(first.originalHeroesVerified, 14);
    assert.equal(first.manifestByteDifferences.length, 1);
    for (const relative of ['.inputs/credentials.json', '.private-build-driver.mts', 'hero-review.json', 'rider-rebuild-inputs.json', 'unreferenced-receipt.json', 'audio/sfx/provenance.json']) {
      assert(!fs.existsSync(path.join(out1, '.vercel/output/static', relative)), relative + ' excluded');
    }
    assert(first.files.some(row => row.path === 'audio/menu.mp3'));
    assert(first.files.some(row => row.path === 'bench/b1-bot-3.json'));
  });
  await t.test('repository security/cache headers and preview linkage', () => {
    const config = JSON.parse(fs.readFileSync(path.join(out1, '.vercel/output/config.json')));
    const headers = target => Object.assign({}, ...config.routes.filter(row => row.src && new RegExp(row.src).test(target)).map(row => row.headers));
    assert.equal(config.version, 3);
    assert.equal(headers('/index.html')['Cache-Control'], 'no-store');
    assert.equal(headers('/assets/review.js')['Cache-Control'], 'public, max-age=31536000, immutable');
    assert.equal(headers('/models/hash/selected.glb')['Cross-Origin-Embedder-Policy'], 'require-corp');
    assert.equal(JSON.parse(fs.readFileSync(path.join(out1, '.vercel/output/builds.json'))).target, 'preview');
    assert.deepEqual(Object.keys(JSON.parse(fs.readFileSync(path.join(out1, '.vercel/project.json')))), ['projectId', 'orgId', 'projectName']);
  });
  await t.test('reject unfinalized measurements before writing output', async () => {
    const marker = measurements.measurement; delete measurements.measurement;
    write('build/rider-comparison-js.json', measurements);
    await rejected('reject-unfinalized', /measure final emitted files/);
    assert(!fs.existsSync(path.join(base, 'reject-unfinalized')));
    measurements.measurement = marker; write('build/rider-comparison-js.json', measurements);
  });
  await t.test('reject overbudget, raised cap, and nonfinite/negative measurements', async () => {
    for (const [index, value] of [717825, null, '717824', -1].entries()) {
      measurements.normalPlayerGzipBytes = value; write('build/rider-comparison-js.json', measurements);
      await rejected(`reject-budget-${index}`, /exceeds the unchanged budget/);
      assert(!fs.existsSync(path.join(base, `reject-budget-${index}`)));
    }
    measurements.normalPlayerGzipBytes = 717824; measurements.normalPlayerLimitGzipBytes++;
    write('build/rider-comparison-js.json', measurements); await rejected('reject-raised-cap', /budget must remain unchanged/);
    measurements.normalPlayerLimitGzipBytes = 717824; write('build/rider-comparison-js.json', measurements);
  });
  await t.test('reject reused output, traversal, and private paths', async () => {
    await assert.rejects(stagePhonePreview({ build, out: out1, root }), /fresh ignored/);
    for (const [index, unsafe] of ['../credentials.json', './assets/.private.json'].entries()) {
      loads.items.push({ path: unsafe, bytes: 1 }); write('build/load-manifest.json', loads);
      await rejected(`reject-path-${index}`, /unsafe/); loads.items.pop();
    }
    write('build/load-manifest.json', loads);
  });
  await t.test('reject selected GLB hash drift', async () => {
    write('build/' + url, 'tampered source!!!!');
    await rejected('reject-drift', /hash mismatch/); write('build/' + url, data);
  });
  await t.test('reject absolute local paths in emitted text', async () => {
    write('build/assets/local.js', 'const receipt = "/Users/private/receipt.json";');
    loads.items.push({ path: './assets/local.js', bytes: 1 }); write('build/load-manifest.json', loads);
    await rejected('reject-local-path', /Local machine path/); loads.items.pop(); write('build/load-manifest.json', loads);
  });
  await t.test('reject symlinked output', async () => {
    fs.symlinkSync(path.join(build, 'assets/review.js'), path.join(build, 'assets/link.js'));
    loads.items.push({ path: './assets/link.js', bytes: review.length }); write('build/load-manifest.json', loads);
    await rejected('reject-symlink', /Symlink/);
  });
});
