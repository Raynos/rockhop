/** Private build overlay only; production GltfRider/physics remain untouched. */
import assert from 'node:assert/strict';
export function patchNewRiderSource(source:string, orthogonalElbowPole = true){
 const replace=(a:string,b:string)=>{assert.equal(source.split(a).length-1,1,'Private adapter source anchor changed: '+a);source=source.replace(a,b);};
 replace('  private readonly q0 = new Map<string, THREE.Quaternion>();',`  private readonly q0 = new Map<string, THREE.Quaternion>();
  private readonly newRiderHandTargetQ = new Map<string, THREE.Quaternion>();
  private readonly newRiderSoleOffsets: (THREE.Vector3 | null)[] = [null, null];
  private readonly newRiderAnkleTargets = [new THREE.Vector3(), new THREE.Vector3()];
  private readonly newRiderLegacyAnkleToSole = new THREE.Vector3();
  private newRiderAnkle(c: Chain, i: number): THREE.Vector3 {
    const offset = this.newRiderSoleOffsets[i];
    return offset ? this.newRiderAnkleTargets[i]!.copy(c.ankle[i]!).add(this.newRiderLegacyAnkleToSole).sub(offset) : c.ankle[i]!;
  }`);
 replace('    holder.remove(this.scene);',`    // Explicit NEW rest-orientation and contact mapping. Captured q0/inverse
    // binds stay intact; physics chain endpoints are read, never rewritten.
    let newAdapter: string | null = null;
    this.scene.traverse(o => { if (typeof o.userData.rockhopRiderContactAdapter === 'string') newAdapter = o.userData.rockhopRiderContactAdapter; });
    if (newAdapter !== null) {
      const metadata = JSON.parse(newAdapter) as { version: number; hands: Record<string, { targetWorldQuaternion: number[]; gripMorphName: string }>; legacyAnkleToSoleDisplacement: number[] };
      if (metadata.version !== 1 || this.bones.size !== 19 || metadata.legacyAnkleToSoleDisplacement.length !== 3 || !metadata.legacyAnkleToSoleDisplacement.every(Number.isFinite)) throw new Error('Invalid private NEW rider mapping');
      this.newRiderLegacyAnkleToSole.fromArray(metadata.legacyAnkleToSoleDisplacement);
      for (const [i, sd] of ['L', 'R'].entries()) {
        const hand = metadata.hands[sd];
        if (!hand || hand.targetWorldQuaternion.length !== 4 || !hand.targetWorldQuaternion.every(Number.isFinite)) throw new Error('Invalid NEW hand quaternion');
        const targetQ = new THREE.Quaternion().fromArray(hand.targetWorldQuaternion);
        if (Math.abs(targetQ.length() - 1) > 1e-5) throw new Error('Nonunit NEW hand quaternion');
        targetQ.normalize();
        const delta = targetQ.clone().multiply(this.q0.get('hand.' + sd)!.clone().invert());
        this.newRiderHandTargetQ.set('hand.' + sd, targetQ);
        this.gripOffsets[i]!.applyQuaternion(delta);
        this.gripRestQ[i]!.premultiply(delta).normalize();
        const foot = this.bones.get('foot.' + sd), sole = this.soleSockets[i];
        if (!foot || !sole || !this.gripSockets[i]) throw new Error('Missing NEW contact node');
        this.newRiderSoleOffsets[i] = sole.getWorldPosition(new THREE.Vector3()).sub(foot.getWorldPosition(new THREE.Vector3()));
        this.scene.traverse(o => { const mesh = o as THREE.Mesh; const index = mesh.morphTargetDictionary?.[hand.gripMorphName]; if (index !== undefined && mesh.morphTargetInfluences) mesh.morphTargetInfluences[index] = 1; });
      }
    }
    holder.remove(this.scene);`);
 replace('      const ankle = c.ankle[i]!;', '      const ankle = this.newRiderAnkle(c, i);');
 replace('this.debug.ankleErr[i] = +this.vc.distanceTo(c.ankle[i]!).toFixed(6);', 'this.debug.ankleErr[i] = +this.vc.distanceTo(this.newRiderAnkle(c, i)).toFixed(6);');
 replace('if (socket) this.setWorld(`hand.${s}`, this.q0.get(`hand.${s}`)!);', 'if (socket) this.setWorld(`hand.${s}`, this.newRiderHandTargetQ.get(`hand.${s}`) ?? this.q0.get(`hand.${s}`)!);');
 replace('const target = arm ? this.wristTarget.copy(c.hand[i]!).sub(this.gripOffsets[i]!) : c.ankle[i]!;', 'const target = arm ? this.wristTarget.copy(c.hand[i]!).sub(this.gripOffsets[i]!) : this.newRiderAnkle(c, i);');
 if (orthogonalElbowPole) replace('if (pole.lengthSq() < 1e-6) pole.set(0.3, -1, i === 0 ? 0.15 : -0.15);', `if (pole.lengthSq() < 1e-6) {
          pole.set(0.3, -1, i === 0 ? 0.15 : -0.15);
          if (this.newRiderHandTargetQ.size) {
            // A two-bone IK pole must remain perpendicular after fallback.
            // Apply only to explicitly mapped NEW anatomy; preserve legacy.
            pole.addScaledVector(dir, -pole.dot(dir));
            if (pole.lengthSq() < 1e-12) { pole.set(1, 0, 0); pole.addScaledVector(dir, -dir.x); }
          }
        }`);
 return source;
}
