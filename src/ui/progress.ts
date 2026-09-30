/**
 * Progression, as stages. A ROCKHOP course (`meta.zone`) progresses by ZONE (store release Phase 3): COAST, then
 * ALPINE, QUARRY, SNOWLINE; a zone opens when every track of every earlier zone holds a medal. A track list with no
 * zones (the retired curriculum, dev lists, old tests) progresses by tier exactly as before. Playgrounds are outside
 * medals. Historical playground handling remains for dev-only retired courses; the shipped ROCKHOP catalog is twelve
 * campaign tracks. The first eight medals open course 9, and courses 9–12 require the purchased/equipped Pro.
 * `?dev=1` unlocks everything. Pure functions, unit-tested.
 */
import type { BikeClass, Medal, TrackDef, TrackTier } from '../core/types';
import { isPlaygroundTrackId } from '../tracks';
import { PRO_PRICE } from './economy';

export const TIER_ORDER: readonly TrackTier[] = ['beginner', 'easy', 'medium', 'hard', 'extreme'];
export const TIER_LABEL: Record<TrackTier, string> = { beginner: 'Beginner', easy: 'Easy', medium: 'Medium', hard: 'Hard', extreme: 'Extreme' };
export const TIER_BLURB: Record<TrackTier, string> = {
  beginner: 'Gas, brake, lean. Learn the bike.',
  easy: 'Weight on the pegs — climbs, drops, stairs.',
  medium: 'Hops, drums and balance.',
  hard: 'Wheelies on wire, gap chains, fire.',
  extreme: 'Everything at once. Bring restarts.',
};

/** The four zones in progression order and their short names (src/tracks/rockhop/zones.ts ZONE_ORDER / ZONE_LABEL). */
export const ZONE_STAGES: readonly string[] = ['coast', 'alpine', 'quarry', 'snowline'];
export const ZONE_STAGE_LABEL: Record<string, string> = { coast: 'Coast', alpine: 'Alpine', quarry: 'Quarry', snowline: 'Snowline' };

/** A track's zone (`meta.zone` on a ROCKHOP course), else null. */
export function zoneOf(t: TrackDef): string | null {
  return (t.meta as { zone?: string } | undefined)?.zone ?? null;
}

/** The progression stage of a track: its zone on a ROCKHOP course, else its tier. */
export function stageOf(t: TrackDef): string {
  return zoneOf(t) ?? t.tier;
}

/** The stage order of a list: zones when any track has one, else tiers. */
export function stagesOf(tracks: readonly TrackDef[]): readonly string[] {
  return tracks.some((t) => zoneOf(t) !== null) ? ZONE_STAGES : TIER_ORDER;
}

export function stageLabel(stage: string): string {
  return ZONE_STAGE_LABEL[stage] ?? TIER_LABEL[stage as TrackTier] ?? stage;
}

export type MedalOf = (trackId: string) => Medal | null;

/** The first eight courses build the Starter career; the final four require the purchased, equipped Pro. */
export const STARTER_COURSE_IDS = [
  'c1-low-tide', 'c2-crane-hop', 'c3-hull-breach',
  'a1-sawdust', 'a2-log-jam', 'a3-timberline',
  'd1-dust-devil', 'd2-conveyor',
] as const;
export const PRO_COURSE_IDS = ['d3-rope-walk', 's1-lift-line', 's2-cornice', 's3-whiteout'] as const;
const proCourseIds: ReadonlySet<string> = new Set(PRO_COURSE_IDS);

export interface CareerBikeState { proOwned: boolean; equipped: BikeClass }
export interface TrackLock { reason: string; garage: boolean }

export function isProCourse(t: TrackDef): boolean { return proCourseIds.has(t.id); }

/** Lab tracks (`lab-*`, src/tracks `isLabTrackId`): listed last under "Lab", outside progression, medals and the career line. */
export function isLabTrack(t: TrackDef): boolean {
  return t.id.startsWith('lab-');
}

export function labTracks(tracks: readonly TrackDef[]): TrackDef[] {
  return tracks.filter(isLabTrack);
}

/** Playground courses (`p<n>-*`, tracks round 10): one beginner course per biome, always open, outside medals and progression. */
export function isPlaygroundTrack(t: TrackDef): boolean {
  return isPlaygroundTrackId(t.id);
}

export function playgroundTracks(tracks: readonly TrackDef[]): TrackDef[] {
  return tracks.filter(isPlaygroundTrack);
}

/** Authored tracks only (no lab tracks, no playgrounds), tier order, stable within a tier. */
export function shipTracks(tracks: readonly TrackDef[], includeTest = false): TrackDef[] {
  return tracks
    .filter((t) => !isLabTrack(t) && !isPlaygroundTrack(t) && (includeTest || !t.id.endsWith('-test')))
    .slice()
    .sort((a, b) => {
      const order = stagesOf(tracks);
      return order.indexOf(stageOf(a)) - order.indexOf(stageOf(b)) || Number(a.id.endsWith('-test')) - Number(b.id.endsWith('-test'));
    });
}

export function tracksInTier(tracks: readonly TrackDef[], tier: TrackTier): TrackDef[] {
  return tracks.filter((t) => t.tier === tier);
}

/** True when every (authored, medal-bearing) track of `stage` has a medal. An empty stage counts as complete. */
export function stageComplete(tracks: readonly TrackDef[], stage: string, medalOf: MedalOf): boolean {
  return tracks
    .filter((t) => stageOf(t) === stage && !t.id.endsWith('-test') && !isPlaygroundTrack(t) && !isLabTrack(t))
    .every((t) => medalOf(t.id) !== null);
}

/** A stage is open when every earlier stage is complete (`?dev=1`: always). */
export function stageUnlocked(tracks: readonly TrackDef[], stage: string, medalOf: MedalOf, devUnlock = false): boolean {
  if (devUnlock) return true;
  const order = stagesOf(tracks);
  const i = order.indexOf(stage);
  for (let k = 0; k < i; k++) if (!stageComplete(tracks, order[k]!, medalOf)) return false;
  return true;
}

/** Authoritative career gate shared by map, quick play, result Next, and direct launch. */
export function trackLock(
  tracks: readonly TrackDef[], t: TrackDef, medalOf: MedalOf,
  bike: CareerBikeState = { proOwned: false, equipped: 'rookie' }, devUnlock = false,
): TrackLock | null {
  if (devUnlock || isLabTrack(t) || (isPlaygroundTrack(t) && zoneOf(t) === null)) return null;
  if (isProCourse(t) && STARTER_COURSE_IDS.some((id) => tracks.some((track) => track.id === id) && medalOf(id) === null)) {
    return { reason: 'Medal levels 01–08 to unlock the Pro run', garage: false };
  }
  if (!stageUnlocked(tracks, stageOf(t), medalOf)) {
    return { reason: unlockRuleFor(tracks, stageOf(t)), garage: false };
  }
  if (isProCourse(t) && !bike.proOwned) return { reason: `Buy the Pro bike in Garage · ${PRO_PRICE} Scrap`, garage: true };
  if (isProCourse(t) && bike.equipped !== 'pro') return { reason: 'Equip the Pro bike in Garage', garage: true };
  return null;
}

/** Whether a track can be ridden, including the final-four purchased-bike rule. */
export function trackUnlocked(
  tracks: readonly TrackDef[], t: TrackDef, medalOf: MedalOf, devUnlock = false,
  bike: CareerBikeState = { proOwned: false, equipped: 'rookie' },
): boolean {
  return trackLock(tracks, t, medalOf, bike, devUnlock) === null;
}

/** The first locked stage's gate rule (`Medal every Coast track`), '' for the first stage. */
export function unlockRuleFor(tracks: readonly TrackDef[], stage: string): string {
  const order = stagesOf(tracks);
  const prev = order[order.indexOf(stage) - 1];
  return prev ? `Medal every ${stageLabel(prev)} track` : '';
}

/** True when every (authored) track of `tier` has a medal. An empty tier counts as complete. */
export function tierComplete(tracks: readonly TrackDef[], tier: TrackTier, medalOf: MedalOf): boolean {
  return stageComplete(tracks, tier, medalOf);
}

/** The tier gate of a zone-less list; on a ROCKHOP list, the gate of the zone the tier's first track is in. */
export function tierUnlocked(tracks: readonly TrackDef[], tier: TrackTier, medalOf: MedalOf, devUnlock = false): boolean {
  if (stagesOf(tracks) === TIER_ORDER) return stageUnlocked(tracks, tier, medalOf, devUnlock);
  const first = tracks.find((t) => t.tier === tier && zoneOf(t) !== null);
  return first ? stageUnlocked(tracks, stageOf(first), medalOf, devUnlock) : true;
}

/** First unlocked track without a medal, else the last unlocked track (the natural "Play" target). */
export function nextTrack(tracks: readonly TrackDef[], medalOf: MedalOf, devUnlock = false, lastPlayed: string | null = null): TrackDef | null {
  const ship = shipTracks(tracks);
  if (lastPlayed) {
    const lp = ship.find((t) => t.id === lastPlayed);
    if (lp && stageUnlocked(ship, stageOf(lp), medalOf, devUnlock)) return lp;
  }
  let lastOpen: TrackDef | null = null;
  for (const t of ship) {
    if (!stageUnlocked(ship, stageOf(t), medalOf, devUnlock)) break;
    lastOpen = t;
    if (medalOf(t.id) === null) return t;
  }
  return lastOpen ?? ship[0] ?? null;
}

export interface MedalTotals {
  platinum: number;
  gold: number;
  silver: number;
  bronze: number;
  cleared: number;
  total: number;
}

export function medalTotals(tracks: readonly TrackDef[], medalOf: MedalOf): MedalTotals {
  const t: MedalTotals = { platinum: 0, gold: 0, silver: 0, bronze: 0, cleared: 0, total: 0 };
  for (const tr of shipTracks(tracks)) {
    t.total++;
    const m = medalOf(tr.id);
    if (m) {
      t.cleared++;
      t[m]++;
    }
  }
  return t;
}
