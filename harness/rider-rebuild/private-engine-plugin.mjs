import path from 'node:path';
import { fileURLToPath } from 'node:url';

const runtime = fileURLToPath(new URL('./private-rider.mjs', import.meta.url));

/** Compile-time substitution in a private build, never writes player sources. */
export function privateEnginePlugin(metadata) {
  const touched = new Set();
  return {
    name: 'rockhop:private-first-principles-rider', enforce: 'pre',
    transform(code, id) {
      const normalized = id.split('?')[0].replaceAll(path.sep, '/');
      if (normalized.endsWith('/src/render/hero/gltfRider.ts')) {
        touched.add('rider');
        return { code: `import * as THREE from 'three';\nimport { createPrivateRiderClass } from ${JSON.stringify(runtime)};\nexport const GltfRider = createPrivateRiderClass(${JSON.stringify(metadata)});\nexport const boneName = name => THREE.PropertyBinding.sanitizeNodeName(name);\n`, map: null };
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
      if (!error && (!touched.has('rider') || !touched.has('parts'))) throw new Error('Private rider build did not consume both scoped substitutions');
    },
  };
}
