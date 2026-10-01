import { describe, expect, it } from 'vitest';
import { readFileSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { Bone, BufferGeometry, Float32BufferAttribute, Group, Mesh, MeshBasicMaterial, Skeleton, SkinnedMesh, Uint16BufferAttribute, Vector3 } from 'three';
import { CONTACT_IDS, pointPrimitiveDistance, prepareSurfaceContacts, runtimeSurfaceSHA256, runtimeRigidSurfaceSHA256, pointTriangleDistance, validateClosedTrianglePatch } from './surface-contacts.mjs';
import type { SurfaceContactManifest, ContactTriangleTarget, WorldTargetTriangle } from './surface-contacts.mjs';

const riderSHA256 = 'a'.repeat(64), bikeSHA256 = 'b'.repeat(64);
function fixture(detached = false) {
  const rider = new Group(), bike = new Group();
  rider.position.set(2, 3, 4); rider.rotation.y = 0.43;
  bike.position.copy(rider.position); bike.rotation.copy(rider.rotation);
  const geometry = new BufferGeometry();
  geometry.setAttribute('position', new Float32BufferAttribute([-.01, 0, .032, .01, 0, .032, -.01, .02, .032], 3));
  geometry.setIndex([0, 2, 1]); // outward palm surface faces into the grip, -z.
  geometry.setAttribute('skinIndex', new Uint16BufferAttribute([0, 1, 0, 0, 0, 1, 0, 0, 0, 1, 0, 0], 4));
  geometry.setAttribute('skinWeight', new Float32BufferAttribute([.25, .75, 0, 0, .25, .75, 0, 0, .25, .75, 0, 0], 4));
  const mesh = new SkinnedMesh(geometry, new MeshBasicMaterial()); mesh.name = 'visible-surface';
  const bone = new Bone(), tip = new Bone(); bone.name = 'root'; tip.name = 'tip'; bone.add(tip);
  rider.add(mesh);
  if (detached) { mesh.bindMode = 'detached'; rider.add(bone); } else mesh.add(bone);
  rider.updateMatrixWorld(true);
  mesh.bind(new Skeleton([bone, tip]));
  bike.updateMatrixWorld(true);
  return { rider, bike, mesh, bone, tip };
}
async function mapping(f: ReturnType<typeof fixture>): Promise<SurfaceContactManifest> {
  const entry = { patch: { mesh: { childPath: [0], name: 'visible-surface' }, geometrySHA256: await runtimeSurfaceSHA256(f.mesh),
    triangles: [0], subdivisions: 2, reviewed: true, evidence: 'synthetic unit triangle: all three vertices are the palm patch' },
  target: { frame: { childPath: [], name: '' }, kind: 'cylinder' as const, a: [0, -.1, 0] as [number, number, number],
    b: [0, .1, 0] as [number, number, number], radius: .022, verifiedAgainstVisibleGeometry: true, evidence: 'synthetic cylinder radius22mm' } };
  return { schema: 'rockhop-surface-contacts-v1', riderSHA256, bikeSHA256, contacts: Object.fromEntries(CONTACT_IDS.map(id => [id, entry])) };
}

describe('world-space primitive distance', () => {
  const a = new Vector3(0, -1, 0), b = new Vector3(0, 1, 0);
  it('distinguishes finite cylinder cap, side, corner and penetration', () => {
    expect(pointPrimitiveDistance(new Vector3(.25, 0, 0), a, b, .2, 'cylinder').signedDistanceM).toBeCloseTo(.05, 12);
    expect(pointPrimitiveDistance(new Vector3(.1, 0, 0), a, b, .2, 'cylinder').signedDistanceM).toBeCloseTo(-.1, 12);
    const cap = pointPrimitiveDistance(new Vector3(.1, 1.03, 0), a, b, .2, 'cylinder');
    expect(cap.signedDistanceM).toBeCloseTo(.03, 12); expect(cap.closestWorld).toEqual([.1, 1, 0]);
    expect(cap.outwardNormalWorld).toEqual([0, 1, 0]);
    expect(pointPrimitiveDistance(new Vector3(.23, 1.04, 0), a, b, .2, 'cylinder').signedDistanceM).toBeCloseTo(.05, 12);
  });
  it('uses capsule hemispheres instead of infinite line or cylinder end caps', () => {
    const end = pointPrimitiveDistance(new Vector3(0, 1.25, 0), a, b, .2, 'capsule');
    expect(end.signedDistanceM).toBeCloseTo(.05, 12); expect(end.closestWorld).toEqual([0, 1.2, 0]);
    expect(pointPrimitiveDistance(new Vector3(0, 1.1, 0), a, b, .2, 'capsule').signedDistanceM).toBeCloseTo(-.1, 12);
    expect(() => pointPrimitiveDistance(new Vector3(), a, a, .2, 'capsule')).toThrow('zero length');
  });
});

describe('posed skin surface measurement', () => {
  for (const detached of [false, true]) it(`applies nonidentity bind and world transforms once (${detached ? 'detached' : 'attached'})`, async () => {
    const f = fixture(detached), manifest = await mapping(f);
    const probe = await prepareSurfaceContacts(manifest, f, { riderSHA256, bikeSHA256 });
    const rest = probe.sample()['hand.L'];
    expect(rest.status).toBe('measured');
    if (rest.status !== 'measured') throw new Error(rest.reason);
    expect(rest.minimumAbsoluteSurfaceGapM).toBeCloseTo(.01, 7);
    expect(rest.nearestNormalMismatchDeg).toBeCloseTo(0, 5);
    expect(rest.sampleCount).toBe(6);
    f.tip.position.z = -.008; // 75% influence moves visible surface6mm, while root remains fixed.
    const posed = probe.sample()['hand.L'];
    if (posed.status !== 'measured') throw new Error(posed.reason);
    expect(posed.minimumAbsoluteSurfaceGapM).toBeCloseTo(.004, 7);
    const expected = new Vector3(0, 0, .026).applyMatrix4(f.rider.matrixWorld);
    expect(new Vector3(...posed.nearestSampleWorld).distanceTo(expected)).toBeLessThan(1e-7);
    // Bone-origin instrumentation cannot detect this geometry displacement.
    expect(f.bone.position.z).toBe(0);
    f.tip.position.z = -.024; // 18mm surface movement: 8mm inside the visible cylinder.
    const penetrating = probe.sample()['hand.L'];
    if (penetrating.status !== 'measured') throw new Error(penetrating.reason);
    expect(penetrating.maximumSampledPenetrationM).toBeCloseTo(.008, 7);
    expect(f.mesh.geometry.getAttribute('position').getZ(0)).toBeCloseTo(.032, 7);
  });
  it('uses posed triangle normals under bending, plus position morph targets', async () => {
    const f = fixture();
    f.mesh.geometry.morphAttributes.position = [new Float32BufferAttribute([0, 0, .002, 0, 0, .002, 0, 0, .002], 3)];
    f.mesh.geometry.morphTargetsRelative = true; f.mesh.updateMorphTargets();
    const probe = await prepareSurfaceContacts(await mapping(f), f, { riderSHA256, bikeSHA256 });
    f.mesh.morphTargetInfluences![0] = 1;
    let sample = probe.sample()['hand.L'];
    if (sample.status !== 'measured') throw new Error(sample.reason);
    expect(sample.minimumAbsoluteSurfaceGapM).toBeCloseTo(.012, 7);
    f.bone.rotation.y = Math.PI / 3;
    sample = probe.sample()['hand.L'];
    if (sample.status !== 'measured') throw new Error(sample.reason);
    // Rotate the whole surface around the cylinder's own y axis: radial separation and
    // opposing normal relationship are invariant despite world-space bend/rotation.
    expect(sample.minimumAbsoluteSurfaceGapM).toBeCloseTo(.012, 7);
    expect(sample.nearestNormalMismatchDeg).toBeCloseTo(0, 5);
  });
  it('leaves absent, unreviewed, stale and changed geometry unmeasured', async () => {
    const f = fixture();
    const absent = await prepareSurfaceContacts(null, f, { riderSHA256, bikeSHA256 });
    expect(Object.values(absent.sample()).every(v => v.status === 'unmeasured')).toBe(true);
    let manifest = await mapping(f);
    manifest.contacts['hand.L']!.patch.reviewed = false;
    const unreviewed = await prepareSurfaceContacts(manifest, f, { riderSHA256, bikeSHA256 });
    expect(unreviewed.sample()['hand.L']).toEqual({ status: 'unmeasured', reason: 'surface patch not visually reviewed' });
    manifest = await mapping(f);
    const stale = await prepareSurfaceContacts(manifest, f, { riderSHA256: 'c'.repeat(64), bikeSHA256 });
    expect(stale.sample()['foot.R'].status).toBe('unmeasured');
    const prepared = await prepareSurfaceContacts(manifest, f, { riderSHA256, bikeSHA256 });
    f.mesh.geometry = f.mesh.geometry.clone();
    expect(prepared.sample()['hand.R']).toEqual({ status: 'unmeasured', reason: 'live scene/geometry changed; prepare mappings again' });
  });
  it('rejects nonuniform collider scales rather than silently using a wrong radius', async () => {
    const f = fixture(), probe = await prepareSurfaceContacts(await mapping(f), f, { riderSHA256, bikeSHA256 });
    f.bike.scale.y = 2;
    expect(probe.sample()['hand.L']).toEqual({ status: 'unmeasured', reason: 'primitive transform has nonuniform scale or shear' });
  });
  it('supports explicit vertex patches with incident triangles and freezes reviewed definitions', async () => {
    const f = fixture(), manifest = await mapping(f);
    for (const id of CONTACT_IDS) {
      delete manifest.contacts[id]!.patch.triangles;
      manifest.contacts[id]!.patch.vertices = [{ index: 0, normalTriangle: 0 }];
    }
    const probe = await prepareSurfaceContacts(manifest, f, { riderSHA256, bikeSHA256 });
    // Post-prepare mutation of the external manifest does not relocate the accepted patch.
    const target = manifest.contacts['hand.L']!.target;
    if (target.kind === 'triangles') throw new Error('expected primitive');
    target.radius = .5;
    const sample = probe.sample()['hand.L'];
    if (sample.status !== 'measured') throw new Error(sample.reason);
    expect(sample.sampleCount).toBe(1);
    expect(sample.minimumSignedDistanceM).toBeCloseTo(Math.hypot(.01, .032) - .022, 7);
    expect(sample.maximumTriangleLatticeEdgeM).toBe(0); // Vertex-only patches have no area-coverage claim.
  });
  it('binds patch ordinals to runtime skin weights as well as visible positions', async () => {
    const f = fixture(), manifest = await mapping(f);
    f.mesh.geometry.getAttribute('skinWeight').setXYZW(0, 1, 0, 0, 0);
    const stale = await prepareSurfaceContacts(manifest, f, { riderSHA256, bikeSHA256 });
    expect(stale.sample()['foot.L']).toEqual({ status: 'unmeasured', reason: 'runtime geometry/skin binding differs from reviewed patch' });
  });
});


function boxTriangles(): WorldTargetTriangle[] {
  const v = [[-1,-1,-1],[1,-1,-1],[1,1,-1],[-1,1,-1],[-1,-1,1],[1,-1,1],[1,1,1],[-1,1,1]].map(p => new Vector3(...p));
  const faces = [[0,2,1],[0,3,2],[4,5,6],[4,6,7],[0,1,5],[0,5,4],[3,7,6],[3,6,2],[0,4,7],[0,7,3],[1,2,6],[1,6,5]];
  return faces.map((ids, ordinal) => ({ ordinal, a: v[ids[0]!]!, b: v[ids[1]!]!, c: v[ids[2]!]! }));
}
async function triangleMapping(f: ReturnType<typeof fixture>, closure: 'open' | 'closed' = 'open') {
  const targetGeometry = new BufferGeometry();
  if (closure === 'open') targetGeometry.setAttribute('position', new Float32BufferAttribute([-.2,-.2,.022, .2,-.2,.022, 0,.2,.022], 3));
  else targetGeometry.setAttribute('position', new Float32BufferAttribute(boxTriangles().flatMap(t => [...t.a.toArray(), ...t.b.toArray(), ...t.c.toArray()]), 3));
  const targetMesh = new Mesh(targetGeometry, new MeshBasicMaterial()); targetMesh.name = 'actual-bike-surface'; f.bike.add(targetMesh);
  const manifest = await mapping(f), runtime = closure === 'closed' ? Array.from({ length: 12 }, (_, i) => i) : [0];
  const target: ContactTriangleTarget = { kind: 'triangles', mesh: { childPath: [0], name: targetMesh.name }, frame: { childPath: [], name: '' },
    geometrySHA256: await runtimeRigidSurfaceSHA256(targetMesh), source: { assetSHA256: bikeSHA256, nodeIndex: 22, meshIndex: 8, primitiveIndex: 0,
      triangleOrdinals: runtime.map(i => i + 100) }, runtimeTriangleOrdinals: runtime, bindingReviewed: true, bindingReviewAuthority: 'parent',
    closedVolumeReviewed: closure === 'closed', evidence: 'synthetic test only: explicit source→runtime correspondence', closure, weldToleranceM: 1e-7 };
  for (const id of CONTACT_IDS) manifest.contacts[id]!.target = structuredClone(target);
  return { manifest, targetMesh };
}

describe('retained triangle surface targets', () => {
  it('returns exact nearest face, edge, corner, barycentric point and geometric normal', () => {
    const triangles: WorldTargetTriangle[] = [{ ordinal: 42, a: new Vector3(0,0,0), b: new Vector3(1,0,0), c: new Vector3(0,1,0) }];
    const face = pointTriangleDistance(new Vector3(.2,.3,.1), triangles, 'open');
    expect(new Vector3(...face.closestWorld).distanceTo(new Vector3(.2,.3,0))).toBeLessThan(1e-14); expect(face.barycentric[0]).toBeCloseTo(.5, 12);
    expect(face.barycentric[1]).toBeCloseTo(.2, 12); expect(face.barycentric[2]).toBeCloseTo(.3, 12);
    expect(face.triangleOrdinal).toBe(42); expect(face.outwardNormalWorld).toEqual([0,0,1]);
    const edge = pointTriangleDistance(new Vector3(.7,.7,.1), triangles, 'open');
    expect(edge.closestWorld).toEqual([.5,.5,0]); expect(edge.unsignedDistanceM).toBeCloseTo(.3, 12);
    const corner = pointTriangleDistance(new Vector3(-.3,-.4,0), triangles, 'open');
    expect(corner.closestWorld).toEqual([0,0,0]); expect(corner.barycentric).toEqual([1,0,0]); expect(corner.unsignedDistanceM).toBe(.5);
    const below = pointTriangleDistance(new Vector3(.2,.3,-.1), triangles, 'open');
    expect(below.sidedDistanceM).toBe(-.1); expect(below.signedDistanceM).toBeNull();
  });
  it('distinguishes closed inside/outside and rejects open, reversed, duplicated or disconnected shells', () => {
    const box = boxTriangles();
    expect(() => validateClosedTrianglePatch(box, 1e-7)).not.toThrow();
    expect(pointTriangleDistance(new Vector3(.25,0,0), box, 'closed').signedDistanceM).toBeCloseTo(-.75, 12);
    expect(pointTriangleDistance(new Vector3(1.2,1.3,1.4), box, 'closed').signedDistanceM).toBeCloseTo(Math.sqrt(.29), 12);
    expect(pointTriangleDistance(new Vector3(1,.2,.3), box, 'closed').signedDistanceM).toBe(0);
    expect(() => pointTriangleDistance(new Vector3(), box.slice(1), 'closed')).toThrow('boundary');
    expect(() => pointTriangleDistance(new Vector3(), box.map(t => ({ ...t, b: t.c, c: t.b })), 'closed')).toThrow('inward');
    expect(() => validateClosedTrianglePatch([...box, box[0]!], 1e-7)).toThrow('nonmanifold');
    const second = box.map(t => ({ ...t, a: t.a.clone().addScalar(5), b: t.b.clone().addScalar(5), c: t.c.clone().addScalar(5) }));
    expect(() => validateClosedTrianglePatch([...box, ...second], 1e-7)).toThrow('one connected shell');
  });
  it('reads actual rigid world triangles once under moving nonuniformly scaled bike frame', async () => {
    const f = fixture(), { manifest, targetMesh } = await triangleMapping(f);
    const probe = await prepareSurfaceContacts(manifest, f, { riderSHA256, bikeSHA256 });
    let sample = probe.sample()['foot.L'];
    if (sample.status !== 'measured') throw new Error(sample.reason);
    expect(sample.minimumAbsoluteSurfaceGapM).toBeCloseTo(.01,7); expect(sample.nearestNormalMismatchDeg).toBeCloseTo(0,5);
    expect(sample.nearestTargetTriangleOrdinal).toBe(0); expect(sample.nearestTargetBarycentric!.reduce((a,b) => a+b,0)).toBeCloseTo(1,12);
    expect(sample.maximumSampledPenetrationM).toBeNull(); expect(sample.penetrationStatus).toBe('unmeasured');
    expect(sample.minimumSignedDistanceM).toBeNull(); expect(sample.minimumSidedDistanceM).toBeCloseTo(.01,7);
    // Move BOTH live roots identically. Bike nonuniform scale remains exact for a triangle target.
    f.rider.position.x += 3; f.bike.position.x += 3; f.bike.scale.set(2,3,2);
    f.rider.updateMatrixWorld(true); // Renderer updates attached bindMatrixInverse before the post-render probe.
    f.bike.updateMatrixWorld(true);
    sample = probe.sample()['foot.L'];
    if (sample.status !== 'measured') throw new Error(sample.reason);
    expect(sample.minimumAbsoluteSurfaceGapM).toBeCloseTo(.012,7); expect(sample.minimumSidedDistanceM).toBeCloseTo(-.012,7);
    expect(sample.maximumSampledPenetrationM).toBeNull(); // Below an open face is not volume penetration.
    const targetWorld = new Vector3(...sample.nearestTargetWorld).applyMatrix4(targetMesh.matrixWorld.clone().invert());
    expect(targetWorld.z).toBeCloseTo(.022,7);
  });
  it('samples closed target penetration after skin deformation without replacing source ordinals', async () => {
    const f = fixture(), { manifest, targetMesh } = await triangleMapping(f, 'closed');
    targetMesh.scale.setScalar(.022);
    const probe = await prepareSurfaceContacts(manifest, f, { riderSHA256, bikeSHA256 });
    let sample = probe.sample()['hand.L'];
    if (sample.status !== 'measured') throw new Error(sample.reason);
    expect(sample.minimumSignedDistanceM).toBeCloseTo(.01,7);
    f.tip.position.z = -.024;
    sample = probe.sample()['hand.L'];
    if (sample.status !== 'measured') throw new Error(sample.reason);
    expect(sample.maximumSampledPenetrationM).toBeCloseTo(.008,7);
    expect(sample.penetrationStatus).toBe('measured');
    expect(sample.nearestTargetTriangleOrdinal).toBeLessThan(12); // Source ordinals start at100, live ordinals at0.
  });
  it('rejects absent source→live binding, stale target bytes, morph targets and ownership changes', async () => {
    const f = fixture(), { manifest, targetMesh } = await triangleMapping(f);
    const entry = manifest.contacts['hand.L']!;
    if (entry.target.kind !== 'triangles') throw new Error('expected triangles');
    entry.target.runtimeTriangleOrdinals = [];
    const unbound = await prepareSurfaceContacts(manifest, f, { riderSHA256, bikeSHA256 });
    expect(unbound.sample()['hand.L'].status).toBe('unmeasured');
    entry.target.runtimeTriangleOrdinals = [0]; entry.target.bindingReviewed = false;
    const notReviewed = await prepareSurfaceContacts(manifest, f, { riderSHA256, bikeSHA256 });
    expect(notReviewed.sample()['hand.L']).toEqual({ status:'unmeasured', reason:'source to runtime triangle binding not reviewed' });
    entry.target.bindingReviewed = true; entry.target.source.assetSHA256 = 'c'.repeat(64);
    const stale = await prepareSurfaceContacts(manifest, f, { riderSHA256, bikeSHA256 });
    expect(stale.sample()['hand.L']).toEqual({ status:'unmeasured', reason:'triangle source differs from consumed bike bytes' });
    entry.target.source.assetSHA256 = bikeSHA256;
    const probe = await prepareSurfaceContacts(manifest, f, { riderSHA256, bikeSHA256 });
    // Detect even a position write that omits needsUpdate: the retained runtime hash is a static contract.
    targetMesh.geometry.getAttribute('position').setZ(0, .02);
    expect(probe.sample()['hand.R']).toEqual({ status: 'unmeasured', reason: 'live target positions/indexing changed; prepare mappings again' });
    targetMesh.geometry.morphAttributes.position = [targetMesh.geometry.getAttribute('position')];
    await expect(runtimeRigidSurfaceSHA256(targetMesh)).rejects.toThrow('without position morphs');
    f.bike.remove(targetMesh);
    expect(probe.sample()['foot.L'].status).toBe('unmeasured');
  });
  it('leaves falsely declared closed and unreviewed volume patches unmeasured', async () => {
    const f = fixture(), { manifest } = await triangleMapping(f);
    const entry = manifest.contacts['foot.L']!;
    if (entry.target.kind !== 'triangles') throw new Error('expected triangles');
    entry.target.closure = 'closed'; entry.target.closedVolumeReviewed = false;
    const unreviewed = await prepareSurfaceContacts(manifest, f, { riderSHA256, bikeSHA256 });
    expect(unreviewed.sample()['foot.L']).toEqual({status:'unmeasured',reason:'closed target volume not reviewed'});
    entry.target.closedVolumeReviewed = true;
    const open = await prepareSurfaceContacts(manifest, f, { riderSHA256, bikeSHA256 });
    expect(open.sample()['foot.L'].status).toBe('unmeasured');
  });
});


it('rechecks closed winding after mirrored frame transform and observes frozen triangle correspondence', async () => {
  const f = fixture(), { manifest, targetMesh } = await triangleMapping(f, 'closed');
  targetMesh.scale.setScalar(.022);
  const probe = await prepareSurfaceContacts(manifest, f, { riderSHA256, bikeSHA256 });
  const target = manifest.contacts['hand.L']!.target;
  if (target.kind !== 'triangles') throw new Error('expected triangles');
  target.runtimeTriangleOrdinals = [100]; // External edits cannot silently turn source indices into live indices.
  expect(probe.sample()['hand.L'].status).toBe('measured');
  f.bike.scale.x = -1;
  expect(probe.sample()['hand.L']).toEqual({ status:'unmeasured', reason:'closed target is inward wound or has zero volume' });
});


it('verifies retained source peg triangles without promoting their ordinals into a live mapping', () => {
  interface RetainedPegs {
    sourceSHA256: string; fileFramePositions: number[][]; indices: number[];
    components: { component: number; sourceTriangleOrdinals: number[] }[];
  }
  for (const asset of ['bike-rookie.glb', 'bike-rookie-lod.glb', 'bike-pro.glb', 'bike-pro-lod.glb']) {
    const retained = JSON.parse(readFileSync(`docs/evidence/hero-remaster/one-rider-v2/contact-targets/pegs/${asset}.json`, 'utf8')) as RetainedPegs;
    expect(createHash('sha256').update(readFileSync(`public/models/${asset}`)).digest('hex')).toBe(retained.sourceSHA256);
    const patch = (component: RetainedPegs['components'][number]): WorldTargetTriangle[] => component.sourceTriangleOrdinals.map(ordinal => {
      const vertices = [0,1,2].map(i => new Vector3(...retained.fileFramePositions[retained.indices[ordinal * 3 + i]!]!));
      return { ordinal, a: vertices[0]!, b: vertices[1]!, c: vertices[2]! };
    });
    for (const c of retained.components.filter(c => c.component === 0 || c.component === 12))
      expect(() => validateClosedTrianglePatch(patch(c), 1e-7)).not.toThrow();
    if (asset.includes('-lod')) {
      const teeth = retained.components.filter(c => c.sourceTriangleOrdinals.length === 1);
      expect(teeth.length).toBe(20);
      for (const c of teeth) {
        const triangles = patch(c), t = triangles[0]!;
        expect(() => validateClosedTrianglePatch(triangles, 1e-7)).toThrow('boundary');
        const centroid = t.a.clone().add(t.b).add(t.c).divideScalar(3);
        const normal = t.b.clone().sub(t.a).cross(t.c.clone().sub(t.a)).normalize();
        const distance = pointTriangleDistance(centroid.addScaledVector(normal, -.001), triangles, 'open');
        expect(distance.unsignedDistanceM).toBeCloseTo(.001,10);
        expect(distance.sidedDistanceM).toBeCloseTo(-.001,10); expect(distance.signedDistanceM).toBeNull();
      }
    }
  }
});
