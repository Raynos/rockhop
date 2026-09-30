/** Unapplied C1 authored ground materials. Loader never changes live meshes.
 * Hidden carriers expose named owned materials to renderer.collectMaterials.
 */
import * as THREE from 'three';
import type { CourseAssetDelivery } from '../courseAssets';
import { modelResourceUrl } from '../../hero/urls';
import { fogify } from '../../lighting/environment';

export type CoastGroundSurface = 'top' | 'wall' | 'terrain';
type Channel = 'albedo' | 'normal' | 'arm';
export interface CoastGroundMap {
  surface: CoastGroundSurface;
  channel: Channel;
  file: string;
  width: number;
  height: number;
}
export const COAST_GROUND_MAPS: readonly CoastGroundMap[] = [
  ...(['albedo','normal','arm'] as const).map(channel=>({surface:'top' as const,channel,file:`quay-top-${channel}.phone.webp`,width:512,height:512})),
  ...(['albedo','normal','arm'] as const).map(channel=>({surface:'wall' as const,channel,file:`quay-wall-${channel}.phone.webp`,width:512,height:128})),
  ...(['albedo','normal','arm'] as const).map(channel=>({surface:'terrain' as const,channel,file:`tidal-ground-${channel}.phone.webp`,width:256,height:256})),
];
const PREFIX='models/course-kits/coast-ground/';
export const COAST_GROUND_MAPPING = {
  top: { existingUv:'arc/6,z/6', tileMetres:[12,6], repeat:[.5,1] },
  wall: { existingUv:'x/4,(profileY-y)/1.45', tileMetres:[12,1.45], repeat:[1/3,1] },
  terrain: { existingUv:'x/4,z/4', tileMetres:[8,8], repeat:[.5,.5] },
} as const;
/** Call only after confirming the course is C1. Obstacle/trim/water/site materials
 * intentionally do not match; top u is arc length, not exactly x on slopes.
 */
export function coastGroundSurface(name: string): CoastGroundSurface | null {
  if (/^zonedeck:top:coast:\d+$/.test(name)) return 'top';
  if (/^zonedeck:face:coast:\d+$/.test(name)) return 'wall';
  return name==='terrain' ? 'terrain' : null;
}
export interface CoastGroundMaterialOptions {
  assetRoot?: string;
  signal?: AbortSignal;
  /** Authoring server can resolve unpublished resources; production uses catalog. */
  resolveResource?: (logicalPath: string) => string;
  completeMaterial?: (material: THREE.MeshStandardMaterial) => void;
}
export interface CoastGroundMaterialDelivery extends CourseAssetDelivery {
  readonly materials: Readonly<Record<CoastGroundSurface,THREE.MeshStandardMaterial>>;
}
/** Nine mandatory source maps form one transaction. Completion/fog and neutral
 * maps are borrowed only after every required map resolves and validates.
 * Parent mounts carrier root, checks owner cancellation, then assigns materials
 * to exact target meshes. Preserve original materials for fallback/retirement.
 */
export async function loadCoastGroundMaterials(options: CoastGroundMaterialOptions = {}): Promise<CoastGroundMaterialDelivery> {
  const root=new THREE.Group();root.name='coast-ground-material-owner';
  const textures=new Set<THREE.Texture>();const materials=new Set<THREE.Material>();
  const failed=new Set<string>();const byMap=new Map<string,THREE.Texture>();
  const carrierGeometry=new THREE.BufferGeometry();let retired=false,carrierDisposed=false;
  const closed=new Set<unknown>();
  const clearOwned=():void=>{
    root.clear();
    for(const m of materials)m.dispose();materials.clear();
    for(const t of textures){t.dispose();const image=t.image as {close?:()=>void}|undefined;if(image?.close&&!closed.has(image)){closed.add(image);image.close();}}
    textures.clear();byMap.clear();
    if(!carrierDisposed){carrierDisposed=true;carrierGeometry.dispose();}
  };
  const dispose=():void=>{retired=true;options.signal?.removeEventListener('abort',dispose);clearOwned();};
  try{
    if(options.signal?.aborted)throw new Error('Coast ground cancelled');
    options.signal?.addEventListener('abort',dispose,{once:true});
    const assetRoot=options.assetRoot ?? new URL(import.meta.env.BASE_URL,document.baseURI).href;
    const manager=new THREE.LoadingManager();manager.onError=url=>{failed.add(url);};
    const loader=new THREE.TextureLoader(manager);
    const resolved=await Promise.allSettled(COAST_GROUND_MAPS.map(async map=>{
      const url=new URL((options.resolveResource ?? modelResourceUrl)(PREFIX+map.file),assetRoot).href;
      const texture=await loader.loadAsync(url);textures.add(texture);byMap.set(map.file,texture);
      // Wait for all sibling resolutions before final cleanup, including failed /
      // cancelled loads; late successful images still belong to this transaction.
      if(retired){clearOwned();return;}
      const image=texture.image as {width?:number;height?:number}|undefined;
      if(image?.width!==map.width||image?.height!==map.height)throw new Error(`Coast ground map dimensions mismatch: ${map.file}`);
      texture.name=`coast-ground:${map.file}`;texture.colorSpace=map.channel==='albedo'?THREE.SRGBColorSpace:THREE.NoColorSpace;
      texture.flipY=false;texture.wrapS=THREE.RepeatWrapping;
      texture.wrapT=map.surface==='wall'?THREE.ClampToEdgeWrapping:THREE.RepeatWrapping;
      texture.repeat.fromArray(COAST_GROUND_MAPPING[map.surface].repeat);texture.anisotropy=4;
      texture.minFilter=THREE.LinearMipmapLinearFilter;texture.magFilter=THREE.LinearFilter;texture.generateMipmaps=true;texture.needsUpdate=true;
    }));
    if(retired)throw new Error('Coast ground cancelled');
    if(failed.size)throw new Error(`Coast ground required maps failed: ${[...failed].join(', ')}`);
    const rejection=resolved.find(result=>result.status==='rejected');
    if(rejection?.status==='rejected')throw rejection.reason;
    const made={} as Record<CoastGroundSurface,THREE.MeshStandardMaterial>;
    for(const surface of ['top','wall','terrain'] as const){
      const maps=COAST_GROUND_MAPS.filter(map=>map.surface===surface);
      const get=(channel:Channel):THREE.Texture=>{
        const name=maps.find(map=>map.channel===channel)!.file;const texture=byMap.get(name);
        if(!texture)throw new Error(`Coast ground required map absent: ${name}`);return texture;
      };
      const material=fogify(new THREE.MeshStandardMaterial({color:0xffffff,vertexColors:true,roughness:1,metalness:0,envMapIntensity:.18,
        map:get('albedo'),normalMap:get('normal'),aoMap:get('arm'),roughnessMap:get('arm'),metalnessMap:get('arm')}));
      materials.add(material);material.name=`coast-ground-owned:${surface}`;
      material.normalScale.setScalar(surface==='top'?.65:surface==='wall'?.6:.45);
      material.aoMapIntensity=.45;
      options.completeMaterial?.(material);made[surface]=material;
      const carrier=new THREE.Mesh(carrierGeometry,material);carrier.name=`coast-ground-material-carrier:${surface}`;
      carrier.visible=false;carrier.frustumCulled=true;root.add(carrier);
    }
    // Identity-deduplicate source images; ARM is one image across three channels.
    const images=new Set<unknown>();let textureBytes=0;
    for(const texture of textures){const image=texture.image as {width:number;height:number};if(!images.has(image)){images.add(image);textureBytes+=image.width*image.height*4*4/3;}}
    return {root,materials:made,textureBytes:Math.round(textureBytes),dispose};
  }catch(error){dispose();throw error;}
}
