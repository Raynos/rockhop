/** Read-only, post-render visible-surface probe. Bundle this into a private harness build;
 * do not infer palm/sole patches from bone names, sockets, or skin weights. */
import { Triangle, Vector3 } from 'three';
import type { BufferGeometry, Mesh, Object3D, SkinnedMesh } from 'three';

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
export interface ContactTriangleTarget {
  kind: 'triangles';
  /** Exact live mesh and its owning bike frame. Source accessor indices are not live indices. */
  mesh: Locator;
  frame: Locator;
  geometrySHA256: string;
  source: { assetSHA256: string; nodeIndex: number; meshIndex: number; primitiveIndex: number; triangleOrdinals: number[] };
  /** Explicit, separately reviewed correspondence, one runtime ordinal per retained source face. */
  runtimeTriangleOrdinals: number[];
  bindingReviewed: boolean;
  bindingReviewAuthority: 'parent';
  /** Separate review of a simple, non-self-intersecting closed volume. */
  closedVolumeReviewed: boolean;
  evidence: string;
  closure: 'closed' | 'open';
  /** Metre-space vertex welding tolerance used only for closure checks. */
  weldToleranceM: number;
}
export type ContactTarget = ContactPrimitive | ContactTriangleTarget;
export interface SurfaceContactManifest {
  schema: 'rockhop-surface-contacts-v1';
  riderSHA256: string;
  bikeSHA256: string;
  contacts: Partial<Record<ContactId, { patch: SurfacePatch; target: ContactTarget }>>;
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
  minimumSignedDistanceM: number | null;
  maximumSignedDistanceM: number | null;
  minimumAbsoluteSurfaceGapM: number;
  maximumSampledPenetrationM: number | null;
  penetrationStatus: 'measured' | 'unmeasured';
  penetrationLimit: string;
  /** Open surfaces provide a local face-sided distance, never a volume penetration claim. */
  minimumSidedDistanceM: number | null;
  maximumSidedDistanceM: number | null;
  nearestTargetTriangleOrdinal: number | null;
  nearestTargetBarycentric: Vec3 | null;
  nearestTargetNormalWorld: Vec3;
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
function worldVertex(mesh: Mesh, index: number): Vector3 {
  const vertex = mesh.getVertexPosition(index, new Vector3()).applyMatrix4(mesh.matrixWorld);
  if (!finiteVec(vertex.toArray())) throw new Error('nonfinite deformed vertex');
  return vertex;
}
function worldFace(mesh: Mesh, triangle: number): [Vector3, Vector3, Vector3, Vector3] {
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

export interface WorldTargetTriangle { ordinal: number; a: Vector3; b: Vector3; c: Vector3 }
export interface TriangleDistance {
  unsignedDistanceM: number;
  signedDistanceM: number | null;
  sidedDistanceM: number;
  closestWorld: Vec3;
  outwardNormalWorld: Vec3;
  triangleOrdinal: number;
  barycentric: Vec3;
}

/** Hash the actual rigid live target indexing/positions. Morphing/skinned targets need a
 * separate deformation contract; they are intentionally unsupported here. */
export async function runtimeRigidSurfaceSHA256(mesh: Mesh): Promise<string> {
  if ((mesh as SkinnedMesh).isSkinnedMesh || mesh.geometry.morphAttributes.position?.length)
    throw new Error('triangle bike target must be rigid without position morphs');
  const g = mesh.geometry, p = g.getAttribute('position');
  if (!p) throw new Error('triangle target has no positions');
  const payload = JSON.stringify({ schema: 'rockhop-rigid-target-v1', positions:
    Array.from({ length: p.count }, (_, i) => [p.getX(i), p.getY(i), p.getZ(i)]),
  index: g.index ? Array.from({ length: g.index.count }, (_, i) => g.index!.getX(i)) : null });
  const digest = await globalThis.crypto.subtle.digest('SHA-256', new TextEncoder().encode(payload));
  return Array.from(new Uint8Array(digest), b => b.toString(16).padStart(2, '0')).join('');
}

/** Conservative eligibility check: one connected, edge-manifold, outward-wound shell.
 * This does not certify absence of geometric self-intersections; human review is required. */
export function validateClosedTrianglePatch(triangles: WorldTargetTriangle[], weldToleranceM: number): void {
  if (!Number.isFinite(weldToleranceM) || weldToleranceM < 1e-9 || weldToleranceM > 1e-4)
    throw new Error('triangle welding tolerance must be 1e-9..1e-4 metres');
  const vertices: Vector3[] = [], buckets = new Map<string, number[]>(), edges = new Map<string, { direction: number; faces: number[] }>();
  const welded = (p: Vector3): number => {
    const x = Math.floor(p.x / weldToleranceM), y = Math.floor(p.y / weldToleranceM), z = Math.floor(p.z / weldToleranceM);
    for (let dx = -1; dx <= 1; dx++) for (let dy = -1; dy <= 1; dy++) for (let dz = -1; dz <= 1; dz++)
      for (const id of buckets.get(`${x + dx}:${y + dy}:${z + dz}`) ?? [])
        if (vertices[id]!.distanceTo(p) <= weldToleranceM) return id;
    const id = vertices.length, key = `${x}:${y}:${z}`;
    vertices.push(p); buckets.set(key, [...(buckets.get(key) ?? []), id]); return id;
  };
  let volume = 0;
  const origin = triangles[0]?.a;
  if (!origin) throw new Error('triangle target empty');
  for (const [fi, t] of triangles.entries()) {
    if (![t.a, t.b, t.c].every(p => finiteVec(p.toArray()))) throw new Error('nonfinite target triangle');
    const ids = [welded(t.a), welded(t.b), welded(t.c)];
    if (new Set(ids).size !== 3 || new Triangle(t.a, t.b, t.c).getArea() < 1e-14)
      throw new Error('triangle target degenerate under weld');
    for (let i = 0; i < 3; i++) {
      const a = ids[i]!, b = ids[(i + 1) % 3]!, key = `${Math.min(a, b)}:${Math.max(a, b)}`;
      const edge = edges.get(key) ?? { direction: 0, faces: [] };
      edge.direction += a < b ? 1 : -1; edge.faces.push(fi); edges.set(key, edge);
    }
    volume += t.a.clone().sub(origin).dot(t.b.clone().sub(origin).cross(t.c.clone().sub(origin))) / 6;
  }
  const neighbours = triangles.map(() => new Set<number>());
  for (const edge of edges.values()) {
    if (edge.faces.length !== 2 || edge.direction !== 0) throw new Error('closed target has boundary, nonmanifold edge or inconsistent winding');
    neighbours[edge.faces[0]!]!.add(edge.faces[1]!); neighbours[edge.faces[1]!]!.add(edge.faces[0]!);
  }
  const seen = new Set<number>([0]), pending = [0];
  while (pending.length) for (const n of neighbours[pending.pop()!]!) if (!seen.has(n)) { seen.add(n); pending.push(n); }
  if (seen.size !== triangles.length) throw new Error('closed target must be one connected shell');
  if (volume <= 1e-15) throw new Error('closed target is inward wound or has zero volume');
}

/** Exact point→retained triangle patch distance. Closed patches are checked for closure,
 * winding and connectivity; a separate review must rule out self-intersection. Open sided
 * distance is only relative to the nearest face. */
export function pointTriangleDistance(point: Vector3, triangles: WorldTargetTriangle[], closure: 'open' | 'closed', weldToleranceM = 1e-7): TriangleDistance {
  if (closure === 'closed') validateClosedTrianglePatch(triangles, weldToleranceM);
  return pointValidatedTriangles(point, triangles, closure);
}
function pointValidatedTriangles(point: Vector3, triangles: WorldTargetTriangle[], closure: 'open' | 'closed'): TriangleDistance {
  if (!finiteVec(point.toArray()) || !triangles.length) throw new Error('invalid point or empty triangle patch');
  let best: TriangleDistance | undefined, angle = 0;
  for (const t of triangles) {
    const tri = new Triangle(t.a, t.b, t.c), normal = tri.getNormal(new Vector3());
    if (tri.getArea() < 1e-14 || !finiteVec(normal.toArray())) throw new Error('target triangle degenerate');
    const closest = tri.closestPointToPoint(point, new Vector3()), distance = closest.distanceTo(point);
    if (!best || distance < best.unsignedDistanceM) {
      const bary = tri.getBarycoord(closest, new Vector3());
      if (!bary) throw new Error('target barycentric undefined');
      best = { unsignedDistanceM: distance, signedDistanceM: null, sidedDistanceM: point.clone().sub(closest).dot(normal),
        closestWorld: closest.toArray(), outwardNormalWorld: normal.toArray(), triangleOrdinal: t.ordinal, barycentric: bary.toArray() };
    }
    if (closure === 'closed') {
      const a = t.a.clone().sub(point), b = t.b.clone().sub(point), c = t.c.clone().sub(point);
      const la = a.length(), lb = b.length(), lc = c.length();
      angle += 2 * Math.atan2(a.dot(b.clone().cross(c)), la * lb * lc + a.dot(b) * lc + b.dot(c) * la + c.dot(a) * lb);
    }
  }
  if (!best) throw new Error('triangle target empty');
  if (closure === 'closed') {
    if (best.unsignedDistanceM <= 1e-10) best.signedDistanceM = 0;
    else {
      const winding = Math.abs(angle) / (4 * Math.PI);
      if (Math.min(Math.abs(winding), Math.abs(winding - 1)) > 1e-5) throw new Error('closed target inside classification ambiguous');
      best.signedDistanceM = best.unsignedDistanceM * (winding > .5 ? -1 : 1);
    }
  }
  return best;
}

function belongsTo(mesh: Object3D, frame: Object3D): boolean {
  for (let node: Object3D | null = mesh; node; node = node.parent) if (node === frame) return true;
  return false;
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
      if (target.kind !== 'triangles') {
        if (target.verifiedAgainstVisibleGeometry !== true || !target.evidence.trim()) throw new Error('target primitive not verified against visible bike');
        if (!finiteVec(target.a) || !finiteVec(target.b) || !Number.isFinite(target.radius) || target.radius <= 0)
          throw new Error('invalid primitive definition');
      }
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
      let targetMesh: Mesh | undefined, targetGeometry: BufferGeometry | undefined;
      let targetPositionSnapshot: number[] = [], targetIndexSnapshot: number[] = [];
      if (target.kind === 'triangles') {
        if (!target.bindingReviewed || target.bindingReviewAuthority !== 'parent' || !target.evidence.trim()) throw new Error('source to runtime triangle binding not reviewed');
        if (target.source.assetSHA256 !== consumed.bikeSHA256 || !digestPattern.test(target.source.assetSHA256))
          throw new Error('triangle source differs from consumed bike bytes');
        if (![target.source.nodeIndex, target.source.meshIndex, target.source.primitiveIndex].every(v => Number.isSafeInteger(v) && v >= 0))
          throw new Error('triangle source accessor identity invalid');
        const source = target.source.triangleOrdinals, runtime = target.runtimeTriangleOrdinals;
        if (!source?.length || !runtime?.length || source.length !== runtime.length ||
          source.some(v => !Number.isSafeInteger(v) || v < 0) || new Set(source).size !== source.length || new Set(runtime).size !== runtime.length)
          throw new Error('explicit source to runtime triangle correspondence missing or duplicated');
        if (target.closure !== 'open' && target.closure !== 'closed') throw new Error('triangle closure missing');
        if (target.closure === 'closed' && target.closedVolumeReviewed !== true) throw new Error('closed target volume not reviewed');
        targetMesh = locate(roots.bike, target.mesh) as Mesh;
        if (!targetMesh.isMesh || !belongsTo(targetMesh, frame)) throw new Error('triangle mesh is not owned by selected bike frame');
        if (!digestPattern.test(target.geometrySHA256) || await runtimeRigidSurfaceSHA256(targetMesh) !== target.geometrySHA256)
          throw new Error('runtime target geometry differs from reviewed binding');
        for (const tri of runtime) face(targetMesh.geometry, tri);
        targetGeometry = targetMesh.geometry;
        const p = targetGeometry.getAttribute('position');
        targetPositionSnapshot = Array.from({ length: p.count * 3 }, (_, i) => p.getComponent(Math.floor(i / 3), i % 3));
        targetIndexSnapshot = targetGeometry.index ? Array.from({ length: targetGeometry.index.count }, (_, i) => targetGeometry!.index!.getX(i)) : [];
      }
      const geometry = mesh.geometry;
      probes.set(id, () => {
        try {
          if (locate(roots.rider, patch.mesh) !== mesh || locate(roots.bike, target.frame) !== frame || mesh.geometry !== geometry)
            throw new Error('live scene/geometry changed; prepare mappings again');
          for (let node: Object3D | null = mesh; node; node = node.parent) if (!node.visible) throw new Error('contact mesh or ancestor hidden');
          let triangles: WorldTargetTriangle[] = [];
          if (target.kind === 'triangles') {
            if (!targetMesh || (targetMesh as SkinnedMesh).isSkinnedMesh || targetMesh.geometry.morphAttributes.position?.length || locate(roots.bike, target.mesh) !== targetMesh || targetMesh.geometry !== targetGeometry ||
              !belongsTo(targetMesh, frame))
              throw new Error('live target geometry/frame changed; prepare mappings again');
            const p = targetMesh.geometry.getAttribute('position'), index = targetMesh.geometry.index;
            if (p.count * 3 !== targetPositionSnapshot.length || targetPositionSnapshot.some((v, i) => v !== p.getComponent(Math.floor(i / 3), i % 3)) ||
              (index?.count ?? 0) !== targetIndexSnapshot.length || targetIndexSnapshot.some((v, i) => v !== index!.getX(i)))
              throw new Error('live target positions/indexing changed; prepare mappings again');
            for (let node: Object3D | null = targetMesh; node; node = node.parent) if (!node.visible) throw new Error('target mesh or ancestor hidden');
            triangles = target.runtimeTriangleOrdinals.map(ordinal => {
              const [a, b, c] = worldFace(targetMesh!, ordinal); return { ordinal, a, b, c };
            });
            if (target.closure === 'closed') validateClosedTrianglePatch(triangles, target.weldToleranceM);
          }
          const primitive = target.kind === 'triangles' ? null : worldPrimitive(frame, target);
          const signed = target.kind !== 'triangles' || target.closure === 'closed';
          let minimumSided = Infinity, maximumSided = -Infinity;
          let nearestOrdinal: number | null = null, nearestBarycentric: Vec3 | null = null, nearestNormal: Vec3 = [0, 0, 0];
          let count = 0, minimum = Infinity, maximum = -Infinity, absolute = Infinity, maxAngle = 0, spacing = 0;
          let nearest: Vec3 = [0, 0, 0], nearestTarget: Vec3 = [0, 0, 0], nearestAngle = 0;
          const add = (point: Vector3, normal: Vector3) => {
            const d = target.kind === 'triangles' ? pointValidatedTriangles(point, triangles, target.closure) :
              pointPrimitiveDistance(point, primitive!.a, primitive!.b, primitive!.radius, target.kind);
            const unsignedDistance = 'unsignedDistanceM' in d ? d.unsignedDistanceM : Math.abs(d.signedDistanceM!);
            if ('sidedDistanceM' in d) { minimumSided = Math.min(minimumSided, d.sidedDistanceM); maximumSided = Math.max(maximumSided, d.sidedDistanceM); }
            const angle = Math.acos(Math.max(-1, Math.min(1, -normal.dot(new Vector3(...d.outwardNormalWorld))))) * 180 / Math.PI;
            count++;
            if (d.signedDistanceM !== null) { minimum = Math.min(minimum, d.signedDistanceM); maximum = Math.max(maximum, d.signedDistanceM); }
            maxAngle = Math.max(maxAngle, angle);
            if (unsignedDistance < absolute) {
              absolute = unsignedDistance; nearest = point.toArray(); nearestTarget = d.closestWorld; nearestAngle = angle;
              nearestNormal = d.outwardNormalWorld;
              if ('triangleOrdinal' in d) { nearestOrdinal = d.triangleOrdinal; nearestBarycentric = d.barycentric; }
            }
          };
          for (const tri of patch.triangles ?? []) {
            const [a, b, c, normal] = worldFace(mesh, tri), n = patch.subdivisions;
            spacing = Math.max(spacing, a.distanceTo(b) / n, b.distanceTo(c) / n, c.distanceTo(a) / n);
            for (let i = 0; i <= n; i++) for (let j = 0; j <= n - i; j++)
              add(a.clone().multiplyScalar(1 - (i + j) / n).addScaledVector(b, i / n).addScaledVector(c, j / n), normal);
          }
          for (const v of patch.vertices ?? []) add(worldVertex(mesh, v.index), worldFace(mesh, v.normalTriangle)[3]);
          return { status: 'measured', sampleCount: count, minimumSignedDistanceM: signed ? minimum : null, maximumSignedDistanceM: signed ? maximum : null,
            minimumAbsoluteSurfaceGapM: absolute, maximumSampledPenetrationM: signed ? Math.max(0, -minimum) : null,
            penetrationStatus: signed ? 'measured' : 'unmeasured',
            penetrationLimit: signed ? 'point samples only; no whole mesh collision or self-intersection certificate' : 'open target has no enclosed volume; nearest-face sided distance only',
            minimumSidedDistanceM: target.kind === 'triangles' ? minimumSided : null,
            maximumSidedDistanceM: target.kind === 'triangles' ? maximumSided : null,
            nearestTargetTriangleOrdinal: nearestOrdinal, nearestTargetBarycentric: nearestBarycentric, nearestTargetNormalWorld: nearestNormal,
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
