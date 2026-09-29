/**
 * Durable key/value storage for progress, best times and settings (docs/plans/STORE_RELEASE.md Phase 5).
 *
 * Web: `localStorage`, exactly as before. Native (the Capacitor shells): WKWebView / Android WebView localStorage
 * can be evicted under storage pressure, so every write also goes to @capacitor/preferences (UserDefaults on iOS,
 * SharedPreferences on Android — app data, never collected). A local write-ahead marker keeps the newest operation
 * if the app exits before that asynchronous bridge write finishes; `hydrateStorage()` replays it on next launch.
 *
 * The UI keeps its synchronous reads: `persistentStorage()` returns a `Storage`-shaped object (the same surface as
 * `localStorage`), so a module that did `const s = localStorage` does `const s = persistentStorage()` instead and
 * nothing else changes. Reads always come from localStorage; `hydrateStorage()` must have resolved before the first
 * read on native (src/platform/index.ts `startPlatform`, awaited before `boot()`).
 *
 * Every call is try/catch'd like the callers already expect: private mode, blocked storage and the harness work.
 */

/** The async key/value store behind the mirror (Preferences on native). Injectable for tests. */
export interface DurableKV {
  keys(): Promise<string[]>;
  get(key: string): Promise<string | null>;
  set(key: string, value: string): Promise<void>;
  remove(key: string): Promise<void>;
  clear(): Promise<void>;
}

let durable: DurableKV | null = null;
let pending: Promise<unknown> = Promise.resolve();
const JOURNAL_PREFIX = 'rockhop.mirror.pending.';
const CLEAR_MARKER = 'rockhop.mirror.clearPending';
let journalId = 0;

type JournalEntry = { id: number; key: string; op: 'set'; value: string } | { id: number; key: string; op: 'remove' };
type JournalAction = { op: 'set'; value: string } | { op: 'remove' };
const journalKey = (key: string): string => `${JOURNAL_PREFIX}${encodeURIComponent(key)}`;
const internalKey = (key: string): boolean => key === CLEAR_MARKER || key.startsWith(JOURNAL_PREFIX);

function local(): Storage | null {
  try {
    return typeof localStorage === 'undefined' ? null : localStorage;
  } catch {
    return null;
  }
}

/** Queue a durable write after the previous one, so the last write of a key always lands last. Errors are logged, never thrown. */
function mirror(op: (kv: DurableKV) => Promise<unknown>, committed?: () => void): void {
  const kv = durable;
  if (!kv) return;
  pending = pending.then(async () => {
    await op(kv);
    committed?.();
  }).catch((e: unknown) => console.warn('[rockhop] durable storage write failed', e));
}

/** A local write-ahead marker survives a WebView exit before its asynchronous Preferences write settles. */
function mark(key: string, entry: JournalAction): string {
  const serialized = JSON.stringify({ ...entry, id: ++journalId, key });
  local()?.setItem(journalKey(key), serialized);
  return serialized;
}

function unmark(key: string, serialized: string): void {
  const ls = local();
  const marker = journalKey(key);
  if (ls?.getItem(marker) === serialized) ls.removeItem(marker);
}

/** A `Storage` whose writes reach localStorage now and the durable store (when there is one) in order, soon after. */
class MirroredStorage implements Storage {
  get length(): number {
    const ls = local();
    if (!ls) return 0;
    let visible = 0;
    for (let i = 0; i < ls.length; i++) if (!internalKey(ls.key(i) ?? '')) visible++;
    return visible;
  }
  key(index: number): string | null {
    const ls = local();
    if (!ls) return null;
    for (let i = 0; i < ls.length; i++) {
      const key = ls.key(i);
      if (key !== null && !internalKey(key) && index-- === 0) return key;
    }
    return null;
  }
  getItem(key: string): string | null {
    return local()?.getItem(key) ?? null;
  }
  setItem(key: string, value: string): void {
    const ls = local();
    const marker = mark(key, { op: 'set', value });
    try {
      ls?.setItem(key, value); // may throw QuotaExceededError, as localStorage does: callers already catch it
    } catch (e) {
      unmark(key, marker);
      throw e;
    }
    mirror((kv) => kv.set(key, value), () => unmark(key, marker));
  }
  removeItem(key: string): void {
    const marker = mark(key, { op: 'remove' });
    local()?.removeItem(key);
    mirror((kv) => kv.remove(key), () => unmark(key, marker));
  }
  clear(): void {
    const ls = local();
    ls?.setItem(CLEAR_MARKER, '1');
    if (ls) for (const key of Array.from({ length: ls.length }, (_, i) => ls.key(i))) {
      if (key !== null && key !== CLEAR_MARKER) ls.removeItem(key);
    }
    mirror((kv) => kv.clear(), () => ls?.removeItem(CLEAR_MARKER));
  }
}

const mirrored = new MirroredStorage();

/** The storage the game reads and writes: `localStorage` on the web, the Preferences-backed mirror in the native shells. */
export function persistentStorage(): Storage | null {
  if (!durable) return local();
  return local() ? mirrored : null;
}

/**
 * Native start-up: make the durable store the source of truth. Keys it holds are written into localStorage (this is
 * what restores progress after the WebView evicted it); keys only localStorage holds (written before the first
 * native launch, or by an older build) are copied into it. Resolves when both agree.
 */
export async function hydrateStorage(kv: DurableKV): Promise<{ restored: number; pushed: number }> {
  durable = kv;
  const ls = local();
  let restored = 0;
  let pushed = 0;
  if (ls && ls.getItem(CLEAR_MARKER) !== null) {
    await kv.clear();
    ls.clear();
  }
  if (ls) {
    const markers = Array.from({ length: ls.length }, (_, i) => ls.key(i)).filter((key): key is string => key?.startsWith(JOURNAL_PREFIX) === true);
    for (const marker of markers) {
      const raw = ls.getItem(marker);
      if (!raw) continue;
      let entry: JournalEntry;
      try { entry = JSON.parse(raw) as JournalEntry; } catch { continue; }
      if (typeof entry.key !== 'string' || marker !== journalKey(entry.key)) continue;
      if (entry.op === 'set' && typeof entry.value === 'string') {
        ls.setItem(entry.key, entry.value);
        await kv.set(entry.key, entry.value);
      } else if (entry.op === 'remove') {
        ls.removeItem(entry.key);
        await kv.remove(entry.key);
      } else continue;
      ls.removeItem(marker);
    }
  }
  const keys = new Set(await kv.keys());
  for (const k of keys) {
    if (internalKey(k)) continue;
    const v = await kv.get(k);
    if (v === null || !ls) continue;
    if (ls.getItem(k) !== v) {
      try {
        ls.setItem(k, v);
        restored += 1;
      } catch {
        /* quota: the durable copy still holds it */
      }
    }
  }
  if (ls) {
    for (let i = 0; i < ls.length; i++) {
      const k = ls.key(i);
      if (k === null || internalKey(k) || keys.has(k)) continue;
      const v = ls.getItem(k);
      if (v === null) continue;
      await kv.set(k, v);
      pushed += 1;
    }
  }
  return { restored, pushed };
}

/** Resolves once every durable write queued so far has landed (tests, and the gate's persistence check). */
export function durableFlushed(): Promise<void> {
  return pending.then(() => undefined);
}

/** Test seam: forget the durable store (back to plain localStorage). */
export function resetStorageForTests(): void {
  durable = null;
  pending = Promise.resolve();
}
