import { createHash } from 'node:crypto';
import { readFileSync } from 'node:fs';
import * as THREE from 'three';
import { afterEach,describe,expect,it,vi } from 'vitest';
import { COAST_GROUND_MAPS,COAST_GROUND_MAPPING,coastGroundSurface,loadCoastGroundMaterials } from './coastGroundMaterials';
import { mountCourseAssets } from '../courseAssets';
import { fogUniforms } from '../../lighting/environment';
const options={assetRoot:'https://game.example/subpath/',resolveResource:(s:string)=>s.replace('/coast-ground/','/coast-ground/byte-hash/')};
function textureFor(url:string):THREE.Texture<HTMLImageElement>{
  const map=COAST_GROUND_MAPS.find(map=>url.endsWith(map.file))!;
  const t=new THREE.Texture({width:map.width,height:map.height} as HTMLImageElement);return t;
}
afterEach(()=>vi.restoreAllMocks());
describe('C1 authored ground map transaction',()=>{
  it('maps only exact top/wall/terrain families, preserving all hazard and trim materials',()=>{
    expect(coastGroundSurface('zonedeck:top:coast:12')).toBe('top');expect(coastGroundSurface('zonedeck:face:coast:0')).toBe('wall');expect(coastGroundSurface('terrain')).toBe('terrain');
    for(const name of ['deck:zone:top:3','deck:rustSteel:4','obstacles:container','zone:sea','coast-harbor-site:4','zonedeck:top:alpine:0','zonedeck:top:coast:bad'])expect(coastGroundSurface(name)).toBeNull();
  });
  it('loads exactly nine required maps through hashed subpath URLs at truthful scale',async()=>{
    const load=vi.spyOn(THREE.TextureLoader.prototype,'loadAsync').mockImplementation(async url=>textureFor(url));
    const delivery=await loadCoastGroundMaterials(options);
    expect(load).toHaveBeenCalledTimes(9);expect(load.mock.calls.every(([url])=>url.startsWith(options.assetRoot+'models/course-kits/coast-ground/byte-hash/'))).toBe(true);
    expect(delivery.textureBytes).toBe(6*1048576);
    for(const [surface,m] of Object.entries(delivery.materials)){
      expect(m.vertexColors).toBe(true);expect(m.map!.colorSpace).toBe(THREE.SRGBColorSpace);expect(m.normalMap!.colorSpace).toBe(THREE.NoColorSpace);
      expect(m.map!.repeat.toArray()).toEqual(COAST_GROUND_MAPPING[surface as keyof typeof COAST_GROUND_MAPPING].repeat);
      expect(m.map!.flipY).toBe(false);expect(m.roughnessMap).toBe(m.metalnessMap);expect(m.aoMap).toBe(m.roughnessMap);
    }
    expect(delivery.materials.wall.map!.wrapT).toBe(THREE.ClampToEdgeWrapping);expect(delivery.materials.top.map!.wrapT).toBe(THREE.RepeatWrapping);
    delivery.dispose();
  });
  it('makes owned materials visible to traverse-based retirement without adding draws',async()=>{
    vi.spyOn(THREE.TextureLoader.prototype,'loadAsync').mockImplementation(async url=>textureFor(url));
    const delivery=await loadCoastGroundMaterials(options);const found=new Set<THREE.Material>();
    delivery.root.traverse(o=>{if(o instanceof THREE.Mesh){expect(o.visible).toBe(false);expect(o.geometry.getAttribute('position')).toBeUndefined();found.add(o.material as THREE.Material);}});
    expect(found.size).toBe(3);for(const m of Object.values(delivery.materials))expect(found.has(m)).toBe(true);
    delivery.dispose();
  });
  it('keeps borrowed completion maps alive, retires authored textures once, and preserves fog chain',async()=>{
    const own:THREE.Texture[]=[];vi.spyOn(THREE.TextureLoader.prototype,'loadAsync').mockImplementation(async url=>{const t=textureFor(url);own.push(t);return t;});
    const neutral=new THREE.Texture(),neutralDispose=vi.spyOn(neutral,'dispose');
    const delivery=await loadCoastGroundMaterials({...options,completeMaterial(m){m.emissiveMap=neutral;}});
    const spies=own.map(t=>vi.spyOn(t,'dispose'));const shader={uniforms:{}};
    delivery.materials.top.onBeforeCompile(shader as THREE.WebGLProgramParametersWithUniforms,{} as THREE.WebGLRenderer);
    expect(shader.uniforms).toHaveProperty('uFogFloor',fogUniforms.uFogFloor);
    delivery.dispose();delivery.dispose();for(const spy of spies)expect(spy).toHaveBeenCalledOnce();expect(neutralDispose).not.toHaveBeenCalled();
  });
  it('rejects a manager-reported required-map error even when image loader resolves',async()=>{
    const own:THREE.Texture[]=[];vi.spyOn(THREE.TextureLoader.prototype,'loadAsync').mockImplementation(async function(this:THREE.TextureLoader,url){const t=textureFor(url);own.push(t);if(url.includes('quay-wall-normal'))this.manager.itemError(url);return t;});
    const complete=vi.fn(),report=vi.fn();const oldMaterial=new THREE.MeshStandardMaterial();
    const mesh=new THREE.Mesh(new THREE.BoxGeometry(),oldMaterial);
    const owner=mountCourseAssets(loadCoastGroundMaterials({...options,completeMaterial:complete}),report);
    await owner.ready;expect(owner.root.children).toHaveLength(0);expect(mesh.material).toBe(oldMaterial);expect(complete).not.toHaveBeenCalled();expect(report).toHaveBeenCalledOnce();owner.dispose();
    expect(own).toHaveLength(9);
  });
  it('cleans sibling image successes after a rejection and rejects malformed image dimensions',async()=>{
    const own:THREE.Texture[]=[];const spies:ReturnType<typeof vi.spyOn>[]=[];
    vi.spyOn(THREE.TextureLoader.prototype,'loadAsync').mockImplementation(async url=>{if(url.includes('wall-arm'))throw new Error('404');const t=textureFor(url);own.push(t);spies.push(vi.spyOn(t,'dispose'));return t;});
    await expect(loadCoastGroundMaterials(options)).rejects.toThrow('404');expect(own).toHaveLength(8);for(const spy of spies)expect(spy).toHaveBeenCalledOnce();
    vi.restoreAllMocks();vi.spyOn(THREE.TextureLoader.prototype,'loadAsync').mockImplementation(async url=>{const t=textureFor(url);if(url.includes('top-normal'))t.image={width:1,height:1} as HTMLImageElement;return t;});
    await expect(loadCoastGroundMaterials(options)).rejects.toThrow('dimensions mismatch');
  });
  it('owns and disposes every late map on cancellation without scene attachment',async()=>{
    let finish!:(t:ReturnType<typeof textureFor>)=>void;const late=new Promise<ReturnType<typeof textureFor>>(resolve=>{finish=resolve;});
    const delayed=textureFor('quay-top-normal.phone.webp');const close=vi.fn();Object.assign(delayed.image,{close});const td=vi.spyOn(delayed,'dispose');
    const load=vi.spyOn(THREE.TextureLoader.prototype,'loadAsync').mockImplementation(async url=>url.includes('top-normal')?late:textureFor(url));
    const abort=new AbortController(),report=vi.fn();const owner=mountCourseAssets(loadCoastGroundMaterials({...options,signal:abort.signal}),report);
    await vi.waitFor(()=>expect(load).toHaveBeenCalledTimes(9));owner.cancel();abort.abort();finish(delayed);await owner.ready;
    expect(owner.root.children).toHaveLength(0);expect(td).toHaveBeenCalledOnce();expect(close).toHaveBeenCalledOnce();expect(report).toHaveBeenCalledOnce();owner.dispose();
  });
  it('cleans source maps/materials when completion throws and closes shared bitmaps once',async()=>{
    const image={width:512,height:512,close:vi.fn()};const own:THREE.Texture[]=[];
    vi.spyOn(THREE.TextureLoader.prototype,'loadAsync').mockImplementation(async url=>{const t=textureFor(url);if(url.includes('quay-top'))t.image=image as unknown as HTMLImageElement;own.push(t);return t;});
    const mats:THREE.Material[]=[];
    await expect(loadCoastGroundMaterials({...options,completeMaterial(m){mats.push(m);throw new Error('failed complete');}})).rejects.toThrow('failed complete');
    expect(image.close).toHaveBeenCalledOnce();expect(own).toHaveLength(9);expect(mats).toHaveLength(1);
  });
  it('delivers immutable compressed maps matching exact byte hashes and declared pixel sizes',()=>{
    const base=new URL('../../../../assets/blender/course-kits/coast-ground/delivery/',import.meta.url);
    const manifest=JSON.parse(readFileSync(new URL('manifest.json',base),'utf8')) as {files:{file:string;sha256:string;width:number;height:number;bytes:number}[]};
    expect(manifest.files).toHaveLength(9);
    for(const file of manifest.files){const bytes=readFileSync(new URL(file.file,base));expect(bytes.length).toBe(file.bytes);expect(createHash('sha256').update(bytes).digest('hex')).toBe(file.sha256);expect(bytes.subarray(8,12).toString()).toBe('WEBP');const map=COAST_GROUND_MAPS.find(m=>m.file===file.file)!;expect([file.width,file.height]).toEqual([map.width,map.height]);}
  });
});
