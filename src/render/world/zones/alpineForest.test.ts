import * as THREE from 'three';
import {describe,it,expect,vi,beforeEach} from 'vitest';
import {A2,A3} from '../../../tracks/rockhop/alpine';
import {compileTrack} from '../../../tracks/compile';
// CI excludes the Blender authoring tree; keep this shared seeded fixture in harness.
import {actualAlpineBatches} from '../../../../harness/fixtures/alpine-rollout';
import {PropBatch} from '../props';
import {zoneGround} from './zoneKit';
import {alpineForestApplicable,planAlpineForest,removeAlpineForestPlaceholders,loadAlpineForest} from './alpineForest';
import {loadAlpineTreeKit} from './alpineTrees';
import {mountCourseAssets} from '../courseAssets';
vi.mock('./alpineTrees',()=>({loadAlpineTreeKit:vi.fn()}));
const fixtures=[A2,A3].map(def=>({track:compileTrack(def),batches:actualAlpineBatches(compileTrack(def))}));
function copy(batches:readonly PropBatch[]) {
  return batches.map(batch=>{const cloned=new PropBatch(batch.name,batch.geometry,batch.material,batch.shadows);cloned.items.push(...batch.items.map(({m,c})=>({m:m.clone(),c:c?.clone()??null})));return cloned;});
}
beforeEach(()=>vi.mocked(loadAlpineTreeKit).mockReset());
describe('complete A2/A3 forest rollout candidate',()=>{
  it.each(fixtures)('uses exact audited source anchors and truthful ground contact: $track.def.id',({track,batches})=>{
    const plan=planAlpineForest(track,batches),trees=[...plan.nearClusters.flat(),...plan.farBanks.flat()];
    expect(alpineForestApplicable(track)).toBe(true);expect(trees).toHaveLength(track.def.id==='a2-log-jam'?266:268);
    for(const tree of trees) {
      expect(tree.y).toBe(zoneGround('alpine',track.def.profile,tree.x,tree.z)-.04);
      expect([tree.x,tree.y,tree.z,tree.scale,tree.yaw].every(Number.isFinite)).toBe(true);
    }
    expect(planAlpineForest(track,[...batches].reverse())).toMatchObject({anchorHash:plan.anchorHash,nearTrees:plan.nearTrees,farTrees:plan.farTrees});
    expect(planAlpineForest(track,batches)).toEqual(plan);
  });
  it.each(fixtures)('removes the entire original family with dedicated identical fallback items: $track.def.id',({track,batches})=>{
    const source=copy(batches),originalTrees=source.filter(b=>/^pine(?:far)?\d$/.test(b.name)).flatMap(b=>b.items),oldTotal=source.reduce((n,b)=>n+b.items.length,0);
    const removed=removeAlpineForestPlaceholders(track,source),fallbackTrees=removed.originals.filter(b=>b.name.startsWith('alpine-original-pine')).flatMap(b=>b.items);
    expect(fallbackTrees).toEqual(originalTrees);expect(fallbackTrees.every(item=>originalTrees.includes(item))).toBe(true);
    expect(source.filter(b=>/^pine(?:far)?\d$/.test(b.name)).every(b=>b.items.length===0)).toBe(true);
    expect(oldTotal-source.reduce((n,b)=>n+b.items.length,0)).toBe(removed.near+removed.far+removed.shadows);
    for(const fallback of removed.originals) {
      const original=source.find(b=>`alpine-original-${b.name}`===fallback.name)!;
      expect(fallback.geometry).toBe(original.geometry);expect(fallback.material).toBe(original.material);
    }
  });
  it('accepts sub-GPU trig rounding while preserving original source matrices',()=>{
    const {track,batches}=fixtures[0]!,source=copy(batches),matrix=source.find(b=>/^pine\d$/.test(b.name))!.items[0]!.m;
    const original=matrix.elements[0]!;matrix.elements[0]=original+Number.EPSILON;
    expect(planAlpineForest(track,source).nearTrees).toBe(51);
    expect(matrix.elements[0]).toBe(original+Number.EPSILON);
  });
  it('rejects any changed tree before mutating any original item',()=>{
    const {track,batches}=fixtures[0]!,source=copy(batches);source.find(b=>/^pine\d$/.test(b.name))!.items[0]!.m.elements[12]!+=.001;
    const counts=source.map(b=>b.items.length);expect(()=>removeAlpineForestPlaceholders(track,source)).toThrow('retaining originals');expect(source.map(b=>b.items.length)).toEqual(counts);
  });
  it('rejects a missing contact shadow before tree removal',()=>{
    const {track,batches}=fixtures[0]!,source=copy(batches),near=source.filter(b=>/^pine\d$/.test(b.name)).flatMap(b=>b.items);
    const shadow=source.find(b=>b.name==='contactshadow'&&b.items.some(i=>near.some(n=>n.m.elements[12]===i.m.elements[12]&&n.m.elements[14]===i.m.elements[14])))!;
    const index=shadow.items.findIndex(i=>near.some(n=>n.m.elements[12]===i.m.elements[12]&&n.m.elements[14]===i.m.elements[14]));shadow.items.splice(index,1);
    const counts=source.map(b=>b.items.length);expect(()=>removeAlpineForestPlaceholders(track,source)).toThrow('contact shadows changed');expect(source.map(b=>b.items.length)).toEqual(counts);
  });
  it('requires the exact audited seed and collider signature',()=>{
    const {track,batches}=fixtures[0]!;expect(alpineForestApplicable({...track,hash:'changed'})).toBe(false);
    expect(()=>planAlpineForest({...track,def:{...track.def,seed:1}},batches)).toThrow('audited A2/A3');
  });
  it('keeps close foreground regrowth below 1.3m and groups far trees into two banks',()=>{
    for(const {track,batches}of fixtures) {
      const plan=planAlpineForest(track,batches);expect(plan.farBanks).toHaveLength(2);
      for(const tree of plan.nearClusters.flat().filter(t=>t.z>0)) {
        expect(tree.variant.startsWith('sapling')).toBe(true);expect(tree.scale!*(tree.variant==='sapling-pine'?3.2:4.5)).toBeLessThanOrEqual(1.3);
      }
    }
  });
  it('returns a far-only delivery using the same kit and release contract',async()=>{
    const {track,batches}=fixtures[0]!,plan=planAlpineForest(track,batches),release=vi.fn(),cluster=vi.fn(),farCluster=vi.fn(()=>new THREE.Group());
    vi.mocked(loadAlpineTreeKit).mockResolvedValue({release,cluster,farCluster,prototypeBytes:0,textureBytes:1});
    const delivery=await loadAlpineForest(plan,{banks:'far-only'});expect(cluster).not.toHaveBeenCalled();expect(farCluster).toHaveBeenCalledTimes(3);expect(delivery.root.children).toHaveLength(3);delivery.dispose();expect(release).toHaveBeenCalledTimes(1);
  });
  it('releases a resolved bank if entry was aborted before construction',async()=>{
    const {track,batches}=fixtures[0]!,plan=planAlpineForest(track,batches),release=vi.fn(),controller=new AbortController();controller.abort();
    vi.mocked(loadAlpineTreeKit).mockResolvedValue({release,cluster:vi.fn(),farCluster:vi.fn(),prototypeBytes:0,textureBytes:1});
    await expect(loadAlpineForest(plan,{signal:controller.signal})).rejects.toThrow('cancelled');expect(release).toHaveBeenCalledTimes(1);
  });
  it('rejects a failed kit without mounting or hiding fallback',async()=>{
    const {track,batches}=fixtures[0]!,plan=planAlpineForest(track,batches);vi.mocked(loadAlpineTreeKit).mockResolvedValue(null);
    const owner=mountCourseAssets(loadAlpineForest(plan),()=>undefined);await owner.ready;expect(owner.root.children).toHaveLength(0);
  });
});
