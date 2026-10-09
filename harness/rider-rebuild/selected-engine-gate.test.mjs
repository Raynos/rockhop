import test from 'node:test';
import assert from 'node:assert/strict';
import fs from 'node:fs';
import crypto from 'node:crypto';
import { decodeGLB, proveDriverInvariant, inspectSelectedSource, deriveCalibration, hashNamedFields,
  SELECTED_OBJECTS, REFERENCE_SHA } from './selected-engine-gate.mjs';

const base = 'harness/out/rider-rebuild/construction01/combined04/';
const available = fs.existsSync(base + 'rider.glb') && fs.existsSync(base + 'rider-contract.json');
const options = { skip: available ? false : 'Ignored original actual rig reference is absent; no generated appearance fixture substitutes for it.' };
const reference = available ? decodeGLB(fs.readFileSync(base + 'rider.glb')) : null;
const contract = available ? JSON.parse(fs.readFileSync(base + 'rider-contract.json')) : null;
const calibration = JSON.parse(fs.readFileSync('docs/evidence/rider-rebuild/runtime02/combined04-adaptive20-pose.json'));
const clone = () => ({ ...reference, document: structuredClone(reference.document) });
// Restrict a reference document to its actual authored body for the rig-only test.
// It is never a full-outfit acceptance fixture or passed to the selected intake.
const rigOnly = () => {
  const result = clone();
  for (const node of result.document.nodes) if (node.name !== 'RiderBody') delete node.mesh;
  return result;
};
const SHA_NEW = crypto.createHash('sha256').update('new source identity, not asset bytes').digest('hex');

void test('original actual 75-joint control is decoded without mutating source bytes', options, () => {
  assert.equal(reference.sha256, REFERENCE_SHA);
  assert.equal(reference.document.skins[0].joints.length, 75);
  const inverse = reference.accessor(reference.document.skins[0].inverseBindMatrices);
  assert.equal(inverse.length, 75); assert.equal(inverse[0].length, 16);
  assert.equal(decodeGLB(fs.readFileSync(base + 'rider.glb')).sha256, REFERENCE_SHA);
});

void test('exact actual rig control inputs produce a measured calibration invariant', options, () => {
  const proof = proveDriverInvariant(reference, rigOnly(), contract, structuredClone(contract));
  assert.equal(proof.jointCount, 75);
  assert.equal(proof.allRestHierarchyAndInverseBindsExact, true);
  const next = deriveCalibration(calibration, REFERENCE_SHA, SHA_NEW, proof);
  assert.equal(next.accepted, false);
  assert.equal(next.sourceSHA256, SHA_NEW);
  assert.deepEqual(next.driver, calibration.driver);
  assert.equal(next.provenance.referenceSourceSHA256, REFERENCE_SHA);
  assert.equal(calibration.sourceSHA256, REFERENCE_SHA, 'Original calibration remains intact');
});

void test('one real rest joint displacement rejects inherited calibration', options, () => {
  const candidate = rigOnly(), index = candidate.document.skins[0].joints[13];
  const node = candidate.document.nodes[index];
  node.translation = [...(node.translation ?? [0, 0, 0])]; node.translation[0] += 1e-7;
  assert.throws(() => proveDriverInvariant(reference, candidate, contract, contract), /rest transform/);
});

void test('a changed actual skin inverse bind rejects inherited calibration', options, () => {
  const candidate = rigOnly(), original = candidate.accessor;
  candidate.accessor = index => {
    const rows = original(index);
    if (index === candidate.document.skins[0].inverseBindMatrices) rows[3][12] += 1e-7;
    return rows;
  };
  assert.throws(() => proveDriverInvariant(reference, candidate, contract, contract), /inverse bind/);
});

void test('native source endpoint and sole changes require fresh calibration', options, () => {
  const changed = structuredClone(contract);
  changed.nativeRest.bones.find(row => row.name === 'SoleSocket.L').head[2] += 1e-7;
  assert.throws(() => proveDriverInvariant(reference, rigOnly(), contract, changed), /endpoint\/mass\/socket/);
});

void test('digit semantic roles and axes cannot be silently changed under old proof', options, () => {
  const changed = structuredClone(contract);
  changed.specification.hands.left.digits.index.reverse();
  assert.throws(() => proveDriverInvariant(reference, rigOnly(), contract, changed), /semantic input/);
  const changedAxis = structuredClone(contract);
  changedAxis.driver.digitFlex.left['DEF-thumb.01.L'].axisLocal[0] += 1e-7;
  assert.throws(() => proveDriverInvariant(reference, rigOnly(), contract, changedAxis), /axes, limits or placement/);
});

void test('rejected actual coarse outfit cannot pass selected seven-piece intake', options, () => {
  assert.throws(() => inspectSelectedSource(reference, contract,
    { authorObjects: Object.keys(contract.specification.meshNames) },
    { glbSHA256: reference.sha256, nativeReceiptSHA256: 'receipt' }, 'receipt'), /Complete real selected native inventory/);
  assert.ok(!Object.keys(contract.specification.meshNames).includes('ActualSelectedGlove.L'));
  assert.equal(SELECTED_OBJECTS.length, 7);
});

void test('a forged source SHA fails before complete-outfit claims are considered', options, () => {
  const bad = structuredClone(contract); bad.glbSHA256 = SHA_NEW;
  assert.throws(() => inspectSelectedSource(reference, bad, {}, {}, 'receipt'), /Contract binds exact GLB/);
});

void test('calibration transfer requires a new identity and the preceding exact proof', () => {
  assert.throws(() => deriveCalibration(calibration, REFERENCE_SHA, REFERENCE_SHA, {}), /New selected source SHA/);
  assert.throws(() => deriveCalibration(calibration, REFERENCE_SHA, SHA_NEW, {}), /Proof precedes/);
  assert.throws(() => deriveCalibration({ ...calibration, sourceSHA256: SHA_NEW }, REFERENCE_SHA, SHA_NEW, {}), /Original calibration/);
});

void test('named-field receipt encoding matches actual Python receipt bytes', () => {
  // Numeric boundary vectors exercise the cross-language receipt, not model art.
  const rows = [[['JointA', 1]], [['JointA', 1678 / 2 ** 24], ['JointB', 1 - 1678 / 2 ** 24]]];
  const pythonEncoding = '[[["JointA",1.0]],[["JointA",0.00010001659393310547],["JointB",0.9998999834060669]]]';
  assert.equal(hashNamedFields(rows), crypto.createHash('sha256').update(pythonEncoding).digest('hex'));
});

void test('all 10582 actual body field encodings match the independent Python proof', options, () => {
  const fields = JSON.parse(fs.readFileSync('harness/out/rider-rebuild/construction01/rig04/weights-four.json'));
  const proof = JSON.parse(fs.readFileSync('docs/evidence/rider-rebuild/construction02/selected-field-protocol01.json'));
  const rows = fields.map(field => {
    const kept = field.map(([name, w]) => [name, Math.fround(w)]).filter(([, w]) => w > .0001)
      .sort((a, b) => a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0);
    const total = kept.reduce((sum, [, w]) => sum + w, 0), grid = 2 ** 24;
    const ideals = kept.map(([, w]) => w / total * grid), counts = ideals.map(w => Math.max(1678, Math.floor(w)));
    const remaining = grid - counts.reduce((sum, w) => sum + w, 0);
    if (remaining > 0) {
      const ranks = counts.map((_, i) => i).sort((a, b) => (ideals[b] - counts[b]) - (ideals[a] - counts[a])
        || (kept[a][0] < kept[b][0] ? -1 : 1));
      for (const i of ranks.slice(0, remaining)) counts[i]++;
    } else if (remaining < 0) {
      const largest = counts.map((_, i) => i).sort((a, b) => counts[b] - counts[a]
        || (kept[a][0] > kept[b][0] ? -1 : 1))[0];
      counts[largest] += remaining;
    }
    return kept.map(([name], i) => [name, Math.fround(counts[i] / grid)]);
  });
  assert.equal(rows.length, 10582);
  assert.equal(hashNamedFields(rows), proof.canonicalNamedFieldSHA256);
});

void test('malformed GLB header rejects decoding', () => {
  assert.throws(() => decodeGLB(Buffer.alloc(32)), /Expected GLB/);
});
