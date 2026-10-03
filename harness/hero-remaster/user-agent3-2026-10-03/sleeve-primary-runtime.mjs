/** Fitted skinning is primary; bounded body response changes render vertices. */
import{BufferGeometry,Float32BufferAttribute,Mesh,MeshStandardMaterial,DoubleSide}from'three';
import{partitionArmFaces,closedConvexVolume,projectOutsideVolume}from'./convex-arm-collider.mjs';
export{liveSleeveTargets,sleeveClearance}from'./sleeve-skin-targets.mjs';
const flat=points=>new Float32Array(points.flatMap(p=>p.toArray()));
export function createPrimarySleeve(debug,handoff,collision,initialTargets){
  const pattern=handoff.pattern,parts=partitionArmFaces(handoff),geometry=new BufferGeometry();geometry.setAttribute('position',new Float32BufferAttribute(flat(initialTargets.cloth),3));geometry.setIndex(pattern.triangleVertexIDs.flat());geometry.computeVertexNormals();
  // Exact same material for both passes. Camera/input/bind are capture inputs.
  const mesh=new Mesh(geometry,new MeshStandardMaterial({color:0x6aa5cf,roughness:.85,metalness:0,side:DoubleSide}));mesh.name='agent3-primary-skinned-sleeve';mesh.frustumCulled=false;debug.scene.add(mesh);
  const clearanceM=.002,maximumCorrectionM=.02,passes=3;let positions=flat(initialTargets.cloth),steps=0;
  const step=targets=>{const start=performance.now(),solids=collision?parts.map(part=>closedConvexVolume(targets.body,part)):[],hullDone=performance.now(),output=targets.cloth.map(p=>p.clone()),capped=new Set();let constraintActivations=0;
    for(let pass=0;pass<passes;pass++)for(let i=0;i<output.length;i++)for(const solid of solids){
      // One separating face at >=padding proves that no surface response is needed.
      let plane=-Infinity;for(const f of solid.facets)plane=Math.max(plane,f.normal.dot(output[i])-f.constant);if(plane>=clearanceM)continue;
      const response=projectOutsideVolume(output[i],solid,clearanceM,maximumCorrectionM);if(!response.deltaM)continue;constraintActivations++;
      const delta=response.point.clone().sub(targets.cloth[i]);if(delta.length()>maximumCorrectionM){delta.clampLength(0,maximumCorrectionM);capped.add(i);}if(response.capped)capped.add(i);output[i].copy(targets.cloth[i]).add(delta);
    }
    let maximumDeltaM=0,changedVertices=0,hardAnchorChanged=0;const changedIDs=[];
    for(let i=0;i<output.length;i++){const delta=output[i].distanceTo(targets.cloth[i]);if(delta>1e-9){changedVertices++;changedIDs.push(i);if(pattern.sewnAnchorWeights[i]===1)hardAnchorChanged++;}maximumDeltaM=Math.max(maximumDeltaM,delta);}
    positions=flat(output);if(!positions.every(Number.isFinite))throw new Error('Nonfinite primary geometry');geometry.attributes.position.array.set(positions);geometry.attributes.position.needsUpdate=true;geometry.computeVertexNormals();steps++;
    return{step:steps,positions:Array.from(positions),hullMs:hullDone-start,correctionAndGeometryMs:performance.now()-hullDone,totalMs:performance.now()-start,
      constraintActivations,changedVertices,changedIDs,maximumDeltaM,hardAnchorChanged,cappedVertices:[...capped],solids:solids.map(s=>({part:s.part.name,...s.qualification}))};
  };
  return{step,mesh,getPositions:()=>positions,dispose(){debug.scene.remove(mesh);geometry.dispose();mesh.material.dispose();},contract:{architecture:'Canonical51bind fitted skinning plus bounded consumed body response',collision,vertices:288,triangles:528,parts:parts.map(p=>({name:p.name,sourceVertices:p.rows.length,sourceFaces:p.sourceTriangleIDs.length})),clearanceM,maximumCorrectionM,passes,
    rapierWorld:false,secondaryMotion:false,material:'same blue roughness.85 metalness0 DoubleSide',selfInterGarment:'No consumed self/inter-garment response in this single-band probe; independent finite contacts required before assembled acceptance.',
    limits:['No post hoc checker masquerades as response: active constraints update actual mesh position buffer.',
      'No fullcloth history or dynamics; input skinning is recomputed from the complete native bind each tick.',
      'Correction cap/anchor changes are reported, never treated as fit or arbitrary-pose safety. No player promotion.']}};
}
