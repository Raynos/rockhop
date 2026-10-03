/** Isolated Rapier cloth; ordinary Game and body skeleton remain kinematic inputs. */
import * as RAPIER from '@dimforge/rapier3d-compat';
import { BufferGeometry, Float32BufferAttribute, Mesh, MeshStandardMaterial, DoubleSide, Vector3, Matrix4, Triangle } from 'three';
const ready=RAPIER.init();
const nativeToFile=p=>new Vector3(p[0]+.65,p[2],-p[1]);
export function liveSleeveTargets(debug,handoff){
  const rider=debug.rider,bodyMesh=rider.sleeveGeometry.find(p=>p.mesh.geometry.attributes.position.count===9981)?.mesh;
  if(!bodyMesh)throw new Error('Exact canonical body template missing');
  rider.scene.updateMatrixWorld(true);bodyMesh.skeleton.update();
  const palette=new Map(bodyMesh.skeleton.bones.map((b,i)=>[b.name,new Matrix4().multiplyMatrices(b.matrixWorld,bodyMesh.skeleton.boneInverses[i])]));
  if(palette.size!==51)throw new Error('Complete native bind missing');
  const skin=(p,weights)=>{const input=nativeToFile(p).applyMatrix4(bodyMesh.bindMatrix),result=new Vector3();let total=0;
    for(const[name,w]of weights){const matrix=palette.get(name.replaceAll('.',''));if(!matrix)throw new Error('Missing collider skin joint '+name);result.addScaledVector(input.clone().applyMatrix4(matrix),w);total+=w;}
    if(Math.abs(total-1)>2e-6)throw new Error('Collider weight sum');return result.multiplyScalar(1/total).applyMatrix4(bodyMesh.bindMatrixInverse).applyMatrix4(bodyMesh.matrixWorld);};
  const pattern=handoff.pattern,body=handoff.nativeConsumedColliders.body;
  const bodyPositions=body.relevantArmVertices.map(v=>skin(v.restNativeM,v.weights)),attribute=bodyMesh.geometry.attributes._source_id;
  if(!attribute)throw new Error('Canonical body ancestry missing');const rows=new Map();for(let i=0;i<attribute.count;i++){const id=attribute.getX(i);if(!rows.has(id))rows.set(id,[]);rows.get(id).push(i);}
  let sourceBodyMaximumResidualM=0,matchedNativeBodyVertices=0;
  for(let i=0;i<body.relevantArmVertices.length;i++){const sourceID=body.relevantArmVertices[i].bodyVertexID,indices=rows.get(sourceID);if(!indices)throw new Error('Collider native body vertex is not visible body '+sourceID);matchedNativeBodyVertices++;
    for(const row of indices)sourceBodyMaximumResidualM=Math.max(sourceBodyMaximumResidualM,bodyMesh.getVertexPosition(row,new Vector3()).applyMatrix4(bodyMesh.matrixWorld).distanceTo(bodyPositions[i]));}
  return{cloth:pattern.verticesNativeM.map((p,i)=>skin(p,pattern.weights[i])),body:bodyPositions,
    skinTemplate:{mesh:bodyMesh.name,bind:bodyMesh.bindMatrix.toArray(),bindInverse:bodyMesh.bindMatrixInverse.toArray(),world:bodyMesh.matrixWorld.toArray(),jointCount:palette.size,matchedNativeBodyVertices,sourceBodyMaximumResidualM}};
}
export function sleeveClearance(cloth,body,handoff){
  const ids=new Map(handoff.nativeConsumedColliders.body.relevantArmVertices.map((v,i)=>[v.bodyVertexID,i])),triangles=handoff.nativeConsumedColliders.body.relevantArmTriangles.map(t=>{
    const p=t.bodyVertexIDs.map(id=>body[ids.get(id)]),normal=p[1].clone().sub(p[0]).cross(p[2].clone().sub(p[0])).normalize();return{triangle:new Triangle(...p),normal,id:t.bodyTriangleID};});
  const samples=cloth.map((p,i)=>({p,kind:'vertex',id:i}));
  for(let i=0;i<handoff.pattern.triangleVertexIDs.length;i++){const p=handoff.pattern.triangleVertexIDs[i].map(id=>cloth[id]);samples.push({p:p[0].clone().add(p[1]).add(p[2]).multiplyScalar(1/3),kind:'centroid',id:i});}
  let minUnsignedM=Infinity,minLocalNormalM=Infinity,witness=null;const closest=new Vector3();
  for(const s of samples){let gap=Infinity,best=null,point=null;for(const t of triangles){t.triangle.closestPointToPoint(s.p,closest);const d=closest.distanceTo(s.p);if(d<gap){gap=d;best=t;point=closest.clone();}}
    const dot=s.p.clone().sub(point).dot(best.normal);minUnsignedM=Math.min(minUnsignedM,gap);if(dot<minLocalNormalM){minLocalNormalM=dot;witness={kind:s.kind,id:s.id,bodyTriangleID:best.id,sampleWorldM:s.p.toArray(),bodyWorldM:point.toArray(),bodyNormal:best.normal.toArray(),unsignedM:gap,localNormalM:dot};}}
  return{samples:samples.length,minUnsignedM,minLocalNormalM,witness,finite:cloth.every(p=>p.toArray().every(Number.isFinite)),
    limits:'Vertex/centroid nearest local face normal and unsigned distance only; open regional collider, not signed-volume or complete triangle intersection proof.'};
}
export async function createSleeveRuntime(debug,handoff,collision,initialTargets,options={}){
  await ready;if(RAPIER.version()!=='0.21.0')throw new Error('Wrong solver version');
  const pattern=handoff.pattern,body=handoff.nativeConsumedColliders.body,world=new RAPIER.World({x:0,y:-9.81,z:0});world.timestep=1/120;
  world.integrationParameters.numSolverIterations=2;world.integrationParameters.numInternalPgsIterations=1;world.integrationParameters.softBodiesMaxExtraSubsteps=2;
  const flat=points=>new Float32Array(points.flatMap(p=>p.toArray())),bodyIds=new Map(body.relevantArmVertices.map((v,i)=>[v.bodyVertexID,i])),bodyIndices=new Uint32Array(body.relevantArmTriangles.flatMap(t=>t.bodyVertexIDs.map(id=>bodyIds.get(id))));
  const colliderTemplate=()=>RAPIER.ColliderDesc.ball(.001).setFriction(.3).setContactSkin(.001);
  const bodyParticleRadiusM=options.bodyParticleRadiusM??.01;
  let bodyDesc=new RAPIER.SoftBodyDesc(flat(initialTargets.body)).setSurface(bodyIndices).setPinnedParticles(Array.from(bodyIds.values())).setGravityScale(0).setShapeMatching(false).setSelfContacts(false).setParticleRadius(bodyParticleRadiusM).setOriented(false).setCanSleep(false);
  bodyDesc=collision?bodyDesc.setSurfaceCollider(colliderTemplate()):bodyDesc.setNoSurfaceCollider();const bodySoft=world.createSoftBody(bodyDesc);
  const hardPins=pattern.sewnAnchorWeights.flatMap((w,i)=>w===1?[i]:[]),halfPins=pattern.sewnAnchorWeights.flatMap((w,i)=>w>0&&w<1?[{id:i,weight:w}]:[]);
  const clothTriangles=new Uint32Array(pattern.triangleVertexIDs.flat());
  // Construct constraints from the authored canonical rest pattern, then assign
  // the independently qualified skinned spawn exactly once, before stepping.
  const authoredRest=pattern.verticesNativeM.map(p=>nativeToFile(p).applyMatrix4(debug.rider.scene.matrixWorld));
  let desc=RAPIER.SoftBodyDesc.trimesh(flat(authoredRest),clothTriangles);if(!desc)throw new Error('Empty sleeve surface');
  desc=desc.setEdges(pattern.edgeRestConstraints.flatMap(e=>e.vertexIDs)).setShapeMatching(false).setVolumePreservation(false).setSoftness(30,1)
    .setParticleMass(handoff.nativeConsumedColliders.cloth.massPerVertexKg).setPinnedParticles(hardPins).setParticleRadius(.001).setSelfContacts(collision).setOriented(false)
    .setLinearDamping(1).setAdditionalPgsIterations(3).setCanSleep(false);
  desc=collision?desc.setSurfaceCollider(colliderTemplate()):desc.setNoSurfaceCollider();const clothSoft=world.createSoftBody(desc);
  for(let i=0;i<initialTargets.cloth.length;i++)clothSoft.setParticlePosition(i,initialTargets.cloth[i]);
  const geometry=new BufferGeometry();geometry.setAttribute('position',new Float32BufferAttribute(flat(initialTargets.cloth),3));geometry.setIndex(Array.from(clothTriangles));geometry.computeVertexNormals();
  const mesh=new Mesh(geometry,new MeshStandardMaterial({color:collision?0x6aa5cf:0xd57b49,roughness:.85,metalness:0,side:DoubleSide}));mesh.name='agent3-live-sleeve-'+(collision?'ON':'OFF');mesh.frustumCulled=false;debug.scene.add(mesh);
  const initialEdges=Array.from({length:clothSoft.numEdges()},(_,i)=>clothSoft.edgeRestLength(i)),pairs=clothSoft.edges();
  const declaredEdges=new Map(pattern.edgeRestConstraints.map(e=>[e.vertexIDs.slice().sort((a,b)=>a-b).join(':'),e.restLengthM]));let restLengthMaximumErrorM=0,checkedStructuralEdges=0;
  for(let i=0;i<clothSoft.numEdges();i++){if(clothSoft.isEdgeBend(i))continue;const key=[pairs[i*2],pairs[i*2+1]].sort((a,b)=>a-b).join(':'),expected=declaredEdges.get(key);if(expected===undefined)throw new Error('Undeclared structural edge '+key);checkedStructuralEdges++;restLengthMaximumErrorM=Math.max(restLengthMaximumErrorM,Math.abs(initialEdges[i]-expected));}
  if(checkedStructuralEdges!==552||restLengthMaximumErrorM>2e-6)throw new Error('Authored structural constraints changed');
  // No normal game input/pose is changed. Only collar anchors are kinematic;
  // the second sewn ring gets a bounded mass-independent spring force.
  let previousTargets=initialTargets.cloth.map(p=>p.clone()),steps=0;
  const step=targets=>{
    const start=performance.now();clothSoft.resetForces(true);
    for(let i=0;i<targets.body.length;i++)bodySoft.setParticleKinematicTarget(i,targets.body[i]);
    for(const id of hardPins)clothSoft.setParticleKinematicTarget(id,targets.cloth[id]);
    for(const{id,weight}of halfPins){const p=clothSoft.particlePosition(id),v=clothSoft.particleVelocity(id),target=targets.cloth[id],prior=previousTargets[id],mass=clothSoft.particleMass(id),omega=2*Math.PI*8;
      const velocity=target.clone().sub(prior).multiplyScalar(120),force=target.clone().sub(new Vector3(p.x,p.y,p.z)).multiplyScalar(omega*omega).sub(new Vector3(v.x-velocity.x,v.y-velocity.y,v.z-velocity.z).multiplyScalar(2*omega));
      force.clampLength(0,100).multiplyScalar(mass*weight);clothSoft.addParticleForce(id,force,true);}
    world.step();previousTargets=targets.cloth.map(p=>p.clone());steps++;
    const positions=clothSoft.particlePositions();if(!positions.every(Number.isFinite))throw new Error('Nonfinite cloth');geometry.attributes.position.array.set(positions);geometry.attributes.position.needsUpdate=true;geometry.computeVertexNormals();
    return{step:steps,solverAndGeometryMs:performance.now()-start,positions:Array.from(positions)};
  };
  return{step,mesh,clothSoft,bodySoft,world,initialEdges,dispose(){debug.scene.remove(mesh);geometry.dispose();mesh.material.dispose();world.free();},
    contract:{rapier:RAPIER.version(),collision,particles:clothSoft.numParticles(),edges:clothSoft.numEdges(),structuralInputEdges:pattern.edgeRestConstraints.length,
      bodyParticles:bodySoft.numParticles(),bodyTriangles:bodyIndices.length/3,clothTriangles:clothTriangles.length/3,hardPins,halfPins,dt:world.timestep,restLengthMaximumErrorM,checkedStructuralEdges,
      solverIterations:2,internalPgs:1,additionalPgs:3,maxExtraSubsteps:2,softnessHz:30,softnessDamping:1,particleMassKg:handoff.nativeConsumedColliders.cloth.massPerVertexKg,bodyParticleRadiusM:bodySoft.particleRadius(),clothParticleRadiusM:clothSoft.particleRadius(),dihedrals:clothSoft.numDihedrals(),
      halfAnchorSpringHz:8,halfAnchorAccelerationCapMPerS2:100,radiusM:.001,colliderSkinM:.001,
      bodyColliderMeshes:bodySoft.numMeshes(),clothColliderMeshes:clothSoft.numMeshes(),selfContacts:collision,
      interGarment:'Single active band; no partner. Shared Rapier world can consume partner deformable surfaces, but assembled inter-garment proof remains open.',
      limits:['Explicit bounded new solver, not a numeric reproduction of Blender cloth parameters.',
        '562 actual weighted arm vertices/1066 triangles form an open regional collider. It must not be called a closed-volume body.',
        'History persists at120Hz; no per-frame particle reset, baked keys, bone displacement or ordinary game physics replacement.']}};
}
