/** Read-only, post-render visible-surface probe. Bundle this into a private harness build;
 * do not infer palm/sole patches from bone names, sockets, or skin weights. */
import { Vector3 } from 'three';
import type { BufferGeometry, Object3D, SkinnedMesh } from 'three';

export const CONTACT_IDS = ['hand.L', 'hand.R', 'foot.L', 'foot.R'] as const;
export type ContactId = typeof CONTACT_IDS[number];
type Vec3 = [number, number, number];
export interface Locator { childPath: number[]; name: string }
export interface SurfacePatch {
  mesh: Locator;
  /** Hash of the actual runtime geometry AFTER merge/conditioning, not GLB accessor order. */
  geometrySHA256: string;
  /** Triangle ordinals in the current index buffer, or consecutive triplets if non-indexed. */
  triangles?: number[];
  /** Explicit vertices with an incident triangle to supply a posed geometric normal. */
  vertices?: { index: number; normalTriangle: number }[];
  /** Triangle lattice edge subdivisions, at least 2; coverage is reported, never assumed exact. */
  subdivisions: number;
  reviewed: boolean;
  evidence: string;
}
export interface ContactPrimitive {
  frame: Locator;
  kind: 'capsule' | 'cylinder';
  /** Local cap/segment centres, in the selected LIVE bike object's coordinates (metres). */
  a: Vec3;
  b: Vec3;
  radius: number;
  verifiedAgainstVisibleGeometry: boolean;
  evidence: string;
}
export interface SurfaceContactManifest {
  schema: 'rockhop-surface-contacts-v1';
  riderSHA256: string;
  bikeSHA256: string;
  contacts: Partial<Record<ContactId, { patch: SurfacePatch; target: ContactPrimitive }>>;
}
export interface PrimitiveDistance {
  signedDistanceM: number;
  closestWorld: Vec3;
  outwardNormalWorld: Vec3;
}
export type ContactMeasurement = {
  status: 'unmeasured'; reason: string;
} | {
  status: 'measured';
  /** No pass flag: a parent must judge coverage, anatomy and played footage together. */
  sampleCount: number;
  minimumSignedDistanceM: number;
  maximumSignedDistanceM: number;
  minimumAbsoluteSurfaceGapM: number;
  maximumSampledPenetrationM: number;
  nearestSampleWorld: Vec3;
  nearestTargetWorld: Vec3;
  nearestNormalMismatchDeg: number;
  maximumNormalMismatchDeg: number;
  /** Conservative spacing diagnostic, not a guaranteed surface intersection bound. */
  maximumTriangleLatticeEdgeM: number;
};

const finiteVec = (v: number[]): boolean => v.length === 3 && v.every(Number.isFinite);
const digestPattern = /^[a-f0-9]{64}$/;
function locate(root: Object3D, locator: Locator): Object3D {
  let node = root;
  if (!Array.isArray(locator.childPath)) throw new Error('object childPath missing');
  for (const i of locator.childPath) {
    if (!Number.isSafeInteger(i) || i < 0 || !node.children[i]) throw new Error('object childPath invalid');
    node = node.children[i]!;
  }
  if (node.name !== locator.name) throw new Error('object name/path changed');
  return node;
}

/** Stable digest of indexing + actual deformation inputs; bindMatrixInverse varies with posing.
 * Includes skin order and inverse bind matrices, and all position morph targets. */
export async function runtimeSurfaceSHA256(mesh: SkinnedMesh): Promise<string> {
  const g = mesh.geometry;
  const attribute = (name: string) => {
    const a = g.getAttribute(name);
    if (!a) return null;
    return { itemSize: a.itemSize, count: a.count, values: Array.from({ length: a.count }, (_, i) =>
      Array.from({ length: a.itemSize }, (_, j) => a.getComponent(i, j))) };
  };
  const payload = JSON.stringify({ schema: 1, position: attribute('position'),
    skinIndex: attribute('skinIndex'), skinWeight: attribute('skinWeight'),
    index: g.index ? Array.from({ length: g.index.count }, (_, i) => g.index!.getX(i)) : null,
    morphTargetsRelative: g.morphTargetsRelative,
    morphPositions: (g.morphAttributes.position ?? []).map(a =>
      Array.from({ length: a.count }, (_, i) => [a.getX(i), a.getY(i), a.getZ(i)])),
    bindMode: mesh.bindMode, bindMatrix: mesh.bindMatrix.toArray(),
    boneNames: mesh.skeleton.bones.map(b => b.name), boneInverses: mesh.skeleton.boneInverses.map(m => m.toArray()) });
  const digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(payload));
  return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
}

/** Exact signed point distance to a WORLD-space round capsule or finite capped cylinder.
 * Positive = outside separation; negative = inside primitive. This is not a mesh collision test. */
export function pointPrimitiveDistance(point: Vector3, a: Vector3, b: Vector3, radius: number,
  kind: ContactPrimitive['kind']): PrimitiveDistance {
  if (![...point.toArray(), ...a.toArray(), ...b.toArray(), radius].every(Number.isFinite) || radius <= 0)
    throw new Error('invalid primitive/point');
  if (kind !== 'capsule' && kind !== 'cylinder') throw new Error('invalid primitive kind');
  const axis = b.clone().sub(a), length = axis.length();
  if (length < 1e-9) throw new Error('primitive axis has zero length');
  axis.divideScalar(length);
  const center = a.clone().add(b).multiplyScalar(0.5);
  const relative = point.clone().sub(center), along = relative.dot(axis), half = length / 2;
  if (kind === 'capsule') {
    const axisPoint = center.addScaledVector(axis, Math.max(-half, Math.min(half, along)));
    const radial = point.clone().sub(axisPoint), distance = radial.length();
    const normal = distance > 1e-12 ? radial.divideScalar(distance) : perpendicular(axis);
    return { signedDistanceM: distance - radius, closestWorld: axisPoint.addScaledVector(normal, radius).toArray(),
      outwardNormalWorld: normal.toArray() };
  }
  const radial = relative.clone().addScaledVector(axis, -along), radialLength = radial.length();
  const radialNormal = radialLength > 1e-12 ? radial.divideScalar(radialLength) : perpendicular(axis);
  const qr = radialLength - radius, qa = Math.abs(along) - half;
  const signedDistanceM = Math.hypot(Math.max(qr, 0), Math.max(qa, 0)) + Math.min(Math.max(qr, qa), 0);
  let capAlong = Math.max(-half, Math.min(half, along)), capRadius = Math.min(radius, radialLength);
  if (qr <= 0 && qa <= 0) {
    if (qr >= qa) capRadius = radius;
    else capAlong = (along < 0 ? -1 : 1) * half;
  }
  const closest = center.addScaledVector(axis, capAlong).addScaledVector(radialNormal, capRadius);
  const outward = signedDistanceM < 0 ? closest.clone().sub(point) : point.clone().sub(closest);
  if (outward.lengthSq() < 1e-20) {
    outward.copy(Math.abs(qa) < Math.abs(qr) ? axis.clone().multiplyScalar(along < 0 ? -1 : 1) : radialNormal);
  } else outward.normalize();
  return { signedDistanceM, closestWorld: closest.toArray(), outwardNormalWorld: outward.toArray() };
}
function perpendicular(axis: Vector3): Vector3 {
  return new Vector3(Math.abs(axis.x) < 0.9 ? 1 : 0, Math.abs(axis.x) < 0.9 ? 0 : 1, 0).cross(axis).normalize();
}
function face(g: BufferGeometry, triangle: number): [number, number, number] {
  const vertexCount = g.getAttribute('position').count, count = g.index?.count ?? vertexCount;
  if (!Number.isSafeInteger(triangle) || triangle < 0 || triangle * 3 + 2 >= count) throw new Error('patch triangle invalid');
  const i = triangle * 3;
  const ids: [number, number, number] = g.index ? [g.index.getX(i), g.index.getX(i + 1), g.index.getX(i + 2)] : [i, i + 1, i + 2];
  if (ids.some(v => !Number.isSafeInteger(v) || v < 0 || v >= vertexCount)) throw new Error('patch face references invalid vertex');
  return ids;
}
function worldVertex(mesh: SkinnedMesh, index: number): Vector3 {
  const vertex = mesh.getVertexPosition(index, new Vector3()).applyMatrix4(mesh.matrixWorld);
  if (!finiteVec(vertex.toArray())) throw new Error('nonfinite deformed vertex');
  return vertex;
}
function worldFace(mesh: SkinnedMesh, triangle: number): [Vector3, Vector3, Vector3, Vector3] {
  const ids = face(mesh.geometry, triangle), a = worldVertex(mesh, ids[0]), b = worldVertex(mesh, ids[1]), c = worldVertex(mesh, ids[2]);
  const normal = b.clone().sub(a).cross(c.clone().sub(a));
  if (normal.lengthSq() < 1e-20) throw new Error('deformed contact triangle degenerate');
  return [a, b, c, normal.normalize()];
}
function worldPrimitive(frame: Object3D, target: ContactPrimitive): { a: Vector3; b: Vector3; radius: number } {
  const e = frame.matrixWorld.elements;
  const x = new Vector3(e[0], e[1], e[2]), y = new Vector3(e[4], e[5], e[6]), z = new Vector3(e[8], e[9], e[10]);
  const sx = x.length(), sy = y.length(), sz = z.length();
  if (sx <= 1e-9 || Math.abs(sx - sy) > 1e-8 * sx || Math.abs(sx - sz) > 1e-8 * sx ||
    Math.max(Math.abs(x.dot(y)), Math.abs(x.dot(z)), Math.abs(y.dot(z))) > 1e-8 * sx * sx)
    throw new Error('primitive transform has nonuniform scale or shear');
  return { a: new Vector3(...target.a).applyMatrix4(frame.matrixWorld),
    b: new Vector3(...target.b).applyMatrix4(frame.matrixWorld), radius: target.radius * sx };
}

/** Bind once AFTER live model merge, sleeve conditioning and settled tier selection. Source hashes
 * must come from the actual GLB fetch bytes (hero-capture __assetProof), not a catalog assertion. */
export async function prepareSurfaceContacts(manifest: SurfaceContactManifest | null,
  roots: { rider: Object3D; bike: Object3D }, consumed: { riderSHA256: string; bikeSHA256: string }): Promise<{
    sample: () => Record<ContactId, ContactMeasurement>;
  }> {
  const probes = new Map<ContactId, () => ContactMeasurement>();
  const digests = new Map<SkinnedMesh, Promise<string>>();
  for (const id of CONTACT_IDS) {
    try {
      if (!manifest || manifest.schema !== 'rockhop-surface-contacts-v1') throw new Error('mapping missing or unsupported');
      if (![manifest.riderSHA256, manifest.bikeSHA256].every(h => digestPattern.test(h)) ||
        manifest.riderSHA256 !== consumed.riderSHA256 || manifest.bikeSHA256 !== consumed.bikeSHA256)
        throw new Error('consumed asset SHA256 differs from mapping');
      const entry = manifest.contacts[id];
      if (!entry) throw new Error('contact definition missing');
      // Freeze the supplied definition so a UI edit cannot silently change a prepared probe.
      const { patch, target } = structuredClone(entry);
      if (patch.reviewed !== true || !patch.evidence.trim()) throw new Error('surface patch not visually reviewed');
      if (target.verifiedAgainstVisibleGeometry !== true || !target.evidence.trim()) throw new Error('target primitive not verified against visible bike');
      if (!finiteVec(target.a) || !finiteVec(target.b) || !Number.isFinite(target.radius) || target.radius <= 0)
        throw new Error('invalid primitive definition');
      if (!Number.isSafeInteger(patch.subdivisions) || patch.subdivisions < 2 || patch.subdivisions > 64)
        throw new Error('patch subdivisions must be integer 2..64');
      const mesh = locate(roots.rider, patch.mesh) as SkinnedMesh, frame = locate(roots.bike, target.frame);
      if (!mesh.isSkinnedMesh) throw new Error('contact mesh is not skinned');
      if (!mesh.visible) throw new Error('contact mesh hidden');
      if (!digests.has(mesh)) digests.set(mesh, runtimeSurfaceSHA256(mesh));
      if (!digestPattern.test(patch.geometrySHA256) || await digests.get(mesh) !== patch.geometrySHA256)
        throw new Error('runtime geometry/skin binding differs from reviewed patch');
      if (!(patch.triangles?.length || patch.vertices?.length)) throw new Error('surface patch empty');
      for (const tri of patch.triangles ?? []) face(mesh.geometry, tri);
      for (const v of patch.vertices ?? []) {
        if (!Number.isSafeInteger(v.index) || v.index < 0 || v.index >= mesh.geometry.getAttribute('position').count ||
          !face(mesh.geometry, v.normalTriangle).includes(v.index)) throw new Error('vertex patch or incident normal triangle invalid');
      }
      const geometry = mesh.geometry;
      probes.set(id, () => {
        try {
          if (locate(roots.rider, patch.mesh) !== mesh || locate(roots.bike, target.frame) !== frame || mesh.geometry !== geometry)
            throw new Error('live scene/geometry changed; prepare mappings again');
          for (let node: Object3D | null = mesh; node; node = node.parent) if (!node.visible) throw new Error('contact mesh or ancestor hidden');
          const primitive = worldPrimitive(frame, target);
          let count = 0, minimum = Infinity, maximum = -Infinity, absolute = Infinity, maxAngle = 0, spacing = 0;
          let nearest: Vec3 = [0, 0, 0], nearestTarget: Vec3 = [0, 0, 0], nearestAngle = 0;
          const add = (point: Vector3, normal: Vector3) => {
            const d = pointPrimitiveDistance(point, primitive.a, primitive.b, primitive.radius, target.kind);
            const angle = Math.acos(Math.max(-1, Math.min(1, -normal.dot(new Vector3(...d.outwardNormalWorld))))) * 180 / Math.PI;
            count++; minimum = Math.min(minimum, d.signedDistanceM); maximum = Math.max(maximum, d.signedDistanceM); maxAngle = Math.max(maxAngle, angle);
            if (Math.abs(d.signedDistanceM) < absolute) {
              absolute = Math.abs(d.signedDistanceM); nearest = point.toArray(); nearestTarget = d.closestWorld; nearestAngle = angle;
            }
          };
          for (const tri of patch.triangles ?? []) {
            const [a, b, c, normal] = worldFace(mesh, tri), n = patch.subdivisions;
            spacing = Math.max(spacing, a.distanceTo(b) / n, b.distanceTo(c) / n, c.distanceTo(a) / n);
            for (let i = 0; i <= n; i++) for (let j = 0; j <= n - i; j++)
              add(a.clone().multiplyScalar(1 - (i + j) / n).addScaledVector(b, i / n).addScaledVector(c, j / n), normal);
          }
          for (const v of patch.vertices ?? []) add(worldVertex(mesh, v.index), worldFace(mesh, v.normalTriangle)[3]);
          return { status: 'measured', sampleCount: count, minimumSignedDistanceM: minimum, maximumSignedDistanceM: maximum,
            minimumAbsoluteSurfaceGapM: absolute, maximumSampledPenetrationM: Math.max(0, -minimum),
            nearestSampleWorld: nearest, nearestTargetWorld: nearestTarget, nearestNormalMismatchDeg: nearestAngle,
            maximumNormalMismatchDeg: maxAngle, maximumTriangleLatticeEdgeM: spacing };
        } catch (e) { return { status: 'unmeasured', reason: e instanceof Error ? e.message : String(e) }; }
      });
    } catch (e) {
      const reason = e instanceof Error ? e.message : String(e);
      probes.set(id, () => ({ status: 'unmeasured', reason }));
    }
  }
  return { sample: () => {
    roots.rider.updateWorldMatrix(true, true); roots.bike.updateWorldMatrix(true, true);
    return Object.fromEntries(CONTACT_IDS.map(id => [id, probes.get(id)!()])) as Record<ContactId, ContactMeasurement>;
  } };
}
