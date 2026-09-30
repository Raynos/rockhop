/** Offline-only Snowline Standard authoring, nine-view board, Meshopt validation. */
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
  const r = spawnSync(command, args, { cwd: root, encoding: 'utf8', maxBuffer: 16 * 1024 * 1024 });
  if (r.status !== 0) {
    process.stderr.write(r.stdout ?? '');
    process.stderr.write(r.stderr ?? '');
    throw new Error(`${command} failed (${r.status})`);
  }
};
run('blender', ['-b', '--python-exit-code', '1', '--python', path.join(dir, 'build.py'), '--', '--out', out]);
for (const stem of ['snowline-standard', 'snowline-standard-lod']) {
  run(process.execPath, [path.join(root, 'assets/blender/hero_art_pack.mjs'),
    path.join(out, `${stem}.glb`), path.join(out, `${stem}-packed.glb`)]);
}
run('magick', ['montage', ...[
  'angle-01-gorge-wall-000.png', 'angle-02-gorge-wall-045.png', 'angle-03-gorge-wall-100.png',
  'angle-04-lift-tower-000.png', 'angle-05-lift-tower-045.png', 'angle-06-lift-tower-100.png',
  'angle-07-snowcat-000.png', 'angle-08-snowcat-045.png', 'angle-09-snowcat-100.png',
].map(f => path.join(out, f)), '-tile', '3x3', '-geometry', '640x480+4+4',
  '-background', '#142d36', path.join(out, 'nine-angle-board.jpg')]);
run('magick', ['montage', ...[
  'angle-02-gorge-wall-045.png','family-shelf-face.png','angle-05-lift-tower-045.png',
  'angle-08-snowcat-045.png','family-lift-station.png','family-summit-beacon.png',
].map(f=>path.join(out,f)),'-tile','3x2','-geometry','640x480+4+4',
  '-background','#142d36',path.join(out,'family-board.jpg')]);
const sha = file => createHash('sha256').update(fs.readFileSync(file)).digest('hex');
const models = ['snowline-standard-packed.glb', 'snowline-standard-lod-packed.glb'].map(file => {
  const s = glbStats(path.join(out, file));
  if (!s.extensionsRequired.includes('EXT_meshopt_compression')) throw new Error(`${file} is not Meshopt packed`);
  if (s.triangles > (file.includes('-lod-') ? 13000 : 20000)) throw new Error(`${file} exceeds triangle budget: ${s.triangles}`);
  if (s.bytes > (file.includes('-lod-') ? 500_000 : 1_000_000)) throw new Error(`${file} exceeds byte budget: ${s.bytes}`);
  return { file, bytes: s.bytes, sha256: s.sha256, triangles: s.triangles, draws: s.draws,
    meshes: s.meshList, images: s.imageList, extensionsRequired: s.extensionsRequired };
});
const manifest = { blender: '5.2.1 LTS', proceduralOriginal: true,
  scriptSha256: sha(path.join(dir, 'build.py')),
  masterSha256: sha(path.join(out, 'snowline-standard.source.blend')),
  boardSha256: sha(path.join(out, 'nine-angle-board.jpg')), models };
manifest.familyBoardSha256 = sha(path.join(out,'family-board.jpg'));
fs.writeFileSync(path.join(out, 'manifest.json'), JSON.stringify(manifest, null, 2) + '\n');
process.stdout.write(JSON.stringify(manifest, null, 2) + '\n');
