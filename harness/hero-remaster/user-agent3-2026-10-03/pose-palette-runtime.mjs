/** Real engine poses as native-point affine maps for same-rest source controls. */
import{Matrix4,Vector3}from'three';
import{liveSleeveTargets}from'./sleeve-skin-targets.mjs';
export function sampleNativePosePalette(debug,handoff){
  const targets=liveSleeveTargets(debug,handoff),body=debug.rider.sleeveGeometry.find(p=>p.mesh.geometry.attributes.position.count===9981)?.mesh;if(!body)throw new Error('Exact body missing');
  const nativeToFile=new Matrix4().set(1,0,0,.65,0,0,1,0,0,-1,0,0,0,0,0,1),skeleton=body.skeleton;
  const matrices=skeleton.bones.map((bone,i)=>new Matrix4().copy(body.matrixWorld).multiply(body.bindMatrixInverse).multiply(bone.matrixWorld).multiply(skeleton.boneInverses[i]).multiply(body.bindMatrix).multiply(nativeToFile));
  const names=skeleton.bones.map(b=>b.name),byName=new Map(names.map((n,i)=>[n,i]));if(names.length!==51||byName.size!==51)throw new Error('Complete native bind absent');
  const apply=(p,weights)=>{const value=new Vector3();let total=0;for(const[name,weight]of weights){const matrix=matrices[byName.get(name.replaceAll('.',''))];if(!matrix)throw new Error('Undeclared native weight joint');value.addScaledVector(new Vector3(...p).applyMatrix4(matrix),weight);total+=weight;}return value.multiplyScalar(1/total);};
  let maximumBodyResidualM=0,maximumGarmentResidualM=0;
  for(const[v,i]of handoff.nativeConsumedColliders.body.relevantArmVertices.map((v,i)=>[v,i]))maximumBodyResidualM=Math.max(maximumBodyResidualM,apply(v.restNativeM,v.weights).distanceTo(targets.body[i]));
  for(let i=0;i<handoff.pattern.verticesNativeM.length;i++)maximumGarmentResidualM=Math.max(maximumGarmentResidualM,apply(handoff.pattern.verticesNativeM[i],handoff.pattern.weights[i]).distanceTo(targets.cloth[i]));
  if(maximumBodyResidualM>2e-12||maximumGarmentResidualM>2e-12)throw new Error('Native affine skin map differs from actual engine');
  const values=matrices.flatMap(m=>m.toArray());if(!values.every(Number.isFinite))throw new Error('Nonfinite native pose map');
  for(const matrix of matrices){const e=matrix.elements;if(Math.abs(e[3])+Math.abs(e[7])+Math.abs(e[11])+Math.abs(e[15]-1)>1e-12)throw new Error('Nonaffine native pose map');}
  return{names,values,maximumBodyResidualM,maximumGarmentResidualM,actualBodySkinResidualM:targets.skinTemplate.sourceBodyMaximumResidualM,physicalPose:debug.rider.debug.physicalPose};
}
