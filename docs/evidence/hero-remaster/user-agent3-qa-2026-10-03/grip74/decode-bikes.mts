/** Read production compressed geometry through its decoder; no render/export. */
import fs from 'node:fs';
import {loadRigAt} from '../../../../../src/render/hero/gltfTestUtils';
import {Vector3} from 'three';
const out='docs/evidence/hero-remaster/user-agent3-qa-2026-10-03/grip74';
const result:any={status:'READ_ONLY_ACTUAL_FINITE_GRIP_TRIANGLES',bikes:[]};
for(const file of ['bike-rookie.glb','bike-rookie-lod.glb','bike-pro.glb','bike-pro-lod.glb']){
 const fit=JSON.parse(fs.readFileSync(`docs/evidence/hero-remaster/one-rider-v2/contact-targets/fits/${file}.json`,'utf8'));
 const gltf=await loadRigAt(new URL(`../../../../../public/models/${file}`,import.meta.url));gltf.scene.updateMatrixWorld(true);
 const rows=[];
 for(const g of fit.grips){const n=await gltf.parser.getDependency('node',g.nodeIndex);let mesh:any;n.traverse((o:any)=>{if(o.geometry)mesh=o});if(!mesh)throw new Error('No source mesh');
 const pos=mesh.geometry.getAttribute('position'),ix=mesh.geometry.index;const tri=[];
 for(const ordinal of g.sourceTriangleOrdinals){const vs=[];for(let k=0;k<3;k++){const i=ix?ix.getX(ordinal*3+k):ordinal*3+k;const v=new Vector3().fromBufferAttribute(pos,i).applyMatrix4(mesh.matrixWorld);v.sub(new Vector3(...g.bikeFrameOriginFileFrame));vs.push(v.toArray())}tri.push(vs)}
 rows.push({side:g.side,trianglesBikeFrame:tri,sourceTriangleOrdinals:g.sourceTriangleOrdinals,fit:g});}
 result.bikes.push({file,sourceSHA256:fit.sourceSHA256,grips:rows});}
fs.writeFileSync(`${out}/finite-grips.json`,JSON.stringify(result)+'\n');console.log(JSON.stringify(result.bikes.map((b:any)=>({file:b.file,triangles:b.grips.map((g:any)=>g.trianglesBikeFrame.length)}))));
