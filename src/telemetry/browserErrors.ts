/** Lazy, error-only Sentry channel. The crash sheet remains the game's error owner. */
import type { captureException, init, withScope } from '@sentry/browser';

declare const __BUILD_ID__: string;

export type CrashSource = 'boot' | 'window' | 'rejection';

// A browser DSN is a public ingest address, not an authentication credential. Local builds opt in.
const productionDsn = 'https://5862fb5726b0b6a752e81cb74ebf24f4@o4512161165410304.ingest.us.sentry.io/4512167555694592';
const dsn = String(import.meta.env.VITE_SENTRY_DSN ?? (import.meta.env.PROD ? productionDsn : '')).trim();
type BrowserSdk = { init: typeof init; withScope: typeof withScope; captureException: typeof captureException };
let sdk: Promise<BrowserSdk | null> | null = null;

/** Headless gates and the deliberate ?crash= probe must not fill the production issue feed. */
export function shouldReportBrowserError(
  options: { dsn: string; webdriver: boolean; search: string; test: boolean },
): boolean {
  return Boolean(options.dsn) && (options.test || (!options.webdriver && !new URLSearchParams(options.search).has('crash')));
}

function loadSdk(): Promise<BrowserSdk | null> {
  sdk ??= import('@sentry/browser').then((sentry) => {
    sentry.init({
      dsn,
      // The web game's envelopes stay on playrockhop.vercel.app, which iOS content blockers allow.
      // Capacitor uses a local app origin, so its explicit production URL needs CORS on the tunnel.
      tunnel: import.meta.env.VITE_STORE === '1' ? 'https://playrockhop.vercel.app/api/sentry' : '/api/sentry',
      release: `rockhop@${__BUILD_ID__}`,
      environment: import.meta.env.PROD ? (import.meta.env.VITE_STORE === '1' ? 'store' : 'production') : 'development',
      // Wild Shard's game client uses explicit error capture: no global duplicate handlers,
      // boot-time SDK cost, fetch/click breadcrumbs, profiling, tracing or replay.
      defaultIntegrations: false,
      integrations: [],
      tracesSampleRate: 0,
      replaysSessionSampleRate: 0,
      replaysOnErrorSampleRate: 0,
      sendClientReports: false,
      maxBreadcrumbs: 0,
      beforeSend(event) {
        // Review URLs can contain arbitrary query values. Only a stable path belongs in an error.
        event.request = { url: `${location.origin}${location.pathname}` };
        delete event.user;
        return event;
      },
    });
    return sentry;
  }).catch(() => null);
  return sdk;
}

function asError(reason: unknown): Error {
  if (reason instanceof Error) return reason;
  if (typeof reason === 'object' && reason !== null && 'message' in reason && typeof reason.message === 'string') {
    const error = new Error(reason.message);
    if ('stack' in reason && typeof reason.stack === 'string') error.stack = reason.stack;
    return error;
  }
  return new Error(String(reason));
}

/** Fire and forget; telemetry may never throw into the crash screen or block reload. */
export function captureBrowserError(reason: unknown, source: CrashSource): void {
  if (!shouldReportBrowserError({
    dsn,
    webdriver: navigator.webdriver === true,
    search: import.meta.env.VITE_STORE === '1' ? '' : location.search,
    test: import.meta.env.VITE_SENTRY_TEST === '1',
  })) return;
  void loadSdk().then((sentry) => {
    if (!sentry) return;
    try {
      sentry.withScope((scope) => {
        scope.setTags({ game: 'rockhop', build: __BUILD_ID__, crash_source: source });
        scope.setLevel('fatal');
        sentry.captureException(asError(reason));
      });
    } catch { /* the crash sheet is more important than telemetry */ }
  });
}
