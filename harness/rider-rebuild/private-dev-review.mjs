/** Actual Vite source-mode review. Production build/release gates remain separate. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { pipeline } from 'node:stream/promises';
import { pathToFileURL } from 'node:url';
import { createServer } from 'vite';
import { register } from 'tsx/esm/api';
import { privateEnginePlugin } from './private-engine-plugin.mjs';

const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
async function hashFile(filename) {
  const hash = crypto.createHash('sha256');
  for await (const chunk of fs.createReadStream(filename)) hash.update(chunk);
  return hash.digest('hex');
}
const identity = stat => [stat.dev, stat.ino, stat.size, stat.mtimeMs, stat.ctimeMs];

/** This transformed source adds an addon specifier absent from the normal scan. */
export function includePrivateRiderDependency(config) {
  config.optimizeDeps ??= {};
  config.optimizeDeps.include = [...new Set([...(config.optimizeDeps.include ?? []), 'three/addons/utils/SkeletonUtils.js'])];
}

export function observePrivateReloads(hot, events) {
  const send = hot.send;
  hot.send = function (payload, ...args) {
    if (payload?.type === 'full-reload') {
      if (events.fullReloads.length < 64) events.fullReloads.push({ epochMs: Date.now(),
        monotonicMs: performance.now(), path: String(payload.path ?? '').slice(0, 2048) });
      else events.dropped++;
    }
    return send.call(this, payload, ...args);
  };
}

/** Explicit unaccepted source diagnostics; none enters comparison. */
export function sourceDiagnosticKind(metadata, clip, allowFailedDiagnostic) {
  assert(allowFailedDiagnostic, 'Unaccepted source requires --allow-failed-diagnostic');
  assert.equal(metadata.accepted, false);
  if (metadata.qualificationState === 'UNACCEPTED_NATIVE_ACTION_LIBRARY') {
    const library = metadata.nativeAuthoringMotion;
    assert.equal(library?.accepted, false);
    assert.equal(library.kind, 'native-control-action-library');
    assert.deepEqual(library.actions.map(action => action.name), ['RiderIdle', 'RiderWalk', 'RiderJog', 'RiderTurn90', 'RiderJumpLand', 'RiderRangeOfMotion']);
    assert(library.actions.some(action => action.name === clip), 'Requested native action is declared');
    const action = metadata.genericActions?.[clip];
    assert(action && action.leadInSeconds === 2);
    assert.equal(action.playback, clip === 'RiderIdle' ? 'LOOP' : 'ONCE');
    assert.deepEqual(library.presentation.positionBike, [-0.6, -0.34, 0.65]);
    assert.equal(metadata.corrective, undefined, 'Native action library cannot reuse the failed corrective');
    return 'native-authoring-motion11';
  }
  assert.equal(metadata.previewClip, clip); assert.equal(metadata.diagnosticMotion?.previewClip, clip);
  assert.equal(metadata.diagnosticMotion?.accepted, false);
  if (clip === 'Anatomical09VolumeRestKey') {
    assert.equal(metadata.qualificationState, 'UNACCEPTED_POSED_VOLUME');
    assert.equal(metadata.diagnosticMotion.status, 'UNACCEPTED_POSED_VOLUME');
    assert.equal(metadata.diagnosticMotion.kind, 'native-posed-volume');
    assert.equal(metadata.weightDerivative?.kind, 'native-regional-weight-only');
    assert.equal(metadata.shapeDerivative?.kind, 'native-relative-shape-key');
    assert.equal(metadata.shapeDerivative.accepted, false);
    assert.equal(metadata.shapeDerivative.name, 'A09_SeatedVolume');
    assert.equal(metadata.corrective, undefined, 'Native volume cannot reuse the failed corrective');
    return 'native-posed-volume';
  }
  if (clip === 'Anatomical09WeightRestKey') {
    assert.equal(metadata.qualificationState, 'UNACCEPTED_WEIGHT_INTERVENTION');
    assert.equal(metadata.diagnosticMotion.status, 'UNACCEPTED_WEIGHT_INTERVENTION');
    assert.equal(metadata.diagnosticMotion.kind, 'native-weight-only');
    assert.equal(metadata.weightDerivative?.kind, 'native-regional-weight-only');
    assert.equal(metadata.corrective, undefined, 'Weight-only source cannot reuse a corrective');
    return 'native-weight-only';
  }
  assert.equal(clip, 'DiagnosticRestKey', 'Unknown source diagnostic clip');
  assert.equal(metadata.qualificationState, 'FAILED_CORRECTIVE_GATES');
  assert.equal(metadata.diagnosticMotion.status, 'FAILED_CORRECTIVE_GATES');
  assert(metadata.corrective, 'Corrective diagnostic requires its declared activation');
  return 'failed-corrective';
}

export async function createPrivateDevReview({ source, contractPath, allowFailedDiagnostic = false, comparison = false, clip }) {
  assert(!comparison, 'Source-mode diagnostic cannot enter comparison');
  const root = process.cwd(); source = path.resolve(source); contractPath = path.resolve(contractPath);
  const contractBytes = fs.readFileSync(contractPath), metadata = JSON.parse(contractBytes);
  const failed = typeof metadata.qualificationState === 'string' && metadata.qualificationState.startsWith('FAILED');
  const diagnosticKind = sourceDiagnosticKind(metadata, clip, allowFailedDiagnostic);
  if (metadata.weightDerivative) {
    for (const name of ['nativeReceipt', 'authoredRows']) {
      const pin = metadata.weightDerivative.sourcePins?.[name];
      assert(pin && typeof pin.path === 'string' && /^[a-f0-9]{64}$/.test(pin.sha256), `Declare weight source ${name}`);
      assert.equal(await hashFile(path.resolve(root, pin.path)), pin.sha256, `Weight source changed: ${name}`);
    }
  }
  if (metadata.shapeDerivative) {
    for (const name of ['native', 'nativeReceipt', 'shapeKey', 'posedSurfaces', 'weightRider', 'weightContract', 'weightReceipt']) {
      const pin = metadata.shapeDerivative.sourcePins?.[name];
      assert(pin && typeof pin.path === 'string' && /^[a-f0-9]{64}$/.test(pin.sha256), `Declare volume source ${name}`);
      assert.equal(await hashFile(path.resolve(root, pin.path)), pin.sha256, `Volume source changed: ${name}`);
    }
  }
  if (diagnosticKind === 'native-authoring-motion11') {
    const library = metadata.nativeAuthoringMotion;
    for (const name of ['nativeReceipt', 'controlNative', 'bakedNative', 'rigGLB', 'nativeMatrices', 'selectedRider', 'selectedContract']) {
      const pin = library.sourcePins?.[name];
      assert(pin && typeof pin.path === 'string' && /^[a-f0-9]{64}$/.test(pin.sha256), `Declare native action source ${name}`);
      assert.equal(await hashFile(path.resolve(root, pin.path)), pin.sha256, `Native action source changed: ${name}`);
    }
    const receipt = JSON.parse(fs.readFileSync(path.resolve(root, library.sourcePins.nativeReceipt.path)));
    assert.equal(receipt.status, 'NATIVE_CONTROL_ACTION_PACKAGE_UNACCEPTED');
    assert.deepEqual(library.actions, receipt.actions, 'All six actual native action records remain exact');
    for (const name of ['controlNative', 'bakedNative', 'rigGLB']) assert.deepEqual(library.sourcePins[name], receipt[name]);
  }
  const sourceStat = fs.statSync(source), sourceSHA256 = await hashFile(source);
  assert.deepEqual(identity(fs.statSync(source)), identity(sourceStat), 'Selected source changed while hashing');
  assert.equal(metadata.glbSHA256, sourceSHA256);
  const nativeLibrary = diagnosticKind === 'native-authoring-motion11';
  let author, authorPin, authorPath, authorRecipe, authorCode;
  if (!nativeLibrary) {
    assert.equal(metadata.diagnosticMotion.outputSHA256, sourceSHA256);
    authorPin = metadata.diagnosticMotion.sourcePins.author;
    authorPath = path.resolve(root, authorPin.path);
    assert.equal(await hashFile(authorPath), authorPin.sha256, 'Saved author receipt changed');
    author = JSON.parse(fs.readFileSync(authorPath));
    assert.deepEqual(author, metadata.diagnosticMotion.authorReceipt, 'Diagnostic carries the exact saved author pose');
    assert.equal(author.bike.path, 'public/models/bike-rookie.glb');
    authorRecipe = path.join(root, 'assets/blender/rider-rebuild/selected-seated-author04/author.mjs');
    authorCode = fs.readFileSync(authorRecipe, 'utf8');
    assert(authorCode.includes("const bikeFrame = new THREE.Group(); bikeFrame.name = 'actual-bike-local-frame';"));
    assert(authorCode.includes('rider.attach({ frame: bikeFrame }); rider.setStage(true); rider.setStageTime(0);'));
    assert(!authorCode.includes('garagePositionBike'), 'Re-audit author-origin placement if author source adds an offset');
  }
  const native = relative => import(pathToFileURL(path.join(root, relative)).href);
  const unregister = register(); let modules;
  try { modules = await Promise.all([
    native('src/boot/model-catalog.ts'), native('src/boot/asset-totals.ts'), native('vite.config.ts'),
  ]); } finally { await unregister(); }
  const [{ readModelCatalog, readModelResources }, { declaredBootTotals }, { buildInline }] = modules;
  const originals = readModelCatalog(path.join(root, 'public'));
  const resources = readModelResources(path.join(root, 'public')).map(({ logical, url, bytes, sha256 }) => ({ logical, url, bytes: bytes.length, sha256 }));
  const slots = originals.filter(asset => /^models\/rider[a-z0-9-]*\.glb$/.test(asset.logical)).map(asset => asset.logical);
  const canonicalLogical = 'models/rider-street-mustard.glb'; assert(slots.includes(canonicalLogical));
  const selectedURL = `models/private-selected/${sourceSHA256}/rider-${sourceSHA256}.glb`;
  const models = originals.map(({ logical, url, bytes, sha256 }) => slots.includes(logical)
    ? { logical, url: selectedURL, bytes: sourceStat.size, sha256: sourceSHA256 }
    : { logical, url, bytes: bytes.length, sha256 });
  if (author) assert.equal(models.find(asset => asset.logical === author.bike.path.slice(7))?.sha256, author.bike.sha256);
  metadata.sourceSHA256 = sourceSHA256; metadata.metadataSHA256 = sha(contractBytes);
  metadata.selectedRiderSource = { modelSlots: slots, canonicalLogical, sourceSHA256, texturePolicy: 'preserve-authored-images' };
  const positionBike = nativeLibrary ? metadata.nativeAuthoringMotion.presentation.positionBike : [0, 0, 0];
  metadata.driver = { ...metadata.driver, garagePositionBike: positionBike };
  if (nativeLibrary) metadata.previewClip = clip;
  metadata.releaseBuild = false;
  const placement = nativeLibrary ? { clip, positionBike, presentation: metadata.nativeAuthoringMotion.presentation,
    why: 'Generic native action inspection beside the actual bike; not normal Garage seated riding.' } :
    { clip, positionBike: [0, 0, 0], authorRecipe, authorRecipeSHA256: sha(authorCode),
    authorReceipt: { path: authorPath, sha256: authorPin.sha256 }, frameOriginFile: author.frameOriginFile,
    why: 'Author04 saved local75 TRS under identity actual-bike-local-frame. Bike-file attach_frame_origin is already subtracted from saddle geometry; the standing-clip presentation offset would translate this saved seated pose away from its bike.' };
  const pins = await Promise.all(['vite.config.ts', 'harness/rider-rebuild/private-engine-plugin.mjs', 'harness/rider-rebuild/private-rider.mjs',
    'harness/rider-rebuild/new-humanoid-contract.mjs', 'harness/rider-rebuild/anthropometric-inverse.mjs',
    'assets/blender/rider-rebuild/selected-seated-corrective06/apply-morph02.mjs', 'harness/rider-rebuild/private-dev-review.mjs']
    .map(async relative => ({ path: relative, sha256: await hashFile(path.join(root, relative)) })));
  const catalog = { models, resources, privateRiderMetadata: metadata };
  const catalogBytes = Buffer.from(JSON.stringify(catalog));
  const values = rows => Object.fromEntries(rows.map(({ logical, ...row }) => [logical, row]));
  let planSource, totals;
  const serverEvents = { clock: 'Node Date.now epoch milliseconds and performance.now monotonic milliseconds', fullReloads: [], dropped: 0 };
  const plugin = {
    name: 'rockhop:private-source-review',
    config: includePrivateRiderDependency,
    configResolved() {
      const originalPlan = fs.readFileSync(path.join(root, 'src/boot/plan.generated.ts'), 'utf8');
      const publicMatch = originalPlan.match(/export const PUBLIC_BYTES = (\{[\s\S]*?\}) as const;/);
      const packMatch = originalPlan.match(/export const OFFLINE_PACK_BYTES = \{ '1x': (\d+), '2x': (\d+) \};/);
      assert(publicMatch && packMatch, 'Actual generated boot table format changed');
      const table = Object.fromEntries([...publicMatch[1].matchAll(/"([^"]+)": (\d+)/g)].map(([, key, bytes]) => [key, Number(bytes)]));
      for (const row of models) table[row.logical] = row.bytes;
      const pack = { '1x': Number(packMatch[1]), '2x': Number(packMatch[2]) };
      totals = declaredBootTotals(key => table[key], pack);
      planSource = originalPlan.replace(publicMatch[0], `export const PUBLIC_BYTES = ${JSON.stringify(table)} as const;`);
    },
    load(id) {
      const file = id.split('?')[0];
      if (file === path.join(root, 'src/render/hero/models.generated.ts')) return `export const MODEL_ASSETS = ${JSON.stringify(values(models))} as const;\nexport const MODEL_RESOURCES = ${JSON.stringify(values(resources))} as const;`;
      if (file === path.join(root, 'src/boot/plan.generated.ts')) return planSource;
      return null;
    },
    transformIndexHtml: { order: 'post', async handler(html) {
      const scripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].filter(match => /\.__boot\s*=/.test(match[1]));
      assert.equal(scripts.length, 1, 'Actual inline boot loader must be inserted before source review totals');
      const buildId = JSON.parse(server.config.define.__BUILD_ID__);
      const inline = await buildInline(root, [], totals, false, buildId);
      return html.replace(scripts[0][0], () => `<script>${inline}</script>`);
    } },
    configureServer(vite) {
      // Observe the actual client hot channel without suppressing or changing
      // its messages. Both optimizer reloads and watcher reloads use this path.
      observePrivateReloads(vite.environments.client.hot, serverEvents);
      vite.middlewares.use((req, res, next) => {
        const pathname = new URL(req.url ?? '/', 'http://localhost').pathname;
        if (pathname === '/model-catalog.json') {
          res.setHeader('Content-Type', 'application/json'); res.setHeader('Content-Length', catalogBytes.length);
          res.setHeader('Cache-Control', 'no-store'); res.end(req.method === 'HEAD' ? undefined : catalogBytes); return;
        }
        if (pathname !== '/' + selectedURL) return next();
        if (!['GET', 'HEAD'].includes(req.method)) { res.statusCode = 405; res.end(); return; }
        let fd;
        try {
          fd = fs.openSync(source, 'r');
          assert.deepEqual(identity(fs.fstatSync(fd)), identity(sourceStat), 'Selected immutable source changed');
          res.setHeader('Content-Type', 'model/gltf-binary'); res.setHeader('Content-Length', sourceStat.size);
          res.setHeader('Cache-Control', 'public, max-age=31536000, immutable');
          if (req.method === 'HEAD') { fs.closeSync(fd); res.end(); return; }
          const stream = fs.createReadStream(source, { fd, autoClose: true }); fd = undefined;
          void pipeline(stream, res).catch(error => { if (!res.destroyed) res.destroy(error); });
        } catch (error) {
          if (fd !== undefined) fs.closeSync(fd);
          res.statusCode = 409; res.end(String(error));
        }
      });
    },
  };
  const server = await createServer({ configFile: path.join(root, 'vite.config.ts'), root,
    plugins: [plugin, privateEnginePlugin(metadata)], server: { host: '127.0.0.1', port: 0, open: false }, logLevel: 'warn' });
  try { await server.listen(); } catch (error) { await server.close(); throw error; }
  return { server, catalog, receipt: { mode: 'actual-vite-development-source', releaseBuild: false, failedDiagnostic: failed, diagnosticKind,
    source: { path: source, bytes: sourceStat.size, sha256: sourceSHA256, url: selectedURL },
    contract: { path: contractPath, sha256: sha(contractBytes) }, runtimeMetadataSHA256: sha(JSON.stringify(metadata)),
    runtime: { qualificationState: metadata.qualificationState, previewClip: metadata.previewClip,
      driver: metadata.driver, corrective: metadata.corrective, weightDerivative: metadata.weightDerivative, shapeDerivative: metadata.shapeDerivative, nativeAuthoringMotion: metadata.nativeAuthoringMotion, genericActions: metadata.genericActions, selectedRiderSource: metadata.selectedRiderSource },
    catalogSHA256: sha(catalogBytes), placement, pins, optimizeDepsInclude: server.config.optimizeDeps.include, serverEvents,
    performanceMeaning: 'Actual rendered-frame measurements from a Vite development server; not a production build or production performance qualification. Production bundle gates remain open.' } };
}
