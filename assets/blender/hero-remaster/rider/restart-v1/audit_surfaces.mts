/** CPU attachment census of actual prepared/conditioned candidate surfaces.
 * This is diagnostic evidence, not played motion or acceptance of the art.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { loadRigAt } from '../../../../../src/render/hero/gltfTestUtils';
import { prepareHero } from '../../../../../src/render/hero/lod';
import { GltfRider, boneName } from '../../../../../src/render/hero/gltfRider';
import type { HeroBike } from '../../../../../src/render/bike/bikeModel';
import type { MaterialLibrary } from '../../../../../src/render/materials/library';
import { FrameBuilder } from '../../../../../src/render/frame';
import { BIKE_GEOMETRY_V2 } from '../../../../../src/render/hero/assetFrame';
import { makeRiderRigPose, riderRigFromHips, riderPoseAtLean, RIDER_TORSO_REST } from '../../../../../src/render/hero/riderRig';
const dir=path.dirname(new URL(import.meta.url).pathname);
const revision=process.argv[2]??'whole-rider';
type End={mesh:THREE.SkinnedMesh,index:number};
const local=(e:End)=>new THREE.Vector3().fromBufferAttribute(e.mesh.geometry.getAttribute('position'),e.index);
const world=(e:End)=>e.mesh.getVertexPosition(e.index,new THREE.Vector3()).applyMatrix4(e.mesh.matrixWorld);
const key=(p:THREE.Vector3)=>p.toArray().map(x=>Math.round(x*1e6)).join(',');
const weight=(e:End)=>{
 const indices=e.mesh.geometry.getAttribute('skinIndex'),values=e.mesh.geometry.getAttribute('skinWeight'),out=new Map<string,number>();
 for(let lane=0;lane<4;lane++){
  const w=values.getComponent(e.index,lane);if(!w)continue;
  const n=boneName(e.mesh.skeleton.bones[indices.getComponent(e.index,lane)]!.name);out.set(n,(out.get(n)??0)+w);
 }
 return out;
};
const poses=[{name:'garage',stage:true,hips:[-.46,.75,40]},...[-1,0,1].map(lean=>{
 const p=riderPoseAtLean(lean,makeRiderRigPose());return{name:lean<0?'backlean':lean>0?'forwardlean':'neutral',stage:false,hips:[p.hips.x,p.hips.y,p.torsoAngle*180/Math.PI]};
}),{name:'compression',stage:false,hips:[-.57,.60,55]},{name:'extension',stage:false,hips:[-.14,.96,40]},{name:'landing',stage:false,hips:[-.40,.70,40]}];
const reports=[];
for(const lod of [false,true]){
 const file=`${dir}/${revision}${lod?'-lod':''}-packed.glb`,sha=crypto.createHash('sha256').update(fs.readFileSync(file)).digest('hex');
 const gltf=await loadRigAt(pathToFileURL(file),true);await prepareHero(gltf);
 const rider=new GltfRider(gltf,{complete(){}} as unknown as MaterialLibrary),frame=new THREE.Group();rider.attach({frame} as HeroBike);frame.updateMatrixWorld(true);
 const meshes:THREE.SkinnedMesh[]=[];frame.traverse(o=>{if((o as THREE.SkinnedMesh).isSkinnedMesh)meshes.push(o as THREE.SkinnedMesh)});
 const bones=meshes[0]!.skeleton.bones;
 const regions=['L','R'].flatMap(side=>[['wrist','hand',.12],['elbow','forearm',.11],['ankle','foot',.13]].map(([name,bone,radius])=>{
  const bn=bones.find(b=>boneName(b.name)===`${bone}.${side}`)!,center=bn.getWorldPosition(new THREE.Vector3());
  const endpoints:End[]=[],groups=new Map<string,End[]>(),faces:End[][]=[];
  const edgeCounts=new Map<string,number>();
  for(const mesh of meshes){
   const p=mesh.geometry.getAttribute('position'),index=mesh.geometry.index!;
   for(let i=0;i<p.count;i++){
    const e={mesh,index:i};if(world(e).distanceTo(center)>+radius!)continue;
    endpoints.push(e);const k=key(local(e));const group=groups.get(k)??[];group.push(e);groups.set(k,group);
   }
   for(let i=0;i<index.count;i+=3){
    const es=[0,1,2].map(k=>({mesh,index:index.getX(i+k)}));
    if(!es.some(e=>world(e).distanceTo(center)<+radius!))continue;faces.push(es);
    for(const [a,b] of [[0,1],[1,2],[2,0]]){
     const x=key(local(es[a!]!)),y=key(local(es[b!]!));if(x===y)continue;
     if(world(es[a!]!).distanceTo(center)>+radius!||world(es[b!]!).distanceTo(center)>+radius!)continue;
     const k=x<y?`${x}|${y}`:`${y}|${x}`;edgeCounts.set(k,(edgeCounts.get(k)??0)+1);
    }
   }
  }
  const duplicates=[...groups.values()].filter(g=>g.length>1),pairs=duplicates.flatMap(g=>g.slice(1).map(b=>({a:g[0]!,b})));
  return{side,name:String(name),bone:String(bone),radius:+radius!,endpoints,pairs,faces,duplicateGroups:duplicates.length,positionCorrespondence:duplicates.map(g=>({position:local(g[0]!).toArray(),vertices:g.map(e=>({mesh:e.mesh.name,index:e.index}))})),topology:{boundaryEdges:[...edgeCounts.values()].filter(n=>n===1).length,nonManifoldEdges:[...edgeCounts.values()].filter(n=>n>2).length}};
 }));
 const rows=[];
 for(const pose of poses){
  rider.setStage(pose.stage);rider.setStageTime(.75);
  const[hx,hy,torso]=pose.hips,rig=riderRigFromHips(hx!,hy!,torso!*Math.PI/180,makeRiderRigPose()),f=new FrameBuilder().frame;
  f.riderBody.present=true;f.riderBody.relX=rig.com.x+BIKE_GEOMETRY_V2.chassisToAxle.x;f.riderBody.relY=rig.com.y+BIKE_GEOMETRY_V2.chassisToAxle.y;f.riderBody.relAngle=rig.torsoAngle-RIDER_TORSO_REST;f.tSim=4;f.dt=1/60;f.cut=true;f.speed=0;
  for(let i=0;i<20;i++){rider.update(f);frame.updateMatrixWorld(true)}
  rows.push({pose:pose.name,regions:regions.map(r=>{
   let maxGap=0,maxRawWeightL1=0,maxPositionDrift=0,collapsedTriangles=0,minArea=Infinity;
   for(const{a,b}of r.pairs){
    maxGap=Math.max(maxGap,world(a).distanceTo(world(b)));maxPositionDrift=Math.max(maxPositionDrift,local(a).distanceTo(local(b)));
    const wa=weight(a),wb=weight(b);maxRawWeightL1=Math.max(maxRawWeightL1,[...new Set([...wa.keys(),...wb.keys()])].reduce((s,n)=>s+Math.abs((wa.get(n)??0)-(wb.get(n)??0)),0));
   }
   for(const es of r.faces){const[p,q,t]=es.map(world),area=new THREE.Triangle(p!,q!,t!).getArea();minArea=Math.min(minArea,area);if(!Number.isFinite(area)||area<1e-10)collapsedTriangles++}
   const socket=frame.getObjectByName(THREE.PropertyBinding.sanitizeNodeName(`${r.name==='wrist'?'gripSocket':'soleSocket'}.${r.side}`));
   const socketPoint=socket?.getWorldPosition(new THREE.Vector3());
   const nearestSurface=socketPoint&&(r.name==='wrist'||r.name==='ankle')?Math.min(...r.faces.map(es=>{const[p,q,t]=es.map(world);return new THREE.Triangle(p!,q!,t!).closestPointToPoint(socketPoint,new THREE.Vector3()).distanceTo(socketPoint)})):null;
   const closestSurface=socketPoint&&(r.name==='wrist'||r.name==='ankle')?r.faces.map(es=>{const[p,q,t]=es.map(world);const point=new THREE.Triangle(p!,q!,t!).closestPointToPoint(socketPoint,new THREE.Vector3());return{point,distance:point.distanceTo(socketPoint)}}).sort((a,b)=>a.distance-b.distance)[0]:null;
   const ownBone=bones.find(b=>boneName(b.name)===`${r.bone}.${r.side}`)!;
   const surfaceOffsetInBone=closestSurface&&socketPoint?new THREE.Vector3().subVectors(socketPoint,closestSurface.point).applyMatrix3(new THREE.Matrix3().setFromMatrix4(ownBone.matrixWorld).invert()).toArray():null;
   const contactDistance=socket&&(r.name==='wrist'||r.name==='ankle')?Math.min(...r.endpoints.map(e=>world(e).distanceTo(socket.getWorldPosition(new THREE.Vector3())))):null;
   return{side:r.side,region:r.name,pairs:r.pairs.length,maxLocalPositionDifferenceMetres:maxPositionDrift,maxRawWeightL1,maxWorldGapMetres:maxGap,selectedTriangles:r.faces.length,collapsedTriangles,minAreaSquareMetres:minArea,nearestVertexToSocketMetres:contactDistance,nearestTriangleSurfaceToSocketMetres:nearestSurface,surfaceOffsetToContactInBoneMetres:surfaceOffsetInBone};
  })});
 }
 reports.push({tier:lod?'lod':'full',file,sha256:sha,regions:regions.map(({endpoints,pairs,faces,...r})=>({...r,selectedVertices:endpoints.length,selectedTriangles:faces.length,vertexPairs:pairs.length})),poses:rows});rider.dispose();
}
const out={status:'diagnostic only; no visual acceptance or complete seam gate asserted',method:'Actual prepareHero/GltfRider/conditionSleeveSkin; explicit 1-micrometre packed-coordinate material/UV duplicate correspondence; seven synthetic settled frame cases; independently merged triangle-edge incidence near each joint.',limits:['Synthetic frames are not played game evidence','Coincident vertex pairs alone cannot prove full boundary continuity; topology figures also expose holes/nonmanifold surfaces','Nearest surface distance supplements the vertex census; grip enclosure, palm orientation and visible contact still require played review','No textures, GPU, self-intersections, cloth fit or visual quality judged'],subjects:reports};
const dest=`docs/evidence/hero-remaster/restart/${revision==='whole-rider'?'whole-rider-v1':revision}-runtime-surfaces.json`;fs.writeFileSync(dest,JSON.stringify(out,null,2)+'\n');
console.log(JSON.stringify({out:dest,subjects:reports.map(r=>({tier:r.tier,sha256:r.sha256,maxWorldGapMetres:Math.max(...r.poses.flatMap(p=>p.regions.map(j=>j.maxWorldGapMetres))),collapseCounts:r.poses.map(p=>p.regions.reduce((s,j)=>s+j.collapsedTriangles,0)),topology:r.regions.map(j=>({side:j.side,region:j.name,...j.topology}))}))},null,2));
