/** CPU-only optical-state audit. Texture pixels remain separately frozen on disk. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import type * as THREE from 'three';
import { loadRigAt } from '../../../../../../../src/render/hero/gltfTestUtils.ts';
import { prepareHero } from '../../../../../../../src/render/hero/lod.ts';
import { prepareHeroMaterials } from '../../../../../../../src/render/hero/gltf.ts';
import { MaterialLibrary } from '../../../../../../../src/render/materials/library.ts';
const source = '/Users/raynos/projects/localai/runtime/rockhop-rider-search-v1/one-rider-v2/rig-adapter01/body-bind22/skin-field01/rider.glb';
const evidence = '/Users/raynos/projects/games/rockhop/docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/body-bind24';
const raw = fs.readFileSync(source);
const sha = (v: string | Buffer) => crypto.createHash('sha256').update(v).digest('hex');
assert.equal(sha(raw), 'cc20ab813669b628c8e5d21596b655188d7188770adc374377cebf40769232ff');
const doc = JSON.parse(raw.subarray(20, 20 + raw.readUInt32LE(12)).toString());
const gltf = await loadRigAt(pathToFileURL(source), true);
function fingerprint(g: THREE.BufferGeometry): string {
  const h = crypto.createHash('sha256');
  for (const [name, attribute] of Object.entries(g.attributes).sort(([a], [b]) => a.localeCompare(b))) {
    h.update(name + '/' + attribute.itemSize + '/' + attribute.count + '/' + attribute.normalized);
    const values = new Float64Array(attribute.count * attribute.itemSize);
    for (let i = 0; i < attribute.count; i++) for (let c = 0; c < attribute.itemSize; c++) values[i * attribute.itemSize + c] = attribute.getComponent(i, c);
    h.update(Buffer.from(values.buffer));
  }
  if (g.index) h.update(Buffer.from(Uint32Array.from(g.index.array).buffer));
  return h.digest('hex');
}
function census() {
  const rows: Record<string, unknown>[] = [];
  gltf.scene.traverse(o => {
    const m = o as THREE.SkinnedMesh;
    if (!m.isMesh) return;
    for (const material of Array.isArray(m.material) ? m.material : [m.material]) {
      const s = material as THREE.MeshPhysicalMaterial;
      m.geometry.computeBoundingBox();
      rows.push({mesh: m.name, material: s.name, type: s.type,
        parserAssociation: gltf.parser.associations.get(material) ?? null,
        vertices: m.geometry.getAttribute('position').count, triangles: (m.geometry.index?.count ?? m.geometry.getAttribute('position').count)/3,
        geometryFingerprint: fingerprint(m.geometry), bounds: {min:m.geometry.boundingBox!.min.toArray(),max:m.geometry.boundingBox!.max.toArray()},
        skeletonBones: m.isSkinnedMesh ? m.skeleton.bones.map(b => b.name) : [],
        opacity:s.opacity, transparent:s.transparent,alphaTest:s.alphaTest,depthWrite:s.depthWrite,side:s.side,
        roughness:s.roughness,metalness:s.metalness,envMapIntensity:s.envMapIntensity,
        transmission:s.transmission ?? null,ior:s.ior ?? null,clearcoat:s.clearcoat ?? null,
        cornealFragmentSurvivesAlphaTest:s.opacity >= s.alphaTest,
      });
    }
  });
  return rows;
}
const decoded = census();
await prepareHero(gltf);
const prepared = census();
const lib = new MaterialLibrary(1);
prepareHeroMaterials(gltf.scene, m => lib.complete(m));
const final = census();
const corneal = final.filter(r => r.material === 'Conservative transparent corneal film');
assert.equal(corneal.length, 1, 'Both original corneal surfaces merge into one semantic material mesh');
assert.equal(corneal[0]!.opacity, .035);
assert.equal(corneal[0]!.alphaTest, .5);
assert.equal(corneal[0]!.transparent, false);
assert.equal(corneal[0]!.cornealFragmentSurvivesAlphaTest, false);
assert.deepEqual(fs.readFileSync(source), raw);
const report = {status:'PASS CPU-only actual decoder/material-path proof; no appearance judgment',sourceSHA256:sha(raw),
  decoded,afterPrepareHero:prepared,afterPrepareHeroMaterials:final,
  sourceCornealPrimitives:doc.meshes[1].primitives.map((p: {material:number;attributes:Record<string,number>;indices:number},i: number)=>({primitive:i,material:p.material,attributes:p.attributes,indices:p.indices})).filter((p:{material:number})=>p.material===7),
  sourceEyeMaterials:doc.materials.slice(6,8),
  verifiedMechanism:'Source cornea alpha .035 is converted from BLEND to alphaTest .5; actual standard alphatest_fragment discards every corneal fragment. The stock neutral albedo is alpha1, so it does not rescue corneal alpha.',
  restrictions:['No GPU, shader execution or actual sampled highlight measured.','loadRigAt strips only texture references in memory; original texture/BIN remains untouched.','Existing aperture, iris depth and lids may independently remain too exposed.','Physical extensions on a GLB would be flattened by prepareHero; a private post-load restoration must run after preparation.'],
};
fs.writeFileSync(evidence+'/runtime-optics-audit.json',JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({sourceSHA256:sha(raw),decodedCornea:decoded.filter(r=>r.material==='Conservative transparent corneal film'),finalCornea:corneal},null,2));
export { fingerprint };
