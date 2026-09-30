/** The twelve 3D island towers in campaign order, with saved medal and lock state. */
import type { Medal, TrackDef } from '../core/types';
import { shipTracks, stageOf, trackLock, zoneOf, type CareerBikeState, type MedalOf } from './progress';

export type RegionId = string;

export interface Marker {
  track: TrackDef;
  code: string;
  region: RegionId;
  medal: Medal | null;
  locked: boolean;
  rule: string | null;
  garage: boolean;
}

export function buildCampaignMarkers(
  tracks: readonly TrackDef[], medalOf: MedalOf,
  bike: CareerBikeState = { proOwned: false, equipped: 'rookie' }, devUnlock = false,
): Marker[] {
  const campaign = shipTracks(tracks);
  return campaign.map((track) => {
    const stage = stageOf(track);
    const lock = trackLock(campaign, track, medalOf, bike, devUnlock);
    return {
      track,
      code: (track.meta as { code?: string } | undefined)?.code ?? track.id.split('-')[0]!.toUpperCase(),
      region: zoneOf(track) ?? stage,
      medal: medalOf(track.id),
      locked: lock !== null,
      rule: lock?.reason ?? null,
      garage: lock?.garage ?? false,
    };
  });
}
