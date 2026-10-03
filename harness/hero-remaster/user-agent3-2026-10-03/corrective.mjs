/** Independent decoded-base/support/controller/native-stream admission. */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import crypto from 'node:crypto';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { Matrix4, Vector3 } from 'three';
const [originalFile,candidateFile,driverFile,streamDir,constructionFile,outputFile]=process.argv.slice(2);
assert(outputFile&&!fs.existsSync(outputFile),'Need original/candidate/driver/stream-directory/construction/fresh-output');
const sha=b=>crypto.createHash('sha256').update(b).digest('hex');
const raw=fs.readFileSync(originalFile), bytes=fs.readFileSync(candidateFile), driverBytes=fs.readFileSync(driverFile);
const driver=JSON.parse(driverBytes), expandedBytes=fs.readFileSync(path.join(streamDir,'expanded-driver.json')), expanded=JSON.parse(expandedBytes);
const constructionBytes=fs.readFileSync(constructionFile), construction=JSON.parse(constructionBytes);
assert.equal(sha(raw),driver.conditionedGLBSHA256);assert.equal(sha(bytes),expanded.GLBSHA256);assert.equal(sha(driverBytes),expanded.poseDriverSHA256);
assert.equal(sha(expandedBytes),'ddced495c7ae0218c7ae83f5b47c1d007da137e8d7f05e37e08ae65a9c15d457');
const parse=b=>new GLTFLoader().parseAsync(b.buffer.slice(b.byteOffset,b.byteOffset+b.byteLength),'');
const [original,candidate]=await Promise.all([parse(raw),parse(bytes)]);
original.scene.updateMatrixWorld(true);candidate.scene.updateMatrixWorld(true);
const collect=s=>{const out=[];s.traverse(o=>{if(o.isSkinnedMesh)out.push(o);});return out;};
const before=collect(original.scene),after=collect(candidate.scene);assert.equal(before.length,4);assert.equal(after.length,3);
const json=candidate.parser.json, bones=new Map();
for(const [o,a]of candidate.parser.associations)if(o.isBone&&a.nodes!==undefined)bones.set(json.nodes[a.nodes].name,o);
assert.deepEqual([...bones.keys()].sort((a,b)=>a.localeCompare(b)),[...driver.jointOrderNative].sort((a,b)=>a.localeCompare(b)));
const attributeValues=a=>Array.from({length:a.count*a.itemSize},(_,i)=>a.getComponent(Math.floor(i/a.itemSize),i%a.itemSize));
const digest=a=>sha(Buffer.from(Float64Array.from(attributeValues(a)).buffer));
const conservation=after.map(mesh=>{
  const reference=before.find(m=>m.name===mesh.name);assert(reference,'Mesh identity differs');
  assert.deepEqual(mesh.skeleton.bones.map(b=>[b.name,b.parent.name]),reference.skeleton.bones.map(b=>[b.name,b.parent.name]));
  assert.deepEqual(mesh.skeleton.boneInverses.map(m=>m.toArray()),reference.skeleton.boneInverses.map(m=>m.toArray()));
  assert.deepEqual(mesh.bindMatrix.toArray(),reference.bindMatrix.toArray());assert.deepEqual(mesh.matrixWorld.toArray(),reference.matrixWorld.toArray());
  assert.deepEqual(Object.keys(mesh.geometry.attributes).sort((a,b)=>a.localeCompare(b)),Object.keys(reference.geometry.attributes).sort((a,b)=>a.localeCompare(b)));
  const normals=[];
  for(const [key,a]of Object.entries(mesh.geometry.attributes)){
    const b=reference.geometry.attributes[key];assert.equal(a.count,b.count);assert.equal(a.itemSize,b.itemSize);
    if(digest(a)!==digest(b)){
      assert(key==='normal'&&mesh.name.includes('sweatshirt'),'Unexpected base change '+key);
      const values=attributeValues(a),old=attributeValues(b);
      values.forEach((v,i)=>{if(v!==old[i])normals.push({component:i,old:old[i],current:v,delta:v-old[i]});});
      assert.equal(normals.length,3);assert(Math.max(...normals.map(n=>Math.abs(n.delta)))<.000101);
      assert.equal(new Set(normals.map(n=>Math.floor(n.component/3))).size,1);
    }
  }
  assert.equal(digest(mesh.geometry.index),digest(reference.geometry.index));
  let owner=mesh;while(owner&&owner.userData.rockhopRiderSkinConditioned===undefined)owner=owner.parent;
  assert(owner&&json.nodes[candidate.parser.associations.get(owner)?.nodes]?.name==='Foundation file frame, game x0.65'&&owner.userData.rockhopRiderSkinConditioned===1,'Scoped source conditioning missing');
  return{mesh:mesh.name,vertices:mesh.geometry.attributes.position.count,indicesSHA256:digest(mesh.geometry.index),baseAttributes:Object.fromEntries(Object.entries(mesh.geometry.attributes).map(([k,a])=>[k,digest(a)])),normalException:normals,completeSkinOrderHierarchyBinds:'exactly unchanged',owner:owner.name};
});
function coefficients(frame,config){
  const centers=expanded.centers[config.region];
  const distances=centers.map(center=>Math.sqrt(config.joints.reduce((sum,joint)=>{
    const q=frame.poseBasisBlender[joint].quaternionWXYZ,p=center.jointLocalQuaternionsWXYZ[joint];
    const dot=q.reduce((v,x,i)=>v+x*p[i],0), angle=2*Math.acos(Math.min(1,Math.abs(dot)));
    return sum+angle*angle;
  },0)));
  const closest=Math.min(...distances);
  if(closest<1e-5)return distances.slice(1).map((_,i)=>Number(i+1===distances.indexOf(closest)));
  const weights=distances.map(d=>1/(d*d*d*d)),total=weights.reduce((a,b)=>a+b,0);
  return weights.slice(1).map(w=>w/total);
}
const entries=expanded.configs.map(config=>{
  const row=driver.meshRows.find(r=>r.region===config.region);
  const mesh=after.find(m=>json.nodes[candidate.parser.associations.get(m).nodes].name===row.exportName);assert(mesh);
  const ids=attributeValues(mesh.geometry.attributes._source_id), support=new Set(config.supportIDs);
  assert.equal(support.size,config.region==='cloth'?117:55);assert.equal(config.supportWeights.length,support.size);
  const targets=config.keys.map(name=>{
    const i=mesh.morphTargetDictionary[name],attr=mesh.geometry.morphAttributes.position[i];assert(attr&&mesh.geometry.morphTargetsRelative);
    const native=construction.construction.find(r=>r.key===name),actual=new Set();let residual=0;
    ids.forEach((id,k)=>{
      const v=[attr.getX(k),attr.getY(k),attr.getZ(k)],d=native.deltasNativeM[id],expected=[d[0],d[2],-d[1]];
      residual=Math.max(residual,Math.hypot(...v.map((x,j)=>x-expected[j])));
      if(Math.hypot(...v)>1e-8)actual.add(id);
    });
    assert.deepEqual([...actual].sort((a,b)=>a-b),config.supportIDs);assert(residual<1e-6);
    return{name,index:i,sourceSupport:actual.size,deltaResidualM:residual};
  });
  const streams={};
  for(const kind of ['native-full','native-four']){
    const name=`${config.region}-corrective-${kind}.f64`,data=fs.readFileSync(path.join(streamDir,name)),pin=expanded.pins[name];
    assert.equal(sha(data),pin.sha256);assert.equal(data.length,pin.bytes);assert.equal(data.length,driver.frames.length*row.vertices*24);
    streams[kind]=new DataView(data.buffer,data.byteOffset,data.byteLength);
  }
  return{config,row,mesh,ids,targets,streams,maxParityM:0,maxFullFourM:0,maxPosedMotionM:0,worstParity:null};
});
let coefficientError=0,matrixError=0;const positions=new Vector3();const frames=[];
for(const frame of driver.frames){
  const wanted=new Map([...bones].map(([name,bone])=>[bone,new Matrix4().fromArray(frame.jointWorldColumnMajor[name])]));
  for(const [bone,world]of wanted){bone.matrixAutoUpdate=false;bone.matrix.copy((wanted.get(bone.parent)??bone.parent.matrixWorld).clone().invert().multiply(world));}
  candidate.scene.updateMatrixWorld(true);
  for(const [bone,w]of wanted)matrixError=Math.max(matrixError,...bone.matrixWorld.elements.map((v,i)=>Math.abs(v-w.elements[i])));
  for(const e of entries){
    const values=coefficients(frame,e.config);assert(values.every(Number.isFinite));assert(values.every(v=>v>=0));assert(values.reduce((a,b)=>a+b,0)<=1+1e-12);
    if(frame.index===0)assert(values.every(v=>v===0));
    e.mesh.skeleton.update();e.mesh.morphTargetInfluences.fill(0);
    const base=e.ids.map((_,i)=>e.mesh.getVertexPosition(i,new Vector3()).applyMatrix4(e.mesh.matrixWorld));
    for(let j=0;j<e.targets.length;j++){
      const target=e.targets[j],recorded=expanded.frames[frame.index].coefficients[e.config.region][target.name];
      coefficientError=Math.max(coefficientError,Math.abs(values[j]-recorded));e.mesh.morphTargetInfluences[target.index]=values[j];
    }
    let parity=0,motion=0;
    e.ids.forEach((id,i)=>{
      const offset=(frame.index*e.row.vertices+id)*24;
      e.mesh.getVertexPosition(i,positions).applyMatrix4(e.mesh.matrixWorld);
      const full=[0,1,2].map(k=>e.streams['native-full'].getFloat64(offset+k*8,true));
      const four=[0,1,2].map(k=>e.streams['native-four'].getFloat64(offset+k*8,true));
      const residual=Math.hypot(positions.x-four[0],positions.y-four[1],positions.z-four[2]);
      parity=Math.max(parity,residual);e.maxFullFourM=Math.max(e.maxFullFourM,Math.hypot(...full.map((v,k)=>v-four[k])));
      motion=Math.max(motion,positions.distanceTo(base[i]));
      if(residual>e.maxParityM){e.maxParityM=residual;e.worstParity={frame:frame.index,sourceID:id,exportedRow:i};}
    });
    e.maxPosedMotionM=Math.max(e.maxPosedMotionM,motion);assert(motion<.040);
    frames.push({frame:frame.index,region:e.config.region,parityM:parity,posedMotionM:motion,coefficients:values});
  }
}
assert(matrixError<1e-10&&coefficientError<1e-8);assert(entries.every(e=>e.maxParityM<1e-6));
const report={status:'UNACCEPTED_CORRECTIVE_BASE_SUPPORT_NATIVE_PARITY_CHECKED',candidateSHA256:sha(bytes),originalSHA256:sha(raw),driverSHA256:sha(driverBytes),expandedSHA256:sha(expandedBytes),constructionSHA256:sha(constructionBytes),conservation,frames:driver.frames.length,matrixError,coefficientError,restExactlyZero:true,regions:entries.map(e=>({region:e.config.region,targets:e.targets,maxParityM:e.maxParityM,maxFullFourM:e.maxFullFourM,maxPosedMotionM:e.maxPosedMotionM,worstParity:e.worstParity})),frameMetrics:frames,limits:['Native5-ring graph/mask construction and contact counts remain builder evidence; decoded target membership/deltas independently checked.','One shirt base normal vector changes as explicitly recorded; other base attributes/index and complete skin binds are unchanged.','Explicit diagnostic pose/controller replay only; no production driver, global fit, art/contact/mobile acceptance.']};
fs.mkdirSync(path.dirname(outputFile),{recursive:true});fs.writeFileSync(outputFile,JSON.stringify(report,null,2)+'\n');
console.log(JSON.stringify({status:report.status,frames:report.frames,matrixError,coefficientError,regions:report.regions}));
