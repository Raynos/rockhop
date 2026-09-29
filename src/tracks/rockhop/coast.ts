/**
 * COAST — the coastal scrapyard (C-ride, D20): containers, cranes, junk piles, rusted hulls, pallets, tyres,
 * buoys, a harbour at low tide. The zone teaches the bike: braking, the first lean back, the
 * jump, the climb and the rear-wheel-first landing, each in the yard's own kit.
 *
 * Authoring numbers are the measured physics-v2 envelope (`FEEL`, docs/design/tracks.md §0): straight lips
 * <= 14 deg below the easy tier, every drop over 0.5 m onto a >= 8 x h down-ramp, grounded cosine hills at
 * 20 m/s, sunk tyres 0.3 m proud, 15 m of flat-or-descending run-up from every spawn to a speed obstacle.
 */
import { rockhop } from './builder';

/**
 * C1 LOW TIDE — the tide is out and the causeway is dry. TEACHES controlled braking: after Marker 2,
 * the rider must ease off to settle a steep pallet ramp and land level on the container deck. Holding GO
 * through that ramp repeatedly fails on both bikes. The later causeway retains its pallet-wedge climb.
 */
export const C1 = rockhop('C1', 'c1-low-tide', 'Low Tide', 'coast', 'beginner', {
  technique: 'brake before the beached ramp',
  demands: 'ease off after Marker 2 to settle the pallet ramp and land level on the deck',
  idea: 'the dry harbour causeway',
  hero: 'Ease Off for the Beached Ramp',
  attemptsBand: [1, 2], // provisional until real-time touch strangers; paused-step blind play took four attempts
  targetTimeS: 36, // current 30.350 s clean reference just earns Diamond; phone calibration remains
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
  .arch({ style: 'girder', span: 10, height: 6 })
  .camera({ mode: 'side-tight', zoomBias: -0.4 })
  .setPiece('balance', 'Ease Off for the Beached Ramp')
  .flat(18)
  .kickerPlank({ angleDeg: 22, rise: 2.2 })
  .box({ width: 12, height: 2.2, surface: 'metal', prop: 'container' })
  .ramp({ length: 28, height: 2.2, direction: 'down', surface: 'wood', prop: 'gangway' })
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

/**
 * C2 CRANE HOP — the harbour is a row of timber piers and moored barges. The final crane kicker
 * requires a level landing: release GO or pitch forward in flight before the container barge.
 */
export const C2 = rockhop('C2', 'c2-crane-hop', 'Crane Hop', 'coast', 'beginner', {
  technique: 'commit to the jump, then release or pitch forward in flight',
  demands: 'the crane hop: an 18 deg kicker off the apron over 5.5 m of harbour onto a container barge',
  idea: 'pier-to-barge harbour jump',
  hero: 'The Crane Hop',
  attemptsBand: [1, 2], // provisional until measured real-time touch attempts
  targetTimeS: 31, // current 26.608 s clean reference earns Gold; Diamond asks for a faster jump
})
  .hint('Gas off the first pier lip')
  .hint('Ease before Pier 2, lift the front briefly, then coast onto the down ramp')
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
  .kickerPlank({ angleDeg: 18, rise: 1.8 })
  .gap({ width: 5.5 })
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

/**
 * C3 HULL BREACH — two rusted freighters lie beached on the scrap strand. TEACHES uphill weight (lean forward,
 * steady gas up the hull plating) and the rear-wheel-first landing (the bilge channel, the slipway gap). DEMANDS
 * the breach: up 40 deg bow plating onto the big hull's deck and out through the torn plating in one flight onto
 * the beach ramp.
 */
export const C3 = rockhop('C3', 'c3-hull-breach', 'Hull Breach', 'coast', 'easy', {
  technique: 'uphill weight and the rear-wheel-first landing',
  demands: 'climb the 40 deg bow, set deck speed, clear the breach and land rear first',
  idea: 'escape the beached freighter',
  hero: 'The Breach',
  attemptsBand: [2, 3], // provisional: first new skill-3 Rookie bot needed two attempts; phone players unmeasured
  targetTimeS: 39, // current 37.817 s one-bail Rookie reference earns Gold; clean route remains to prove
})
  .hint('Lean forward up the stern')
  .hint('Set speed across the hull deck')
  .hint('Level before the breach')
  .hint('Land rear wheel first on the beach')
  .camera({ mode: 'side' })
  .setPiece('start', 'The Wreck Beach')
  .flat(6)
  .arch({ style: 'start' })
  .flat(18)
  .endSetPiece()
  .bumpDrum(0.6, 0.2, { surface: 'metal', prop: 'buoy' }) // beached buoys
  .flat(10)
  .bumpDrum(0.6, 0.2, { surface: 'metal', prop: 'buoy', variant: 1 })
  .flat(10)
  .checkpoint()
  .flat(16)
  .camera({ mode: 'side', zoomBias: -0.4 })
  .setPiece('climb', 'The Stern')
  .kickerPlank({ angleDeg: 34, rise: 2.2 }) // the small hull's stern plating: 34 deg
  .box({ width: 10, height: 2.2, prop: 'hull' })
  .ramp({ length: 20, height: 2.2, direction: 'down', surface: 'metal', prop: 'hull' })
  .endSetPiece()
  .camera({ mode: 'side' })
  .flat(10)
  .rollers(20, 0.25, 3)
  .flat(8)
  .checkpoint()
  .flat(16)
  .camera({ mode: 'high34' })
  .ramp({ length: 5, height: 1.2, surface: 'metal', prop: 'hull' }) // over the bilge channel
  .gap({ width: 4 })
  .gapLanding(1.0, 6, 8, 10) // land rear first on the incline
  .camera({ mode: 'side' })
  .flat(12)
  .bumpRow(2, 0.3, 16)
  .flat(8)
  .checkpoint()
  .flat(20)
  .camera({ mode: 'high34', zoomBias: -0.2 })
  .setPiece('climb', 'The Bow')
  .kickerPlank({ angleDeg: 40, rise: 3.2 }) // the big hull's bow plating: 40 deg over the kicker foot, a momentum climb
  .box({ width: 16, height: 3.2, prop: 'hull', variant: 1 }) // room to set speed across the hull before the torn opening
  .setPiece('air', 'The Breach')
  .ramp({ length: 2, height: 0.4, surface: 'metal', prop: 'hull' }, { base: 3.2 }) // the torn plating curls up: an 11 deg lip
  .gap({ width: 3.5 }) // daylight through the torn hull: the landing now requires an actual flight
  .ramp({ length: 28, height: 2.8, direction: 'down', surface: 'dirt' }) // a 0.8 m drop onto a 10 x h beach ramp
  .endSetPiece()
  .camera({ mode: 'side' })
  .flat(12)
  .rollers(20, 0.25, 3)
  .flat(8)
  .checkpoint()
  .flat(16)
  .camera({ mode: 'high34' })
  .ramp({ length: 5, height: 1.0, surface: 'wood', prop: 'pallet' }) // the slipway gap
  .gap({ width: 4 })
  .gapLanding(0.8, 5, 6, 8)
  .camera({ mode: 'side' })
  .flat(12)
  .wave(28, 1.2, 16)
  .flat(4)
  .arch({ style: 'crowd' })
  .setPiece('finish')
  .flat(10)
  .arch({ style: 'finish' })
  .finish();

export const COAST_TRACKS = [C1, C2, C3] as const;
