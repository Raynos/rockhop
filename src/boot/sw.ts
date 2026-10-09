/**
 * The service worker, driven from the first line of the loading screen (bundled into the ≤ 8 KB
 * inline loader, so every byte here is spent on purpose).
 *
 * Two jobs, both before the bars move:
 *
 *  1. **Be in control before the boot asks for 27 MB.** Registering at the tail of `front`
 *     (where this used to live) let install/activate/`clients.claim()` land after the 14 hero GLBs
 *     had already been requested, so the first visit cached 4 MB and 0 models and the player needed
 *     a *second* online visit before offline worked. Registering here and waiting (briefly, capped)
 *     for control means every byte the boot streams passes through the worker's `cacheFirst`.
 *
 *  2. **Take the new build now, not with a toast.** If a newer worker is waiting, it is activated
 *     and the page reloads immediately — the player sees one loading screen and comes up on the new
 *     build. The caches are split so that reload costs only what actually changed (src/pwa/sw.js).
 *     A build published while the app is already open is announced by the "new build" pill on the
 *     menu screens (src/ui/updatePill.ts, which reuses `handOver` below) — never applied under a run.
 *
 * The boot is never held hostage: everything here races a `CAP_MS` timeout, and any failure resolves.
 */

/** The longest the loading screen waits for the worker to take control (or to hand over to a new build). */
const CAP_MS = 2500;

/**
 * THE hand-over to a waiting worker: `SKIP_WAITING` → it activates and `clients.claim()`s → `controllerchange`
 * → reload onto the new build. One copy, used by the boot below and by the "new build" pill (src/ui/updatePill.ts).
 */
export const handOver = (sw: ServiceWorkerContainer, w: ServiceWorker): (() => void) => {
  const reload = (): void => location.reload();
  sw.addEventListener('controllerchange', reload, { once: true });
  w.postMessage({ type: 'SKIP_WAITING' });
  return () => sw.removeEventListener('controllerchange', reload);
};

export function swBoot(enabled: boolean): Promise<void> {
  // Browser-only (the inline loader): `navigator` exists; `serviceWorker` is undefined outside a secure context.
  const sw = navigator.serviceWorker as ServiceWorkerContainer | undefined;
  if (!enabled || !sw || /[?&]sw=0/.test(location.search)) return Promise.resolve();
  return new Promise<void>((resolve) => {
    let finished = false;
    let cancelHandOver: (() => void) | undefined;
    let installing: ServiceWorker | null = null;
    const done = (): void => {
      if (finished) return;
      finished = true;
      clearTimeout(timer);
      cancelHandOver?.();
      sw.removeEventListener('controllerchange', done);
      installing?.removeEventListener('statechange', changed);
      resolve();
    };
    let timer = setTimeout(done, CAP_MS);
    const changed = (): void => {
      if (installing?.state === 'installed') {
        // Activation belongs to the admitted handover, not the install watch.
        // Its next statechange must not cancel reload before clients.claim().
        installing.removeEventListener('statechange', changed);
        adopt(installing);
      } else if (installing?.state !== 'installing') done();
    };
    /** A newer build is installed: activate it and come up on it, instead of booting the old one. */
    const adopt = (w: ServiceWorker | null): void => {
      // The timeout ends startup ownership. A slow install must not reload
      // normal play or a Garage visit after the loading screen has finished.
      if (finished) return;
      if (!w) return done();
      clearTimeout(timer);
      timer = setTimeout(done, CAP_MS);
      cancelHandOver = handOver(sw, w);
    };
    void sw.register('./sw.js', { scope: './' }).then(async (reg) => {
      // Standalone installs live for days: keep discovering updates so the next launch adopts one for free.
      document.addEventListener('visibilitychange', () => {
        if (!document.hidden) void reg.update().catch(() => undefined);
      });
      if (finished) return;
      // First visit (or an evicted worker): wait for `clients.claim()`, so the boot's own bytes are cached.
      if (!sw.controller) return sw.addEventListener('controllerchange', done, { once: true });
      await reg.update().catch(() => undefined);
      if (finished) return;
      const inst = reg.installing;
      if (reg.waiting || !inst) return adopt(reg.waiting);
      installing = inst;
      inst.addEventListener('statechange', changed);
    }, done);
  });
}
