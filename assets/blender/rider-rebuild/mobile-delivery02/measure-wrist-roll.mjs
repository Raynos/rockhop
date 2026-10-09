/** Diagnose actual captured wrist axial rotation using exact delivered native rest. No pose writes. */
import fs from 'node:fs';
import assert from 'node:assert/strict';
import { Quaternion, Vector3 } from 'three';
const [source, played, output] = process.argv.slice(2);
assert(source && played && output);
const descriptor = fs.openSync(source, 'r'), header = Buffer.alloc(20);
fs.readSync(descriptor, header, 0, 20, 0);
assert.equal(header.toString('ascii', 0, 4), 'glTF');
const metadata = Buffer.alloc(header.readUInt32LE(12));
fs.readSync(descriptor, metadata, 0, metadata.length, 20); fs.closeSync(descriptor);
const doc = JSON.parse(metadata.toString()), report = JSON.parse(fs.readFileSync(played));
assert.equal(report.source.sha256, '585ae314e2b354768a1385e5a85828c142d542b47f8d9fe948f46c7478c112ef');
const hands = {};
for (const side of ['L', 'R']) {
  const id = 'DEF-hand.' + side, node = doc.nodes.find(node => node.name === id);
  const rest = new Quaternion().fromArray(node.rotation ?? [0, 0, 0, 1]);
  const axis = new Vector3().fromArray(node.translation).normalize();
  const samples = report.played.motionSamples.map(row => {
    const hand = row.joints.find(joint => joint.id === id);
    const delta = new Quaternion().fromArray(hand.quaternion).multiply(rest.clone().invert()).normalize();
    const signed = 2 * Math.atan2(delta.x * axis.x + delta.y * axis.y + delta.z * axis.z, delta.w);
    const axialDegrees = Math.atan2(Math.sin(signed), Math.cos(signed)) * 180 / Math.PI;
    return { tick: row.tick, phase: row.phase, axialDegrees };
  });
  hands[side] = { sourceLocalQuaternion: rest.toArray(), parentShaftAxisLocal: axis.toArray(),
    minimumDegrees: Math.min(...samples.map(row => row.axialDegrees)),
    maximumDegrees: Math.max(...samples.map(row => row.axialDegrees)), samples };
}
fs.writeFileSync(output, JSON.stringify({ accepted: false, source: report.source, profileSHA256: report.requestedGripProfileSHA256,
  method: 'Captured native wrist local quaternion times exact GLB rest inverse; swing/twist axial component about native parent-to-wrist shaft.',
  limits: 'Diagnostic only. Cuff source projection and anatomical forearm pronation correction require independent construction and played qualification.', hands }, null, 2) + '\n');
console.log(JSON.stringify(Object.fromEntries(Object.entries(hands).map(([side, hand]) => [side, [hand.minimumDegrees, hand.maximumDegrees]]))));
