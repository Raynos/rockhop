import * as THREE from 'three';
import { GLTFLoader, type GLTF } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { afterEach, describe, expect, it, vi } from 'vitest';
import { COAST_HARBOR_VARIANTS, coastHarborResourceUrl, loadCoastHarbor, planC1Harbor } from '../../../../src/render/world/zones/coastHarbor';
import { mountCourseAssets } from '../../../../src/render/world/courseAssets';
const assetRoot = 'https://game.example/subpath/';
const options = { assetRoot, resolveModel: (s: string) => s, resolveResource: (s: string) => s };
const placement = { variant: 'cargo-freighter' as const, x: 12, y: -2.8, z: -60, scale: .9, yaw: .03 };
function documentFor(): GLTF {
  const scene = new THREE.Group();
  const material = new THREE.MeshStandardMaterial(); material.name = 'coast manufactured PBR atlas';
  material.map = new THREE.DataTexture(new Uint8Array([100,110,120,255]),1,1);
  material.normalMap = new THREE.DataTexture(new Uint8Array([128,128,255,255]),1,1);
  material.roughnessMap = new THREE.DataTexture(new Uint8Array([255,180,90,255]),1,1); material.metalnessMap = material.roughnessMap;
  for (const variant of COAST_HARBOR_VARIANTS) {
    const group = new THREE.Group(); group.name = variant;
    group.add(new THREE.Mesh(new THREE.BoxGeometry(2,2,2),material)); scene.add(group);
  }
  return { scene, scenes: [scene], animations: [], cameras: [], asset: { version: '2.0' } } as unknown as GLTF;
}
afterEach(() => vi.restoreAllMocks());
describe('Coast authored leaf lifecycle', () => {
  it('resolves only explicit maps through hashed subpath/store catalog URLs', () => {
    const hash = (s: string) => s.replace('/coast-albedo.phone.webp','/abc/coast-albedo.phone-abc.webp');
    expect(coastHarborResourceUrl('https://game.example/subpath/models/hash/coast-albedo.phone.webp',assetRoot,hash))
      .toBe(assetRoot+'models/course-kits/coast-harbor/abc/coast-albedo.phone-abc.webp');
    expect(coastHarborResourceUrl('unknown.png',assetRoot,hash)).toBe('unknown.png');
    expect(coastHarborResourceUrl('coast-albedo.phone.webp','capacitor://localhost/',hash))
      .toBe('capacitor://localhost/models/course-kits/coast-harbor/abc/coast-albedo.phone-abc.webp');
  });
  it('shares each decoded prototype between cells, loading one phone bank', async () => {
    const load = vi.spyOn(GLTFLoader.prototype,'loadAsync').mockResolvedValue(documentFor());
    const delivery = await loadCoastHarbor([placement,{...placement,x:15},{...placement,x:100}],options);
    const meshes = delivery.root.children as THREE.InstancedMesh[];
    expect(meshes).toHaveLength(2); expect(meshes[0]!.count).toBe(2); expect(meshes[0]!.geometry).toBe(meshes[1]!.geometry);
    expect(meshes[0]!.material).toBe(meshes[1]!.material); expect(load).toHaveBeenCalledTimes(1);
    expect(load.mock.calls[0]![0]).toContain('coast-harbor-lod.glb');
    expect(delivery.textureBytes).toBe(16); delivery.dispose(); delivery.dispose(); expect(delivery.root.children).toHaveLength(0);
  });
  it('retains library neutral maps and closes shared decoded images once', async () => {
    const gltf=documentFor(); const material=(gltf.scene.children[0]!.children[0] as THREE.Mesh).material as THREE.MeshStandardMaterial;
    const owned=material.map!; const disposal=vi.spyOn(owned,'dispose');
    const image={width:1,height:1,close:vi.fn()}; owned.image=image; material.normalMap!.image=image;
    const neutral = new THREE.DataTexture(); const neutralDispose=vi.spyOn(neutral,'dispose');
    vi.spyOn(GLTFLoader.prototype,'loadAsync').mockResolvedValue(gltf);
    const asset=await loadCoastHarbor([placement],{...options,completeMaterial(m){m.aoMap=neutral;m.emissiveMap=neutral;}});
    asset.dispose();asset.dispose(); expect(neutralDispose).not.toHaveBeenCalled();expect(disposal).toHaveBeenCalledTimes(1);expect(image.close).toHaveBeenCalledTimes(1);
  });
  it('rejects a resolved GLTF whose manager reported a mandatory map failure', async () => {
    const gltf=documentFor(); const geometry=(gltf.scene.children[0]!.children[0] as THREE.Mesh).geometry;const dispose=vi.spyOn(geometry,'dispose');
    vi.spyOn(GLTFLoader.prototype,'loadAsync').mockImplementation(async function(this: GLTFLoader){this.manager.itemError('coast-normal.phone.webp');return gltf;});
    const complete=vi.fn(), report=vi.fn(); const original=new THREE.Group();original.name='original-harbor';
    const owner=mountCourseAssets(loadCoastHarbor([placement],{...options,completeMaterial:complete}),report);
    await owner.ready;expect(owner.root.children).toHaveLength(0);expect(original.visible).toBe(true);expect(report).toHaveBeenCalledOnce();expect(complete).not.toHaveBeenCalled();expect(dispose).toHaveBeenCalledOnce();owner.dispose();
  });
  it('does not allow library complete to replace an absent source PBR map', async () => {
    const gltf=documentFor();const material=(gltf.scene.children[0]!.children[0] as THREE.Mesh).material as THREE.MeshStandardMaterial;material.normalMap=null;
    vi.spyOn(GLTFLoader.prototype,'loadAsync').mockResolvedValue(gltf); const complete=vi.fn();
    await expect(loadCoastHarbor([placement],{...options,completeMaterial:complete})).rejects.toThrow('PBR map missing');expect(complete).not.toHaveBeenCalled();
  });
  it('cleans a late resolution after A1-like course cancellation without attachment', async () => {
    const gltf=documentFor();const geometry=(gltf.scene.children[0]!.children[0] as THREE.Mesh).geometry;const dispose=vi.spyOn(geometry,'dispose');
    let finish!: (gltf:GLTF)=>void;const pending=new Promise<GLTF>(resolve=>{finish=resolve;});
    const load=vi.spyOn(GLTFLoader.prototype,'loadAsync').mockReturnValue(pending); const controller=new AbortController();
    const report=vi.fn();const owner=mountCourseAssets(loadCoastHarbor([placement],{...options,signal:controller.signal}),report);
    await vi.waitFor(()=>expect(load).toHaveBeenCalledOnce());owner.cancel();controller.abort();finish(gltf);await owner.ready;
    expect(owner.root.children).toHaveLength(0);expect(dispose).toHaveBeenCalledOnce();expect(report).toHaveBeenCalledOnce();owner.dispose();
  });
  it('cleans malformed prototype documents and invalid matrices', async () => {
    const gltf=documentFor(); gltf.scene.children[0]!.name='unknown';
    const dispose=vi.spyOn((gltf.scene.children[0]!.children[0] as THREE.Mesh).geometry,'dispose');
    vi.spyOn(GLTFLoader.prototype,'loadAsync').mockResolvedValueOnce(gltf).mockResolvedValueOnce(documentFor());
    await expect(loadCoastHarbor([placement],options)).rejects.toThrow('Unknown');expect(dispose).toHaveBeenCalledOnce();
    await expect(loadCoastHarbor([{...placement,x:NaN}],options)).rejects.toThrow('Invalid');
  });
  it('cleans already owned resources if completeMaterial fails', async () => {
    const gltf=documentFor();const dispose=vi.spyOn((gltf.scene.children[0]!.children[0] as THREE.Mesh).geometry,'dispose');
    vi.spyOn(GLTFLoader.prototype,'loadAsync').mockResolvedValue(gltf);
    await expect(loadCoastHarbor([placement],{...options,completeMaterial(){throw Error('complete failed');}})).rejects.toThrow('complete failed');expect(dispose).toHaveBeenCalledOnce();
  });
  it('builds a pure entire C1 plan with no tall actor in the brake reading window', () => {
    const plan=planC1Harbor((x,z)=>x*.001+z*.001,-2.82);expect(plan).toHaveLength(52);
    expect(planC1Harbor((x,z)=>x*.001+z*.001,-2.82)).toEqual(plan);
    for(const p of plan){expect(p.x<180||p.x>260||p.z<=-90).toBe(true);expect([p.x,p.y,p.z].every(Number.isFinite)).toBe(true);}
    expect(plan.find(p=>p.variant==='cargo-freighter')!.y).toBe(-2.82);
    expect(plan.find(p=>p.variant==='open-warehouse')!.y).toBeCloseTo(.0222);
  });
});
