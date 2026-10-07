import fs from 'node:fs';
import path from 'node:path';
import crypto from 'node:crypto';
import { gzipSync } from 'node:zlib';
const root = path.resolve(process.argv[2]);
const inputs = JSON.parse(fs.readFileSync(path.join(root, 'rider-rebuild-inputs.json')));
const manifest = JSON.parse(fs.readFileSync(path.join(root, 'load-manifest.json')));
const html = fs.readFileSync(path.join(root, 'index.html'), 'utf8');
const js = manifest.items.filter(row => row.path.endsWith('.js') && !/^\.\/assets\/(retired|audio-offline|legacy-physics|sentry-errors)-/.test(row.path));
const gzipBytes = js.reduce((sum, row) => sum + gzipSync(fs.readFileSync(path.join(root, row.path))).length, 0);
const bootScripts = [...html.matchAll(/<script>([\s\S]*?)<\/script>/g)].map(match => Buffer.byteLength(match[1]));
const catalog = JSON.parse(fs.readFileSync(path.join(root, 'model-catalog.json')));
const report = {
  accepted: false, out: root, inputs, jsGzipBytes: gzipBytes, jsBudgetBytes: 701 * 1024,
  inlineScriptBytes: bootScripts, inlineBudgetBytes: 8192,
  externalMetadataSHA256: crypto.createHash('sha256').update(JSON.stringify(catalog.privateRiderMetadata)).digest('hex'),
  actualSourceCalibrationNativeEndpoints: catalog.privateRiderMetadata.nativeRest.bones.length,
  declaredActualJointCount: Object.keys(catalog.privateRiderMetadata.specification.jointNames).length,
  limits: ['Socket centers only; glove surfaces/bar radius/phalange penetration unqualified',
    '41-knot input lean table does not guarantee contact under every force-displaced physical COM',
    'No moving art, physical device or release acceptance'],
};
fs.writeFileSync(process.argv[3], JSON.stringify(report, null, 2) + '\n');
console.log(JSON.stringify({ gzipBytes, bootScripts, externalMetadataSHA256: report.externalMetadataSHA256,
  actualJointCount: report.declaredActualJointCount }));
