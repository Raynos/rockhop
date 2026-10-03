import { readFile, writeFile } from 'node:fs/promises';
import { generateFixture } from './fixture';
import { readGlbBinding } from './read-glb';
import type { BindingManifest } from './read-glb';

const args = process.argv.slice(2), flags = new Map<string, string>();
for (let i = 0; i < args.length; i += 2) {
  const key = args[i]!, value = args[i + 1];
  if (!['--glb', '--binding', '--out', '--fps', '--subdivisions', '--duration'].includes(key) || !value || flags.has(key))
    throw new Error('Usage: --glb SOURCE --binding DECLARATION --out NEW_JSON [--fps 24 --subdivisions 2 --duration 4]');
  flags.set(key, value);
}
for (const key of ['--glb', '--binding', '--out']) if (!flags.has(key)) throw new Error('Missing ' + key);
const [bytes, declaration] = await Promise.all([
  readFile(flags.get('--glb')!), readFile(flags.get('--binding')!, 'utf8'),
]);
const binding = readGlbBinding(bytes, JSON.parse(declaration) as BindingManifest);
const fixture = generateFixture(binding, Number(flags.get('--fps') ?? 24), Number(flags.get('--subdivisions') ?? 2),
  Number(flags.get('--duration') ?? 4));
await writeFile(flags.get('--out')!, JSON.stringify(fixture), { flag: 'wx' });
console.log(JSON.stringify({ sourceSHA256: binding.sourceSHA256, frames: fixture.frames.length, families: fixture.families,
  output: flags.get('--out'), acceptance: 'UNACCEPTED', grip: 'UNMEASURED', contacts: 'UNMEASURED' }));
