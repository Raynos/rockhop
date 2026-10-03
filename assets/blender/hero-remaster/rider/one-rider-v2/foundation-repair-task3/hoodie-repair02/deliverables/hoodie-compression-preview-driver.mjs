/** Isolated clip driver. No production GltfRider, reconditioning, neural retarget, or physics. */
import * as THREE from 'three';
export function createHoodieCompressionPreviewDriver(gltf) {
  const scene=gltf.scene;
  const skins=[];scene.traverse(o=>{if(o.isSkinnedMesh)skins.push(o);});
  if(!skins.length)throw new Error('No skinned meshes');
  const expected=19;
  for(const mesh of skins)if(mesh.skeleton.bones.length!==expected)throw new Error('Unexpected joint count');
  const mixer=new THREE.AnimationMixer(scene);
  let action=null;
  function select(name='hoodie_compression_stand_to_sit') {
    const clip=THREE.AnimationClip.findByName(gltf.animations,name);
    if(!clip)throw new Error(`Missing clip ${name}`);
    mixer.stopAllAction();action=mixer.clipAction(clip);action.setLoop(THREE.LoopOnce,1);action.clampWhenFinished=true;action.play();return clip;
  }
  select();
  function seek(fraction) {
    const clip=action.getClip();action.reset().play();mixer.setTime(THREE.MathUtils.clamp(fraction,0,1)*clip.duration);
    scene.updateMatrixWorld(true);for(const mesh of skins)mesh.skeleton.update();
  }
  return {scene,mixer,select,seek,dispose(){mixer.stopAllAction();mixer.uncacheRoot(scene);}};
}
