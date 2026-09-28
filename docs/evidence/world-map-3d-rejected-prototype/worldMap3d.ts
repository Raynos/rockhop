/** A small, deterministic, procedural diorama for the level select. No image plates are used. */
import * as THREE from 'three';
import { ANCHOR, legPoints, MAP, routeMarkers, type Marker, type Region } from './worldMap';

const S = 86;
export const mapPoint = (x: number, y: number): THREE.Vector3 => new THREE.Vector3((x - MAP.w / 2) / S, 0, (y - MAP.h / 2) / S);

const clamp = (x: number): number => Math.max(0, Math.min(1, x));
const smooth = (x: number): number => { const t = clamp(x); return t * t * (3 - 2 * t); };

/** Height in metres, shared by the terrain, road, and destination foundations. */
export function terrainHeight(x: number, y: number): number {
  const route = [ANCHOR['c1-low-tide']!, ANCHOR['c2-crane-hop']!, ANCHOR['c3-hull-breach']!, ANCHOR['a1-sawdust']!, ANCHOR['a2-log-jam']!, ANCHOR['a3-timberline']!, ANCHOR['d1-dust-devil']!, ANCHOR['d2-conveyor']!, ANCHOR['d3-rope-walk']!, ANCHOR['s1-lift-line']!, ANCHOR['s2-cornice']!, ANCHOR['s3-whiteout']!];
  let reach = 0;
  for (const p of route) reach = Math.max(reach, Math.exp(-(((x - p.x) / 310) ** 2 + ((y - p.y) / 245) ** 2)));
  const shoreline = smooth((reach - 0.11) / 0.20);
  const alpine = smooth((x - 410) / 260) * (1 - smooth((x - 920) / 200));
  const quarry = smooth((x - 900) / 260) * (1 - smooth((y - 390) / 180));
  const snow = smooth((x - 1150) / 250) * (1 - smooth((y - 375) / 180));
  const ridges = 0.18 * Math.sin(x * 0.018 + Math.sin(y * 0.012) * 2.4) * Math.sin(y * 0.018) + 0.12 * Math.sin(x * 0.037 + y * 0.027);
  const terraces = Math.floor((0.52 + ridges + quarry * 1.4) * 3) / 3;
  return -0.62 + shoreline * (0.75 + alpine * 0.7 + quarry * (terraces + 0.35) + snow * 2.1 + ridges);
}

function colour(x: number, y: number, h: number): THREE.Color {
  const sea = new THREE.Color('#126273');
  const sand = new THREE.Color('#bfaa77');
  const forest = new THREE.Color('#456f55');
  const rock = new THREE.Color('#a57755');
  const snow = new THREE.Color('#dae4df');
  if (h < -0.35) return sea;
  const c = sand.clone().lerp(forest, smooth((x - 390) / 260));
  c.lerp(rock, smooth((x - 890) / 260));
  c.lerp(snow, smooth((x - 1190) / 220) * (1 - smooth((y - 390) / 160)));
  const facet = 0.87 + 0.13 * Math.sin(x * 0.066 + y * 0.031) * Math.sin(y * 0.047);
  return c.multiplyScalar(facet);
}

function terrain(): THREE.Mesh {
  const nx = 112;
  const ny = 76;
  const pos: number[] = [];
  const col: number[] = [];
  const heights: number[] = [];
  const idx: number[] = [];
  for (let j = 0; j <= ny; j++) for (let i = 0; i <= nx; i++) {
    const x = i * MAP.w / nx;
    const y = j * MAP.h / ny;
    const p = mapPoint(x, y);
    const h = terrainHeight(x, y);
    heights.push(h);
    const c = colour(x, y, h);
    pos.push(p.x, h, p.z);
    col.push(c.r, c.g, c.b);
  }
  for (let j = 0; j < ny; j++) for (let i = 0; i < nx; i++) {
    const a = j * (nx + 1) + i;
    const b = a + nx + 1;
    if (Math.max(heights[a]!, heights[a + 1]!, heights[b]!, heights[b + 1]!) <= -0.35) continue;
    idx.push(a, b, a + 1, a + 1, b, b + 1);
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos, 3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(col, 3));
  g.setIndex(idx);
  g.computeVertexNormals();
  return new THREE.Mesh(g, new THREE.MeshStandardMaterial({ vertexColors: true, roughness: 1, side: THREE.DoubleSide }));
}

function pathPoints(regions: readonly Region[]): THREE.Vector3[] {
  const ms = routeMarkers(regions);
  const pts: THREE.Vector3[] = [];
  for (let i = 0; i < ms.length - 1; i++) {
    const leg = legPoints(ms[i]!, ms[i + 1]!);
    for (const p of leg.slice(i ? 1 : 0)) pts.push(mapPoint(p.x, p.y).setY(terrainHeight(p.x, p.y) + 0.13));
  }
  return pts;
}

function labelTexture(label: string, fill: string): THREE.CanvasTexture {
  const canvas = document.createElement('canvas');
  canvas.width = canvas.height = 128;
  const ctx = canvas.getContext('2d');
  if (ctx) {
    ctx.fillStyle = fill;
    ctx.beginPath();
    ctx.arc(64, 64, 61, 0, 2 * Math.PI);
    ctx.fill();
    ctx.strokeStyle = '#f8eccc';
    ctx.lineWidth = 7;
    ctx.stroke();
    ctx.fillStyle = '#fff9e8';
    ctx.font = `900 ${label.length > 2 ? 48 : 61}px system-ui`;
    ctx.textAlign = 'center';
    ctx.textBaseline = 'middle';
    ctx.fillText(label, 64, 67);
  }
  const tex = new THREE.CanvasTexture(canvas);
  tex.colorSpace = THREE.SRGBColorSpace;
  tex.anisotropy = 4;
  return tex;
}

function markerColour(m: Marker): string {
  if (m.locked) return '#777e80';
  if (m.proving) return '#1aa5a8';
  if (!m.medal) return '#dc603d';
  return { platinum: '#45d5cb', gold: '#c79632', silver: '#9ba8b6', bronze: '#a66944' }[m.medal];
}

/** WebGL scene and projected, raycastable 3D places. The screen owns camera motion and HTML accessibility. */
export class WorldMapDiorama {
  readonly scene = new THREE.Scene();
  readonly camera = new THREE.PerspectiveCamera(43, 1, 0.1, 100);
  readonly places = new Map<string, THREE.Group>();
  private readonly focusRings = new Map<string, THREE.Mesh>();
  readonly sceneRoot = new THREE.Group();
  private renderer: THREE.WebGLRenderer | null = null;
  private readonly materials: THREE.Material[] = [];
  private readonly textures: THREE.Texture[] = [];

  constructor(readonly canvas: HTMLCanvasElement, regions: readonly Region[]) {
    this.scene.background = new THREE.Color('#0b4757');
    this.scene.add(this.sceneRoot);
    this.scene.add(new THREE.HemisphereLight('#fff1d6', '#2d6771', 2.4));
    const sun = new THREE.DirectionalLight('#fff4dc', 2.7);
    sun.position.set(-5, 12, 8);
    this.scene.add(sun);
    this.sceneRoot.add(terrain());
    const water = new THREE.Mesh(new THREE.PlaneGeometry(200, 200), new THREE.MeshStandardMaterial({ color: '#0b5265', metalness: 0.1, roughness: 0.42 }));
    water.rotation.x = -Math.PI / 2;
    water.position.y = -0.65;
    this.sceneRoot.add(water);
    const pts = pathPoints(regions);
    if (pts.length > 1) {
      const curve = new THREE.CatmullRomCurve3(pts, false, 'centripetal');
      const road = new THREE.Mesh(new THREE.TubeGeometry(curve, 180, 0.087, 5, false), new THREE.MeshStandardMaterial({ color: '#f1d79d', roughness: 1 }));
      this.sceneRoot.add(road);
    }
    const all = regions.flatMap((r) => r.markers);
    for (const m of all) this.addPlace(m);
    this.addProps();
  }

  private addPlace(m: Marker): void {
    const p = mapPoint(m.x, m.y);
    p.y = terrainHeight(m.x, m.y) + 0.17;
    const g = new THREE.Group();
    g.position.copy(p);
    g.userData['track'] = m.track.id;
    const colourHex = markerColour(m);
    const radius = m.proving ? 0.3 : 0.43;
    const base = new THREE.Mesh(new THREE.CylinderGeometry(radius, radius + 0.07, 0.21, 24), new THREE.MeshStandardMaterial({ color: '#27383a', metalness: 0.34, roughness: 0.55 }));
    g.add(base);
    const rim = new THREE.Mesh(new THREE.CylinderGeometry(radius - 0.02, radius, 0.08, 24), new THREE.MeshStandardMaterial({ color: colourHex, metalness: 0.35, roughness: 0.35, emissive: colourHex, emissiveIntensity: m.locked ? 0 : 0.12 }));
    rim.position.y = 0.13;
    g.add(rim);
    const t = labelTexture(m.proving ? 'FR' : m.code, colourHex);
    this.textures.push(t);
    const cap = new THREE.Mesh(new THREE.CircleGeometry(radius - 0.08, 32), new THREE.MeshBasicMaterial({ map: t, transparent: true, side: THREE.DoubleSide }));
    cap.rotation.x = -Math.PI / 2;
    cap.position.y = 0.178;
    g.add(cap);
    const focusRing = new THREE.Mesh(new THREE.TorusGeometry(radius + 0.08, 0.055, 8, 32), new THREE.MeshBasicMaterial({ color: '#9af7ea' }));
    focusRing.rotation.x = -Math.PI / 2;
    focusRing.position.y = 0.20;
    focusRing.visible = false;
    g.add(focusRing);
    this.focusRings.set(m.track.id, focusRing);
    const stem = new THREE.Mesh(new THREE.CylinderGeometry(0.065, 0.08, 0.26, 8), new THREE.MeshStandardMaterial({ color: '#415154', roughness: 0.7 }));
    stem.position.y = -0.22;
    g.add(stem);
    this.places.set(m.track.id, g);
    this.sceneRoot.add(g);
  }

  private addProps(): void {
    // Instancing keeps the four biomes modelled without turning the map into a draw-call wall.
    const trunk = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.04, 0.07, 0.35, 5), new THREE.MeshStandardMaterial({ color: '#654f37' }), 82);
    const crown = new THREE.InstancedMesh(new THREE.ConeGeometry(0.21, 0.56, 6), new THREE.MeshStandardMaterial({ color: '#244d3e' }), 82);
    const quarry = new THREE.InstancedMesh(new THREE.CylinderGeometry(0.17, 0.28, 0.45, 5), new THREE.MeshStandardMaterial({ color: '#ac7d5d', flatShading: true }), 36);
    const snow = new THREE.InstancedMesh(new THREE.ConeGeometry(0.24, 0.65, 6), new THREE.MeshStandardMaterial({ color: '#d6e7e4' }), 44);
    const dummy = new THREE.Object3D();
    const clear = (x: number, y: number): boolean => Object.values(ANCHOR).every((p) => Math.hypot(x - p.x, y - p.y) > 55);
    for (let i = 0; i < 82; i++) {
      const x = 490 + (i * 137 % 520);
      const y = 360 + (i * 197 % 420);
      const h = terrainHeight(x, y);
      const xx = clear(x, y) && h > -0.2 ? x : x + 65;
      const yy = clear(x, y) && h > -0.2 ? y : y + 55;
      const p = mapPoint(xx, yy);
      p.y = terrainHeight(xx, yy);
      dummy.position.set(p.x, p.y + 0.17, p.z);
      dummy.scale.setScalar(0.7 + (i % 5) * 0.13);
      dummy.updateMatrix(); trunk.setMatrixAt(i, dummy.matrix);
      dummy.position.y += 0.34;
      dummy.updateMatrix(); crown.setMatrixAt(i, dummy.matrix);
    }
    for (let i = 0; i < 36; i++) {
      const x = 1070 + (i * 101 % 390);
      const y = 395 + (i * 149 % 230);
      const p = mapPoint(x, y);
      dummy.position.set(p.x, terrainHeight(x, y) + 0.2, p.z);
      dummy.scale.set(0.8 + i % 4 * 0.2, 0.7 + i % 3 * 0.15, 0.8 + i % 5 * 0.1);
      dummy.updateMatrix(); quarry.setMatrixAt(i, dummy.matrix);
    }
    for (let i = 0; i < 44; i++) {
      const x = 1170 + (i * 89 % 345);
      const y = 155 + (i * 67 % 245);
      const p = mapPoint(x, y);
      dummy.position.set(p.x, terrainHeight(x, y) + 0.24, p.z);
      dummy.scale.setScalar(0.6 + i % 4 * 0.15);
      dummy.updateMatrix(); snow.setMatrixAt(i, dummy.matrix);
    }
    this.sceneRoot.add(trunk, crown, quarry, snow);
    // Coast's containers make the harbour leg distinct even at a glance.
    const boxes = new THREE.InstancedMesh(new THREE.BoxGeometry(0.5, 0.22, 0.25), new THREE.MeshStandardMaterial({ color: '#d16f48', metalness: 0.22, roughness: 0.72 }), 20);
    for (let i = 0; i < 20; i++) {
      const x = 65 + (i % 5) * 98;
      const y = 475 + Math.floor(i / 5) * 56;
      const p = mapPoint(x, y);
      dummy.position.set(p.x, terrainHeight(x, y) + 0.13, p.z);
      dummy.scale.set(1, 1 + i % 3 * 0.3, 1);
      dummy.updateMatrix(); boxes.setMatrixAt(i, dummy.matrix);
    }
    this.sceneRoot.add(boxes);
  }

  resize(width: number, height: number): void {
    if (!width || !height) return;
    if (!this.renderer) {
      try {
        this.renderer = new THREE.WebGLRenderer({ canvas: this.canvas, antialias: true, powerPreference: 'low-power', alpha: false });
        this.renderer.outputColorSpace = THREE.SRGBColorSpace;
        this.renderer.toneMapping = THREE.ACESFilmicToneMapping;
        this.renderer.toneMappingExposure = 1.28;
      } catch { return; } // jsdom and a truly unavailable WebGL context: the accessible list still works.
    }
    this.camera.aspect = width / height;
    this.camera.updateProjectionMatrix();
    this.renderer.setPixelRatio(Math.min(2, window.devicePixelRatio || 1));
    this.renderer.setSize(width, height, false);
  }

  draw(): void { this.renderer?.render(this.scene, this.camera); }
  get available(): boolean { return this.renderer !== null; }
  select(trackId: string): void { for (const [id, ring] of this.focusRings) ring.visible = id === trackId; }
  project(trackId: string, width: number, height: number): { x: number; y: number; behind: boolean } | null {
    const g = this.places.get(trackId);
    if (!g) return null;
    const p = g.position.clone().add(new THREE.Vector3(0, 0.25, 0)).project(this.camera);
    return { x: (p.x + 1) * width / 2, y: (1 - p.y) * height / 2, behind: p.z < -1 || p.z > 1 };
  }

  dispose(): void {
    this.sceneRoot.traverse((o) => {
      if (!(o instanceof THREE.Mesh)) return;
      o.geometry.dispose();
      const mats = Array.isArray(o.material) ? o.material : [o.material];
      for (const m of mats) this.materials.push(m);
    });
    for (const m of this.materials) m.dispose();
    for (const t of this.textures) t.dispose();
    this.renderer?.dispose();
  }
}
