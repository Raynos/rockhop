import { test } from 'node:test';
import assert from 'node:assert/strict';
import { mkdtempSync, mkdirSync, writeFileSync, cpSync, rmSync, symlinkSync } from 'node:fs';
import { tmpdir } from 'node:os';
import { resolve, join, dirname } from 'node:path';
import { fileURLToPath } from 'node:url';
import { spawnSync } from 'node:child_process';

const source = resolve(dirname(fileURLToPath(import.meta.url)), '..');
const env = { ...process.env, GIT_CONFIG_GLOBAL: '/dev/null', GIT_CONFIG_SYSTEM: '/dev/null' };
for (const key of Object.keys(env)) {
  if (key === 'CODEX_THREAD_ID' || key === 'CODEX_SESSION_ID' ||
      key === 'CODEX_CLOUD_ATTRIBUTION_FILE' ||
      (key.startsWith('GIT_') && !key.startsWith('GIT_CONFIG_')) ||
      key.startsWith('SKIP_')) delete env[key];
}
const valid = [
  'fix(boot): recover the startup context', '',
  'A transient context loss left the player stuck at startup.', '',
  'Validation: startup regression passes; physical phone pending.', '',
  'Assisted-by: Codex:gpt-6.1-sol', '',
].join('\n');
const journal = 'Finding: The startup context can recover.\nValidation: Regression passes.\nLimits: Physical phone pending.\n';

function fixture(t) {
  const root = mkdtempSync(join(tmpdir(), 'rockhop-hooks-'));
  t.after(() => rmSync(root, { recursive: true, force: true }));
  const run = (cmd, args, options = {}) => spawnSync(cmd, args, {
    cwd: root, env: { ...env, ...options.env }, encoding: 'utf8', ...options,
  });
  const git = (...args) => {
    const result = run('git', args);
    assert.equal(result.status, 0, result.stdout + result.stderr);
    return result.stdout;
  };
  const write = (path, data) => {
    mkdirSync(dirname(join(root, path)), { recursive: true });
    writeFileSync(join(root, path), data);
  };
  git('init', '-q');
  git('config', 'user.name', 'Hook fixture');
  git('config', 'user.email', 'fixture@example.test');
  git('config', 'commit.gpgsign', 'false');
  cpSync(join(source, '.githooks'), join(root, '.githooks'), { recursive: true });
  mkdirSync(join(root, '.claude/hooks'), { recursive: true });
  cpSync(join(source, '.claude/hooks/md-ratio.sh'), join(root, '.claude/hooks/md-ratio.sh'));
  write('src.mjs', 'export const x = 1;\n');
  git('add', '.githooks', '.claude/hooks/md-ratio.sh', 'src.mjs');
  git('-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'fixture baseline');
  git('config', 'core.hooksPath', '.githooks');
  const message = (text = valid, extraEnv = {}) => {
    write('.git/message', text);
    return run(process.execPath, ['.githooks/check-commit-message.mjs', '.git/message'],
      { env: { ...env, ...extraEnv } });
  };
  return { root, run, git, write, message };
}

const messageCases = [
  ['valid message', valid, true],
  ['unscoped subject', valid.replace('fix(boot)', 'fix'), true],
  ['breaking subject', valid.replace('fix(boot)', 'fix(boot)!'), true],
  ['actual tool/model', valid.replace('Codex:gpt-6.1-sol', 'Claude Code:claude-fable-5'), true],
  ['comments ignored', valid + '# editor instructions\n', true],
  ['72-character subject', valid.replace(valid.split('\n')[0], 'fix: ' + 'x'.repeat(67)), true],
  ['overlong subject', valid.replace(valid.split('\n')[0], 'fix: ' + 'x'.repeat(68)), false],
  ['72-grapheme subject', valid.replace(valid.split('\n')[0], 'fix: ' + '🛠️'.repeat(67)), true],
  ['overlong grapheme subject', valid.replace(valid.split('\n')[0], 'fix: ' + '🛠️'.repeat(68)), false],
  ['legacy subject', valid.replace('fix(boot):', 'Fix:'), false],
  ['unknown type', valid.replace('fix(boot)', 'update(boot)'), false],
  ['uppercase scope', valid.replace('(boot)', '(BOOT)'), false],
  ['trailing period', valid.replace('context\n', 'context.\n'), false],
  ['missing blank line', valid.replace('context\n\n', 'context\n'), false],
  ['subject only', valid.split('\n')[0], false],
  ['trailer-only body', valid.split('\n')[0] + '\n\nAssisted-by: Codex:gpt-6.1-sol\n', false],
  ['missing validation', valid.replace('Validation:', 'Checks:'), false],
  ['metadata-only body', valid.replace(
    'A transient context loss left the player stuck at startup.',
    'Signed-off-by: Person <person@example.test>'), false],
  ['missing attribution', valid.replace('Assisted-by: Codex:gpt-6.1-sol\n', ''), false],
  ['body after trailer', valid + '\nMore body after attribution.\n', false],
  ['trailer without blank', valid.replace('pending.\n\nAssisted', 'pending.\nAssisted'), false],
  ['empty model', valid.replace('Codex:gpt-6.1-sol', 'Codex:   '), false],
  ['empty tool', valid.replace('Codex:gpt-6.1-sol', ':gpt-6.1-sol'), false],
  ['padded tool', valid.replace('Codex:gpt-6.1-sol', 'Codex :gpt-6.1-sol'), false],
  ['model with spaces', valid.replace('Codex:gpt-6.1-sol', 'Codex:gpt model'), false],
  ['unknown model rejected', valid.replace('gpt-6.1-sol', 'unknown'), false],
  ['placeholder model rejected', valid.replace('gpt-6.1-sol', 'actual-model'), false],
  ['forged revert bypass', valid.replace(valid.split('\n')[0], 'Revert anything'), false],
  ['human coauthor plus AI assist', valid.replace('Assisted-by:',
    'Co-authored-by: Human <human@example.test>\nAssisted-by:'), true],
];
for (const [name, input, pass] of messageCases) {
  void test(name, (t) => {
    const result = fixture(t).message(input);
    assert.equal(result.status === 0, pass, result.stderr);
  });
}
void test('human bypass skips only attribution', (t) => {
  const f = fixture(t);
  assert.equal(f.message(valid.replace('Assisted-by: Codex:gpt-6.1-sol\n', ''),
    { SKIP_ATTRIB: '1' }).status, 0);
  assert.notEqual(f.message('Update everything', { SKIP_ATTRIB: '1' }).status, 0);
});
void test('Codex resolver uses matching session and latest recorded model', (t) => {
  const f = fixture(t);
  const metadata = [
    { type: 'session_meta', payload: { id: 'fixture-session' } },
    { type: 'turn_context', payload: { model: 'gpt-6-sol' } },
    { type: 'turn_context', payload: { model: 'gpt-6.1-sol' } },
  ];
  f.write('runtime/sessions/2026/09/30/rollout-fixture-session.jsonl',
    metadata.map((row) => JSON.stringify(row)).join('\n') + '\n');
  const sessionEnv = { ...env, CODEX_HOME: join(f.root, 'runtime'), CODEX_THREAD_ID: 'fixture-session' };
  const result = f.run(process.execPath, ['.githooks/resolve-attribution.mjs'], { env: sessionEnv });
  assert.equal(result.status, 0, result.stderr);
  assert.equal(result.stdout.trim(), 'Assisted-by: Codex:gpt-6.1-sol');
  assert.equal(f.message(valid, sessionEnv).status, 0);
  assert.notEqual(f.message(valid.replace('gpt-6.1-sol', 'gpt-6-sol'), sessionEnv).status, 0);
  for (const tool of ['codex', 'Codex CLI', 'Claude Code']) {
    assert.notEqual(f.message(valid.replace('Codex:gpt-6.1-sol', tool + ':gpt-imaginary'),
      sessionEnv).status, 0);
  }
  assert.notEqual(f.message(valid, { ...sessionEnv, CODEX_THREAD_ID: 'missing-session' }).status, 0);
});

const cloudPath = 'docs/evidence/cloud-attribution/user-declaration.json';
const cloudDeclaration = {
  schemaVersion: 1, execution: 'cloud', source: 'user-provided',
  session: 'fixture-cloud-session', tool: 'codex', model: 'Astra-6',
  authorization: 'The user explicitly authorized codex:Astra-6.',
};
function cloudFixture(t, declaration = cloudDeclaration) {
  const f = fixture(t);
  f.write(cloudPath, JSON.stringify(declaration) + '\n');
  f.git('add', cloudPath);
  const cloudEnv = {
    ...env, CODEX_THREAD_ID: 'fixture-cloud-session',
    CODEX_CLOUD_ATTRIBUTION_FILE: cloudPath, CODEX_HOME: join(f.root, 'absent-desktop-metadata'),
  };
  const resolveCloud = (extraEnv = {}) => f.run(process.execPath,
    ['.githooks/resolve-attribution.mjs'], { env: { ...cloudEnv, ...extraEnv } });
  return { ...f, cloudEnv, resolveCloud };
}
function cloudMessage(trailers) {
  return valid.replace('Assisted-by: Codex:gpt-6.1-sol', trailers.trim());
}
void test('explicit cloud declaration records user provenance without desktop access', (t) => {
  const f = cloudFixture(t);
  const result = f.resolveCloud();
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /^Attribution-source: user-provided\n/);
  assert.match(result.stdout, /Assisted-by: codex:Astra-6\n$/);
  assert.match(result.stdout, /Attribution-session: fixture-cloud-session\n/);
  assert.match(result.stdout, /Attribution-evidence: docs\/evidence\/cloud-attribution\/user-declaration.json@[a-f0-9]{64}\n/);
  const message = cloudMessage(result.stdout);
  assert.equal(f.message(message, f.cloudEnv).status, 0);
  assert.notEqual(f.message(message.replace('codex:Astra-6', 'codex:gpt-imaginary'), f.cloudEnv).status, 0);
  assert.notEqual(f.message(message.replace('codex:Astra-6', 'Codex:Astra-6'), f.cloudEnv).status, 0);
  for (const field of ['Attribution-source', 'Attribution-session', 'Attribution-evidence']) {
    assert.notEqual(f.message(message.replace(new RegExp('^' + field + ':.*\\n', 'm'), ''), f.cloudEnv).status, 0);
  }
  assert.notEqual(f.message(message.replace('user-provided\n', 'auto-detected\n'), f.cloudEnv).status, 0);
  assert.notEqual(f.message(message.replace('Attribution-source: user-provided',
    'Attribution-source: user-provided\nAttribution-source: user-provided'), f.cloudEnv).status, 0);
  assert.notEqual(f.message(message.replace('Attribution-source: user-provided',
    'Attribution-source: user-provided\nattribution-source: user-provided'), f.cloudEnv).status, 0);
  assert.notEqual(f.message(cloudMessage('Assisted-by: codex:Astra-6'), { ...f.cloudEnv, SKIP_ATTRIB: '1' }).status, 0);
  f.write(cloudPath, JSON.stringify({ ...cloudDeclaration, authorization: 'User authorized codex:Astra-6 again.' }) + '\n');
  assert.notEqual(f.message(message, f.cloudEnv).status, 0, 'declaration hash must match the commit provenance');
  assert.notEqual(f.message(cloudMessage(f.resolveCloud().stdout), f.cloudEnv).status, 0, 'reviewed declaration bytes must be staged');
  f.git('add', cloudPath);
  assert.equal(f.message(cloudMessage(f.resolveCloud().stdout), f.cloudEnv).status, 0);
});
void test('cloud declaration works through an ordinary commit with both hooks', (t) => {
  const f = cloudFixture(t);
  f.write('project/journal/cloud.md', journal);
  f.git('add', cloudPath, 'project/journal/cloud.md');
  f.write('.git/message', cloudMessage(f.resolveCloud().stdout));
  const result = f.run('git', ['commit', '-qF', '.git/message'], { env: f.cloudEnv });
  assert.equal(result.status, 0, result.stdout + result.stderr);
  assert.match(f.git('log', '-1', '--format=%B'), /Attribution-source: user-provided/);
  assert.match(f.git('log', '-1', '--format=%B'), /Assisted-by: codex:Astra-6\n/);
});
const rejectedCloudDeclarations = [
  ['wrong schema', { ...cloudDeclaration, schemaVersion: 2 }],
  ['non-cloud context', { ...cloudDeclaration, execution: 'desktop' }],
  ['automatic provenance claim', { ...cloudDeclaration, source: 'auto-detected' }],
  ['foreign session', { ...cloudDeclaration, session: 'foreign-session' }],
  ['missing source', Object.fromEntries(Object.entries(cloudDeclaration).filter(([key]) => key !== 'source'))],
  ['extra field', { ...cloudDeclaration, fallbackModel: 'Astra-6' }],
  ['placeholder model', { ...cloudDeclaration, model: 'unknown' }],
  ['empty model', { ...cloudDeclaration, model: '' }],
  ['model with trailer injection', { ...cloudDeclaration, model: 'Astra-6\nSigned-off-by: someone' }],
  ['unrelated tool', { ...cloudDeclaration, tool: 'Claude Code' }],
  ['unrecorded authorization', { ...cloudDeclaration, authorization: 'I guessed this model.' }],
  ['non-object declaration', []],
];
for (const [name, declaration] of rejectedCloudDeclarations) {
  void test('cloud rejects ' + name, (t) => {
    const f = cloudFixture(t, declaration);
    assert.notEqual(f.resolveCloud().status, 0);
    assert.notEqual(f.message(cloudMessage('Assisted-by: codex:Astra-6'), f.cloudEnv).status, 0);
  });
}
void test('cloud rejects missing or malformed files and never falls back to desktop', (t) => {
  const f = cloudFixture(t);
  f.write('runtime/sessions/rollout-fixture-cloud-session.jsonl', [
    { type: 'session_meta', payload: { id: 'fixture-cloud-session' } },
    { type: 'turn_context', payload: { model: 'gpt-6.1-sol' } },
  ].map(row => JSON.stringify(row)).join('\n') + '\n');
  const desktopHome = { CODEX_HOME: join(f.root, 'runtime') };
  for (const path of ['', 'docs/evidence/missing.json', '../foreign.json', '/tmp/foreign.json']) {
    assert.notEqual(f.resolveCloud({ ...desktopHome, CODEX_CLOUD_ATTRIBUTION_FILE: path }).status, 0);
  }
  f.write(cloudPath, '{malformed JSON');
  assert.notEqual(f.resolveCloud(desktopHome).status, 0);
  assert.notEqual(f.message(valid, { ...f.cloudEnv, ...desktopHome }).status, 0);
  f.write(cloudPath, ' '.repeat(16385));
  assert.notEqual(f.resolveCloud(desktopHome).status, 0);
  f.write(cloudPath, JSON.stringify(cloudDeclaration));
  assert.notEqual(f.resolveCloud({ CODEX_THREAD_ID: '', CODEX_SESSION_ID: '' }).status, 0);
});
void test('cloud declaration cannot escape the repository through a symlink', (t) => {
  const f = cloudFixture(t);
  const outside = mkdtempSync(join(tmpdir(), 'rockhop-cloud-outside-'));
  t.after(() => rmSync(outside, { recursive: true, force: true }));
  writeFileSync(join(outside, 'user.json'), JSON.stringify(cloudDeclaration));
  rmSync(join(f.root, cloudPath));
  symlinkSync(join(outside, 'user.json'), join(f.root, cloudPath));
  const result = f.resolveCloud();
  assert.notEqual(result.status, 0);
  assert.match(result.stderr, /must stay inside the repository/);
});
void test('small commit succeeds without a journal', (t) => {
  const f = fixture(t);
  f.write('src.mjs', 'export const x = 2;\n');
  f.write('.git/message', valid);
  f.git('commit', '-qF', '.git/message', '--', 'src.mjs');
});
void test('journal gate rejects missing, template-only, and empty entries', (t) => {
  const f = fixture(t);
  f.write('work.txt', 'line\n'.repeat(30));
  f.git('add', 'work.txt');
  f.write('src.mjs', 'export const x = 2;\n');
  f.git('add', 'src.mjs');
  assert.notEqual(f.run('bash', ['.githooks/pre-commit']).status, 0);
  f.write('project/journal/_TEMPLATE.md', journal);
  f.git('add', 'project/journal/_TEMPLATE.md');
  assert.notEqual(f.run('bash', ['.githooks/pre-commit']).status, 0);
  f.write('project/journal/round.md', '# Empty entry\n');
  f.git('add', 'project/journal/round.md');
  assert.notEqual(f.run('bash', ['.githooks/pre-commit']).status, 0);
});
void test('journal and syntax checks read staged blobs', (t) => {
  const f = fixture(t);
  f.write('work.txt', 'line\n'.repeat(30));
  f.git('add', 'work.txt');
  f.write('project/journal/round.md', journal);
  f.git('add', 'project/journal/round.md');
  f.write('project/journal/round.md', '# Broken unstaged journal\n');
  f.write('src.mjs', 'export const x = 2;\n');
  f.git('add', 'src.mjs');
  f.write('src.mjs', 'broken !!!\n');
  assert.equal(f.run('bash', ['.githooks/pre-commit']).status, 0);
  f.git('add', 'src.mjs');
  f.write('src.mjs', 'export const x = 2;\n');
  assert.notEqual(f.run('bash', ['.githooks/pre-commit']).status, 0);
});
void test('small commits skip journal but retain syntax and whitespace checks', (t) => {
  const f = fixture(t);
  f.write('src.mjs', 'broken !!!\n');
  f.git('add', 'src.mjs');
  assert.notEqual(f.run('bash', ['.githooks/pre-commit']).status, 0);
  f.write('src.mjs', 'export const x = 2; \n');
  f.git('add', 'src.mjs');
  assert.notEqual(f.run('bash', ['.githooks/pre-commit']).status, 0);
});
void test('29 changed lines need no journal; 30 do', (t) => {
  const f = fixture(t);
  f.write('work.txt', 'line\n'.repeat(29));
  f.git('add', 'work.txt');
  assert.equal(f.run('bash', ['.githooks/pre-commit']).status, 0);
  f.write('work.txt', 'line\n'.repeat(30));
  f.git('add', 'work.txt');
  assert.notEqual(f.run('bash', ['.githooks/pre-commit']).status, 0);
  f.write('project/journal/round.md', journal);
  f.git('add', 'project/journal/round.md');
  assert.equal(f.run('bash', ['.githooks/pre-commit']).status, 0);
});
void test('threshold counts added and deleted lines', (t) => {
  const f = fixture(t);
  f.write('work.txt', 'old\n'.repeat(15));
  f.git('add', 'work.txt');
  f.git('-c', 'core.hooksPath=/dev/null', 'commit', '-qm', 'fixture prior text');
  f.write('work.txt', 'new\n'.repeat(15));
  f.git('add', 'work.txt');
  assert.notEqual(f.run('bash', ['.githooks/pre-commit']).status, 0);
});
void test('staged MJS over one MiB receives its full syntax check', (t) => {
  const f = fixture(t);
  f.write('large.mjs', 'export const x = 1;\n' + '// valid comment\n'.repeat(70000));
  f.write('project/journal/round.md', journal);
  f.git('add', 'large.mjs', 'project/journal/round.md');
  const result = f.run('bash', ['.githooks/pre-commit']);
  assert.equal(result.status, 0, result.stderr);
});
void test('journal itself does not trigger its threshold', (t) => {
  const f = fixture(t);
  f.write('project/journal/round.md', '# Historical note\n'.repeat(40));
  f.git('add', 'project/journal/round.md');
  assert.equal(f.run('bash', ['.githooks/pre-commit']).status, 0);
});
void test('pathspec commit excludes unrelated staged work and can amend', (t) => {
  const f = fixture(t);
  f.write('unrelated.mjs', 'broken !!!\n');
  f.git('add', 'unrelated.mjs');
  f.write('src.mjs', 'export const x = 2;\n');
  f.write('project/journal/round.md', journal);
  f.git('add', 'project/journal/round.md');
  f.write('.git/message', valid);
  f.git('commit', '-qF', '.git/message', '--', 'src.mjs', 'project/journal/round.md');
  assert.equal(f.git('diff', '--cached', '--name-only').trim(), 'unrelated.mjs');
  assert(!f.git('ls-tree', '-r', '--name-only', 'HEAD').includes('unrelated.mjs'));
  f.write('src.mjs', 'export const x = 3;\n');
  f.write('project/journal/round.md', journal +
    '\nFinding: Amend preserves the owned path set.\nValidation: Fixture checks pass.\nLimits: No gameplay exercised.\n');
  f.git('commit', '--amend', '-qF', '.git/message', '--', 'src.mjs', 'project/journal/round.md');
  assert.equal(f.git('show', 'HEAD:src.mjs'), 'export const x = 3;\n');
});
void test('scoped docs/design types pass markdown guard', (t) => {
  const f = fixture(t);
  f.write('notes.md', 'notes\n'.repeat(100));
  f.git('add', 'notes.md');
  for (const subject of ['docs(hooks): record the policy', 'design(c1): record the finding']) {
    f.write('.git/message', subject + '\n');
    assert.equal(f.run('bash', ['.claude/hooks/md-ratio.sh', 'commit', '.git/message']).status, 0);
  }
  f.write('.git/message', 'fix(boot): fix startup\n');
  assert.notEqual(f.run('bash', ['.claude/hooks/md-ratio.sh', 'commit', '.git/message']).status, 0);
});
void test('evidence markdown is excluded from the commit ratio', (t) => {
  const f = fixture(t);
  f.write('docs/evidence/example/README.md', 'proof\n'.repeat(100));
  f.write('src.mjs', 'export const x = 2;\n');
  f.git('add', 'docs/evidence/example/README.md', 'src.mjs');
  f.write('.git/message', 'fix(boot): fix startup\n');
  const result = f.run('bash', ['.claude/hooks/md-ratio.sh', 'commit', '.git/message']);
  assert.equal(result.status, 0, result.stderr);
  assert.match(result.stdout, /md 0 \/ code 2/);
});
void test('markdown just above forty percent is rejected without rounding', (t) => {
  const f = fixture(t);
  f.write('notes.md', 'notes\n'.repeat(41));
  f.write('code.ts', 'export const x = 1;\n'.repeat(60));
  f.git('add', 'notes.md', 'code.ts');
  f.write('.git/message', 'fix(boot): fix startup\n');
  const result = f.run('bash', ['.claude/hooks/md-ratio.sh', 'commit', '.git/message']);
  assert.notEqual(result.status, 0);
});
