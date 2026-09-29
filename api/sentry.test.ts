import { afterEach, beforeEach, describe, expect, it, vi } from 'vitest';
import { GET, MAX_ENVELOPE_BYTES, OPTIONS, POST, RATE_LIMIT_PER_MINUTE, resetSentryRateLimit } from './sentry';

const dsn = 'https://5862fb5726b0b6a752e81cb74ebf24f4@o4512161165410304.ingest.us.sentry.io/4512167555694592';
const upstream = 'https://o4512161165410304.ingest.us.sentry.io/api/4512167555694592/envelope/';

function envelope({ to = dsn, type = 'event', event = { exception: { values: [{ type: 'Error', value: 'test' }] } } }:
  { to?: string; type?: string; event?: Record<string, unknown> } = {}): string {
  return `${JSON.stringify({ sent_at: '2026-09-29T00:00:00Z', dsn: to })}\n${JSON.stringify({ type })}\n${JSON.stringify(event)}`;
}

function request(body: string, headers: Record<string, string> = {}): Request {
  return new Request('https://playrockhop.vercel.app/api/sentry', {
    method: 'POST',
    headers: { origin: 'https://playrockhop.vercel.app', 'x-forwarded-for': '192.0.2.5', ...headers },
    body,
  });
}

beforeEach(() => resetSentryRateLimit());
afterEach(() => vi.unstubAllGlobals());

describe('Sentry first-party tunnel', () => {
  it('forwards only a ROCKHOP exception envelope to the fixed ingest endpoint', async () => {
    const fetch = vi.fn(async () => new Response(null, { status: 200 }));
    vi.stubGlobal('fetch', fetch);
    const raw = envelope();
    const res = await POST(request(raw, { 'x-forwarded-for': '192.0.2.5', authorization: 'do-not-forward' }));
    expect(res.status).toBe(200);
    expect(fetch).toHaveBeenCalledTimes(1);
    const [url, init] = fetch.mock.calls[0] as unknown as [string, RequestInit];
    expect(url).toBe(upstream);
    expect(init.method).toBe('POST');
    expect(new TextDecoder().decode(init.body as ArrayBuffer)).toBe(raw);
    expect(init.headers).toEqual({ 'content-type': 'application/x-sentry-envelope' });
  });

  it('rejects an alien DSN, a transaction, an attachment and malformed input without forwarding', async () => {
    const fetch = vi.fn();
    vi.stubGlobal('fetch', fetch);
    const cases = [
      envelope({ to: 'https://elsewhere.invalid/1' }),
      envelope({ type: 'transaction' }),
      envelope({ type: 'attachment' }),
      envelope({ event: { message: 'not an exception' } }),
      `${envelope()}\n${envelope()}`,
      'not an envelope',
    ];
    for (const raw of cases) expect((await POST(request(raw))).status).toBe(400);
    expect(fetch).not.toHaveBeenCalled();
  });

  it('bounds the actual body even without a truthful Content-Length', async () => {
    const fetch = vi.fn();
    vi.stubGlobal('fetch', fetch);
    expect((await POST(request('x', { 'content-length': String(MAX_ENVELOPE_BYTES + 1) }))).status).toBe(413);
    expect((await POST(request('x'.repeat(MAX_ENVELOPE_BYTES + 1)))).status).toBe(413);
    expect(fetch).not.toHaveBeenCalled();
  });

  it('accepts only the site and the two native app origins, with bounded warm-instance rate', async () => {
    const fetch = vi.fn(async () => new Response(null, { status: 200 }));
    vi.stubGlobal('fetch', fetch);
    expect((await POST(request(envelope(), { origin: 'https://attacker.example' }))).status).toBe(403);
    const native = await POST(request(envelope(), { origin: 'capacitor://localhost' }));
    expect(native.status).toBe(200);
    expect(native.headers.get('access-control-allow-origin')).toBe('capacitor://localhost');
    for (let i = 1; i < RATE_LIMIT_PER_MINUTE; i++) expect((await POST(request(envelope()))).status).toBe(200);
    expect((await POST(request(envelope()))).status).toBe(429);
    expect(fetch).toHaveBeenCalledTimes(RATE_LIMIT_PER_MINUTE);
  });

  it('permits CORS preflight only for the native origins and refuses GET', () => {
    const url = 'https://playrockhop.vercel.app/api/sentry';
    expect(OPTIONS(new Request(url, { method: 'OPTIONS', headers: { origin: 'http://localhost' } })).headers.get('access-control-allow-origin')).toBe('http://localhost');
    expect(OPTIONS(new Request(url, { method: 'OPTIONS', headers: { origin: 'https://attacker.example' } })).status).toBe(403);
    expect(GET(new Request(url)).status).toBe(405);
  });
});
