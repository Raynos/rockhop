import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';
import { createHash } from 'node:crypto';

const runtime = fileURLToPath(new URL('./private-rider.mjs', import.meta.url));
const reviewModules = ['private-rider.mjs', 'new-humanoid-contract.mjs', 'anthropometric-inverse.mjs']
  .map(name => fileURLToPath(new URL(name, import.meta.url)));
export const comparisonRider = {
  id: 'street-remastered', label: 'Mustard · Remastered',
  full: 'models/rider-street-remastered.glb', lod: 'models/rider-street-remastered-lod.glb',
};
export const comparisonModelMapping = source => Object.fromEntries([comparisonRider.full, comparisonRider.lod].map(slot => [slot, source]));
const replaceOnce = (code, before, after) => {
  if (code.split(before).length !== 2) throw new Error(`Private comparison source changed: ${before}`);
  return code.replace(before, after);
};
export function comparisonSnapshotSource(code) {
  code = replaceOnce(code,
    '  if (!fs.existsSync(path.join(sourceRoot, logical))) throw new Error(`unknown logical model ${logical}`);',
    `  if (logical === ${JSON.stringify(comparisonRider.lod)}) fs.linkSync(path.join(sourceRoot, ${JSON.stringify(comparisonRider.full)}), path.join(sourceRoot, logical));
  else fs.copyFileSync(path.resolve(mapping[logical]), path.join(sourceRoot, logical));`);
  return replaceOnce(code, 'const assets = readModelCatalog(sourceRoot);',
    `const assets = readModelCatalog(sourceRoot);
const selectedFull = assets.find(a => a.logical === ${JSON.stringify(comparisonRider.full)})!;
const selectedLod = assets.find(a => a.logical === ${JSON.stringify(comparisonRider.lod)})!;
if (selectedFull.sha256 !== selectedLod.sha256) throw new Error('Selected review full/LOD alias differs');
selectedLod.url = selectedFull.url;`);
}

function comparisonSource(code, id) {
  const { id: outfit, full, label } = comparisonRider;
  if (id.endsWith('/src/core/riderPresets.ts')) {
    code = replaceOnce(code, "export type RiderOutfit = ", `export type RiderOutfit = '${outfit}' | `);
    code = replaceOnce(code, '];\nexport const AVAILABLE_RIDER_PRESETS',
      `  { id: '${outfit}', available: true, family: 'street', label: '${label}', detail: 'New face, hoodie, jeans, gloves & boots', reference: '06' },\n];\nexport const AVAILABLE_RIDER_PRESETS`);
    code = replaceOnce(code, "  if (value === 'street-openface')", `  if (value === '${outfit}') return 'street';\n  if (value === 'street-openface')`);
    return replaceOnce(code, "  if (value === 'street')", `  if (value === '${outfit}') return '${outfit}';\n  if (value === 'street')`);
  }
  if (id.endsWith('/src/render/hero/urls.ts')) {
    code = replaceOnce(code, '  rider: {', `  rider: {\n    '${outfit}': '${full}',`);
    code = replaceOnce(code, 'export const HERO_FILES_BY_OUTFIT_CLASS = {',
      `export const HERO_FILES_BY_OUTFIT_CLASS = {\n  '${outfit}': { rookie: heroFiles('${outfit}', 'rookie'), pro: heroFiles('${outfit}', 'pro') },`);
    return replaceOnce(code, 'export const HERO_FILES_BY_OUTFIT = {',
      `export const HERO_FILES_BY_OUTFIT = {\n  '${outfit}': [...HERO_FILES_BY_OUTFIT_CLASS['${outfit}'].rookie, ...HERO_FILES_BY_OUTFIT_CLASS['${outfit}'].pro],`);
  }
  if (id.endsWith('/src/ui/garage.ts')) return replaceOnce(code, 'export const OUTFIT_SWATCH: Record<RiderOutfit, string> = {',
    `export const OUTFIT_SWATCH: Record<RiderOutfit, string> = {\n  '${outfit}': '#d6a021',`);
  if (id.endsWith('/src/render/index.ts') || id.endsWith('/src/boot/asset-totals.ts')) {
    const marker = 'Object.values(HERO_FILES_BY_OUTFIT_CLASS).flatMap';
    code = replaceOnce(code, marker, `Object.entries(HERO_FILES_BY_OUTFIT_CLASS).filter(([outfit]) => outfit !== '${outfit}').map(([, value]) => value).flatMap`);
    if (id.endsWith('/src/render/index.ts')) {
      code = replaceOnce(code, '    const files = HERO_FILE_SET.filter',
        `    const inventory = this.riderOutfit === '${outfit}' ? [...HERO_FILE_SET, ...heroPair(this.riderOutfit, this.bikeClass, 'full'), ...heroPair(this.riderOutfit, this.bikeClass, 'lod')] : HERO_FILE_SET;\n    const files = inventory.filter`);
      // The review source is fetched on choice, outside the unchanged original
      // boot-byte bucket, including when the private preference was persisted.
      code = replaceOnce(code, 'loadGltf(f, false, bytes)', `loadGltf(f, false, f.includes('rider-${outfit}') ? undefined : bytes)`);
      code = replaceOnce(code, "    return (this.heroDocUrl.get(doc!) ?? '').endsWith('-lod.glb');",
        "    return !doc?.scene.userData.privateSelectedRider && (this.heroDocUrl.get(doc!) ?? '').endsWith('-lod.glb');");
    }
    return code;
  }
  if (id.endsWith('/src/boot/offline-pack.ts')) return replaceOnce(code, '    if (heroes.has(logical)',
    `    if (logical === '${full}' || logical === '${comparisonRider.lod}') continue;\n    if (heroes.has(logical)`);
  return null;
}

/** Only explicitly declared slots containing this same source may share a document. */
export function selectedRiderAliases(metadata) {
  const source = metadata.selectedRiderSource;
  if (!source) return {};
  const slots = source.modelSlots;
  if (!Array.isArray(slots) || !slots.length || new Set(slots).size !== slots.length
    || !slots.every(slot => typeof slot === 'string' && /^models\/rider[a-z0-9-]*\.glb$/.test(slot))) {
    throw new Error('Private rider: declare unique exact rider source slots');
  }
  if (!slots.includes(source.canonicalLogical)) throw new Error('Private rider: canonical source slot is undeclared');
  if (!/^[a-f0-9]{64}$/.test(source.sourceSHA256 ?? '') || source.sourceSHA256 !== metadata.sourceSHA256) {
    throw new Error('Private rider: alias source SHA does not match the loaded source');
  }
  return Object.fromEntries(slots.map(slot => [slot, source.canonicalLogical]));
}

/** Compile-time substitution in a private build, never writes player sources. */
export function privateEnginePlugin(metadata) {
  const touched = new Set();
  const resolvedChunks = new Map();
  const aliases = selectedRiderAliases(metadata);
  const comparison = metadata.comparison === true;
  if (comparison && metadata.releaseBuild !== false) throw new Error('Private comparison must declare releaseBuild false');
  if (comparison && (Object.keys(aliases).length !== 2 || ![comparisonRider.full, comparisonRider.lod].every(slot => aliases[slot] === comparisonRider.full))) {
    throw new Error('Private comparison requires only the new full/LOD selected slots');
  }
  const preserveImages = metadata.selectedRiderSource?.texturePolicy === 'preserve-authored-images';
  if (comparison && !preserveImages) throw new Error('Private comparison requires selected authored images');
  if (metadata.selectedRiderSource?.texturePolicy && !preserveImages) throw new Error('Private rider: unknown texture policy');
  if (preserveImages && !Object.keys(aliases).length) throw new Error('Private rider: authored images require exact selected source aliases');
  return {
    name: 'rockhop:private-first-principles-rider', enforce: 'pre',
    async buildStart() {
      if (!comparison) return;
      for (const source of ['three', '@sentry/browser', ...reviewModules]) {
        const resolved = await this.resolve(source);
        if (!resolved || resolved.external) throw new Error(`Private comparison module unresolved: ${source}`);
        resolvedChunks.set(source, resolved.id);
      }
    },
    outputOptions(options) {
      if (!comparison) return null;
      if (!options.manualChunks || typeof options.manualChunks !== 'object') throw new Error('Private comparison expects explicit vendor chunks');
      const roots = new Map(), assigned = new Map();
      for (const [name, sources] of Object.entries(options.manualChunks)) for (const source of sources) {
        const id = resolvedChunks.get(source);
        if (!id) throw new Error(`Private comparison vendor chunk changed: ${source}`);
        roots.set(id, name);
      }
      for (const source of reviewModules) {
        const id = resolvedChunks.get(source);
        if (!id) throw new Error('Private comparison native module unresolved');
        roots.set(id, 'rider-review');
      }
      // Preserve the existing vendor dependency closures. Explicit-only chunks
      // then keep shared game geometry out of the optional native75 module.
      const visit = (id, name) => {
        if (assigned.has(id) || roots.has(id) && roots.get(id) !== name) return;
        const info = this.getModuleInfo(id); if (!info || info.isExternal) return;
        assigned.set(id, name);
        for (const child of info.importedIds) visit(child, name);
      };
      for (const [id, name] of roots) {
        if (name === 'rider-review') assigned.set(id, name); else visit(id, name);
      }
      return { ...options, onlyExplicitManualChunks: true, manualChunks: id => assigned.get(id) };
    },
    generateBundle: { order: 'post', handler(_options, bundle) {
      const catalog = bundle['model-catalog.json'], manifest = bundle['load-manifest.json'];
      if (!catalog || !manifest) throw new Error('Private rider: missing actual model/load manifests');
      catalog.source = JSON.stringify({ ...JSON.parse(String(catalog.source)), privateRiderMetadata: metadata });
      const loads = JSON.parse(String(manifest.source)), row = loads.items.find(item => item.path === './model-catalog.json');
      if (!row) throw new Error('Private rider: missing catalog load receipt');
      row.bytes = Buffer.byteLength(catalog.source); row.gz = gzipSync(catalog.source).length;
      if (comparison) {
        const chunks = Object.values(bundle).filter(item => item.type === 'chunk');
        const reviews = chunks.filter(chunk => chunk.name === 'rider-review');
        if (reviews.length !== 1 || reviews[0].isEntry || Object.keys(reviews[0].modules).length !== reviewModules.length
          || Object.keys(reviews[0].modules).some(id => !reviewModules.some(source => resolvedChunks.get(source) === id))) {
          throw new Error('Private comparison needs one exact native75 review chunk');
        }
        const review = reviews[0], pending = chunks.filter(chunk => chunk.isEntry).map(chunk => chunk.fileName), seen = new Set();
        for (const file of pending) {
          if (seen.has(file)) continue; seen.add(file);
          if (file === review.fileName) throw new Error('Private review chunk became a static player dependency');
          const chunk = bundle[file]; if (chunk?.type === 'chunk') pending.push(...chunk.imports);
        }
        const measurements = { releaseBuild: false, normalPlayerLimitGzipBytes: 701 * 1024,
          normalPlayerGzipBytes: 0, selectedReviewGzipBytes: 0, otherExcludedGzipBytes: 0, allJavaScriptGzipBytes: 0 };
        for (const [name, item] of Object.entries(bundle)) {
          if (item.type !== 'chunk' && !name.endsWith('.js')) continue;
          const bytes = gzipSync(item.type === 'chunk' ? item.code : item.source).length;
          measurements.allJavaScriptGzipBytes += bytes;
          if (name === review.fileName) measurements.selectedReviewGzipBytes += bytes;
          else if (/^assets\/(retired|audio-offline|legacy-physics|sentry-errors)-[\w-]+\.js$/.test(name)) measurements.otherExcludedGzipBytes += bytes;
          else measurements.normalPlayerGzipBytes += bytes;
        }
        const report = JSON.stringify({ ...measurements,
          comparisonBudgetGzipBytes: measurements.normalPlayerGzipBytes + measurements.selectedReviewGzipBytes,
          reviewChunk: review.fileName, reviewChunkSHA256: createHash('sha256').update(review.code).digest('hex'),
          limits: 'Selected review JS is additional to the unchanged normal-player gate; full comparison cost remains reported.' });
        this.emitFile({ type: 'asset', fileName: 'rider-comparison-js.json', source: report });
        loads.items.push({ path: './rider-comparison-js.json', bytes: Buffer.byteLength(report), gz: gzipSync(report).length, phase: 'other', label: 'Private comparison JS measurements' });
        // The reused hero recipe emits candidate assets after the normal load
        // manifest hook. Retain exact selected bytes in this private manifest.
        const models = JSON.parse(String(catalog.source)).models;
        const full = models.find(model => model.logical === comparisonRider.full);
        const lod = models.find(model => model.logical === comparisonRider.lod);
        if (!full || !lod || full.url !== lod.url || full.sha256 !== metadata.sourceSHA256 || lod.sha256 !== full.sha256 || lod.bytes !== full.bytes) {
          throw new Error('Private comparison model manifest differs from selected alias');
        }
        const asset = bundle[full.url];
        if (asset?.type !== 'asset' || Buffer.byteLength(asset.source) !== full.bytes) throw new Error('Private comparison emitted model missing');
        if (!loads.items.some(item => item.path === './' + full.url)) loads.items.push({
          path: './' + full.url, bytes: full.bytes, gz: full.bytes, phase: 'models', label: comparisonRider.label, sha256: full.sha256,
        });
      }
      manifest.source = JSON.stringify(loads);
    } },
    transform(code, id) {
      const normalized = id.split('?')[0].replaceAll(path.sep, '/');
      if (comparison) {
        const changed = comparisonSource(code, normalized);
        if (changed !== null) { touched.add(normalized.slice(normalized.lastIndexOf('/src/') + 5)); return { code: changed, map: null }; }
      }
      if (normalized.endsWith('/src/render/hero/gltfRider.ts')) {
        touched.add('rider');
        if (comparison) {
          code = replaceOnce(code, 'export class GltfRider {', 'class OriginalGltfRider {');
          return { code: `import { privateSelectedRiderClass } from './gltf';\n` + code + `
export class GltfRider extends OriginalGltfRider {
  constructor(gltf, lib) {
    if (gltf.scene.userData.privateSelectedRider) {
      if (!privateSelectedRiderClass) throw new Error('Selected rider driver unavailable');
      return new privateSelectedRiderClass(gltf, lib);
    }
    super(gltf, lib);
  }
  static [Symbol.hasInstance](instance) {
    return instance instanceof OriginalGltfRider || !!privateSelectedRiderClass && instance instanceof privateSelectedRiderClass;
  }
}\n`, map: null };
        }
        return { code: `import * as THREE from 'three';\nimport { createPrivateRiderClass } from ${JSON.stringify(runtime)};\nimport { privateRiderMetadata } from './gltf';\nexport const GltfRider = createPrivateRiderClass(privateRiderMetadata);\nexport const boneName = name => THREE.PropertyBinding.sanitizeNodeName(name);\n`, map: null };
      }
      if (normalized.endsWith('/src/render/hero/gltf.ts')) {
        const marker = '              resolve(g);';
        if (code.split(marker).length !== 2) throw new Error('Private rider build: actual GLTF resolve changed');
        if (Object.keys(aliases).length) {
          const cacheMarker = '  url = modelAssetUrl(url);';
          if (code.split(cacheMarker).length !== 2) throw new Error('Private rider build: logical model resolution changed');
          // Canonicalize logical names before immutable URL resolution and the
          // existing cache. Ten source slots then share one parsed document,
          // maps and retry lifecycle; bikes keep their original logical URLs.
          code = code.replace(cacheMarker,
            `  url = modelAssetUrl((${JSON.stringify(aliases)})[url] ?? url);`);
          touched.add('source-aliases');
        }
        if (preserveImages) {
          const shrinkMarker = '          shrinkTextures(g.scene);';
          if (code.split(shrinkMarker).length !== 2) throw new Error('Private rider build: texture preparation changed');
          // Review the selected source at its authored resolution. Other models
          // retain the ordinary game budget; no maps are synthesized or upscaled.
          code = code.replace(shrinkMarker,
            `          if (url === modelAssetUrl(${JSON.stringify(metadata.selectedRiderSource.canonicalLogical)})) {
            ${comparison ? 'g.scene.userData.privateSelectedRider = true;' : ''}
            rememberPrivateAuthoredImages(g.scene);
          }
          shrinkTextures(g.scene);`);
          const textureMarker = '        if (!t || done.has(t)) continue;';
          if (code.split(textureMarker).length !== 2) throw new Error('Private rider build: resident texture budget changed');
          code = `const privateAuthoredImages = new WeakSet<object>();
function rememberPrivateAuthoredImages(root: THREE.Object3D) {
  root.traverse(object => {
    const mesh = object as THREE.Mesh;
    if (!mesh.isMesh) return;
    for (const material of Array.isArray(mesh.material) ? mesh.material : [mesh.material]) {
      for (const value of Object.values(material)) {
        const texture = value as THREE.Texture;
        if (texture?.isTexture) privateAuthoredImages.add(texture);
      }
    }
  });
}\n` + code.replace(textureMarker,
            '        if (!t || done.has(t) || privateAuthoredImages.has(t)) continue;');
          touched.add('authored-images');
        }
        touched.add('metadata');
        const ready = comparison
          ? `export let privateSelectedRiderClass;
          function loadPrivateSelectedRider() {
            return loadPrivateRiderMetadata().then(() => import(${JSON.stringify(runtime)})).then(module => {
              return privateSelectedRiderClass ??= module.createPrivateRiderClass(privateRiderMetadata);
            });
          }\n` : '';
        return { code: ready + `export const privateRiderMetadata = {}; let privateRiderRequest;
          function loadPrivateRiderMetadata() {
            return privateRiderRequest ??= fetch(new URL('model-catalog.json', document.baseURI))
              .then(response => { if (!response.ok) throw new Error('Private rider metadata HTTP ' + response.status); return response.json(); })
              .then(value => { if (!value.privateRiderMetadata) throw new Error('Private rider metadata missing'); return Object.assign(privateRiderMetadata, value.privateRiderMetadata); })
              .catch(error => { privateRiderRequest = null; throw error; });
          }\n` +
          code.replace(marker, comparison
            ? '              if (g.scene.userData.privateSelectedRider) void loadPrivateSelectedRider().then(() => resolve(g), () => resolve(null)); else resolve(g);'
            : '              void loadPrivateRiderMetadata().then(() => resolve(g), () => resolve(null));'), map: null };
      }
      if (normalized.endsWith('/src/render/hero/lod.ts')) {
        const marker = '  mergeSkinnedByMaterial(root);';
        if (code.split(marker).length !== 2) throw new Error('Private rider build: prepareHero material-merge call changed');
        touched.add('parts');
        return { code: code.replace(marker, comparison ? '  if (!root.userData.privateSelectedRider) mergeSkinnedByMaterial(root);'
          : '  // Private rider review preserves explicitly declared object/primitive roles.'), map: null };
      }
      return null;
    },
    buildEnd(error) {
      if (!error && (!touched.has('rider') || !touched.has('parts') || !touched.has('metadata'))) throw new Error('Private rider build did not consume all scoped substitutions');
      if (!error && Object.keys(aliases).length && !touched.has('source-aliases')) throw new Error('Private rider build did not consume selected source aliases');
      if (!error && preserveImages && !touched.has('authored-images')) throw new Error('Private rider build did not preserve authored images');
      if (!error && comparison) for (const source of ['core/riderPresets.ts', 'render/hero/urls.ts', 'ui/garage.ts', 'render/index.ts', 'boot/asset-totals.ts', 'boot/offline-pack.ts']) {
        if (!touched.has(source)) throw new Error(`Private comparison did not consume ${source}`);
      }
    },
  };
}
