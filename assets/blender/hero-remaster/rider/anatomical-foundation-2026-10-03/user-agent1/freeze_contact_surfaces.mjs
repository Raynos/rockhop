// Candidate-local surface proposals; anatomy labels require the parent's played review.
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';
import * as THREE from 'three';
const [file, driverFile, expandedFile, out] = process.argv.slice(2);
const sha = b => crypto.createHash('sha256').update(b).digest('hex');
const bytes = fs.readFileSync(file), doc = JSON.parse(bytes.subarray(20, 20 + bytes.readUInt32LE(12)));
if (sha(bytes) !== 'ecc3bb87b2b9ff934c20345e47b422665f676a23f26a84622b6ec42cc0d42181') throw Error('Expected frozen05');
fs.mkdirSync(out, { recursive: true });
if (fs.existsSync(path.join(out, 'surfaces.json'))) throw Error('Frozen map exists');
const { loadRigAt } = await import(pathToFileURL(path.resolve('src/render/hero/gltfTestUtils.ts')).href);
const gltf = await loadRigAt(pathToFileURL(path.resolve(file)));
gltf.scene.updateMatrixWorld(true);
const meshes = [], bones = [];
gltf.scene.traverse(o => { if (o.isSkinnedMesh) meshes.push(o); if (o.isBone) bones.push(o); });
const jointName = b => doc.nodes[gltf.parser.associations.get(b).nodes].name;
const boneByName = new Map(bones.map(b => [jointName(b), b]));
const point = name => boneByName.get(name).getWorldPosition(new THREE.Vector3());
const pelvis = point('pelvis'), frames = {};
for (const side of ['L', 'R']) {
  const wrist = point('hand.' + side), middle = point('middle_01.' + side);
  const longitudinal = middle.clone().sub(wrist).normalize();
  const lateral = point('index_01.' + side).sub(point('pinky_01.' + side)).normalize();
  const palmar = longitudinal.clone().cross(lateral).normalize();
  const thumbCue = point('thumb_02.' + side).sub(wrist).dot(palmar);
  if (Math.abs(thumbCue) < .002) throw Error('Ambiguous palmar orientation cue');
  if (thumbCue < 0) palmar.negate();
  frames[side] = { wrist, longitudinal, palmar, length: middle.distanceTo(wrist), thumbCue };
}
const proposals = [];
const worldPositions = mesh => {
  mesh.skeleton.update();
  return Array.from({ length: mesh.geometry.attributes.position.count }, (_, i) => {
    const p = mesh.getVertexPosition(i, new THREE.Vector3()); return mesh.localToWorld(p);
  });
};
for (const mesh of meshes) {
  const association = gltf.parser.associations.get(mesh), mi = association.meshes;
  if (![0, 1, 4, 5].includes(mi)) continue;
  const geometry = mesh.geometry, positions = worldPositions(mesh), jointNames = mesh.skeleton.bones.map(jointName);
  const weights = id => Array.from({ length: 4 }, (_, k) => ({ jointIndex: geometry.attributes.skinIndex.array[id * 4 + k],
    joint: jointNames[geometry.attributes.skinIndex.array[id * 4 + k]], weight: geometry.attributes.skinWeight.array[id * 4 + k] }));
  const mass = (id, predicate) => weights(id).reduce((s, r) => s + (predicate(r.joint) ? r.weight : 0), 0);
  const surfaces = [];
  if (mi === 0 || mi === 4) for (const side of ['L', 'R']) surfaces.push({ label: (mi === 4 ? 'glove' : 'body') + '-palm-' + side, side, kind: 'palm', color: side === 'L' ? [1, .15, .06] : [.05, .55, 1] });
  if (mi === 0 || mi === 5) for (const side of ['L', 'R']) surfaces.push({ label: (mi === 5 ? 'boot' : 'body') + '-sole-' + side, side, kind: 'sole', color: side === 'L' ? [.95, .65, .03] : [.25, 1, .1] });
  if (mi === 1) surfaces.push({ label: 'jeans-posterior-seat', kind: 'seat', color: [.9, .05, 1] });
  for (const surface of surfaces) {
    const triangles = [];
    const minimumY = Math.min(...positions.filter(p => surface.kind !== 'sole' || (surface.side === 'L' ? p.z > 0 : p.z < 0)).map(p => p.y));
    for (let ti = 0; ti < geometry.index.count / 3; ti++) {
      const ids = [0, 1, 2].map(k => geometry.index.getX(ti * 3 + k)), p = ids.map(i => positions[i]);
      const center = p[0].clone().add(p[1]).add(p[2]).multiplyScalar(1 / 3);
      const normal = p[1].clone().sub(p[0]).cross(p[2].clone().sub(p[0])).normalize();
      let selected = false;
      if (surface.kind === 'palm') {
        const frame = frames[surface.side], delta = center.clone().sub(frame.wrist), along = delta.dot(frame.longitudinal);
        const ownership = ids.reduce((s, i) => s + mass(i, n => n === 'hand.' + surface.side || /^(index|middle|ring|pinky|thumb)_\d\d\./.test(n) && n.endsWith('.' + surface.side)), 0) / 3;
        selected = ownership >= .5 && along >= .008 && along <= frame.length * .94 && normal.dot(frame.palmar) > .25;
      } else if (surface.kind === 'sole') {
        const ownership = ids.reduce((s, i) => s + mass(i, n => ['foot.' + surface.side, 'ball.' + surface.side].includes(n)), 0) / 3;
        selected = ownership >= .5 && normal.y < -.3 && center.y <= minimumY + .03;
      } else {
        const ownership = ids.reduce((s, i) => s + mass(i, n => n === 'pelvis' || n.startsWith('thigh.')), 0) / 3;
        selected = ownership >= .5 && normal.x < -.3 && center.x < pelvis.x && center.y >= pelvis.y - .19 && center.y <= pelvis.y + .04 && Math.abs(center.z) < .17;
      }
      if (selected) triangles.push({ triangleID: ti, vertexIDs: ids, sourceIDs: geometry.attributes._source_id ? ids.map(i => geometry.attributes._source_id.getX(i)) : null,
        fileWorldCentroidM: center.toArray(), fileWorldOutwardNormal: normal.toArray() });
    }
    if (!triangles.length) throw Error('Empty anatomical proposal: ' + surface.label);
    const ids = [...new Set(triangles.flatMap(t => t.vertexIDs))].sort((a, b) => a - b);
    proposals.push({ ...surface, source: { mesh: mi, primitive: association.primitives,
      node: association.nodes ?? doc.nodes.findIndex(n => n.mesh === mi), meshName: doc.meshes[mi].name, actualLoaderName: mesh.name },
      matrixWorldColumnMajor: mesh.matrixWorld.toArray(), bindMatrixColumnMajor: mesh.bindMatrix.toArray(),
      bindMatrixInverseColumnMajor: mesh.bindMatrixInverse.toArray(), jointOrder: jointNames,
      inverseBindSHA256: sha(Buffer.from(new Float64Array(mesh.skeleton.boneInverses.flatMap(m => m.toArray())).buffer)),
      sourceIDAncestry: geometry.attributes._source_id ? 'Current05 attribute _SOURCE_ID; no legacy mapping borrowed' : 'No _SOURCE_ID on donor-derived gear; exact current05 exported primitive row IDs only',
      vertices: ids.map(i => ({ vertexID: i, sourceID: geometry.attributes._source_id?.getX(i) ?? null,
        rawPositionM: new THREE.Vector3().fromBufferAttribute(geometry.attributes.position, i).toArray(),
        actualRestMeshLocalM: mesh.getVertexPosition(i, new THREE.Vector3()).toArray(), fileWorldM: positions[i].toArray(),
        centeredRuntimeM: positions[i].clone().sub(new THREE.Vector3(.65, 0, 0)).toArray(), weights: weights(i) })), triangles });
  }
}
const report = { status: 'UNACCEPTED05 candidate-local labeled contact surface proposals, parent visual review pending',
  candidateGLBSHA256: sha(bytes), parent04GLBSHA256: 'ac64e79a6a2e7595a01a2da9d714df78ee7058d9a22dcc5ecf24915f8085dfdd',
  parent04to05Ancestry: 'All BIN bytes identical; full primitive row/index/morph/UV/skin ancestry exact. Defaults/root label differ.',
  recipeSHA256: sha(fs.readFileSync(new URL(import.meta.url))), actualGLTFLoader: true, threeRevision: THREE.REVISION,
  axes: { units: 'metres', glTF: '+X forward, +Y up, +Z left', native: '+X forward, +Z up, -Y left', fileRootX: .65,
    runtimeCenterOnce: [-.65, 0, 0], fileWorldToNativeWorld: '[x,-z,y]', fileWorldToNativeCentered: '[x-.65,-z,y]' },
  LOD: { available: false, mapping: null, limitation: 'No05 LOD asset; historical rider LOD fields are not ancestry evidence.' },
  selection: { palms: 'Current wrist/middle MCP longitudinal axis crossed with index-pinky MCP lateral axis; sign toward thumb02 out-of-plane cue. Mean own hand/finger mass>=.5, proximal longitudinal interval .008m..94%MCP length, outward normal dot>.25.',
    soles: 'Current side foot/ball mass>=.5, outward normal up-dot<-.3, centroid within30mm of current source side minimum height.',
    seat: 'Jeans posterior triangle normal -X>.3; pelvis/thigh mass>=.5, centroid behind own pelvis, y pelvis-.19..+.04m, |z|<.17m.',
    parentJudgment: 'Automatic anatomical selection proposes patches; played labeled binding receipt must be judged before acceptance.' },
  handFrames: Object.fromEntries(Object.entries(frames).map(([s, f]) => [s, { wristFileWorldM: f.wrist.toArray(), longitudinal: f.longitudinal.toArray(), proposedPalmarNormal: f.palmar.toArray(), MCPDistanceM: f.length, signedThumbCueM: f.thumbCue }])),
  surfaces: proposals, limits: ['Gear and underlying anatomy are separate proposals; glove/boot coverage and garment fit are unaccepted.', 'These are real current triangles, not bone-point substitutes. Bike grips/pegs/saddle are Agent3 targets and are not guessed here.', 'No supported-bike, penetration, closed-volume, visual-art or device pass.'] };
fs.writeFileSync(path.join(out, 'surfaces.json'), JSON.stringify(report, null, 2) + '\n', { flag: 'wx' });
const driver = JSON.parse(fs.readFileSync(driverFile)), expanded = JSON.parse(fs.readFileSync(expandedFile));
const sampled = [];
for (let index = 0; index < driver.frames.length; index += 8) {
  const frame = driver.frames[index];
  for (const bone of bones) {
    const desired = new THREE.Matrix4().fromArray(frame.jointWorldColumnMajor[jointName(bone)]);
    bone.parent.updateWorldMatrix(true, false); bone.matrixAutoUpdate = false;
    bone.matrix.copy(bone.parent.matrixWorld).invert().multiply(desired); bone.matrixWorldNeedsUpdate = true; bone.updateWorldMatrix(false, false, true);
  }
  gltf.scene.updateMatrixWorld(true);
  for (const mesh of meshes) {
    if (mesh.morphTargetInfluences) {
      const region = mesh.morphTargetInfluences.length === 3 ? 'cloth' : 'jeans'; mesh.morphTargetInfluences.fill(0);
      for (const [key, value] of Object.entries(expanded.frames[index].coefficients[region])) mesh.morphTargetInfluences[mesh.morphTargetDictionary[key]] = value;
    }
    mesh.skeleton.update();
  }
  sampled.push({ driverFrame: index, patches: proposals.map(surface => {
    const mesh = meshes.find(m => { const a = gltf.parser.associations.get(m); return a.meshes === surface.source.mesh && a.primitives === surface.source.primitive; });
    return { label: surface.label, positionsFileWorldM: surface.vertices.map(v => mesh.localToWorld(mesh.getVertexPosition(v.vertexID, new THREE.Vector3())).toArray()) };
  }) });
}
const played = { status: 'Exact05 evaluated patch streams for labeled diagnostic film, no target contacts', candidateGLBSHA256: report.candidateGLBSHA256,
  surfaceMapSHA256: sha(fs.readFileSync(path.join(out, 'surfaces.json'))), poseDriverSHA256: sha(fs.readFileSync(driverFile)), expandedDriverSHA256: sha(fs.readFileSync(expandedFile)),
  sampleStride: 8, frames: sampled };
fs.writeFileSync(path.join(out, 'played-surfaces.json'), JSON.stringify(played) + '\n', { flag: 'wx' });
console.log(JSON.stringify({ mapSHA256: played.surfaceMapSHA256, frames: sampled.length, surfaces: proposals.map(p => ({ label: p.label, vertices: p.vertices.length, triangles: p.triangles.length })) }));
