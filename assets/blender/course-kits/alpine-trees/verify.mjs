import { readFileSync, readdirSync, statSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { dirname, resolve } from 'node:path';
import { fileURLToPath } from 'node:url';
import { createRequire } from 'node:module';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder as ProductionDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';

const here = dirname(fileURLToPath(import.meta.url));
const root = resolve(here, '../../../..');
const toolingRequire = createRequire(resolve(root, '../wildshard-singleplayer/package.json'));
const { NodeIO } = await import(toolingRequire.resolve('@gltf-transform/core'));
const { ALL_EXTENSIONS } = await import(toolingRequire.resolve('@gltf-transform/extensions'));
const { MeshoptDecoder } = await import(toolingRequire.resolve('meshoptimizer'));
const staged = process.argv.includes('--staged');
const dest = staged ? resolve(root, 'public/models/course-kits/alpine-trees') : resolve(here, 'build');
const io = new NodeIO().registerExtensions(ALL_EXTENSIONS).registerDependencies({ 'meshopt.decoder': MeshoptDecoder });
const report = { candidate: true, checked: new Date().toISOString(), variants: [], files: [], sources: [] };
const hash = p => createHash('sha256').update(readFileSync(p)).digest('hex');
await MeshoptDecoder.ready;
await ProductionDecoder.ready;
const specs = JSON.parse(readFileSync(resolve(here, 'build/trees.json'), 'utf8'));
const productionLoader = new GLTFLoader().setMeshoptDecoder(ProductionDecoder);
for (const file of readdirSync(dest).sort()) {
  if (file.endsWith('.raw.glb')) continue;
  report.files.push({ file, bytes: statSync(resolve(dest, file)).size, sha256: hash(resolve(dest, file)) });
  if (!file.endsWith('.glb')) continue;
  const document = await io.read(resolve(dest, file));
  const meshes = document.getRoot().listMeshes();
  const rows = meshes.map(mesh => {
    let triangles = 0;
    for (const primitive of mesh.listPrimitives()) {
      const positions = primitive.getAttribute('POSITION').getArray();
      if (Array.from(positions).some(value => !Number.isFinite(value))) throw new Error(`${file}: nonfinite positions`);
      const indices = primitive.getIndices().getArray();
      if (Array.from(indices).some(value => value >= positions.length / 3)) throw new Error(`${file}: index outside mesh`);
      triangles += indices.length / 3;
    }
    return { name: mesh.getName(), triangles };
  });
  // Exercise the exact shipping decoder and its quantized node transforms.
  // Node has no image renderer: material maps were read and verified by NodeIO above.
  const original = readFileSync(resolve(dest, file));
  const jsonLength = original.readUInt32LE(12);
  const header = JSON.parse(original.subarray(20, 20 + jsonLength).toString());
  delete header.images; delete header.textures; delete header.samplers;
  for (const material of header.materials) {
    for (const key of ['normalTexture', 'occlusionTexture', 'emissiveTexture']) delete material[key];
    for (const key of ['baseColorTexture', 'metallicRoughnessTexture']) delete material.pbrMetallicRoughness[key];
  }
  const rewrittenJson = Buffer.from(JSON.stringify(header));
  const padding = Buffer.alloc((4 - rewrittenJson.length % 4) % 4, 32);
  const binChunk = original.subarray(20 + jsonLength);
  const rewritten = Buffer.alloc(20 + rewrittenJson.length + padding.length + binChunk.length);
  rewritten.writeUInt32LE(0x46546c67, 0); rewritten.writeUInt32LE(2, 4); rewritten.writeUInt32LE(rewritten.length, 8);
  rewritten.writeUInt32LE(rewrittenJson.length + padding.length, 12); rewritten.writeUInt32LE(0x4e4f534a, 16);
  rewrittenJson.copy(rewritten, 20); padding.copy(rewritten, 20 + rewrittenJson.length);
  binChunk.copy(rewritten, 20 + rewrittenJson.length + padding.length);
  const production = await productionLoader.parseAsync(rewritten.buffer.slice(rewritten.byteOffset, rewritten.byteOffset + rewritten.byteLength), '');
  production.scene.updateMatrixWorld(true);
  let decodedMeshes = 0;
  production.scene.traverse(object => {
    if (!(object instanceof THREE.Mesh)) return;
    const bounds = new THREE.Box3().setFromObject(object);
    if (![...bounds.min, ...bounds.max].every(Number.isFinite)) throw new Error(`${file}: shipping decoder produced nonfinite bounds`);
    const variant = specs.variants.find(variant => object.name.startsWith(variant.name + '__'));
    if (!variant) throw new Error(`${file}: unexpected mesh ${object.name}`);
    if (object.name.endsWith('__bark') && bounds.max.y < variant.height * .8) throw new Error(`${file}: quantized height lost for ${object.name}`);
    if (object.name.endsWith('__branches')) {
      const uv = object.geometry.getAttribute('uv');
      for (let i = 0; i < uv.count; i++) {
        const v = uv.getY(i);
        if (variant.species === 'snag' ? v > .5 : v < .5) throw new Error(`${file}: bottom-origin atlas UVs persisted for ${object.name}`);
      }
    }
    decodedMeshes++;
  });
  if (decodedMeshes !== rows.length) throw new Error(`${file}: production decoder lost a mesh`);
  report.variants.push({ file, meshes: rows, totalTriangles: rows.reduce((sum, row) => sum + row.triangles, 0), materials: document.getRoot().listMaterials().length, productionDecoderMeshes: decodedMeshes });
}
for (const dir of [here, resolve(here, 'source')]) for (const file of readdirSync(dir).sort()) {
  const path = resolve(dir, file);
  if (statSync(path).isFile()) report.sources.push({ file: path.slice(root.length + 1), sha256: hash(path) });
}
writeFileSync(resolve(root, `docs/evidence/course-remaster/alpine-tree-kit/${staged ? 'staged-report' : 'build-report'}.json`), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify(report.variants.map(({ file, totalTriangles, materials }) => ({ file, totalTriangles, materials })), null, 2));
