/** Actual rendered peg mesh topology and authored source frame, independent of sole markers. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import { Vector3 } from 'three';
import { loadRigAt } from '../../../src/render/hero/gltfTestUtils.ts';
import { triangleRows, bvhContacts } from './triangle-bvh.mjs';
const [file,outFile]=process.argv.slice(2);assert(outFile&&!fs.existsSync(outFile));const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const bytes=fs.readFileSync(file);assert.equal(sha(bytes),'e55919d60267849358ef5e97f4731f42fac6eb2835b9998e1d146d056c0f10f7');
const g=await loadRigAt(pathToFileURL(path.resolve(file)),true);g.scene.updateMatrixWorld(true);const mesh=g.scene.getObjectByName('pegs');assert(mesh?.isMesh&&!mesh.isSkinnedMesh);
const point=name=>g.scene.worldToLocal(g.scene.getObjectByName('attach_'+name).getWorldPosition(new Vector3()));
const origin=point('frame_origin'),com=point('chassis_com'),vertices=[],rowIDs=[],map=new Map();
for(let i=0;i<mesh.geometry.attributes.position.count;i++){
 const raw=new Vector3().fromBufferAttribute(mesh.geometry.attributes.position,i),key=raw.toArray().join(',');
 if(!map.has(key)){map.set(key,vertices.length);vertices.push(g.scene.worldToLocal(mesh.localToWorld(raw.clone())).sub(origin).toArray());}rowIDs.push(map.get(key));
}
const faces=Array.from({length:mesh.geometry.index.count/3},(_,i)=>[0,1,2].map(k=>rowIDs[mesh.geometry.index.getX(i*3+k)]));
const edges=new Map();faces.forEach((face,id)=>{for(let k=0;k<3;k++){const a=face[k],b=face[(k+1)%3],key=[Math.min(a,b),Math.max(a,b)].join(',');const list=edges.get(key)??[];list.push({face:id,direction:a<b?1:-1});edges.set(key,list);}});
const badEdges=[...edges].filter(([,list])=>list.length!==2||list[0].direction+list[1].direction!==0),adj=faces.map(()=>new Set());
for(const list of edges.values())for(const a of list)for(const b of list)if(a.face!==b.face)adj[a.face].add(b.face);
const visited=new Set(),components=[];
for(let i=0;i<faces.length;i++)if(!visited.has(i)){const stack=[i],ids=[];while(stack.length){const f=stack.pop();if(visited.has(f))continue;visited.add(f);ids.push(f);stack.push(...adj[f]);}
 const unique=[...new Set(ids.flatMap(id=>faces[id]))],volume=ids.reduce((sum,id)=>{const[a,b,c]=faces[id].map(v=>new Vector3(...vertices[v]));return sum+a.dot(b.clone().cross(c))/6;},0);
 const selected=ids.map(id=>faces[id]),selectedEdges=new Set(selected.flatMap(f=>f.map((v,k)=>[Math.min(v,f[(k+1)%3]),Math.max(v,f[(k+1)%3])].join(','))));
 const rows=triangleRows(vertices,selected),self=bvhContacts(rows,rows,true,true);
 components.push({component:components.length,triangles:ids,vertices:unique.length,edges:selectedEdges.size,euler:unique.length-selectedEdges.size+ids.length,signedVolumeM3:volume,selfContact:self,bounds:{min:[0,1,2].map(k=>Math.min(...unique.map(v=>vertices[v][k]))),max:[0,1,2].map(k=>Math.max(...unique.map(v=>vertices[v][k])))}});
}
const report={status:badEdges.length?'REJECTED_RENDERED_PEG_SOLID_TOPOLOGY':'UNACCEPTED_RENDERED_PEG_COMPONENTS_CLOSED_ONLY',sourceSHA256:sha(bytes),codeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),loaderSHA256:sha(fs.readFileSync('src/render/hero/gltfTestUtils.ts')),
 meshName:mesh.name,association:g.parser.associations.get(mesh),exportRows:rowIDs.length,uniqueExactPositionVertices:vertices.length,triangles:faces.length,rowIDs,verticesFrameLocalM:vertices,triangleVertexIDs:faces,
 sourceFrameOrigin:origin.toArray(),chassisToFrameOffsetM:origin.clone().sub(com).toArray(),markers:{L:point('peg_L').sub(origin).toArray(),R:point('peg_R').sub(origin).toArray()},badEdges:badEdges.slice(0,16),badEdgeCount:badEdges.length,components,
 limits:['Exact-position aliases only; no near-vertex merge, collider generation, source topology alteration or marker-only solid claim.', 'Closed component topology does not establish convexity, self/component intersection freedom, source normals, moving support, load bearing or consumed collision.', 'Current boot art remains rejected; source inventory is a support qualification checkpoint, not acceptance.']};
fs.mkdirSync(path.dirname(outFile),{recursive:true});fs.writeFileSync(outFile,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({status:report.status,rows:report.exportRows,unique:vertices.length,triangles:faces.length,badEdges:badEdges.length,components:components.map(({triangles,...c})=>({...c,triangles:triangles.length}))}));
