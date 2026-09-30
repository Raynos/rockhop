/** A1 material standard trial: quiet soil masses, damp cut earth and an opaque rippled lake.
 * Canvas maps belong to the course's unnamed materials and existing retirement path.
 * No collision, seeded prop draw or geometry position changes.
 */
import * as THREE from 'three';
import type { MaterialLibrary } from '../../materials/library';
import { fogify } from '../../lighting/environment';
import { canvas, tex } from '../canvasTex';
import { lcg } from './geo';
import type { ZoneKit } from './zoneKit';

type SoilPart = 'tread' | 'bank' | 'floor';

/** Broad damp/duff masses carry the read; small stones and needles are sparse accents. */
function soilPainting(part: SoilPart): THREE.CanvasTexture {
  const [c, g] = canvas(512, part === 'bank' ? 256 : 512);
  const w = c.width, h = c.height, rnd = lcg(0x8ca11 + part.length * 917);
  g.fillStyle = part === 'floor' ? '#6c7457' : part === 'bank' ? '#625145' : '#756f5e';
  g.fillRect(0, 0, w, h);
  for (let i = 0; i < 19; i++) {
    const x = rnd() * w, y = rnd() * h, radius = 45 + rnd() * 112;
    for (const dx of [-w, 0, w]) for (const dy of [-h, 0, h]) {
      const grad = g.createRadialGradient(x + dx, y + dy, 0, x + dx, y + dy, radius);
      grad.addColorStop(0, i % 3 ? 'rgba(36,40,29,.24)' : 'rgba(140,128,99,.17)');
      grad.addColorStop(1, 'rgba(36,40,29,0)');
      g.fillStyle = grad; g.fillRect(x + dx - radius, y + dy - radius, radius * 2, radius * 2);
    }
  }
  // A continuous compressed wheel corridor, without drawing a second physical route.
  if (part === 'tread') {
    const grad = g.createLinearGradient(0, 0, 0, h);
    grad.addColorStop(0, 'rgba(34,34,27,.15)'); grad.addColorStop(.35, 'rgba(34,34,27,0)');
    grad.addColorStop(.65, 'rgba(34,34,27,0)'); grad.addColorStop(1, 'rgba(34,34,27,.15)');
    g.fillStyle = grad; g.fillRect(0, 0, w, h);
  }
  for (let i = 0; i < 1400; i++) {
    const x = rnd() * w, y = rnd() * h, size = .6 + rnd() * 1.8;
    g.fillStyle = i % 3 ? 'rgba(37,38,30,.17)' : 'rgba(163,152,123,.22)';
    g.fillRect(x, y, size * 1.6, size);
  }
  for (let i = 0; i < (part === 'tread' ? 370 : 720); i++) {
    const x = rnd() * w, y = rnd() * h, angle = rnd() * Math.PI, len = 2 + rnd() * 5;
    g.strokeStyle = i % 3 ? 'rgba(63,52,36,.30)' : 'rgba(137,116,77,.26)';
    g.lineWidth = .7; g.beginPath(); g.moveTo(x, y); g.lineTo(x + Math.cos(angle) * len, y + Math.sin(angle) * len); g.stroke();
  }
  return tex(c);
}

/** Tile-periodic derivatives keep normal seams invisible at repeat boundaries. */
function normalPainting(water: boolean): THREE.CanvasTexture {
  const n = 128, [c, g] = canvas(n, n), image = g.createImageData(n, n);
  const height = (x: number, y: number): number => {
    const u = x / n * Math.PI * 2, v = y / n * Math.PI * 2;
    return water ? Math.sin(u * 3 + v * 2) * .6 + Math.sin(u * 7 - v * 4) * .2
      : Math.sin(u * 11 + Math.sin(v * 3)) * .35 + Math.sin(v * 17 + u * 5) * .2;
  };
  for (let y = 0; y < n; y++) for (let x = 0; x < n; x++) {
    const dx = (height(x + 1, y) - height(x - 1, y)) * (water ? .6 : .3);
    const dy = (height(x, y + 1) - height(x, y - 1)) * (water ? .6 : .3);
    const len = Math.hypot(dx, dy, 1), k = (y * n + x) * 4;
    image.data[k] = Math.round(127.5 - dx / len * 127.5);
    image.data[k + 1] = Math.round(127.5 - dy / len * 127.5);
    image.data[k + 2] = Math.round(127.5 + 1 / len * 127.5); image.data[k + 3] = 255;
  }
  g.putImageData(image, 0, 0);
  return tex(c, false);
}

/** One course-owned map set per surface role; generation jobs cannot overwrite it. */
export function alpineSoil(lib: MaterialLibrary, part: SoilPart): { mat: THREE.MeshStandardMaterial; bytes: number } {
  const map = soilPainting(part), normalMap = normalPainting(false);
  const mat = fogify(new THREE.MeshStandardMaterial({ map, normalMap, roughness: .96,
    metalness: 0, vertexColors: true, normalScale: new THREE.Vector2(.28, .28) }));
  lib.complete(mat);
  return { mat, bytes: (512 * (part === 'bank' ? 256 : 512) + 128 * 128) * 4 * 4 / 3 };
}

/** Reuse the same truthful ground and lake meshes, with authored-scale material response. */
export function applyAlpineSurface(kit: ZoneKit, lib: MaterialLibrary): void {
  const terrain = kit.meshes.find(mesh => mesh.name === 'terrain');
  if (terrain) {
    const soil = alpineSoil(lib, 'floor'); terrain.material = soil.mat; kit.textureBytes += soil.bytes;
    const p = terrain.geometry.getAttribute('position'), c = terrain.geometry.getAttribute('color') as THREE.BufferAttribute;
    const trail = new THREE.Color(0xb6ae94), moss = new THREE.Color(0x9ca880), green = new THREE.Color(0xc5cbb0);
    for (let i = 0; i < p.count; i++) {
      const x = p.getX(i), z = p.getZ(i), edge = Math.min(1, Math.max(0, (Math.abs(z) - 3) / 4));
      const mass = .5 + .25 * Math.sin(x * .055 + z * .083) + .25 * Math.sin(x * .027 - z * .051);
      const color = moss.clone().lerp(green, mass).lerp(trail, 1 - edge);
      c.setXYZ(i, color.r, color.g, color.b);
    }
  }
  const lake = kit.meshes.find(mesh => mesh.name === 'zone:lake');
  if (lake) {
    const old = lake.material as THREE.MeshStandardMaterial;
    const normalMap = normalPainting(true);
    const p = lake.geometry.getAttribute('position');
    let minX = Infinity, maxX = -Infinity, minZ = Infinity, maxZ = -Infinity;
    for (let i = 0; i < p.count; i++) { minX = Math.min(minX,p.getX(i)); maxX=Math.max(maxX,p.getX(i)); minZ=Math.min(minZ,p.getZ(i)); maxZ=Math.max(maxZ,p.getZ(i)); }
    normalMap.repeat.set((maxX-minX)/8, (maxZ-minZ)/8);
    const mat = fogify(new THREE.MeshStandardMaterial({ color: 0x285a65, roughness: .67,
      metalness: 0, envMapIntensity: .22, normalMap, normalScale: new THREE.Vector2(.3,.3) }));
    lib.complete(mat); lake.material=mat; old.dispose();
    kit.scroll.push({ tex: normalMap, vx: .004, vy: .0015 }); kit.textureBytes += 128 * 128 * 4 * 4 / 3;
  }
}

/** Needle cards keep their source detail without the full-strength normal's brittle mottling. */
export function calibrateAlpineCanopy(material: THREE.MeshStandardMaterial): void {
  if (material.name !== 'alpine-branches') return;
  material.color.setRGB(.72, 1, .84);
  material.normalScale.set(.45,.45);
}
