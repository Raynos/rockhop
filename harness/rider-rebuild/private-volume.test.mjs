import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { preparePrivateClipTrack, createPrivateRiderClass } from './private-rider.mjs';
import { sourceDiagnosticKind } from './private-dev-review.mjs';

const metadata = { shapeDerivative: { accepted: false, kind: 'native-relative-shape-key', name: 'A09_SeatedVolume' },
  weightDerivative: { kind: 'native-regional-weight-only' }, accepted: false,
  previewClip: 'Anatomical09VolumeRestKey', qualificationState: 'UNACCEPTED_POSED_VOLUME',
  diagnosticMotion: { accepted: false, previewClip: 'Anatomical09VolumeRestKey', status: 'UNACCEPTED_POSED_VOLUME', kind: 'native-posed-volume' } };

test('native volume source remains explicit and cannot reuse the failed helper', () => {
  assert.equal(sourceDiagnosticKind(metadata, metadata.previewClip, true), 'native-posed-volume');
  assert.throws(() => sourceDiagnosticKind(metadata, metadata.previewClip, false), /allow-failed-diagnostic/);
  assert.throws(() => sourceDiagnosticKind({ ...metadata, corrective: {} }, metadata.previewClip, true), /failed corrective/);
  assert.throws(() => sourceDiagnosticKind({ ...metadata, shapeDerivative: { ...metadata.shapeDerivative, accepted: true } }, metadata.previewClip, true));
});

test('actual runtime updates native mesh arrays through rest, key, return and cycle', () => {
  const scene = new THREE.Group(), bone = new THREE.Bone(); bone.name = 'joint'; scene.add(bone);
  const meshes = ['Jeans', 'Body'].map(name => {
    const mesh = new THREE.SkinnedMesh(new THREE.BufferGeometry(), new THREE.MeshBasicMaterial());
    mesh.name = name; mesh.morphTargetDictionary = { A09_SeatedVolume: 0 }; mesh.morphTargetInfluences = [0]; scene.add(mesh); return mesh;
  });
  const byId = new Map([['joint', bone]]), rests = new Map([['joint', { translation: [0, 0, 0], rotationXYZW: [0, 0, 0, 1], scale: [1, 1, 1] }]]);
  const binding = { root: scene, order: [...byId], byId, rests, exact: name => scene.getObjectByName(name) };
  const times = [0, 1, 2, 4, 5, 6], tracks = meshes.map(mesh => new THREE.NumberKeyframeTrack(mesh.name + '.morphTargetInfluences', times, [0, 0, 1, 1, 0, 0]));
  tracks.push(new THREE.VectorKeyframeTrack('joint.position', [0, 2, 4, 6], [0,0,0, 0,1,0, 0,1,0, 0,0,0]));
  const rider = Object.create(createPrivateRiderClass(metadata).prototype);
  Object.assign(rider, { bike: {}, release: null, stage: true, scene, binding, clip: { name: metadata.previewClip, duration: 6 },
    clipTracks: tracks.map(track => preparePrivateClipTrack(track, binding, metadata)),
    debug: { fullResetCount: 0, handOnGrip: [false, false], footOnPeg: [false, false] } });
  const originalArrays = meshes.map(mesh => mesh.morphTargetInfluences);
  for (const [time, weight] of [[0,0],[1.5,.5],[2,1],[4,1],[4.5,.5],[5,0],[6,0],[8,1]]) {
    rider.stageTime = time; rider.update({});
    assert.deepEqual(meshes.map(mesh => mesh.morphTargetInfluences[0]), [weight, weight]);
    meshes.forEach((mesh, i) => assert.equal(mesh.morphTargetInfluences, originalArrays[i]));
    assert(rider.debug.allBoneFinite); assert.equal(rider.applyPoseCorrective, undefined);
  }
  assert.throws(() => preparePrivateClipTrack(tracks[0], binding, {}), /declaration/);
  assert.throws(() => preparePrivateClipTrack(new THREE.NumberKeyframeTrack('Jeans.morphTargetInfluences[0]', [0,1], [0,1]), binding, metadata), /Invalid native volume/);
  meshes.forEach(mesh => { mesh.geometry.dispose(); mesh.material.dispose(); });
});
