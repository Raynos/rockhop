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
