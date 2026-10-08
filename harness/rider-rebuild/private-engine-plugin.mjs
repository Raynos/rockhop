import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';

const runtime = fileURLToPath(new URL('./private-rider.mjs', import.meta.url));

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
  const aliases = selectedRiderAliases(metadata);
  const preserveImages = metadata.selectedRiderSource?.texturePolicy === 'preserve-authored-images';
  if (metadata.selectedRiderSource?.texturePolicy && !preserveImages) throw new Error('Private rider: unknown texture policy');
  if (preserveImages && !Object.keys(aliases).length) throw new Error('Private rider: authored images require exact selected source aliases');
  return {
    name: 'rockhop:private-first-principles-rider', enforce: 'pre',
    generateBundle: { order: 'post', handler(_options, bundle) {
      const catalog = bundle['model-catalog.json'], manifest = bundle['load-manifest.json'];
      if (!catalog || !manifest) throw new Error('Private rider: missing actual model/load manifests');
      catalog.source = JSON.stringify({ ...JSON.parse(String(catalog.source)), privateRiderMetadata: metadata });
      const loads = JSON.parse(String(manifest.source)), row = loads.items.find(item => item.path === './model-catalog.json');
      if (!row) throw new Error('Private rider: missing catalog load receipt');
      row.bytes = Buffer.byteLength(catalog.source); row.gz = gzipSync(catalog.source).length;
      manifest.source = JSON.stringify(loads);
    } },
    transform(code, id) {
      const normalized = id.split('?')[0].replaceAll(path.sep, '/');
      if (normalized.endsWith('/src/render/hero/gltfRider.ts')) {
        touched.add('rider');
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
            `          if (url === modelAssetUrl(${JSON.stringify(metadata.selectedRiderSource.canonicalLogical)})) rememberPrivateAuthoredImages(g.scene);
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
        return { code: `export const privateRiderMetadata = {}; let privateRiderRequest;
          function loadPrivateRiderMetadata() {
            return privateRiderRequest ??= fetch(new URL('model-catalog.json', document.baseURI))
              .then(response => { if (!response.ok) throw new Error('Private rider metadata HTTP ' + response.status); return response.json(); })
              .then(value => { if (!value.privateRiderMetadata) throw new Error('Private rider metadata missing'); return Object.assign(privateRiderMetadata, value.privateRiderMetadata); })
              .catch(error => { privateRiderRequest = null; throw error; });
          }\n` +
          code.replace(marker, '              void loadPrivateRiderMetadata().then(() => resolve(g), () => resolve(null));'), map: null };
      }
      if (normalized.endsWith('/src/render/hero/lod.ts')) {
        const marker = '  mergeSkinnedByMaterial(root);';
        if (code.split(marker).length !== 2) throw new Error('Private rider build: prepareHero material-merge call changed');
        touched.add('parts');
        return { code: code.replace(marker, '  // Private rider review preserves explicitly declared object/primitive roles.'), map: null };
      }
      return null;
    },
    buildEnd(error) {
      if (!error && (!touched.has('rider') || !touched.has('parts') || !touched.has('metadata'))) throw new Error('Private rider build did not consume all scoped substitutions');
      if (!error && Object.keys(aliases).length && !touched.has('source-aliases')) throw new Error('Private rider build did not consume selected source aliases');
      if (!error && preserveImages && !touched.has('authored-images')) throw new Error('Private rider build did not preserve authored images');
    },
  };
}
