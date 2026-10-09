/** Source-only gate for the actual selected seven-part rider. Never accepts art.
 * node harness/rider-rebuild/selected-engine-gate.mjs --source=GLB --contract=JSON
 * --native-receipt=JSON --decoded-receipt=JSON --out=FRESH_DIRECTORY
 * The original combined04 rig is a control reference, never a wardrobe fallback.
 */
import assert from 'node:assert/strict';
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { pathToFileURL } from 'node:url';

export const SELECTED_OBJECTS = Object.freeze(['RiderBody', 'RiderHoodie', 'RiderJeans',
  'ActualSelectedGlove.L', 'ActualSelectedGlove.R', 'ActualSelectedBoot.L', 'ActualSelectedBoot.R']);
export const REFERENCE_SHA = '58677cc37aff6b22bb98144762eb5a93dfe689ac207ea0b74a214ba60538f6fc';
const REFERENCE_CONTRACT_SHA = '32d67e9031bd6865a561ba29dc6d2765ace49ad13bfb08bd61df07df85440ee4';
const CALIBRATION_SHA = '0b85504e221e33e63505a0cf18a7231ed7143f2730b4402a50994c40c4869cbc';
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
const sorted = values => [...values].sort((a, b) => {
  const left = String(a), right = String(b);
  return left < right ? -1 : left > right ? 1 : 0;
});
const exact = (a, b, why) => assert.deepEqual(a, b, why);
const require = (value, why) => assert(value, why);

/** Decode the actual binary accessors, including strides; no GLTFLoader rewrite. */
export function decodeGLB(bytes) {
  require(Buffer.isBuffer(bytes) && bytes.toString('ascii', 0, 4) === 'glTF', 'Expected GLB bytes');
  exact([bytes.readUInt32LE(4), bytes.readUInt32LE(8)], [2, bytes.length], 'GLB header');
  const size = bytes.readUInt32LE(12);
  require(bytes.readUInt32LE(16) === 0x4e4f534a, 'GLB JSON chunk');
  const document = JSON.parse(bytes.subarray(20, 20 + size).toString());
  const start = 20 + size;
  require(bytes.readUInt32LE(start + 4) === 0x004e4942, 'GLB binary chunk');
  const binary = bytes.subarray(start + 8);
  exact(binary.length, bytes.readUInt32LE(start), 'Binary chunk length');
  require(document.buffers?.length === 1 && !document.buffers[0].uri, 'Embedded buffer only');
  const types = { SCALAR: 1, VEC2: 2, VEC3: 3, VEC4: 4, MAT4: 16 };
  const formats = { 5120: ['readInt8', 1], 5121: ['readUInt8', 1], 5122: ['readInt16LE', 2],
    5123: ['readUInt16LE', 2], 5125: ['readUInt32LE', 4], 5126: ['readFloatLE', 4] };
  const accessor = index => {
    const row = document.accessors?.[index], view = document.bufferViews?.[row?.bufferView];
    require(row && view && view.buffer === 0 && !row.sparse && !row.normalized, 'Explicit nonnormalized accessor');
    const [reader, width] = formats[row.componentType] ?? [];
    const count = types[row.type];
    require(reader && count && Number.isInteger(row.count) && row.count > 0, 'Accessor shape');
    const stride = view.byteStride ?? width * count, local = row.byteOffset ?? 0;
    require(stride >= width * count && local + (row.count - 1) * stride + width * count <= view.byteLength, 'Accessor bounds');
    const base = (view.byteOffset ?? 0) + local;
    require(base + (row.count - 1) * stride + width * count <= binary.length, 'Binary accessor bounds');
    return Array.from({ length: row.count }, (_, i) => Array.from({ length: count }, (_, k) => binary[reader](base + i * stride + k * width)));
  };
  return { document, binary, accessor, sha256: sha(bytes) };
}

/** Compare only rig/control inputs. Changed face/outfit geometry is intentional. */
export function proveDriverInvariant(reference, candidate, referenceContract, contract) {
  const ref = reference.document, doc = candidate.document;
  require(ref.skins?.length === 1 && doc.skins?.length === 1, 'Exactly one shared skin');
  const describe = glb => {
    const { document: d, accessor } = glb, skin = d.skins[0], parents = new Map();
    for (const [i, node] of d.nodes.entries()) for (const child of node.children ?? []) {
      require(!parents.has(child), 'Joint has two parents'); parents.set(child, i);
    }
    const transform = node => node.matrix ? { matrix: node.matrix } : { translation: node.translation ?? [0, 0, 0],
      rotation: node.rotation ?? [0, 0, 0, 1], scale: node.scale ?? [1, 1, 1] };
    const inverse = accessor(skin.inverseBindMatrices);
    require(skin.joints.length === 75 && inverse.length === 75, 'Exactly 75 joints and inverse binds');
    const rows = skin.joints.map((index, slot) => {
      const node = d.nodes[index], ancestors = [], seen = new Set([index]);
      for (let p = parents.get(index); p !== undefined; p = parents.get(p)) {
        require(!seen.has(p), 'Cyclic hierarchy'); seen.add(p);
        ancestors.push({ name: d.nodes[p].name, transform: transform(d.nodes[p]) });
      }
      return { name: node.name, transform: transform(node), ancestors, inverse: inverse[slot] };
    }).sort((a, b) => a.name < b.name ? -1 : a.name > b.name ? 1 : 0);
    require(new Set(rows.map(row => row.name)).size === 75, 'Unique named joints');
    return { rows, transform };
  };
  const old = describe(reference), current = describe(candidate);
  exact(current.rows, old.rows, 'Every source rest transform, ancestor and inverse bind must remain exact');
  for (const key of ['units', 'frame', 'jointNames', 'roles', 'hands']) {
    exact(contract.specification[key], referenceContract.specification[key], `Driver semantic input changed: ${key}`);
  }
  exact(contract.nativeRest, referenceContract.nativeRest, 'Native endpoint/mass/socket geometry changed; recalibrate explicitly');
  exact(contract.driver, referenceContract.driver, 'Driver axes, limits or placement changed; recalibrate explicitly');
  const oldBody = ref.nodes.find(node => node.name === 'RiderBody' && node.mesh !== undefined);
  require(oldBody, 'Reference body bind object');
  for (const node of doc.nodes.filter(node => node.mesh !== undefined)) {
    exact(current.transform(node), old.transform(oldBody), `Object bind transform changed: ${node.name}`);
  }
  return { jointCount: 75, allRestHierarchyAndInverseBindsExact: true,
    palmAndSoleFramesExact: true, nativeMassEndpointsExact: true, driverSemanticInputsExact: true,
    measuredRigSignatureSHA256: sha(JSON.stringify(current.rows)),
    geometryScope: 'Unchanged joint centres, source native endpoints and socket frames; replacement face and garments are deliberately not required to match rejected geometry.' };
}

// Python native receipts serialize exact unit weights as 1.0. All other weights
// here are dyadic float32 >= 1678/2^24, so neither encoder uses exponential form.
export function hashNamedFields(rows) {
  return sha('[' + rows.map(row => '[' + row.map(([name, weight]) => '[' + JSON.stringify(name) + ','
    + (Number.isInteger(weight) ? weight.toFixed(1) : String(weight)) + ']').join(',') + ']').join(',') + ']');
}

/** Recompute per-current-native-ID fields and body identity/position byte arrays. */
export function inspectSelectedSource(glb, contract, native, decoded, nativeReceiptSHA) {
  const { document: doc, binary, accessor } = glb;
  exact(contract.glbSHA256, glb.sha256, 'Contract binds exact GLB');
  exact(decoded.glbSHA256, glb.sha256, 'Decoded receipt binds exact GLB');
  exact(decoded.nativeReceiptSHA256, nativeReceiptSHA, 'Decoded receipt binds exact native receipt');
  exact(sorted(native.authorObjects), sorted(SELECTED_OBJECTS), 'Complete real selected native inventory required');
  exact(sorted(Object.keys(contract.specification.meshNames)), sorted(SELECTED_OBJECTS), 'Complete explicit author roles required');
  exact(sorted(Object.values(contract.specification.meshNames)), sorted(SELECTED_OBJECTS), 'No substitute author objects');
  for (const flag of ['nativeIDIsCurrentInventory', 'nonSoleRestExactlyEqualToFrozen',
    'protectedLikedFacePointIDsExactlyRetained', 'allPositiveSourcePointIDsUniqueAndAtOriginalCoordinates',
    'canonicalOperatorMatchesPreFieldsExactly', 'skinFinishGeometryAndSourceIDsByteIdentical']) require(native[flag] === true, `Native source guard: ${flag}`);
  require(native.jointCount === 75 && decoded.jointCount === 75 && doc.skins?.length === 1, 'Single complete 75-joint source');
  const joints = doc.skins[0].joints.map(index => doc.nodes[index].name);
  require(joints.length === 75 && new Set(joints).size === 75, 'Unique full joint palette');
  exact(sorted(joints), sorted(Object.values(contract.specification.jointNames)), 'Author joint mapping');
  const nodes = doc.nodes.filter(node => node.mesh !== undefined);
  exact(sorted(nodes.map(node => node.name)), sorted(SELECTED_OBJECTS), 'Only seven selected skinned author objects');
  const objects = {}, fieldHashes = {}, bodyIDs = new Map();
  let triangles = 0, maxWeightSumError = 0;
  for (const node of nodes) {
    require(node.skin === 0, `Unskinned selected object ${node.name}`);
    const fields = new Map(), materials = [], rows = [];
    for (const primitive of doc.meshes[node.mesh].primitives) {
      require((primitive.mode ?? 4) === 4 && primitive.indices !== undefined, 'Indexed triangle primitive required');
      const attrs = primitive.attributes;
      for (const key of ['POSITION', 'NORMAL', 'TEXCOORD_0', 'JOINTS_0', 'WEIGHTS_0', '_NATIVE_ID']) require(attrs[key] !== undefined, `${node.name}: missing ${key}`);
      require(attrs.JOINTS_1 === undefined && attrs.WEIGHTS_1 === undefined, 'Exactly author FOUR fields');
      const positions = accessor(attrs.POSITION), normals = accessor(attrs.NORMAL), uv = accessor(attrs.TEXCOORD_0);
      const slots = accessor(attrs.JOINTS_0), weights = accessor(attrs.WEIGHTS_0), ids = accessor(attrs._NATIVE_ID);
      for (const array of [normals, uv, slots, weights, ids]) exact(array.length, positions.length, 'Primitive attribute count');
      const indices = accessor(primitive.indices).map(row => row[0]);
      require(indices.length % 3 === 0 && indices.length > 0 && indices.every(i => Number.isInteger(i) && i >= 0 && i < positions.length), 'Nonempty valid indexed surface');
      const sourceIDs = node.name === 'RiderBody' ? accessor(attrs._SOURCE_VERTEX_ID) : null;
      if (sourceIDs) exact(sourceIDs.length, positions.length, 'Body source ID count');
      for (let i = 0; i < positions.length; i++) {
        const id = ids[i][0];
        require(Number.isInteger(id) && id >= 0 && slots[i].length === 4 && weights[i].length === 4, 'Current native identity/FOUR shape');
        require([...positions[i], ...normals[i], ...uv[i], ...weights[i]].every(Number.isFinite), 'Finite skin/appearance attributes');
        require(slots[i].every(j => Number.isInteger(j) && j >= 0 && j < 75), 'Joint slot range');
        const names = slots[i].map((slot, k) => [joints[slot], weights[i][k]]).filter(row => row[1] !== 0)
          .sort((a, b) => a[0] < b[0] ? -1 : a[0] > b[0] ? 1 : 0);
        require(names.length > 0 && new Set(names.map(row => row[0])).size === names.length
          && names.every(([, w]) => w > .0001 && Number.isInteger(w * 2 ** 24)), 'Canonical positive named dyadic fields');
        const error = Math.abs(weights[i].reduce((sum, w) => sum + w, 0) - 1);
        maxWeightSumError = Math.max(maxWeightSumError, error);
        require(error < 2e-7 && weights[i].every(w => w >= 0), 'Unchanged normalization guard');
        if (fields.has(id)) exact(names, fields.get(id), 'Split primitive changed named native field');
        fields.set(id, names);
        if (sourceIDs) {
          const sourceID = sourceIDs[i][0]; require(Number.isInteger(sourceID), 'Integer source identity');
          const row = { sourceID, position: positions[i] };
          if (bodyIDs.has(id)) exact(row, bodyIDs.get(id), 'Split body vertex changed source identity/position');
          bodyIDs.set(id, row);
        }
      }
      const material = doc.materials[primitive.material];
      require(material?.name, 'Named original material');
      if (node.name !== 'RiderBody') require(material.pbrMetallicRoughness?.baseColorTexture, `Missing selected garment PBR: ${node.name}`);
      materials.push(material.name); triangles += indices.length / 3;
      rows.push({ vertices: positions.length, triangles: indices.length / 3, material: material.name, attributes: sorted(Object.keys(attrs)) });
    }
    exact(sorted(new Set(materials)), sorted(native.materialsByAuthorObject[node.name]), 'All native material primitives preserved');
    exact(sorted(fields.keys()).map(Number).sort((a, b) => a - b), Array.from({ length: fields.size }, (_, i) => i), 'Dense current native IDs');
    const hash = hashNamedFields(Array.from({ length: fields.size }, (_, i) => fields.get(i)));
    exact(hash, native.canonicalNamedFieldsByNativeIDSHA256[node.name], 'GPU/native named FOUR byte identity');
    exact(hash, decoded.canonicalNamedFieldSHA256ByObject[node.name], 'Independent decoded field identity');
    fieldHashes[node.name] = hash; objects[node.name] = rows;
    exact(rows, decoded.authorObjectPrimitives[node.name], 'Independent primitive receipt identity');
  }
  require(bodyIDs.size > 10582, 'Actual joined head/body current inventory');
  const identities = Buffer.alloc(bodyIDs.size * 4), positions = Buffer.alloc(bodyIDs.size * 12);
  for (let i = 0; i < bodyIDs.size; i++) {
    const row = bodyIDs.get(i); require(row, 'Dense joined body IDs'); identities.writeInt32LE(row.sourceID, i * 4);
    row.position.forEach((value, axis) => positions.writeFloatLE(value, i * 12 + axis * 4));
  }
  require([...bodyIDs.values()].some(row => row.sourceID === -1)
    && [...bodyIDs.values()].some(row => row.sourceID >= 1000000), 'Derived seams and protected liked-face identity required');
  exact(sha(identities), native.bodySourceIDByNativeIDSHA256, 'Body source identity bytes');
  exact(sha(positions), native.bodyGLTFPositionByNativeIDSHA256, 'Body position bytes');
  const images = (doc.images ?? []).map(image => {
    const view = doc.bufferViews[image.bufferView];
    require(view && view.buffer === 0 && !image.uri, 'Original PBR images embedded');
    const bytes = binary.subarray(view.byteOffset ?? 0, (view.byteOffset ?? 0) + view.byteLength);
    require(bytes.length === view.byteLength && ['image/png', 'image/jpeg'].includes(image.mimeType), 'Image format/bounds');
    require(image.mimeType === 'image/png' ? bytes.subarray(0, 8).equals(Buffer.from([137, 80, 78, 71, 13, 10, 26, 10]))
      : bytes[0] === 255 && bytes[1] === 216, 'Embedded image signature');
    return { name: image.name ?? null, mimeType: image.mimeType, bytes: bytes.length, sha256: sha(bytes) };
  });
  require(images.length > 0, 'Original selected maps required'); exact(images, decoded.embeddedPBRImages, 'Embedded original image byte receipts');
  return { authorObjects: SELECTED_OBJECTS, authorObjectPrimitives: objects, triangles, jointCount: 75,
    maxWeightNormalizationError: maxWeightSumError, canonicalNamedFieldSHA256ByObject: fieldHashes,
    sourceAndCurrentNativeIDsAndFOURFieldsExact: true, originalEmbeddedPBRImages: images };
}

export function deriveCalibration(referenceCalibration, referenceSHA, candidateSHA, invariant) {
  exact(referenceCalibration.sourceSHA256, referenceSHA, 'Original calibration binds original source');
  require(candidateSHA !== referenceSHA && /^[0-9a-f]{64}$/.test(candidateSHA), 'New selected source SHA required');
  require(invariant.allRestHierarchyAndInverseBindsExact && invariant.nativeMassEndpointsExact
    && invariant.palmAndSoleFramesExact && invariant.driverSemanticInputsExact, 'Proof precedes calibration transfer');
  return { accepted: false, sourceSHA256: candidateSHA, driver: structuredClone(referenceCalibration.driver),
    selection: referenceCalibration.selection, provenance: { method: 'Exact measured rig/control-input preservation; explicit new source identity',
      referenceSourceSHA256: referenceSHA, referenceCalibrationSHA256: CALIBRATION_SHA,
      measuredRigSignatureSHA256: invariant.measuredRigSignatureSHA256 },
    limits: ['Rig-preserved CPU driver parameters only; new garment/head deformation, finite glove/bar contact, actual played art and phone performance remain unaccepted.'] };
}

async function main() {
  const arg = name => process.argv.find(value => value.startsWith(`--${name}=`))?.slice(name.length + 3);
  for (const name of ['source', 'contract', 'native-receipt', 'decoded-receipt', 'out']) require(arg(name), `Missing --${name}`);
  const out = path.resolve(arg('out')); require(!fs.existsSync(out), 'Use a fresh private receipt directory');
  require(out.startsWith(path.resolve('harness/out/rider-rebuild') + path.sep), 'Private harness output only');
  const files = Object.fromEntries(['source', 'contract', 'native-receipt', 'decoded-receipt'].map(name => [name, path.resolve(arg(name))]));
  const buffers = Object.fromEntries(Object.entries(files).map(([name, file]) => [name, fs.readFileSync(file)]));
  const contract = JSON.parse(buffers.contract), native = JSON.parse(buffers['native-receipt']), decoded = JSON.parse(buffers['decoded-receipt']);
  const base = path.resolve('harness/out/rider-rebuild/construction01/combined04');
  const oldBytes = fs.readFileSync(path.join(base, 'rider.glb')), oldContractBytes = fs.readFileSync(path.join(base, 'rider-contract.json'));
  exact(sha(oldBytes), REFERENCE_SHA, 'Frozen original rig source'); exact(sha(oldContractBytes), REFERENCE_CONTRACT_SHA, 'Frozen original contract');
  const calibrationBytes = fs.readFileSync('docs/evidence/rider-rebuild/runtime02/combined04-adaptive20-pose.json');
  exact(sha(calibrationBytes), CALIBRATION_SHA, 'Frozen actual-state adaptive20 calibration');
  exact(sha(fs.readFileSync(native.native.path)), native.native.sha256, 'Native receipt still binds exact authored .blend');
  const candidate = decodeGLB(buffers.source), reference = decodeGLB(oldBytes);
  const transport = inspectSelectedSource(candidate, contract, native, decoded, sha(buffers['native-receipt']));
  const invariant = proveDriverInvariant(reference, candidate, JSON.parse(oldContractBytes), contract);
  const calibration = deriveCalibration(JSON.parse(calibrationBytes), REFERENCE_SHA, candidate.sha256, invariant);
  const report = { accepted: false, kind: 'Complete selected-source engine intake and explicit calibration provenance',
    sourceSHA256: candidate.sha256, sourceBytes: buffers.source.length, invariant, transport,
    inputs: Object.fromEntries(Object.entries(files).map(([name, file]) => [name, { path: file, sha256: sha(buffers[name]) }])),
    gateSHA256: sha(fs.readFileSync(new URL(import.meta.url))),
    referencePins: { sourceSHA256: REFERENCE_SHA, contractSHA256: REFERENCE_CONTRACT_SHA, calibrationSHA256: CALIBRATION_SHA },
    driverSourcePins: ['private-rider.mjs', 'anthropometric-inverse.mjs', 'new-humanoid-contract.mjs'].map(name => ({ name, sha256: sha(fs.readFileSync(new URL(name, import.meta.url))) })),
    runtimeTexturePolicy: { albedoMax: 1024, dataMapMax: 512, wholeSceneBudgetBytes: 96 * 1024 * 1024,
      originalEmbeddedMapsPreserved: true, requiredSourceAliasPolicy: 'All outfit/LOD slots share one parsed source document', actualGPUAllocationMeasured: false },
    limits: ['No browser/native execution or visual acceptance. Parent must build, replay, play and judge the complete actual outfit.',
      '96 MiB remains a whole-scene gate; map policy alone is not a measured GPU or transient decode-memory pass.'] };
  for (const [name, file] of Object.entries(files)) exact(sha(fs.readFileSync(file)), sha(buffers[name]), 'Source changed during intake');
  const reportBytes = JSON.stringify(report, null, 2) + '\n';
  calibration.provenance.engineIntakeReceiptSHA256 = sha(reportBytes);
  fs.mkdirSync(out, { recursive: true });
  fs.writeFileSync(path.join(out, 'selected-engine-intake.json'), reportBytes);
  fs.writeFileSync(path.join(out, 'selected-adaptive20-pose.json'), JSON.stringify(calibration, null, 2) + '\n');
  console.log(JSON.stringify({ accepted: false, out, sourceSHA256: candidate.sha256, authorObjects: transport.authorObjects, calibrationTransferredAfterExactProof: true }));
}
if (process.argv[1] && pathToFileURL(path.resolve(process.argv[1])).href === import.meta.url) await main();
