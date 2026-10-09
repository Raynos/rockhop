/**
 * Best time per track in localStorage (`rockhop.best.<trackId>`), plus the
 * quality override (`rockhop.quality`). Every access is try/catch'd: private
 * mode, blocked storage and the headless harness must all just work.
 */
import type { BikeClass, Medal, QualityTier, RouteProof, RunResult } from '../core/types';
import { parseRouteProof } from '../core/replay';
import { persistentStorage } from '../platform/storage';
import { getTrack } from '../tracks';

export interface BestEntry {
  time: number;
  faults: number;
  /** Medal on the fastest recorded run, used when seeding the run board. */
  medal: Medal;
  /** Highest medal ever earned on this bike, even when that run was slower than the PB. */
  bestMedal?: Medal;
  /** Proof for the PB medal; legacy top medals on a new route track have no proof. */
  routeProof?: RouteProof;
  /** Proof for a slower medal improvement, independent of the PB replay. */
  bestMedalRouteProof?: RouteProof;
  /** Input replay for a slower proved top-medal run; PB recording remains the faster ride. */
  bestMedalRecording?: string;
  /** A pre-route top medal is preserved but identified as earned under the old rules. */
  legacyRouteMedal?: boolean;
  /** Bike class the PB was set on (absent in pre-garage entries = rookie). */
  bike?: BikeClass;
  /** Run clock at each checkpoint of the PB run. */
  splits?: number[];
  /** JSON InputRecording of the PB run (GO → finish) for the ghost. */
  recording?: string;
}

/** One row of the local per-track leaderboard (game.md § leaderboard). */
export interface BoardEntry {
  time: number;
  faults: number;
  medal: Medal;
  routeProof?: RouteProof;
  legacyRouteMedal?: boolean;
  /** ISO time the run finished ('' for a row seeded from a pre-board PB). */
  at: string;
}

/** Rows kept per track per class. */
export const BOARD_SIZE = 5;

const PREFIX = 'rockhop.best.';
const QUALITY_KEY = 'rockhop.quality';
const FPS_KEY = 'rockhop.fps';
const HELD_KEY = 'rockhop.heldTier';
const MEDAL_RANK: Record<Medal, number> = { bronze: 1, silver: 2, gold: 3, platinum: 4 };

function medalOf(entry: BestEntry): Medal {
  return entry.bestMedal ?? entry.medal;
}

function higherMedal(a: Medal, b: Medal): Medal {
  return MEDAL_RANK[a] >= MEDAL_RANK[b] ? a : b;
}

function legacyRouteMedal(trackId: string, medal: Medal, proof?: RouteProof): boolean {
  const goal = getTrack(trackId)?.diamondGoal;
  return medal === 'platinum' && !!goal && (proof?.goalId !== goal.id || proof.crossed !== true);
}

/** New top-medal writes require proof; old saved top medals remain grandfathered on read. */
function provedMedal(trackId: string, medal: Medal, proof?: RouteProof): Medal {
  return legacyRouteMedal(trackId, medal, proof) ? 'gold' : medal;
}

/** Storage key per track and bike class: rookie keeps the legacy key so pre-garage PBs survive; pro gets a suffix. */
export function bestKey(trackId: string, bike: BikeClass): string {
  return bike === 'pro' ? `${PREFIX}${trackId}@pro` : PREFIX + trackId;
}

/** `rockhop.best.<trackId>[@pro]#board`: under the best-times prefix so Reset progress clears it with the PBs. */
export function boardKey(trackId: string, bike: BikeClass): string {
  return `${bestKey(trackId, bike)}#board`;
}

/** Board order: faster first; equal times, fewer faults first. */
export function boardOrder(a: BoardEntry, b: BoardEntry): number {
  return a.time - b.time || a.faults - b.faults;
}

/** localStorage on the web, the Preferences-backed mirror in the native shells (src/platform/storage.ts). */
function store(): Storage | null {
  try {
    return persistentStorage();
  } catch {
    return null;
  }
}

/**
 * PB per track **per bike class**. `get(id, bike)` is that class's entry; `get(id)` is the
 * track's career best across classes (higher medal wins, then PB time) — what cards, tier locks and
 * the career line read. The ghost and splits always come from the class being ridden.
 */
export class BestTimes {
  private readonly cache = new Map<string, BestEntry | null>();

  get(trackId: string, bike?: BikeClass): BestEntry | null {
    if (bike) return this.read(trackId, bike);
    const a = this.read(trackId, 'rookie');
    const b = this.read(trackId, 'pro');
    if (!a && !b) return null;
    const chosen = !a ? b! : !b ? a : MEDAL_RANK[medalOf(b)] > MEDAL_RANK[medalOf(a)] || (medalOf(b) === medalOf(a) && b.time < a.time) ? b : a;
    // The no-bike view is a career summary. Keep each class's actual PB medal in storage and on its run board.
    return { ...chosen, medal: medalOf(chosen) };
  }

  private read(trackId: string, bike: BikeClass): BestEntry | null {
    const key = bestKey(trackId, bike);
    if (this.cache.has(key)) return this.cache.get(key) ?? null;
    const s = store();
    if (!s) return null;
    try {
      const raw = s.getItem(key);
      if (!raw) {
        this.cache.set(key, null);
        return null;
      }
      const o = JSON.parse(raw) as Partial<BestEntry>;
      if (typeof o.time !== 'number' || typeof o.faults !== 'number') return null;
      const proof = parseRouteProof(o.routeProof);
      const bestProof = parseRouteProof(o.bestMedalRouteProof);
      const rawMedal = o.medal && o.medal in MEDAL_RANK ? o.medal : 'bronze';
      const entry: BestEntry = { time: o.time, faults: o.faults, medal: rawMedal, bike };
      if (proof) entry.routeProof = proof;
      if (o.bestMedal && o.bestMedal in MEDAL_RANK) entry.bestMedal = higherMedal(entry.medal, o.bestMedal);
      if (bestProof) entry.bestMedalRouteProof = bestProof;
      if (typeof o.bestMedalRecording === 'string' && o.bestMedalRecording.length > 0) entry.bestMedalRecording = o.bestMedalRecording;
      if (legacyRouteMedal(trackId, entry.medal, proof) || legacyRouteMedal(trackId, entry.bestMedal ?? entry.medal, bestProof ?? proof)) entry.legacyRouteMedal = true;
      if (Array.isArray(o.splits) && o.splits.every((x) => typeof x === 'number')) entry.splits = o.splits;
      if (typeof o.recording === 'string' && o.recording.length > 0) entry.recording = o.recording;
      this.cache.set(key, entry);
      return entry;
    } catch {
      return null;
    }
  }

  private save(key: string, entry: BestEntry): void {
    this.cache.set(key, entry);
    try {
      store()?.setItem(key, JSON.stringify(entry));
    } catch {
      /* storage unavailable: the in-memory career entry still serves this session */
    }
  }

  clear(): void {
    this.cache.clear();
    this.boards.clear();
    clearAllBest();
  }

  // -- local per-track leaderboard (MEGA_PLAN P4; additive: the PB entries above are untouched) --------------------

  private readonly boards = new Map<string, BoardEntry[]>();

  /**
   * The best `BOARD_SIZE` finished runs on a track for a bike class, fastest first. A track with a PB from
   * before the board existed shows that PB as its one row, so old progress is never a blank board.
   */
  board(trackId: string, bike: BikeClass): BoardEntry[] {
    const key = boardKey(trackId, bike);
    const cached = this.boards.get(key);
    if (cached) return cached;
    let rows: BoardEntry[] = [];
    try {
      const raw = store()?.getItem(key);
      const o = raw ? (JSON.parse(raw) as unknown) : null;
      if (Array.isArray(o)) {
        rows = o
          .filter((e): e is BoardEntry => !!e && typeof e === 'object' && typeof (e as BoardEntry).time === 'number' && typeof (e as BoardEntry).faults === 'number')
          .map((e) => {
            const proof = parseRouteProof(e.routeProof);
            const medal = e.medal in MEDAL_RANK ? e.medal : 'bronze';
            return { time: e.time, faults: e.faults, medal, at: typeof e.at === 'string' ? e.at : '',
              ...(proof ? { routeProof: proof } : {}), ...(legacyRouteMedal(trackId, medal, proof) ? { legacyRouteMedal: true } : {}) };
          })
          .sort(boardOrder)
          .slice(0, BOARD_SIZE);
      }
    } catch {
      rows = [];
    }
    if (rows.length === 0) {
      const pb = this.read(trackId, bike);
      if (pb) rows = [{ time: pb.time, faults: pb.faults, medal: pb.medal, at: '', ...(pb.routeProof ? { routeProof: pb.routeProof } : {}),
        ...(pb.legacyRouteMedal ? { legacyRouteMedal: true } : {}) }];
    }
    this.boards.set(key, rows);
    return rows;
  }

  /**
   * Insert a finished run; returns its 1-based rank when it made the board, else null. Every clear is
   * offered (a PB is rank 1 by construction); ties keep the earlier run ahead.
   */
  record(trackId: string, r: RunResult, at: string = new Date().toISOString()): number | null {
    const bike: BikeClass = r.bike ?? 'rookie';
    const row: BoardEntry = { time: r.time, faults: r.faults, medal: provedMedal(trackId, r.medal, r.routeProof), at,
      ...(r.routeProof ? { routeProof: r.routeProof } : {}) };
    const rows = [...this.board(trackId, bike)];
    let i = rows.findIndex((e) => boardOrder(row, e) < 0);
    if (i < 0) i = rows.length;
    if (i >= BOARD_SIZE) return null;
    rows.splice(i, 0, row);
    rows.length = Math.min(rows.length, BOARD_SIZE);
    const key = boardKey(trackId, bike);
    this.boards.set(key, rows);
    try {
      store()?.setItem(key, JSON.stringify(rows));
    } catch {
      /* storage unavailable: the in-memory board still serves this session */
    }
    return i + 1;
  }

  put(trackId: string, r: RunResult, run?: { splits: number[]; recording: string | null }): void {
    const bike: BikeClass = r.bike ?? 'rookie';
    const prior = this.read(trackId, bike);
    const medal = provedMedal(trackId, r.medal, r.routeProof);
    const currentBest = prior ? medalOf(prior) : null;
    const currentWins = !currentBest || MEDAL_RANK[medal] >= MEDAL_RANK[currentBest];
    const entry: BestEntry = { time: r.time, faults: r.faults, medal, bestMedal: currentWins ? medal : currentBest!, bike };
    if (r.routeProof) entry.routeProof = r.routeProof;
    if (!currentWins && prior) {
      if (prior.bestMedalRouteProof) entry.bestMedalRouteProof = prior.bestMedalRouteProof;
      if (prior.bestMedalRecording) entry.bestMedalRecording = prior.bestMedalRecording;
      if (prior.legacyRouteMedal) entry.legacyRouteMedal = true;
    }
    if (run) {
      entry.splits = run.splits;
      if (run.recording) entry.recording = run.recording;
    }
    this.save(bestKey(trackId, bike), entry);
  }

  /** Record a slower run's medal improvement without replacing its bike class PB, ghost or board row. */
  recordMedal(trackId: string, medal: Medal, bike: BikeClass, routeProof?: RouteProof, recording?: string | null): void {
    const prior = this.read(trackId, bike);
    if (!prior) return;
    medal = provedMedal(trackId, medal, routeProof);
    const bestMedal = higherMedal(medalOf(prior), medal);
    const provesLegacy = prior.legacyRouteMedal && medal === 'platinum' && !legacyRouteMedal(trackId, medal, routeProof);
    if (bestMedal === medalOf(prior) && !provesLegacy) return;
    const keepRecording = medal === 'platinum' && !!getTrack(trackId)?.diamondGoal && routeProof?.crossed === true && !!recording;
    const entry: BestEntry = { ...prior, bestMedal };
    if (routeProof) entry.bestMedalRouteProof = routeProof;
    if (keepRecording) entry.bestMedalRecording = recording!;
    // A newly proved career medal does not rewrite an older PB ride's history.
    if (provesLegacy && !legacyRouteMedal(trackId, prior.medal, prior.routeProof)) delete entry.legacyRouteMedal;
    this.save(bestKey(trackId, bike), entry);
  }
}

const BIKE_KEY = 'rockhop.bikeClass';
const TELEMETRY_KEY = 'rockhop.telemetry';
const ONBOARDED_KEY = 'rockhop.onboarded';

/** The Garage choice, or null when the player has never picked (then the per-tier default applies, rules.ts). */
export function loadBikeChoice(): BikeClass | null {
  try {
    const v = store()?.getItem(BIKE_KEY);
    return v === 'pro' || v === 'rookie' ? v : null;
  } catch {
    return null;
  }
}

export function saveBikeChoice(b: BikeClass): void {
  try {
    store()?.setItem(BIKE_KEY, b);
  } catch {
    /* storage unavailable */
  }
}

/** Local run log: default ON, opt-out in Settings. */
export function loadTelemetryEnabled(): boolean {
  try {
    return store()?.getItem(TELEMETRY_KEY) !== '0';
  } catch {
    return true;
  }
}

export function saveTelemetryEnabled(on: boolean): void {
  try {
    store()?.setItem(TELEMETRY_KEY, on ? '1' : '0');
  } catch {
    /* storage unavailable */
  }
}

export function loadOnboarded(): boolean {
  try {
    return store()?.getItem(ONBOARDED_KEY) === '1';
  } catch {
    return true; // no storage: never nag
  }
}

export function saveOnboarded(): void {
  try {
    store()?.setItem(ONBOARDED_KEY, '1');
  } catch {
    /* storage unavailable */
  }
}

const GHOST_KEY = 'rockhop.ghost';
const MODEL_KEYS = { rider: 'rockhop.riderModel', bike: 'rockhop.bikeModel' } as const;

export type ModelChoice = 'proc' | 'gltf';

/**
 * glTF hero is the default (MEGA_PLAN P1: procedural bike retained as a
 * stored 'proc' bike choice). The rider is always the Blender model (asks 30 / 31: the Classic and Img2 chips left
 * the garage; ask 41: the img2 code itself is gone); a stored 'proc' / 'img2' rider from before is read as 'gltf' so
 * nobody stays stranded on a retired model. The rider has no procedural override or fallback.
 */
export function loadModelChoice(which: 'rider' | 'bike'): ModelChoice {
  try {
    const v = store()?.getItem(MODEL_KEYS[which]);
    return which === 'rider' ? 'gltf' : v === 'proc' ? 'proc' : 'gltf';
  } catch {
    return 'gltf';
  }
}

export function saveModelChoice(which: 'rider' | 'bike', v: ModelChoice): void {
  try {
    store()?.setItem(MODEL_KEYS[which], v);
  } catch {
    /* storage unavailable */
  }
}

export function loadGhostEnabled(): boolean {
  try {
    return store()?.getItem(GHOST_KEY) !== '0';
  } catch {
    return true;
  }
}

export function saveGhostEnabled(on: boolean): void {
  try {
    store()?.setItem(GHOST_KEY, on ? '1' : '0');
  } catch {
    /* storage unavailable */
  }
}

const SOUND_KEY = 'rockhop.sound';
const VOLUME_KEY = 'rockhop.volume';

export function loadSoundEnabled(): boolean {
  try {
    return store()?.getItem(SOUND_KEY) !== '0';
  } catch {
    return true;
  }
}

export function saveSoundEnabled(on: boolean): void {
  try {
    store()?.setItem(SOUND_KEY, on ? '1' : '0');
  } catch {
    /* storage unavailable */
  }
}

export function loadVolume(): number {
  try {
    const v = Number(store()?.getItem(VOLUME_KEY));
    return Number.isFinite(v) && v >= 0 && v <= 1 && store()?.getItem(VOLUME_KEY) !== null ? v : 0.8;
  } catch {
    return 0.8;
  }
}

export function saveVolume(v: number): void {
  try {
    store()?.setItem(VOLUME_KEY, String(Math.max(0, Math.min(1, v))));
  } catch {
    /* storage unavailable */
  }
}

const MUSIC_KEY = 'rockhop.musicVolume';

/** The music-only level (Settings · Music), 0..1; default 1 (the master still scales it). */
export function loadMusicVolume(): number {
  try {
    const raw = store()?.getItem(MUSIC_KEY);
    const v = Number(raw);
    return raw !== null && raw !== undefined && Number.isFinite(v) && v >= 0 && v <= 1 ? v : 1;
  } catch {
    return 1;
  }
}

export function saveMusicVolume(v: number): void {
  try {
    store()?.setItem(MUSIC_KEY, String(Math.max(0, Math.min(1, v))));
  } catch {
    /* storage unavailable */
  }
}

/** Reset progress: every `rockhop.best.*` entry (medals, PBs, ghosts). Settings stay. */
export function clearAllBest(): number {
  const s = store();
  if (!s) return 0;
  const keys: string[] = [];
  try {
    for (let i = 0; i < s.length; i++) {
      const k = s.key(i);
      if (k && k.startsWith(PREFIX)) keys.push(k);
    }
    for (const k of keys) s.removeItem(k);
  } catch {
    /* storage unavailable */
  }
  return keys.length;
}

export function loadQualityOverride(): QualityTier | 'auto' {
  try {
    const v = store()?.getItem(QUALITY_KEY);
    // A phone never boots on a stored `high`: earlier builds' probe promoted phones to high and the
    // manual override then stuck (the meter read "H" at 24–28 fps on a flagship). Auto re-probes from low.
    const phone = typeof matchMedia === 'function' && matchMedia('(pointer: coarse)').matches;
    if (phone && v === 'high') return 'auto';
    return v === 'low' || v === 'medium' || v === 'high' ? v : 'auto';
  } catch {
    return 'auto';
  }
}

/** The highest tier the governor saw this device hold for 30 s (Auto's start tier next boot). */
export function loadHeldTier(): QualityTier | null {
  try {
    const v = store()?.getItem(HELD_KEY);
    return v === 'low' || v === 'medium' || v === 'high' ? v : null;
  } catch {
    return null;
  }
}
export function saveHeldTier(t: QualityTier): void {
  try {
    const cur = loadHeldTier();
    const rank = { low: 0, medium: 1, high: 2 };
    if (!cur || rank[t] >= rank[cur]) store()?.setItem(HELD_KEY, t);
  } catch {
    /* storage unavailable */
  }
}

/** Frame cap: 'auto' = 60 (`src/game/app.ts frameCapHz`). */
export type FpsChoice = 'auto' | '30' | '60';
export function loadFpsChoice(): FpsChoice {
  try {
    const v = store()?.getItem(FPS_KEY);
    return v === '30' || v === '60' ? v : 'auto';
  } catch {
    return 'auto';
  }
}
export function saveFpsChoice(v: FpsChoice): void {
  try {
    const s = store();
    if (!s) return;
    if (v === 'auto') s.removeItem(FPS_KEY);
    else s.setItem(FPS_KEY, v);
  } catch {
    /* storage unavailable */
  }
}

export function saveQualityOverride(v: QualityTier | 'auto'): void {
  try {
    const s = store();
    if (!s) return;
    if (v === 'auto') s.removeItem(QUALITY_KEY);
    else s.setItem(QUALITY_KEY, v);
  } catch {
    /* storage unavailable */
  }
}

// ---------------------------------------------------------------------------
// Last run per track (replay viewer, docs/design/game.md §16)
// ---------------------------------------------------------------------------

const LAST_RUN_PREFIX = 'rockhop.lastrun.';

export interface LastRunEntry {
  time: number;
  faults: number;
  bike: BikeClass;
  /** ISO time the run finished. */
  at: string;
  /** JSON InputRecording, GO → finish. */
  recording: string;
}

/**
 * `rockhop.lastrun.<trackId>`: the most recent *finished* run on a track, any bike class, whatever
 * its time — "Watch replay" after a run that was not a PB, and the track card's second watch option.
 * Reset progress leaves these alone (they are not progress); a full storage clear drops them.
 */
export class LastRuns {
  private readonly cache = new Map<string, LastRunEntry | null>();

  get(trackId: string): LastRunEntry | null {
    const key = LAST_RUN_PREFIX + trackId;
    if (this.cache.has(key)) return this.cache.get(key) ?? null;
    const s = store();
    if (!s) return null;
    try {
      const raw = s.getItem(key);
      const o = raw ? (JSON.parse(raw) as Partial<LastRunEntry>) : null;
      const entry =
        o && typeof o.time === 'number' && typeof o.faults === 'number' && typeof o.recording === 'string' && o.recording.length > 0
          ? { time: o.time, faults: o.faults, bike: o.bike === 'pro' ? 'pro' : 'rookie', at: typeof o.at === 'string' ? o.at : '', recording: o.recording } satisfies LastRunEntry
          : null;
      this.cache.set(key, entry);
      return entry;
    } catch {
      return null;
    }
  }

  put(trackId: string, entry: LastRunEntry): void {
    const key = LAST_RUN_PREFIX + trackId;
    this.cache.set(key, entry);
    try {
      store()?.setItem(key, JSON.stringify(entry));
    } catch {
      /* quota / unavailable: the in-memory entry still serves this session */
    }
  }
}
