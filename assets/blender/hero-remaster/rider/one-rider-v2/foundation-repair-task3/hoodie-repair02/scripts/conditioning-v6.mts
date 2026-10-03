import { writeFile } from 'node:fs/promises';
import { loadRigAt } from '/Users/raynos/projects/games/rockhop/src/render/hero/gltfTestUtils.ts';
import { conditionSleeveSkin } from '/Users/raynos/projects/games/rockhop/src/render/hero/sleeveSkin.ts';
import * as THREE from '/Users/raynos/projects/games/rockhop/node_modules/three/build/three.module.js';

const rows: unknown[] = [];
const witnesses: any[] = [];
const witness = [.6235605,.9135,-.3507394];
for (const name of ['v5', 'v6']) {
  const gltf = await loadRigAt(new URL(name === 'v5' ? '../deliverables/rider-foundation-v5.glb' : '../deliverables/rider-compression-v6.glb', import.meta.url));
  const meshes: any[] = []; gltf.scene.traverse(o => { if ((o as any).isSkinnedMesh) meshes.push(o); });
  const clip = gltf.animations.find(c=>c.name==='hoodie_compression_stand_to_sit' || c.name==='foundation_stand_to_sit') ?? gltf.animations[0];
  const mixer = new THREE.AnimationMixer(gltf.scene), action = mixer.clipAction(clip);
  action.setLoop(THREE.LoopOnce,1); action.clampWhenFinished=true; action.play(); mixer.setTime(clip.duration); gltf.scene.updateMatrixWorld(true);
  for (const [primitive, mesh] of meshes.entries()) {
    const geometry = mesh.geometry, p = geometry.getAttribute('position');
    const beforeWeights = geometry.getAttribute('skinWeight'), beforeIndices = geometry.getAttribute('skinIndex');
    const witnessIds = Array.from({length:p.count},(_,i)=>i).filter(i=>Math.hypot(p.getX(i)-witness[0],p.getY(i)-witness[1],p.getZ(i)-witness[2])<.000001);
    const witnessBefore = witnessIds.map(i=>mesh.getVertexPosition(i,new THREE.Vector3()).applyMatrix4(mesh.matrixWorld).toArray());
    const release = conditionSleeveSkin(mesh);
    const afterWeights = mesh.geometry.getAttribute('skinWeight'), afterIndices = mesh.geometry.getAttribute('skinIndex');
    let changed = 0, hipRoiChanged = 0, maxWeightDelta = 0;
    for (let i = 0; i < p.count; i++) {
      const before = Array(mesh.skeleton.bones.length).fill(0), after = Array(mesh.skeleton.bones.length).fill(0);
      for (let k=0;k<4;k++) {
        before[beforeIndices.getComponent(i,k)] += beforeWeights.getComponent(i,k);
        after[afterIndices.getComponent(i,k)] += afterWeights.getComponent(i,k);
      }
      const delta = Math.max(...before.map((v,j)=>Math.abs(v-after[j])));
      maxWeightDelta = Math.max(maxWeightDelta,delta);
      if (delta > 0.000001) {
        changed++;
        if (p.getY(i) > .69 && p.getY(i) < 1.08 && Math.abs(p.getZ(i)) < .245) hipRoiChanged++;
      }
    }
    rows.push({variant:name,primitive,vertices:p.count,geometry_cloned:mesh.geometry!==geometry,changed_vertices:changed,hip_roi_changed:hipRoiChanged,max_weight_delta:maxWeightDelta});
    witnessIds.forEach((i,k)=>witnesses.push({variant:name,primitive,vertex:i,source_position:[p.getX(i),p.getY(i),p.getZ(i)],before_world_position:witnessBefore[k],after_world_position:mesh.getVertexPosition(i,new THREE.Vector3()).applyMatrix4(mesh.matrixWorld).toArray(),before_weights:Array.from({length:4},(_,j)=>({bone:mesh.skeleton.bones[beforeIndices.getComponent(i,j)].name,weight:beforeWeights.getComponent(i,j)})),after_weights:Array.from({length:4},(_,j)=>({bone:mesh.skeleton.bones[afterIndices.getComponent(i,j)].name,weight:afterWeights.getComponent(i,j)}))}));
    release();
  }
}
const witness_gaps = ['v5','v6'].map(variant=>{const found=witnesses.filter(w=>w.variant===variant);let before=0,after=0;for(const a of found)for(const b of found){before=Math.max(before,new THREE.Vector3(...a.before_world_position).distanceTo(new THREE.Vector3(...b.before_world_position)));after=Math.max(after,new THREE.Vector3(...a.after_world_position).distanceTo(new THREE.Vector3(...b.after_world_position)));}return {variant,matches:found.length,max_before_m:before,max_after_m:after};});
await writeFile(new URL('./conditioning.json',import.meta.url),JSON.stringify({date:'2026-10-01',method:'Actual installed production conditionSleeveSkin, influence comparison by joint rather than slot. Hip ROI raw POSITION y .69..1.08, abs(z)<.245. Cuff witness sampled at actual true sit endpoint.',rows,witness,witnesses,witness_gaps},null,2)+'\n');
console.log(JSON.stringify(rows,null,2));
