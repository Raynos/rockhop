/** Small read-only coverage proof: GLB JSON/native-ID accessor ranges and NPZ.
 * No Blender, full GLB/native reads, geometry writes, or acceptance judgment.
 */
import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';
import { fileURLToPath } from 'node:url';
import { unzipSync } from 'three/addons/libs/fflate.module.js';

const ROOT = fileURLToPath(new URL('../../../../', import.meta.url));
const BASE = 'harness/out/rider-rebuild/selected-seated-anatomical09/';
const sha = bytes => crypto.createHash('sha256').update(bytes).digest('hex');
export function nativeTriangleIDs(archive, name) {
  const b = Buffer.from(archive[name+'_triangles.npy'] ?? []);
  assert.equal(b[0], 0x93); assert.equal(b.toString('ascii', 1, 6), 'NUMPY'); assert.equal(b[6], 1);
  const offset = 10+b.readUInt16LE(8), header = b.toString('ascii', 10, offset);
  assert(header.includes("'descr': '<i4'") && header.includes("'fortran_order': False"));
  const shape = /'shape': \(([^)]*)\)/.exec(header)[1].split(',').map(s => s.trim()).filter(Boolean).map(Number);
  assert(shape.length === 2 && shape[1] === 3 && shape[0] > 0); assert.equal(b.length-offset, shape[0]*12);
  const ids = new Set(); for (let i = offset; i < b.length; i += 4) { const id = b.readInt32LE(i); assert(id >= 0); ids.add(id); }
  return {ids, triangles: shape[0], arraySHA256: sha(b)};
}
export function verifyVolumeCoverage(name, primitiveIDs, native, movedRows) {
  const exported = new Set(primitiveIDs.flat());
  assert(exported.size && [...exported].every(id => Number.isInteger(id) && id >= 0));
  const missingReferenced = [...native.ids].filter(id => !exported.has(id));
  const extraExported = [...exported].filter(id => !native.ids.has(id));
  assert.equal(missingReferenced.length, 0, `${name}: native face-referenced IDs were lost from the pinned original export`);
  assert.equal(extraExported.length, 0, `${name}: pinned original export has IDs absent from the frozen native faces`);
  const absentMoved = movedRows.filter(row => !exported.has(row.nativeID)).map(row => row.nativeID).sort((a,b) => a-b);
  assert.equal(new Set(movedRows.map(row => row.nativeID)).size, movedRows.length);
  if (name !== 'RiderBody') assert.equal(absentMoved.length, 0, `${name}: moved IDs absent from the original export remain forbidden`);
  assert(absentMoved.every(id => !native.ids.has(id)), 'Never waive omission of a native face-referenced moved ID');
  const canonical = [...exported].sort((a,b) => a-b);
  return {object: name, primitiveRows: primitiveIDs.map(ids => ids.length), exportedNativeIDs: exported.size,
    exportedNativeIDSetSHA256: sha(JSON.stringify(canonical)), originalPrimitiveIDRowsSHA256: primitiveIDs.map(ids => sha(JSON.stringify(ids))),
    frozenNativeTriangles: native.triangles, nativeTriangleArraySHA256: native.arraySHA256,
    nativeFaceReferencedIDs: native.ids.size, originalExportCoversEveryNativeFaceReferencedID: true,
    movedNativeIDs: movedRows.length, movedExportedNativeIDs: movedRows.length-absentMoved.length,
    movedIDsAbsentFromOriginalExport: absentMoved, absentMovedIDsReferencedByNativeFaces: 0,
    omissionReason: absentMoved.length ? 'Pre-existing unused vertices retained by original FACES_ONLY outfit Body mask; the pinned original export contains precisely the face-referenced native IDs. This transport adds no mask or ID loss.' : 'No moved native IDs omitted.',
    fullNativeBodyJeansContacts: 'UNMEASURED; full native contact/crossing qualification remains separate, including vertices absent from the render export. RiderBody__FullAnatomyReference remains unchanged and has no companion sculpt; unused render-body deltas do not prove complete wearer enclosure.'};
}
function readIDRows(filename) {
  const fd = fs.openSync(filename, 'r');
  try {
    const read = (offset, count) => { const b = Buffer.alloc(count); assert.equal(fs.readSync(fd, b, 0, count, offset), count); return b; };
    const h = read(0,20); assert.equal(h.toString('ascii',0,4),'glTF'); const length = h.readUInt32LE(12), json = read(20,length), doc = JSON.parse(json);
    const result = {};
    for (const name of ['RiderBody','RiderJeans']) {
      const node = doc.nodes.find(n => n.name === name); assert(node);
      result[name] = doc.meshes[node.mesh].primitives.map(p => {
        const a = doc.accessors[p.attributes._NATIVE_ID], v = doc.bufferViews[a.bufferView];
        assert(a.type === 'SCALAR' && a.componentType === 5126 && !a.sparse && !a.normalized && !v.extensions);
        const stride = v.byteStride ?? 4, offset = a.byteOffset ?? 0, count = (a.count-1)*stride+4;
        assert(offset+count <= v.byteLength); const raw = read(28+length+(v.byteOffset ?? 0)+offset,count);
        return Array.from({length:a.count},(_,i) => raw.readFloatLE(i*stride));
      });
    }
    return {rows: result, jsonSHA256: sha(json)};
  } finally { fs.closeSync(fd); }
}
function main() {
  const manifest = JSON.parse(fs.readFileSync(path.join(ROOT,'assets/blender/rider-rebuild/selected-seated-anatomical09/volume03.input.json')));
  const readPinned = name => { const p = manifest.pins[name], b = fs.readFileSync(path.join(ROOT,p.path)); assert.equal(sha(b),p.sha256); return b; };
  const shape = JSON.parse(readPinned('shapeKey')), nativeReceipt = JSON.parse(readPinned('nativeReceipt'));
  assert.equal(nativeReceipt.basisWeightsRestUVMapsExact,true);
  const archive = unzipSync(readPinned('posedSurfaces'));
  const original = readIDRows(path.join(ROOT,'harness/out/rider-rebuild/selected-complete-engine01/engine05/rider.glb'));
  const current = readIDRows(path.join(ROOT,BASE+'transport02/rider.glb'));
  assert.deepEqual(original.rows,current.rows,'Original engine05 and transport02 primitive native-ID rows must be exact');
  const objects = ['RiderBody','RiderJeans'].map(name => verifyVolumeCoverage(name,current.rows[name],nativeTriangleIDs(archive,name),shape.deltas[name]));
  const report = {accepted:false,status:'PREEXISTING_UNUSED_BODY_VERTEX_OMISSION_PROVEN',sourcePins:manifest.pins,
    recipeSHA256:sha(fs.readFileSync(fileURLToPath(import.meta.url))),originalEngine05AndTransport02PrimitiveIDRowsExact:true,
    originalEngine05JSONSHA256:original.jsonSHA256,transport02JSONSHA256:current.jsonSHA256,objects,
    proofScope:'Reads original GLB JSON and native-ID accessor ranges only; full large-file SHA pins come from parent actual receipts and are rechecked by guarded transport. Native triangles and shape arrays independently SHA-checked here.',
    maskRecipe:{path:'assets/blender/rider-rebuild/outfit-body-mask01/apply.py',sha256:sha(fs.readFileSync(path.join(ROOT,'assets/blender/rider-rebuild/outfit-body-mask01/apply.py'))),operation:'bmesh.ops.delete(..., context="FACES_ONLY"); original vertex indices including unused covered vertices retained'},
    limits:['No new mask or geometry removal is authorized. Every original exported ID row, primitive and binary byte remains protected.', 'No full native collision/contact or moving appearance acceptance.']};
  const filename = path.join(ROOT,'docs/evidence/rider-rebuild/selected-seated-anatomical09/volume-coverage03.json');
  fs.writeFileSync(filename,JSON.stringify(report,null,2)+'\n',{flag:'wx'});
  console.log(JSON.stringify({report:path.relative(ROOT,filename),objects:objects.map(({movedIDsAbsentFromOriginalExport,...row})=>({...row,absentMovedCount:movedIDsAbsentFromOriginalExport.length}))}));
}
if (process.argv[1] && path.resolve(process.argv[1]) === fileURLToPath(import.meta.url)) main();
