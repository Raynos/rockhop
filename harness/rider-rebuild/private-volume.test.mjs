import test from 'node:test';
import assert from 'node:assert/strict';
import * as THREE from 'three';
import { preparePrivateClipTrack, createPrivateRiderClass, privateStageClipTime } from './private-rider.mjs';
import { sourceDiagnosticKind } from './private-dev-review.mjs';

const metadata = { shapeDerivative: { accepted: false, kind: 'native-relative-shape-key', name: 'A09_SeatedVolume' },
  weightDerivative: { kind: 'native-regional-weight-only' }, accepted: false,
  previewClip: 'Anatomical09VolumeRestKey', qualificationState: 'UNACCEPTED_POSED_VOLUME',
  diagnosticMotion: { accepted: false, previewClip: 'Anatomical09VolumeRestKey', status: 'UNACCEPTED_POSED_VOLUME', kind: 'native-posed-volume' } };

void test('native volume source remains explicit and cannot reuse the failed helper', () => {
  assert.equal(sourceDiagnosticKind(metadata, metadata.previewClip, true), 'native-posed-volume');
  assert.throws(() => sourceDiagnosticKind(metadata, metadata.previewClip, false), /allow-failed-diagnostic/);
  assert.throws(() => sourceDiagnosticKind({ ...metadata, corrective: {} }, metadata.previewClip, true), /failed corrective/);
  assert.throws(() => sourceDiagnosticKind({ ...metadata, shapeDerivative: { ...metadata.shapeDerivative, accepted: true } }, metadata.previewClip, true));
});

void test('actual runtime updates native mesh arrays through rest, key, return and cycle', () => {
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

// A travelling action must retain its final root position across long Garage clocks.
void test('native one-shot actions hold the initial frame and clamp without root teleport', () => {
  const clip = { name: 'RiderJog', duration: .75 };
  const native = { nativeAuthoringMotion: {}, genericActions: { RiderJog: { durationSeconds: .75, leadInSeconds: 2, playback: 'ONCE' } } };
  for (const [clock, expected] of [[10,0],[11.9,0],[12.375,.375],[12.75,.75],[50,.75]]) {
    assert.equal(privateStageClipTime(clip, clock, 10, native), expected);
  }
  const idle = { ...native, genericActions: { RiderJog: { durationSeconds: .75, leadInSeconds: 2, playback: 'LOOP' } } };
  assert.equal(privateStageClipTime(clip, 13, 10, idle), .25);
  assert.throws(() => privateStageClipTime(clip, 13, 10, { nativeAuthoringMotion: {}, genericActions: {} }), /playback/);
});

void test('native library intake permits only the six declared actions and exact presentation', () => {
  const names = ['RiderIdle','RiderWalk','RiderJog','RiderTurn90','RiderJumpLand','RiderRangeOfMotion'];
  const declared = { ...metadata, qualificationState: 'UNACCEPTED_NATIVE_ACTION_LIBRARY',
    nativeAuthoringMotion: { accepted: false, kind: 'native-control-action-library', actions: names.map(name => ({ name })), presentation: { positionBike: [-.6,-.34,.65] } },
    genericActions: { RiderJog: { playback: 'ONCE', leadInSeconds: 2 } } };
  assert.equal(sourceDiagnosticKind(declared, 'RiderJog', true), 'native-authoring-motion11');
  assert.throws(() => sourceDiagnosticKind(declared, 'Unknown', true), /declared/);
  assert.throws(() => sourceDiagnosticKind({ ...declared, corrective: {} }, 'RiderJog', true), /failed corrective/);
  assert.throws(() => sourceDiagnosticKind({ ...declared, genericActions: { RiderJog: { playback: 'LOOP', leadInSeconds: 2 } } }, 'RiderJog', true));
});

void test('native seated bike actions require origin placement and matching bike sources', () => {
  const names = ['RiderBikeSeatedLeanRookie', 'RiderBikeSeatedLeanPro'];
  const bikes = ['rookie', 'pro'].map((name, index) => ({ name, clip: names[index],
    bike: { path: `public/models/bike-${name}.glb`, sha256: String(index).repeat(64) } }));
  const declared = { accepted: false, qualificationState: 'UNACCEPTED_NATIVE_BIKE_ACTION_LIBRARY',
    nativeAuthoringMotion: { accepted: false, kind: 'native-bike-control-action-library', shapeActivation: 0,
      presentation: { positionBike: [0,0,0] }, bikes,
      actions: bikes.map(row => ({ name: row.clip, bike: row.bike })) },
    genericActions: Object.fromEntries(names.map(name => [name, { durationSeconds: 10, playback: 'ONCE', leadInSeconds: 2 }])) };
  assert.equal(sourceDiagnosticKind(declared, names[0], true), 'native-authoring-bike11');
  assert.equal(privateStageClipTime({ name: names[0], duration: 10 }, 100, 1, declared), 10);
  for (const change of [{ shapeActivation: 1 }, { presentation: { positionBike: [-.6,-.34,.65] } },
    { bikes: [bikes[1], bikes[0]] }]) {
    assert.throws(() => sourceDiagnosticKind({ ...declared, nativeAuthoringMotion: { ...declared.nativeAuthoringMotion, ...change } }, names[0], true));
  }
  assert.throws(() => sourceDiagnosticKind({ ...declared, corrective: {} }, names[0], true));
});

void test('actual gameplay review cannot silently select an authored stage action', () => {
  const physical = { accepted: false, qualificationState: 'UNACCEPTED_GAMEPLAY_LEAN_REVIEW',
    gameplayLeanReview: { accepted: false, kind: 'simulated-rider-com-and-torso' } };
  assert.equal(sourceDiagnosticKind(physical, undefined, true), 'actual-gameplay-lean');
  assert.throws(() => sourceDiagnosticKind(physical, 'RiderBikeSeatedLeanRookie', true));
  for (const inherited of [{ previewClip: 'DiagnosticRestKey' }, { nativeAuthoringMotion: {} }, { corrective: {} }]) {
    assert.throws(() => sourceDiagnosticKind({ ...physical, ...inherited }, undefined, true));
  }
});
