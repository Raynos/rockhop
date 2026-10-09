import { afterEach, beforeEach, expect, it, vi } from 'vitest';
import { handOver, swBoot } from './sw';

const flush = async (): Promise<void> => { for (let i = 0; i < 8; i++) await Promise.resolve(); };
const worker = () => Object.assign(new EventTarget(), { state: 'installing', postMessage: vi.fn() });
let reload: ReturnType<typeof vi.fn>;
let sw: EventTarget & { controller: unknown; register: ReturnType<typeof vi.fn> };
let reg: { waiting: unknown; installing: ReturnType<typeof worker> | null; update: ReturnType<typeof vi.fn> };

beforeEach(() => {
  vi.useFakeTimers();
  reload = vi.fn();
  reg = { waiting: null, installing: null, update: vi.fn().mockResolvedValue(undefined) };
  sw = Object.assign(new EventTarget(), { controller: {}, register: vi.fn().mockResolvedValue(reg) });
  vi.stubGlobal('navigator', { serviceWorker: sw });
  vi.stubGlobal('location', { search: '', reload });
  vi.stubGlobal('document', Object.assign(new EventTarget(), { hidden: false }));
});
afterEach(() => { vi.useRealTimers(); vi.unstubAllGlobals(); });

it('does not adopt a worker whose update finishes after startup timed out', async () => {
  let finish!: () => void;
  reg.update.mockReturnValue(new Promise<void>(resolve => { finish = resolve; }));
  const boot = swBoot(true); await flush();
  await vi.advanceTimersByTimeAsync(2500); await boot;
  const next = worker(); reg.waiting = next; finish(); await flush();
  sw.dispatchEvent(new Event('controllerchange'));
  expect(next.postMessage).not.toHaveBeenCalled(); expect(reload).not.toHaveBeenCalled();
});

it('removes a slow installation watcher when startup times out', async () => {
  const next = worker(); reg.installing = next;
  const boot = swBoot(true); await flush();
  await vi.advanceTimersByTimeAsync(2500); await boot;
  next.state = 'installed'; next.dispatchEvent(new Event('statechange'));
  sw.dispatchEvent(new Event('controllerchange'));
  expect(next.postMessage).not.toHaveBeenCalled(); expect(reload).not.toHaveBeenCalled();
});

it('cancels a stalled handover so a later claim cannot reload the Garage', async () => {
  const next = worker(); reg.waiting = next;
  const boot = swBoot(true); await flush();
  expect(next.postMessage).toHaveBeenCalledWith({ type: 'SKIP_WAITING' });
  await vi.advanceTimersByTimeAsync(2500); await boot;
  sw.dispatchEvent(new Event('controllerchange'));
  expect(reload).not.toHaveBeenCalled();
});

it('still reloads once for an update adopted within the startup handover', async () => {
  reg.waiting = worker(); const boot = swBoot(true); await flush();
  sw.dispatchEvent(new Event('controllerchange')); sw.dispatchEvent(new Event('controllerchange'));
  expect(reload).toHaveBeenCalledTimes(1);
  await vi.advanceTimersByTimeAsync(2500); await boot;
});

it('keeps a timely installing update handover through activation', async () => {
  const next = worker(); reg.installing = next;
  const boot = swBoot(true); await flush();
  next.state = 'installed'; next.dispatchEvent(new Event('statechange'));
  expect(next.postMessage).toHaveBeenCalledWith({ type: 'SKIP_WAITING' });
  next.state = 'activating'; next.dispatchEvent(new Event('statechange'));
  next.state = 'activated'; next.dispatchEvent(new Event('statechange'));
  sw.dispatchEvent(new Event('controllerchange'));
  expect(reload).toHaveBeenCalledTimes(1);
  await vi.advanceTimersByTimeAsync(2500); await boot;
  sw.dispatchEvent(new Event('controllerchange'));
  expect(reload).toHaveBeenCalledTimes(1);
});

it('finishes first-install control without reloading the new visitor', async () => {
  sw.controller = null; const boot = swBoot(true); await flush();
  sw.dispatchEvent(new Event('controllerchange')); await boot;
  expect(reload).not.toHaveBeenCalled(); expect(vi.getTimerCount()).toBe(0);
});

it('lets an explicit handover owner cancel its reload listener', () => {
  const cancel = handOver(sw as unknown as ServiceWorkerContainer, worker() as unknown as ServiceWorker);
  cancel(); sw.dispatchEvent(new Event('controllerchange'));
  expect(reload).not.toHaveBeenCalled();
});
