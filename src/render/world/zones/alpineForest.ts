/** A2/A3 rollout candidate. Derive from actual seeded items, validate before removal.
 * A1 keeps its accepted static-anchor leaf. All courses reuse the same phone tree bank.
 * No extra model/maps, scene RNG, collider edits or hook activation here.
 */
import * as THREE from 'three';
import { StateHasher } from '../../../core/hash';
import type { CompiledTrack } from '../../../core/types';
import type { CourseAssetDelivery } from '../courseAssets';
import { PropBatch } from '../props';
import { zoneGround } from './zoneKit';
import { loadAlpineTreeKit, type AlpineTreeLoadOptions, type AlpineTreePlacement, type AlpineTreeVariant } from './alpineTrees';

interface TrackSpec { seed:number; hash:string; anchors:string; near:number; far:number; shadows:number; guards:readonly (readonly [number,number])[] }
const SPECS:Readonly<Record<string,TrackSpec>>={
  'a2-log-jam':{seed:3947357332,hash:'17aa87ab00450408',anchors:'cf9768f05ed6fb9b',near:51,far:215,shadows:27,
    guards:[[-10,61],[108,150.8],[186.8,248.8],[280,345.5],[371.5,401.5]]},
  'a3-timberline':{seed:849270865,hash:'0f8561baf09bd28e',anchors:'e347205b901b5490',near:59,far:209,shadows:39,
    guards:[[-10,53],[91,146],[171,211.2],[232.2,301.7],[323.7,353.7]]},
};
const HEIGHT:Readonly<Record<AlpineTreeVariant,number>>={
  'pine-a':22,'pine-b':17,'pine-c':26,'pine-young':13,'fir-a':24,'fir-b':30,
  'snag-a':14,'snag-b':10,'sapling-pine':3.2,'sapling-fir':4.5,
};
const TREE=/^pine(?:far)?\d$/;
export interface AlpineForestPlan {
  trackId:string; anchorHash:string; nearTrees:number; farTrees:number;
  nearClusters:readonly (readonly AlpineTreePlacement[])[];
  farBanks:readonly (readonly AlpineTreePlacement[])[];
}
export function alpineForestApplicable(track:CompiledTrack):boolean {
  const spec=SPECS[track.def.id];return !!spec&&spec.seed===track.def.seed&&spec.hash===track.hash;
}
function specOf(track:CompiledTrack):TrackSpec {
  if(!alpineForestApplicable(track)) throw new Error('Alpine forest requires the audited A2/A3 seed and collider hash');
  return SPECS[track.def.id]!;
}
/** Scene signatures use GPU Float32 precision: browser/Node trig can differ by one Float64 ULP.
 * Original double matrices/colours are retained unchanged for placement and fallback. */
export function alpineForestAnchorHash(batches:readonly PropBatch[]):string {
  const hash=new StateHasher();
  for(const batch of batches.filter(b=>TREE.test(b.name)).sort((a,b)=>a.name.localeCompare(b.name))) {
    hash.string(batch.name).number(batch.items.length);
    for(const {m,c} of batch.items) {
      for(const value of m.elements) hash.number(Math.fround(value));
      hash.bool(!!c);if(c) hash.number(Math.fround(c.r)).number(Math.fround(c.g)).number(Math.fround(c.b));
    }
  }
  return hash.digest();
}
function validated(track:CompiledTrack,batches:readonly PropBatch[]):TrackSpec {
  const spec=specOf(track),near=batches.filter(b=>TREE.test(b.name)&&!b.name.startsWith('pinefar')).reduce((n,b)=>n+b.items.length,0);
  const far=batches.filter(b=>b.name.startsWith('pinefar')&&TREE.test(b.name)).reduce((n,b)=>n+b.items.length,0);
  if(near!==spec.near||far!==spec.far||alpineForestAnchorHash(batches)!==spec.anchors) throw new Error(`${track.def.id}: seeded forest changed; retaining originals`);
  return spec;
}
export function planAlpineForest(track:CompiledTrack,batches:readonly PropBatch[]):AlpineForestPlan {
  const spec=validated(track,batches),clusters=new Map<string,AlpineTreePlacement[]>(),far:[AlpineTreePlacement[],AlpineTreePlacement[]]=[[],[]];
  const isA2=track.def.id==='a2-log-jam';
  for(const batch of batches.filter(b=>TREE.test(b.name))) batch.items.forEach(({m},index)=>{
    const x=m.elements[12]!,z=m.elements[14]!;
    let seed=(spec.seed^Math.imul(index+1,0x9e3779b1))>>>0;
    for(const char of batch.name)seed=Math.imul(seed^char.charCodeAt(0),16777619)>>>0;
    const t=(seed%1000)/999,guarded=spec.guards.some(([a,b])=>x>=a-3&&x<=b+3),bin=Math.floor(x/48);
    let variant:AlpineTreeVariant,height:number;
    if(batch.name.startsWith('pinefar')) {
      const palette:readonly AlpineTreeVariant[]=isA2?['pine-a','pine-b','fir-a','fir-b','pine-young']:['fir-a','pine-young','snag-a','pine-b','snag-b'];
      variant=palette[seed%palette.length]!;height=isA2?8+t*5:5+t*5;
    } else if(z>-14||(guarded&&z>-20)) {variant=seed%2?'sapling-pine':'sapling-fir';height=z>0?.9+t*.4:isA2?1.1+t*.4:.9+t*.4;}
    else {
      const palette:readonly AlpineTreeVariant[]=isA2?(bin%2?['pine-b','pine-young']:['fir-a','pine-b']):(bin%2?['fir-a','pine-young']:['pine-young','snag-a']);
      variant=palette[seed%palette.length]!;height=guarded?4.8+t*1.2:isA2?8+t*3:5.5+t*3;
    }
    const tree={variant,x,y:zoneGround('alpine',track.def.profile,x,z)-.04,z,scale:height/HEIGHT[variant],yaw:Math.atan2(m.elements[8]!,m.elements[0]!)};
    if(batch.name.startsWith('pinefar'))far[z<-49?1:0].push(tree);
    else {const key=`${bin}:${z>0?'front':'back'}`;const trees=clusters.get(key)??[];trees.push(tree);clusters.set(key,trees);}
  });
  return {trackId:track.def.id,anchorHash:spec.anchors,nearTrees:spec.near,farTrees:spec.far,nearClusters:[...clusters.values()],farBanks:far};
}
/** Return dedicated exact-item fallback batches; originals hide only after owner attachment.
 * Source family and shadow counts are checked before the first mutation.
 */
export function removeAlpineForestPlaceholders(track:CompiledTrack,batches:readonly PropBatch[]):{originals:PropBatch[];near:number;far:number;shadows:number} {
  const spec=validated(track,batches),near=batches.filter(b=>TREE.test(b.name)&&!b.name.startsWith('pinefar')).flatMap(b=>b.items);
  const removals=batches.flatMap(batch=>{
    const tree=TREE.test(batch.name),shadow=batch.name==='contactshadow';
    if(!tree&&!shadow)return [];
    const items=batch.items.filter(item=>tree||near.some(({m})=>Math.abs(m.elements[12]!-item.m.elements[12]!)<1e-7&&Math.abs(m.elements[14]!-item.m.elements[14]!)<1e-7));
    return items.length?[{batch,items}]:[];
  });
  const shadows=removals.filter(r=>r.batch.name==='contactshadow').reduce((n,r)=>n+r.items.length,0);
  if(shadows!==spec.shadows)throw new Error(`${track.def.id}: forest contact shadows changed; retaining originals`);
  const originals=removals.map(({batch,items})=>{
    const original=new PropBatch(`alpine-original-${batch.name}`,batch.geometry,batch.material,batch.shadows);
    original.items.push(...items);return original;
  });
  for(const {batch,items}of removals) {const removed=new Set(items);for(let i=batch.items.length-1;i>=0;i--)if(removed.has(batch.items[i]!))batch.items.splice(i,1);}
  return {originals,near:spec.near,far:spec.far,shadows};
}
/** Demand-load only the existing phone full/near/atlas bank, including required-map cleanup. */
export async function loadAlpineForest(plan:AlpineForestPlan,options:AlpineTreeLoadOptions={}):Promise<CourseAssetDelivery> {
  const kit=await loadAlpineTreeKit(options);if(!kit)throw new Error('Alpine forest assets failed or were cancelled');
  try {
    if(options.signal?.aborted)throw new Error('Alpine forest entry cancelled');
    const root=new THREE.Group();root.name=`${plan.trackId}-botanical-forest`;
    if(options.banks==='far-only')root.add(kit.farCluster(plan.nearClusters.flat()));else for(const trees of plan.nearClusters)root.add(kit.cluster(trees));
    for(const trees of plan.farBanks)root.add(kit.farCluster(trees));
    return {root,textureBytes:kit.textureBytes,dispose:kit.release};
  } catch(error) {kit.release();options.onError?.(error);throw error;}
}
