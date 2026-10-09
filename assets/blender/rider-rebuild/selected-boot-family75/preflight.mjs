/** Actual own-side right topology reuse; CPU measurement, no optimizer/native. */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { SourceTree, faceCensus } from '../selected-boot-surface67/surface.mjs';
import { normalCensus } from '../selected-boot-closure62/closure.mjs';
import { ROOT, arrays, pinned, filePin } from '../selected-boot-surface67/io.mjs';

// Exact ray/triangle intersections on two independent axes. A boundary or
// inconsistent parity is reported unresolved, never promoted to enclosure.
export function rayParity(tree, q, axis) {
  const x=(axis+1)%3,y=(axis+2)%3,hits=new Set();let boundary=false;
  const visit=index=>{
    const node=tree.nodes[index],b=node.bounds;
    if(q[x]<b[x]||q[x]>b[x+3]||q[y]<b[y]||q[y]>b[y+3]||q[axis]>b[axis+3])return;
    if(node.left>=0){visit(node.left);visit(node.right);return;}
    for(let j=node.start;j<node.end;j++){
      const face=tree.ids[j],ids=tree.triangles.subarray(3*face,3*face+3);
      const [a,c,d]=Array.from(ids,id=>Array.from(tree.positions.subarray(3*id,3*id+3)));
      const ux=c[x]-a[x],uy=c[y]-a[y],vx=d[x]-a[x],vy=d[y]-a[y],det=ux*vy-uy*vx;
      if(det===0)continue;
      const dx=q[x]-a[x],dy=q[y]-a[y],u=(dx*vy-dy*vx)/det,v=(ux*dy-uy*dx)/det;
      if(u<0||v<0||u+v>1)continue;
      const z=a[axis]+u*(c[axis]-a[axis])+v*(d[axis]-a[axis]);if(z<q[axis])continue;
      if(u===0||v===0||u+v===1||z===q[axis])boundary=true;
      hits.add(z);
    }
  };
  visit(tree.root);return {inside:hits.size%2===1,boundary,crossings:hits.size};
}

function enclosure(tree,points,ids,reflect=false){
  const inside=[],outside=[],unresolved=[];let minimumInside=Infinity,maximumOutside=0;
  for(let i=0;i<ids.length;i++){
    const q=Array.from(points.subarray(3*i,3*i+3));if(reflect)q[0]*=-1;
    const a=rayParity(tree,q,0),b=rayParity(tree,q,2),near=tree.nearest(q);
    if(a.boundary||b.boundary||a.inside!==b.inside){unresolved.push(ids[i]);continue;}
    if(a.inside){inside.push(ids[i]);minimumInside=Math.min(minimumInside,near.distanceM);}
    else{outside.push(ids[i]);maximumOutside=Math.max(maximumOutside,near.distanceM);}
  }
  return {samples:ids.length,insideCount:inside.length,outsideCount:outside.length,unresolvedCount:unresolved.length,
    outsideOriginalBodyVertexIds:outside,unresolvedOriginalBodyVertexIds:unresolved,
    minimumInsideDistanceM:Number.isFinite(minimumInside)?minimumInside:null,maximumOutsideDistanceM:maximumOutside,
    limits:'Two-axis exact ray parity of the closed source surface at actual foot/toe-weighted vertices. This is not a cavity/leather, triangle-crossing, posed-contact or art acceptance gate.'};
}

export function preflight(inputPath) {
const input=path.resolve(inputPath);assert(input.startsWith(path.join(ROOT,'harness/out/rider-rebuild/selected-boot-family75/')));
const source=JSON.parse(fs.readFileSync(input)),a=arrays(source.arrays);
pinned(source.native70);pinned(source.production70);pinned(source.canonicalNative02);
const evidence=path.join(ROOT,'docs/evidence/rider-rebuild/selected-boot-family75');fs.mkdirSync(evidence,{recursive:true});
const report={status:'PARTIAL_ACTUAL_SIDE_PREFLIGHT_UNACCEPTED',acceptedArt:false,source:filePin(input),sides:{},
  sourceAsymmetry:source.selectedRightVersusReflectedLeftM,footAsymmetry:source.native02ReflectedLeftFootNearestRightVertexM,
  thresholds:{minimumNormalDot:.25,maximumSurfaceErrorM:.001},optimizerCalls:0,nativeExecuted:false,
  recipe:filePin(fileURLToPath(import.meta.url))};
for(const [file,sha256] of [['selected-boot-surface67/surface.mjs','4c68f83bfd76f2fedb2cec42de6cfef4ee8d1cca74f3959cffa813521778d07a'],['selected-boot-closure62/closure.mjs','89cb51a5d9587a0c6726ab65d7678b9e0072756d16973dab3263e96e849ce294']])pinned({path:'assets/blender/rider-rebuild/'+file,sha256});
const write=()=>fs.writeFileSync(path.join(evidence,'preflight.json'),`${JSON.stringify(report,null,2)}\n`);write();
for(const side of ['L','R']){
  const mesh={positions:a[side+'Positions'],triangles:a[side+'Triangles'],normals:a[side+'Normals']},tree=new SourceTree(mesh.positions,mesh.triangles);
  const row=report.sides[side]={vertex:normalCensus(mesh,a[side+'CandidateOriginalTriangles'])};write();
  row.face=faceCensus(mesh,a[side+'CandidateOriginalTriangles'],tree).report;write();
  row.actualNative02FootEnclosure=enclosure(tree,a[side+'FootPoints'],a[side+'FootOriginalIds']);
  if(side==='L')row.reflectedLeftAgainstActualRightFoot=enclosure(tree,a.RFootPoints,a.RFootOriginalIds,true);
  write();
}
report.cpuReusePassed=Object.values(report.sides).every(side=>side.vertex.passed&&side.face.passed);
report.status=report.cpuReusePassed?'ACTUAL_BILATERAL_TOPOLOGY_CPU_PASS_NATIVE_PENDING':'RIGHT_TOPOLOGY_REUSE_REJECTED_NO_NATIVE_OR_OPTIMIZER';
report.limits='Source and CPU checkpoint only. Right uses genuine own-side source coordinates/fields, no reflection fit assumption. CPU geometric source normals are proxies; native orientation/surface/skin gates remain. Foot enclosure evidence is explicit and grants no fit, bake, allocation or art acceptance.';
write();return report;
}
if(process.argv[1]&&path.resolve(process.argv[1])===fileURLToPath(import.meta.url)){
  assert.equal(process.argv.length,3,'Usage: node preflight.mjs CPU_SOURCE_JSON');
  const report=preflight(process.argv[2]);console.log(JSON.stringify({status:report.status,sides:Object.fromEntries(Object.entries(report.sides).map(([s,r])=>[s,{vertexFailures:r.vertex.failingVertices,faceFailures:r.face.failingFaces,minimumFaceDot:r.face.minimumNormalDot,maximumDistanceM:r.face.maximumDistanceM,outsideFootSamples:r.actualNative02FootEnclosure.outsideCount}]))}));
}
