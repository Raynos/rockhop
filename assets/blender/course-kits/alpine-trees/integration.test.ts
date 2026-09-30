import { readFileSync } from 'node:fs';
import * as THREE from 'three';
import { GLTFLoader, type GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import { afterEach, describe, expect, it, vi } from 'vitest';

vi.mock('../../../../src/render/hero/urls', () => ({
  modelAssetUrl: (url: string) => url.replace(/\/trees/, '/byte-snapshot/trees'),
  modelResourceUrl: (url: string) => url.replace(/\/([^/]+)\.webp$/, '/aa11bb22cc33dd44/$1-aa11bb22cc33dd44.webp'),
}));
import { alpineTreeResourceUrl, loadAlpineTreeCourse, loadAlpineTreeKit } from '../../../../src/render/world/zones/alpineTrees';
import { buildA1ForestPlan, loadA1Forest, removeA1ForestPlaceholders } from '../../../../src/render/world/zones/a1Forest';
import { compileTrack } from '../../../../src/tracks/compile';
import { A1 } from '../../../../src/tracks/rockhop/alpine';
import { zoneGround } from '../../../../src/render/world/zones/zoneKit';
import { PropBatch } from '../../../../src/render/world/props';
import { mountCourseAssets } from '../../../../src/render/world/courseAssets';

async function documentFor(level: 'full' | 'near'): Promise<GLTF> {
  const source = readFileSync(new URL(`../../../../public/models/course-kits/alpine-trees/trees${level === 'near' ? '-lod' : ''}.glb`, import.meta.url));
  const jsonLength = source.readUInt32LE(12);
  const doc = JSON.parse(source.subarray(20, 20 + jsonLength).toString());
  delete doc.images; delete doc.textures; delete doc.samplers;
  for (const material of doc.materials) {
    for (const key of ['normalTexture', 'occlusionTexture', 'emissiveTexture']) delete material[key];
    for (const key of ['baseColorTexture', 'metallicRoughnessTexture']) delete material.pbrMetallicRoughness[key];
  }
  const json = Buffer.from(JSON.stringify(doc));
  const padding = Buffer.alloc((4 - json.length % 4) % 4, 32);
  const binary = source.subarray(20 + jsonLength);
  const buffer = Buffer.alloc(20 + json.length + padding.length + binary.length);
  buffer.writeUInt32LE(0x46546c67, 0); buffer.writeUInt32LE(2, 4); buffer.writeUInt32LE(buffer.length, 8);
  buffer.writeUInt32LE(json.length + padding.length, 12); buffer.writeUInt32LE(0x4e4f534a, 16);
  json.copy(buffer, 20); padding.copy(buffer, 20 + json.length); binary.copy(buffer, 20 + json.length + padding.length);
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).parseAsync(buffer.buffer.slice(buffer.byteOffset, buffer.byteOffset + buffer.byteLength), '');
  const seen = new Set<THREE.Material>();
  gltf.scene.traverse(object => {
    if (!(object instanceof THREE.Mesh) || seen.has(object.material as THREE.Material)) return;
    seen.add(object.material as THREE.Material);
    const material = object.material as THREE.MeshStandardMaterial;
    material.map = new THREE.DataTexture(new Uint8Array([100, 110, 120, 255]), 1, 1);
  });
  return gltf;
}

const assetRoot = 'https://game.example/subpath/';
const placement = { variant: 'pine-b' as const, x: 31, y: -1.1, z: -13.5, scale: .6, yaw: .35 };
function stubMaps(): void {
  vi.spyOn(THREE.TextureLoader.prototype, 'loadAsync').mockImplementation(async () => new THREE.DataTexture(new Uint8Array([100, 110, 120, 255]), 1, 1));
}
afterEach(() => vi.restoreAllMocks());

describe('Alpine staged integration', () => {
  it('redirects only known maps from catalog subfolders to a subpath/store root', () => {
    expect(alpineTreeResourceUrl(`${assetRoot}models/course-kits/alpine-trees/hash/cards-albedo.phone.webp`, assetRoot))
      .toBe(`${assetRoot}models/course-kits/alpine-trees/aa11bb22cc33dd44/cards-albedo.phone-aa11bb22cc33dd44.webp`);
    const model = `${assetRoot}models/course-kits/alpine-trees/hash/trees-sha.glb`;
    expect(alpineTreeResourceUrl(model, assetRoot)).toBe(model);
    expect(alpineTreeResourceUrl('capacitor://localhost/models/hash/cards-normal.phone.webp', 'capacitor://localhost/'))
      .toBe('capacitor://localhost/models/course-kits/alpine-trees/aa11bb22cc33dd44/cards-normal.phone-aa11bb22cc33dd44.webp');
  });

  it('shares decoded prototypes between clusters and preserves packed UV/colour attributes', async () => {
    stubMaps();
    vi.spyOn(GLTFLoader.prototype, 'loadAsync').mockImplementation(url => documentFor(url.includes('-lod') ? 'near' : 'full'));
    const kit = (await loadAlpineTreeKit({ assetRoot }))!;
    const a = kit.cluster([placement, { ...placement, x: 37 }]);
    const b = kit.cluster([{ ...placement, x: 45 }]);
    const first = a.getObjectByName('alpine-full-pine-b-bark') as THREE.InstancedMesh;
    const second = b.getObjectByName('alpine-full-pine-b-bark') as THREE.InstancedMesh;
    expect(first.geometry).toBe(second.geometry);
    expect(first.count).toBe(2);
    expect(first.geometry.getAttribute('position').array).toBeInstanceOf(Float32Array);
    expect(first.geometry.getAttribute('color').array).toBeInstanceOf(Uint8Array);
    expect(first.geometry.getAttribute('color').normalized).toBe(true);
    expect((first.material as THREE.MeshStandardMaterial).vertexColors).toBe(true);
    const branches = a.getObjectByName('alpine-full-pine-b-branches') as THREE.InstancedMesh;
    expect(branches.geometry.getAttribute('uv').array).toBeInstanceOf(Uint16Array);
    expect(branches.geometry.getAttribute('uv').normalized).toBe(true);
    expect((branches.material as THREE.MeshStandardMaterial).vertexColors).toBe(true);
    expect((branches.material as THREE.MeshStandardMaterial).alphaTest).toBe(.45);
    expect((branches.material as THREE.MeshStandardMaterial).transparent).toBe(false);
    first.geometry.computeBoundingBox();
    expect(first.geometry.boundingBox!.max.y).toBeGreaterThan(16);
    expect(kit.prototypeBytes).toBeGreaterThan(0);
    const far = a.getObjectByName('alpine-far') as THREE.Mesh;
    expect(far).toBeInstanceOf(THREE.Mesh);
    const farMaterial = far.material as THREE.MeshStandardMaterial;
    expect(farMaterial.alphaTest).toBe(.45);
    expect(farMaterial.transparent).toBe(false);
    expect(farMaterial.depthWrite).toBe(true);
    expect(farMaterial.fog).toBe(true);
    expect(farMaterial.map!.flipY).toBe(false);
    const shader = { uniforms: {} };
    farMaterial.onBeforeCompile(shader as THREE.WebGLProgramParametersWithUniforms, {} as THREE.WebGLRenderer);
    expect(shader.uniforms).toHaveProperty('uFogFloor');
    expect(shader.uniforms).toHaveProperty('uGradeA');
    kit.release();
    expect(() => kit.cluster([placement])).toThrow('released');
  });

  it('leaves shared renderer neutral maps alive after completeMaterial injects them', async () => {
    stubMaps();
    vi.spyOn(GLTFLoader.prototype, 'loadAsync').mockImplementation(url => documentFor(url.includes('-lod') ? 'near' : 'full'));
    const neutral = new THREE.DataTexture(new Uint8Array([128,128,255,255]), 1, 1);
    const dispose = vi.spyOn(neutral, 'dispose');
    const kit = (await loadAlpineTreeKit({ assetRoot, completeMaterial(material) {
      for (const key of ['normalMap', 'roughnessMap', 'metalnessMap', 'aoMap', 'emissiveMap'] as const) {
        material[key] ??= neutral;
      }
    } }))!;
    kit.cluster([placement]); kit.release(); kit.release();
    expect(dispose).not.toHaveBeenCalled();
  });

  it('disposes both existing resources and a late document when aborted mid-load', async () => {
    stubMaps();
    const near = await documentFor('near'), full = await documentFor('full');
    let disposalCount = 0;
    for (const document of [near, full]) document.scene.traverse(object => {
      if (object instanceof THREE.Mesh) object.geometry.addEventListener('dispose', () => disposalCount++);
    });
    let finishFull!: (value: GLTF) => void;
    const fullPending = new Promise<GLTF>(resolve => { finishFull = resolve; });
    const load = vi.spyOn(GLTFLoader.prototype, 'loadAsync').mockResolvedValueOnce(near).mockReturnValueOnce(fullPending);
    const abort = new AbortController();
    const pending = loadAlpineTreeKit({ assetRoot, signal: abort.signal });
    await vi.waitFor(() => expect(load).toHaveBeenCalledTimes(2));
    abort.abort();
    expect(disposalCount).toBeGreaterThan(0);
    const beforeLate = disposalCount;
    finishFull(full);
    expect(await pending).toBeNull();
    expect(disposalCount).toBeGreaterThan(beforeLate);
  });

  it('cleans a successful first bank when the second bank fails', async () => {
    stubMaps();
    const near = await documentFor('near');
    let geometryDisposals = 0, textureDisposals = 0;
    near.scene.traverse(object => {
      if (!(object instanceof THREE.Mesh)) return;
      object.geometry.addEventListener('dispose', () => geometryDisposals++);
      (object.material as THREE.MeshStandardMaterial).map?.addEventListener('dispose', () => textureDisposals++);
    });
    vi.spyOn(GLTFLoader.prototype, 'loadAsync').mockResolvedValueOnce(near).mockRejectedValueOnce(new Error('network failed'));
    const onError = vi.fn();
    expect(await loadAlpineTreeKit({ assetRoot, onError })).toBeNull();
    expect(geometryDisposals).toBeGreaterThan(0);
    expect(textureDisposals).toBeGreaterThan(0);
    expect(onError).toHaveBeenCalledTimes(1);
  });

  it('rejects a resolved GLTF with an external map error, cleans it and preserves fallback', async () => {
    stubMaps();
    const near = await documentFor('near');
    let geometryDisposals = 0, textureDisposals = 0;
    near.scene.traverse(object => {
      if (!(object instanceof THREE.Mesh)) return;
      object.geometry.addEventListener('dispose', () => geometryDisposals++);
      (object.material as THREE.MeshStandardMaterial).map?.addEventListener('dispose', () => textureDisposals++);
    });
    const completeMaterial = vi.fn();
    const load = vi.spyOn(GLTFLoader.prototype, 'loadAsync').mockImplementation(function (this: GLTFLoader) {
      this.manager.itemError(`${assetRoot}models/course-kits/alpine-trees/cards-albedo.phone.webp`);
      return Promise.resolve(near);
    });
    const fallback = new THREE.Group();
    const report = vi.fn();
    const owner = mountCourseAssets(loadA1Forest(compileTrack(A1), { assetRoot, completeMaterial }), report);
    void owner.ready.then(() => { if (owner.root.children.length) fallback.visible = false; });
    await owner.ready;
    expect(load).toHaveBeenCalledTimes(1);
    expect(report).toHaveBeenCalledTimes(1);
    expect(completeMaterial).not.toHaveBeenCalled();
    expect(owner.root.children).toHaveLength(0);
    expect(owner.textureBytes).toBe(0);
    expect(fallback.visible).toBe(true);
    expect(geometryDisposals).toBeGreaterThan(0);
    expect(textureDisposals).toBeGreaterThan(0);
    owner.dispose();
  });

  it('delivers the parent course owner API and rejects failed deliveries', async () => {
    stubMaps();
    vi.spyOn(GLTFLoader.prototype, 'loadAsync').mockImplementation(url => documentFor(url.includes('-lod') ? 'near' : 'full'));
    const delivery = await loadAlpineTreeCourse([[placement]], { assetRoot });
    expect(delivery.root.name).toBe('alpine-authored-trees');
    expect(delivery.root.children).toHaveLength(1);
    expect(delivery.textureBytes).toBeCloseTo(6.333333333333333 * 1024 * 1024);
    delivery.dispose(); delivery.dispose();
    vi.mocked(GLTFLoader.prototype.loadAsync).mockRejectedValueOnce(new Error('missing pair'));
    await expect(loadAlpineTreeCourse([[placement]], { assetRoot })).rejects.toThrow('failed');
  });
});


describe('complete A1 forest', () => {
  const track = compileTrack(A1);
  const audit = JSON.parse(readFileSync(new URL('../../../../docs/evidence/course-remaster/alpine-tree-kit/a1-existing-tree-audit.json', import.meta.url), 'utf8')) as {
    allOriginalTreePlacements: { name: string; matrix: number[]; x: number; z: number }[];
  };
  function oldBatches(): PropBatch[] {
    const batches = new Map<string, PropBatch>();
    for (const row of audit.allOriginalTreePlacements) {
      const batch = batches.get(row.name) ?? new PropBatch(row.name, new THREE.BufferGeometry(), new THREE.MeshStandardMaterial());
      batch.items.push({ m: new THREE.Matrix4().fromArray(row.matrix), c: null }); batches.set(row.name, batch);
    }
    const shadow = new PropBatch('contactshadow', new THREE.BufferGeometry(), new THREE.MeshStandardMaterial());
    for (const row of audit.allOriginalTreePlacements) if (!row.name.startsWith('pinefar') && row.z > -20) {
      shadow.items.push({ m: new THREE.Matrix4().makeTranslation(row.x, 0, row.z), c: null });
    }
    shadow.items.push({ m: new THREE.Matrix4().makeTranslation(999, 0, -2), c: null });
    return [...batches.values(), shadow];
  }

  it('retains all audited anchors with exact ground and two bounded permanent far banks', () => {
    const plan = buildA1ForestPlan(track);
    const near = plan.nearClusters.flat(), far = plan.farBanks.flat();
    expect(near).toHaveLength(55); expect(far).toHaveLength(221); expect(plan.farBanks).toHaveLength(2);
    for (const tree of [...near, ...far]) {
      expect(tree.y).toBe(zoneGround('alpine', track.def.profile, tree.x, tree.z) - .04);
      expect(audit.allOriginalTreePlacements.some(row => Math.abs(row.x-tree.x)<1e-7 && Math.abs(row.z-tree.z)<1e-7)).toBe(true);
    }
    expect(new Set([...near, ...far].map(tree=>tree.variant)).size).toBe(10);
    expect(near.filter(tree=>tree.z>0).every(tree=>tree.variant.startsWith('sapling'))).toBe(true);
    expect(buildA1ForestPlan(track)).toEqual(plan);
  });

  it('removes all original trees/shadows while preserving other props and rejects changed builders atomically', () => {
    const batches = oldBatches();
    const count = removeA1ForestPlaceholders(batches, track);
    expect(count.near).toBe(55); expect(count.far).toBe(221); expect(count.shadows).toBeGreaterThan(0);
    expect(batches.filter(batch=>batch.name.startsWith('pine')).every(batch=>batch.items.length===0)).toBe(true);
    expect(batches.find(batch=>batch.name==='contactshadow')!.items).toHaveLength(1);
    const changed = oldBatches(); changed[0]!.items[0]!.m.elements[12] += .1;
    const before = changed.map(batch=>batch.items.length);
    expect(()=>removeA1ForestPlaceholders(changed, track)).toThrow('placement changed');
    expect(changed.map(batch=>batch.items.length)).toEqual(before);
  });

  it('loads far-only phone atlases without GLBs or prototypes and shares the far material', async () => {
    stubMaps();
    const models = vi.spyOn(GLTFLoader.prototype, 'loadAsync');
    const delivery = await loadA1Forest(track, { assetRoot, banks: 'far-only' });
    expect(models).not.toHaveBeenCalled();
    expect(THREE.TextureLoader.prototype.loadAsync).toHaveBeenCalledTimes(2);
    expect(delivery.textureBytes).toBeCloseTo(1.3333333333333333 * 1024 * 1024);
    expect(delivery.root.children).toHaveLength(3);
    let triangles = 0;
    const materials = new Set<THREE.Material>();
    delivery.root.traverse(object=>{
      if (!(object instanceof THREE.Mesh)) return;
      triangles += object.geometry.index!.count / 3; materials.add(object.material as THREE.Material);
    });
    expect(triangles).toBe(276*4); expect(materials.size).toBe(1);
    delivery.dispose();
  });

  it('loads one shared prototype pair for full forest and rejects mismatched tracks before loading', async () => {
    stubMaps();
    const models = vi.spyOn(GLTFLoader.prototype, 'loadAsync').mockImplementation(url=>documentFor(url.includes('-lod')?'near':'full'));
    const delivery = await loadA1Forest(track, { assetRoot });
    expect(models).toHaveBeenCalledTimes(2);
    let fullTrees = 0;
    const prototypes = new Map<string, THREE.BufferGeometry>();
    delivery.root.traverse(object=>{
      if (!(object instanceof THREE.InstancedMesh) || !object.name.startsWith('alpine-full-')) return;
      if (object.name.endsWith('-bark')) fullTrees += object.count;
      if (prototypes.has(object.name)) expect(object.geometry).toBe(prototypes.get(object.name));
      prototypes.set(object.name, object.geometry);
    });
    expect(fullTrees).toBe(55); delivery.dispose();
    const wrong = { ...track, hash: 'wrong' };
    await expect(loadA1Forest(wrong, { assetRoot })).rejects.toThrow('audited A1');
    expect(models).toHaveBeenCalledTimes(2);
  });
});
