/** Inspect every candidate GLB with the game's GLTFLoader and MeshoptDecoder.
 * Node has no ImageBitmap: only image references are stripped for this decode;
 * packed image dimensions and MIME are checked on the original file below.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { glbStats } from '../../glb_stats.mjs';

const dir = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(dir, 'out');
const kinds = ['drill', 'crusher', 'haul', 'gantry'];
await MeshoptDecoder.ready;

function geometryOnly(bytes) {
  const length = bytes.readUInt32LE(12);
  const doc = JSON.parse(bytes.subarray(20, 20 + length).toString());
  delete doc.images; delete doc.textures; delete doc.samplers;
  for (const m of doc.materials ?? []) {
    delete m.normalTexture; delete m.occlusionTexture; delete m.emissiveTexture;
    const pbr = m.pbrMetallicRoughness;
    if (pbr) { delete pbr.baseColorTexture; delete pbr.metallicRoughnessTexture; }
  }
  const json = Buffer.from(JSON.stringify(doc));
  const pad = Buffer.alloc((4 - json.length % 4) % 4, 32);
  const bin = bytes.subarray(20 + length);
  const result = Buffer.alloc(20 + json.length + pad.length + bin.length);
  result.writeUInt32LE(0x46546c67, 0);
  result.writeUInt32LE(2, 4);
  result.writeUInt32LE(result.length, 8);
  result.writeUInt32LE(json.length + pad.length, 12);
  result.writeUInt32LE(0x4e4f534a, 16);
  json.copy(result, 20); pad.copy(result, 20 + json.length);
  bin.copy(result, 20 + json.length + pad.length);
  return result;
}

const report = [];
for (const kind of kinds) for (const low of [false, true]) {
  const file = `quarry-${kind}${low ? '-lod' : ''}-packed.glb`;
  const absolute = path.join(out, file);
  const stats = glbStats(absolute);
  assert(stats.extensionsRequired.includes('EXT_meshopt_compression'), `${file}: missing Meshopt`);
  assert(stats.draws <= 7 && stats.draws > 0, `${file}: draw budget`);
  assert(stats.triangles <= (low ? 3000 : 10000), `${file}: triangle budget`);
  assert(stats.bytes <= (low ? 150_000 : 260_000), `${file}: transfer budget`);
  assert(stats.images === 1 && stats.maxTexture === 256, `${file}: expected one 256px paint map`);
  assert(stats.imageList[0].mime === 'image/png', `${file}: unsupported image`);
  const geometry = geometryOnly(fs.readFileSync(absolute));
  const loaded = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder)
    .parseAsync(geometry.buffer.slice(geometry.byteOffset, geometry.byteOffset + geometry.byteLength), '');
  loaded.scene.updateMatrixWorld(true);
  const box = new THREE.Box3().setFromObject(loaded.scene);
  assert([...box.min, ...box.max].every(Number.isFinite), `${file}: nonfinite bounds`);
  assert(box.min.y >= -0.06 && box.min.y <= 0.28, `${file}: ground origin ${box.min.y}`);
  assert(box.max.y > (kind === 'haul' ? 5 : 10), `${file}: collapsed model`);
  assert(box.max.x - box.min.x < (kind === 'crusher' ? 30 : 25) && box.max.z - box.min.z < 20, `${file}: unexpected horizontal bounds`);
  let actualDraws = 0;
  let maxAbs = 0;
  loaded.scene.traverse(object => {
    if (!(object instanceof THREE.Mesh)) return;
    actualDraws += Array.isArray(object.material) ? object.material.length : 1;
    const pos = object.geometry.getAttribute('position');
    assert(pos && pos.count > 0, `${file}: missing vertex buffer`);
    for (let i = 0; i < pos.count; i++) {
      for (const v of [pos.getX(i), pos.getY(i), pos.getZ(i)]) {
        assert(Number.isFinite(v), `${file}: nonfinite decoded vertex`);
        maxAbs = Math.max(maxAbs, Math.abs(v));
      }
    }
  });
  assert.equal(actualDraws, stats.draws, `${file}: draw count changed in decoder`);
  report.push({ file, bytes: stats.bytes, sha256: stats.sha256,
    triangles: stats.triangles, draws: stats.draws,
    bounds: { min: box.min.toArray(), max: box.max.toArray() },
    image: stats.imageList[0], maxDecodedCoordinate: maxAbs });
}
fs.writeFileSync(path.join(out, 'decoder-report.json'), JSON.stringify(report, null, 2) + '\n');
process.stdout.write(JSON.stringify(report, null, 2) + '\n');
