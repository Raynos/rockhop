/** Refresh leaf-only source proposal from current builders; no browser/build/public writes. */
import fs from 'node:fs';
import {createHash} from 'node:crypto';
import {A2,A3} from '../../../../src/tracks/rockhop/alpine';
import {compileTrack} from '../../../../src/tracks/compile';
import {alpineForestAnchorHash,planAlpineForest} from '../../../../src/render/world/zones/alpineForest';
import {actualAlpineBatches} from '../../../../harness/fixtures/alpine-rollout';
const prototypes=JSON.parse(fs.readFileSync(new URL('../../../../docs/evidence/course-remaster/alpine-tree-kit/build-report.json',import.meta.url),'utf8')) as {variants:{file:string;meshes:{name:string;triangles:number}[]}[]};
const triangles=(level:'full'|'near',variant:string)=>prototypes.variants.find(v=>v.file===`trees-${level}.phone.glb`)!.meshes.filter(m=>m.name.startsWith(`${variant}__`)).reduce((n,m)=>n+m.triangles,0);
const rows=[A2,A3].map(def=>{
  const track=compileTrack(def),batches=actualAlpineBatches(track);
  const plan=planAlpineForest(track,batches);
  const clusters=plan.nearClusters.map(trees=>({trees:trees.length,x:trees.reduce((n,t)=>n+t.x,0)/trees.length,
    draws:2*new Set(trees.map(t=>t.variant)).size,full:trees.reduce((n,t)=>n+triangles('full',t.variant),0),near:trees.reduce((n,t)=>n+triangles('near',t.variant),0),far:trees.length*4}));
  const maxima={draws:0,triangles:0,shadowDraws:0,detailedClusters:0};
  for(let x=track.bounds.minX-100;x<track.bounds.maxX+100;x+=.5) {
    let draws=2,tris=plan.farTrees*4,shadows=0,detailed=0;
    for(const cluster of clusters) {
      const distance=Math.abs(x-cluster.x),level=distance<26?'full':distance<65?'near':'far';
      draws+=level==='far'?1:cluster.draws;tris+=cluster[level];
      if(level==='full')shadows+=cluster.draws;if(level!=='far')detailed++;
    }
    maxima.draws=Math.max(maxima.draws,draws);maxima.triangles=Math.max(maxima.triangles,tris);maxima.shadowDraws=Math.max(maxima.shadowDraws,shadows);maxima.detailedClusters=Math.max(maxima.detailedClusters,detailed);
  }
  return {id:def.id,seed:def.seed,trackHash:track.hash,anchorHash:alpineForestAnchorHash(batches),
    near:batches.filter(b=>/^pine\d$/.test(b.name)).reduce((n,b)=>n+b.items.length,0),far:batches.filter(b=>/^pinefar\d$/.test(b.name)).reduce((n,b)=>n+b.items.length,0),
    clusters,maxima,farOnly:{draws:3,triangles:(plan.nearTrees+plan.farTrees)*4},
    bank:{additionalPublicBytes:0,sharedPhoneMapsMiB:6.333333333333333},
    limits:['Conservative x-only LOD selection; excludes frustum/tier benefits and original-family removal credits.','Draws are forest main-pass bounds, not total renderer calls; shadow pass maximum reported separately.','CPU Canvas/art stubs cannot establish actual moving art, frame timing or device cost.']};
});
const report={nodeOnly:true,pixelsStubbed:true,tracks:rows,sources:Object.fromEntries(['src/render/world/biomeKit.ts','src/render/world/zones/zoneKit.ts','src/render/world/zones/geo.ts','src/tracks/rockhop/alpine.ts'].map(file=>[file,createHash('sha256').update(fs.readFileSync(file)).digest('hex')]))};
fs.mkdirSync(new URL('./rollout/',import.meta.url),{recursive:true});fs.writeFileSync(new URL('./rollout/anchor-audit.json',import.meta.url),JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify(rows,null,2));
