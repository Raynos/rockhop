import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import os from 'node:os';
import path from 'node:path';
import crypto from 'node:crypto';
import ts from 'typescript';
import { privateEnginePlugin, comparisonRider, comparisonModelMapping, comparisonSnapshotSource } from './private-engine-plugin.mjs';

const read = file => fs.readFileSync(file, 'utf8');
const original = ['street-mustard', 'street-openface', 'race-bluewhite', 'street-charcoal', 'race-charcoalyellow'];
const metadata = { comparison: true, releaseBuild: false, sourceSHA256: 'a'.repeat(64), selectedRiderSource: {
  modelSlots: [comparisonRider.full, comparisonRider.lod], canonicalLogical: comparisonRider.full,
  sourceSHA256: 'a'.repeat(64), texturePolicy: 'preserve-authored-images' } };
const plugin = () => privateEnginePlugin(metadata);
const transformed = (p, file) => p.transform(read(file), '/' + file).code;
const transpile = (code, module = ts.ModuleKind.ESNext) => ts.transpileModule(code, { compilerOptions: { module, target: ts.ScriptTarget.ES2020 } }).outputText;
const evaluate = code => import('data:text/javascript,' + encodeURIComponent(transpile(code)));

test('comparison appends a separately normalized sixth preset and keeps all originals', async () => {
  const p = plugin(), presets = await evaluate(transformed(p, 'src/core/riderPresets.ts'));
  assert.deepEqual(presets.RIDER_PRESETS.map(row => row.id), [...original, comparisonRider.id]);
  assert.equal(presets.riderPreset(comparisonRider.id).label, 'Mustard · Remastered');
  assert.equal(presets.normalizeRiderOutfit(comparisonRider.id), comparisonRider.id);
  assert.equal(presets.normalizeRiderFamily(comparisonRider.id), 'street');
  assert.equal(presets.DEFAULT_RIDER_OUTFIT, 'street-mustard');
  original.forEach(id => assert.equal(presets.normalizeRiderOutfit(id), id));
  let urls = transformed(p, 'src/render/hero/urls.ts');
  urls = urls.replace("import { MODEL_ASSETS, MODEL_RESOURCES } from './models.generated';", 'const MODEL_ASSETS = {}, MODEL_RESOURCES = {};');
  const api = await evaluate(urls);
  original.forEach(id => assert.equal(api.riderUrl(id), `models/rider-${id}.glb`));
  assert.deepEqual(api.heroFiles(comparisonRider.id, 'pro'), ['models/bike-pro.glb', 'models/bike-pro-lod.glb', comparisonRider.full, comparisonRider.lod]);
  assert.deepEqual(Object.keys(api.HERO_FILES_BY_OUTFIT_CLASS).sort(), [...original].sort(), 'Eager boot inventory remains the original five');
});

test('comparison wrapper uses legacy driver for originals and selected driver only for tagged documents', async () => {
  const p = plugin();
  let code = p.transform('export class GltfRider { constructor(gltf, lib) { this.source = gltf; this.lib = lib; } }', '/src/render/hero/gltfRider.ts').code;
  code = code.replace("import { privateSelectedRiderClass } from './gltf';", 'class Selected { constructor(gltf) { this.source = gltf; this.native75 = true; } } const privateSelectedRiderClass = Selected;');
  const { GltfRider } = await evaluate(code), oldDoc = { scene: { userData: {} } }, newDoc = { scene: { userData: { privateSelectedRider: true } } };
  const old = new GltfRider(oldDoc, {}), selected = new GltfRider(newDoc, {});
  assert.equal(old.source, oldDoc); assert.equal(old.native75, undefined);
  assert.equal(selected.source, newDoc); assert.equal(selected.native75, true);
  assert(old instanceof GltfRider); assert(selected instanceof GltfRider);
});

test('new source is requested only when selected and omitted from eager offline pack', () => {
  const p = plugin(), renderer = transformed(p, 'src/render/index.ts');
  const expression = renderer.slice(renderer.indexOf('    const inventory ='), renderer.indexOf('    this.heroLoading++;'));
  const old = ['models/rider-street-mustard.glb', 'models/bike-rookie.glb'];
  const heroPair = (_outfit, bike, detail) => [`models/bike-${bike}${detail === 'lod' ? '-lod' : ''}.glb`, detail === 'lod' ? comparisonRider.lod : comparisonRider.full];
  const state = { riderOutfit: original[0], bikeClass: 'rookie', heroDocs: new Map(), models: { riderModel: 'gltf', bikeModel: 'gltf' } };
  // The original method's filtering refers to its already captured model choice.
  const run = Function('HERO_FILE_SET', 'heroPair', 'want', expression + ';return files;');
  assert.deepEqual(run.call(state, old, heroPair, state.models), old);
  state.riderOutfit = comparisonRider.id;
  const requested = run.call(state, old, heroPair, state.models);
  assert(requested.includes(comparisonRider.full)); assert(requested.includes(comparisonRider.lod));
  assert(!requested.includes('models/rider-street-charcoal.glb'));
  assert.match(transformed(p, 'src/boot/offline-pack.ts'), /logical === 'models\/rider-street-remastered\.glb'.*continue/);
  assert.match(transformed(p, 'src/render/hero/gltf.ts'), /if \(g.scene.userData.privateSelectedRider\).*loadPrivateSelectedRider/);
  assert.match(transformed(p, 'src/render/hero/lod.ts'), /if \(!root.userData.privateSelectedRider\) mergeSkinnedByMaterial/);
});

test('private snapshots keep original bytes and alias full/LOD to one emitted URL', () => {
  const directory = fs.mkdtempSync(path.join(os.tmpdir(), 'rockhop-comparison-'));
  try {
    const root = path.join(directory, 'repo'), out = path.join(directory, 'out');
    fs.mkdirSync(path.join(root, 'public/models'), { recursive: true });
    for (const id of original) for (const detail of ['', '-lod']) fs.writeFileSync(path.join(root, `public/models/rider-${id}${detail}.glb`), `${id}${detail}`);
    const source = path.join(directory, 'selected.glb'); fs.writeFileSync(source, 'exact selected source');
    const recipe = comparisonSnapshotSource(read('harness/hero-remaster/build.mts'));
    const section = recipe.slice(recipe.indexOf('const sourceRoot ='), recipe.indexOf('const changed ='));
    const readModelCatalog = input => fs.readdirSync(path.join(input, 'models')).map(name => {
      const bytes = fs.readFileSync(path.join(input, 'models', name)), sha256 = crypto.createHash('sha256').update(bytes).digest('hex');
      return { logical: `models/${name}`, bytes, sha256, url: `models/${name}-${sha256}` };
    });
    const js = transpile(section + ';export {assets,values};', ts.ModuleKind.CommonJS);
    const exports = {}, module = { exports };
    Function('fs', 'path', 'root', 'out', 'mapping', 'readModelCatalog', 'module', 'exports', js)(fs, path, root, out, comparisonModelMapping(source), readModelCatalog, module, exports);
    const values = module.exports.values;
    for (const id of original) for (const detail of ['', '-lod']) assert.equal(fs.readFileSync(path.join(out, `.inputs/models/rider-${id}${detail}.glb`), 'utf8'), id + detail);
    assert.deepEqual(Object.keys(comparisonModelMapping(source)), [comparisonRider.full, comparisonRider.lod]);
    assert.equal(values[comparisonRider.full].url, values[comparisonRider.lod].url);
    assert.equal(values[comparisonRider.full].sha256, values[comparisonRider.lod].sha256);
    assert.equal(fs.statSync(path.join(out, '.inputs', comparisonRider.full)).ino, fs.statSync(path.join(out, '.inputs', comparisonRider.lod)).ino);
    assert.equal(new Set(module.exports.assets.map(a => a.url)).size, original.length * 2 + 1);
  } finally { fs.rmSync(directory, { recursive: true, force: true }); }
});

test('comparison rejects old-slot aliases and detects source anchor drift', () => {
  assert.throws(() => privateEnginePlugin({ ...metadata, selectedRiderSource: { ...metadata.selectedRiderSource, modelSlots: ['models/rider-street-mustard.glb'], canonicalLogical: 'models/rider-street-mustard.glb' } }), /only the new/);
  assert.throws(() => comparisonSnapshotSource('changed recipe'), /source changed/);
  assert.throws(() => plugin().transform('changed presets', '/src/core/riderPresets.ts'), /source changed/);
});

test('all scoped actual sources parse and selected alias has one exact load receipt', async () => {
  const p = plugin();
  const nativeFiles = ['private-rider.mjs', 'new-humanoid-contract.mjs', 'anthropometric-inverse.mjs'].map(name => path.resolve('harness/rider-rebuild', name));
  await p.buildStart.call({ resolve: async id => ({ id }) });
  for (const file of ['src/core/riderPresets.ts', 'src/render/hero/urls.ts', 'src/ui/garage.ts', 'src/render/index.ts', 'src/boot/asset-totals.ts', 'src/boot/offline-pack.ts',
    'src/render/hero/gltfRider.ts', 'src/render/hero/gltf.ts', 'src/render/hero/lod.ts']) {
    const code = transformed(p, file);
    const result = ts.transpileModule(code, { compilerOptions: { module: ts.ModuleKind.ESNext, target: ts.ScriptTarget.ES2020 }, reportDiagnostics: true });
    assert.deepEqual(result.diagnostics?.filter(row => row.category === ts.DiagnosticCategory.Error), [], file);
  }
  p.buildEnd();
  const models = [comparisonRider.full, comparisonRider.lod].map(logical => ({ logical, url: 'models/exact-selected.glb', sha256: metadata.sourceSHA256, bytes: 3 }));
  const bundle = {
    'model-catalog.json': { type: 'asset', source: JSON.stringify({ models }) },
    'load-manifest.json': { type: 'asset', source: JSON.stringify({ items: [{ path: './model-catalog.json', bytes: 0, gz: 0 }] }) },
    'models/exact-selected.glb': { type: 'asset', source: Buffer.from([1, 2, 3]) },
    'assets/rider-review-test.js': { type: 'chunk', name: 'rider-review', fileName: 'assets/rider-review-test.js', code: 'export const native75 = true;', isEntry: false,
      modules: Object.fromEntries(nativeFiles.map(file => [file, {}])), imports: [] },
    'assets/index-test.js': { type: 'chunk', name: 'index', fileName: 'assets/index-test.js', code: 'export const original = true;', isEntry: true, modules: {}, imports: [] },
  };
  p.generateBundle.handler.call({ emitFile: asset => { bundle[asset.fileName] = asset; } }, null, bundle);
  const loads = JSON.parse(bundle['load-manifest.json'].source).items;
  assert.equal(loads.filter(row => row.path === './models/exact-selected.glb').length, 1);
  assert.equal(loads.find(row => row.path === './models/exact-selected.glb').bytes, 3);
  assert.equal(loads[0].bytes, Buffer.byteLength(bundle['model-catalog.json'].source));
  assert.equal(JSON.parse(bundle['model-catalog.json'].source).models.length, 2);
  const measurement = JSON.parse(bundle['rider-comparison-js.json'].source);
  assert.equal(measurement.releaseBuild, false);
  assert.equal(measurement.normalPlayerLimitGzipBytes, 701 * 1024);
  assert.equal(measurement.comparisonBudgetGzipBytes, measurement.normalPlayerGzipBytes + measurement.selectedReviewGzipBytes);
  assert.equal(measurement.allJavaScriptGzipBytes, measurement.comparisonBudgetGzipBytes + measurement.otherExcludedGzipBytes);
  bundle['assets/index-test.js'].imports.push('assets/rider-review-test.js');
  assert.throws(() => p.generateBundle.handler.call({ emitFile() {} }, null, bundle), /static player dependency/);
});

test('only comparison isolates exact native modules; vendor closures and normal budget policy remain intact', async () => {
  const normal = privateEnginePlugin({ ...metadata, comparison: false }), options = { manualChunks: { three: ['three'], 'sentry-errors': ['@sentry/browser'] } };
  await normal.buildStart.call({ resolve() { throw Error('normal build must not resolve private chunks'); } });
  assert.equal(normal.outputOptions(options), null);
  const p = plugin(); await p.buildStart.call({ resolve: async id => ({ id }) });
  const files = ['private-rider.mjs', 'new-humanoid-contract.mjs', 'anthropometric-inverse.mjs'].map(name => path.resolve('harness/rider-rebuild', name));
  const graph = { three: ['three-core'], 'three-core': [], '@sentry/browser': ['sentry-core'], 'sentry-core': [], 'shared-game': [] };
  files.forEach(file => { graph[file] = ['shared-game', 'three']; });
  const output = p.outputOptions.call({ getModuleInfo: id => graph[id] ? { importedIds: graph[id] } : null }, options);
  assert.equal(output.onlyExplicitManualChunks, true);
  files.forEach(file => assert.equal(output.manualChunks(file), 'rider-review'));
  assert.equal(output.manualChunks('shared-game'), undefined);
  assert.equal(output.manualChunks('three-core'), 'three');
  assert.equal(output.manualChunks('sentry-core'), 'sentry-errors');
  assert.deepEqual(options.manualChunks, { three: ['three'], 'sentry-errors': ['@sentry/browser'] });
  assert.match(read('vite.config.ts'), /const BUNDLE_BUDGET_GZ_BYTES = 701 \* 1024/);
  assert.throws(() => privateEnginePlugin({ ...metadata, releaseBuild: true }), /releaseBuild false/);
});
