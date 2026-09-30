/** Candidate Snowline Standard kit: authored local-scale models and collider-derived ice depth.
 *
 * This leaf is deliberately not wired into zoneKit yet. The current deterministic
 * zone build finishes first; the parent snapshots its matrices, then only after
 * this delivery succeeds may it hide named legacy batches. No physics or RNG is
 * consumed here. See the delivery README for the exact replacement contract.
 */
import * as THREE from 'three';
import { GLTFLoader } from 'three/examples/jsm/loaders/GLTFLoader.js';
import { MeshoptDecoder } from 'three/examples/jsm/libs/meshopt_decoder.module.js';
import type { CompiledTrack } from '../../../core/types';
import type { MaterialLibrary } from '../../materials/library';
import { fogify } from '../../lighting/environment';
import { modelAssetUrl } from '../../hero/urls';
import { profileY } from '../track';
import type { PropBatch } from '../props';
import { zoneGround } from './zoneKit';

export const SNOWLINE_FULL = 'models/course-kits/snowline-standard/snowline-standard.glb';
export const SNOWLINE_LOD = 'models/course-kits/snowline-standard/snowline-standard-lod.glb';
export const SNOWLINE_AUTHORED_BATCHES = ['icewall0', 'icewall1', 'lifttower', 'liftchair', 'snowcat'] as const;
export type SnowlineBatchName = typeof SNOWLINE_AUTHORED_BATCHES[number];
export type SnowlineAnchors = Readonly<Record<SnowlineBatchName, readonly THREE.Matrix4[]>>;

/** Call after the ordinary zone build. Cloning avoids depending on the batch lifetime. */
export function snapshotSnowlineAnchors(batches: readonly PropBatch[]): SnowlineAnchors {
  const result = Object.fromEntries(SNOWLINE_AUTHORED_BATCHES.map(name => [name, [] as THREE.Matrix4[]])) as Record<SnowlineBatchName, THREE.Matrix4[]>;
  for (const b of batches) if (b.name in result) {
    for (const it of b.items) result[b.name as SnowlineBatchName].push(it.m.clone());
  }
  return result;
}

export interface SnowlineAsset {
  root: THREE.Group;
  textureBytes: number;
  /** Disposed after the shared renderer retires all material/program links. */
  dispose(): void;
}

interface PrototypePart { geometry: THREE.BufferGeometry; material: THREE.Material | THREE.Material[] }
interface Prototype { parts: PrototypePart[] }
type PrototypeName = 'gorge-wall-a' | 'gorge-wall-b' | 'shelf-face' | 'lift-tower' | 'lift-chair' | 'lift-station' | 'snowcat' | 'summit-beacon';
const PROTOTYPES: readonly PrototypeName[] = ['gorge-wall-a', 'gorge-wall-b', 'shelf-face', 'lift-tower', 'lift-chair', 'lift-station', 'snowcat', 'summit-beacon'];
const scratchPos = new THREE.Vector3();
const scratchRot = new THREE.Quaternion();
const scratchScale = new THREE.Vector3();

function matrix(x: number, y: number, z: number, yaw = 0, sx = 1, sy = 1, sz = 1): THREE.Matrix4 {
  return new THREE.Matrix4().compose(new THREE.Vector3(x, y, z),
    new THREE.Quaternion().setFromAxisAngle(new THREE.Vector3(0, 1, 0), yaw), new THREE.Vector3(sx, sy, sz));
}

/** Scalar 0..1 hash; this does not advance the track's seeded zone RNG. */
function noise(x: number, seed: number): number {
  let n = (Math.imul(Math.floor(x * 17) ^ seed, 0x45d9f3b) ^ seed) >>> 0;
  n ^= n >>> 16;
  n = Math.imul(n, 0x45d9f3b) >>> 0;
  return (n ^ (n >>> 16)) / 4294967295;
}

/** A single contact-facing snow/blue-ice section and eroded outside shoulder.
 * Gaps are skipped. The rider sees blue fracture depth and wind-combed edge,
 * while every vertex remains below true contact and outside the wheel line.
 */
export function snowContactFaceGeometry(track: CompiledTrack, x0: number, x1: number): THREE.BufferGeometry {
  const gaps = track.placed.filter(p => p.kind === 'gap').map(p => ({
    x0: p.pos.x, x1: p.pos.x + Number(p.params.width),
  }));
  const pos: number[] = [], colors: number[] = [], uv: number[] = [];
  const pale = new THREE.Color(0xb9d3d8), blue = new THREE.Color(0x3b778c), dark = new THREE.Color(0x152f40);
  const crust = new THREE.Color(0xdde7e6), powder = new THREE.Color(0xf0f1e7), windIce = new THREE.Color(0x8bbcc3);
  const add = (x: number, y: number, z: number, c: THREE.Color): void => {
    pos.push(x, y, z); colors.push(c.r, c.g, c.b); uv.push(x / 6, y / 5);
  };
  for (let x = x0; x < x1 - 1e-4; x += 1.5) {
    const nx = Math.min(x1, x + 1.5);
    if (gaps.some(g => x < g.x1 - .05 && nx > g.x0 + .05)) continue;
    const y0 = profileY(track.def.profile, x) - .115;
    const y1 = profileY(track.def.profile, nx) - .115;
    // Only intermittent wind-scoured outcrops cover the old ground. A
    // continuous white shoulder would read as another arbitrary slab sheet.
    const patchStart=Math.floor(x/9)*9;
    const exposure=noise(patchStart,track.def.seed^0x517a);
    if(exposure>.56) {
      const taper=(sx:number):number=>Math.max(0,Math.min(1,(sx-patchStart)/1.5,(patchStart+9-sx)/1.5));
      const shoulderMid=exposure>.78?windIce:crust;
      const shoulder=[
        {z:1.74,dy:0,color:crust},
        {z:2.20,dy:-.18-.12*exposure,color:shoulderMid},
        {z:3.25,dy:-.43,color:windIce},
        {z:3.95,dy:-.58,color:powder},
      ];
      for(let row=0;row<shoulder.length-1;row++) {
        const a=shoulder[row]!,b=shoulder[row+1]!;
        const nr=(noise(x+row*.8,track.def.seed)-.5)*.045;
        const shoulderY=(sx:number,py:number,level:number):number=>level<2?py+shoulder[level]!.dy:
          zoneGround('snow',track.def.profile,sx,shoulder[level]!.z)+.026;
        const point=(sx:number,py:number,level:number,color:THREE.Color):[number,number,number,THREE.Color]=>{
          const t=taper(sx);
          const strip=shoulder[level]!;
          return [sx,py+(shoulderY(sx,py,level)-py)*t,1.74+(strip.z-1.74)*t+nr,color];
        };
        const l=point(x,y0,row,a.color), d=point(x,y0,row+1,b.color);
        const r=point(nx,y1,row,a.color), f=point(nx,y1,row+1,b.color);
        for(const v of [l,d,r,r,d,f]) add(v[0],v[1],v[2],v[3]);
      }
    }
    for (let band = 0; band < 3; band++) {
      const a = band === 0 ? 0 : band === 1 ? 1.0 : 2.15;
      const b = band === 0 ? 1.0 : band === 1 ? 2.15 : 3.6;
      const n0 = (noise(x + band * 1.7, track.def.seed) - .5) * .17;
      const n1 = (noise(nx + band * 1.7, track.def.seed) - .5) * .17;
      const front = 1.985 + (band === 1 ? .16 : band === 2 ? -.08 : 0);
      const top = band === 0 ? pale : band === 1 ? blue : dark;
      const bottom = band === 0 ? blue : dark;
      const tri = [
        [x,y0-a,front+n0,top], [x,y0-b,front+n0-.09,bottom],
        [nx,y1-a,front+n1,top], [nx,y1-a,front+n1,top],
        [x,y0-b,front+n0-.09,bottom], [nx,y1-b,front+n1-.09,bottom],
      ] as const;
      for (const v of tri) add(v[0],v[1],v[2],v[3]);
      // Two dark joints per eight metres, below the line of wheel contact.
      if (band === 1 && Math.floor(x / 8) !== Math.floor(nx / 8)) {
        const seamX = nx - .04;
        for (const sy of [y1-.95,y1-1.95]) {
          add(seamX-.018,sy,front+.024,dark);
          add(seamX+.018,sy,front+.024,dark);
          add(seamX+.018,sy-.25,front+.024,dark);
        }
      }
    }
  }
  const g = new THREE.BufferGeometry();
  g.setAttribute('position', new THREE.Float32BufferAttribute(pos,3));
  g.setAttribute('color', new THREE.Float32BufferAttribute(colors,3));
  g.setAttribute('uv', new THREE.Float32BufferAttribute(uv,2));
  g.computeVertexNormals();
  return g;
}

/** Load a full/LOD pair via the same Meshopt path as C1. No objects are mounted
 * until the promise resolves; parent owner discards late resolutions.
 */
export async function loadSnowlineStandard(
  track: CompiledTrack, anchors: SnowlineAnchors, detail: 'full' | 'lod', lib: MaterialLibrary,
): Promise<SnowlineAsset> {
  if (track.def.meta?.biome !== 'snow') throw new Error(`Snowline kit given ${track.def.id}`);
  const file = detail === 'lod' ? SNOWLINE_LOD : SNOWLINE_FULL;
  const gltf = await new GLTFLoader().setMeshoptDecoder(MeshoptDecoder).loadAsync(modelAssetUrl(file));
  const source = gltf.scene;
  source.updateMatrixWorld(true);
  const geometries = new Set<THREE.BufferGeometry>();
  const materials = new Set<THREE.Material>();
  const maps = new Set<THREE.Texture>();
  const prototypes = new Map<PrototypeName, Prototype>();
  let textureBytes = 0;
  let disposed = false;
  const root = new THREE.Group();
  root.name = `snowline:standard:${track.def.id}`;
  const dispose = (): void => {
    if (disposed) return;
    disposed = true;
    for (const geo of geometries) geo.dispose();
    for (const mat of materials) mat.dispose();
    const closed = new Set<unknown>();
    for (const map of maps) {
      const image = map.image as { close?: () => void } | undefined;
      map.dispose();
      if (image?.close && !closed.has(image)) { closed.add(image); image.close(); }
    }
    root.clear();
    source.clear();
  };
  try {
    for (const name of PROTOTYPES) {
      // Three.PropertyBinding sanitizes punctuation in glTF node names during
      // load ("snowline:gorge-wall" becomes "snowlinegorge-wall").
      const node = source.getObjectByName(`snowline${name}`);
      if (!node) throw new Error(`Snowline GLB missing ${name}`);
      const parts: PrototypePart[]=[];
      node.traverse(object=>{
        const mesh=object as THREE.Mesh;
        if (!mesh.isMesh) return;
        const geo=mesh.geometry.clone().applyMatrix4(mesh.matrixWorld);
        geometries.add(mesh.geometry);
        geometries.add(geo);
        const mats=Array.isArray(mesh.material)?mesh.material:[mesh.material];
        for(const m of mats) {
          materials.add(m);
          const standard=m as THREE.MeshStandardMaterial;
          if(!standard.isMeshStandardMaterial) continue;
          // Capture every GLB-owned map before complete() may attach shared
          // neutral library maps. In particular Snowline ice has a normal map.
          for(const owned of [standard.map,standard.normalMap,standard.roughnessMap,
            standard.metalnessMap,standard.aoMap,standard.emissiveMap,standard.alphaMap]) {
            if(!owned||maps.has(owned)) continue;
            maps.add(owned);
            const image=owned.image as {width?:number;height?:number}|undefined;
            textureBytes+=(image?.width??0)*(image?.height??0)*4*1.33;
          }
          fogify(standard);lib.complete(standard);
        }
        parts.push({geometry:geo,material:mesh.material});
      });
      if (!parts.length || parts.length>4) throw new Error(`Snowline GLB invalid primitive count for ${name}`);
      prototypes.set(name,{parts});
    }
    const addInstances = (name: PrototypeName, transforms: readonly THREE.Matrix4[]): void => {
      if (!transforms.length) return;
      const p = prototypes.get(name)!;
      const chunks = new Map<number, THREE.Matrix4[]>();
      for (const transform of transforms) {
        const key = Math.floor(transform.elements[12]! / 40);
        if (!chunks.has(key)) chunks.set(key, []);
        chunks.get(key)!.push(transform);
      }
      for (const [chunk, matrices] of chunks) {
        p.parts.forEach((part,partIndex)=>{
          const mesh=new THREE.InstancedMesh(part.geometry,part.material,matrices.length);
          mesh.name=`snowline:${name}:${chunk}:${partIndex}`;
          matrices.forEach((m,i)=>mesh.setMatrixAt(i,m));
          mesh.instanceMatrix.needsUpdate=true;
          mesh.castShadow=false;mesh.receiveShadow=true;
          mesh.computeBoundingSphere();
          root.add(mesh);
        });
      }
    };
    // Legacy wall geometry is unit width. Its long second instances carry the
    // actual 9–14 m section span; the short rib instances are intentionally
    // suppressed instead of multiplying the new model count.
    for (const [key, prototype] of [['icewall0','gorge-wall-a'],['icewall1','gorge-wall-b']] as const) {
      const walls: THREE.Matrix4[] = [];
      for (const old of anchors[key]) {
        old.decompose(scratchPos,scratchRot,scratchScale);
        if (scratchScale.x < 7) continue;
        walls.push(matrix(scratchPos.x,scratchPos.y,scratchPos.z,0,
          scratchScale.x/10, scratchScale.y/11.8, 1.0));
      }
      addInstances(prototype, walls);
    }
    const towerRotation = new THREE.Matrix4().makeRotationY(Math.PI/2);
    addInstances('lift-tower', anchors.lifttower.map(old => old.clone().multiply(towerRotation)));
    addInstances('lift-chair', anchors.liftchair.map(old => {
      const m=old.clone();
      // Legacy pivot is the cable grip; authored local pivot is the seat's foot.
      m.multiply(new THREE.Matrix4().makeTranslation(0,-2.84,0));
      return m;
    }));
    addInstances('snowcat', anchors.snowcat.map(old => {
      old.decompose(scratchPos,scratchRot,scratchScale);
      return matrix(scratchPos.x,scratchPos.y,scratchPos.z,0,.78,.78,.78);
    }));
    if (track.def.id === 's1-lift-line') {
      addInstances('lift-station', [matrix(297.0, zoneGround('snow',track.def.profile,297,-7.1),-7.1,0,.9,.9,.9)]);
    }
    if (track.def.id === 's2-cornice' || track.def.id === 's3-whiteout') {
      const parts = track.placed.filter(p => p.params.prop === 'snowcat');
      if (parts.length) {
        const center = (parts[0]!.pos.x + parts[parts.length-1]!.pos.x) / 2;
        addInstances('snowcat', [matrix(center,profileY(track.def.profile,center)-.35,-6.2,0,.92,.92,.92)]);
      }
    }
    if (track.def.id === 's3-whiteout') {
      const x=track.def.finishX-16;
      addInstances('summit-beacon',[matrix(x,profileY(track.def.profile,x)-.38,-13.8,0,1,1,1)]);
    }
    const shelfFaces: THREE.Matrix4[]=[];
    for (const p of track.placed) {
      if (p.params.prop !== 'ice-ledge' || p.kind !== 'box') continue;
      const collider = track.colliders.find(c => c.id === p.colliderIds[0]);
      if (collider?.kind !== 'polyline' || collider.points.length < 2) continue;
      const xs=collider.points.map(point=>point.x);
      const minX=Math.min(...xs), maxX=Math.max(...xs);
      if (maxX-minX < 3) continue;
      const top=Math.max(...collider.points.map(point=>point.y));
      shelfFaces.push(matrix((minX+maxX)/2,top-.08,1.83,0,Math.min((maxX-minX)/8,1.65),1,1));
    }
    if(track.def.id==='s2-cornice') {
      const lip=track.placed.find(p=>p.kind==='ramp'&&p.params.prop==='cornice');
      const face=lip&&track.colliders.find(c=>c.id===lip.colliderIds[0]);
      if(face?.kind==='polyline'&&face.points.length>=2) {
        const x0=Math.min(...face.points.map(point=>point.x));
        const x1=Math.max(...face.points.map(point=>point.x));
        const top=Math.max(...face.points.map(point=>point.y));
        // Ends 0.12 m before the gap so the rider sees the true launch edge.
        const end=Math.min(x1-.12,161.804243);
        shelfFaces.push(matrix((x0+end)/2,top-.085,1.86,0,(end-x0)/8,.68,.85));
      }
    }
    // Accepted S2 lip/upper underside remain in the legacy kit until moving
    // comparison. This candidate only adds below-contact ice to their front.
    addInstances('shelf-face',shelfFaces);
    // A single visible mesh per 40 m; gap spans have no face triangles.
    const faceMat = (prototypes.get('gorge-wall-a')!.parts[0]!.material as THREE.MeshStandardMaterial).clone();
    materials.add(faceMat);
    faceMat.vertexColors = true;
    faceMat.side = THREE.DoubleSide;
    faceMat.roughness=.73;
    for (let x=Math.floor((track.bounds.minX-10)/40)*40; x<track.def.finishX+20; x+=40) {
      const geo=snowContactFaceGeometry(track,x,Math.min(x+40,track.def.finishX+20));
      if (!geo.getAttribute('position').count) { geo.dispose(); continue; }
      geometries.add(geo);
      const mesh=new THREE.Mesh(geo,faceMat);
      mesh.name=`snowline:contact-face:${Math.floor(x/40)}`;
      mesh.castShadow=false;
      mesh.receiveShadow=true;
      root.add(mesh);
    }
  } catch (error) { dispose(); throw error; }
  return { root,textureBytes,dispose };
}
