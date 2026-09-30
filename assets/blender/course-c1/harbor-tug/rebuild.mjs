/** Rebuild and verify the C1 tug without changing runtime source or assets. */
import { spawnSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import fs from 'node:fs';
import path from 'node:path';
import { fileURLToPath } from 'node:url';
import { glbStats } from '../../glb_stats.mjs';

const dir = path.dirname(fileURLToPath(import.meta.url));
const root = path.resolve(dir, '../../../..');
const out = path.join(dir, 'out');
fs.mkdirSync(out, { recursive: true });
const run = (command, args) => {
  const result = spawnSync(command, args, { cwd: root, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 });
  if (result.status !== 0) {
    process.stderr.write(result.stdout ?? '');
    process.stderr.write(result.stderr ?? '');
    throw new Error(`${command} failed (${result.status})`);
  }
};
const script = path.join(dir, 'build.py');
run('blender', ['-b', '--python-exit-code', '1', '--python', script, '--', '--out', out]);
for (const lod of [false, true]) {
  const stem = lod ? 'harbor-tug-lod' : 'harbor-tug';
  run(process.execPath, [path.join(root, 'assets/blender/hero_art_pack.mjs'),
    path.join(out, `${stem}.glb`), path.join(out, `${stem}-packed.glb`)]);
}
run('magick', ['montage', ...[0, 40, 80, 120, 160, 200, 240, 280, 320].map((a, i) => path.join(out, `angle-${String(i + 1).padStart(2, '0')}-${String(a).padStart(3, '0')}.png`)),
  '-tile', '3x3', '-geometry', '640x480+4+4', '-background', '#152d32', path.join(out, 'nine-angle-board.jpg')]);
const sha = file => createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const models = ['harbor-tug-packed.glb', 'harbor-tug-lod-packed.glb'].map(file => {
  const { bytes, sha256, triangles, draws, meshes, materials, images, maxTexture, extensionsRequired } = glbStats(path.join(out, file));
  if (draws > 5 || triangles > (file.includes('-lod-') ? 8000 : 15000) || !extensionsRequired.includes('EXT_meshopt_compression')) {
    throw new Error(`asset budget failed: ${file}`);
  }
  return { file, bytes, sha256, triangles, draws, meshes, materials, images, maxTexture };
});
const manifest = { blender: '5.2.1 LTS', scriptSha256: sha(script), masterSha256: sha(path.join(out, 'harbor-tug.source.blend')),
  boardSha256: sha(path.join(out, 'nine-angle-board.jpg')), models };
fs.writeFileSync(path.join(out, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
process.stdout.write(JSON.stringify(manifest, null, 2) + '\n');
