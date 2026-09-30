/** Node-only actual seeded builders. Canvas/art pixels are stubs, never visual evidence. */
import * as THREE from 'three';
import type { CompiledTrack } from '../../src/core/types';
import { MaterialLibrary } from '../../src/render/materials/library';
import { BIOMES } from '../../src/render/biomes';
import { buildBiomeKit } from '../../src/render/world/biomeKit';
import { PropBatch } from '../../src/render/world/props';
import type { ArtLibrary } from '../../src/render/art/library';
export function actualAlpineBatches(track:CompiledTrack):PropBatch[] {
  const previous=Object.getOwnPropertyDescriptor(globalThis,'document'),noop=()=>undefined,gradient={addColorStop:noop};
  const context=new Proxy<Record<string,unknown>>({}, {get(target,key){
    if(key in target)return target[String(key)];
    if(key==='createLinearGradient'||key==='createRadialGradient')return ()=>gradient;
    if(key==='getImageData'||key==='createImageData')return (_x:number,_y:number,w:number,h:number)=>({data:new Uint8ClampedArray((w??_x)*(h??_y)*4)});
    if(key==='measureText')return ()=>({width:100});return noop;
  }});
  Object.defineProperty(globalThis,'document',{value:{createElement:()=>({width:0,height:0,getContext:()=>context})},configurable:true});
  const dummy=new THREE.DataTexture(new Uint8Array([128,128,128,255]),1,1),art={texture:()=>dummy,entry:()=>({bytes:0}),has:()=>true,bitmap:()=>({width:512,height:512})}as unknown as ArtLibrary;
  // buildBatches splits foreground items in place. Snapshot at add-time, before that split.
  const batches=new Map<PropBatch,PropBatch['items']>(),add=PropBatch.prototype.add;
  PropBatch.prototype.add=function(...args:Parameters<typeof add>){add.apply(this,args);const items=batches.get(this)??[];items.push(this.items[this.items.length-1]!);batches.set(this,items);};
  try {buildBiomeKit(track,BIOMES.alpine,new MaterialLibrary(track.def.seed),art,'low',false);}
  finally {PropBatch.prototype.add=add;if(previous)Object.defineProperty(globalThis,'document',previous);else Reflect.deleteProperty(globalThis,'document');}
  return [...batches].map(([batch,items])=>{const source=new PropBatch(batch.name,batch.geometry,batch.material,batch.shadows);source.items.push(...items);return source;});
}
