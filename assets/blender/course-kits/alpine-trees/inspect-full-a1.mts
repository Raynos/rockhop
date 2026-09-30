/** Exact placement/LOD construction bounds; no browser, no shared dist build. */
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { compileTrack } from '../../../../src/tracks/compile';
import { A1 } from '../../../../src/tracks/rockhop/alpine';
import { buildA1ForestPlan } from '../../../../src/render/world/zones/a1Forest';
const plan = buildA1ForestPlan(compileTrack(A1));
const metadata = JSON.parse(readFileSync(new URL('./build/trees.json',import.meta.url),'utf8')) as { variants: { name: string; triangles: Record<string,number> }[] };
const tris = new Map(metadata.variants.map(v=>[v.name,v.triangles]));
const clusters = plan.nearClusters.map((trees,i)=>({
  cluster:i, trees:trees.length, centreX:trees.reduce((sum,t)=>sum+t.x,0)/trees.length,
  centreZ:trees.reduce((sum,t)=>sum+t.z,0)/trees.length,
  widthX:Math.max(...trees.map(t=>t.x))-Math.min(...trees.map(t=>t.x)),
  draws:2*new Set(trees.map(t=>t.variant)).size,
  triangles:Object.fromEntries(['full','near','far'].map(level=>[level,trees.reduce((sum,t)=>sum+tris.get(t.variant)![level]!,0)])),
}));
const events = [...new Set(clusters.flatMap(c=>[-65,-26,26,65].map(offset=>c.centreX+offset)))].sort((a,b)=>a-b);
const samples = [events[0]!-1,events.at(-1)!+1,...events.slice(1).map((value,i)=>(value+events[i]!)/2)];
let maxDraws=0,maxFull=0,maxActive=0,maxTriangles=0,maxShadow=0;
for (const x of samples) {
  let draws=plan.farBanks.length,full=0,active=0,triangles=221*4,shadow=0;
  for (const cluster of clusters) {
    const dx=Math.abs(x-cluster.centreX),level=dx<26?'full':dx<65?'near':'far';
    draws += level==='far'?1:cluster.draws; triangles += cluster.triangles[level]!;
    if (level==='full') { full++; shadow += cluster.draws; }
    if (level!=='far') active++;
  }
  maxDraws=Math.max(maxDraws,draws);maxFull=Math.max(maxFull,full);maxActive=Math.max(maxActive,active);
  maxTriangles=Math.max(maxTriangles,triangles);maxShadow=Math.max(maxShadow,shadow);
}
const report = {
  candidate:true,trackHash:compileTrack(A1).hash,
  assumptions:['Camera zoom1; x-only distances conservatively overselect detailed LODs.','No frustum/tier benefit or original-tree material chunk removal credited.','Protected close/foreground crowns become regrowth; original x/z anchors remain fixed.'],
  sourceHashes:Object.fromEntries(['src/render/world/zones/a1Forest.ts','src/render/world/zones/alpineTrees.ts'].map(file=>[file,createHash('sha256').update(readFileSync(file)).digest('hex')])),
  nearTrees:55,farTrees:221,nearClusters:clusters,farBanks:plan.farBanks.map((trees,i)=>({bank:i,trees:trees.length,draws:1,triangles:trees.length*4})),
  speciesCounts:Object.fromEntries([...plan.nearClusters.flat(),...plan.farBanks.flat()].reduce((map,t)=>map.set(t.variant,(map.get(t.variant)??0)+1),new Map<string,number>())),
  maxDetailedClusters:maxActive,maxFullClusters:maxFull,maxCandidateMainDraws:maxDraws,maxCandidateMainTriangles:maxTriangles,maxCandidateShadowDrawsPerPass:maxShadow,
  farOnlyMainDraws:1+plan.farBanks.length,farOnlyTriangles:276*4,
  staticWorldBaselineDraws:178,staticWorldMainDrawUpper:178+maxDraws,
  historicalStartWindowCalls:108,historicalStartWindowEstimatedCalls:108+maxDraws+maxShadow,
  historicalWarning:'Historical window is not current same-head or whole-ride measurement. Shadows/tier/post can change frame totals.',
  placements:plan,
};
writeFileSync(new URL('../../../../docs/evidence/course-remaster/alpine-tree-kit/a1-full-forest-budget.json',import.meta.url),JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({nearClusters:clusters.length,farBanks:report.farBanks,speciesCounts:report.speciesCounts,maxDetailedClusters:maxActive,maxFullClusters:maxFull,maxMainDraws:maxDraws,maxMainTriangles:maxTriangles,maxShadowDraws:maxShadow,farOnlyMainDraws:report.farOnlyMainDraws},null,2));
