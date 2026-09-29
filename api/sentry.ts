/**
 * First-party Sentry tunnel for Safari content blockers. Only ROCKHOP error envelopes may pass;
 * the upstream URL is fixed, so this cannot be used as an arbitrary HTTP proxy.
 */
const DSN = 'https://5862fb5726b0b6a752e81cb74ebf24f4@o4512161165410304.ingest.us.sentry.io/4512167555694592';
const UPSTREAM = 'https://o4512161165410304.ingest.us.sentry.io/api/4512167555694592/envelope/';
export const MAX_ENVELOPE_BYTES = 128 * 1024;
export const RATE_LIMIT_PER_MINUTE = 12;
const STORE_ORIGINS = new Set(['capacitor://localhost', 'http://localhost']);
const hits = new Map<string, number[]>();

function headers(origin: string | null, ownOrigin: string): Record<string, string> {
  return {
    'cache-control': 'no-store',
    ...(origin && origin !== ownOrigin && STORE_ORIGINS.has(origin) ? { 'access-control-allow-origin': origin, vary: 'Origin' } : {}),
  };
}

function deniedOrigin(req: Request): boolean {
  const origin = req.headers.get('origin');
  return Boolean(origin && origin !== new URL(req.url).origin && !STORE_ORIGINS.has(origin));
}

function limited(req: Request, now = Date.now()): boolean {
  const ip = (req.headers.get('x-forwarded-for') ?? req.headers.get('x-real-ip') ?? 'unknown').split(',')[0]!.trim();
  const recent = (hits.get(ip) ?? []).filter((time) => time > now - 60_000);
  recent.push(now);
  hits.set(ip, recent);
  if (hits.size > 500) for (const key of hits.keys()) if (key !== ip) hits.delete(key);
  return recent.length > RATE_LIMIT_PER_MINUTE;
}

export function resetSentryRateLimit(): void {
  hits.clear();
}

function reply(req: Request, status: number): Response {
  return new Response(null, { status, headers: headers(req.headers.get('origin'), new URL(req.url).origin) });
}

/** Bounded stream read: a false or absent Content-Length cannot bypass the 128 KiB limit. */
async function readEnvelope(req: Request): Promise<Uint8Array | null> {
  const declared = req.headers.get('content-length');
  if (declared && (!/^\d+$/.test(declared) || Number(declared) > MAX_ENVELOPE_BYTES)) return null;
  if (!req.body) return null;
  const reader = req.body.getReader();
  const chunks: Uint8Array[] = [];
  let total = 0;
  try {
    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      total += value.byteLength;
      if (total > MAX_ENVELOPE_BYTES) {
        await reader.cancel();
        return null;
      }
      chunks.push(value);
    }
  } finally {
    reader.releaseLock();
  }
  const bytes = new Uint8Array(total);
  let offset = 0;
  for (const chunk of chunks) { bytes.set(chunk, offset); offset += chunk.byteLength; }
  return bytes;
}

/** The SDK emits header\nitem-header\nJSON event; attachments and other signal types are refused. */
export function validErrorEnvelope(bytes: Uint8Array): boolean {
  const first = bytes.indexOf(10);
  const second = first < 0 ? -1 : bytes.indexOf(10, first + 1);
  if (first < 1 || second <= first + 1 || second === bytes.length - 1) return false;
  try {
    const header = JSON.parse(new TextDecoder().decode(bytes.subarray(0, first))) as Record<string, unknown>;
    const item = JSON.parse(new TextDecoder().decode(bytes.subarray(first + 1, second))) as Record<string, unknown>;
    const event = JSON.parse(new TextDecoder().decode(bytes.subarray(second + 1))) as Record<string, unknown>;
    if (!header || header.dsn !== DSN || !item || item.type !== 'event' || !event || Array.isArray(event)) return false;
    if (event.type === 'transaction' || !event.exception || typeof event.exception !== 'object') return false;
    const values = (event.exception as { values?: unknown }).values;
    return Array.isArray(values) && values.length > 0;
  } catch {
    return false;
  }
}

export async function POST(req: Request): Promise<Response> {
  if (deniedOrigin(req)) return reply(req, 403);
  if (limited(req)) return reply(req, 429);
  const bytes = await readEnvelope(req);
  if (!bytes) return reply(req, 413);
  if (!validErrorEnvelope(bytes)) return reply(req, 400);
  try {
    const upstream = await fetch(UPSTREAM, {
      method: 'POST',
      headers: { 'content-type': 'application/x-sentry-envelope' },
      body: bytes.buffer as ArrayBuffer,
      redirect: 'error',
      signal: AbortSignal.timeout(5000),
    });
    return reply(req, upstream.status);
  } catch {
    return reply(req, 502);
  }
}

export function OPTIONS(req: Request): Response {
  if (deniedOrigin(req)) return reply(req, 403);
  return new Response(null, {
    status: 204,
    headers: {
      ...headers(req.headers.get('origin'), new URL(req.url).origin),
      'access-control-allow-methods': 'POST, OPTIONS',
      'access-control-allow-headers': 'content-type',
      'access-control-max-age': '86400',
    },
  });
}

export function GET(req: Request): Response {
  return new Response(null, { status: 405, headers: { ...headers(req.headers.get('origin'), new URL(req.url).origin), allow: 'POST, OPTIONS' } });
}
