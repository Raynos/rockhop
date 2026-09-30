import { build } from 'vite';
import { fileURLToPath } from 'node:url';

/** Standalone private browser code; never writes into a player's frozen build. */
export async function privateContactBundle(): Promise<string> {
  const result = await build({ configFile: false, logLevel: 'error', publicDir: false,
    build: { write: false, minify: false, rollupOptions: {
      external: ['three'], output: { globals: { three: '__rockhopContactTHREE' } },
    }, lib: {
      entry: fileURLToPath(new URL('./contact-browser.mts', import.meta.url)),
      name: 'RockhopContactProbe', formats: ['iife'],
    } } });
  const outputs = Array.isArray(result) ? result : [result];
  const chunks = outputs.flatMap(output => {
    if (!('output' in output)) throw new Error('private contact helper bundle output unavailable');
    return output.output.filter(part => part.type === 'chunk');
  });
  if (chunks.length !== 1) throw new Error('private contact helper must be one standalone chunk');
  return chunks[0]!.code;
}
