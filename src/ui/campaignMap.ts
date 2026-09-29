/** The twelve 3D island towers in campaign order, with saved medal and lock state. */
import type { Medal, TrackDef } from '../core/types';
import { shipTracks, stageOf, trackUnlocked, unlockRuleFor, zoneOf, type MedalOf } from './progress';

export type RegionId = string;

export interface Marker {
  track: TrackDef;
  code: string;
  region: RegionId;
  medal: Medal | null;
  locked: boolean;
  rule: string | null;
}

export function buildCampaignMarkers(tracks: readonly TrackDef[], medalOf: MedalOf): Marker[] {
  const campaign = shipTracks(tracks);
  return campaign.map((track) => {
    const stage = stageOf(track);
    const locked = !trackUnlocked(campaign, track, medalOf);
    return {
      track,
      code: (track.meta as { code?: string } | undefined)?.code ?? track.id.split('-')[0]!.toUpperCase(),
      region: zoneOf(track) ?? stage,
      medal: medalOf(track.id),
      locked,
      rule: locked ? unlockRuleFor(campaign, stage) : null,
    };
  });
}
