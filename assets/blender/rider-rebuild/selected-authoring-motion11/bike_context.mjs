/** Small offline bike context: exact saddle triangles and editable contact targets.
 * node bike_context.mjs FRESH_OUTPUT.json. Does not load a rider or solve a pose.
 */
import fs from 'node:fs';
import path from 'node:path';
import assert from 'node:assert/strict';
import { Matrix4, Quaternion, Vector3, Triangle } from 'three';
import { load, mesh, pinned, sha } from '../selected-ankle-contact02/surface.mjs';

const here = path.dirname(new URL(import.meta.url).pathname);
const configPath = path.join(here, 'bike-context-source.json');
const config = JSON.parse(fs.readFileSync(configPath));
assert.equal(config.accepted, false);
for (const pin of Object.values(config.pins)) pinned(pin);
const read = name => JSON.parse(pinned(config.pins[name]));
const contract = read('contract'), calibration = read('calibration'), measurement = read('measurement');
const out = process.argv[2]; assert(out && !fs.existsSync(out), 'Provide fresh output');
const M = () => new Matrix4();
const nativeRest = Object.fromEntries(contract.nativeRest.bones.map(b => [b.name, M().set(...b.matrix.flat())]));
const nativeToGLTF = M().set(1, 0, 0, 0, 0, 0, 1, 0, 0, -1, 0, 0, 0, 0, 0, 1);
const nativeToBike = M().makeRotationFromQuaternion(new Quaternion().fromArray(contract.driver.assetToBikeQuaternionXYZW)).multiply(nativeToGLTF);
const bikeToNative = nativeToBike.clone().invert();
const frame = (point, rotation) => M().compose(new Vector3().fromArray(point), new Quaternion().fromArray(rotation), new Vector3(1, 1, 1));
const rowMajor = m => Array.from({ length: 4 }, (_, r) => Array.from({ length: 4 }, (_, c) => m.elements[c * 4 + r]));
const bikes = [];
for (const item of measurement.bikes) {
  assert(calibration.bikes.some(p => JSON.stringify(p) === JSON.stringify(item.bike)));
  const raw = await load(item.bike), origin = raw.node('attach_frame_origin').point;
  const bodywork = mesh(raw, item.saddleSource.node, M().makeTranslation(-origin.x, -origin.y, -origin.z));
  const saddle = item.saddleSource.sourceTriangleOrdinals.map(ordinal => {
    const sourceVertexRows = [0, 1, 2].map(k => bodywork.indices.get(ordinal * 3 + k));
    const points = sourceVertexRows.map(id => bodywork.point(id));
    return { sourceTriangleOrdinal: ordinal, sourceVertexRows, pointsBike: points.map(p => p.toArray()),
      pointsNative: points.map(p => p.clone().applyMatrix4(bikeToNative).toArray()),
      upward: new Triangle(...points).getNormal(new Vector3()).y > 1e-9 };
  });
  assert.equal(saddle.length, 116); assert.equal(saddle.filter(t => t.upward).length, 48);
  const saved = read(item.name + 'ContactReceipt');
  assert.deepEqual(saved.bike, item.bike); assert.deepEqual(saved.frameOriginFile, origin.toArray());
  const controls = {}, contactFrames = {};
  for (const [side, suffix] of [['left', 'L'], ['right', 'R']]) {
    const palm = saved.frames.palms.find(p => p.side === side); assert(palm);
    const palmBike = frame(palm.position, palm.rotationXYZW);
    controls['CTRL-palm.' + suffix] = rowMajor(bikeToNative.clone().multiply(palmBike));
    assert.deepEqual(saved.frames.soles[side], calibration.driver.selectedPegSurfaceBike[side]);
    const bootBike = frame(calibration.driver.selectedPegSurfaceBike[side], calibration.driver.soleQuaternionBike[side]);
    // The measured boot contact frame is NOT the anatomical SoleSocket frame.
    const contactInFoot = M().fromArray(calibration.driver.selectedSoleInFoot[side]);
    const footNative = bikeToNative.clone().multiply(bootBike).multiply(contactInFoot.clone().invert());
    const socketInFoot = nativeRest['DEF-foot.' + suffix].clone().invert().multiply(nativeRest['SoleSocket.' + suffix]);
    const soleControl = footNative.clone().multiply(socketInFoot);
    controls['CTRL-sole.' + suffix] = rowMajor(soleControl);
    const recovered = nativeToBike.clone().multiply(soleControl).multiply(socketInFoot.clone().invert()).multiply(contactInFoot);
    assert(Math.max(...recovered.elements.map((v, i) => Math.abs(v - bootBike.elements[i]))) < 1e-12);
    contactFrames[side] = { palmBike: rowMajor(palmBike), bootContactBike: rowMajor(bootBike),
      measuredContactInFoot: rowMajor(contactInFoot), anatomicalSocketInFoot: rowMajor(socketInFoot) };
  }
  bikes.push({ name: item.name, bike: item.bike, frameOriginFile: origin.toArray(), saddleSource: item.saddleSource,
    saddle, nativeControlMatrices: controls, contactFrames });
}
const result = { accepted: false, status: 'EDITABLE_BIKE_CONTEXT_CONTACT_AND_POSE_UNACCEPTED',
  source: { path: path.relative(process.cwd(), configPath), sha256: sha(fs.readFileSync(configPath)) }, pins: config.pins,
  matrixStorage: 'row-major 4x4', nativeToBike: rowMajor(nativeToBike), bikeToNative: rowMajor(bikeToNative), bikes,
  limits: ['No pelvis, spine, knee, elbow or rejected author04 fitted pose is imported.',
    'Palm and finite boot contact frames are existing unaccepted targets, not proven surface bearing or motion.',
    'Saddle triangles are exact pinned bike geometry in native rig coordinates. Fully dressed posed review remains mandatory.'] };
fs.writeFileSync(out, JSON.stringify(result, null, 2) + '\n');
console.log(JSON.stringify({ out, bikes: bikes.map(b => ({ name: b.name, saddleTriangles: b.saddle.length, controls: Object.keys(b.nativeControlMatrices) })) }));
