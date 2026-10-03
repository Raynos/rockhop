/** Actual decoded rigid bike components for parent target selection; no contact pass. */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import { Vector3 } from 'three';
import { loadRigAt } from '../../../src/render/hero/gltfTestUtils.ts';
import { prepareHero } from '../../../src/render/hero/lod.ts';
const [buildArg,outArg]=process.argv.slice(2);assert(outArg&&!fs.existsSync(outArg));
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const build=path.resolve(buildArg),manifest=JSON.parse(fs.readFileSync(path.join(build,'hero-review.json'))),reports=[];
for(const logical of ['models/bike-rookie.glb','models/bike-pro.glb','models/bike-rookie-lod.glb','models/bike-pro-lod.glb']){
  const entry=manifest.models.find(m=>m.logical===logical),file=path.join(build,entry.url);assert.equal(sha(fs.readFileSync(file)),entry.sha256);
  const g=await loadRigAt(pathToFileURL(file),true);g.scene.updateMatrixWorld(true);const sources=[];
  g.scene.traverse(mesh=>{
    if(!mesh.isMesh||!['handlebar','pegs','bodywork'].includes(mesh.name))return;
    const assoc=g.parser.associations.get(mesh);assert(assoc?.meshes!==undefined&&assoc?.primitives!==undefined);
    const nodeIndex=g.parser.json.nodes.findIndex(n=>n.mesh===assoc.meshes&&n.name===mesh.name);assert(nodeIndex>=0);
    const p=mesh.geometry.attributes.position,idx=mesh.geometry.index;assert(idx);
    // Weld only coincident decoded rest vertices; components are triangle adjacency,
    // never a bone/socket-derived contact patch or a closed-volume certificate.
    const welded=new Map(),ids=[],roots=[];
    for(let i=0;i<p.count;i++){
      const key=[p.getX(i),p.getY(i),p.getZ(i)].map(v=>Math.round(v/1e-6)).join(',');
      if(!welded.has(key)){welded.set(key,roots.length);roots.push(roots.length);}ids.push(welded.get(key));
    }
    const root=i=>{while(roots[i]!==i){roots[i]=roots[roots[i]];i=roots[i];}return i;};
    for(let t=0;t<idx.count;t+=3){const a=root(ids[idx.getX(t)]);for(let c=1;c<3;c++)roots[root(ids[idx.getX(t+c)])]=a;}
    const components=new Map();for(let t=0;t<idx.count;t+=3){const r=root(ids[idx.getX(t)]),rows=components.get(r)??[];rows.push(t/3);components.set(r,rows);}
    const parts=[...components.values()].map((triangles,component)=>{
      const vertices=[...new Set(triangles.flatMap(t=>[0,1,2].map(c=>idx.getX(t*3+c))))].sort((a,b)=>a-b);
      const min=[Infinity,Infinity,Infinity],max=[-Infinity,-Infinity,-Infinity];
      for(const v of vertices){const pt=new Vector3(p.getX(v),p.getY(v),p.getZ(v)).applyMatrix4(mesh.matrixWorld).toArray();pt.forEach((x,k)=>{min[k]=Math.min(min[k],x);max[k]=Math.max(max[k],x);});}
      return{component,sourceTriangleOrdinals:triangles,sourceVertexIndices:vertices,fileFrameBoundsM:[min,max]};
    });
    const geometryPayload=JSON.stringify({positions:Array.from({length:p.count},(_,i)=>[p.getX(i),p.getY(i),p.getZ(i)]),indices:Array.from({length:idx.count},(_,i)=>idx.getX(i))});
    sources.push({sourceNodeName:mesh.name,nodeIndex,sourceMeshIndex:assoc.meshes,primitiveIndex:assoc.primitives,geometrySHA256:sha(Buffer.from(geometryPayload)),
      sourceNodeMatrixWorld:mesh.matrixWorld.toArray(),vertices:p.count,triangles:idx.count/3,components:parts});
  });assert.equal(sources.length,3);
  await prepareHero(g);g.scene.updateMatrixWorld(true);
  for(const source of sources){const m=g.scene.getObjectByName(source.sourceNodeName);assert(m?.isMesh);const p=m.geometry.attributes.position,idx=m.geometry.index;
    const payload=JSON.stringify({positions:Array.from({length:p.count},(_,i)=>[p.getX(i),p.getY(i),p.getZ(i)]),indices:Array.from({length:idx.count},(_,i)=>idx.getX(i))});assert.equal(sha(Buffer.from(payload)),source.geometrySHA256);}
  const origin=g.scene.getObjectByName('attach_frame_origin');assert(origin);reports.push({logical,assetSHA256:entry.sha256,frameOriginFileFrameM:origin.getWorldPosition(new Vector3()).toArray(),sources,exactGeometryAfterPrepareHero:true});
}
const report={status:'UNACCEPTED_RIGID_TARGET_COMPONENT_INVENTORY',candidateSHA256:manifest.models.find(m=>m.logical==='models/rider-street-mustard.glb').sha256,
  codeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),reports,
  limits:['Components are a numerical selection inventory. No selected saddle/grip/peg surface, parent review, runtime instance correspondence, closed volume or contact verdict.',
    'Weld rounds coordinates to1micrometre grid; this is not a proof of true topology or closure. Source IDs remain decoded source geometry ordinals.',
    'Normal game bike is cloned and translated by frame_origin, then live chassis placement; next receipt must pin actual instance child paths and matrices.',
    'No current rider LOD mapping supplied; listed bike LOD is independently decoded, never substituted for full geometry.']};
fs.mkdirSync(path.dirname(outArg),{recursive:true});fs.writeFileSync(outArg,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify(reports.map(r=>({logical:r.logical,assetSHA256:r.assetSHA256,sources:r.sources.map(s=>({name:s.sourceNodeName,components:s.components.map(c=>({id:c.component,triangles:c.sourceTriangleOrdinals.length,bounds:c.fileFrameBoundsM}))}))}))));
