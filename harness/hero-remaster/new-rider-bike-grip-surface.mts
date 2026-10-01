/** Actual unchanged bike handlebar surface measurement, CPU decoder only. */
import fs from 'node:fs';
import * as THREE from 'three';
import { loadRigAt } from '../../src/render/hero/gltfTestUtils';
const results=[];
for(const name of ['bike-rookie.glb','bike-pro.glb']){
 const g=await loadRigAt(new URL('file://'+process.cwd()+'/public/models/'+name));g.scene.updateMatrixWorld(true);
 const all:THREE.Mesh[]=[];g.scene.traverse(o=>{if((o as THREE.Mesh).isMesh&&o.name.toLowerCase().includes('handlebar'))all.push(o as THREE.Mesh);});
 const markers:THREE.Object3D[]=[];g.scene.traverse(o=>{if(o.name.includes('attach_grip'))markers.push(o);});
 const sides=[];
 for(const marker of markers){
  const centre=marker.getWorldPosition(new THREE.Vector3());const rows=[];
  for(const mesh of all){const attr=mesh.geometry.getAttribute('position');for(let i=0;i<attr.count;i++){const p=new THREE.Vector3().fromBufferAttribute(attr,i);mesh.localToWorld(p);if(Math.abs(p.z-centre.z)<.04){const radius=Math.hypot(p.x-centre.x,p.y-centre.y);rows.push({vertex:i,mesh:mesh.name,point:p.toArray(),radialDistance:radius,axialDistance:p.z-centre.z});}}}
  rows.sort((a,b)=>a.radialDistance-b.radialDistance);sides.push({marker:marker.name,centre:centre.toArray(),sectionHalfWidthM:.04,vertices:rows.length,radiusRangeM:rows.length?[rows[0]!.radialDistance,rows.at(-1)!.radialDistance]:[],rows});
 }
 results.push({asset:name,handlebarMeshes:all.map(m=>m.name),sides});
}
const out='docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/bike-grip-surface01';fs.mkdirSync(out,{recursive:true});fs.writeFileSync(out+'/report.json',JSON.stringify({scope:'Actual unchanged bike vertex witnesses, approximate local rod-axisZ section; requires triangle/camera inspection',results},null,2)+'\n');console.log(JSON.stringify(results.map(r=>({asset:r.asset,sides:r.sides.map(s=>({marker:s.marker,centre:s.centre,vertices:s.vertices,radiusRange:s.radiusRangeM}))}))));
