import { describe, expect, it } from 'vitest';
import { Bone, BufferGeometry, Float32BufferAttribute, Group, MeshBasicMaterial, Skeleton, SkinnedMesh, Uint16BufferAttribute, Vector3 } from 'three';
import { CONTACT_IDS, pointPrimitiveDistance, prepareSurfaceContacts, runtimeSurfaceSHA256 } from './surface-contacts.mjs';
import type { SurfaceContactManifest } from './surface-contacts.mjs';

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
    manifest.contacts['hand.L']!.target.radius = .5;
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
