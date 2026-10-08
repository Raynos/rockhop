/** Private actual-engine rider. Author semantics are explicit; player sources stay intact. */
import * as THREE from 'three';
import { clone as cloneSkeleton } from 'three/addons/utils/SkeletonUtils.js';
import { countTriangles, prepareHeroMaterials } from '../../src/render/hero/gltf.ts';
import { makeRiderRigPose, riderRigFromCOM, riderPoseAtLean, RIDER_PROFILE, RIDER_TORSO_REST } from '../../src/core/riderGeometry.ts';
import { bindHumanoidContract, captureHumanoidContract, resetHumanoidPose, setJointWorldQuaternion, solvePalmSocketTarget } from './new-humanoid-contract.mjs';
import { calibrateAnthropometry, invertAnthropometricCOM, measureAnthropometricCOM } from './anthropometric-inverse.mjs';

const V = (...xyz) => new THREE.Vector3(...xyz);
const Q = () => new THREE.Quaternion();
const first = value => Array.isArray(value) ? value[0] : value;
const ids = value => value == null ? [] : Array.isArray(value) ? value : [value];
const fail = (ok, message) => { if (!ok) throw new Error(`Private rider: ${message}`); };
const SIDES = ['left', 'right'];
const suffix = side => side === 'left' ? 'Left' : 'Right';
const sanitize = name => THREE.PropertyBinding.sanitizeNodeName(name);

function loadedSpecification(metadata, scene) {
  const spec = structuredClone(metadata.specification ?? metadata.spec);
  fail(spec, 'Author specification required');
  spec.jointNames = Object.fromEntries(Object.entries(spec.jointNames).map(([id, name]) => [id, sanitize(name)]));
  const parts = {};
  // A declared author object can become a Group of material primitives in GLTFLoader.
  // Resolve its exact node, then enumerate its actual descendants; never infer roles.
  for (const [role, name] of Object.entries(spec.meshNames)) {
    const nodes = scene.getObjectsByProperty('name', sanitize(name));
    fail(nodes.length === 1, `Object ${name}: expected one node`);
    const skins = nodes[0].getObjectsByProperty('isSkinnedMesh', true);
    skins.forEach((skin, index) => { parts[skins.length === 1 ? role : `${role}.primitive${index}`] = skin.name; });
  }
  spec.meshNames = parts;
  for (const hand of Object.values(spec.hands)) hand.socketNodeName = sanitize(hand.socketNodeName);
  return spec;
}

/** Actual rest landmarks define orientation, including mirrored hands. */
function alignPalm(forward, normal, wantedForward, wantedNormal) {
  const basis = (f, n) => {
    const x = f.clone().normalize(), y = n.clone().addScaledVector(x, -n.dot(x)).normalize();
    fail(x.lengthSq() > 0.99 && y.lengthSq() > 0.99, 'Degenerate palm axes');
    return new THREE.Matrix4().makeBasis(x, y, V().crossVectors(x, y));
  };
  return Q().setFromRotationMatrix(basis(wantedForward, wantedNormal).multiply(basis(forward, normal).invert()));
}

export function createPrivateRiderClass(metadata) {
  return class GltfRider {
    root = new THREE.Group();
    placement = new THREE.Group();
    debug = {
      armStretch: [1, 1], legStretch: [1, 1], handOnGrip: [false, false], footOnPeg: [false, false],
      wristErr: [0, 0], gripErr: [0, 0], gripAngleErr: [0, 0], ankleErr: [0, 0], armLen: [0, 0],
      additiveWeight: 0, physicalPose: false, comResidual: 0, ragdollResidual: -1, ragdollBlend: 0,
      ragdollDetail: [], bones: 0, clips: [], stageClip: null, stageBlend: 0, soleErr: [0, 0],
      inheritedSoleErr: [0, 0], soleContactDefinition: [],
      stance: { on: false, pose: 'seated', blend: 0, lean: 0, land: 0, extend: 0, dy: 0, lag: 0, limit: 1 },
      candidate: {}, allBoneFinite: false, fullResetCount: 0,
    };
    stage = false;
    stageTime = 0;
    bike = null;
    release = null;
    physicalRig = makeRiderRigPose();
    restQ = new Map();
    restP = new Map();
    limbs = new Map();
    handTargets = new Map();
    soleFrames = new Map();

    constructor(gltf, lib) {
      fail(metadata.driver?.assetToBikeQuaternionXYZW?.length === 4, 'assetToBikeQuaternionXYZW required');
      this.source = gltf;
      this.scene = cloneSkeleton(gltf.scene);
      this.binding = bindHumanoidContract(this.scene, captureHumanoidContract(this.scene, loadedSpecification(metadata, this.scene)));
      this.roles = this.binding.contract.roles;
      this.driver = metadata.driver;
      for (const role of ['pelvis', 'trunk', 'head', ...SIDES.flatMap(side => ['upperArm', 'forearm', 'wrist', 'thigh', 'shin', 'foot'].map(role => role + suffix(side)))]) {
        fail(ids(this.roles[role]).length, `Role ${role} required`);
      }
      const materialCopies = new Map();
      this.scene.traverse(node => {
        if (!node.isMesh) return;
        const copy = material => {
          if (!materialCopies.has(material)) materialCopies.set(material, material.clone());
          return materialCopies.get(material);
        };
        node.material = Array.isArray(node.material) ? node.material.map(copy) : copy(node.material);
      });
      // No legacy sleeve conditioning: exact author weights are used on this candidate.
      this.materials = prepareHeroMaterials(this.scene, material => lib.complete(material));
      this.triangles = countTriangles(this.scene);
      this.root.name = 'rider:gltf:rebuild';
      this.placement.name = 'rider:author-frame'; this.placement.add(this.scene);
      this.placement.quaternion.fromArray(this.driver.assetToBikeQuaternionXYZW);
      this.root.add(this.placement); this.root.updateWorldMatrix(true, true);
      for (const [id, bone] of this.binding.byId) {
        this.restQ.set(id, bone.getWorldQuaternion(Q()).normalize());
        this.restP.set(id, bone.getWorldPosition(V()));
      }
      for (const side of SIDES) this.calibrateSide(side);
      this.anthropometry = calibrateAnthropometry(this, metadata);
      this.debug.bones = this.binding.byId.size;
      this.debug.clips = gltf.animations.map(clip => clip.name);
      this.debug.candidate = {
        sourceSHA256: metadata.sourceSHA256 ?? null, metadataSHA256: metadata.metadataSHA256 ?? null,
        roles: structuredClone(this.roles), meshRoles: this.binding.meshes.map(({ role, mesh }) => ({ role, name: mesh.name })),
        authorMeshRoles: structuredClone((metadata.specification ?? metadata.spec).meshNames), visibleMeshes: [],
        jointNames: Object.fromEntries([...this.binding.byId].map(([id, bone]) => [id, bone.name])),
        contractSchema: this.binding.contract.schema, geometry: 'Unchanged author FOUR',
        massApproximation: this.anthropometry.approximation,

      };
      this.scene.traverse(node => {
        if (node.isMesh) this.debug.candidate.visibleMeshes.push({ name: node.name, skinned: !!node.isSkinnedMesh, triangles: (node.geometry.index?.count ?? node.geometry.attributes.position.count) / 3 });
      });
      // Garage defaults to the selected bike's contact solver. Authored actions
      // are diagnostic overrides, never an implicit source-contract default.
      const selectedClip = metadata.previewClip ?? (typeof location === 'object' ? new URLSearchParams(location.search).get('riderClip') : null);
      if (selectedClip) {
        const clip = gltf.animations.find(item => item.name === selectedClip);
        fail(clip, `Clip ${selectedClip} required`);
        this.clip = clip;
        this.clipTracks = clip.tracks.map(track => {
          const parsed = THREE.PropertyBinding.parseTrackName(track.name), node = this.binding.exact(parsed.nodeName);
          fail(['position', 'quaternion', 'scale'].includes(parsed.propertyName), `Invalid clip property ${track.name}`);
          return { node, property: parsed.propertyName, interpolant: track.createInterpolant(), original: node[parsed.propertyName].clone() };
        });
      }
    }

    get hasStageMotion() { return true; }
    setStageTime(seconds) { this.stageTime = seconds; }
    setStage(on) {
      this.stage = on;
      this.placement.position.fromArray(on && this.clip ? (this.driver.garagePositionBike ?? [-0.6, -0.34, 0.65]) : [0, 0, 0]);
    }
    setLivery() {}
    detach() { this.placement.removeFromParent(); }
    attach(bike) {
      this.bike = bike; bike.frame.add(this.placement);
      this.placement.position.set(0, 0, 0); this.placement.scale.set(1, 1, 1);
      this.placement.quaternion.fromArray(this.driver.assetToBikeQuaternionXYZW);
      this.release = null; resetHumanoidPose(this.binding);
    }

    bone(id) { return this.binding.byId.get(id); }
    role(name) { return first(this.roles[name]); }
    frameQ() { return this.bike ? this.bike.frame.getWorldQuaternion(Q()).normalize() : Q(); }
    toWorld(point) { return this.bike ? this.bike.frame.localToWorld(point.clone()) : point.clone(); }
    toBike(point) { return this.bike ? this.bike.frame.worldToLocal(point.clone()) : point.clone(); }
    position(id) { return this.toBike(this.bone(id).getWorldPosition(V())); }

    calibrateSide(side) {
      const s = suffix(side), wrist = this.role('wrist' + s), foot = this.role('foot' + s);
      const limb = (kind, upperRole, lowerRole, end) => {
        const upperIds = ids(this.roles[upperRole + s]), lowerIds = ids(this.roles[lowerRole + s]);
        const upper = first(upperIds), lower = first(lowerIds);
        this.limbs.set(kind + s, { upper, lower, end, upperIds, lowerIds,
          lengths: [this.restP.get(upper).distanceTo(this.restP.get(lower)), this.restP.get(lower).distanceTo(this.restP.get(end))] });
      };
      limb('arm', 'upperArm', 'forearm', wrist);
      limb('leg', 'thigh', 'shin', foot);
      const hand = this.binding.contract.hands[side]; fail(hand, `Hand ${side} required`);
      const axes = hand.axesInWrist, wristQ = this.restQ.get(wrist);
      const forward = V().fromArray(axes.forward).applyQuaternion(wristQ), normal = V().fromArray(axes.normal).applyQuaternion(wristQ);
      const alignment = alignPalm(forward, normal, V().fromArray(this.driver.palmForwardBike ?? [1, -0.25, 0]), V().fromArray(this.driver.palmNormalBike ?? [0, -1, 0]));
      const socketLocalQ = Q().setFromRotationMatrix(new THREE.Matrix4().fromArray(hand.socketInWrist)).normalize();
      this.handTargets.set(side, this.driver.gripSocketQuaternionBike?.[side]
        ? Q().fromArray(this.driver.gripSocketQuaternionBike[side]).normalize() : alignment.multiply(wristQ).multiply(socketLocalQ).normalize());
      const soleName = this.driver.soleSocketNames?.[side]; fail(soleName, `Sole socket ${side} required`);
      const sole = this.binding.exact(sanitize(soleName)), footBone = this.bone(foot);
      footBone.updateWorldMatrix(true, true);
      const selected = this.driver.selectedSoleInFoot?.[side];
      const selectedPeg = this.driver.selectedPegSurfaceBike?.[side];
      fail(!!selected === !!selectedPeg, `Sole/peg pair ${side} required`);
      if (selected) {
        fail(selected.length === 16 && selected.every(Number.isFinite), `Invalid selectedSoleInFoot.${side}`);
        fail(selectedPeg.length === 3 && selectedPeg.every(Number.isFinite), `Invalid selectedPegSurfaceBike.${side}`);
      }
      const local = selected ? new THREE.Matrix4().fromArray(selected)
        : footBone.matrixWorld.clone().invert().multiply(sole.matrixWorld);
      fail(Math.abs(local.determinant()) > 1e-6, `Singular sole ${side}`);
      const targetQ = this.driver.soleQuaternionBike?.[side] ? Q().fromArray(this.driver.soleQuaternionBike[side]).normalize()
        : this.restQ.get(foot).clone().multiply(Q().setFromRotationMatrix(local).normalize()).normalize();
      this.soleFrames.set(side, { node: sole, local, targetQ, selectedPeg });
      this.debug.soleContactDefinition.push(selected
        ? 'Selected sole witness/finite peg; surfaces unqualified'
        : 'Anatomy socket; boot surfaces unqualified');
      fail(this.driver.sideZ?.[side] === -1 || this.driver.sideZ?.[side] === 1, `sideZ.${side} must be +/-1`);
      for (const id of Object.values(hand.digits).flat()) {
        const flex = this.driver.digitFlex?.[side]?.[id];
        fail(flex?.axisLocal?.length === 3 && Number.isFinite(flex.maxRadians), `digitFlex.${id} required`);
        fail(Math.abs(V().fromArray(flex.axisLocal).length() - 1) < 1e-5, `Nonunit digitFlex.${id}`);
      }
    }

    setPosition(id, world) {
      const bone = this.bone(id); bone.position.copy(bone.parent ? bone.parent.worldToLocal(world.clone()) : world);
      bone.updateMatrix(); bone.updateWorldMatrix(false, true);
    }

    setWorld(id, quaternion) {
      setJointWorldQuaternion(this.binding, id, quaternion, this.driver.nearSimilarityTolerance ?? 1e-5);
    }

    aim(group, referenceEnd, directionBike) {
      const list = ids(group); if (!list.length) return;
      const restDirection = this.restP.get(referenceEnd).clone().sub(this.restP.get(list[0])).normalize();
      fail(restDirection.lengthSq() > 0.99 && directionBike.lengthSq() > 1e-12, 'Invalid rest/aim axes');
      const swing = Q().setFromUnitVectors(restDirection, directionBike.clone().normalize()), frameQ = this.frameQ();
      for (const id of list) this.setWorld(id, frameQ.clone().multiply(swing).multiply(this.restQ.get(id)));
    }

    solveLimb(limb, targetWorld, poleBike, kind, index) {
      const { upper, lower, upperIds, lowerIds, lengths: [a, b] } = limb;
      const start = this.position(upper), target = this.toBike(V().setFromMatrixPosition(targetWorld));
      const ray = target.clone().sub(start), distance = ray.length(); ray.normalize();
      const pole = poleBike.clone().sub(start).addScaledVector(ray, -poleBike.clone().sub(start).dot(ray));
      fail(distance > 1e-7 && pole.lengthSq() > 1e-10, 'Invalid IK pole'); pole.normalize();
      const reachable = Math.max(Math.abs(a - b) + 1e-7, Math.min(a + b - 1e-7, distance));
      const along = (a * a + reachable * reachable - b * b) / (2 * reachable);
      const middle = start.clone().addScaledVector(ray, along).addScaledVector(pole, Math.sqrt(Math.max(0, a * a - along * along)));
      this.aim(upperIds, lower, middle.clone().sub(start));
      this.aim(lowerIds, limb.end, target.clone().sub(middle));
      const targetQ = Q().setFromRotationMatrix(targetWorld).normalize(); this.setWorld(limb.end, targetQ);
      this.debug[kind + 'Stretch'][index] = distance / (a + b);
      if (kind === 'arm') this.debug.armLen[index] = a + b;
    }

    physicsTarget(frame) {
      if (!this.stage && frame.riderBody.present && this.bike) {
        const cosine = Math.cos(frame.bikeAngle), sine = Math.sin(frame.bikeAngle);
        const com = this.toBike(V(frame.bikeX + frame.riderBody.relX * cosine - frame.riderBody.relY * sine,
          frame.bikeY + frame.riderBody.relX * sine + frame.riderBody.relY * cosine, 0));
        this.bike.frame.updateWorldMatrix(true, false);
        const elements = this.bike.frame.matrixWorld.elements, frameAngle = Math.atan2(elements[1], elements[0]);
        const relative = frame.riderBody.relAngle + frame.bikeAngle - frameAngle;
        const p = riderRigFromCOM(com.x, com.y, RIDER_TORSO_REST + Math.atan2(Math.sin(relative), Math.cos(relative)), this.physicalRig);
        return { ...p, requestedCOM: com };
      }
      const p = riderPoseAtLean(this.stage ? 0 : frame.rider.lean, this.physicalRig);
      if (this.stage) p.torsoAngle += Math.sin(this.stageTime * 2) * 0.008;
      return { ...p, requestedCOM: V(p.com.x, p.com.y, 0) };
    }

    poseRiding(frame) {
      const p = this.physicsTarget(frame), started = performance.now();
      const bound = this.driver.maxSpineFlexRadians ?? 0, candidates = [];
      fail(Number.isFinite(bound) && bound >= 0 && bound <= Math.PI / 9, 'maxSpineFlexRadians outside 0..pi/9');
      const evaluate = (hips, flex) => {
        resetHumanoidPose(this.binding); this.debug.fullResetCount++;
        this.poseFromHips(frame, p, hips, flex);
        return this.toBike(measureAnthropometricCOM(this, this.anthropometry));
      };
      const solve = flex => {
        const inverse = invertAnthropometricCOM(hips => evaluate(hips, flex), p.requestedCOM, [p.hips.x, p.hips.y], 8);
        evaluate(inverse.hips, flex);
        const arm = Math.max(...this.debug.armStretch), leg = Math.max(...this.debug.legStretch);
        const armGapM = Math.max(...this.debug.gripErr), legGapM = Math.max(...this.debug.soleErr);
        const candidate = { flex, inverse, arm, leg, armGapM, legGapM, reach: Math.max(arm, leg), gapM: Math.max(armGapM, legGapM) };
        candidates.push(candidate); return candidate;
      };
      const initial = solve(0);
      if (bound && initial.gapM > 1e-5) {
        const role = initial.arm > initial.leg ? 'arm' : 'leg';
        const edge = solve((role === 'arm' ? -1 : 1) * bound);
        const slope = initial[role] - edge[role];
        solve(edge.flex * (slope > 0 ? Math.min(1, Math.max(0, (initial[role] - 1) / slope)) : 1));

      }
      const feasible = candidates.filter(row => row.gapM <= 0.001 && row.inverse.converged);
      const best = feasible.length ? feasible.sort((a, b) => Math.abs(a.flex) - Math.abs(b.flex))[0]
        : candidates.sort((a, b) => a.gapM - b.gapM)[0];
      const inverse = best.inverse;
      const measuredCOM = evaluate(inverse.hips, best.flex);
      this.debug.comResidual = inverse.residualM;
      this.debug.anthropometry = { ...inverse, requestedCOM: p.requestedCOM.toArray(),
        physicsDimensions: 'XY', measuredCOM: measuredCOM.toArray(), lateralResidualM: measuredCOM.z - p.requestedCOM.z,
        carrierAngle: p.torsoAngle, spineFlexRadians: best.flex, elapsedMs: performance.now() - started,
        articulationRule: 'Least evaluated flex: <=1mm + XY convergence; else least max gap',
        candidateCount: candidates.length,
        candidates: candidates.map(({ flex, gapM, armGapM, legGapM, reach, inverse }) => ({ flex, gapM, armGapM, legGapM, reach, comResidualM: inverse.residualM })),
        palmForwardBike: this.driver.palmForwardBike ?? [1, -0.25, 0],
        contactLimit: 'Socket-only; glove/bar/finger surfaces unqualified' };
      this.debug.physicalPose = !this.stage && !!frame.riderBody.present;
      this.debug.stageClip = this.stage ? 'Riding IK/breathing' : null;
      const lean = this.stage ? 0 : frame.rider.lean;
      Object.assign(this.debug.stance, { on: true, pose: lean < 0 ? 'back' : lean > 0 ? 'forward' : 'seated', blend: Math.abs(lean), lean });
    }

    poseFromHips(frame, p, hips, spineFlex = 0) {
      const torso = V(Math.cos(p.torsoAngle), Math.sin(p.torsoAngle), 0);
      this.setPosition(this.role('pelvis'), this.toWorld(V(hips[0], hips[1], 0)));
      // The declared trunk also contains the pelvis; extra spinal flex must never
      // overwrite the fixed physical pelvis carrier orientation.
      const trunk = ids(this.roles.trunk).filter(id => !ids(this.roles.pelvis).includes(id)), head = this.role('head');
      fail(trunk.length > 0, 'Spine above pelvis required');
      this.aim(this.roles.pelvis, trunk.at(-1), torso);
      this.aim(trunk, head, V(Math.cos(p.torsoAngle + spineFlex), Math.sin(p.torsoAngle + spineFlex), 0));
      const neck = ids(this.roles.neck);
      if (neck.length) this.aim(neck, head, V(Math.cos(p.headAngle), Math.sin(p.headAngle), 0));
      const neckBase = neck[0] ?? trunk.at(-1);
      const headSwing = Q().setFromUnitVectors(this.restP.get(head).clone().sub(this.restP.get(neckBase)).normalize(), V(Math.cos(p.headAngle), Math.sin(p.headAngle), 0));
      this.setWorld(head, this.frameQ().multiply(headSwing).multiply(this.restQ.get(head)));
      SIDES.forEach((side, index) => {
        const sign = this.driver.sideZ[side], s = suffix(side);
        const grip = V(RIDER_PROFILE.grip.x, RIDER_PROFILE.grip.y, sign * RIDER_PROFILE.grip.z);
        const gripWorld = this.bike.frame.matrixWorld.clone().multiply(new THREE.Matrix4().compose(grip, this.handTargets.get(side), V(1, 1, 1)));
        this.solveLimb(this.limbs.get('arm' + s), solvePalmSocketTarget(this.binding, side, gripWorld), V(p.elbow.x, p.elbow.y, sign * p.elbow.z), 'arm', index);
        const sole = this.soleFrames.get(side);
        const inheritedPeg = V(RIDER_PROFILE.peg.x, RIDER_PROFILE.peg.y + 0.011, sign * RIDER_PROFILE.peg.z);
        const peg = sole.selectedPeg ? V().fromArray(sole.selectedPeg) : inheritedPeg;
        const soleWorld = this.bike.frame.matrixWorld.clone().multiply(new THREE.Matrix4().compose(peg, sole.targetQ, V(1, 1, 1)));
        this.solveLimb(this.limbs.get('leg' + s), soleWorld.multiply(sole.local.clone().invert()), V(p.knee.x, p.knee.y, sign * p.knee.z), 'leg', index);
        const hand = this.binding.contract.hands[side];
        for (const id of Object.values(hand.digits).flat()) {
          const flex = this.driver.digitFlex[side][id], bone = this.bone(id);
          bone.quaternion.multiply(Q().setFromAxisAngle(V().fromArray(flex.axisLocal), flex.maxRadians * (frame.crashed ? 0 : 1)));
        }
        this.scene.updateWorldMatrix(true, true);
        const palm = this.binding.exact(hand.socketNodeName);
        this.debug.gripErr[index] = this.toBike(palm.getWorldPosition(V())).distanceTo(grip);
        this.debug.gripAngleErr[index] = palm.getWorldQuaternion(Q()).normalize().angleTo(this.frameQ().multiply(this.handTargets.get(side)));
        this.debug.wristErr[index] = this.debug.gripErr[index]; this.debug.handOnGrip[index] = !frame.crashed && this.debug.gripErr[index] < 0.01;
        const supportWorld = this.bone(this.role('foot' + s)).matrixWorld.clone().multiply(sole.local);
        this.debug.soleErr[index] = this.toBike(V().setFromMatrixPosition(supportWorld)).distanceTo(peg);
        this.debug.inheritedSoleErr[index] = this.toBike(sole.node.getWorldPosition(V())).distanceTo(inheritedPeg);
        this.debug.ankleErr[index] = this.debug.soleErr[index]; this.debug.footOnPeg[index] = this.debug.soleErr[index] < 0.01;
      });
    }

    beginRelease(frame) {
      this.scene.updateWorldMatrix(true, true);
      const pelvis = frame.ragdoll.find(body => body.id === 'pelvis');
      fail(pelvis, 'Ragdoll pelvis required');
      this.release = {
        time: frame.tSim, angles: new Map(frame.ragdoll.map(body => [body.id, body.angle])),
        locals: new Map([...this.binding.byId].map(([id, bone]) => [id, { p: bone.position.clone(), q: bone.quaternion.clone(), s: bone.scale.clone() }])),
        worldQ: new Map([...this.binding.byId].map(([id, bone]) => [id, bone.getWorldQuaternion(Q())])),
        pelvisOffset: this.bone(this.role('pelvis')).getWorldPosition(V()).sub(V(pelvis.pos.x, pelvis.pos.y, 0)),
      };
      this.root.attach(this.placement);
    }

    poseReleased(frame) {
      const release = this.release;
      for (const [id, saved] of release.locals) {
        const bone = this.bone(id); bone.position.copy(saved.p); bone.quaternion.copy(saved.q); bone.scale.copy(saved.s); bone.updateMatrix();
      }
      this.scene.updateWorldMatrix(true, true);
      const targets = new Map();
      for (const body of frame.ragdoll) {
        const delta = Q().setFromAxisAngle(V(0, 0, 1), body.angle - release.angles.get(body.id));
        const roles = body.id === 'pelvis' ? ['pelvis'] : body.id === 'torso' ? ['trunk'] : body.id === 'head' ? ['neck', 'head']
          : SIDES.map(side => body.id + suffix(side));
        for (const role of roles) for (const id of ids(this.roles[role])) targets.set(id, delta.clone().multiply(release.worldQ.get(id)));
        if (body.id === 'pelvis') this.setPosition(this.role('pelvis'), release.pelvisOffset.clone().applyQuaternion(delta).add(V(body.pos.x, body.pos.y, 0)));
      }
      for (const [id] of this.binding.order) if (targets.has(id)) this.setWorld(id, targets.get(id).normalize());
      const open = Math.min(1, Math.max(0, (frame.tSim - release.time) / 0.18));
      for (const hand of Object.values(this.binding.contract.hands)) for (const id of Object.values(hand.digits).flat()) {
        this.bone(id).quaternion.slerp(Q().fromArray(this.binding.rests.get(id).rotationXYZW), open);
      }
      this.debug.physicalPose = false; this.debug.handOnGrip.fill(false); this.debug.footOnPeg.fill(false);
      this.debug.ragdollBlend = 1; this.debug.stageClip = null;
    }

    update(frame) {
      if (!this.bike) return;
      if (this.release && !frame.ragdoll?.length) this.attach(this.bike);
      if (frame.ragdoll?.length && !this.release) {
        resetHumanoidPose(this.binding); this.poseRiding(frame); this.beginRelease(frame);
      }
      resetHumanoidPose(this.binding); this.debug.fullResetCount++;
      for (const track of this.clipTracks ?? []) if (!track.node.isBone) track.node[track.property].copy(track.original);
      if (frame.ragdoll?.length) this.poseReleased(frame);
      else if (this.stage && this.clip) {
        const time = ((this.stageTime % this.clip.duration) + this.clip.duration) % this.clip.duration;
        for (const track of this.clipTracks) track.node[track.property].fromArray(track.interpolant.evaluate(time));
        this.debug.stageClip = this.clip.name; this.debug.physicalPose = false;
        this.debug.handOnGrip.fill(false); this.debug.footOnPeg.fill(false);
      }
      else this.poseRiding(frame);
      this.scene.updateWorldMatrix(true, true);
      this.debug.allBoneFinite = [...this.binding.byId.values()].every(bone => bone.matrixWorld.elements.every(Number.isFinite));
      fail(this.debug.allBoneFinite, 'Nonfinite joint matrix');
    }

    dispose() { for (const material of this.materials) material.dispose(); }
  };
}
