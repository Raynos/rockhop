// Distinguish real seams from sub-texel exporter differences before protection.
import fs from 'node:fs';
import { MeshoptSimplifier } from 'meshoptimizer/simplifier';
import { openGlb, accessorBytes } from '../geometry01/glb.mjs';
const [input, output] = process.argv.slice(2);
await MeshoptSimplifier.ready;
const glb = openGlb(input), result = [];
for (const mi of [0, 2, 5]) {
  const p = glb.json.meshes[mi].primitives[0];
  const floats = async i => {
    const b = await accessorBytes(glb, i);
    return new Float32Array(b.buffer, b.byteOffset, b.length / 4);
  };
  const positions = await floats(p.attributes.POSITION), normals = await floats(p.attributes.NORMAL);
  const uvs = await floats(p.attributes.TEXCOORD_0);
  const remap = MeshoptSimplifier.generatePositionRemap(positions, 3);
  const uvLimits = [0, 1e-8, 1e-7, 1e-6, 1e-5, 0.25 / 4096, 0.001, 0.01, 0.1, 1, Infinity];
  const normalLimits = [0, 0.001, 0.01, 0.1, 0.5, 1, 5, 30, 180, Infinity];
  const uvHistogram = Array(uvLimits.length).fill(0), normalHistogram = Array(normalLimits.length).fill(0);
  let maxUv = 0, maxNormal = 0;
  for (let v = 0; v < remap.length; v++) {
    const r = remap[v]; if (v === r) continue;
    const uvError = Math.hypot(uvs[v * 2] - uvs[r * 2], uvs[v * 2 + 1] - uvs[r * 2 + 1]);
    let dot = 0, normA = 0, normB = 0;
    for (let k = 0; k < 3; k++) {
      const a = normals[v * 3 + k], b = normals[r * 3 + k];
      dot += a * b; normA += a * a; normB += b * b;
    }
    const angle = Math.acos(Math.max(-1, Math.min(1, dot / Math.sqrt(normA * normB)))) * 180 / Math.PI;
    uvHistogram[uvLimits.findIndex(limit => uvError <= limit)]++;
    normalHistogram[normalLimits.findIndex(limit => angle <= limit)]++;
    maxUv = Math.max(maxUv, uvError); maxNormal = Math.max(maxNormal, angle);
  }
  const row = { mesh: mi, name: glb.json.meshes[mi].name,
    uvBinsUpperLimit: uvLimits.map(v => Number.isFinite(v) ? v : 'Infinity'), uvHistogram,
    normalBinsUpperDegrees: normalLimits.map(v => Number.isFinite(v) ? v : 'Infinity'), normalHistogram,
    maxUv, maxNormalDegrees: maxNormal };
  result.push(row); console.log(JSON.stringify(row));
}
fs.closeSync(glb.fd); fs.writeFileSync(output, `${JSON.stringify(result, null, 2)}\n`);
