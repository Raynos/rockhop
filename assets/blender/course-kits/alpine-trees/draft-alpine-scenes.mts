/** Source-only A2/A3 botanical proposals from audited anchors. No runtime/public writes. */
import { readFileSync, writeFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { A2,A3 } from '../../../../src/tracks/rockhop/alpine';
import { zoneGround } from '../../../../src/render/world/zones/zoneKit';
import type { AlpineTreeVariant } from '../../../../src/render/world/zones/alpineTrees';
interface Tree {batch:string;index:number;x:number;y:number;z:number;matrix:number[];color:number[]|null}
interface Audit {tracks:{id:string;seed:number;trackHash:string;tiers:{near:Tree[];far:Tree[];treeShadowCount:number;farDepthBanks:number[];constructedStaticWorld:{draws:number;triangles:number;castMeshes:number}}[]}[]}
const auditFile=new URL('../../../../docs/evidence/course-remaster/alpine-tree-kit/a2-a3-existing-forest-audit.json',import.meta.url);
const auditBytes=readFileSync(auditFile),audit=JSON.parse(auditBytes.toString()) as Audit;
const prototypes=JSON.parse(readFileSync(new URL('../../../../docs/evidence/course-remaster/alpine-tree-kit/build-report.json',import.meta.url),'utf8')) as {variants:{file:string;meshes:{name:string;triangles:number}[]}[]};
const heights:Record<AlpineTreeVariant,number>={'pine-a':22,'pine-b':17,'pine-c':26,'pine-young':13,'fir-a':24,'fir-b':30,'snag-a':14,'snag-b':10,'sapling-pine':3.2,'sapling-fir':4.5};
const tris=(level:'full'|'near',variant:AlpineTreeVariant)=>prototypes.variants.find(v=>v.file===`trees-${level}.phone.glb`)!.meshes.filter(m=>m.name.startsWith(`${variant}__`)).reduce((sum,m)=>sum+m.triangles,0);
const guards:Record<string,{name:string;x0:number;x1:number}[]>={
 'a2-log-jam':[{name:'landing gate',x0:-10,x1:34},{name:'first pile ramp and exit',x0:30,x1:61},{name:'first teetering log',x0:108,x1:150.8},{name:'cribbed big log and second teetering log',x0:186.8,x1:248.8},{name:'Jam takeoff, pivot, pile and rollout',x0:280,x1:345.5},{name:'finish approach',x0:371.5,x1:401.5}],
 'a3-timberline':[{name:'logging road start',x0:-10,x1:24},{name:'cribbing hop',x0:21,x1:53},{name:'thin skid-beam landing',x0:91,x1:146},{name:'stump gap and log cribbing',x0:171,x1:211.2},{name:'loader takeoff, log lift and thin exit',x0:232.2,x1:301.7},{name:'finish approach',x0:323.7,x1:353.7}],
};
function seed(trackSeed:number,t:Tree):number{let n=(trackSeed^Math.imul(t.index+1,0x9e3779b1))>>>0;for(const c of t.batch)n=Math.imul(n^c.charCodeAt(0),16777619)>>>0;return n;}
const reports=[];
for(const def of [A2,A3]) {
 const audited=audit.tracks.find(t=>t.id===def.id)!,source=audited.tiers[0]!,guard=guards[def.id]!;
 const trees=[...source.near,...source.far].map(t=>{
  const n=seed(def.seed,t),v=(n%1000)/999,far=t.batch.startsWith('pinefar'),protectedWindow=guard.find(g=>t.x>=g.x0&&t.x<=g.x1);
  const cluster=Math.floor(t.x/48),palette:AlpineTreeVariant[]=def===A2?(cluster%2?['pine-b','pine-young']:['fir-a','pine-b']):(cluster%2?['fir-a','pine-young']:['pine-young','snag-a']);
  let variant:AlpineTreeVariant,height:number;
  if(far){const p:AlpineTreeVariant[]=def===A2?['pine-a','pine-b','fir-a','fir-b','pine-young']:['fir-a','pine-young','snag-a','pine-b','snag-b'];variant=p[n%p.length]!;height=def===A2?8+v*5:5+v*5;}
  else if(t.z>-14||(protectedWindow&&t.z>-20)){variant='sapling-pine';height=def===A2?1.1+v*.4:.9+v*.4;}
  else {variant=palette[n%palette.length]!;height=protectedWindow?4.8+v*1.2:def===A2?8+v*3:5.5+v*3;}
  return {sourceBatch:t.batch,sourceItem:t.index,variant,x:t.x,y:zoneGround('alpine',def.profile,t.x,t.z)-.04,z:t.z,yaw:Math.atan2(t.matrix[8]!,t.matrix[0]!),height,scale:height/heights[variant],far,protectedWindow:protectedWindow?.name??null,bin:cluster};
 });
 const clusters=[...new Set(trees.filter(t=>!t.far).map(t=>t.bin))].map(bin=>{const group=trees.filter(t=>!t.far&&t.bin===bin);return {bin,trees:group,centreX:group.reduce((s,t)=>s+t.x,0)/group.length,draws:2*new Set(group.map(t=>t.variant)).size,triangles:{full:group.reduce((s,t)=>s+tris('full',t.variant),0),near:group.reduce((s,t)=>s+tris('near',t.variant),0),far:group.length*4}};});
 const bounds={mainDraws:0,mainTriangles:0,fullClusters:0,detailedClusters:0,shadowDrawsPerPass:0};
 for(let x=-100;x<def.finishX+200;x+=.5){let draws=2,triangles=source.far.length*4,full=0,detailed=0,shadow=0;for(const c of clusters){const d=Math.abs(x-c.centreX),level=d<26?'full':d<65?'near':'far';draws+=level==='far'?1:c.draws;triangles+=c.triangles[level];if(level==='full'){full++;shadow+=c.draws;}if(level!=='far')detailed++;}bounds.mainDraws=Math.max(bounds.mainDraws,draws);bounds.mainTriangles=Math.max(bounds.mainTriangles,triangles);bounds.fullClusters=Math.max(bounds.fullClusters,full);bounds.detailedClusters=Math.max(bounds.detailedClusters,detailed);bounds.shadowDrawsPerPass=Math.max(bounds.shadowDrawsPerPass,shadow);}
 reports.push({id:def.id,seed:def.seed,trackHash:audited.trackHash,status:'proposal only, no runtime module or public writes',nearTrees:source.near.length,farTrees:source.far.length,matchingTreeShadows:source.treeShadowCount,guards:guard,binMetres:48,clusters,farBanks:[trees.filter(t=>t.far&&t.z>=-49),trees.filter(t=>t.far&&t.z<-49)],candidateBounds:bounds,staticWorldNoRemovalCredit:{baseline:source.constructedStaticWorld,mainDrawUpper:source.constructedStaticWorld.draws+bounds.mainDraws,triangleUpper:source.constructedStaticWorld.triangles+bounds.mainTriangles,shadowDrawUpper:source.constructedStaticWorld.castMeshes+bounds.shadowDrawsPerPass},farOnly:{draws:3,triangles:trees.length*4},coldAdditionalPublicBytes:0,bankResidentMapsMiB:6.333333333333333,sourceAuditSHA256:createHash('sha256').update(auditBytes).digest('hex'),limits:['Conservative x-only LOD count, no frustum/remove-credit; not measured GPU performance.','Static world bound excludes hero/ghost/post and applies no tier/frustum/removal credit.','48m clusters trade finer culling for bounded species draws; matched moving trial must decide.','Heights/palette/guards are authoring proposals, not accepted screen-space occlusion proof.','Existing full/near kit remains unchanged; proposed phone near-only policy needs a separate loader API change.']});
}
writeFileSync(new URL('../../../../docs/evidence/course-remaster/alpine-tree-kit/a2-a3-scene-draft.json',import.meta.url),JSON.stringify({nodeOnly:true,tracks:reports},null,2)+'\n');
console.log(JSON.stringify(reports.map(r=>({id:r.id,clusters:r.clusters.length,bounds:r.candidateBounds,farOnly:r.farOnly})),null,2));
