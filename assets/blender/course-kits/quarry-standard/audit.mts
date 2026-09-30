/** CPU-only source and lifetime audit for the unintegrated quarry kit. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { compileTrack } from '../../../../src/tracks/compile';
import { D1, D2, D3 } from '../../../../src/tracks/rockhop/quarry';
import { zoneGround } from '../../../../src/render/world/zones/zoneKit';
import { buildQuarryStandard, loadQuarryLandmarks, planQuarryStandard,
  quarryCutY } from '../../../../src/render/world/zones/quarryStandard';

const dir = path.dirname(fileURLToPath(import.meta.url));
const out = path.join(dir, 'out');
const report: unknown[] = [];
const lib = { complete(_material: THREE.MeshStandardMaterial) {} } as never;

function geometryOnly(bytes: Buffer): Buffer {
  const length = bytes.readUInt32LE(12);
  const doc = JSON.parse(bytes.subarray(20, 20 + length).toString());
  delete doc.images; delete doc.textures; delete doc.samplers;
  for (const m of doc.materials ?? []) {
    delete m.normalTexture; delete m.occlusionTexture; delete m.emissiveTexture;
    if (m.pbrMetallicRoughness) {
      delete m.pbrMetallicRoughness.baseColorTexture;
      delete m.pbrMetallicRoughness.metallicRoughnessTexture;
    }
  }
  const json = Buffer.from(JSON.stringify(doc));
  const pad = Buffer.alloc((4 - json.length % 4) % 4, 32);
  const bin = bytes.subarray(20 + length);
  const result = Buffer.alloc(20 + json.length + pad.length + bin.length);
  result.writeUInt32LE(0x46546c67, 0); result.writeUInt32LE(2, 4);
  result.writeUInt32LE(result.length, 8);
  result.writeUInt32LE(json.length + pad.length, 12);
  result.writeUInt32LE(0x4e4f534a, 16);
  json.copy(result, 20); pad.copy(result, 20 + json.length);
  bin.copy(result, 20 + json.length + pad.length);
  return result;
}

for (const def of [D1, D2, D3]) {
  const track = compileTrack(def);
  const groundAt = (x: number, z: number) => zoneGround('quarry', def.profile, x, z);
  const plan = planQuarryStandard(track, 0, def.finishX);
  const summaries = [];
  for (const detail of ['full', 'low'] as const) {
    const kit = buildQuarryStandard(plan, { lib, detail, groundAt });
    assert.equal(kit.meshes.filter(m => m.name.endsWith('excavated-terraces')).length, 1);
    assert(kit.textureBytes <= (detail === 'low' ? 400_000 : 1_500_000));
    let terrainVertices = 0;
    for (const mesh of kit.meshes) {
      const pos = mesh.geometry.getAttribute('position');
      assert(pos && pos.count > 0);
      terrainVertices += pos.count;
      for (let i = 0; i < pos.count; i++)
        for (const v of [pos.getX(i), pos.getY(i), pos.getZ(i)])
          assert(Number.isFinite(v), `${def.id}: ${mesh.name} nonfinite coordinate`);
    }
    const bedding = kit.meshes.find(m => m.name.endsWith('d1-contact-bedding'));
    if (def.id === D1.id) {
      assert(bedding && plan.contacts.length === 4);
      const p = bedding.geometry.getAttribute('position');
      for (let i = 0; i < p.count; i++) {
        const x = p.getX(i), y = p.getY(i), z = p.getZ(i);
        const c = plan.contacts.find(contact => x >= contact.x0 - 1e-4 && x <= contact.x1 + 1e-4);
        assert(c, `D1 bedding outside four real ledges at x=${x}`);
        assert(y <= c.topY - .09, `D1 cosmetic bedding above real top at x=${x}`);
        assert(z < -3, `D1 bedding crossed tire line at x=${x}`);
      }
      assert.deepEqual(plan.contacts.map(c => [c.x0, c.x1, c.topY]),
        [[91.4, 98.4, .4], [98.4, 104.4, .8],
          [104.4, 110.4, 1.2], [110.4, 118.4, 1.6]]);
    } else assert(!bedding);
    for (const landmark of plan.landmarks) {
      const y = quarryCutY(plan, groundAt, landmark.x, landmark.z);
      assert(Number.isFinite(y));
      assert(y <= groundAt(landmark.x, -9) + .01);
    }
    summaries.push({ detail, terrainVertices, textureBytes: kit.textureBytes,
      modelSites: plan.landmarks.length, protectedWindows: plan.protectedWindows });
    kit.dispose(); kit.dispose();
  }
  report.push({ course: def.id, contacts: plan.contacts, summaries });
}

// Substitute only file fetch, retaining Three's actual parseAsync+Meshopt path.
const originalLoad = GLTFLoader.prototype.loadAsync;
let imageClosed = 0;
GLTFLoader.prototype.loadAsync = async function (url: string) {
  const file = path.basename(url);
  const bytes = geometryOnly(fs.readFileSync(path.join(out, file)));
  const gltf = await this.parseAsync(bytes.buffer.slice(bytes.byteOffset,
    bytes.byteOffset + bytes.byteLength), '');
  const first = gltf.scene.children.find(o => (o as THREE.Mesh).isMesh) as THREE.Mesh | undefined;
  if (first) (first.material as THREE.MeshStandardMaterial).map = new THREE.Texture({
    width: 16, height: 16, close: () => { imageClosed++; },
  });
  return gltf;
} as typeof GLTFLoader.prototype.loadAsync;
try {
  await MeshoptDecoder.ready;
  for (const def of [D1, D2, D3]) {
    const track = compileTrack(def);
    const plan = planQuarryStandard(track, 0, def.finishX);
    const groundAt = (x: number, z: number) => zoneGround('quarry', def.profile, x, z);
    for (const detail of ['full', 'lod'] as const) {
      const previous = imageClosed;
      const asset = await loadQuarryLandmarks(plan, detail, lib, groundAt, file => file);
      assert.equal(asset.root.children.length, plan.landmarks.length);
      assert(asset.textureBytes > 1000);
      for (const node of asset.root.children) {
        const landmark = plan.landmarks.find(a => node.name === `quarry:${a.kind}:${Math.round(a.x)}`);
        assert(landmark, `orphan model ${node.name}`);
        assert(Math.abs(node.position.y - quarryCutY(plan, groundAt, landmark.x,
          landmark.z) - .08) < 1e-6);
      }
      asset.dispose(); asset.dispose();
      assert.equal(asset.root.children.length, 0);
      assert.equal(imageClosed - previous,
        new Set(plan.landmarks.map(a => a.kind)).size, 'each decoded bitmap closes once');
    }
  }
} finally { GLTFLoader.prototype.loadAsync = originalLoad; }

fs.writeFileSync(path.join(out, 'source-audit.json'), JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ passed: true, report }, null, 2));
