/** The campaign starts on Rookie; Pro enters only after an earned Garage purchase. */
import { DEFAULT_BIKE, type BikeClass } from '../../src/core/types';
import { defaultBikeForTier } from '../../src/game/rules';
import { getTrack } from '../../src/tracks';
import { ROCKHOP_ALL } from '../../src/tracks/rockhop';
import { parseBike } from '../lib/sim';

const CAMPAIGN_IDS = new Set(ROCKHOP_ALL.map((track) => track.id));

export function defaultStrangerBike(trackId: string): BikeClass {
  if (CAMPAIGN_IDS.has(trackId)) return 'rookie';
  const track = getTrack(trackId);
  return track ? defaultBikeForTier(track.tier, null) : DEFAULT_BIKE;
}

export function bikeForTrack(trackId: string, flag: unknown): BikeClass {
  return parseBike(flag, defaultStrangerBike(trackId));
}
