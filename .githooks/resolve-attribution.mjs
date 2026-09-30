import { createReadStream, readdirSync } from 'node:fs';
import { homedir } from 'node:os';
import { join, resolve } from 'node:path';
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

if (process.argv[1] && import.meta.url === pathToFileURL(resolve(process.argv[1])).href) {
  try {
    console.info('Assisted-by: Codex:' + await codexModel());
  } catch (error) {
    console.error(error.message);
    process.exitCode = 1;
  }
}
