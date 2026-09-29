/** A1's working saw shed, assembled as one static, vertex-coloured prop behind the playable stair line. */
import * as THREE from 'three';
import * as G from './zones/geo';

export function a1MillComplexGeometry(): THREE.BufferGeometry {
  const p: THREE.BufferGeometry[] = [];
  const timber = G.rgb(0x98704c);
  const fresh = G.rgb(0xd4aa70);
  const dark = G.rgb(0x4d3727);
  const iron = G.rgb(0x555752);
  const steel = G.rgb(0xb9b5a4);
  const roof = G.rgb(0x59605b);
  const dust = G.rgb(0xb89564);
  const add = (w: number, h: number, d: number, x: number, y: number, z: number, c: G.RGB, rz = 0, ry = 0, rx = 0): void => {
    p.push(G.box(w, h, d, x, y, z, c, rz, ry, rx));
  };

  // A raised, open mill floor. The dark recess is framed rather than filled, so the blade and carriage show.
  add(16.8, 0.34, 6.7, 0, 1.28, 0, dark);
  for (const x of [-7.5, -4.4, -1.2, 2.2, 5.2, 7.5]) for (const z of [-3, 3]) {
    add(0.34, 5.1, 0.34, x, 2.66, z, timber);
    add(0.52, 0.28, 0.5, x, 0.22, z, G.rgb(0x77746b));
  }
  for (const z of [-3, 3]) {
    add(16.5, 0.28, 0.3, 0, 5.05, z, fresh);
    add(16.5, 0.2, 0.28, 0, 1.78, z, dark);
  }
  // Close the outer two bays with uneven cladding; leave the central saw bay visually open.
  for (let i = 0; i < 10; i++) {
    const y = 1.98 + i * 0.29;
    for (const [a, b] of [[-7.45, -4.55], [5.3, 7.45]] as const) {
      add(b - a - 0.08, 0.27, 0.1, (a + b) / 2, y, 3.19, i % 3 === 0 ? fresh : timber);
    }
  }
  for (const x of [-7.7, 7.7]) for (let i = 0; i < 10; i++) add(0.12, 0.27, 5.9, x, 2.0 + i * 0.29, 0, i % 2 ? timber : dark);
  for (const x of [-4.35, 5.05]) {
    p.push(G.beam(x, 1.85, 3.3, x + 1.3, 4.9, 3.3, 0.16, dark));
  }

  // Two pitched, shingled roof planes with repeated exposed rafters. All roof mass remains well behind z=-3.
  for (const side of [-1, 1]) {
    add(17.4, 0.18, 4.3, 0, 6.15, side * 1.63, roof, 0, 0, side * 0.47);
    for (let x = -8; x < 8.2; x += 1.05) add(0.075, 0.035, 4.0, x, 6.28, side * 1.63, x % 2 ? timber : dark, 0, 0, side * 0.47);
    for (const x of [-7.7, -3.8, 0, 3.8, 7.7]) p.push(G.beam(x, 5.04, side * 3.12, x, 7.22, 0, 0.16, timber));
  }
  add(17.1, 0.15, 0.18, 0, 7.26, 0, fresh);
  add(0.8, 1.65, 0.85, 5.8, 7.2, -1.3, dark);
  add(1.15, 0.18, 1.15, 5.8, 8.0, -1.3, iron);

  // Visible cut line: a steel blade, tooth rhythm, drive hub, feed rails and a log behind the blade.
  p.push(G.cyl(0.72, 0.72, 0.055, 24, 0.1, 3.1, 3.39, steel, 'z'));
  p.push(G.cyl(0.18, 0.18, 0.1, 12, 0.1, 3.1, 3.47, iron, 'z'));
  for (let i = 0; i < 16; i++) {
    const a = i * Math.PI / 8;
    add(0.19, 0.085, 0.075, 0.1 + Math.cos(a) * 0.77, 3.1 + Math.sin(a) * 0.77, 3.4, steel, a);
  }
  for (const z of [2.55, 3.48]) add(7.4, 0.12, 0.16, -0.35, 1.86, z, iron);
  for (let x = -3.6; x <= 3; x += 0.65) add(0.12, 0.1, 1.05, x, 1.83, 3.0, timber);
  p.push(G.cyl(0.36, 0.36, 2.6, 10, -2.25, 2.29, 2.9, dark, 'x'));
  for (const x of [-3.55, -0.95]) p.push(G.cyl(0.32, 0.32, 0.035, 12, x, 2.29, 2.9, fresh, 'x'));
  add(1.2, 0.74, 0.7, 2.5, 2.2, 2.7, iron);
  p.push(G.cyl(0.41, 0.41, 0.1, 16, 2.5, 2.95, 3.33, dark, 'z'));
  p.push(G.cyl(0.28, 0.28, 0.12, 16, 2.5, 2.95, 3.39, fresh, 'z'));
  for (const x of [-2.8, 2.0]) add(0.13, 1.2, 0.16, x, 1.15, 3.56, dark);

  // The log-feed conveyor is physically supported from the ground and meets the open bay at deck height.
  const conveyorAngle = Math.atan2(1.25, 9.0);
  add(9.1, 0.14, 1.75, -12.2, 1.04, 3.7, dark, conveyorAngle);
  for (const z of [2.82, 4.58]) add(9.25, 0.23, 0.18, -12.2, 1.0, z, timber, conveyorAngle);
  for (let x = -16.45; x < -7.8; x += 0.52) {
    const y = 1.04 + (x + 12.2) * Math.tan(conveyorAngle);
    add(0.12, 0.045, 1.82, x, y + 0.09, 3.7, iShade(x));
  }
  for (const x of [-16.0, -12.3, -8.1]) {
    const y = 1.04 + (x + 12.2) * Math.tan(conveyorAngle);
    for (const z of [2.9, 4.5]) {
      add(0.2, Math.max(0.32, y - 0.2), 0.2, x, Math.max(0.32, y - 0.2) / 2, z, timber);
      p.push(G.cyl(0.18, 0.18, 0.06, 12, x, y - 0.09, z + 0.11, steel, 'z'));
    }
  }

  // Cut stock and the sawdust discharge make the site's input and output legible from the moving camera.
  const trunks: [number, number, number, number][] = [[-12.8, 0.45, -0.7, 0.38], [-11.7, 0.48, -1.45, 0.45], [9.7, 0.42, 0.0, 0.33], [11.4, 0.51, -1.0, 0.43]];
  for (const [x, y, z, r] of trunks) {
    const length = 3.7 + r * 2.3;
    p.push(G.cyl(r, r * 0.92, length, 9, x, y, z, r > 0.42 ? G.rgb(0x675039) : dark, 'x'));
    for (const end of [-1, 1]) p.push(G.cyl(r * 0.85, r * 0.85, 0.035, 12, x + end * (length / 2 + 0.02), y, z, fresh, 'x'));
  }
  for (const [x, z, radius, height] of [[5.2, 4.8, 1.3, 1.25], [7.5, 5.15, 0.9, 0.8], [10.2, 4.2, 1.65, 1.5]] as const) {
    const g = new THREE.ConeGeometry(radius, height, 11);
    g.translate(x, height / 2, z);
    p.push(G.paint(g, dust, (px, py) => 0.84 + 0.12 * Math.sin(px * 2.7 + py * 4.1)));
  }
  add(2.5, 0.13, 1.7, 5.7, 0.55, 3.8, timber, 0.1);
  return G.ao(G.merge(p), 7.4, 0.2);
}

function iShade(x: number): G.RGB {
  return G.rgb(Math.round(x * 2) % 3 === 0 ? 0xc49a68 : 0x886443);
}
