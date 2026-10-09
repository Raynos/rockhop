// Make an unchanged-index control for exactly the same surface sampling method.
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { openGlb, accessorBytes, fileSha, sha } from '../geometry01/glb.mjs';
const [input, reductionPath, outDir] = process.argv.slice(2);
const glb = openGlb(input), report = JSON.parse(fs.readFileSync(reductionPath));
assert.equal(fileSha(input), report.source.sha256);
report.mode = 'unchanged-source-control';
fs.mkdirSync(outDir, { recursive: true });
for (const row of report.meshes) {
  const p = glb.json.meshes[row.mesh].primitives[0];
  const bytes = await accessorBytes(glb, p.indices);
  const output = path.join(outDir, `mesh${row.mesh}-indices.u32`);
  fs.writeFileSync(output, bytes);
  row.triangles = row.originalTriangles;
  row.triangleReductionPercent = 0;
  row.referencedVertices = row.originalVertices;
  row.aggregateEstimatedErrorMeters = 0;
  row.indices = { path: output, sha256: sha(bytes), bytes: bytes.length };
}
fs.closeSync(glb.fd);
fs.writeFileSync(path.join(outDir, 'reduction.json'), `${JSON.stringify(report, null, 2)}\n`);
