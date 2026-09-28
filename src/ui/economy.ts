/**
 * Career Scrap is earned once per course medal tier, not once per finish. The
 * wallet and its award ledger live in one storage record so a reload cannot
 * replay an already paid medal. `platinum` is the historical save key for the
 * player-facing Diamond medal.
 */
import type { BikeClass, Medal } from '../core/types';
import { persistentStorage } from '../platform/storage';
import { ROCKHOP_TRACKS } from '../tracks/rockhop';

export const PRO_PRICE = 800;
export const SCRAP_REWARD: Readonly<Record<Medal, number>> = Object.freeze({ bronze: 100, silver: 160, gold: 220, platinum: 300 });
export const ECONOMY_KEY = 'rockhop.economy.v1';

const BIKE_KEY = 'rockhop.bikeClass';
const BEST_PREFIX = 'rockhop.best.';
const TRACK_IDS = new Set(ROCKHOP_TRACKS.map((track) => track.id));

interface Ledger {
  version: 1;
  wallet: number;
  medals: Record<string, Medal>;
  proOwned: boolean;
  equipped: BikeClass;
}

export interface EconomySnapshot {
  wallet: number;
  lifetimeEarned: number;
  proOwned: boolean;
  equipped: BikeClass;
  medals: Readonly<Record<string, Medal>>;
}

export interface AwardResult {
  delta: number;
  wallet: number;
  previous: Medal | null;
  current: Medal;
}

export type PurchaseResult = 'purchased' | 'already-owned' | 'insufficient-scrap';

function storage(): Storage | null {
  try {
    return persistentStorage();
  } catch {
    return null;
  }
}

function isMedal(value: unknown): value is Medal {
  return value === 'bronze' || value === 'silver' || value === 'gold' || value === 'platinum';
}

function maxMedal(a: Medal | undefined, b: Medal): Medal {
  return !a || SCRAP_REWARD[b] > SCRAP_REWARD[a] ? b : a;
}

function earned(medals: Record<string, Medal>): number {
  return Object.values(medals).reduce((sum, medal) => sum + SCRAP_REWARD[medal], 0);
}

/** Read only authored campaign PBs. Board rows and dev tracks never pay Scrap. */
function priorProgress(store: Storage | null): { medals: Record<string, Medal>; proUsed: boolean } {
  const medals: Record<string, Medal> = {};
  let proUsed = false;
  if (!store) return { medals, proUsed };
  for (const id of TRACK_IDS) {
    for (const bike of ['rookie', 'pro'] as const) {
      let raw: string | null;
      try {
        raw = store.getItem(`${BEST_PREFIX}${id}${bike === 'pro' ? '@pro' : ''}`);
      } catch {
        continue;
      }
      if (!raw) continue;
      try {
        const entry = JSON.parse(raw) as unknown;
        if (!entry || typeof entry !== 'object') continue;
        const value = entry as Record<string, unknown>;
        if (!Number.isFinite(value['time']) || !Number.isFinite(value['faults'])) continue;
        const medal = isMedal(value['medal']) ? value['medal'] : null;
        const best = isMedal(value['bestMedal']) ? value['bestMedal'] : null;
        if (!medal && !best) continue;
        if (bike === 'pro') proUsed = true;
        if (medal) medals[id] = maxMedal(medals[id], medal);
        if (best) medals[id] = maxMedal(medals[id], best);
      } catch {
        // A malformed PB cannot grant currency or ownership.
      }
    }
  }
  return { medals, proUsed };
}

function readLedger(store: Storage | null): Ledger | null {
  try {
    const raw = store?.getItem(ECONOMY_KEY);
    if (!raw) return null;
    const value = JSON.parse(raw) as unknown;
    if (!value || typeof value !== 'object') return null;
    const o = value as Record<string, unknown>;
    if (o['version'] !== 1 || !Number.isSafeInteger(o['wallet']) || (o['wallet'] as number) < 0 || typeof o['proOwned'] !== 'boolean') return null;
    if (!o['medals'] || typeof o['medals'] !== 'object' || Array.isArray(o['medals'])) return null;
    const medals: Record<string, Medal> = {};
    for (const [id, medal] of Object.entries(o['medals'])) {
      if (TRACK_IDS.has(id) && isMedal(medal)) medals[id] = medal;
    }
    const equipped = o['equipped'] === 'pro' && o['proOwned'] ? 'pro' : 'rookie';
    return { version: 1, wallet: Math.min(o['wallet'] as number, earned(medals)), medals, proOwned: o['proOwned'], equipped };
  } catch {
    return null;
  }
}

/**
 * Construct after legacy-key migration and before processing a run result.
 * Existing players receive exactly the value of their best career medals.
 * Pro usage or a saved Pro garage selection is grandfathered as ownership.
 */
export class CareerEconomy {
  private readonly store: Storage | null;
  private ledger: Ledger;

  constructor(store: Storage | null = storage()) {
    this.store = store;
    const prior = priorProgress(store);
    let choice: string | null = null;
    try {
      choice = store?.getItem(BIKE_KEY) ?? null;
    } catch {
      // Storage is optional in private mode and the headless harness.
    }
    const saved = readLedger(store);
    const proOwned = (saved?.proOwned ?? false) || prior.proUsed || choice === 'pro';
    const medals = { ...(saved?.medals ?? {}) };
    let backfill = 0;
    for (const [id, medal] of Object.entries(prior.medals)) {
      const previous = medals[id];
      if (previous && SCRAP_REWARD[previous] >= SCRAP_REWARD[medal]) continue;
      backfill += SCRAP_REWARD[medal] - (previous ? SCRAP_REWARD[previous] : 0);
      medals[id] = medal;
    }
    const equipped: BikeClass = choice === 'pro' && proOwned ? 'pro' : saved?.equipped === 'pro' && proOwned ? 'pro' : 'rookie';
    this.ledger = { version: 1, wallet: saved ? Math.min(saved.wallet + backfill, earned(medals)) : earned(medals), medals, proOwned, equipped };
    this.persist();
  }

  snapshot(): EconomySnapshot {
    const { wallet, medals, proOwned, equipped } = this.ledger;
    return { wallet, lifetimeEarned: earned(medals), proOwned, equipped, medals: { ...medals } };
  }

  /** Improvement pays only the difference from the already awarded tier. */
  award(trackId: string, medal: Medal): AwardResult {
    const previous = this.ledger.medals[trackId] ?? null;
    if (!TRACK_IDS.has(trackId) || !isMedal(medal)) return { delta: 0, wallet: this.ledger.wallet, previous, current: previous ?? 'bronze' };
    const delta = Math.max(0, SCRAP_REWARD[medal] - (previous ? SCRAP_REWARD[previous] : 0));
    if (delta > 0) {
      this.ledger.medals[trackId] = medal;
      this.ledger.wallet += delta;
      this.persist();
    }
    return { delta, wallet: this.ledger.wallet, previous, current: this.ledger.medals[trackId]! };
  }

  purchasePro(): PurchaseResult {
    if (this.ledger.proOwned) return 'already-owned';
    if (this.ledger.wallet < PRO_PRICE) return 'insufficient-scrap';
    this.ledger.wallet -= PRO_PRICE;
    this.ledger.proOwned = true;
    this.persist();
    return 'purchased';
  }

  /** Only owned bikes can be equipped. The legacy garage choice stays in sync. */
  equip(bike: BikeClass): boolean {
    if (bike === 'pro' && !this.ledger.proOwned) return false;
    this.ledger.equipped = bike;
    this.persist();
    try {
      this.store?.setItem(BIKE_KEY, bike);
    } catch {
      // Session state still works without persistence.
    }
    return true;
  }

  /** Pair with BestTimes.clear() when the player resets career progress. */
  clear(): void {
    this.ledger = { version: 1, wallet: 0, medals: {}, proOwned: false, equipped: 'rookie' };
    try {
      this.store?.removeItem(ECONOMY_KEY);
      this.store?.removeItem(BIKE_KEY);
    } catch {
      // In-memory reset still applies for this session.
    }
  }

  private persist(): void {
    try {
      this.store?.setItem(ECONOMY_KEY, JSON.stringify(this.ledger));
    } catch {
      // A blocked store is an in-memory session. PB backfill recovers medal awards next boot.
    }
  }
}
