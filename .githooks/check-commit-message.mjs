import { readFileSync } from 'node:fs';
import { execFileSync } from 'node:child_process';
import { createHash } from 'node:crypto';
import { attributionTrailers, placeholderModel, resolveAttribution } from './resolve-attribution.mjs';

// Syntax is enforceable; truth and editorial quality remain the parent's review.
const fail = (message) => {
  console.error('REFUSED: ' + message + '\nSee docs/git/COMMITS.md.');
  process.exit(1);
};
const file = process.argv[2];
if (!file) fail('commit-msg needs a message file');
const message = execFileSync('git', ['stripspace', '--strip-comments'], {
  input: readFileSync(file, 'utf8'), encoding: 'utf8',
}).trimEnd();
const lines = message.split('\n');
const subject = lines[0];
const pattern = /^(feat|fix|docs|design|art|style|refactor|perf|test|build|ci|chore|revert)(\([a-z0-9][a-z0-9/-]*\))?!?: \S.*$/;
if (!pattern.test(subject)) fail('use type(scope): finding (scope optional)');
const subjectLength = Array.from(new Intl.Segmenter('en', { granularity: 'grapheme' }).segment(subject)).length;
if (subjectLength > 72) fail('subject must be at most 72 characters');
if (subject.endsWith('.') || subject !== subject.trim()) {
  fail('subject must have no trailing period or whitespace');
}
if (lines[1] !== '') fail('separate the subject and body with a blank line');
const paragraphs = lines.slice(2).join('\n').split(/\n\n+/);
const last = paragraphs.at(-1) ?? '';
const trailerLine = /^[A-Za-z][A-Za-z-]*: \S.*$/;
const hasTrailerBlock = /^(Assisted-by|Co-authored-by|Signed-off-by):/im.test(last) &&
  last.split('\n').every((line) => trailerLine.test(line));
const body = (hasTrailerBlock ? paragraphs.slice(0, -1) : paragraphs).join('\n\n');
if (!body.trim() || !body.split('\n').some((line) =>
  line.trim() && !/^[A-Za-z][A-Za-z-]*:\s/.test(line))) {
  fail('include a substantive body explaining why the change matters');
}
if (!/^Validation: \S.*$/m.test(body)) {
  fail('include Validation: with checks and outcomes (or why none ran)');
}
const attributions = lines.filter((line) => /^Assisted-by:/i.test(line));
const activeCodex = process.env.CODEX_THREAD_ID || process.env.CODEX_SESSION_ID;
const explicitCloud = process.env.CODEX_CLOUD_ATTRIBUTION_FILE !== undefined;
let expected;
if (explicitCloud || (activeCodex && process.env.SKIP_ATTRIB !== '1')) {
  try { expected = await resolveAttribution(); } catch (error) { fail(error.message); }
}
if (process.env.SKIP_ATTRIB !== '1' && attributions.length === 0) {
  fail('end AI commits with Assisted-by: tool:actual-model');
}
if (expected && !attributions.includes(`Assisted-by: ${expected.tool}:${expected.model}`)) {
  fail('the active Codex session requires its resolved tool/model trailer');
}
if (expected?.source === 'user-provided') {
  for (const trailer of attributionTrailers(expected).filter(line => line.startsWith('Attribution-'))) {
    const key = trailer.split(':', 1)[0];
    const declared = lines.filter(line => line.toLowerCase().startsWith(key.toLowerCase() + ':'));
    if (declared.length !== 1 || declared[0] !== trailer || !last.split('\n').includes(trailer)) {
      fail('cloud attribution requires exact user-provided provenance trailers in the final block');
    }
  }
  const split = expected.evidence.lastIndexOf('@');
  const path = expected.evidence.slice(0, split);
  let staged;
  try { staged = execFileSync('git', ['show', ':' + path], { stdio: ['ignore', 'pipe', 'pipe'] }); }
  catch { fail('stage the reviewed cloud attribution declaration in this commit index'); }
  if (createHash('sha256').update(staged).digest('hex') !== expected.evidence.slice(split + 1)) {
    fail('staged cloud attribution declaration does not match the reviewed bytes');
  }
}
for (const attribution of attributions) {
  if (!hasTrailerBlock || !last.split('\n').includes(attribution) ||
      !/^Assisted-by: [^:\s](?:[^:]*[^:\s])?:\S+$/.test(attribution) ||
      attribution !== attribution.trimEnd()) {
    fail('Assisted-by must be a well-formed final trailer, after a blank line');
  }
  const [, tool, model] = attribution.match(/^Assisted-by: ([^:]+):(\S+)$/);
  if (/^codex\b/i.test(tool) && tool !== (expected?.tool ?? 'Codex')) {
    fail('use the canonical tool name Codex so its session model can be verified');
  }
  if (placeholderModel.test(model)) {
    fail('resolve the real session model; placeholders are forbidden');
  }
  if (expected && tool === expected.tool && model !== expected.model) {
    fail('Codex trailer model does not match resolved session attribution');
  }
  if (!explicitCloud && tool === 'Codex' && activeCodex && !expected) {
    // Preserve model validation even when the human-only bypass is present.
    try {
      if (model !== (await resolveAttribution()).model) fail('Codex trailer model does not match active session metadata');
    } catch (error) { fail(error.message); }
  }
}
