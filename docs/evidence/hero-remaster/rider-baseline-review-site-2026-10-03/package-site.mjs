import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import crypto from 'node:crypto';
import assert from 'node:assert/strict';

const recipe = path.dirname(fileURLToPath(import.meta.url));
const repo = path.resolve(recipe, '../../../..');
const checkout = path.resolve(process.argv[2] ||
  path.join(repo, 'harness/out/rider-baseline-review-site'));
assert(checkout.startsWith(path.join(repo, 'harness/out') + path.sep));
const output = path.join(checkout, 'dist');
fs.mkdirSync(path.join(output, 'media'), { recursive: true });
fs.mkdirSync(path.join(checkout, '.openai'), { recursive: true });
for (const file of ['index.html', 'feedback-tools.js']) {
  fs.copyFileSync(path.join(recipe, file), path.join(output, file));
}
const sources = JSON.parse(fs.readFileSync(path.join(recipe, 'media.json')));
const pins = sources.map(({ source, destination }) => {
  const from = path.resolve(repo, source);
  const to = path.resolve(output, destination);
  assert(from.startsWith(repo + path.sep) && to.startsWith(output + path.sep));
  const bytes = fs.readFileSync(from);
  fs.writeFileSync(to, bytes);
  return { source, destination, bytes: bytes.length,
    sha256: crypto.createHash('sha256').update(bytes).digest('hex') };
});
const manifestPath = path.join(checkout, '.openai/hosting.json');
const existing = fs.existsSync(manifestPath) ?
  JSON.parse(fs.readFileSync(manifestPath)) : {};
fs.writeFileSync(manifestPath, JSON.stringify({ ...existing,
  static: { directory: 'dist' } }, null, 2) + '\n');
fs.writeFileSync(path.join(recipe, 'asset-pins.json'), JSON.stringify(pins, null, 2) + '\n');
console.log(JSON.stringify({ checkout, assets: pins.length,
  bytes: pins.reduce((sum, pin) => sum + pin.bytes, 0) }));
