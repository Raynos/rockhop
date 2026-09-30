import { execFileSync, spawnSync } from 'node:child_process';

const git = (...args) => execFileSync('git', args, { encoding: 'utf8' });
const fail = (message) => {
  console.error('REFUSED: ' + message + '\nSee docs/git/COMMITS.md.');
  process.exit(1);
};
const files = git('diff', '--cached', '--name-only', '-z', '--diff-filter=ACMR')
  .split('\0').filter(Boolean);
console.error('Paths in this commit:');
console.error(git('diff', '--cached', '--name-only', '-z').split('\0')
  .filter(Boolean).map((file) => '  ' + JSON.stringify(file)).join('\n'));
const whitespace = spawnSync('git', ['diff', '--cached', '--check'], { encoding: 'utf8' });
if (whitespace.status !== 0) fail(whitespace.stdout + whitespace.stderr);

// Count added + removed text lines; the required journal cannot inflate its
// own threshold. Binary changes contribute no text lines.
const stats = git('diff', '--cached', '--numstat', '-z').split('\0');
let changedLines = 0;
for (let i = 0; i < stats.length; i++) {
  if (!stats[i]) continue;
  const [added, removed, ...pathParts] = stats[i].split('\t');
  let path = pathParts.join('\t');
  if (!path) { i++; path = stats[++i]; } // Rename: old path, then new path.
  if (!path.startsWith('project/journal/')) {
    changedLines += (Number(added) || 0) + (Number(removed) || 0);
  }
}
console.error('Non-journal text lines changed: ' + changedLines);
if (changedLines >= 30) {
  const journals = files.filter((file) =>
    /^project\/journal\/.+\.md$/.test(file) &&
    !/(^|\/)(README|_TEMPLATE)\.md$/.test(file));
  const recorded = journals.some((file) => {
    const diff = git('diff', '--cached', '--no-ext-diff', '--unified=0', '--', file);
    const added = diff.split('\n').filter((line) =>
      line.startsWith('+') && !line.startsWith('+++')).map((line) => line.slice(1)).join('\n');
    return ['Finding', 'Validation', 'Limits'].every((field) =>
      new RegExp('^' + field + ': \\S.+$', 'm').test(added));
  });
  if (!recorded) fail('include a journal entry adding Finding:, Validation:, and Limits:');
} else {
  console.error('Under 30 changed lines: journal optional');
}

for (const file of files) {
  const object = git('rev-parse', ':' + file).trim();
  const size = Number(git('cat-file', '-s', object));
  if (size > 100 * 1024 * 1024) fail('blob exceeds the GitHub 100 MiB limit: ' + file);
  // Check the proposed blob, never another worker's working-tree version.
  let command;
  let args;
  if (file.endsWith('.sh')) {
    command = 'bash'; args = ['-n'];
  } else if (file.endsWith('.mjs')) {
    command = process.execPath; args = ['--input-type=module', '--check'];
  } else {
    continue;
  }
  const mode = git('ls-files', '--stage', '-z', '--', file).slice(0, 6);
  if (mode === '120000') continue; // A symlink's blob is its target path.
  const check = spawnSync(command, args, {
    input: execFileSync('git', ['cat-file', 'blob', object], { maxBuffer: size + 1 }),
    encoding: 'utf8',
  });
  if (check.status !== 0) fail('syntax check failed for ' + file + '\n' + check.stderr);
}
