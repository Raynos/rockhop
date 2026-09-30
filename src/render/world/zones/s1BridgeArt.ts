/** Rear-offset lift machinery beside S1's optional station bridge. It never enters either riding lane. */
import * as THREE from 'three';
import * as G from './geo';

export function s1LiftTerminalGeometry(): THREE.BufferGeometry {
  const steel = G.rgb(0x354b54);
  const edge = G.rgb(0x5d7880);
  const dark = G.rgb(0x253b43);
  const orange = G.rgb(0xc77439);
  const snow = G.rgb(0xe9f3f5);
  const parts: THREE.BufferGeometry[] = [];
  const heads = [{ x: 0, y: 7.5 }, { x: 14.4, y: 6.75 }];

  for (const { x, y } of heads) {
    // Four sloping chords and their gussets make each sheave tower read as a grounded frame.
    for (const z of [-0.72, 0.72]) {
      for (const side of [-1, 1]) {
        parts.push(G.beam(x + side * 1.0, 0.18, z, x + side * 0.28, y - 0.45, z, 0.18, steel));
        parts.push(G.beam(x + side * 0.8, 2.2, z, x - side * 0.15, y - 1.1, z, 0.075, edge));
      }
      parts.push(G.beam(x - 0.58, y * 0.47, z, x + 0.58, y * 0.47, z, 0.10, edge));
    }
    parts.push(G.box(2.35, 0.22, 1.9, x, y - 0.5, 0, dark));
    parts.push(G.box(2.1, 0.08, 1.7, x, y - 0.35, 0, snow));
    for (const side of [-1, 1]) {
      parts.push(G.box(0.9, 0.28, 1.1, x + side * 0.85, 0.15, 0, dark));
      parts.push(G.box(0.83, 0.07, 1.03, x + side * 0.85, 0.32, 0, snow));
    }
    // Two exposed cable wheels with a contrasting rim, axle and top guard.
    for (const z of [-0.96, 0.96]) {
      parts.push(G.cyl(0.54, 0.54, 0.12, 12, x, y - 0.17, z, dark, 'z'));
      parts.push(G.paint(new THREE.TorusGeometry(0.49, 0.07, 5, 16).translate(x, y - 0.17, z + (z > 0 ? 0.09 : -0.09)), edge));
      parts.push(G.cyl(0.12, 0.12, 0.2, 8, x, y - 0.17, z + (z > 0 ? 0.1 : -0.1), orange, 'z'));
      parts.push(G.box(1.35, 0.08, 0.09, x, y + 0.46, z, orange));
    }
  }
  for (const z of [-0.96, 0.96]) {
    parts.push(G.beam(0, 7.33, z, 14.4, 6.58, z, 0.06, dark));
  }
  // A pair of visible raking struts carries the rear edge of each bridge section into its tower footing.
  // The bridge end remains at z=-1.75 in world space; both lower and upper bike lanes stay in front of it.
  for (const { foot, deck, y } of [{ foot: 0, deck: 4.2, y: 4.85 }, { foot: 14.4, deck: 10.2, y: 4.4 }]) {
    for (const side of [-0.66, 0.66]) {
      parts.push(G.beam(foot + side, 0.28, 0.67, deck + side, y, 3.95, 0.23, steel));
      parts.push(G.box(0.46, 0.28, 0.2, deck + side, y, 3.95, dark));
    }
  }
  return G.merge(parts);
}

/** The lift's approach and its two real choices, in S1 world coordinates. Nothing here is a riding surface. */
export function s1LiftRouteReadGeometry(): THREE.BufferGeometry {
  const steel = G.rgb(0x304a52);
  const edge = G.rgb(0x8aa4aa);
  const orange = G.rgb(0xf38a3b);
  const amber = G.rgb(0xffc45c);
  const blue = G.rgb(0x54bfd2);
  const snow = G.rgb(0xf0f6f5);
  const parts: THREE.BufferGeometry[] = [];
  const z = -3.15;

  // Two grounded sheave frames carry one continuous cable into the already authored x288 bridge terminal.
  // The first frame enters the camera before the station lip and makes the high route's destination visible.
  for (const { x, h } of [{ x: 255.5, h: 5.15 }, { x: 266.1, h: 5.7 }]) {
    parts.push(G.beam(x - 0.72, 0.08, z, x - 0.23, h - 0.35, z, 0.18, steel));
    parts.push(G.beam(x + 0.72, 0.08, z, x + 0.23, h - 0.35, z, 0.18, steel));
    parts.push(G.box(2.15, 0.16, 0.48, x, h - 0.45, z, edge));
    parts.push(G.cyl(0.47, 0.47, 0.13, 12, x, h, z + 0.1, steel, 'z'));
    parts.push(G.paint(new THREE.TorusGeometry(0.42, 0.065, 5, 16).translate(x, h, z + 0.2), orange));
    parts.push(G.box(1.2, 0.12, 0.44, x, 0.06, z, steel));
  }
  parts.push(G.beam(255.5, 5.15, z, 266.1, 5.7, z, 0.075, steel));
  parts.push(G.beam(266.1, 5.7, z, 289.2, 6.8, -4.74, 0.075, steel));
  // The pennants ascend toward the landing tower, not a floating decorative line.
  for (const x of [260.4, 271.1, 277.1, 283.1]) {
    const y = x < 266.1 ? 5.15 + (x - 255.5) * (0.55 / 10.6)
      : 5.7 + (x - 266.1) * (1.1 / 23.1);
    const pennantZ = x < 266.1 ? z : z + (x - 266.1) * (-1.59 / 23.1);
    parts.push(G.beam(x, y, pennantZ, x, y - 0.57, pennantZ, 0.065, edge));
    parts.push(G.box(0.6, 0.28, 0.055, x + 0.3, y - 0.52, pennantZ + 0.02, x < 266.1 ? amber : orange));
  }

  // One grounded, rear-offset fork sign at the run-in: amber rises to the station shelf, blue stays low.
  // Silhouettes are part of the world, so the decision reads even when the HUD cue is missed.
  parts.push(G.box(0.17, 3.0, 0.2, 259.1, 1.55, -2.68, steel));
  parts.push(G.box(3.9, 0.66, 0.16, 260.9, 2.64, -2.68, steel));
  parts.push(G.box(3.9, 0.66, 0.16, 260.9, 1.72, -2.68, steel));
  parts.push(G.box(2.2, 0.19, 0.06, 260.65, 2.64, -2.56, amber, Math.PI / 12));
  parts.push(G.box(0.7, 0.19, 0.06, 261.86, 2.93, -2.56, amber, Math.PI / 4));
  parts.push(G.box(2.2, 0.19, 0.06, 260.65, 1.72, -2.56, blue));
  parts.push(G.box(0.7, 0.19, 0.06, 261.91, 1.55, -2.56, blue, -Math.PI / 4));
  parts.push(G.box(0.46, 0.25, 0.23, 259.1, 0.16, -2.68, snow));

  // The amber cheek follows the actual x266.5–272.0 launch lip, and the landing beacon sits on the real x288 deck.
  parts.push(G.beam(266.5, -0.08, -1.75, 272.03, 2.08, -1.75, 0.12, orange));
  parts.push(G.box(0.12, 2.8, 0.14, 288.35, 5.95, -1.8, steel));
  parts.push(G.box(0.9, 0.55, 0.06, 288.8, 7.05, -1.8, orange));
  parts.push(G.box(0.32, 0.12, 0.08, 289.3, 7.05, -1.74, amber));
  return G.merge(parts);
}
