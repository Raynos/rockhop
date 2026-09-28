/** Isolated C2 crane-jump candidate; intentionally unregistered in production. */
import { rockhop } from '../../src/tracks/rockhop/builder';

export function makeCandidate(angleDeg: number, rise: number, gapWidth = 5.5, id = 'c2-crane-hop') {
  return rockhop('C2', id, 'Crane Hop', 'coast', 'beginner', {
  technique: 'commit to the jump, then release or pitch forward in flight',
  demands: `the crane hop: a ${angleDeg} deg kicker off the apron over ${gapWidth} m of harbour onto a container barge`,
  idea: 'hop the harbour pier to pier, then jump the water onto the barge under the crane',
  hero: 'The Crane Hop',
  attemptsBand: [2, 4], // unmeasured design hypothesis; real-time touch players required
  targetTimeS: 50, // retain the registered C2 target for comparison; candidate medal tuning is unresolved
})
  .hint('Gas off the first pier lip')
  .hint('Ease off and lean forward over Pier 2’s falling ramp')
  .hint('Land on the ramp down')
  .hint('At the crane, release GO or lean forward in flight')
  .camera({ mode: 'side' })
  .setPiece('start', 'The Harbour Road')
  .flat(6)
  .arch({ style: 'start' })
  .flat(18)
  .endSetPiece()
  .flat(16)
  // pier 1: up the pallet ramp onto the deck, off the lip at its end, land on the pier's ramp down
  .ramp({ length: 10, height: 1.0, surface: 'wood', prop: 'pallet' })
  .box({ width: 6, height: 1.0, surface: 'wood', prop: 'pier' })
  .ramp({ length: 3, height: 0.5, surface: 'wood', prop: 'pallet' }, { base: 1.0 }) // 9.5 deg lip
  .ramp({ length: 14, height: 1.0, direction: 'down', surface: 'wood', prop: 'gangway' }) // a 0.5 m drop off the lip onto 4 deg
  .flat(14)
  .checkpoint()
  .flat(16)
  // pier 2: taller, a steeper lip
  .ramp({ length: 10, height: 1.2, surface: 'wood', prop: 'pallet' })
  .box({ width: 5, height: 1.2, surface: 'wood', prop: 'pier' })
  .ramp({ length: 3, height: 0.75, surface: 'wood', prop: 'pallet' }, { base: 1.2 }) // 14 deg lip
  .ramp({ length: 16, height: 1.2, direction: 'down', surface: 'wood', prop: 'gangway' }) // a 0.75 m drop off the lip
  .flat(12)
  .bumpRow(2, 0.25, 20)
  .flat(8)
  .checkpoint()
  .flat(16)
  .ramp({ length: 5, height: 1.0, surface: 'wood', prop: 'pallet' }) // over the slipway cut: 11.3 deg
  .gap({ width: 3 })
  .gapLanding(0.6, 6, 6, 8) // a moored pontoon: land on its incline
  .flat(12)
  .rollers(20, 0.2, 3)
  .flat(8)
  .checkpoint()
  .flat(30) // the dock apron: 30 m of flat into the hop
  .camera({ mode: 'side-tight', zoomBias: -0.3, pitch: (12 * Math.PI) / 180 })
  .setPiece('air', 'The Crane Hop')
  .arch({ style: 'girder', span: 10, height: 7 }) // the crane gantry over the apron lip
  .kickerPlank({ angleDeg, rise })
  .gap({ width: gapWidth })
  .gapLanding(0.8, 9, 6, 10) // the container barge: incline, 9 m roof, the gangway down
  .endSetPiece()
  .camera({ mode: 'side' })
  .flat(12)
  .wave(32, 1.0, 20)
  .flat(4)
  .arch({ style: 'crowd' })
  .setPiece('finish')
  .flat(10)
  .arch({ style: 'finish' })
  .finish();
}

/** Selected candidate after the dimension scan; the production C2 remains untouched. */
export const C2_CHALLENGE = makeCandidate(18, 1.8);
