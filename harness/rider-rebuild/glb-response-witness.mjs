/** Stream the same immutable local asset URL without WebKit inspector caching.
 * This witnesses server bytes, not a second read of the browser response body.
 */
import assert from 'node:assert/strict';
import crypto from 'node:crypto';

export async function witnessGlbResponse(response, cache) {
  const url = response.url(), parsed = new URL(url);
  assert(['127.0.0.1', 'localhost', '[::1]'].includes(parsed.hostname));
  assert.equal(response.status(), 200);
  const browserHeaders = response.headers();
  if (!cache.has(url)) cache.set(url, (async () => {
    const streamed = await fetch(url, { headers: { 'Accept-Encoding': 'identity' } });
    assert.equal(streamed.status, 200); assert.equal(streamed.url, url);
    const hash = crypto.createHash('sha256'); let bytes = 0;
    for await (const chunk of streamed.body) { hash.update(chunk); bytes += chunk.length; }
    assert.equal(bytes, Number(streamed.headers.get('content-length')));
    return { sha256: hash.digest('hex'), bytes };
  })());
  const witness = await cache.get(url);
  if (!browserHeaders['content-encoding'] && browserHeaders['content-length'])
    assert.equal(witness.bytes, Number(browserHeaders['content-length']));
  return { url, status: response.status(), ...witness,
    browserContentLength: browserHeaders['content-length'] ?? null,
    hashScope: 'Independent streamed HTTP witness of the same immutable local build URL; browser body cache not read' };
}
