// Parent invokes only after candidate admission; no browser or source mutation.
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { openGlb, readAt, viewBytes, fileSha } from '../download-opt01/geometry01/glb.mjs';
import { BASELINE, sha, validateCuffParity } from './transfer.mjs';

export async function verifyParityFiles(parityFile, candidateFile, { decoded = true } = {}) {
  const parityBytes = fs.readFileSync(parityFile), parity = JSON.parse(parityBytes);
  assert.equal(fileSha(parity.baseline.path), BASELINE);
  assert.equal(fileSha(candidateFile), parity.candidate.sha256);
  assert.equal(fs.statSync(candidateFile).size, parity.candidate.bytes);
  assert.deepEqual(Object.keys(parity.sourcePatch).sort(), ['patch', 'report']);
  for (const record of Object.values(parity.sourcePatch)) {
    assert.equal(fileSha(record.path), record.sha256, 'Exact source patch/fit bytes');
    assert.equal(fs.statSync(record.path).size, record.bytes);
  }
  const baseline = openGlb(parity.baseline.path), candidate = openGlb(candidateFile);
  try {
    const facts = validateCuffParity(parity, baseline.json, candidate.json);
    // Exact prefix plus exact existing views/codecs proves all unchanged payloads.
    const baselineBinBytes = fs.statSync(parity.baseline.path).size - baseline.binOffset;
    for (let offset = 0; offset < baselineBinBytes; offset += 1024 * 1024) {
      const count = Math.min(1024 * 1024, baselineBinBytes - offset);
      assert(readAt(baseline.fd, count, baseline.binOffset + offset).equals(
        readAt(candidate.fd, count, candidate.binOffset + offset)), 'Actual original BIN prefix differs');
    }
    for (const row of parity.imagePayloadsExact) {
      const view = baseline.json.bufferViews[row.bufferView];
      assert.equal(sha(readAt(baseline.fd, view.byteLength, baseline.binOffset + (view.byteOffset ?? 0))), row.beforeSHA256);
    }
    if (decoded) {
      for (const row of parity.protectedAccessorStreamsExact) {
        assert.equal(sha(await viewBytes(baseline, baseline.json.accessors[row.accessor].bufferView)), row.beforeDecodedSHA256,
          `Actual protected decoded accessor ${row.accessor}`);
      }
      for (const row of parity.changedAccessors) {
        assert.equal(sha(await viewBytes(baseline, baseline.json.accessors[row.accessor].bufferView)), row.beforeDecodedSHA256);
        assert.equal(sha(await viewBytes(candidate, candidate.json.accessors[row.accessor].bufferView)), row.afterDecodedSHA256);
      }
    }
    return { ...facts, accepted: false, pass: true, sourceSHA256: parity.candidate.sha256,
      parityReceiptSHA256: sha(parityBytes), actualOriginalBINPrefixChecked: true,
      actualImagePayloadHashesChecked: true, actualDecodedAccessorHashesChecked: decoded,
      baselineJSON: baseline.json, candidateJSON: candidate.json };
  } finally { fs.closeSync(baseline.fd); fs.closeSync(candidate.fd); }
}

if (process.argv[1]?.endsWith('/verify-parity.mjs')) {
  assert.equal(process.argv.length, 4, 'Parity receipt and actual candidate required');
  const { baselineJSON, candidateJSON, ...facts } = await verifyParityFiles(process.argv[2], process.argv[3]);
  console.log(JSON.stringify(facts));
}
