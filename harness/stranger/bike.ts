/** A fresh campaign rides C1–D2 on Rookie and D3–S3 on the earned Pro. */
import { DEFAULT_BIKE, type BikeClass } from '../../src/core/types';
import { defaultBikeForTier } from '../../src/game/rules';
import { getTrack } from '../../src/tracks';
import { ROCKHOP_TRACKS } from '../../src/tracks/rockhop';
import { parseBike } from '../lib/sim';

const CAMPAIGN_BIKES = new Map(ROCKHOP_TRACKS.map((track, index) => [track.id, index < 8 ? 'rookie' : 'pro'] as const));

export function campaignBikeForTrack(trackId: string): BikeClass | null {
  return CAMPAIGN_BIKES.get(trackId) ?? null;
}

export function defaultStrangerBike(trackId: string): BikeClass {
  const campaignBike = campaignBikeForTrack(trackId);
  if (campaignBike) return campaignBike;
  const track = getTrack(trackId);
  return track ? defaultBikeForTier(track.tier, null) : DEFAULT_BIKE;
}

export function bikeForTrack(trackId: string, flag: unknown): BikeClass {
  return parseBike(flag, defaultStrangerBike(trackId));
}

/** Reflex retains Rookie on retired tracks; only the current career selects Pro by default. */
export function reflexBikesForTrack(trackId: string, flag: unknown): BikeClass[] {
  if (flag === 'both' || flag === 'rookie,pro') return ['rookie', 'pro'];
  return [parseBike(flag, campaignBikeForTrack(trackId) ?? DEFAULT_BIKE)];
}
