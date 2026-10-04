// Source-owned actual-loader outsole bottom surfaces and proposed arch frames.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import {pathToFileURL} from 'node:url';
import * as THREE from 'three';
const [file,nativeFile,output]=process.argv.slice(2),sha=b=>crypto.createHash('sha256').update(b).digest('hex');
if(fs.existsSync(output))throw Error('Frozen sole inventory exists');
const {loadRigAt}=await import(pathToFileURL(path.resolve('src/render/hero/gltfTestUtils.ts')).href);
const gltf=await loadRigAt(pathToFileURL(path.resolve(file)),true);gltf.scene.updateMatrixWorld(true);
const native=JSON.parse(fs.readFileSync(nativeFile)),meshes=[];gltf.scene.traverse(o=>{if(o.isSkinnedMesh)meshes.push(o);});
const sole=meshes.find(m=>m.material.name==='Rubber outsole separate volume');if(!sole)throw Error('Missing constructed rubber outsole');
sole.skeleton.update();const associations=gltf.parser.associations.get(sole),rows=[];let maximumNativeResidual=0;
for(let i=0;i<sole.geometry.attributes.position.count;i++){
 const raw=new THREE.Vector3().fromBufferAttribute(sole.geometry.attributes.position,i),world=sole.localToWorld(sole.getVertexPosition(i,new THREE.Vector3()));
 const point=[raw.x-.65,-raw.z,raw.y],matches=native.vertices.map(r=>({id:r.nativeVertexID,error:Math.hypot(...point.map((v,k)=>v-r.restNativeM[k]))})).filter(r=>r.error<2e-6).sort((a,b)=>a.error-b.error);
 if(matches.length!==1)throw Error('Ambiguous native sole row '+JSON.stringify({i,matches}));
 maximumNativeResidual=Math.max(maximumNativeResidual,matches[0].error);
 const weights={};for(let k=0;k<4;k++){const w=sole.geometry.attributes.skinWeight.array[i*4+k];if(w>0){const name=sole.skeleton.bones[sole.geometry.attributes.skinIndex.array[i*4+k]].name;weights[name]=(weights[name]??0)+w;}}
 rows.push({exportedRow:i,sourceToken:{GLBSHA256:sha(fs.readFileSync(file)),mesh:associations.meshes,primitive:associations.primitives,row:i},nativeBootVertexID:matches[0].id,
  restFileWorldM:raw.toArray(),actualLoadedRestWorldM:world.toArray(),restRuntimeCenteredM:[world.x-.65,world.y,world.z],nativeResidualM:matches[0].error,
  actualLoaderNormalizedWeights:weights,rawNativeWeightSum:native.vertices[matches[0].id].rawWeightSum});
}
const triangles=[];
for(let i=0;i<sole.geometry.index.count/3;i++){
 const ids=[0,1,2].map(k=>sole.geometry.index.getX(i*3+k)),points=ids.map(id=>new THREE.Vector3(...rows[id].actualLoadedRestWorldM));
 const cross=new THREE.Vector3().subVectors(points[1],points[0]).cross(new THREE.Vector3().subVectors(points[2],points[0])),area=cross.length()/2;
 const normal=cross.clone().normalize(),centroid=points[0].clone().add(points[1]).add(points[2]).multiplyScalar(1/3);
 const nativeIDs=ids.map(id=>rows[id].nativeBootVertexID),matches=native.triangles.filter(t=>t.materialSlot===1&&t.nativeVertexIDs.slice().sort((a,b)=>a-b).join(',')===nativeIDs.slice().sort((a,b)=>a-b).join(','));
 if(matches.length!==1)throw Error('Unmapped constructed sole triangle');
 triangles.push({exportedTriangleID:i,exportedRows:ids,nativeBootTriangleID:matches[0].nativeTriangleID,nativeBootPolygonID:matches[0].nativePolygonID,nativeBootVertexIDs:nativeIDs,
  restWorldCentroidM:centroid.toArray(),restWorldGeometricNormal:normal.toArray(),areaM2:area});
}
const sides={};
for(const side of ['L','R']){
 const foot=sole.skeleton.bones.find(b=>b.name==='foot'+side);if(!foot)throw Error('Missing actual foot parent');foot.updateWorldMatrix(true,false);
 const relevant=triangles.filter(t=>t.exportedRows.every(id=>{const w=rows[id].actualLoaderNormalizedWeights;return(w['foot'+side]??0)+(w['ball'+side]??0)+(w['shin'+side]??0)>.5;}));
 const minimumY=Math.min(...relevant.flatMap(t=>t.exportedRows.map(id=>rows[id].restFileWorldM[1])));
 const bottom=relevant.filter(t=>t.restWorldGeometricNormal[1]<-.3&&t.exportedRows.every(id=>Math.abs(rows[id].restFileWorldM[1]-minimumY)<2e-6));
 if(!bottom.length)throw Error('No actual outsole bottom');
 const xs=bottom.flatMap(t=>t.exportedRows.map(id=>rows[id].restFileWorldM[0])),xmin=Math.min(...xs),xmax=Math.max(...xs);
 const arch=bottom.filter(t=>t.restWorldCentroidM[0]>=xmin+.20*(xmax-xmin)&&t.restWorldCentroidM[0]<=xmin+.60*(xmax-xmin));
 if(!arch.length)throw Error('Empty proposed arch surface');
 const area=arch.reduce((s,t)=>s+t.areaM2,0),center=new THREE.Vector3();for(const t of arch)center.addScaledVector(new THREE.Vector3(...t.restWorldCentroidM),t.areaM2/area);
 const local=foot.worldToLocal(center.clone()),footWorld=foot.getWorldQuaternion(new THREE.Quaternion()),localQuaternion=footWorld.clone().invert();
 const matrix=new THREE.Matrix4().compose(local,localQuaternion,new THREE.Vector3(1,1,1));
 const back=foot.matrixWorld.clone().multiply(matrix),residual=new THREE.Vector3().setFromMatrixPosition(back).distanceTo(center);
 if(residual>1e-12)throw Error('Foot-parent marker closure');
 const weights={};for(const t of arch)for(const id of t.exportedRows)for(const [n,w] of Object.entries(rows[id].actualLoaderNormalizedWeights))weights[n]=(weights[n]??0)+w*t.areaM2/area/3;
 sides[side]={actualFootParentName:foot.name,actualFootParentWorldMatrixColumnMajor:foot.matrixWorld.toArray(),actualFootParentWorldQuaternionXYZW:footWorld.toArray(),
  completeOutsoleBottomTriangleIDs:bottom.map(t=>t.exportedTriangleID),proposedArchTriangleIDs:arch.map(t=>t.exportedTriangleID),proposedArchAreaM2:area,
  proposedMarker:{label:'ConstructedBootArchSupport.'+side,parentBone:foot.name,restFileWorldPositionM:center.toArray(),restRuntimeCenteredPositionM:[center.x-.65,center.y,center.z],
   footParentLocalPositionM:local.toArray(),footParentLocalQuaternionXYZW:localQuaternion.toArray(),footParentLocalMatrixColumnMajor:matrix.toArray(),
   preferredRestWorldFrame:'+Xanterior/+Yintofoot/+Zleft; surface outward normal−Y',closureResidualM:residual,areaMeanSurfaceWeights:weights},
  limits:['Complete bottom and proposed20–60%longitudinal arch selection are geometry proposals, not anatomical/peg load-bearing acceptance.',
   'A single parent-foot marker is a rigid-frame proposal; actual skinned surface also follows ball/shin weights and must be evaluated during motion. No source marker injected.']};
}
const report={status:'UNACCEPTED09 source-owned constructedoutsole surfaces/proposedfootparent frames; actualgame/root review required',
 GLBSHA256:sha(fs.readFileSync(file)),nativeInventorySHA256:sha(fs.readFileSync(nativeFile)),recipeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),actualGLTFLoader:true,threeRevision:THREE.REVISION,
 primitive:{name:sole.name,material:sole.material.name,association:associations,vertices:rows.length,triangles:triangles.length},axes:native.axes,
 maximumNativeRowResidualM:maximumNativeResidual,meshWorldMatrixColumnMajor:sole.matrixWorld.toArray(),bindMatrixColumnMajor:sole.bindMatrix.toArray(),bindMatrixInverseColumnMajor:sole.bindMatrixInverse.toArray(),jointOrder:sole.skeleton.bones.map(b=>b.name),rows,triangles,sides,
 sourceNativeWeightSemantics:{rawWeightSumRange:native.rawNativeWeightSumRange,nonUnitNativeWeightVertices:native.nonUnitNativeWeightVertices,
  meaning:'Frozen09 source may contain stale old memberships from its original replacement loop. These records report actual normalized loader weights and current geometry; prior native769fit result remains empirical, not a pure-barycentric field claim.'},
 limits:['Currentconstructedrubber12mm outsole geometry; no05bodyhemisphere/legacybootsource IDs or10rejectedroof geometry.',
  'No normal-player asset promotion, source overwrite, marker injection, body/51bind modification, collider/bodyweights correction or collision-response acceptance.',
  'Coordinates are file-world metres or explicitly centered once. Agent3 must consume current surfaces/footframe semantics and measure actual peg/restart/mobile behavior; root alone judges.']};
fs.writeFileSync(output,JSON.stringify(report,null,2)+'\n');console.log(JSON.stringify({maximumNativeResidual,primitive:report.primitive,sides:Object.fromEntries(Object.entries(sides).map(([s,r])=>[s,{bottom:r.completeOutsoleBottomTriangleIDs.length,arch:r.proposedArchTriangleIDs.length,local:r.proposedMarker.footParentLocalPositionM}]))}));
