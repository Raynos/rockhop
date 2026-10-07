import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { gzipSync } from 'node:zlib';

const runtime = fileURLToPath(new URL('./private-rider.mjs', import.meta.url));

/** Compile-time substitution in a private build, never writes player sources. */
export function privateEnginePlugin(metadata) {
  const touched = new Set();
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
    },
  };
}
