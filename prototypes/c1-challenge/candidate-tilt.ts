/** Exploratory C1 tipping gangway variant; built with the production ROCKHOP DSL. */
import { rockhop } from '../../src/tracks/rockhop/builder';

export function makeTilt(id: string, length: number, height: number, runup: number) {
  return rockhop('C1', id, 'Low Tide', 'coast', 'beginner', {
  technique: 'throttle control over a tipping gangway',
  demands: 'ease off to settle a tipping gangway, then accelerate into the container causeway',
  idea: 'the harbour at low tide: ride the dry causeway out to the containers',
  hero: 'The Tipping Gangway',
  attemptsBand: [1, 1],
  targetTimeS: 50, // gold: skill-3 bot 29.72 s x 1.6 = 47.5, rounded up to 5 s, non-decreasing through the tier (OBSIDIAN = 0.85 x gold, 0 bails)
})
  .hint('Hold the gas up the slipway')
  .hint('Steady gas over the tyres')
  .hint('Ease off before the tipping gangway')
  .hint('Balance over the gangway; gas out')
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
  .flat(runup)
  .camera({ mode: 'side-tight', zoomBias: -0.4 })
  .setPiece('balance', 'The Tipping Gangway')
  .seesawEntry({ length, height, surface: 'wood', prop: 'gangway' })
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
