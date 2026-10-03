import { createReadStream, readFileSync, readdirSync, realpathSync, statSync } from 'node:fs';
import { createHash } from 'node:crypto';
import { execFileSync } from 'node:child_process';
import { homedir } from 'node:os';
import { isAbsolute, join, relative, resolve, sep } from 'node:path';
import { createInterface } from 'node:readline';
import { pathToFileURL } from 'node:url';

export async function codexModel() {
  const session = process.env.CODEX_THREAD_ID || process.env.CODEX_SESSION_ID;
  if (!session) throw new Error('No Codex session ID; inspect the active tool session before committing');
  const sessions = join(process.env.CODEX_HOME || join(homedir(), '.codex'), 'sessions');
  const files = readdirSync(sessions, { recursive: true })
    .filter((file) => file.endsWith('.jsonl') && file.includes(session));
  if (files.length !== 1) throw new Error('Expected one local record for the active Codex session');
  let model;
  let matched = false;
  const input = createInterface({ input: createReadStream(join(sessions, files[0])), crlfDelay: Infinity });
  for await (const line of input) {
    let row;
    try { row = JSON.parse(line); } catch { continue; }
    if (row.type === 'session_meta' && row.payload?.id === session) matched = true;
    if (row.type === 'turn_context' && row.payload?.model) model = row.payload.model;
  }
  if (!matched || !model) throw new Error('Active session has no verified model metadata');
  return model;
}

export const placeholderModel = /^(unknown|actual-model|model|model_version|latest|default|auto|n\/a|null|undefined)$/i;

export async function resolveAttribution() {
  const declaration = process.env.CODEX_CLOUD_ATTRIBUTION_FILE;
  if (declaration === undefined) {
    return { tool: 'Codex', model: await codexModel(), source: 'desktop-session' };
  }
  // This is an explicit user declaration, never a fallback for failed metadata.
  if (!/^docs\/evidence\/[A-Za-z0-9_./-]+\.json$/.test(declaration) ||
      isAbsolute(declaration) || declaration.split('/').some(part => part === '.' || part === '..')) {
    throw new Error('Cloud attribution requires a repository docs/evidence JSON path');
  }
  const session = process.env.CODEX_THREAD_ID || process.env.CODEX_SESSION_ID;
  if (!session) throw new Error('Cloud attribution requires the active session ID');
  const root = realpathSync(execFileSync('git', ['rev-parse', '--show-toplevel'], { encoding: 'utf8' }).trim());
  const path = realpathSync(resolve(root, declaration));
  if (!path.startsWith(root + sep)) throw new Error('Cloud attribution declaration must stay inside the repository');
  const stat = statSync(path);
  if (!stat.isFile() || stat.size > 16384) throw new Error('Cloud attribution declaration must be a file of at most 16 KiB');
  const bytes = readFileSync(path);
  const data = JSON.parse(bytes.toString('utf8'));
  const keys = ['schemaVersion', 'execution', 'source', 'session', 'tool', 'model', 'authorization'];
  if (!data || Array.isArray(data) || typeof data !== 'object' ||
      Object.keys(data).length !== keys.length || keys.some(key => !Object.hasOwn(data, key)) ||
      data.schemaVersion !== 1 || data.execution !== 'cloud' || data.source !== 'user-provided') {
    throw new Error('Cloud attribution requires schemaVersion 1, cloud execution and user-provided provenance');
  }
  if (data.session !== session) throw new Error('Cloud attribution declaration does not match the active session');
  if (!['Codex', 'codex'].includes(data.tool) || typeof data.model !== 'string' ||
      !/^[A-Za-z0-9][A-Za-z0-9._-]{0,79}$/.test(data.model) || placeholderModel.test(data.model)) {
    throw new Error('Cloud attribution requires an explicit Codex tool/model label, without placeholders');
  }
  if (typeof data.authorization !== 'string' || data.authorization.length > 2000 ||
      !data.authorization.includes(`${data.tool}:${data.model}`)) {
    throw new Error('Cloud attribution must record the user authorization for the exact tool/model label');
  }
  return {
    tool: data.tool, model: data.model, source: data.source, session,
    evidence: relative(root, path).split(sep).join('/') + '@' + createHash('sha256').update(bytes).digest('hex'),
  };
}

export function attributionTrailers(attribution) {
  const lines = [];
  if (attribution.source === 'user-provided') {
    lines.push('Attribution-source: user-provided', `Attribution-session: ${attribution.session}`,
      `Attribution-evidence: ${attribution.evidence}`);
  }
  lines.push(`Assisted-by: ${attribution.tool}:${attribution.model}`);
  return lines;
}

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    console.info(attributionTrailers(await resolveAttribution()).join('\n'));
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
