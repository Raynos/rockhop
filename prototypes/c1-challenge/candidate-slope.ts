/** Parameterized pallet-ramp prototype, authored with the shipping ROCKHOP builder. */
import { rockhop } from '../../src/tracks/rockhop/builder';

export function makeSlope(id: string, angleDeg: number, rise: number) {
  return rockhop('C1', id, 'Low Tide', 'coast', 'beginner', {
  technique: 'throttle control before a raised container deck',
  demands: 'ease off after Marker 2 to settle the pallet ramp and land level on the deck',
  idea: 'the harbour at low tide: ride the dry causeway out to the containers',
  hero: 'The Beached Ramp',
  attemptsBand: [1, 3], // candidate proxy: average reflex 1 Rookie, 2–3 Pro; strangers still required
  targetTimeS: 50, // preserve the existing C1 medal target for comparison
})
  .hint('Hold the gas up the slipway')
  .hint('Steady gas over the tyres')
  .hint('Ease off after Marker 2; roll up the pallet ramp')
  .hint('Level the bike on the deck, then gas out')
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
  .arch({ style: 'girder', span: 10, height: 6 }) // visible harbour girder, 18 m before the pallet ramp
  .camera({ mode: 'side-tight', zoomBias: -0.4 })
  .setPiece('balance', 'Ease Off for the Beached Ramp')
  .flat(18) // braking lane after Marker 2: an intentional roll makes the deck landing level
  .kickerPlank({ angleDeg, rise })
  .box({ width: 12, height: rise, surface: 'metal', prop: 'container' })
  .ramp({ length: 28, height: rise, direction: 'down', surface: 'wood', prop: 'gangway' })
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
}
