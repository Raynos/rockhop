/** Full CPU reconstruction checked against all actual fresh34 played bones. */
/* oxlint-disable typescript/no-explicit-any -- frozen diagnostic recordings. */
import fs from 'node:fs';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
import { build } from 'vite';
import { patchFreshC19Source } from './new-rider-fresh-c19-adapter.mjs';
import { loadRigAt } from '../../src/render/hero/gltfTestUtils';
import { prepareHero } from '../../src/render/hero/lod';
import { GltfBike } from '../../src/render/hero/gltfBike';
import { FrameBuilder } from '../../src/render/frame';

const repo = process.cwd();
const argument=(name:string)=>process.argv.find(a=>a.startsWith('--'+name+'='))?.slice(name.length+3);
const source=argument('source'),out=argument('out'),evidence=argument('evidence'),playedFile=argument('played'),fourFile=argument('four'),fourDirectory=argument('four-dir');
assert(source&&out&&evidence&&playedFile&&fourFile&&fourDirectory,'Explicit frozen paths required');
const sha = (b: Buffer) => crypto.createHash('sha256').update(b).digest('hex');
const sourceBytes = fs.readFileSync(source);
const playedBytes = fs.readFileSync(playedFile);
const played = JSON.parse(playedBytes.toString());
assert.equal(played.sourceSHA256, sha(sourceBytes));
assert.equal(played.samples.length, 480);
assert.deepEqual(played.errors, []);
fs.mkdirSync(out, { recursive: true });
fs.mkdirSync(evidence, { recursive: true });
assert(!fs.existsSync(out + '/report.json') && !fs.existsSync(out + '/body0-joint-matrices.f64'), 'Preserve frozen motion outputs');
const bundle = repo + '/harness/out/hero-remaster/physical-surface168-' + sha(Buffer.from(out)).slice(0,12);
await build({ configFile: false, publicDir: false, logLevel: 'error',
  build: { ssr: 'src/render/hero/gltfRider.ts', outDir: bundle, emptyOutDir: true,
    minify: false, rollupOptions: { external: ['three', /^three\//], output: { entryFileNames: 'rider.mjs' } } },
  plugins: [{ name: 'exact-retained-c19-adapter', enforce: 'pre', transform(code, id) {
    return id.toLowerCase().endsWith('/src/render/hero/gltfrider.ts')
      ? { code: patchFreshC19Source(code), map: null } : null;
  } }],
});
const { GltfRider } = await import(pathToFileURL(bundle + '/rider.mjs').href);
(globalThis as any).document = { createElement: () => ({ width: 128, height: 64,
  getContext: () => ({ createRadialGradient: () => ({ addColorStop() {} }), scale() {}, fillRect() {} }) }) };
const lib: any = { complete() {} };
const bikeSource = await loadRigAt(pathToFileURL(repo + '/public/models/bike-rookie.glb'), true);
await prepareHero(bikeSource);
const bike = new GltfBike(bikeSource, lib);
const g = await loadRigAt(pathToFileURL(source), true);
await prepareHero(g);
const rider = new GltfRider(g, lib);
rider.attach(bike);
const meshes: THREE.SkinnedMesh[] = [];
rider.scene.traverse((o: THREE.Object3D) => {
  if ((o as THREE.SkinnedMesh).isSkinnedMesh) meshes.push(o as THREE.SkinnedMesh);
});
const body0 = meshes.find(m => m.name.startsWith('Protected') && !m.name.endsWith('_1') && !m.name.endsWith('_2'));
assert(body0);
assert.equal(body0.skeleton.bones.length, 19);
const histories = new Map(meshes.map(m => [m, new Float64Array(480 * 19 * 16)]));
const frames: any[] = [];
const prefixes=new Float64Array(480*16);
const selected=new Set([35,114,186,304,426,445,446,447]);
const literalFour=JSON.parse(fs.readFileSync(fourFile,'utf8'));
const snapshots:any[]=[];
const save=(name:string,values:number[])=>{const bytes=Buffer.from(new Float64Array(values).buffer);fs.writeFileSync(out+'/'+name+'.f64',bytes);return {file:name+'.f64',bytes:bytes.length,sha256:sha(bytes)};};
const bodywork=bike.root.getObjectByName('bodywork') as THREE.Mesh;assert(bodywork&&bodywork.geometry.index);
const attrs:Record<string,any>={};for(const name of ['position','skinIndex','skinWeight']){const a=body0.geometry.getAttribute(name);attrs[name]={itemSize:a.itemSize,count:a.count,...save('body-'+name,Array.from({length:a.count},(_,i)=>Array.from({length:a.itemSize},(_,j)=>a.getComponent(i,j))).flat())};}
const index=body0.geometry.index;assert(index);const bodyTriangles=save('body-triangles',Array.from({length:index.count},(_,i)=>index.getX(i)));
const bikeTriangles=save('bike-triangles',Array.from({length:bodywork.geometry.index.count},(_,i)=>bodywork.geometry.index!.getX(i)));
let maximumLiteralPositionDifferenceM=0;

let maximumWorldPositionError = 0, maximumQuaternionComponentError = 0;
let maximumBikeFramePositionError = 0;
for (const sample of played.samples) {
  const before = JSON.stringify(sample.state);
  const frame = new FrameBuilder().build(sample.state, 1);
  assert(frame.riderBody.present && !frame.ragdoll, 'This capture covers physical riding only');
  bike.update(frame); rider.update(frame);
  bike.root.updateMatrixWorld(true); rider.scene.updateWorldMatrix(true, true);
  const frameInverse = bike.frame.matrixWorld.clone().invert();
  let worldError = 0, quaternionError = 0, frameError = 0;
  for (const bone of body0.skeleton.bones) {
    const ref = sample.bones[bone.name];
    assert(ref && sample.bonesInBikeFrame[bone.name]);
    const p = bone.getWorldPosition(new THREE.Vector3());
    worldError = Math.max(worldError, p.distanceTo(new THREE.Vector3().fromArray(ref.position)));
    frameError = Math.max(frameError, p.applyMatrix4(frameInverse)
      .distanceTo(new THREE.Vector3().fromArray(sample.bonesInBikeFrame[bone.name])));
    const q = bone.getWorldQuaternion(new THREE.Quaternion()).toArray();
    const componentError = (sign: number) => Math.max(...q.map((v, k) => Math.abs(v - sign * ref.quaternion[k])));
    quaternionError = Math.max(quaternionError, Math.min(componentError(1), componentError(-1)));
  }
  assert(worldError < 1e-10 && frameError < 1e-10 && quaternionError < 1e-10,
    `CPU differs from actual played frame ${sample.i}: ${worldError}/${frameError}/${quaternionError}`);
  maximumWorldPositionError = Math.max(maximumWorldPositionError, worldError);
  maximumQuaternionComponentError = Math.max(maximumQuaternionComponentError, quaternionError);
  maximumBikeFramePositionError = Math.max(maximumBikeFramePositionError, frameError);
  for (const mesh of meshes) {
    assert.equal(mesh.skeleton.bones.length, 19);
    const prefix = frameInverse.clone().multiply(mesh.matrixWorld).multiply(mesh.bindMatrixInverse);
    const values = mesh.skeleton.bones.flatMap((bone, j) => prefix.clone()
      .multiply(bone.matrixWorld).multiply(mesh.skeleton.boneInverses[j]!).multiply(mesh.bindMatrix).elements);
    histories.get(mesh)!.set(values, sample.i * 19 * 16);
    if(mesh===body0){
      prefixes.set(prefix.elements,sample.i*16);
      if(selected.has(sample.i)){
        const p:THREE.BufferAttribute|THREE.InterleavedBufferAttribute=mesh.geometry.getAttribute('position');
        const bp:THREE.BufferAttribute|THREE.InterleavedBufferAttribute=bodywork.geometry.getAttribute('position');
        const values:number[]=Array.from({length:p.count},(_,v)=>mesh.localToWorld(mesh.getVertexPosition(v,new THREE.Vector3())).applyMatrix4(frameInverse).toArray()).flat();
        const reference=literalFour.rows.find((row:any)=>row.i===sample.i);
        let literalDifferenceM:number|null=null;
        if(reference){const record=reference.dump[0].positions;const bytes:Buffer=fs.readFileSync(fourDirectory+'/'+record.file);assert.equal(sha(bytes),record.sha256);const exact=new Float64Array(bytes.buffer,bytes.byteOffset,bytes.byteLength/8);assert.equal(exact.length,values.length);literalDifferenceM=0;for(let j=0;j<values.length;j++)literalDifferenceM=Math.max(literalDifferenceM,Math.abs(exact[j]!-values[j]!));assert(literalDifferenceM<1e-12);maximumLiteralPositionDifferenceM=Math.max(maximumLiteralPositionDifferenceM,literalDifferenceM);}
        snapshots.push({i:sample.i,tick:sample.tick,phase:sample.phase,lean:sample.state.rider.lean,grounded:[sample.state.wheels.rear.grounded,sample.state.wheels.front.grounded],positions:save('sample'+sample.i+'-body',values),bikePositions:save('sample'+sample.i+'-bike',Array.from({length:bp.count},(_,v)=>bodywork.localToWorld(new THREE.Vector3().fromBufferAttribute(bp,v)).applyMatrix4(frameInverse).toArray()).flat()),outerPrefix:prefix.elements.slice(),bindMatrix:mesh.bindMatrix.elements.slice(),morphInfluences:mesh.morphTargetInfluences?.slice(),literalFourPositionMaxDifferenceM:literalDifferenceM,debug:structuredClone(rider.debug)});
      }
    }
  }
  assert.equal(JSON.stringify(sample.state), before);
  frames.push({ i: sample.i, tick: sample.tick, lean: sample.state.rider.lean,
    worldPositionErrorM: worldError, quaternionComponentError: quaternionError,
    bikeFramePositionErrorM: frameError, physicalPose: rider.debug.physicalPose,
    handOnGrip: [...rider.debug.handOnGrip], footOnPeg: [...rider.debug.footOnPeg] });
}
const four = JSON.parse(fs.readFileSync(fourFile, 'utf8'));
let maximumFourKeyMatrixDelta = 0;
for (const row of four.rows) {
  const record = row.dump[0].jointTransforms;
  const bytes:Buffer = fs.readFileSync(fourDirectory + '/' + record.file);
  assert.equal(sha(bytes), record.sha256);
  const expected = new Float64Array(bytes.buffer, bytes.byteOffset, bytes.byteLength / 8);
  const values = histories.get(body0)!.subarray(row.i * 19 * 16, (row.i + 1) * 19 * 16);
  for (let i = 0; i < values.length; i++) maximumFourKeyMatrixDelta = Math.max(maximumFourKeyMatrixDelta, Math.abs(values[i]! - expected[i]!));
}
assert(maximumFourKeyMatrixDelta < 1e-10);
const outputs = meshes.map((mesh, i) => {
  const file = mesh === body0 ? 'body0-joint-matrices.f64' : `mesh${i}-joint-matrices.f64`;
  const bytes = Buffer.from(histories.get(mesh)!.buffer);
  fs.writeFileSync(out + '/' + file, bytes);
  return { mesh: mesh.name, file, bytes: bytes.length, sha256: sha(bytes),
    bones: mesh.skeleton.bones.map(b => b.name), sourceBindMatrix: mesh.bindMatrix.toArray() };
});
assert.equal(sha(fs.readFileSync(source)), sha(sourceBytes));
const prefixOutput=save('body0-outer-prefixes',Array.from(prefixes));
const report = { prefixOutput,attrs,bodyTriangles,bikeTriangles,snapshots,maximumLiteralPositionDifferenceM,compiledRuntimeSHA256:sha(fs.readFileSync(bundle+'/rider.mjs')),kind: 'All480 frozen actual riding states reconstructed with explicit outer prefixes; selected actual Three CPU surfaces',
  captureDependencySHA256: Object.fromEntries([
    'src/render/hero/gltfRider.ts', 'src/render/frame.ts',
    'harness/hero-remaster/new-rider-fresh-c19-adapter.mts',
    'harness/hero-remaster/new-rider-private-adapter.mts',
    'harness/hero-remaster/physical-surface-dump168.mts',
  ].map(file => [file, sha(fs.readFileSync(repo + '/' + file))])),
  sourceSHA256: sha(sourceBytes), sourceUnchanged: true, playedReportSHA256: sha(playedBytes),
  source: playedFile, frames: frames.length, fps: played.fps, matrixOrder: 'frame,bone,column-major4x4Float64LE',
  matricesPrivateDirectory: out, outputs, maximumWorldPositionErrorM: maximumWorldPositionError,
  maximumQuaternionComponentError, maximumBikeFramePositionErrorM: maximumBikeFramePositionError,
  maximumFourKeyMatrixDelta, leanRange: [Math.min(...frames.map(f => f.lean)), Math.max(...frames.map(f => f.lean))],
  physicalPoseEveryFrame: frames.every(f => f.physicalPose), framesChecked: frames,
  limits: ['No geometry or rendering changed; exact currentC19 motion reconstruction only.',
    'Grip/peg booleans are socket diagnostics, not visible surface contact acceptance.',
    'New CPU surfaces and prefixes; no new browser pixels/physics or GPU shader parity. No sitting/Garage/device/appearance acceptance.'] };
fs.writeFileSync(out + '/report.json', JSON.stringify(report) + '\n');
fs.writeFileSync(evidence + '/report.json', JSON.stringify({...report,framesChecked:undefined},null,2)+'\n');
console.log(JSON.stringify({ frames: report.frames, maximumWorldPositionError, maximumQuaternionComponentError,
  maximumBikeFramePositionError, maximumFourKeyMatrixDelta,maximumLiteralPositionDifferenceM,selectedSurfaceFrames:snapshots.length,outputs: outputs.length }));
