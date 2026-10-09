/** Shared pose solver for the authored glTF riders. */
import * as THREE from 'three';
import { BIKE } from '../bike/bikeModel';
import { DEFAULT_OPTS, makeChain, riderChain, type Chain as PoseChain, type ChainOpts } from './pose';

const L = { pelvis: 0.2 };

/** Joint positions of the drawn rider chain in axle (frame-local) coordinates, metres. Index 0 = rider's left (+z, camera side). */
export interface Chain {
  hips: THREE.Vector3;
  pelvisBottom: THREE.Vector3;
  shoulders: THREE.Vector3;
  head: THREE.Vector3;
  /** Head group rotation about z (frame-local). */
  headAngle: number;
  /** Torso lean from +y toward +x (rad). */
  torsoAngle: number;
  shoulder: THREE.Vector3[];
  elbow: THREE.Vector3[];
  hand: THREE.Vector3[];
  hip: THREE.Vector3[];
  knee: THREE.Vector3[];
  ankle: THREE.Vector3[];
}

export interface ChainInput {
  lean: number;
  torsoPitch: number;
  armExtend: number;
  crouch: number;
}

export function newChain(): Chain {
  const pair = (): THREE.Vector3[] => [new THREE.Vector3(), new THREE.Vector3()];
  return { hips: new THREE.Vector3(), pelvisBottom: new THREE.Vector3(), shoulders: new THREE.Vector3(), head: new THREE.Vector3(), headAngle: 0, torsoAngle: 0, shoulder: pair(), elbow: pair(), hand: pair(), hip: pair(), knee: pair(), ankle: pair() };
}

const POSE_OUT: PoseChain = makeChain();
// Physics round 10 (d98236a): `crouch` is the hop preload alone and `torsoPitch` the transient
// only, so the chain's coupling removal is off (it would double-strip).
const POSE_OPTS: ChainOpts = { ...DEFAULT_OPTS, grips: { x: BIKE.grip.x, y: BIKE.grip.y, z: BIKE.gripZ }, pegs: { x: BIKE.pegs.x, y: BIKE.pegs.y, z: BIKE.pegHalfWidth }, seatTop: { x: BIKE.seatTop.x, y: BIKE.seatTop.y }, crouchIsHopOnly: true, torsoPitchLeanBias: 0 };

/**
 * The chain the glTF rig poses from. Round 8: the body is the
 * pose owner's `riderChain` (rider/pose.ts — canonical poses from assets/blender/RIDER_CHAIN.md,
 * curves measured from the reference, and the physics lean→crouch coupling removed), converted
 * to the render's joint set: torsoAngle here is measured from +y toward +x, `headAngle` is the
 * head group's rotation about z. `crouchExtra` (0..1) is the render-driven landing compression.
 */
export function solveChain(r: ChainInput, c: Chain, crouchExtra = 0): Chain {
  POSE_OPTS.crouchExtra = crouchExtra;
  const p = riderChain({ lean: r.lean, crouch: r.crouch, torsoPitch: r.torsoPitch, armExtend: r.armExtend }, POSE_OPTS, POSE_OUT);
  c.hips.set(p.hips.x, p.hips.y, p.hips.z);
  c.shoulders.set(p.shoulders.x, p.shoulders.y, p.shoulders.z);
  c.head.set(p.head.x, p.head.y, p.head.z);
  c.torsoAngle = Math.PI / 2 - p.torsoAngle;
  c.headAngle = -(Math.PI / 2 - p.headAngle);
  const tx = Math.sin(c.torsoAngle);
  const ty = Math.cos(c.torsoAngle);
  c.pelvisBottom.set(p.hips.x - tx * L.pelvis * 0.9, p.hips.y - ty * L.pelvis * 0.9, 0);
  for (let i = 0; i < 2; i++) {
    const S = p.shoulder[i]!;
    const E = p.elbow[i]!;
    const H = p.hand[i]!;
    const HP = p.hipSide[i]!;
    const K = p.knee[i]!;
    const A = p.ankle[i]!;
    c.shoulder[i]!.set(S.x, S.y, S.z);
    c.elbow[i]!.set(E.x, E.y, E.z);
    c.hand[i]!.set(H.x, H.y, H.z);
    c.hip[i]!.set(HP.x, HP.y, HP.z);
    c.knee[i]!.set(K.x, K.y, K.z);
    c.ankle[i]!.set(A.x, A.y, A.z);
  }
  return c;
}
