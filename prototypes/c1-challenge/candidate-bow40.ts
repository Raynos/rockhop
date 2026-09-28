/** Standalone C1 challenge candidate. Authored with the shipping ROCKHOP builder; no production registration. */
import { rockhop } from '../../src/tracks/rockhop/builder';

export const C1_CHALLENGE = rockhop('C1', 'c1-low-tide', 'Low Tide', 'coast', 'beginner', {
  technique: 'brake and lean into a steep container bow',
  demands: 'brake at the girder marker, then lean forward up the beached bow before accelerating onto the causeway',
  idea: 'the harbour at low tide: ride the dry causeway out to the containers',
  hero: 'The Beached Container Bow',
  attemptsBand: [1, 3], // candidate proxy: average reflex 1 Rookie, 2–3 Pro; strangers still required
  targetTimeS: 50, // preserve the existing C1 medal target for comparison
})
  .hint('Hold the gas up the slipway')
  .hint('Steady gas over the tyres')
  .hint('Brake at the girder, then lean forward up the bow')
  .hint('Level the bike on the gangway')
  .camera({ mode: 'side' })
  .setPiece('start', 'The Slipway')
  .flat(6)
  .arch({ style: 'start' })
  .flat(18)
  .endSetPiece()
  .smooth(20, 1.4) // up the slipway (grounded at 20 m/s: 16.8 m needed)
  .flat(16) // the quay top
  .descent(20, 1.4, 20)
  .flat(8)
  .checkpoint()
  .flat(4)
  .bumpDrum(0.6, 0.18, { surface: 'rubber', prop: 'tyre' }) // the tyre line: half-buried truck tyres, 0.18 m proud, met at rolling speed off the spawn
  .flat(5)
  .bumpDrum(0.6, 0.18, { surface: 'rubber', prop: 'tyre' })
  .flat(5)
  .bumpDrum(0.6, 0.18, { surface: 'rubber', prop: 'tyre' })
  .flat(14)
  .rollers(30, 0.15, 4) // tide ripples in the sand
  .flat(8)
  .ledge({ height: 0.3, length: 6, surface: 'wood', prop: 'pallet' }) // a pallet kerb: 0.3 m rolls
  .ramp({ length: 4, height: 0.3, direction: 'down', surface: 'wood', prop: 'pallet' })
  .flat(12)
  .checkpoint()
  .flat(12) // checkpoint sightline before the braking marker
  .arch({ style: 'girder', span: 10, height: 6 }) // the brake marker, 18 m before the steep foot
  .camera({ mode: 'side-tight', zoomBias: -0.4 })
  .setPiece('balance', 'Brake for the Beached Bow')
  .flat(18) // braking lane: line speed ~14 m/s on entry
  .kickerPlank({ angleDeg: 40, rise: 3.2 })
  .box({ width: 12, height: 3.2, surface: 'metal', prop: 'container' })
  .ramp({ length: 28, height: 3.2, direction: 'down', surface: 'wood', prop: 'gangway' })
  .endSetPiece()
  .camera({ mode: 'side' })
  .flat(22)
  .checkpoint()
  .flat(8)
  .camera({ mode: 'side', zoomBias: 0.2 })
  .setPiece('balance', 'The Causeway')
  .ramp({ length: 12, height: 1.0, surface: 'wood', prop: 'pallet' }) // 4.8 deg pallet ramp
  .box({ width: 8, height: 1.0, prop: 'container', variant: 0 })
  .ramp({ length: 4, height: 0.3, surface: 'wood', prop: 'pallet' }, { base: 1.0 }) // a 4.3 deg pallet wedge up each 0.3 m step
  .box({ width: 6, height: 1.3, prop: 'container', variant: 1 })
  .ramp({ length: 4, height: 0.3, surface: 'wood', prop: 'pallet' }, { base: 1.3 })
  .box({ width: 8, height: 1.6, prop: 'container', variant: 2 })
  .ramp({ length: 20, height: 1.6, direction: 'down', surface: 'metal', prop: 'gangway' }) // 12.5 x h gangway
  .endSetPiece()
  .camera({ mode: 'side' })
  .flat(12)
  .rollers(20, 0.2, 3)
  .flat(6)
  .wave(36, 1.2, 20)
  .flat(4)
  .arch({ style: 'crowd' })
  .setPiece('finish')
  .flat(10)
  .arch({ style: 'finish' })
  .finish();
