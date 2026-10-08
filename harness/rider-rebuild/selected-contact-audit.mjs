/** Deterministic selected surface/socket audit, no browser, image load, rig edit or acceptance.
 * node harness/rider-rebuild/selected-contact-audit.mjs --source=GLB --contract=JSON --bike=GLB --out=JSON
 */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { Matrix4, Quaternion, Vector3, Ray, Triangle } from 'three';
import { MeshoptDecoder } from 'three/addons/libs/meshopt_decoder.module.js';
const arg = k => process.argv.find(v => v.startsWith(`--${k}=`))?.slice(k.length+3);
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const V = a => new Vector3().fromArray(a), I = () => new Matrix4();
await MeshoptDecoder.ready;
function load(file) {
  const bytes=fs.readFileSync(file), length=bytes.readUInt32LE(12), d=JSON.parse(bytes.subarray(20,20+length));
  assert(bytes.toString('ascii',0,4)==='glTF'); const bin=bytes.subarray(28+length), cache=new Map(), world=[];
  const view = i => {
    if(cache.has(i))return cache.get(i);
    const b=d.bufferViews[i], e=b.extensions?.EXT_meshopt_compression; let raw;
    if(e){raw=new Uint8Array(e.count*e.byteStride);MeshoptDecoder.decodeGltfBuffer(raw,e.count,e.byteStride,bin.subarray(e.byteOffset,e.byteOffset+e.byteLength),e.mode,e.filter);}
    else {assert(b.buffer===0);raw=bin.subarray(b.byteOffset??0,(b.byteOffset??0)+b.byteLength);}
    const dv=new DataView(raw.buffer,raw.byteOffset,raw.byteLength);cache.set(i,dv);return dv;
  };
  const read = i => {
    const a=d.accessors[i], b=d.bufferViews[a.bufferView], dv=view(a.bufferView), components={SCALAR:1,VEC2:2,VEC3:3,VEC4:4,MAT4:16}[a.type];
    assert(!a.sparse);const [method,width,denom]={5121:['getUint8',1,255],5123:['getUint16',2,65535],5125:['getUint32',4,4294967295],5126:['getFloat32',4,1]}[a.componentType];
    return {count:a.count,get:(row,k=0)=>dv[method]((a.byteOffset??0)+row*(b.byteStride??width*components)+k*width,true)/(a.normalized?denom:1),row(row){return Array.from({length:components},(_,k)=>this.get(row,k));}};
  };
  function walk(i,parent=I()) {const n=d.nodes[i], m=n.matrix?I().fromArray(n.matrix):I().compose(V(n.translation??[0,0,0]),new Quaternion().fromArray(n.rotation??[0,0,0,1]),V(n.scale??[1,1,1]));world[i]=parent.clone().multiply(m);for(const c of n.children??[])walk(c,world[i]);}
  for(const i of d.scenes[d.scene??0].nodes)walk(i);
  const node = name => {const i=d.nodes.findIndex(n=>n.name===name);assert(i>=0,name);return {i,n:d.nodes[i],world:world[i],point:new Vector3().setFromMatrixPosition(world[i])};};
  return {d,read,node,sha256:sha(bytes),file};
}
function mesh(g,name,transform=I()) {
  const n=g.node(name), p=g.d.meshes[n.n.mesh].primitives;assert(p.length===1);
  const a=p[0].attributes, pos=g.read(a.POSITION), indices=g.read(p[0].indices), ids=a._NATIVE_ID===undefined?null:g.read(a._NATIVE_ID);
  const matrix=transform.clone().multiply(n.world), joint=a.JOINTS_0===undefined?null:g.read(a.JOINTS_0), weights=a.WEIGHTS_0===undefined?null:g.read(a.WEIGHTS_0);
  const names=g.d.skins?.[n.n.skin]?.joints.map(i=>g.d.nodes[i].name);
  return {pos,indices,point:i=>V(pos.row(i)).applyMatrix4(matrix),id:i=>ids?.get(i)??i,
    fields:i=>joint?Array.from({length:4},(_,k)=>[names[joint.get(i,k)],weights.get(i,k)]).filter(([,w])=>w>0):[],name};
}
function intersections(m,origin,direction,{rows=null,predicate=null}={}) {
  const ray=new Ray(origin,direction), hits=[], a=new Vector3(),b=new Vector3(),c=new Vector3(),point=new Vector3();
  const selected=rows??Array.from({length:m.indices.count/3},(_,i)=>i);
  for(const row of selected){const ids=Array.isArray(row)?row:[0,1,2].map(k=>m.indices.get(row*3+k));a.copy(m.point(ids[0]));b.copy(m.point(ids[1]));c.copy(m.point(ids[2]));if(predicate&&!predicate(a,b,c))continue;
    if(!ray.intersectTriangle(a,b,c,false,point))continue;
    hits.push({triangleRow:Array.isArray(row)?null:row,decodedVertexRows:ids,nativeVertexIDs:ids.map(i=>m.id(i)),point:point.toArray(),normal:new Triangle(a.clone(),b.clone(),c.clone()).getNormal(new Vector3()).toArray(),barycentric:new Triangle(a,b,c).getBarycoord(point,new Vector3()).toArray(),fields:ids.map(i=>m.fields(i)),distance:point.distanceTo(origin)});
  }return hits.sort((a,b)=>a.distance-b.distance);
}
const source=load(arg('source')), bike=load(arg('bike')), contractBytes=fs.readFileSync(arg('contract')), contract=JSON.parse(contractBytes);
assert(source.sha256===contract.glbSHA256,'Exact source contract');
const result={accepted:false,source:{path:source.file,sha256:source.sha256},contract:{path:arg('contract'),sha256:sha(contractBytes)},bike:{path:bike.file,sha256:bike.sha256},recipeSHA256:sha(fs.readFileSync(new URL(import.meta.url))),boots:[],gloves:[],limits:['Source surface audit only; parent must judge played real Garage/game.','Sole patch rays are finite support samples, not a global collision proof.','Palm pad witnesses do not qualify articulated finger wrap or finite bar penetration.']};
const rotation=I().makeRotationFromQuaternion(new Quaternion().fromArray(contract.driver.assetToBikeQuaternionXYZW));
const rear=bike.node('attach_frame_origin').point; // Exact GltfBike source frame shift.
const bikeFrame=I().makeTranslation(-rear.x,-rear.y,-rear.z), pegs=mesh(bike,'pegs',bikeFrame), bar=mesh(bike,'handlebar',bikeFrame);
const gripReport=JSON.parse(fs.readFileSync('docs/evidence/hero-remaster/one-rider-v2/rig-adapter01/bike-grip-surface02/report.json'));
const historicalGrip=gripReport.results.find(r=>r.sourceSHA256===bike.sha256);assert(historicalGrip,'Measured exact bike grip surface source');
for(const [side,suffix]of[['left','L'],['right','R']]) {
  const sign=contract.driver.sideZ[side], sole=source.node(contract.driver.soleSocketNames[side]), boot=mesh(source,'ActualSelectedBoot.'+suffix);
  const target=V([-.14,.031,sign*.2]), samples=[];
  for(const dx of[-.04,0,.04])for(const dz of[-.035,0,.035]){
    const pegOrigin=V([target.x+dx,.15,target.z+dz]), peg=intersections(pegs,pegOrigin,V([0,-1,0]))[0];if(!peg)continue;
    const sourceXZ=V([0,0,0]).add(V([dx,0,dz]).applyMatrix4(rotation.clone().invert())).add(sole.point);
    const soleHit=intersections(boot,V([sourceXZ.x,-.2,sourceXZ.z]),V([0,1,0]))[0];if(!soleHit)continue;
    const placed=V(soleHit.point).sub(sole.point).applyMatrix4(rotation).add(target);
    samples.push({peg,sole:soleHit,currentPlacedSole:placed.toArray(),verticalGapM:placed.y-peg.point[1]});
  }
  assert(samples.length,'Selected boot must intersect inherited sole support footprint');
  const worst=[...samples].sort((a,b)=>a.verticalGapM-b.verticalGapM)[0];
  const foot=source.node('DEF-foot.'+suffix), local=V(worst.sole.point).applyMatrix4(foot.world.clone().invert());
  const selectedSoleInFoot=foot.world.clone().invert().multiply(sole.world).setPosition(local);
  const soleNormalBike=V(worst.sole.normal).transformDirection(rotation);
  const supportNormalsOpposition=soleNormalBike.dot(V(worst.peg.normal).negate());
  result.boots.push({side,object:boot.name,inheritedSolePoint:sole.point.toArray(),driverPegTarget:target.toArray(),supportSamples:samples,maximumSampledPegPenetrationM:Math.max(0,-worst.verticalGapM),measuredSupportPointInFoot:local.toArray(),selectedSoleInFoot:selectedSoleInFoot.toArray(),measuredSoleOutwardNormalBike:soleNormalBike.toArray(),sampledSupportNormalsOpposition:supportNormalsOpposition,orientationPolicy:'Inherited rest orientation retained for isolated translation diagnostic; selected curved sole and finite peg normals recorded, orientation not accepted.',supportPointSource:worst.sole,finitePegPoint:worst.peg,proposedMinimalTranslationBike:[0,Math.max(0,-worst.verticalGapM),0],correctionMeaning:'Move inherited target upward by measured selected outer-sole/actual peg mismatch; preserve rig rest. Or use measured selected supportPointInFoot with the corresponding finitePegPoint target.'});
  const palm=source.node('PalmSocket.'+suffix), wrist=source.node('DEF-hand.'+suffix), spec=contract.specification.hands[side];
  const forward=source.node(spec.forwardJointId).point.clone().sub(wrist.point).normalize();
  const radial=source.node(spec.radialJointId).point.clone().sub(source.node(spec.ulnarJointId).point);radial.addScaledVector(forward,-radial.dot(forward)).normalize();
  const normal=new Vector3().crossVectors(forward,radial).multiplyScalar(spec.normalSign).normalize();
  const glove=mesh(source,'ActualSelectedGlove.'+suffix), outward=intersections(glove,palm.point,normal)[0], inward=intersections(glove,palm.point,normal.clone().negate())[0];
  const grip=V([.27,.78,sign*.33]), old=historicalGrip.grips.find(g=>g.side===(sign>0?'L':'R'));assert(old);
  const barTop=intersections(bar,grip,V([0,1,0]),{rows:old.sourceMeshSurface.triangles})[0];
  result.gloves.push({side,object:glove.name,inheritedPalmPoint:palm.point.toArray(),anatomicalPalmOutwardNormal:normal.toArray(),outwardSurface:outward??null,inwardSurface:inward??null,driverGripAxisTarget:grip.toArray(),finiteBarUpperSurface:barTop??null,palmPadOffsetAlongOutwardM:outward?.distance??null,barSurfaceAboveAxisM:barTop?barTop.point[1]-grip.y:null,supportedContactCorrection:'Anatomical ray hit includes thumb-web articulation, so this is not a rigid palm-pad calibration. Do not apply a hand translation from this ray. Socket-center zero still does not qualify finite surface contact.',unqualifiedOutwardRayPointInWrist:outward?V(outward.point).applyMatrix4(wrist.world.clone().invert()).toArray():null});
}
fs.writeFileSync(arg('out'),JSON.stringify(result,null,2)+'\n');
console.log(JSON.stringify({out:arg('out'),boots:result.boots.map(r=>({side:r.side,maximumSampledPegPenetrationM:r.maximumSampledPegPenetrationM})),gloves:result.gloves.map(r=>({side:r.side,palmPadOffsetAlongOutwardM:r.palmPadOffsetAlongOutwardM,barSurfaceAboveAxisM:r.barSurfaceAboveAxisM}))}));
