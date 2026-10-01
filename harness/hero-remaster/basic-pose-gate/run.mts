/** CPU stock-Three.js gate foundation. Never accepts visual/art/contact gates. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { loadRigAt } from '../../../src/render/hero/gltfTestUtils';
import { prepareHero } from '../../../src/render/hero/lod';
import { createFixturePlayer, type PoseFixture } from './protocol';
const arg=(key:string)=>process.argv.find(a=>a.startsWith('--'+key+'='))?.slice(key.length+3);
const source=arg('source'), fixturePath=arg('fixture'), out=arg('out');
assert(source&&fixturePath&&out,'--source --fixture --out required');
assert(!fs.existsSync(out),'Preserve frozen gate results');
const hash=(p:string)=>crypto.createHash('sha256').update(fs.readFileSync(p)).digest('hex');
const sourceHash=hash(source),fixtureHash=hash(fixturePath);
const fixture:PoseFixture=JSON.parse(fs.readFileSync(fixturePath,'utf8'));
const gltf=await loadRigAt(pathToFileURL(path.resolve(source)),true);await prepareHero(gltf);
const player=createFixturePlayer(gltf.scene,fixture);
const garment=player.meshes.filter(m=>m.name.startsWith('Protected')&&!m.name.endsWith('_1'));
assert.equal(garment.length,2,'Explicit body and hood inventory required');
const v=new THREE.Vector3(),p0=new THREE.Vector3(),p1=new THREE.Vector3(),p2=new THREE.Vector3();
const cross=new THREE.Vector3(),edge=new THREE.Vector3(),other=new THREE.Vector3();
const rest=garment.map(m=>{
  const attribute=m.geometry.getAttribute('position'),index=m.geometry.index;assert(index);
  const points=new Float64Array(attribute.count*3);
  for(let i=0;i<attribute.count;i++) {
    m.localToWorld(v.fromBufferAttribute(attribute,i));points.set(v.toArray(),i*3);
  }
  const areas=new Float64Array(index.count/3);
  for(let i=0;i<areas.length;i++) {
    p0.fromArray(points,index.getX(i*3)*3);p1.fromArray(points,index.getX(i*3+1)*3);p2.fromArray(points,index.getX(i*3+2)*3);
    areas[i]=cross.crossVectors(edge.subVectors(p1,p0),other.subVectors(p2,p0)).length();
  }
  return {mesh:m,points,areas,positions:new Float64Array(points.length),previous:new Float64Array(points.length)};
});
const rows=[];let maximumMatrixError=0;
let previousFamily='';
for(const frame of fixture.frames) {
  const parity=player.apply(frame);maximumMatrixError=Math.max(maximumMatrixError,parity.maximumWorldMatrixError);
  const stats=[];
  for(const rec of rest) {
    const m=rec.mesh,index=m.geometry.index!;let movement=0,neutralError=0;
    for(let i=0;i<rec.positions.length/3;i++) {
      m.localToWorld(m.getVertexPosition(i,v));
      assert(v.toArray().every(Number.isFinite),'Nonfinite skinned vertex');
      for(let j=0;j<3;j++) {
        const x=v.getComponent(j),offset=i*3+j;rec.positions[offset]=x;
        neutralError=Math.max(neutralError,Math.abs(x-rec.points[offset]!));
      }
      if(previousFamily===frame.family) {
        p0.fromArray(rec.previous,i*3);movement=Math.max(movement,v.distanceTo(p0));
      }
    }
    let collapse=0,minRatio=Infinity;
    for(let i=0;i<rec.areas.length;i++) {
      p0.fromArray(rec.positions,index.getX(i*3)*3);p1.fromArray(rec.positions,index.getX(i*3+1)*3);p2.fromArray(rec.positions,index.getX(i*3+2)*3);
      const area=cross.crossVectors(edge.subVectors(p1,p0),other.subVectors(p2,p0)).length();
      if(rec.areas[i]!>1e-12) {const ratio=area/rec.areas[i]!;minRatio=Math.min(minRatio,ratio);if(ratio<.25)collapse++;}
    }
    if(frame.frame===0||frame.frame===fixture.fps*fixture.secondsPerFamily)assert(neutralError<1e-5,'Neutral endpoint geometry drift');
    stats.push({mesh:m.name,vertices:rec.positions.length/3,triangles:rec.areas.length,quarterAreaFaces:collapse,minimumAreaRatio:minRatio,maximumStoredFrameVertexMotionM:movement,neutralEndpointMaximumComponentErrorM:frame.frame===0||frame.frame===fixture.fps*fixture.secondsPerFamily?neutralError:null});
    rec.previous.set(rec.positions);
  }
  rows.push({family:frame.family,frame:frame.frame,timeSeconds:frame.timeSeconds,stats});previousFamily=frame.family;
}
assert.equal(hash(source),sourceHash);assert.equal(hash(fixturePath),fixtureHash);
const families=fixture.families.map(name=>{
  const subset=rows.filter(r=>r.family===name);return {name,frames:subset.length,maximumQuarterAreaFaces:Math.max(...subset.flatMap(r=>r.stats.map(s=>s.quarterAreaFaces))),maximumStoredFrameVertexMotionM:Math.max(...subset.flatMap(r=>r.stats.map(s=>s.maximumStoredFrameVertexMotionM)))};
});
fs.mkdirSync(path.dirname(out),{recursive:true});
fs.writeFileSync(out,JSON.stringify({kind:'Continuous authored exported Three.js CPU geometry probe; unaccepted',source,sourceSHA256:sourceHash,fixture:fixturePath,fixtureSHA256:fixtureHash,frames:rows.length,maximumWorldMatrixError:maximumMatrixError,families,rows,gates:{continuousGrayTexturedMovies:'UNMEASURED',selfIntersection:'UNMEASURED',gloveCuffJoin:'UNMEASURED',surfaceContacts:'UNMEASURED',appearance:'UNMEASURED',physicalGameplay:'UNMEASURED',mobilePerformance:'UNMEASURED'},limits:['CPU loader omits textures in memory. No GPU, material or visual gate pass.','Stored24fps positions do not certify continuous-time collision or all intermediate poses.','Quarter-area flags identify failure witnesses; neither zero flags nor matrix parity accept anatomy.','Authored fixture is separate from retained physics posing/leaning.']},null,2)+'\n');
console.log(JSON.stringify({frames:rows.length,maximumMatrixError,families}));
