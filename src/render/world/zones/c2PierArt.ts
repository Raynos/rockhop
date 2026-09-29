/** C2's two playable harbour set pieces. Geometry is scenery only; colliders stay in the track. */
import * as THREE from 'three';
import type { CompiledTrack } from '../../../core/types';
import { ao, beam, box, merge, paint, rgb } from './geo';
import { profileY } from '../track';

const steel = rgb(0x31565b);
const edge = rgb(0x203f45);
const wet = rgb(0x274247);
const timber = rgb(0x765b3d);
const orange = rgb(0xc37b2e);
const chalk = rgb(0xe3d5b7);

/** Open trestle under the actual Pier 2 ramp, deck and fall (x 103–137). */
export function c2PierTrestleGeometry(): THREE.BufferGeometry {
  const p: THREE.BufferGeometry[] = [];
  // Local origin is x=119. The ride surface stays visible through the open frame.
  for (const z of [-3.1, 3.15]) {
    p.push(box(36, 0.32, 0.28, 1, -0.54, z, steel));
    p.push(box(36, 0.16, 0.42, 1, -1.28, z, edge));
    for (let x = -15; x <= 17; x += 4) {
      p.push(box(0.32, 2.7, 0.34, x, -1.45, z, x % 8 ? timber : steel));
      if (x < 17) p.push(beam(x, -2.54, z, x + 4, -0.8, z, 0.17, edge));
      p.push(box(0.46, 0.18, 0.54, x, -0.34, z, orange));
    }
  }
  // Cross ties show the road as a supported dock instead of a floating slab.
  for (let x = -15; x <= 17; x += 4) {
    p.push(box(0.23, 0.19, 6.6, x, -0.68, 0, timber));
    p.push(beam(x, -2.38, -3.1, x + 2, -0.76, 3.15, 0.12, steel));
  }
  // Mooring dolphins and fenders sit below the tire plane on the camera side.
  for (const x of [-15, -3, 9, 17]) {
    p.push(box(0.55, 3.5, 0.55, x, -1.73, 4.25, timber));
    p.push(box(0.82, 0.32, 0.7, x, -0.25, 4.25, wet));
    p.push(box(0.62, 0.54, 0.15, x, -0.9, 4.66, edge));
  }
  return ao(merge(p), 4, 0.2);
}

/** Plated barge side follows the final ramp, roof and down ramp's real contact polyline. */
export function c2LandingFasciaGeometry(track: CompiledTrack): THREE.BufferGeometry {
  const p: THREE.BufferGeometry[] = [];
  // These three colliders are the authored final landing (not a second approximated surface).
  const byX = new Map<number, number>();
  for (const placed of track.placed) if (placed.pos.x >= 311 && placed.pos.x < 338) {
    for (const id of placed.colliderIds) {
      const collider = track.colliders.find((c) => c.id === id);
      if (collider?.kind === 'polyline') for (const pt of collider.points) byX.set(pt.x, pt.y);
    }
  }
  const top = [...byX].sort((a, b) => a[0] - b[0]);
  if (top.length < 4) throw new Error('C2 final landing has no continuous collider profile');
  const bottom = Math.min(...top.map(([x]) => profileY(track.def.profile, x))) - 2.5;
  const yAt = (x: number): number => {
    for (let i = 1; i < top.length; i++) if (x <= top[i]![0]) {
      const a = top[i - 1]!, b = top[i]!;
      return a[1] + (b[1] - a[1]) * (x - a[0]) / (b[0] - a[0]);
    }
    return top[top.length - 1]![1];
  };
  const shape = new THREE.Shape();
  shape.moveTo(top[0]![0], top[0]![1] - 0.06);
  for (const [x, y] of top.slice(1)) shape.lineTo(x, y - 0.06);
  shape.lineTo(top[top.length - 1]![0] - 0.5, bottom);
  shape.lineTo(top[0]![0] + 0.5, bottom);
  shape.closePath();
  const side = new THREE.ExtrudeGeometry(shape, { depth: 0.14, bevelEnabled: false });
  side.translate(0, 0, 1.54); // obstacle skirts have a 3 m depth, so their near face is z=1.5
  p.push(paint(side, rgb(0x29454a), (_x, y) => y < bottom + 0.55 ? 0.72 : 1));
  for (let i = 1; i < top.length; i++) {
    const a = top[i - 1]!, b = top[i]!;
    p.push(beam(a[0], a[1] - 0.13, 1.77, b[0], b[1] - 0.13, 1.77, 0.12, chalk));
  }
  for (let x = top[0]![0] + 1; x < top[top.length - 1]![0] - 0.5; x += 2.4) {
    const high = yAt(x) - 0.22;
    p.push(box(0.1, high - bottom - 0.2, 0.1, x, (high + bottom) / 2, 1.76, steel));
    p.push(box(0.34, 0.18, 0.15, x, high - 0.42, 1.83, wet));
  }
  p.push(box(top[top.length - 1]![0] - top[0]![0] - 1.4, 0.15, 0.14,
    (top[0]![0] + top[top.length - 1]![0]) / 2, bottom + 0.78, 1.78, orange));
  for (const x of [315, 324, 333]) {
    p.push(paint(new THREE.TorusGeometry(0.32, 0.11, 6, 12).translate(x, yAt(x) - 1.05, 1.9), rgb(0x252b2b)));
  }
  return ao(merge(p), 3.5, 0.13, bottom).translate(-320, 0, 0);
}

/** Harbour jib crane over the actual kicker and barge gap, seen from the riding side. */
export function c2JumpCraneGeometry(): THREE.BufferGeometry {
  const p: THREE.BufferGeometry[] = [];
  // The tower is placed at world x=299, behind the road at z=-8.
  for (const x of [-2, 2]) {
    p.push(box(0.66, 12.5, 0.72, x, 6.25, 0, steel));
    p.push(beam(x, 1.1, 0, -x, 11.8, 0, 0.24, edge));
  }
  for (let y = 2.4; y <= 11; y += 2.4) p.push(box(4.6, 0.24, 0.48, 0, y, 0, orange));
  p.push(box(7, 1.0, 5, 0, 12.4, 0, steel));
  p.push(box(5.2, 2.5, 3.4, -0.2, 14.1, 0, chalk));
  p.push(box(4.4, 0.7, 0.1, -0.2, 14.4, 1.76, wet));
  // Open lattice boom points along the flight rather than disappearing into camera depth.
  p.push(beam(0, 13.6, 0, 26, 17.6, 0, 0.52, orange));
  p.push(beam(0, 15.3, 0, 26, 17.6, 0, 0.27, orange));
  for (let i = 0; i <= 5; i++) {
    const x = i * 5;
    const low = 13.6 + x * 4 / 26;
    const high = 15.3 + x * 2.3 / 26;
    p.push(beam(x, low, 0, x + 5, high + 0.44, 0, 0.12, edge));
  }
  p.push(beam(-1, 17.6, 0, 26, 17.6, 0, 0.11, chalk));
  p.push(beam(19, 16.45, 0, 19, 6.4, 0, 0.08, chalk));
  p.push(box(0.65, 0.9, 0.65, 19, 5.95, 0, orange));
  p.push(beam(19, 5.7, 0, 19.75, 5.15, 0, 0.12, edge));
  return ao(merge(p), 5, 0.14);
}
