/**
 * ROCKHOP course set: twelve original tracks in four zones, three per zone. This is the set the store build ships;
 * the 3D island lists these tracks in normal play. They also resolve through `getTrack(id)` for the harness
 * and reviewer. `listTrackIds()` / `ALL_TRACKS` remain dev fixture and retired-track catalogs.
 *
 * The retired set (the 15-track curriculum, the five `p<n>-*` playgrounds, the Labs in `../courses`) stays in the
 * repo as dev-only reference: `RETIRED_TRACKS` names it, and `scripts/track-originality.mjs` holds every track
 * here under 0.6 profile correlation with every one of them (bar 2).
 */
import type { TrackDef } from '../../core/types';
import { rockhopMeta, medalTargets, type MedalTargets } from './builder';
import { ALPINE_TRACKS } from './alpine';
import { COAST_TRACKS } from './coast';
import { QUARRY_TRACKS } from './quarry';
import { SNOWLINE_TRACKS } from './snowline';
import { ZONE_ORDER, type ZoneId } from './zones';

export { ROCKHOP_ZONE_BIOME, ZONE_ORDER, ZONE_LABEL, ZONE_CODE, type ZoneId } from './zones';
export { medalTargets, rockhopMeta, type MedalTargets, type RockhopMeta } from './builder';

/** One row of the shipped progression, in order: what the world map / results screen read. */
export interface RockhopEntry {
  id: string;
  code: string;
  name: string;
  zone: ZoneId;
  tier: TrackDef['tier'];
  /** The four medals (bronze / silver / gold / OBSIDIAN = `platinum` in code), from `meta.targetTimeS`. */
  medals: MedalTargets;
  def: TrackDef;
}

/** The twelve tracks in progression order C1 -> S3. */
export const ROCKHOP_TRACK_DEFS: readonly TrackDef[] = [...COAST_TRACKS, ...ALPINE_TRACKS, ...QUARRY_TRACKS, ...SNOWLINE_TRACKS];

function entry(def: TrackDef): RockhopEntry {
  const m = rockhopMeta(def);
  return { id: def.id, code: m.code, name: def.name, zone: m.zone, tier: def.tier, medals: medalTargets(m.targetTimeS ?? 60), def };
}

export const ROCKHOP_TRACKS: readonly RockhopEntry[] = ROCKHOP_TRACK_DEFS.map(entry);
/** The shipped set has exactly twelve campaign courses. The old Free Ride source remains unregistered for historical evidence. */
export const ROCKHOP_ALL: readonly TrackDef[] = ROCKHOP_TRACK_DEFS;

/** Tracks of a zone, in order. */
export function rockhopZone(zone: ZoneId): RockhopEntry[] {
  return ROCKHOP_TRACKS.filter((t) => t.zone === zone);
}

export const ROCKHOP_ZONES = ZONE_ORDER;
