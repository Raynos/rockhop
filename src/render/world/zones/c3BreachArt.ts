/** C3's ridden freighter. These meshes sit outside/below the authored collider; the deck stays the contact surface. */
import * as THREE from 'three';
import { ao, beam, box, cyl, merge, paint, rgb } from './geo';

/** Near-side hull, aft wheelhouse and torn exit, anchored to the 16 m box and 2 m lip. */
export function c3BreachHullGeometry(sternX: number, lipX: number, deckY: number, lipY: number, face: number): THREE.BufferGeometry {
  const p: THREE.BufferGeometry[] = [];
  const dark = rgb(0x28464a), rust = rgb(0x99543b), seam = rgb(0x593a34);
  const edge = rgb(0xc49169), cream = rgb(0xc7bc9e), glass = rgb(0x203d46);
  const x = (v: number): number => sternX + v;
  const skin = new THREE.Shape();
  skin.moveTo(x(0), deckY - 0.055);
  skin.lineTo(x(16), deckY - 0.055);
  skin.lineTo(lipX, lipY - 0.055);
  skin.lineTo(lipX - 0.85, deckY - 1.08);
  skin.lineTo(lipX - 2.7, deckY - 2.36);
  skin.lineTo(x(3.1), deckY - 2.55);
  skin.lineTo(x(0.25), deckY - 1.37);
  skin.closePath();
  const shell = new THREE.ExtrudeGeometry(skin, { depth: 0.28, bevelEnabled: false });
  shell.translate(0, 0, face + 0.08);
  p.push(paint(shell, dark, (_x, y) => y < deckY - 1.25 ? 0.68 : 1));

  // Five broad plates and angled welds imply a fabricated ship side without corrugated-box repetition.
  for (let i = 0; i < 5; i++) {
    const v = 1.2 + i * 3.02;
    p.push(box(2.84, 1.68, 0.055, x(v + 1.4), deckY - 0.96, face + 0.41,
      i % 2 ? rgb(0x894b37) : rust, 0, 0, -0.04));
    p.push(beam(x(v), deckY - 0.22, face + 0.46,
      x(v + 0.55), deckY - 1.82, face + 0.46, 0.055, seam));
  }
  p.push(beam(x(0.35), deckY - 0.55, face + 0.5, x(15.7), deckY - 0.55, face + 0.5, 0.14, edge));
  p.push(beam(x(2.2), deckY - 1.97, face + 0.47, x(15.7), deckY - 1.97, face + 0.47, 0.13, seam));
  p.push(beam(x(15.8), deckY - 0.55, face + 0.48, lipX - 0.13, lipY - 0.54, face + 0.48, 0.17, edge));
  // Portholes and a nearly continuous rub rail survive a small landscape phone frame.
  for (const v of [3.2, 8.2, 13.2]) {
    p.push(paint(new THREE.CylinderGeometry(0.28, 0.28, 0.045, 12).rotateX(Math.PI / 2)
      .translate(x(v), deckY - 1.12, face + 0.49), glass));
    p.push(paint(new THREE.TorusGeometry(0.28, 0.055, 5, 16)
      .translate(x(v), deckY - 1.12, face + 0.53), edge));
  }
  // A low aft house is behind the ridden strip. Its roof, glazing and funnel create a ship skyline.
  p.push(box(4.2, 2.15, 2.15, x(3.35), deckY + 1.02, -2.85, cream));
  p.push(box(4.65, 0.15, 2.55, x(3.35), deckY + 2.15, -2.85, dark));
  p.push(box(2.85, 0.62, 0.08, x(3.3), deckY + 1.48, -1.73, glass));
  for (const v of [2.35, 3.38, 4.42]) p.push(box(0.075, 0.66, 0.1, x(v), deckY + 1.48, -1.67, cream));
  p.push(cyl(0.32, 0.37, 1.5, 8, x(2.1), deckY + 2.97, -3.35, dark));
  p.push(box(0.92, 0.12, 0.92, x(2.1), deckY + 3.73, -3.35, seam));
  // Rail remains on the far side of the tire line; nothing rises from the near contact edge.
  for (const v of [8, 11, 14]) p.push(box(0.065, 0.74, 0.065, x(v), deckY + 0.37, -2.05, seam));
  p.push(box(8, 0.07, 0.08, x(11), deckY + 0.77, -2.05, edge));
  // The opening is visibly torn below the real x=lipX, y=lipY launch corner.
  p.push(box(0.18, 0.17, 3.1, lipX - 0.09, lipY - 0.1, 0, edge));
  for (const z of [face - 0.45, face + 0.17, face + 0.52]) {
    const shard = new THREE.Shape();
    shard.moveTo(lipX - 0.53, lipY - 0.16);
    shard.lineTo(lipX - 0.04, lipY - 0.11);
    shard.lineTo(lipX - 0.23, lipY - 0.9 - (z - face) * 0.2);
    shard.closePath();
    const g = new THREE.ExtrudeGeometry(shard, { depth: 0.07, bevelEnabled: false });
    g.translate(0, 0, z);
    p.push(paint(g, edge));
  }
  // The old skirt's exposed end was an unlit black rectangle in the jump camera. Treat it as the
  // severed ship bulkhead: a framed opening, transverse webs and bright sheared steel below the lip.
  p.push(box(0.065, lipY - 0.15, 3.06, lipX + 0.045, (lipY - 0.15) / 2, 0, rgb(0xa58d75)));
  // Offset steel skins expose a narrow dark void; the broad lit surfaces show the vessel's thickness.
  p.push(box(0.07, 2.08, 0.82, lipX + 0.09, 1.28, -1.07, rgb(0xbc9d7d)));
  p.push(box(0.08, 1.62, 0.84, lipX + 0.105, 1.58, 1.08, rgb(0x8f705e)));
  p.push(box(0.082, 1.26, 0.62, lipX + 0.11, 1.61, 0, glass));
  p.push(box(0.11, 0.25, 2.66, lipX + 0.115, lipY - 0.5, 0, rgb(0xcbab87)));
  for (const z of [-1.38, -0.66, 0.66, 1.38]) {
    p.push(box(0.11, lipY - 0.37, 0.085, lipX + 0.13, (lipY - 0.37) / 2, z, rust));
  }
  for (const y of [0.32, 1.06, 2.7, lipY - 0.23]) {
    p.push(box(0.12, 0.09, 3.14, lipX + 0.12, y, 0, y > 2.6 ? edge : seam));
  }
  p.push(beam(lipX + 0.16, 0.33, -1.32, lipX + 0.16, 2.68, -0.67, 0.09, edge));
  p.push(beam(lipX + 0.16, 0.33, 1.32, lipX + 0.16, 2.68, 0.67, 0.09, edge));
  // Break the giant rectangular top with deck ribs, all sunk below y=deckY.
  for (let v = 5.8; v < 15.5; v += 2.4) p.push(box(0.12, 0.045, 2.7, x(v), deckY - 0.04, 0, seam));
  return ao(merge(p), 6, 0.13, deckY - 2.55);
}
