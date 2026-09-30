import type { Page } from 'playwright';

export type OfflineBrowserBackend = 'swiftshader' | 'metal';

/** Keep the original portable flags unless Metal was explicitly requested on macOS. */
export function selectOfflineBrowserBackend(requested = process.env.TRIALS_BROWSER_BACKEND ?? 'swiftshader', platform = process.platform): { backend: OfflineBrowserBackend; args: string[] } {
  if (requested === 'swiftshader') return { backend: 'swiftshader', args: ['--use-angle=swiftshader', '--enable-unsafe-swiftshader', '--ignore-gpu-blocklist'] };
  if (requested === 'metal') {
    if (platform !== 'darwin') throw new Error('Offline Metal benchmark requires macOS');
    return { backend: 'metal', args: ['--use-angle=metal', '--enable-webgl', '--ignore-gpu-blocklist'] };
  }
  throw new Error(`Unsupported offline browser backend: ${requested}`);
}

export interface ActualBootRenderer { renderer: string; contextKind: string }

/** No Metal result may be qualified when Chromium silently selected a software GL backend. */
export function assertRequestedBootRenderer(backend: OfflineBrowserBackend, actual: ActualBootRenderer | null, phase: string): void {
  if (backend !== 'metal') return;
  if (actual?.contextKind !== 'webgl2' || !/Metal/i.test(actual.renderer) || /SwiftShader|llvmpipe|software/i.test(actual.renderer)) {
    throw new Error(`${phase}: requested Metal WebGL2, actual game renderer ${JSON.stringify(actual)}`);
  }
}

/** These are observer times on the page's performance time origin, not exact script execution times. */
export interface BootTrace {
  timeOrigin: number;
  observerInstalledAtMs: number;
  observerReadyState: DocumentReadyState;
  loaderFirstObservedAtMs: number | null;
  moduleScriptFirstObservedAtMs: number | null;
  loaderDoneObservedAtMs: number | null;
  loaderRemovedObservedAtMs: number | null;
  sampledAtMs: number;
  rowsAtDone: { key: string; label: string; state: string; durationMsRounded: number | null; text: string }[] | null;
  navigation: {
    startTimeMs: number;
    workerStartMs: number;
    fetchStartMs: number;
    responseStartMs: number;
    responseEndMs: number;
    domInteractiveMs: number;
    domContentLoadedEventStartMs: number;
    domContentLoadedEventEndMs: number;
    loadEventEndMs: number;
    transferSize: number;
  } | null;
  marks: { name: string; startTimeMs: number }[];
  /** The normal game's own renderer, from window.__render.stats(); null if startup never constructed it. */
  actualRenderer: ActualBootRenderer | null;
}

/**
 * Test-only probe, installed before navigation. A MutationObserver snapshots the loader when its
 * data-done flag flips, before the app's 300 ms removal timer can discard its rounded step rows.
 * Observing insertion is not a timestamp for when a module actually began executing.
 */
export const BOOT_TRACE_INIT = `(() => {
  if (window !== window.top) return;
  const trace = {
    observerInstalledAtMs: performance.now(),
    observerReadyState: document.readyState,
    loaderFirstObservedAtMs: null,
    moduleScriptFirstObservedAtMs: null,
    loaderDoneObservedAtMs: null,
    loaderRemovedObservedAtMs: null,
    rowsAtDone: null,
  };
  window.__rockhopBootTrace = trace;
  let loader = null;
  const snapshotRows = () => Array.from(loader.querySelectorAll('ol li[data-key]'), (li) => {
    const text = (li.children[1]?.textContent ?? '').trim();
    const match = /^(\\d+)\\s*ms$/.exec(text);
    return {
      key: li.dataset.key ?? '',
      label: (li.children[0]?.textContent ?? '').trim(),
      state: li.className,
      durationMsRounded: match ? Number(match[1]) : null,
      text,
    };
  });
  const observe = () => {
    if (!loader) {
      loader = document.getElementById('loader');
      if (loader) trace.loaderFirstObservedAtMs = performance.now();
    }
    if (trace.moduleScriptFirstObservedAtMs === null && document.querySelector('script[type="module"][src]')) {
      trace.moduleScriptFirstObservedAtMs = performance.now();
    }
    if (loader && trace.loaderDoneObservedAtMs === null && loader.dataset.done === '1') {
      trace.loaderDoneObservedAtMs = performance.now();
      trace.rowsAtDone = snapshotRows();
    }
    if (loader && !loader.isConnected && trace.loaderRemovedObservedAtMs === null) {
      trace.loaderRemovedObservedAtMs = performance.now();
      observer.disconnect();
    }
  };
  const observer = new MutationObserver(observe);
  observer.observe(document, { subtree: true, childList: true, attributes: true, attributeFilter: ['data-done'] });
  observe();
})();`;

/** Read only this page's navigation; an update handover may have created a newer document. */
export async function readBootTrace(page: Page): Promise<BootTrace | null> {
  return page.evaluate(() => {
    const w = window as typeof window & {
      __rockhopBootTrace?: Omit<BootTrace, 'timeOrigin' | 'sampledAtMs' | 'navigation' | 'marks' | 'actualRenderer'>;
      __render?: { stats(): ActualBootRenderer };
    };
    const trace = w.__rockhopBootTrace;
    if (!trace) return null;
    const nav = performance.getEntriesByType('navigation')[0] as PerformanceNavigationTiming | undefined;
    const marks: BootTrace['marks'] = [];
    for (const entry of performance.getEntriesByType('mark')) {
      if (entry.name.startsWith('render:prepare:') || entry.name === 'render:ctor' || entry.name === 'render:entry') {
        marks.push({ name: entry.name, startTimeMs: entry.startTime });
      }
    }
    let actualRenderer: ActualBootRenderer | null = null;
    try {
      const stats = w.__render?.stats();
      if (stats) actualRenderer = { renderer: stats.renderer, contextKind: stats.contextKind };
    } catch { /* Preserve the trace for a failed startup; Metal qualification rejects null. */ }
    return {
      ...trace,
      timeOrigin: performance.timeOrigin,
      sampledAtMs: performance.now(),
      navigation: nav ? {
        startTimeMs: nav.startTime,
        workerStartMs: nav.workerStart,
        fetchStartMs: nav.fetchStart,
        responseStartMs: nav.responseStart,
        responseEndMs: nav.responseEnd,
        domInteractiveMs: nav.domInteractive,
        domContentLoadedEventStartMs: nav.domContentLoadedEventStart,
        domContentLoadedEventEndMs: nav.domContentLoadedEventEnd,
        loadEventEndMs: nav.loadEventEnd,
        transferSize: nav.transferSize,
      } : null,
      marks,
      actualRenderer,
    } satisfies BootTrace;
  }).catch(() => null);
}
